#!/usr/bin/python3

# A python FIFO implementation
# Configurable depth and blocking.
# Indexable (i.e. fifo[n] returns the nth item waiting in the buffer)

class FIFO(object):
    def __init__(self, bufferDepth = 3, blockOnFull = True):
        """A simple FIFO implementation.
        bufferDepth = the number of items the buffer can hold
        blockOnFull = boolean
            if False: adds to a full buffer are accepted (returns True, last item deleted)
            if True: adds to a full buffer are rejected (returns False, item not added)"""
        self._depth = int(bufferDepth)
        self._blockOnFull = blockOnFull
        self._buffer = [None]*self._depth
        self._addPtr = 0
        self._getPtr = 0
        self._empty = True

    def add(self, item):
        """Add an item to the buffer.
        Blocking Buffer:
            if full, returns False
            else, returns True
        Non-blocking Buffer:
            always returns True
            if Full, the next item to 'get' will be forgotten (garbage-collected)"""
        # Check for full
        if self.isFull():
            if self._blockOnFull:
                return False
            else:
                # Increment (wrap) get pointer to 'forget' last item
                self._getPtr = (self._getPtr + 1) % self._depth
        self._buffer[self._addPtr] = item
        # Increment (wrap if necessary) add pointer
        self._addPtr = (self._addPtr + 1) % self._depth
        # It is now not empty
        self._empty = False
        return True

    def get(self):
        """Get the next item in the buffer.
        If empty, returns None
        Else, returns the item"""
        # Check for empty
        if self.isEmpty():
            return None
        # Fetch the item to return
        item = self._buffer[self._getPtr]
        # Increment (wrap if necessary) get pointer
        self._getPtr = (self._getPtr + 1) % self._depth
        # Now if pointers are equal, we must be empty
        if self._addPtr == self._getPtr:
            self._empty = True
        return item

    def isFull(self):
        """Return True if the buffer is full, else return False."""
        return (not self._empty) and (self._addPtr == self._getPtr)

    def isEmpty(self):
        """Return True if the buffer is empty, else return False."""
        return self._empty

    def getNumItems(self):
        """Get the number of items currently in the buffer.  Will always
        return a number between 0 and bufferDepth - 1"""
        if self.isFull():
            return self._depth
        else:
            return (self._addPtr + self._depth - self._getPtr) % self._depth

    def __getitem__(self, index):
        index = self._convertGetIndex(index)
        if index == None:
            return None
        return self._buffer[index]

    def __setitem__(self, key, value):
        """Note slicable in the current implementation"""
        try:
            key = int(key)
        except ValueError:
            raise TypeError("Buffer index must be an integer")
        print("key = {}".format(key))
        index = self._convertSetIndex(key)
        print("index = {}".format(index))
        if index == None:
            return False
        self._buffer[index] = value
        return True

    def _convertGetIndex(self, index):
        if index > self._depth - 1:
            raise IndexError("Buffer index out of range.")
            return None
        if index <= (self.getNumItems() - 1):
            index = (index + self._getPtr) % self._depth
            return index
        else:
            return None

    def _convertSetIndex(self, index):
        if index > self._depth - 1:
            raise IndexError("Buffer index out of range.")
            return None
        if index <= (self.getNumItems() - 1):
            index = (index + self._depth - 1 - self._getPtr) % self._depth
            return index
        else:
            return None

    def __str__(self):
        f = []
        for n in range(self.getNumItems()):
            f.append(str(self.__getitem__(n)))
        if len(f) == 0:
            return '[]'
        return '[' + ','.join(f) + ']'

    def __repr__(self):
        return self.__str__()

if __name__ == "__main__":
    blockOnFull = input("Block FIFO on full buffer [T/F]: ?")
    if blockOnFull.lower()[0] == 'f':
        blockOnFull = False
        print("Shift on full buffer.")
    else:
        blockOnFull = True
        print("Block on full buffer.")
    
    fifo = FIFO(3, blockOnFull)
    while True:
        try:
            query = input("Add [a], get [g], or index[i]? ")
            if query.lower()[0] == 'a':
                toAdd = input("String to add: ")
                result = fifo.add(toAdd)
                print("Result: {}".format(result))
            elif query.lower()[0] == 'g':
                result = fifo.get()
                if result == None:
                    print("Buffer is empty")
                else:
                    print("Got: {}".format(result))
            elif query.lower()[0] == 'i':
                while True:
                    index = input("Index: ")
                    try:
                        index = int(index)
                        break
                    except ValueError:
                        print("Index must be an integer")
                print("fifo[{}] = {}".format(index, fifo[index]))
        except KeyboardInterrupt:
            print("Exiting...")
            break


