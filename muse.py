#!/usr/bin/python3

"""
An algorithmic pseudo-random melody generator using pypond.py

class Key(keystring)
    keystring = "[T][Q]"
    where T is a valid note name (Ab through G#)
    and Q is a valid scale quality.

    Valid scale qualities:
        Major = enum('M', 'Maj', 'maj', 'MAJ')
        Minor = enum('m', 'Min', 'min', 'MIN')
        Diminished Whole-Half = enum('D', 'd', 'Dwh', 'DWH', 'dwh')
        Diminished Half-Whole = enum('Dhw', 'DHW', 'dhw')
        Chromatic = enum('*', 'C', 'c')
        Whole Tone = enum('W', 'w')
"""

# CHECK! TODO! Do we want to represent scale qualities as enum constants or classes rather than strings?
# CHECK! TODO! Finish _ENCODING_NOTES
# TODO! Finish class Key
#   How do we say what notes are in a given key without simple brute-forcing?
# CHECK! TODO! Learn regex and implement in parsing
# TODO! Finish class MelodyAlgorithm

import configparser
import re
import pypond, theory
import random

DEBUG = True

class MelodyAlgorithm(object):
    def __init__(self, configuration = None):
        # Ultimately a configuration should go here
        self.numNotes = 16
        self.minPitch = 36    # Min pitch. This will eventually come from the configuration file
        self.maxPitch = 96  # Max pitch
        self.keyNoteMin = None
        self.keyNoteMax = None
        self.maxDurationPwr2 = 0 # Maximum duration (whole note).
        self.minDurationPwr2 = 4 # Sixteenth note
        # rint*(2**(maxDur - minDur))
        self.lengthRange = (2**(-x) for x in (self.minDurationPwr2, self.maxDurationPwr2))
        self.lastNote = None
        if configuration != None:
            self.setConfig(configuration)

    def setConfig(self, config):
        noteLowest = config.get('noteLowest', None)
        if noteLowest != None:
            self.minPitch = noteLowest.getMIDIByte()
        noteHighest = config.get('noteHighest', None)
        if noteHighest != None:
            self.maxPitch = noteHighest.getMIDIByte()
        _dbg("self.minPitch = {}; = {}".format(self.minPitch, self.maxPitch))
        self.density = config.get('density', None)
        if self.density == None:
            self.density = 1.0
        print("self.density = {}".format(self.density))
        self.key = config.get('key')
        self.keyNoteMin = config.get('keyNoteMin')
        self.keyNoteMax = config.get('keyNoteMax')
        self.numRange = self.key.getNumNotesInRange(self.keyNoteMin, self.keyNoteMax)

    def getNoteInKey(self, n):
        """Get a note within the key by a float from 0 to 1, which will be
        quantized to key notes within self.keyNoteMin and self.keyNoteMax"""
        nint = int(n*self.numRange)
        minScaleDegree = self.key.getScaleDegree(self.keyNoteMin)
        #maxScaleDegree = self.key.getScaleDegree(self.keyNoteMax)
        minOctave = self.keyNoteMin.getOctave()
        notesInKey = len(self.key.getNotes())
        octaves = nint // notesInKey
        rem = nint % notesInKey
        note = self.key.getNoteByScaleDegree((rem + minScaleDegree) % notesInKey)
        note.setOctave(minOctave + octaves)
        return note

    def plantSeed(self, seed):
        """Seed any pseudo-random number generation."""
        pass

    def getNextNote(self):
        pass

    def setNextNote(self):
        pass

    def getNextNoteLily(self):
        """Returns the next note the algorithm generates as GNU lilypad text"""
        note = self.getNextNote()
        return note.asLily()

class MARandom(MelodyAlgorithm):
    def __init__(self):
        super().__init__(None)

    def getNextNote(self):
        #pitch = int(random.random()*(self.maxPitch - self.minPitch) + self.minPitch)
        isRest = False
        if random.random() > self.density:
            isRest = True
        rint = random.randint(1, 2**(self.minDurationPwr2 - self.maxDurationPwr2))
        duration = rint*(2**(self.maxDurationPwr2 - self.minDurationPwr2))
        #print("pitch = {}, duration = {}, note = {}".format(pitch, duration, note.getNoteName()))
        if isRest:
            rest = pypond.Rest(duration)
            return rest
        else:
            #pitch = random.randint(self.minPitch, self.maxPitch)
            #note = pypond.Note.fromMIDIByte(pitch, duration = duration)
            note = self.getNoteInKey(random.random())
            note.setDuration(duration)
            return note

