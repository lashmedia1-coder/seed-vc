---
Title: Add one-click portable starter and echo post-processing (start_portable + echo_control)
---

This branch adds a portable Windows starter and an optional echo-postprocessing flow to the Seed-VC fork.

What changed:
- start_portable.bat: creates/activates a virtual environment, installs requirements (if present), and launches the repository's realtime app. Use `start_portable.bat --echo` to enable automatic post-processing of final outputs.
- modules/echo_control.py: a best-effort offline echo-reduction utility that uses `noisereduce` when available, with a `librosa+scipy` fallback and a simple copy fallback.
- app_vc.py, app_vc_v2.py, app.py: added a helper `_save_and_postprocess` that writes final WAV outputs to `outputs/converted_<timestamp>.wav` and runs `modules.echo_control.process_file(...)` when `ECHO_CONTROL=true` to produce an echo-reduced file. Gradio outputs now yield the processed file path for the Full Output audio.
- requirements.txt: added `noisereduce` as an optional dependency for echo reduction.

Usage:
1. Double-click `start_portable.bat` (or run it from cmd). To enable echo post-processing, run `start_portable.bat --echo`.
2. If you run without `noisereduce` installed, the post-processor will fall back to a librosa+scipy method or copy the file unchanged.

Notes:
- This is offline post-processing (applied after output files are produced). It is not a real-time AEC solution for microphone loopback.
- The project is GPL-3.0 licensed and this change keeps that licensing.

Please review and let me know if you'd like a packaged installer (PyInstaller + NSIS) or real-time AEC integration as future work.
