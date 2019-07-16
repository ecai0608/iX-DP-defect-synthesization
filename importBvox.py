import bpy
import numpy as np  

# *** COMMAND TO RUN PYTHON/BLENDER API SCRIPTS IN TERMINAL: blender [myscene.blend] --background --python myscript.py ***

# This script is to use the Blender API to automatically render models generated using Blender Voxel

# setting cube to be active object
cube = bpy.data.objects["Cube"]
bpy.context.scene.objects.active = cube

# importing voxel data for the texture
bpy.data.textures["Tex"].type = "VOXEL_DATA"
bpy.data.textures["Tex"].voxel_data.file_format = "BLENDER_VOXEL"
bpy.data.textures["Tex"].voxel_data.filepath = "Example.bvox"

# saving image render
bpy.ops.render.render()
bpy.data.images['Render Result'].save_render(filepath = "testRender.png")

# saving scene
bpy.ops.wm.save_as_mainfile(filepath = "testscene.blend") 


# STILL NEED TO IMPLEMENT:
# SETTING COLOR AND DENSITY RANGES

# POSSIBLE IMPLEMENTATIONS TO WORK ON LATER:
# CHOOSING DIFFERENT CAMERA VIEW TO RENDER FROM

# EXTERNAL PARAMETERS THAT WILL PROBABLY NEED TO BE PASSED ON TO THIS SCRIPT:
# CAMERA PLACEMENT, LIGHT SOURCE,...