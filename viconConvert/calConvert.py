""" attempt at solving Ax=B conversion of a vanillia Projection matrix derived from Optitrack or Vicon into Giant's perverted one. """
import os
import numpy as np
import coreMaths as cm
from optiFiles import CalTxReader
from giantFiles import CalDLTReader, CalDLTWriter
from viconFiles import CalXCPReader


def _test1():
    path_g = r"C:\temp\g_files"
    cal_g  = "calib_dlt.bin" # I'll need a pair of cals for this!
    cal_o  = "Cal.txt"

    opti  = CalTxReader()
    giant = CalDLTReader()

    opti.read( os.path.join( path_g, cal_o ) )
    giant.read( os.path.join( path_g, cal_g ) )

    opti.system.marshel()

    O_mats = opti.system.P_mats
    G_mats = giant.cameras

    # try with one to start with
    O_ = np.diagflat( O_mats[0] )
    G_ = np.diagflat( G_mats[0] )

    x_ = np.linalg.solve( O_, G_ )

    x = np.diagonal( x_ ).reshape( (3,4) )

    Gcon = np.matmul( O_mats[0], x )

    print( Gcon, G_mats[0] )
    print( Gcon - G_mats[0] )

    
def convert( source_fq, target_fq, as_dlt=True ):
    vicon = CalXCPReader()
    vicon.read( source_fq )
    
    if( as_dlt ):
        # convert to dlt
        vicon.marshel()    
        outMats = []
        conversion = np.ones( (3,4), dtype=cm.FLOAT_T )
        for i, mat in enumerate( vicon.P_mats ):
            outMats.append( np.matmul( mat, conversion ) )
        giant = CalDLTWriter( outMats )
    else:
        giant = CalCSFWriter( vicon.system )
        
    giant.write( target_fq )
    
    
if( __name__ == "__main__" ):
    import argparse
    parser = argparse.ArgumentParser(
                 description="The hardest part of this whole project. Direct conversion "
                             "of a vicon calibration to a giant DLT file.",
                 formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group( required=True )
    group.add_argument( "-d", "--dlt",
                        dest="output_dlt",
                        help="Convert the XCP to a DLT",
                        action="store_true"
    )
    group.add_argument( "-c", "--csf",
                        dest="output_dlt",
                        help="Convert the XCP to a CSF",
                        action="store_false"
    )
    parser.add_argument( "taskpath",
                         help="Path to the Vicon XCP"
    )
    parser.add_argument( "targetpath",
                         help="Path to where the calibration should be placed"
    )
    args = parser.parse_args()
    
    convert( args.taskpath, args.targetpath, args.output_dlt )
