"""Explicit AI output jobs, separate from the rendering graph."""
from comfy_api.latest import io

from ..adapters.ai_media import read_media
from ..adapters.native_ai import CONDITIONING_ONLY, conditioning_only, native_request, parse_result
from ..adapters.probe import file_stamp
from .provider_node import HFDAI
from .context_nodes import CATEGORY


class HFDAIRequest(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDAIRequest", display_name="HFD AI Request", category=CATEGORY + "/Technical", is_dev_only=True,
                         is_output_node=True, enable_expand=True,
                         inputs=[HFDAI.Input("ai_provider"), io.Combo.Input("action", options=["analyze", "direct", "write", "build", "storyboard"]),
                                 io.String.Input("request_json", default="{}")], outputs=[io.String.Output()])

    @classmethod
    def fingerprint_inputs(cls, ai_provider, action, request_json):
        return float("nan")  # every click is a new request; see HFDAIResult

    @classmethod
    def execute(cls, ai_provider, action, request_json):
        expanded, result = native_request(ai_provider, action, request_json)
        return io.NodeOutput(result, expand=expanded)


class HFDAICheckEncoder(io.ComfyNode):
    """Stops an AI job at once when the connected CLIP cannot generate text."""
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDAICheckEncoder", display_name="HFD AI Encoder Check", category=CATEGORY + "/Technical", is_dev_only=True,
                         inputs=[io.Clip.Input("clip")], outputs=[io.Clip.Output()])

    @classmethod
    def execute(cls, clip):
        if conditioning_only(clip):
            raise ValueError(CONDITIONING_ONLY)
        return io.NodeOutput(clip)


class HFDAIReadMedia(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDAIReadMedia", display_name="HFD AI Media", category=CATEGORY + "/Technical", is_dev_only=True,
                         inputs=[io.Combo.Input("media", options=["image", "video", "audio"]), io.String.Input("source")],
                         outputs=[io.Image.Output(), io.Audio.Output()])

    @classmethod
    def fingerprint_inputs(cls, media, source):
        return file_stamp(source)

    @classmethod
    def execute(cls, media, source):
        return io.NodeOutput(*read_media(media, source))


class HFDAIResult(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(node_id="HFDAIResult", display_name="HFD AI Suggestion", category=CATEGORY + "/Technical", is_dev_only=True,
                         is_output_node=True,
                         inputs=[io.String.Input("text", force_input=True), io.String.Input("action"), io.String.Input("request_json")],
                         outputs=[io.String.Output()])

    @classmethod
    def fingerprint_inputs(cls, text, action, request_json):
        # Asking again with the same card or prompt is a new request: from ComfyUI's cache this node would not run,
        # send no suggestion, and the Studio reported "finished without a suggestion". Generate Text may stay cached.
        return float("nan")

    @classmethod
    def execute(cls, text, action, request_json):
        return io.NodeOutput(text, ui={"ng_suggestion": [parse_result(text, action, request_json)]})


NODES = [HFDAIRequest, HFDAICheckEncoder, HFDAIReadMedia, HFDAIResult]
