# Perseverance: Earth to Mars — Clip Breakdown (Blender)

Total runtime: ~2:10 · 5 clips

---

## Global Settings

| Setting | Value |
|---|---|
| Software | Blender 4.x |
| Render engine | Cycles (hero shots), EEVEE (space/wide shots, previews) |
| Resolution | 1920×1080 (upscale option: 3840×2160) |
| Frame rate | 24 fps |
| Color management | AgX, Medium High Contrast |
| Motion blur | On (shutter 0.5) |
| Output | PNG sequence → edit/stitch in Blender VSE or DaVinci Resolve |

### Shared Assets

- **Perseverance rover**: NASA official 3D model (free, science.nasa.gov 3D resources). Glb/fbx → clean up materials.
- **Atlas V 541 rocket**: model from scratch or NASA 3D resources.
- **Aeroshell / backshell / heat shield / descent stage**: NASA Mars 2020 EDL models, or model from simple primitives.
- **Mars terrain**: HiRISE DTM of Jezero Crater (uahirise.org) → displacement in Blender.
- **Planet textures**: Earth + Mars 8K maps (NASA Visible Earth, Solar System Scope).
- **Star background**: HDRI star map (NASA SVS Deep Star Maps) as world texture.

### Color Script

| Clip | Mood | Palette |
|---|---|---|
| 1 | Mystery | Deep red, black, cold blue water glow |
| 2 | Power | Warm orange flame, white smoke, blue sky |
| 3 | Loneliness | Black space, tiny white craft, soft red approach |
| 4 | Danger | Plasma orange/pink → dusty tan → harsh rocket white |
| 5 | Relief | Soft Martian daylight, butterscotch sky |

---

## Clip 1 — "The Question"

**Duration:** 20s (frames 1–480)

**Story beat:** Why go? Mars once had water. Maybe life.

### Shots

| # | Time | Shot | Camera |
|---|---|---|---|
| 1a | 0–6s | Black. Mars slowly fades in, half lit by the sun. | Static, wide. Slow push in. |
| 1b | 6–14s | Dive toward the surface. Clouds of dust. Jezero Crater appears. | Fast dolly in, slight rotation. |
| 1c | 14–20s | Above Jezero. A ghost lake fills the crater with blue water and the river delta lights up, then fades back to dry rock. | Slow overhead orbit. |

### Blender Notes
- Mars: UV sphere + 8K color + bump/displacement maps. Thin atmosphere shell with Volume Scatter shader (red-orange haze on rim).
- Zoom transition: switch from planet sphere to HiRISE DTM plane, hidden by a dust/cloud wipe.
- Ghost lake: transparent water plane, animated **Z position** + shader **Alpha** keyframes. Emission glow on river channels via mask texture.

### Text / Narration
> "3.5 billion years ago, water flowed here. Was anything alive?"

### Audio
Low drone, single deep tone. Water shimmer sound when the lake appears.

---

## Clip 2 — "Liftoff"

**Duration:** 25s (frames 481–1080)

**Story beat:** Leaving home. Power and hope.

### Shots

| # | Time | Shot | Camera |
|---|---|---|---|
| 2a | 0–5s | Atlas V on pad SLC-41 at dawn. Steam venting. Text: *July 30, 2020*. | Low angle, slow tilt up. |
| 2b | 5–10s | Ignition. Flame and huge smoke burst. Rocket rises. | Ground level, camera shake. |
| 2c | 10–16s | Rocket climbs, trail curving into sky. | Long lens, tracking. |
| 2d | 16–25s | In space: payload fairing splits, spacecraft separates and drifts away. Earth fills background, then shrinks. | Slow follow cam, then pull away. |

### Blender Notes
- Flame + smoke: **Mantaflow** fire/smoke sim, or VDB from a smoke pack. Bake at high resolution only for shot 2b.
- Exhaust plume in flight: emission cone with noise texture (cheaper than sim).
- Camera shake: Noise modifier on camera F-curves.
- Earth: sphere + day/night textures + cloud layer + atmosphere shell (blue rim).

### Text / Narration
> "July 30, 2020. Cape Canaveral, Florida."

### Audio
Countdown voice ("3, 2, 1"), rumble that builds into a roar, then sudden silence in space.

---

## Clip 3 — "The Long Dark"

**Duration:** 25s (frames 1081–1680)

**Story beat:** 7 months alone. 470 million km. No one can help.

### Shots

| # | Time | Shot | Camera |
|---|---|---|---|
| 3a | 0–10s | Solar system view: Sun, Earth orbit, Mars orbit. A glowing arc traces the path from Earth to Mars. Counter: km and days rising. | Top-down, slow rotation. |
| 3b | 10–17s | Close on spacecraft. Sun glints off solar panels. Tiny thruster puffs (course correction). | Slow orbit around craft. |
| 3c | 17–25s | Mars grows from a dot to fill frame. Cruise stage separates. | Behind spacecraft, looking ahead. |

### Blender Notes
- Trajectory: Bezier curve + **Geometry Nodes** "Trim Curve" animated to draw the path. Emission material.
- Counter: Text object driven by a frame driver, or add in compositing/VSE.
- Thruster puffs: small particle burst, short lifetime, emission.
- Scale cheat: planets enlarged for readability. That's fine for storytelling.

