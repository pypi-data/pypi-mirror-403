from resonitelink.json import MISSING, json_model, json_list
from typing import List

from .submesh import Submesh


@json_model("points", Submesh)
class PointSubmesh(Submesh):
    vertex_indices : List[int] = json_list("vertexIndices", int, default=MISSING)
