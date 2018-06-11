""" system to export various data into giant native formats """
import numpy as np
import coreMaths as cm
from genericMoCap import CameraSystem, GenericCamera
import os

class TCLTool( object ):
    """ Generic tool to read & write TCL style dumps into pythonic datastructures """
    def __init__( self, data=None ):
        if( data is not None ):
            self._data = data # for writing
        else:
            self.reset()

            
    def reset( self ):
        self._data = {}
        self.source_file = ""
        self._fh = None


    def _parseBraces( self ):
        # build a 'structure' of a braced block of data
        collector = {}
        val_list = []
        done = False

        line = self._fh.readline()
        while( line and not done ):
            if( ":" in line ):
                self._parse_fwd( line, collector )
            elif( "{" in line ):
                # create sub structure
                self._parse_fwd( line, collector )
            elif( "}" in line ):
                done = True
                break
            else:
                val_list.append( line.strip().split() )
            line = self._fh.readline()

        if( len( val_list ) > 0 ):
            return val_list
        else:
            return collector

        
    def _parse_fwd( self, line, data ):
        element = ""
        value   = None
        if( ":" in line ):
            # key : value assignment
            i = line.find( ":" )
            element = line[:i].strip()
            value = line[i+1:].strip().strip()
            data[ element ] = value
            return
        if( "{" in line ):
            i = line.find( "{" )
            element = line[:i].strip()
            value = self._parseBraces()
            if( element in data ):
                store = data[ element ]
                if type( store ) != list:
                    data[ element ] = [ store ]
                data[ element ].append( value )
            else:
                data[ element ] = value
            return
        if( line.strip() == "" ):
            pass
        else:
            print( "Inconceivable!", line )
            
        
    def read( self, file_path, assume_headings=True ):
        self.reset()
        self.source_file = file_path

        self._fh = open( file_path, "r" )
        if( assume_headings ):
            self._data[ "GIANT_HEADER_TYPE" ] = self._fh.readline()
            self._data[ "GIANT_HEADER_VERSION" ] = self._fh.readline()
        line = self._fh.readline()
        while line:
            self._parse_fwd( line, self._data )
            line = self._fh.readline()
        self._fh.close()
        
        
    @staticmethod
    def _tabKeyVal( key, val, indent, pad="  " ):
        buff = ""
        vtype = type( value )
        if( vtype in [ list, dict ] ):
            if( vtype == list ):
                if( type( value[0] ) == dict ):
                    # named list
                    for item in value:
                        buff += key
                        buff += " {\n"
                        buff += TCLTool._tabPrinter( item, indent+1, pad )
                        buff += "{}}}\n".format( pad*indent )
                else:
                    buff += indent*pad
                    buff += key
                    buff += " [\n"
                    for item in value:
                        buff += TCLTool._tabPrinter( item, indent+1, pad )
                        buff += ",\n"
                    buff = buff[:-2]
                    buff += "\n{}]\n".format( pad*indent )
            else: # dict
                buff += key
                buff += " {\n"
                for vkey in sorted( value.keys() ):
                    buff += TCLTool._tabKeyVal( vkey, value[ vkey ], indent+1, pad )
                #buff += "\n"
                buff += pad*indent + "}\n"
        else:
            buff = pad*indent
            buff += key + ": {}\n".format( value )
        return buff
        
        
    @staticmethod
    def _tabPrinter( data, indent=0, pad="  " ):
        buff = ""
        vtype = type( data )
        if( vtype == list ):
            buff += indent*pad
            for item in data:
                buff += TCLTool._tabPrinter( item, indent, pad )
        elif( vtype == dict ):
            for key in sorted( data.keys() ):
                buff += TCLTool._tabKeyVal( key, data[ key ], indent, pad )
        else:
            buff += "{}{}\n".format( indent*pad, data )
        return buff
        
        
    def formatTCL( self, input_dict=None ):
        if( input_dict is None ):
            return self._tabPrinter( self._data )
        else:
            return self._tabPrinter( input_dict )

            
    def write( self, file_fq ):
        fh = open( file_fq, "wb" )
        if( "GIANT_HEADER_TYPE" in self._data ):
            fh.write( "{}\n".format( self._data[ "GIANT_HEADER_TYPE" ] ) )
            del( self._data[ "GIANT_HEADER_TYPE" ] )
        if( "GIANT_HEADER_VERSION" in self._data ):
            fh.write( "{}\n".format( self._data[ "GIANT_HEADER_VERSION" ] ) )
            del( self._data[ "GIANT_HEADER_VERSION" ] )
        fh.write( self.formatTCL() )
        fh.close()
        
        
