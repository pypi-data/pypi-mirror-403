# Whitebox Plugin - Pannellum

This is a plugin for [whitebox](https://gitlab.com/whitebox-aero) that provides Pannellum 360 video player integration.

## Installation

Install the plugin to whitebox:

```bash
poetry add whitebox-plugin-pannellum
```

## Features

### 360 Video Playback

The `Pannellum360Video` React component wraps Video.js with Pannellum for equirectangular 360-degree video rendering.

```jsx
import { Pannellum360Video } from 'whitebox-plugin-pannellum';

<Pannellum360Video
  options={{
    sources: [{ src: '/video.mp4', type: 'video/mp4' }],
    pannellum: {
      autoRotate: -2,
      hfov: 120,
    }
  }}
  onReady={(player) => console.log('Player ready')}
/>
```

### WebRTC Live Streaming Support

The component supports both regular video URLs and WebRTC streams (via `srcObject`):

| Source Type | Detection | Initialization |
|-------------|-----------|----------------|
| URL (`src`) | `!srcObject` | videojs-pannellum plugin |
| WebRTC (`srcObject`) | `!!srcObject` | Direct Pannellum init |

For WebRTC sources, the component:

1. Waits for video frames using `requestVideoFrameCallback` (with polling fallback)
2. Initializes Pannellum directly with the video element as a WebGL texture
3. Handles play/pause synchronization with the Pannellum viewer

See [whitebox-plugin-videojs README](https://gitlab.com/whitebox-aero/whitebox-plugin-videojs/-/blob/main/README.md) for the full WebRTC/WHEP architecture documentation.

### Frame Detection

The `waitForVideoFrame()` utility ensures Pannellum only initializes after actual video data is available:

```javascript
// Uses requestVideoFrameCallback when available (Chrome 83+, Firefox 130+)
// Falls back to polling videoWidth/videoHeight for Safari
await waitForVideoFrame(videoEl, maxWaitMs);
```

This prevents the "black sphere" issue common with WebRTC streams where metadata arrives before video frames.

## Additional Instructions

- [Plugin Development Guide](https://docs.whitebox.aero/plugin_guide/#plugin-development-workflow)
- [Plugin Testing Guide](https://docs.whitebox.aero/plugin_guide/#testing-plugins)
- [Contributing Guidelines](https://docs.whitebox.aero/development_guide/#contributing)
