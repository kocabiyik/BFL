# Perseverance v2 — shot list (action cut)

v1 (`shots.md`, 8 shots) played as slow drifts with crossfades and no sound. v2 follows the 18 shots of the Blender breakdown in `clips.md` exactly (same order, timing and camera) and is cut for action. ~130 s.
Prompts live in `pipeline/shots_v2.py`.

What changes from v1:

- **Keyframes start mid-action**: low and ground-level angles, the flame already blazing, the chute already bursting.
- **Motion prompts in timed phases** with named camera moves (crash dive, whip pan, hero orbit, crane up) and "the motion never freezes".
- **Sound on** (`generate_audio: true`): each prompt names its sound (ignition roar, chute bang, rocket hiss, heartbeat). The rockets fade to silence before mission control.
- **Hard cuts inside a clip**, 0.4 s crossfades only between clips.
- **Camera shake in the cut** (`shake` 0–3 per shot): the frame is scaled up and the crop jitters, so no edges show.
- **Clip 4 HUD**: countdown 7:00 → 0:00 at touchdown, plus altitude and speed from the fact sheet.

| Clip | Shot | s | Action | Shake |
|---|---|---|---|---|
| 1 The Question | 1a_mars | 6 | push in on half-lit Mars | 0 |
| | 1b_dive | 8 | crash dive through dust to Jezero | 1 |
| | 1c_lake | 6 | ghost lake floods in, drains away | 0 |
| 2 Liftoff | 2a_pad | 5 | tilt up Atlas V, steam bursts | 0 |
| | 2b_ignition | 5 | ignition flash, smoke wall hits camera | 3 |
| | 2c_climb | 6 | whip pan, long-lens track of climb | 1 |
| | 2d_separation | 9 | fairing blasts apart, craft pushes free | 1 |
| 3 The Long Dark | 3a_path | 10 | arc races Earth → Mars | 0 |
| | 3b_thrusters | 7 | thruster bursts jolt the craft | 1 |
| | 3c_approach | 8 | Mars swells, cruise stage snaps off | 1 |
| 4 7 Minutes of Terror | 4a_entry | 8 | plasma, shield white hot, buffeting | 3 |
| | 4b_chute | 7 | chute snaps open, capsule jerked up | 3 |
| | 4c_shield | 6 | heat shield tumbles away, ground rushes up | 2 |
| | 4d_powered | 7 | stage drops free, 8 rockets ignite | 3 |
| | 4e_skycrane | 12 | rover lowered through dust, touch, stage roars off | 2 |
| 5 Touchdown Confirmed | 5a_control | 6 | frozen room erupts | 0 |
| | 5b_hazcam | 5 | grainy b&w frame floods with colour | 0 |
| | 5c_rover | 9 | dust settles, crane up and pull back | 0 |

Rover consistency as in v1: `5c_rover` is the text hero; `4e_skycrane` start and end are Klein edits of it.

## Run

```
# GPU box (same settings as v1's keyframes)
python pipeline/keyframes.py --v2 --model base --scale 1.0 --lora nsc7-style-lora_000001000.safetensors
# Mac
python pipeline/video.py --v2                 # 18 drafts with audio
python pipeline/video.py --v2 --only 4b_chute # redo a draft
python pipeline/cut_v2.py --drafts            # preview cut
python pipeline/video.py --v2 --final         # fhd
python pipeline/cut_v2.py [--music music.mp3] # out/v2/film.mp4
```
