import bpy
from bpy_extras.object_utils import world_to_camera_view
from bpy_extras.mesh_utils import face_random_points

from mathutils import Vector
from mathutils.bvhtree import BVHTree as tree

import numpy as np
import math
import random
import time

# *** TERMINAL COMMAND: blender [myscene.blend] --background --python myscript.py ***
# *** SAVE FILE: bpy.ops.wm.save_as_mainfile(filepath = "[myscene.blend]") ***


# -------------------------------------------------------------------------------
# GLOBAL PARAMETERS:
# FILEPATH        - filepath to .blend file of model
# NUM_ITERATIONS  - number of defect models to generate
# NUM_DEFECTS_MIN - minimum number of defects to randomly generate
# NUM_DEFECTS_MAX - maximum number of defects to randomly generate
# NUM_CAMS        - number of cameras to randomly generate
# DEFECT_TYPES    - list of possible defect types ("PIT", "BUMP")
# HDRIS           - list of HDRI backgrounds
# -------------------------------------------------------------------------------

FILEPATH = "disc_brake_model.blend"
NUM_ITERATIONS = 2
NUM_DEFECTS_MIN = 1
NUM_DEFECTS_MAX = 3
NUM_CAMS = 4
DEFECT_TYPES = ["PIT"]

HDRIS = ["Autoshop Classroom", "Autoshop Engines", "Autoshop Floor Lifts 01", "Autoshop Floor Lifts 02", "Classroom Automotive", 
"Factory - Plastic Bags 1", "Industrial Warehouse", "Machine Shop 01", "Machine Shop 02"]


# function to load in blender scene
def load_environment():
    # opening .blend file
    bpy.ops.wm.open_mainfile(filepath = FILEPATH)

    # setting obj
    obj = bpy.data.objects["Object"]
    bpy.context.scene.objects.active = obj
    obj.select = True
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    scene = bpy.context.scene

    # setting to OBJECT mode
    bpy.ops.object.mode_set(mode = "OBJECT")

    # setting render engine to CYCLES
    scene.render.engine = "CYCLES"
    bpy.data.worlds["World"].horizon_color = (0.8, 0.8, 0.8)

    # scaling and setting resolution values
    render = scene.render
    res_x = render.resolution_x*(scene.render.resolution_percentage / 100)
    res_y = render.resolution_y*(scene.render.resolution_percentage / 100)

    # setting GPU settings
    bpy.context.user_preferences.addons["cycles"].preferences.compute_device_type = "CUDA"
    bpy.context.user_preferences.addons["cycles"].preferences.devices[0].use = True
    bpy.context.scene.cycles.device = "GPU"

    # randomly picking number of defects
    num_defects = random.randint(NUM_DEFECTS_MIN, NUM_DEFECTS_MAX)

    # list to store bounding box data for each defect
    bounding_boxes = []

    # table to store visibility of each defect with respect to each camera
    visible_defects = np.zeros((NUM_CAMS, num_defects))

    # computing radius and center of bounding sphere of object
    bb = obj.bound_box
    bound_xs = []
    bound_ys = []
    bound_zs = []
    for vert in bb:
        coords = Vector(vert)
        bound_xs.append(coords[0])
        bound_ys.append(coords[1])
        bound_zs.append(coords[2])
    [min_x, max_x] = [min(bound_xs), max(bound_xs)]
    [min_y, max_y] = [min(bound_ys), max(bound_ys)]
    [min_z, max_z] = [min(bound_zs), max(bound_zs)]
    center = Vector([np.mean(bound_xs), np.mean(bound_ys), np.mean(bound_zs)])
    radius = np.sqrt((max_x - min_x)**2 + (max_y - min_y)**2 + (max_z - max_z)**2)/2
    
    return obj, scene, res_x, res_y, bounding_boxes, visible_defects, center, radius, num_defects


