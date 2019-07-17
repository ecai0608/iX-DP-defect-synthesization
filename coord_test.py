import bpy
import bpy_extras

## for output readability in terminal window
print(' \n*******************************************\n ')

# Gather blender data
scene = bpy.context.scene
obj = bpy.context.object
co = bpy.context.scene.cursor_location

co_2d = bpy_extras.object_utils.world_to_camera_view(scene, obj, co)
print("2D Coords:", co_2d)

# Get Pixel coordinates
render_scale = scene.render.resolution_percentage / 100
render_size = (
        int(scene.render.resolution_x * render_scale),
        int(scene.render.resolution_y * render_scale),
        )
print("Pixel Coords:", (
      round(co_2d.x * render_size[0]),
      round(co_2d.y * render_size[1]),
      ))

print(' \n*******************************************\n ')