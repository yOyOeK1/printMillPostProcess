
class GPoint:
    
    def __init__( self, orgLine, id, g, x, y, z, e, f, other = "", comment = "" ):
        self.orgLine = orgLine
        self.id = id
        self.g = g
        self.x = x
        self.y = y
        self.z = z
        self.e = e
        self.f = f
        self.other = other
        self.comment = comment