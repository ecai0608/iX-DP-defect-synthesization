import bpy
import numpy as np
import math

from mathutils import Vector

# WILL HAVE TO SELECT FACE IN EDIT MODE


obj = bpy.data.objects["Suzanne"]
obj.name = "obj"
bpy.ops.object.mode_set(mode = "OBJECT")
bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)

# bpy.ops.object.mode_set(mode = "OBJECT")



normal = 0
center = 0

bpy.ops.object.mode_set(mode = "EDIT")
bpy.ops.mesh.select_mode(type = "FACE")
for face in obj.data.polygons:
    if face.select:
        # bpy seems to pass by reference, so store the concrete values elsewhere for later use
        normal = np.array(face.normal)
        center = np.array(face.center)


bpy.ops.object.mode_set(mode = "OBJECT")

bpy.ops.mesh.primitive_uv_sphere_add(location = center, segments = 100, ring_count = 100)
bpy.context.active_object.name = "defect"
marker = bpy.data.objects["defect"]

# scaling blemish to smaller size
marker.scale.x = 0.1
marker.scale.y = 0.1
marker.scale.z = 0.1

print(obj)
#bpy.ops.object.mode_set(mode = "EDIT")
bpy.context.scene.objects.active = obj
obj.select = True
print(obj)
bpy.ops.object.modifier_add(type = "BOOLEAN")
subtract = obj.modifiers["Boolean"]
subtract.operation = "DIFFERENCE"
subtract.object = marker
bpy.ops.object.modifier_apply(apply_as = "DATA", modifier = "Boolean")

obj.select = False
bpy.ops.object.delete(use_global = False)


"""
print(center)

# NEED TO SET TO EDIT MODE
# bpy.ops.object.mode_set(mode = "EDIT")
bpy.ops.mesh.subdivide()
bpy.ops.mesh.subdivide()
bpy.ops.mesh.subdivide()
bpy.ops.mesh.subdivide()
bpy.ops.mesh.subdivide()
bpy.ops.mesh.subdivide()
bpy.ops.mesh.subdivide()
bpy.ops.mesh.subdivide()


# switch to object mode to update vertex data and allow for vertex translation



# defining parameters for sphere of influence
radius = 0.2
noise_var = 0.05


# dists = []
unchanged = []

bpy.ops.object.mode_set(mode = "OBJECT")
for vertex in obj.data.vertices:
    if vertex.select:
        # dists.append(vertex.co)
        dist = np.linalg.norm(np.array(vertex.co) - center)
        if (dist <= radius):
            dist_2 = (1/2)*np.sqrt(radius**2 - dist**2)
            vertex.co = vertex.co - Vector(dist_2*normal)
            #vertex.co = vertex.co - Vector((1/(1 + np.exp(-dist)))*normal)
            vertex.select = False
        else:
            unchanged.append(vertex.index)



bpy.ops.object.mode_set(mode="EDIT") 
bpy.ops.mesh.select_all(action = 'DESELECT') #Deselecting all
bpy.ops.mesh.select_mode(type = "VERT")
bpy.ops.object.mode_set(mode = "OBJECT")
print(len(unchanged))
for i in range(len(unchanged)):
    obj.data.vertices[unchanged[i]].select = True
bpy.ops.object.mode_set(mode="EDIT") 


bpy.ops.mesh.dissolve_limited(angle_limit = math.pi/20)
# TO DO: RANDOMIZE DISPLACEMENT
# MARK VERTICES OUTSIDE OF RANGE
# SELECT FACES WITHIN RANGE
"""




#bpy.ops.object.mode_set(mode="OBJECT") 
bpy.ops.wm.save_as_mainfile(filepath = "defectrule1.blend")



# DEFINING OUR DEFECT
# FOR NOW, SPECIFY SPHERE OF INFLUENCE
