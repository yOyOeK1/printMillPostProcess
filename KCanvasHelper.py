
from kivy.graphics import Color, Rectangle, Line
from kivy.core.text import Label as CoreLabel
from kivy.core.image import Image

class KCanvasHelper:
    
    
    def __init__(self):
        print("KCanvasHelper.__init__")
        
        
    def dClear(self, canvas):
        canvas.clear()
        
    def dImage(self, canvas, x, y, imgSrc, size_=( None, None )):
        print("dImage:[",imgSrc,"]")
        img = Image( imgSrc )
        imgTexture = img.texture
        with canvas:
            if size_[0] == None:
                Rectangle(
                    pos = ( x, y ),
                    texture = imgTexture,
                    size = img.size
                    )
            else:
                Rectangle(
                    pos = ( x, y ),
                    texture = imgTexture,
                    size = size_
                    )
        
    def dLine(self, canvas, x0, y0, x1, y1, width_=1.0, rgb=None):
        if rgb == None:
            rgb = [ 100, 100,100 ]
        
        with canvas:
            Color(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
            Line(
                points=[ x0, y0, x1, y1 ],
                width=width_
                )  
    
        
    def dText(self, canvas, x,y,text_,fontSize=12,rgb=None):
        if rgb == None:
            rgb = [ 100, 100,100 ]
        
        label = CoreLabel(
            text=text_,
            color=(0.1,1.0,1.0,0.1),
            font_size = fontSize,
            )
        label.refresh()
        with canvas:
            Rectangle(
                pos=(x,y),
                texture = label.texture,
                size = label.texture.size
                )
        
    
    def dRectangle(self, canvas, x0,y0, x1=None,y1=None,rgb=None):
        if x1 == None:
            x1 = x0+1
        if y1 == None:
            y1 = y0+1
        if rgb == None:
            rgb = [ 100, 100,100 ]
            
        with canvas:
            Color(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
            Rectangle( 
                pos = ( x0, y0 ),
                size = ( x1, y1 ) 
                )
    
    def dPixel(self, canvas, x,y,rgb_=None):
        self.dRectangle( canvas, x,y, rgb=rgb_)
    