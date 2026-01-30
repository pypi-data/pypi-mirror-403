from resonitelink.json import MISSING, json_model, json_element

from ..member import Member


@json_model("reference", Member)
class Reference(Member):
    target_id : str = json_element("targetId", str, default=MISSING)
    target_type : str = json_element("targetType", str, default=MISSING)
