#!/usr/bin/python3

"""A python script to generate GNU lilypad sheet music from muse.py and pypond.py"""
# Lilypond path: C:\Program Files (x86)\LilyPond\usr\bin

# TODO! Keep track of the beats in the measure and break up a single note into two notes
# tied together across a barline when necessary.
# TODO! Compose a given number of measures, not notes.

# TODO Dotted notes need to know when to break across measures

import os, subprocess
import muse, pypond
import time

DEBUG = False

# Change the below to match the install path of GNU Lilypond on your system
_LILYPATH = "\"C:/Program Files (x86)/LilyPond/usr/bin\""
# If using Windows, this should be "lilypond.exe"; if using MacOS/Linux, it should simply be "lilypond"
_LILYEXEC = "lilypond.exe"

class Composer():
    headerString = '\\version "2.20.0"\n{\n  '
    footerString = '\n  \\bar "|."\n}'
    _defaultConfigFile = "cfg.ini"
    _defaultOutputFile = "test.ly"
    _lilyExt = "ly"
    def __init__(self, configFilename, outputFilename):
        #if algorithm == None:
        #    algorithm = muse.MAGaussMeander() # Ultimately a configuration should go here
        if configFilename == None:
            self.configFilename = self._defaultConfigFile
        else:
            self.configFilename = configFilename
        self.config = muse.Configuration(self.configFilename)
        if outputFilename == None:
            self.outputFilename = self.generateOutputFilename()
        else:
            root, ext = os.path.splitext(outputFilename)
            if ext.lower().strip('.') != self._lilyExt:     # Ensure we have the correct file extension
                outputFilename = root + '.' + self._lilyExt
            self.outputFilename = outputFilename
        self.algorithm = self.config.get('algorithm')
        self.algorithm.setConfig(self.config)
        #print("self.algorithm = {}".format(self.algorithm))
        self.numMeasures = self.config.get('numMeasures')
        self.measureCount = 0
        self.beatCount = 0
        self.measureDuration = self.config.getMeasureDuration()
        self.finished = False

    def getNextNoteLilyOLD(self):
        return self.algorithm.getNextNoteLily()

    def getNextNoteLily(self):
        #tiesymbol = pypond._LILYTIE
        startBeat = self.beatCount
        note = self.algorithm.getNextNote()
        notes = self.splitAtMeasures(note)  # modifies self.beatCount
        if len(notes) > 1:
            return (notes[0].asLily(startBeat) + notes[0]._lilyTie, notes[1].asLily())
        else:
            return (notes[0].asLily(startBeat),)      # TODO Handle ties in GNU lilypond format
        
        #return (x.asLily(self.beatCount) for x in notes)

    def splitAtMeasures(self, note):
        # figure out the math here
        noteDuration = note.getDuration()
        noteLength = noteDuration # recall duration not stored as reciprocol units
        _dbg("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
        _dbg("beatCount = {}; noteLength = {}; measureCount = {}".format(
             self.beatCount, noteLength, self.measureCount))
        if self.beatCount + noteLength >= self.measureDuration:     # If the note would continue to the next measure
            firstLength = self.measureDuration - self.beatCount     # Split the note into two notes
            secondLength = noteLength - firstLength                 # Get the difference
            self.measureCount += 1                                  # Increment the measure count
            self.beatCount = secondLength                           # Wrap the beat count
        else:
            firstLength = noteLength
            secondLength = 0
            self.beatCount += firstLength
        if self.measureCount == self.numMeasures:                   # If we hit the max measures
            self.finished = True                                    # terminate the composition
            secondLength = 0                                        # And ignore any remaining duration
        #firstDuration = self._invert(firstLength)
        #secondDuration = self._invert(secondLength)
        note1 = note.copy()
        note2 = note.copy()
        note1.setDuration(firstLength)
        _dbg("note1 = {}; note2 = {}".format(firstLength, secondLength))
        if secondLength != 0:
            note2.setDuration(secondLength)
            return (note1, note2)
        else:
            return (note1,)

    def _getLilyDuration(self, note):
        # UNUSED CURRENTLY
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
        to round out the beat count, then continue with the largest-to-smallest pattern."""
        # To tie notes, we can simply replace the duration with power-of-two
        # durations (or dotted durations) with tildes (~) between them.
        length = note.getDuration() # non-reciprocal units
        if length == None:
            return ""
        nNotes = pypond.Note.parseBeatLength(length)
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
                    break
            if nNotes[shortestBeat] > 0:    # If the note duration includes this shortest beat, let's start with that one
                ll.append(str(2**shortestBeat))  # Append it to the lily list
                nNotes = [x for x in nNotes]    # Need to convert tuple to a list to modify contents
                nNotes[shortestBeat] = 0    # Then blank it out of the loop
                tieSymbol = "~ "        # Set the tie symbol for subsequent items in the list
        
        for n in range(len(nNotes)):    # Walk through the breakdown of the note duration, starting from whole notes
            if nNotes[n] > 0:           # If a duration exists,
                if candot:              # If the last duration exists, we can dot it!
                    candot = False      # Then we turn off dotting so we don't end up with double-dots
                    ll.append('.')      # (those are silly)
                else:
                    candot = True       # The next note can be a dot if present
                    durationInt = 2**n  # 4 for quarter note, 8 for eighth note, etc...
                    ll.append("{}{}".format(tieSymbol, str(durationInt)))
                    tieSymbol = "~ "   # Once the first symbol has been added to lily list, set the tie symbol
            else:
                candot = False      # The next note cannot be a dot
        return "".join(ll)


    @staticmethod
    def _invert(length):
        if (length == None) or (length == 0):
            return None
        else:
            return 1/length

    def getFd(self):
        #return None     # TEMPORARY BYPASS
        try:
            _dbg("opening {}".format(self.outputFilename))
            fd = open(self.outputFilename, 'w')
        except:
            return None
        return fd

    def writeString(self, string, fd = None):
        self._write(string, fd)

    def writeStringOLD(self, string, fd = None):
        closeAfter = False
        if fd == None:
            closeAfter = True
            fd = self.getFd()
        fd.write(string)
        if closeAfter:
            fd.close()

    def writeHeader(self, fd = None):
        """Write a GNU Lilypad header"""
        self.writeString(self.headerString, fd)

    def writeNotes(self, fd = None):
        wordcount = 0
        wordsperline = 4
        notes = []
        while not self.finished:
            nextNotes = self.getNextNoteLily()
            for note in nextNotes:
                notes.append(note)
                if wordcount == wordsperline:
                    wordcount = 0
                    notes.append('\n\r  ')
                else:
                    wordcount += 1
        notestring = " ".join(notes)
        self.writeString(notestring, fd)

    def writeFooter(self, fd = None):
        """Write a GNU Lilypad footer"""
        self.writeString(self.footerString, fd)
    
    def writeAll(self, fd = None):
        closeAfter = False
        self.finished = False
        if fd == None:
            closeAfter = True
            fd = self.getFd()
        self.writeHeader(fd)
        self.writeNotes(fd)
        self.writeFooter(fd)
        if fd != None:
            fd.close()

    def _write(self, string, fd = None):
        if fd == None:
            print(string)
        else:
            fd.write(string)

    def generateOutputFilename(self):
        algorithm = self.config.gets('algorithm', None)
        if algorithm == None:
            algorithm = "test"
        datestring = self.getTimeStamp()
        return "{}_{}.{}".format(algorithm, datestring, self._lilyExt)

    def getTimeStamp(self):
        ts = time.localtime()
        return "{:02}{:02}{:02}_{:02}{:02}{:02}".format(ts.tm_year%100, ts.tm_mon,
               ts.tm_mday, ts.tm_hour, ts.tm_min, ts.tm_sec)

def _dbg(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def execLily(filename):
    lily = os.path.join(_LILYPATH, _LILYEXEC)
    lilyCall = "{} {}".format(lily, filename)
    print(lilyCall)
    #return os.system(lilyCall)
    return subprocess.call(lilyCall, shell=True)

def _testComposer(args, makepdf = False):
    USAGE = "python3 {} <configFile.ini> [outputFilename]".format(args[0])
    cfgFilename = None
    outputFilename = None
    if len(args) > 2:
        cfgFilename = args[1]
        outputFilename = args[2]
    elif len(args) > 1:
        cfgFilename = args[1]
    composer = Composer(cfgFilename, outputFilename)
    composer.writeAll()
    if makepdf:
        execLily(composer.outputFilename)

if __name__ == "__main__":
    import sys
    DEBUG = True
    argv = sys.argv
    _testComposer(argv, makepdf = True)



