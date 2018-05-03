""" system to export various data into giant native formats """
import numpy as np
import os

class TKLtool( object ):
    pass

class NPCwrite( object ):

    EXPORT_ORDER = ( "CameraSerial", "LensCenterX", "LensCenterY", "HorizontalFocalLength",
                     "VerticalFocalLength", "KC1", "KC2", "KC3", "Tangential0", "Tangential1",
                     "ImagerPixelWidth", "ImagerPixelHeight", "PositionX", "PositionY",
                     "PositionZ", "Orientation0", "Orientation1", "Orientation2",
                     "Orientation3", "Orientation4", "Orientation5", "Orientation6",
                     "Orientation7", "Orientation8" )
    
    EXPORT_KEYS = {
        "CameraSerial" : lambda x: x.hw_id,
        "LensCenterX" : lambda x: x._pp[0],
        "LensCenterY" : lambda x: x._pp[1],
        "HorizontalFocalLength" : lambda x: x._focal,
        "VerticalFocalLength" : lambda x: x._focal/x.px_aspect,
        "KC1" : lambda x: x._radial[0],
        "KC2" : lambda x: x._radial[1],
        "KC3" : lambda x: 0.,
        "Tangential0" : lambda x: 0.,
        "Tangential1" : lambda x: 0.,
        "ImagerPixelWidth" : lambda x: x.sensor_wh[0],
        "ImagerPixelHeight" : lambda x: x.sensor_wh[1],
        "PositionX" : lambda x: x.T[0],
        "PositionY" : lambda x: x.T[1],
        "PositionZ" : lambda x: x.T[2],
    }

    
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

        
    def generate( self ):
        if( self.system is None ):
            print( "ERROR: No camera system to export!" )
            return
        lines = []
        for cam_id in self.system.camera_order:
            cam = self.system.cameras[ cam_id ]
            # assemble data
            out = {}
            for key, cast in self.EXPORT_KEYS.iteritems():
                out[ key ] = cast( cam )
            self._genOrients( cam.R, out )
            # add to txt
            for key in self.EXPORT_ORDER:
                lines.append( "{},{}\n".format( key, out[ key ] ) )

            lines.append( "\n" )
        # finalize
        self.txt = "".join( lines )


    def writeOut( self, file_path ):
        if( self.txt == "" ):
            self.generate()

        fh = open( file_path, "wb" )
        fh.write( self.txt )
        fh.close()

        
if( __name__ == "__main__" ):
    # testing reading an xml
    from viconFiles import CalReader
    import os

    file_path = r"C:\temp\xcp_examples"
    file_name = "170202_WictorK_Body_ROM_01.xcp"
    
    cal_reader = CalReader()
    cal_reader.read( os.path.join( file_path, file_name ) )

    cal_writer = NPCwrite( cal_reader.system )
    cal_writer.generate()
    cal_writer.writeOut( os.path.join( file_path, "170202_WictorK_Body_ROM_01.txt" ) )
    
