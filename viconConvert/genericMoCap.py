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
        self.P_mats = None

        
    def marshel( self ):
        # for now, we'll build an array of P mats, in camera_order order
        collector = []
        for cam_id in self.camera_order:
            cam = self.data[ cam_id ]
            if( not cam._p_computed ):
                cam.computeMatrix()
            collector.append( cam.P )
        self.P_mats = np.array( collector )
        self.P_mats.flags.writeable = False # secure hashing
        
        
    def hash_( self ):
        self.marshel()
        return hash( self.P_mats.data )
    
    
class GenericCamera( object ):
    
    def __init__( self ):
        # metadata
        self.type = ""
        self.name = ""
        self.hw_id = -1
        
        # cam hardware
        self.sensor_wh = [0, 0] # px
        self._focal  = [0.,0.] # RAW focal length in sensor px
        self.px_aspect = 1.
        self._skew = 0.
        
        # intrinsics
        self._pp = [0.,0.]
        self.K  = np.eye( 3, dtype=cm.FLOAT_T )
        
        # extrinsics
        self.R  = np.eye( 3, dtype=cm.FLOAT_T )
        self.T  = np.zeros( (3,),  dtype=cm.FLOAT_T )
        self.RT = np.zeros( (3,4), dtype=cm.FLOAT_T )
        
        # projection
        self.P  = np.zeros( (3,4), dtype=cm.FLOAT_T )
        self._p_computed = False


    def computeMatrix( self ):
        # see also: http://run.usc.edu/cs420-s15/lec05-viewing/05-viewing-6up.pdf
        
        # compose RT
        self.RT[ :3, :3 ] = self.R
        self.RT[ :, 3 ]   = -np.matmul( self.R, self.T )
        
        # compose K
        a           = self.px_aspect
        x_pp, y_pp  = self._pp
        f_x, f_y    = self._focal
        k           = self._skew
        
        self.K = np.array(
            [ [ f_x,   k, x_pp ],
              [  0., f_y, y_pp ],
              [  0.,  0.,   1. ] ] , dtype=cm.FLOAT_T )
        
        # compute P = K.RT
        self.P = np.matmul( self.K, self.RT )
        self._p_computed = True

        
    def getFoV( self ):
        if( not self._p_computed ):
            return 0.
        # otherwise...
        # https://stackoverflow.com/questions/39992968/how-to-calculate-field-of-view-of-the-camera-from-camera-intrinsic-matrix
        # Assuming f is in px, and relates to sensor width
        hw    = self.sensor_wh[0] / 2.
        f     = sum( self._focal ) / 2. # average conflicting Hz/Vt FoVs.  Better would be an image circle calculation.
        fov_r = np.arctan( hw / f ) * 2.

        return np.degrees( fov_r )


    def projectPoint( self, point3D ):
        # !Hopefully! this is consistant between any correctly formed P matrix
        p_ = point3D
        if( len( point3D ) == 3 ):
            p_.append( 1. )
        x, y, z = np.matmul( self.P, np.array( p_ ) )
        return ( x/z, y/z )
