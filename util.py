#!/usr/bin/env python

import codecs
import csv

# These two classes were adopted from 
# https://docs.python.org/2/library/csv.html#examples
# UnicodeReader was slightly modified to return a DictReader
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")
        
class UnicodeReader(object):
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.DictReader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return {k: unicode(v, "utf-8") for (k, v) in row.iteritems()}

    def __iter__(self):
        return self

def colorise(text, color):
    return colorise_text_segment(text, 0, len(text), color)
    
def colorise_text_segment(text, start, end, color):
    ANSI_COLORS = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m"
    }
    if color not in ANSI_COLORS.keys():
        raise ValueError("Argument 'color' must be one of [" + ", ".join(ANSI_COLORS.keys()) + "]")
    s = ANSI_COLORS[color]
    e = "\033[0m"
    return text[:start] + s + text[start:end] + e + text[end:]