class MAGaussMeander(MelodyAlgorithm):
    def __init__(self):
        super().__init__(None)

    def getNextNote(self):
        mu = 0
        sigma = 0.1
        if self.lastNote == None:
            lastpitch = (self.maxPitch + self.minPitch)//2
        else:
            lastpitch = self.lastNote.getMIDIByte()
        pitch = lastpitch + int(self.boundedGauss(mu, sigma)*(self.maxPitch - self.minPitch))
        #print("lastpitch = {}; pitch = {}".format(lastpitch, pitch))
        rint = random.randint(0, 2**(self.minDurationPwr2 - self.maxDurationPwr2))
        duration = rint*(2**(self.maxDurationPwr2 - self.minDurationPwr2))
        note = pypond.Note.fromMIDIByte(pitch, duration = duration)
        #note.setDuration(duration)
        self.lastNote = note
        return note

    def boundedGauss(self, mu, sigma):
        n = random.gauss(mu, sigma)
        if n < -1:
            n = -1
        elif n > 1:
            n = 1
        #print("gauss = {}".format(n))
        return n

def _getIntervalsModal(intervals, scaleDegree):
    l = len(intervals)
    # [(f[(6 - 1 + n) % l] + 12 - f[6 - 1]) % 12 for n in range(l)]
    return ((intervals[(scaleDegree - 1 + n) % l] + 12 - intervals[scaleDegree - 1]) % 12
            for n in range(l))

class _KeyQuality(object):
    major = 0
    minor = 1
    dimwh = 2
    dimhw = 3
    chromatic = 4
    wholetone = 5

    qualities = (major, minor, dimwh, dimhw, chromatic, wholetone)

    _decodeDict = {
        major : "maj",
        minor : "min",
        dimwh : "dwh",
        dimhw : "dhw",
        chromatic : "*",
        wholetone : "w"
    }

    # Regex match-strings for parsing input
    _reMajor = re.compile("((M((AJ)|(aj))?)|maj)$")
    _reMinor = re.compile("((m(in)?)|(M((IN)|(in))))$")
    _reDimWH = re.compile("((D((wh)|(WH)|(im)|(IM))?)|(d((wh)|(im)?)))$")
    _reDimHW = re.compile("((D((HW)|(hw)))|dhw)$")
    _reChromatic = re.compile("[*cC]$")
    _reWholeTone = re.compile("[Ww]$")

    @classmethod
    def parse(cls, qstring):
        """Parse a string describing a key quality and return a _KeyQuality class attribute
        or None if no match is found."""
        if cls._reMajor.match(qstring):
            r = cls.major
        elif cls._reMinor.match(qstring):
            r = cls.minor
        elif cls._reDimWH.match(qstring):
            r = cls.dimwh
        elif cls._reDimHW.match(qstring):
            r = cls.dimhw
        elif cls._reChromatic.match(qstring):
            r = cls.chromatic
        elif cls._reWholeTone.match(qstring):
            r = cls.wholetone
        else:
            r = None
        return (r, cls._decodeDict.get(r, None))

    @classmethod
    def decode(cls, keyquality):
        errstring = "Cannot decode {}".format(keyquality)
        dec = cls._decodeDict.get(keyquality, None)
        if dec == None:
            print(errstring)
        return dec


