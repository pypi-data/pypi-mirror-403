from resonitelink.json import json_model

from ..member import Member


@json_model("empty", Member)
class EmptyElement(Member):
    pass
