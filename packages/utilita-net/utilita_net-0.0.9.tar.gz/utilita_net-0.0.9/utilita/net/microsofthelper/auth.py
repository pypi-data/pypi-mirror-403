from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import os
import socket
import sqlite3
import json
import datetime
import requests
from urllib.parse import urlparse, parse_qs
from . import constants, log
import msal
import time
import atexit

class MSFTAuthHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.response_data = None
        self._keep_running = True

    def serve_until_done(self):
            try:
                while self._keep_running:
                    self.handle_request()
            except KeyboardInterrupt:
                self.shutdown()
                print("Shutting down due to Ctrl+C")

    def handle_one_request(self):
        self.handle_request()

    def finish_request(self, request, client_address) -> None:
        return super().finish_request(request, client_address)
    
    def shutdown(self):
        """Stop the serve_until_down loop."""
        self._keep_running = False
    
class MSFTAuthRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.response_data = self.path
        self.server.shutdown()
        
        resp_string = "Login was successful. It's now safe to close this window"

        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        if query_params.get("error", False):
            resp_string = f"""
            <!DOCTYPE html>
            <html> <head></head>
            <body>
            <p>We got an error: <b>{query_params.get("error", [""])[0]}</b></p>
            <pre style="max-width: 90%; overflow-x: auto;">
            {query_params.get('error_description', [""])[0]}
            {query_params.get('error_uri', [""])[0]}
            </pre>
            It's now safe to close this window.
            </body>
            </html
            """
            self.send_response(401)
        else:
            self.send_response(200)

        self.end_headers()
        self.wfile.write(resp_string.encode('utf-8'))

class AccessToken:
    def __init__(self, account_id, access_token, token_expiry, refresh_token, scopes):
        self.account_id = account_id
        self.access_token = access_token
        self.token_expiry = token_expiry
        self.refresh_token = refresh_token
        self.scopes = json.loads(scopes)

def account_id_required(func):
    def wrapper(self, *args, **kwargs):
        if not self.account_id:
            raise Exception("We have not successfully authenticated yet. Please sign in using the login() function.")
        return func(self, *args, **kwargs)
    return wrapper

