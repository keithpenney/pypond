#!/usr/bin/python3

"""Add to config script"""

import configparser

DEFAULT_OUTFILENAME = "cfgtext.txt"
DEFAULT_INFILENAME = "cfg.ini"
WHITESPACE = "        "
CONFIG_NAME = "config"

def printCode(infilename, outfilename = None):
    config = configparser.ConfigParser()
    config.read(infilename)
    if outfilename == None:
        fd = None
    else:
        try:
            fd = open(outfilename, 'w')
        except IOError:
            print("Cannot open filename {}".format(outfilename))
    if len(config) == 0:
        _print("Cannot open filename {}".format(infilename))
        return False
    for section in config.keys():
        _print(fd, "{}#[{}]".format(WHITESPACE, section))
        for key in config[section].keys():
            _print(fd, "{}self.{} = {}.get('{}', None)".format(WHITESPACE, key, CONFIG_NAME, key))


def _print(fd = None, *args, **kwargs):
    if fd != None:
        print(*args, **kwargs, file = fd)
    else:
        print(*args, **kwargs)

if __name__ == "__main__":
    import sys
    args = sys.argv
    USAGE = "python3 {} <input.ini> <output.txt>".format(args[0])
    if len(args) > 2:
        infilename = args[1]
        outfilename = args[2]
    elif len(args) > 1:
        infilename = args[1]
        outfilename = None
    else:
        print(USAGE)
        sys.exit(1)
    if infilename == '*':
        infilename = DEFAULT_INFILENAME
    if outfilename == '*':
        outfilename = DEFAULT_OUTFILENAME
    printCode(infilename, outfilename)