class GiantCamera( GenericCamera ):

    def __init__( self, input_dict=None ):
        # super
        super( GiantCamera, self ).__init__()
        
        # camera data
        self.hw_id = -1 # uniue id.  data is in id order in the x2d
        
        # raw calibration data
        self._pos   = [0., 0., 0.] # tx, ty, tz
        self._focal = [0., 0.] # f in sensor px (h,v)
        
        if( input_dict is not None ):
            self.setFromDict( input_dict )

    CASTS = {
        "POSITION" : lambda x : map( float, x.split() ),
        "ASPECT_RATIO" : lambda x : float( x ),
        "ROTATION" : lambda x : map( float, x.split()[-1] ),
    }
    @staticmethod
    def gCast( item, d ):
        return GiantCamera.CASTS[ item ]( d[ item ] )

    
    def setFromDict( self, dict ):
        self.hw_id     = dict["ID"]
        self.px_aspect = self.gCast( "ASPECT_RATIO", dict )
        self._pos      = self.gCast( "POSITION", dict )
        self._rot      = None
        if( "ROTATION_MATRIX" in dict ):
            self._rot = np.array( dict[ "ROTATION_MATRIX" ], dtype=cm.FLOAT_T )
        else:
            self._rot = cm.mat33.formMatDirect(
                        np.radians( self.gCast( "ROTATION", dict )),
                        dict[ "ROTATION_ORDER" ]
            )
        # From a csf, there is no calibrated pp, or focal-length available. bodge in
        # giant units...
        # approx focal length
        fov_x = np.radians( float( dict[ "FOV_X" ] ) )
        f_x = 256. / np.tan( fov_x/2. )

        fov_y = np.radians( float( dict[ "FOV_Y" ] ) )
        f_y = 256. / np.tan( fov_y/2. )
        self._focal = [ f_x, f_y ]

        # we know sensor is locked to 512x512
        self.sensor_wh = [512., 512.]
        self._pp = [256., 256.]
        
        # T
        self.T = np.array( self._pos, dtype=cm.FLOAT_T )
        
        # R
        self.R = self._rot
        
        # Can't Compute P or K without resolution, pp
        self.computeMatrix()

        
    def computeMatrix( self ):
        super( GiantCamera, self ).computeMatrix()

        # now compute Giant's perverted matrix
        self.P_g = self.P / self.P[2,3]
        self.P_g[0:2,3] /= 10.


class CalDLTReader( object ):
    def __init__( self ):
        self._tclt = TCLTool()
        self.cameras = []
        
    def read( self, source_file ):
        self._tclt.read( source_file )
        for  cam_d in self._tclt._data["CAMERA"]:
            cam = np.ones( (12), dtype=cm.FLOAT_T )
            cam[:11] = np.array( cam_d["DLT"], dtype=cm.FLOAT_T ).reshape( (11) )
            # I seem to recall Vaugn saying one col needs to be 10x
            cam = cam.reshape( (3,4) )
            cam[0:2,3] *= 10.
            self.cameras.append( cam )
         self.cameras = np.array( self.cameras, dtype=cm.FLOAT_T )  
            
            
class CalDLTWriter( object ):

    def __init__( self, mats ):
        self.mats = mats
        
        
    def write( self, out_fq ):
        d = {
            "CAMERA" : [],
            "GIANT_HEADER_TYPE"  : "Bio Camera Calibration File",
            "GIANT_HEADER_VERSION" : "v1.00"
        }
        for m in self.mats:
            d["CAMERA"].append({"DLT":[ v for v in m ]})
        tt = TCLTool( d )
        tt.write( out_fq )
        
        
class CalCSFReader( object ): # or inherit TCLTool??
    
    def __init__( self ):
        self._tclt = TCLTool()
        self.system = CameraSystem()
        self.system.hardware = "Giant"
        self.system.camera_order = []
        
    def read( self, source_file ):
        self._tclt.read( source_file )
        
        for i, cam_d in enumerate( self._tclt._data["CAMERA"] ):
            cam = GiantCamera( cam_d )
            cam_id = i +1
            self.system.cameras[ cam_id ] = cam
            self.system.camera_order.append( cam_id )

        
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
            a = cam.px_aspect

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
    
    ccfr = CalCSFReader()
    file_name = "svv.csf"
    ccfr.read( os.path.join( file_path, file_name ) )
    
    cdtr = CalDLTReader()
    file_name = "calib_dlt.bin"
    cdtr.read( os.path.join( file_path, file_name ) )
