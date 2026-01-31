import os
import json
import argparse

from utilita.net.microsofthelper import auth

def cli():
    """This CLI is specifically for initalizing and authenticating to the Microsoft Graph API. (via the bi.integration application.)
    You should only realistically need to do this once.
    """
    # note, 
    p = argparse.ArgumentParser(description = "Authenticate to the bi.integration application at eataly. This realistically should only need to be done once.", formatter_class=argparse.RawTextHelpFormatter)

    # Define arguments
    p.add_argument("-db_path", type=str, help="Specify the DB Path (Default directory is %userprofile%\AppData\Local\MicrosoftHelper\mshelper.db)")
    p.add_argument("-scopes", type=str, help="Specify permission scopes for this login session (see application_defaults.json for defaults) Must be in comma separated format eg: -scopes user.read,user.write,user.all")
    p.add_argument("-log_level", type=str, help="Specify log level. Uses standard python logging level names.")
    p.add_argument("-application_json", type=str, help="If you have an application_defaults.json file, specify it here.")

    args = p.parse_args()

    if args.application_json is not None:
        application_defaults_path = args.application_json
    else:
        application_defaults_path = 'application_defaults.json'

    with open(application_defaults_path, 'r') as f:
        APPLICATION_DEFAULTS = json.loads(f.read())

    scopes = args.scopes.split(',') if args.scopes is not None else APPLICATION_DEFAULTS.get('default_scopes')
    application_settings = APPLICATION_DEFAULTS.get('application_settings')
    db_path = args.db_path # library takes default if db_path is none.
    log_level = args.log_level.upper() if type(args.log_level) == str else None

    session = auth.Authenticate(db_path=db_path, application_settings=application_settings, log_level=log_level)

    session.login(request_scopes=scopes)


if __name__ == '__main__':
    cli()
