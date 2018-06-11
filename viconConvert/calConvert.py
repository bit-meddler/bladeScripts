""" attempt at solving Ax=B conversion of a vanillia Projection matrix derived from Optitrack or Vicon into Giant's perverted one. """
import os
import numpy as np
import coreMaths as cm
from optiFiles import CalTxReader
from giantFiles import CalDLTReader

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

pritn( Gcon - G_mats[0] )
