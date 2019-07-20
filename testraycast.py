import bpy
from mathutils import Vector

obj = bpy.data.objects["Cube"]
cam = bpy.data.objects["Camera"]

locs = []


for vert in obj.data.vertices :
    result, intersection = cam.ray_cast(cam.location, )



for vert in obj.data.vertices :
    name = "{}".format(i)
    bpy.ops.mesh.primitive_uv_sphere_add(location = vert.co)
    locs.append(vert.co)


    bpy.context.active_object.name = name
    marker = bpy.data.objects[name]
     # scaling blemish to smaller size
    marker.scale.x = 0.02
    marker.scale.y = 0.02
    marker.scale.z = 0.02
   
    # assigning red material to each blemish
    blemish_mat = bpy.data.materials.new("blemish")
    blemish_mat.diffuse_color = (1, 0, 0)
    marker.data.materials.append(blemish_mat)


