import bpy
from bpy_extras.object_utils import world_to_camera_view
from bpy_extras.mesh_utils import face_random_points
import numpy as np 

# *** TERMINAL COMAND: blender [myscene.blend] --background --python myscript.py ***
# *** SAVE FILE: bpy.ops.wm.save_as_mainfile(filepath = "[myscene.blend]") ***

# global parameters for number of defects and number of cameras
num_defects = 30
num_cams = 3

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
def render_cameras(scene, defect_locs):
    render = scene.render
    res_x = render.resolution_x
    res_y = render.resolution_y
    # TO DO: FACTOR IN RES %
    # render_scale = scene.render.resolution_percentage / 100
    
    # iterating through all cameras to render images
    for obj in bpy.data.objects:
        if (obj.type == "CAMERA"):
            # setting camera to active camera
            bpy.context.scene.camera = obj

            # saving image render to "renders" folder
            bpy.ops.render.render(write_still = True)
            bpy.data.images["Render Result"].save_render(filepath = ("renders/%s.png" % obj.name))

            # writing image coordinates to text file
            binfile = open(("renders/%s.txt" % obj.name), "w")
            binfile.write("Image Resolution: %sx%s\n" % (res_x, res_y))
            binfile.write("Image Coordinates:\n")
            for i, coords in enumerate(defect_locs):
                # computing image coordinates
                co_2d = world_to_camera_view(scene, obj, coords)
                x, y = round(res_x*co_2d[0]), round(res_y*(1 - co_2d[1]))

                # writing image resolution and coordinates to text file
                binfile.write("     %d: %s,%s\n" % (i, x, y))


# function to blemish object in given scene
def generate_defects(obj):
    # modifying settings to ensure there are no errors with placement or edit mode
    bpy.ops.object.mode_set(mode = "OBJECT")
    bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)


    # --- CREATING BLEMISHES ON 3D MODEL ---
    
    weights = calc_tess_weights(obj)

    print("SAMPLING FACES")
    # randomly sampling faces (WITH replacement) using weights
    rand_faces = np.random.choice(obj.data.tessfaces, num_defects, p = weights, replace = True)
    print("CHOOSING POINTS")
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


    # setting scene/resolution variables for clarity
    scene = bpy.context.scene
    render_cameras(scene, defect_locs)
    

# running on test object
test_object = bpy.data.objects["Pistons"]
test_object.select = True
generate_defects(test_object)