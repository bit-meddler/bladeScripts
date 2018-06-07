"""
    Tool to inspect Vicon 'enf' files in a shooting database.
    
    There are two Taxonomies of MoCap shoot, "Organised" and "Chaotic".
    
    It can be expected that in an
    Organised shoot, there will be separate 'sessions' for System Calibration, Subject calibration, and then
    some kind of structure breaking up the day into AM/PM blocks, or perhaps more granular such as a sessions
    per setup (Better suited to cutscene or drama).
    
    In a Chaotic shoot there may be only one session, which contains all mocap data.
    
"""
import timecode as tc
import glob
import os
import ConfigParser
from viconFiles import CalXCPReader

class Take( tc.TcRange ):
    
    _DEFAULTS = {
        "STARTTIMECODE" : "00:00:00:00",
    }
    
    def __init__( self, rate=25, multiplier=5 ):
        super( Take, self ).__init__( rate, multiplier )        
        # take metadata
        self.file_name = ""
        self._file_fq = ""
        self.name = ""
        self._creation_time = ""
        self.subject_list = []
        self.chain = ""
        self.calibration_file = ""
        self.cal_id = 0
        self.cal_fq = ""
        self.notes = ""
        self.description = ""
        self.session = ""
        self.x2d_fq = ""

    def __str__( self ):
        durr_tc = self.end - self.start
        return "Take:'{}' lasting {} and featuring:{}".format(
            self.name, durr_tc, self.subject_list )
        
class ShootingDay( object ):
    """ Object representing a shooting day """
    
    def __init__( self, rate, multiplier, source_dir=None ):
        self.rate = rate
        self.multiplier = multiplier
        self.encountered_subjects = set()
        self.encountered_calibrations = {}
        self.subject_mixes = set()
        self.chains = set()
        self.takes = []
        self.data = {}
        self.sessions = []
        self._cur_session = ""
        self.remarks = ""
        self.skels = {}
        self._orphan_x2ds = []
        self.cals = []
        self.roms = []
        self.cxr = CalXCPReader()
        
        if( source_dir is not None ):
            self.setSession( source_dir )
        
        
    def setSession( self, source_dir ):
        self.name = os.path.basename( source_dir )
        self.source_dir = source_dir
        
        
    def newTake( self, name ):
        take = Take( self.rate, self.multiplier )
        take.name = name
        dup = False
        while( take.name in self.takes ):
            if( dup ):
                take.name += "_"
            else:
                take.name = self.session + "_" + take.name
                dup = True
        if( dup ):
            print( "'{}' in '{}' is a duplicate take in this session, and has been renamed '{}'".format(
                name, self.session, take.name
            ) )
        self.data[ take.name ] = take
        self.takes.append( take.name )
        take.session = self._cur_session
        return take


    def updateWith( self, take ):
        """ Examine take's calibration and subject list """
        assert( take in self.data.values() )
        # Scan the take for session info
        
        # calibration
        f_stat  = os.stat( take.cal_fq )
        cal_dob = f_stat.st_mtime
        
        # OK try a cal hash
        self.cxr.read( take.cal_fq )
        cal_hash = self.cxr.system.hash_()
        
        if( cal_hash not in self.encountered_calibrations ):
            self.encountered_calibrations[ cal_hash ] = []
        self.encountered_calibrations[ cal_hash ].append( (take.cal_fq, cal_dob) )
        take.cal_id = cal_hash
        
        # subject list
        subs = take.subject_list
        if( subs in self.subject_mixes ):
            return
        
        self.subject_mixes.add( subs )
        for sub in subs:
            self.encountered_subjects.add( sub )

        
    def newSession( self, session ):
        self.sessions.append( session )
        self._cur_session = session

        
    def getYoungCals( self ):
        ret = {}
        for cal_id, cal_list in self.encountered_calibrations.iteritems():
            youngest = ""
            val = 2**(31) - 1
            for cal_fq, cal_dob in cal_list:
                if( cal_dob < val ):
                    youngest = cal_fq
                    val = cal_dob
            ret[ cal_id ] = youngest        
        return ret
    
    
    ROM_CLUES = ( "rom", "snap" )
    CAL_CLUES = ( "wand", "calibration" )
    def separateTypes( self ):
        # work through all takes, and look for ROMs, and x2ds of wand waves
        
        # reset
        self.cals = []
        self.roms = []
        for take_name, take in self.data.iteritems():
            t_name = take_name.lower()
            for clue in self.ROM_CLUES:
                if( clue in t_name ):
                    # Might be a ROM!
                    self.roms.append( take_name )
                    self.takes.remove( take_name )
                    continue
            for clue in self.CAL_CLUES:
                if( clue in t_name ):
                    self.cals.append( take_name )
                    self.takes.remove( take_name )


