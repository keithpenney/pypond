# pypond
## An overly ambitious pet project to generate sheet music algorithmically

**In baby development stage! - most everything is broken; don't try to use it unless you love to hurt**
_Disclaimer: all this is subject to change at my very whim during baby development_

### How to install:
1. Install Python 3 [https://www.python.org]
  1.a. (latest version is fine, though I'm developing on 3.6ish)
2. Install GNU Lilypond [https://lilypond.org]
3. Copy/clone this repository to some handy location on your computer.
   [Github How-to](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository)

### How to make it go:
1. **composer.py** is the main event.  Until I make it more elegant, you need to modify a few variables
   at the top of this file.
```python
# composer.py
# Change the below to match the install path of GNU Lilypond on your system
_LILYPATH = "\"C:/Program Files (x86)/LilyPond/usr/bin\""
# If using Windows, this should be "lilypond.exe"; if using MacOS/Linux, it should simply be "lilypond"
_LILYEXEC = "lilypond.exe"
```
2. _(optional)_ Create your own configuration file.  Copy _cfg.ini_ to another file and modify the values
   (if you **dare**!).
3. Open a terminal (this is command-line only at the moment) and navigate to the directory where you
   extracted/cloned/copied the _pypond_ repository (e.g. _C:\repos\pypond_ or _/home/me/pypond_)
4. Run **composer.py**, passing your prepared configuration file or _cfg.ini_, like this:
`python3 composer.py cfg.ini` on MacOS/Linux or `py -3 composer.py cfg.ini` on Windows.
5. If everything worked (fat chance), two new files are generated and auto-named based on the chosen
   melody algorithm and the timestamp.  One has the extension `.ly` and is GNU Lilypond language script,
   and the other has the extension `.pdf` and is a pdf which pdfs when you pdf it.
6. If you hate the auto-naming, you can pass a name to **composer.py** as such:
   `python3 composer.py cfg.ini this_name_is_my_favorite` (note the lack of spaces or a file extension)

### Known bugs/wackiness to work out:

- Rhythms are still often written in a non-standard manner; that logic is surprisingly difficult.
- In low-density music, rests are not combined and will look stupid.  This requires some type of lookback
  logic (and that's a whole big thing).
- The internal structure is a bit of a mess - need to have clear division of labor, reduce passing references
  up and down the inheritance chain.
- muse.Key.getNotes() still returns wrong enharmonic equivalents for keys like "C#Maj" or "Fd"

### Unimplemented - TODO (hopefully)

- Add key awareness, complete with choosing the correct enharmonic equivalent.
- Implement the circle of fifths; changing keys by interval or by traversing the circle.
- Polyphony!
- Lots of new algorithms...

Cheers,
Keith