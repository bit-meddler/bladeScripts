""" On the other hand, lets convert an optitrack calibration to vicon, and a Projection matrix """

import numpy as np
import coreMaths as cm
import os

class CalTxReader( object ):

    CASTS = {
        #"CameraSerial" : int,
        "ImagerPixelWidth" : int,
        "ImagerPixelHeight" : int
    }
    
    def __init__( self ):
        self.cam_data = {}
        self.cam_mats = {}
        self.cam_order = []


    def probablyFloat( key, val ):
        if( key in self.CASTS ):
            return self.CASTS[ key ]( val )
        else:
            return float( val )

        
    def read( self, file_fq ):
        cur_cam = {}
        fh.open( file_fq, "r" )
        line = "boot"
        while( True ):
            line = fh.readline()
            if( not line ):
                break
            key, val = line.split(",")
            if( key in cur_cam ):
                # new block!, always start at CameraSerial
                assert( key == "CameraSerial" )
                cur_cam = {}
                cid = int( CameraSerial )
                cam_order.append( cid )
                self.cam_data[ cid ] = cur_cam
            cur_cam[ key ] = probablyFloat( key, val )

            
    def compute( self ):
        for cid in self.cam_order:
            self.cam_mats[ cid ] = {}
            cam = self.cam_mats[ cid ]
            raw = self.cam_data[ cid ]
            # T
            cam[ "T" ] = np.array( [
                raw[ "PositionX" ],
                raw[ "PositionY" ],
                raw[ "PositionZ" ]], dtype=cm.FLOAT_T
            )
            
            # R
            cam[ "R" ] = np.zeros( (9), dtype=cm.FLOAT_T )
            for i in range( 9 ):
                cam[ "R" ][i] = raw[ "Orientation{}".format( i ) ]
            cam[ "R" ].reshape( (3,3) ) # To tanspose, or not transpose
            
            # RT
            cam[ "RT" ] = np.zeros( (3,4), dtype=cm.FLOAT_T )
            cam[ "RT" ][:,3] = -np.matmul( cam[ "R" ], cam[ "T" ] )
            cam[ "RT" ][:3,:3] = cam[ "R" ]
            
            # K
            cam[ "T" ] = np.array( [
                [ raw[ "HorizontalFocalLength" ],                           0., raw[ "LensCenterX" ] ],
                [                             0., raw[ "VerticalFocalLength" ], raw[ "LensCenterY" ] ],
                [                             0.,                           0.,                 1. ] ],
                dtype=cm.FLOAT_T
            )
            
            # KRT
            cam[ "P" ][:,3] = np.matmul( cam[ "K" ], cam[ "RT" ] )
            
if( __name__ == "__main__" ):
    pass
