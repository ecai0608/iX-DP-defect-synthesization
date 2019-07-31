import bpy
from bpy_extras.object_utils import world_to_camera_view
from bpy_extras.mesh_utils import face_random_points

from mathutils import Vector
from mathutils.bvhtree import BVHTree as tree

import numpy as np 
import random
import time

# *** TERMINAL COMAND: blender [myscene.blend] --background --python myscript.py ***
# *** SAVE FILE: bpy.ops.wm.save_as_mainfile(filepath = "[myscene.blend]") ***

# global parameters for number of defects and number of cameras
num_defects = 5
num_cams = 5

# table to store which defects are visible for which camera
visible_defects = np.zeros((num_cams, num_defects))


# function to point a given camera to a given location - credit: https://blender.stackexchange.com/a/5220
def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()


# function to tessellate the object and calculate weights for each tessellated face
def calc_tess_weights(obj):
    # tessellating object model
    obj.data.calc_tessface()

    # assigning weights to faces corresponding to surface area
    weights = [w.area for w in obj.data.tessfaces]
    weights = weights/np.sum(weights)
    return weights


# function to subtract defects from part model
def subtract_defect(obj, defect):
    # selecting part model and setting it to active
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.context.scene.objects.active = obj
    obj.select = True

    # adding modifier to part model
    bpy.ops.object.modifier_add(type = "BOOLEAN")
    subtract = obj.modifiers["Boolean"]
    subtract.operation = "DIFFERENCE"
    subtract.object = defect

    # applying modifier and deleting blemish
    bpy.ops.object.modifier_apply(apply_as = "DATA", modifier = "Boolean")
    obj.select = False
    bpy.ops.object.delete(use_global = False)


# function to render images from each camera
def render_cameras(cameras, scene):
    for cam in cameras:
        # setting cam to active camera
        bpy.context.scene.camera = cam

        # saving image render to renders folder
        bpy.ops.render.render(write_still = True)
        bpy.data.images["Render Result"].save_render(filepath = ("renders/%s.png" % cam.name))


# function to record locations of visible defects
def record_visible(cameras, scene, location, bvh, res_x, res_y, defect_index):
    # iterating through each randomly created camera
    for cam_index, cam in enumerate(cameras):

        # --- COLLISION DETECTION --- 

        # casting ray from defect location back to camera
        direction = cam.location - location
        ray = bvh.ray_cast(location + 0.001*direction, direction)

        # if the ray does not record a hit, this means the original defect location is visible
        if ray[0] == None:
            # computing image coordinates
            co_2d = world_to_camera_view(scene, cam, location)

            # --- IMAGE BOUNDARY DETECTION ---

            if (co_2d[0] >= 0 and co_2d[0] <= 1 and co_2d[1] >= 0 and co_2d[1] <= 1):
                x, y = round(res_x*co_2d[0]), round (res_y*(1 - co_2d[1]))

                # setting appropiate index in visible_defects to 1 to indicate that the given object is visible from this camera
                visible_defects[cam_index][defect_index] = 1

                # writing image coordinates to text file - defect must be within image boundary and have unobstructed view
                binfile = open(("renders/%s.txt" % cam.name), "a")
                binfile.write("%s, %s\n" % (x, y))
                binfile.close()
        

# function to record bounding boxes of visible defects
def record_bound_boxes(cameras, scene, bound_box, res_x, res_y, defect_index):
    # iterating through each randomly created camera
    for cam_index, cam in enumerate(cameras):

        # checking if the defect is visible
        if (visible_defects[cam_index][defect_index] == 1):

            # only recording bounding box data if the defect is visible from the camera view
            binfile = open(("renders/%s.txt" % cam.name), "a")

            # store x and y coordinates of each vertex of the bounding box in the camera space
            bound_xs = []
            bound_ys = []
            for vert_index in range(len(bound_box)):
                # storing coordinates for vertex of bounding box in an np array
                vert_coords = Vector(bound_box[vert_index])

                # computing coordinates in camera plane
                co_2d = world_to_camera_view(scene, cam, vert_coords)
                x, y = round(res_x*co_2d[0]), round (res_y*(1 - co_2d[1]))
                bound_xs.append(x)
                bound_ys.append(y)

            # use the minimum and maximum x and y values to define a bounding box in the plane of the camera view
            min_x = min(bound_xs)
            max_x = max(bound_xs)
            min_y = min(bound_ys)
            max_y = max(bound_ys)

            # writing coordinates of the corners of the bounding box to text file
            binfile.write("(%s, %s)  (%s, %s)  (%s, %s)  (%s, %s)\n" % (min_x, min_y, min_x, max_y, max_x, min_y, max_x, max_y))
            binfile.close()


