import os
import dropbox
import json
import webbrowser
import base64
import requests
import pathlib


def open_url(app_key: str | None = None):
    url = f'https://www.dropbox.com/oauth2/authorize?client_id={app_key}&' \
          f'response_type=code&token_access_type=offline'
    webbrowser.open(url)


def refresh_token(app_key_var_name: str | None = None,
                  app_secret_var_name: str | None = None,
                  access_generated_code_var_name: str | None = None,
                  local_tokens_path: pathlib.Path | None = None,
                  refresh_token_var_name: str | None = None):
    app_key = get_env_variable(env_variable=app_key_var_name, local_tokens_path=local_tokens_path)
    app_secret = get_env_variable(env_variable=app_secret_var_name, local_tokens_path=local_tokens_path)
    access_generated_code = get_env_variable(env_variable=access_generated_code_var_name,
                                             local_tokens_path=local_tokens_path)
    refresh_token = get_env_variable(env_variable=refresh_token_var_name, local_tokens_path=local_tokens_path)
    dbx = None
    response = None
    if refresh_token is not None:
        try:
            dbx = dropbox.Dropbox(
                app_key=app_key,
                app_secret=app_secret,
                oauth2_refresh_token=refresh_token)
        except ValueError:
            pass
    if dbx is None:
        response = renew_access_key(app_key=app_key,
                                    app_secret=app_secret,
                                    access_generated_code=access_generated_code)
        dbx = dropbox.Dropbox(response['refresh_token'])
    return response, dbx


def renew_access_key(app_key: str | None = None,
                     app_secret: str | None = None,
                     access_generated_code: str | None = None
                     ):

    basic_auth = base64.b64encode(f'{app_key}:{app_secret}'.encode())

    headers = {
        'Authorization': f"Basic {basic_auth}",
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = f'code={access_generated_code}&grant_type=authorization_code'
    _response = requests.post('https://api.dropboxapi.com/oauth2/token',
                              data=data,
                              auth=(app_key, app_secret),
                              headers=headers)
    response = json.loads(_response.text)

    if 'error' in response.keys():
        open_url(app_key=app_key)
    _response = requests.post('https://api.dropboxapi.com/oauth2/token',
                              data=data,
                              auth=(app_key, app_secret))
    response = json.loads(_response.text)
    return response


def upload_file(input_file: str | None = None,
                remote_file: str | None = None,
                dbx: object | None = None
                ):
    if dbx is None:
        return
    dbx.users_get_current_account()

    for entry in dbx.files_list_folder('').entries:
        print(entry.name)

    with open(input_file):
        _f_bytes = open(input_file, mode="rb")
        data = _f_bytes.read()
        r = dbx.files_upload(data, remote_file, mode=dropbox.files.WriteMode.overwrite)

        try:
            settings = dropbox.sharing.SharedLinkSettings(
                requested_visibility=dropbox.sharing.RequestedVisibility.public,
                audience=dropbox.sharing.LinkAudience.public,
                access=dropbox.sharing.RequestedLinkAccessLevel.viewer,
                allow_download=True
            )
            shared_link_metadata = dbx.sharing_create_shared_link_with_settings(settings=settings,
                                                                                path=r.path_display)
            shared_link = shared_link_metadata.url
        except dropbox.exceptions.ApiError:
            existing_link = dbx.sharing_list_shared_links(path=r.path_display)
            shared_link = existing_link.links[0].url
    shared_file_name = pathlib.Path(input_file).name
    return shared_file_name, shared_link


def get_env_variable(env_variable: str | None = None, local_tokens_path: str | None = None):
    token = os.getenv(env_variable)
    if token is None:
        try:
            print('Could not find {:} in environment. Trying local path {:}'.format(env_variable, local_tokens_path))
            token = json.load(open(local_tokens_path))[env_variable]
        except FileNotFoundError as e:
            print(e.strerror, e.filename)
            token = None
    else:
        print('TOKEN found in $({:})'.format(env_variable))
    return token
