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
import pypond
import random


class MelodyAlgorithm(object):
    def __init__(self, configuration):
        # Ultimately a configuration should go here
        self.numNotes = 16
        self.minPitch = 36    # Min pitch. This will eventually come from the configuration file
        self.maxPitch = 96  # Max pitch
        self.maxDurationPwr2 = 0 # Maximum duration (whole note).
        self.minDurationPwr2 = 4 # Sixteenth note
        # rint*(2**(maxDur - minDur))
        self.lengthRange = (2**(-x) for x in (self.minDurationPwr2, self.maxDurationPwr2))
        self.lastNote = None

    def setConfig(self, config):
        noteLowest = config.get('noteLowest', None)
        if noteLowest != None:
            self.minPitch = noteLowest.getMIDIByte()
        noteHighest = config.get('noteHighest', None)
        if noteHighest != None:
            self.maxPitch = noteHighest.getMIDIByte()
        print("self.minPitch = {}; = {}".format(self.minPitch, self.maxPitch))

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
        pitch = random.randint(self.minPitch, self.maxPitch)
        rint = random.randint(1, 2**(self.minDurationPwr2 - self.maxDurationPwr2))
        duration = rint*(2**(self.maxDurationPwr2 - self.minDurationPwr2))
        #duration = 2**(int(random.random()*(self.minDurationPwr2 - self.maxDurationPwr2) + self.maxDurationPwr2))
        note = pypond.Note.fromMIDIByte(pitch, duration = duration)
        #note.setDuration(duration)
        #print("pitch = {}, duration = {}, note = {}".format(pitch, duration, note.getNoteName()))
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

class Key(object):
    def __init__(self, keystring):
        self._setValidators()
        if keystring == None:
            keystring = "CM"
        if not self.parse(keystring):
            print("Invalid keystring {}. Using default CM".format(keystring))
            self.parse("CM")

    def _setValidators(self):
        self._vNoteNames = ('a', 'b', 'c', 'd', 'e', 'f', 'g')
        self._vAccidentals = ('b', '#')
        # These are not used; replaced by Regex strings, but they're handy
        # to leave here for redundant documentation
        self._vMajor = ('M', 'Maj', 'maj', 'MAJ')
        self._vMinor = ('m', 'Min', 'min', 'MIN')
        self._vDWH = ('D', 'd', 'Dwh', 'DWH', 'dwh')
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
            # len(keystring) >= 2
            if keystring[1] in self._vAccidentals:
                sdiv = 2
                #tonicString = keystring[:2]
            else:
                sdiv = 1
            tonicString = keystring[:sdiv]
            if len(keystring) > sdiv:
                qstring = keystring[sdiv:]
        self.tonic = pypond.Note(tonicString)
        self.quality, self.qualityString = self.parseQuality(qstring)
        if (not self.tonic.checkValid()) or (self.quality == None):
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

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "{}/{}".format(self.getBeatsPerMeasure(), self.getMajorBeat())

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
    _reDimWH = re.compile("((D((wh)|(WH))?)|(d(wh)?))$")
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

def TheoryClass(object):
    CircleOfFifths = ('c', 'g', 'd', 'a', 'e', 'b', 'f#', 'db', 'ab', 'eb', 'bb', 'f')
    fourthInterval = 5 # 5 half-steps make a perfect fourth
    fifthInterval  = 7 # 7 half-steps make a perfect fifth

    @classmethod
    def getKeyAtInterval(cls, key, interval):
        """Returns a Key object of the same key quality as 'key', with tonic rooted
        up a perfect-fifth from that of 'key'"""
        interval = pypond._int(interval)
        if interval == None:
            raise pypond.Error_Interval("Cannot interpret interval {}".format(interval))
        note = pypond.Note(key.getTonicName())
        nextNote = note.getNoteByInterval(interval)
        quality = key.getQuality()
        nextKey = Key(nextNote.getNoteName())
        nextKey.setQuality(quality)
        return nextKey

    @classmethod
    def getNextFifth(cls, key):
        """Returns a Key object of the same key quality as 'key', with tonic rooted
        up a perfect-fifth from that of 'key'"""
        return cls.getKeyAtInterval(cls.fifthInterval)

    @classmethod
    def getNextFourth(cls, key):
        """Returns a Key object of the same key quality as 'key', with tonic rooted
        up a perfect-fourth from that of 'key'"""
        return cls.getKeyAtInterval(cls.fourthInterval)


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
        'noteLowest'        : (pypond.Note, "A2"),
        'noteHighest'       : (pypond.Note, "C6"),
        'Key'               : (Key, "CM"),
        'Diatonicity'       : (float, 0),
        'timeSignature'     : (_TimeSignature, "4/4"),
        'algorithm'         : (_AlgorithmParser, "MARandom"),
        'numMeasures'       : (int, 8)
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
            self._configStrings[item[0]] = val      # Add the string name to self._configStrings
        return (userCount, defaultCount)

    def useDefaults(self):
        """Force the use of default values for self.config by passing an empty user config"""
        self.filename = "--DEFAULTS--"
        return self._populateConfig({})

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
    print("Time Signature : {}".format(timeSig))

def _testConfiguration(args):
    USAGE = "python3 {} <configFileName.ini>".format(argv[0])
    if len(argv) > 1:
        filename = argv[1]
        cfg = Configuration(filename)
    else:
        print(USAGE)
    print("Configuration : {}".format(cfg))

if __name__ == "__main__":
    import sys
    argv = sys.argv
    #_testTimeSignature(argv)
    #_testConfiguration(argv)
