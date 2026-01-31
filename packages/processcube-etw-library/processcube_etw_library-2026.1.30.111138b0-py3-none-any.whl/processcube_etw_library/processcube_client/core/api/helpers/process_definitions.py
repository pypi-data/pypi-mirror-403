from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from enum import IntFlag
from typing import Callable

from ..base_client import BaseClient


class StartCallbackType(IntFlag):
    CallbackOnProcessInstanceCreated = 1
    CallbackOnProcessInstanceFinished = 2
    CallbackOnEndEventReached = 3


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ProcessDefinitionUploadPayload:
    xml: str
    overwrite_existing: bool = False


class ProcessDefinitionHandler(BaseClient):
    def __init__(self, url: str, identity: Callable = None, api_version: str = "v1"):
        super(ProcessDefinitionHandler, self).__init__(url, identity, api_version)

    def upload(
        self, request: ProcessDefinitionUploadPayload, options: dict = {}
    ) -> None:
        path = "process_definitions"

        payload = request.to_dict()

        self.do_post(path, payload, options)

    def delete(
        self,
        process_definition_id: str,
        delete_all_related_data: bool = False,
        options: dict = {},
    ) -> None:
        path = f"process_definitions/{process_definition_id}"

        if delete_all_related_data:
            path = f"{path}?delete_all_related_data=true"

        self.do_delete(path, options)
