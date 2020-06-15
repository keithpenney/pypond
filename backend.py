#!/usr/bin/python3

# Some backend stuff for pypond

class RhythmElement():
    def __init__(self):
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

    def getEncoding(self):
        """Get note name encoding according to global _ENCODING_NOTES dict"""
        noteSimple = self.simplify()
        return _ENCODING_NOTES.get(noteSimple.getNoteName(), None)

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

    def __repr__(self):
        return "{}".format(self.getNoteString())

