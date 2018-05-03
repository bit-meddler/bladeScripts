""" Generate a batch file to run 'X2DToAscii.exe' on a vicon take and extract:
        Camera metadata
        Timecode of first frame
        Raw 2D detections

    TODO:
        Implement a 'scatter' process to task all available cores

"""
import os
import glob


def fragmentFilePath( file_path ) :
    path_name, ext = os.path.splitext( file_path )
    path_part = os.path.dirname( path_name )
    name_part = os.path.basename( path_name )
    return path_part, name_part, ext


CONVERSIONS = { "a_meta" : "C",
                "a_time" : "T",
                "a_data" : "c"
}

CONVERTER = r"C:\temp\X2DToAscii.exe"

def genJobList( source_fq, target_path=None, target_append=None ):
    src_path, src_name, src_ext = fragmentFilePath( source_fq )
    
    tgt_path = target_path
    if( target_path is None ):
        tgt_path = src_path

    tgt_name = src_name
    if( target_append is not None ):
        tgt_name += "_" + target_append

    jobs = [ "ECHO:Converting '{}'\n".format( src_name ) ]
    for ext, param in CONVERSIONS.iteritems():
        jobs.append( '"{}" "{}" -t {} > "{}.{}"\n'.format( CONVERTER,
            source_fq, param, os.path.join( tgt_path, tgt_name ), ext ) )
    jobs.append( "\n" )
    return jobs


def genBatFile( out_file_fq, task_list, target_path=None, target_append=None ):
    # generate jobs
    conv_jobs = []
    for task in task_list:
        conv_jobs += genJobList( task, target_path, target_append )
    # write to batch
    fh = open( out_file_fq, "wb" )
    fh.write( "ECHO OFF\n" )
    for job in conv_jobs:
        fh.write( job )
    fh.close()

    
if( __name__ == "__main__" ):
    session = r"C:\ViconData\Teaching_2016\Workshops\180502_A1_CalTest01\data"
    files = glob.glob( os.path.join( session, "*.x2d" ) )
    genBatFile( os.path.join( session, "convert.bat" ), files )
    
