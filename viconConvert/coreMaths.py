import numpy as np

# project standard types
FLOAT_T = np.float32
INT_T = np.int32


class mat33( object ):
    """ just a rotation matrix, and that it involves... """
    # -- Auto Generated Rotation matrixes for call combinations of DoFs and orders -- #
    
    def _rotMatXYZ( rx, ry, rz ):
        # compose and simplify rotation matrix in order of XYZ
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        cz_sy = cz * sy
        sz_sy = sz * sy
        
        M = [ [(cz*cy), (-sz*cx)+(cz_sy*sx), (-sz*-sx)+(cz_sy*cx)],
              [(sz*cy), (cz*cx)+(sz_sy*sx),  (cz*-sx)+(sz_sy*cx) ],
              [-sy,     (cy*sx),             (cy*cx)             ] ]
        return M


    def _rotMatXZY( rx, ry, rz ):
        # compose and simplify rotation matrix in order of XZY
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        msy_msz = -sy * -sz
        cy_msz  =  cy * -sz
        
        M = [ [(cy*cz),  (cy_msz*cx)+(sy*sx),  (cy_msz*-sx)+(sy*cx)  ],
              [sz,       (cz*cx),              (cz*-sx)              ],
              [(-sy*cz), (msy_msz*cx)+(cy*sx), (msy_msz*-sx)+(cy*cx) ] ]
        return M


    def _rotMatYXZ( rx, ry, rz ):
        # compose and simplify rotation matrix in order of YXZ
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        msz_msx = -sz * -sx
        cz_msx  = cz  * -sx
        
        M = [ [(cz*cy)+(msz_msx*-sy), (-sz*cx), (cz*sy)+(msz_msx*cy) ],
              [(sz*cy)+(cz_msx*-sy),  (cz*cx),  (sz*sy)+(cz_msx*cy)  ],
              [(cx*-sy),              sx,       (cx*cy)              ] ]
        return M


    def _rotMatYZX( rx, ry, rz ):
        # compose and simplify rotation matrix in order of YZX
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        cx_sz = cx * sz
        sx_sz = sx * sz
        
        M = [ [(cz*cy),              -sz,     (cz*sy)            ],
              [(cx_sz*cy)+(-sx*-sy), (cx*cz), (cx_sz*sy)+(-sx*cy)],
              [(sx_sz*cy)+(cx*-sy),  (sx*cz), (sx_sz*sy)+(cx*cy) ] ]
        return M


    def _rotMatZXY( rx, ry, rz ):
        # compose and simplify rotation matrix in order of ZXY
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        sy_sx = sy * sx
        cy_sx = cy * sx
        
        M = [ [(cy*cz)+(sy_sx*sz),  (cy*-sz)+(sy_sx*cz), (sy*cx)],
              [(cx*sz),             (cx*cz),                 -sx],
              [(-sy*cz)+(cy_sx*sz), (-sy*-sz)+(cy_sx*cz), (cy*cx)] ]
        return M


    def _rotMatZYX( rx, ry, rz ):
        # compose and simplify rotation matrix in order of ZYX
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        msx_msy =-sx * -sy
        cx_msy  = cx * -sy
        
        M = [ [(cy*cz),              (cy*-sz),                    sy],
              [(msx_msy*cz)+(cx*sz), (msx_msy*-sz)+(cx*cz), (-sx*cy)],
              [(cx_msy*cz)+(sx*sz),  (cx_msy*-sz)+(sx*cz),  (cx*cy) ] ]
        return M


    def _rotMatXY( rx, ry, rz ):
        # compose and simplify rotation matrix in order of XY
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )

        M = [ [cy,  (sy*sx), (sy*cx) ],
              [0,   cx,      -sx     ],
              [-sy, (cy*sx), (cy*cx) ] ]
        return M


    def _rotMatXZ( rx, ry, rz ):
        # compose and simplify rotation matrix in order of XZ
        cx, sx = np.cos( rx ), np.sin( rx )
        cz, sz = np.cos( rz ), np.sin( rz )

        M = [ [cz, (-sz*cx), (-sz*-sx)],
              [sz, (cz*cx),  (cz*-sx) ],
              [0,  sx,        cx      ] ]
        return M


    def _rotMatYX( rx, ry, rz ):
        # compose and simplify rotation matrix in order of YX
        cx, sx = np.cos( rx ), np.sin( rx )
        cy, sy = np.cos( ry ), np.sin( ry )

        M = [ [cy,         0, sy      ],
              [(-sx*-sy), cx, (-sx*cy)],
              [(cx*-sy),  sx, (cx*cy) ] ]
        return M


    def _rotMatYZ( rx, ry, rz ):
        # compose and simplify rotation matrix in order of YZ
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        M = [ [(cz*cy), -sz, (cz*sy)],
              [(sz*cy),  cz, (sz*sy)],
              [-sy,       0,  cy    ] ]
        return M


    def _rotMatZX( rx, ry, rz ):
        # compose and simplify rotation matrix in order of ZX
        cx, sx = np.cos( rx ), np.sin( rx )
        cz, sz = np.cos( rz ), np.sin( rz )

        M = [ [cz,      -sz,     0  ],
              [(cx*sz), (cx*cz), -sx],
              [(sx*sz), (sx*cz),  cx] ]
        return M


    def _rotMatZY( rx, ry, rz ):
        # compose and simplify rotation matrix in order of ZY
        cy, sy = np.cos( ry ), np.sin( ry )
        cz, sz = np.cos( rz ), np.sin( rz )

        M = [ [(cy*cz),  (cy*-sz),  sy],
              [sz,       cz,        0 ],
              [(-sy*cz), (-sy*-sz), cy] ]
        return M


    def _rotMatX( rx, ry, rz ):
        # compose and simplify rotation matrix in order of X
        cx, sx = np.cos( rx ), np.sin( rx )

        M = [ [1, 0,   0 ],
              [0, cx, -sx],
              [0, sx,  cx] ]
        return M


    def _rotMatY( rx, ry, rz ):
        # compose and simplify rotation matrix in order of Y
        cy, sy = np.cos( ry ), np.sin( ry )


        M = [ [cy,  0, sy],
              [0,   1,  0],
              [-sy, 0, cy] ]
        return M


    def _rotMatZ( rx, ry, rz ):
        # compose and simplify rotation matrix in order of Z
        cz, sz = np.cos( rz ), np.sin( rz )


        M = [ [cz, -sz, 0],
              [sz,  cz, 0],
              [0,   0,  1] ]
        return M
        
    AXISDICT = {
        "XYZ" : _rotMatXYZ,
        "XZY" : _rotMatXZY,
        "YXZ" : _rotMatYXZ,
        "YZX" : _rotMatYZX,
        "ZXY" : _rotMatZXY,
        "ZYX" : _rotMatZYX,
        "XY"  : _rotMatXY,
        "XZ"  : _rotMatXZ,
        "YX"  : _rotMatYX,
        "YZ"  : _rotMatYZ,
        "ZX"  : _rotMatZX,
        "ZY"  : _rotMatZY,
        "X"   : _rotMatX,
        "Y"   : _rotMatY,
        "Z"   : _rotMatZ
    }
    # -- End of autogenerated code ----------------------------------------------- #

    def formMatDirect( rx, ry, rz, axis ):
        # Assumes valid input, angles in floats, units radians
        return AXISDICT[ axis ]( rx, ry, rz )


