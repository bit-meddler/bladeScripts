import numpy as np
import coreMaths as cm


class CameraSystem( object ):
    
    VENDORS = ( "Vicon", "Giant", "Optitrack" )
    
    def __init__( self ):
        # metadata
        self.camera_order = None
        self.cameras = {}
        self.source_file = ""
        self.hardware = ""

        
class GenericCamera( object ):
    
    def __init__( self ):
        # metadata
        self.type = ""
        self.name = ""
        self.hw_id = -1
        
        # cam hardware
        self.sensor_wh = [0, 0] # px
        
        # intrinsics
        self.K  = np.eye( 3, dtype=cm.FLOAT_T )
        
        # extrinsics
        self.R  = np.eye( 3, dtype=cm.FLOAT_T )
        self.T  = np.zeros( (3,),  dtype=cm.FLOAT_T )
        self.RT = np.zeros( (3,4), dtype=cm.FLOAT_T )
        
        # projection
        self.P  = np.zeros( (3,4), dtype=cm.FLOAT_T )
        self._p_computed = False


    def getFoV( self ):
        if( not self._p_computed ):
            return 0.
        # otherwise...
        # OpenGL formula = atan( 1/x ) * 2, but this way off the given data
        x = self.P[1,1]
        fov_r = np.arctan( x )
        print fov_r
        return np.degrees( fov_r )
