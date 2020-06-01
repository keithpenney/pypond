#!/usr/bin/python3

"""An OOP approach to music scores with GNU lilypond text output"""

# MIDI notes:
#   Recall: Middle C (C4) is key 60
#   C1 = 24
#   A1 = 21
#   C0 = 12
#   A0 = 9
#   C-1 = 0

import sys
import re

DEBUG = True
LOGFILE = None
FILENAME = "pypond.py"

_LILYFLAT = 'es'
_LILYSHARP = 'is'
_LILYTIE = "~ "
_LILYMIDDLEOCTAVE = 3

_DEFAULT_OCTAVE = 4

_ENCODING_NOTES = {
    'C'  : 0,
    'c'  : 0,
    'B#' : 0,
    'b#' : 0,
    'C#' : 1,
    'c#' : 1,
    'Db' : 1,
    'db' : 1,
    'D'  : 2,
    'd'  : 2,
    'Eb' : 3,
    'eb' : 3,
    'D#' : 3,
    'd#' : 3,
    'E'  : 4,
    'e'  : 4,
    'Fb' : 4,
    'fb' : 4,
    'F'  : 5,
    'f'  : 5,
    'E#' : 5,
    'e#' : 5,
    'Gb' : 6,
    'gb' : 6,
    'F#' : 6,
    'f#' : 6,
    'G'  : 7,
    'g'  : 7,
    'Ab' : 8,
    'ab' : 8,
    'G#' : 8,
    'g#' : 8,
    'A'  : 9,
    'a'  : 9,
    'Bb' : 10,
    'bb' : 10,
    'A#' : 10,
    'a#' : 10,
    'B'  : 11,
    'b'  : 11,
}

#_ENCODING_ACCIDENTALS = {
#    'b'  : -1,
#    '#'  : 1,
#    ""   : 0
#}

class LilySyntax():
    kwClef = "\\clef"
    kwKey = "\\key"
    kwTimeSignature = "\\time"
    kwKeyMajor = "\\major"
    kwKeyMinor = "\\minor"
    headerString = '\\version "2.20.0"\n{\n  '
    footerString = '\n  \\bar "|."\n}'
    lilyTie = "~ "
    lilyDot = "."
    lilyFlat = "es"
    lilySharp = "is"
    encodingAccidentals = {
        lilyFlat    : -1,
        lilySharp   : 1
    }
    _reFlat = re.compile(lilyFlat+ "+")
    _reSharp = re.compile(lilySharp + "+")
    defaultOctave = 4
    octaveUp = "'"
    octaveDown = ','
 
    @classmethod
    def _DecodeAccidentalString(cls, sAccidental):
        """Return the encoding (integer) corresponding to a particular
        GNU Lilypond accidental.  Handles up to infinity sharp and infinity flat."""
        sAcc = sAccidental.strip()
        # Strip non-accidental content
        index = 0
        for n in range(len(sAcc)):
            if (sAcc[n] not in cls.lilyFlat) and (sAcc[n] not in cls.lilySharp):
                index = n
                break
        sAcc = sAcc[:index]
        encFlat = cls.encodingAccidentals.get(cls.lilyFlat, None)
        encSharp = cls.encodingAccidentals.get(cls.lilySharp, None)
        if cls._reFlat.match(sAcc):
            return encFlat*len(sAcc)//2
        elif cls._reSharp.match(sAcc):
            return encSharp*len(sAcc)//2
        else:
            return 0