# function to randomize environment of scene
def randomize_environment(obj):
    # randomizing rotational position of part model
    obj.rotation_euler[0] = random.uniform(0, 2*math.pi)
    obj.rotation_euler[1] = random.uniform(0, 2*math.pi)
    obj.rotation_euler[2] = random.uniform(0, 2*math.pi)
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)

    # randomizing HDRI background
    hdri_name = np.random.choice(HDRIS, 1, replace = False)
    bpy.data.worlds["World"].node_tree.nodes["Environment Texture"].image.filepath = "//HDRIs/{}.exr".format(hdri_name[0])


# function to point a given camera to a given location - credit: https://blender.stackexchange.com/a/5220
def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the camera's '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()


# function to tessellate the object and calculate weights for the tessellated faces
def calc_tess_weights(obj):
    # tessellating object model
    obj.data.calc_tessface()

    #assigning weights to faces corresponding to surface area
    weights = [w.area for w in obj.data.tessfaces]
    weights = weights/np.sum(weights)
    return weights


# function to record locations of visible defects
def record_visible(obj, scene, visible_defects, cameras, bvh, defect_index):
    # obtaining all new defect vertices
    new_vertices = [v.co.copy() for v in obj.data.vertices if v.select]

    # deselecting all new vertices
    bpy.context.scene.objects.active = obj
    bpy.ops.object.mode_set(mode = "EDIT")
    bpy.ops.mesh.select_all(action = "DESELECT")
    bpy.ops.object.mode_set(mode = "OBJECT")

    # iterating through each randomly generated camera
    for cam_index in range(NUM_CAMS):
        cam = cameras[cam_index]

        # -- COLLISION DETECTION -- 

        for coords in new_vertices:
            direction = cam.location - coords
            ray = bvh.ray_cast(coords + 0.001*direction, direction)

            # if the ray does not record a hit, this means the original defect location is visible
            if ray[0] == None:
                # computing image coordinates
                co_2d = world_to_camera_view(scene, cam, coords)

                # -- IMAGE BOUNDARY DETECTION -- 

                if (co_2d[0] >= 0 and co_2d[0] <= 1 and co_2d[1] >= 0 and co_2d[1] <= 1):
                    # updating visible_defects
                    visible_defects[cam_index][defect_index] = 1
                    break


# function to record bounding boxes of visible defects
def record_bound_boxes(scene, visible_defects, bounding_boxes, cameras, defect_type, defect_index, res_x, res_y):
    bb = bounding_boxes[defect_index]
    
    # initializing new_annotations
    new_annotations = ""

    # iterating through each randomly generated camera
    for cam_index in range(NUM_CAMS):
        cam = cameras[cam_index]

        # checking if the defect is visble
        if (visible_defects[cam_index][defect_index] == 1):
            # store x and y coordinates of each vertex of the bounding box in the camera space
            bound_xs = []
            bound_ys = []
            for vert_index in range(len(bb)):
                vert_coords = bb[vert_index]

                # computing coordinates in camera space
                co_2d = world_to_camera_view(scene, cam, vert_coords)
                x, y = round(res_x*co_2d[0]), round(res_y*(1 - co_2d[1]))
                bound_xs.append(x)
                bound_ys.append(y)

            # using minimum and maximium x and y values to define bounding box in the camera space
            min_x = min(bound_xs)
            max_x = max(bound_xs)
            min_y = min(bound_ys)
            max_y = max(bound_ys)

            # clipping coordinates to lie within the image boundary
            min_x = max(0, min_x)
            max_x = min(res_x, max_x)
            min_y = max(0, min_y)
            max_y = min(res_y, max_y)

            # writing image coordinates to text file
            binfile = open("camera_metadata/{}.txt".format(cam.name), "a")
            binfile.write("{}  |  ".format(defect_type))
            binfile.write("({}, {})  ({}, {})  ({}, {})  ({}, {})\n".format(min_x, min_y, min_x, max_y, max_x, min_y, max_x, max_y))
            binfile.close()

            # appending to annotations
            new_annotations = new_annotations + "renders/{}.txt,{},{},{},{},{}\n".format(cam.name, min_x, min_y, max_x, max_y, defect_type)
    
    return new_annotations


