"""Shot list for the film: "Perseverance", Earth to Mars in eight shots.

One source of truth for keyframes.py (Klein + nsc7 LoRA) and video.py
(FLUX 3 video). Story and timing are in shots.md.

Each shot has:
  key:       start keyframe. Either a text prompt ("prompt") written like the
             training captions (content only, never the look; the trigger is
             appended by keyframes.py), or an edit ("edit_of" another
             keyframe + "edit" instruction) to keep the rover consistent.
  end:       optional end keyframe, same form, pinned at the clip's end.
  duration:  seconds of video to generate (the cut trims it).
  motion:    video prompt: what happens after the first frame.
"""

TRIGGER = "nsc7 style"

# Said in every video prompt so the look holds after frame one.
HOLD = ("The image never turns into a photograph or 3D render; it stays a flat "
        "hand-painted 1970s gouache space painting with brushy skies and "
        "speckled stars the whole time.")

SHOTS = [
    {
        "id": "01_mars",
        "beat": "Why go? Mars once had water.",
        "key": {"prompt": "The planet Mars hangs in black space, half lit by the distant Sun, its rust-red surface marked by dark plains, a long canyon and a white polar cap. A thin pale haze glows along the curved edge of the planet, and faint stars fill the sky around it."},
        "duration": 8,
        "motion": "The camera pushes slowly toward Mars as it turns, the lit edge brightening and the canyon sliding into view.",
    },
    {
        "id": "02_liftoff",
        "beat": "Leaving home. July 30, 2020.",
        "key": {"prompt": "A tall white Atlas V rocket stands on its launch pad at dawn beside a steel launch tower, just at the moment of ignition, with a bright flame and the first billows of white exhaust spreading across the ground. The sky glows orange and violet behind it."},
        "duration": 8,
        "motion": "The rocket lifts off and climbs out of frame, the exhaust cloud rolling outward across the pad and the flame lighting the smoke from inside.",
    },
    {
        "id": "03_cruise",
        "beat": "Seven months alone. 470 million km.",
        "key": {"prompt": "A small disc-shaped spacecraft with solar panels drifts through dark space, a tiny blue Earth far behind it on the left and a small red Mars ahead on the right. A thin white line traces its curving path between the two planets across a starfield streaked with faint violet clouds."},
        "duration": 10,
        "motion": "The spacecraft drifts slowly across the frame toward Mars, a tiny thruster puff flickering on its side, while the stars barely move.",
    },
    {
        "id": "04_entry",
        "beat": "Seven minutes of terror. Entry at 19,500 km/h.",
        "key": {"prompt": "A blunt cone-shaped capsule plunges into the thin atmosphere of Mars heat shield first, wrapped in a glowing orange and white plasma trail that streams out behind it. Far below, the red surface curves away under a dark violet sky."},
        "duration": 8,
        "motion": "The capsule shakes as it falls, the plasma glow flaring brighter and the fiery trail stretching longer behind it.",
    },
    {
        "id": "05_parachute",
        "beat": "Parachute at Mach 1.7.",
        "key": {"prompt": "A cone-shaped spacecraft descends over a dusty red planet under a huge red and white striped parachute, high above craters and canyons, with the curved horizon below."},
        "duration": 8,
        "motion": "The parachute snaps open and fills, swinging the capsule beneath it, then the heat shield drops away below and falls toward the ground.",
    },
    {
        "id": "06_skycrane",
        "beat": "Sky crane. Twenty metres up, on three cables.",
        "key": {"edit_of": "08_rover",
                "edit": "Show the same rover hanging on three cables beneath a rocket-powered descent stage, a few metres above the crater floor, its thrusters blasting swirling clouds of dust."},
        "end": {"edit_of": "08_rover",
                "edit": "Show the same rover standing on the crater floor, its cables just cut, while the descent stage flies up and away in the distance trailing rocket exhaust and settling dust."},
        "duration": 10,
        "motion": "The descent stage lowers the rover on its cables until the wheels touch the ground, the cables release, and the descent stage flies up and away.",
    },
    {
        "id": "07_control",
        "beat": "February 18, 2021. Touchdown confirmed.",
        "key": {"prompt": "Engineers in short-sleeved shirts sit at rows of consoles in a dim mission control room, staring at large screens that glow blue and orange. One woman in the front row leans forward with her hands pressed together."},
        "duration": 8,
        "motion": "The room is frozen and silent, then the engineers jump up from their consoles cheering, hugging and raising their arms.",
    },
    {
        "id": "08_rover",
        "beat": "Alone in Jezero. Dare mighty things.",
        "key": {"prompt": "The Perseverance rover, a six-wheeled car-sized robot with a tall camera mast, sits alone on a rock-strewn crater floor on Mars, with a low ridge on the horizon and a dusty butterscotch sky. Its long shadow stretches across the ground in the low evening sun."},
        "duration": 10,
        "motion": "The dust settles around the rover, then the camera rises and pulls back until the rover is a tiny dot on the wide crater floor.",
    },
]

BY_ID = {shot["id"]: shot for shot in SHOTS}
