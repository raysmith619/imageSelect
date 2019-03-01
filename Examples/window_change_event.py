def onFormEvent( event ):
    for key in dir( event ):
        if not key.startswith( '_' ):
            print('%s=%s' % ( key, getattr( event, key ) ))
    print()

import tkinter as tkinter
root = tkinter.Tk()
lblText = tkinter.Label( root, text='Form event tester' )
lblText.pack()
root.bind( '<Configure>', onFormEvent )
root.mainloop()
"""
Update: Here's what I learned about the following events:

event.type == 22 (one or more of following changed: width, height, x, y)

event.type == 18 (minimized) event.widget.winfo_viewable() = 0 (invisible)

event.type == 19 (restore after minimized)

event.type == 2 (maximize)

event.type == 22 (restore after maximized due to change in width and height)
"""
