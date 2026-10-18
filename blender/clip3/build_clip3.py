"""Build greybox layout scenes for Clip 3 ("The Long Dark").

Geometry, cameras and animation only: no materials, no lights, no shading
setup. Thruster puffs are "Steam_" blobs that the EEVEE render turns into
volumes.

Usage:
    blender -b --python blender/clip3/build_clip3.py

Writes shot_3a.blend, shot_3b.blend and shot_3c.blend next to this script.
Frame numbers are global to the film (docs/clips.md): 3a = 1081-1320,
3b = 1321-1488, 3c = 1489-1680.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

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

AU = 100.0                 # 3a scene scale: 1 AU = 100 units
DAYS = 203                 # Jul 30 2020 -> Feb 18 2021
KM_TOTAL = 470_000_000
CRUISE_SEP = 1610          # 3c: cruise stage separation frame

COUNTER_SCRIPT = '''\
"""Drives the 3a distance/day counter. Runs at render time, and in the
viewport when auto-run scripts is enabled."""
import bpy


def update_counter(scene, *_):
    km = scene.objects.get("Counter_km")
    day = scene.objects.get("Counter_days")
    if km is None or day is None:
        return
    f0, f1 = scene["counter_f0"], scene["counter_f1"]
    t = max(0.0, min(1.0, (scene.frame_current - f0) / (f1 - f0)))
    p = t * t * (3 - 2 * t)
    km.data.body = f"{p * scene['counter_km']:,.0f} km"
    day.data.body = f"Day {round(p * scene['counter_days'])}"


bpy.app.handlers.frame_change_pre[:] = [
    h for h in bpy.app.handlers.frame_change_pre
    if getattr(h, "__name__", "") != "update_counter"]
bpy.app.handlers.frame_change_pre.append(update_counter)
update_counter(bpy.context.scene)
'''


def text_object(name, body, size, location, parent):
    data = bpy.data.curves.new(name, type="FONT")
    data.body = body
    data.size = size
    obj = link(bpy.data.objects.new(name, data), parent)
    obj.location = location
    return obj


def orbit_curve(name, points, bevel):
    curve = bpy.data.curves.new(name, type="CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (co.x, co.y, co.z, 1.0)
    return link(bpy.data.objects.new(name, curve)), curve, spline


def planet(name, radius, subdivisions=5, seed=1, pits=40):
    """Ico sphere with a few swells and craters so it reads as a body."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=radius)
    rng = random.Random(seed)

    def rand_dir():
        return Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                       rng.uniform(-1, 1))).normalized()

    swells = [(rand_dir(), rng.uniform(0.2, 0.5), rng.uniform(-0.006, 0.008))
              for _ in range(14)]
    craters = [(rand_dir(), rng.uniform(0.02, 0.07)) for _ in range(pits)]
    for v in bm.verts:
        n = v.co.normalized()
        h = 0.0
        for d, width, amp in swells:
            h += amp * math.exp(-(n.angle(d) / width) ** 2)
        for d, size in craters:
            ang = n.angle(d)
            if ang < size * 2.0:
                r = ang / size
                if r < 1.0:
                    h -= size * 0.13 * (1.0 - r * r)
                h += size * 0.045 * math.exp(-((r - 1.0) / 0.18) ** 2)
        v.co = n * radius * (1.0 + h)
    return finish_mesh(name, bm, sharp_angle=180)


def build_mars2020(parent=None, panels=True):
    """Cruise configuration, heat shield along local +Z.

    Returns (root, cruise_stage, thruster_positions_local)."""
    root = empty("Mars2020", parent=parent)
    cruise = empty("Cruise_Stage", parent=root)
    lathe("Cruise_Stage_Body", [(0, 0), (2.0, 0), (2.0, 0.7), (0, 0.7)],
          parent=cruise)
    if panels:
        # Solar array ring on the outward (-Z) face, 10 wedge panels.
        for i in range(10):
            a0 = math.radians(i * 36 + 1.5)
            a1 = math.radians((i + 1) * 36 - 1.5)
            lathe(f"Solar_Panel_{i}", [(0.95, -0.03), (1.95, -0.03)],
                  segments=6, a0=a0, a1=a1, parent=cruise)
        lathe("Radiator_Ring", [(2.0, 0.05), (2.25, 0.05), (2.25, 0.6),
                                (2.0, 0.6)], segments=48, parent=cruise)
    thrusters = []
    for i in range(8):
        a = math.radians(i * 45 + 22.5)
        pos = Vector((2.3 * math.cos(a), 2.3 * math.sin(a), 0.35))
        cone = lathe(f"Thruster_{i}", [(0, 0), (0.07, 0), (0.14, 0.28)],
                     segments=12, location=pos, parent=cruise)
        cone.rotation_euler = (0, math.radians(90), a)
        thrusters.append(pos)

    aeroshell = empty("Aeroshell", parent=root)
    lathe("Backshell", [(0, 0.7), (0.8, 0.7), (2.25, 3.2), (2.25, 3.4),
                        (0, 3.4)], parent=aeroshell)
    lathe("Heat_Shield", [(2.25, 3.4), (1.0, 4.1), (0, 4.3)],
          parent=aeroshell)
    return root, cruise, thrusters