class mat34( object ):

    def __init__( self, source=None, eye=False ):
        if( eye ):
            self.mat = self.eye34()
            return
        
        self.mat = np.zeros( (3,4), dtype=FLOAT_T )
        
        if( source is not None ):
            # guess input f;avour based on type
            array = source
            if( type( array ) in ( (), [] ) ):
                # list type, cast to np
                array = np.array( source, dtype=FLOAT_T )
            if( type( array ) == np.ndarray ):
                # it was, or now is an np array
                dims = len( array.shape )
                if( dims == 2 ):
                    # multi dim
                    pass
                elif( dims == 1 ):
                    # id, so either Qs or euler
                    pass
                else:
                    # > 2 dims
                    print( "Warning, can't imply a rotation frokm 3 or more dimentions" )
                    assert( False )
        # __init__


    @staticmethod
    def eye34():
        return np.array( [[1.,0.,0.,0.],[0.,1.,0.,0.],[0.,0.,1.,0.]], dtype=FLOAT_T )


    @staticmethod
    def angle2Mat( angle, M=None, axis=(1.,0.,0.) ):
        
        if( M is None ):
            M_ = np.zeros( (3,4), dtype=FLOAT_T )
        else:
            M_ = M

        c = np.cos( angle )
        s = np.sin( angle )
        v = 1.0 - c

        vx  = v * axis[0]
        vy  = v * axis[1]
        vz  = v * axis[2]

        sx  = s * axis[0]
        sy  = s * axis[1]
        sz  = s * axis[2]

        M_[0,0] = (vx * axis[0] +  c)
        M_[1,0] = (vx * axis[1] + sz)
        M_[2,0] = (vx * axis[2] - sy)

        M_[0,1] = (vy * axis[0] - sz)
        M_[1,1] = (vy * axis[1] +  c)
        M_[2,1] = (vy * axis[2] + sx)

        M_[0,2] = (vz * axis[0] + sy)
        M_[1,2] = (vz * axis[1] - sx)
        M_[2,2] = (vz * axis[2] +  c)
        return M_

    @staticmethod
    def mat2Angles( M ):
        yaw   = np.arctan2(  M[1,0], M[0,0] )
        pitch = np.arctan2( -M[2,0], np.sqrt( M[2,1]**2. + M[2,2]**2. ) )
        roll  = np.arctan2(  M[2,1], M[2,2] )
        return roll, pitch, yaw 


    def toAngles( self ):
        return self.mat2Angles( self.mat )


    def fromAngle( self, angle, axis=(1.,0.,0.) ):
        self.angle2Mat( angle, M=self.mat, axis=axis )

        
    @staticmethod
    def multiply( A, B ):
        return mat34._multi( A.mat, B.mat )
                
    @staticmethod
    def _multi( A, B ):
        """ Helper, expects ndarray """
        assert( A.shape == B.shape )
        assert( A.shape == (3,4) )
        
        ret = np.zeros( (3,4), dtype=FLOAT_T )
        ret
    def __str__( self ):
        tx, ty, tz = self.mat[:,3]
        rx, ry, rz = self.toAngles()
        return "mat34 TX:{} TY:{} TZ:{} RX:{} RY:{} RZ:{}".format( tx, ty, tz, rx, ry, rz )


