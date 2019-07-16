import numpy as np

##############################################
#
#   3D Functions
#
##############################################


def TripleSine(x,y,z):
	return np.sin(x)+ np.sin(y) + np.sin(z)



def customFunc(x, y, z):
    return x + y + z




def CustomFunction(x,y,z):
	#Replace the following line with CustomData=YourFunction.
	CustomData=customFunc(x, y, z)
	return float(CustomData)

##############################################
#
#   USER PARAMETERS
#
##############################################

#X, Y, Z, dimensions (resolution) of the voxel datacube.
nx, ny, nz = 100,100,100
header =  np.array([nx,ny,nz,1])

min_x,min_y,min_z=-1,-1,-1
max_x,max_y,max_z=1,1,1

#############################################
#
#   VOXELIZER EXAMPLE
#
#############################################

#Fill the data array based on a function.
data=[]

#Go over the x,y,z coordinates from the min values to the max values.
#We start with the z coordinate, then the y coordinates, finally the x coordinate.

for k in range(nz):
    #z=min_z + (max_z-min_z)*float(k)/float(nz)
    for j in range(ny):
        #y=min_y + (max_y-min_y)*float(j)/float(ny)
        for i in range(nx):
            # x=min_x + (max_x-min_x)*float(i)/float(nx)
            data.append(CustomFunction(i,100*j,100*100*k))
data=np.array(data)

print(data.shape)
print(data)


#Normalization of the dataset to have values between 0-1
data=data-np.min(data)
data=data/np.max(data)


#Open binary file. Write Header. Write Data.
binfile = open('Example.bvox','wb')
header.astype('<i4').tofile(binfile)
data.astype('<f4').tofile(binfile)
binfile.close()