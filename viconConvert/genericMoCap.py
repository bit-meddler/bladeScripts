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
        # marsheled data for computation
        self.num_cameras = 0
        self.P_mats = None
        self.C_dims = None

        
    def marshel( self ):
        # for now, we'll build an array of P mats, in camera_order order
        self.num_cameras = len( self.camera_order )
        self.P_mats = np.zeros( (self.num_cameras, 3, 4), dtype=cm.FLOAT_T )
        self.C_dims = np.zeros( (self.num_cameras, 2),    dtype=cm.INT_T )
        
        for idx, cam_id in enumerate( self.camera_order ):
            cam = self.cameras[ cam_id ]
            if( not cam._p_computed ):
                cam.computeMatrix()
            self.P_mats[ idx, :, : ] = cam.P
            self.C_dims[ idx, : ]    = cam.sensor_wh
        self.P_mats.flags.writeable = False # secure hashing
        
        
    def hash_( self ):
        self.marshel()
        return hash( self.P_mats.data )


    def projectPoints( self, points, labels ):
        """ points is a list of x,y,z points, they will be projected into all cameras
            labels is a list of ID numbers for the points

            returns
            projections - array of camera projections
            ids - labels of projections in each camera, 0 or -1 if no label or out of camera
        """
        # bit of sanity checking
        projections = None
        ids = None
        if( self.P_mats is None ):
            self.marshel()
        if( self.num_cameras < 1 ):
            return projections, ids

        num_points = len( points )
        if( num_points < 1 ):
            return projections, ids

        # collect projections
        projections = np.zeros( (self.num_cameras, num_points, 3), dtype=cm.FLOAT_T )

        # project each camera
        for idx, P in enumerate( self.P_mats ):
            projections[ idx, :, : ]  = np.matmul( points, P[:,:3] )
            projections[ idx, :, : ] += P[:,3]
        # rescale to u,v,1
        projections[ :, :, :2 ] /= projections[ :, :, 2 ]

        # police projections outside of sensor ???
        allowed = []
        #
        return projections, ids

    
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


    def projectPoint3D( self, point ):
        # !Hopefully! this is consistant between any correctly formed P matrix
        M  = np.matmul( self.P[:,:3] , point )
        M += self.P[:,3]
        M[:2] /= M[2]
        return ( M[0], M[1] )