class Key(object):
    _intervalsMajor = (0, 2, 4, 5, 7, 9, 11) # wwhwwwh
    _intervalsMinor = _getIntervalsModal(_intervalsMajor, 6)    # Aeolian
    _intervalsDWH   = (0, 2, 3, 5, 6, 8, 9, 11)
    _intervalsDHW   = (0, 1, 3, 4, 6, 7, 9, 10)
    _intervalsChromatic = range(12)
    _intervalsWholeTone = (0, 2, 4, 6, 8, 10)
    _intervals = {
        _KeyQuality.major : _intervalsMajor,
        _KeyQuality.minor : _intervalsMinor,
        _KeyQuality.dimwh : _intervalsDWH,
        _KeyQuality.dimhw : _intervalsDHW,
        _KeyQuality.chromatic : _intervalsChromatic,
        _KeyQuality.wholetone : _intervalsWholeTone
    }
    _alterationsMajor = (0, 0, 0, 0, 0, 0, 0)
    _alterationsMinor = (0, 0, -1, 0, 0, -1, -1)    # Aeolian minor
    _alterationsDWH   = (0, 0, -1, 0, -1, (-1, 0), 0)
    _alterationsDHW   = (0, -1, -1, -1, (-1, 0), 0, -1)
    _alterations = {
        _KeyQuality.major : _alterationsMajor,
        _KeyQuality.minor : _alterationsMinor,
        _KeyQuality.dimwh : _alterationsDWH,
        _KeyQuality.dimhw : _alterationsDHW
    }
    def __init__(self, keystring):
        self._setValidators()
        if keystring == None:
            keystring = "CM"
        if not self.parse(keystring):
            print("Invalid keystring {}. Using default CM".format(keystring))
            self.parse("CM")

    def getKeyString(self):
        tonicString = self.tonic.getNoteName()
        qualityString = self.getQualityString()
        return tonicString + qualityString

    def getKeyLily(self):
        """Return the tonic and \\major \\minor according to GNU Lilypond syntax"""
        keystring = self.tonic.asLilyNoteName()
        if self.quality in (_KeyQuality.minor, _KeyQuality.dimwh, _KeyQuality.dimhw):
            qualityString = pypond.LilySyntax.kwKeyMinor
        else:
            qualityString = pypond.LilySyntax.kwKeyMajor
        return "{} {}".format(keystring, qualityString)

    def _setValidators(self):
        self._vNoteNames = ('a', 'b', 'c', 'd', 'e', 'f', 'g')
        self._vAccidentals = ('b', '#')
        # These are not used; replaced by Regex strings, but they're handy
        # to leave here for redundant documentation
        self._vMajor = ('M', 'Maj', 'maj', 'MAJ')
        self._vMinor = ('m', 'Min', 'min', 'MIN')
        self._vDWH = ('D', 'd', 'Dim', 'dim', 'Dwh', 'DWH', 'dwh')
        self._vDHW = ('Dhw', 'DHW', 'dhw')
        self._vChromatic = ('*', 'C', 'c')
        self._vWholeTone = ('W', 'w')

    def parse(self, keystring):
        tonicString = 'c'
        self.quality = _KeyQuality.major
        qstring = "M"
        if len(keystring) < 1:
            return False
        elif len(keystring) == 1:
            tonicString = keystring
        else:
            n = 1
            while n < len(keystring):
                t, f = pypond.Note._isAccidentalChar(keystring[n])
                #print("{} is accidental char? {}".format(keystring[n], t))
                if not t:
                    break
                n += 1
            tonicString = keystring[:n]
            if len(keystring) > n:
                qstring = keystring[n:]
        #print("n = {}; tonicString = {}; qstring = {}".format(n, tonicString, qstring))
        self.tonic = pypond.Note(tonicString)
        self.quality, self.qualityString = self.parseQuality(qstring)
        self.intervals = self._intervals.get(self.quality, None)
        if (not self.tonic.checkValid()) or (self.quality == None) or (self.intervals == None):
            return False
        return True

    def getTonic(self):
        return self.tonic

    def getTonicName(self):
        return self.tonic.getNoteName()

    def getQuality(self):
        return self.quality

    def setQuality(self, quality):
        if quality not in _KeyQuality.qualities:
            return False
        else:
            self.quality = quality
            return True

    def getQualityString(self):
        return self.qualityString

    def __repr__(self):
        return "{}{}".format(self.tonic.getNoteName(), self.qualityString)

    def parseQuality(self, qstring):
        return _KeyQuality.parse(qstring)

    def asByte(self):
        """Return the key encoded as a byte using the custom encoding:
        LS half-word = quality
        MS half-word = note"""
        ls = self.quality
        ms = self.tonic.getEncoding()
        return (ms << 4) + ls

    def getNotes(self, octave = None):
        """Return a list of notes in the key in octave 'octave' (or default octave)."""
        #intervals = self.getIntervals()
        alterations = self._alterations.get(self.quality, None)
        if alterations == None:
            intervals = self.getIntervals()
        else:
            intervals = self._intervalsMajor    # First generate a major scale, we'll alter it later
        tonic = self.getTonic()
        acc = tonic.getAccidental()
        key = None                              # Need this in case acc != 0
        if acc != 0:
            tonic = pypond.Note(tonic.getNoteLetter())  # If the key has an accidental, first get the
            tonicString = tonic.getNoteName()           # non-accidental scale
            qualityString = self.getQualityString()
            #print("New key: tonicString + qualityString = {}".format(tonicString + qualityString))
            key = self.new(tonicString + qualityString)
        notes = []
        sharp = self.isSharpKey(key)
        for ival in intervals:
            notes.append(tonic.getNoteByInterval(ival, sharp = sharp))
        if acc != 0:                            # If there's an accidental
            for n in range(len(notes)):         # Apply that accidental to all notes in the scale
                notes[n] = notes[n].alter(acc)
        if alterations == None or self.quality == _KeyQuality.major:
            return notes                        # If no alterations are required, we're done!
                                    # Otherwise,
        for n in range(len(notes)): # Perform any alterations as needed
            alt = alterations[n]
            if isinstance(alt, int):
                if alt != 0:
                    notes[n] = notes[n].alter(alt)
            elif len(alt) > 1:
                originalNote = notes[n]             # need to keep a reference to the unaltered note
                notes[n] = originalNote.alter(alt[0])   # Alter the first note
                for m in range(len(alt[1:])):
                    notes.insert(n+m+1, originalNote.alter(alt[m+1])) # Jam any remaining alterations in there
        return notes

    def getNumNotesInRange(self, noteMin, noteMax):
        """Get the number of notes in the key within the range noteMin to noteMax (inclusive)."""
        minoctave = noteMin.getOctave()
        maxoctave = noteMax.getOctave()
        scaleDegreeMin = self.getScaleDegree(noteMin)
        scaleDegreeMax = self.getScaleDegree(noteMin)
        return 7 * (maxoctave - minoctave) + (7 - scaleDegreeMin) + (scaleDegreeMax)

    def getScaleDegree(self, note):
        """Get the scale degree of note 'note' or None if 'note' not in key
        (zero-indexed).  I.e. if key is AbMaj, key.getScaleDegree(Note(C)) = 2"""
        t, high, low = self.isInKey(note)
        if not t:
            return None
        index = 0
        for keynote in self.getNotes():
            if keynote.isEqualNote(note):
                break
            index += 1
        return index

    def getNoteByScaleDegree(self, degree):
        notes = self.getNotes()
        if degree < len(notes):
            return notes[degree]
        else:
            return None

    def isSharpKey(self, key = None):
        if key == None:
            key = self
        return theory.TheoryClass.isSharpKey(key)

    def isInKey(self, note):
        """If 'note' is within the key, returns (True, nextHigher, nextLower).
        Otherwise, returns (False, nextHigher, nextLower)
        where 'nextHigher' is the next higher note in the key and 'nextLower' is
        the next lower note in the key."""
        intervalPositive = 12
        intervalNegative = -12
        nextHigher = None
        nextLower = None
        match = False
        for keynote in self.getNotes():
            interval = keynote.getInterval(note)    # interval > 0 if note > keynote
            #print("{} - {} = {}".format(note, keynote, interval))
            if interval > 0 and interval < intervalPositive:
                intervalPositive = interval
                nextLower = keynote
            elif interval < 0 and interval > intervalNegative:
                intervalNegative = interval
                nextHigher = keynote
            if keynote.isEqualNote(note):
                match = True
        octave = note.getOctave()
        print("octave = {}".format(octave))
        nextHigher.setOctave(octave)
        if nextHigher.getMIDIByte() < note.getMIDIByte():
            nextHigher.setOctave(octave + 1)
        nextLower.setOctave(octave)
        if nextLower.getMIDIByte() > note.getMIDIByte():
            nextLower.setOctave(octave - 1)
        return (match, nextHigher, nextLower)

    def getIntervals(self):
        return self.intervals

    def copy(self):
        return self.new(self.getKeyString())

    @classmethod
    def new(cls, keystring):
        return cls(keystring)

    def getNotesModal(self, scaleDegree):
        intvals = _getIntervalsModal(self.getIntervals(), scaleDegree)
        pass

