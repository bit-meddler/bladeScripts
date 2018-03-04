import maya.cmds as MC

# Encountered Arnold Shaders
arnold_shaders = ( "aiStandardSurface", "aiStandard" )

# Converters
def passThru( v ):
    return v
    
def flip1d( v ):
    return (1. - v)
    
def flip3d( v ):
    return ( (1. - v[0]), (1. - v[1]), (1. - v[2]) )

# Conversion LUT
blinn_LUT = { # source  :   target              dtype    conversion
    "color"             : ( "color",           "float3", passThru ),
    "emissionColor"     : ( "incandescence",   "float3", flip3d ),
    "Kb"                : ( "translucence",    "float",  passThru ),
    "Kd"                : ( "diffuse",         "float",  passThru ),
    "Kr"                : ( "reflectivity",    "float",  passThru ),
    "KrColor"           : ( "reflectedColor",  "float3", passThru ),
    "Ks"                : ( "specularRollOff", "float",  passThru ),
    "KsColor"           : ( "specularColor",   "float3", passThru ),
    "normalCamera"      : ( "normalCamera",    "float3", passThru ),
    "opacity"           : ( "transparency",    "float3", flip3d   ),
    "specularRoughness" : ( "eccentricity",    "float",  passThru ),
}
    
def aiToBlinn( ai_shader ):
    new_name = ai_shader + "_blinn"
    # create new shader
    blinn = MC.shadingNode( "blinn", name=new_name, asShader=True )
    for source in blinn_LUT.keys():
        exists = MC.attributeQuery( source, node=ai_shader, exists=True )
        if exists:
            target, dtype, convert = blinn_LUT[ source ]
            
            spath = ai_shader + "." + source
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
            print( "'{}' not present in '{}'",  source, ai_shader )
            
    # texture Experiment ?
    X = MC.attributeQuery( "Kd_color", node=ai_shader, exists=True )
    if X:
        print "KD_c", MC.getAttr( ai_shader + ".Kd_color" )
    return blinn

# ---------------------------- start 
# Session Settings
destructive = False
new_shaders = []

# get all Arnold Shaders
for shader_type in arnold_shaders:
    shaders = MC.ls( exactType=shader_type )
    for ai_shader in shaders:
        # TODO: Determine what type replacement shader we need - needs to be MoBu
        #       compatible and lightweight
        
        # convert to Blinn
        blinn = aiToBlinn( ai_shader )
        new_shaders.append( blinn )
        # Replace Shading group
        sg = MC.listConnections( ai_shader, type="shadingEngine" )
        print "SG:", sg
        MC.connectAttr( blinn + ".outColor", sg[0] + ".surfaceShader", force=True )
        if destructive:
            MC.delete( ai_shader )
            # if current sg has no more connections delete it too.

print( "Replaced {} Shaders".format( len( new_shaders ) ) )