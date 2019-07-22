import bpy
from bpy_extras.object_utils import world_to_camera_view
from bpy_extras.mesh_utils import face_random_points

from mathutils import Vector
from mathutils.bvhtree import BVHTree as tree

import numpy as np 

# *** TERMINAL COMAND: blender [myscene.blend] --background --python myscript.py ***
# *** SAVE FILE: bpy.ops.wm.save_as_mainfile(filepath = "[myscene.blend]") ***

# global parameters for number of defects and number of cameras
num_defects = 20
num_cams = 5

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
def render_cameras(scene, obj, defect_locs):
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

            # saving image render to "renders" folder
            bpy.ops.render.render(write_still = True)
            bpy.data.images["Render Result"].save_render(filepath = ("renders/%s.png" % cam.name))

            # recording metadata for camera
            record_visible(scene, cam, bvh, defect_locs, res_x, res_y)
            """
            # writing image coordinates to text file TO DO: ONLY RECORD METADATA OF "VISIBLE" POINTS
            binfile = open(("renders/%s.txt" % cam.name), "w")
            binfile.write("Image Resolution: %sx%s\n" % (res_x, res_y))
            binfile.write("Image Coordinates:\n")
            for i, coords in enumerate(defect_locs):
                # computing image coordinates
                co_2d = world_to_camera_view(scene, cam, coords)
                x, y = round(res_x*co_2d[0]), round(res_y*(1 - co_2d[1]))

                # writing image resolution and coordinates to text file
                binfile.write("     %d: %s,%s\n" % (i, x, y))
            """


# function to record metadata for visible defects for a specific camera
def record_visible(scene, cam, bvh, defect_locs, res_x, res_y):
    # opening metadata file for given camera
    binfile = open(("renders/%s.txt" % cam.name), "w")
    binfile.write("Image Resolution: %sx%s\n" % (res_x, res_y))
    binfile.write("Image Coordinates:\n")

    # counter to keep track of visible defects (will probably remove later - this is just to check the script)
    i = 0

    # looping through each defect location in 3D space
    for coords in defect_locs:

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
                binfile.write("     %d: %s,%s\n" % (i, x, y))            
    binfile.close()


# function to blemish object in given scene
def generate_defects(obj):
    # modifying settings to ensure there are no errors with placement or edit mode
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)


    # --- CREATING BLEMISHES ON 3D MODEL ---
    
    # randomly sampling faces (WITH replacement) using weights
    weights = calc_tess_weights(obj)
    rand_faces = np.random.choice(obj.data.tessfaces, num_defects, p = weights, replace = True)

    # generating locations for each blemish
    defect_locs = face_random_points(1, rand_faces)

    # marking all defects with blemishes
    for i, loc in enumerate(defect_locs):        
        name = "{}".format(i)
        bpy.ops.mesh.primitive_uv_sphere_add(location = loc)
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
    for i, vert in enumerate(cam_verts):
        bpy.ops.object.camera_add(location = 4*vert.co)

        cam_name = "camera{}".format(i)
        bpy.context.active_object.name = cam_name
        cam = bpy.data.objects[cam_name]
        look_at(cam, obj.location)
    

    # --- RENDERING IMAGES AND SAVING METADATA FOR EACH CAMERA ---


    # setting render engine to CYCLES
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'

    # adjusting resolution and environment lighting
    scene.render.resolution_percentage = 50
    bpy.data.worlds["World"].horizon_color = (0.8, 0.8, 0.8)

    # rendering images
    render_cameras(scene, obj, defect_locs)
    

# running on test object
test_object = bpy.data.objects["test_object"]
test_object.select = True
bpy.context.scene.objects.active = test_object
generate_defects(test_object)
bpy.ops.wm.save_as_mainfile(filepath = "testpoly1.blend")