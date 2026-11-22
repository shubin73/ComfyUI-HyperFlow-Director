"""The native loop graph for HyperFlow H3 Flash: euler, CFG 1 (BasicGuider), the checkpoint's own few-step sigmas, no Turbo LoRA.

Adapted from ComfyUI-MiniMaxH3-Director (GPL-3.0), ng/adapters/render_graph.py."""
import json

from comfy_execution.graph_utils import GraphBuilder
from comfy_execution.validation import validate_loops

# Everything in the render settings that changes the sampled latent.
RESUME_SETTINGS = ("seed", "steps", "sampler_name", "ref_image_size", "resize_method")


def render_sequence(inputs, settings):
    graph = GraphBuilder()
    start = graph.node("StartLoop", "start", mode="List", **{"mode.list": inputs["chunks"]}, cache_iterations=False)
    conditioning = graph.node("HFDChunkConditioning", "conditioning", chunk=start.out(3), previous=start.out(4),
                              clip=inputs["clip"], vae=inputs["vae"], audio_vae=inputs["audio_vae"],
                              ref_image_size=settings.get("ref_image_size", "match"), resize_method=settings.get("resize_method", "crop"),
                              # Flash's sigmas already carry the video shift (see HFDChunkSampling); a second shift would distort them
                              apply_sigma_shift=False)
    for name in ("model_fl2va", "model_ref2va"):
        if inputs.get(name) is not None:
            conditioning.set_input(name, inputs[name])
    model = conditioning.out(0)
    noise = graph.node("HFDChunkNoise", "noise", chunk=start.out(3), seed=settings["seed"])
    sampled_with = json.dumps({key: settings.get(key) for key in RESUME_SETTINGS}, sort_keys=True)
    sampling = graph.node("HFDChunkSampling", "sampling", chunk=start.out(3), model=model, settings=sampled_with)
    guider = graph.node("BasicGuider", "guider", model=model, conditioning=conditioning.out(1))   # no CFG: Flash is trained at CFG 1
    sample = graph.node("SamplerCustomAdvanced", "sample", noise=noise.out(0), guider=guider.out(0),
                        sampler=sampling.out(0), sigmas=sampling.out(1), latent_image=conditioning.out(2))
    part = sample.out(0)
    if settings.get("resume", True):
        # a finished part is kept on disk and reused after a crash (adapters/resume.py)
        part = graph.node("HFDResumeChunk", "resume", chunk=start.out(3), sampled=part, settings=sampled_with).out(0)
    # pictures of this part that later shots take their place from (core/places.py); a pass-through for every other part
    part = graph.node("HFDPlaceStill", "place", chunk=start.out(3), sampled=part, vae=inputs["vae"], models=settings.get("models", "")).out(0)
    end = graph.node("EndLoop", "end", output_value=part, next_iteration_value=part, accumulate=True)
    collect = graph.node("HFDCollect", "collect", latents=end.out(0), chunks=inputs["chunks"],
                         vae=inputs["vae"], audio_vae=inputs["audio_vae"])
    if settings.get("resume", True) and settings.get("resume_delete_done", True):
        collect.set_input("resume_settings", sampled_with)
    video = graph.node("CreateVideo", "video", images=collect.out(0), audio=collect.out(1), fps=24.0)
    expanded = graph.finalize()
    # Expanded graphs do not pass through the top-level loop validator again.
    validate_loops(expanded, [video.id, collect.id], expanded.keys(), [start.id], [end.id])
    return expanded, (video.out(0), collect.out(0), collect.out(1), collect.out(2))
