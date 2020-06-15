#!/usr/bin/python3

"""
An algorithmic pseudo-random melody generator using pypond.py
"""

import configparser
import re
import pypond, theory
import random
import circular

import math

DEBUG = True
LOGFILE = None
FILENAME = "muse.py"

# This is a wacky forward declaration temporary fix 
def _float(s):
    if isinstance(s, float):
        return s
    try:
        r = float(s)
        return r
    except ValueError:
        pass
    if '/' in s:
        r = _eval(s)
        return r
    return r

class MelodyAlgorithm(object):
    def __init__(self, configuration = None):
        # Most/all of these get overwritten by a valid configuration.
        # These provide defaults in case the configuration doesn't
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
        #print("self.density = {}".format(self.density))
        self.key = config.get('key')
        self.keyNoteMin = config.get('keyNoteMin')
        self.keyNoteMax = config.get('keyNoteMax')
        self.numRange = self.key.getNumNotesInRange(self.keyNoteMin, self.keyNoteMax)
        print("keyNoteMin = {}; keyNoteMax = {}; self.numRange = {}".format(
            self.keyNoteMin, self.keyNoteMax, self.numRange))
        self.notesInRange = self.key.getNumNotesInRange(self.keyNoteMin, self.keyNoteMax)
        self.shortestNote = config.get('shortestNote')
        self.longestNote = config.get('longestNote')
        self.minDurationPwr2 = config._invLog2(self.shortestNote)
        self.maxDurationPwr2 = config._invLog2(self.longestNote)
        self.diatonicity = config.get('diatonicity')
        self.config = config

    def reloadConfig(self):
        self.setConfig(self.config)

    def changeKey(self, newKey):
        self.config.changeKey(newKey)
        self.reloadConfig()

    def getNoteInKey(self, n):
        """Get a note within the key by a float from 0 to 1, which will be
        quantized to key notes within self.keyNoteMin and self.keyNoteMax"""
        index = int(n*self.notesInRange)
        return self.key.getNoteInRange(self.keyNoteMin, self.keyNoteMax, index)
        """
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
        """

    def changeParameters(self, changeDict):
        """Change parameters based on those of the changeDict object."""
        for key, value in changeDict.items():
            if hasattr(self, key):
                setattr(self, key, value)

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

class MAFixed(MelodyAlgorithm):
    #pattern = [1, 1/8, 1/2, 1/8 + 1/4, 1/16 + 1/2, 1/8, 1/16 + 1/8, 1/2, 1/4, 1, 1/2 + 1/4 + 1/16] 
    pattern = [1, 1, 1]
    def __init__(self):
        super().__init__(None)
        self.index = 0

    def getNextNote(self):
        dur = self.pattern[self.index]
        if self.index >= len(self.pattern) - 1:
            self.index = 0
        else:
            self.index += 1
        return pypond.Note('C4', dur)


