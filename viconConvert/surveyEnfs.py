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
    """ Also a 'Take factory' once the rate & multi is configured """
    pass
    
    
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
        self.calibration_name = ""
        self.notes = "NOTES"
        self.description = "DESCRIPTION"
        
        
        
def getSessionTakes( path ):
    res = glob.glob( os.path.join( path, "*.enf" ) )
    takes = [ t for t in res if ".Take" in t ]

    cf = ConfigParser.SafeConfigParser( Take._DEFAULTS )

    take_data = []
    for t in takes:
        take = Take( 25, 4 )# Do in a factory
        cf.read( t )
        name = cf.get( "Node Information", "NAME" )
        star = cf.get( "TRIAL_INFO", "STARTTIMECODE" )
        durr = cf.get( "TRIAL_INFO", "DURATIONFIELDS" )
        date = cf.get( "TRIAL_INFO", "CREATIONDATEANDTIME" )
        note = cf.get( "TRIAL_INFO", "NOTES" )
        desc = cf.get( "TRIAL_INFO", "DESCRIPTION" )
        cal  = cf.get( "TRIAL_INFO", "CAMERACALIBRATION" )
        subs = cf.get( "TRIAL_INFO", "SUBJECTS" )
        
        take.setFromStartDur( star, durr )
        
        take.name      = name
        take._file_fq  = t
        take.file_name = os.path.basename( t )
        
        take._creation_time = date
        
        take.notes = note
        take.description = desc
        
        take.subject_list = subs.split( "," )

        take_data.append( take )
    return take_data
    
# test
path = r"C:\ViconData\Teaching\ShootingDays\180226_A1_GroupB_01\PM"
d = getSessionTakes( path )

print d[0].file_name
print d[0].subject_list
print d[0]
