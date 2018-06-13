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
from genConvert import genJobList, outputBatFile
from utils import mkdir_p, fragmentFilePath
import giantFiles as gf


class Take( tc.TcRange ):
    
    _DEFAULTS = {
        "STARTTIMECODE" : "00:00:00:00",
    }
    
    def __init__( self, rate=25, multiplier=5 ):
        super( Take, self ).__init__( rate, multiplier )        
        # take metadata
        self.file_name = ""
        self.enf_fq = ""
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
        # giant conversion stuff
        self.prefered_cal_fq = ""
        self.prefered_cal_name = ""
        

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
        self.skels = {} # structured data ( name, skel_fq, session, vsk_dob, vsk_sz )
        self._orphan_x2ds = []
        self.cals = [] # structured data
        self.roms = []
        self.cxr = CalXCPReader()
        
        if( source_dir is not None ):
            self.setRoot( source_dir )
        
        
    def setRoot( self, source_dir ):
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
                take.name = self._cur_session + "_" + take.name
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
        cal_sz  = f_stat.st_size
        
        # OK try a cal hash
        self.cxr.read( take.cal_fq )
        cal_hash = self.cxr.system.hash_()
        
        if( cal_hash not in self.encountered_calibrations ):
            self.encountered_calibrations[ cal_hash ] = []
        self.encountered_calibrations[ cal_hash ].append( (take.cal_fq, cal_dob, cal_sz) )
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
            for cal_fq, cal_dob, cal_sz in cal_list:
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
        for take_name in self.data.keys():
            t_name = take_name.lower()
            for clue in self.ROM_CLUES:
                if( clue in t_name ):
                    # Might be a ROM!
                    self.roms.append( take_name )
                    self.takes.remove( take_name )
                    # remove empty sub list if present, so sub can be attached later
                    rom = self.data[ take_name ]
                    if( '' in rom.subject_list ):
                        new_sl = list( rom.subject_list )
                        new_sl.remove( '' )
                        rom.subject_list = tuple( new_sl )
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

            take.enf_fq  = t
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
            # collision here with skels in 'rom' session vs am/pm sessions
            name = os.path.basename( skel )[:-4]
            canonical_name = self.shoot._cur_session + "_" + name
            # TODO: Fingerprint the VSK with a hash, for now lets use size (again)
            f_stat  = os.stat( skel )
            vsk_dob = f_stat.st_mtime
            vsk_sz  = f_stat.st_size
            self.shoot.skels[ canonical_name ] = ( name, skel, self.shoot._cur_session, vsk_dob, vsk_sz )
        # Now make unique??

            
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
        self.shoot.setRoot( session_path )
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
        self.shoot.subject_mixes.remove( ('',) )
        # scan encountered subjects and look for subs who are in a mix, but not alone!
        # Split out obvious calibration and ROM takes
        self.shoot.separateTypes()
        
        # attach suitable calibrations to takes
        prefered_cals = self.shoot.getYoungCals()
        for take_name in self.shoot.takes:
            take = self.shoot.data[ take_name ]
            take.prefered_cal_fq = prefered_cals[ take.cal_id ]
            _, take.prefered_cal_name, _ = fragmentFilePath( take.prefered_cal_fq )

        # Try to match subjects to ROMs in session, locate orphaned Subjects
        for skel_dat in self.shoot.skels.values():
            name, skel_fq, session, vsk_dob, vsk_sz = skel_dat
            # humm O^2 - as there will not be 000s of ROM's I'm OK with it.
            for rom_name in self.shoot.roms:
                if( name in rom_name ):
                    rom_take = self.shoot.data[ rom_name ]
                    if( len( rom_take.subject_list ) < 1 ):
                        rom_take.subject_list = [name]

            
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
            print( "\t'{}' features '{}' and uses '{}'".format( take_name, take.chain,
                    os.path.basename( take.prefered_cal_fq ) )
            )
            
            
        print( "\nCalibrations:" )
        for cal_name in self.shoot.cals:
            print( "\tWandwave '{}' exists in session".format( cal_name ) )
        prefered_cals = self.shoot.getYoungCals()
        for cal_id, cal_name in prefered_cals.iteritems():
            print( "\tCalibration '{}' is prefered".format( os.path.basename( cal_name ) ) )
            
        print( "\nROMS:" )
        for rom in self.shoot.roms:
            rom_take = self.shoot.data[ rom ]
            sub = "nothing"
            if( len( rom_take.subject_list ) > 0 ):
                sub = rom_take.subject_list
            print( "\tROM '{}' is available, and calibrates {}".format( rom, sub ) )
            
        print( "\nSubjects:" )
        subject_jumble = self.shoot.subject_mixes | set( (x,) for x in self.shoot.encountered_subjects )
        subs = sorted( list( subject_jumble ), key=lambda x : len( x ) )
        for sub in subs:
            if( len( sub ) > 1 ):
                print( "\tA chain of '{}' is required".format( " and ".join( sub ) ) )
            else:
                print( "\tA scaling for '{}' needs to be generated".format( sub ) )

                
    def doConversion( self, giant_base_path, simulate=False ):
        """ Hacky but seems to deliver as expected.  Needs a considerable refactor to enable
            pluggable giant folder structure (eg. stock Giant Vs Customer1, Customer2, etc)
        """
        print( "Building Conversion from '{}' into '{}'".format( self.shoot.name, giant_base_path ) )
        
        batch_jobs = []
        
        # stub in giant day & standard folders
        DEFAULT_STRUCT = [ "capture", "calib", "probspec", "volume", "subject", "scaling" ]
        for folder in DEFAULT_STRUCT:
            mkdir_p( os.path.join( giant_base_path, folder ) )
            
        # stub in calibrations
        prefered_cals = self.shoot.getYoungCals()
        section = os.path.join( giant_base_path, "calib" )
        for cal_fq in prefered_cals.values():
            _, cal_name, _ = fragmentFilePath( cal_fq )
            mkdir_p( os.path.join( section, cal_name ) )
            # needs a csf as an inital estimate
            tgt_fq = "{0}\\{1}\\{1}".format( section, cal_name )
            # if there is a direct method possible??
            if( not simulate ):
                batch_jobs.append( 'python calConvert.py --csf "{}" "{}"\n'.format( cal_fq, tgt_fq ) )
                batch_jobs.append( 'REM python calConvert.py --dlt "{}" "{}"\n'.format( cal_fq, tgt_fq ) )
            else:
                batch_jobs.append( 'TYPE NUL > "{}.csf"\n'.format( tgt_fq ) )
                batch_jobs.append( 'TYPE NUL > "{}.dlt"\n'.format( tgt_fq ) )
        # convert wand-waves
        section = os.path.join( giant_base_path, "volume" )
        for wand_name in self.shoot.cals:
            take = self.shoot.data[ wand_name ]
            take_name = take.name
            mkdir_p( os.path.join( section, take_name ) )
            tgt_fq = "{0}\\{1}".format( section, wand_name )
            batch_jobs.append( genJobList( take.x2d_fq, tgt_fq, simulate=simulate ) )
            prj_dat = { "RAW_DATA" : "$GIANT_DATA_DIR/volume/{0}/{0}.raw".format( wand_name ) }
            gf.makePRJ( "{0}\\{1}.prj".format( section, wand_name ), prj_dat )
            
        # convert ROMs
        section = os.path.join( giant_base_path, "capture", "talent" )
        g_path = "capture/talent"
        for rom in self.shoot.roms:
            take = self.shoot.data[ rom ]
            take_name = take.name
            mkdir_p( os.path.join( section, take_name ) )
            tgt_fq = "{0}\\{1}".format( section, take_name )
            batch_jobs.append( genJobList( take.x2d_fq, tgt_fq, simulate=simulate ) )
            prj_dat = {
                "RAW_DATA" : "$GIANT_DATA_DIR/{0}/{1}/{1}.raw".format( g_path, take_name ),
                "CALIBRATION" : "$GIANT_DATA_DIR/{0}/{1}/{1}.cal".format( "calib", take.prefered_cal_name ),
                "SEARCH_PARAMS" :"$GIANT_DATA_DIR/probspec/body.sch"
            }
            gf.makePRJ( "{0}\\{1}.prj".format( section, take_name ), prj_dat )
            
   
        # scalings & chains
        # These are scaled:
        # $bio/subject/name/[bdf|ppf]
        # $bio/scaling/name.scl
        # these are default:
        # $bio/probspec/X/[lmt|pdf]
        # Don't recall where the mdl is sourced from.
        # for a chain, a new 'compound' of bdf, ppf, scl, lmt, pdf are needed
        # for now, just stub out the required folders
        # what happened to dof files??
        
        # obviously!!! update to suit company preference / shooting requirements
        PSPEC = "male_2.0"
        
        subject_jumble = self.shoot.subject_mixes | set( (x,) for x in self.shoot.encountered_subjects )
        subs = sorted( list( subject_jumble ), key=lambda x : len( x ) )
        for sub in subs:
            # The retorts below could be emited into ''pipeline'' and become tasks assigned to artists
            # keep in mind the dependancy.  Need *all* scallings before we can chain, but chains could be
            # batched.
            if( len( sub ) > 1 ):
                print( "\tA chain of '{}' is required".format( " and ".join( sub ) ) )
                # giant has a script to do this????
                chain = "-".join( sub )
                stubs = [   [ giant_base_path, "probspec", "characters", "combined", chain ],
                            [ giant_base_path, "subject", chain ],
                            [ giant_base_path, "model", "combined", chain ],
                ]
                for stub in stubs:
                    mkdir_p( os.path.join( *stub ) )
            else:
                print( "\tA scaling for '{}' needs to be generated".format( sub ) )
                chain = "-".join( sub )
                stubs = [   [ giant_base_path, "probspec", "characters", PSPEC ],
                            [ giant_base_path, "subject", chain ],
                            [ giant_base_path, "model", PSPEC ],
                ]
                for stub in stubs:
                    mkdir_p( os.path.join( *stub ) )
                    
        # Finally, the takes!
        section = os.path.join( giant_base_path, "capture" )
        g_path = "capture"
        for take_name in self.shoot.takes:
            take = self.shoot.data[ take_name ]
            take_name = take.name
            mkdir_p( os.path.join( section, take_name ) )
            tgt_fq = "{0}\\{1}".format( section, take_name )
            batch_jobs.append( genJobList( take.x2d_fq, tgt_fq, simulate=simulate ) )
            prj_dat = {
                "RAW_DATA" : "$GIANT_DATA_DIR/{0}/{1}/{1}.raw".format( g_path, take_name ),
                "CALIBRATION" : "$GIANT_DATA_DIR/{0}/{1}/{1}.cal".format( "calib", take.prefered_cal_name ),
                "SEARCH_PARAMS" :"$GIANT_DATA_DIR/probspec/body.sch",
            }
            pdf = "$GIANT_DATA_DIR/probspec/characters/{0}.pdf".format( PSPEC )
            lmt = "$GIANT_DATA_DIR/probspec/characters/{0}/{0}.lmt".format( PSPEC )
            mdl = "$GIANT_DATA_DIR/model/{0}.mdl".format( PSPEC )
            
            scl = "$GIANT_DATA_DIR/scaling/{0}.scl".format( take.chain )
            bdf = "$GIANT_DATA_DIR/subject/{0}/{0}.scl".format( take.chain )
            ppf = "$GIANT_DATA_DIR/subject/{0}/{0}.ppf".format( take.chain )
            
            if( len( take.subject_list ) > 1 ):
                # combined case
                pdf = "$GIANT_DATA_DIR/probspec/characters/combined/{0}/{0}.pdf".format( take.chain )
                lmt = "$GIANT_DATA_DIR/probspec/characters/combined/{0}/{0}.lmt".format( take.chain )
                mdl = "$GIANT_DATA_DIR/model/combined/{0}/{0}.mdl".format( take.chain )
                
            prj_dat[ "PROBLEM_DEF" ] = pdf
            prj_dat[ "LIMITS" ]      = lmt
            prj_dat[ "GFX_MODEL" ]   = mdl
            prj_dat[ "GFX_SCALING" ] = scl
            prj_dat[ "BODY_DEF" ]    = bdf
            prj_dat[ "PATTERN" ]     = ppf

            gf.makePRJ( "{0}/{1}.prj".format( section, take_name ), prj_dat )
        
        # output the batch file
        print( "{} conversion tasks\n".format( len( batch_jobs ) ) )
        name = "convert{}.bat".format( "" if not simulate else "_simulation" )
        outputBatFile( os.path.join( self.shoot.source_dir, name ), batch_jobs )
  
# test
#path = r"C:\ViconData\Teaching\ShootingDays\170323_A1_MosCap01"
path = r"C:\ViconData\Teaching\ShootingDays\180226_A1_GroupA_01"

giant = r"C:\temp\giantstrut\day01"

surveyer = Survey( 25, 4 )
surveyer.searchSession( path )

surveyer.printDigest()

#surveyer.doConversion( giant, simulate=True )
import json
json.dumps( surveyer.shoot.__dict__ )
