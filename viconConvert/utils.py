""" Some Utility functions """
import os
import errno

def mkdir_p( path ):
    """https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python"""
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

        
def fragmentFilePath( file_path ) :
    path_name, ext = os.path.splitext( file_path )
    path_part = os.path.dirname( path_name )
    name_part = os.path.basename( path_name )
    return path_part, name_part, ext


def openMkdir( file_name, mode='r' ):
    mkdir_p( os.path.dirname( file_name ) )
    return open( file_name, mode )
