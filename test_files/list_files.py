from os import walk

mypath = "/home/pi/memories/"
f = []
for (dirpath, dirnames, filenames) in walk(mypath):
    f.extend(filenames)
    break
print f