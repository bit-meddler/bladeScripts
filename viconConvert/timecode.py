#!/usr/bin/env python
'''
Timecode computation and utility class
'''

class Timecode( object ):

    # Consts
    COMP_RATES = {  23:24, # these need to be ints
                    24:24,
                    25:25,
                    29:30,
                    30:30
    }
    TIME_RATES = {  23:23.976, # for display
                    24:24,
                    25:25,
                    29:29.97,
                    30:30
    }
    DIVISORS = {    23:1.001,
                    24:1.000,
                    25:1.000,
                    29:1.001,
                    30:1.000
    }
    # Retorts
    TYPE_ERROR_COMP_MSG = "Can't compare Timecode and '{}'"
    TYPE_ERROR_ARTH_MSG = "Can't do arithmatic with Timecode and '{}'"
    DECODE_ERROR_STRING = "Couldn't interpret '{}' as a valid timecode"

    '''
        The Drop frame tools are static as they are only a view onto an underlying Timecode,
        rather than tools to manipulate it.
        And frankly DFTC needs to die in a fire.
    '''
    @staticmethod
    def frames2DropTC( framesSinceEpoch ):
        '''
        http://en.wikipedia.org/wiki/SMPTE_Timecode#Drop_frame_Timecode
        Only "30" (29.97) fps Timecodes suffer the scurge of DF representation so 30 is hardcoded here.
        rule of thumb, 18f dropped every 10 mins - watch for mod 10 mins, as no frames are droppped.
        don't let the language confuse you, dropped == added to display count.
        No frames are lost or missing, they are just counted differently.
        '''
        # dfFramesInDecade = (10 * 60 * 30) - 18 # 10mins * 60secs * 30fps - 18 dropped frames
        dfFramesInDecade = 17982
        decadesSinceEpoch = framesSinceEpoch / dfFramesInDecade
        subDecadeFrames = framesSinceEpoch % dfFramesInDecade
        # adding the "dropped" frames on makes a "display Time" in the future
        newFramesSinceEpoch = framesSinceEpoch + 18*decadesSinceEpoch
        # plus acumulated drops in in the subdecade mins but not the mod 10 min
        if( subDecadeFrames > 2 ) :
            # 1798 = (60*30) -2 # two drops per min, over a decade
            newFramesSinceEpoch += 2*( (subDecadeFrames-2) / 1798 )

        # calculate display time
        secs = newFramesSinceEpoch / 30
        mins = secs / 60
        hour = mins / 60
        frms = newFramesSinceEpoch % 30
        secs = secs % 60
        mins = mins % 60
        hour = hour % 24
        return ( hour, mins, secs, frms )

    @staticmethod
    def dropTC2Frames( hour, mins, secs, frms ):
        # directly reading this tc value would be too high, so we need to compute an offset
        totalMinutes    = (60 * hour) + mins
        adjustment      = (2 * (totalMinutes - (totalMinutes / 10) ))# 2f *not* dropped every 10
        frameNumber     = ((((((hour*60) + mins)*60 + secs)*30) + frms) - adjustment)
        return frameNumber

    def getnosubTC( self ):
        ''' Babak counts frames as frames, even when there are 120 of them.
            Optitrack displays this way as well.  I thinkn Giant is frame agnostoc
        '''
        fps = Timecode.COMP_RATES[ self.rate ] * self.multiplier
        secs = self.quantaSinceEpoch / fps
        mins = secs / 60
        hour = mins / 60
        frms = self.quantaSinceEpoch % fps
        secs = secs % 60
        mins = mins % 60
        hour = hour % 24
        return ( hour, mins, secs, frms )

    def setnosubTC( self, hour, mins, secs, frms ):
        tMins = ( ( hour * 60) + mins )
        tSecs = ( (tMins * 60) + secs )
        tFrms = ( (tSecs * Timecode.COMP_RATES[ self.rate ] ) )
        tSubs = ( (tFrms * self.multiplier) + frms )
        self.quantaSinceEpoch = tSubs

    def getTC( self ):
        cardinality = -1 if( self.quantaSinceEpoch < 0 ) else 1
        rate = Timecode.COMP_RATES[ self.rate ]
        frms = self.quantaSinceEpoch / self.multiplier
        secs = frms / rate
        mins = secs / 60
        hour = mins / 60
        subs = self.quantaSinceEpoch % self.multiplier
        frms = frms % rate
        secs = secs % 60
        mins = mins % 60
        hour = hour % 24
        hour *= cardinality
        return ( hour, mins, secs, frms, subs )

    def setFromTC( self, other ):
        self.rate = other.rate
        self.multiplier = other.multiplier
        self.quantaSinceEpoch = other.quantaSinceEpoch
        self.msOffset = other.msOffset
        self.qTime = other.qTime
        self.sourceBwavRate = other.sourceBwavRate
        self._dfFlag = other._dfFlag

    def setTC( self, hour, mins, secs, frms=0, subs=0 ):
        cardinality = -1 if( hour < 0 ) else 1
        # TODO: Do the right thing with -ve Timecodes!
        tMins = ( ( hour * 60) + mins )
        tSecs = ( (tMins * 60) + secs )
        tFrms = ( (tSecs * Timecode.COMP_RATES[ self.rate ] ) + frms )
        tSubs = ( (tFrms * self.multiplier) + subs )
        self.quantaSinceEpoch = tSubs
        self.msOffset = 0
        
    def setFromStringTC( self, tcString ):
        # TODO try: catch ValueError?
        
        toks = tcString.split( ":" )
        num_toks = len( toks )
        hrs, min = int(toks[0]), int(toks[1])
        if num_toks==4:
            # NDF format
            sec, frm = int(toks[2]), int(toks[3])
            self.setTC( hrs, min, sec, frm )
            return
        elif num_toks==3:
            # Assume DF format (hh:mm:ss;ff)
            if ";" in toks[2]:
                ftoks = toks[2].split( ";" )
                sec, frm = int(ftoks[0]), int(ftoks[1])
                self.setDFTC( hrs, min, sec, frm )
                return
            # Vicon format (hh:mm:ss.ff)
            if "." in toks[2]:
                ftoks = toks[2].split( "." )
                sec, frm = int(ftoks[0]), int(dftoks[1])
                self.setTC( hrs, min, sec, frm )
                return
            
        raise ValueError( Timecode.DECODE_ERROR_STRING.format( tcString ) )

    def getRateData(self):
        return self.rate, self.multiplier

    def getRateDataHuman(self):
        return Timecode.TIME_RATES[ self.rate ], self.multiplier

    def getDFTC( self ):
        subs = self.quantaSinceEpoch % self.multiplier
        ( hour, mins, secs, frms ) = frames2DropTC( self.getFramesFromEpoch() )
        return ( hour, mins, secs, frms, subs )

    def setDFTC( self, hour, mins, secs, frms=0, subs=0, offset=0 ):
        framesSinceEpoch = self.dropTC2Frames( hour, mins, secs, frms )
        self.quantaSinceEpoch = ( (framesSinceEpoch * self.multiplier) + subs )
        self.msOffset = offset
        self._dfFlag = True

    def getQuantaFromEpoch( self ):
        return self.quantaSinceEpoch

    def setQuantaFromEpoch( self, quanta ):
        self.quantaSinceEpoch = quanta

    def getFramesFromEpoch( self ):
        return (self.quantaSinceEpoch / self.multiplier)

    def setFramesFromEpoch( self, frames ):
        self.quantaSinceEphoch = (frames * self.multiplier)

    def getMSfromEpoch( self ):
        return ((self.qTime * self.quantaSinceEpoch) * 1000.) + self.msOffset

    def setMSfromEpoch( self, msFromEp ):
        # Set TC based on ms from Epoch value
        f_mse = float( msFromEp )
        quantas = round( (f_mse / 1000.0) / self.qTime, 0. )
        remainder = f_mse - (quantas * self.qTime)*1000.
        self.quantaSinceEpoch = int( quantas )
        self.msOffset = remainder

    def getHMS( self ):
        ( hour, mins, secs, frms, subs ) = self.getTC()
        fracs  = (frms  * self.multiplier ) + subs
        fracs  =  fracs * self.qTime
        fracs +=  secs
        return (hour, mins, fracs)

    def setHMS( self, hour, mins, secs ):
        tSecs = ((hour * 60) + mins) * 60
        tSecs += secs
        quantas = round( tSecs / self.qTime, 0 )
        remainder = tSecs - (quantas * self.qTime) * 1000
        self.quantaSinceEpoch = int( quantas )
        self.msOffset = remainder

    def getBwavTC( self, rate=48000 ):
        '''
        The Timecode in a bWav is samples since Epoch.
        Common audio sample rates are 44.1kHz & 48kHz, bWav mostly being 48k.
        '''
        return ( self.getMSfromEpoch() * (rate/1000) )

    def setBwavTC( self, audioSamplesSinceEpoch, rate=48000 ):
        msFromEpoch = float( audioSamplesSinceEpoch ) / float( rate )
        msFromEpoch *= 1000 # ms
        self.sourceBwavRate = rate
        self.setMSfromEpoch( msFromEpoch )

    def isWholeFrame( self ):
        return ( (self.quantaSinceEpoch % self.multiplier) == 0 )

    def isCompatible( self, other ):
        return ( (self.rate == other.rate) and (self.multiplier == other.multiplier) )
        
    def isBroadcastable( self, other):
        ''' With division/multiplication these rates can comunicate.
            TODO: I'm ignoring for the moment that 150fps = 25fps and 30fps
        '''
        return ( (self.rate == other.rate) )
        
    def inc( self ):
        ''' Depricated by the += (iadd) operation '''
        self.quantaSinceEpoch += 1

    def jumpQuanta( self, quanta ):
        self.quantaSinceEpoch += quanta

    def jumpFrames( self, frames ):
        quanta = frames * self.multiplier
        self.quantaSinceEpoch += quanta

    def readAs( self, alienRate=29, alienMultiplier=1 ):
        ''' Given self, what would the Timecode be if we were running a different fps?'''
        newTC = Timecode( alienRate, alienMultiplier )
        newTC.setMSfromEpoch( self.getMSfromEpoch() )
        return newTC.getTC()

    def __init__( self, rate=25, multiplier=1):
        ''' You Cannot instanciate and set a time, trust me it's better this way. '''
        self.rate = rate
        self.multiplier = multiplier if multiplier != 0 else 1
        self.quantaSinceEpoch = 0
        self.msOffset = 0 # This is a notional ms Offset for aligning diferent TC universes.
        exact_rate = Timecode.COMP_RATES[ self.rate ] / Timecode.DIVISORS[ self.rate ]
        self.qTime = 1. / ( exact_rate * self.multiplier )
        self.sourceBwavRate = -1 # don't know if we derived from a bWav
        self._dfFlag = False # Don't know yet
        
    def __repr__( self ):
        h, m, s, f, u = self.getTC()
        d = ";" if self._dfFlag else ":"
        D = "DF" if self._dfFlag else "NDF"
        rate = Timecode.TIME_RATES[ self.rate ]
        multi = self.multiplier
        freq = rate * multi
        ret = "Timecode {:0>2d}:{:0>2d}:{:0>2d}{}{:0>2d}.{} {} " + \
              "{: .3f}ms offset @ {}fps x{} multiplier ({}Hz)"
        return ret.format( h, m, s, d, f, u, D, self.msOffset, rate, multi, freq )

    def __str__( self ):
        h, m, s, f, u = self.getTC()
        d = ";" if self._dfFlag else ":"
        return "{:0>2d}:{:0>2d}:{:0>2d}{}{:0>2d}.{}".format( h, m, s, d, f, u )

    ''' Arythmetic overloads.  These allow 3 types to manipulare Timecode.
        It is assumed that:
            Ints = Quanta from Epoch
            Floats = ms From Epoch
            Timecodes = any Timecode (compensate for alien format and msOffsest by working in ms)
    '''
    def __add__( self, other ):
        ret = Timecode( self.rate, self.multiplier )
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_ARTH_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            if self.isCompatible( other ):
                ret.quantaSinceEpoch = ( self.quantaSinceEpoch + other.quantaSinceEpoch )
            else:
                ret.setMSfromEpoch( self.getMSfromEpoch() + other.getMSfromEpoch() )
        elif isinstance( other, int ):
            ret.quantaSinceEpoch = ( self.quantaSinceEpoch + other )
        elif isinstance( other, float ):
            ret.setMSfromEpoch( self.getMSfromEpoch() + other )
        return ret

    def __iadd__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_ARTH_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            if self.isCompatible( other ):
                self.quantaSinceEpoch += other.quantaSinceEpoch
            else:
                self.setMSfromEpoch( self.getMSfromEpoch() + other.getMSfromEpoch() )
        elif isinstance( other, int ):
            self.quantaSinceEpoch = ( self.quantaSinceEpoch + other )
        elif isinstance( other, float ):
            self.setMSfromEpoch( self.getMSfromEpoch() + other )
        return self

    def __sub__( self, other ):
        ret = Timecode( self.rate, self.multiplier )
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_ARTH_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            if self.isCompatible( other ):
                ret.quantaSinceEpoch = ( self.quantaSinceEpoch - other.quantaSinceEpoch )
            else:
                ret.setMSfromEpoch( self.getMSfromEpoch() - other.getMSfromEpoch() )
        elif isinstance( other, int ):
            ret.quantaSinceEpoch = ( self.quantaSinceEpoch - other )
        elif isinstance( other, float ):
            ret.setMSfromEpoch( self.getMSfromEpoch() - other )
        return ret

    def __isub__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_ARTH_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            if self.isCompatible( other ):
                self.quantaSinceEpoch -= other.quantaSinceEpoch
            else:
                self.setMSfromEpoch( self.getMSfromEpoch() - other.getMSfromEpoch() )
        elif isinstance( other, int ):
            self.quantaSinceEpoch = ( self.quantaSinceEpoch - other )
        elif isinstance( other, float ):
            self.setMSfromEpoch( self.getMSfromEpoch() - other )
        return self

    def __lt__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            return (self.getMSfromEpoch() <  other.getMSfromEpoch())
        elif isinstance( other, int ):
            return self.quantaSinceEpoch < other
        elif isinstance( other, float ):
            return self.getMSfromEpoch() < other

    def __le__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            return (self.getMSfromEpoch() <=  other.getMSfromEpoch())
        elif isinstance( other, int ):
            return self.quantaSinceEpoch <= other
        elif isinstance( other, float ):
            return self.getMSfromEpoch() <= other

    def __gt__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            return (self.getMSfromEpoch() >  other.getMSfromEpoch())
        elif isinstance( other, int ):
            return self.quantaSinceEpoch > other
        elif isinstance( other, float ):
            return self.getMSfromEpoch() > other

    def __ge__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            return (self.getMSfromEpoch() >=  other.getMSfromEpoch())
        elif isinstance( other, int ):
            return self.quantaSinceEpoch >= other
        elif isinstance( other, float ):
            return self.getMSfromEpoch() >= other

    def __eq__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            return (self.getMSfromEpoch() ==  other.getMSfromEpoch())
        elif isinstance( other, int ):
            return self.quantaSinceEpoch == other
        elif isinstance( other, float ):
            return self.getMSfromEpoch() == other

    def __ne__( self, other ):
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            return (self.getMSfromEpoch() !=  other.getMSfromEpoch())
        elif isinstance( other, int ):
            return self.quantaSinceEpoch != other
        elif isinstance( other, float ):
            return self.getMSfromEpoch() != other

    def __cmp__( self, other ):
        selfComp, otherComp = 0, 0
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            selfComp, otherComp = self.getMSfromEpoch(), other.getMSfromEpoch()
        elif isinstance( other, int ):
            selfComp, otherComp = self.quantaSinceEpoch, other
        elif isinstance( other, float ):
            selfComp, otherComp = self.getMSfromEpoch(), other
        if   selfComp <  otherComp:
            return -1
        elif selfComp == otherComp:
            return  0
        else:
            return  1      