# function to generate defects on part model (obj)
def generate_defects(obj):


    # --- SETTING ENVIRONMENT/SCENE VARIABLES ---


    print("Setting Scene")
    # modifying settings to ensure there are no errors with placement or edit mode
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)

    # setting render engine to CYCLES
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    bpy.data.worlds["World"].horizon_color = (0.8, 0.8, 0.8)

    # scaling and storing resolution values
    render = scene.render
    render.resolution_percentage = 50
    render_scale = render.resolution_percentage / 100
    res_x = render.resolution_x*render_scale
    res_y = render.resolution_y*render_scale

    # generating BVH tree of object to allow efficient raycasting
    bvh = tree.FromObject(obj, scene, epsilon = 0)


    # --- RANDOMLY GENERATING CAMERAS AROUND OBJECT MODEL --- 

    print("Generating Cameras")
    # randomly generating origins for each camera
    cam_verts = np.random.choice(obj.data.vertices, num_cams, replace = False)

    cameras = []
    # creating each camera, translating them further away from the object, and re-orienting them to face the object
    for i in range(num_cams):
        bpy.ops.object.camera_add(location = 4*cam_verts[i].co)

        cam_name = "camera{}".format(i + 1)
        bpy.context.active_object.name = cam_name
        cam = bpy.data.objects[cam_name]
        look_at(cam, obj.location)
        cameras.append(cam)

        # writing a text file to store metadata for each camera
        binfile = open(("renders/%s.txt" % cam.name), "w")
        binfile.write("Image Resolution: %sx%s\n" % (res_x, res_y))
        binfile.close()
            

    # --- CREATING DEFECTS ON 3D MODEL ---
    

    print("Creating Defects")
    # randomly sampling faces (WITH replacement) using weights
    weights = calc_tess_weights(obj)
    rand_faces = np.random.choice(obj.data.tessfaces, num_defects, p = weights, replace = True)

    # generating locations for each defect
    # Note: this implementation allows for multiple blemishes to be generated on the same face
    defect_locs = face_random_points(1, rand_faces)

    # creating texture for microdisplacement
    bpy.data.textures.new("noise", type = "DISTORTED_NOISE")
    print("1")
    # placing defects at locations
    noise = bpy.data.textures["noise"]
    for defect_index, loc in enumerate(defect_locs):
        print("1")
        # recording metadata regarding visibility of objects
        record_visible(cameras, scene, loc, bvh, res_x, res_y, defect_index)

        # creating model of defect        
        name = "{}".format(i)
        bpy.ops.mesh.primitive_uv_sphere_add(location = loc)
        bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
        bpy.context.active_object.name = name
        defect = bpy.data.objects[name]

        # scaling defect to smaller size
        # Note: Long axis should be defined along z-axis. This will align properly with rotation_euler
        defect.scale.x = 0.04
        defect.scale.y = 0.04
        defect.scale.z = 0.10

        # re-aligning ellipsoid
        defect.rotation_euler = rand_faces[i].normal

        """
        # adding noise
        bpy.data.textures["noise"].distortion = 0.3
        bpy.data.textures["noise"].noise_scale = 2
        bpy.ops.object.modifier_add(type = "DISPLACE")
        defect.modifiers["Displace"].texture = noise
        """
        print("1")
        # recording metadata regarding bounding boxes of visible defects
        record_bound_boxes(cameras, scene, defect.bound_box, res_x, res_y, defect_index)

        print("1")
        # subtracting blemishes from model
        subtract_defect(obj, defect)


    # --- RENDERING IMAGES AND SAVING METADATA FOR RANDOMLY GENERATED CAMERA ---

    print("Rendering Images")
    render_cameras(cameras, scene)
    

# running on test object
model = bpy.data.objects["Suzanne"]
model.select = True

generate_defects(model)
# bpy.ops.wm.save_as_mainfile(filepath = "testpoly1.blend")