"""Build greybox layout scenes for Clip 1 ("The Question").

Geometry, cameras and animation only: no materials, no lights, no shading
setup. Every file renders with Workbench in its default solid look, i.e.
exactly what the viewport shows.

Usage:
    blender -b --python blender/clip1/build_clip1.py

Writes shot_1a.blend, shot_1b.blend and shot_1c.blend next to this script.
Frame numbers are global to the film (docs/clips.md): 1a = 1-144,
1b = 145-336, 1c = 337-480.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Vector

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

MARS_RADIUS = 10.0
# Jezero on the globe, enlarged for readability (scale cheat, see docs/clips.md).
CRATER_DIR = Vector((0.25, -1.0, 0.35)).normalized()
CRATER_ANGLE = 0.06  # angular radius in radians -> ~0.6 units on the globe


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


def add_camera(name, lens=50.0, clip_end=1000.0):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.clip_start = 0.01
    data.clip_end = clip_end
    cam = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def look_at(obj, target, roll=0.0):
    direction = Vector(target) - obj.location
    quat = direction.to_track_quat("-Z", "Y")
    obj.rotation_euler = quat.to_euler()
    obj.rotation_euler.rotate_axis("Z", roll)


def mesh_object(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def set_interpolation(obj, interp):
    action = obj.animation_data.action if obj.animation_data else None
    if action is None:
        return
    # Blender 5 layered actions keep F-curves in channelbags.
    curves = []
    if hasattr(action, "layers") and action.layers:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    curves.extend(bag.fcurves)
    else:
        curves = action.fcurves
    for fc in curves:
        for kp in fc.keyframe_points:
            kp.interpolation = interp


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


# ---------------------------------------------------------------- Mars

def build_mars(crater=False):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=7, radius=MARS_RADIUS)

    rng = random.Random(7)
    # A handful of broad highland swells so the limb isn't a perfect circle.
    swells = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                       rng.uniform(-1, 1))).normalized(),
               rng.uniform(0.2, 0.5), rng.uniform(-0.06, 0.08))
              for _ in range(14)]
    # Generic small craters scattered over the globe.
    pits = [(Vector((rng.uniform(-1, 1), rng.uniform(-1, 1),
                     rng.uniform(-1, 1))).normalized(),
             rng.uniform(0.02, 0.07), 1.3)
            for _ in range(60)]
    if crater:
        pits.append((CRATER_DIR, CRATER_ANGLE, 2.5))

    for v in bm.verts:
        n = v.co.normalized()
        h = 0.0
        for d, width, amp in swells:
            ang = n.angle(d)
            h += amp * math.exp(-(ang / width) ** 2)
        for d, size, depth_ratio in pits:
            ang = n.angle(d)
            if ang > size * 2.0:
                continue
            r = ang / size
            depth = size * depth_ratio
            if r < 1.0:
                h -= depth * (1.0 - r * r)
            h += depth * 0.35 * math.exp(-((r - 1.0) / 0.18) ** 2)
        v.co = n * (MARS_RADIUS + h)

    obj = mesh_object("Mars", bm)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


# ---------------------------------------------------------------- shot 1a

def build_shot_1a():
    """0-6s. Mars fades in from black, half lit. Static wide, slow push in."""
    scene = new_scene(1, 144)
    build_mars()

    cam = add_camera("CAM_1a", lens=50.0)
    for frame, dist in ((1, 55.0), (144, 45.0)):
        cam.location = (0.0, -dist, 0.0)
        look_at(cam, (0, 0, 0))
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)
    set_interpolation(cam, "LINEAR")

    add_marker("1a fade-in (comp)", 1)
    add_marker("1a end", 144)
    save(scene, "shot_1a")


# ---------------------------------------------------------------- shot 1b

def build_shot_1b():
    """6-14s. Dive toward the surface through dust; Jezero appears."""
    scene = new_scene(145, 336)
    build_mars(crater=True)

    crater_pt = CRATER_DIR * MARS_RADIUS
    start = Vector((0.0, -45.0, 0.0))     # where 1a ends
    end = crater_pt + CRATER_DIR * 3.2    # high enough to frame the rim

    # Dust clouds: clusters of blobs the camera punches through near the end.
    rng = random.Random(3)
    side = CRATER_DIR.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(CRATER_DIR).normalized()
    for i in range(9):
        alt = rng.uniform(3.6, 5.5)
        off = side * rng.uniform(-1.5, 1.5) + up * rng.uniform(-1.0, 1.0)
        center = crater_pt + CRATER_DIR * alt + off
        bm = bmesh.new()
        for _ in range(rng.randint(5, 9)):
            blob = bmesh.ops.create_icosphere(
                bm, subdivisions=2, radius=rng.uniform(0.25, 0.6))
            jitter = Vector((rng.uniform(-0.6, 0.6), rng.uniform(-0.6, 0.6),
                             rng.uniform(-0.3, 0.3)))
            bmesh.ops.translate(bm, verts=blob["verts"], vec=jitter)
        obj = mesh_object(f"Dust_{i:02d}", bm)
        obj.location = center
        obj.rotation_euler = CRATER_DIR.to_track_quat("Z", "Y").to_euler()
        for poly in obj.data.polygons:
            poly.use_smooth = True
        # Dust only exists for the wipe; hidden from orbit.
        for frame, hidden in ((145, True), (285, False)):
            obj.hide_render = hidden
            obj.hide_viewport = hidden
            obj.keyframe_insert("hide_render", frame=frame)
            obj.keyframe_insert("hide_viewport", frame=frame)

    cam = add_camera("CAM_1b", lens=50.0)
    f0, f1 = 145, 336
    for frame in range(f0, f1 + 1, 4):
        t = (frame - f0) / (f1 - f0)
        # Accelerate in, settle at the end.
        k = smoothstep(t) ** 1.6
        # Swing around the globe on an arc, not a straight line.
        start_dir = start.normalized()
        dir_now = start_dir.slerp(CRATER_DIR, smoothstep(t)) \
            if start_dir.angle(CRATER_DIR) > 1e-6 else CRATER_DIR
        dist = start.length + (end.length - start.length) * k
        cam.location = dir_now * dist
        target = Vector((0, 0, 0)).lerp(crater_pt, smoothstep(t * 1.4))
        look_at(cam, target, roll=math.radians(15.0) * smoothstep(t))
        cam.keyframe_insert("location", frame=frame)
        cam.keyframe_insert("rotation_euler", frame=frame)

    add_marker("1b dust wipe", 300)
    add_marker("1b end", 336)
    save(scene, "shot_1b")


# ---------------------------------------------------------------- shot 1c

def build_shot_1c():
    """14-20s. Overhead orbit of Jezero; ghost lake fills and drains."""
    scene = new_scene(337, 480)

    R = 40.0          # crater radius
    DEPTH = 3.0
    RIM = 1.5
    SIZE = 320.0

    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=560, y_segments=560, size=SIZE / 2)
    rng = random.Random(11)
    bumps = [(Vector((rng.uniform(-100, 100), rng.uniform(-100, 100), 0)),
              rng.uniform(4, 15), rng.uniform(-0.6, 0.6)) for _ in range(80)]
    pits = [(Vector((rng.uniform(-100, 100), rng.uniform(-100, 100), 0)),
             rng.uniform(1.0, 4.0)) for _ in range(40)]

    for v in bm.verts:
        p = Vector((v.co.x, v.co.y, 0))
        r = p.length / R
        z = 0.0
        # Jezero bowl + raised rim.
        if r < 1.0:
            z -= DEPTH * (1.0 - r ** 4)
        z += RIM * math.exp(-((r - 1.0) / 0.12) ** 2)

        # Neretva Vallis: inlet channel from the west, through the rim.
        if v.co.x < -R * 0.75:
            wobble = 2.5 * math.sin(v.co.x * 0.12)
            d = abs(v.co.y - 6.0 - wobble)
            z -= 1.4 * math.exp(-(d / 1.6) ** 2)

        # Western delta fan: lobed deposit just inside the rim.
        fan_origin = Vector((-R * 0.88, 6.0, 0))
        q = p - fan_origin
        if q.x > 0:
            ang = math.atan2(q.y, q.x)
            reach = 14.0 * (1.0 + 0.18 * math.cos(ang * 7.0))
            fr = q.length / reach
            if fr < 1.0 and abs(ang) < 1.2:
                z += 1.6 * (1.0 - fr ** 2) * math.cos(ang * 0.6)

        # Pilot Valles: smaller outlet to the east.
        if v.co.x > R * 0.85:
            d = abs(v.co.y + 3.0 + 1.5 * math.sin(v.co.x * 0.15))
            z -= 0.9 * math.exp(-(d / 1.2) ** 2)

        for c, width, amp in bumps:
            z += amp * math.exp(-((p - c).length / width) ** 2)
        for c, size in pits:
            pr = (p - c).length / size
            if pr < 2.0:
                if pr < 1.0:
                    z -= size * 0.25 * (1.0 - pr * pr)
                z += size * 0.08 * math.exp(-((pr - 1.0) / 0.2) ** 2)
        v.co.z = z

    terrain = mesh_object("Jezero_Terrain", bm)
    for poly in terrain.data.polygons:
        poly.use_smooth = True

    # Ghost lake: flat disc animated in Z only (alpha fade is a shading job,
    # left for the lookdev pass).
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=128, radius=R * 1.02)
    lake = mesh_object("Ghost_Lake", bm)
    for frame, z in ((337, -DEPTH - 0.5), (345, -DEPTH - 0.5),
                     (390, -0.4), (430, -0.4), (470, -DEPTH - 0.5)):
        lake.location.z = z
        lake.keyframe_insert("location", index=2, frame=frame)
    set_interpolation(lake, "BEZIER")

    # Slow overhead orbit: camera on a rotating pivot, aimed at the crater.
    pivot = bpy.data.objects.new("CAM_1c_pivot", None)
    scene.collection.objects.link(pivot)
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=337)
    pivot.rotation_euler = (0, 0, math.radians(40))
    pivot.keyframe_insert("rotation_euler", index=2, frame=480)
    set_interpolation(pivot, "LINEAR")

    cam = add_camera("CAM_1c", lens=35.0)
    cam.parent = pivot
    cam.location = (0.0, -80.0, 125.0)
    track = cam.constraints.new("TRACK_TO")
    track.target = pivot
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"

    add_marker("1c lake rises", 345)
    add_marker("1c lake full", 390)
    add_marker("1c lake drains", 430)
    add_marker("1c end", 480)
    save(scene, "shot_1c")


build_shot_1a()
build_shot_1b()
build_shot_1c()
