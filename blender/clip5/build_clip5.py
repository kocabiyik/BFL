"""Build greybox layout scenes for Clip 5 ("Touchdown Confirmed").

Geometry, cameras and animation only: no materials, no lights, no shading
setup. Units are metres. The rover and Jezero terrain match Clip 4; landing
dust is "Rocketdust_" blobs that the EEVEE render turns into volumes.

Usage:
    blender -b --python blender/clip5/build_clip5.py

Writes shot_5a.blend, shot_5b.blend and shot_5c.blend next to this script.
Frame numbers are global to the film (clips.md): 5a = 2641-2784,
5b = 2785-2904, 5c = 2905-3120.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Quaternion, Vector

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


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


# ---------------------------------------------------------------- shared

def add_shake(cam, strength, start, end, blend_in, scale=1.5):
    """Noise on the camera's rotation F-curves over a frame range."""
    for fc in fcurves(cam):
        if fc.data_path != "rotation_euler":
            continue
        mod = fc.modifiers.new("NOISE")
        mod.scale = scale
        mod.strength = strength
        mod.phase = fc.array_index * 7.0 + start
        mod.use_restricted_range = True
        mod.frame_start = start
        mod.frame_end = end
        mod.blend_in = blend_in


def bind_camera(cam, frame, label):
    marker = bpy.context.scene.timeline_markers.new(label, frame=frame)
    marker.camera = cam


def small_blob(name, radius, location=(0, 0, 0), parent=None, subdiv=2):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=radius)
    return finish_mesh(name, bm, location, parent, sharp_angle=180)


# ---------------------------------------------------------------- vehicles

def build_rover(parent=None, location=(0, 0, 0)):
    """Perseverance, stowed. Origin at the bottom of the wheels."""
    root = empty("Perseverance", location=location, parent=parent)
    root.scale = (0.85, 0.85, 0.85)      # stowed fit inside the backshell
    box("Rover_Body", (2.2, 1.6, 0.55), location=(0, 0, 0.75), parent=root)
    rtg = box("Rover_RTG", (0.5, 0.7, 0.5), location=(-1.25, 0, 0.85),
              parent=root)
    rtg.rotation_euler = (0, math.radians(30), 0)
    mast = lathe("Rover_Mast", [(0, 0), (0.06, 0), (0.06, 1.6), (0, 1.6)],
                 segments=12, location=(-0.6, 0.55, 1.4), parent=root)
    mast.rotation_euler = (0, math.radians(90), 0)
    box("Rover_Mast_Head", (0.3, 0.25, 0.2), location=(1.05, 0.55, 1.3),
        parent=root)
    box("Rover_Arm", (0.15, 1.2, 0.15), location=(1.18, 0, 0.85), parent=root)
    for side in (-1, 1):
        box(f"Rover_Rocker_{side:+d}", (2.3, 0.08, 0.08),
            location=(0.0, side * 1.05, 0.55), parent=root)
        for i, x in enumerate((-1.0, 0.0, 1.05)):
            box(f"Rover_Strut_{side:+d}_{i}", (0.08, 0.08, 0.3),
                location=(x, side * 1.05, 0.26), parent=root)
            wheel = lathe(f"Rover_Wheel_{side:+d}_{i}",
                          [(0, -0.13), (0.26, -0.13), (0.26, 0.13),
                           (0, 0.13)], segments=24,
                          location=(x, side * 1.05, 0.26), parent=root)
            wheel.rotation_euler = (math.radians(90), 0, 0)
    return root



# ---------------------------------------------------------------- terrain

JEZERO_CENTER = Vector((12400.0, -2250.0, 0.0))   # landing site is origin
JEZERO_R = 22500.0


