# command_file.py
"""
Game Control - parameters and such
Facilitates setting and display of game controls
"""
from tkinter import filedialog
from tkinter import *
import re
import os

from select_error import SelectError
from select_trace import SlTrace
from Tools.scripts.nm2def import NM


    
    
    
class SelectGameControl(Toplevel):
    CONTROL_NAME_PREFIX = "game_control"
    def __init__(self,
                 parent=None,
                 title=None,
                 cmd_execute=None,
                 display=True
                 ):
        """ Player attributes
        :title: window title
        """
        if parent is None:
            parent = Tk()
        self.parent = parent
        if title is None:
            title = "Game Control"
        self.title = title
        self.ctls = {}          # Dictionary of field control widgets
        self.ctls_vars = {}     # Dictionary of field control widget variables
        if display:
            self.control_display()

            
    def control_display(self):
        """ display /redisplay controls to enable
        entry / modification
        """
        win_width =  500
        win_height = 200
        win_x0 = 600
        win_y0 = 100
                    
        self.mw = Toplevel()
        win_setting = "%dx%d+%d+%d" % (win_width, win_height, win_x0, win_y0)

        
        self.mw.geometry(win_setting)
        self.mw.title(self.title)
        top_frame = Frame(self.mw)
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        top_frame.pack(side="top", fill="x", expand=True)
        self.top_frame = top_frame
        
        controls_frame = Frame(top_frame)
        controls_frame.pack(side="top", fill="x", expand=True)
        self.controls_frame = controls_frame

        running_frame = Frame(controls_frame)
        field = "Looping"
        src_dir_label = Label(master=dir_frame,
                               text="Dir", anchor="w",
                               justify=LEFT)
        src_dir_label.pack(side="left", fill="x", expand=True)
        dir_frame.pack(side="top", fill="x", expand=True)
        width = 60
        content = StringVar()
        src_dir_entry = Entry(dir_frame, textvariable=content, width=width)
        src_dir_entry.pack(side="left", fill="x", expand=True)
        self.ctls[field] = src_dir_entry
        self.ctls_vars[field] = content
        
        dir_search_button = Button(master=dir_frame, text="Search",
                                     command=self.src_dir_search)
        dir_search_button.pack(side="left", expand=True)
        if self.src_dir is None:
            self.src_dir = "../csrc"
        self.src_dir = os.path.abspath(self.src_dir)
        self.set_ctl_val("src_dir_name", self.src_dir)


        file_frame = Frame(controls_frame)
        field = "src_file_name"
        src_file_label = Label(master=file_frame,
                               text="Src File", anchor="w",
                               justify=LEFT)
        src_file_label.pack(side="left", fill="x", expand=True)
        file_frame.pack(side="top", fill="x", expand=True)
        width = 15
        content = StringVar()
        src_file_entry = Entry(file_frame, textvariable=content, width=width)
        src_file_entry.pack(side="left", fill="x", expand=True)
        self.ctls[field] = src_file_entry
        self.ctls_vars[field] = content
        
        file_search_button = Button(master=file_frame, text="Search",
                                     command=self.src_file_search)
        file_search_button.pack(side="left", expand=True)

        
        
        field = "new_src_file_name_ckbox"
        content = BooleanVar
        new_src_file_name_ckbox = Checkbutton(file_frame, variable=content, width=None)
        new_src_file_name_ckbox.pack(side="left", fill="x", expand=True)
        self.ctls[field] = new_src_file_name_ckbox
        self.ctls_vars[field] = content
        
        src_file_label = Label(master=file_frame,
                               text="New Src File", anchor="w",
                               justify=LEFT)
        src_file_label.pack(side="left", fill="x", expand=True)
        
        field = "new_src_file_name_entry"
        width = 15
        content = StringVar()
        new_src_file_name_entry = Entry(file_frame, textvariable=content, width=width)
        new_src_file_name_entry.pack(side="left", fill="x", expand=True)
        self.ctls[field] = new_src_file_name_entry
        self.ctls_vars[field] = content
        
        run_frame = Frame(controls_frame)
        run_frame.pack(side="top", fill="x", expand=True)
        run_button = Button(master=run_frame, text="Run", command=self.run_file)
        run_button.pack(side="left", expand=True)
        step_button = Button(master=run_frame, text="Step",
                            command=self.run_step_file)
        step_button.pack(side="left", expand=True)

    
    def get_prop_key(self, name):
        """ Translate full  control name into full Properties file key
        """
        
        key = (SelectGameControl.CONTROL_NAME_PREFIX
                + "."  + "." + name)
        return key


    def get_val(self, field_name):
        """ get value in data field, returning value
        :field_name: - field name = use lower case
        """
        field = field_name.lower()
        if field in self.ctls:
            return self.ctls_vars[field].get()
        
        raise SelectError("SelectPlayerControlEntry.get_val(%s) - no entry: %s"
                           % (field_name, field))

    def get_val_from_ctl(self, field_name):
        """ Get value from field
        Does not set value
        :field_name: field name
        """
        field = field_name.lower()
        if field not in self.ctls_vars:
            raise SelectError("Command has no attribute %s" % field)
        value = self.ctls_vars[field].get()
        return value

    def set_val_from_ctl(self, field_name):
        """ Set value from field
        Also updates value properties
        :field_name: field name
        """
        value = self.get_val_from_ctl(field_name)
        self.set_val(field_name, value)        
        self.set_prop_val(field_name)


    def set_ctl_val(self, field_name, val):
        """ Set control field
        :field_name: field name
        :val: value to display
        """
        if field_name not in self.ctls_vars:
            raise SelectError("Command has no attribute %s" % field_name)
        self.ctls_vars[field_name].set(val)

        

    def set_prop_val(self, field_name):
        """ Update properties value for field, so that properties file
        will contain the updated value
        :field_name: field attribute name
        """
        prop_key = self.get_prop_key(field_name)
        field_value = self.get_val(field_name)
        prop_value = str(field_value)
        SlTrace.setProperty(prop_key, prop_value)
                
       
    def delete_window(self):
        """ Process Control window close
        """
        if self.mw is not None:
            self.mw.destroy()
            self.mw = None

    
if __name__ == '__main__':
        
    root = Tk()

    frame = Frame(root)
    frame.pack()
    SlTrace.setProps()
    SlTrace.setFlags("csrc")
    cF = SelectGameControl(frame, title="SelectGameControl", display=True)
    ##cF.open("cmdtest")
        
    root.mainloop()