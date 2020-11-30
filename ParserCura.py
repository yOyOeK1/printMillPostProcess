import json
import sys
from MyCalculate import *
from shapely.geometry import Polygon,Point,LineString,MultiLineString
from shapely.geometry.multipolygon import MultiPolygon
import numpy as np
import random
from builtins import enumerate
import math
from myPickle import myPickle
from FileActions import *


def mkPrefixAndSufix(gcodeLines,dVal):
    for k in dVal['gcode']:
        v = str(dVal['gcode'][k])
        #print("    -- >> k",k,' = ',v)
        gcodeLines = gcodeLines.replace(
            "??{}??".format(k),
            v
            )
      
    gcodeLines = '\n\n;//--------- START--------------------------------'+ \
        gcodeLines+ \
        ';\\\\------------------END----------------------------\n\n'
        
    #print(gcodeLines)
    # for linuxcnc
    if 1:
        return gcodeLines.replace(
            "T0",";4lcnc T0").replace(
            "M118", ";4lcnc M118").replace(
            "G92", ";4lcnc G92").replace(
            " E", " ;4lcnc E").replace(
            "M42", ";4lcnc M42").replace(
            "M300", ";4lcnc M300").replace(
            'M302 S0',';4lcnc M302 S0')
    else:
        return gcodeLines
        
        

class PCLine:
    
    
    stats = {
        'G0': 0,
        'G1': 0,
        'Comment': 0,
        'offset': 0,
        'Others': 0,
        'orgLine': ""
        }
    def __init__(self, lineNo, line):
        self.lineNo = lineNo
        self.line = line
        
        if line[0] == ';':
            self.t = 'comment'
            self.stats['Comment']+= 1
            #print(line)
            
        elif line[0] == 'G':
            if line[1] == '0':
                self.t = 'G0'
                self.stats['G0']+= 1
            
            elif line[1] == '1':
                self.t = 'G1'
                self.stats['G1']+= 1
            
            elif line[:3] == 'G28':
                self.t = 'home'
                self.stats['Others']+= 1
            
            elif line[:3] == 'G92':
                self.t = 'offset axis'
                self.stats['offset']+= 1            
            
            else:
                print("unknown G! [",line,"]")
                
        else:
            self.t = 'other'
            self.stats['Others']+= 1
    

