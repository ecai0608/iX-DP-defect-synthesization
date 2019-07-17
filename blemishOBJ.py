import bpy
import numpy as np 
import random

# *** COMMAND TO RUN PYTHON/BLENDER API SCRIPTS IN TERMINAL: blender [myscene.blend] --background --python myscript.py ***

def blemishOBJ(obj):
    #obj = bpy.data.objects[object_name]

    # checking if the "blemish" material has already been added to the object
    if "blemish" not in obj.data.materials :
        # making the material and setting it to a red color
        blemish_mat = bpy.data.materials.new("blemish")
        blemish_mat.diffuse_color = (1, 0, 0)

        # checking if there are no material slots - if there are not, a dummy material slot needs to be added first
        if len(obj.data.materials) <= 1 :
            obj.data.materials.append(bpy.data.materials.new("material"))

        # adding material to object
        obj.data.materials.append(blemish_mat)
    
    # obtaining index of blemish material
    blemish_index = list(obj.data.materials).index(bpy.data.materials["blemish"])
    
    
    # choosing random face on mesh and assigning it blemish material
    rand_face = random.choice(obj.data.polygons)
    rand_face.material_index = blemish_index

    
    # rendering all 4 images
    bpy.context.scene.camera = bpy.data.objects["front_cam"]
    bpy.ops.render.render(write_still = True)
    bpy.data.images['Render Result'].save_render(filepath = "renders/front_render.png")

    bpy.context.scene.camera = bpy.data.objects["back_cam"]
    bpy.ops.render.render(write_still = True)
    bpy.data.images['Render Result'].save_render(filepath = "renders/back_render.png")

    bpy.context.scene.camera = bpy.data.objects["top_cam"]
    bpy.ops.render.render(write_still = True)
    bpy.data.images['Render Result'].save_render(filepath = "renders/top_render.png")

    bpy.context.scene.camera = bpy.data.objects["bot_cam"]
    bpy.ops.render.render(write_still = True)
    bpy.data.images['Render Result'].save_render(filepath = "renders/bot_render.png")



test_object = bpy.data.objects["test_object"]
blemishOBJ(test_object)


# saving scene
#bpy.ops.wm.save_as_mainfile(filepath = "testpoly.blend")
