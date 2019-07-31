import bpy
from bpy_extras.object_utils import world_to_camera_view
from bpy_extras.mesh_utils import face_random_points

from mathutils import Vector
from mathutils.bvhtree import BVHTree as tree

import numpy as np 
import random
import time
import math

# *** TERMINAL COMAND: blender [myscene.blend] --background --python myscript.py ***
# *** SAVE FILE: bpy.ops.wm.save_as_mainfile(filepath = "[myscene.blend]") ***

# global parameters for number of defects and number of cameras
num_defects = 3
num_cams = 3
DEFECT_BOXES = {}
VISIBLE_DEFECTS_GLOBAL = {}

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


# function to render images from all cameras in the scene and store metadata on image locations of defects
def render_images(scene, obj, defect_locs):
    render = scene.render
    render_scale = render.resolution_percentage / 100

    # scaling resolution values
    res_x = render.resolution_x*render_scale
    res_y = render.resolution_y*render_scale
    
    # building BVHTree of object model
    bvh = tree.FromObject(obj, scene, epsilon = 0)

    # iterating through all cameras to render images
    for cam in bpy.data.objects:
        if (cam.type == "CAMERA"):
            # setting camera to active camera
            bpy.context.scene.camera = cam

            # recording metadata for camera
            record_2D_boxes(scene, cam, bvh, defect_locs, res_x, res_y)

            # Only render the image if there is a defect visible
            if VISIBLE_DEFECTS_GLOBAL[cam.name]:
                # saving image render to "renders" folder
                bpy.ops.render.render(write_still = True)
                bpy.data.images["Render Result"].save_render(filepath = ("renders/%s.png" % cam.name))


# function to record metadata for visible defects for a specific camera
def record_visible_verts(scene, cam, bvh, defect_locs, res_x, res_y):
    # opening metadata file for given camera
    binfile = open(("renders/%s.txt" % cam.name), "w")
    binfile.write("Image Resolution: %sx%s\n" % (res_x, res_y))
    binfile.write("Image Coordinates:\n")

    # counter to keep track of visible defects (will probably remove later - this is just to check the script)
    i = 0

    # looping through each defect location in 3D space
    for defect in DEFECT_BOXES:
        for coords in DEFECT_BOXES[defect]:
            # --- COLLISION DETECTION --- 

            # casting ray from defect location back to camera
            direction = cam.location - coords
            ray = bvh.ray_cast(coords + 0.001*direction, direction)

            # if the ray does not record a hit, this means the original defect location is visible
            if ray[0] == None:
                # computing image coordinates
                co_2d = world_to_camera_view(scene, cam, coords)

                # --- IMAGE BOUNDARY DETECTION ---
                if (co_2d[0] >= 0 and co_2d[0] <= 1 and co_2d[1] >= 0 and co_2d[1] <= 1):
                    x, y = round(res_x*co_2d[0]), round(res_y*(1 - co_2d[1]))

                    # writing image coordinates to text file - defect must be within image boundary and have unobstructed view
                    i = i + 1
                    binfile.write("[ Defect %s ]    %d: %s,%s\n" % (defect,i, x, y))            
    binfile.close()


# function to record the 2D bounding box coordinates of defects in rendered images
def record_2D_boxes(scene, cam, bvh, defect_locs, res_x, res_y):
    # initialize visible defects structures for each camera
    VISIBLE_DEFECTS_GLOBAL[cam.name] = []
    visible_defects = []

    # opening metadata file for given camera
    binfile = open(("renders/%s.txt" % cam.name), "w")
    binfile.write("Image Resolution: %sx%s\n" % (res_x, res_y))
    binfile.write("Defect's Bounding Box Image Coordinates:\n")

    # loop through defect bounding box coords and log if at least one vertice is visible, store defect name in list
    for defect in DEFECT_BOXES:
        for coords in DEFECT_BOXES[defect]:
            # --- COLLISION DETECTION --- 

            # casting ray from defect location back to camera
            direction = cam.location - coords
            ray = bvh.ray_cast(coords + 0.001*direction, direction)

            # if the ray does not record a hit, this means the original defect location is visible
            if ray[0] == None:
                # computing image coordinates
                co_2d = world_to_camera_view(scene, cam, coords)

                # --- IMAGE BOUNDARY DETECTION ---
                # make sure that the point is in the frame
                if (co_2d[0] >= 0 and co_2d[0] <= 1 and co_2d[1] >= 0 and co_2d[1] <= 1):
                    x, y = round(res_x*co_2d[0]), round(res_y*(1 - co_2d[1]))
                    
                    # if the defect is at all visible, store the defect name in the defect_list
                    visible_defects.append(defect)
                    VISIBLE_DEFECTS_GLOBAL[cam.name].append(defect)

    # looping through each defect location in 3D space
    for defect in DEFECT_BOXES:
        # Only log boundning boxes for defects in visible frame
        if defect in visible_defects:
            # initialize x and y coord lists for each defect
            x_coords = []
            y_coords = []
            # Loop through the defect's bounding box's coordinates
            for coords in DEFECT_BOXES[defect]:
                # computing image coordinates of the vertice's 3D coordinates
                co_2d = world_to_camera_view(scene, cam, coords)
                # make sure that the point is in the frame
                if (co_2d[0] >= 0 and co_2d[0] <= 1 and co_2d[1] >= 0 and co_2d[1] <= 1):
                    x, y = round(res_x*co_2d[0]), round(res_y*(1 - co_2d[1]))
                    x_coords.append(x)
                    y_coords.append(y)
            # Calculate min and max for x and y values for the defect
            x_min = min(x_coords)
            y_min = min(y_coords)
            x_max = max(x_coords)
            y_max = max(y_coords)
            # Log bounding box image coords using min and max values
            binfile.write("[ Defect {} ]  : {},{}\n".format(defect, x_min, y_min))
            binfile.write("[ Defect {} ]  : {},{}\n".format(defect, x_min, y_max)) 
            binfile.write("[ Defect {} ]  : {},{}\n".format(defect, x_max, y_min)) 
            binfile.write("[ Defect {} ]  : {},{}\n".format(defect, x_max, y_max)) 
    # close the text file                   
    binfile.close()


