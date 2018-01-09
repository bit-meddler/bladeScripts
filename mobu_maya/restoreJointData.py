import maya.cmds as mc
import pickle
import os.path


# find skel data
file_pathname = mc.fileDialog( m=0, dm="*.pk", t="Open Skeleton Data" )

# load dumped T-pose
if os.path.isfile( file_pathname ): 
    skel_base = pickle.load( open( file_pathname, "rb" ) )
else:
    print "File Doesn't exist!"
    exit()
    
# recover each joint
for j in skel_base.keys():
    # Restore Angles
    mc.setAttr( "{}.{}".format( j, "rotateX" ), skel_base[ j ]["atr"][ "Rx" ] )
    mc.setAttr( "{}.{}".format( j, "rotateY" ), skel_base[ j ]["atr"][ "Ry" ] )
    mc.setAttr( "{}.{}".format( j, "rotateZ" ), skel_base[ j ]["atr"][ "Rz" ] )
    
    # set limits, angles
    mc.joint( j, edit=True, **skel_base[ j ]["jnt"] )
    
    # set limit activation
    mc.transformLimits( j, edit=True, **skel_base[ j ]["txl"] )
    

    
# Done
print "Restored: {}".format( file_pathname  )