from base64 import b64encode
from datetime import datetime
import json
from typing import Any

from hotglue_singer_sdk.target_sdk.client import HotglueSink


class PicqerSink(HotglueSink):
    api_version = "v1"

    @property
    def base_url(self) -> str:
        org = self.config.get("org")
        base_url = f"https://{org}.picqer.com/api/{self.api_version}/"
        return base_url

    def auth_header(self):
        user = self.config.get("api_key")
        passwd = None
        token = b64encode(f"{user}:{passwd}".encode()).decode()
        return f"Basic {token}"

    @property
    def http_headers(self):
        headers = {"Authorization": self.auth_header()}
        headers["User-Agent"] = "MyPicqerClient (picqer.com/api - support@picqer.com)"
        return headers

    def validate_input(self, record: dict):
        return record

    def parse_json(self, input):
        # if it's a string, use json.loads, else return whatever it is
        if isinstance(input, str):
            return json.loads(input)
        return input

    def convert_datetime(self, date: Any):
        # convert datetime.datetime into str
        if isinstance(date, datetime):
            # This is the format -> "2022-08-15T19:16:35Z"
            return date.strftime("%Y-%m-%dT%H:%M:%SZ")
        return date
