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

    tgt_fq = os.path.join( tgt_path, tgt_name )
    
    res = ["ECHO:Converting '{}'\n".format( src_name )]
    jobs = []
    conversion = ['python convertViconAscii.py "{}" "{}"\n'.format( tgt_path, tgt_name )]
    cleanup = []
    for ext, param in CONVERSIONS.iteritems():
        jobs.append( '"{}" "{}" -t {} > "{}.{}"\n'.format( CONVERTER,
            source_fq, param, tgt_fq, ext ) )
        cleanup.append( '"DEL "{}.{}"\n'.format( tgt_fq, ext ) )
    res += jobs + conversion + cleanup 
    res.append( "\n" )
    return "".join( res )


def genBatFile( out_file_fq, task_list, target_path=None, target_append=None ):
    # generate jobs
    conv_jobs = []
    for task in task_list:
        conv_jobs.append( genJobList( task, target_path, target_append ) )
    outputBatFile( out_file_fq, conv_jobs )

        
def outputBatFile( out_fq, jobs ):
    # write to batch
    fh = open( out_fq, "wb" )
    fh.write( "ECHO OFF\n" )
    for job in jobs:
        fh.write( job )
    fh.close()


def _apiExample():
    session_roms = r"C:\ViconData\Client\Project\day\ROM"
    rom_list = ["ben_rom.x2d","dave_rom.x2d"]
    session_takes = r"C:\ViconData\Client\Project\day\PM"
    take_list = [ "take_0001.x2d", "take_0002.x2d", "take_0004.x2d",
                  "take_0008.x2d", "take_0016.x2d", "take_0032.x2d", ]
    giant_base = "C:\giant\client\project\day"
    tasks = []
    # do ROMs
    for rom in rom_list:
        rom_fq = os.path.join( session_roms, rom )
        _, name, _ = fragmentFilePath( rom_fq )
        giant_tgt = os.path.join( giant_base, "capture", "talent", name )
        tasks.append( genJobList( rom_fq, giant_tgt ) )
    # do takes
    for take in take_list:
        take_fq = os.path.join( session_takes, take )
        _, name, _ = fragmentFilePath( take_fq )
        giant_tgt = os.path.join( giant_base, "capture", name )
        tasks.append( genJobList( take_fq, giant_tgt ) )
        
    outputBatFile( "demo.bat", tasks )

    
def _scatter( out_path, out_name, tasks, ways ):
    num_t = len( tasks )
    blocks = num_t / ways
    last = 0
    basename = os.path.join( out_path, out_name + "{}.bat" )
    for i in range( 1, ways ):
        end = blocks * i
        outputBatFile( basename.format(i), tasks[last:end] )
        last = end
    outputBatFile( basename.format(ways), tasks[last:] )
    
    
def _test1():
    x = genJobList( r"C:\temp\xyz\take0001.x2d", r"C:\giant\day\volume\take\take" )
    for l in x:
        print(l)

    if False:
        session = r"C:\ViconData\Teaching_2016\Workshops\180502_A1_CalTest01\data"
        files = glob.glob( os.path.join( session, "*.x2d" ) )
        genBatFile( os.path.join( session, "convert.bat" ), files )

        
if( __name__ == "__main__" ):
    _apiExample()
    exit(0)
    import argparse
    parser = argparse.ArgumentParser(
                 description="First stage in Vicon to Giant conversion process.\n"
                             "Use at the command line to convert an entire session "
                             "or access internal functions programaticly (preffered).\n"
                             "In either case a windows batch file will be generated which "
                             "will convert desired x2ds into giant '.raw's.  This file is "
                             "placed in the 'session' you define as the first argumnt.",
                 formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument( "session",
                         help="Path to the Vicon session to convert"
    )
    parser.add_argument( "-f", "--force",
                         dest="output_path",
                         help="Force creation of the batch file in this path"
    )
    parser.add_argument( "-i", "--input",
                         dest="taskname",
                         help="If you only want to convert one x2d (expected to be in 'session')"
    )
    parser.add_argument( "-o", "--output",
                         dest="target_path",
                         help="Path the converted files will be placed into.  By "
                              "default conversions will be placed in the source path"
    )
    parser.add_argument( "-a", "--append",
                         dest="append",
                         help="Optional appendage for converted files"
    )
    parser.add_argument( "-b", "--buys",
                         dest="buy_list",
                         help="Only convert takes that are in this 'buy list' file.  "
                              "Expects one take name per line, no extension."
    )
    args = parser.parse_args()
    tgt_p = None
    just_one  = None
    buy_file = None
    append = None
    
    if( args.target_path ):
        tgt_p = args.target_path
    if( args.taskname ):
        just_one = args.taskname
    if( args.buy_list ):
        buy_file = args.buy_list
    if( args.append ):
        append = args.append

    # allow overiding path to batch file
    session = args.session
    out_path = session
    if( args.output_path ):
        out_path = args.output_path
    output_fq = os.path.join( out_path, "convert.bat" )

    if( just_one ):
        # one off conversion
        task_fq = os.path.join( out_path, just_one )
        genBatFile( output_fq, [task_fq], tgt_p, append )
    else:
        # do whole session
        all_files = glob.glob( os.path.join( session, "*.x2d" ) )
        # restricted buys?
        tasks = []
        if( buy_file ):
            fh = open( buy_file, "r" )
            buys = fh.readlines()
            fh.close()
            for file in all_files:
                f_path, f_name, f_ext = fragmentFilePath( file )
                if( f_name in buys ):
                    tasks.append( file )
        else:
            tasks = all_files

        genBatFile( output_fq, tasks, tgt_p, append )
        