class _TimeSignature(object):
    def __init__(self, *args, **kwargs):
        """Multiple constructors. E.g. 6/8 time:
        self.__init__('6/8')
        self.__init__(6, 8)
        """ 
        success = False
        if len(args) == 1:
            if isinstance(args[0], str):
                success = self.newFromString(args[0])
        elif len(args) == 2:
            success = self.newFromArgs(*args)
        if not success:
            if len(kwargs) == 0:
                print("Failed to interpret TimeSignature args: {}\nDefaulting to 4/4".format(args))
                return self.newFromArgs(4, 4)
            if 'beatsPerMeasure' in kwargs.keys():
                beatsPerMeasure = kwargs['beatsPerMeasure']
            else:
                beatsPerMeasure = 4
            if 'majorBeat' in kwargs.keys():
                majorBeat = kwargs['majorBeat']
            else:
                majorBeat = 4
            return self.newFromArgs(beatsPerMeasure, majorBeat)

    def newFromArgs(self, beatsPerMeasure, majorBeat):
        try:
            self.beatsPerMeasure = int(beatsPerMeasure)
            self.majorBeat = int(majorBeat)
        except ValueError:
            raise Error_IntegerParse("Cannot parse one of {} or {} as int".format(
                                     beatsPerMeasure, majorBeat))
            return False
        return True

    def newFromString(self, s):
        if '/' in s:
            delim = '/'
        elif '\\' in s:
            delim = '\\'
        beatsPerMeasure, majorBeat = s.split(delim)
        return self.newFromArgs(beatsPerMeasure, majorBeat)

    def getBeatsPerMeasure(self):
        return self.beatsPerMeasure

    def getMajorBeat(self):
        return self.majorBeat

    def getMeasureDuration(self):
        return self.beatsPerMeasure/self.majorBeat

    def asLily(self):
        """Return the time signature string in GNU Lilypond syntax"""
        # Currently the same as __str__(), but may change in the future
        return "{}/{}".format(self.getBeatsPerMeasure(), self.getMajorBeat())

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "{}/{}".format(self.getBeatsPerMeasure(), self.getMajorBeat())




