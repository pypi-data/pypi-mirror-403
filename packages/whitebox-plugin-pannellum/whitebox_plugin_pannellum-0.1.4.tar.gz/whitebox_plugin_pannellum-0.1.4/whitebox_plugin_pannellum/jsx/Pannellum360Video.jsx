import { useEffect, useRef } from "react";

/**
 * Wait for a video element to have a valid frame ready for rendering.
 * Uses requestVideoFrameCallback when available, falls back to dimension polling.
 *
 * @param {HTMLVideoElement} videoEl - The video element to monitor
 * @param {number} maxWaitMs - Maximum time to wait (default: 10000ms)
 * @returns {Promise<{width: number, height: number}>} - Resolves with video dimensions
 */
function waitForVideoFrame(videoEl, maxWaitMs = 10000) {
  return new Promise((resolve, reject) => {
    // Check if video already has valid dimensions and is playing
    if (videoEl.videoWidth > 0 && videoEl.videoHeight > 0 && !videoEl.paused) {
      resolve({ width: videoEl.videoWidth, height: videoEl.videoHeight });
      return;
    }

    const startTime = Date.now();
    let resolved = false;
    let timeoutId = null;

    // Event listeners for cleanup
    const eventListeners = [];

    const cleanup = () => {
      if (resolved) return;
      resolved = true;
      if (timeoutId) clearTimeout(timeoutId);
      // Remove all event listeners
      eventListeners.forEach(({ event, handler }) => {
        videoEl.removeEventListener(event, handler);
      });
    };

    const resolveWithDimensions = () => {
      if (resolved) return;
      cleanup();
      resolve({ width: videoEl.videoWidth, height: videoEl.videoHeight });
    };

    const rejectWithTimeout = () => {
      if (resolved) return;
      cleanup();
      reject(new Error("Timeout waiting for video frame"));
    };

    // Method 1: requestVideoFrameCallback (Chrome 83+, Firefox 130+)
    // Most reliable - fires exactly when a frame is ready to render
    if ("requestVideoFrameCallback" in videoEl) {
      const checkFrame = () => {
        if (resolved) return;

        if (videoEl.videoWidth > 0 && videoEl.videoHeight > 0) {
          resolveWithDimensions();
        } else if (Date.now() - startTime > maxWaitMs) {
          rejectWithTimeout();
        } else {
          videoEl.requestVideoFrameCallback(checkFrame);
        }
      };
      videoEl.requestVideoFrameCallback(checkFrame);
    } else {
      // Method 2: Dimension polling fallback (Safari, older browsers)
      const pollInterval = 100; // Check every 100ms

      const checkDimensions = () => {
        if (resolved) return;

        if (videoEl.videoWidth > 0 && videoEl.videoHeight > 0 && !videoEl.paused) {
          resolveWithDimensions();
        } else if (Date.now() - startTime > maxWaitMs) {
          rejectWithTimeout();
        } else {
          timeoutId = setTimeout(checkDimensions, pollInterval);
        }
      };

      // Also listen for video events as additional triggers
      const onVideoReady = () => {
        if (videoEl.videoWidth > 0 && videoEl.videoHeight > 0) {
          resolveWithDimensions();
        }
      };

      // Track listeners for cleanup
      ["loadeddata", "playing", "canplay"].forEach((event) => {
        eventListeners.push({ event, handler: onVideoReady });
        videoEl.addEventListener(event, onVideoReady);
      });

      checkDimensions();
    }
  });
}

