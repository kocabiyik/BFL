# Perseverance — shot list (FLUX 3 film)

Replaces the Blender plan in `clips.md` for the challenge film. Eight shots, one keyframe-started clip each, ~70 s generated, cut to 55–65 s.
Prompts live in `pipeline/shots.py` (shared by `keyframes.py` and `video.py`).

Look: `nsc7 style` LoRA (Rick Guidice, NASA Ames 1970s paintings) on FLUX 3 Image Klein. Every video prompt ends with the same "stays a flat hand-painted 1970s gouache space painting" line so the look holds in motion.

| # | Shot | Beat | Keyframes | Gen | Motion |
|---|---|---|---|---|---|
| 1 | Mars | Why go? Mars once had water. | text | 8 s | slow push toward the half-lit planet |
| 2 | Liftoff | Leaving home. July 30, 2020. | text | 8 s | Atlas V lifts off, smoke rolls out |
| 3 | Cruise | Seven months alone. 470 million km. | text | 10 s | spacecraft drifts Earth → Mars, thruster puff |
| 4 | Entry | Seven minutes of terror. | text | 8 s | capsule shakes, plasma flares |
| 5 | Parachute | Parachute at Mach 1.7. | text | 8 s | chute snaps open, heat shield drops |
| 6 | Sky crane | Twenty metres up, on three cables. | start + end, both edited from shot 8's rover | 10 s | rover lowered, touches down, stage flies off |
| 7 | Mission control | Touchdown confirmed. | text | 8 s | frozen room erupts in cheers |
| 8 | Rover | Alone in Jezero. Dare mighty things. | text (hero rover) | 10 s | dust settles, camera rises and pulls back |

## Consistency

- The rover is generated once (shot 8, the hero frame). Shot 6's start and end frames are Klein edits of it, so it is the same rover throughout.
- Same seed (1975) for every keyframe; LoRA scale 0.75.

## Sound

`generate_audio: false` on every clip; one music track under the whole film in the cut, so sound does not change at each cut. Optional title cards: dates from the fact sheet in `clips.md`.
