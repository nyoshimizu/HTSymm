scriptID = '20160204'
scriptname = 'runscript' + scriptID

import pathsets

runscript = __import__(scriptname)

if __name__ == "__main__":
    runscript.runscript()