class Survey( object ):
    def __init__( self, fps, multiplier ):
        self.shoot = ShootingDay( fps, multiplier )
        self.cf = ConfigParser.SafeConfigParser( Take._DEFAULTS )

        
    def getSessionData( self, day_path, session ):
        # setup
        self.shoot.newSession( session )
        
        # Explore takes
        res = glob.glob( os.path.join( day_path, session, "*.enf" ) )
        takes = [ t for t in res if ".Take" in t ]
        for t in takes:
            self.cf.read( t )
            name = self.cf.get( "Node Information", "NAME" )
            star = self.cf.get( "TRIAL_INFO", "STARTTIMECODE" )
            durr = self.cf.get( "TRIAL_INFO", "DURATIONFIELDS" )
            date = self.cf.get( "TRIAL_INFO", "CREATIONDATEANDTIME" )
            cal  = self.cf.get( "TRIAL_INFO", "CAMERACALIBRATION" )
            subs = self.cf.get( "TRIAL_INFO", "SUBJECTS" )
            note = self.cf.get( "TRIAL_INFO", "NOTES" )
            desc = self.cf.get( "TRIAL_INFO", "DESCRIPTION" )
            
            take = self.shoot.newTake( name )
            take._file_fq  = t
            take.file_name = os.path.basename( t )
            take.setFromStartDur( star, durr )
            take._creation_time = date
            take.calibration_file = cal
            take.cal_fq = os.path.join( day_path, session, cal )
            take.subject_list = tuple( sorted( subs.split( "," ) ) )
            take.notes = note
            take.description = desc
            
            self.shoot.updateWith( take )
        
        # Explore X2Ds
        x2ds = glob.glob( os.path.join( day_path, session, "*.x2d" ) )
        for x2d_fq in x2ds:
            name = os.path.basename( x2d_fq )[:-4]
            if( name in self.shoot.takes ):
                self.shoot.data[ name ].x2d_fq = x2d_fq
            else:
                # Orphaned X2D!
                take = self.shoot.newTake( name )
                take.x2d_fq = x2d_fq
                take.notes = "Orphaned X2D"
                self.shoot._orphan_x2ds.append( take )
                
        # Explore VSKs
        skels = glob.glob( os.path.join( day_path, session, "*.vsk" ) )
        for skel in skels:
            name = os.path.basename( skel )[:-4]
            self.shoot.skels[ name ] = skel

            
    @staticmethod
    def findSessions( path ):
        """ At a 'Capture Day' level, we're looking for dirs containing 'dir_name.Session???.enf' """
        ess = [] # Eclipse Subsessions
        for d in os.listdir( path ):
            res = glob.glob( os.path.join( path, d, "*Session*.enf" ) )
            if( len( res ) > 0 ):
                ses_name = os.path.basename( os.path.dirname( res[0] ) )
                ess.append( ses_name )
        return ess

        
    @staticmethod
    def compactName( name, drop_vowels=True ):
        if( (len( name ) > 8) and drop_vowels ):
            # Keep first letter
            return name[:1] + name[1:].translate( None, '_-aeiouAEIOU' )
        else:
            return name.translate( None, '_-' )

            
    def searchSession( self, session_path ):
        # collect session data
        self.shoot.setSession( session_path )
        day_sessions = self.findSessions( session_path )
        for ses in day_sessions:
            self.getSessionData( path, ses )
            
        # make more Giant friendly
        for take in self.shoot.data.values():
            chain_name, chain_order = self.orderSubjects( take.subject_list )
            take.chain = chain_name
            self.shoot.chains.add( take.chain )

        # cleanup bad stuff
        self.shoot.chains.remove( '' )
        self.shoot.encountered_subjects.remove( '' )
        # Split out obvious calibration and ROM takes
        self.shoot.separateTypes()
        
        
    # ----- order subject chain --- #
    HUMAN_CLUES = [ "hmc", "_cap", "softcap", "cara" ]
    PROP_CLUES  = [ "prop", "prp",
                   # Stage equipment
                   "calibrator", "clapper", "slate", "vslate", "deneke",
                   # virtual/tracked Cameras
                   "simulcam", "vcam", "ex3", "z1e", "epic", "camera",
                   # Colour codes
                   "pnk", "pink", "red", "grn", "green", "orange", "yellow", "yel", "blue", "blu", 
                   # Weapons Modern
                   "rifle", "pistol", "shotgun", "sniper",
                   # Bond Weapons
                   "p99", "870", "m4", "ak47", "mp5", "92f", "glock", "tt33", "psg", "g36",
                   # BF1 Weapons
                   "luger", "webley", "enfield", "tank", "mauser", "c96", "k98", "smle",
                   # Weapons Ancient
                   "sword", "swd", "kukuri", "axe", "sheild", "knife", "machette",
                   # Ryse
                   "roman", "celtic", "hammer", "gladius", "balista", "barbarian", "pilum", "spear",
                   # Ape tools / randoms
                   "stick", "spoon", "mug",
                   # Arm extensions
                   "ext" ]
    @staticmethod
    def orderSubjects( subject_list ):
        humans = []
        unknowns = []
        props = []
        for sub in subject_list:
            subject = sub.lower()
            find_h = [ c for c in Survey.HUMAN_CLUES if c in subject ]
            if( len( find_h ) > 0 ):
                humans.append( subject )
                continue
            find_p = [ c for c in Survey.PROP_CLUES  if c in subject ]
            if( len( find_p ) > 0 ):
                props.append( subject )
                continue
            unknowns.append( subject )
        order = sorted( humans ) + sorted( unknowns ) + sorted( props )
        chain = "-".join( map( Survey.compactName, order ) )
        return (chain, order)


    def printDigest( self ):
        print( "Surveying '{}'".format( self.shoot.name ) )
        print( "Takes:" )
        for take_name in self.shoot.takes:
            take = self.shoot.data[ take_name ]
            print( "\t'{}' uses '{}' and '{}'".format( take_name, take.cal_id, take.chain ) )
        print( "Calibrations:" )
        for cal_name in self.shoot.cals:
            print( "\tCalibration '{}' has id:{}".format( cal_name, "?" ) )
        prefered_cals = self.shoot.getYoungCals()
        for cal_id, cal_name in prefered_cals.iteritems():
            print( "\tCalibration '{}' has id {}".format( cal_name, cal_id ) )
        print( "ROMS:" )
        for rom in self.shoot.roms:
            print( "\tROM '{}' is available".format( rom ) )
            
# test
path = r"C:\ViconData\Teaching\ShootingDays\170323_A1_MosCap01"
#path = r"C:\ViconData\Teaching_2016\Workshops\170202_A1_MarkerTests_01"

surveyer = Survey( 25, 4 )
surveyer.searchSession( path )

surveyer.printDigest()