class Note(object):
    noteMIDIOffsets = {'c' : 0, 'd' : 2, 'e' : 4, 'f' : 5, 'g' : 7, 'a' : 9, 'b' : 11}
    flatChar = 'b'
    sharpChar = '#'
    naturalChar = ""
    encodingAccidentals = {
        flatChar    : -1,
        sharpChar   : 1,
        naturalChar : 0
    }
    _reFlat = re.compile(flatChar + "+$")
    _reSharp = re.compile(sharpChar + "+$")
    _lilyTie = "~ "
    def __init__(self, notestring, duration = None, isTied = False):
        self.noteString = notestring
        self.noteName = Note._NoteNameFromString(notestring)
        self.accidental = Note._AccidentalFromString(notestring)
        self.octave = Note._OctaveFromString(notestring)
        self.duration = None
        self.tempo = None           # Use self.setTempo() to configure tempo for MIDI
        self.beatDuration = None    # the duration note that gets the beat (at self.tempo)
        self.durationMs = None      # self.setDuration()
        self.isTied = isTied
        self.measureNum = None
        self.beatNum = None
        self.dotted = False
        # Requires configuration of self.setBeatDuration() and self.setTempo() first
        if duration != None:
            self.setDuration(duration)
        if not self.checkValid():
            _dbg("Warning!  This Note object is no good: {}".format(self.__repr__()))
        #self.noteString = self.getNoteLetter() + self.getAccidentalString() + str(self.getOctave())
        #print("__init__ : self = {}".format(self))

    def isRest(self):
        return False

    def getNoteName(self):
        """Returns the note name as a lower-case string"""
        return self.noteName

    def getNoteLetter(self):
        """Returns the note letter name without any accidentals"""
        if self.noteName != None and self.noteName != "":
            return self.noteName[0]
        else:
            return ""

    def getAccidental(self):
        """Returns -1 for flat, +1 for sharp, or 0 for natural."""
        return self.accidental

    def getAccidentalString(self, accidental = None):
        """Return a string representing the accidental as sharps or flats
        if 'accidental' == None, uses self.accidental"""
        if accidental == None:
            accidental = self.getAccidental()
        #print("accidental = {}".format(accidental))
        accidental = _int(accidental)
        sign = 0
        self.naturalChar
        if accidental > 0:
            sign = 1
        elif accidental < 0:
            sign = -1
        for (k, v) in self.encodingAccidentals.items():
            if sign == v:
                sAcc = k
                break
        return sAcc * abs(accidental)

    def getOctave(self):
        """Returns the octave as a positive integer between 0 and 9"""
        return self.octave

    def setOctave(self, octave):
        oct = _int(octave)
        if oct != None:
            self.octave = oct

    def getNote(self):
        """Returns (noteName, accidental, octave)"""
        return (self.noteName[0], self.accidental, self.octave)

    def checkValid(self):
        """Check that Note constructor made a valid note object"""
        if (self.noteName is not None) and (self.accidental is not None) and (self.octave is not None):
            return True
        else:
            return False

    def _getLilyAccidental(self):
        """Get the note accidental string in GNU lilypond syntax"""
        s = ""
        if self.accidental == 0:
            return ""
        elif self.accidental < 0:
            s = _LILYFLAT
        elif self.accidental > 0:
            s = _LILYSHARP
        return  s * abs(self.accidental)

    def _getLilyOctave(self):
        """Get the note octave string indicator in GNU lilypad syntax"""
        o = self.getOctave()
        if o == _LILYMIDDLEOCTAVE:
            return ""
        elif o > _LILYMIDDLEOCTAVE:
            return "'" * (o - _LILYMIDDLEOCTAVE)
        else:
            return "," * (_LILYMIDDLEOCTAVE - o)

    #@DEPRECATED!
    def _getLilyDurationAligned(self, alignBeat):
        """First parse the alignBeat, then walk from LS-to-MS through the alignBeat parse
        and 'fill in the holes' taking from the note duration.  Once the beat has rounded
        out to all zeros (an even multiple of whole notes), walk down MS-to-LS the remaining
        note duration parse.

        On the first pass (LS-to-MS), we don't need to worry about dotting notes."""
        # Hmmm... didn't seem to get it right.  Poke further into this
        _dbg("  -   -   -   -   -   -   -   - alignBeat = {}".format(alignBeat))
        if alignBeat == None:
            alignBeat = self.getBeatNum()
            if alignBeat == None:
                return self._getLilyDuration()
        if self.duration == None:
            return ""
        duration = self.duration        # Need a shallow copy since we'll be modifying this
        nBeats = self.parseBeatLength(alignBeat)
        _dbg("parsed beat = {}{}{}{}{}{}{}".format(*nBeats))
        _dbg("old duration = {}".format(duration))
        ll = []
        tieSymbol = ""
        for n in range(len(nBeats)):    # Walk the beat parse
            if nBeats[-(n+1)]:          # (LS-to-MS)
                index = len(nBeats) - (n + 1)
                ddur = 2**(-index)      # We need to borrow this delta-duration from the note if possible
                if duration >= ddur:
                    duration -= ddur
                    ll.append("{}{}".format(tieSymbol, str(2**index)))
                    tieSymbol = self._lilyTie
                    alignBeat += ddur   # Give that duration to the alignBeat
                    nBeats = self.parseBeatLength(alignBeat)    # then parse the beat again
        _dbg("After walk up: {}".format("".join(ll)))
        _dbg("new duration = {}".format(duration))
        # Now we walk down the parsed remainder of the note duration
        nNotes = self.parseBeatLength(duration)
        candot = False                  # Note dotting
        for n in range(len(nNotes)):    # Walk through the breakdown of the note duration, starting from whole notes
            if nNotes[n] > 0:           # If a duration exists,
                if candot:              # If the last duration exists, we can dot it!
                    candot = False      # Then we turn off dotting so we don't end up with double-dots
                    ll.append('.')      # (those are silly)
                else:
                    candot = True       # The next note can be a dot if present
                    durationInt = 2**n  # 4 for quarter note, 8 for eighth note, etc...
                    ll.append("{}{}".format(tieSymbol, str(durationInt)))
                    tieSymbol = self._lilyTie # Once the first symbol has been added to lily list, set the tie symbol
            else:
                candot = False      # The next note cannot be a dot
        _dbg("After walk down: {}".format("".join(ll)))
        return "".join(ll)

    def _isBasisDuration(self):
        """Returns True if the note is a basis note (whole, half, quarter, eighth, 1/16, 1/32, 1/64)
        Returns False if the note is a combination of basis notes."""
        invdur = 1/self.getDurationNoDot()
        if invdur % 1 > 0:
            return False
        else:
            return True

    @staticmethod
    def _invLog2(x):
        y = 0
        inv = 1/x
        while inv > 1:
            inv /= 2
            y += 1
        return y

    def _getLilyDuration(self, alignBeat = None):
        """Get the duration indication in GNU lilypond format.
        For a power-of-two (i.e. quarter note, eighth note, whole note, etc.), we simply
        return a string of the reciprocal.
        For non-power-of-two (i.e. 11/16ths), we will end up with a combination of notes
        tied together, or potentially a single dotted note.

        We can use 'alignBeat' to try to suggest the best order of mixed-duration notes.
        For example, if the duration of the note is 1/2 + 1/8 (half-note plus eighth note),
        we could express it as a half note tied to an eighth note, or as an eighth tied to
        a half.  If we're at the beginning of a measure (alignBeat = 0), we bias toward
        starting with the larger beat (half note in this example).  If the current beat has
        an odd number of eighth notes, it makes more sense to start with the eighth note
        to round out the beat count, then continue with the largest-to-smallest pattern.

        We first parse the note duration and the alignBeat into a binary number.
        [b0, b1, b2, b3, b4, b5, b6]"""
        # To tie notes, we can simply replace the duration with power-of-two
        # durations (or dotted durations) with tildes (~) between them.
        if self.duration == None:
            return ""
        if self._isBasisDuration():
            return int(1/self.getDurationNoDot())
        length = self.duration # non-reciprocal units
        nNotes = self.parseBeatLength(length)
        nNotes = [x for x in nNotes]    # Need to convert tuple to a list to modify contents
        #print("1: {}\n1/2: {}\n1/4: {}\n1/8: {}\n1/16: {}\n1/32: {}\n1/64: {}".format(
        #      nNotes[0], nNotes[1], nNotes[2], nNotes[3], nNotes[4], nNotes[5], nNotes[6]))
        ll = []
        candot = False
        tieSymbol = ""                  # This will be populated later (this hack is to work around the dotted note)
        if alignBeat != None:           # If we're considering the alignment beat,
            nBeats = self.parseBeatLength(alignBeat)    # Parse the alignment beat count
            shortestBeat = 0
            for n in range(len(nBeats)):    # Find the shortest non-zero beat duration
                if nBeats[-(n+1)] > 0:      # i.e. if we're on beat 2.5 of 4/4 (alignBeat = 1/4 + 1/4 + 1/8 = 1/2 + 1/8,
                    shortestBeat = len(nBeats) - (n + 1)    # the shortest beat is 1/8
                    if nNotes[shortestBeat] > 0:    # If the note duration includes this shortest beat, let's start with that one
                        ll.append(str(2**shortestBeat))  # Append it to the lily list
                        nNotes[shortestBeat] = 0    # Then blank it out of the loop
                        tieSymbol = self._lilyTie # Set the tie symbol for subsequent items in the list
        
        for n in range(len(nNotes)):    # Walk through the breakdown of the note duration, starting from whole notes
            if nNotes[n] > 0:           # If a duration exists,
                if candot:              # If the last duration exists, we can dot it!
                    candot = False      # Then we turn off dotting so we don't end up with double-dots
                    ll.append('.')      # (those are silly)
                else:
                    candot = True       # The next note can be a dot if present
                    durationInt = 2**n  # 4 for quarter note, 8 for eighth note, etc...
                    ll.append("{}{}".format(tieSymbol, str(durationInt)))
                    tieSymbol = self._lilyTie # Once the first symbol has been added to lily list, set the tie symbol
            else:
                candot = False      # The next note cannot be a dot
        return "".join(ll)

    @staticmethod
    def parseBeatLength(length):
        """Parse a beat length into number of whole notes, half notes, quarter notes, etc...
        The beat length should be 1/2 or a half note, 1/4 for a quarter note (non-reciprocal
        units).
        Returns [nWhole, nHalf, nQuarter, n8th, n16th, n32nd, n64th]
        
        Here we're basically just representing a duration in a binary system with 1/64th as
        the least-significant (LS) bit and a whole note as the most-significant (MS) bit.
        This gives us a 7 digit number (0 to 127).
        0 = No duration
        1 = 1/64th note
        2 = 1/32nd note
        4 = 1/16th note
        8 = 1/8th note
        16 = 1/4 note
        32 = 1/2 note
        64 = whole note
        Any other number is simply a combination of these."""
        return [int(x) for x in "{:07b}".format(int(length*64))]

    def _getLilyTie(self):
        if self.getTie():
            return LilySyntax.lilyTie
        else:
            return ""

    def _getLilyDot(self):
        if self.getDot():
            return LilySyntax.lilyDot
        else:
            return ""

    def asLily(self):
        """Return a string of the GNU lilypad representation of the note."""
        n = self.getNoteName()[0].lower()
        a = self._getLilyAccidental()
        o = self._getLilyOctave()
        d = self._getLilyDuration()
        s = self._getLilyDot()
        t = self._getLilyTie()
        return "{}{}{}{}{}{}".format(n, a, o, d, s, t)

    def asLilyNoteName(self):
        n = self.getNoteLetter().lower()
        a = self._getLilyAccidental()
        return "{}{}".format(n, a)

    def setBeatDuration(self, beatDuration):
        dur = _float(beatDuration)
        if dur == None:
            raise Error_Float("Cannot parse {}".format(beatDuration))
            return
        self.beatDuration = dur

    def getDurationDecomposed(self, reciprocal = True):
        nBeats = self.parseBeatLength(self.getDuration())
        s = []
        for n in range(len(nBeats)):
            if nBeats[n]:
                m = 2**n
                if not reciprocal:
                    s.append("1/{}".format(m))
                else:
                    s.append(str(m))
        return "+".join(s)

    def setTempo(self, tempoBPM):
        tempo = _float(tempoBPM)
        if dur == None:
            raise Error_Float("Cannot parse {}".format(tempoBPM))
            return
        self.tempo = tempoBPM

    def durationToMs(self, duration):
        if self.beatDuration == None or self.tempo == None:
            #_dbg("Unconfigured tempo. beatDuration = {}\ttempo = {}".format(\
            #          self.beatDuration, self.tempo))
            return None
        if duration == 0:
            _dbg("Invalid duration {}".format(duration))
            return None
        return (1000 * 60 * self.beatDuration * duration) / self.tempo

    def getDuration(self):
        """Return the note duration as a float (i.e. 0.125 = 1/8 for an eighth note)
        Includes effect of dotting."""
        if self.getDot():
            return self.duration*1.5
        else:
            return self.duration

    def getDurationNoDot(self):
        """Return the note duration ignoring dotting."""
        return self.duration

    def getDurationReciprocal(self):
        """Return the note duration in reciprocol units
        (i.e. 1 = whole note, 8 = 1/8th note, 16 = 1/16th note)"""
        return 1/self.duration

    def setDuration(self, duration):
        """Set the note duration in normal units, i.e. 0.125 = 1/8 for an eighth note.
        Tuplets are undetermined as of yet."""
        dur = _float(duration)
        if dur == None:
            raise Error_Float("Cannot interpret duration {}".format(duration))
            return False
        else:
            self.duration = dur
            self.durationMs = self.durationToMs(dur)
            return True

    def getDurationMs(self):
        """Return the note duration in milliseconds (ms)"""
        return self.durationMs

    def isEqualNote(self, notestring):
        """Returns true if 'notestring' represents the same note (could be
        in a different octave) as self"""
        if isinstance(notestring, Note):
            noteEncoding = notestring.getEncoding()
        else:
            note = self.new(notestring)
            simpleNote = note.simplify()
            noteEncoding = simpleNote.getEncoding()
        if noteEncoding == None:
            return False
        else:
            if self.getEncoding() == noteEncoding:
                return True
            else:
                return False

    def isEqualOctave(self, notestring):
        """Returns True if 'notestring' represents a note in the same octave as self.
        Note that this isn't all that useful outside of Note.isEqualPitch, since the
        octave division point is somewhat arbitrary (between B and C)."""
        if isinstance(notestring, Note):
            octave = notestring.getOctave()
        else:
            octave = Note._OctaveFromString(notestring)
        if octave == self.getOctave():
            return True
        else:
            return False

    def isEqualPitch(self, notestring):
        """Returns True only if 'notestring' represents the exact same pitch as self
        (note name and octave)."""
        if self.isEqualNote(notestring) and self.isEqualOctave(notestring):
            return True
        else:
            return False

    def getEncoding(self):
        """Get note name encoding according to global _ENCODING_NOTES dict"""
        noteSimple = self.simplify()
        return _ENCODING_NOTES.get(noteSimple.getNoteName(), None)

    def simplify(self, notestring = None):
        """Return a simplified enharmonic equivalent note.
        I.e. if note = Dbb, note.simplify = C"""
        if notestring != None:
            note = self.new(notestring)
        else:
            note = self
        b = note.getMIDIByte()
        return self.fromMIDIByte(b)

    def getInterval(self, note):
        """Return the smallest interval between self and note, ignoring octaves.
        If note is higher than self, returns interval > 0"""
        note = note.copy() # Shouldn't need this.  I believe it passes a copy
        note.setOctave(self.getOctave())
        selfpitch = self.getMIDIByte()
        notepitch = note.getMIDIByte()
        interval = notepitch - selfpitch
        if abs(interval) < 7:
            return interval
        else:
            if interval < 0:
                # Note is too low, go up an octave
                sign = 1
            else:
                # Note is too high, go down an octave
                sign = -1
        while abs(interval) > 6:
            interval += sign*12
        return interval

    def getNoteByInterval(self, interval, sharp = True):
        """Returns a new Note object that is 'interval' away from self.
        'interval' is an integer number of half-steps (+/-).
        If sharp == True, default to the sharp (#) enharmonic equivalent
        if appropriate.  Else, default to the flat (b) equivalent."""
        interval = _int(interval)
        if interval == None:
            raise Error_Interval("Cannot interpret interval {}".format(interval))
            return None
        midibyte = self.getMIDIByte()
        return self.fromMIDIByte(midibyte + interval, sharp = sharp)

    @classmethod
    def _NoteNameFromString(cls, notestring):
        if notestring == None:
            return ""
        notestring = notestring.strip()
        notenames = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        if (len(notestring) < 1):
            _dbg("Empty notestring")
            return None
        if notestring[0].lower() not in notenames:
            _dbg("Note name not valid: {}".format(notestring[0]))
            return None
        if len(notestring) > 1:
            n = 1
            while n < len(notestring):
                t, c = cls._isAccidentalChar(notestring[n])
                if not t:
                    # If we hit a character that's not an accidental char
                    break
                n += 1
            return notestring[0].upper() + notestring[1:n].lower()
        else:
            return notestring[0].upper()

    @classmethod
    def _NoteNameFromLilyString(cls, lilystring):
        if lilystring == None:
            return ""
        lilystring = lilystring.strip()
        notenames = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'r'] # Allow for rest too
        if (len(lilystring) < 1):
            _dbg("Empty lilystring")
            return None
        if lilystring[0].lower() not in notenames:
            _dbg("Note name not valid: {}".format(lilystring[0]))
            return None
        if lilystring[0] == 'r':
            return 'r'
        if len(lilystring) > 1:
            accidental = ''
            t, c = cls._isAccidentalCharLily(lilystring[1:])
            #print("_isAccidentalCharLily: {}, {}".format(t, c))
            if t:
                accidental = c
            return lilystring[0].upper() + accidental
        else:
            return lilystring[0].upper()

    @classmethod
    def _DecodeLilyDuration(cls, lilystring):
        nl = []
        for c in lilystring:
            if c.isdigit():
                nl.append(c)
        invdur = _int(''.join(nl))
        if invdur == None:
            return 1
        return 1/invdur

    @classmethod
    def _DecodeLilyOctave(cls, lilystring):
        octave = LilySyntax.defaultOctave
        for c in lilystring:
            if c == LilySyntax.octaveUp:
                octave += 1
            elif c == LilySyntax.octaveDown:
                octave -= 1
        return octave

    @classmethod
    def _DecodeLilyTie(cls, lilystring):
        if not hasattr(lilystring, '__len__'):
            return False
        if lilystring == '':
            return False
        tied = False
        for c in lilystring:
            if c == LilySyntax.lilyTie[0]:
                tied = True
        return tied

    @classmethod
    def _AccidentalFromString(cls, notestring):
        """Parse the accidental from a notestring.  E.g.
        notestring      Accidental
        ----------      ----------
        Ab4             -1
        G8              0
        C#-1            1
        Fbb10           -2
        B##6            2
        etc..."""
        if notestring == None:
            return ""
        notestring = notestring.strip()
        if (len(notestring) < 1):
            _dbg("Empty notestring")
            return None
        if len(notestring) >= 2:
            if _isDigit(notestring[1]):
                # Accidental not specified; Default to natural
                return 0
            count = 0
            n = 1
            while n < len(notestring):
                t, c = cls._isAccidentalChar(notestring[n].lower())
                if t:
                    count += c
                elif _isDigit(notestring[n]):
                    break
                n += 1
            return count
        else:
            # len(notestring) = 1, no accidental, no octave
            return 0

    @classmethod
    def _OctaveFromString(cls, notestring):
        """Get the octave specified by a notestring.
        Returns None on failure.  Returns _DEFAULT_OCTAVE if no octave
        is specified in notestring"""
        if notestring == None:
            return ""
        notestring = notestring.strip()
        index = -1
        if len(notestring) <= 1:
            # No octave specified
            return _DEFAULT_OCTAVE
        else:
            n = 1
            while n < len(notestring):
                c = notestring[n]
                if _isDigit(c):
                    break
                n += 1
            if n < len(notestring):
                # A digit has been encountered
                index = n
            else:
                # No octave specified
                return _DEFAULT_OCTAVE
        oct = _int(notestring[index:])
        if oct == None:
            _dbg("Cannot interpret octave from notestring {}".format(notestring))
        return oct

    @classmethod
    def _DecodeAccidentalInt(cls, intAccidental):
        """Return the encoding (string) corresponding to a particular integer
        accidental.  Handles up to infinity sharp and infinity flat."""
        intAccidental = _int(intAccidental) # Just in case
        if intAccidental == None:
            raise Error_Integer("{} cannot be interpreted as an integer".format(intAccidental))
        for item in cls.encodingAccidentals.items():
            if item[1] == -1:
                encMinus = item[0]
            elif item[1] == 0:
                encZero = item[0]
            elif item[1] == 1:
                encPlus = item[0]
        if intAccidental == 0:
            s = encZero
        elif intAccidental < 0:
            s = encMinus
        elif intAccidental > 0:
            s = encPlus
        return s*abs(intAccidental)

    @classmethod
    def _DecodeAccidentalString(cls, sAccidental):
        """Return the encoding (integer) corresponding to a particular
        string accidental.  Handles up to infinity sharp and infinity flat."""
        sAcc = sAccidental.strip()
        encFlat = cls.encodingAccidentals.get(cls.flatChar, None)
        encSharp = cls.encodingAccidentals.get(cls.sharpChar, None)
        encNatural = cls.encodingAccidentals.get(cls.naturalChar, None)
        if sAcc == cls.naturalChar:
            return encNatural
        if cls._reFlat.match(sAcc):
            return encFlat*len(sAcc)
        if cls._reSharp.match(sAcc):
            return encSharp*len(sAcc)

    @classmethod
    def _isAccidentalChar(cls, char):
        char = char[0]  # Just in case someone tries to pass more than one character
        acc = cls.encodingAccidentals.get(char, None)
        if acc == None:
            f = False
        else:
            f = True
        return (f, acc)

    @classmethod
    def _isAccidentalCharLily(cls, accstr):
        if len(accstr) > 1:
            chars = accstr[:2]
        else:
            return (False, None)
        acc = LilySyntax.encodingAccidentals.get(chars, None)
        if acc == None:
            # No accidental
            f = False
        else:
            # Accidental
            accint = LilySyntax._DecodeAccidentalString(accstr) # Get the integer encoding
            acc = cls._DecodeAccidentalInt(accint)  # Decode as standard syntax (b/#)
            f = True
        return (f, acc)

    @classmethod
    def getPitchFromNoteString(cls, noteString):
        """Same as getMIDIByte(), but without creating an object to use the instance method.
        Parse 'noteString' and return the integer pitch (based on MIDI standard) corresponding
        to this note."""
        noteName = cls._NoteNameFromString(noteString)
        offset = cls.noteMIDIOffsets.get(noteName.lower(), None)
        if offset == None:
            _dbg("Note.getPitchFromNoteString() offset not found.")
            return None
        octave = cls._OctaveFromString(noteString)
        accidental = cls._AccidentalFromString(noteString)
        return 12*(octave + 1) + offset + accidental

    def toInteger(self):
        """A synonym for 'getMIDIByte' which is more intuitive in most use cases."""
        return self.getMIDIByte()

    def getMIDIByte(self):
        """Get the corresponding MIDI number representing the pitch"""
        offset = self.noteMIDIOffsets.get(self.getNoteName()[0].lower(), None)
        if offset == None:
            _dbg("Note.getMIDIByte() offset not found.")
            return None
        return 12*(self.getOctave() + 1) + offset + self.getAccidental()

    @classmethod
    def fromInteger(cls, integer, duration = None, sharp = True):
        """A synonym for 'fromMIDIByte' which is more intuitive in most use cases."""
        return cls.fromMIDIByte(integer, duration, sharp)

    @classmethod
    def fromMIDIByte(cls, midibyte, duration = None, sharp = True):
        """Return a Note object represented by integer 'midibyte'
        If sharp == True, default to the sharp (#) enharmonic equivalent
        if appropriate.  Else, default to the flat (b) equivalent."""
        midibyte = _int(midibyte)   # Convert to an integer, just in case
        if midibyte == None:
            raise Error_MIDI_Byte("Cannot interpret {}".format(midibyte))
        octave = midibyte//12 - 1
        offset = midibyte%12
        noteMatch = None
        nextHighest = None
        nextLowest = None
        accidental = None
        accstring = None
        for note in cls.noteMIDIOffsets.keys():
            noffset = cls.noteMIDIOffsets[note]
            if offset == noffset:
                noteMatch = note
            elif offset == noffset + 1:
                nextLowest = note
            elif offset == noffset - 1:
                nextHighest = note
        if noteMatch == None:
            # We're looking at a black key
            if sharp:
                noteName = nextLowest # start with lower, then sharp it
                accidental = 1
            else:
                noteName = nextHighest # start with higher, then flat it
                accidental = -1
        else:
            noteName = noteMatch
            accidental = 0
        for key in cls.encodingAccidentals:
            if accidental == cls.encodingAccidentals[key]:
                accstring = key
        notestring = "{}{}{}".format(noteName.upper(), accstring, str(octave))
        return Note(notestring, duration)

    def getNoteString(self):
        self.noteString = self.getNoteLetter() + self.getAccidentalString() + str(self.getOctave())
        return self.noteString

    def copy(self):
        return self.new(self.noteString, self.duration)

    def alter(self, interval):
        """Similar to getNoteByInterval() except simply alters the note further.
        I.e. if note = C#, note.getNoteByInterval(1) = D, note.alter(1) = C##
        I.e. if note = Bb, note.getNoteByInterval(-2) = Ab, note.alter(-2) = Bbbb"""
        acc = self.getAccidental()
        sAcc = self.getAccidentalString(acc + _int(interval))
        noteName = self.getNoteLetter()
        return self.new(noteName + sAcc, self.getDuration())

    def sharp(self):
        """Return a copy of the note sharped E.g.:
        if note = C,  note.sharp() = C#
        if note = Eb, note.sharp() = E
        if note = G#, note.sharp() = G##"""
        return self.alter(1)

    def flat(self):
        """Return a copy of the note flatted E.g.:
        if note = C,  note.flat() = Cb
        if note = Eb, note.flat() = Ebb
        if note = G#, note.flat() = G"""
        return self.alter(-1)

    def getTie(self):
        """Returns True if this note is tied to the subsequent note.
        Only meaningful in sheet music."""
        return self.isTied

    def setTie(self, tie):
        """Set the 'isTied' flag to declare that this note is tied
        to a subsequent note (only meaningful in sheet music)."""
        if tie == None:
            return
        if tie:
            self.isTied = True
        else:
            self.isTied = False

    def setDot(self, dotted):
        if dotted:
            self.dotted = True
        else:
            self.dotted = False

    def getDot(self):
        return self.dotted

    def setBeatNum(self, beatNum):
        beatNum = _float(beatNum)   # Sanitize input
        if beatNum == None:
            return False
        self.beatNum = beatNum
        return True

    def getBeatNum(self):
        return self.beatNum

    def setMeasureNum(self, measureNum):
        measureNum = _int(measureNum)   # Sanitize input
        if measureNum == None:
            return False
        self.measureNum = measureNum
        return True

    def getMeasureNum(self):
        return self.measureNum

    @classmethod
    def new(cls, notestring, duration = None):
        return cls(notestring, duration)

    @classmethod
    def fromLily(cls, lilystring):
        """Create a new Note object from a GNU Lilypond string."""
        if lilystring == None:
            return ''
        if len(lilystring) < 1:
            return ''
        name = cls._NoteNameFromLilyString(lilystring)
        if name == None:
            return None
        dur = cls._DecodeLilyDuration(lilystring)
        octave = cls._DecodeLilyOctave(lilystring)
        if name == 'r':
            note = Rest.new(dur)
        else:
            note = cls.new(name + str(octave), dur)
        tie = cls._DecodeLilyTie(lilystring)
        if tie:
            note.setTie(True)
        return note

    def __repr__(self):
        return "{}".format(self.getNoteString())

    def _summary(self):
        return "{} = {} =\t{} (MIDI)\t{} (lilypond)".format(self.getNoteString(), 
              self.getNoteName(), self.getMIDIByte(), self.asLily())

    def _shortSummary(self):
        dur = self.getDuration()
        if dur == None:
            dur = '-'
        else:
            dur = int(1/dur)
        if self.getDot():
            dot = '.'
        else:
            dot = ""
        return "{:}{:d}{}".format(self.getNoteName(), dur, dot)

    def _print(self):
        print(self._summary())