def _AlgorithmParser(algorithm):
    """Parse the string 'algorithm' and match it to a Python class which
    inherits from MelodyAlgorithm; returning an instance of the class or
    None if no match is found."""
    # TODO. Consider using importlib.import_module('userlib') for a dynamic import of a user library
    # in 'userlib.py' and using getattr(importlib.import_module('userlib'), 'someClass') to try to
    # get the class from the user library without importing the whole library
    # For now, we'll just use the globals() dict
    #print("_AlgorithmParser looking for {}".format(algorithm))
    for item in globals().items():
        #print(item[0])
        if algorithm.lower() == item[0].lower():    # If 'algorithm' matches any item in globals (non case sensitive)
            #print("name match: {} = {}".format(algorithm, item[0]))
            cls = item[1]       # Then let's see if it's a subclass of MelodyAlgorithm
            if issubclass(cls, MelodyAlgorithm):    # If it is,
                #print("Is subclass!")
                return cls()                        # Return an instance of the class
            #else:
            #    print("... is not subclass")
    return None                                     # if no match is found, return None

class Configuration(object):
    _FilenameForceDefaults = '*'
    _ConfigCalls = {
        #Name               : (callable, defaultValue)
        'clef'              : (theory.TheoryClass._clefParser, "treble"),
        'noteLowest'        : (pypond.Note, "A2"),
        'noteHighest'       : (pypond.Note, "C6"),
        'key'               : (Key, "CM"),
        'diatonicity'       : (float, 0),
        'timeSignature'     : (_TimeSignature, "4/4"),
        'algorithm'         : (_AlgorithmParser, "MARandom"),
        'numMeasures'       : (int, 8),
        'density'           : (float, 1.0),
    }
    def __init__(self, filename = None):
        self.filename = filename
        if filename != None:
            if filename == self._FilenameForceDefaults:
                items = self.useDefaults()
            else:
                items = self.readIni()
            print("{} read {} items; used defaults for {} items".format(
                  self.__str__(), items[0], items[1]))
        else:
            print("{} uninitialized.  Call self.readIni(filename) or \
                  self.useDefaults() before using.")

    def readIni(self, filename = None):
        if filename == None:
            filename = self.filename
        config = configparser.ConfigParser()
        t = config.read(filename)
        if len(t) == 0:
            raise Error_FileNotFound("Cannot open file {}".format(filename))
            return False
        return self._populateConfig(config)

    def _populateConfig(self, config):
        """Add items from INI config dict to self.config using the callables in
        _ConfigCalls, using the default in _ConfigCalls if the key is not included
        in user config.
        Returns (userCount, defaultCount) where userCount is the number of items
        loaded to self.config from the user config, and defaultCount is the number
        of items loaded to self.config from their default values."""
        self.config = {}
        self._configStrings = {}
        userCount = 0
        defaultCount = 0
        if len(config) > 0:
            config = config["DEFAULT"]
        for item in self._ConfigCalls.items():
            val = config.get(item[0], None)     # Check for a value in the user config
            if val == None:
                val = item[1][1]                # If not provided in the user config, use default
                defaultCount += 1
            else:
                userCount += 1
            self.config[item[0]] = item[1][0](val)  # Add to self.config using the corresponding callable
            print("config({}) = {}".format(item[0], val))
            self._configStrings[item[0]] = val      # Add the string name to self._configStrings
        # = =  Add derived quantities = = 
        noteMin = self.config.get('noteLowest')
        noteMax = self.config.get('noteHighest')
        print("noteMin = {}; noteMax = {}".format(noteMin, noteMax))
        keyNoteMin, keyNoteMax = self.getKeyNoteRange(noteMin, noteMax)
        self.config['keyNoteMin'] = keyNoteMin
        self.config['keyNoteMax'] = keyNoteMax
        return (userCount, defaultCount)

    def useDefaults(self):
        """Force the use of default values for self.config by passing an empty user config"""
        self.filename = "--DEFAULTS--"
        return self._populateConfig({})

    def getKeyNoteRange(self, noteMin, noteMax):
        key = self.config.get('key')
        print("key = {}".format(key))
        mint, minlow, minhigh = key.isInKey(noteMin)
        maxt, maxlow, maxhigh = key.isInKey(noteMax)
        print("noteMin = {}; in key? {}".format(noteMin, mint))
        print("noteMax = {}; in key? {}".format(noteMax, maxt))
        if not mint:
            noteMin = minhigh
        if not maxt:
            noteMax = maxlow
        return (noteMin, noteMax)

    def __str__(self):
        return "Configuration({})".format(self.filename)

    def __repr__(self):
        return self.__str__()

    def getMeasureDuration(self):
        return self.config['timeSignature'].getMeasureDuration()

    def get(self, key, defaultVal = None):
        if self.config == None:
            raise Error_InvalidConfig("Configuration.config = None!")
            return defaultVal
        return self.config.get(key, defaultVal)

    def gets(self, key, defaultVal = None):
        """Same as self.get() but searches self._configStrings rather than self.config"""
        if self._configStrings == None:
            raise Error_InvalidConfig("Configuration._configStrings = None!")
            return defaultVal
        return self._configStrings.get(key, defaultVal)
        
