#!/usr/bin/python3

"""A python script to generate GNU lilypad sheet music from muse.py and pypond.py"""

import os, subprocess
import muse, pypond, theory, fifo, diagnostics
import time

DEBUG = False
LOGFILE = None
FILENAME = "composer.py"

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
        self.numMeasures = self.config.get('numMeasures')
        self.measureCount = 0
        self.beatCount = 0
        self.measureDuration = self.config.getMeasureDuration()
        self.homeKey = self.config.get('key', None)         # The key signature of the sheet music
        #print("self.measureDuration = {}".format(self.measureDuration))
        self.precision = self.config.get('shortestNote', 1/64)
        self.initBuffer(self.measureDuration, self.precision)
        self.finished = False       # Terminates the composition process

    def initBuffer(self, measureDuration, precision = 1/64):
        """Initialize the MeasureBuffer with a measure duration and minimum note
        duration that will need to be contained in the buffer."""
        self._buffer = MeasureBuffer(measureDuration, precision)

    def inspectBuffer(self, index):
        return self._buffer.inspectBuffer(index)

    def isMeasureFull(self):
        return self._buffer.isMeasureFull()

    def addNoteToBuffer(self, note):
        """Returns None if measureBuffer is full.
        Returns the remainder note if the measure buffer overflowed.
        If measure buffer did not overflow,
            returns True if the measure became full.
            returns False if there is still room in the measure."""
        response = self._buffer.add(note)
        if response == None:
            # Either we gave it an invalid note or the buffer is full
            if self.isMeasureFull():
                return None
            else:
                raise Error_Note("Composer.addNoteToBuffer() {} might not be a note.".format(note))
        else:
            return response

    def getMeasureFromBuffer(self):
        """Returns the measure in the buffer and whether the measure was full before extracting
        the buffer contents."""
        #print("Getting measure")
        full = self.isMeasureFull()
        measure = self._buffer.getMeasure()
        return (measure, full)

    #@DEPRECATED!
    def getNextNoteLilyOLD(self):
        return self.algorithm.getNextNoteLily()

    def compose(self):
        """Returns a formatted measure string (in GNU Lilypond format) after each measure
        is completed.  Returns None if we're mid-measure (no new measure is ready).
        Sets self.finished = True when we reach the measure count."""
        #print("- - - - compose - - - -")
        # Get the next note from the algorithm
        note = self.algorithm.getNextNote()
        # Associate the beat number with the note
        note.setBeatNum(self.beatCount)
        # Increment the beat number
        self.beatCount += note.getDuration()
        # Add to the measure buffer
        again = True
        measureStrings = [] 
        while again:
            again = False
            response = self.addNoteToBuffer(note)
            #print("        response = {}".format(response))
            if response:    # Measure is ready for orchestration
                tieLastNote = False
                self.beatCount = 0                      # Reset the beat number
                measure, isfull = self.getMeasureFromBuffer()
                if not isfull:
                    _dbg("WARNING: Measure number {} is not full!".format(self.measureCount))
                self.measureCount += 1
                if self.measureCount == self.numMeasures:   # If we've made our last measure, let's exit
                    self.finished = True
                elif hasattr(response, 'getDuration'):  # If there was a remainder note
                    tieLastNote = True
                    #self.addNoteToBuffer(response)      # Add it to the buffer
                    note = response                     # Register the response to be the new note for the next round
                    self.beatCount += response.getDuration()    # Add the remainder duration to the beat number
                    again = True
                #print(diagnostics.prettyMeasure(measure, self.measureDuration))
                measureStrings.append(self.processMeasure(measure, tieLastNote))
        if len(measureStrings) == 0:
            return None
        return ' '.join(measureStrings)

    def processMeasure(self, measure, tieLastNote = False):
        """Send a measure to the Orchestrator.  Get a formatted measure back, and
        return it."""
        print("measure #{}".format(self.measureCount))
        return Orchestrator.processMeasure(measure, tieLastNote, homeKey = self.homeKey)

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
        lineMeasureCount = 0
        measuresPerLine = 4
        indent = "    "
        #notes = []
        self.writeString("\n", fd)
        while not self.finished:
            formattedMeasure = self.compose()
            if formattedMeasure != None:
                self.writeString(indent + formattedMeasure, fd)
                if lineMeasureCount == measuresPerLine - 1:
                    lineMeasureCount = 0
                    #self.writeString("\n", fd)
                    self.writeString("    % Measure {}\n".format(self.measureCount), fd)
                else:
                    lineMeasureCount += 1
        self.writeString("\n", fd)
        """
            for note in nextNotes:
                notes.append(note)
                if wordcount == wordsperline:
                    wordcount = 0
                    notes.append('\n\r  ')
                else:
                    wordcount += 1
        # Flush out the remainder of the buffer
        lastNotes = self.flushBuffer()
        for note in lastNotes:
            notes.append(note)
        notestring = " ".join(notes)
        self.writeString(notestring, fd)
        """

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

