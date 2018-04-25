import maya.cmds as mc

def getCpPos( shape ) :
    pos_list = []
    idx_list = mc.getAttr( shape + ".cp", multiIndices=True )
    for i in idx_list :
        pos = mc.xform( "{}.cp[{}]".format( shape, i ), query=True, translation=True, worldSpace=True )
        pos_list.append( pos )
    return pos_list
     
def getSelected( all=False ):
    sel = mc.ls( selection=True )
    if( len( sel ) < 1 ):
        print( "Error! Nothing Selected" )
        return
    if( all ):
        return sel
    else:
        return sel[0]
        
print getCpPos( getSelected() )