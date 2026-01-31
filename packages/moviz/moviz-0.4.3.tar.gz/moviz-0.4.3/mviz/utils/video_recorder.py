import json
import textwrap
import viser
from viser import _messages


class VideoRecordingManager:
    def __init__(self, server: viser.ViserServer, *, fps: int = 60, bitrate: int = 6_000_000) -> None:
        self.server = server
        self._target_fps = fps
        self._target_bitrate = bitrate
        self._state: str = "idle"
        self._bootstrap_script = self._build_bootstrap_script()
        self._toggle_button = self.server.gui.add_button("Start Recording", color=(0, 180, 0))
        self._stop_button = self.server.gui.add_button("Stop & Save", color=(210, 55, 55), visible=False)
        self._status = self.server.gui.add_text(
            "Recording Status",
            "Idle • Click start to capture the viser viewport only.",
        )
        self._toggle_button.on_click(self._handle_toggle)
        self._stop_button.on_click(lambda _: self._stop())
        self._install_frontend_script()

    def _install_frontend_script(self) -> None:
        def _send_to_client(client: viser.ClientHandle) -> None:
            client._websock_connection.queue_message(  # type: ignore[attr-defined]
                _messages.RunJavascriptMessage(source=self._bootstrap_script)
            )

        self.server._websock_server.queue_message(  # type: ignore[attr-defined]
            _messages.RunJavascriptMessage(source=self._bootstrap_script)
        )
        self.server.on_client_connect(_send_to_client)

    def _handle_toggle(self, _event) -> None:
        if self._state == "idle":
            self._start()
        elif self._state == "recording":
            self._pause()
        elif self._state == "paused":
            self._resume()

    def _start(self) -> None:
        payload = {
            "fps": self._target_fps,
            "bitrate": self._target_bitrate,
            "filenamePrefix": "mviz-recording",
        }
        self._send_command(f"window.__mvizRecorder && window.__mvizRecorder.start({json.dumps(payload)});")
        self._state = "recording"
        self._toggle_button.label = "Pause Recording"
        self._toggle_button.color = (230, 180, 0)
        self._stop_button.visible = True
        self._status.value = "Recording • Click pause or use “Stop & Save” to finish."

    def _pause(self) -> None:
        self._send_command("window.__mvizRecorder && window.__mvizRecorder.pause();")
        self._state = "paused"
        self._toggle_button.label = "Resume Recording"
        self._toggle_button.color = (0, 120, 230)
        self._status.value = "Paused • Resume or use “Stop & Save” to finish."

    def _resume(self) -> None:
        self._send_command("window.__mvizRecorder && window.__mvizRecorder.resume();")
        self._state = "recording"
        self._toggle_button.label = "Pause Recording"
        self._toggle_button.color = (230, 180, 0)
        self._status.value = "Recording • Click pause or use “Stop & Save” to finish."

    def _stop(self) -> None:
        self._send_command("window.__mvizRecorder && window.__mvizRecorder.stop();")
        self._state = "idle"
        self._toggle_button.label = "Start Recording"
        self._toggle_button.color = (0, 180, 0)
        self._stop_button.visible = False
        self._status.value = "Stopped • The file downloads via your browser."

    def _send_command(self, script: str) -> None:
        self.server._websock_server.queue_message(  # type: ignore[attr-defined]
            _messages.RunJavascriptMessage(source=script)
        )

    def _build_bootstrap_script(self) -> str:
        return textwrap.dedent(
            r"""
            (() => {
              const KEY = "__mvizRecorder";
              const MIME_CANDIDATES = [
                { mime: "video/mp4;codecs=avc1.42E01E", extension: ".mp4" },
                { mime: "video/mp4;codecs=h264", extension: ".mp4" },
                { mime: "video/mp4", extension: ".mp4" },
                { mime: "video/webm;codecs=vp9", extension: ".webm" },
                { mime: "video/webm;codecs=vp8", extension: ".webm" },
                { mime: "video/webm", extension: ".webm" },
              ];

              const existing = window[KEY];
              if (existing && typeof existing.cleanup === "function") {
                try { existing.cleanup(); } catch (err) { console.warn("[mviz-recorder] cleanup failed", err); }
              }

              const findCanvas = () => {
                const selectors = [
                  "canvas[data-engine]",
                  "#root canvas",
                  ".viser-app canvas",
                  "canvas"
                ];
                for (const selector of selectors) {
                  const canvas = document.querySelector(selector);
                  if (canvas instanceof HTMLCanvasElement && canvas.width > 0 && canvas.height > 0) {
                    return canvas;
                  }
                }
                return null;
              };

              const buildSupportedCandidates = () => {
                if (!window.MediaRecorder || typeof MediaRecorder.isTypeSupported !== "function") {
                  return [];
                }
                return MIME_CANDIDATES.filter((candidate) =>
                  MediaRecorder.isTypeSupported(candidate.mime)
                );
              };

              const safeStopRecorder = (recorder) => {
                if (!recorder) return;
                try { recorder.stop(); } catch (_) {}
              };

              const cleanupStream = () => {
                if (state.compositorCleanup) {
                  state.compositorCleanup();
                  state.compositorCleanup = null;
                }
                if (state.stream) {
                  state.stream.getTracks().forEach((track) => {
                    try { track.stop(); } catch (_) {}
                  });
                }
                state.stream = null;
              };

              const createCompositeStream = (sourceCanvas, fps) => {
                const compositor = document.createElement("canvas");
                compositor.width = sourceCanvas.width;
                compositor.height = sourceCanvas.height;
                const ctx = compositor.getContext("2d", { alpha: false });
                
                let active = true;
                
                const draw = () => {
                  if (!active) return;
                  
                  if (compositor.width !== sourceCanvas.width || compositor.height !== sourceCanvas.height) {
                    compositor.width = sourceCanvas.width;
                    compositor.height = sourceCanvas.height;
                  }
                  
                  // Fill white
                  ctx.fillStyle = "#ffffff";
                  ctx.fillRect(0, 0, compositor.width, compositor.height);
                  // Draw source
                  ctx.drawImage(sourceCanvas, 0, 0);
                  
                  requestAnimationFrame(draw);
                };
                
                draw();
                
                return {
                  stream: compositor.captureStream(fps),
                  cleanup: () => { active = false; }
                };
              };

              const state = {
                recorder: null,
                chunks: [],
                stream: null,
                compositorCleanup: null,
                status: "idle",
                mimeType: "",
                fileExtension: ".webm",
                filenamePrefix: "mviz-recording",
                candidates: [],
                activeCandidateIndex: -1,
                suppressNextSave: false,
              };

              const saveRecording = () => {
                if (!state.chunks.length) {
                  return;
                }
                const blob = new Blob(state.chunks, { type: state.mimeType || "video/webm" });
                const stamp = new Date().toISOString().replace(/[:.]/g, "-");
                const base = `${state.filenamePrefix}-${stamp}`;
                const extension =
                  typeof state.fileExtension === "string" && state.fileExtension.length > 0
                    ? state.fileExtension
                    : state.mimeType && state.mimeType.includes("mp4")
                      ? ".mp4"
                      : ".webm";

                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = `${base}${extension}`;
                link.style.display = "none";
                document.body.appendChild(link);
                link.click();
                window.setTimeout(() => {
                  URL.revokeObjectURL(link.href);
                  link.remove();
                }, 1000);
              };

              const attemptStartWithCandidate = (options, candidateIndex) => {
                const candidate = state.candidates[candidateIndex];
                if (!candidate) {
                  throw new Error("No supported MediaRecorder codecs (MP4/WebM) are available.");
                }
                const canvas = findCanvas();
                if (!canvas) {
                  throw new Error("Unable to locate the viser canvas.");
                }

                cleanupStream();
                state.chunks = [];
                state.suppressNextSave = false;

                // Create composite stream with white background
                const composite = createCompositeStream(canvas, options.fps || 60);
                state.stream = composite.stream;
                state.compositorCleanup = composite.cleanup;

                let recorder;
                try {
                  recorder = new MediaRecorder(state.stream, {
                    mimeType: candidate.mime,
                    videoBitsPerSecond: options.bitrate || 6_000_000,
                  });
                } catch (error) {
                  console.warn(`[mviz-recorder] Failed to init ${candidate.mime}, trying fallback`, error);
                  return attemptStartWithCandidate(options, candidateIndex + 1);
                }

                state.recorder = recorder;
                state.activeCandidateIndex = candidateIndex;
                state.mimeType = candidate.mime;
                state.fileExtension = candidate.extension;

                recorder.ondataavailable = (event) => {
                  if (event.data && event.data.size > 0) {
                    state.chunks.push(event.data);
                  }
                };

                recorder.onstop = () => {
                  if (!state.suppressNextSave) {
                    saveRecording();
                  }
                  state.chunks = [];
                  state.suppressNextSave = false;
                };

                recorder.onerror = (event) => {
                  const err = event?.error ?? event;
                  const name = err?.name || "";
                  const recoverable =
                    typeof name === "string" && name.toLowerCase().includes("encoding");
                  if (recoverable && candidateIndex + 1 < state.candidates.length) {
                    console.warn(`[mviz-recorder] ${candidate.mime} failed, trying fallback`, err);
                    api.lastError = err?.message || String(err);
                    state.suppressNextSave = true;
                    safeStopRecorder(recorder);
                    cleanupStream();
                    state.recorder = null;
                    state.status = "idle";
                    attemptStartWithCandidate(options, candidateIndex + 1);
                    return;
                  }

                  console.error("[mviz-recorder] MediaRecorder error", err);
                  api.lastError = err;
                  safeStopRecorder(recorder);
                  cleanupStream();
                  state.recorder = null;
                  state.status = "idle";
                };

                recorder.start();
                state.status = "recording";
                api.lastError = null;
              };

              const api = {
                getStatus: () => state.status,
                lastError: null,
                start: (options = {}) => {
                  try {
                    state.filenamePrefix = options.filenamePrefix || "mviz-recording";
                    state.candidates = buildSupportedCandidates();
                    if (!state.candidates.length) {
                      throw new Error("MediaRecorder MP4/WebM support is unavailable in this browser.");
                    }
                    attemptStartWithCandidate(options, 0);
                  } catch (error) {
                    console.error("[mviz-recorder] start failed", error);
                    api.lastError = error instanceof Error ? error.message : String(error);
                    state.status = "idle";
                    cleanupStream();
                  }
                },
                pause: () => {
                  if (state.recorder && state.status === "recording") {
                    state.recorder.pause();
                    state.status = "paused";
                  }
                },
                resume: () => {
                  if (state.recorder && state.status === "paused") {
                    state.recorder.resume();
                    state.status = "recording";
                  }
                },
                stop: () => {
                  if (state.recorder) {
                    safeStopRecorder(state.recorder);
                  }
                  cleanupStream();
                  state.recorder = null;
                  state.status = "idle";
                },
                cleanup: () => {
                  if (state.recorder && state.status !== "idle") {
                    safeStopRecorder(state.recorder);
                  }
                  cleanupStream();
                  state.recorder = null;
                  state.status = "idle";
                  state.chunks = [];
                  window[KEY] = undefined;
                }
              };

              window[KEY] = api;
            })();
            """
        )

