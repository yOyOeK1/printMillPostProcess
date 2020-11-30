
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget  

from KCanvasHelper import *
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.core.window import Window

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import random
import _thread
import sys


from kivy.config import Config
Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'left', 10)
Config.set('graphics', 'top',  10)

class RootLayout(BoxLayout):
    def yyySomething(self):
        pass

def setWindowSize():
    Window.size = (200,550)

setWindowSize()

#class gui:
class gui(App):
    
    
    def on_zUp(self):
        print('on_zUp')
        z = self.getZShow()
        for zz in self.parser.zLayers:
            if zz > z:
                z = zz
                break
        self.rl.ids.s_sh_hLayer.value = z
        self.plotFromNewThread()
    
    def on_zDown(self):
        print('on_zDown')
        z = self.getZShow()
        zn = z
        for zz in self.parser.zLayers:
            if zz < z:
                zn = zz
            elif zz == z or zz > z:
                break
        self.rl.ids.s_sh_hLayer.value = zn
        self.plotFromNewThread()
    
    def on_plot(self):
        print("on_plot")
        self.plotFromNewThread()
        
    def on_hLayerChange(self,obj):
        print("on_plot")
        self.plotFromNewThread()
        
    def on_hLayerMove(self,obj):
        self.rl.ids.l_zSlider.text = str(self.getZShow())
        
    
    def plotFromNewThread(self):
        try:
            if self.plotRunning:
                self.plot( self.inFile, self.dVal )
            
        except:
            i = _thread.start_new_thread( self.plot, (self.inFile, self.dVal, ) )
            self.plotRunning = True
    
    def build(self):
        Builder.load_file('layoutMain.kv')
        
        self.pltInit = False
        
        self.title = "Print Mill Post Process - PMPP"
        self.rl = RootLayout()
        
        '''
        self.kc = KCanvasHelper()
        self.bl = BoxLayout( orientation = 'vertical' )
        
        self.blControls = BoxLayout(
            orientation = 'vertical'
            )
        self.bl.add_widget( self.blControls )
        
        btLoadFile = Button(
            text = "Load file",
            on_release = self.on_loadFile
            )
        self.blControls.add_widget(btLoadFile)
        
        self.l_layersCount = Label(text="l_layersCount")
        self.blControls.add_widget( self.l_layersCount )
        
        self.w = Widget()
        self.bl.add_widget( self.w )
        
        self.kc.dClear( self.w.canvas )
        
        #tests 
        if 0:
            imgT = '/home/yoyo/Apps/icons/ico_firma_256_256.png'
            self.kc.dImage( self.w.canvas, 10, 50, imgT)
        
            self.kc.dImage( self.w.canvas, 10, 200, imgT, (32,32))
                
            self.kc.dRectangle( self.w.canvas,
                10,50,5,5, (255,0,0)
                )
            
            self.kc.dLine( self.w.canvas, 0,0, 10,50, 2, (0,255,0) )
        
         
        
        return self.bl
        '''
        
        k = self.parser.zLayers
        print("k",k)
        self.rl.ids.s_sh_hLayer.min = min(k)
        self.rl.ids.s_sh_hLayer.value = min(k)
        self.rl.ids.s_sh_hLayer.max = max(k)
        
        self.plotRunningProcess = False
        self.plotFromNewThread()
        
        d = self.dVal
        self.rl.ids.lAddInf.text = '''
Stock at bottom left:
    {} x {} x {}[mm]

'''.format(
            d['bottomLeft'][0], d['bottomLeft'][1], d['bottomLeft'][2],
             
            )
        
        setWindowSize()
        
        return self.rl
    
    def setParser(self, parser, inFile, dVal):
        self.parser = parser
        self.inFile = inFile
        self.dVal = dVal
        
        
    def getZShow(self):
        zShow = -1.0
        sv = self.rl.ids.s_sh_hLayer.value
        
        #print("show layer on slider ",sv)
        for z in self.parser.zLayers:
            if sv >= z:
                zShow = z
            else:
                break
        #print(" so from slider show:",zShow)
        return zShow
    
    def plotLine(self, ax, paths, 
                 label_=None, 
                 color_=None, 
                 lineWidth_=1.0,
                 linestyle_='-'
                 ):
        if color_ == None:
            color_ = ( random.random(), random.random(), random.random() )
        
        addedLabel = False
        showAllLayers = self.rl.ids.cb_sh_allLayer.active
        zShow = self.getZShow()            
        
        #print("paths",len(paths))
        for i,path in enumerate(paths):
            xs = []
            ys = []
            zs = []
            #print("")
            for ii,l4 in enumerate(path):
                try:
                    if showAllLayers == True or ( showAllLayers == False and zShow == l4['Z'] ):
                        if l4['X'] and l4['Y'] and l4['Z']:
                            xs.append(l4['X'])
                            ys.append(l4['Y'])
                            zs.append(l4['Z'])
                            #if showAllLayers == False:
                            #    print(self.parser.V4lToStr(l4),"    -> ",l4['orgLine'])
                    elif showAllLayers == False and zShow != l4['Z']:
                        #print("zShow {} and l4 is {}".format(zShow,l4['Z']))
                        break
                except:
                    pass
            
            if addedLabel == False and label_ != None:
                ax.plot(xs, ys, zs,
                    color=color_,
                    linewidth=lineWidth_,
                    label=label_,
                    linestyle=linestyle_
                    )
                addedLabel = True
            else:
                ax.plot(xs, ys, zs,
                    color=color_,
                    linewidth=lineWidth_,
                    linestyle=linestyle_
                    )
    
    def plot(self, filePath, dVal):
        print("gui.plot")
        
        if self.plotRunningProcess == True:
            print("    in running ....")
            return 0
        else:
            self.plotRunningProcess = True
            
        
        self.layers= {
            'foam' : 0,
            'outer': 1,
            'offsets90': 0,
            'offset': 1,
            }
        
        self.rl.ids.l_zSlider.text = "{}mm".format(self.getZShow())
        
        
        for c in self.layers.keys():
            #print(c)
            active = self.rl.ids["cb_sh_%sLayer"%c].active
            #print("checkt ?",active)
            self.layers[c] =  1 if active else 0 
        #fig = plt.figure()
        #ax = fig.add_subplot(projection='3d')
        
        
            
        if self.pltInit == False:
            self.fig = plt.figure("Print Mill Post Process - PMPP [{}]".format(filePath))
            self.ax = self.fig.add_subplot(
                2 if self.rl.ids.cb_sh_volume.active else 1,
                1,1,
                projection='3d')
            self.pltInit = True
            fig = self.fig
            ax = self.ax
            
            
             
            #ax.axis('equal')  # list of float or {‘on’, ‘off’, ‘equal’, ‘tight’, ‘scaled’, ‘normal’, ‘auto’, ‘image’, ‘square’}
            #ax.set_proj_type('persp')
            ax.set_aspect(aspect='equal')
            ax.autoscale_view()
            #ax.set_title('Print Mill Post Process - PMPP')
            ax.grid(True)
            
        else:
            ax = self.ax
            fig = self.fig
            ax.clear()
        
        # 0,0,0 axis to show x,y,z
        scaleSize = 10.0
        ax.plot([0,scaleSize], [0,0], [0,0],
                color = 'r',
                linewidth=2.0
                )
        ax.plot([0,0],[0,scaleSize],[0,0],
                color = 'g',
                linewidth=2.0
                )
        ax.plot([0,0],[0,0],[0,scaleSize],
                color = 'b',
                linewidth=2.0
                )
        
        if self.layers['foam']:
            self.plotLine( ax, self.parser.allWorkPathsV4l, 
                       "all foam", 
                       color_ = (0.1, 0.68, 0.5), 
                       lineWidth_=0.38
                       )
        if self.layers['outer']:
            self.plotLine( ax, self.parser.outerWallV4l, 
                       "outer foam", 
                       color_ = (0.5,0.5,1.0),
                       linestyle_="--"
                       )
        if self.layers['offsets90']:
            self.plotLine( ax, self.parser.offsets90LinesV4l,
                       "offsets 90' lines", 
                       color_ = (1.0,0,0),
                       lineWidth_= 0.7
                       )
        if self.layers['offset']:
            self.plotLine( ax, self.parser.offsetsLinesV4l, 
                       "mill path tool D:{}[mm]".format(dVal['mill']['toolD']), 
                       color_ = (0.75,0.5,0.0),
                       lineWidth_= 0.7
                       )
        
        
        
        if self.rl.ids.cb_sh_volume.active:
            print("volume graph !")
            showAllLayers = self.rl.ids.cb_sh_allLayer.active
            zShow = self.getZShow()
            flow = []
            xs = []
            xBase = 0.0 
            volTotal = 0.0
            for path in self.parser.allWorkPathsV4l:
                for p in path[:-1]:
                    if showAllLayers == True or ( showAllLayers == False and zShow == p['Z'] ):
                        xs.append(xBase)
                        flow.append(p['EFlow'])
                        xBase+= p['dist']
            
            try:
                abcea = self.axE
            except:
                self.axE = self.fig.add_subplot(
                    3,1,3)
            self.axE.clear()
            self.axE.plot(xs,flow)
            self.axE.autoscale_view()
            self.axE.grid(True)
            self.axE.set_ylabel("E flow")
            self.axE.set_xlabel("path in mm")
            
           
        
        
        if 1:
            thismanager = plt.get_current_fig_manager()
            thismanager.window.wm_geometry("+300+0")
            ax.legend()
            self.plotRunningProcess = False
            plt.show()
            #fig.canvas.draw()
            #fig.canvas.flush_events()
            #plt.pause(0.1)
        else:
            plt.savefig('/tmp/plt.png')
            self.kc.dImage( 
                self.w.canvas, 
                0, 
                0, 
                '/tmp/plt.png'
                )
    
    def killPlt(self):
        plt.close()
    
    def on_loadFile(self,a):
        print("on_loadFile")
        self.plot()
    
    
    
