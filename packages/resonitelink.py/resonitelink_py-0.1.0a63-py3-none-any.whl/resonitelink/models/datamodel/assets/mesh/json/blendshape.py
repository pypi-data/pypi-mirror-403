from .blendshape_frame import BlendshapeFrame
from resonitelink.json import MISSING, json_model, json_element, json_list
from typing import List


@json_model()
class Blendshape():
    # Name of the Blendshape.
    name : str = json_element("name", str, default=MISSING)

    # Frames that compose this blendshape.
    # Blendshapes need at least 1 frame.
    frames : List[BlendshapeFrame] = json_list("frames", BlendshapeFrame, default=MISSING)
