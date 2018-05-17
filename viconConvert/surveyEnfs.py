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
        self.takes = {}
        self.sessions = []
        self._cur_session = ""
        self.remarks = ""
        
        
    def newTake( self, name ):
        take = Take( self.rate, self.multiplier )
        take.name = name
        while( take.name in self.takes ):
            take.name += "_"
        self.takes[ take.name ] = take
        take.session = self._cur_session
        return take


    def updateWith( self, take ):
        """ Examine takes calibration and subject list """
        assert( take in self.takes.values() )
        # Scan the take for session info
        calibration_fq = os.path.join( self.source_dir, take.session, take.calibration_file )
        # calibration
        # TODO: fingerprinting file byu sz works in 98% case, should really read, for P mats, then hash them
        f_stat = os.stat( calibration_fq )
        cal_sz = f_stat.st_size
        if( cal_sz not in self.encountered_calibrations ):
            self.encountered_calibrations[ cal_sz ] = []
        self.encountered_calibrations[ cal_sz ].append( take.calibration_file )
        
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

        
        
class Take( tc.TcRange ):
    
    _DEFAULTS = {
        "STARTTIMECODE" : "00:00:00:00",
    }
    
    def __init__( self, rate=25, multiplier=5 ):
        super( Take, self ).__init__( rate, multiplier )        
        # take metadata
        self.file_name = ""
        self._file_fq = ""
        self.name = "NAME"
        self._creation_time = "CREATIONDATEANDTIME"
        self.subject_list = []
        self.calibration_file = ""
        self.notes = "NOTES"
        self.description = "DESCRIPTION"
        self.session = ""
        
        
        
def getSessionTakes( day_path, session, shoot ):
    res = glob.glob( os.path.join( day_path, session, "*.enf" ) )
    takes = [ t for t in res if ".Take" in t ]

    cf = ConfigParser.SafeConfigParser( Take._DEFAULTS )

    shoot.newSession( session )
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
        take.subject_list = tuple( sorted( subs.split( "," ) ) )
        take.notes = note
        take.description = desc
        
        shoot.updateWith( take )
        

def findSessions( path ):
    """ At a 'Capture Day' level, we're looking for dirs containing 'dir_name.Session???.enf' """
    ess = [] # Eclipse Subsessions
    for d in os.listdir( path ):
        res = glob.glob( os.path.join( path, d, "*Session*.enf" ) )
        if( len( res ) > 0 ):
            ses_name = os.path.basename( os.path.dirname( res[0] ) )
            ess.append( ses_name )
    return ess
        
# test 1
path = r"C:\ViconData\Teaching\ShootingDays\170323_A1_MosCap01"
day_sessions = findSessions( path )
shoot = ShootingDay( 25, 4, path )
for ses in day_sessions:
    getSessionTakes( path, ses, shoot )

print shoot.encountered_subjects
print shoot.takes.keys()
