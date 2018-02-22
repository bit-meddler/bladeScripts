import maya.cmds as MC

blinn_LUT = { # source  :  target    dtype    conversion
    'color'             : ( 'color', "float3", lambda x: x ),
    'emissionColor'     : ( 'incandescence', "float3", lambda x: x ),
    'Kb'                : ( 'translucence', "float", lambda x: x ),
    'Kd'                : ( 'diffuse', "float", lambda x: x ),
    'Kr'                : ( 'reflectivity', "float", lambda x: x ),
    'KrColor'           : ( 'reflectedColor', "float3", lambda x: x ),
    'Ks'                : ( 'specularRollOff', "float", lambda x: x ),
    'KsColor'           : ( 'specularColor', "float3", lambda x: x ),
    'normalCamera'      : ( 'normalCamera', "float3", lambda x: x ),
    'opacity'           : ( 'transparency', "float3", lambda x: 1.0 - x ),
    'specularRoughness' : ( 'eccentricity', "float", lambda x: x ),
}
    
def aiToBlinn( ai_shader ):
    new_name = ai_shader + "_blinn"
    # create new shader
    blinn = MC.shadingNode( 'blinn', name=new_name, asShader=True )
    for source in blinn_LUT.keys():
        exists = MC.attributeQuery( source, node=aiShader, exists=True )
        if exists:
            target, dtype, convert = blinn_LUT[ source ]
            
            spath = aiShader + "." + source
            tpath = blinn + "." + target
            
            value = MC.getAttr( spath )
            
            if dtype.endswith( "3" ):
                # 3vec
                converted = convert( value[0] )
                MC.setAttr( tpath, *converted, type=dtype )
            else:
                # uni
                MC.setAttr( tpath, convert( value ) )
        else:
            print( "'{}' not present in '{}'",  source, aiShader )
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
    MC.connectAttr( blinn + ".outColor", sg[0] + ".surfaceShader", force=True )
    MC.delete( ai_shader )

print( "Done" )