class Orchestrator():
    """The composer does the work of grabbing notes from the algorithm and chopping
    them up at measure (bar) lines, but does no formatting.  The composer passes Note objects
    (and/or Rest objects) to the Orchestrator in single-measure chunks, with each Note already
    associated with its beat in the measure.  It is then the Orchestrator's job to format
    the measure according to common notation standards and practice, and then hand the formatted
    measure string back to the composer to write it to the output file (and take credit for it)."""
    def __init__(self):
        pass

    @classmethod
    def processMeasure(cls, measure, tieLastNote = False, homeKey = None):
        """Multi-pass algorithm:
        1. Combine adjacent rests.
        2. Replace notes with more appropriate enharmonic equivalents when necessary
        3. Replace notes with lists of tied notes from self.decomposeNotes
        4. Flatten note list and join into Lilypond-formatted string.
        5. Return string to caller.

        'homeKey' is the key that is in use at the top of the piece (see cfg).
        """
        if not isinstance(homeKey, muse.Key):
            try:
                homeKey = muse.Key(homeKey)
            except Exception as e:
                print(e)
                homeKey = None
        measure = cls.combineRests(measure)
        #measure = cls.optimizeEnharmonics(measure, homeKey)
        measure = cls.expand(measure)
        return cls.stringify(measure, tieLast = tieLastNote)

    @classmethod
    def combineRests(cls, measure):
        """Step through the list of pypond.Notes making up a measure. If the note is
        a rest and the next note is also a rest, replace the first with a new rest
        with a duration the sum of the two. Delete the second rest.
        """
        # We need a separate index which gets decremented whenever we combine/delete
        # a rest so we can continue to combine if there are further rests.
        m = 0
        for n in range(len(measure)):
            #print('n = {}; m = {}, len = {}'.format(n, m, len(measure)))
            if  measure[m].isRest():
                if m < len(measure) - 1:
                    if measure[m+1].isRest():
                        measure[m] += measure[m+1]  # Combine
                        del measure[m+1]            # Remove 2nd note
                        m -= 1
            m += 1
        return measure

    @classmethod
    def optimizeEnharmonics(cls, measure, key = None):
        """For each note in the measure, determine the best enharmonic equivalent
        for this particular case."""
        if key == None:
            # Could also try to filter out double-sharps and double-flats
            return measure
        for n in range(len(measure)):
            measure[n] = key.getBestEnharmonic(measure[n])
        return measure

    @classmethod
    def expand(cls, measure):
        """Replace each note with a list of tied basis notes if needed, returning
        the expanded (nested-list) measure."""
        for n in range(len(measure)):
            measure[n] = cls.decomposeNote(measure[n])
        return measure

    @classmethod
    def stringify(cls, measure, tieLast = False):
        """Assume measure is nested-list.  Flatten it first, then convert each note
        in the measure to a string in GNU Lilypond format, concatenate the strings
        in order, and return the resulting string."""
        measure = cls._flattenList(measure, depth = 1)
        if tieLast:
            if hasattr(measure[-1], 'setTie'):
                measure[-1].setTie(True)
        for n in range(len(measure)):
            if hasattr(measure[n], 'asLily'):
                measure[n] = measure[n].asLily()
            else:
                measure[n] = ''
        return ' '.join(measure)

    @classmethod
    def decomposeNote(cls, note):
        """First parse the alignBeat, then walk from LS-to-MS through the alignBeat parse
        and 'fill in the holes' taking from the note duration.  Once the beat has rounded
        out to all zeros (an even multiple of whole notes), walk down MS-to-LS the remaining
        note duration parse.

        On the first pass (LS-to-MS), we don't need to worry about dotting notes.

        Returns a list of notes representing input 'note' decomposed into unit notes
        (2**(-n)) with beats and ties set accordingly."""
        alignBeat = note.getBeatNum()
        if alignBeat == None:
            return (note)
        duration = note.getDuration()
        nBeats = cls.parseBeat(alignBeat)
        #print("0:\t{:.4f}\t{:.4f}\t{}".format(alignBeat, duration, nBeats))
        notelist = []
        for n in range(len(nBeats)):    # Walk the beat parse
            if nBeats[-(n+1)]:          # (LS-to-MS)
                index = len(nBeats) - (n + 1)
                ddur = 2**(-index)      # We need to borrow this delta-duration from the note if possible
                if duration >= ddur:
                    duration -= ddur
                    newNote = note.copy()
                    newNote.setDuration(ddur)
                    newNote.setBeatNum(alignBeat)
                    notelist.append(newNote)
                    alignBeat += ddur   # Give that duration to the alignBeat
                    nBeats = cls.parseBeat(alignBeat)    # then parse the beat again
                    #print("{}:\t{:.4f}\t{:.4f}\t{}".format(n+1, alignBeat, duration, nBeats))
        # Now we walk down the parsed remainder of the note duration
        nNotes = cls.parseBeat(duration)
        #print("X:\t{:.4f}\t{:.4f}\t{}".format(alignBeat, duration, nNotes))
        candot = False                  # Note dotting
        for n in range(len(nNotes)):    # Walk through the breakdown of the note duration, starting from whole notes
            if nNotes[n] > 0:           # If a duration exists,
                if candot:              # If the last duration exists, we can dot it!
                    candot = False      # Then we turn off dotting so we don't end up with double-dots
                    notelist[-1].setDot(True) # (those are silly)
                else:
                    candot = True       # The next note can be a dot if present
                    dur = 2**(-n)  # 4 for quarter note, 8 for eighth note, etc...
                    newNote = note.copy()
                    newNote.setDuration(dur)
                    newNote.setBeatNum(alignBeat)
                    notelist.append(newNote)
                    alignBeat += dur
            else:
                candot = False          # The next note cannot be a dot
        if len(notelist) > 1:           # If results in more than one note
            for n in range(len(notelist)-1):  # Set the tie for all but the last
                notelist[n].setTie(True)
        return notelist

    @staticmethod
    def parseBeat(duration):
        """Returns [n1, n2, n4, n8, n16, n32, n64] where nX is (either 0 or 1)
        the number of the 'X'th unit duration in the decomposition of
        'duration'.  The 'X'th unit duration means, e.g.:
            2nd = 1/2 = half note
            16th = 1/16 = sixteenth note
            etc...
        """
        return [int(x) for x in "{:07b}".format(int(duration*64))]

    @staticmethod
    def _flattenList(l, depth = 1):
        if not hasattr(l, '__len__'):
            return l
        n = 0
        passes = 0
        while True:
            while True:
                if hasattr(l[n], '__len__'):        # If the nth member is a list-like object
                    todel = n
                    for m in range(len(l[todel])):
                        l.insert(1+todel+m, l[todel][m])
                        n += 1
                    del l[todel]
                    n -= 1
                n += 1
                if n >= len(l):
                    break
            n = 0
            passes += 1
            if passes == depth:
                break
        return l

    @staticmethod
    def _setBeatNums(measure):
        beat = 0
        for n in range(len(measure)):
            measure[n].setBeatNum(beat)
            beat += measure[n].getDuration()
        return measure

    @staticmethod
    def _printMeasure(measure):
        print(diagnostics.prettyMeasure(measure, self.measureDuration))

