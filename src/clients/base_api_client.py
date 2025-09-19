import requests
from typing import Optional

from utils.logger import log, LogLevel


class BaseApiClient:
    def __init__(self, base_url: str, authorization_header: Optional[dict]) -> None:
        self.base_url = base_url
        self.authorization_header = authorization_header

    def log_error_response(self, response: requests.Response):
        category = response.status_code // 100
        if category == 4:  # Bad request
            log(f'Bad request: got {response.status_code} calling {response.request.url}', LogLevel.ERROR)
        elif category == 5:
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
        response = requests.post(
            f'{self.base_url}/{url}',
            headers=self.authorization_header,
            json=body
        )
        self.log_error_response(response)
        return response
