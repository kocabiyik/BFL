"""Shot list for v2 of the film: the 18 shots of the Blender breakdown in
docs/clips.md (1a-5c, same timing and camera), cut for action.

Same schema as shots.py (keyframes.py, video.py and cut.py take --v2), plus:
  clip:     docs/clips.md clip number; hard cuts inside a clip, crossfades between.
  shake:    post-shake strength in the cut, 0 (none) to 3 (violent).
  caption:  optional narration line burned in at the bottom left.

Motion prompts follow the FLUX 3 video guide: timed phases, named camera
moves, "never freezes", and the sound of the shot (generate_audio is on).
Story and timing are in docs/shots_v2.md.
"""

from shots import TRIGGER  # noqa: F401  (keyframes.py reads it from here)

HOLD = ("The camera may shake and move fast, but the image never turns into a "
        "photograph or 3D render; it stays a flat hand-painted 1970s gouache "
        "space painting with brushy skies and speckled stars the whole time. "
        "The motion never freezes. No on-screen text, no music, no speech.")

SHOTS = [
    # Clip 1: "The Question"
    {
        "id": "1a_mars", "clip": 1, "duration": 6, "shake": 0,
        "beat": "Mars fades in, half lit by the sun.",
        "key": {"prompt": "The planet Mars hangs in black space, half lit by the distant Sun, its rust-red surface marked by dark plains, a long canyon and a white polar cap. A thin orange haze glows along the curved edge of the planet, and faint stars fill the sky around it."},
        "motion": "0-6s: the camera pushes steadily toward Mars as sunlight sweeps across the terminator and the canyon slides into the light. Sound: a single deep low drone that slowly swells.",
        "caption": "3.5 billion years ago, water flowed here.",
    },
    {
        "id": "1b_dive", "clip": 1, "duration": 8, "shake": 1,
        "beat": "Dive toward the surface through dust. Jezero appears.",
        "key": {"prompt": "Looking straight down from high above Mars through swirling tan and orange dust clouds, the round rim of a large crater breaks through the haze, with a dark fan-shaped river delta on its western side."},
        "motion": "0-3s: the camera crash-dives toward the ground, tearing through the dust clouds as they rush past the lens, rotating slowly. 3-8s: the clouds part and the crater rim races up to fill the frame. Sound: rushing wind and a rising roar.",
    },
    {
        "id": "1c_lake", "clip": 1, "duration": 6, "shake": 0,
        "beat": "Ghost lake fills Jezero, then fades back to dry rock.",
        "key": {"prompt": "Seen from above, a wide round crater on Mars with a branching river delta on its western rim, the dry red-brown floor scattered with rocks and long shadows under a low Sun."},
        "motion": "0-2s: the camera orbits overhead as translucent painted water spills in from the river delta and spreads across the crater floor, the rocks still showing through it, the channels glinting. 2-4s: the lake ripples with brushy highlights, a deep teal that reflects the orange sky, never a flat solid colour. 4-6s: the water sinks into the ground and fades, leaving dry red rock. Sound: a water shimmer that rises and fades.",
        "caption": "Was anything alive?",
    },
    # Clip 2: "Liftoff"
    {
        "id": "2a_pad", "clip": 2, "duration": 5, "shake": 0,
        "beat": "Atlas V on SLC-41 at dawn, steam venting.",
        "key": {"prompt": "Looking up from the base of the launch pad at a tall white Atlas V rocket beside a steel launch tower at dawn, jets of white steam venting from its sides, the sky glowing orange and violet behind it."},
        "motion": "0-5s: the camera tilts up the rocket from its engines to its nose while jets of steam burst out and roll down the tower. Sound: hissing steam, metal creaks, a distant countdown beep.",
        "caption": "July 30, 2020 · Cape Canaveral",
    },
    {
        "id": "2b_ignition", "clip": 2, "duration": 5, "shake": 3,
        "beat": "Ignition. Flame and a huge smoke burst. Rocket rises.",
        "key": {"prompt": "At ground level beside the launch pad, the engines of a white rocket blaze with a blinding orange flame while an enormous wall of white smoke bursts sideways across the ground toward the viewer, the rocket just lifting above the tower."},
        "motion": "0-1s: a blinding ignition flash. 1-3s: the smoke wall surges straight at the camera, which shakes violently from the blast. 3-5s: the rocket clears the tower and rises on a pillar of fire. Sound: an explosive ignition, then a ground-shaking roar and crackle.",
    },
    {
        "id": "2c_climb", "clip": 2, "duration": 6, "shake": 1,
        "beat": "Rocket climbs, trail curving into the sky.",
        "key": {"prompt": "Far away through a long lens, a small white rocket rides a bright flame high into a blue and violet sky, trailing a thick white exhaust plume that curves back down to the horizon."},
        "motion": "0-1s: a fast whip pan catches the rocket. 1-6s: the long lens tracks it as it climbs fast and straight up in one smooth arc, flame flickering, the exhaust trail a single clean curve behind it that never loops or spirals, the image jittering from the long lens. Sound: a thundering roar crackling in the distance.",
    },
    {
        "id": "2d_separation", "clip": 2, "duration": 9, "shake": 1,
        "beat": "Fairing splits, spacecraft separates. Earth shrinks behind.",
        "key": {"prompt": "High above the curved blue Earth, two huge curved white fairing shells drift apart on either side, opening like a split eggshell around a flat disc-shaped spacecraft with a ring of solar panels. The spacecraft sits on top of a plain smooth silver cylinder, the rocket's upper stage, with a single engine bell at its base and no fins or wings, against black space."},
        "motion": "0-1s: bright pyro flashes. 1-3s: the two fairing shells blast apart and tumble past the camera, spinning end over end. 3-6s: the spacecraft springs free of the upper stage, which falls away toward Earth. 6-9s: the camera banks and pulls far back as the spacecraft heads into the dark. Sound: sharp bangs of the pyrotechnics, then sudden silence.",
    },
    # Clip 3: "The Long Dark"
    {
        "id": "3a_path", "clip": 3, "duration": 10, "shake": 0,
        "beat": "Solar system: a glowing arc traces the path to Mars.",
        "key": {"prompt": "Seen from far above the solar system, the bright Sun sits at the center with two thin circular orbits around it, a small blue Earth on the inner orbit and a small red Mars on the outer one, across a starfield streaked with faint violet clouds."},
        "motion": "0-10s: the view rotates slowly while a glowing white arc races out from Earth and curves around the Sun to meet Mars, the planets sliding along their orbits. Sound: soft low ambient pads.",
        "caption": "7 months · 470 million km",
    },
    {
        "id": "3b_thrusters", "clip": 3, "duration": 7, "shake": 1,
        "beat": "Close on the craft. Sun glints. Thruster puffs.",
        "key": {"prompt": "Close up on a disc-shaped spacecraft with a ring of solar panels drifting through black space, a hard white glint of sunlight on its panels and a tiny puff of thruster gas at its rim."},
        "motion": "0-7s: the camera orbits fast around the spacecraft as its thrusters fire in sharp bursts of white gas, each burst jolting the craft, sunlight flaring across the panels. Sound: muffled thumps of each thruster burst over quiet pads.",
    },
    {
        "id": "3c_approach", "clip": 3, "duration": 8, "shake": 1,
        "beat": "Mars grows to fill the frame. Cruise stage separates.",
        "key": {"prompt": "From just behind a disc-shaped spacecraft, the red planet Mars hangs ahead in black space, large and half lit, its canyons and craters clearly visible."},
        "motion": "0-5s: the camera rushes forward behind the spacecraft as Mars swells to fill the whole frame. 5-8s: the ring of solar panels snaps off and spins away, leaving the capsule diving alone toward the planet. Sound: rising rumble, a sharp clank at separation.",
        "caption": "From here, it's on its own.",
    },
    # Clip 4: "7 Minutes of Terror"
    {
        "id": "4a_entry", "clip": 4, "duration": 8, "shake": 3,
        "beat": "Entry at 19,500 km/h. Heat shield glows. Plasma trail.",
        "key": {"prompt": "Side view of a blunt cone-shaped capsule slamming into the thin atmosphere of Mars heat shield first, its shield glowing white hot and wrapped in a violent orange and pink plasma trail that tears out behind it. Far below, the red surface curves away under a dark violet sky."},
        "motion": "0-8s: the camera tracks alongside the capsule, shaking hard, as the heat shield flares from orange to white and the plasma whips and flickers around it, sparks streaming past the lens. Sound: a deafening roar of entry and a fast heartbeat.",
        "caption": "Entry · 19,500 km/h",
    },
    {
        "id": "4b_chute", "clip": 4, "duration": 7, "shake": 3,
        "beat": "Parachute at Mach 1.7 snaps open violently.",
        "key": {"prompt": "Looking up from below at a cone-shaped capsule as a huge red and white parachute bursts out of its back and begins to open against a dusty butterscotch sky, the canopy patterned with bold rings of red and white panels."},
        "motion": "0-1s: the half-open canopy is crumpled and fluttering. 1-2s: it slams fully open in an instant with a violent jolt, yanking the capsule hard upward and shaking the camera. 2-4s: the capsule swings wildly beneath the canopy on its lines. 4-7s: the camera swings fast around it in a hero orbit as dust streaks past. Sound: an explosive mortar bang, a canopy crack, roaring wind.",
        "caption": "Parachute deployed",
    },
    {
        "id": "4c_shield", "clip": 4, "duration": 6, "shake": 2,
        "beat": "Heat shield drops. The rover sees the ground.",
        "key": {"prompt": "Looking straight down from under a descending spacecraft, a round glowing heat shield falls away toward the dusty red ground of a crater far below, tumbling as it drops."},
        "motion": "0-3s: the heat shield tumbles away and shrinks toward the ground. 3-6s: the crater floor rushes up, ridges and boulders sharpening as the camera sways. Sound: a heavy clunk, then rushing wind and a fast heartbeat.",
        "caption": "Heat shield separated",
    },
    {
        "id": "4d_powered", "clip": 4, "duration": 7, "shake": 3,
        "beat": "Backshell separates. Eight rockets ignite.",
        "key": {"prompt": "Falling through the dusty sky of Mars beside a rocket-powered descent stage carrying a six-wheeled rover beneath it, the empty cone-shaped backshell and parachute dropping away above, the crater floor below."},
        "motion": "0-2s: the descent stage drops free of the backshell. 2-4s: eight rocket engines ignite with bright flames, braking hard, the camera shaking with the thrust. 4-7s: dust starts to blow off the ground below. Sound: a loud bang, then a screaming rocket hiss.",
    },
    {
        "id": "4e_skycrane", "clip": 4, "duration": 12, "shake": 2,
        "beat": "Sky crane: rover lowered on three cables, touches down.",
        "key": {"edit_of": "5c_rover",
                "edit": "Show the same rover hanging on three cables beneath a rocket-powered descent stage, a few metres above the crater floor, its thrusters blasting violent swirling clouds of dust."},
        "end": {"edit_of": "5c_rover",
                "edit": "Show the same rover standing on the crater floor, its cables just cut, while the descent stage flies up and away in the distance trailing rocket exhaust and settling dust."},
        "motion": "0-6s: from a low ground angle, the descent stage lowers the rover on its cables through a storm of blasting dust, the camera shaking. 6-9s: slow motion as the wheels touch the ground and the cables cut. 9-12s: the descent stage roars up and away. Sound: screaming rockets, then sudden total silence at touchdown.",
        "caption": "Sky crane",
    },
    # Clip 5: "Touchdown Confirmed"
    {
        "id": "5a_control", "clip": 5, "duration": 6, "shake": 0,
        "beat": "Mission control frozen. Touchdown confirmed. Room erupts.",
        "key": {"prompt": "Engineers in short-sleeved shirts sit frozen at rows of consoles in a dim mission control room, staring at large screens that glow blue and orange. One woman in the front row leans forward with her hands pressed together."},
        "motion": "0-2s: total stillness, the camera pushing in on the woman. 2-6s: the room erupts, engineers jumping up cheering, hugging and punching the air. Sound: silence, then a roar of cheering and applause.",
        "caption": "February 18, 2021 · Touchdown confirmed",
    },
    {
        "id": "5b_hazcam", "clip": 5, "duration": 5, "shake": 0,
        "beat": "First image: grainy black and white, then colour.",
        "key": {"prompt": "A grainy black and white view from a camera low on a rover, looking across a flat rock-strewn crater floor on Mars toward a low ridge, the edge of a metal wheel in the corner."},
        "motion": "0-2s: the grainy black and white picture flickers. 2-5s: the grain clears and the scene floods with warm butterscotch and rust colour. Sound: soft electronic beeps, distant cheering.",
    },
    {
        "id": "5c_rover", "clip": 5, "duration": 9, "shake": 0,
        "beat": "Alone in Jezero. Camera rises and pulls back.",
        "key": {"prompt": "The Perseverance rover, a six-wheeled car-sized robot with a tall camera mast, sits alone on a rock-strewn crater floor on Mars, with a low ridge on the horizon and a dusty butterscotch sky. Its long shadow stretches across the ground in the low evening sun."},
        "motion": "0-3s: the last dust settles around the rover. 3-9s: the camera cranes up and pulls back until the rover is a tiny dot on the wide crater floor. Sound: a soft wind and one warm, wide tone.",
    },
]

BY_ID = {shot["id"]: shot for shot in SHOTS}