# ---------------------------------------------------------------- shot 3a

def transfer_point(nu, theta0):
    """Point on the Earth->Mars transfer ellipse, nu = true anomaly."""
    r_p, r_a = 1.0 * AU, 1.524 * AU
    a = (r_p + r_a) / 2
    e = (r_a - r_p) / (r_a + r_p)
    r = a * (1 - e * e) / (1 + e * math.cos(nu))
    return Vector((r * math.cos(theta0 + nu), r * math.sin(theta0 + nu), 0))


def build_shot_3a():
    """0-10s. Top-down solar system, path draws Earth -> Mars, counter."""
    scene = new_scene(1081, 1320)
    f0, f1 = 1105, 1300            # cruise plays out between these frames

    theta_launch = math.radians(200)                  # Earth at launch
    theta_arrive = theta_launch + math.pi             # Mars at arrival
    earth_rate = math.radians(0.9856) * DAYS          # sweep during cruise
    mars_rate = math.radians(0.524) * DAYS

    sphere("Sun", radius=10.0)
    earth = sphere("Earth", radius=3.0)
    mars = sphere("Mars", radius=2.4)
    craft = sphere("Spacecraft_Marker", radius=1.2)

    circle = [Vector((math.cos(a), math.sin(a), 0))
              for a in (2 * math.pi * i / 256 for i in range(257))]
    orbit_curve("Earth_Orbit", [c * AU for c in circle], 0.3)
    orbit_curve("Mars_Orbit", [c * 1.524 * AU for c in circle], 0.3)

    nus = [math.pi * i / 300 for i in range(301)]
    pts = [transfer_point(nu, theta_launch) for nu in nus]
    lengths = [0.0]
    for a, b in zip(pts, pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    _, path, _ = orbit_curve("Transfer_Path", pts, 0.7)
    path.bevel_factor_mapping_end = "SPLINE"

    for frame in range(1081, 1321, 2):
        t = max(0.0, min(1.0, (frame - f0) / (f1 - f0)))
        p = smoothstep(t)
        ea = theta_launch + earth_rate * p
        ma = theta_arrive - mars_rate * (1 - p)
        earth.location = (AU * math.cos(ea), AU * math.sin(ea), 0)
        mars.location = (1.524 * AU * math.cos(ma),
                         1.524 * AU * math.sin(ma), 0)
        i = round(p * 300)
        craft.location = pts[i]
        path.bevel_factor_end = max(1e-4, lengths[i] / lengths[-1])
        for obj in (earth, mars, craft):
            obj.keyframe_insert("location", frame=frame)
        path.keyframe_insert("bevel_factor_end", frame=frame)

    # Slow rotation of the whole view.
    pivot = empty("CAM_3a_pivot")
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=1081)
    pivot.rotation_euler = (0, 0, math.radians(25))
    pivot.keyframe_insert("rotation_euler", index=2, frame=1320)
    set_interpolation(pivot, "LINEAR")
    cam = add_camera("CAM_3a", lens=35.0, clip_end=2000.0)
    cam.parent = pivot
    cam.location = (0.0, 0.0, 600.0)
    cam.rotation_euler = (0, 0, 0)

    # Counter rides on the camera, lower left of frame.
    text_object("Counter_km", "0 km", 0.32, (-4.7, -2.3, -10.0), cam)
    text_object("Counter_days", "Day 0", 0.32, (-4.7, -2.75, -10.0), cam)
    scene["counter_f0"] = f0
    scene["counter_f1"] = f1
    scene["counter_km"] = KM_TOTAL
    scene["counter_days"] = DAYS
    script = bpy.data.texts.new("counter.py")
    script.write(COUNTER_SCRIPT)
    script.use_module = True

    add_marker("3a cruise begins", f0)
    add_marker("3a arrival", f1)
    add_marker("3a end", 1320)
    save(scene, "shot_3a")


# ---------------------------------------------------------------- shot 3b

