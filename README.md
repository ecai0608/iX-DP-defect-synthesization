# iX-DP-defect-synthesization

Possible improvements to make:
- (DONE) make camera placement uniformly random with respect to bounding sphere
- (DONE) randomize rotation of object part so that shots from the same angle do not always have the same background
- need to fix issue of boolean difference modifier not working properly all the time (can check if object is manifold)



If we have time:
- randomize HDRI background and grunge texture (might have to find a couple more)
- swap out all operator calls for alternative implementations - operator calls always reload the blender scene, which can drastically increase runtime
- add noise to pits
- implement bumps


Very problematic but very hard to fix:
- need to 