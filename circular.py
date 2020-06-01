#!/usr/bin/python3

"""A circular list-like object for non-integral modulo arithmetic."""

class Circular():
    def __init__(self, array):
        if not hasattr(array, '__len__'):
            raise InitError("arg1 must be a list-like object (list, tuple, string).")
            self.array = []
            return
        self.array = array

    def __len__(self):
        return len(self.array)

    def __getitem__(self, index):
        if isinstance(index, int) or isinstance(index, float):
            index = self._internalIndex(index)
        return self.array[index]

    def __setitem__(self, key, value):
        if isinstance(key, int) or isinstance(key, float):
            key = self._internalIndex(key)
        self.array[key] = value

    def _internalIndex(self, index):
        """Get the internal index (ranging from 0 to len(self) - 1) corresponding to
        outward-facing index 'index' (which can range from -inf to +inf)."""
        index = int(index)
        l = len(self)
        while index > l - 1:
            index -= l
        while index < 0:
            index += l
        return index

    def __repr__(self):
        return repr(self.array)

    def index(self, val):
        """Return the index of the first value matching 'val' if found.
        Return None if 'val' not found in self."""
        for n in range(len(self.array)):
            if self.array[n] == val:
                return n
        return None

    def rindex(self, val):
        """Return the index of the first value matching 'val' if found, starting
        from the end and counting backwards.
        Return None if 'val' not found in self."""
        for n in range(len(self.array)-1, -1, -1):
            if self.array[n] == val:
                return n
        return None

    def rotate(self, n):
        """Rotate the underlying array by 'n' units (positive or negative)."""
        self.array = rotate(self.array, n)

def rotate(l, n):
    """Return a copy of list/yuple 'l' as a list rotated by increment 'n'
    Negative 'n' shifts everything to the right (0 -> 1, 1 -> 2, etc..., last -> 0)
    Positive 'n' shifts values left."""
    length = len(l)
    return [l[(n + m) % length] for m in range(length)]

def _testInternalIndex(argv):
    USAGE = "python3 {} length index"
    if len(argv) > 2:
        l = int(argv[1])
        n = int(argv[2])
        crc = Circular([0]*l)
        print("len(Circular) = {}; index {} yields {}".format(len(crc), n, crc._internalIndex(n)))
    else:
        print(USAGE)

def _testCircular(argv):
    if len(argv) > 1:
        array = [x.strip(',') for x in argv[1:]]
    else:
        array = []
        while True:
            try:
                query = input("Add item to Circular: ")
                if query == "":
                    break
                else:
                    array.append(query)
            except KeyboardInterrupt:
                print("Exiting...")
                return
    circ = Circular(array)
    while True:
        try:
            query = input("Get [g], set [s], print [p], or rotate [r]? ")
            if query == '':
                raise KeyboardInterrupt()
            if query.lower()[0] == 's':
                index = input("Index to set: ")
                if index == "":
                    index = 0
                else:
                    try:
                        index = int(index)
                    except TypeError:
                        print("Type Error!")
                        continue
                toSet = input("Set at {}: ".format(index))
                circ[index] = toSet
                print("Circular[{}] = {}".format(index, toSet))
            elif query.lower()[0] == 'g':
                index = input("Index to get: ")
                if index == "":
                    index = 0
                else:
                    try:
                        index = int(index)
                    except TypeError:
                        print("Type Error!")
                        continue
                print("Circular[{}] = {}".format(index, circ[index]))
            elif query.lower()[0] == 'p':
                print(circ)
            elif query.lower()[0] == 'r':
                amount = input("Rotate by: ")
                try:
                    amount = int(amount)
                except TypeError:
                    print("Type Error!")
                    continue
                circ.rotate(amount)
                print("Rotated by {}")
                print(circ)
        except KeyboardInterrupt:
            print("Exiting...")
            break

if __name__ == '__main__':
    import sys
    argv = sys.argv
    #_testInternalIndex(argv)
    _testCircular(argv)

