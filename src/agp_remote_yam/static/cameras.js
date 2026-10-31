/* Same source, tile order and crop geometry as the pinned public viewer.
 * Reference: codex-runner/static/hosted.js synchronizedPanels + video_stream.py.
 * Display video is independent of the agent's fresh JPEG/RGB-D captures.
 */
(function (root) {
  "use strict";
  const roles = ["observer", "top", "left", "right"];
  function crop(role, width, height, order) {
    if (width === 2560 && height === 1080) {
      return {observer:[0,0,1920,1080], left:[1920,0,640,360], top:[1920,360,640,360], right:[1920,720,640,360]}[role];
    }
    const index = order.indexOf(role);
    if (index < 0) return null;
    return [(index % 2) * width / 2, Math.floor(index / 2) * height / 2, width / 2, height / 2];
  }
  function start(config) {
    const video = document.getElementById("camera-video"), label = document.getElementById("camera-state");
    const play = document.getElementById("camera-play"), atlas = document.createElement("canvas");
    const context = atlas.getContext("2d", {alpha:false});
    const tiles = roles.map(role => ({role, canvas:document.getElementById("camera-" + role), loading:false, snapshotAt:0, requestedAt:-Infinity}));
    const stream = config.video_stream;
    let hls, timer, animation, stopped = false, frames = 0, lastTime = -1, lastPaint = -Infinity, lastAdvance = performance.now();
    let status = "Connecting to public camera stream";
    function draw(target, source, rect) {
      const [, , width, height] = rect;
      if (target.width !== width) target.width = width;
      if (target.height !== height) target.height = height;
      target.getContext("2d", {alpha:false}).drawImage(source, ...rect, 0, 0, width, height);
    }
    // Public snapshots also keep the arms current when the video publisher is
    // delayed. One request per view may be in flight, at most 2.5 fps. These
    // independent views are labelled as such; model captures stay separate.
    let snapshots = true;
    function snapshot(tile, now) {
      if (tile.loading || now-tile.requestedAt < 400) return;
      tile.loading=true;tile.requestedAt=now;
      const image = new Image();
      image.onload = () => {
        tile.loading=false;
        if (stopped || !snapshots) return;
        draw(tile.canvas,image,[0,0,image.naturalWidth,image.naturalHeight]);
        tile.snapshotAt=performance.now();lastAdvance=tile.snapshotAt;
        tile.canvas.dataset.frameSource=config.camera_source==="synthetic"?"synthetic":"api_snapshot";
        tile.canvas.dataset.presentedFrame=String(Number(tile.canvas.dataset.presentedFrame||0)+1);
      };
      image.onerror=()=>{tile.loading=false;};
      image.src="/api/cameras/"+tile.role+".jpg?robot_id="+encodeURIComponent(config.robot_id)+"&frame="+Date.now();
    }
    for(const tile of tiles)snapshot(tile,performance.now());
    if (config.camera_source === "synthetic") { label.textContent = "Synthetic camera fixtures · offline test"; return; }
    if (!stream) { label.textContent = "Public API snapshots · no video stream configured"; return; }
    function cleanup() {
      hls?.destroy(); hls = null;
      video.pause(); video.removeAttribute("src"); video.load();
    }
    function retry() {
      if (stopped || timer) return;
      status = "Camera stream reconnecting";
      timer = setTimeout(() => {timer = null; connect();}, 3000);
    }
    function connect() {
      if (stopped) return;
      cleanup(); lastAdvance = performance.now();
      status = "Connecting to public camera stream";
      const url = "/" + stream.path + "/index.m3u8";
      if (root.Hls?.isSupported()) {
        // Complete-segment playback with a short target on both HD feeds. No extra stream,
        // transcoder, independently refreshed camera or synthetic fallback.
        const hd = ["synchronized-hd", "robo-house"].includes(stream.path);
        hls = new root.Hls({enableWorker:false, lowLatencyMode:false, maxBufferLength:4,
          liveSyncMode:"buffered", backBufferLength:0, liveSyncDuration:hd ? .5 : 1,
          liveMaxLatencyDuration:hd ? 1 : 2, liveSyncOnStallIncrease:0, maxLiveSyncPlaybackRate:1.05});
        hls.on(root.Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {play.hidden = false;}));
        hls.on(root.Hls.Events.ERROR, (_, data) => {if (data.fatal) retry();});
        hls.loadSource(url); hls.attachMedia(video);
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = url; video.play().catch(() => {play.hidden = false;});
      } else { status = "This browser does not support the public video stream"; }
    }
    function paint(now) {
      if (stopped) return;
      const playingDate=hls?.playingDate;
      const lag=playingDate instanceof Date?(Date.now()-playingDate.getTime())/1000:null;
      snapshots=video.readyState<2 || (Number.isFinite(lag)&&lag>2);
      if(!document.hidden&&snapshots){
        for(const tile of tiles)snapshot(tile,now);
        const current=tiles.every(tile=>now-tile.snapshotAt<3000&&tile.snapshotAt>0);
        status=current?"Live camera snapshots · independent views":"Waiting for fresh public camera snapshots";
        video.dataset.publisherLagSeconds=Number.isFinite(lag)?lag.toFixed(2):"unknown";
      }
      if (!document.hidden && !snapshots && video.readyState >= 2 && video.currentTime !== lastTime && now - lastPaint >= 125) {
        const width = video.videoWidth, height = video.videoHeight;
        if (atlas.width !== width) atlas.width = width;
        if (atlas.height !== height) atlas.height = height;
        context.drawImage(video, 0, 0, width, height);
        frames++;
        for (const tile of tiles) {
          const rect = crop(tile.role, width, height, stream.cameras);
          if (!rect) continue;
          draw(tile.canvas, atlas, rect);
          tile.canvas.dataset.frameSource = "video";
          tile.canvas.dataset.presentedFrame = String(frames);
        }
        lastTime = video.currentTime; lastPaint = now; lastAdvance = performance.now();
        status = "Live public cameras · main observer, overhead, left and right";
        play.hidden = true;
      }
      if (performance.now() - lastAdvance > 20000) retry();
      label.textContent = snapshots ? status : frames ? status : "Connecting to public cameras";
      animation = requestAnimationFrame(paint);
    }
    play.onclick = () => video.play().catch(() => {status = "Press play to resume cameras";});
    function visible(){if(!document.hidden&&!stopped)connect();}
    function stop(){stopped=true;clearTimeout(timer);cancelAnimationFrame(animation);cleanup();video.removeEventListener("error",retry);document.removeEventListener("visibilitychange",visible);window.removeEventListener("pagehide",stop);}
    video.addEventListener("error",retry);
    document.addEventListener("visibilitychange",visible);
    window.addEventListener("pagehide",stop);
    connect();animation=requestAnimationFrame(paint);
    return stop;
  }
  root.AgPCameras = {start, crop};
  if (typeof module !== "undefined") module.exports = {crop};
})(typeof window !== "undefined" ? window : globalThis);