class Rest(Note):
    _lilyTie = " r" # HACK ALERT! This might work, but it's a band-aid on a stab wound
    def __init__(self, duration = None):
        super().__init__(notestring = None, duration = duration)
        self.noteName = 'r'
        self.noteString = 'r'
        self.isTied = False

    def isRest(self):
        return True

    def setTie(self, tie):
        """Rests are never tied."""
        return

    def _getLilyAccidental(self):
        """A rest has no accidental"""
        return ""

    def _getLilyOctave(self):
        """A rest has no associated octave"""
        return ""

    def getNoteByInterval(self, interval, sharp = True):
        """This is nonsense; might as well return another rest."""
        return Rest(self.duration)

    def __repr__(self):
        dur = str(self.getDuration())
        return "Rest({})".format(dur)

    def copy(self):
        return self.new(self.duration)

    @classmethod
    def new(cls, duration):
        return cls(duration)

    def __add__(self, rest):
        """Gets the beat number from the first operand."""
        if hasattr(rest, 'getDuration'):
            duration = rest.getDuration()
        elif isinstance(rest, float):
            duration = rest
        temp = self.new(self.getDuration() + duration)
        temp.setBeatNum(self.getBeatNum())
        return temp

def _dbg(*args, **kwargs):
    if DEBUG:
        if LOGFILE != None:
            print("[{}]\t".format(FILENAME), file = LOGFILE, end = '')
            print(*args, **kwargs, file = LOGFILE)