class MARandom(MelodyAlgorithm):
    def __init__(self):
        super().__init__(None)

    def getNextNote(self):
        isRest = False
        # Decide if rest or note
        if random.random() > self.density:
            isRest = True
        # Decide if we change key
        r = 2*random.random() - 1 # A random number between -1 and +1
        if abs(r) >= self.diatonicity:
            # Change key
            r = 2*random.random() - 1 # Another random number
            nFourths = int(12*r)
            newKey = self.key.getNewByFourths(nFourths)
            #print("Changing keys: {} -> {}".format(self.key, newKey))
            self.changeKey(newKey)
        # Get the next duration
        rint = random.randint(1, 2**(self.minDurationPwr2 - self.maxDurationPwr2))
        duration = rint*(2**(self.maxDurationPwr2 - self.minDurationPwr2))
        if isRest:
            rest = pypond.Rest(duration)
            return rest
        else:
            # Get a random pitch
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
    _intervalsMajor = circular.Circular((0, 2, 4, 5, 7, 9, 11)) # wwhwwwh
    _intervalsMinor = circular.Circular((0, 2, 3, 5, 6, 8, 10)) # Aeolian
    _intervalsDWH   = circular.Circular((0, 2, 3, 5, 6, 8, 9, 11))
    _intervalsDHW   = circular.Circular((0, 1, 3, 4, 6, 7, 9, 10))
    _intervalsChromatic = circular.Circular([x for x in range(12)])
    _intervalsWholeTone = circular.Circular((0, 2, 4, 6, 8, 10))
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
                    notes.insert(n+m+1, originalNote.alter(alt[m+1])) # Jam any remaining alterations in
        return notes

    def getNumNotesInRange(self, note0, note1):
        """Get the number of notes in the key within the range noteMin to noteMax (inclusive)."""
        # First determine which note is higher than the other
        enc0 = note0.toInteger()
        enc1 = note1.toInteger()
        if enc1 > enc0:
            noteMin = note0
            noteMax = note1
        else:
            noteMin = note1
            noteMax = note0
        # Then verify that the notes are both within the key
        inkey, higher, lower = self.isInKey(noteMin)
        if not inkey:
            #print("{} not in key, using {} instead".format(noteMin, higher))
            noteMin = higher
        inkey, higher, lower = self.isInKey(noteMax)
        if not inkey:
            #print("{} not in key, using {} instead".format(noteMax, lower))
            noteMax = lower
        minoctave = noteMin.getOctave()
        maxoctave = noteMax.getOctave()
        scaleDegreeMin = self.getScaleDegree(noteMin)
        scaleDegreeMax = self.getScaleDegree(noteMax)
        #print('scaleDegreeMin = {}; scaleDegreeMax = {}'.format(scaleDegreeMin, scaleDegreeMax))
        #docts = maxoctave - minoctave
        #print('docts = {}'.format(docts))
        # Remember that octaves breaks are between B and C (B4->C5)
        # If octindexmax < octindexmin, subtract one octave difference
        octIndexMax = noteMax.getOctaveIndex()
        octIndexMin = noteMin.getOctaveIndex()
        #print('octIndexMin = {}; octIndexMax = {}'.format(octIndexMin, octIndexMax))
        #if octIndexMax < octIndexMin:
        #    docts -= 1
        #print('docts = {}'.format(docts))
        octIndexTonic = self.getTonic().getOctaveIndex()
        # Adjust the octave numbers to account for octave break vs. octave index break
        if octIndexMax < octIndexTonic:
            maxoctave -= 1
        if octIndexMin < octIndexTonic:
            minoctave -= 1
        maxnum = 7*maxoctave + scaleDegreeMax
        minnum = 7*minoctave + scaleDegreeMin
        return maxnum - minnum + 1
        #return 7 * docts - scaleDegreeMin + scaleDegreeMax + 1

    def getNoteInRange(self, noteMin, noteMax, index):
        """Get a note within the key between 'noteMin' and 'noteMax' by index
        'index' which can range from 0 to self.getNumNotesInRange(noteMin, noteMax)."""
        if index <= 0:
            return noteMin
        nmax = self.getNumNotesInRange(noteMin, noteMax)
        if index > nmax - 1:
            return noteMax
        iv = self.getIntervals()
        minsd = self.getScaleDegree(noteMin)
        stepsTotal = 0
        prior = iv[minsd]           # The half-steps from tonic of noteMin
        delta = 0
        for n in range(index + 1):
            this = iv[minsd + n]        # The half-steps from tonic of the next note
            if this >= prior:
                delta = this - prior  # Add the difference in half-steps
            else:
                delta = (12 + this) - prior
            #print("Step {}. Adding {}".format(n, delta))
            stepsTotal += delta
            prior = this
        #print("stepsTotal = {}".format(stepsTotal))
        issharp = self.isSharpKey()
        newnote = noteMin.getNoteByInterval(stepsTotal, sharp = issharp)
        return newnote

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
        #print("octave = {}".format(octave))
        nextHigher.setOctave(octave)
        if nextHigher.getMIDIByte() < note.getMIDIByte():
            nextHigher.setOctave(octave + 1)
        nextLower.setOctave(octave)
        if nextLower.getMIDIByte() > note.getMIDIByte():
            nextLower.setOctave(octave - 1)
        return (match, nextHigher, nextLower)

    def getEnharmonicInKey(self, note):
        """Get the enharmonic equivalent of 'note' within key 'self'"""
        inkey, high, low = self.isInKey(note)
        dur = note.getDuration()
        octave = note.getOctave()
        beatnum = note.getBeatNum()
        newnote = None
        if inkey:
            for keynote in self.getNotes():
                if keynote.isEqualNote(note):
                    newnote = keynote
                    break
        else:
            sharp = self.isSharpKey()
            newnote = note.simplify(sharp = sharp)
        if newnote == None:
            return note
        newnote.setOctave(octave)
        newnote.copyRhythmParams(note)
        return newnote
 
    def getBestEnharmonic(self, note):
        """Choose the best enharmonic representation of 'note' given the key (self)
        and return it."""
        # Produce a list of enharmonic notes +/- two half-steps in either direction,
        # e.g. if note == C#, enharmonic list would be:
        # [B##, C#, Db, Ebbb]
        if note.isRest():
            return note
        enlist = []
        inkey, high, low =  self.isInKey(note)
        if inkey:
            newnote = self.getEnharmonicInKey(note)
            #print("Returning (1): {}".format(newnote))
            return newnote
        for n in (-2, -1, 0, 1, 2):
            newnote = note.getEnharmonicEquivalent(n)
            enlist.append(newnote)
        #print("enlist = {}".format(enlist))
        accs = []
        for note in enlist:
            accs.append(note.getAccidental())
        accsabs = [abs(x) for x in accs]
        minacc = min(accsabs)
        count = accsabs.count(minacc)
        if count == 1:
            index = accsabs.index(minacc)
        elif count == 2:
            # We probably have one sharp and one flat (e.g. C# and Db), choose
            # based on the key.
            if self.isSharpKey():
                index = accs.index(minacc)
            else:
                index = accs.index(-minacc)
        #print("Returning (2): {}".format(enlist[index]))
        return enlist[index]
        # If any note is in the key, return it.
        # If the original note has >1 sharp or >1 flat, return the enharmonic with
        # fewer (e.g. C## -> D, Cbb -> Bb (not A#), Abbb -> Gb)

    def getIntervals(self):
        return self.intervals

    def copy(self):
        return self.new(self.getKeyString())

    @classmethod
    def new(cls, keystring):
        return cls(keystring)

    def getNotesModal(self, scaleDegree):
        #intvals = _getIntervalsModal(self.getIntervals(), scaleDegree)
        notes = self.getNotes()
        return _rotate(notes, scaleDegree)

    def getNewByInterval(self, interval):
        """Return a new Key object representing the key 'interval' half
        steps away from the current Key.  'interval' is any valid signed
        integer.
        If 'interval' == 0, equivalent to self.copy()."""
        return theory.TheoryClass.getKeyByInterval(self, interval)

    def getNewByFourths(self, nFourths):
        """Return a new Key object representing the key 'nFourths' degrees
        away from the current Key on the circle of fourths.  'nFourths' is
        any valid signed integer.
        If 'nFourths' > 0, the key signature adds flats/removes sharps
        (e.g. C -> F -> Bb -> Eb...).
        If 'nFourths' < 0, the key signature add sharps/removes flats (e.g.
        C -> G -> D -> A...).
        If 'nFourths' == 0, equivalent to self.copy()."""
        return theory.TheoryClass.getKeyByFourths(self, nFourths)

    def getNewByFifths(self, nFifths):
        return theory.TheoryClass.getKeyByFifths(self, nFifths)

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

