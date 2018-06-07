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
    
    def __init__( self, rate, multiplier, source_dir ):
        assert( source_dir is not None )
        self.rate = rate
        self.multiplier = multiplier
        self.source_dir = source_dir
        self.encountered_subjects = set()
        self.encountered_calibrations = {}
        self.subject_mixes = set()
        self.takes = []
        self.data = {}
        self.sessions = []
        self._cur_session = ""
        self.remarks = ""
        self.skels = {}
        self._orphan_x2ds = []
        self.cals = []
        self.roms = []
        
        
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
        # TODO: fingerprinting file by size works in the 98% case,
        #       but I should really read, form P mats, then hash them.
        f_stat  = os.stat( take.cal_fq )
        cal_sz  = f_stat.st_size
        cal_dob = f_stat.st_mtime
        if( cal_sz not in self.encountered_calibrations ):
            self.encountered_calibrations[ cal_sz ] = []
        self.encountered_calibrations[ cal_sz ].append( (take.cal_fq, cal_dob) )
        take.cal_id = cal_sz
        
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
                    self.takes.delete( take_name )
                    continue
            for clue in self.CAL_CLUES:
                if( clue in t_name ):
                    self.cals.append( take_name )
                    self.takes.delete( take_name )

                    
def getSessionData( day_path, session, shoot ):
    # setup
    cf = ConfigParser.SafeConfigParser( Take._DEFAULTS )
    shoot.newSession( session )
    
    # Explore takes
    res = glob.glob( os.path.join( day_path, session, "*.enf" ) )
    takes = [ t for t in res if ".Take" in t ]
    for t in takes:
        cf.read( t )
        name = cf.get( "Node Information", "NAME" )
        star = cf.get( "TRIAL_INFO", "STARTTIMECODE" )
        durr = cf.get( "TRIAL_INFO", "DURATIONFIELDS" )
        date = cf.get( "TRIAL_INFO", "CREATIONDATEANDTIME" )
        cal  = cf.get( "TRIAL_INFO", "CAMERACALIBRATION" )
        subs = cf.get( "TRIAL_INFO", "SUBJECTS" )
        note = cf.get( "TRIAL_INFO", "NOTES" )
        desc = cf.get( "TRIAL_INFO", "DESCRIPTION" )
        
        take = shoot.newTake( name )
        take._file_fq  = t
        take.file_name = os.path.basename( t )
        take.setFromStartDur( star, durr )
        take._creation_time = date
        take.calibration_file = cal
        take.cal_fq = os.path.join( day_path, session, cal )
        take.subject_list = tuple( sorted( subs.split( "," ) ) )
        take.notes = note
        take.description = desc
        
        shoot.updateWith( take )
    
    # Explore X2Ds
    x2ds = glob.glob( os.path.join( day_path, session, "*.x2d" ) )
    for x2d_fq in x2ds:
        name = os.path.basename( x2d_fq )[:-4]
        if( name in shoot.takes ):
            shoot.data[ name ].x2d_fq = x2d_fq
        else:
            # Orphaned X2D!
            take = shoot.newTake( name )
            take.x2d_fq = x2d_fq
            take.notes = "Orphaned X2D"
            shoot._orphan_x2ds.append( take )
            
    # Explore VSKs
    skels = glob.glob( os.path.join( day_path, session, "*.vsk" ) )
    for skel in skels:
        name = os.path.basename( skel )[:-4]
        shoot.skels[ name ] = skel


def findSessions( path ):
    """ At a 'Capture Day' level, we're looking for dirs containing 'dir_name.Session???.enf' """
    ess = [] # Eclipse Subsessions
    for d in os.listdir( path ):
        res = glob.glob( os.path.join( path, d, "*Session*.enf" ) )
        if( len( res ) > 0 ):
            ses_name = os.path.basename( os.path.dirname( res[0] ) )
            ess.append( ses_name )
    return ess


def compactName( name, drop_vowels=True ):
    if( (len( name ) > 8) and drop_vowels ):
        # Keep first letter
        return name[:1] + name[1:].translate( None, '_-aeiouAEIOU' )
    else:
        return name.translate( None, '_-' )


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
def orderSubjects( subject_list ):
    humans = []
    unknowns = []
    props = []
    for sub in subject_list:
        subject = sub.lower()
        find_h = [ c for c in HUMAN_CLUES if c in subject ]
        if( len( find_h ) > 0 ):
            humans.append( subject )
            continue
        find_p = [ c for c in PROP_CLUES  if c in subject ]
        if( len( find_p ) > 0 ):
            props.append( subject )
            continue
        unknowns.append( subject )
    order = sorted( humans ) + sorted( unknowns ) + sorted( props )
    chain = "-".join( map( compactName, order ) )
    return (chain, order)
    
# test
path = r"C:\ViconData\Teaching\ShootingDays\170323_A1_MosCap01"
#path = r"C:\ViconData\Teaching_2016\Workshops\170202_A1_MarkerTests_01"
day_sessions = findSessions( path )
shoot = ShootingDay( 25, 4, path )
for ses in day_sessions:
    getSessionData( path, ses, shoot )

print shoot.encountered_subjects
print shoot.data.keys()
print shoot.getYoungCals()
