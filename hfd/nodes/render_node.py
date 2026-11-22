"""User-facing model ports and one render connection for HyperFlow H3 Flash; the native graph does the work.

Adapted from ComfyUI-MiniMaxH3-Director (GPL-3.0), ng/nodes/render_node.py."""
import json
import logging

from comfy_api.latest import io
from comfy_extras.nodes_custom_sampler import KSamplerSelect, RandomNoise

from ..adapters import model_files, places, resume
from ..adapters.render_graph import render_sequence
from ..core import flash
from .chunk_node import _decode_video
from .context_nodes import CATEGORY
from .director_node import HFDChunk


def model_inputs():
    return [io.Clip.Input("clip", raw_link=True, lazy=True), io.Vae.Input("vae", raw_link=True, lazy=True, display_name="video_vae"),
            io.Vae.Input("audio_vae", raw_link=True, lazy=True),
            io.Model.Input("model_fl2va", raw_link=True, lazy=True, optional=True,
                           tooltip="HyperFlow Loader with a minimax_h3_fl2va_hyperflow_flash_* checkpoint (text / first-last frames)."),
            io.Model.Input("model_ref2va", raw_link=True, lazy=True, optional=True,
                           tooltip="HyperFlow Loader with a minimax_h3_ref2va_hyperflow_flash_* checkpoint (reference pictures).")]


def sampling_inputs():
    return [io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff, control_after_generate=True),
            io.Combo.Input("steps", options=[str(n) for n in flash.STEPS], default=str(flash.DEFAULT_STEPS),
                           tooltip="4 = speed, 6 = balanced (default), 8 = quality. Sampler is euler at CFG 1, as the model was trained."),
            io.Boolean.Input("resume", default=True, advanced=True,
                             tooltip="Keep each finished part on disk and reuse it when the same plan is queued again. "
                                     "Switch off after changing the checkpoint: the key does not include the model file.")]


def render_outputs():
    return [io.Video.Output(display_name="video"), io.Image.Output(display_name="images"),
            io.Audio.Output(display_name="audio"), io.String.Output(display_name="render_warnings")]


def split_render_inputs(values):
    names = ("chunks", "clip", "vae", "audio_vae", "model_fl2va", "model_ref2va")
    inputs = {name: values[name] for name in names if name in values}
    if not any(inputs.get(name) for name in ("model_fl2va", "model_ref2va")):
        raise ValueError("Connect a HyperFlow Flash model to model_fl2va (text/frames) or model_ref2va (references).")
    settings = {"seed": values["seed"], "steps": int(values["steps"]), "sampler_name": flash.SAMPLER,
                "resume": bool(values.get("resume", True))}
    return inputs, settings


class HFDRenderSequence(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDRenderSequence", display_name="HFD Chunk Sequence (Flash)", category=CATEGORY + "/Custom loop",
                         description="Connect the planner's chunks and HyperFlow H3 Flash models. Renders and joins the whole sequence with "
                                     "euler, CFG 1 and the model's 4/6/8-step schedule, using native sampling, progress and interrupt.",
                         inputs=[HFDChunk.Input("chunks", raw_link=True), *model_inputs(), *sampling_inputs()],
                         outputs=render_outputs(), enable_expand=True)

    @classmethod
    def execute(cls, **values):
        inputs, settings = split_render_inputs(values)
        expanded, outputs = render_sequence(inputs, settings)
        return io.NodeOutput(*outputs, expand=expanded)


class HFDChunkNoise(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDChunkNoise", display_name="HFD Chunk Noise", category=CATEGORY + "/Technical", is_dev_only=True,
                         inputs=[HFDChunk.Input("chunk"), io.Int.Input("seed", default=0, min=0, max=0xffffffffffffffff)],
                         outputs=[io.Noise.Output()])

    @classmethod
    def execute(cls, chunk, seed):
        job = chunk[0] if isinstance(chunk, list) else chunk
        return RandomNoise.execute(noise_seed=(int(seed) + job.index) % (1 << 64))


class HFDChunkSampling(io.ComfyNode):
    """Sampler and sigmas of one render part. HyperFlow Flash ships its schedule: 6 steps come from the checkpoint when it carries one
    (the loader keeps it on the diffusion model), 4 and 8 from the model card's grids; all with the video shift of 12 applied."""
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDChunkSampling", display_name="HFD Chunk Sampling", category=CATEGORY + "/Technical", is_dev_only=True,
                         inputs=[HFDChunk.Input("chunk"), io.Model.Input("model"), io.String.Input("settings")],
                         outputs=[io.Sampler.Output(), io.Sigmas.Output()])

    @classmethod
    def execute(cls, chunk, model, settings):
        import torch
        values = json.loads(settings)
        steps = int(values["steps"])
        sampler = KSamplerSelect.execute(sampler_name=flash.SAMPLER).args[0]
        embedded = getattr(model.model.diffusion_model, "hyperflow_sigmas", None) if steps == flash.DEFAULT_STEPS else None
        sigmas = embedded.clone().float().cpu() if embedded is not None else torch.tensor(flash.sigmas_for(steps), dtype=torch.float32)
        return io.NodeOutput(sampler, sigmas)


class HFDResumeChunk(io.ComfyNode):
    """A finished render part comes from disk when the same plan is queued again (adapters/resume.py); its sampler then
    does not run at all."""
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDResumeChunk", display_name="HFD Resume Chunk", category=CATEGORY + "/Technical", is_dev_only=True,
                         inputs=[HFDChunk.Input("chunk"), io.String.Input("settings"),
                                 io.Latent.Input("sampled", lazy=True, optional=True)],
                         outputs=[io.Latent.Output()])

    @classmethod
    def check_lazy_status(cls, chunk, settings, sampled=None):
        job = chunk[0] if isinstance(chunk, list) else chunk
        return [] if resume.has(resume.part_key(job, json.loads(settings))) else ["sampled"]

    @classmethod
    def execute(cls, chunk, settings, sampled=None):
        job = chunk[0] if isinstance(chunk, list) else chunk
        key = resume.part_key(job, json.loads(settings))
        if resume.has(key):
            logging.info("[HFD] render part %d comes from %s (resume)", job.index + 1, resume.folder())
            return io.NodeOutput(resume.load(key))
        resume.save(key, sampled)
        return io.NodeOutput(sampled)


class HFDPlaceStill(io.ComfyNode):
    """After a part is sampled: the pictures later shots take their place from ("Place like Shot 1", core/places.py)."""
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDPlaceStill", display_name="HFD Place Still", category=CATEGORY + "/Technical", is_dev_only=True,
                         inputs=[HFDChunk.Input("chunk"), io.Latent.Input("sampled"), io.Vae.Input("vae"),
                                 io.String.Input("models", default="", optional=True)],
                         outputs=[io.Latent.Output()])

    @classmethod
    def execute(cls, chunk, sampled, vae, models=""):
        job = chunk[0] if isinstance(chunk, list) else chunk
        for path, how in places.write(job, sampled, lambda video: _decode_video(vae, video), model_files.chosen(models)):
            logging.info("[HFD] render part %d: place picture %s (%s)", job.index + 1, path, how)
        return io.NodeOutput(sampled)


NODES = [HFDRenderSequence, HFDChunkNoise, HFDChunkSampling, HFDResumeChunk, HFDPlaceStill]
