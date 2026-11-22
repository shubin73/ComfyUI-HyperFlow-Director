"""Sampling constants of HyperFlow H3 Flash (Video Rebirth, hyperflow-h3-flash model card): euler, CFG 1, 4/6/8 steps.

The knots are the model card's unshifted grids; the video flow shift of 12 is applied here, as the HyperFlow node pack's
HyperFlow Sigmas node does, so the sampler gets the final sigmas and no shift is applied to the model."""
STEPS = (4, 6, 8)
DEFAULT_STEPS = 6
VIDEO_SHIFT = 12.0
SAMPLER = "euler"
RAW_SIGMAS = {
    4: (1.0, 0.681872, 0.205019, 0.036496, 0.0),
    6: (1.0, 0.825217, 0.471725, 0.147401, 0.049626, 0.015517, 0.0),
    8: (1.0, 0.931506, 0.839236, 0.703462, 0.5, 0.296538, 0.160764, 0.068494, 0.0),
}


def shifted(raw, shift=VIDEO_SHIFT):
    return [shift * s / (1 + (shift - 1) * s) for s in raw]


def sigmas_for(steps):
    if int(steps) not in RAW_SIGMAS:
        raise ValueError("HyperFlow Flash samples %s steps, got %s" % (list(STEPS), steps))
    return shifted(RAW_SIGMAS[int(steps)])
