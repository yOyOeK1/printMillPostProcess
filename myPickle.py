
import pickle

class myPickle:
    
    def make(self, obj,fileName):
        print("myPickle make file",fileName)
        pickle.dump( obj, open(fileName,'wb') )
        print("    DONE")
        
    def load(self, fileName):
        print("myPickle load file",fileName)
        tr = pickle.load( open(fileName,'rb') )
        print("    DONE")
        return tr
        