def _isDigit(c):
    if isinstance(c, int):
        return True
    if c.isdigit():
        return True
    if c == '-':
        return True
    if c == '+':
        return True
    return False

def midiByte(note, onoff):
    noteName = None
    noteOctave = None
    accidental = 0
    notes = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
    acc = ['b', '#']
    if len(note) > 3:
        print("note {} not valid".format(note))
        return None
    else: pass
    if note[0].lower() not in notes:
        print("Note name not valid: {}".format(note[0]))
        return None
    else:
        noteName = note[0].lower()
    if not _isDigit(note[1]):
        if note[1].lower() in acc:
            if note[1] == acc[0]:
                accidental = -1
            elif note[1] == acc[1]:
                accidental = 1
            else:
                print("How the hell did this happen?")
        else:
            print("Octave not valid: {}".format(note[1]))
    else:
        noteOctave = int(note[1])

def _int(s):
    r = None
    try:
        r = int(s)
        return r
    except ValueError:
        pass
    if 'x' in s.lower():
        # Maybe it's a hex string?
        try:
            r = int(s, 16)
            return r
        except ValueError:
            pass
        # Maybe it's a non-standard hex string? With no prepended '0'?
        index = s.lower().index('x')
        if index == 0:
            s = '0' + s
        else:
            s[index-1] = '0'
        try:
            r = int(s, 16)
            return r
        except ValueError:
            pass
    if '.' in s:
        # Maybe it's a float string with a decimal point?
        index = s.index('.')
        try:
            # Try just converting the part before the decimal point
            r = int(s[:index])
            return r
        except ValueError:
            pass
    # If we reach here, just give up
    return None