### Text / Narration
> "7 months. 470 million kilometers."
> "Signals take 11 minutes to reach Earth. From here, it's on its own."

### Audio
Slow ambient music, soft piano or pads. Very quiet.

---

## Clip 4 — "7 Minutes of Terror"

**Duration:** 40s (frames 1681–2640) · **The climax**

**Story beat:** Entry, descent, landing. Everything has to work perfectly, on its own.

**Persistent overlay:** countdown timer **7:00 → 0:00** (sped up), plus HUD: speed + altitude.

### Shots

| # | Time | Shot | Camera |
|---|---|---|---|
| 4a | 0–8s | **Entry.** Aeroshell hits the atmosphere at 19,500 km/h. Heat shield glows orange → white. Plasma trail. | Side tracking, heavy shake. |
| 4b | 8–15s | **Parachute.** Chute fires at Mach 1.7, ~11 km up. Canopy snaps open violently. Brief freeze: red/white canopy pattern → reveal **"Dare Mighty Things"**. | Below looking up, then hero orbit. |
| 4c | 15–21s | **Heat shield drops.** Rover sees the ground. Scan overlay: green grid, hazard spots marked red, safe zone green. | Rover POV, then wide. |
| 4d | 21–28s | **Powered descent.** Backshell separates. Descent stage drops free, 8 rockets ignite. Dust starts to blow. | Falling alongside. |
| 4e | 28–40s | **Sky crane.** Hover at 20 m. Rover lowered on 3 cables (6.4 m). Wheels lock down. Touch. Cables cut. Descent stage flies away. | Low ground angle, slow motion at touchdown. |

### Blender Notes
- Plasma: emission shader on stretched shell around aeroshell, animated noise texture + glow in compositor.
- Heat shield glow: **Blackbody** node, temperature keyframed 1000K → 1600K.
- Parachute: **Cloth sim** for inflation, or shape keys (more control). Canopy texture with the binary code pattern.
- Terrain scan: Geometry Nodes or animated wireframe overlay; or render pass + compositing.
- Rocket dust: Mantaflow smoke with dust color, or particle system with large soft sprites.
- Cables: Bezier curves hooked to rover + descent stage (Hook modifier). Animate length.
- Descent stage fly-away: simple keyframes. Distant crash = small dust puff.
- Slow motion at touchdown: change time remapping, or keyframe actual slow movement.

### Text / Narration
> "Entry. 19,500 km/h."
> "Parachute deployed."
> "Heat shield separated. It's looking for a safe place."
> "Sky crane."

### Audio
Heartbeat pulse that speeds up. Roar of entry, snap of chute, rocket hiss. Cut to **silence** just before touchdown.

---

## Clip 5 — "Touchdown Confirmed"

**Duration:** 20s (frames 2641–3120)

**Story beat:** Relief. Joy. Perseverance arrived.

### Shots

| # | Time | Shot | Camera |
|---|---|---|---|
| 5a | 0–6s | JPL mission control (stylized). Team frozen, staring at screens. Silence. Then: "Touchdown confirmed." Room erupts. | Slow push on one person, then wide. |
| 5b | 6–11s | First image: grainy black & white Hazcam frame, then sharp color view. | Flat screen insert. |
| 5c | 11–20s | Dust settles. Rover alone in Jezero. Camera rises and pulls back until the rover is a tiny dot on the crater floor. Fade out. | Crane up + pull back. |

### Blender Notes
- Mission control: simple stylized room, low-poly people (Mixamo for animation: cheering, clapping). Keep silhouettes simple; lighting does the work (screen glow).
- Hazcam image: real NASA image as image plane (NASA images are public domain).
- Final shot: HiRISE Jezero DTM terrain, sun low for long shadows. Dust settle = particle fade.

### Text / Narration
> "February 18, 2021. Touchdown confirmed."

**End card:** *Dare Mighty Things.*

### Audio
Real JPL "Touchdown confirmed" call (NASA public domain). Cheering. Music swells, warm and wide. Ends on one soft tone.

---

## Production Order (suggested)

1. Build shared assets: rover, Mars terrain, planets, star HDRI.
2. **Clip 4 first.** Hardest, most important. Lock the look.
3. Clip 5 (reuses terrain + rover).
4. Clip 2 (rocket + smoke sim).
5. Clips 1 & 3 (mostly shaders + camera moves).
6. Edit, sound, overlays in VSE / Resolve.

## Fact Sheet (for on-screen text)

| Fact | Value |
|---|---|
| Launch | July 30, 2020 · Atlas V 541 · Cape Canaveral SLC-41 |
| Cruise | ~7 months · ~470 million km |
| Landing | February 18, 2021 · Jezero Crater |
| Entry speed | ~19,500 km/h |
| Heat shield peak | ~1,300 °C |
| Parachute | 21.5 m diameter · deployed ~Mach 1.7, ~11 km altitude |
| Sky crane | Hover ~20 m · cables 6.4 m · touchdown ~0.75 m/s |
| Signal delay | ~11 min 22 s |
| Hidden message | "Dare Mighty Things" + JPL GPS coordinates on parachute |
