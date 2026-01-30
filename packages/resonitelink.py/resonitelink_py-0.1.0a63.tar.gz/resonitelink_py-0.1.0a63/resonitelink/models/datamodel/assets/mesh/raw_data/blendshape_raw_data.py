from resonitelink.json import MISSING, json_model, json_element, json_list
from typing import List

from .blendshape_frame_raw_data import BlendshapeFrameRawData


@json_model()
class BlendshapeRawData():
    # Name of the blendshape.
    name : str = json_element("name", str, default=MISSING)

    # Indicates if this blenshape has normal datas.
    has_normal_deltas : bool = json_element("hasNormalDeltas", bool, default=MISSING)

    # Indicates if this blendshape has tangent deltas.
    has_tangent_deltas : bool = json_element("hasTangentDeltas", bool, default=MISSING)

    # Frames that compose this blendshape.
    # Blendshapes need at least 1 frame.
    frames : List[BlendshapeFrameRawData] = json_list("frames", BlendshapeFrameRawData, default=MISSING)