def build_shot_3b():
    """10-17s. Close on spacecraft, panels catch the sun, thruster puffs."""
    scene = new_scene(1321, 1488)
    root, cruise, thrusters = build_mars2020()

    # Spin-stabilised at about 2 rpm.
    f0, f1 = 1321, 1488
    spin_total = math.radians(12.0 * (f1 - f0) / 24.0)
    root.rotation_euler = (0, 0, 0)
    root.keyframe_insert("rotation_euler", index=2, frame=f0)
    root.rotation_euler = (0, 0, spin_total)
    root.keyframe_insert("rotation_euler", index=2, frame=f1)
    set_interpolation(root, "LINEAR")

    # Course-correction burns: opposite thruster pairs fire short pulses.
    rng = random.Random(4)
    n = 0
    for fire, pair in ((1385, (1, 5)), (1395, (1, 5)), (1440, (3, 7))):
        spin = spin_total * (fire - f0) / (f1 - f0)
        for k in pair:
            local = thrusters[k]
            c, s = math.cos(spin), math.sin(spin)
            world = Vector((local.x * c - local.y * s,
                            local.x * s + local.y * c, local.z))
            out = Vector((world.x, world.y, 0)).normalized()
            for j in range(3):
                start = fire + j * 2
                life = rng.randint(16, 24)
                puff = blob(f"Steam_Thruster_{n:02d}", location=world)
                key_scale(puff, start, 0.0)
                puff.keyframe_insert("location", frame=start)
                key_scale(puff, start + life * 0.35, rng.uniform(0.35, 0.55))
                puff.location = world + out * rng.uniform(2.5, 4.0) + \
                    Vector((0, 0, rng.uniform(-0.4, 0.4)))
                puff.keyframe_insert("location", frame=start + life)
                key_scale(puff, start + life, 0.0)
                n += 1

    pivot = empty("CAM_3b_pivot", location=(0, 0, 1.8))
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=f0)
    pivot.rotation_euler = (0, 0, math.radians(55))
    pivot.keyframe_insert("rotation_euler", index=2, frame=f1)
    set_interpolation(pivot, "LINEAR")
    cam = add_camera("CAM_3b", lens=35.0, clip_end=500.0)
    cam.parent = pivot
    cam.location = (0.0, -11.0, -3.5)
    track = cam.constraints.new("TRACK_TO")
    track.target = pivot
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    add_marker("3b burn", 1385)
    add_marker("3b burn", 1440)
    add_marker("3b end", f1)
    save(scene, "shot_3b")


# ---------------------------------------------------------------- shot 3c

def build_shot_3c():
    """17-25s. Behind the craft; Mars grows from a dot. Cruise stage drops."""
    scene = new_scene(1489, 1680)
    f0, f1 = 1489, 1680

    # Heat shield faces Mars (+Y). ZYX order: spin about the craft axis
    # first, then tip that axis onto +Y.
    root, cruise, _ = build_mars2020()
    root.rotation_mode = "ZYX"
    for frame in (f0, f1):
        spin = math.radians(12.0 * (frame - f0) / 24.0)
        root.rotation_euler = (math.radians(-90), 0, spin)
        root.keyframe_insert("rotation_euler", frame=frame)
    set_interpolation(root, "LINEAR")

    # Cruise stage separation: backs off toward camera, drifts, tumbles.
    for frame, loc, rot in ((f0, (0, 0, 0), (0, 0, 0)),
                            (CRUISE_SEP, (0, 0, 0), (0, 0, 0)),
                            (f1, (-3.0, 1.0, -4.5), (25, 10, 0))):
        cruise.location = loc
        cruise.rotation_euler = [math.radians(a) for a in rot]
        cruise.keyframe_insert("location", frame=frame)
        cruise.keyframe_insert("rotation_euler", frame=frame)

    # Mars approaches: log-spaced distance so the dot keeps swelling.
    # Mars sits right of the craft along the camera's line of sight, so the
    # craft frames lower left and never hides the dot.
    cam = add_camera("CAM_3c", lens=35.0, clip_end=400000.0)
    cam.data.clip_start = 0.5
    cam.location = (3.0, -18.0, 2.0)
    ahead = Vector((0.15, 1.0, 0.08)).normalized()
    look_at(cam, cam.location + ahead * 1000.0)

    mars = planet("Mars", radius=300.0, subdivisions=6, seed=7)
    d0, d1 = 300000.0, 640.0
    for frame in range(f0, f1 + 1, 4):
        t = (frame - f0) / (f1 - f0)
        k = t ** 1.6
        mars.location = cam.location + ahead * (d0 * (d1 / d0) ** k)
        mars.keyframe_insert("location", frame=frame)
    set_interpolation(mars, "LINEAR")

    add_marker("3c cruise stage sep", CRUISE_SEP)
    add_marker("3c end", f1)
    save(scene, "shot_3c")


build_shot_3a()
build_shot_3b()
build_shot_3c()
