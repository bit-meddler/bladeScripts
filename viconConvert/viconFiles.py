"""
    collection of functions to read vicon data, staring simple with the XML stuff
        XCP
        VSK
        VSS
    Then on to the hard one, x2d
        X2D
"""

import numpy as np
from xml.dom import minidom
from genericMoCap import CameraSystem, GenericCamera
import coreMaths as cm


class ViconCamera( GenericCamera ):

    def __init__( self, input_dict=None ):
        # super
        super( ViconCamera, self ).__init__()
        
        # camera data
        self.hw_id       = -1 # uniue id.  data is in id order in the x2d
        self.vicon_name  = ""
        self.px_aspect   = -1 # 
        self.sensor_type = ""
        self.user_id     = -1
        
        # raw calibration data
        self._pp    = [0., 0.] # px
        self._radial= [0., 0.] # k1, k2
        self._pos   = [0., 0., 0.] # tx, ty, tz
        self._rotQ  = [0., 0., 0., 0.] # uartonions [x,y,z,w]
        self._err   = 0. # rms reprojection error
        self._skew  = 0. # ??
        self._focal = 0. # f in sensor px?
        
        # Vicon specific matrix
        self.Q  = cm.Quaternion()

        if( input_dict is not None ):
            self.setFromDict( input_dict )

            
    def setFromDict( self, dict ):
        self.hw_id       = dict["DEVICEID"]
        self.type        = dict["TYPE"]
        self.vicon_name  = dict["NAME"]
        self.px_aspect   = dict["PIXEL_ASPECT_RATIO"]
        self.sensor_type = dict["SENSOR"]
        self.sensor_wh   = dict["SENSOR_SIZE"]
        self.user_id     = dict["USERID"]
        self._pp         = dict["PRINCIPAL_POINT"]
        self._radial     = dict["VICON_RADIAL"]
        self._skew       = dict["SKEW"]
        self._focal      = [dict["FOCAL_LENGTH"], dict["FOCAL_LENGTH"]/self.px_aspect]
        self._pos        = dict["POSITION"]
        self._rotQ       = dict["ORIENTATION"]
        self._err        = dict["IMAGE_ERROR"]

        # setup some calibration settings
        self.T = self._pos
        
        x, y, z, w = self._rotQ
        self.Q.setQ( x, y, z, w )
        self.R = self.Q.toRotMatT()
        
        self.computeMatrix()


    def undistort( self, point ):
        # As Vicon doesn't use NDCs the undistort is computed per det - dumb!
        a          = self.px_aspect
        w1, w2     = self._radial
        x_pp, y_pp = self._pp
        # Again from the CaraPost Refference pdf
        x_r, y_r = point
        dp = [ x_r - x_pp, a * ( y_r - y_pp ) ]
        print dp
        r = np.linalg.norm( dp )
        print r
        s = 1 + w1 * r**1 + w2 * r**2
        print s
        ud = [ s * dp[0] + x_pp, (s * dp[1] + y_pp)/a ]
        print ud

    
    def __str__( self ):
        tx, ty, tz = self.T
        rx, ry, rz = np.degrees( cm.mat34.mat2Angles( self.R.T ) )
        fov = self.getFoV()
        return "Vicon Camera {}, at Tx:{}, Ty:{}, Tz:{}; Rx:{}, Ry:{}, Rz:{}; FoV:{} Deg".format(
            self.hw_id, tx, ty, tz, rx, ry, rz, fov )

        
