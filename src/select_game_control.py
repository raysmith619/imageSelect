# command_file.py
"""
Game Control - parameters and such
Facilitates setting and display of game controls
"""
from tkinter import *
import re
import os

from select_error import SelectError
from select_trace import SlTrace


    

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise SelectError('Not a recognized Boolean value %s' % v)
    
    
    
class SelectGameControl(Toplevel):
    CONTROL_NAME_PREFIX = "game_control"
    DEF_WIN_X = 500
    DEF_WIN_Y = 300
    
    def __init__(self, play_control=None,
                control_prefix=None,
                title=None,
                display=True
                 ):
        """ Control attributes
        :title: window title
        """
        self.play_control = play_control
        if control_prefix is None:
            control_prefix = self.CONTROL_NAME_PREFIX
        self.control_prefix = control_prefix
        self.mw = Toplevel()
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        if title is None:
            title = "Game Control"
        self.title = title
        self.ctls = {}          # Dictionary of field control widgets
        self.ctls_vars = {}     # Dictionary of field control widget variables

        top_frame = Frame(self.mw)
        top_frame.pack(side="top", fill="x", expand=True)
        self.top_frame = top_frame
        
        self.base_frame = top_frame     # Changed on use
        self.base_field = "game_control"
        
        
        
        if display:
            self.control_display()

    def set_play_control(self, play_control):
        """ Link ourselves to the display
        """
        self.play_control = play_control
        
            
    def control_display(self):
        """ display /redisplay controls to enable
        entry / modification
        """
        self.mw.title(self.title)
        top_frame = Frame(self.mw)
        top_frame.pack(side="top", fill="x", expand=True)
        self.top_frame = top_frame
        
        controls_frame = Frame(top_frame)
        controls_frame.pack(side="top", fill="x", expand=True)
        self.controls_frame = controls_frame

        
        running_frame = Frame(controls_frame)
        running_frame.pack()
        running_frame1 = Frame(running_frame)

        running_frame2 = Frame(running_frame)
        
        self.set_fields(running_frame1, "running", title="Running")
        self.set_check_box(field="loop")
        self.set_entry(field="loop_after", label="After", value=5, width=4)
        self.set_sep()
        self.set_button(field="new_game", label="New Game", command=self.new_game)
        self.set_sep()
        self.set_button(field="stop_game", label="Stop Game", command=self.stop_game)

        self.set_fields(running_frame2, "running", title="")
        self.set_button(field="run", label="Run", command=self.run_game)
        self.set_button(field="pause", label="Pause", command=self.pause_game)
        self.set_sep()
        self.set_entry(field="speed_step", label="Speed step", value=-1, width=4)
        
        scoring_frame = Frame(controls_frame)
        self.set_fields(scoring_frame, "scoring", title="Scoring")
        self.set_check_box(field="run_reset", label="Run Resets", value=True)
        self.set_button(field="reset_score",label="Reset Scores", command=self.reset_score)
        self.set_sep()
        self.set_check_box(field="show_ties", label="Show Ties", value=True)

        
        viewing_frame = Frame(controls_frame)
        self.set_fields(viewing_frame, "viewing", title="Viewing")
        self.set_entry(field="columns", label="columns", value=5, width=3)
        self.set_entry(field="rows", label="rows", value=5, width=3)
        
        self.arrange_windows()

    """ Control functions for game control
    """
    def new_game(self):
        self.set_vals()
        if self.play_control is not None:
            self.play_control.new_game("New Game")

    def reset_score(self):
        """ Reset multi-game scores/stats, e.g., games, wins,..
        """
        if self.play_control is not None:
            self.play_control.reset_score()

    
    def stop_game(self):
        self.set_vals()
        if self.play_control is not None:
            self.play_control.stop_game("Stop Game")

    
    def set_vals(self):
        """ Read form, if displayed, and update internal values
        """
        for field in self.ctls_vars:
            self.set_val_from_ctl(field)

    def set_val_from_ctl(self, field_name):
        """ Set ctls value from field
        Also updates player value properties
        :field_name: field name
        """
        ctl_var = self.ctls_vars[field_name]
        if ctl_var is None:
            raise SelectError("No variable for %s" % field_name)
        
        value = ctl_var.get()
        self.set_prop_val(field_name, value)


    def run_game(self):
        self.set_vals()
        if self.play_control is not None:
            self.play_control.run_cmd()

    def pause_game(self):
        self.set_vals()
        if self.play_control is not None:
            self.play_control.pause_cmd()


    def set_fields(self, base_frame, base_field, title=None):
        """ Set current control area
        :frame: current frame into which controls go
        :base_field: base for variables/widgets are stored
        """
        base_frame.pack()
        self.base_frame = base_frame
        self.base_field = base_field
        if title is None:
            title = base_field
        if title != "":
            wlabel = Label(base_frame, text=title, anchor=W)
            wlabel.pack(side="left", anchor=W)
            self.set_text("   ")
        

    def set_text(self, text, frame=None):
        """ Add text to current location/frame
        :text: text string to add
        :frame: frame into add default: base_frame
        """
        if frame is None:
            frame = self.base_frame
        wlabel = Label(frame, text=text, anchor=W)
        wlabel.pack(side="left", anchor=W)


    def set_sep(self, frame=None):
        """ Add default separator
        :frame:  destination frame
        """
        if frame is None:
            frame = self.base_frame
        self.set_text("  ", frame=frame)


    def set_check_box(self, frame=None, field=None,
                        label=None, value=False):
        """ Set up check box for field
        :field: local field name
        :label: button label - default final section of field name
        :value: value to set
        """
        if frame is None:
            frame = self.base_frame
        if label is None:
            label = field
            
        if label is not None:
            wlabel = Label(frame, text=label)
            wlabel.pack(side="left")
        content = BooleanVar()
        full_field = self.field_name(field)
        value = self.get_prop_val(full_field, value)
        content.set(value)
        widget =  Checkbutton(frame, variable=content)
        widget.pack(side="left", fill="none", expand=True)
        self.ctls[full_field] = widget
        self.ctls_vars[full_field] = content
        self.set_prop_val(full_field, value)


    def set_entry(self, frame=None, field=None,
                        label=None, value=None,
                        width=None):
        """ Set up check box for field
        :frame: containing frame
        :field: relative field name (after self.base_field)
        :label: field label default: no label
        :value: value to set, iff not in properties
        """
        if frame is None:
            frame = self.base_frame
        content = StringVar()
        full_field = self.field_name(field)
        value = self.get_prop_val(full_field, value)
        content.set(value)
        if label is not None:
            wlabel = Label(frame, text=label)
            wlabel.pack(side="left")
            
        widget =  Entry(frame, textvariable=content, width=width)
        widget.pack(side="left", fill="none", expand=True)
        self.ctls[full_field] = widget
        self.ctls_vars[full_field] = content
        self.set_prop_val(full_field, value)


    def set_button(self, frame=None, field=None,
                        label=None, command=None):
        """ Set up check box for field
        :frame: containing frame, default self.base_frame
        :field: field name
        :label: button label - default: field
        :command: command to execute when button pressed
        """
        if frame is None:
            frame = self.base_frame
        if label is None:
            label = field
        widget =  Button(frame, text=label, command=command)
        widget.pack(side="left", fill="none", expand=True)
        full_field = self.field_name(field)
        self.ctls[field] = widget
        # No variable

    def field_name(self, *fields):
        """ Create basic field name from list
        :fields: set of field segments
        """
        field_name = self.base_field
        for field in fields:
            if field_name != "":
                field_name += "."
            field_name += field
        return field_name
            
    def win_size_event(self, event):
        """ Window sizing event
        """
        win_x = self.mw.winfo_x()
        win_y = self.mw.winfo_y()
        win_width = self.mw.winfo_width()
        win_height = self.mw.winfo_height()
        self.resize_window(win_x, win_y, win_width, win_height)

        
    def resize_window(self, x, y, width, height, change=False):
        """ Size our window
        :change: True force window resize
        """
        self.set_prop_val("win_x", x)
        self.set_prop_val("win_y", y)
        self.set_prop_val("win_width", width)
        self.set_prop_val("win_height", height)
        if SlTrace.trace("resize_window"):
            if ( not hasattr(self, "prev_x") or self.prev_x != x
                 or not hasattr(self, "prev_y") or self.prev_y != y
                 or not hasattr(self, "prev_width") or self.prev_width != width
                 or not hasattr(self, "prev_height") or self.prev_height != height):
                SlTrace.lg("resize_window change=%d x=%d y=%d width=%d height=%d" % (change, x,y,width,height))
            self.prev_x = x 
            self.prev_y = y
            self.prev_width = width
            self.prev_height = height
        if change:
            geo_str = "%dx%d+%d+%d" % (x, y, width, height)
            self.mw.geometry(geo_str)
    
    def arrange_windows(self):
        """ Arrange windows
            Get location and size for properties if any
        """
        win_x = self.get_prop_val("win_x", self.DEF_WIN_X)
        if win_x < 0:
            win_x = 50
        win_y = self.get_prop_val("win_y", self.DEF_WIN_Y)
        if win_y < 0:
            win_y = 50
        
        win_width = self.get_prop_val("win_width", self.mw.winfo_width())
        win_height = self.get_prop_val("win_height", self.mw.winfo_height())
        self.resize_window(win_width, win_height, win_x, win_y, change=True)
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        self.mw.bind('<Configure>', self.win_size_event)
       
    
    def get_prop_key(self, name):
        """ Translate full control name into full Properties file key
        """        
        key = self.control_prefix + "." + name
        return key

    def get_prop_val(self, name, default):
        """ Get property value as (string)
        :name: field name
        :default: default value, if not found
        :returns: "" if not found
        """
        prop_key = self.get_prop_key(name)
        prop_val = SlTrace.getProperty(prop_key)
        if prop_val is None or prop_val == "":
            return default
        if isinstance(default, bool):
            bv = str2bool(prop_val)
            return bv
        
        if isinstance(default, int):
            if prop_val == "":
                return 0
            try:
                prop_val = int(prop_val)
            except:
                try:
                    prop_val = float(prop_val)
                except:
                    prop_val = 0
                    
            return int(prop_val)
        
        if isinstance(default, float):
            if prop_val == "":
                return 0.
           
            return float(prop_val)
        else:
            return prop_val



    def set_ctl(self, field_name, value):
        """ Set field, given value
        Updates field display and properties value
        :field_name: field name
        :value:        value to set
        """
        if field_name not in self.ctls_vars:
            raise SelectError("Control has no field variable %s" % field_name)
        ctl_var = self.ctls_vars[field_name]
        ctl_var.set(value)
        self.set_prop_val(field_name, value)           # Update properties



    def set_prop_val(self, name, value):
        """ Set property value as (string)
        :name: field name
        :value: default value, if not found
        """
        prop_key = self.get_prop_key(name)
        SlTrace.setProperty(prop_key, str(value))



    def destroy(self):
        """ Destroy window resources
        """
        if self.mw is not None:
            self.mw.destroy()
        self.mw = None
        
        
    def delete_window(self):
        """ Handle window deletion
        """
        if self.play_control is not None:
            self.play_control.close_score_window()
        else:
            self.destroy()
            quit()
            SlTrace.lg("Properties File: %s"% SlTrace.getPropPath())
            SlTrace.lg("Log File: %s"% SlTrace.getLogPath())
            sys.exit(0)

        self.play_control = None

    
if __name__ == '__main__':
        
    root = Tk()
    root.withdraw()       # Hide main window

    SlTrace.setProps()
    cF = SelectGameControl(None, title="SelectGameControl Testing", display=True)
    ##cF.open("cmdtest")
        
    root.mainloop()