class Quaternion( object ):
    
    def __init__( self, x=0., y=0., z=0., w=0. ):
        self.setQ( x, y, z, w )


    def setQ( self, x=0., y=0., z=0., w=0. ):
        self.X = x
        self.Y = y
        self.Z = z
        self.W = w
        if( (x + y + z + w) > 0.0 ):
            self.normalize()

        
    def normalize( self ):
        #
        s = self.X*self.X + self.Y*self.Y + self.Z*self.Z + self.W*self.W
        if( s == 1.0 ):
            # allready normalised
            return

        if( s < 1e-8 ):
            print( "Danger Div by Zero (Quartonion:normalize)" )
            return
        
        sqrt_rcp = 1.0 / np.sqrt( s )
        self.W = self.W * sqrt_rcp
        self.X = self.X * sqrt_rcp
        self.Y = self.Y * sqrt_rcp
        self.Z = self.Z * sqrt_rcp

        
    def fromAngles( self, x, y, z ): # yzx
        # http://www.euclideanspace.com/maths/geometry/rotations/conversions/eulerToQuaternion/index.htm
        angle = y * 0.5# was x
        sx, cx = np.sin( angle ), np.cos( angle )

        angle = z * 0.5# was y
        sy, cy = np.sin( angle ), np.cos( angle )

        angle = x * 0.5# was z
        sz, cz = np.sin( angle ), np.cos( angle )

        cxcy = cx * cy
        sxsy = sx * sy

        self.W = cxcy * cz - sxsy * cz
        self.X = cxcy * sz + sxsy * cz
        self.Y = sx*cy*cz  + cx*sy*sz
        self.Z = cx*sy*cz  - sx*cy*sz

        # should I normalize?


    def toRotMat( self ):
        # http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToMatrix/index.htm
        M = np.zeros( (3,3), dtype=np.float32 )

        XX = self.X * self.X
        XY = self.X * self.Y
        XZ = self.X * self.Z
        XW = self.X * self.W

        YY = self.Y * self.Y
        YZ = self.Y * self.Z
        YW = self.Y * self.W
        
        ZZ = self.Z * self.Z
        ZW = self.Z * self.W
        
        # x
        M[0,0] = 1. - 2. * YY - 2. * ZZ
        M[1,0] =      2. * XY + 2. * ZW
        M[2,0] =      2. * XZ - 2. * YW

        # y
        M[0,1] =      2. * XY - 2. * ZW
        M[1,1] = 1. - 2. * XX - 2. * ZZ
        M[2,1] =      2. * YZ + 2. * XW

        # z
        M[0,2] =      2. * XZ + 2. * YW
        M[1,2] =      2. * YZ - 2. * XW
        M[2,2] = 1. - 2. * XX - 2. * YY

        return M

    def toRotMat2( self ):
        # http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToMatrix/index.htm
        M = np.zeros( (3,3), dtype=np.float32 )

        XX = self.X * self.X
        XY = self.X * self.Y
        XZ = self.X * self.Z
        XW = self.X * self.W

        YY = self.Y * self.Y
        YZ = self.Y * self.Z
        YW = self.Y * self.W
        
        ZZ = self.Z * self.Z
        ZW = self.Z * self.W
        
        # x
        M[0,0] = 1. - 2. * YY - 2. * ZZ
        M[0,1] =      2. * XY + 2. * ZW
        M[0,2] =      2. * XZ - 2. * YW

        # y
        M[1,0] =      2. * XY - 2. * ZW
        M[1,1] = 1. - 2. * XX - 2. * ZZ
        M[1,2] =      2. * YZ + 2. * XW

        # z
        M[2,0] =      2. * XZ + 2. * YW
        M[2,1] =      2. * YZ - 2. * XW
        M[2,2] = 1. - 2. * XX - 2. * YY

        return M

    
    def toAngles( self ):
        # http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToEuler/index.htm
        x, y, z = 0., 0., 0.
        
        XX = self.X * self.X
        YY = self.Y * self.Y
        ZZ = self.Z * self.Z
        WW = self.W * self.W
        
        XY = self.X * self.Y
        ZW = self.Z * self.W

        test = (XY - ZW)
        #scale = XX + YY + ZZ + WW
        
        #  test singularitys
        if( test > 0.499 ):#(0.499 * scale) ):
            #
            x = 0.
            y = np.PI / 2.
            z = 2. * np.arctan2( self.X, self.W )
        elif( test < -0.499 ):#(-0.499 * scale) ):
            #
            x = 0.
            y = np.PI / -2.
            z = -2. * np.arctan2( self.X, self.W )
        else:
            #
            XW = self.X * self.W
            YZ = self.Y * self.Z
            YW = self.Y * self.W
            XZ = self.X * self.Z
            
            x = np.arctan2( ((2. * XW) - (2. * YZ)), (-XX + YY - ZZ + WW) )
            y = np.arcsin( 2. * test )
            z = np.arctan2( ((2. * YW) - (2. * XZ)) , (XX - YY - ZZ + WW) )
        return (x, y, z)


    def toAngles2( self ):
        
        return mat34.mat2Angles( self.toRotMat2() )


    def toAngles3( self ):
        # https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#Quaternion_to_Euler_Angles_Conversion
        x, y, z = 0., 0., 0.
        
        YY = self.Y * self.Y
        sx = 2. * (self.W * self.X + self.Y * self.Z)
        cx = 1. - 2. * (self.X * self.X + YY)
        x = np.arctan2( sx, cx )

        sy =  2. * (self.W * self.Y - self.Z * self.X)
        sy =  1. if sy > +1.0 else sy
        sy = -1. if sy < -1.0 else sy
        y = np.arcsin( sy )

        sz = 2. * (self.W * self.Z + self.X * self.Y)
        cz = 1. - 2. * (YY + self.Z * self.Z)
        z = np.arctan2( sz, cz )

        return (x, y, z)

    
    def __str__( self ):
        return "Quaternion X:{} Y:{} Z:{} W:{}".format(
            self.X, self.Y, self.Z, self.W )


