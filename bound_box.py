#!/usr/bin/env python3

## bound_box.py
# Author:   Joe Delle Donne
# Date:     07/17/2019

## Link to object properties
# https://docs.blender.org/api/blender_python_api_2_63_14/bpy.types.Object.html?highlight=object

## Execute script in terminal:
# blender bound_box.blend --background --python bound_box.py

## for output readability in terminal window
print(' \n*******************************************\n ')

## Import Libraries
import bpy     # Library that allows you to interact with objects in blender
import sys
import os

## Gather object data
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)  # Automatically updates the position of the selected object
obj = bpy.context.active_object    # Selects the current active object
print('Bounding box and object data type: \n{}\n{}'.format(obj.bound_box,obj.data))       
# Outputs eight floating point arrays, three elements 
#   in each. Represents the eight points of the 
#   object's bounding box

# Iterate and display bounding box vertice coordinates
print('\nObject\'s bounding box verticies:')
for i in range(0,8):
    print('Vertice {}: {}'.format(i,obj.bound_box[i][0:]))

# Iterate through and display all verticies of the object
print('\nObjects total vertices:\n')
for index, vert in enumerate(obj.data.vertices):
    print('Vertice {}: {}'.format(index,vert.co))

## Create a cube and put it into the blender file
n = 6   # Length of the sides of the cube
verts = [(0,0,0),(0,n,0),(n,n,0),(n,0,0),(0,0,n),(0,n,n),(n,n,n),(n,0,n)]
faces = [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]

mymesh = bpy.data.meshes.new("Cube")
myobject = bpy.data.objects.new("Cube",mymesh)

myobject.location = bpy.context.scene.cursor_location
bpy.context.scene.objects.link(myobject)

mymesh.from_pydata(verts,[],faces)
mymesh.update(calc_edges=True)

print(' \n*******************************************\n ')