# function to subtract defects from part model
def subtract_defect(obj, defect):
    time.sleep(5)
    # selecting part model and setting it to active
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.context.scene.objects.active = obj
    obj.select = True

    # adding modifier to part model
    bpy.ops.object.modifier_add(type = "BOOLEAN")
    subtract = obj.modifiers["Boolean"]
    subtract.operation = "UNION"
    subtract.object = defect

    # applying modifier and deleting blemish
    bpy.ops.object.modifier_apply(apply_as = "DATA", modifier = "Boolean")
    obj.select = False
    bpy.ops.object.delete(use_global = False)


# function to generate defects on part model (obj)
def generate_defects(obj):
    # modifying settings to ensure there are no errors with placement or edit mode
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)


    # --- CREATING DEFECTS ON 3D MODEL ---
    

    # randomly sampling faces (WITH replacement) using weights
    weights = calc_tess_weights(obj)
    rand_faces = np.random.choice(obj.data.tessfaces, num_defects, p = weights, replace = True)
    print("rand_faces: \n{}\n".format(rand_faces))

    # generating locations for each defect
    # Note: this implementation allows for multiple blemishes to be generated on the same face
    defect_locs = face_random_points(1, rand_faces)
    print("defect_locs: \n{}\n".format(defect_locs))

    # creating texture for microdisplacement
    bpy.data.textures.new("noise", type = "DISTORTED_NOISE")

    '''
    bpy.data.scenes["Scene"].tool_settings.use_snap = True
    bpy.data.scenes["Scene"].tool_settings.snap_element = "FACE"
    bpy.data.scenes["Scene"].tool_settings.snap_target = "ACTIVE"
    bpy.data.scenes["Scene"].tool_settings.use_snap_align_rotation = True
    '''

    # placing defects at locations
    noise = bpy.data.textures["noise"]
    for i, loc in enumerate(defect_locs):        
        name = "{}".format(i)
        bpy.ops.mesh.primitive_cube_add(location = loc)

        # subdivide plane
        bpy.ops.object.mode_set(mode = "EDIT")
        for subdivide in range(3):
            bpy.ops.mesh.subdivide()
        bpy.ops.object.mode_set(mode = "OBJECT")
        bpy.context.active_object.name = name
        defect = bpy.data.objects[name]

        '''
        defect.rotation_euler[0] = rand_faces[i].normal[0]*(180/math.pi)
        defect.rotation_euler[1] = rand_faces[i].normal[1]*(180/math.pi)
        defect.rotation_euler[2] = rand_faces[i].normal[2]*(180/math.pi)
        '''

        # scaling defect
        defect.scale.x = 0.10
        defect.scale.y = 0.10
        defect.scale.z = 0.10

        # create new material
        bpy.ops.material.new()

        # adding noise
        bpy.data.textures["noise"].distortion = 6 #random.randint(6,10)
        bpy.data.textures["noise"].noise_scale = 1 #random.randint(0,2)
        bpy.ops.object.modifier_add(type = "DISPLACE")
        defect.modifiers["Displace"].texture = noise
        defect.modifiers["Displace"].strength = 0.2

        # adding subsurf
        bpy.ops.object.modifier_add(type = "SUBSURF")
        bpy.data.objects[name].modifiers["Subsurf"].levels = 2

        # Add bounding box info to the global dictionary
        bpy.ops.object.transform_apply(location = True, scale = True)
        coords_list = []
        for coords_vec in defect.bound_box:
            coords_list.append(Vector([coords_vec[0],coords_vec[1],coords_vec[2]]))
        DEFECT_BOXES[defect.name] = coords_list

        # subtracting blemishes from model
        #subtract_defect(obj, defect)

    #print("DEFECT BOXES: \n{}\n".format(DEFECT_BOXES))

    # --- RENDERING IMAGES AND SAVING METADATA FOR RANDOMLY GENERATED CAMERA ---


    # randomly generating origins for each camera
    cam_verts = np.random.choice(obj.data.vertices, num_cams, replace = False)

    # creating each camera, translating them further away from the object, and re-orienting them to face the object
    for i, vert in enumerate(cam_verts):
        bpy.ops.object.camera_add(location = 4*vert.co)

        cam_name = "camera{}".format(i)
        bpy.context.active_object.name = cam_name
        cam = bpy.data.objects[cam_name]
        look_at(cam, obj.location)

    # setting render engine to CYCLES
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'

    # adjusting resolution and environment lighting
    scene.render.resolution_percentage = 50
    bpy.data.worlds["World"].horizon_color = (0.8, 0.8, 0.8)

    # rendering images
    render_images(scene, obj, defect_locs)
    

# running on test object
model = bpy.data.objects["Torus"]
model.select = True

generate_defects(model)

# List which defects are visible to each camera
for x in VISIBLE_DEFECTS_GLOBAL:
    print (x)
    for y in VISIBLE_DEFECTS_GLOBAL[x]:
        print ("\t{}".format(y))

bpy.ops.wm.save_as_mainfile(filepath = "test_bump1.blend")