def _float(s):
    if s == None:
        return None
    if isinstance(s, float):
        return s
    try:
        r = float(s)
    except (ValueError, TypeError):
        return None
    return r

class Error_MIDI_Byte(Exception):
    pass

class Error_Interval(Exception):
    pass

class Error_Integer(Exception):
    pass

class Error_Float(Exception):
    pass

def _testNoteCopy(args):
    USAGE = "Usage:\n\tpython3 {0} <NoteString>".format(sys.argv[0])
    if len(argv) > 1:
        note1 = Note(argv[1])
        note2 = note1.copy()
        print("Note = {}; copy = {}".format(note1._summary(), note2._summary()))
        note2.setDuration(16)
        print("Note = {}; copy = {}".format(note1._summary(), note2._summary()))
    else:
        print(USAGE)

def _testNoteInterval(args):
    USAGE = "Usage:\n\tpython3 {0} [NoteString]\n\tpython3 {0} [NoteString] [Interval]".format(sys.argv[0])
    if len(argv) > 2:
        note1 = Note(argv[1])
        interval = _int(argv[2])
        note2 = note1.getNoteByInterval(interval, sharp = False)
        print("{} + {} = {}".format(note1.getNoteString(), interval, note2.getNoteString()))
    elif len(argv) > 1:
        noteName = argv[1]
        note = Note(noteName)
        note._print()
    else:
        print(USAGE)