if( __name__ == "__main__" ):
    angle = np.radians( 90 )
    print( np.cos( angle ), np.sin( angle ) )
    for axis in ( (1.,0.,0.),(0.,1.,0.), (0.,0.,1.) ):
        print( mat34.angle2Mat( angle, axis=axis ) )

    print( "----------------------------" )

    angle = np.radians( 90 )
    angle2 = np.radians( 45 )

    q = Quaternion()
    q.fromAngles( angle, 0., 0. )
    print( mat34.angle2Mat( angle ) )
    print q
    print q.toRotMat()
    print np.degrees( q.toAngles3() )

    q.fromAngles( angle2, 0, 0. )
    print( mat34.angle2Mat( angle2 ) )
    print q
    print q.toRotMat()
    print np.degrees( q.toAngles3() )
    
    A = mat34.angle2Mat( angle,  axis=(1.,0.,0.))
    B = mat34.angle2Mat( angle2, axis=(0.,1.,0.))
    M = np.matmul( B[:,:3], A[:,:3] ) # post multiply
    print M
    print np.degrees(mat34.mat2Angles( M ) )
    q.fromAngles( angle, angle2, 0. )
    print q
    print q.toRotMat()
    print np.degrees(mat34.mat2Angles( q.toRotMat() ) )
    print np.degrees( q.toAngles3() )

    print( "----------------------------" )
    # 2107343 test
    x, y, z, w = -0.305359643181186, 0.675003109597591, -0.262267007345134, 0.61833834363402
    true_true = np.array( [ 166.443497, -84.229225, -119.051704 ] )
    
    q.setQ( x, y, z, w )
    print q
    
    m1 = q.toRotMat()
    m2 = q.toRotMat2()

    print m1
    print m2

    print np.allclose( m1.T, m2 )
    print true_true
    d1 = np.degrees( mat34.mat2Angles( m1.T ) )
    d2 = np.degrees( mat34.mat2Angles( m2 ) )
    print d1
    print d2
    print true_true - d1

        
    