# function to subtract defect models from part model
def subtract_defect(obj, defect, defect_type):
    # selecting part model and setting it to active object
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.context.scene.objects.active = obj
    obj.select = True

    # adding boolean modifier to part model
    bpy.ops.object.modifier_add(type = "BOOLEAN")
    modify = obj.modifiers["Boolean"]
    modify.operation = "DIFFERENCE"
    """
    if (defect_type == "PIT"):
        modify.operation = "DIFFERENCE"
    elif (defect_type == "BUMP"):
        modify.operation = "UNION"
    """
    modify.object = defect

    # applying modifier and deleting blemish
    bpy.ops.object.modifier_apply(apply_as = "DATA", modifier = "Boolean")
    obj.select = False
    bpy.context.scene.objects.active = defect
    bpy.ops.object.delete(use_global = False)


# function to render images for each camera
def render_cameras(scene, visible_defects, cameras):
    # iterating through each randomly generated camera
    for cam_index in range(NUM_CAMS):
        if (sum(visible_defects[cam_index][:]) > 0):
            cam = cameras[cam_index]

            # setting camera to active camera
            scene.camera = cam

            # saving image render to renders folder
            bpy.ops.render.render(write_still = True)
            bpy.data.images["Render Result"].save_render(filepath = "renders/{}.jpg".format(cam.name))


# function to create pit at given location
def build_pit(defect_loc, defect_index, align):
    # creating pit model
    name = "{}".format(defect_index)
    bpy.ops.mesh.primitive_uv_sphere_add(segments = 256, ring_count = 128, location = defect_loc)
    bpy.context.active_object.name = name
    defect = bpy.data.objects[name]

    # scaling defect to smaller size
    # NOTE: long axis should be defined along z-axis to align properly with rotation_euler
    defect.scale.x = 0.05 + random.uniform(-0.01, 0.01)
    defect.scale.y = 0.05 + random.uniform(-0.01, 0.01)
    defect.scale.z = 0.05 + random.uniform(-0.01, 0.01)    

    # realigning ellipsoid
    defect.rotation_euler = align

    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    return defect


# function to create bump at given location
def build_bump(defect_loc, defect_index, align, noise):
    # creating bump model
    name = "{}".format(defect_index)
    bpy.ops.mesh.primitive_cube_add(location = defect_loc)

    # subdivide model
    bpy.ops.object.mode_set(mode = "EDIT")
    for subdivide in range(3):
        bpy.ops.mesh.subdivide()
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.context.active_object.name = name
    defect = bpy.data.objects[name]

    # scaling defect
    defect.scale.x = 0.08
    defect.scale.y = 0.08
    defect.scale.z = 0.08
    """
    # create new material
    bpy.ops.material.new()

    # adding noise
    noise.distortion = 6 #random.randint(6, 10)
    noise.noise_scale = 1 #random.randint(0, 2)
    bpy.ops.object.modifier_add(type = "DISPLACE")
    defect.modifiers["Displace"].texture = noise
    defect.modifiers["Displace"].strength = 0.2

    # adding subsurf
    bpy.ops.object.modifier_add(type = "SUBSURF")
    defect.modifiers["Subsurf"].levels = 2
    """
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
    return defect