const Pannellum360Video = (props) => {
  const videoRef = useRef(null);
  const playerRef = useRef(null);
  const pannellumInitialized = useRef(false);
  const cleanupRef = useRef(null);
  const viewerRef = useRef(null);
  const videoEventHandlersRef = useRef(null);
  const { options, onReady } = props;

  useEffect(() => {
    // Skip if already initialized
    if (playerRef.current) {
      const player = playerRef.current;
      player.autoplay(options.autoplay);
      player.src(options.sources);

      if (options.pannellum && player.pannellum) {
        player.pannellum(options.pannellum);
      }
      return;
    }

    // Clear any leftover elements from previous mount (React StrictMode)
    if (videoRef.current) {
      videoRef.current.innerHTML = "";
    }

    // Reset initialization flag
    pannellumInitialized.current = false;
    viewerRef.current = null;
    videoEventHandlersRef.current = null;

    const videoElement = document.createElement("video-js");
    const elementId = `panorama-${Date.now()}`;

    videoElement.id = elementId;
    videoElement.classList.add("vjs-big-play-centered");
    videoElement.classList.add("vjs-fill");
    videoElement.setAttribute("crossorigin", "anonymous");
    videoRef.current.appendChild(videoElement);

    const player = (playerRef.current = window.videojs(
      elementId,
      options,
      () => {
        const pannellumConfig = {
          default: {
            type: "equirectangular",
            autoLoad: true,
            ...options.pannellum,
          },
        };

        const playerEl = player.el();

        // Call onReady immediately (before Pannellum init)
        onReady?.(player);

        // Initialize Pannellum once video is ready
        const initPannellum = (videoEl) => {
          // Guard: Check if player was disposed or already initialized
          if (!playerRef.current || player.isDisposed() || pannellumInitialized.current) {
            return;
          }
          pannellumInitialized.current = true;

          // Check if this is a WebRTC source (uses srcObject instead of src)
          const isWebRTC = !!videoEl?.srcObject;

          if (isWebRTC) {
            // For WebRTC, initialize Pannellum directly on the video element
            // The videojs-pannellum plugin doesn't handle srcObject properly
            const pnlmDiv = document.createElement("div");
            pnlmDiv.id = `pnlm-${Date.now()}`;
            pnlmDiv.style.width = "100%";
            pnlmDiv.style.height = "100%";
            pnlmDiv.style.position = "absolute";
            pnlmDiv.style.top = "0";
            pnlmDiv.style.left = "0";
            pnlmDiv.style.zIndex = "1";
            playerEl.appendChild(pnlmDiv);

            // Ensure Video.js control bar is above Pannellum and can receive clicks
            const controlBar = playerEl.querySelector(".vjs-control-bar");
            if (controlBar) {
              controlBar.style.zIndex = "2";
              controlBar.style.pointerEvents = "auto";
            }

            try {
              const viewer = window.pannellum.viewer(pnlmDiv.id, {
                type: "equirectangular",
                panorama: videoEl,
                dynamic: true,
                autoLoad: true,
                showZoomCtrl: false,
                showFullscreenCtrl: false,
                ...options.pannellum,
              });

              // Store viewer reference for cleanup
              viewerRef.current = viewer;
              player.pannellumViewer = viewer;

              // Start updating when video plays
              const updatePannellum = () => {
                if (viewer && !videoEl.paused) {
                  viewer.setUpdate(true);
                }
              };

              // Store handlers for cleanup
              videoEventHandlersRef.current = {
                videoEl,
                handlers: [
                  { event: "play", handler: updatePannellum },
                  { event: "playing", handler: updatePannellum },
                ],
              };

              videoEl.addEventListener("play", updatePannellum);
              videoEl.addEventListener("playing", updatePannellum);
              updatePannellum(); // Start immediately if already playing

              // Handle fullscreen changes - resize Pannellum viewer
              const handleFullscreenChange = () => {
                if (viewer) {
                  // Give browser time to complete fullscreen transition
                  setTimeout(() => {
                    window.dispatchEvent(new Event("resize"));
                  }, 100);
                }
              };
              player.on("fullscreenchange", handleFullscreenChange);
              videoEventHandlersRef.current.handlers.push({
                event: "fullscreenchange",
                handler: handleFullscreenChange,
                isPlayerEvent: true,
              });
            } catch (err) {
              console.error("[Pannellum] WebRTC init error:", err);
            }
          } else {
            // For regular video sources, use the videojs-pannellum plugin
            try {
              player.pannellum(pannellumConfig);
            } catch (err) {
              console.error("[Pannellum] Plugin init error:", err);
              return;
            }

            const pnlmContainer = playerEl.querySelector(".pnlm-container");
            if (pnlmContainer) {
              pnlmContainer.style.width = "100%";
              pnlmContainer.style.height = "100%";
              pnlmContainer.style.position = "absolute";
              pnlmContainer.style.top = "0";
              pnlmContainer.style.left = "0";
              window.dispatchEvent(new Event("resize"));
            }
          }

          // Hide Video.js text track display overlay
          // This overlay blocks interaction with the Pannellum canvas underneath
          const textTrackDisplay = playerEl.querySelector(".vjs-text-track-display");
          if (textTrackDisplay) {
            textTrackDisplay.style.display = "none";
          }
        };

        // Wait for video to be ready, then initialize Pannellum
        const videoEl = playerEl.querySelector("video");
        if (videoEl) {
          // Store cleanup function to cancel pending frame detection
          let cancelled = false;
          cleanupRef.current = () => {
            cancelled = true;
          };

          waitForVideoFrame(videoEl)
            .then(() => {
              if (!cancelled) {
                initPannellum(videoEl);
              }
            })
            .catch((err) => {
              console.error("[Pannellum] Frame detection failed:", err);
              // Fallback: try to init anyway if we have dimensions
              if (!cancelled && videoEl.videoWidth > 0 && videoEl.videoHeight > 0) {
                initPannellum(videoEl);
              }
            });
        }
      }
    ));

    // Cleanup function
    // Guards handle: StrictMode double-mount, early unmount during async init, init failures
    return () => {
      // Cancel pending frame detection
      if (cleanupRef.current) {
        cleanupRef.current();
        cleanupRef.current = null;
      }

      // Remove video element and player event listeners
      if (videoEventHandlersRef.current) {
        const { videoEl, handlers } = videoEventHandlersRef.current;
        handlers.forEach(({ event, handler, isPlayerEvent }) => {
          if (isPlayerEvent && playerRef.current && !playerRef.current.isDisposed()) {
            playerRef.current.off(event, handler);
          } else if (!isPlayerEvent) {
            videoEl.removeEventListener(event, handler);
          }
        });
        videoEventHandlersRef.current = null;
      }

      // Destroy Pannellum viewer
      if (viewerRef.current) {
        try {
          viewerRef.current.destroy();
        } catch (e) {
          // Ignore errors during cleanup
        }
        viewerRef.current = null;
      }

      // Dispose player
      if (playerRef.current && !playerRef.current.isDisposed()) {
        playerRef.current.dispose();
      }
      playerRef.current = null;
      pannellumInitialized.current = false;
    };
  }, [options, onReady]);

  return (
    <div data-vjs-player className="w-full h-full" ref={videoRef}></div>
  );
};

export { Pannellum360Video };
export default Pannellum360Video;
