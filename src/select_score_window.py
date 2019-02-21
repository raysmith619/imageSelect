# select_score_window.py    21-Feb_2019  crs
"""
Window control for display of game score_window
"""
from tkinter import *

from select_trace import SlTrace
from select_error import SelectError
            
        
class ScoreWindow:
    
    def __init__(self, play_control):
        """ Setup score /undo/redo window
        """
        self.play_control = play_control
        move_win_x0 = 750
        move_win_y0 = 650
        geo = "+%d+%d" % (move_win_x0, move_win_y0)
        self.mw = Tk()
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
    
        self.mw.geometry(geo)
        move_frame = Frame(self.mw)
        move_frame.pack()
        move_no_frame = Frame(move_frame)
        move_no_frame.pack()
        move_no = 0
        move_no_str = "Move: %d" % move_no
        move_font = ('Helvetica', '25')
        self.move_no_label = Label(move_no_frame,
                              text=move_no_str,
                              font=move_font
                              )
        self.move_no_label.pack(side="left", expand=True)
        ###move_no_label.config(width=2, height=1)
        bw = 5
        bh = 1
        undo_font = ('Helvetica', '50')
        undo_button = Button(master=move_frame, text="Undo",
                            font=undo_font,
                            command=self.undo_button)
        undo_button.pack(side="left", expand=True)
        undo_button.config(width=bw, height=bh)
        redo_button = Button(master=move_frame, text="ReDo",
                             font=undo_font,
                            command=self.redo_button)
        redo_button.pack(side="left", expand=True)
        redo_button.config(width=bw, height=bh)
    
        ###self.setup_score_window(move_no_label=move_no_label)
        self.update_window()


    def destroy(self):
        """ Destroy window resources
        """
        if self.mw is not None:
            self.mw.destroy()
        
    def delete_window(self):
        """ Handle window deletion
        """
        self.play_control.close_score_window()
        
    
    def update_window(self):
        if self.mw is None:
            return
        
        if self.move_no_label is not None:
            scmd = self.play_control.get_last_cmd()
            if scmd is None:
                self.move_no_label.config(text="Start")
            else:
                move_no_str = "Move: %d" % scmd.move_no
                self.move_no_label.config(text=move_no_str)


        
        
    def undo_button(self):
        SlTrace.lg("undoButton")
        res = self.play_control.undo()
        return res
                
        
    def redo_button(self):
        SlTrace.lg("redoButton")
        res = self.play_control.redo()
        return res