def _testNoteDuration(args):
    USAGE = "Usage:\n\tpython3 {0} <NoteString> <length> [alignBeat]".format(sys.argv[0])
    if len(args) > 3:
        note = Note(args[1])
        length = eval(args[2])
        beat = eval(args[3])
        note.setDuration(length)
        print("duration = {}".format(note._getLilyDuration(beat)))
    elif len(args) > 2:
        note = Note(args[1])
        length = eval(args[2])
        note.setDuration(length)
        print("duration = {}".format(note._getLilyDuration()))
    else:
        print(USAGE)

def _testGetPitchFromNoteString(args):
    USAGE = "Usage:\n\tpython3 {0} <NoteString>".format(sys.argv[0])
    if len(args) > 1:
        noteString = args[1]
        pitch = Note.getPitchFromNoteString(noteString)
        print("pitch = {}".format(pitch))
    else:
        print(USAGE)

def _testRest(args):
    USAGE = "Usage:\n\tpython3 {0} <RestDuration>".format(sys.argv[0])
    if len(args) > 2:
        restDuration1 = _float(args[1])
        restDuration2 = _float(args[2])
        rest1 = Rest(restDuration1)
        rest2 = Rest(restDuration2)
        print(rest1 + rest2)
    elif len(args) > 1:
        restDuration = _float(args[1])
        rest = Rest(restDuration)
        print("rest = {} = {}".format(rest, rest.asLily()))
    else:
        print(USAGE)

