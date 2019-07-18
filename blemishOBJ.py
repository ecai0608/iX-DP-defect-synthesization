import bpy
from bpy_extras.object_utils import world_to_camera_view
import numpy as np 

# *** COMMAND TO RUN PYTHON/BLENDER API SCRIPTS IN TERMINAL: blender [myscene.blend] --background --python myscript.py ***
# *** COMMAND TO SAVE FILE: bpy.ops.wm.save_as_mainfile(filepath = "[myscene.blend]") ***

# global parameters for number of defects and number of cameras
num_verts = 8
num_cams = 5

# function to point a given camera to a given location - credit: https://blender.stackexchange.com/a/5220
def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()


# function to blemish object in given scene
def blemishOBJ(obj):


    # --- CREATING BLEMISHES ON 3D MODEL ---


    # choosing random vertices to blemish
    rand_verts = np.random.choice(obj.data.vertices, num_verts, replace = False)

    cos_3d = []
    for i, vert in enumerate(rand_verts) :
        # storing location
        cos_3d.append(vert.co)

        # creating blemish at each point
        name = "{}".format(i)
        bpy.ops.mesh.primitive_uv_sphere_add(location = cos_3d[i])
        bpy.context.active_object.name = name
        marker = bpy.data.objects[name]

        # scaling blemish to smaller size
        marker.scale.x = 0.01
        marker.scale.y = 0.01
        marker.scale.z = 0.01
        
        # assigning red material to each blemish
        blemish_mat = bpy.data.materials.new("blemish")
        blemish_mat.diffuse_color = (1, 0, 0)
        marker.data.materials.append(blemish_mat)


    # --- CREATING CAMERAS IN RANDOM LOCATIONS ---


    # randomly generating origins for each camera
    cam_verts = np.random.choice(obj.data.vertices, num_cams, replace = False)

    # creating each camera, transforming them further away from the object, and re-orienting them to face the object
    for i, vert in enumerate(cam_verts) :
        bpy.ops.object.camera_add(location = 2*vert.co)

        cam_name = "camera{}".format(i)
        bpy.context.active_object.name = cam_name
        cam = bpy.data.objects[cam_name]
        look_at(cam, obj.location)
    

    # --- RENDERING IMAGES AND SAVING METADATA FOR EACH CAMERA


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

            # saving image render to "renders" folder
            bpy.ops.render.render(write_still = True)
            bpy.data.images["Render Result"].save_render(filepath = ("renders/%s.png" % obj.name))

            # writing image coordinates to text file
            binfile = open(("renders/%s.txt" % obj.name), "w")
            binfile.write("Image Resolution: %sx%s\n" % (res_x, res_y))
            binfile.write("Image Coordinates:\n")
            for i, coords in enumerate(cos_3d) :
                
                # computing image coordinates
                co_2d = world_to_camera_view(scene, obj, coords)
                x, y = round(res_x*co_2d[0]), round(res_y*(1 - co_2d[1]))

                # writing image resolution and coordinates to text file
                binfile.write("     %d: %s,%s\n" % (i, x, y))


# running on test object
test_object = bpy.data.objects["test_object"]
blemishOBJ(test_object)