def jezero_raw(x, y):
    px, py = x - JEZERO_CENTER.x, y - JEZERO_CENTER.y
    r = math.hypot(px, py) / JEZERO_R
    h = 0.0
    if r < 1.0:
        h -= 450.0 * (1.0 - r ** 4)
    h += 250.0 * math.exp(-((r - 1.0) / 0.08) ** 2)
    # Western delta fan.
    qx, qy = px + 0.9 * JEZERO_R, py - 0.1 * JEZERO_R
    if qx > 0:
        a = math.atan2(qy, qx)
        reach = 9000.0 * (1.0 + 0.15 * math.cos(a * 6.0))
        fr = math.hypot(qx, qy) / reach
        if fr < 1.0 and abs(a) < 1.2:
            h += 120.0 * (1.0 - fr * fr) * math.cos(a * 0.6)
    # Neretva Vallis inlet from the west.
    if px < -0.85 * JEZERO_R:
        d = abs(py - 0.1 * JEZERO_R - 800.0 * math.sin(px / 3000.0))
        h -= 80.0 * math.exp(-(d / 600.0) ** 2)
    h += 30.0 * math.sin(x / 7000.0) * math.cos(y / 9000.0)
    return h


def build_jezero(parent=None):
    """Jezero at real scale (metres), landing site at the origin."""
    base = jezero_raw(0.0, 0.0) + 0.4      # sits just under the local patch
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=320, y_segments=320, size=80000.0)
    for v in bm.verts:
        v.co.z = jezero_raw(v.co.x, v.co.y) - base
    return finish_mesh("Jezero", bm, parent=parent, sharp_angle=180)


def build_landing_patch(parent=None, rocks=True):
    """2 km of crater floor around the landing site, with rocks."""
    rng = random.Random(42)
    bumps = [(rng.uniform(-1000, 1000), rng.uniform(-1000, 1000),
              rng.uniform(30, 150), rng.uniform(-2.0, 2.0))
             for _ in range(60)]
    pits = [(rng.uniform(-900, 900), rng.uniform(-900, 900),
             rng.uniform(5, 40)) for _ in range(14)]

    def height(x, y):
        # Follows the crater floor and fades its own detail out at the
        # edges, so it meets the coarse Jezero mesh without a step.
        z = 0.0
        for bx, by, w, amp in bumps:
            z += amp * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (w * w))
        for cx, cy, size in pits:
            r = math.hypot(x - cx, y - cy) / size
            if r < 2.0:
                if r < 1.0:
                    z -= size * 0.2 * (1.0 - r * r)
                z += size * 0.06 * math.exp(-((r - 1.0) / 0.2) ** 2)
        fade = smoothstep((1000.0 - max(abs(x), abs(y))) / 200.0)
        return z * fade + jezero_raw(x, y) - jezero_raw(0.0, 0.0)

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=200, y_segments=200, size=1000.0)
    for v in bm.verts:
        v.co.z = height(v.co.x, v.co.y)
    patch = finish_mesh("Landing_Patch", bm, parent=parent, sharp_angle=180)

    if rocks:
        for i in range(260):
            dist = 150.0 * math.sqrt(rng.random())
            a = rng.uniform(0, 2 * math.pi)
            x, y = dist * math.cos(a), dist * math.sin(a)
            if dist < 6.0:
                continue                   # keep the touchdown spot clear
            radius = min(1.2, 0.06 * math.exp(rng.gauss(0.6, 0.7)))
            rock = small_blob(f"Rock_{i:03d}", radius, subdiv=1,
                              location=(x, y, height(x, y) - 0.3 * radius),
                              parent=parent)
            rock.scale = (1.0, rng.uniform(0.6, 1.0), rng.uniform(0.4, 0.8))
            rock.rotation_euler = (0, 0, rng.uniform(0, math.pi))
    return patch, height


def build_ground(rocks=True):
    ground = empty("Ground")
    build_jezero(parent=ground)
    _, height = build_landing_patch(parent=ground, rocks=rocks)
    return ground, height



# ---------------------------------------------------------------- clip 5

TOUCHDOWN_CALL = 2722      # "Touchdown confirmed." in 5a


def build_rover_landed(location=(0, 0, 0)):
    """Perseverance on the ground with the remote sensing mast raised."""
    root = build_rover(location=location)
    mast = bpy.data.objects["Rover_Mast"]
    mast.location = (0.95, 0.55, 1.3)
    mast.rotation_euler = (0, 0, 0)
    mast.scale = (1, 1, 0.56)            # 0.9 m above the deck
    head = bpy.data.objects["Rover_Mast_Head"]
    head.location = (0.95, 0.55, 2.2)
    return root


# ---------------------------------------------------------------- people

