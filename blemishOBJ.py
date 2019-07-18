import bpy
from bpy_extras.object_utils import world_to_camera_view
import numpy as np 
import random

# *** COMMAND TO RUN PYTHON/BLENDER API SCRIPTS IN TERMINAL: blender [myscene.blend] --background --python myscript.py ***

def blemishOBJ(obj):
    #obj = bpy.data.objects[object_name]

    # choosing a random vertex
    rand_vert = random.choice(obj.data.vertices)
    co_3d = rand_vert.co

    # creating and placing marker at defect vertex
    bpy.ops.mesh.primitive_uv_sphere_add()
    marker = bpy.data.objects["Sphere"]
    marker.location = co_3d
    # scaling marker to smaller size
    marker.scale.x = 0.01
    marker.scale.y = 0.01
    marker.scale.z = 0.01

    # adding red material to marker for visibility
    blemish_mat = bpy.data.materials.new("blemish")
    blemish_mat.diffuse_color = (1, 0, 0)
    marker.data.materials.append(blemish_mat)

    # setting scene/resolution variables for clarity
    scene = bpy.context.scene
    render = scene.render
    res_x = render.resolution_x
    res_y = render.resolution_y
    
    # iterating through all cameras to render images
    for obj in bpy.data.objects :
        if (obj.type == "CAMERA") :
            # setting camera to active camera
            bpy.context.scene.camera = obj

            # computing image coordinates
            co_2d = world_to_camera_view(scene, obj, co_3d)
            x, y = round(res_x*co_2d[0]), round(res_y*co_2d[1])

            # saving image render to "renders" folder
            bpy.ops.render.render(write_still = True)
            bpy.data.images["Render Result"].save_render(filepath = ("renders/%s.png" % obj.name))
            # writing image coordinates to text file
            binfile = open(("renders/%s.txt" % obj.name), "w")
            binfile.write("Image Coordinates: %s,%s" % (x, y))


# running on test object
test_object = bpy.data.objects["test_object"]
blemishOBJ(test_object)


# saving scene
#bpy.ops.wm.save_as_mainfile(filepath = "testpoly.blend")
