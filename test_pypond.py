#!/usr/bin/python3

"""A test module for pypond.py"""

import pypond

ERR_ENCODING_MISMATCH = "Encoding Mismatch"
ERR_NOTESTRING_PARSING = "Error Parsing Notestring"
ERR_ACC_DECODE = "Error decoding accidental"
MSG_SUCCESS = "Success! All tests passed"

def testClassNote():
    failures = []
    def testIsEqualNote(note, encoding):
        fname = "testIsEqualNote"
        allPass = True
        # test note encoding
        noteEncoding = note.getEncoding()
        args = (ERR_ENCODING_MISMATCH, note, encoding)
        if noteEncoding != encoding:
            print("{} != {}".format(noteEncoding, encoding))
            failures.append((fname, args))
            return False

        # Split up encoding table into note that should match and those
        # that should not match
        encodingMatch = []
        encodingMismatch = []
        for enc in pypond._ENCODING_NOTES.keys():
            if pypond._ENCODING_NOTES[enc] == noteEncoding:
                encodingMatch.append(enc)
            else:
                encodingMismatch.append(enc)

        # test for True
        expectedResult = True
        for noteName in encodingMatch:
            result = note.isEqualNote(noteName)
            if result != expectedResult:
                args = (ERR_ENCODING_MISMATCH, note, noteName)
                failures.append((fname, args))
                allPass = False

        # test for False
        expectedResult = False
        for noteName in encodingMismatch:
            result = note.isEqualNote(noteName)
            if result != expectedResult:
                args = (ERR_ENCODING_MISMATCH, note, noteName)
                failures.append((fname, args))
                allPass = False

        return allPass

    def test_Note_Accidental_OctaveFromString(notestring, notename, accidental, octave):
        fname = "test_Note_Accidental_OctaveFromString"
        allPass = True
        tNoteName = pypond.Note._NoteNameFromString(notestring)
        tAccidental = pypond.Note._AccidentalFromString(notestring)
        tOctave = pypond.Note._OctaveFromString(notestring)
        if (tNoteName.lower() != notename.lower()) or (tAccidental != accidental) or (tOctave != octave):
            print("tNoteName = {}\tnotename = {}\ttAccidental = {}\taccidental = {}\ttOctave = {}\toctave = {}".format(
                  tNoteName, notename, tAccidental, accidental, tOctave, octave))
            args = (ERR_NOTESTRING_PARSING, notestring, tNoteName, tAccidental, tOctave)
            failures.append((fname, args))
            allPass = False
        return allPass

    def test_DecodeAccidentalString(intMin, intMax, charFlat, charSharp, charNatural):
        fname = "test_DecodeAccidentalString"
        allPass = True
        for n in range(intMin, intMax):
            if n < 0:
                accStr = charFlat*abs(n)
            elif n == 0:
                accStr = charNatural
            else:
                accStr = charSharp*abs(n)
            accInt = pypond.Note._DecodeAccidentalString(accStr)
            if accInt != n:
                args = (ERR_ACC_DECODE, accStr, accInt, n)
                failures.append((fname, args))

    validNotes = pypond._ENCODING_NOTES.keys()
    octaveStrings = ('', '0', '1', '2', '3', '4', '5', '6', '7', '8')
    for noteName in validNotes:
        if len(noteName) == 2:
            accidental = pypond.Note.encodingAccidentals.get(noteName[1], None)
        else:
            accidental = 0
        for octave in octaveStrings:
            tNoteName = noteName + octave
            tNote = pypond.Note(tNoteName)
            expectedEncoding = pypond._ENCODING_NOTES.get(noteName, None)
            #print("tNoteName = {}\texpectedEncoding = {}".format(tNoteName, expectedEncoding))
            testIsEqualNote(tNote, expectedEncoding)
            test_Note_Accidental_OctaveFromString(tNoteName, noteName, accidental, _intOctave(octave))

    # Test class and static methods
    test_DecodeAccidentalString(-12, 13, pypond.Note.flatChar, pypond.Note.sharpChar,
                                pypond.Note.naturalChar)
    return failures

def _intOctave(s):
    if s == "":
        return pypond._DEFAULT_OCTAVE
    else:
        return int(s)

def testAll():
    failures = testClassNote()
    if len(failures) == 0:
        print(MSG_SUCCESS)
    else:
        #pass
        printFailures(failures)

def printFailures(failures):
    for fail in failures:
        print(("{}" + "\t{}"*(len(fail[1]) - 1)).format(fail[0], *fail[1]))

if __name__ == "__main__":
    testAll()