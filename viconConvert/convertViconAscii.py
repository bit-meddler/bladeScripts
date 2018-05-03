""" Tool to extract relevant data from the output of X2DToAscii.exe """
import numpy as np
import coreMaths as cm
import glob
import os


class ViconTake( object ):
    def __init__( self ):
        self.tc_standard = ""
        self.tc_start    = []
        self.cam_ids     = []
        self.cam_data    = {}
        self.frame_data  = []
        self.giant_data  = []
        self.source_name = ""

        
class ViconCamMeta( object ):
    CASTS = {
        "CameraId"    : ("id", int),
        "Type" : ("name", lambda x: x.replace( "\n", "" )),
        "ImageWidth"  : ("sensor_w", int),
        "ImageHeight" : ("sensor_h", int),
        "PixelAspectRatio" : ("sensor_a", int)
    }
    
    def __init__( self ):
        self.id = 0
        self.name = ""
        self.sensor_w = 0
        self.sensor_h = 0
        self.sensor_a = 0

        
    def parse( self, key, val ):
        if key in self.CASTS:
            dest, cast = self.CASTS[ key ]
            setattr( self, dest, cast( val ) )


    def __str__( self ):
        return "Camera: {} '{}', ({}x{})".format(
            self.id, self.name, self.sensor_w, self.sensor_h )

            
def readTC( file_fq, collector ):
    """ collector is a 'ViconTake' """
    fh = open( file_fq, "r" )
    _ = fh.readline()
    line = fh.readline()
    _, std = line.split()
    tc = [0,0,0,0,0]
    for i in range( 5 ):
        line = fh.readline()
        _, time = line.strip().split()
        tc[ i ] = int( time )
    fh.close()
    collector.tc_standard = std
    collector.tc_start = tc


def readMeta( file_fq, collector ):
    fh = open( file_fq, "r" )

    cur_cam = None
    line = "booting"
    while( line ):
        line = fh.readline()
        if( "CameraInfo" in line ):
            # new camera
            if( cur_cam is not None ):
                collector.cam_ids.append( cur_cam.id )
                collector.cam_data[ cur_cam.id ] = cur_cam
            cur_cam = ViconCamMeta()
        else:
            if( len( line ) > 1 ):
                key, val = line.split( " ", 1 )
                cur_cam.parse( key, val )
                
    # finish the last camera
    if( cur_cam is not None ):
        collector.cam_ids.append( cur_cam.id )
        collector.cam_data[ cur_cam.id ] = cur_cam
    fh.close()


def readData( file_fq, collector ):
    # requires the a_meta to have been parsed allready
    if( len( collector.cam_ids ) < 1 ):
        print( "EROR: no camera data!" )
        return
    # ok....
    # frames = [ [[dets],[splits]], *n ]
    fh = open( file_fq, "r" )
    size = os.path.getsize( file_fq )
    
    line = "booting"
    curr_frame = 0
    frames = []
    while( line ):
        place = fh.tell()
        if( (place+20) > size ):
            break
        roids_ac = []
        split_ac = [0]
        for cid in collector.cam_ids :
            # read a camera for this frame
            line = fh.readline() # centroid data
            line = fh.readline() # cam id
            _, id = line.split()
            if( cid != int( id ) ):
                print( "ERROR: Data missmatch" )
            line = fh.readline() # frame
            line = fh.readline() # roids
            _, num = line.split()
            num_roids = int( num )
            for i in range( num_roids ):
                line = fh.readline()
                x, y, r, c = line.split()
                roids_ac.append( map( float, (x,y) ) )
            split_ac.append( split_ac[-1] + num_roids )
            line = fh.readline() # empty line
        collector.frame_data.append(
            [np.array( roids_ac, dtype=cm.FLOAT_T),
             np.array( split_ac, dtype=cm.INT_T)]
        )
    fh.close()

def convert512( take ):
    # build conversion
    conversion = []
    take.giant_data = []
    # per camera rescaling
    for cam in take.cam_ids:
        w = take.cam_data[ cam ].sensor_w
        h = take.cam_data[ cam ].sensor_h
        half_w = w/2.
        half_h = h/2.
        offset = half_w - half_h
        hw_rec = 1./half_w
        conversion.append( [hw_rec, offset] )
    # per frame, adapt
    for f_roids, f_splits in take.frame_data:
        roids_ac = []
        for cid, (f_in, f_out) in enumerate( zip( f_splits[:-1], f_splits[1:] ) ):
            hw_rec, offset = conversion[ cid ]
            c_roids = np.array( f_roids[ f_in : f_out ] )
            c_roids[:,1] -= offset
            c_roids *= hw_rec
            roids_ac.append( c_roids )
        tmp = np.concatenate( roids_ac, axis=0 )
        tmp *= 256.0 # vectorize that shit!
        take.giant_data.append( [tmp, f_splits] )
    assert( len( take.giant_data ) == len( take.frame_data ) )


def outputGiant( take ):
    num_cams   = len( take.cam_ids )
    num_frames = len( take.giant_data )

    fh = open( take.source_name + ".raw", "wb" )
    fh.write( "{}\n{}\n".format( num_cams, num_frames ) )
    out_txt = ""
    for fi, (f_roids, f_splits) in enumerate( take.giant_data ):
        fi += 1
        fh.write("{}\n".format( fi )) # frame header
        for f_in, f_out in zip( f_splits[:-1], f_splits[1:] ):
            cam_dets = f_roids[ f_in:f_out ]
            out_txt = "{}\n".format( len( cam_dets ) )           
            for glob in cam_dets:
                out_txt += "1 {} {}\n".format( glob[ 0 ], glob[ 1 ] )
            fh.write( out_txt )
    fh.close()

    
PROCS = { "a_time" : readTC,
          "a_meta" : readMeta,
          "a_data" : readData
}
PROC_ORDER = ("a_time","a_meta","a_data")


if( __name__ == "__main__" ):
    tasks_path = r"C:\ViconData\Teaching_2016\Workshops\180502_A1_CalTest01\data"
    task_name = "examples_quad_positive_01"

    take = ViconTake()
    task_pn = os.path.join( tasks_path, task_name )
    take.source_name = task_pn
    for ext in PROC_ORDER:
        proc = PROCS[ ext ]
        proc(  task_pn + "." + ext, take )

    print( "Read" )
    convert512( take )
    print( "Converted" )
    print take.frame_data[0]
    print take.giant_data[0]
    outputGiant( take )
    print( "Done?" )
