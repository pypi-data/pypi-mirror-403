from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from typing import Callable

from ..base_client import BaseClient


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ApplicationInfo:
    id: str
    name: str
    package_name: str
    version: str
    authority_url: str
    allow_anonymous_root_access: str
    extra_info: dict


class ApplicationInfoHandler(BaseClient):
    def __init__(self, url: str, identity: Callable = None, api_version: str = "v1"):
        super(ApplicationInfoHandler, self).__init__(url, identity, api_version)

    def info(self) -> ApplicationInfo:
        json_data = self.do_get("info")

        info = ApplicationInfo.from_dict(json_data)

        return info

    def authority(self) -> str:
        json_data = self.do_get("authority")

        return json_data
