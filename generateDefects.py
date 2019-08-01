import bpy
from bpy_extras.object_utils import world_to_camera_view
from bpy_extras.mesh_utils import face_random_points

from mathutils import Vector
from mathutils.bvhtree import BVHTree as tree

import numpy as np 
import random
import time

# *** TERMINAL COMMAND: blender [myscene.blend] --background --python myscript.py ***
# *** SAVE FILE: bpy.ops.wm.save_as_mainfile(filepath = "[myscene.blend]") ***


# -------------------------------------------------------------------------------
# GLOBAL PARAMETERS:
# NUM_DEFECTS     - number of defects to randomly generate
# NUM_CAMS        - number of cameras to randomly generate
# DEFECT_TYPES    - list of possible defect types ("PIT", "BUMP")
# VISIBLE_DEFECTS - table to store which defects are visible from which camera
# BOUNDING_BOXES  - list to store bounding boxes of generated defects
# SCENE           - scene from Blender file (used for image rendering)
# RES_X           - resolution of image x-axis
# RES_Y           - resolution of image y-axis
# -------------------------------------------------------------------------------

NUM_DEFECTS = 5
NUM_CAMS = 3
DEFECT_TYPES = ["PIT", "BUMP"]
VISIBLE_DEFECTS = np.zeros((NUM_CAMS, NUM_DEFECTS))
BOUNDING_BOXES = []

SCENE = bpy.context.scene

# setting render engine to CYCLES
SCENE.render.engine = "CYCLES"
bpy.data.worlds["World"].horizon_color = (0.8, 0.8, 0.8)

# scaling and setting resolution values
render = SCENE.render
RES_X = render.resolution_x*(SCENE.render.resolution_percentage / 100)
RES_Y = render.resolution_y*(SCENE.render.resolution_percentage / 100)


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
def record_visible(cameras, obj, bvh, defect_index):
    # obtaining all new defect vertices
    new_vertices = []
    for v in obj.data.vertices:
        if v.select:
            new_vertices.append(v.co.copy())

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
                co_2d = world_to_camera_view(SCENE, cam, coords)

                # -- IMAGE BOUNDARY DETECTION -- 

                if (co_2d[0] >= 0 and co_2d[0] <= 1 and co_2d[1] >= 0 and co_2d[1] <= 1):
                    # updating VISIBLE_DEFECTS
                    VISIBLE_DEFECTS[cam_index][defect_index] = 1
                    break


# function to record bounding boxes of visible defects
def record_bound_boxes(cameras, defect_index):
    bb = BOUNDING_BOXES[defect_index]
    
    # iterating through each randomly generated camera
    for cam_index in range(NUM_CAMS):
        cam = cameras[cam_index]

        # checking if the defect is visble
        if (VISIBLE_DEFECTS[cam_index][defect_index] == 1):
            # store x and y coordinates of each vertex of the bounding box in the camera space
            bound_xs = []
            bound_ys = []
            for vert_index in range(len(bb)):
                vert_coords = Vector(bb[vert_index])

                # computing coordinates in camera space
                co_2d = world_to_camera_view(SCENE, cam, vert_coords)
                x, y = round(RES_X*co_2d[0]), round(RES_Y*(1 - co_2d[1]))
                bound_xs.append(x)
                bound_ys.append(y)

            # using minimum and maximium x and y values to define bounding box in the camera space
            min_x = min(bound_xs)
            max_x = max(bound_xs)
            min_y = min(bound_ys)
            max_y = max(bound_ys)

            # clipping coordinates to lie within the image boundary
            min_x = max(0, min_x)
            max_x = min(RES_X, max_x)
            min_y = max(0, min_y)
            max_y = min(RES_Y, max_y)

            # writing image coordinates to text file
            binfile = open("renders/{}.txt".format(cam.name), "a")
            binfile.write("({}, {})  ({}, {})  ({}, {})  ({}, {})\n".format(min_x, min_y, min_x, max_y, max_x, min_y, max_x, max_y))
            binfile.close()


# function to subtract defect models from part model
def subtract_defect(obj, defect, defect_type):
    # selecting part model and setting it to active object
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.context.scene.objects.active = obj
    obj.select = True

    # adding boolean modifier to part model
    bpy.ops.object.modifier_add(type = "BOOLEAN")
    modify = obj.modifiers["Boolean"]
    if (defect_type == "PIT"):
        modify.operation = "DIFFERENCE"
    elif (defect_type == "BUMP"):
        modify.operation = "UNION"
    modify.object = defect

    # applying modifier and deleting blemish
    bpy.ops.object.modifier_apply(apply_as = "DATA", modifier = "Boolean")
    obj.select = False
    bpy.context.scene.objects.active = defect
    bpy.ops.object.delete(use_global = False)