class Error_InvalidConfig(Exception):
    pass

class Error_FileNotFound(Exception):
    pass

def _dbg(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def _testTimeSignature(args):
    USAGE = "python3 {} <key>".format(argv[0])
    if len(argv) > 2:
        beats = int(argv[1])
        major = int(argv[2])
        timeSig = _TimeSignature(beats, major)
    elif len(argv) > 1:
        s = argv[1]
        timeSig = _TimeSignature(s)
    else:
        print(USAGE)
        return
    print("Time Signature : {}".format(timeSig))

def _testConfiguration(args):
    USAGE = "python3 {} <configFileName.ini>".format(args[0])
    if len(argv) > 1:
        filename = args[1]
        cfg = Configuration(filename)
    else:
        print(USAGE)
        return
    print("Configuration : {}".format(cfg))

def _testKey(args):
    USAGE = "python3 {} <keyString>".format(args[0])
    if len(argv) > 1:
        keyString = args[1]
        key = Key(keyString)
    else:
        print(USAGE)
        return
    print("Key : {}\t{}".format(key, [n.getNoteName() for n in key.getNotes()]))

def _testIsInKey(args):
    USAGE = "python3 {} <keyString> [note]".format(args[0])
    if len(argv) > 2:
        keyString = args[1]
        key = Key(keyString)
        note = pypond.Note(args[2])
    elif len(argv) == 2:
        return _testKey(args)
    else:
        print(USAGE)
        return
    t, high, low = key.isInKey(note)
    scaleDegree = key.getScaleDegree(note)
    print("note {} is in Key {}? {}\nNext Higher = {}\nNext Lower = {}\nscale degree = {}".format(
          note, key, t, high, low, scaleDegree))
    print("highByte = {}; noteByte = {}; lowByte = {}".format(high.getMIDIByte(), note.getMIDIByte(),
          low.getMIDIByte()))

def _testGetNumNotesInRange(args):
    USAGE = "python3 {} <keyString> [noteLow] [noteHigh]".format(args[0])
    if len(argv) > 3:
        keyString = args[1]
        key = Key(keyString)
        note1 = pypond.Note(args[2])
        note2 = pypond.Note(args[3])
    else:
        print(USAGE)
        return
    numNotes = key.getNumNotesInRange(note1, note2)
    print("notes in range ({}, {}) = {}".format(note1, note2, numNotes))

if __name__ == "__main__":
    import sys
    argv = sys.argv
    #_testTimeSignature(argv)
    #_testConfiguration(argv)
    #_testKey(argv)
    _testIsInKey(argv)
    #_testGetNumNotesInRange(argv)

