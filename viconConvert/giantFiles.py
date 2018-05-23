""" system to export various data into giant native formats """
import numpy as np
import coreMaths as cm
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
    
    EXPORT_CASTS = {
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


    def writeOut( self, file_path ):
        if( self.txt == "" ):
            self.generate()

        fh = open( file_path, "wb" )
        fh.write( self.txt )
        fh.close()


class CSFwrite( object ):
    #
    def __init__( self ):
        pass


    def generate( self, transposeR=False ):
        output_matrix = True
        output_script = False

        # setup output files
        csf_lines = []
        sh_lines  = []

        # header
        csf_lines.append( "Giant Studios Camera Set File\nv1.00\n" )

        # Process caemras
        for count, cam_id in enumerate( self.system.camera_order ):
            cam = self.system.cameras[ cam_id ]
            # Camera Heading
            out_txt  = "CAMERA {{\n"
            out_txt += "ID: {}\n".format( count+1 )

            # Position
            tx, ty, tz = cam.T * cm.INCHCONVERT
            out_txt += "  POSITION: {} {} {}\n".format( tx, ty, tz )

            # Orientation
            if( output_matrix ):
                if( transposeR ):
                    M = cam.R.T
                else:
                    M = cam.R
                out_txt += "  ROTATION_MATRIX {{\n    {} {} {}\n    {} {} {}\n    {} {} {}\n  }}\n".foMat(
                            M[0,0], M[0,1], M[0,2],
                            M[1,0], M[1,1], M[1,2],
                            M[2,0], M[2,1], M[2,2] )
            else:
                Rx, Ry, Rz = cm.mat34.rot2Angles( cam.R )
                out_txt += "  ROTATION: {} {} {} DEG\n".format( Rx, Ry, Rz )
                out_txt += "  ROTATION_ORDER: XYZ\n"

            # Aspect & FoV
            w, h = cam.sensor_wh
            a = cam._aspect

            out_txt += "  ASPECT_RATIO: {}\n".format( a )

            h_fov = cam.getfOv()
            v_fov = h_fov # compensated for letterboxed

            out_txt += "  FOV_X: {}\n  FOV_Y: {}\n".format( h_fov, v_fov )
            out_txt += "}}\n"

            # finalize
            csf_lines.append( out_txt )

            if output_script:
                sh_lines.append( "mkdlt {} {} {} {} {} {} {} 1\n".format(
                    pos[ 0 ], pos[ 1 ], pos[ 2 ],
                    Rx, Ry, Rz, np.degrees( h_fov ) ) )
        
        
def makePRJ( target_file, elements ):
    # Make Giant project file
    # Keys should be expected Project components, values the path
    
    header = "Bio Project File\nv3.00\n"

    fh = open( target_file, 'wb' )
    fh.write( header )
        
    for key, value in elements.iteritems():
        key += ":"
        fh.write( "{: <30}{}\n".format(key, value) )
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
    cal_writer.unitConvert = True
    cal_writer.conversion  = 1./1000.
    cal_writer.generate(transposeR=True)
    cal_writer.writeOut( os.path.join( file_path, file_name.replace( ".xcp", "_new.txt" ) ) )
    
