# command_file.py
"""
Command File PROCESSING
Facilitates reading human readable commands from files
Specifying input/output file names
Specifying execution parameters such as:
    delay before command execution
    delay after command execution
Executing programs from files
    Stepping through program
Generating listing file
"""
from tkinter import filedialog
from tkinter import *
import re
import os

from select_error import SelectError
from select_trace import SlTrace
from Tools.scripts.nm2def import NM


class SelectLangCmd:
    def __init__(self, name):
        self.name = name
        self.args = []
        
    def __str__(self):
        return self.name

class SelectToken:
    def __init__(self, name):
        self.name = name
        self.args = []
        
    def is_cmd(self):
        return True
    
    
    
class CommandFile(Toplevel):
    CONTROL_NAME_PREFIX = "command_file"
    def __init__(self,
                 parent=None,
                 title=None,
                 in_file=None,
                 src_file_name = None,
                 src_dir = None,
                 lst_file_name = None,
                 cmd_execute=None,
                 display=True
                 ):
        """ Player attributes
        :title: window title
        :in_file: Opened input file handle, if one
        :src_file_name: source file name
        :src_dir: default src directory
                default: "csrc"
        :lst_file_name: listing file name
                default: base name of src_file_name
                        ext: ".clst"
        :cmd_execute: function to be called to execute command
        """
        if parent is None:
            parent = Tk()
        self.parent = parent
        if title is None:
            title = "CommandFile"
        self.title = title
        self.src_file_name = src_file_name
        if src_dir is None:
            src_dir = "../csrc"
        self.src_dir = src_dir
        self.lineno = 0         # Src line number
        self.in_file = in_file
        self.ctls = {}          # Dictionary of field control widgets
        self.ctls_vars = {}     # Dictionary of field control widget variables
        self.cmd_execute = cmd_execute
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

        dir_frame = Frame(controls_frame)
        field = "src_dir_name"
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


    def src_dir_search(self):
        start_dir = self.src_dir
        filedir =  filedialog.askdirectory(
            initialdir = start_dir,
            title = "Select dir")
        name = filedir
        self.src_file_name = name
        self.set_ctl_val("src_dir_name", name)


    def src_file_search(self):
        start_dir = self.src_dir
        filename =  filedialog.askopenfile("r",
            initialdir = start_dir,
            title = "Select file",
            filetypes = (("csrc files","*.csrc"),("all files","*.*")))
        fullname = filename.name
        dir_name = os.path.dirname(fullname)
        base_name = os.path.basename(fullname)
        self.src_dir = dir_name
        self.set_ctl_val("src_dir_name", dir_name)
        self.src_file_name = base_name
        self.set_ctl_val("src_file_name", base_name)
        filename.close()

    def run_file(self):
        """
        Run command filr
        """
        SlTrace.lg("run_file")
        src_file_name = self.get_val_from_ctl("src_file_name")
        if re.match(r'^\s*$', src_file_name) is not None:
            SlTrace.lg("Blank src file name - ignored")
            return
        
        if not self.open(src_file=src_file_name):
            SlTrace.lg("Can't open src_file %s"
                       % (src_file_name))
            return
        
        while True:
            cmd = self.get_cmd()
            if cmd is None:
                break
            SlTrace.lg("cmd: %s" % cmd, "cexecute")
            if self.cmd_execute is not None:
                self.cmd_execute(cmd)
            
        


    def run_step_file(self):
        """
        steep command filr
        """
        SlTrace.lg("run_step_file")

    
    def get_prop_key(self, name):
        """ Translate full  control name into full Properties file key
        """
        
        key = (CommandFile.CONTROL_NAME_PREFIX
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

    def open(self, src_file=None):
        """ Open command file
        Opens output files, if specified
        :src_file: Source file default, if no extension ext="csrc"
        """
        if src_file is None:
            src_file = self.src_file_name
        if src_file is None:
            src_file = "test_csrc"
        if re.search(r'\.\w+$', src_file) is None:
            src_file += ".csrc"     # Default extension
        if not os.path.isabs(src_file):
            src_file = os.path.join(self.src_dir, src_file)
            if not os.path.isabs(src_file):
                src_file = os.path.abspath(src_file)
        self.src_file = src_file
        try:
            self.in_file = open(self.src_file, "r")
        except IOError as e:
            errno, strerror = e.args
            SlTrace.lg("Can't open command source file %s: %d %s"
                              % (self.src_file, errno, strerror))
            return False
        
        return True
    
    
    def get_cmd(self):
        """ Get next command
        :returns: cmd, None on EOF
        """
        while True:
            tok = self.get_tok()
            if tok is None:
                return None
            if tok.is_cmd():
                break
        return SelectLangCmd(tok.name)
    

    def get_tok(self):
        """ Get next input token
        Ignores comments
        One token per line
        """
        while True:
            line = self.get_line()
            if line is None:
                return None
            lm = re.match(r'^(.*?)\s*#', line)
            if lm is not None:
                line = lm.group(1)
            if re.match(r'^\s*$', line) is not None:
                continue
            break
        return SelectToken(name=line)


    def get_line(self):
        """ Get next source line
        """
        line = self.in_file.readline()
        if line is None or line == "":
            SlTrace.lg("Src EOF", "csrc")
            return None
        else:
            line = line.rstrip()
            self.lineno += 1
            if SlTrace.trace("csrc"):
                SlTrace.lg("%s %d: %s"
                           % (os.path.basename(self.src_file),
                              self.lineno, line))
        return line

    
if __name__ == '__main__':
        
    root = Tk()

    frame = Frame(root)
    frame.pack()
    SlTrace.setProps()
    SlTrace.setFlags("csrc")
    cF = CommandFile(frame, title="ComandFIle", display=True)
    ##cF.open("cmdtest")
        
    root.mainloop()