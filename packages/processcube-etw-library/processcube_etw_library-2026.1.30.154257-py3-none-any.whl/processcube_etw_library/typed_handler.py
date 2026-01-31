import inspect
from typing import Callable, Any
from pydantic import BaseModel


def create_typed_handler_wrapper(handler: Callable) -> Callable[[dict], Any]:
    signature = inspect.signature(handler)
    params = signature.parameters

    if len(params) != 1:
        raise ValueError(
            f"Handler function must have exactly one parameter, got {len(params)}."
        )

    payload_parameter = next(iter(params.values()))
    if not issubclass(payload_parameter.annotation, BaseModel):
        raise ValueError(
            f"Handler parameter must be a subclass of BaseModel from pydantic, got {payload_parameter.annotation}."
        )

    ResultModel = signature.return_annotation
    if ResultModel is inspect.Signature.empty:
        raise ValueError("Handler function must have a return type annotation.")

    if not issubclass(ResultModel, BaseModel):
        raise ValueError(
            f"Handler return type must be a subclass of BaseModel from pydantic, got {ResultModel}."
        )

    PayloadModel = payload_parameter.annotation

    async def wrapper(raw_payload: dict) -> dict:
        parsed_payload = PayloadModel.model_validate(
            raw_payload, by_alias=False, by_name=True
        )
        result = handler(parsed_payload)
        if inspect.iscoroutine(result):
            result = await result

        if not isinstance(result, ResultModel):
            raise ValueError(
                f"Handler return value must be an instance of {ResultModel.__name__}, got {type(result).__name__}."
            )
        return result.model_dump(
            mode="json",
            by_alias=False,
        )

    return wrapper
