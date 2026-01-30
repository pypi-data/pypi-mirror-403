from resonitelink.json import json_model

from ...messages import Message


@json_model("requestSessionData", Message)
class RequestSessionData(Message):
    pass