"""Build greybox layout scenes for Clip 2 ("Liftoff").

Geometry, cameras and animation only: no materials, no lights, no shading
setup. Units are metres.

Usage:
    blender -b --python blender/clip2/build_clip2.py

Writes shot_2a.blend ... shot_2d.blend next to this script. Frame numbers
are global to the film (docs/clips.md): 2a = 481-600, 2b = 601-720,
2c = 721-864, 2d = 865-1080.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

MLP_HEIGHT = 6.0           # mobile launch platform deck
ROCKET_BASE = 10.0         # core base sits above the exhaust hole
IGNITION = 610
LIFTOFF = 625


# ---------------------------------------------------------------- helpers

def new_scene(frame_start, frame_end):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    scene.frame_set(frame_start)
    scene.render.fps = 24
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.image_settings.file_format = "PNG"

    world = bpy.data.worlds.new("World")
    world.color = (0.0, 0.0, 0.0)
    scene.world = world

    scene.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            scene.view_settings.look = look
            break
        except TypeError:
            pass
    return scene


def link(obj, parent=None):
    bpy.context.scene.collection.objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def empty(name, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    return link(obj, parent)


def finish_mesh(name, bm, location=(0, 0, 0), parent=None, sharp_angle=40):
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(sharp_angle))
    obj = bpy.data.objects.new(name, me)
    obj.location = location
    return link(obj, parent)


def lathe(name, profile, segments=48, a0=0.0, a1=2 * math.pi,
          offset=(0, 0, 0), location=(0, 0, 0), parent=None):
    """Spin an (r, z) profile around Z. Partial sweeps make open shells."""
    full = abs((a1 - a0) - 2 * math.pi) < 1e-6
    rings = segments if full else segments + 1
    m = len(profile)
    ox, oy, oz = offset
    bm = bmesh.new()
    verts = []
    for i in range(rings):
        th = a0 + (a1 - a0) * i / segments
        c, s = math.cos(th), math.sin(th)
        for r, z in profile:
            verts.append(bm.verts.new((r * c + ox, r * s + oy, z + oz)))
    for i in range(segments):
        i2 = (i + 1) % rings
        for j in range(m - 1):
            quad = [verts[i * m + j], verts[i2 * m + j],
                    verts[i2 * m + j + 1], verts[i * m + j + 1]]
            if len({v.co.to_tuple(5) for v in quad}) >= 3:
                try:
                    bm.faces.new(quad)
                except ValueError:
                    pass
    return finish_mesh(name, bm, location, parent)


def box(name, size, location=(0, 0, 0), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    sx, sy, sz = size
    for v in bm.verts:
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz + sz / 2))
    return finish_mesh(name, bm, location, parent, sharp_angle=30)


def blob(name, radius=1.0, location=(0, 0, 0), parent=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=radius)
    return finish_mesh(name, bm, location, parent, sharp_angle=180)


def sphere(name, radius, location=(0, 0, 0)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=64,
                              radius=radius)
    return finish_mesh(name, bm, location, sharp_angle=180)


def add_camera(name, lens=50.0, clip_end=1000.0):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_start = 0.1
    data.clip_end = clip_end
    cam = link(bpy.data.objects.new(name, data))
    bpy.context.scene.camera = cam
    return cam


def look_at(obj, target, roll=0.0):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    obj.rotation_euler.rotate_axis("Z", roll)


def fcurves(obj):
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return []
    # Blender 5 layered actions keep F-curves in channelbags.
    if hasattr(action, "layers") and action.layers:
        return [fc for layer in action.layers for strip in layer.strips
                for bag in strip.channelbags for fc in bag.fcurves]
    return list(action.fcurves)


def set_interpolation(obj, interp):
    for fc in fcurves(obj):
        for kp in fc.keyframe_points:
            kp.interpolation = interp


def key_scale(obj, frame, s):
    obj.scale = (s, s, s)
    obj.keyframe_insert("scale", frame=frame)


def add_marker(name, frame):
    bpy.context.scene.timeline_markers.new(name, frame=frame)


def save(scene, name):
    scene.render.filepath = f"//renders/{name}/frame_"
    path = os.path.join(OUT_DIR, f"{name}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("saved", path)


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- Atlas V 541

FAIRING_PROFILE = [(2.7, 0.0), (2.7, 14.0), (2.45, 17.0), (1.9, 19.5),
                   (1.1, 21.2), (0.3, 22.0), (0.0, 22.0)]


def build_atlas_v(flames=False):
    """Atlas V 541 on its own root. Root origin = core base."""
    root = empty("Atlas_V")

    # Common Core Booster, Centaur interstage flare, 5 m fairing.
    lathe("CCB", [(0, 0), (1.9, 0), (1.9, 32.5), (0, 32.5)], parent=root)
    lathe("CISA", [(0, 32.5), (1.9, 32.5), (2.7, 34.0), (2.7, 36.0),
                   (0, 36.0)], parent=root)
    for side, (a0, a1) in (("+Y", (0, math.pi)), ("-Y", (math.pi, 2 * math.pi))):
        lathe(f"Fairing_{side}", FAIRING_PROFILE, segments=24, a0=a0, a1=a1,
              offset=(0, 0, 36.0), parent=root)

    # RD-180: two bells under the core.
    for i, x in enumerate((-0.7, 0.7)):
        lathe(f"RD180_bell_{i}", [(0.35, 0.0), (0.5, -0.5), (1.0, -3.5)],
              segments=32, offset=(x, 0, 0), parent=root)

    # Four solid rocket boosters.
    srb_angles = [math.radians(a) for a in (30, 150, 210, 330)]
    for i, a in enumerate(srb_angles):
        x, y = 2.75 * math.cos(a), 2.75 * math.sin(a)
        lathe(f"SRB_{i}", [(0, 0.5), (0.8, 0.5), (0.8, 18.0), (0.6, 19.5),
                           (0, 20.5)], segments=32, offset=(x, y, 0),
              parent=root)
        lathe(f"SRB_{i}_nozzle", [(0.3, 0.5), (0.6, -1.3)], segments=24,
              offset=(x, y, 0), parent=root)

    flame_objs = []
    if flames:
        flame_profile = [(0.0, 0.0), (0.95, 0.0), (1.5, -7.0), (0.0, -20.0)]
        for i, x in enumerate((-0.7, 0.7)):
            flame_objs.append(lathe(f"Flame_RD180_{i}", flame_profile,
                                    segments=24, location=(x, 0, -3.5),
                                    parent=root))
        for i, a in enumerate(srb_angles):
            x, y = 2.75 * math.cos(a), 2.75 * math.sin(a)
            flame_objs.append(lathe(f"Flame_SRB_{i}", flame_profile,
                                    segments=24, location=(x, y, -1.3),
                                    parent=root))
    return root, flame_objs


# ---------------------------------------------------------------- SLC-41

def build_pad(ground_size=4000.0):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=ground_size / 2)
    finish_mesh("Ground", bm)

    box("MLP", (22, 18, MLP_HEIGHT))
    for i, (x, y) in enumerate(((-6, -5), (6, -5), (-6, 5), (6, 5))):
        box(f"MLP_pedestal_{i}", (2.5, 2.5, 3.0), location=(x, y, MLP_HEIGHT))
    box("Crew_Access_Tower", (12, 12, 70), location=(-22, 0, 0))
    box("Crew_Access_Arm", (12, 2.5, 2.5), location=(-12, 0, 52))
    for i, (x, y) in enumerate(((60, 60), (-60, 60), (60, -60), (-60, -60))):
        lathe(f"Lightning_Mast_{i}", [(0, 0), (0.8, 0), (0.5, 100), (0, 100)],
              segments=12, location=(x, y, 0))
    box("VIF", (50, 40, 90), location=(-420, 320, 0))


# ---------------------------------------------------------------- shot 2a

def build_shot_2a():
    """0-5s. Atlas V on SLC-41 at dawn, steam venting. Low angle, tilt up."""
    scene = new_scene(481, 600)
    build_pad()
    root, _ = build_atlas_v()
    root.location = (0, 0, ROCKET_BASE)

    # Boil-off steam: puffs that rise, grow and vanish, two cycles each.
    rng = random.Random(21)
    vents = [Vector((1.9, 0, ROCKET_BASE + 32.0)),       # top of core (LOX)
             Vector((-1.9, 0, ROCKET_BASE + 30.0)),
             Vector((2.7, 0, ROCKET_BASE + 40.0))]       # Centaur vent
    vents += [Vector((rng.uniform(-9, 9), rng.uniform(-8, 8), MLP_HEIGHT))
              for _ in range(6)]                         # deck steam
    n = 0
    for vent in vents:
        for cycle in range(3):
            start = 481 - 30 + cycle * 50 + rng.randint(0, 30)
            life = rng.randint(55, 75)
            puff = blob(f"Steam_{n:02d}", radius=1.0, location=vent)
            drift = Vector((rng.uniform(1, 4), rng.uniform(-2, 2),
                            rng.uniform(6, 12)))
            key_scale(puff, start, 0.0)
            puff.keyframe_insert("location", frame=start)
            key_scale(puff, start + life * 0.4, rng.uniform(1.2, 2.0))
            puff.location = vent + drift
            puff.keyframe_insert("location", frame=start + life)
            key_scale(puff, start + life, 0.0)
            n += 1

    cam = add_camera("CAM_2a", lens=24.0, clip_end=5000.0)
    cam.location = (42.0, -52.0, 1.6)
    f0, f1 = 481, 600
    for frame in range(f0, f1 + 1, 4):
        t = smoothstep((frame - f0) / (f1 - f0))
        look_at(cam, (0, 0, 10.0 + 48.0 * t))
        cam.keyframe_insert("rotation_euler", frame=frame)

    add_marker("2a text: July 30, 2020", 500)
    add_marker("2a end", 600)
    save(scene, "shot_2a")


# ---------------------------------------------------------------- shot 2b

def build_shot_2b():
    """5-10s. Ignition, smoke burst, rocket rises. Ground cam, shake."""
    scene = new_scene(601, 720)
    build_pad()
    root, flames = build_atlas_v(flames=True)

    # Flames grow at ignition (RD-180 first, SRBs at T-0).
    for obj in flames:
        start = IGNITION if "RD180" in obj.name else LIFTOFF - 3
        obj.scale = (0.01, 0.01, 0.01)
        obj.keyframe_insert("scale", frame=start)
        obj.scale = (1, 1, 1)
        obj.keyframe_insert("scale", frame=start + 10)

    # Liftoff: constant acceleration, about 20 m by the end of the shot.
    accel = 2.5
    for frame in range(601, 721, 2):
        t = max(0.0, (frame - LIFTOFF) / 24.0)
        root.location = (0, 0, ROCKET_BASE + 0.5 * accel * t * t)
        root.keyframe_insert("location", frame=frame)
    set_interpolation(root, "LINEAR")

    # Exhaust cloud: blobs thrown out of the trench and rolling outward.
    rng = random.Random(5)
    for i in range(60):
        start = IGNITION + rng.randint(2, 50)
        life = rng.randint(50, 90)
        side = rng.choice((-1, 1))
        ang = rng.uniform(-0.6, 0.6)
        out = Vector((side * math.cos(ang), math.sin(ang), 0))
        origin = Vector((side * 12, 0, 1.0))
        dist = rng.uniform(30, 130)
        puff = blob(f"Smoke_{i:02d}", location=origin)
        key_scale(puff, start, 0.0)
        puff.keyframe_insert("location", frame=start)
        puff.location = origin + out * dist + Vector((0, 0, rng.uniform(4, 30)))
        puff.keyframe_insert("location", frame=start + life)
        key_scale(puff, start + life, rng.uniform(8, 18))

    cam = add_camera("CAM_2b", lens=35.0, clip_end=5000.0)
    cam.location = (150.0, -150.0, 1.8)
    look_at(cam, (0, 0, 38.0))
    cam.keyframe_insert("rotation_euler", frame=601)
    cam.keyframe_insert("rotation_euler", frame=720)
    # Shake: noise on rotation, fading in from ignition to liftoff.
    for fc in fcurves(cam):
        mod = fc.modifiers.new("NOISE")
        mod.scale = 2.0
        mod.strength = 0.012
        mod.phase = fc.array_index * 7.0
        mod.use_restricted_range = True
        mod.frame_start = IGNITION
        mod.frame_end = 720
        mod.blend_in = LIFTOFF + 5 - IGNITION

    add_marker("2b ignition", IGNITION)
    add_marker("2b liftoff", LIFTOFF)
    add_marker("2b end", 720)
    save(scene, "shot_2b")


# ---------------------------------------------------------------- shot 2c

def ascent(t):
    """Rocket base position t seconds into shot 2c: climbing, pitching east."""
    return Vector((3.0 * t ** 3, 0.0, 400.0 + 150.0 * t + 25.0 * t * t))


def ascent_velocity(t):
    return Vector((9.0 * t * t, 0.0, 150.0 + 50.0 * t))


def build_shot_2c():
    """10-16s. Rocket climbs, trail curving into sky. Long lens tracking."""
    scene = new_scene(721, 864)
    build_pad(ground_size=60000.0)
    root, flames = build_atlas_v(flames=True)
    root.rotation_mode = "QUATERNION"
    for obj in flames:
        obj.scale = (1.4, 1.4, 3.0)       # plume stretches at altitude

    f0, f1 = 721, 864
    duration = (f1 - f0) / 24.0
    up = Vector((0, 0, 1))
    for frame in range(f0, f1 + 1, 2):
        t = (frame - f0) / 24.0
        root.location = ascent(t)
        root.rotation_quaternion = up.rotation_difference(
            ascent_velocity(t).normalized())
        root.keyframe_insert("location", frame=frame)
        root.keyframe_insert("rotation_quaternion", frame=frame)
    set_interpolation(root, "LINEAR")

    # Smoke trail: a chain of puffs along pad -> straight up -> curving
    # ascent. Each appears as the rocket passes it, then swells and drifts
    # downwind (the render turns "Trail_" blobs into volumes).
    # The vertical climb happened before this shot: spread it over 10 s.
    track_pts = [(ROCKET_BASE + 390.0 * i / 100, -10.0 + 10.0 * i / 100)
                 for i in range(100)]
    track_pts = [(Vector((0, 0, z)), t) for z, t in track_pts]
    track_pts += [(ascent(duration * i / 400), duration * i / 400)
                  for i in range(401)]
    spacing = 4.0
    samples = [track_pts[0]]
    walked = 0.0
    for (a, ta), (b, tb) in zip(track_pts, track_pts[1:]):
        walked += (b - a).length
        if walked >= spacing:
            samples.append((b, tb))
            walked = 0.0

    wind = Vector((0.0, 2.5, 0.0))     # metres per second, drifting north

    def puff_radius(age):
        return min(20.0, 6.0 + 1.5 * age)

    rng = random.Random(9)
    for i, (pos, t_pass) in enumerate(samples):
        pos = pos + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                            rng.uniform(-1, 1)))
        puff = blob(f"Trail_{i:03d}", location=pos)
        f_pass = f0 + t_pass * 24.0
        if f_pass > f0:
            key_scale(puff, max(f0, f_pass - 1), 0.0)
            puff.keyframe_insert("location", frame=f_pass)
            key_scale(puff, f_pass, puff_radius(0.0))
        else:
            puff.location = pos + wind * -t_pass
            puff.keyframe_insert("location", frame=f0)
            key_scale(puff, f0, puff_radius(-t_pass))
        age_end = duration - t_pass
        puff.location = pos + wind * age_end
        puff.keyframe_insert("location", frame=f1)
        key_scale(puff, f1, puff_radius(age_end))
        set_interpolation(puff, "LINEAR")

    aim = empty("CAM_2c_aim", location=(0, 0, 30.0), parent=root)
    cam = add_camera("CAM_2c", lens=300.0, clip_end=100000.0)
    cam.location = (3200.0, -4200.0, 2.0)
    track = cam.constraints.new("TRACK_TO")
    track.target = aim
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    add_marker("2c end", 864)
    save(scene, "shot_2c")


# ---------------------------------------------------------------- shot 2d

FAIRING_SPLIT = 885
SPACECRAFT_SEP = 935


def build_shot_2d():
    """16-25s. Fairing splits, spacecraft separates. Earth behind, shrinking."""
    scene = new_scene(865, 1080)

    stack = empty("Stack")
    # Centaur upper stage + RL10.
    centaur = lathe("Centaur", [(0, 0), (1.52, 0), (1.52, 12.7), (0, 12.7)],
                    parent=stack)
    lathe("RL10_bell", [(0.3, 0), (0.6, -1.6)], segments=24, parent=centaur)
    lathe("Payload_Adapter", [(1.52, 12.7), (0.8, 13.5), (0, 13.5)],
          parent=centaur)

    # Mars 2020: cruise stage on the adapter, aeroshell above, shield on top.
    craft = empty("Mars2020", location=(0, 0, 13.5), parent=stack)
    lathe("Cruise_Stage", [(0, 0), (2.0, 0), (2.0, 0.7), (0, 0.7)],
          parent=craft)
    lathe("Backshell", [(0, 0.7), (0.8, 0.7), (2.25, 3.2), (2.25, 3.4),
                        (0, 3.4)], parent=craft)
    lathe("Heat_Shield", [(2.25, 3.4), (1.0, 4.1), (0, 4.3)], parent=craft)

    # Fairing halves hinge outward at their base, then drift and tumble off.
    base_z = 0.0
    for side, sign, (a0, a1) in (("+Y", 1, (0, math.pi)),
                                 ("-Y", -1, (math.pi, 2 * math.pi))):
        hinge = Vector((0, sign * 2.7, base_z))
        half = lathe(f"Fairing_{side}", FAIRING_PROFILE, segments=24,
                     a0=a0, a1=a1, offset=-hinge + Vector((0, 0, base_z)),
                     location=hinge, parent=stack)
        keys = ((865, 0, 0, 0), (FAIRING_SPLIT, 0, 0, 0),
                (FAIRING_SPLIT + 25, 25, 4, -1), (1080, 95, 70, -18))
        for frame, ang, out, drop in keys:
            half.rotation_euler = (-sign * math.radians(ang), 0, 0)
            half.location = hinge + Vector((0, sign * out, drop))
            half.keyframe_insert("rotation_euler", frame=frame)
            half.keyframe_insert("location", frame=frame)

    # Separation: spacecraft drifts up and spins; Centaur backs off, tumbles.
    for frame, lift, spin in ((865, 0, 0), (SPACECRAFT_SEP, 0, 0),
                              (1080, 9.0, 25)):
        craft.location = (0, 0, 13.5 + lift)
        craft.rotation_euler = (0, 0, math.radians(spin))
        craft.keyframe_insert("location", frame=frame)
        craft.keyframe_insert("rotation_euler", frame=frame)
    for frame, back, tumble in ((865, 0, 0), (SPACECRAFT_SEP, 0, 0),
                                (1080, -7.0, 12)):
        centaur.location = (0, 0, back)
        centaur.rotation_euler = (math.radians(tumble), 0, 0)
        centaur.keyframe_insert("location", frame=frame)
        centaur.keyframe_insert("rotation_euler", frame=frame)

    # Earth behind the stack; moving it away is the stack leaving Earth.
    earth_dir = Vector((-1.0, 1.0, -0.9)).normalized()
    earth = sphere("Earth", radius=3000.0, location=earth_dir * 4200.0)
    for frame, dist in ((865, 4200.0), (960, 4400.0), (1080, 14000.0)):
        earth.location = earth_dir * dist
        earth.keyframe_insert("location", frame=frame)

    # Slow follow, then pull away.
    cam = add_camera("CAM_2d", lens=35.0, clip_end=50000.0)
    for frame, pos, target_z in ((865, (30, -32, 16), 12.0),
                                 (960, (34, -36, 18), 14.0),
                                 (1080, (95, -105, 38), 18.0)):
        cam.location = pos
        look_at(cam, (0, 0, target_z))
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)

    add_marker("2d fairing split", FAIRING_SPLIT)
    add_marker("2d spacecraft sep", SPACECRAFT_SEP)
    add_marker("2d pull away", 960)
    add_marker("2d end", 1080)
    save(scene, "shot_2d")


build_shot_2a()
build_shot_2b()
build_shot_2c()
build_shot_2d()
