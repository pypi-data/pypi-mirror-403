from resonitelink.json import MISSING, json_model, json_element, json_list
from typing import List

from ....datamodel.assets.mesh import Bone, SubmeshRawData, BlendshapeRawData
from ...messages import Message, BinaryPayloadMessage


@json_model("importMeshRawData", Message)
class ImportMeshRawData(BinaryPayloadMessage):
    # Number of vertices in this mesh.
    vertex_count : int = json_element("vertexCount", int, default=MISSING)
    
    # Do vertices have normals?
    has_normals : bool = json_element("hasNormals", bool, default=MISSING)
    
    # Do vertices have tangents?
    has_tangents : bool = json_element("hasTangents", bool, default=MISSING)
    
    # Do vertices have colors?
    has_colors : bool = json_element("hasColors", bool, default=MISSING)
    
    # How many bone weights does each vertex have.
    # If some vertices have fewer bone weights, use weight of 0 for remainder bindings.
    bone_weight_count : int = json_element("boneWeightCount", int, default=MISSING)
    
    # Configuration of UV channels for this mesh.
    # Each entry represents one UV channel of the mesh.
    # Number indicates number of UV dimensions. This must be between 2 and 4 (inclusive).
    uv_channel_dimensions : List[int] = json_list("uvChannelDimensions", int, default=MISSING)

    # Submeshes that form this mesh. Meshes will typically have at least one submesh.
    submeshes : List[SubmeshRawData] = json_list("submeshes", SubmeshRawData, default=MISSING)

    # Blendshapes of this mesh.
    # These allow modifying the vertex positions, normals & tangents for animations such as facial expressions.
    blendshapes : List[BlendshapeRawData] = json_list("blendshapes", BlendshapeRawData, default=MISSING)

    # Bones of the mesh when data represents a skinned mesh.
    # These will be referred to by their index from vertex data.
    bones : List[Bone] = json_list("bones", Bone, default=MISSING)
