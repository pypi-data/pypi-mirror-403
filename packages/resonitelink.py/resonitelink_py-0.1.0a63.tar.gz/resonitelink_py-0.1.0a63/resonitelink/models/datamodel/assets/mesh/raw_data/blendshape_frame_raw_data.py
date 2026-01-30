from resonitelink.json import MISSING, json_model, json_element


@json_model()
class BlendshapeFrameRawData():
    # Position of the frame within the blendshape animation
    # When blendshape has only a single frame, this should be set to 1.0
    # With multiple frames per blendshape, this determines the position at which this set of deltas is fully applied.
    position : float = json_element("position", float, default=MISSING)
