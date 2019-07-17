#!/usr/bin/env python3

## 3D_to_2D.py
# Author: Joe Delle Donne
# Date: 07/17/2019
# Converts 3D coordinates to 2D pixel coordinates

# Execution command: blender [BLENDER_SCENE_NAME].blend --background --python 3D_to_2D.py

## Import Libraries
import bpy
from bpy_extras.object_utils import world_to_camera_view

## for output readability in terminal window
print(' \n*******************************************\n ')

# Gather blender scene data
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)  # Automatically updates the position of the selected object
scene = bpy.context.scene
obj = bpy.data.objects['Cube']
cam = bpy.data.objects['Camera']

# need to rescale 2d coordinates later
render = scene.render
res_x = render.resolution_x
res_y = render.resolution_y

# Get 3D coordinates
coord = obj.data.vertices[0].co
coords_2D = world_to_camera_view(scene,cam,coord)

rnd = lambda i: round(i)    # simple anon rounding function

# Output translated coordinates
print("(x,y) = ({},{})".format(rnd(res_x*coords_2D[0]), rnd(res_y*coords_2D[1])))

print(' \n*******************************************\n ')