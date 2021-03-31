
import sys
import os
from ParserCura import *

'''
cura files 3.1.0

M218 T1 X?? Y?? Z?? - offset of t1 to t0 in x

marlin

M42 P{pin} S{0|255} I 
    I - ignore protection
    on: S0    off: S255
    43 - spindel
    32 - red
    45 - white
    47 - green

M300 S1 P{ms}
    ms - play sound for ms 

M302 S0 
    allow cold extrusion :)

M118 ABC 
    display on host a msg ABC
    
M0 
    wait for confirmation on screeen of lcd

'''




foamStart = '''
; foam work start start gcode
M118 Foam work start
T0
M302 S0

;prime ?
G92 E0
G0 F800 E??foamPrime??
G92 E0

M118 Foam work start end
; foam work start ends gcode
'''

foamEnd = '''
; foam work end gcode
M118 Foam work end cleaning ....

; go to cleaning spot
G0 X0 Y0 F5000


; ---- valvs sequence -----

; open valvs
;valvAir
M42 P??valvAir?? S??relayOn?? 

; wait 1 sec
G91
G0 Z+1 F120
G0 Z-1 F120
G90
; wait 1 sec

;close valvs
M42 P??valvAir?? S??relayOff??

; wait 1 sec
G91
G0 Z+1 F120
G0 Z-1 F120
G90
; wait 1 sec

; open valvs
;valvAir
M42 P??valvAir?? S??relayOn?? 

; wait 1 sec
G91
G0 Z+1 F120
G0 Z-1 F120
G90
; wait 1 sec

;close valvs
M42 P??valvAir?? S??relayOff??


M118 Foam work end and park
; foam work end ends gcode
'''

millStart = '''
; mill start
M118 Mill starts ...
T1

; spin up speendel
M42 P??spindelPinOnOff?? S??selenoidOn??

; mill start end
'''

millEnd = '''
; mill end 

; stop spindel
M42 P??spindelPinOnOff?? S??selenoidOff??

; wait 4 sec
G91
G0 Z+2 F60
G0 Z-2 F60
G90
; wait 4 sec


; to parking spot 
G0 X??millHeadXPark?? F8000

M118 Mill stops and park
; mill end end
'''


dVal = {
    'cura':{
        'outerF': 123.00 #mm/s
        },    
    'bottomLeft': [#[0.1,0.1,0.1],
        2600.0,  # x
        689.0,   # y
        111.00    # z
        ],
    'gcode': {
        'foamPrime': 3.2,    # mil ? E 
        'millHeadXPark': 3900.0,
        'valvA':    11,  #pin
        'valvB':    11,  #pin
        'valvAir':  45,  #pin
        'valvSolvent':  11,  #pin
        'spindelPinOnOff':  43,  #pin
        'selenoidOn': 0,
        'selenoidOff': 255,
        'relayOn': 0,
        'relayOff': 255,
        },
    'feeds': {
        'rHorizontal': 5000.0,
        'rVertical': 800.0,
        'wHorizontal': 1800.0,
        'wVertical': 600.0,
        },
    'foam': {
        'layerH': 12.0,      
        'width': 36.0,
        'expand': 20.0,
        'fromEdgeIn': 9.0,
        'Etune': 1.0,
        'ZSafe': 13.0,
        'prefix': foamStart,
        'sufix': foamEnd,
        'preloadIfDistance': 60.0,
        'preloadStart': 0.5 #add so much on start of paths
        },
    'mill': {
        'toolD' : 4.0, #12.7
        'toolH' : 10.0, #26.0
        'layerH': 0.5,
        'millTopOverlap': 0.2, # mm
        'prefix': millStart,
        'sufix': millEnd
        },
    
    }

#dVal['bottomLeft'] = [0.1,0.1,0.1]
dVal['mill']['toolD'] = 12.7
dVal['mill']['toolH'] = 26.0

dVal['foam']['prefix'] = mkPrefixAndSufix( dVal['foam']['prefix'],dVal )
dVal['foam']['sufix'] = mkPrefixAndSufix( dVal['foam']['sufix'],dVal )
dVal['mill']['prefix'] = mkPrefixAndSufix( dVal['mill']['prefix'],dVal )
dVal['mill']['sufix'] = mkPrefixAndSufix( dVal['mill']['sufix'],dVal )
  
  
  
  
def findArg(args,fArg):
    fArgLen = len(fArg)
    fArg = "-%s" % fArg
    for a in args:
        if a[1:fArgLen] == fArg:
            return a[fArgLen+1:]
            
    return None  

def printHelp():
    print('''
Current config:
    {defVal}
        
        
Help:
    Aplication usage:
    main.py inputFile.gcode option
    
option:
    E      -    final version
    noE    -    don't generate E axis for files
    
        '''.format(
            defVal = dVal
            ))
    sys.exit(0)
  
  
if __name__ == "__main__":
    print("Welcome to\n\tPrint Mill Post Process - PMPP !")
    args = sys.argv[1:]
    argsCount = len( args )
    
    print("args{}: {}".format(len(args),args))
    
    if argsCount not in [2]:
        printHelp()
        
        
    if argsCount == 2:
        inFile = args[0]
        ft = inFile.split(".")
        outFile = '.'.join(ft[:-1])
        arg2 = args[1]
        if arg2 in [ 'E', 'noE']:
            outFile+="_"+arg2
        else:
            printHelp()
        
        if arg2 in ['h','-h','--h','--help']:
            printHelp()
            
        
        fa = FileActions()
        fName = os.path.basename(outFile)
        fa.mkDir(outFile)
        outFile = fa.join(outFile,fName)
        
        
        
        print('''
input file:     {inF}
output file:    {ouF}
option:         {option}
        '''.format(
            inF = inFile,
            ouF = outFile,
            option = arg2
            ))
        
        #sys.exit(9)
        
        
        #print("inFile",inFile)
        #print("outFile",outFile)
        ##print("outFileBuild[",outFileBuild,']')
        #print("exit debug")
        #sys.exit(0)
        
        makeE = True if arg2 == 'E' else False
        
        pc = ParserCura()
        pc.makeIt(inFile,outFile,makeE,dVal)
        print("parser makeIt DONE!")
        
        if 0:
            
            if 1:
                f = open(outFile+"_complit.gcode","w")
                for l in pc.complitLines:
                    f.write(l+"\n")

                f.close()
                
            if 1:
                f = open(outFile+"_complitOnlyG.gcode","w")
                for l in pc.complitLines:
                    if l[:2] in ["G1","G0"] or l[0] == ";":
                        f.write(l.replace("E","F10000;E")+"\n")
                f.write("M2\n")
                f.close()
                
            if 1:
                f = open(outFile+"_outer.gcode","w")
                pOld = ""
                for i,path in enumerate(pc.outerWall):
                    f.write( "; path no {}\n".format(i+1) )
                    for ii,p in enumerate(path):
                        if ii == 0:
                            f.write(p.replace("E","F10000;E").replace("G1","G0")+"\n")
                        f.write(p.replace("E","F10000;E")+"\n")
                        pOld = p
                    f.write( "; path no {} END\n".format(i+1) )
                f.write("M2\n")
                f.close()
                
            #sys.exit(0)
    
    
    from gui import *
    g = gui()
    g.setParser(pc, inFile, dVal)
    #g.plot(inFile, dVal)
    g.run()
    g.killPlt()
    
    
    