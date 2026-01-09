import requests
from typing import Optional

from utils.logger import log, LogLevel


class BaseApiClient:
    def __init__(self, base_url: str, authorization_header: Optional[dict]) -> None:
        self.base_url = base_url
        self.authorization_header = authorization_header

    def log_error_response(self, response: requests.Response):
        if response.status_code == 400:
            log(f'400 Bad request calling {response.request.url}', LogLevel.ERROR)
        elif response.status_code == 401:
            log(f'401 Unauthorized {response.request.url}', LogLevel.ERROR)
        elif response.status_code == 403:
            log(f'403 Forbidden calling {response.request.url}', LogLevel.ERROR)
        elif response.status_code != 404 and response.status_code >= 400 and response.status_code < 500:
            log(f'Bad request: Got {response.status_code} calling {response.request.url}', LogLevel.ERROR)
        elif 500 <= response.status_code <600:
            log(f'Server internal error: got {response.status_code} calling {response.request.url}', LogLevel.ERROR)

    async def GET(self, url: str) -> requests.Response:
        response = requests.get(
            f'{self.base_url}/{url}',
            headers=self.authorization_header
        )
        self.log_error_response(response)
        return response

    async def DELETE(self, url: str) -> requests.Response:
        response = requests.delete(
            f'{self.base_url}/{url}',
            headers=self.authorization_header
        )
        self.log_error_response(response)
        return response

    async def PATCH(self, url: str, body: dict) -> requests.Response:
        response = requests.patch(
            f'{self.base_url}/{url}',
            headers=self.authorization_header,
            json=body
        )
        self.log_error_response(response)
        return response

    async def POST(self, url: str, body: dict) -> requests.Response:
        if body is None:
            response = requests.post(
                f'{self.base_url}/{url}',
                headers=self.authorization_header,
            )
        else:
            response = requests.post(
                f'{self.base_url}/{url}',
                headers=self.authorization_header,
                json=body
            )
        self.log_error_response(response)
        return response

    async def PUT(self, url: str, body: Optional[dict] = None) -> requests.Response:
        if body is None:
            response = requests.put(
                f'{self.base_url}/{url}',
                headers=self.authorization_header,
            )
        else:
            response = requests.put(
                f'{self.base_url}/{url}',
                headers=self.authorization_header,
                json=body
            )
        self.log_error_response(response)
        return response
