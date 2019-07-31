import bpy

from mathutils import Vector
from mathutils.bvhtree import BVHTree as tree

import numpy as np 
import random


cube = bpy.data.objects["Cube"]
sphere = bpy.data.objects["Sphere"]

zs = []
for vertex in cube.data.vertices:
    zs.append(np.array(vertex.co)[2])

minimum = min(zs)
counter = 0
for i in range(len(zs)):
    if zs[i] == minimum:
        counter = counter + 1

print(counter)



zs = []
for vertex in sphere.data.vertices:
    zs.append(np.array(vertex.co)[2])

maximum = max(zs)
counter = 0
for i in range(len(zs)):
    if zs[i] == maximum:
        counter = counter + 1

print(counter)


cubes = []
for vertex in cube.data.vertices:
    if vertex.co.z == minimum:
        cubes.append(vertex.co.y)


spheres = []
for vertex in sphere.data.vertices:
    if vertex.co.z == maximum:
        spheres.append(vertex.co.y)

y_cube = max(cubes)
y_sphere = max(spheres)


cube_loc = 0
counter = 0
for vertex in cube.data.vertices:
    if (vertex.co.z == minimum and vertex.co.y == y_cube):
        vertex.select = True
        counter = counter + 1
        cube_loc = vertex.co
print(cube_loc)

counter = 0
sphere_loc = 0
for vertex in sphere.data.vertices:
    if (vertex.co.z == maximum and vertex.co.y == y_sphere):
        vertex.select = True
        sphere_loc = vertex.co
        counter = counter + 1
print(sphere_loc)

"""
print(sphere.location)
sphere.location = sphere.location + (cube_loc - sphere_loc)
print(sphere.location)
"""

bpy.ops.wm.save_as_mainfile(filepath = "testpitdefect.blend")