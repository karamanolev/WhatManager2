f = open('/Users/ivailo/Downloads/test_log.log', 'r')
d = f.read()

from .logfile import *
l = LogFile(d)
print(l.toc)
print()
print(l.tracks)