class CalXCPReader( object ):

    CASTS = {
        # Intrinsics
        "PRINCIPAL_POINT"    : lambda x: map( float, x.split() ),
        "VICON_RADIAL"       : lambda x: map( float, x.split() ),
        "SKEW"               : float,
        "FOCAL_LENGTH"       : float,
        # extrinsics
        "ORIENTATION"        : lambda x: np.array( x.split(), dtype=cm.FLOAT_T),
        "POSITION"           : lambda x: np.array( x.split(), dtype=cm.FLOAT_T),
        # Meta Data
        "SENSOR_SIZE"        : lambda x: map( int, x.split() ),
        "PIXEL_ASPECT_RATIO" : float,
        "DEVICEID"           : int,
        "USERID"             : int,
        "NAME"               : lambda x: x, # passthru
        "SENSOR"             : lambda x: x, # passthru
        "TYPE"               : lambda x: x, # passthru
        "IMAGE_ERROR"        : float,
    }
    
    CAMERA_ID_KEY = "DEVICEID"
    CAMERA_ATTERS_HARDWARE = ( "DEVICEID", "NAME", "PIXEL_ASPECT_RATIO", "SENSOR", "SENSOR_SIZE", "SKEW", "TYPE", "USERID" )
    CAMERA_ATTERS_CALIBRATION = ( "FOCAL_LENGTH", "IMAGE_ERROR", "ORIENTATION", "POSITION", "PRINCIPAL_POINT", "VICON_RADIAL" )
    
    def __init__( self ):
        self.reset()


    def reset( self ) :
        self.data = {}
        self.system = CameraSystem()
        

    def read( self, file_path=None ):
        if( file_path is None ):
            print( "Error: no file supplied" )
            return -1
            
        self.reset()
        mode = "XCP"
        
        self.system.source_file = file_path
        
        if( file_path.lower().endswith( ".xcp" ) ):
            mode = "XCP"
        elif( file_path.lower().endswith( ".cp" ) ):
            print( "Error: .cp not yet supported" )
            return -1
        
        if( mode == "XCP" ):
            XD = minidom.parse( file_path )
            cameras = XD.getElementsByTagName( "Camera" )
            
            for camera in cameras:
                # create dict
                cid = camera.attributes[ CalXCPReader.CAMERA_ID_KEY ].value.encode( "ascii" )
                self.data[ cid ] = {}
                # load camera data
                for entry in CalXCPReader.CAMERA_ATTERS_HARDWARE:
                    self.data[ cid ][ entry ] = camera.attributes[ entry ].value.encode( "ascii" )

                # load calibration data
                kf_list = camera.getElementsByTagName( "KeyFrame" )
                if( len( kf_list ) > 0 ):
                    for entry in CalXCPReader.CAMERA_ATTERS_CALIBRATION:
                        self.data[ cid ][ entry ] = kf_list[0].attributes[ entry ].value.encode( "ascii" )
                        
                # cast
                for atter, cast in CalXCPReader.CASTS.iteritems():
                    self.data[ cid ][ atter ] = cast( self.data[ cid ][ atter ] )
                
        for cam_id, cam_data in self.data.iteritems():
            camera = ViconCamera( cam_data )
            self.system.cameras[ int( cam_id ) ] = camera

        self.system.camera_order = sorted( self.system.cameras.keys() )

        
def genHSL( system ):
    pass

    
if( __name__ == "__main__" ):
    # testing reading an xml
    import os
    import glob

    file_path = r"C:\temp\xcp_examples"

    center_test = {   18955 : [    1.4343, 1669.543, 2405.95  ],
                    2107343 : [ -178.20,   -408.21,   142.86  ],
                    2106443 : [  -65.095,    80.5978,  25.967 ]
    }

    cal_reader = CalXCPReader()
    if False:
        cal_list = glob.glob( os.path.join( file_path, "*.xcp" ) )
        retorts = ""
        for cal in cal_list:
            print( "Testing:'{}'---------------------------------".format( os.path.basename( cal ) ) )
            cal_reader.reset()
            cal_reader.read( cal )
            
            for cid in cal_reader.system.camera_order:
                cam = cal_reader.system.cameras[ cid ]
                #print( cam )
                if( cid in center_test ):
                    retorts += "Camera {} projected to {} (sensor size {})\n".format(
                        cid,
                        cam.projectPoint( center_test[ cid ] ),
                        cam.sensor_wh )
    if False:
        # Specific test
        cal_reader.read( os.path.join( file_path, "170202_WictorK_Body_ROM_01.xcp" ) )
        known_cam = 2107343
        # examining this in blade, the rot should be [166.497, -84.23, -119.151]
        cam = cal_reader.system.cameras[ known_cam ]
        
        print np.degrees( cam.Q.toAngles()  )
        print np.degrees( cam.Q.toAngles2() )
        print np.degrees( cam.Q.toAngles3() )
        print retorts
        print cam

    file_path = r"C:\temp\converter"
    cal_reader.read( os.path.join( file_path, "seed_aa_01.xcp" ) )
    from optiFiles import CalTxWriter
    ctr = CalTxWriter( cal_reader.system )
    ctr.unitConvert = True
    ctr.conversion  = 1./1000.
    ctr.generate(transposeR=True)
    ctr.write( os.path.join( file_path, "seed_aa_01.xcp" ) )
