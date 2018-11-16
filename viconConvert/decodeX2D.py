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
    KEEP = ( "CAM_COUNT", "FRAME_COUNT" )
    DECODER_KEYS = {
        (170, 223) : self.__decodeCentroids,
    }
    def __decodeCentroids( self, num ):
        ret = []
        for i in xrange( num ):#                               ___---___H
            x0, x1, x2, y0, y1, y2, r0, r1, r2, sc = struct.unpack_from( "<BBBBBBBBBH", self.dat, self.offset )
            self.offset += 11
            # not completly sure about this!
            x  = x2 * 256 * 256
            x += x1 * 256
            x += x0
            y  = y2 * 256 * 256
            y += y1 * 256
            y += y0
            # to float
            x /= 16384. # 64*256
            y /= 16384.
            # x & y -> /16384.0 (256*64)
            
            r  = r2 * 256 * 256
            r += r1 * 256
            r += r0
            
            ret.append( [x, y, r, sc] )
        return ret
        
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
        
    def readTagBlock( self ):
        tag, ref, size, count = struct.unpack_from( "<BBHH", self.dat, self.offset )
        self.offset += 10
        return (tag, ref), size, count
        
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
        meta_data = {}
        magic = self.readCast( "MAGIC_NUM" )
        # Header (Inc camera ID/Sensor sz)
        header_parsed = False
        while not header_parsed:
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
                if( cast_id in SELF.KEEP ):
                    meta_data[ cast_id ] = val
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
            # working through header...
            
        # Frame data
        num_cams    = meta_data[ "CAM_COUNT"   ]
        num_frames  = meta_data[ "FRAME_COUNT" ]
        frame_data  = [ [] for i in xrange( num_frames ) ]
        
        for i in xrange( num_frames ):
            # process each frame
            tag_tup, frame_size, frame_no = readTagBlock()
            frame_end_pos = self.offset + frame_size
            
            if( tag_tup != (256, 256) ):
                print "not a frame block"
                break
            if( frame_no != i ):
                print "Frame out of sequence"
            
            # TODO: Double scan to enable VBO-like indexing
            frame_data[i] = [ [] for j in xrange( num_cams ) ]
            
            for j in xrange( num_cams ):
                tag_tup cam_size, cam_no = readTagBlock()
                cam_end_pos = self.offset + cam_size
                if( tag_tup != (204, 204) ):
                    print "not a camera block"
                    break
                if( cam_no > num_cams ):
                    print "Unexpected Camera"
                    
                for k in xrange( 5 ): # 5 camera data types!
                    tag_tup d_size, num_elems = readTagBlock()
                    if( tag_tup in self.DECODER_KEYS ):
                        # decode data block
                        roids = self.DECODER_KEYS[ tag_tup ]()
                        frame_data[i][j] = roids
                    else:
                        # skip this block for now...
                        self.offset += d_size
                        
        # seeking index
        pass

        
fh = open( "path.secret", "r" )
x2d_fq = fh.readline()
fh.close()
reader = readX2D( x2d_fq )
reader.open()
reader.parse()

# 0x014c changes between files

# Camera Data block:
# "<I" num cams
#   camera block...
#       W, H, hw_id, unknown, odd_string,  : "<IIfQ", "<I" (len of string + 4)... "<IIHII" noidea, funny string.
# Self description and camera metadata is still a bit of a mystery, but frame data is becoming clear:
# (256, 256) "<HH" [size of frame block] [frame number] <Block>
#   (204, 204) "<HH" [size of cam block] [camera numbetr] <block>
#       (170, 223) "<HH" [size of data block] [num elements] <block> Centroid position
#       (208, 223) "<HH" [size of data block] [num elements] <block> ?
#       (187, 223) "<HH" [size of data block] [num elements] <block> ?
#       (238, 223) "<HH" [size of data block] [num elements] <block> Track ID?
#       (204, 223) "<HH" [size of data block] [num elements] <block> ?

# decoding centroid data
# X      | Y      | R         |score
#5F 72 60 0A 17 75 5E A3 00 6F A4 -> 385.787 468.36  1.27631 0.642319
#4E C4 6C 4C 79 7C F8 C1 00 5A BA -> 435.067 497.895 1.51538 0.727936
#06 98 86 C9 9B 8B DF AR 00 B6 C4 -> 538.375 558.434 1.36618 0.768402
#
#BD E3 92 97 AD 7B D8 E5 00 24 A7 00 C0 1D EF 6E D3 0D 50 00 84 A8 -> 587.558 494.712 1.79565 0.652893; 119.0 845.733 0.625397 0.658264
#CC E3 92 70 AD 7B 1D E6 00 60 A7 00 C0 1D 76 62 D3 3E 5A 00 5E EC -> 587.577 494.697 1.79874 0.651978; 119.0 845.882 0.95578 0.615524

