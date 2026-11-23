# EPTC 2026 Opening Countdown Video

`EPTC_2026_Opening_Countdown_Video.mp4`: 28 s, 1024×576, 30 fps, H.264 + AAC stereo.

Timeline: flyover → "ARE YOU READY?" (1–5.7 s) → countdown 5…1 (6–16 s, one bar each)
→ logo + conference details (16–28 s, final chord at 24 s).

Everything (visuals and orchestral score) is generated procedurally by the scripts in `src/`.

## Rebuild

Needs Python 3 with numpy, scipy, pillow, plus ffmpeg. Fonts (OFL) come from npm:

```bash
cd opening_video/src && mkdir -p fonts && cd fonts && npm pack @fontsource/orbitron @fontsource/russo-one @fontsource/montserrat && for f in *.tgz; do tar xzf $f && mv package ${f%.tgz}; done && cp fontsource-russo-one-*/files/russo-one-latin-400-normal.woff russo.woff && cp fontsource-orbitron-*/files/orbitron-latin-900-normal.woff orbitron900.woff && cp fontsource-montserrat-*/files/montserrat-latin-500-normal.woff mont500.woff
```

```bash
cd opening_video/src && python3 music.py music_raw.wav && python3 eqmatch.py <reference_44k.wav> music_raw.wav music.wav
```

```bash
cd opening_video/src && python3 video.py render video_silent.mp4 && ffmpeg -i video_silent.mp4 -i music.wav -map 0:v -map 1:a -c:v libx264 -crf 21 -tune grain -pix_fmt yuv420p -c:a aac -b:a 192k -shortest out.mp4
```

`eqmatch.py` matches the score's tonal balance to a reference track (the EPTC 2025 video's audio was used); skip it to use the raw mix.
`python3 video.py frames 2.5 9 19.5` renders still test frames.
