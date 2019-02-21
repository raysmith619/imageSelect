"""
Created on September 18, 2018

@author: raysm
"""
import math
from cmath import rect
import os
import sys
from tkinter import *    
import argparse
from PIL import Image, ImageDraw, ImageFont
from select_area import SelectRegion


nx = 5              # Number of x divisions
ny = nx             # Number of y divisions
show_id = False     # Display component id numbers
show_moved = True   # Display component id numbers
width = 600         # Window width
height = width      # Window height

parser = argparse.ArgumentParser()

parser.add_argument('--nx=', type=int, dest='nx', default=nx)
parser.add_argument('--ny=', type=int, dest='ny', default=ny)
parser.add_argument('--show_id', type=bool, dest='show_id', default=show_id)
parser.add_argument('--show_moved', type=bool, dest='show_moved', default=show_moved)
parser.add_argument('--width=', type=int, dest='width', default=width)
parser.add_argument('--height=', type=int, dest='height', default=height)
args = parser.parse_args()             # or die "Illegal options"

nx = args.nx
ny = args.ny
show_id = args.show_id
show_moved = args.show_moved
width = args.width
height = args.height

print("%s %s\n" % (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])))
print("args: %s\n" % args)





rect1 = ((width*.1, height*.1), (width*.5, height*.5))
rect2 = ((width*.5, height*.5), (width*.9, height*.9))
rects =  []
###rects.append(rect1)
###rects.append(rect2)
xmin = .1*width
xmax = .9*width
xlen = (xmax-xmin)/nx
ymin = .1*height
ymax = .9*height
ylen = (ymax-ymin)/ny
for i in range(nx):
    x1 = xmin + i*xlen
    x2 = x1 + xlen
    for j in range(ny):
        y1 = ymin + j*ylen
        y2 = y1 + ylen
        rect = ((x1, y1), (x2, y2))
        rects.append(rect)
        
im = Image.new("RGB", (width, height))
frame = Frame(width=width, height=height, bg="", colormap="new")
frame.pack()
canvas = Canvas(frame, width=width, height=height)
canvas.pack()   
sr = SelectRegion(canvas, im, rects=rects,
                  show_moved=show_moved, show_id=show_id)
sr.display()
mainloop()