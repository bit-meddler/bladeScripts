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

        # set to defaults (not included in NP calibration)
        self.px_aspect = 1.
        self._skew = 1.
        
        if( input_dict is not None ):
            self.setFromDict( input_dict )

            
    def setFromDict( self, dict ):
        self.hw_id     = dict["CameraSerial"]
        self.sensor_wh = [ dict["ImagerPixelWidth"], dict["ImagerPixelHeight"] ]
        self.px_aspect = self.sensor_wh[0] / self.sensor_wh[1]
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
        self.system.camera_order = []
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

        
class CalTxWriter( object ):

    EXPORT_ORDER = ( "CameraSerial", "LensCenterX", "LensCenterY", "HorizontalFocalLength",
                     "VerticalFocalLength", "KC1", "KC2", "KC3", "Tangential0", "Tangential1",
                     "ImagerPixelWidth", "ImagerPixelHeight", "PositionX", "PositionY",
                     "PositionZ", "Orientation0", "Orientation1", "Orientation2",
                     "Orientation3", "Orientation4", "Orientation5", "Orientation6",
                     "Orientation7", "Orientation8" )
    
    EXPORT_CASTS = {
        "CameraSerial" : lambda x: x.hw_id,
        "LensCenterX" : lambda x: x._pp[0],
        "LensCenterY" : lambda x: x._pp[1],
        "HorizontalFocalLength" : lambda x: x._focal[0],
        "VerticalFocalLength" : lambda x: x._focal[1]/x.px_aspect,
        "KC1" : lambda x: x._radial[0],
        "KC2" : lambda x: x._radial[1],
        "KC3" : lambda x: 0.,
        "Tangential0" : lambda x: 0.,
        "Tangential1" : lambda x: 0.,
        "ImagerPixelWidth" : lambda x: x.sensor_wh[0],
        "ImagerPixelHeight" : lambda x: x.sensor_wh[1],
        "PositionX" : lambda x: x.T[0],
        "PositionY" : lambda x: x.T[1],
        "PositionZ" : lambda x: x.T[2]
    }
    
    NEEDS_CONV = ( "PositionX", "PositionY", "PositionZ" )

    
    @staticmethod
    def _genOrients( mat, d ):
        for i, v in enumerate( mat.ravel() ):
            d[ "Orientation{}".format( i ) ] = v


    def __init__( self, system=None ):
        self.reset()
        if( system is not None ):
            self.system = system


    def reset( self ):
        self.system = None
        self.txt = ""
        self.unitConvert = False
        self.conversion  = 1.

        
    def generate( self, transposeR=False ):
        if( self.system is None ):
            print( "ERROR: No camera system to export!" )
            return
        lines = []
        for cam_id in self.system.camera_order:
            cam = self.system.cameras[ cam_id ]
            
            # assemble data
            out = {}
            for key, cast in self.EXPORT_CASTS.iteritems():
                out[ key ] = cast( cam )
                
            if( transposeR ):
                self._genOrients( cam.R.T, out )
            else:
                self._genOrients( cam.R, out )
            
            # convert mm to inches
            if( self.unitConvert ):
                for key in self.NEEDS_CONV:
                    out[ key ] = out[ key ] * self.conversion
                    
            # add to txt
            for key in self.EXPORT_ORDER:
                lines.append( "{},{}\n".format( key, out[ key ] ) )

            lines.append( "\n" )
        # finalize
        self.txt = "".join( lines )


    def write( self, file_path ):
        if( self.txt == "" ):
            self.generate()

        fh = open( file_path, "wb" )
        fh.write( self.txt )
        fh.close()
        
            
if( __name__ == "__main__" ):
    file_fq = r"C:\temp\g_data\Cal.txt"
    c_reader = CalTxReader()
    c_reader.read( file_fq )
    cam_id = c_reader.system.camera_order[0]
    m2a  = cm.mat34.mat2Angles
    print "serial", c_reader.system.cameras[ cam_id ].hw_id
    print "ColMaj", np.degrees( m2a( c_reader.system.cameras[ cam_id ].R ) )
    print "RowMaj", np.degrees( m2a( c_reader.system.cameras[ cam_id ].R.T ) )
    #print mats[ cam ][ "P" ]

    # testing reading an xml & writing txt
    from viconFiles import CalXCPReader
    #from optiFiles import CalTxWriter
    import os

    file_path = r"C:\temp\xcp_examples"
    file_name = "170202_WictorK_Body_ROM_01.xcp"
    
    cal_reader = CalXCPReader()
    cal_reader.read( os.path.join( file_path, file_name ) )

    cal_writer = CalTxWriter( cal_reader.system )
    cal_writer.unitConvert = True
    cal_writer.conversion  = 1./1000.
    cal_writer.generate(transposeR=True)
    cal_writer.write( os.path.join( file_path, file_name.replace( ".xcp", "_new.txt" ) ) )
    
