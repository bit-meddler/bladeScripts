import maya.cmds as mc

# Imitation of Mark's footieFudger.
#   1) Select 'child' or target, then 'parent' or source
#   2) set play range to be the set of frames that need fudging
#   3) run the script!

selected = mc.ls( selection=True )
if( len( selected ) != 2 ):
    print( "Select 'child' then 'parent' node, 2 Nodes are needed!" )
    exit()
    
child_obj  = selected[0]
parent_obj = selected[1]

f_min = int( mc.playbackOptions( query=True, min=True ) )
f_max = int( mc.playbackOptions( query=True, max=True ) )

for f in xrange( f_min, f_max ):
    mc.currentTime( f )
    parent_xform = mc.xform( parent_obj, ws=True, m=True, query=True )
    mc.xform( child_obj, ws=True, m=parent_xform )
    mc.setKeyframe( child_obj )