def _testNoteSharpFlat(args):
    USAGE = "Usage:\n\tpython3 {0} [NoteString]\n\tpython3 {0} [NoteString] [s,f]".format(sys.argv[0])
    if len(argv) > 2:
        note1 = Note(argv[1])
        sharpflat = argv[2]
        if sharpflat.strip().lower() == 'f':
            note2 = note1.flat()
            f = 'flat'
        elif sharpflat.strip().lower() == 's':
            note2 = note1.sharp()
            f = 'sharp'
        else:
            print("{} must be 's' or 'f'".format(sharpflat))
            return
        print("{}({}) = {}".format(f, note1.getNoteString(), note2.getNoteString()))
    elif len(argv) > 1:
        noteName = argv[1]
        note = Note(noteName)
        note._print()
    else:
        print(USAGE)

def _testNoteGetInterval(args):
    USAGE = "Usage:\n\tpython3 {0} [NoteString]\n\tpython3 {0} [NoteString] [NoteString]".format(sys.argv[0])
    if len(argv) > 2:
        note1 = Note(argv[1])
        note2 = Note(argv[2])
        interval = note1.getInterval(note2)
        print("{} - {} = {}".format(note2.getNoteString(), note1.getNoteString(), interval))
    elif len(argv) > 1:
        noteName = argv[1]
        note = Note(noteName)
        print(str(note))
        #note._print()
    else:
        print(USAGE)

def _testNoteFromLily(args):
    USAGE = "Usage:\n\tpython3 {0} [LilyString]".format(sys.argv[0])
    if len(argv) > 1:
        lilystring = argv[1]
        note = Note.fromLily(lilystring)
        print("{}\tDuration = {}\tTie = {}".format(note, note.getDuration(), note.getTie()))
    else:
        print(USAGE)

if __name__ == "__main__":
    import sys
    argv = sys.argv
    FILENAME = argv[0]
    #_testNoteInterval(argv)
    #_testNoteCopy(argv)
    #_testNoteDuration(argv)
    #_testGetPitchFromNoteString(argv)
    #_testRest(argv)
    #_testNoteSharpFlat(argv)
    #_testNoteGetInterval(argv)
    _testNoteFromLily(argv)
