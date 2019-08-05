# iX-DP-defect-synthesization

Possible improvements to make:
- (DONE) make camera placement uniformly random with respect to bounding sphere
- (DONE) randomize rotation of object part so that shots from the same angle do not always have the same background
- (DONE) need to fix issue of boolean difference modifier not working properly all the time (can check if object is manifold)
        -(DONE) still need to update metadata generation - metadata needs to not only specify which camera, but which iteration as well.
        -(DONE) annotations.csv needs to be opened outside of generate_defects()



If we have time:
- (DONE) randomize HDRI background (might have to find a couple more)
- swap out all operator calls for alternative implementations - operator calls always reload the blender scene, which can drastically increase runtime
- add noise to pits
- implement bumps
- right now, it is technically possible for a camera to be generated inside of the model - this is bad for obvious reasons


Very problematic but very hard to fix:
- (DONE?) need to completely get rid of EXCEPTION_ACCESS_VIOLATION errors. These completely crash blender and have no traceback making them EXTREMELY difficult to deal with. Since we're most likely running everything from one script, running into one of these errors can be very costly since we will have to start everything over again. The primary cause for this error seems to be mishandled memory allocation - blender seems to pass many variables regarding object data by reference rather than by value. Need to go back through the script and extract data ASAP in any instance where a variable (like the part model, or a defect model) will likely be modified down the road.