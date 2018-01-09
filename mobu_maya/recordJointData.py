import maya.cmds as mc
import pickle

# get location to stash the skeleton data
file_pathname = mc.fileDialog( m=1, dm="*.pk", dfn="skeleton_data", t="Save Skeleton Paramiters As..." )

# find *all* joints in scene
# TODO: Only store selected, or work out root node of selected item and store that root's children
joint_list = mc.ls( type=['joint'] )
# place to stash base skeleton settings in
skel_base = {}
# inspect each joint
for j in joint_list:
    # Prep empty record
    skel_base[ j ] = { "jnt":{}, "txl":{}, "atr":{} }
    
    # joint & transform data
    ax,           ay,               az = mc.joint( j, query=True,  ax=True,  ay=True,  az=True ) # angle
    lxl,   lxh,  lyl,  lyh,  lzl,  lzh = mc.joint( j, query=True,  lx=True,  ly=True,  lz=True ) # limits
    lsxl, lsxh, lsyl, lsyh, lszl, lszh = mc.joint( j, query=True, lsx=True, lsy=True, lsz=True ) # limit active?
    # Rot-angles
    Rx = mc.getAttr( "{}.{}".format( j, "rotateX" ) )
    Ry = mc.getAttr( "{}.{}".format( j, "rotateY" ) )
    Rz = mc.getAttr( "{}.{}".format( j, "rotateZ" ) )
    
    # Stash - keys are 'short names' for the cmd, so can be passed as kwags
    skel_base[ j ]["jnt"][ "lx"   ]  = ( lxl, lxh )
    skel_base[ j ]["jnt"][ "ly"   ]  = ( lyl, lyh )
    skel_base[ j ]["jnt"][ "lz"   ]  = ( lzl, lzh )
    skel_base[ j ]["txl"][ "erx"  ]  = (lsxl, lsxh)
    skel_base[ j ]["txl"][ "ery"  ]  = (lsyl, lsyh)
    skel_base[ j ]["txl"][ "erz"  ]  = (lszl, lszh)
    # clamp rotation values that are quite small to Zero
    # TODO: compare setAttr("%s.rotateX"%j, Rx) against joint(j, ax)
    skel_base[ j ]["jnt"][ "ax"   ]  = ax if ax**2 > 1e-6 else 0.0
    skel_base[ j ]["jnt"][ "ay"   ]  = ay if ay**2 > 1e-6 else 0.0
    skel_base[ j ]["jnt"][ "az"   ]  = az if az**2 > 1e-6 else 0.0
    skel_base[ j ]["atr"][ "Rx"   ]  = Rx if Rx**2 > 1e-6 else 0.0
    skel_base[ j ]["atr"][ "Ry"   ]  = Ry if Ry**2 > 1e-6 else 0.0
    skel_base[ j ]["atr"][ "Rz"   ]  = Rz if Rz**2 > 1e-6 else 0.0
    
#print skel_base
        
# dump full skeleton data
pickle.dump( skel_base, open( file_pathname, "wb" ) )
print "Saved '{}'".format( file_pathname )

# unlock joint limts
print "Unlocking *ALL* Limits"
for j in joint_list:
    mc.transformLimits( j, edit=True, erx=(False,False), ery=(False,False), erz=(False,False) )
print "Done"