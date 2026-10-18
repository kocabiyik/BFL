"""Build greybox layout scenes for Clip 4 ("7 Minutes of Terror").

Geometry, cameras and animation only: no materials, no lights, no shading
setup. Units are metres; Jezero is at real scale with the landing site at
the origin. Plasma and rocket dust are "Plasma_" / "Rocketdust_" blobs
that the EEVEE render turns into volumes.

Usage:
    blender -b --python blender/clip4/build_clip4.py

Writes shot_4a.blend ... shot_4e.blend next to this script. Frame numbers
are global to the film (clips.md): 4a = 1681-1872, 4b = 1873-2040,
4c = 2041-2184, 4d = 2185-2352, 4e = 2353-2640.
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

HEAT_SHIELD_SEP = 2055     # 4c
BACKSHELL_SEP = 2200       # 4d
ENGINES_ON = 2222          # 4d
TOUCHDOWN = 2520           # 4e
CABLE_CUT = 2545           # 4e


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


def build_descent_stage(parent=None, location=(0, 0, 0)):
    """Sky crane. Origin at the bottom centre of the body."""
    root = empty("Descent_Stage", location=location, parent=parent)
    lathe("DS_Body", [(0, 0), (1.0, 0), (1.0, 0.5), (0, 0.5)], segments=8,
          parent=root)
    for i in range(4):
        a = math.radians(45 + 90 * i)
        small_blob(f"DS_Tank_{i}", 0.34,
                   location=(0.6 * math.cos(a), 0.6 * math.sin(a), 0.75),
                   parent=root)
        x, y = 1.1 * math.cos(a), 1.1 * math.sin(a)
        box(f"DS_Pod_{i}", (0.45, 0.45, 0.4), location=(x, y, 0.05),
            parent=root).rotation_euler = (0, 0, a)
        for j, off in enumerate((-0.14, 0.14)):
            tx, ty = -math.sin(a) * off, math.cos(a) * off
            nozzle = lathe(f"DS_Engine_{i}_{j}", [(0.06, 0), (0.18, -0.45)],
                           segments=16, location=(x + tx, y + ty, 0.05),
                           parent=root)
            nozzle.rotation_euler = (0, math.radians(15), a)
    box("DS_Bridle", (0.4, 0.4, 0.15), location=(0, 0, -0.15), parent=root)
    return root


def build_entry_vehicle(parent=None):
    """Aeroshell with heat shield down (local -Z), rover and sky crane in."""
    root = empty("Entry_Vehicle", parent=parent)
    heat_shield = lathe("Heat_Shield",
                        [(0, -0.9), (1.0, -0.7), (2.25, 0.0), (0, 0.0)],
                        parent=root)
    backshell = empty("Backshell", parent=root)
    lathe("Backshell_Shell", [(2.25, 0.0), (2.25, 0.2), (0.8, 2.7),
                              (0.5, 2.7), (0.5, 3.4), (0, 3.4)],
          parent=backshell)
    pdv = empty("Powered_Descent_Vehicle", parent=root)
    rover = build_rover(parent=pdv, location=(0, 0, 0.02))
    stage = build_descent_stage(parent=pdv, location=(0, 0, 1.25))
    return root, heat_shield, backshell, pdv, rover, stage


def build_parachute(parent=None, location=(0, 0, 0)):
    """Disk-gap-band, 21.5 m. Origin at the line confluence, canopy +Z."""
    root = empty("Parachute", location=location, parent=parent)
    lathe("Canopy_Disk", [(0.6, 47.6), (3.0, 47.2), (6.0, 46.0),
                          (8.5, 44.9), (9.6, 44.3)], segments=80,
          parent=root)
    lathe("Canopy_Band", [(9.6, 43.5), (9.7, 40.0)], segments=80,
          parent=root)
    curve = bpy.data.curves.new("Suspension_Lines", type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.03
    curve.bevel_resolution = 0
    for i in range(32):
        a = 2 * math.pi * i / 32
        spline = curve.splines.new("POLY")
        spline.points.add(1)
        spline.points[0].co = (0, 0, 0, 1)
        spline.points[1].co = (9.7 * math.cos(a), 9.7 * math.sin(a), 40.0, 1)
    link(bpy.data.objects.new("Suspension_Lines", curve), root)
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
    base = jezero_raw(0.0, 0.0) + 3.0      # sits just under the local patch
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
        z = 0.0
        for bx, by, w, amp in bumps:
            z += amp * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (w * w))
        for cx, cy, size in pits:
            r = math.hypot(x - cx, y - cy) / size
            if r < 2.0:
                if r < 1.0:
                    z -= size * 0.2 * (1.0 - r * r)
                z += size * 0.06 * math.exp(-((r - 1.0) / 0.2) ** 2)
        return z

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


# ---------------------------------------------------------------- shot 4a

def build_shot_4a():
    """0-8s. Entry: aeroshell hits the atmosphere, plasma. Side tracking."""
    scene = new_scene(1681, 1872)
    f0, f1 = 1681, 1872

    root, heat_shield, *_ = build_entry_vehicle()
    vdir = Vector((1.0, 0.0, -0.27)).normalized()
    root.rotation_mode = "QUATERNION"
    # Heat shield into the flow, plus ~16 degrees angle of attack.
    q = Vector((0, 0, -1)).rotation_difference(vdir)
    root.rotation_quaternion = Quaternion((0, 1, 0), math.radians(-16)) @ q

    # Ground far below, sliding past: the craft stays at the origin.
    rng = random.Random(8)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=240, y_segments=240, size=500000.0)
    craters = [(rng.uniform(-500000, 500000), rng.uniform(-500000, 500000),
                rng.uniform(2000, 20000)) for _ in range(220)]
    for v in bm.verts:
        z = 0.0
        for cx, cy, size in craters:
            r = math.hypot(v.co.x - cx, v.co.y - cy) / size
            if r < 2.0:
                if r < 1.0:
                    z -= size * 0.12 * (1.0 - r * r)
                z += size * 0.04 * math.exp(-((r - 1.0) / 0.2) ** 2)
        v.co.z = z
    ground = finish_mesh("Mars_Surface", bm, sharp_angle=180)
    speed = 5400.0                          # ~19,500 km/h
    for frame in (f0, f1):
        t = (frame - f0) / 24.0
        ground.location = (-speed * vdir.x * t, 0.0,
                           -70000.0 - speed * vdir.z * t)
        ground.keyframe_insert("location", frame=frame)
    set_interpolation(ground, "LINEAR")

    # Plasma: glowing puffs peel off the heat shield rim and stream back,
    # stretched along the flow so neighbours overlap into one sheath.
    rim_world = root.rotation_quaternion
    along_flow = (-vdir).to_track_quat("Z", "Y").to_euler()
    n = 0
    for frame in range(1690, f1, 3):
        ramp = smoothstep((frame - 1690) / 70.0)
        for _ in range(2):
            a = rng.uniform(0, 2 * math.pi)
            local = Vector((2.3 * math.cos(a), 2.3 * math.sin(a), -0.1))
            start_pos = rim_world @ local
            side = (start_pos - vdir * start_pos.dot(vdir)).normalized()
            end_pos = start_pos - vdir * rng.uniform(10, 22) + \
                side * rng.uniform(0.5, 2.5)
            life = rng.randint(18, 26)
            puff = blob(f"Plasma_{n:03d}", location=start_pos)
            puff.rotation_euler = along_flow
            r0 = rng.uniform(1.0, 1.5) * (0.4 + 0.6 * ramp)
            r1 = rng.uniform(2.0, 2.8) * (0.3 + 0.7 * ramp)
            for f, r in ((frame, 0.0), (frame + life * 0.25, r0),
                         (frame + life, r1), (frame + life + 1, 0.0)):
                puff.scale = (r, r, r * 3.5)
                puff.keyframe_insert("scale", frame=f)
            puff.keyframe_insert("location", frame=frame)
            puff.location = end_pos
            puff.keyframe_insert("location", frame=frame + life)
            n += 1

    cam = add_camera("CAM_4a", lens=35.0, clip_end=2000000.0)
    cam.location = (-3.0, -15.0, 1.5)
    look_at(cam, (-4.0, 0.0, 0.0))
    cam.keyframe_insert("rotation_euler", frame=f0)
    cam.keyframe_insert("rotation_euler", frame=f1)
    add_shake(cam, 0.006, f0, 1740, 20, scale=2.0)
    add_shake(cam, 0.02, 1740, f1, 30, scale=1.2)

    add_marker("4a text: Entry. 19,500 km/h", 1700)
    add_marker("4a end", f1)
    save(scene, "shot_4a")


# ---------------------------------------------------------------- shot 4b

def build_shot_4b():
    """8-15s. Parachute fires and snaps open. Below, then hero orbit."""
    scene = new_scene(1873, 2040)
    f0, f1 = 1873, 2040
    ground, _ = build_ground(rocks=False)
    for frame, alt in ((f0, 11000.0), (f1, 10100.0)):
        ground.location = (0, 0, -alt)
        ground.keyframe_insert("location", frame=frame)
    set_interpolation(ground, "LINEAR")

    root, *_ = build_entry_vehicle()
    chute = build_parachute(parent=root, location=(0, 0, 3.4))
    mortar = 1885
    for frame, sxy, sz in ((f0, 0.02, 0.001), (mortar, 0.02, 0.001),
                           (1898, 0.035, 1.0), (1906, 1.12, 0.95),
                           (1914, 0.96, 1.0), (1920, 1.0, 1.0)):
        chute.scale = (sxy, sxy, sz)
        chute.keyframe_insert("scale", frame=frame)

    # Below, looking up the lines.
    cam_low = add_camera("CAM_4b_low", lens=24.0, clip_end=200000.0)
    cam_low.location = (7.0, -9.0, -22.0)
    look_at(cam_low, (0, 0, 28.0))
    cam_low.keyframe_insert("rotation_euler", frame=f0)
    cam_low.keyframe_insert("rotation_euler", frame=1955)
    add_shake(cam_low, 0.01, mortar, 1895, 2, scale=0.8)
    add_shake(cam_low, 0.035, 1904, 1930, 2, scale=0.8)

    # Hero orbit around the whole system, canopy pattern reveal.
    pivot = empty("CAM_4b_pivot", location=(0, 0, 26.0))
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=1956)
    pivot.rotation_euler = (0, 0, math.radians(100))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f1)
    set_interpolation(pivot, "LINEAR")
    cam_orbit = add_camera("CAM_4b_orbit", lens=28.0, clip_end=200000.0)
    cam_orbit.parent = pivot
    cam_orbit.location = (0.0, -82.0, -6.0)
    track = cam_orbit.constraints.new("TRACK_TO")
    track.target = pivot
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    bind_camera(cam_low, f0, "4b below")
    bind_camera(cam_orbit, 1956, "4b hero orbit")
    add_marker("4b mortar fires", mortar)
    add_marker("4b canopy open", 1906)
    add_marker("4b freeze: Dare Mighty Things", 1965)
    add_marker("4b end", f1)
    save(scene, "shot_4b")


# ---------------------------------------------------------------- shot 4c

def build_shot_4c():
    """15-21s. Heat shield drops; rover sees the ground. POV, then wide."""
    scene = new_scene(2041, 2184)
    f0, f1 = 2041, 2184
    ground, _ = build_ground(rocks=False)
    for frame, alt in ((f0, 8000.0), (f1, 7400.0)):
        ground.location = (0, 0, -alt)
        ground.keyframe_insert("location", frame=frame)
    set_interpolation(ground, "LINEAR")

    root, heat_shield, *_ = build_entry_vehicle()
    build_parachute(parent=root, location=(0, 0, 3.4))

    # Shield falls away faster than the craft under its chute, tumbling.
    for frame in range(f0, f1 + 1, 2):
        t = max(0.0, (frame - HEAT_SHIELD_SEP) / 24.0)
        heat_shield.location = (0.3 * t * t, 0, -0.5 * 12.0 * t * t)
        heat_shield.rotation_euler = (math.radians(7.0 * t * t), 0, 0)
        heat_shield.keyframe_insert("location", frame=frame)
        heat_shield.keyframe_insert("rotation_euler", frame=frame)
    set_interpolation(heat_shield, "LINEAR")

    # Rover POV: under the rover belly, looking straight down.
    cam_pov = add_camera("CAM_4c_rover_pov", lens=18.0, clip_end=200000.0)
    cam_pov.data.clip_start = 0.05
    cam_pov.location = (0.4, 0.0, 0.12)
    cam_pov.rotation_euler = (0, 0, math.radians(90))

    cam_wide = add_camera("CAM_4c_wide", lens=28.0, clip_end=200000.0)
    cam_wide.location = (30.0, -35.0, -14.0)
    look_at(cam_wide, (0, 0, 6.0))

    bind_camera(cam_pov, f0, "4c rover POV")
    bind_camera(cam_wide, 2112, "4c wide")
    add_marker("4c heat shield sep", HEAT_SHIELD_SEP)
    add_marker("4c scan overlay (comp)", 2070)
    add_marker("4c end", f1)
    save(scene, "shot_4c")


# ---------------------------------------------------------------- shot 4d

def build_shot_4d():
    """21-28s. Backshell separates, descent stage drops and lights up."""
    scene = new_scene(2185, 2352)
    f0, f1 = 2185, 2352
    ground, height = build_ground(rocks=True)

    root, heat_shield, backshell, pdv, rover, stage = build_entry_vehicle()
    heat_shield.hide_render = True          # already gone (4c)
    heat_shield.hide_viewport = True
    build_parachute(parent=backshell, location=(0, 0, 3.4))

    # The sky crane is tracked; backshell + chute fall behind and away.
    for frame in range(f0, f1 + 1, 2):
        t = max(0.0, (frame - BACKSHELL_SEP) / 24.0)
        free = min(t, 1.0)
        rise = 0.5 * 9.0 * free * free + 9.0 * max(0.0, t - 1.0) + \
            2.0 * max(0.0, t - 1.0) ** 2
        backshell.location = (-2.0 * t * t, 0.0, rise)
        backshell.keyframe_insert("location", frame=frame)
    set_interpolation(backshell, "LINEAR")

    # Ground rushes up from 2.1 km to 60 m.
    duration = (f1 - f0) / 24.0
    for frame in range(f0, f1 + 1, 2):
        t = (frame - f0) / 24.0
        k = (t / duration) ** 0.8
        alt = 2100.0 * (60.0 / 2100.0) ** k
        ground.location = (0, 0, -alt)
        ground.keyframe_insert("location", frame=frame)
    set_interpolation(ground, "LINEAR")

    # Dust starts lifting under the engines in the last second.
    rng = random.Random(13)
    n = 0
    for frame in range(f1 - 26, f1 + 1, 2):
        for _ in range(3):
            a = rng.uniform(0, 2 * math.pi)
            r0 = rng.uniform(5, 25)
            x, y = r0 * math.cos(a), r0 * math.sin(a)
            start = Vector((x, y, height(x, y) + 0.5))
            puff = blob(f"Rocketdust_{n:03d}", location=start, parent=ground)
            key_scale(puff, frame, 0.0)
            puff.keyframe_insert("location", frame=frame)
            out = Vector((math.cos(a), math.sin(a), 0))
            puff.location = start + out * rng.uniform(8, 20) + \
                Vector((0, 0, rng.uniform(1, 4)))
            puff.keyframe_insert("location", frame=frame + 30)
            key_scale(puff, frame + 30, rng.uniform(3, 6))
            n += 1

    cam = add_camera("CAM_4d", lens=28.0, clip_end=200000.0)
    cam.location = (9.0, -11.0, 1.5)
    look_at(cam, (0, 0, 0.5))
    cam.keyframe_insert("rotation_euler", frame=f0)
    cam.keyframe_insert("rotation_euler", frame=f1)
    add_shake(cam, 0.008, ENGINES_ON, f1, 10, scale=1.0)

    add_marker("4d backshell sep", BACKSHELL_SEP)
    add_marker("4d engines on", ENGINES_ON)
    add_marker("4d end", f1)
    save(scene, "shot_4d")


# ---------------------------------------------------------------- shot 4e

def build_shot_4e():
    """28-40s. Sky crane lowers the rover, touchdown, fly-away."""
    scene = new_scene(2353, 2640)
    f0, f1 = 2353, 2640
    ground, height = build_ground(rocks=True)
    floor = height(0.0, 0.0)

    stage = build_descent_stage()
    rover = build_rover()
    rover_height = 1.2                  # stowed rover at 0.85 scale
    cable_max = 6.4

    # Three bridle cables + umbilical, unit length, scaled to pay out.
    cables = []
    for i, (x, y) in enumerate(((0.5, 0.0), (-0.25, 0.43), (-0.25, -0.43),
                                (0.0, 0.0))):
        cable = lathe(f"Cable_{i}", [(0, 0), (0.015, 0), (0.015, -1.0),
                                     (0, -1.0)], segments=6,
                      location=(x, y, -0.15), parent=stage)
        cables.append(cable)

    def stage_z(frame):
        if frame <= 2440:
            t = (frame - f0) / (2440 - f0)
            return floor + 21.0 + (17.7 - 21.0) * smoothstep(t)
        if frame <= TOUCHDOWN:
            t = (frame - 2440) / (TOUCHDOWN - 2440)
            # Ease out hard: the last metre is the slow-motion beat.
            return floor + 17.7 + (7.7 + 0.05 - 17.7) * (1 - (1 - t) ** 2.5)
        return floor + 7.75

    def cable_len(frame):
        t = (frame - 2365) / (2440 - 2365)
        return 0.001 + cable_max * smoothstep(t)

    for frame in range(f0, CABLE_CUT + 1, 2):
        z = stage_z(frame)
        length = cable_len(frame)
        stage.location = (0, 0, z)
        stage.keyframe_insert("location", frame=frame)
        rover_z = max(floor, z - 0.15 - length - rover_height)
        rover.location = (0, 0, rover_z)
        rover.keyframe_insert("location", frame=frame)
        for cable in cables:
            cable.scale = (1, 1, z - 0.15 - rover_height - rover_z)
            cable.keyframe_insert("scale", frame=frame)

    # Cut: cables reel up, stage throttles up and flies off to the side.
    for cable in cables:
        cable.scale = (1, 1, 0.3)
        cable.keyframe_insert("scale", frame=CABLE_CUT + 12)
    start = Vector(stage.location)
    stage.rotation_euler = (0, 0, 0)
    stage.keyframe_insert("rotation_euler", frame=CABLE_CUT + 10)
    for frame in range(CABLE_CUT + 10, f1 + 1, 2):
        t = (frame - CABLE_CUT - 10) / 24.0
        stage.location = start + Vector((6.0 * t * t, 0.0,
                                         4.0 * t + 3.0 * t * t))
        stage.keyframe_insert("location", frame=frame)
    stage.rotation_euler = (0, math.radians(45), 0)
    stage.keyframe_insert("rotation_euler", frame=CABLE_CUT + 40)

    # Rocket dust: thrown out radially, heavier the lower the stage hangs,
    # settling away after its life so the frame doesn't fill with haze.
    rng = random.Random(17)
    n = 0
    for frame in range(f0, CABLE_CUT + 30, 4):
        z = stage_z(frame) - floor
        strength = max(0.3, min(1.0, 14.0 / max(z, 1.0)))
        a = rng.uniform(0, 2 * math.pi)
        r0 = rng.uniform(2, 6)
        x, y = r0 * math.cos(a), r0 * math.sin(a)
        p0 = Vector((x, y, height(x, y) + 0.4))
        puff = blob(f"Rocketdust_{n:03d}", location=p0)
        life = rng.randint(36, 60)
        key_scale(puff, frame, 0.0)
        puff.keyframe_insert("location", frame=frame)
        out = Vector((math.cos(a), math.sin(a), 0))
        puff.location = p0 + out * rng.uniform(15, 35) * strength + \
            Vector((0, 0, rng.uniform(0.5, 2.5)))
        puff.keyframe_insert("location", frame=frame + life)
        key_scale(puff, frame + life, rng.uniform(3.0, 6.0) * strength)
        key_scale(puff, frame + life + 40, 0.0)
        n += 1

    cam = add_camera("CAM_4e", lens=28.0, clip_end=200000.0)
    cam.location = (16.0, -20.0, floor + 1.0)
    # Aim follows the stage down, then tilts up after the fly-away.
    look_at(cam, (0, 0, floor + 12.0))
    cam.keyframe_insert("rotation_euler", frame=f0)
    look_at(cam, (0, 0, floor + 6.0))
    cam.keyframe_insert("rotation_euler", frame=2480)
    cam.keyframe_insert("rotation_euler", frame=CABLE_CUT + 10)
    look_at(cam, (25.0, 0, floor + 30.0))
    cam.keyframe_insert("rotation_euler", frame=f1)

    add_marker("4e text: Sky crane", 2360)
    add_marker("4e cables pay out", 2365)
    add_marker("4e silence (audio)", 2500)
    add_marker("4e touchdown", TOUCHDOWN)
    add_marker("4e cables cut", CABLE_CUT)
    add_marker("4e end", f1)
    save(scene, "shot_4e")


build_shot_4a()
build_shot_4b()
build_shot_4c()
build_shot_4d()
build_shot_4e()
