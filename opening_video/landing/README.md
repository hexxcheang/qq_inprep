# EPTC 2026 Landing Scene (follows the countdown video)

Current version (v2, 34.5 s: ends on a 20 s still of the landed ship at the MBS fountain), stored in Higgsfield:
https://d2ol7oe51mr4n9.cloudfront.net/user_3KVLcaaolY1ju8ahMbcysIiBVCz/eb46dd9a-ca0d-44fd-876c-aad97e6e25d0.mp4

v1 (14 s, ends on white): https://d2ol7oe51mr4n9.cloudfront.net/user_3KVLcaaolY1ju8ahMbcysIiBVCz/b8d32e08-17b1-4745-998c-490c31c4f7a1.mp4

| Time | Shot | Music |
|---|---|---|
| 0–4 s | Fade in from black; ship + humanoid approach Earth at sunrise | Space ambience, choir, strings build |
| 4–8 s | Atmospheric re-entry in orange fire, breaks through clouds to city lights | Hit at 4.0, taiko groove |
| 8–9.4 s | Ship descends over Marina Bay / Marina Bay Sands | Hit at 8.0, majestic brass + choir |
| 9.4–12.6 s | Lands on the fountain in front of MBS; mist erupts at 11.0 | Biggest hit at 11.0 |
| 12.6–13 s | Full white | D-major chord rings out |
| 13–14.5 s | White dissolves into the still of the landed ship at the MBS fountain (no robot; image job 7fbb5efc-86ad-4c2e-9d22-06bb13bd28f7) | Chord tail |
| 14.5–34.5 s | Still held for 20 s, then the video ends | Silence |

Built with Higgsfield: keyframes with GPT Image 2.6 (job 78583425-a37b-4fe5-9d87-f6d3a8498834 = design
reference; 17561afa…, 548a26df…, e3fc3495…, ef731be7… = shot start frames), clips with Kling 3.0 Pro
(5572396a…, a59c2095…, 7a37a19c…, 6daba15f…), then edited/graded with `assemble.sh` (v1) / `assemble_v2.sh` (v2) in the Higgsfield
sandbox. Music: `landing_music.wav` from `../src/landing_music.py` (same engine as the countdown score).
