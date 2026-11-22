# ComfyUI-HyperFlow-Director

Standalone nodes for long, multi-shot videos with **HyperFlow H3 Flash**: reference cards, a chunk planner and a chunk renderer.
Derived from [ComfyUI-MiniMaxH3-Director](https://github.com/seesee75-commits/ComfyUI-MiniMaxH3-Director) (GPL-3.0, see `NOTICE`).
Every node ID, type, route, folder and CSS class has its own name (`HFD…`, `/hfd/…`), so it installs next to the original and
workflows that use `NG…` nodes are not touched.

## Nodes (category *HyperFlow Director*)

| Node | Same job as |
|---|---|
| HFD Context Image / Video / Audio / Text | NG Context Image / … (the reference cards) |
| HFD Chunk Planner (`HFDDirector`) | NG Chunk Planner |
| HFD Chunk Sequence (Flash) (`HFDRenderSequence`) | NG Chunk Sequence, rewritten for Flash |
| HFD AI Loader (`HFDAIProvider`), HFD AI Request | the cards' optional AI analysis |
| HFD Chunk Conditioning / Collect / Collect Video / Noise / Sampling / Resume Chunk / Place Still | the loop internals |

Chunk Sequence renders with `euler`, CFG 1 (`BasicGuider`) and Flash's 4/6/8-step schedule (video shift 12 already applied;
no `MiniMaxH3SigmaShift`, no Turbo LoRA). Wire the model from **HyperFlow Loader**
(`minimax_h3_ref2va_hyperflow_flash_14b-…` into `model_ref2va`, the `fl2va` file into `model_fl2va`).

## Requirements

* ComfyUI 0.43.0 or newer (native H3 nodes).
* [ComfyUI-HyperFlow-Flash](https://github.com/Video-Rebirth/ComfyUI-HyperFlow-Flash) for **HyperFlow Loader** (the INT8/GGUF checkpoints need it).
* `pip install -r requirements.txt` (OpenCV).
* Text encoder and video/audio VAEs of MiniMax H3, as for any H3 workflow.

## Status

Not run inside ComfyUI yet. The ported unit tests of the pure-Python layers pass (`python3 -I tests/run_tests.py`; tests that need
ComfyUI, aiohttp or av are skipped or error without them). First things to check in ComfyUI: nodes load, a Context Image card
opens its editor, one short render matches the original at the same seed, then the 4/6/8 step settings.

Not carried over: Studio, Storyboard, Guide, Connector, Output, Preview, Control, Still, the Legacy Director and the Turbo LoRA path.
Resume parts are keyed on seed, steps and prompt, not on the model file; switch **resume** off after changing the checkpoint.

## License

GPL-3.0. Flash weights use the MiniMax H3 Community License, which excludes the EU, UK, South Korea and the US without MiniMax's authorization.
