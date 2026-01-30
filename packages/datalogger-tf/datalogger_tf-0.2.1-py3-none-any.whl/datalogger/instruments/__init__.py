import os
from os import listdir
from os.path import dirname

os.chdir(dirname(__file__))

for module in listdir(dirname(__file__)):
    if module == "__init__.py" or module[-3:] != ".py":
        continue
    modules = "datalogger.instruments.%s" % (module[:-3])
    __import__(modules, locals(), globals())

os.chdir("../")

del module, listdir, dirname
