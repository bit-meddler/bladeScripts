""" system to export various data into giant native formats """
import numpy as np
import coreMaths as cm
import os

class TKLtool( object ):
    """ Generic tool to read TKL style dumps into pythonic datastructures """
    pass


class CalCSFWriter( object ):
    # from a camera system, generate a CSF, and optioncaly a shell script to
    # call 'mkdlt' with the same data
    
    def __init__( self, system=None, script=False, dlt=True, matrix=True ):
        if( system is not None ):
            self.system = system
        self._output_matrix = matrix
        self._output_dlt = dlt
        self._output_script = script

        self._DLT = ""
        self._SH  = ""
        

    def generate( self, transposeR=False ):
        # setup output files
        csf_lines = []
        sh_lines  = []

        # header
        csf_lines.append( "Giant Studios Camera Set File\nv1.00\n" )

        # Process caemras
        for count, cam_id in enumerate( self.system.camera_order ):
            cam = self.system.cameras[ cam_id ]
            # Camera Heading
            out_txt  = "CAMERA {\n"
            out_txt += "  ID: {}\n".format( count+1 )

            # Position
            tx, ty, tz = cam.T * cm.INCHCONVERT
            out_txt += "  POSITION: {} {} {}\n".format( tx, ty, tz )

            # Orientation
            if( self._output_matrix ):
                if( transposeR ):
                    M = cam.R.T
                else:
                    M = cam.R
                out_txt += "  ROTATION_MATRIX {{\n    {} {} {}\n    {} {} {}\n    {} {} {}\n  }}\n".format(
                            M[0,0], M[0,1], M[0,2],
                            M[1,0], M[1,1], M[1,2],
                            M[2,0], M[2,1], M[2,2] )
                
            Rx, Ry, Rz = np.degrees( cm.mat34.mat2Angles( cam.R ) )
            out_txt += "  ROTATION: {} {} {} DEG\n".format( Rx, Ry, Rz )
            out_txt += "  ROTATION_ORDER: XYZ\n"

            # Aspect & FoV
            w, h = cam.sensor_wh
            a = cam._aspect

            out_txt += "  ASPECT_RATIO: {}\n".format( a )

            h_fov = cam.getFoV()
            v_fov = h_fov # compensated for letterboxed

            out_txt += "  FOV_X: {}\n  FOV_Y: {}\n".format( h_fov, v_fov )
            out_txt += "}\n"

            # finalize
            csf_lines.append( out_txt )

            sh_lines.append( "mkdlt {} {} {} {} {} {} {} 1\n".format(
                tx, ty, tz, Rx, Ry, Rz,  h_fov ) )
        
        # update with text
        self._DLT = "".join( csf_lines )
        self._SH  = "".join( sh_lines  )


    def write( self, orig_file_path ):
        file_path, _ = os.path.splitext( orig_file_path )
        print file_path
        if( self._output_dlt and self._DLT != "" ):
            fh = open( file_path + ".csf", 'wb' )
            fh.write( self._DLT )
            fh.close()
        if( self._output_script and self._SH != "" ):
            fh = open( file_path + ".sh", 'wb' )
            fh.write( "#!/usr/bin/env bash\n" )
            fh.write( self._SH )
            fh.close()

            
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
    # testing Giant stuff...
    from optiFiles import CalTxReader

    file_path = r"C:\temp\g_data"
    file_name = "Cal.txt"
    
    ctxr = CalTxReader()
    ctxr.read( os.path.join( file_path, file_name ) )
    
    ccsfw = CalCSFWriter( system=ctxr.system )
    ccsfw.generate()
    ccsfw.write( os.path.join( file_path, file_name ) )
    
