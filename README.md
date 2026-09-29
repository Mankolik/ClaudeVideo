# Reddit in 30 seconds

A 30s, 1080p/30fps motion-graphics explainer about Reddit, built as a deterministic canvas animation.

- `index.html` – the whole animation; `window.draw(t)` paints any frame (open it in a browser to preview live)
- `render.js` – steps through the timeline with Playwright and saves frames (`node render.js <dir> 30 4`)
- `make_audio.py` – synthesizes the soundtrack (numpy only) → `audio.wav`
- `reddit-motion-graphics.mp4` – final render

Encode: `ffmpeg -framerate 30 -i frames/f_%04d.jpg -i audio.wav -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -shortest out.mp4`