def build_person(name, location, facing=0.0, seed=0):
    """Low-poly standing figure facing +Y (rotated by `facing`).

    Returns (root, (left_shoulder, right_shoulder))."""
    rng = random.Random(seed)
    root = empty(name, location=location)
    root.rotation_euler = (0, 0, facing)
    s = rng.uniform(0.92, 1.06)
    root.scale = (s, s, s)
    for side in (-1, 1):
        box(f"{name}_Leg_{side:+d}", (0.14, 0.16, 0.85),
            location=(side * 0.1, 0, 0), parent=root)
    lathe(f"{name}_Torso", [(0, 0.85), (0.19, 0.85), (0.22, 1.25),
                            (0.2, 1.45), (0, 1.47)], segments=10,
          parent=root)
    small_blob(f"{name}_Head", 0.12, location=(0, 0, 1.62), parent=root)
    shoulders = []
    for side in (-1, 1):
        sh = empty(f"{name}_Shoulder_{side:+d}",
                   location=(side * 0.27, 0, 1.42), parent=root)
        box(f"{name}_Arm_{side:+d}", (0.09, 0.09, 0.62),
            location=(0, 0, -0.62), parent=sh)
        shoulders.append(sh)
    return root, shoulders


def animate_celebration(root, shoulders, start, end, rng):
    """Frozen until `start`, then arms up, jumping and waving to `end`."""
    base_z = root.location.z
    root.keyframe_insert("location", index=2, frame=start)
    for sh in shoulders:
        sh.rotation_euler = (0, 0, 0)
        sh.keyframe_insert("rotation_euler", frame=start)
    up = start + rng.randint(4, 7)
    jumper = rng.random() < 0.6
    for frame in range(up, end + 1, 3):
        phase = (frame - up) / 3
        for k, sh in enumerate(shoulders):
            wave = math.radians(20) * math.sin(phase * 1.3 + k * 1.7)
            sh.rotation_euler = (math.radians(165) + wave,
                                 (-1 if k == 0 else 1) * math.radians(15), 0)
            sh.keyframe_insert("rotation_euler", frame=frame)
        if jumper:
            root.location.z = base_z + (0.22 if int(phase) % 2 == 0 else 0.0)
            root.keyframe_insert("location", index=2, frame=frame)


# ---------------------------------------------------------------- shot 5a

def build_shot_5a():
    """0-6s. JPL mission control. Frozen, then the room erupts."""
    scene = new_scene(2641, 2784)
    f0, f1 = 2641, 2784

    # Room: no ceiling, so the sun can light it (lookdev lights it later).
    box("Floor", (30, 22, 0.1), location=(0, 0, -0.1))
    box("Wall_Back", (30, 0.3, 6), location=(0, 10.5, 0))
    box("Wall_Left", (0.3, 22, 6), location=(-15, 0, 0))
    box("Wall_Right", (0.3, 22, 6), location=(15, 0, 0))
    for i, x in enumerate((-9.0, 0.0, 9.0)):
        box(f"Wall_Screen_{i}", (7.5, 0.1, 3.2), location=(x, 10.3, 1.8))

    # Three rows of consoles with monitors, people standing behind them.
    rng = random.Random(30)
    hero = None
    people = []
    for row, y in enumerate((-4.0, 0.0, 4.0)):
        box(f"Console_{row}", (13.0, 0.9, 0.75), location=(0, y, 0))
        for k in range(6):
            x = -5.5 + k * 2.2
            mon = box(f"Monitor_{row}_{k}", (0.65, 0.06, 0.42),
                      location=(x, y + 0.15, 0.8))
            mon.rotation_euler = (math.radians(-10), 0, 0)
            px = x + rng.uniform(-0.3, 0.3)
            name = f"Person_{row}_{k}"
            person = build_person(name, (px, y - 0.95, 0.0),
                                  facing=math.radians(rng.uniform(-12, 12)),
                                  seed=row * 10 + k)
            people.append(person)
            if row == 1 and k == 2:
                hero = person
    for root, shoulders in people:
        delay = 0 if (root, shoulders) == hero else rng.randint(0, 10)
        animate_celebration(root, shoulders, TOUCHDOWN_CALL + delay, f1, rng)

    # Slow push on one face, staring at the screens.
    hero_root = hero[0]
    face = hero_root.location + Vector((0, 0, 1.6))
    cam_push = add_camera("CAM_5a_push", lens=50.0, clip_end=200.0)
    # Stays between this row and the next, so no heads cross the lens.
    for frame, dist in ((f0, 3.3), (TOUCHDOWN_CALL + 8, 1.9)):
        cam_push.location = face + Vector((0.5, dist, 0.05))
        look_at(cam_push, face)
        cam_push.keyframe_insert("location", frame=frame)
        cam_push.keyframe_insert("rotation_euler", frame=frame)

    cam_wide = add_camera("CAM_5a_wide", lens=24.0, clip_end=200.0)
    cam_wide.location = (-13.5, -10.0, 5.5)
    look_at(cam_wide, (0.0, 2.0, 1.0))

    bind_camera(cam_push, f0, "5a push on face")
    bind_camera(cam_wide, TOUCHDOWN_CALL + 10, "5a wide: room erupts")
    add_marker("5a audio: Touchdown confirmed", TOUCHDOWN_CALL)
    add_marker("5a end", f1)
    save(scene, "shot_5a")


