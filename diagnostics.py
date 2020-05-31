#! /usr/bin/python3
# A short suite a diagnostic functions for pypond

import pypond
import composer

def prettyMeasure(measure, duration):
    """Returns a measure (a list of pypond.Note objects) in a nice intuitive text-based form."""
    blank = '|' + '-'*int(64*duration) + '|'
    nbeat = 0
    for note in measure:
        beat = note.getBeatNum()
        if beat == None:
            beat = nbeat
        dur = note.getDuration()
        index = 64*beat + 1
        blank = overwrite(blank, note._shortSummary(), index)
    return blank

def overwrite(sfrom, sto, index):
    """Return a copy of string 'sfrom' with 'sto' overwriting characters starting at index."""
    fi = int(index)
    lfrom = [x for x in sfrom]
    for n in range(len(sto)):
        if fi > len(lfrom) - 1:
            break
        lfrom[fi] = sto[n]
        fi += 1
    return ''.join(lfrom)

def _testPrettyMeasure(argv):
    USAGE = "python3 -m {}".format(argv[0])
    if len(argv) > 1:
        measure = []
        for arg in argv[1:]:
            measure.append(pypond.Note.fromLily(arg))
        measure = composer.Orchestrator._setBeatNums(measure)
        print(prettyMeasure(measure, 1))
    else:
        print(USAGE)



if __name__ == "__main__":
    import sys
    argv = sys.argv
    _testPrettyMeasure(argv)
