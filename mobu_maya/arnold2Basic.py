import maya.cmds as MC

blinn_LUT = { # source  :  target    dtype
    'color'             : ( 'color', "float3" ),
    'emissionColor'     : ( 'incandescence', "float3" ),
    'Kb'                : ( 'translucence', "float" ),
    'Kd'                : ( 'diffuse', "float" ),
    'Kr'                : ( 'reflectivity', "float" ),
    'KrColor'           : ( 'reflectedColor', "float3" ),
    'Ks'                : ( 'specularRollOff', "float" ),
    'KsColor'           : ( 'specularColor', "float3" ),
    'normalCamera'      : ( 'normalCamera', "float3" ),
    'opacity'           : ( 'transparency', "float3" ),
    'specularRoughness' : ( 'eccentricity', "float" ),
}
    
def aiToBlinn( ai_shader ):
    new_name = ai_shader + "_blinn"
    # create new shader
    blinn = MC.cmds( 'blinn', name=new_name, asShader=True )
    for source in blinn_LUT.keys():
        exists = MC.attributeQuery( source, node=aiShader, exists=True )
        if exists:
            target, dtype = blinn_LUT[ source ]
            
            spath = aiShader + "." + source
            tpath = blinn + "." + target
            
            value = MC.getAttr( spath )
            if dtype.endswith( "3" ):
                # 3vec
                MC.setAttr( tpath, value[0], type=dtype )
            else:
                # uni
                MC.setAttr( tpath, value )
        else:
            print( "'{}' not present in '{}'",  source, aiShader )
    MC.setAttr( blinn + ".emission", 1.0 )
    return blinn

# get all Arnold Shaders
al = MC.ls( exactType='aiStandard' )
print sl

for ai_shader in al:
    # TODO: Determine what type replacement shader we need?
    # convert to Blinn
    blinn = aiToBlinn( ai_shader )
    # Replace Shading group
    sg = MC.listConnections( ai_shader, type="shadingEngine" )
    MC.connectAttr( blinn + ".outColour", sg[0] + ".surfaceShader", force=True )
    MC.delete( ai_shader )

print( "Done" )