# function to generate defects on part model (obj)
def generate_defects(complete_iter):


    # --- LOADING AND SETTING ENVIRONMENT VARIABLES ---


    obj, scene, res_x, res_y, bounding_boxes, visible_defects, center, radius, num_defects = load_environment()
    randomize_environment(obj)

    # generating BVH tree of part model to allow efficient raycasting
    bvh = tree.FromObject(obj, scene, epsilon = 0)


    # --- RANDOMLY GENERATING CAMERAS AROUND OBJECT MODEL ---


    cameras = []
    # creating each camera, translating them away from the object, and re-orienting them to face the object
    for i in range (NUM_CAMS):
        # randomly sampling from the bounding sphere using spherical coordinates
        theta = random.uniform(0, 2*math.pi)
        phi = random.uniform(0, math.pi)

        # allowing for variance in distance from camera to center of object
        dist = radius
        dist = (2 + random.uniform(-1, 1))*radius

        # computing rectangular coordinates
        x = dist*np.sin(phi)*np.cos(theta)
        y = dist*np.sin(phi)*np.sin(theta)
        z = dist*np.cos(phi)
        cam_loc = center + Vector([x, y, z])

        # adding camera to scene
        bpy.ops.object.camera_add(location = cam_loc)
        cam_name = "camera{}-{}".format(complete_iter, i)
        bpy.context.active_object.name = cam_name
        cam = bpy.data.objects[cam_name]
        look_at(cam, obj.location)
        cameras.append(cam)

        # opening text file to store metadata for newly generated camera
        binfile = open("camera_metadata/{}.txt".format(cam_name), "w")
        binfile.write("Image Resolution: {}x{}\n".format(res_x, res_y))
        binfile.close()


    # --- CREATING DEFECTS ON 3D MODEL ---


    # randomly sampling faces (WITH replacement) using weights based on surface area
    weights = calc_tess_weights(obj)
    rand_faces = np.random.choice(obj.data.tessfaces, num_defects, p = weights, replace = True)
    
    # creating a list to store normal vectors - this will allow us to align defects AFTER we have changed the geometry of the surface
    defect_normals = [np.array(face.normal) for face in rand_faces]

    # generating locations for each defect by randomly choosing a point on each face
    # NOTE: this implementation allows for multiple defects to be generated on the same face
    defect_locs = face_random_points(1, rand_faces)
    rand_faces = None

    # creating texture for microdisplacement
    bpy.data.textures.new("noise", type = "DISTORTED_NOISE")
    noise = bpy.data.textures["noise"]

    # initializing annotations
    annotations = ""

    # placing defects at locations
    for defect_index in range(num_defects):
        defect_type = random.choice(DEFECT_TYPES)
        defect_loc = defect_locs[defect_index]

        # creating defect model
        align = defect_normals[defect_index]
        defect = build_pit(defect_loc, defect_index, align)

        # extracting bounding box coordinates
        bb_verts = [Vector(v) for v in defect.bound_box]
        bounding_boxes.append(bb_verts)

        # deforming part surface with defect model
        subtract_defect(obj, defect, defect_type)

        # recording metadata regarding visibility and location of defect
        record_visible(obj, scene, visible_defects, cameras, bvh, defect_index)
        annotations = annotations + record_bound_boxes(scene, visible_defects, bounding_boxes, cameras, defect_type, defect_index, res_x, res_y)

    
    # checking if geometry was modified properly
    bpy.context.scene.objects.active = obj
    obj.select = True
    bpy.ops.object.mode_set(mode = "EDIT")
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.object.mode_set(mode = "OBJECT")
    non_manifold_verts = [v for v in obj.data.vertices if v.select]
    
    # will be set to True if the resulting model is manifold, and render_iterations will not repeat the defect generation
    manifold = False
    if (len(non_manifold_verts) == 0):
        manifold = True
        # only record metadata to annotations.csv if the defect model is properly generated
        binfile = open("annotations.csv", "a")
        binfile.write(annotations)
        binfile.close()


    return manifold, scene, visible_defects, cameras
    

# function to generate renders of correctly deformed part models
def render_iterations():
    # creating annotations .csv file
    binfile = open("annotations.csv", "w")
    binfile.close()

    # iteratively generating defect models
    complete_iters = 0
    while (complete_iters < NUM_ITERATIONS):
        manifold, scene, visible_defects, cameras = generate_defects(complete_iters)
        # only producing renders and moving to next iteration if deformed model is still a manifold
        if (manifold):
            complete_iters = complete_iters + 1
            print("RENDERING ITERATION: {}".format(complete_iters))
            render_cameras(scene, visible_defects, cameras)



render_iterations()