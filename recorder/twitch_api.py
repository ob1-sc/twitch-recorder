import requests
from requests.exceptions import HTTPError

class TwitchApi:

    """
    TwitchApi class
    """

    def __init__(self, client_id, client_secret):

        try:

            self.client_id = client_id
            self.client_secret = client_secret

            request_params = {
                "client_id" : self.client_id,
                "client_secret" : self.client_secret,
                "grant_type" : "client_credentials"
            }

            response = requests.post("https://id.twitch.tv/oauth2/token", params=request_params)
            response.raise_for_status()

            self.bearer_token = response.json().get("access_token")
            print(f'Access Token succesfully granted: {self.bearer_token}')

        except HTTPError as http_err:
            print(f'HTTP Error occured: {http_err}')

    def get(self, url, request_params = {}, request_headers = {}):

        try:

            # add auth headers            
            request_headers.update(
                {
                    "Authorization" : "Bearer " + self.bearer_token,
                    "Client-ID" : self.client_id
                }
            )

            response = requests.get(url, params=request_params, headers=request_headers)
            response.raise_for_status()

            return response

        except HTTPError as http_err:
            print(f'HTTP Error occured: {http_err}')