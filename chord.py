#!/usr/bin/python3

# Class Chord(): implements an array of pypond.Note() objects which sound simultaneously
#                (i.e. have the same duration and beat number).

import pypond

class Chord(pypond.Note):
    def __init__(self, notes = [], duration = None, beatNum = 0):
        super().__init__("C")   # A rando notestring. Need to create new 'RhythmElement' superclass
        self.notes = notes
        duration = self._setAttr('duration', duration, 'getDuration')
        if duration != None:
            self.setAllDurations(duration)
        beatNum = self._setAttr('beatNum', beatNum, 'getBeatNum')
        if beatNum != None:
            self.setAllBeatNums(beatNum)

    def _setAttr(self, attrString, attrVal, getter = None):
        #print("setting attribute {} to {}".format(attrString, attrVal))
        if attrVal != None:
            setattr(self, attrString, attrVal)
        else:
            if len(notes) > 0:
                if hasattr(notes[0], getter):
                    attrVal = getattr(notes[0], getter)()
                    if attrVal != None:
                        setattr(self, attrString, attrVal)
        if attrVal == None:
            print("No value determined for attribute {}".format(attrString))
        #print("self.{} = {}".format(attrString, getattr(self, attrString)))
        return attrVal

    def setAllDurations(self, duration):
        """Set the duration of all notes in chord to 'duration'
        Returns True if all items in self.notes have a 'setDuration' method.
        Returns False otherwise."""
        allgood = True
        for note in self.notes:
            if hasattr(note, 'setDuration'):
                note.setDuration(duration)
            else:
                print("{} has no attribute setDuration".format(note))
                allgood = False
        return allgood

    def setAllBeatNums(self, beatNum):
        """Set the beat number for all notes in chord to 'beatNum'
        Returns True if all items in self.notes have a 'setDuration' method.
        Returns False otherwise."""
        allgood = True
        for note in self.notes:
            if hasattr(note, 'setBeatNum'):
                note.setBeatNum(beatNum)
            else:
                print("{} has no attribute setBeatNum".format(note))
                allgood = False
        return allgood

    def getDuration(self):
        return self.duration

    def getBeatNum(self):
        return self.beatNum

    def setDuration(self, duration):
        dur = pypond._float(duration)
        if dur == None:
            raise pypond.Error_Float("Cannot interpret duration {}".format(duration))
            return False
        else:
            self.duration = dur
            self.setAllDurations(dur)
            return True

    def setBeatNum(self, beatNum):
        nbeat = pypond._float(beatNum)
        if nbeat == None:
            raise pypond.Error_Float("Cannot interpret beatNum {}".format(beatNum))
            return False
        else:
            self.beatNum = nbeat
            self.setAllBeatNums(nbeat)
            return True

    def asLily(self):
        """Return a string representation of the chord in GNU Lilypond format"""
        # <c e g>8.~
        noteNames = []
        for note in self.notes:
            s = note.getNoteName()[0].lower() + note._getLilyAccidental() + note._getLilyOctave()
            noteNames.append(s)
        notestring = "<" + " ".join(noteNames) + ">"
        d = self._getLilyDuration()
        s = self._getLilyDot()
        t = self._getLilyTie()
        return "{}{}{}{}".format(notestring, d, s, t)

def testChord(argv):
    USAGE = "python3 {} [-d duration] [-t] [-o] note0 note1 note2..."
    dot = False
    tie = False
    duration = 1
    nextDur = False
    notestrings = []
    if len(argv) > 1:
        for arg in argv[1:]:
            if arg == '-d':
                nextDur = True
            elif arg == '-t':
                tie = True
            elif arg == '-o':
                dot = True
            else:
                if nextDur:
                    duration = pypond._float(arg)
                    nextDur = False
                else:
                    notestrings.append(arg)
    else:
        print(USAGE)
        return
    if len(notestrings) == 0:
        notestrings = ['C', 'E', 'G']
    notes = [pypond.Note(x) for x in notestrings]
    chord = Chord(notes, duration)
    if tie:
        chord.setTie(True)
    if dot:
        chord.setDot(True)
    print(chord.asLily())
    return

if __name__ == '__main__':
    import sys
    argv = sys.argv
    testChord(argv)