def _dbg(*args, **kwargs):
    if DEBUG:
        if LOGFILE != None:
            print("[{}]\t".format(FILENAME), file = LOGFILE, end = '')
            print(*args, **kwargs, file = LOGFILE)

class MeasureBuffer():
    def __init__(self, measureDuration, precision = 1/64):
        self.measureDuration = measureDuration
        self.precision = precision
        self.fifoDepth = int(measureDuration/precision + 1)
        self.fifo = self.initBuffer(self.fifoDepth)
        self.total = 0

    def add(self, note):
        """Add a note to the measure.
        Returns a note representing the remainder if adding causes a
        measure overflow.
        Returns False if no overflow occurred and measure has room left.
        Returns True if no overflow occurred and measure is full.
        Returns None if measure is full.
        Returns None if 'note' doesn't have a 'getDuration' attribute.
        """
        #print("+ + + + Add + + + +")
        #print("Measure Full? {}".format(self.isMeasureFull()))
        #print("total = {}\tAdding {}{}".format(self.total, note.getNoteName(),
        #   note.getDurationDecomposed(reciprocal = False)))
        if hasattr(note, 'getDuration'):
            duration = note.getDuration()
        else:
            return None
        if self.isMeasureFull():
            return None
        newTotal = self.total + duration
        if newTotal > self.measureDuration:         # If adding the note will overflow the measure
            newDuration = self.measureDuration - self.total # Add only enough duration to fill the measure
            note.setDuration(newDuration)           # Shorten the note
            self.addToBuffer(note)                  # Then add it to the buffer
            remainder = newTotal - self.measureDuration # The remainder of the note will go to a new note
            #print("@Overflow; {} - {} = {}".format(newTotal, self.measureDuration, remainder))
            reNote = note.copy()                    # Copy so we get the same pitch
            reNote.setDuration(remainder)           # Then set the duration
            self.total += newDuration               # Add the new duration to the total
            return reNote                           # And return the new remainder note
        else:                                       # If the note will fit without overflowing the measure
            self.addToBuffer(note)                  # Add the full note
            self.total = newTotal                   # And update the total
            #print("@Non-overflow; total = {}; measDur = {}; isMeasureFull? {}".format(
            #   self.total, self.measureDuration, self.isMeasureFull()))
            if self.isMeasureFull():                # Check again to see if the measure is now full
                #print("returning True")
                return True                         # If so, return True
            else:
                return False                        # If not, return False

    def getMeasure(self):
        """Empty the FIFO and return the resulting measure's worth of notes as a list."""
        notes = []
        while True:
            note = self.getFromBuffer()
            if note == None:    # FIFO is empty
                break
            self.total -= note.getDuration()
            notes.append(note)
        #print("getMeasure() nNotes = {}\tlen(buffer) = {}".format(len(notes),
        #      self.getNumBufferItems()))
        #print("&&&&&&&&&&&&&&&&&&&&& total = {}".format(self.total))
        return notes

    def isMeasureFull(self):
        return self.total == self.measureDuration

    def initBuffer(self, bufferDepth = 8):
        return fifo.FIFO(int(bufferDepth), blockOnFull = False)

    def inspectBuffer(self, index):
        return self.fifo[index]

    def bufferItemReplace(self, index, newitem):
        if abs(index) < self.getNumBufferItems():
            self.fifo[index] = newitem
            return True
        return False

    def addToBuffer(self, item):
        return self.fifo.add(item)

    def getFromBuffer(self):
        return self.fifo.get()

    def getNumBufferItems(self):
        return len(self.fifo)
    