# function to render images for each camera
def render_cameras(cameras):
    # iterating through each randomly generated camera
    for cam_index in range(NUM_CAMS):
        if (sum(VISIBLE_DEFECTS[cam_index][:]) > 0):
            cam = cameras[cam_index]

            # setting camera to active camera
            SCENE.camera = cam

            # saving image render to renders folder
            bpy.ops.render.render(write_still = True)
            bpy.data.images["Render Result"].save_render(filepath = "renders/{}.png".format(cam.name))


# function to create pit at given location
def build_pit(defect_loc, defect_index, align):
    # creating pit model
    name = "{}".format(defect_index)
    bpy.ops.mesh.primitive_uv_sphere_add(location = defect_loc)
    bpy.context.active_object.name = name
    defect = bpy.data.objects[name]

    # scaling defect to smaller size
    # NOTE: long axis should be defined along z-axis to align properly with rotation_euler
    defect.scale.x = 0.05
    defect.scale.y = 0.05
    defect.scale.z = 0.12    

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
def generate_defects(obj):


    # --- SETTING ENVIRONMENT VARIABLES ---


    # modifying settings to ensure that there are no errors with placement or edit mode
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)

    # generating BVH tree of part model to allow efficient raycasting
    bvh = tree.FromObject(obj, SCENE, epsilon = 0)


    # --- RANDOMLY GENERATING CAMERAS AROUND OBJECT MODEL ---


    # randomly generating origins for each camera using vertices of object model
    cam_verts = np.random.choice(obj.data.vertices, NUM_CAMS, replace = False)

    cameras = []
    # creating each camera, translating them away from the object, and re-orienting them to face the object
    for i in range (NUM_CAMS):
        bpy.ops.object.camera_add(location = 4*cam_verts[i].co)

        cam_name = "camera{}".format(i)
        bpy.context.active_object.name = cam_name
        cam = bpy.data.objects[cam_name]
        look_at(cam, obj.location)
        cameras.append(cam)

        # opening text file to store metadata for newly generated camera
        binfile = open("renders/{}.txt".format(cam_name), "w")
        binfile.write("Image Resolution: {}x{}\n".format(RES_X, RES_Y))
        binfile.close()

    
    # --- CREATING DEFECTS ON 3D MODEL ---

    
    # randomly sampling faces (WITH replacement) using weights based on surface area
    weights = calc_tess_weights(obj)
    rand_faces = np.random.choice(obj.data.tessfaces, NUM_DEFECTS, p = weights, replace = True)
    
    # creating a list to store normal vectors - this will allow us to align defects AFTER we have changed the geometry of the surface
    defect_normals = [np.array(face.normal) for face in rand_faces]

    # generating locations for each defect by randomly choosing a point on each face
    # NOTE: this implementation allows for multiple defects to be generated on the same face
    defect_locs = face_random_points(1, rand_faces)
    rand_faces = None

    # creating texture for microdisplacement
    bpy.data.textures.new("noise", type = "DISTORTED_NOISE")
    noise = bpy.data.textures["noise"]

    # placing defects at locations
    for defect_index in range(NUM_DEFECTS):
        defect_type = random.choice(DEFECT_TYPES)
        defect_loc = defect_locs[defect_index]

        # creating defect model and deforming surface of part model
        align = defect_normals[defect_index]
        if (defect_type == "PIT"):
            defect = build_pit(defect_loc, defect_index, align)
            BOUNDING_BOXES.append(defect.bound_box)
            subtract_defect(obj, defect, defect_type)
        elif (defect_type == "BUMP"):
            defect = build_bump(defect_loc, defect_index, align, noise)
            BOUNDING_BOXES.append(defect.bound_box)
            subtract_defect(obj, defect, defect_type)
        
        # recording metadata regarding visibility and location of defect
        record_visible(cameras, obj, bvh, defect_index)
        record_bound_boxes(cameras, defect_index)
        

    # --- RENDERING IMAGES ---


    render_cameras(cameras)
    

# running on test object
model = bpy.data.objects["Object"]
bpy.context.scene.objects.active = model
model.select = True

generate_defects(model)
bpy.ops.wm.save_as_mainfile(filepath = "bearing1.blend")