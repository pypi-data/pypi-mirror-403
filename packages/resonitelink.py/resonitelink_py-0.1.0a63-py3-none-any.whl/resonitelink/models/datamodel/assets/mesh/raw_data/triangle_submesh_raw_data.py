from resonitelink.json import MISSING, json_model, json_element

from .submesh_raw_data import SubmeshRawData


@json_model("triangles", SubmeshRawData)
class TriangleSubmeshRawData(SubmeshRawData):
    triangle_count : int = json_element("triangleCount", int, default=MISSING)

    @property
    def indices_count(self) -> int:
        return self.triangle_count * 3
