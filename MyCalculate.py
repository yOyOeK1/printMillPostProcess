
import math
import copy
#from GPoint import *

class SPoint:
    def __init__(self,x,y):
        self.x = x
        self.y = y

class MyCalculate:
    
    
    
    def findIntersection(self, x1, y1, x2, y2, x3, y3, x4, y4 ):
        px= ( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) ) 
        py= ( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) )
        return [px, py]
    
    def distance(self, p0, p1):
        if p0.x and p0.y and p1.x and p1.y:
            return math.sqrt((p1.x - p0.x)**2 + (p1.y - p0.y)**2)
        return None
    
    
    def angle( self, p0, p1, p2 = None):
        if p2==None:
            deltax = p1.x- p0.x
            deltay = p1.y- p0.y
            a = math.atan2(deltay,deltax)
            return math.degrees(a)
            
        else:
            a0 = self.angle(p1, p2)
            a1 = self.angle( p1, p0)
            if a0>=a1:
                a =  a0 - a1
            else:
                a = a1 - a0 
            return a
    
    def newPoint(self, 
        pStart, pEnd, 
        dist, 
        addAngle=0.0,
        returnAngle = False
        ):
        
        
        ang = self.angle(pStart, pEnd)+addAngle
        xn = pStart.x + dist*math.cos( math.radians(ang) )
        yn = pStart.y + dist*math.sin( math.radians(ang))
        
        pc = copy.copy(pEnd)
        pc.x = xn
        pc.y = yn
        
        if returnAngle:
            print("ang",png)
            return pc,ang
        else:
            return pc
        
    
    
    def scale(self, a, b):
        return a/b
    
    def scaleForOffset(self, xo, yo, scale, step, tpx, tpy ):
        w = tpx
        h = tpy
        
        xoff = ((xo-w)/scale)
        yoff = ((yo-h)/scale)
        
        scale*=step
        
        xo = (xoff * scale)+w
        yo = (yoff * scale)+h
    
        return [scale, xo, yo]
    
    def mRound(self, val, accu):
        return round(val,accu)
        