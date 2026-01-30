from resonitelink.json import MISSING, json_model, json_list
from typing import List

from .member import Member

@json_model("list", Member)
class SyncList(Member):
    elements : List[Member] = json_list("elements", Member, default=MISSING)