# ---------------------------------------------------------------- shot 5b

def settling_dust(rng, count, f_start, f_end, height, radius=(3, 14)):
    """Dust left from landing: hangs around the rover, then thins away."""
    for i in range(count):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(*radius)
        x, y = r * math.cos(a), r * math.sin(a)
        p = Vector((x, y, height(x, y) + rng.uniform(0.5, 2.0)))
        puff = blob(f"Rocketdust_{i:03d}", location=p)
        key_scale(puff, f_start, rng.uniform(2.5, 4.5))
        puff.keyframe_insert("location", frame=f_start)
        puff.location = p + Vector((rng.uniform(-2, 2), rng.uniform(1, 3),
                                    -0.4))
        puff.keyframe_insert("location", frame=f_end)
        key_scale(puff, f_end - rng.randint(0, 25), 0.0)


def build_shot_5b():
    """6-11s. First Hazcam frame: wheel, rocks, the rover's own shadow."""
    scene = new_scene(2785, 2904)
    f0, f1 = 2785, 2904
    ground, height = build_ground(rocks=True)
    rover = build_rover_landed(location=(0, 0, height(0, 0)))
    settling_dust(random.Random(51), 10, f0, f1, height, radius=(4, 12))

    # Front Hazcam: low on the body, looking ahead and down past the wheel.
    cam = add_camera("CAM_5b_hazcam", lens=12.0, clip_end=100000.0)
    cam.data.clip_start = 0.05
    cam.location = rover.location + Vector((1.05, -0.35, 0.68))
    look_at(cam, rover.location + Vector((5.0, -0.8, 0.0)))

    add_marker("5b comp: grainy B&W Hazcam", f0)
    add_marker("5b comp: sharp colour view", 2845)
    add_marker("5b end", f1)
    save(scene, "shot_5b")


# ---------------------------------------------------------------- shot 5c

def build_shot_5c():
    """11-20s. Dust settles; crane up and pull back to a dot. Fade out."""
    scene = new_scene(2905, 3120)
    f0, f1 = 2905, 3120
    ground, height = build_ground(rocks=True)
    floor = height(0, 0)
    build_rover_landed(location=(0, 0, floor))
    settling_dust(random.Random(52), 14, f0, 2990, height)

    target = Vector((0, 0, floor + 0.8))
    cam = add_camera("CAM_5c", lens=35.0, clip_end=200000.0)
    for frame in range(f0, f1 + 1, 3):
        t = (frame - f0) / (f1 - f0)
        k = smoothstep(t)
        dist = 6.0 * (900.0 / 6.0) ** (t ** 1.3)
        az = math.radians(-120 + 35 * k)
        el = math.radians(10 + 50 * k)
        cam.location = target + dist * Vector((math.cos(el) * math.cos(az),
                                               math.cos(el) * math.sin(az),
                                               math.sin(el)))
        look_at(cam, target)
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)

    add_marker("5c text: February 18, 2021. Touchdown confirmed.", 2930)
    add_marker("5c comp: fade out", 3080)
    add_marker("5c end card: Dare Mighty Things", f1)
    save(scene, "shot_5c")


build_shot_5a()
build_shot_5b()
build_shot_5c()
