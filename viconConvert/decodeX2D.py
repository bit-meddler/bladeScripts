"""
Decode an X2D.
    Assumtions:
        # There will be a header describing cameras (number, type, HWid, resolution)
        # there will be a header describing the shoot data (rate, number of frames, timecode start Time, ??Userbits??)
        # there will be blocks of frame data
            * each frame will have records per camera
            
comparing with data extracted with x2dtoascii we know the following:
CameraInfo
    CameraId 2107334
    UserId 2107334
    Type BONITA_2_MOCAP_1MP
    DisplayType Bonita 10
    ImageWidth 1024
    ImageHeight 1024
    PixelAspectRatio 1
    CircularityThreshold 0.385204
"""

import os
import struct

class readX2D( object ):
    CASTS = {
#       "" : ("", 0),
        "MAGIC_NUM"   : ("<I", 4), # allways, 3.  Which *is* the magic number
        "CAM_COUNT"   : ("<I", 4),
        "FRAME_COUNT" : ("<I", 4),
        "ELEMENTS_5"  : ("<I", 4),
        "ELEMENTS_6"  : ("<BBQH", 8),
        "E5_B1_DATA"  : ("<BBIII", 14),
        "E5_B2_DATA"  : ("<BBHH", 10),
        "E5_B3_DATA"  : ("<BBHH", 10),
        "E5_B4_DATA"  : ("<BBHH", 10),
        "E5_B5_DATA"  : ("<BBHH", 10),
        "16-0_NUM"    : ("<Q", 8),
        "208-0_NUM"   : ("<Q", 8),
        "E6_B1_DATA"  : ("<BBHH", 10),
        "DFFD_B1_DATA" : ("<BBHH", 10),
        
    }
    
    TAG_PAIRS = {
        (204,   0) : ( "CAST",  "CAM_COUNT" ),
        (252,   0) : ( "CAST",  "FRAME_COUNT" ),
        (252,  13) : ( "ELEM",  "ELEMENTS_5" ),
        (223,   0) : ( "BLOCK", "GENERIC" ), # TAGGED BLOCK
        (170, 223) : ( "TAG",   "E5_B1_DATA" ),
        (208, 223) : ( "TAG",   "E5_B2_DATA" ),
        (187, 223) : ( "TAG",   "E5_B3_DATA" ),
        (238, 223) : ( "TAG",   "E5_B4_DATA" ),
        (204, 223) : ( "TAG",   "E5_B5_DATA" ),
        ( 16,   0) : ( "CAST",  "16-0_NUM" ), # Changes per file, bigger number with bigger file
        (208,   0) : ( "CAST",  "208-0_NUM" ),
        (223, 253) : ( "BLOCK", "ELEMENTS_6" ),
        (150,   3) : ( "TAG",   "E6_B1_DATA" ),
        (171, 207) : ( "TAG",   "DFFD_B1_DATA" ),
    }
    
    def __init__( self, file_fq=None ):
        self.file_fq = file_fq
        self.fh = None
        self.offset = -1
        self.discovies = {}
        
    def open( self, file_fq=None ):
        if( self.file_fq is None ):
            self.file_fq = file_fq
        if( self.file_fq is None ):
            print( "No file!" )
            return
        self.fh = open( self.file_fq, "rb" )
        # TODO: Read in Nk blocks
        self.dat = self.fh.read()
        print len( self.dat )
        self.fh.close()
        self.offset = 0
        
    def readTag( self ):
        t,r,d = struct.unpack_from( "<BBI", self.dat, self.offset )
        self.offset += 6
        return t, r, d # tag, reff, data
        
    def readCast( self, cast_id ):
        if( not cast_id in self.CASTS ):
            print( "unknown cast ID '{}'".format( cast_id ) )
            return
        cast, size = self.CASTS[ cast_id ]
        ret = struct.unpack_from( cast, self.dat, self.offset )
        self.offset += size
        return ret
        
    def d2h( self, data=None, size=-1, start=-1 ):
        bytes = []
        if( not data is None ):
            bytes = data
        else:
            if( start < 0 ):
                start = self.offset
            if( size < 0 ):
                size = 16
            bytes = self.dat[ start:start+size ]
        return " ".join( [ "%02X" % ord( x ) for x in bytes ] ) 
        
    def parse( self ):
        magic = self.readCast( "MAGIC_NUM" )
        done = False
        while not done:
            tag, ref, data_sz = self.readTag()
            t_id = (tag, ref)
            if t_id not in self.TAG_PAIRS:
                print( "tag Id not found '{}'".format( t_id ) )
                print self.offset
                print data_sz
                print self.d2h( None, start=(self.offset - 6), size=32 )
                break
                
            mode, cast_id = self.TAG_PAIRS[ t_id ]
            
            if( mode == "CAST" ):
                val = self.readCast( cast_id )
                print t_id, cast_id, val
            elif( mode == "ELEM" ):
                num = self.readCast( cast_id )
                print mode, t_id, data_sz, num[ -1 ] # to enable skipping
            elif( mode == "BLOCK" ):
                #data_sz = data_sz[ -1 ]
                print mode, t_id, data_sz
                old_os = self.offset
                tag_1, ref_1, count = self.readTag()
                t_1_id = (tag_1, ref_1)
                print ">", t_1_id, count
                if t_1_id == t_id :
                    # special skip event
                    _, _, size = self.readTag()
                    print "223/253 >", size
                    tag_1, ref_1, count = self.readTag()
                    t_1_id = (tag_1, ref_1)
                    
                if not t_1_id in self.TAG_PAIRS:
                    print( "Inner Tag id not found '{}'".format( t_1_id ) )
                    print self.d2h( None, size=16 )
                    break
                mode_1, cast_1 = self.TAG_PAIRS[ t_1_id ]
                for i in range( count ):
                    res = self.readCast( cast_1 )
                    print res
                print "size >", self.offset, old_os + data_sz
                
fh = open( "path.secret", "r" )              
x2d_fq = fh.readline()
fh.close()
reader = readX2D( x2d_fq )
reader.open()
reader.parse()

# 0x014c changes between files