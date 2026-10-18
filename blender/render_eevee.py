"""Render a shot to MP4 with EEVEE.

Adds one white sun at render time (no materials) and leaves the .blend
untouched.

Usage:
    blender -b blender/clip1/shot_1a.blend --python blender/render_eevee.py
"""

import math
import os

import bpy
from mathutils import Vector

# Direction the light travels, per shot. 1a/1b light Mars from +X so the
# globe is half lit from the camera; 1c rakes Jezero low from the east.
SUN_DIRECTION = {
    "shot_1a": Vector((-1.0, 0.0, 0.0)),
    "shot_1b": Vector((-1.0, 0.0, 0.0)),
    "shot_1c": Vector((-1.0, 0.3, -math.tan(math.radians(25)))),
    # Dawn at the Cape: low sun from the east (+X).
    "shot_2a": Vector((-1.0, 0.25, -math.tan(math.radians(12)))),
    "shot_2b": Vector((-1.0, 0.25, -math.tan(math.radians(12)))),
    "shot_2c": Vector((-1.0, 0.25, -math.tan(math.radians(15)))),
    "shot_2d": Vector((-1.0, 0.3, -0.2)),
    # 3a is seen from straight above: light from the camera side.
    "shot_3a": Vector((0.0, 0.0, -1.0)),
    # 3b: side light, rising slightly to catch the -Z solar array.
    "shot_3b": Vector((-1.0, 0.4, 0.45)),
    "shot_3c": Vector((-1.0, 0.35, -0.2)),
    # Clip 4: mid-morning sun over Jezero.
    "shot_4a": Vector((-0.5, 0.6, -0.6)),
    "shot_4b": Vector((-0.6, 0.5, -0.6)),
    "shot_4c": Vector((-0.6, 0.5, -0.6)),
    "shot_4d": Vector((-0.6, 0.5, -0.6)),
    "shot_4e": Vector((-0.6, 0.5, -0.6)),
    # Mission control has no ceiling: light falls in from above.
    "shot_5a": Vector((0.25, 0.35, -1.0)),
    # Sun behind the rover throws its shadow ahead into the Hazcam view.
    "shot_5b": Vector((1.0, 0.25, -0.45)),
    # Late afternoon: low sun, long shadows.
    "shot_5c": Vector((1.0, 0.4, -0.18)),
}

# Flat grey sky for the ground shots so daylight doesn't read as night.
WORLD_COLOR = {
    "shot_2a": (0.25, 0.25, 0.25, 1.0),
    "shot_2b": (0.25, 0.25, 0.25, 1.0),
    "shot_2c": (0.25, 0.25, 0.25, 1.0),
    "shot_4b": (0.25, 0.25, 0.25, 1.0),
    "shot_4c": (0.25, 0.25, 0.25, 1.0),
    "shot_4d": (0.25, 0.25, 0.25, 1.0),
    "shot_4e": (0.25, 0.25, 0.25, 1.0),
    "shot_5a": (0.25, 0.25, 0.25, 1.0),
    "shot_5b": (0.25, 0.25, 0.25, 1.0),
    "shot_5c": (0.25, 0.25, 0.25, 1.0),
}

scene = bpy.context.scene
name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 4.0
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = SUN_DIRECTION[name].normalized().to_track_quat("-Z", "Y").to_euler()

# 1b dust is only a wipe; its shadows read as black holes on the surface.
for obj in scene.objects if name == "shot_1b" else []:
    if obj.name.startswith("Dust_"):
        obj.visible_shadow = False
        # Gone once the wipe is through, so the end frame shows only Jezero.
        obj.hide_render = True
        obj.keyframe_insert("hide_render", frame=318)

# At grazing sun the globe's facets shadow themselves into black blotches
# around Jezero; normal falloff alone gives the half-lit look.
mars = scene.objects.get("Mars")
if mars:
    mars.visible_shadow = False

# Smoke, steam and dust render as volumes instead of solid blobs. Each blob
# becomes a unit sphere container (scaled to its old size) holding noisy
# density that fades to zero at the rim, so overlapping blobs merge into
# one cloud. Density is per unit length, so big smoke blobs get less.
VOLUME_DENSITY = {"Dust_": 3.0, "Steam_": 12.0, "Smoke_": 0.5,
                  "Trail_": 1.5, "Plasma_": 2.0, "Rocketdust_": 0.8}
# Self-glow per unit density; entry plasma burns bright.
VOLUME_GLOW = {"Plasma_": 3.0}
VOLUME_RANGE = {"shot_1b": (0.05, 30.0), "shot_2a": (0.5, 200.0),
                "shot_2b": (1.0, 450.0),
                "shot_2c": (4900.0, 5900.0),   # trail is ~5.3 km from camera
                "shot_3b": (0.5, 60.0),
                "shot_4a": (1.0, 80.0),
                "shot_4d": (1.0, 300.0),
                "shot_4e": (0.5, 200.0),
                "shot_5b": (0.05, 40.0),
                "shot_5c": (0.5, 200.0)}
