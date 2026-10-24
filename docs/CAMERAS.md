# Public camera parity

The viewer uses the same public Remote YAM sources and camera mapping as the
pinned public playground: main observer, overhead (`top`), left wrist and right
wrist. The observer is the main panel; the three auxiliary cameras remain visible.

`/api/cameras/{observer,top,left,right}.jpg` forwards the corresponding public
API JPEG unchanged. These real API stills cover stream startup only. Continuous
video uses the existing `synchronized-hd` stream through a read-only localhost
proxy to https://playground.blupe.io. No stream, camera or transcoder is created.

The existing public stream configuration is imported from the pinned
`remote_yam.video_stream`. Camera crops match `static/hosted.js`:
1280×720 uses the configured four-tile order; the 2560×1080 atlas preserves the
1920×1080 observer and three 640×360 auxiliary images. All panels crop one decoded
frame, retaining their source alignment. HLS.js and its license are served
unmodified from the pinned external dependency.

Robot execution and viewing are independent. `--demo` uses a scripted mock
robot but displays live public cameras. `--synthetic-cameras` explicitly selects
offline camera fixtures for tests. Real agent captures continue to use the
fresh API JPEG/RGB-D command surface; delayed display video is not model input.

References: `docs/refs/hls.js/API-1.7.2.md`, pinned
`codex-runner/local_playground.py`, `static/hosted.js` synchronizedPanels/camera,
and `src/remote_yam/video_stream.py`. No robot lease is needed for viewing.