"""If account_id is None, then we should take the first entry in the database (eg: a default credential)
"""
class Authenticate:
    def __init__(self, db_path=None, log_level='INFO', application_settings=None, account_id=None, keep_in_memory=True, auto_refresh=True, flush_at_exit=True) -> object:
        """Creates a new microsoft oauth token flow.
        
        Params:
            db_path: str = None - String path to the mshelper.db sqlite3 file

            log_level: str = INFO - log_level of the microsofthelper logger object

            application_settings: dict = None - dict of the application_settings required to identify to microsoft.
                example: application_settings = { "backend_port": int, "client_id": uuid4, "tenant_id": uuid4, "redirect_uri": str, "authority": str }

            account_id: str = None - Define the account_id to useif the database has multiple account_ids stored.

            keep_in_memory: bool = True - Takes the database on disk, copies it to memory, and preform all opertations in memory. 
                This was because when doing direct disk writes on a GCS Fuse mounted partition, the disk operations preformed by 
                this object causes it to crash. Defaults to True.

            auto_refresh: bool = True - Take the resolved account (either defined via account_id or the default) and attempts a token refresh if it is expired.

            flush_at_exit: bool = True - If keep_in_memory is True, this will flush database writes if it occured to the disk before exiting.
        """

        self.logger = log.get_logger(logger_name='microsoft_helper', level=log_level)
        self.db_path = db_path if db_path is not None else self._get_default_db_path()
        self.logger.debug(f'db_path is {self.db_path}')
        self.application_settings = application_settings
        self._write_occured = False # allows us to see at the end of a session if we should update the on-disk db if we are keeping everything in memory.
        self.keep_in_memory = keep_in_memory
        
        # init connection to db
        self._manage_db_connection(mode='ro') # either ro, rw, or rwc
        self.logger.debug(f'database is in {self.db_mode} mode')

        # get default user
        self.account_id = self._get_account_id(account_id=account_id)
        self.application_settings = self._get_application_settings(account_id=self.account_id) if application_settings is None else application_settings

        if self.application_settings is None:
            raise AttributeError('Please supply application_settings.')
        
        if auto_refresh and self.account_id is not None:
            self.get_access_token(attempt_refresh_if_necessary=True)

        if keep_in_memory and flush_at_exit:
            atexit.register(self.flush_db_to_disk)
    
    def login(self, request_scopes=[], open_browser_if_available=True) -> str:
        token_data = self._start_authentication_flow(scopes=request_scopes, open_browser_if_available=open_browser_if_available)
        login_name = token_data.get('id_token_claims', {}).get('preferred_username', None)
        
        was_account_deleted = self._del_data_by_account_id(account_id=login_name)
        if was_account_deleted:
            self.logger.warn(f'login() attempted for an account that is already in the credentials database ({login_name}). Replacing the current credentials.')

        # We get allowed scopes from the API, why are we feeding it in separately? because the API adds extra scopes that we cannot feed back in
        #  eg: API sends us 'openid', 'profile', 'offline_access' scopes, but we may not request them on refresh. :/
        login_name = self._token_response_to_db_insert(token=token_data, scopes=request_scopes)

        self.logger.info(f'Got successful Auth for {login_name}')

        self.account_id = login_name
        return login_name

    @account_id_required
    def logout(self):
        return self._del_data_by_account_id()

    @account_id_required
    def refresh_credentials_now(self) -> bool:
        """Forces a refresh of the auth token even if the current one is still valid. Return True if the refresh was successful. Otherwise an exception is raised.        """
        token = self._get_db_token()
        new_token = self._refresh_token_using_refresh_token(refresh_token=token.refresh_token, scopes=token.scopes)
        self._del_data_by_account_id()
        self._token_response_to_db_insert(token=new_token, scopes=token.scopes)
        return True

    @account_id_required
    def get_access_token(self, attempt_refresh_if_necessary=True) -> str:
        """ Get the access token stored as a string.
        Params:
            attempt_refresh_if_necessary: bool = True - Automatically refreshes token if it is expired.

        Returns:
            access_token: str -- an access token that is valid for microsoft graph.
        """
        token = self._get_db_token()
        exp_time = datetime.datetime.strptime(token.token_expiry, '%Y-%m-%d %H:%M:%S')

        if exp_time < datetime.datetime.now():
            self.logger.warn(f'The current access token expired {datetime.datetime.now() - exp_time} ago at {token.token_expiry}.')

            if attempt_refresh_if_necessary:
                self.logger.info(f'Refreshing access token')
                self.refresh_credentials_now()
                token = self._get_db_token()
                return token.access_token           

        return token.access_token           

    def get_available_account_ids(self):
        """Gets all of the available account IDs that are currently in the database, eg: accounts we have logged into."""
        query = 'select account_id from access_tokens'
        q_resp = self.credentials_database.execute(query).fetchall()

        if q_resp is not None:
            return [id[0] for id in q_resp]
        else:
            return []
        
    def check_token_valid(self, token=None):
        """Checks if the current token is valid. Returns True or False. if we have a token from outside,
                we can check it by using the token param.        
        """
        token_string = token if token is not None else self._get_db_token().access_token
        params = {
            'Authorization': f'Bearer {token_string}'
        }

        resp = requests.get('https://graph.microsoft.com/v1.0/me', headers=params)

        if resp.status_code != 200:
            self.logger.debug(f'Token is not valid, got message {resp.text}')
            return False
        else:
            return True

    def flush_db_to_disk(self):
        """Takes an in-memory database and flushes it to the db_path set in instantation. the path must exist beforehand. Returns True or False if successful."""
        if self.keep_in_memory and self._write_occured:
            disk_credentials_database = self._check_credential_db(db_path=self.db_path, mode='rw')

            if disk_credentials_database == None:
                if not os.path.exists(path=self.db_path):
                    db_directory = os.path.dirname(self.db_path)
                    self.logger.debug(f'Creating directory {db_directory}')
                    os.makedirs(name=db_directory, exist_ok=True)
                
                disk_credentials_database = sqlite3.connect(database=self.db_path)

            self.logger.debug(f'Syncing in-memory db to path {self.db_path}')
            self.credentials_database.backup(disk_credentials_database)
            disk_credentials_database.close()
            # This is to hopefully allow GCS fuse to fully sync to the bucket.
            time.sleep(2)
            return True
        else:
            return False


    ### db init and maintainence
    def _manage_db_connection(self, mode: str):
        """Creates and maintains the db connection. We should default in ro mode unless rw/rwc was specified."""

        if self.keep_in_memory:
            if not hasattr(self, 'credentials_database'):
                disk_credentials_database = self._check_credential_db(db_path=self.db_path, mode='ro')
                if disk_credentials_database == None:
                    disk_credentials_database = self._init_default_db(db_path=':memory:')

                self.credentials_database = sqlite3.connect(':memory:')
                disk_credentials_database.backup(self.credentials_database)
                disk_credentials_database.close()
                time.sleep(2)
                self.logger.info(f'Copied {self.db_path} into in-memory database.')
            else:
                self.logger.debug('using in-memory database. Ignoring reconnect attempt.')

            self.db_mode = 'rw'

        else:
            # If db has not been init
            if not hasattr(self, 'credentials_database'):
                self.credentials_database = self._check_credential_db(db_path = self.db_path, mode=mode) ### readonly or readwrite
                
                if self.credentials_database == None:
                    self.logger.warning('Database does not exist in path, creating default database.')
                    self.credentials_database = self._init_default_db()
            else:
                self.logger.debug(f'Remounting {self.db_path} as {mode}')
                self.credentials_database.close()
                
                full_connect_string = 'file:' + self.db_path + f'?mode={mode}'
                self.logger.debug('full_connect_string is {a}'.format(a=full_connect_string))
                self.credentials_database = sqlite3.connect(database=full_connect_string, uri=True)
        

    def _check_credential_db(self, db_path, mode):
        if os.path.exists(db_path):
            full_connect_string = 'file:' + self.db_path + f'?mode={mode}'
            self.logger.debug('full_connect_string is {a}'.format(a=full_connect_string))    
            conn = sqlite3.connect(database=full_connect_string, uri=True)
            self.db_mode = mode
            return conn
        else:
            self.logger.warning('Database does not exist.')
            self.db_mode = None
            return None

    ### ############################################################

    def _get_account_id(self, account_id=None):
        """Get the account ID from the database. if account_id is none it gets the first row"""
        if account_id is not None:
            query = f'select account_id from access_tokens where account_id = \'{account_id}\' COLLATE NOCASE limit 1;'
        
        else:
            query = 'select account_id from access_tokens limit 1;'

        q_data = self.credentials_database.execute(query).fetchone()

        if q_data is None:
            account_id = f'an active user' if account_id is None else account_id
            self.logger.warn(f'Could not find {account_id} in the database. Please call login().')
            return None
        
        else:
            self.logger.info(f'Logged in as {q_data[0]}')
            return q_data[0]
        
    def _get_application_settings(self, account_id=None):
        """Get application settings if it already exists in the database."""
        if account_id is not None:
            query = f"""
                SELECT tenant_application_settings.application_settings FROM tenant_application_settings
                    INNER JOIN access_tokens ON access_tokens.tenant = tenant_application_settings.tenant
                    WHERE access_tokens.account_id = \'{account_id}\' COLLATE NOCASE LIMIT 1;
                """
        q_data = self.credentials_database.execute(query).fetchone()

        if q_data is None:
            raise Exception(f'Could not get cached application settings from database. You must supply application_settings.')
        
        else:
            self.logger.debug(f'Got cached application settings.')
            return json.loads(q_data[0])
        
    def _get_db_token(self):
        select_statement = f"SELECT account_id, access_token, token_expiry, refresh_token, scopes from access_tokens where account_id = \'{self.account_id}\' COLLATE NOCASE"

        q_results = self.credentials_database.execute(select_statement).fetchone()

        if q_results is not None:
            return AccessToken(*q_results)
        else:
            raise Exception(f'Could not get access token. account id is {self.account_id}.')        

    def _init_default_db(self, force=True, db_path=None):
        """Creates default database if one was not found either in the path specified or in the default path."""
        db_path = self.db_path if db_path is None else db_path
        self.db_mode = 'rw'

        # Hack to allow creating a default database in a sqlite memory database.
        if db_path != ':memory:':
            if not os.path.exists(path=db_path):
                db_directory = os.path.dirname(db_path)
                self.logger.debug(f'Creating directory {db_directory}')
                os.makedirs(name=db_directory, exist_ok=True)

            if force and os.path.exists(db_path):
                if self.credentials_database:
                    self.credentials_database.close()
                    
                self.logger.debug('Deleting old database')
                os.remove(db_path)

        conn = sqlite3.connect(database=db_path)
        create_statement = """
            CREATE TABLE \"access_tokens\" (account_id TEXT PRIMARY KEY, access_token TEXT, token_expiry TIMESTAMP, refresh_token TEXT, id_token TEXT, scopes TEXT, tenant TEXT, debug_response TEXT);
            CREATE TABLE \"tenant_application_settings\" (tenant TEXT PRIMARY KEY, application_settings TEXT);
            """
        conn.executescript(create_statement)
        conn.commit()
        self._write_occured = True
        return conn

    def _token_response_to_db_insert(self, token: dict, scopes: list) -> str:

        # Only keep the db in rw mode when we are writing. this lowers the chance of scripts breaking due
        #  to file locks.
        self._manage_db_connection(mode='rw')
        token_claims = token.get('id_token_claims')

        exp_timestamp = datetime.datetime.fromtimestamp(token_claims.get('exp')).strftime('%Y-%m-%d %H:%M:%S')

        insert_statement = "INSERT INTO access_tokens (account_id, access_token, token_expiry, refresh_token, id_token, scopes, tenant, debug_response) values (?, ?, ?, ?, ?, ?, ?, ?)"
        tenant_insert_statement = "INSERT OR REPLACE INTO tenant_application_settings (tenant, application_settings) values (?, ?)"

        insert_values = (
            token_claims.get('preferred_username'),               # account_id
            token.get('access_token'),                      # access_token
            exp_timestamp,                                        # token_expiry
            token.get('refresh_token'),                     # refresh_token
            token.get('id_token'),                          # id_token
            json.dumps(scopes),                               # scopes
            token_claims.get('tid'),                              # tenant id
            json.dumps(token)                                 # raw object
            )
        
        tenant_values = (
            self.application_settings.get('tenant_id'), # tenant id
            json.dumps(self.application_settings)   # application settings json string
        )

        cursor = self.credentials_database.cursor()

        cursor.execute(insert_statement, insert_values)
        cursor.execute(tenant_insert_statement, tenant_values)
        cursor.close()
        self.logger.debug(f'Inserted token for {insert_values[0]} into credentials database.')

        self.credentials_database.commit()
        self._write_occured = True
        self._manage_db_connection(mode='ro')
        return insert_values[0]
    
    def _del_data_by_account_id(self, account_id=None):
        """Looks in the database and deletes the row matching account_id. account_id can be passed in if needed.

        Params:
            account_id: str = None. account id in the form of id_token_claims / preferred_username. This should be an email. 
        """
        account_id = account_id if account_id is not None else self.account_id

        self._manage_db_connection(mode='rw')
        query = f'delete from access_tokens where account_id = \'{account_id}\' COLLATE NOCASE'

        q_resp = self.credentials_database.execute(query)
        self.credentials_database.commit()
        self._write_occured = True
        self._manage_db_connection(mode='ro')
        if q_resp.rowcount == 1:
            return True
        else:
            return False

    def _get_default_db_path(self) -> str:
        """Gets the default path for storing the mshelper database."""
        if os.name == 'nt':
            _default_credential_path = os.path.expandvars(constants.DEFAULT_DEV_CREDENTIAL_PATH_WINDOWS)
        elif os.name == 'posix':
            _default_credential_path: constants.DEFAULT_DEV_CREDENTIAL_PATH_LINUX
        else:
            _default_credential_path = ''
            
        _default_db_path = os.path.join(_default_credential_path, constants.DEFAULT_DB_NAME)

        self.logger.debug(f'Defaulting db_path to {_default_db_path}')
        return _default_db_path
    
    def _start_authentication_flow(self, scopes: list, open_browser_if_available=True) -> str:
        """Begins an oauth flow using the msal library to get the url and session tokens.
        
        params:
            open_browser_if_available: bool = True - uses the webbrowser library to open a browser window for auth.
        """
        CLIENT_ID = self.application_settings.get('client_id')
        AUTHORITY = self.application_settings.get('authority')
        REQUEST_SCOPES = scopes
        REDIRECT_URI = self.application_settings.get('redirect_uri')
        BACKEND_PORT = self.application_settings.get('backend_port')

        app_public = msal.PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)

        # https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest prompt=select_account forces the browser to let you choose.
        auth_url = app_public.get_authorization_request_url(REQUEST_SCOPES, redirect_uri=REDIRECT_URI, prompt='select_account')
        httpd = MSFTAuthHTTPServer(('localhost', BACKEND_PORT), MSFTAuthRequestHandler)
        # There is an issue where sometimes the http port does not get released back to the OS.
        httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        if open_browser_if_available:
            webbrowser.open(auth_url)

        self.logger.info('If the browser does not open, copy the following url into it:')
        self.logger.info(auth_url)

        httpd.handle_one_request()
        # response_data = httpd.response_data
        httpd.server_close()
        # response_data = return url string sent by Microsoft
        parsed_url = urlparse(httpd.response_data)
        params = parse_qs(parsed_url.query)

        params = {k: v[0] if len(v) == 1 else v for k, v in params.items()}

        if 'code' in params:
            token_data: str = app_public.acquire_token_by_authorization_code(params.get('code'), REQUEST_SCOPES, redirect_uri=REDIRECT_URI)
            return token_data
        else:
            raise PermissionError(f'oauth service did not send an authorization code. the returned url was {httpd.response_data}')
        
    def _refresh_token_using_refresh_token(self, refresh_token: str, scopes: list) -> dict:
        CLIENT_ID = self.application_settings.get('client_id')
        AUTHORITY = self.application_settings.get('authority')
        REQUEST_SCOPES = scopes
        app_public = msal.PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY)
        
        token_data = app_public.acquire_token_by_refresh_token(refresh_token=refresh_token, scopes=REQUEST_SCOPES)

        if 'access_token' in token_data:
            return token_data
        
        else:
            raise PermissionError(f'oauth service did not send an authorization code. the returned data was {json.dumps(token_data)}')