import tkinter as tkinter
root = tkinter.Tk()
def onFormEvent( event ):
    width = root.winfo_width()
    height = root.winfo_height()
    x = root.winfo_x()
    y = root.winfo_y()
    print("x: %d y:%d height:%d width: %d" % (x, y, width, height))

lblText = tkinter.Label( root, text='window positioning/sizing tester' )
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
