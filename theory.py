#!/usr/bin/python3

import pypond, muse
import re

def _rotate(l, n):
    """Return a copy of list/yuple 'l' as a list rotated by increment 'n'
    Negative 'n' shifts everything to the right (0 -> 1, 1 -> 2, etc..., last -> 0)
    Positive 'n' shifts values left."""
    length = len(l)
    return [l[(n + m) % length] for m in range(length)]

class TheoryClass(object):
    CircleOfFifths  = ('c', 'g', 'd', 'a', 'e', 'b', 'f#', 'db', 'ab', 'eb', 'bb', 'f')
    OrderOfFlats    = ('b', 'e', 'a', 'd', 'g', 'c', 'f')
    SharpsMajor     = (1, 1, 1, 1, 1, 1, 0)
    SharpsMinor     = (1, 1, 1, 0, 0, 0, 0)
    fourthInterval  = 5 # 5 half-steps make a perfect fourth
    fifthInterval   = 7 # 7 half-steps make a perfect fifth
    _clefTreble     = 'treble'
    _reClefTreble   = re.compile("[Tt]((reble)|(REBLE))?$")
    _clefBass       = 'bass'
    _reClefBass     = re.compile("[Bb]((ass)|(ASS))?$")
    _clefAlto       = 'alto'
    _reClefAlto     = re.compile("[Aa]((lto)|(LTO))?$")
    _clefTenor      = 'tenor'
    _reClefTenor    = re.compile("[Tt]((enor)|(ENOR))$")
    _encodingClef   = {
        _clefTreble : 0,
        _clefBass   : 1,
        _clefAlto   : 2,
        _clefTenor  : 3
    }

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

    @classmethod
    def isSharpKey(cls, key):
        """Return True if 'key' is major and tonic has # or is : B, E, A, D, G, C
        If 'key' is minor or dim, returns True if tonic has a # or if tonic is B, E, A
        Does not handle double-flats"""
        flat  = pypond.Note.encodingAccidentals.get(pypond.Note.flatChar)
        sharp = pypond.Note.encodingAccidentals.get(pypond.Note.sharpChar)
        acc = key.getTonic().getAccidental()
        if acc == flat:
            return False
        elif acc == sharp:
            return True
        # If there is no accidental in the tonic name
        quality = key.getQuality()
        # These are my best guesses
        if quality == muse._KeyQuality.major:
            offset = 0
        elif quality == muse._KeyQuality.minor:
            offset = 3
        elif quality == muse._KeyQuality.dimwh:
            offset = 3
        elif quality == muse._KeyQuality.dimhw:
            offset = 3
        elif quality == muse._KeyQuality.chromatic:
            offset = 0
        elif quality == muse._KeyQuality.wholetone:
            offset = 0
        else:
            offset = 0
        noteName = key.getTonic().getNoteName().lower()
        l = len(cls.OrderOfFlats)
        #print("noteName = {}".format(noteName))
        index = cls.OrderOfFlats.index(noteName) + offset
        if (index < l) and (index >= 0):
            return cls.SharpsMajor[index]
        elif index < 0:
            return True
        else:
            return False

    @classmethod
    def _clefParser(cls, clefstring):
        """Parse clef string input and return the corresponding encoding"""
        if cls._reClefTreble.match(clefstring):
            clefstring = cls._clefTreble
        elif cls._reClefBass.match(clefstring):
            clefstring = cls._clefBass
        elif cls._reClefAlto.match(clefstring):
            clefstring = cls._clefAlto
        elif cls._reClefTenor.match(clefstring):
            clefstring = cls._clefTenor
        else:
            raise Error_ClefParser("Cannot parse clef string: {}".format(clefstring))
            return None
        return cls._encodingClef[clefstring]

    @classmethod
    def _getClefString(cls, clef):
        """Return the clef string corresponding to a particular clef integer"""
        for item in cls._encodingClef.items():
            if item[1] == clef:
                return item[0]
        return None

class Error_ClefParser(Exception):
    pass

def _testTheoryClass(args):
    pass

def _testRotate(args):
    USAGE = "python3 {0} <listObject> <rotateAmount>".format(args[0])
    if len(args) > 2:
        f = eval(argv[1])
        n = int(argv[2])
    else:
        print(USAGE)
        return
    print(_rotate(f, n))

if __name__ == "__main__":
    import sys
    argv = sys.argv
    _testTheoryClass(argv)



