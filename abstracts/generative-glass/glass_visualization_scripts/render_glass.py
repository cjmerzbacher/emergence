"""
render_glass.py (v2 - sphere turntable video)
Run with Blender:
    /Applications/Blender.app/Contents/MacOS/Blender --background --python render_glass.py

Outputs: glass_render.mp4 (120 frames, 5 seconds at 24fps)
"""
import bpy
import os
import math

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OBJ_PATH = os.path.join(SCRIPT_DIR, "rd_sphere.obj")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "glass_sphere_turntable.mp4")

bpy.ops.wm.read_factory_settings(use_empty=True)

# Import
print("Importing " + OBJ_PATH)
bpy.ops.wm.obj_import(filepath=OBJ_PATH)
obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
obj.name = "RD_Sphere"
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
obj.location = (0, 0, 0)
bpy.ops.object.shade_smooth()

mod = obj.modifiers.new(name="Subdiv", type="SUBSURF")
mod.levels = 1
mod.render_levels = 2

# --- Iridescent glass material ---
mat = bpy.data.materials.new(name="IridescentGlass")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
for n in nodes:
    nodes.remove(n)

output = nodes.new("ShaderNodeOutputMaterial")
output.location = (800, 0)

glass = nodes.new("ShaderNodeBsdfGlass")
glass.location = (200, 200)
glass.inputs["Color"].default_value = (0.95, 0.97, 1.0, 1.0)
glass.inputs["Roughness"].default_value = 0.05
glass.inputs["IOR"].default_value = 1.45

principled = nodes.new("ShaderNodeBsdfPrincipled")
principled.location = (200, -200)
principled.inputs["Base Color"].default_value = (0.95, 0.6, 0.8, 1.0)
principled.inputs["Metallic"].default_value = 0.1
principled.inputs["Roughness"].default_value = 0.1
principled.inputs["Transmission Weight"].default_value = 0.8
principled.inputs["IOR"].default_value = 1.45

layer_weight = nodes.new("ShaderNodeLayerWeight")
layer_weight.location = (-200, 0)
layer_weight.inputs["Blend"].default_value = 0.3

ramp = nodes.new("ShaderNodeValToRGB")
ramp.location = (0, -400)
ramp.color_ramp.elements[0].position = 0.3
ramp.color_ramp.elements[0].color = (0.9, 0.4, 0.6, 1.0)
ramp.color_ramp.elements[1].position = 0.7
ramp.color_ramp.elements[1].color = (0.4, 0.9, 0.85, 1.0)

links.new(layer_weight.outputs["Fresnel"], ramp.inputs["Fac"])
links.new(ramp.outputs["Color"], principled.inputs["Base Color"])

mix = nodes.new("ShaderNodeMixShader")
mix.location = (500, 0)
links.new(layer_weight.outputs["Facing"], mix.inputs["Fac"])
links.new(glass.outputs["BSDF"], mix.inputs[1])
links.new(principled.outputs["BSDF"], mix.inputs[2])
links.new(mix.outputs["Shader"], output.inputs["Surface"])

obj.data.materials.append(mat)

# --- Lighting ---
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.92, 0.90, 0.91, 1.0)
bg.inputs["Strength"].default_value = 1.0

light1 = bpy.data.lights.new(name="Key", type="AREA")
light1.energy = 200
light1.size = 3
light1_obj = bpy.data.objects.new(name="Key", object_data=light1)
bpy.context.scene.collection.objects.link(light1_obj)
light1_obj.location = (2, -2, 3)
light1_obj.rotation_euler = (math.radians(45), 0, math.radians(45))

light2 = bpy.data.lights.new(name="Fill", type="AREA")
light2.energy = 80
light2.size = 4
light2_obj = bpy.data.objects.new(name="Fill", object_data=light2)
bpy.context.scene.collection.objects.link(light2_obj)
light2_obj.location = (-3, 1, 2)
light2_obj.rotation_euler = (math.radians(60), 0, math.radians(-30))

light3 = bpy.data.lights.new(name="Rim", type="AREA")
light3.energy = 40
light3.size = 5
light3_obj = bpy.data.objects.new(name="Rim", object_data=light3)
bpy.context.scene.collection.objects.link(light3_obj)
light3_obj.location = (0, 2, -1)
light3_obj.rotation_euler = (math.radians(-80), 0, 0)

# --- Ground plane ---
bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, -1.8))
plane = bpy.context.active_object
plane.name = "Ground"
plane_mat = bpy.data.materials.new(name="GroundMat")
plane_mat.use_nodes = True
plane_bsdf = plane_mat.node_tree.nodes["Principled BSDF"]
plane_bsdf.inputs["Base Color"].default_value = (0.92, 0.90, 0.91, 1.0)
plane_bsdf.inputs["Roughness"].default_value = 0.15
plane.data.materials.append(plane_mat)

# --- Camera ---
cam_data = bpy.data.cameras.new(name="Camera")
cam_data.lens = 85
cam_obj = bpy.data.objects.new(name="Camera", object_data=cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (3, 0, 1.5)

# Point at object
direction = obj.location - cam_obj.location
rot_quat = direction.to_track_quat("-Z", "Y")
cam_obj.rotation_euler = rot_quat.to_euler()
bpy.context.scene.camera = cam_obj

# --- Turntable animation: rotate the object ---
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

obj.rotation_euler = (0, 0, 0)
obj.keyframe_insert(data_path="rotation_euler", frame=1)
obj.rotation_euler = (0, 0, math.radians(360))
obj.keyframe_insert(data_path="rotation_euler", frame=121)

# --- Render settings ---
scene.render.engine = "CYCLES"
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 100

# Video output
scene.render.image_settings.media_type = "VIDEO"
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.filepath = OUTPUT_PATH

try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    for device in prefs.devices:
        device.use = True
    scene.cycles.device = "GPU"
    print("Using GPU (Metal)")
except Exception:
    scene.cycles.device = "CPU"
    print("Falling back to CPU")

print("Rendering 120 frames to " + OUTPUT_PATH)
bpy.ops.render.render(animation=True)
print("Done!")
