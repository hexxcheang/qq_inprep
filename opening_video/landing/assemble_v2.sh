# Inputs: v1..v4.mp4 (Kling clips), landing_music.wav, s1.png (still, job 7fbb5efc-86ad-4c2e-9d22-06bb13bd28f7).
# Output: EPTC_2026_Landing_Scene_v2.mp4 (34.5 s): same as v1 up to the white-out, then the still fades in 13.0-14.5 s and holds 20 s.
set -e
G="eq=contrast=1.07:saturation=1.06:brightness=-0.015,colorbalance=rs=0.02:bs=-0.03:rh=0.04:gh=0.01:bh=-0.04,vignette=angle=PI/5"
T=34.5
ffmpeg -v error -y -i v1.mp4 -i v2.mp4 -i v3.mp4 -i v4.mp4 -i landing_music.wav -loop 1 -framerate 30 -t $T -i s1.png -filter_complex "
[0:v]trim=0.5:4.5,setpts=PTS-STARTPTS,fps=30,scale=2048:1152,zoompan=z='1+0.14*on/120':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1024x576:fps=30,setsar=1,$G,fade=t=in:st=0:d=0.8[a];
[1:v]trim=0.7:4.7,setpts=PTS-STARTPTS,fps=30,scale=1024:576,setsar=1,$G[b];
[2:v]trim=1.0:2.4,setpts=PTS-STARTPTS,fps=30,scale=2048:1152,zoompan=z='1+0.07*on/42':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1024x576:fps=30,setsar=1,$G[c];
[3:v]trim=1.65:5.04,setpts=PTS-STARTPTS,fps=30,scale=1024:576,setsar=1,$G[d];
[a][b][c][d]concat=n=4:v=1:a=0,tpad=stop_mode=clone:stop_duration=30,trim=0:$T,setpts=PTS-STARTPTS,format=rgba[base];
color=c=0xFFB878:s=1024x576:r=30:d=$T,format=rgba,fade=t=in:st=3.93:d=0.07:alpha=1,fade=t=out:st=4.0:d=0.4:alpha=1,colorchannelmixer=aa=0.85[f1];
color=c=0xFFC890:s=1024x576:r=30:d=$T,format=rgba,fade=t=in:st=7.94:d=0.06:alpha=1,fade=t=out:st=8.0:d=0.35:alpha=1,colorchannelmixer=aa=0.6[f2];
color=c=white:s=1024x576:r=30:d=$T,format=rgba,fade=t=in:st=11.8:d=0.8:alpha=1[wt];
[5:v]scale=1024:-2,crop=1024:576,setsar=1,$G,format=rgba,fade=t=in:st=13.0:d=1.5:alpha=1[st];
[base][f1]overlay=format=auto[o1];[o1][f2]overlay=format=auto[o2];[o2][wt]overlay=format=auto,noise=alls=5:allf=t+u[pre];
[pre][st]overlay=format=auto,format=yuv420p[v];
[4:a]apad[aud]" \
 -map "[v]" -map "[aud]" -c:v libx264 -preset slow -crf 20 -tune grain -r 30 -c:a aac -b:a 192k -t $T -movflags +faststart EPTC_2026_Landing_Scene_v2.mp4
