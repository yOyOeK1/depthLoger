import os

class FileActs:
    
    def loadFile(self, filePath):
        
        try:
            f = open(filePath)
        except:
            return None
        
        
        fOrg = []
        line = ""
        
        while True:
            line = f.readline()
            if line:
               fOrg.append( ("%s"%line).replace("\n", " ").replace("\r", " ") )
            else:
                break
        print "loaded: %i" % len(fOrg)
        
        
        return fOrg
    
    def writeFile(self, path, str):
        f = open(path,"w")
        f.write(str)
        f.close()

	    
    def isFile(self, path):
        return os.path.isfile(path)

    def isDir(self, path):
        return os.path.isdir(path)

    