import requests
import json
import urllib
import os
import io

def attribute_allowed_list(value: str, allowed_list: list, raise_exception=False, hint='') -> bool:
    """Checks if a value is in a list of accepted values. Will raise a ValueError exception when raise_exception is true."""
    if value in allowed_list:
        return True
    if raise_exception:
        raise ValueError(f'{hint}Expected {allowed_list} but got {value}')
    return False

def validate_attribute_allowed_list(value: str, allowed_list: list, raise_exception=True, hint='') -> str:
    """Checks if a value is in a list of accepted values. Will raise a ValueError exception when raise_exception is true. Otherwise return None"""
    if value in allowed_list:
        return value
    if raise_exception:
        raise ValueError(f'{hint}Expected {allowed_list} but got {value}')
    return None

class APIException(Exception):
    """This is a catchall for API Errors. json response should be available via the extra_data attribute."""
    def __init__(self, Exception, extra_data=None):
        self.extra_data = extra_data

class SharepointHelper:
    def __init__(self, authorization_token: str, sharepoint_site_url: str, base_url: str='https://graph.microsoft.com/v1.0', log_level='INFO'):
        """Allows interaction with a sharepoint site. One object instance is one site.

            Params:
                
                authorization_token: bearer token for authenticating to Microsoft.

                sharepoint_site_url: actual URL of the site: eg: https://tenant.sharepoint.com/sites/Sharepoint-Site

                base_url: This should not be needed, but change the URL of the microsoft graph service.

                log_level: Sets the verbosity of the logging messages. Defaults to INFO. Follows the standard python logging log levels.
        """
        self.logger = self._get_logger(logger_name='sharepoint_helper', level=log_level)
        self.base_url = base_url
        self.authorization_token = authorization_token
        self.sharepoint_site_url = sharepoint_site_url
        self.sharepoint_site_id = self.get_sharepoint_site_id(sharepoint_site_url=sharepoint_site_url)


    def _get_logger(self, logger_name: str, level='INFO'):
        """
        Check if logger instance already exists. Default will be set to INFO.
        """
        import logging
        if logger_name in logging.Logger.manager.loggerDict.keys():
            # Logger exists, so return it
            return logging.getLogger(logger_name)
        else:
            log_level = {'NOTSET': 0, 'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40, 'CRITICAL': 50}.get(level)
            logger = logging.getLogger(name=logger_name)
            handler = logging.StreamHandler()
            formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(fmt=formatter)
            logger.addHandler(hdlr=handler)
            logger.setLevel(level=log_level)
            return logger


    def get_token_info(self):
        """Gets the raw json string of the token used for this object.

            Params:
                None.

            Returns:
                token_info as a json string.

            Raises:
                APIException if we do not get a 200 response.
        """
        full_url = self.base_url + '/me'
        headers = {
            'Authorization' : f'Bearer {self.authorization_token}'
        }
        r = requests.get(url=full_url, headers=headers, timeout=60)

        if r.status_code != 200:
            raise APIException(f'Got an error getting /me ({r.status_code}). Extra data is {r.text}', extra_data=r.text)

        return json.loads(r.text)
    
    def get_graph_url_from_web_url(self, sharepoint_url: str) -> {'sharepoint_string': str, 'hostname': str, 'site_url': str, 'graph_url': str}:
        """Reformats a human-readable URL into a web/sharepoint URL. This is just reformatting, we do not make calls to micrsoft here.

            Params:
                sharepoint_url: full url of a sharepoint file (or expected file) eg: https://tenant.sharepoint.com/sites/Sharepoint-Site/reports folder/report1.xlsx

            Returns:
                formatted path parts in web format as a dict

            Raises:
                None.
        """
        split = urllib.parse.urlparse(sharepoint_url)
        path_components = split.path.split('/')
        assert len(path_components) > 2 and path_components[1].lower() == 'sites', f'could not determine sharepoint path. expected https://tenant.sharepoint.com/sites/Sharepoint-Site, got {sharepoint_url}'
        site_url = f'/{path_components[1]}/{path_components[2]}'
        file_path = f'/'.join(path_components[3:-1])
        file_name = path_components[-1]

        return {
            'sharepoint_string': f'{split.scheme}://{split.netloc}{site_url}',
            'hostname': split.netloc,
            'site_url': '%20'.join(site_url.split()),
            'file_path': '%20'.join(file_path.split()), #TODO: Ugly as shit. #'%20'.join(path_metadata.get('file_path').split())
            'file_name': '%20'.join(file_name.split()),
            'graph_url': f'{split.netloc}:{site_url}'
        }
    

    def get_sharepoint_site_id(self, sharepoint_site_url: str):
        """Gets an internal sharepoint site ID from a human readable url

            Params:
                sharepoint_url: full human readable url of a sharepoint site eg: https://tenant.sharepoint.com/sites/Sharepoint-Site

            Returns:
                sharepoint internal site ID as a string.

            Raises:
                APIException: In the event we get any response of >= 400
        """
        decoded_dict = self.get_graph_url_from_web_url(sharepoint_url=sharepoint_site_url)

        full_url: str = f'{self.base_url}/sites/{decoded_dict.get("graph_url")}'
        # print('full_url:', full_url)
        headers = {
            'Authorization' : f'Bearer {self.authorization_token}'
        }

        r = requests.get(url=full_url, headers=headers, timeout=60)
        self.logger.debug(f'get_sharepoint_site_id: GET {full_url}')
        if r.status_code >= 400:
            raise APIException(f'We got an API Exception {r.status_code}. extra data is {r.text}', extra_data=r.text)

        full_resp = json.loads(s=r.text)
        
        return full_resp.get('id')
    
    def upload_file_from_bytes(self, upload_path: str, file_bytes: bytes, if_exists='fail'):
        """Upload a file to sharepoint from bytes.

            Params:
                upload_path: full human readable url of a sharepoint file eg: "https://tenant.sharepoint.com/sites/Sharepoint-Site/report folder/Finance Report 2023-1-1.xlsx"
                
                file_bytes: the raw bytes of a file eg: when using open()

                if_exists: What to do if the file in that path already exists. Can be (fail | warn | ignore). Defaults to fail.

            Returns:
                dict of the file metadata that was uploaded.

            Raises:
                APIException: In the event we get any response of >= 400
        """
        if_exists = validate_attribute_allowed_list(value=if_exists, allowed_list=['fail', 'warn', 'ignore'], hint='upload_from_bytes if_exists ')
        web_path = urllib.parse.quote(upload_path)
        # https://learn.microsoft.com/en-us/graph/api/driveitem-createuploadsession?view=graph-rest-1.0#upload-bytes-to-the-upload-session
        preferred_chunk_size = 26214400 # ~25mb # This is for the future when we support more than 64mb of data. Must be divsible by 320KiB

        if isinstance(file_bytes, bytes):
            file_bytes = io.BytesIO(file_bytes)
        
        if isinstance(file_bytes, io.BytesIO):
            file_size = file_bytes.getbuffer().nbytes
        else:
            file_size = os.fstat(file_bytes.fileno()).st_size

        max_single_request_size = 61865984 # Microsoft graph only allows 64mb per POST. We must chunk the file if we want to do more.

        initial_body = {
            "@microsoft.graph.conflictBehavior": "fail", # fail (default) | replace | rename THIS LINE DOES NOT WORK WITH UPLOAD SESSIONS
            "fileSize": file_size,
            "deferCommit": True # Do not make file available until its completed.
        }
        initial_headers = {
            'Authorization' : f'Bearer {self.authorization_token}',
            'Content-Type': 'application/json'
        }

        initial_full_url = f"{self.base_url}/sites/{self.sharepoint_site_id}/drive/root:/{web_path}:/createUploadSession"

        # This exists because it looks like the @microsoft.graph.conflictBehavior does not protect you on createUploadSession.
        file_metadata = self.get_file_metadata(file_path=upload_path)
        if file_metadata is not None:
            if if_exists == 'fail':
                raise APIException(f'The file {upload_path} exists and if_exists is {if_exists}')
            elif if_exists == 'warn':
                # Why do this? Overwrites are supported by default. but deleting the file deletes sharing links.
                self.delete_file_by_path(file_path=upload_path)
                self.logger.warning(f'The file {upload_path} exists. Overwriting.')

        r = requests.post(url=initial_full_url, headers=initial_headers, data=json.dumps(initial_body), timeout=600)

        if r.status_code != 200:
            raise APIException(f'Got an exception while creating upload session: {r.status_code}. Extra data is {r.text}', extra_data=r.text)
        try:
            file_bytes.seek(0) # Should not need this, but just in case lets make sure we know where we start.
            upload_info = json.loads(r.text)
            upload_url = upload_info.get('uploadUrl')
            self.logger.debug(f'Upload URL is {upload_url}')

            # If the file size is below 64mb, lets upload it all in one request
            if file_size < max_single_request_size:
                headers: dict[str, str] = {
                'Content-Length': f'{file_size}',
                'Content-Range': f'bytes 0-{file_size-1}/{file_size}' # If uploading a 65536 size file, the string must be 'bytes 0-65535/65536'
                }
                rq: requests.Response = requests.put(url=upload_url, headers=headers, data=file_bytes.read(), timeout=600)
                # pass
                if rq.status_code != 202:
                    ex = requests.delete(url=upload_url, timeout=60)
                    raise APIException(f'Unable to upload file. Code is {rq.status_code} Cancelling upload.  Extra data is {rq.text}', extra_data=rq.text)
                
            else:
                byte_position = 0
                while byte_position < file_size:
                    current_chunk_size: int = preferred_chunk_size
                    if byte_position + current_chunk_size >= file_size:
                        current_chunk_size: int = file_size - byte_position
                    
                    self.logger.debug('Uploading %i -> %i of %i. Chunksize %i', byte_position, (byte_position + current_chunk_size), file_size, current_chunk_size)
                    
                    headers: dict[str, str] = {
                    'Content-Length': f'{current_chunk_size}',
                    'Content-Range': f'bytes {byte_position}-{byte_position+current_chunk_size-1}/{file_size}' # If uploading a 65536 size file, the string must be 'bytes 0-65535/65536'
                    }
                    rq: requests.Response = requests.put(url=upload_url, headers=headers, data=file_bytes.read(current_chunk_size), timeout=600)

                    byte_position = byte_position + current_chunk_size

                    if rq.status_code != 202:
                        ex = requests.delete(url=upload_url, timeout=60)
                        raise APIException(f'Unable to upload file. Code is {rq.status_code} Cancelling upload. Extra data is {rq.text}', extra_data=rq.text)
            
            # Finalize the file.
            headers_finalize = {
            'Content-Length': '0'
            }
            r_finalize: requests.Response = requests.post(url=upload_url, headers=headers_finalize, timeout=60)

            uploaded_file_info = json.loads(r_finalize.text)
            self.logger.info(f'Uploaded to {upload_path}')
            return uploaded_file_info
            
        except Exception:
            rq_del = requests.delete(url=upload_url, timeout=60)
            raise APIException(f'Got an exception while attempting to upload a multipart file. Cancelling upload session.')
        

    def get_file_metadata(self, file_path) -> dict:
        """Get Individual metadata about a sharepoint file.
        Returns either a dict or None if the file does not exist.

        Params:
            file_path: full human readable url of a sharepoint file eg: "https://tenant.sharepoint.com/sites/Sharepoint-Site/report folder/Finance Report 2023-1-1.xlsx"

        Returns:
            sharepoint file metadata as a dict

        Raises:
            APIException: In the event we get any response of >= 400
        """
        web_path = urllib.parse.quote(file_path)
        full_url = f"{self.base_url}/sites/{self.sharepoint_site_id}/drive/root:/{web_path}"
        self.logger.debug(f'Formatted URL for {file_path} is {full_url}')
        headers = {
            'Authorization' : f'Bearer {self.authorization_token}'
        }

        r = requests.get(url=full_url, headers=headers, timeout=60)
        if r.status_code not in [200, 404]:
            raise APIException(f'Got an exception getting file metadata for {file_path} {r.status_code}, full text is {r.text}', extra_data=r.text)

        if r.status_code == 404:
            return None
            
        return json.loads(r.text)
    
    def get_file_id(self, file_path) -> str:
        """
        Get the Sharepoint file ID if it exists, else return None

        Params:
            file_path: full human readable url of a sharepoint file eg: "https://tenant.sharepoint.com/sites/Sharepoint-Site/report folder/Finance Report 2023-1-1.xlsx"

        Returns:
            sharepoint file ID as a string.

        Raises:
            APIException: In the event we get any response of >= 400
        """

        file_metadata = self.get_file_metadata(file_path=file_path)

        if file_metadata is not None:
            return file_metadata.get('id')
        return None
    
    def delete_file_by_path(self, file_path) -> bool:
        """Delete a file in a sharepoint folder. Returns true if succeeded.

        Params:
            file_path: full human readable url of a sharepoint file eg: "https://tenant.sharepoint.com/sites/Sharepoint-Site/report folder/Finance Report 2023-1-1.xlsx"

        Returns:
            True if the file was deleted, False if it did not.
        """
        web_path = urllib.parse.quote(file_path)
        full_url = f"{self.base_url}/sites/{self.sharepoint_site_id}/drive/root:/{web_path}"
        self.logger.debug(f'Formatted URL for {file_path} is {full_url}')
        headers = {
            'Authorization' : f'Bearer {self.authorization_token}'
        }
        del_req = requests.delete(url=full_url, headers=headers, timeout=60)

        self.logger.debug(f'Delete response for {file_path}: {del_req.status_code}')
        
        if del_req.status_code == 204:
            return True
        
        return False
    
    def list_files_using_prefix(self, path: str) -> list:
        """Given a specified path, return all files in the directory."""
        # https://learn.microsoft.com/en-us/graph/api/driveitem-search?view=graph-rest-1.0&tabs=http
        # https://learn.microsoft.com/en-us/graph/api/driveitem-list-children?view=graph-rest-1.0&tabs=http
        web_path = urllib.parse.quote(path)
        full_url = f"{self.base_url}/sites/{self.sharepoint_site_id}/drive/root/search(q='{web_path}')"
        print(full_url)
        headers = {
            'Authorization' : f'Bearer {self.authorization_token}'
        }

        get_req = requests.get(url=full_url, headers=headers)

        return get_req
    
    # auth_type = 'users' # organization | users # Must pick one or the other.
    # https://learn.microsoft.com/en-us/graph/api/driveitem-createlink?view=graph-rest-1.0&tabs=http
    # Looks like we cannot create passworded links. Pitty.
    def create_access_link_from_path(self, file_path, file_permissions):
        """Create an access link from an already uploaded sharepoint file.

            Params:
                file_path: full human readable url of a sharepoint file eg: "https://tenant.sharepoint.com/sites/Sharepoint-Site/report folder/Finance Report 2023-1-1.xlsx"
                
                file_permissions: as a dict, the settings of the share link. Examples are:

                    view access to specific people: {'access_scope': 'users','access_type': 'view','emails': ['email1@test.com', 'email2@test.com', 'email3@externaltest.com']}

                    view access to whole orgnization: {'access_scope': 'organization','access_type': 'view'}

                    edit access to whole orginzation: {'access_scope': 'organization','access_type': 'edit'}

            Returns:
                as a string the email-able share link

            Raises:
                APIException: In the event we get any response of >= 400
        """
        file_id = self.get_file_id(file_path=file_path)
        access_scope = validate_attribute_allowed_list(value=file_permissions.get('access_scope'), allowed_list=['users', 'organization'], raise_exception=True, hint='create_upload_link_from_path acces_scope ')
        access_type = validate_attribute_allowed_list(value=file_permissions.get('access_type'), allowed_list=['view', 'edit'], raise_exception=True, hint='create_upload_link_from_path access_type ')
        access_emails = file_permissions.get('emails', [])
        retainInheritedPermissions = True # This is default, kept for completeness. If this is set to False, existing permissions are removed.

        if len(access_emails) == 0 and access_scope == 'users':
            self.logger.warning('Warning, Creating an upload link that is restricted to individual users but no users were given.')

        if file_id is None:
            raise APIException(f'The file {file_path} does not exist.')
        
        """
        Add emails to invite link (if applicable)
        """
        full_url = f"{self.base_url}/sites/{self.sharepoint_site_id}/drive/items/{file_id}/createLink"

        headers = {
            'Authorization' : f'Bearer {self.authorization_token}',
            'Content-Type': 'application/json'
        }

        request_body = {
            'type': access_type,
            'scope': access_scope,
            "retainInheritedPermissions": retainInheritedPermissions
        }

        rq_share_link = requests.post(url=full_url, headers=headers, data=json.dumps(request_body), timeout=60)

        self.logger.debug(f"Got {rq_share_link.status_code} when creating an upload link for {file_path}")

        if rq_share_link.status_code not in [200, 201]:
            raise APIException(f'We got code {rq_share_link.status_code} when attempting to create an upload link. Exception was: {rq_share_link.text}', extra_data=rq_share_link.text)
        
        rq_share_link_data = json.loads(rq_share_link.text)
        share_link_id = rq_share_link_data.get('shareId')
        share_url = rq_share_link_data.get('link').get('webUrl')

        self.logger.debug(f'Got sharing link ID! {share_link_id}')
        self.logger.info(f'Created share link {share_url}')

        """
        Add people to share link we just created.
        """
        if len(access_emails) > 0:
            self.logger.debug(f'Attempting to add {access_emails} to share link ID {share_link_id}')
            # What is this? there is a view or edit permission on the link, but then individual people i guess can have write access.
            #  We are going to map directly on what the link says.
            link_access_type = {'view': 'read', 'edit': 'write'}.get(access_type)
            grant_url: str = f"{self.base_url}/shares/{share_link_id}/permission/grant"

            headers = headers # This specifically is to show we are carrying the headers from above forward.

            grant_request_body = {
                'roles': [link_access_type],
                'recipients': [
                    {'email': email } for email in access_emails
                ]
            }
            
            rq_invite_link = requests.post(url=grant_url, headers=headers, data=json.dumps(grant_request_body), timeout=60)
            
            if rq_invite_link.status_code != 200:
                raise APIException(f'Got {rq_invite_link.status_code} when attempting to add people to share link. extra data is {rq_invite_link.text}', extra_data=rq_invite_link.text)

        return share_url