class ParserCura:
    
    def __init__(self):
        print("ParserCura __init__")
        self.cal = MyCalculate()
        self.pic = myPickle()
        self.fa = FileActions()
        self.simpli = 0.05
        self.totalFoamMil = 0.0
        
        
    def makeIt(self, filePath, dVal):
        self.bottomLeftForFinish = dVal['bottomLeft']
        print("ParserCura makeIt [{0}]".format(filePath))
        filehashhash = "cashePMPP_{}_{}".format(
            len(filePath), self.fa.getSize(filePath)
            )
        filePathCash = "%s_cashe_"%filePath
        print("    file hashhash [",filehashhash,']')
        
        self.linesOrg = self.loadOrgFile(filePath)
        self.lineWidth = self.lookForLineWidth( self.linesOrg )
        self.filamentWidth = self.lookForFilamentWidth( self.linesOrg )
        self.layerHeight = self.lookForLayerHeight( self.linesOrg )
        self.complitLines,self.complitV4l = self.makeComplitLines( self.linesOrg )
        self.zLayers = sorted(self.zLayers.keys())
        self.complitV4l = self.makeOffsets( self.complitV4l, [0.01, 0.01, 0.01] )
        #self.allWorkPathsV4l = self.extractAllWorkPaths( self.complitV4l, dVal )
        self.allWorkPathsV4l = self.complitV4l
        #self.outerWallV4l = self.extractOuter( self.complitV4l, dVal )
        #self.outerWallV4l = self.extractOuter2( self.complitV4l, dVal )
        #self.offsets90LinesV4l = self.make90OffsetsLines( self.outerWallV4l, dVal )
        #self.offsetsLinesV4l,self.offsetPoligons = self.makeOffsetsLines( self.outerWallV4l, dVal )
        self.allWorkPathsV4l = self.makeAllPathStartEZero(self.allWorkPathsV4l)
        
        #sys.exit(0)
        
        
        if 1 and self.fa.isFile('%s%s0.data'%(filePathCash,filehashhash)):
            print("unpickle ! unpickle ! unpickle ! unpickle !")
            self.offsetsLinesV4l = self.pic.load('%s%s0.data'%(filePathCash,filehashhash))
            self.offsetPoligons = self.pic.load('%s%s1.data'%(filePathCash,filehashhash))
            self.outerWallV4l = self.pic.load('%s%s2.data'%(filePathCash,filehashhash))
            self.polys = self.pic.load('%s%s3.data'%(filePathCash,filehashhash))
            
        else:
            self.offsetsLinesV4l,self.offsetPoligons,self.outerWallV4l,self.polys = self.makeOffsetsLines2( self.complitV4l, dVal )
            print("make pickle !")
            self.pic.make( self.offsetsLinesV4l, '%s%s0.data'%(filePathCash,filehashhash))
            self.pic.make( self.offsetPoligons, '%s%s1.data'%(filePathCash,filehashhash))
            self.pic.make( self.outerWallV4l, '%s%s2.data'%(filePathCash,filehashhash))
            self.pic.make( self.polys, '%s%s3.data'%(filePathCash,filehashhash))


        self.chkLayersForWork( dVal )
        print("total volume of foam in part:",self.totalFoamMil)
        
        sys.exit(9)
        
        if 0:
            print("------------------------------------------------------------------")
            print("----full-------------------------------------------------org------")
            lw = len("G1 X3093.376 Y2999.285 Z0.3 E7.12955 F1800.0      ")
            ls = 470
            for i,l in enumerate(self.complitLines[ls:570]):
                ll = self.complitLines[i+ls]
                tp = str(i+1+ls)+"    [full] "+ll
                for a in range(lw - len(ll)):
                    tp+= " "
                tp+= "[org] "+self.linesOrg[i+ls].line
                print( tp )
       
    def makeAllPathStartEZero(self, pathsV4l):
        print("- make all paths start E zero")
        print("    adding dist, Emm, vol, Espeed, EFlow to V4l elements ...")
        eTotal = 0.0
        
        objOfFilament = math.pow(self.filamentWidth*0.5,2)*math.pi
        
        for path in pathsV4l:
            pathV = []
            p0 = path[0]
            #print("p0:",p0)
            p0E = p0['E']
            eStart = p0E
            p0S = SPoint(p0['X'],p0['Y'])
            #print("|--------")
            for p in path[1:]:
                p1 = p
                p1S = SPoint(p1['X'],p1['Y'])
                p1E = p1['E']
                eLen = p1E - p0E
                dist = self.cal.distance(p0S,p1S)
                #print("dist:",dist)
                if dist == 0.0:
                    dist+=0.00000000001
                eSpeed = (eLen/dist)
                vol = eLen*objOfFilament
                eFlow = (eLen/dist)*objOfFilament
                if dist <= 0.0:
                    print("EE - distance negative !!!")
                if eLen <= 0.0:
                    print("EE - eLen negative !! or == 0.0")
                
                p0['dist'] = dist
                p0['Emm'] = eLen
                p0['vol'] = vol
                p0['Espeed'] = eSpeed
                p0['EFlow'] = eFlow
                
                p0 = p1
                p0S = p1S
                p0E = p1E
                
            for p in path:
                p['E']-= eStart
                
            if path[0]['E'] != 0.0:
                print("EE - first on path have not E zero")
                
            eTotal+= path[-1]['E']
            #print("--------|")
        
        print("    E total distance {}[mm] {:.5f}[m]".format(eTotal,(eTotal/1000.0)))
        #sys.exit(0)
        return pathsV4l
                
    def makeOffsetsLines2(self, pathsV4l, dVal ):
        print("- make offsets lines v2")
        
        offLinesV4l = []
        offPoligons = []
        outerWallV4l = []
        polys = {}
        
        lines = []
        line = []
        lastZ = None
        dist_ = (dVal['mill']['toolD']*.5)
        printRSoft = self.lineWidth*0.5
        
        pc = len(pathsV4l)
        ppiEvery = int(pc/10.0)
        
        for ppi,path in enumerate( pathsV4l ):
            if (ppi%ppiEvery) == 0:
                print("    progress {}/{}".format(ppi,pc))
            if lastZ != path[0]['Z'] or len(pathsV4l) == ppi+1:
                
                if len(lines) > 0:
                    mp = MultiPolygon()
                    for l in lines:
                        mp = mp.union(l)
                    #print("area is ",mp.area)
                   
                    if len(lines) > 0:
                        polyOuter = mp.buffer( printRSoft, cap_style=3 
                                   ).buffer( -printRSoft,cap_style=3 ) 
                        polyOff = mp.buffer(dist_, cap_style=3)
                        try:
                            aeoaeuob = polys[lastZ]
                        except:
                            polys[lastZ] = {
                                'outer': [],
                                'offset': [],
                                }
                        
                        polys[lastZ]['outer'].append(polyOuter)
                        polys[lastZ]['offset'].append(polyOff)
                            
                        outerWallV4l = self.polyToPath(
                            polyOuter, 
                            lastZ, 
                            outerWallV4l
                            )
                        offLinesV4l = self.polyToPath(
                            polyOff, 
                            lastZ, 
                            offLinesV4l
                            )
                        
                        
                   
                    lines = []
                lastZ = path[0]['Z']
                
            
            
            for p in path:
                line.append((p['X'],p['Y']))
                
            #print(line)
            
            ls = LineString(line)
            ls = ls.buffer(self.lineWidth*0.5, cap_style=3)#.simplify(0.02,preserve_topology=True)
            lines.append(ls)
            line = []
              
        print("    polygon status after pass...")
        for z in polys.keys():
            
            outerGeoms = 1
            offGeoms = 1
            
            for o in polys[z]['outer']:
                try:
                    outerGeoms+= len(o.geoms)
                except:
                    pass    
            for o in polys[z]['offset']:
                try:
                    offGeoms+= len(o.geoms)
                except:
                    pass    
            
            
            print("    polys Z[{}]    outer:{}({})    offset:{}({})".format(
                z,
                len(polys[z]['outer']),outerGeoms,
                len(polys[z]['offset']),offGeoms,
                ))
        
        #sys.exit(0)
        return offLinesV4l,offPoligons,outerWallV4l,polys
                
    def chkIfThereIsAWork(self, z, paths, desc = ""):
        for path in paths:
            pl = len(path)
            p0 = path[0]
            for p in path[1:]:
                p1 = p
                try:
                    if pl > 1 and p1['G'] == 1 and p1['Z'] == z:
                        #if z >=15.0:
                        #    print("pl",desc,pl)
                        #    print(p1)
                            
                        return True,pl
                except:
                    pass
                p0 = p1
                    
        return False,0
     
    def rou(self,v):
        return round(v,3)
                
    def chkLayersForWork(self, dVal):
        print("- chk layers for work")
        deb = 0
        foamLayers = []
        foamLast = 0.0
        millLayers = []
        millLast = 0.0
        zTzs = []
        offSets = dVal['bottomLeft']
        
        zLast = sorted(list(self.polys.keys()))[-1]
        fFoam = open("/tmp/foamPath.gcode","w")
        fFoam.write("G0 Z{0} F{1}\n".format(
            dVal['foam']['ZSafe']+offSets[2],
            dVal['feeds']['rVertical'] 
            ))
        
        fMillTops = open("/tmp/millTopsPath.gcode","w")
        fMillTops.write("G0 Z{0} F{1}\n".format(
            dVal['foam']['ZSafe']+offSets[2],
            dVal['feeds']['rVertical']
            ))
                
        fAll = open("/tmp/allPaths.gcode","w")
        fAll.write("G0 Z{0} F{1}\n".format(
            dVal['foam']['ZSafe']+offSets[2],
            dVal['feeds']['rVertical']
            ))
        
        
        
        millStatus = False
        for zi,z in enumerate(self.zLayers):
            zTzs.append(z)
            if deb: print("zLast",zLast,' z',z)
            lPrint,lPrintC = self.chkIfThereIsAWork(z, self.allWorkPathsV4l," foam ")
            lMill,lMillC = self.chkIfThereIsAWork(z, self.offsetsLinesV4l, " mill ")
            lPm = False
            lMm = False
            
            if dVal['foam']['layerH'] <= ( z-foamLast ) or z == zLast:
                lPm = True
            if dVal['mill']['layerH'] <= ( z-millLast ) or z == zLast:
                lMm = True
            
            
            
            
            if deb: print("    ",z," [mm]    foam: {} ({}) {}    mill: {} ({}) {}".format(
                lPrint, lPrintC, lPm, lMill, lMillC, lMm
                ))

            
            if lPm:
                zFoamFromLast = z-foamLast
                workZ = zTzs[-1]
                print("zFoamFromLast:",zFoamFromLast,"mm")
                print("zTzs:",zTzs)
                
                try:
                    aeuoao = self.polys[workZ]['outer']
                except:
                    print("EE - detect more zLayers then polys in buffer")
                    self.polys[workZ] = { 'outer': [], 'offset': []}
                
                fPoly = MultiPolygon()
                fPolyOuterByLayer = {}
                for fz in zTzs:
                    fPolyForLayer = MultiPolygon()
                    for poly in self.polys[fz]['outer']:
                        fPolyForLayer = fPolyForLayer.union(poly)
                    fPoly = fPoly.union(fPolyForLayer)
                    try:
                        abc = fPolyOuterByLayer[fz]
                        print("EE - more then one outer poly on z")
                        sys.exit(0)
                    except:
                        fPolyOuterByLayer[fz] = fPolyForLayer
                    
                

                # foam extruder path
                fFoam.write(dVal['foam']['prefix'])
                fAll.write(dVal['foam']['prefix'])
                
                toolD = dVal['foam']['width']*0.5 
                fPolyOrg = fPoly
                foamPaths = self.makeIslandPath(
                    fPoly.buffer( -toolD*.3 ).buffer( 0.0 ), 
                    toolD, workZ, dVal)
                self.mPathsToGCode("FOAM",
                            dVal, foamPaths, workZ, fFoam, fAll,
                            calE = True,
                            layerH = zFoamFromLast
                            )
                
                fFoam.write(dVal['foam']['sufix'])
                fAll.write(dVal['foam']['sufix'])
                # foam extruder path



                
                if millStatus == False:
                    fMillTops.write(dVal['mill']['prefix'])
                    fAll.write(dVal['mill']['prefix'])
                    millStatus = True
                
                # mill top flat stock
                if 0:
                    print("areas of work for ",zTzs)
                    print("foam area",fPolyOrg.area)
                    for poz in fPolyOuterByLayer.keys():
                        poly = fPolyOuterByLayer[poz]
                        print("Z",poz," area",poly.area)
                
                
                toolD = dVal['mill']['toolD']-dVal['mill']['millTopOverlap'] 
                millTopsPaths = self.makeIslandPath(fPolyOrg, toolD, workZ, dVal)
                self.mPathsToGCode("MILL TOP FLAT STOCK",
                    dVal, millTopsPaths, workZ, fMillTops, fAll)
                # mill top flat stock
                
                
                # mill flat parts
                mziMax = len(zTzs)-1
                toolD = dVal['mill']['toolD']-dVal['mill']['millTopOverlap']
                millFlatsStats = 0
                lastMz = None
                for mzi, mz in enumerate(zTzs[::-1]):
                    if lastMz != None and mzi < mziMax and mzi > 0:
                        flatIsland = fPolyOuterByLayer[mz]
                        for mmz in zTzs:
                            if mmz >= lastMz:
                                flatIsland = flatIsland.difference(
                                    fPolyOuterByLayer[mmz].buffer( dVal['mill']['toolD'] ).buffer( 0.0 )
                                    )
                                
                        flatIsland = flatIsland
                        if flatIsland.area > 0.0:
                            millFlatsPaths = self.makeIslandPath(flatIsland, toolD, lastMz, dVal)
                            self.mPathsToGCode("MILL FLAT PARTS",
                                dVal, millFlatsPaths, lastMz, fMillTops, fAll)
                            millFlatsStats+=1
                    
                    lastMz = mz
                if millFlatsStats > 0:
                    print(" - mill flat parts ends ({}) DONE".format(millFlatsStats))
                # mill flat parts
                
                
                
                #  mill outer milll
                
                try:
                    aeuo = missingZ
                    print("adding missing Z",missingZ)
                    zTzs.insert(0, missingZ)
                    fPolyOuterByLayer[missingZ] = missingPoly
                    missingPoly = fPolyOuterByLayer[missingZ]
                    missingZ = zTzs[-1]
                except:
                    print("no missing Z it's a first mill run ")
                    missingZ = zTzs[-1]
                    missingPoly = fPolyOuterByLayer[missingZ]
                
                toolD = dVal['mill']['toolD'] 
                inzTz = zTzs[::-1]
                #print("invert zTz",inzTz)
                #print("normal zTz",zTzs)
                mZTop = inzTz
                mLastZ = None
                polyy = MultiPolygon()
                for mzi,mz in enumerate(inzTz[1:]):
                    polyy = polyy.union(fPolyOuterByLayer[mz])
                    poly = polyy.buffer( toolD*.5 ).buffer( 0.0 )
                    path = self.polyToPath(
                        poly.simplify(self.simpli,preserve_topology=True), 
                        mz, 
                        [], 
                        optimizePathsConnection = {
                            'dVal': dVal
                            })
                    self.mPathsToGCode("outer mill", 
                        dVal, path, mz, fMillTops, fAll
                        )
             
                if millStatus:
                    fMillTops.write(dVal['mill']['sufix'])
                    fAll.write(dVal['mill']['sufix'])
                    millStatus = False
                # mill outer mill
                
                
                zTzs = [] 
            
            if lPm:
                foamLast = z
                #sys.exit(11)
            if lMm:
                millLast = z

        fFoam.write("M2\n")
        fFoam.close()
        
        fMillTops.write("M2\n")
        fMillTops.close()
        
        fAll.write("M2\n")
        fAll.close()
        

    def makeIslandPath(self, polys, toolD, z, dVal):
        
        polys = polys.buffer(toolD*.5)
        paths = []
        while True:
            #print("shrink NO",steps," area:",fPoly.area)
            if polys.area == 0.0:
                break
            else:
                paths = self.polyToPath(
                    polys.simplify(self.simpli,preserve_topology=True), 
                    z, 
                    paths,
                    optimizePathsConnection = {
                        'dVal': dVal
                        }
                    )
            polys = polys.buffer( -(toolD) ).buffer(0.0)
        return paths

    def mPathsToGCode(self, desc, dVal, millpaths, workZ, fileToPut, fAll, calE=False, layerH=0 ):
        offSets = dVal['bottomLeft']
        if calE:
            # 1 liter is 1 000 000 mm^3 ?
            Earea = (  
                dVal['foam']['width'] * 
                layerH / dVal['foam']['expand'] )*dVal['foam']['Etune'] 
            print("Earea is %s"%Earea)
        eBase = 0.0                  
        
        for ppi,path in enumerate(millpaths):
            gLine = "\n;{0} PATHS path START at Z{1} NO{2}/{3}\n".format(
                desc, 
                workZ, 
                ppi, 
                len(millpaths)
                )
            fileToPut.write( gLine )
            fAll.write( gLine )
            
            if calE:
                fileToPut.write( ";4lcnc G92 E0\n" )
                fAll.write( ";4lcnc G92 E0\n" )
            
            pLast = None
            dist = 0.0
            for pi,p in enumerate(path):
                pSp = SPoint(p['X'],p['Y'])                       
                if pi == 0:
                    gLine = "G0 Z{0} F{3}\nG0 Z{0} X{1} Y{2} F{3}\n".format(
                        self.rou( workZ+dVal['foam']['ZSafe']+offSets[2]+dVal['foam']['layerH'] ),
                        self.rou( p['X']+offSets[0] ),
                        self.rou( p['Y']+offSets[1] ),
                        dVal['feeds']['rHorizontal']
                        )
                    fileToPut.write( gLine )
                    fAll.write( gLine )
                    
                gLine = "%s"%self.V4lToStr(p, offSet = offSets)
                if calE and pLast != None:
                    dist = self.cal.distance(pSp, pLast)
                    eVol = Earea*dist/1000.00 # its milliliters
                    self.totalFoamMil+= eVol
                    #print("dist:",dist,' eVol',eVol)
                    gLine+= " ;4lcnc E{} dist {} used E {}".format(
                        eBase+eVol,
                        dist,
                        eVol
                        )
                    eBase+= eVol
                
                gLine+= "\n"    
                fileToPut.write( gLine )
                fAll.write( gLine )
                
                
                pLast = pSp
                
                
            gLine = "G0 Z{0} F{1}\n \n;{2} PATHS path END at Z{3} NO{4}/{5}\n\n".format(
                (workZ+dVal['foam']['ZSafe']+offSets[2]+dVal['foam']['layerH']),
                dVal['feeds']['rVertical'], 
                desc, 
                workZ, 
                ppi, 
                len(millpaths)
                )
            fileToPut.write( gLine )
            fAll.write( gLine )
        
    def makeOffsetsLines( self, paths, dVal ):
        print("- make offsets from poligones")
        poligones = []
        offsets = []
        dist_ = (dVal['mill']['toolD']*.5)+(self.lineWidth*.5)
        zOld = None
        pUnion = []
        pDiff = []
        #print("paths",len(paths))
        for pi,path in enumerate( paths ):
            line = []
            
            # find direction
            yMax = None
            pn = None
            for i,p0 in enumerate(path):
                if p0['G'] in [1,0]:
                    if yMax == None:
                        yMax = p0['Y']
                        pn = i
                    
                    if yMax < p0['Y']:
                        yMax = p0['Y']
                        pn = i
            
            angDifSum = 0.0
            try:
                pm1 = path[pn-1]
                if pm1['G'] not in [1,0]:
                    pm1 = path[pn-2]
                pp1 = path[pn+1]
                angDifSum = pp1['X']-pm1['X']
            except:
                print('''EE - detecting direction error
    pn: {}
    path len: {}
    path -1: {}
    path +1: {}'''.format(
        pn,
        len(path),
        path[pn-1],
        path[pn+1]
        ))
            
            for i,p4 in enumerate(path):
                if p4['G'] in [0,1]:
                    z = p4['Z']
                    line.append( ( p4['X'], p4['Y'] ) )
                    
            
            if zOld == None:
                zOld = z
                 
            if z != zOld:
                offsets = self.makePolyFromUnionDiff( pUnion, pDiff, dist_, zOld, offsets )
                
                pUnion = []
                pDiff = []
                
                if angDifSum <= 0:
                    pUnion.append( Polygon( line ) )
                else:
                    pDiff.append( Polygon( line ) )
                zOld = z
            else:
                if angDifSum <= 0:
                    pUnion.append( Polygon( line ) )
                else:
                    pDiff.append( Polygon( line ) )
                
        offsets = self.makePolyFromUnionDiff( pUnion, pDiff, dist_, z, offsets )      
        print("    poligones offsets ready")        
        #print(len(offsets))
        
        return offsets,poligones
    
       
    def makePolyFromUnionDiff( self, pUnion, pDiff, dist_, zOld, offsets ): 
        polyDiff = Polygon()
        for p in pDiff:
            polyDiff = polyDiff.union(p)        
                       
        if len(pUnion) > 0:                    
            layerPoly = Polygon()
            for ui,p in enumerate(pUnion):
                contains = layerPoly.contains(p)
                #print(" poly contains on ui ",ui,"/",len(pUnion)," z",zOld," mm -> ",contains)
                if contains:
                    print("    \----- sub island ---->")
                    offsets = self.makePolyFromUnionDiff( pUnion[ui:], [], dist_, zOld, offsets )
                    print("        < -- end sub")
                    break
                else:
                    layerPoly = layerPoly.union(p)
            #print(" polly diff contains poly?",polyDiff.contains(layerPoly))
            layerPoly = layerPoly.difference( polyDiff )    
            
            polyOff = layerPoly.buffer( dist_ )#* ( 1.0 if angDifSum <= 0.0 else -1.0 ) )
            if isinstance(polyOff, MultiPolygon):
                for g in polyOff:
                    offset = self.polyToPath( g, zOld, offsets )
            else:
                offsets = self.polyToPath( polyOff, zOld, offsets ) 
                
        return offsets
    
    
    def optimizePaths(self, paths, optParams):
        #print("- optimize Paths")
        
        pathsToUse = paths[1:]
        pathsOpti = [paths[0]]
        
        while len( pathsToUse ) > 0:
            disMin = None
            pathMin = None
            pLast = pathsOpti[-1][-1]
            pS = SPoint(pLast['X'],pLast['Y'])
            for pi, path in enumerate(pathsToUse):
                p = path[0]
                pN = SPoint(p['X'],p['Y'])
                dist = self.cal.distance( pS, pN )
                
                if disMin == None or disMin > dist:
                    disMin = dist
                    pathMin = pi
                    
            pathsOpti.append( pathsToUse[pathMin] )
            pathsToUse.pop(pathMin)
            
        return pathsOpti
    
    def polyToPath(self, poly, z, tToReturn, optimizePathsConnection = None):
        #optimizePathsConnection = None
       
        #print("polyToPath: interrion for z ",z," len:",len(poly.interiors))
        #print("-> ",np.array( poly.interiors ))
        
        try:
            if len( poly.geoms ) > 1:
                for g in poly:
                    tToReturn = self.polyToPath( g, z, tToReturn, optimizePathsConnection = optimizePathsConnection )
                return tToReturn
        except:
            pass
        
        pInter = True
        pExt = True
        
        if pInter and len(poly.interiors) > 0:
            for p in poly.interiors:
                nPolyOff = np.array( p )
                offPath = []
                for n in nPolyOff:
                    offPath.append(self.getV4l("G1 X{} Y{} Z{}".format(
                        n[0], n[1], z
                        )))
                tToReturn.append(offPath)

        
        
        if pExt:
            nPolyOff = np.array( poly.exterior )
            offPath = []
            for n in nPolyOff:
                offPath.append(self.getV4l("G1 X{} Y{} Z{}".format(
                    n[0], n[1], z
                    )))
            tToReturn.append(offPath)
            
        if optimizePathsConnection != None:
            tToReturn = self.optimizePaths(tToReturn, optimizePathsConnection)
            
        return tToReturn
    
        
    def make90OffsetsLines( self, paths, dVal ):
        print("- make 90` offsets lines")
        offsets = []
        dist_ = (dVal['mill']['toolD']*.5)+(self.lineWidth*.5)
        #dist_ = 20.0
        
        for path in paths:
            line = []
            pO = path[0]
            for i,p in enumerate(path[1:]):
                makeIt = True
                '''
                try:
                    if pO['Z'] < 2.0:
                        makeIt = True
                except:
                    pass
                '''
                if makeIt and pO['G'] in [1,0]:
                    pN = p
                    
                    if i == 0:
                        pL = path[-1]
                        if pO['X'] == pL['X'] and pO['Y'] == pL['Y']:
                            #print("loop path at Z ", pL['Z'],"[mm]")
                            pass
                        else:
                            print("open path", pL['Z'])
                            print("EE - open path not implemented !!")
                            for o in path:
                                print(self.V4lToStr(o))
                            sys.exit(9)
                    
                    newPointS = self.cal.newPoint(
                        SPoint(pO['X'], pO['Y']),
                        SPoint(pN['X'], pN['Y']),
                        dist = dist_,
                        addAngle = -90.0
                        )
                    newPointE = self.cal.newPoint(
                        SPoint(pN['X'], pN['Y']),
                        SPoint(pO['X'], pO['Y']),
                        dist = dist_,
                        addAngle = 90.0
                        )
                    
                    # at start 
                    #line.append( "G1 X{} Y{} Z{}".format(pO['X'], pO['Y'], pO['Z']) )
                    #line.append( "G1 X{} Y{} Z{}".format(newPointS.x, newPointS.y, pO['Z']) )
                    line.append( self.getV4l( "G1 X{} Y{} Z{}".format(pO['X'], pO['Y'], pO['Z']) ) )
                    line.append( self.getV4l( "G1 X{} Y{} Z{}".format(newPointS.x, newPointS.y, pO['Z']) ) )
                    offsets.append(line)
                    line = []
                    
                    #at end 
                    line.append( self.getV4l( "G1 X{} Y{} Z{}".format(pN['X'], pN['Y'], pN['Z']) ) )
                    line.append( self.getV4l( "G1 X{} Y{} Z{}".format(newPointE.x, newPointE.y, pO['Z']) ) )
                    offsets.append(line)
                    line = []    
                
                    pO = pN
        
        
        return offsets
        
        
    def extractAllWorkPaths(self, linesV4l, dVal):
        print("- extract all working paths")
        cl = linesV4l
        paths = []
        wo = 0
        path = []
        le = None 
        for i,l4 in enumerate(cl):
            if le == None:
                le = l4['E']
            
            if l4['G'] == 1:
                if wo == 0:
                    if cl[i-1]['orgLine'][0] != ";":
                        l4n = cl[i-1]
                        l4n['G'] = 1
                        l4n['E'] = le
                        path.append( l4n )
                    elif cl[i-2]['G'] in [0,1]:
                        l4n = cl[i-2]
                        l4n['G'] = 1
                        l4n['E'] = le
                        path.append( l4n )
                wo = 1
                path.append(l4)
            if wo == 1 and l4['G'] != 1:
                wo = 0
                if len(path)>0:
                    paths.append(path)
                    
                path = []
            
            le = l4['E']
        
        if len(path)>0:
            #print("--> + <--",len(path))
            paths.append(path)
            
        return paths
     
    def extractOuter2(self, linesV4l, dVal):
        print(" - extracting v2 outer walls paths")
        ls = linesV4l
        
        paths = {}
        path = []
        xys = []
        zNow = None
        inPath = False
        for i,l4 in enumerate(ls):
            
            if ( zNow == None and l4['G'] in [0,1] ) or zNow != l4['Z']:
                zNow = l4['Z']
                paths[l4['Z']] = []
            
            if inPath == False and l4['G'] == 0 and ls[i+1]['G'] == 1:
                inPath = True
                l4['G'] = 1
                path.append(l4)
                xys.append([ l4['X'], l4['Y'] ])
            
            elif inPath and l4['G'] == 1:
                path.append(l4)
                xys.append([ l4['X'], l4['Y'] ])
            
            if inPath and ( ls[i+1]['G'] == 0  or len(ls) <= (i+2) ) :
                inPath = False
                paths[zNow].append({
                    'path':path,
                    'loop': None,
                    'outer': None,
                    'inner': None,
                    'poly' : None,
                    'points': [],
                    'xys': xys
                    })
                
                path = []
                xys = [] 
        
        if len(path) > 0:
            paths[zNow].append({
                'path':path,
                'loop': None,
                'outer': None,
                'inner': None,
                'poly' : None,
                'points': [],
                'xys': xys
                })
        
    
        for z in paths.keys():
            zPaths = paths[z]
            #print("z",z,' paths',len(zPaths))
            if len(zPaths) > 0:
                for path in zPaths:
                    if len(path['xys']) > 2:                        
                        if path['xys'][0] == path['xys'][-1]:
                            path['loop'] = True
                        else:
                            path['loop'] = False 
                        
                        path['poly'] = Polygon(path['xys'])
                    else:
                        path['poly'] = False
                        path['loop'] = False
                        for xy in path['xys']:
                            path['points'].append(Point(xy))
                            
        
        print("    looking for inner")
        for z in paths.keys():
            zPaths = paths[z]
            for bi,bpath in enumerate(zPaths):
                for ci,cpath in enumerate[zPaths]:
                    pass                
                    
                
            
        
         
        #sys.exit()      
        
    def extractOuter(self, pathsV4l, dVal):
        print("- extracting outer walls paths")
        outerWallPaths = []
        wo = 0
        outerF = dVal['cura']['outerF']*60.0
        path = []
        
        for pathV4l in pathsV4l:
            for i,l4 in enumerate(pathV4l):
                if l4['G'] in [0,1] and l4['F'] == outerF:
                    path.append(l4)
            
            if len(path)>0:
                outerWallPaths.append(path)
                path = []
            
        if len(path)>0:
            outerWallPaths.append(path)
            
        #print("outerWallPaths",len(outerWallPaths))
            
        return outerWallPaths
    
        
    def makeOffsets( self, pathsV4l, bottomLeft ):
        #return pathsV4l
        print("- offset work pice. New bottom left is {} mm x {} mm".format(
            bottomLeft[0],bottomLeft[1]
            ))
        xOff = self.xMin - bottomLeft[0]
        yOff = self.yMin - bottomLeft[1]
        #zOff = bottomLeft[2]
        
        
        for ppi, path in enumerate(pathsV4l):
            for pi, l4 in enumerate(path):
                if l4['G'] in [0,1]:
                    try:
                        #print('offset oldX',l4['X']," new ",(l4['X']- xOff))
                        l4['X']-= xOff
                    except:
                        pass
                    try:
                        l4['Y']-= yOff
                    except:
                        pass
                    
                    pathsV4l[ppi][pi] = l4
                    
        return pathsV4l
    
       
    def getV4l(self, line):
        v = {'orgLine':line}
        try:
            s = line.split(" ")
        except:
            print("EE - getV4l")
            print("    line[",line,"]")
            sys.exit(12)
            
        for i in s:
            if i != "":
                try:
                    
                    if i[0] == 'G':
                        v[i[0]] = int(i[1:]) 
                    elif i[0] == 'E':
                        v[i[0]] = float(i[1:])
                    else:
                        v[i[0]] = float(i[1:])
                    '''
                    
                    if i[0] != 'G':
                        v[i[0]] = float(i[1:])
                    else:
                        v[i[0]] = int(i[1:])
                    '''
                except:
                    v[i[0]] = i[1:]
                    
        if line[0] != 'G':
            v['G'] = -1
                    
        return v
    
    
    def V4lToStr(self,v4l, offSet = None):
        tr = ""
        for k in v4l.keys():
            if ( v4l[k] != None 
                 and k != 'orgLine' 
                 and k != 'org' 
                 and k != 'dist' 
                 and k != 'Emm' 
                 and k != 'vol'
                 and k != 'Espeed'
                 and k != 'EFlow'
                ):
                if k == 'G':
                    w = int(v4l[k]) 
                elif k == 'E':
                    w = v4l[k]
                elif k in ['X','Y','Z']:
                    if offSet:
                        if k == 'X':
                            w = self.rou(v4l[k]+offSet[0])
                        elif k == 'Y':
                            w = self.rou(v4l[k]+offSet[1])
                        elif k == 'Z':
                            w = self.rou(v4l[k]+offSet[2])    
                    else:
                        w = self.rou(v4l[k])
                else:
                    w = v4l[k]
                tr+= "%s%s "%(
                    k,
                    w 
                    )
        return tr
    
    
    def findBorder(self, pathsV4l):
        print("- find borders min max")
        xMin = None
        yMin = None
        xMax = None
        yMax = None
        zMin = None
        zMax = None
        
        for path in pathsV4l:
            for l4 in path:
                if l4['G'] == 1:
                    if l4['X'] != None:
                        if xMin == None or xMin > l4['X']: xMin = l4['X']
                        if xMax == None or xMax < l4['X']: xMax = l4['X']
                    
                    if l4['Y'] != None:
                        if yMin == None or yMin > l4['Y']: yMin = l4['Y']
                        if yMax == None or yMax < l4['Y']: yMax = l4['Y']            
                    
                    if l4['Z'] != None:
                        if zMin == None or zMin > l4['Z']: zMin = l4['Z']
                        if zMax == None or zMax < l4['Z']: zMax = l4['Z']
            
        print("working box:")
        print("    width: {:.3f} [mm] from {:.3f} to {:.3f} [mm]".format(
            xMax-xMin,
            xMin,
            xMax
            ))
        print("    long: {:.3f} [mm] from {:.3f} to {:.3f} [mm]".format(
            yMax-yMin,
            yMin,
            yMax
            ))
        print("    tall: {:.3f} [mm] from {:.3f} to {:.3f} [mm]".format(
            zMax-zMin,
            zMin,
            zMax
            ))
        
        self.xMin, self.xMax = xMin,xMax
        self.yMin, self.yMax = yMin,yMax
        self.zMin, self.zMax = zMin,zMax    
        
        
    def findAllZts(self, pathsV4l):
        print("- find all z'ts :P")
        self.zLayers = {}
        
        for path in pathsV4l:
            for l4 in path:
                if l4['Z']:
                    self.zLayers[l4['Z']] = 1
                    
        print(" z'ts: ",sorted(self.zLayers.keys()))
       
        
    def makeComplitLines(self, oLines ):
        print("- making lines complit with values")
        
        m = {
            'G': None,
            'X': None,
            'Y': None,
            'Z': None,
            'E': 0.0,
            'F': None
            }
        mkeys = m.keys()
        
        g92 = []
        for i,l in enumerate(oLines):
            l = l.line
            if l[:3] == "G92":
                g92.append(i)
        print("found ",len(g92)," of G92 ! ")
        if len(g92) == 3:
            print("    GOOOOD!")
        else:
            print("EE - wrong G92 count in file!")
        
        linesV4l = []
        lastE = 0.0
        eBase = 0.0
        for i,l in enumerate(oLines[ g92[1]+1: ]):
            l = l.line        
            if l == "M107" and len(linesV4l) > 1:
                print("end of work!")
                break
            
            elif l[:3] == 'G92':
                eBase = lastE
                m['E'] = lastE
                print("zero E! line:",i," new E base:",eBase," at:",l)
                
                
            
            elif l[:2] in ['G0', 'G1']:
                l4 = self.getV4l(l)
                for km in mkeys:
                    try:
                        m[km] = l4[km]
                    except:
                        pass
                for km in mkeys:
                    try:
                        a = l4[km]
                    except:
                        l4[km] = m[km]

                l4['E']+= eBase
                #m['E']+= eBase
                
                lastE = l4['E']
                
                linesV4l.append( l4 )
                #if l4['Z']>30.0 and l4['Z']<33.0:
                #    print(l4)
        #sys.exit(9)
        print("linesV4l - first pass",len(linesV4l))
        
        
        pathsV4l = []
        pp = []
        lastE = 0.0
        
        for i,l in enumerate( linesV4l ):
            #print(l)
            if lastE < l['E']:
                if len(pp) == 0:
                    pStart = linesV4l[i-1]
                    pStart['F'] = l['F']
                    pp.append( pStart )
                pp.append( l )
                    
                lastE = l['E']
                
                #print("+")
            else:
                #print("?")
                if len(pp)>0:
                    pathsV4l.append( pp )
                    #print("---------------")
                    #print(pp)
                    #sys.exit(0)
                    pp = []


        if len(pp)>0:
            pathsV4l.append( pp )
            
        print("paths found ",len(pathsV4l))
        
        
        self.findBorder(pathsV4l)
        self.findAllZts(pathsV4l)
        
        #sys.exit(9)
        
        return None,pathsV4l
        
    def yyyySomethingToUse(self):
        
        
        self.zLayers = {}        
        lines = []
        linesV4l = []
        lastE = None
        
        for l in oLines:
            l4 = self.getV4l(l.line)
            
            if lastE == None:
                try:
                    lastE = l4['E']
                except:
                    pass
            
            for k in self.gMem.keys():
                try:
                    self.gMem[k] = l4[k]
                except:
                    pass
                
                try:
                    l4[k] = self.gMem[k]
                except:
                    pass
            
            
            
            if l.line[:2]  in ["G0","G1"] and self.gMem['Z'] != None:
                self.zLayers[ self.gMem['Z'] ] = 1
            
            try:
                if l4['G'] in [0,1] and l4['orgLine'][0] != ';':
                    lines.append(l.line)
                    linesV4l.append( l4 )
            except:
                print("II - no G in line [",l4['orgLine'],']')
                pass
            
            
            lastE = l4['E']
            
    
        return lines,linesV4l
    
    
    def loadOrgFile(self,filePath):
        print("- loadOrgFile")
        
        f = open(filePath,'r')
        l = f.readline()[:-1]
        linesOrg = []
        cl = 1
        while l:
            linesOrg.append( PCLine( cl, l ) )
            l = f.readline()[:-1]
            cl+=1
        
        print("file have {0} lines".format(len(linesOrg)))
        print("some statistics about org file: ",linesOrg[-1].stats)
        return linesOrg
    
        
    def lookForLineWidth(self, lines):
        print("- lookForLineWidth")
        curaSetStr = ""
        for l in lines:
            if l.line[:11] == ";SETTING_3 ":
                curaSetStr += l.line[11:]
        
        try:
            j = json.loads(curaSetStr)
        except:
            print("EE - no cura file ? no setting_3 part")
            lineWidth = 0.8
            print("II - setting default ",lineWidth)
            return lineWidth
        
        lineWidth = 0.0
        pdeb = False
        if pdeb : print("-----------")
        for k in j.keys():
            if pdeb : print("key: ",k )
            
            try:
                s = j[k].replace('\\n',"\n\t")
                if pdeb : print("    ",s)
            except:
                for s in j[k]:
                    s = s.replace('\\n',"\n\t")
                    if pdeb : print("    >>[",s,"]<<")
                    
                    try:
                        si = s.index("line_width = ")
                        if si != -1:
                            si+= 13
                            le = s[si:].index("\n")
                            if pdeb : print("got it !!![",s[si:si+le],"]")
                            lineWidth = float(s[si:si+le])
                            
                    except:
                        pass
                    
        if lineWidth != 0.0:
            print("from setting extract line width: {0} [mm]".format(lineWidth))     
        else:
            print("EE - no line width !!!")
            sys.exit(11)
        return lineWidth
    
    
    def lookForFilamentWidth(self, lines):
        print("- lookForFilamentWidth")
        curaSetStr = ""
        for l in lines:
            if l.line[:11] == ";SETTING_3 ":
                curaSetStr += l.line[11:]
        
        
        #print("",curaSetStr)
        try:
            j = json.loads(curaSetStr)
        except:
            print("EE - no cura file ? no setting_3 part")
            filamentWidth = 0.8
            print("II - setting default ",filamentWidth)
            return filamentWidth
        
        filamentWidth = 0.0
        pdeb = False
        if pdeb : print("-----------")
        for k in j.keys():
            if pdeb : print("key: ",k )
            
            try:
                s = j[k].replace('\\n',"\n\t")
                if pdeb : print("    ",s)
            except:
                for s in j[k]:
                    s = s.replace('\\n',"\n\t")
                    if pdeb : print("    >>[",s,"]<<")
                    
                    try:
                        si = s.index("material_diameter = ")
                        if si != -1:
                            si+= 20
                            le = s[si:].index("\n")
                            if pdeb : print("got it !!![",s[si:si+le],"]")
                            filamentWidth = float(s[si:si+le])
                            
                    except:
                        pass
                    
        if filamentWidth != 0.0:
            print("from setting extract filament width: {0} [mm]".format(filamentWidth))     
        else:
            print("EE - no filament width !!!")
            filamentWidth = 2.75
            print("II - setting filament to {} mm".format(filamentWidth))
            
        return filamentWidth
    
    
    def lookForLayerHeight(self, lines):
        print("- lookForLayerHeight")
        curaSetStr = ""
        for l in lines:
            if l.line[:11] == ";SETTING_3 ":
                curaSetStr += l.line[11:]
        
        layerHeight = 0.0
        s = curaSetStr
        try:
            t = s.split("layer_height_0")
            t = t[1].split("=")
            t = t[1].split('\\\\')
            t = t[0]
            lh = float(t)
            layerHeight = lh
                    
        except:
            print("EE - no layer height 0 info in settings")
            pass
        
        if layerHeight != 0.0:
            print("from setting extract layer height: {} [mm]".format( layerHeight ))     
        else:
            print("EE - no layer height !!!")
            layerHeight = 0.6
            print("II - setting it from default to ",layerHeight,"mm")
        return layerHeight
    
    
    
    
    