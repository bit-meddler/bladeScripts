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


def readTag( dat, os ):
    t,r,d = struct.unpack_from( "<BBI", dat, os )
    return t, r, d
    
def readElem( dat, os ):
    num, tag, a, b, c = struct.unpack_from( "<BBIII", dat, os )
    return num, tag, a, b, c
    
def readInt( dat, os ):
    return struct.unpack_from( "<I", dat, os )
    
def readBlock( dat, sz, os ):
    return dat[os:os+sz]
    
def b2h( bytes ):
    return " ".join( [ "%02X" % ord( x ) for x in bytes ] )
    
    
x2d_fq = r""
fh = open( x2d_fq, "rb" )
raw = fh.read()
offset = 0

# header
magic_number = struct.unpack_from( "<I", raw, offset )
print magic_number
offset += 4
# Cam count
tag, ref, sz = readTag( raw, offset )
offset +=6
print tag, ref, sz
print readInt( raw, offset )
offset += sz
# Frame Count
tag, ref, sz = readTag( raw, offset )
print tag, ref, sz
offset +=6
element_count = readInt( raw, offset )
offset += sz
# Mystery Data
tag, ref, sz = readTag( raw, offset )
print tag, ref, sz
offset +=6
element_count = readInt( raw, offset )
offset += sz
print element_count
tag, ref, sz = readTag( raw, offset )
print tag, ref, sz
offset +=6
element_block = readBlock( raw, sz, offset )
os_e = 0
tag, ref, sz = readTag( element_block, os_e )
print tag, ref, sz
os_e +=6
for i in range( sz ):
    print readElem( element_block, os_e )
    os_e += 14
print b2h( element_block )

fh.close()