# Depth slices: 2c needs fine slices or its thin trail puffs alias.
VOLUME_SAMPLES = {"shot_2c": 96}
# Coarser cells where hundreds of puffs would otherwise crawl.
VOLUME_TILE = {"shot_4a": "8", "shot_4e": "8"}


def volume_material(name, density, glow_amount=0.35):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    # Pure scattering, no absorption: exhaust and steam read bright white.
    vol.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    vol.inputs["Absorption Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    # A little self-glow stands in for the bounce light that keeps real
    # exhaust clouds white; scaled with density so thin wisps stay faint.
    vol.inputs["Emission Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    vol.inputs["Emission Strength"].default_value = 0.0
    vol.inputs["Anisotropy"].default_value = 0.2
    coords = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.6
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.6
    shape = nt.nodes.new("ShaderNodeMapRange")       # noise -> wisps
    shape.inputs["From Min"].default_value = 0.42
    shape.inputs["From Max"].default_value = 0.72
    length = nt.nodes.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    rim = nt.nodes.new("ShaderNodeMapRange")         # fade out at radius 1
    rim.interpolation_type = "SMOOTHSTEP"
    rim.inputs["From Min"].default_value = 0.35
    rim.inputs["From Max"].default_value = 1.0
    rim.inputs["To Min"].default_value = 1.0
    rim.inputs["To Max"].default_value = 0.0
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    amount = nt.nodes.new("ShaderNodeMath")
    amount.operation = "MULTIPLY"
    amount.inputs[1].default_value = density
    links = nt.links
    links.new(coords.outputs["Object"], noise.inputs["Vector"])
    links.new(coords.outputs["Object"], length.inputs[0])
    links.new(noise.outputs["Fac"], shape.inputs["Value"])
    links.new(length.outputs["Value"], rim.inputs["Value"])
    links.new(shape.outputs["Result"], mul.inputs[0])
    links.new(rim.outputs["Result"], mul.inputs[1])
    links.new(mul.outputs["Value"], amount.inputs[0])
    links.new(amount.outputs["Value"], vol.inputs["Density"])
    glow = nt.nodes.new("ShaderNodeMath")
    glow.operation = "MULTIPLY"
    glow.inputs[1].default_value = glow_amount
    links.new(amount.outputs["Value"], glow.inputs[0])
    links.new(glow.outputs["Value"], vol.inputs["Emission Strength"])
    links.new(vol.outputs["Volume"], out.inputs["Volume"])
    return mat


container = None
for prefix, density in VOLUME_DENSITY.items():
    objs = [o for o in scene.objects
            if o.type == "MESH" and o.name.startswith(prefix)]
    if not objs:
        continue
    if container is None:
        import bmesh
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
        container = bpy.data.meshes.new("Volume_Container")
        bm.to_mesh(container)
        bm.free()
        container.materials.append(None)
    mat = volume_material(f"Volume_{prefix.rstrip('_')}", density,
                          VOLUME_GLOW.get(prefix, 0.35))
    for obj in objs:
        # Dust clusters are many blobs in one mesh: wrap them in one sphere.
        # Smoke/steam blobs are already unit spheres with animated scale.
        radius = max(v.co.length for v in obj.data.vertices)
        if obj.animation_data is None:
            obj.scale = obj.scale * radius
        obj.data = container
        obj.material_slots[0].link = "OBJECT"
        obj.material_slots[0].material = mat
        obj.visible_shadow = True

if container is not None:
    eevee_settings = scene.eevee
    start, end = VOLUME_RANGE.get(name, (0.1, 100.0))
    eevee_settings.volumetric_start = start
    eevee_settings.volumetric_end = end
    eevee_settings.volumetric_tile_size = VOLUME_TILE.get(name, "4")
    eevee_settings.volumetric_samples = VOLUME_SAMPLES.get(name, 48)
    # Self-shadowing turns thick clouds near-black under a low sun.
    if hasattr(eevee_settings, "use_volumetric_shadows"):
        eevee_settings.use_volumetric_shadows = False

# 3a's distance/day counter: the build stores its handler in the file.
counter = bpy.data.texts.get("counter.py")
if counter is not None:
    scene.render.use_lock_interface = True
    exec(compile(counter.as_string(), "counter.py", "exec"))

# Space stays black.
world = scene.world
if world.use_nodes:
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = WORLD_COLOR.get(name, (0.0, 0.0, 0.0, 1.0))

scene.render.engine = "BLENDER_EEVEE"
# Speed: half resolution, few samples, no raytracing.
scene.render.resolution_percentage = 50
eevee = scene.eevee
eevee.taa_render_samples = 8
if hasattr(eevee, "use_raytracing"):
    eevee.use_raytracing = False
if hasattr(eevee, "shadow_ray_count"):
    eevee.shadow_ray_count = 1
    eevee.shadow_step_count = 4
img = scene.render.image_settings
if hasattr(img, "media_type"):
    img.media_type = "VIDEO"
img.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.ffmpeg.audio_codec = "NONE"
scene.render.use_file_extension = False
scene.render.filepath = f"//renders/{name}.mp4"

bpy.ops.render.render(animation=True)
print("RENDERED", bpy.path.abspath(scene.render.filepath))