# end of Timecode       

class TcRange( object ):
    ''' A Timecode Region, having a start, and an end.
    
    '''
    def __init__( self, rate=25, multiplier=1 ):
        self.rate = rate
        self.multiplier = multiplier
        self.start = Timecode( self.rate, self.multiplier )
        self.end   = Timecode( self.rate, self.multiplier )
        
    def __str__( self ):
        sh, sm, ss, sf, su = self.start.getTC()
        eh, em, es, ef, eu = self.end.getTC()
        durr_tc = self.end - self.start
        
        return "{:0>2d}:{:0>2d}:{:0>2d}:{:0>2d}.{} to {:0>2d}:{:0>2d}:{:0>2d}:{:0>2d}.{} lasting {}".format(
                sh, sm, ss, sf, su, eh, em, es, ef, eu, durr_tc.getQuantaFromEpoch() )
    
    def setFromStartDur( self, start_string, durr ):
        ''' Duration is assumed to be frames, could extend to float==seconds
        '''
        durr_int = 0
        if( type(durr) == int ):
            durr_int = durr
        elif( type(durr) == str ):
            durr_int = int( durr )
        self.start.setFromStringTC( start_string )
        self.end.setFromTC( self.start )
        self.end += durr_int
        
    def __contains__( self, other ):
        ''' Yum yum, syntactic sweatenr '''
        begint = endt = other_comp = 0
        
        if type( other ) not in ( Timecode, int, float ):
            raise TypeError( Timecode.TYPE_ERROR_COMP_MSG.format( type( other ).__name__ ) )
        elif isinstance( other, Timecode ):
            begint, endt, other_comp = self.start.getMSfromEpoch(), self.end.getMSfromEpoch(), other.getMSfromEpoch()
        elif isinstance( other, int ):
            begint, endt, other_comp = self.start.quantaSinceEpoch, self.end.quantaSinceEpoch, other
        elif isinstance( other, float ):
            begint, endt, other_comp = self.start.getMSfromEpoch(), self.end.getMSfromEpoch(), other
        
        if other_comp < begint : return False
        if other_comp > endt   : return False
        return True
        
    def __index__( self, idx ):
        if idx<0 or idx>1:
            raise IndexError( "index out of range" )
        else:
            return self.start if idx==0 else self.end

        
