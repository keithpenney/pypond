#!/usr/bin/python3

"""A python script to generate GNU lilypad sheet music from muse.py and pypond.py"""
# Lilypond path: C:\Program Files (x86)\LilyPond\usr\bin

# TODO! Keep track of the beats in the measure and break up a single note into two notes
# tied together across a barline when necessary.
# TODO! Compose a given number of measures, not notes.

# TODO Dotted notes need to know when to break across measures

import os, subprocess
import muse, pypond, theory, fifo
import time

DEBUG = False

# Change the below to match the install path of GNU Lilypond on your system
_LILYPATH = "\"C:/Program Files (x86)/LilyPond/usr/bin\""
# If using Windows, this should be "lilypond.exe"; if using MacOS/Linux, it should simply be "lilypond"
_LILYEXEC = "lilypond.exe"

class Composer():
    headerString = pypond.LilySyntax.headerString
    footerString = pypond.LilySyntax.footerString
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
        self.initBuffer()
        self.finished = False       # Terminates the composition process

    def initBuffer(self, bufferDepth = 3):
        self._buffer = fifo.FIFO(int(bufferDepth), blockOnFull = False)

    def inspectBuffer(self, index):
        return self._buffer[index]

    def addToBuffer(self, item):
        return self._buffer.add(item)

    def getFromBuffer(self):
        return self._buffer.get()

    def getNextNoteLilyOLD(self):
        return self.algorithm.getNextNoteLily()

    def getNextNoteLily(self):
        #tiesymbol = pypond._LILYTIE
        startBeat = self.beatCount
        note = self.algorithm.getNextNote()
        notes, beats = self.splitAtMeasures(note)  # modifies self.beatCount
        for n in range(len(notes)):
            self.addToBuffer((notes[n], beats[n]))
        #print(self._buffer)
        
        slist = [notes[n].asLily(beats[n]) for n in range(len(notes))]
        if len(slist) > 1:
            for n in range(len(slist) - 1):
                slist[n] += pypond.Note._lilyTie
        return slist
        """
        if len(notes) > 1:
            return (notes[0].asLily(startBeat) + notes[0]._lilyTie, notes[1].asLily())
        else:
            return (notes[0].asLily(startBeat),)      # TODO Handle ties in GNU lilypond format
        """
        
        #return (x.asLily(self.beatCount) for x in notes)

    def splitAtMeasuresOLD(self, note):
        """Feel free to delete this"""
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

    def splitAtMeasures(self, note):
        """Let's try to accomodate the case of notes spanning more than two measures."""
        noteLength = note.getDuration()
        _dbg("=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=")
        _dbg("beatCount = {}; noteLength = {}; measureCount = {}".format(
             self.beatCount, noteLength, self.measureCount))
        noteDurations = []
        alignBeats = [self.beatCount]
        while self.beatCount + noteLength >= self.measureDuration:  # If the note would continue beyond the bar
            tempDur = self.measureDuration - self.beatCount         # Pop off the duration to fill the measure
            noteLength -= tempDur                                   # Subtract that duration from the previous
            noteDurations.append(tempDur)                           # and add it to the list
            self.measureCount += 1                                  # Increment the measure count
            if self.measureCount == self.numMeasures:               # If we hit the max measures
                self.finished = True                                # terminate the composition
                break                                               # and quit tallying up notes
            self.beatCount = 0                                      # And reset the beat count
            alignBeats.append(self.beatCount)
        if not self.finished and noteLength != 0:
            if self.beatCount + noteLength < self.measureDuration:      # If the note won't span the bar
                noteDurations.append(noteLength)                        # Append the full duration to the list
                self.beatCount += noteLength                            # And update the beat count
                alignBeats.append(self.beatCount)

        noteList = []
        for n in range(len(noteDurations)):
            newnote = note.copy()
            newnote.setDuration(noteDurations[n])
            noteList.append(newnote)
        _dbg("noteDurations = {}".format(noteDurations))
        return (noteList, alignBeats)

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

    def writeClefKeyTime(self, fd = None):
        """Write the introductory clef, key, and time signature"""
        clefstring = self.getClefLily()
        keystring = self.getKeyLily()
        timestring = self.getTimeSignatureLily()
        outstring = clefstring + keystring + timestring
        self.writeString(outstring, fd)

    def getClefLily(self):
        """Get the clef command in GNU Lilypond format"""
        WHITESPACE = 4*" "
        clef =  self.config.get('clef')
        if clef == None:
            return ""
        clefstring = theory.TheoryClass._getClefString(clef)
        if clefstring == None:
            return ""
        return "{}{} {}\n".format(WHITESPACE, pypond.LilySyntax.kwClef, clefstring)

    def getKeyLily(self):
        """Get the key signature command in GNU Lilypond format"""
        WHITESPACE = 4*" "
        key = self.config.get('key', None)
        if key == None:
            return ""
        keyString = key.getKeyLily()
        if keyString == None:
            return ""
        return "{}{} {}\n".format(WHITESPACE, pypond.LilySyntax.kwKey, keyString)

    def getTimeSignatureLily(self):
        """Get the time signature command in GNU Lilypond format"""
        WHITESPACE = 4*" "
        time = self.config.get('timeSignature', None)
        if time == None:
            return ""
        timeString = time.asLily()
        if timeString == None:
            return ""
        return "{}{} {}\n".format(WHITESPACE, pypond.LilySyntax.kwTimeSignature, timeString)

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
        self.writeClefKeyTime(fd)
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