class LogFile():
    def __init__(self, filename = None):
        self.filename = filename
        self._new = True
        self.fd = None
    
    def write(self, s):
        if self.open():
            self.fd.write(s)
            self.close()
            return
        print(s)

    def open(self):
        """The first time this is called after instantiating this class,
        the filename is opened for writing (to overwrite the previous log file).
        Each subsequent time, the file is opened in append mode.
        The file is opened before and closed after each write so the program
        is free to crash whenever it wants."""
        try:
            if self._new:
                wa = 'w'
            else:
                wa = 'a'
            self.fd = open(self.filename, wa)
            self._new = False
        except IOError:
            print("Cannot open file {}".format(self.filename))
            return False
        return True

    def close(self):
        if self.fd != None:
            if hasattr(self.fd, 'close'):
                self.fd.close()

class Error_Note(Exception):
    pass

def execLily(filename):
    lily = os.path.join(_LILYPATH, _LILYEXEC)
    lilyCall = "{} {}".format(lily, filename)
    print(lilyCall)
    #return os.system(lilyCall)
    return subprocess.call(lilyCall, shell=True)

def _testComposer(args):
    USAGE = "python3 {} <configFile.ini> [outputFilename] [-x]\n\
             -x : Do not call GNU Lilypond (don't generate PDF)".format(args[0])
    cfgFilename = None
    outputFilename = None
    if len(args) > 2:
        cfgFilename = args[1]
        outputFilename = args[2]
    elif len(args) > 1:
        cfgFilename = args[1]
    if '-x' in args:
        makepdf = False
    else:
        makepdf = True
    composer = Composer(cfgFilename, outputFilename)
    composer.writeAll()
    if makepdf:
        execLily(composer.outputFilename)

