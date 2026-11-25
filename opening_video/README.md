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

## Full opening (countdown + landing scene)

`EPTC_2026_Opening_Full_v2.mp4`: 62.5 s (28 s countdown, then the 34.5 s landing scene ending on a 20 s still of the ship at the MBS fountain), 1024×576, 30 fps, stored in Higgsfield:
https://d2ol7oe51mr4n9.cloudfront.net/user_3KVLcaaolY1ju8ahMbcysIiBVCz/0ec77d20-bfcb-4dab-8229-e1bb04e22fc9.mp4

v1 (42 s, ends on white): https://d2ol7oe51mr4n9.cloudfront.net/user_3KVLcaaolY1ju8ahMbcysIiBVCz/4a2951c9-e23d-4aac-a028-a783c4edbb04.mp4

Joined with:

```bash
ffmpeg -i EPTC_2026_Opening_Countdown_Video.mp4 -i EPTC_2026_Landing_Scene.mp4 -filter_complex "[0:v]setsar=1,fps=30,format=yuv420p[v0];[1:v]setsar=1,fps=30,format=yuv420p[v1];[0:a]aresample=44100,aformat=channel_layouts=stereo[a0];[1:a]aresample=44100,aformat=channel_layouts=stereo[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -preset slow -crf 21 -tune grain -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart EPTC_2026_Opening_Full.mp4
```
