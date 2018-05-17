""" On the other hand, lets convert an optitrack calibration to vicon, and a Projection matrix """

import numpy as np
import coreMaths as cm
from genericMoCap import CameraSystem, GenericCamera
import os

class OptiCamera( GenericCamera ):

    def __init__( self, input_dict=None ):
        # super
        super( OptiCamera, self ).__init__()
        
        # camera data
        self.hw_id = -1 # uniue id.  data is in id order in the x2d
        
        # raw calibration data
        self._pp    = [0., 0.] # px
        self._radial= [0., 0., 0.] # k1, k2, K3
        self._pos   = [0., 0., 0.] # tx, ty, tz
        self._focal = [0., 0.] # f in sensor px (h,v)

        if( input_dict is not None ):
            self.setFromDict( input_dict )

            
    def setFromDict( self, dict ):
        self.hw_id     = dict["CameraSerial"]
        self.sensor_wh = [ dict["ImagerPixelWidth"], dict["ImagerPixelHeight"] ]
        self._pp       = [ dict["LensCenterX"], dict["LensCenterY"] ]
        self._radial   = [ dict["KC1"], dict["KC2"], dict["KC3"] ]
        self._focal    = [ dict["HorizontalFocalLength"], dict["VerticalFocalLength" ] ]
        
        # T
        self.T = np.array( [
            dict[ "PositionX" ],
            dict[ "PositionY" ],
            dict[ "PositionZ" ]], dtype=cm.FLOAT_T
        )
        
        # R
        M = np.zeros( (9), dtype=cm.FLOAT_T )
        for i in range( 9 ):
            M[i] = dict[ "Orientation{}".format( i ) ]
        self.R = M.reshape( (3,3) ).T
        
        # Compute K, RT, KRT
        self.computeMatrix()


    def computeMatrix( self ):
        self.RT[ :3, :3 ] = self.R
        self.RT[ :, 3 ]   = -np.matmul( self.R, self.T )
        
        # compose K
        a           = 1. #self.px_aspect
        x_pp, y_pp  = self._pp
        f           = self._focal
        k           = 1. #self._skew
        
        self.K = np.array(
            [ [  f,     k, x_pp ],
              [ 0., (f/a), y_pp ],
              [ 0.,    0.,   1. ] ] , dtype=cm.FLOAT_T )
        
        # compute P = K.RT
        self.P = np.matmul( self.K, self.RT )
        self._p_computed = True
        
        
    def __str__( self ):
        tx, ty, tz = self.T
        rx, ry, rz = np.degrees( cm.mat34.mat2Angles( self.R ) )
        fov = self.getFoV()
        return "Optitrack Camera {}, at Tx:{}, Ty:{}, Tz:{}; Rx:{}, Ry:{}, Rz:{}; FoV:{}Deg".format(
            self.hw_id, tx, ty, tz, rx, ry, rz, fov )
            
            
class CalTxReader( object ):

    CASTS = {
        "CameraSerial"      : int,
        "ImagerPixelWidth"  : int,
        "ImagerPixelHeight" : int
    }
    
    def __init__( self ):
        self.data = {}
        self.system = CameraSystem()

    @staticmethod
    def optiCast( key, val ):
        if( key in CalTxReader.CASTS ):
            return CalTxReader.CASTS[ key ]( val )
        else:
            return float( val )

        
    def read( self, file_fq ):
        cur_cam = {}
        fh = open( file_fq, "r" )
        self.system.source_file = file_fq
        line = ""
        while( True ):
            line = fh.readline()
            if( not line ): # EOF
                break
            if( len( line ) < 2 ):
                continue # skip block separations / blank lines
            key, val = line.split(",")
            if( key in cur_cam ):
                # new block!, always start at CameraSerial
                assert( key == "CameraSerial" )
                cur_cam = {}
                cid = int( val )
                self.system.camera_order.append( cid )
                self.data[ cid ] = cur_cam
            cur_cam[ key ] = self.optiCast( key, val )
        fh.close()
        
        # marshel
        for cam_id, cam_data in self.data.iteritems():
            camera = OptiCamera( cam_data )
            self.system.cameras[ int( cam_id ) ] = camera
        
        
            
if( __name__ == "__main__" ):
    file_fq = r"C:\temp\opti\Cal.txt"
    c_reader = CalTxReader()
    c_reader.read( file_fq )
    cam_id = c_reader.system.camera_order[0]
    m2a  = cm.mat34.mat2Angles
    print "serial", c_reader.system.cameras[ cam ].hw_id
    print "ColMaj", np.degrees( m2a( c_reader.system.cameras[ cam ].R ) )
    print "RowMaj", np.degrees( m2a( c_reader.system.cameras[ cam ].R.T ) )
    #print mats[ cam ][ "P" ]