def _clefParser(*args, **kwargs):
    """Wrapper function. Namespace hell."""
    theory.TheoryClass._clefParser(*args, **kwargs)

class Configuration(object):
    _FilenameForceDefaults = '*'
    _ConfigCalls = {
        #Name               : (callable, defaultValue)
        'clef'              : (_clefParser, "treble"),
        'noteLowest'        : (pypond.Note, "A2"),
        'noteHighest'       : (pypond.Note, "C6"),
        'key'               : (Key, "CM"),
        'diatonicity'       : (float, 0),
        'timeSignature'     : (_TimeSignature, "4/4"),
        'algorithm'         : (_AlgorithmParser, "MARandom"),
        'numMeasures'       : (int, 8),
        'density'           : (_float, 1.0),
        'shortestNote'      : (_float, 1/64),
        'longestNote'       : (_float, 1),
        'diatonicity'       : (_float, 1)
    }
    def __init__(self, filename = None):
        self.filename = filename
        if filename != None:
            if filename == self._FilenameForceDefaults:
                items = self.useDefaults()
            else:
                items = self.readIni()
            _dbg("{} read {} items; used defaults for {} items".format(
                  self.__str__(), items[0], items[1]))
        else:
            _dbg("{} uninitialized.  Call self.readIni(filename) or \
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
            _dbg("config({}) = {}".format(item[0], val))
            self._configStrings[item[0]] = val      # Add the string name to self._configStrings
        # = =  Add derived quantities = = 
        self.addDerivedQuantities()
        return (userCount, defaultCount)

    def addDerivedQuantities(self):
        noteMin = self.config.get('noteLowest')
        noteMax = self.config.get('noteHighest')
        _dbg("noteMin = {}; noteMax = {}".format(noteMin, noteMax))
        #print("noteMin = {}; noteMax = {}".format(noteMin, noteMax))
        keyNoteMin, keyNoteMax = self.getKeyNoteRange(noteMin, noteMax)
        self.config['keyNoteMin'] = keyNoteMin
        self.config['keyNoteMax'] = keyNoteMax
        #print("keyNoteMin = {}; keyNoteMax = {}".format(keyNoteMin, keyNoteMax))
        return
 
    def changeKey(self, newKey):
        if isinstance(newKey, Key):
            self.config['key'] = newKey
            self.addDerivedQuantities()

    def useDefaults(self):
        """Force the use of default values for self.config by passing an empty user config"""
        self.filename = "--DEFAULTS--"
        return self._populateConfig({})

    def getKeyNoteRange(self, noteMin, noteMax):
        key = self.config.get('key')
        _dbg("key = {}".format(key))
        mint, minlow, minhigh = key.isInKey(noteMin)
        maxt, maxlow, maxhigh = key.isInKey(noteMax)
        _dbg("noteMin = {}; in key? {}".format(noteMin, mint))
        _dbg("noteMax = {}; in key? {}".format(noteMax, maxt))
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

    @staticmethod
    def _invLog2(x):
        y = 0
        inv = 1/x
        while inv > 1:
            inv /= 2
            y += 1
        return y

class Randomer():
    x0 = math.sqrt(2*math.log(2))
    def __init__(self):
        pass

    @staticmethod
    def coinToss(heads = None, tails = None):
        """A custom-weighted random binary choice.  Returns True on 'heads'
        and False on 'tails'.  If 'heads' is given, 'tails' is ignored.
        'heads' + 'tails' = 1.0
        """
        if heads != None:
            heads = _float(heads)
            tails = 1.0 - heads
        elif tails != None:
            tails = _float(tails)
            heads = 1.0 - heads
        else:
            heads = 0.5
            tails = 0.5
        n = random.random()
        if n < heads:
            return True
        else:
            return False

    @staticmethod
    def randArray(array):
        """Select a random element of 'array' and return it. Like picking a
        card from a deck."""
        n = random.randint(0, len(array) - 1)
        return array[n]

    @classmethod
    def boundedGauss(cls, begin, end, center = None, order = 0):
        """This function is kinda weak right now.  'order' must be an integer
        and the probability rapidly peaks. Try something else.
        order = odd polynomial order
        If order == 0, linear function, equal probability.
        As order -> +inf, probability becomes peaked around the center."""
        x = 2*random.random() - 1     # Rand number between -1 and 1
        order = int((order + 1)*2 - 1)
        y = x**order                    # A weighted random number between -1 and 1
        yp = 5.5 + 4.5*y                # A weighted random number between 1 and 10
        ly = math.log10(yp)             # Now take the log; result between 0 and 1
        rng = abs(end - begin)
        #r = rng*ly
        r = rng*(y + 1)/2
        #print("x = {:.4}\torder = {}\ty = {:.4}\tr = {:.4}".format(x, order, y, r))
        return r

def _eval(s):
    """A safer version of eval, primarily for evaluating simple arithmetic expressions in
    string form."""
    l = []
    safechars = ('/', '+', '-', '*', '.', ')', '(')
    for c in s:
        if c.isdigit() or c in safechars:
            l.append(c)
    return eval(''.join(l))

class Error_InvalidConfig(Exception):
    pass

class Error_FileNotFound(Exception):
    pass

def _dbg(*args, **kwargs):
    if DEBUG:
        if LOGFILE != None:
            print("[{}]\t".format(FILENAME), file = LOGFILE, end = '')
            print(*args, **kwargs, file = LOGFILE)

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

def _testGetNumNotesInRange(argv):
    USAGE = "python3 {} <keyString> [noteLow] [noteHigh]".format(args[0])
    if len(argv) > 3:
        keyString = argv[1]
        key = Key(keyString)
        note1 = pypond.Note(argv[2])
        note2 = pypond.Note(argv[3])
    else:
        print(USAGE)
        return
    numNotes = key.getNumNotesInRange(note1, note2)
    print("notes in range ({}, {}) = {}".format(note1, note2, numNotes))

def _plotHistogram(array, nmin, nmax, bins = 10):
    rng = abs(nmax - nmin)
    mod = rng/bins
    #print("rng = {}; bins = {}; mod = {}".format(rng, bins, mod))
    binarray = [0]*bins
    for num in array:
        index = int((num - nmin)/mod)
        #print("num = {:.4}\tindex = {}".format(num, index))
        binarray[index] += 1
    fullchars = 60              # How many chars should represent a 'full' bar
    maxbin = max(binarray)
    total = 0
    for n in range(len(binarray)):
        pop = binarray[n]
        #print("bin {} has {}".format(n, pop))
        total += pop
    #print("Total ticks = {}".format(total))
    normarray = [int((fullchars*x)/maxbin) for x in binarray]
    for n in range(len(normarray)):
        row = normarray[n]
        print('{:2} |'.format(n) + '#'*row)

def _testRandomer(args):
    # Take 100 samples and make a histogram
    USAGE = "python3 {} [order]".format(args[0])
    l = 100000
    if len(args) > 1:
        order = abs(int(args[1]))
    else:
        order = 1
    function = lambda : Randomer.boundedGauss(0, 100, order = order)
    results = [0]*l
    for n in range(l):
        results[n] = function()
    _plotHistogram(results, 0, 100, bins = 40)

def _testKeyGetBestEnharmonic(argv):
    USAGE = "python3 {} keystring notestring".format(argv[0])
    if len(argv) > 2:
        keystring = argv[1]
        notestring = argv[2]
        key = Key(keystring)
        note = pypond.Note(notestring)
        newnote = key.getBestEnharmonic(note)
        print("key = {}; note = {}; enharmonic = {}".format(key, note, newnote))
    else:
        print(USAGE)
        return

def _testKeyGetEnharmonicInKey(argv):
    USAGE = "python3 {} keystring notestring".format(argv[0])
    if len(argv) > 2:
        keystring = argv[1]
        notestring = argv[2]
        key = Key(keystring)
        note = pypond.Note(notestring)
        newnote = key.getEnharmonicInKey(note)
        print("key = {}; note = {}; enharmonic = {}".format(key, note, newnote))
    else:
        print(USAGE)
        return

def _testKeyGetNoteInRange(argv):
    USAGE = "python3 {} <keyString> noteLow noteHigh index".format(argv[0])
    if len(argv) > 4:
        keyString = argv[1]
        key = Key(keyString)
        note1 = pypond.Note(argv[2])
        note2 = pypond.Note(argv[3])
        index = int(argv[4])
    else:
        print(USAGE)
        return
    indexNote = key.getNoteInRange(note1, note2, index)
    print("({}, {})[{}] = {}".format(note1, note2, index, indexNote))

if __name__ == "__main__":
    import sys
    argv = sys.argv
    FILENAME = argv[0]
    #_testTimeSignature(argv)
    #_testConfiguration(argv)
    #_testKey(argv)
    #_testIsInKey(argv)
    #_testGetNumNotesInRange(argv)
    #_testRandomer(argv)
    #_testKeyGetBestEnharmonic(argv)
    #_testKeyGetEnharmonicInKey(argv)
    _testKeyGetNoteInRange(argv)