def _testOrchestratorDecomposeNote(args):
    USAGE = "python3 {} <noteDuration> [beat]".format(args[0])
    if len(args) > 1:
        duration = eval(args[1])
    else:
        print(USAGE)
        return
    if len(args) > 2:
        beat = eval(args[2])
    else:
        beat = 0
    note = pypond.Note("C4", duration)
    note.setBeatNum(beat)
    noteList = Orchestrator.decomposeNote(note)
    print("Name\tBeat\tDuration")
    for note in noteList:
        print("{}\t{:.4f}\t{:.4f}".format(note.getNoteName(), note.getBeatNum(), note.getDuration()))
    return

def _testOrchestratorCombineRests(args):
    USAGE = "python3 {}".format(args[0])
    testMeasure = [None]*6
    for n in range(len(testMeasure)):
        testMeasure[n] = pypond.Rest(1/8)
    testMeasure[3] = pypond.Note("C4")
    testMeasure[3].setDuration(1/8 + 1/4)
    def setBeatNums(measure):
        beat = 0
        for n in range(len(measure)):
            measure[n].setBeatNum(beat)
            beat += measure[n].getDuration()
        return measure
    testMeasure = setBeatNums(testMeasure)
    def printMeasure(measure):
        print("Note\tBeat\tDuration")
        for note in measure:
            print("{}\t{:.4f}\t{:.4f}".format(note.getNoteName(),
                  note.getBeatNum(), note.getDuration()))
    printMeasure(testMeasure)
    testMeasure = Orchestrator.combineRests(testMeasure)
    printMeasure(testMeasure)
    return

def _testOrchestratorFlattenList(args):
    l = [0, 1, 2, [3, [4, 5], 6, 7], 8, 9, [10, 11], [12]]
    print(l)
    l = Orchestrator._flattenList(l,2)
    print(l)
    return

def _testOrchestratorStringify(args):
    measure = [pypond.Note('C4', 1/4), [pypond.Rest(1/8), pypond.Rest(1/4)],
               pypond.Note('Eb3', 1/2)]
    lilystring = Orchestrator.stringify(measure, tieLast = True)
    print(lilystring)

def _testOrchestratorProcessMeasure(args):
    USAGE = "python3 {} <lilyNote> ...".format(args[0])
    if len(args) > 1:
        measure = []
        for arg in args[1:]:
            measure.append(pypond.Note.fromLily(arg))
        measure = Orchestrator._setBeatNums(measure)
        Orchestrator._printMeasure(measure)
        lilystring = Orchestrator.processMeasure(measure)
        print(lilystring)
    else:
        print(USAGE)

if __name__ == "__main__":
    import sys
    DEBUG = True
    LOGFILE = LogFile("dbg.log")
    FILENAME = sys.argv[0]
    muse.LOGFILE = LOGFILE
    pypond.LOGFILE = LOGFILE
    argv = sys.argv
    _testComposer(argv)
    #_testOrchestratorDecomposeNote(argv)
    #_testOrchestratorCombineRests(argv)
    #_testOrchestratorFlattenList(argv)
    #_testOrchestratorStringify(argv)
    #_testOrchestratorProcessMeasure(argv)