# End of tcRange    
class ClipTimecode( Timecode ):
    ''' Mocap data starts at frame 0 ... n
        The recording will have started at some random time.
        We want to display the "Frame offset" 0..n of the clip and
        the hh:mm:ss:ff.uu Timecode for sync to audio etc.
        we can also read the "time in clip" for display
    '''
    def __init__( self, rate=25, multiplier=1):
        super( clipTimecode, self ).__init__( rate, multiplier )
        self.offset = Timecode( rate, multiplier )

    def getDisplayTC( self ):
        ret = Timecode( self.rate, self.multiplier )
        ret = self + self.offset
        return ret.getTC

    def setFromDisplayTC( self, targetTimecode ):
        actual = targetTimecode - self.offset
        self.setFromTC( actual )
# end of clipTimecode   

class DualMultiTimecode( Timecode ):
    ''' Syncronising MoCap data and Video data, usually Video is x1 and MoCap x4 or x5.
        this class will provide functions to maintain correct frame numbers and display TC.

        Highest Multiplier has primacy.
        inc():
            primary += primary.multiplier
            secondary += secondary.multiplier

    '''
    pass
# end of dualMultiTimecode

if __name__ == "__main__":
    # Testing Timecode object
    tc = Timecode( 23, 5 )
    if False:
        tc.setTC( 3, 10, 27, 6, 2 )
        time = tc.getMSfromEpoch()
        print time, tc, Timecode.frames2DropTC( tc.getFramesFromEpoch() ), tc.getnosubTC()
        time += 5599
        tc.setMSfromEpoch( time )
        print tc.getMSfromEpoch(), tc, Timecode.frames2DropTC( tc.getFramesFromEpoch() ), tc.getnosubTC()
    elif False:
        tc.setTC( 3, 10, 27, 23, 2 )
        for i in range( 8 ):
            tc.inc()
            print tc.getTC(), tc.getHMS(), tc.getnosubTC()
    elif False:
        # test nosubTC
        tc.setnosubTC( 3, 10, 27, 119 )
        print tc.getTC(), tc.getnosubTC()
    # test MS
    elif False:
        tc = Timecode( 23, 1 )
        for i in xrange( 1, 10 ):
            tc.setTC( 0, 0, i, 0, 0 )
            print tc, tc.quantaSinceEpoch, tc.getMSfromEpoch()
    elif False:
        # Test bWav TC
        bRate = 48000
        tc.setTC( 0, 0, 10, 0, 0 )
        time = tc.getMSfromEpoch()
        print time, tc, tc.msOffset
        tc.setBwavTC( 48000, bRate ) # 1 sec
        print tc, tc.getBwavTC( bRate )
        samps = (time / 1000) * bRate
        tc.setBwavTC( samps, bRate )
        print repr( tc )
    elif True:
        # Test Maths
        tc1 = Timecode( 23, 1 )
        tc2 = Timecode( 23, 1 )
        tc1.setTC( 0, 0, 12, 0, 0 )
        tc2.setTC( 0, 0, 8, 0, 0 )
        print tc1, tc2
        tc1 = tc1 + 12
        tc2 = tc2 + tc1
        print tc1, tc2
        tc1 = tc1 + 50.0 # about 1f
        tc2 = tc2 + tc1
        print tc1, tc2
        print tc1>tc2, tc1<tc2, tc1!=tc2, tc1==tc2
        tc1.setQuantaFromEpoch( -100 )
        print tc1
        print repr( tc )
    elif False:
        tc = Timecode( 23, 5 )
        tc.setTC( 13, 22, 22, 22, 0 )
        ctc = clipTimecode( 23, 5 )
        ctc.offset.setTC( 13, 22, 12, 22, 0 )
        print ctc, ctc.getDisplayTC()
        ctc += 144
        print ctc, ctc.getDisplayTC()
        ctc.setFromDisplayTC( tc )
        print ctc, ctc.getDisplayTC()