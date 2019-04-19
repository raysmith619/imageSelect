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
Facilitate integration with game program by
 1. open - open input file
 2. get_cmd - return next command for action by game functions
 
"""
from tkinter import filedialog
from tkinter import *
import re
import os

from select_error import SelectError
from select_trace import SlTrace
from Tools.scripts.nm2def import NM
from pdb import TESTCMD


class SelectStreamCmd:
    DOC_STRING = "DOC_STRING"          # Special commands
    NULL_CMD = "NULL_CMD"
    EOF = "EOF"                         # End of file
    
    def __init__(self, name, args=None):
        self.name = name.lower()        # case insensitive
        self.args = []
        for arg in args:
            self.args.append(arg)

        
        
    def __str__(self):
        string = self.name
        if self.args:
            for arg in self.args:
                if arg.type == SelectStreamToken.NUMBER:
                    st = arg.str
                elif arg.type == SelectStreamToken.QSTRING:        
                    st = arg.delim + arg.str + arg.delim
                else:
                    st = arg.str
                string += " " + st
        return string

class SelectStreamToken:
    WORD = "WORD"                # Token type
    QSTRING = "QSTRING"
    NUMBER = "NUMBER"
    PUNCT = "PUNCT"
    SEMICOLON = "SEMICOLON"
    PERIOD = "PERIOD"
    EOL = "EOL"                 # End of line
    COMMENT = "COMMENT"             # comment (not passed by get_tok())
    
    def __init__(self, type, str=None, doc_string=False, delim=None):
        self.type = type
        self.str = str
        self.doc_string = doc_string    # Python like doc string
        self.delim = delim              # iff quoted

    
    def __str__(self):
        string = self.type
        string += self.str
        return string
    

    def is_cmd(self):
        return True
    
    
    
class CommandFile(Toplevel):
    CONTROL_NAME_PREFIX = "command_file"
    def __init__(self,
                 parent=None,
                 run=False,
                 run_cmd=None,
                 title=None,
                 in_file=None,
                 src_file_name = None,
                 src_dir = None,
                 src_lst = False,
                 stx_lst = False,
                 lst_file_name = None,
                 cmd_execute=None,
                 display=True
                 ):
        """ Player attributes
        :title: window title
        :in_file: Opened input file handle, if one
        :src_file_name: source file name
        :run: run file after opening
                default: False
        :run_cmd: command to run when run button hit
                default: self.run
        :src_dir: default src directory
                default: "csrc"
        :src_lst: List src as run
                    default: No listing
        :stx_lst: List expanded commands as run
                    default: No listing
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
        self.src_lst = src_lst
        self.stx_lst = stx_lst
        self.run = run
        self.run_cmd = run_cmd
        self.lineno = 0         # Src line number
        self.in_file = in_file
        self.ctls = {}          # Dictionary of field control widgets
        self.ctls_vars = {}     # Dictionary of field control widget variables
        self.cmd_execute = cmd_execute
        self.stcmd_stack = []   # get/unget stcmd stack
        self.tok = None         # Token if found
        self.line = None    # Remaining unparsed line
        self.src_prefix = ""    # Source listing prefix
        if src_file_name is not None:
            self.set_ctl_val("src_file_name", src_file_name)
       
        if display:
            self.control_display()
        if self.run:
            self.run_file()
            
            
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
        if "src_file_entry" not in self.ctls_vars:
            content = self.content_var(str)
            self.ctls_vars[field] = content
        else:
            content = self.ctls_vars[field]
        src_file_entry = Entry(file_frame, textvariable=content, width=width)
        src_file_entry.pack(side="left", fill="x", expand=True)
        self.ctls[field] = src_file_entry
        self.set_ctl_val("src_file_name", self.src_file_name)

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
        run_button = Button(master=run_frame, text="Run", command=self.run_button)
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

    def run_button(self):
        """ Called when our button is pressed
        """
        if self.run_cmd is not None:
            return self.run_cmd()
        
        return self.run_file()  # Local - default
    
    
    def run_file(self):
        """
        Run command filr (Local version)
        """
        SlTrace.lg("run_file")
        src_file_name = self.get_val_from_ctl("src_file_name")
        if re.match(r'^\s*$', src_file_name) is not None:
            SlTrace.lg("Blank src file name - ignored")
            return
        
        if not self.reset():
            SlTrace.lg("Can't (re)open src_file %s"
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
        Creates field variable if not already present
        :field_name: field name
        :val: value to display
        """
        if field_name not in self.ctls_vars:
            content_var = self.content_var(type(val))
            self.ctls_vars[field_name] = content_var
        self.ctls_vars[field_name].set(val)


    def content_var(self, type):
        """ create content variable of the type val
        :type: variable type
        """
        if type == str:
            var = StringVar()
        elif type == int:
            var = IntVar()
        elif type == float:
            var = DoubleVar()
        elif type == bool:
            var = BooleanVar()
        else:
            raise SelectError("Unsupported content var type %s"
                              % type)
        
        return var

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
        self.eof = False                # Set True at EOF
        try:
            if self.src_lst or SlTrace.trace("csrc"):
                SlTrace.lg("Open %s" % self.src_file)
            self.in_file = open(self.src_file, "r")
        except IOError as e:
            errno, strerror = e.args
            SlTrace.lg("Can't open command source file %s: %d %s"
                              % (self.src_file, errno, strerror))
            return False
        
        return True


    def reset(self):
        """ Reset stream to allow traversing again
            closes current file, if any, reopen
        """
        if (hasattr(self, "in_file")
                and self.in_file is not None
                and self.in_file.is_open()):
            self.in_file.close()
        if not self.open():
            raise("Can't reset command_file")
        
        self.stcmd_stack = []   # get/unget stcmd stack
        self.tok = None         # Token if found
        self.line = None        # Remaining unparsed line
        return True
    
    
    def get_cmd(self):
        """ Get next command: word [[, ] word]* [EOL|;]
         ==> cmd.name == first word
             cmd.args == subsequent words
        :returns: cmd, None on EOF
        """
        if self.stcmd_stack:
            stcmd = self.stcmd_stack.pop()
            return stcmd

        toks = []
        tok = None
        while True:
            tok = self.get_tok()
            if tok is None:
                break       # EOF
            if (tok.type == SelectStreamToken.EOL
                or tok.type == SelectStreamToken.SEMICOLON):
                if not toks:
                    continue        # Ignore if no cmd started
                break       # End of command
            if tok.type == SelectStreamToken.QSTRING:
                if len(toks) == 0:
                    toks.append(tok)                # Allow doc_string command
                    break           # Special doc_string cmd
            toks.append(tok)
        
        if len(toks) == 0:
            stcmd =  None
        elif len(toks) == 1 and toks[0].type == SelectStreamToken.QSTRING and toks[0].doc_string:
            stcmd = SelectStreamCmd(SelectStreamCmd.DOC_STRING,
                                    args=toks)     
        else:
            tok = toks.pop(0)
            if not re.match(r'^[_a-z]\w*', tok.str.lower()):
                raise SelectError("'%s' is not a legal stream command name"
                                  % tok.str)
            stcmd = SelectStreamCmd(tok.str.lower(), args=toks)
    
        if self.stx_lst or SlTrace.trace("stx_lst"):
            prefix_base = " " * len(self.src_prefix)    # src name length
            prefix1 = prefix_base + " STCMD:"
            prefix2 = prefix_base + " -----:"    # if subsequent start with this
            cmdstr = str(stcmd)
            cmdstr_lines = cmdstr.splitlines()
            for i in range(len(cmdstr_lines)):
                if i == 0:
                    prefix = prefix1
                else:
                    prefix = prefix2
                SlTrace.lg(prefix + " " + cmdstr_lines[i])
                 
        return stcmd
    

    def get_tok(self):
        """ Get next input token
        Ignores comments(Unquoted # to end of line)
        Tokens end at whitespace, end of line, ";",
            character not part of the token (e.g. ",", ";")
        """
        while True:
            if self.line is None:
                self.line = self.get_line()  # Get next line
            if self.line is None:
                return None                 # EOF
            
                
            self.line = self.line.lstrip()
            if self.get_tok_comment():
                continue                # Ignore comment
            if self.get_tok_word():
                return self.tok
            if self.get_tok_quote():
                return self.tok
            if self.get_tok_number():
                return self.tok
            if self.get_tok_punct():    # incl SEMICOLON, PERIOD
                return self.tok
            if self.get_tok_eol():
                return self.tok


    def get_tok_comment(self):
        """ Check if we are at a comment
        Returns a token, which is can be ignored
            comment format: "#" to rest of line
        """
        if self.line.startswith("#"):
            tok = SelectStreamToken(SelectStreamToken.COMMENT,
                                    str=self.line)
            self.line = ""        # To end of line
            return tok
        
        
    def get_tok_quote(self):
        """ get quoted str ("...." or '....')
                    \<chr> escapes the included character
        :returns: True if token found, result in self.tok
        """
        # Must do multicharacter quote tests
        # before single character quote tests
        if self.get_tok_str(delim='"""', multi_line=True):
            self.tok.doc_string = True
            return True
        
        if self.get_tok_str(delim="'''", multi_line=True):
            self.tok.doc_string = True
            return True
        
        if self.get_tok_str(delim='"'):
            return True
        if self.get_tok_str(delim=("'")):
            return True
 
        return False

    
    def get_tok_str(self, delim=None, multi_line=False, esc='\\'):
        """ Get string, creating a SelectStreamToken in self.tok
        adjusting self.line to after string trailing delimiter
        :delim: String trailing delimiter default: REQUIRED
        :multi_line: string can be multi-line default: single line
        :esc: escape character defaule "\"
        """
        if delim is None:
            raise SelectError("get_tok_str: missing required delim")
        
        line = self.get_line()
        if line is None or not line.startswith(delim):
            self.line = line
            return False
        
        tok_str = ""
        iend = 0
        iend += len(delim)        # Start after beginning delimiter
        line = line[iend:]
        iend = 0
        while True:
            if line is None:
                line = self.get_line()
                iend = 0
            if line is None:
                break               # EOF
            while iend < len(line):
                ch = line[iend]
                if esc is not None and ch == esc:
                    iend += 1
                    if iend >= len(line):
                        ch = "\n"           # Escaped newline
                    else:
                        ch = line[iend]
                        iend += 1
                    continue                # Go on to character after escaped
                rem_line = line[iend:]
                if rem_line.startswith(delim): 
                    self.tok = SelectStreamToken(SelectStreamToken.QSTRING,
                                                  str=tok_str,
                                                  delim=delim)
                    iend += len(delim)
                    self.line = line[iend:]
                    return True
                
                ch = line[iend]
                tok_str += ch
                iend += 1
            if multi_line:
                tok_str += "\n"         # Add in newline, separating lines
                line = self.get_line()
                iend = 0
                if line is None:
                    break               # EOF
                continue
            break                       # Single line 
        raise SelectError("Missing delimiter (%s)" % delim)
 
                        
    def get_tok_word(self):
        """ get word from input ([a-z_]\w*)
        :returns: True if token found, result in self.tok
        """
        line = self.line
        if len(line) == 0:
            return False
        ib = 0
        iend = ib
        tok_str = ""
        ch = line[ib]
        if not re.match(r'[a-zA-Z_]', ch):
            return False
        
        tok_str = ch
        iend += 1    
        while iend < len(line):
            ch = line[iend]
            if not re.match(r'\w', ch):
                break       # end of word
            tok_str += ch
            iend += 1
        self.tok = SelectStreamToken(SelectStreamToken.WORD,
                                      str=tok_str)
        self.line = line[iend:]
        return True


    def get_tok_number(self):
        """ get nu ber from input ([+-]?\d*(\.\d*)?
        :returns: True if token found, result in self.tok
        """
        line = self.line
        if len(line) == 0:
            return False
        
        match = re.match(r'^[+-]?(\d+|(\d*\.\d*))', line)
        if not match:
            return False
        
        tok_str = match.group()
        self.tok = SelectStreamToken(SelectStreamToken.NUMBER,
                                     tok_str)
        self.line = line[len(tok_str)+1:]
        return True


    def get_tok_punct(self):
        """ get punctuation non-tokenized, non-whitespace
        :returns: True if token found, result in self.tok
                Checks for ;(SEMICOLON), .(PERIOD)
                    else labeled (PUNCT)
        """
        line = self.line
        if len(line) == 0:
            return False
        
        match = re.match(r'^\S', line)
        if not match:
            return False
        
        tok_str = line[0]
        if tok_str == ";":
            tok_type = SelectStreamToken.SEMICOLON
        elif tok_str == ".":
            tok_type = SelectStreamToken.PERIOD
        else:
            tok_type = SelectStreamToken.PUNCT
                
        self.tok = SelectStreamToken(tok_type,
                                     tok_str)
        self.line = line[len(tok_str)+1:]
        return True


    def get_tok_eol(self):
        """ get End of Line
        :returns: True if token found, result in self.tok
        """
        line = self.line
        if len(line) == 0:
            tok_str = "\n"
            self.tok = SelectStreamToken(SelectStreamToken.EOL,
                                     tok_str)
            self.line = None
            return True
            
        return False
    

    def get_line(self, chomp=True):
        """ Get next source line
            use self.line if not None
            Set self.line to None
        :chomp: Remove EOL iff at end on reading from file
        """
        if self.line is not None:
            line = self.line
            self.line = None
            return line        # Return unprocessed part
        
        if self.eof:
            return None
        
        line = self.in_file.readline()
        if line is None or line == "":
            self.eof = True
            if self.src_lst or SlTrace.trace("csrc"):
                SlTrace.lg("%s: End of File"
                           % (os.path.basename(self.src_file)))
            return None
        
        if chomp:
            if len(line) > 0:
                line = line.splitlines()[0]     # Generic line separator 
        self.lineno += 1
        if self.src_lst or SlTrace.trace("src_lst"):
            self.src_prefix = ("%s %3d:"
                       % (os.path.basename(self.src_file),
                          self.lineno))
            SlTrace.lg("%s %s"
                       % (self.src_prefix,
                          line))
        return line

    
if __name__ == "__main__":
    import os
    import sys
    from tkinter import *    
    import argparse
    from PIL import Image, ImageDraw, ImageFont
    
    
    file = "3down.scrc"             # Number of x divisions
    run = True                      # Number of y divisions
    src_lst = True                  # List source as run
    stx_lst = True                # List Stream Trace cmd
    parser = argparse.ArgumentParser()
    
    parser.add_argument('-f', '--file', default=file)
    parser.add_argument('-r', '--run', action='store_true', default=run,
                        help=("Run program upon loading"
                              " (default:%s" % run))
    parser.add_argument('-l', '--src_lst', action='store_true', default=src_lst,
                        help=("List source as run"
                              " (default:%s" % src_lst))
    parser.add_argument('-x', '--stx_lst', action='store_true', default=stx_lst,
                        help=("List commands expanded as run"
                              " (default:%s" % stx_lst))

    args = parser.parse_args()             # or die "Illegal options"
    
    file = args.file
    src_lst = args.src_lst
    stx_lst = args.stx_lst
    run = args.run
    
    SlTrace.lg("%s %s\n" % (os.path.basename(sys.argv[0]), " ".join(sys.argv[1:])))
    SlTrace.lg("args: %s\n" % args)
        
    root = Tk()
    frame = Frame(root)
    frame.pack()
    SlTrace.setProps()
    SlTrace.setFlags("csrc")
    cF = CommandFile(frame, title="ComandFIle",
                     src_lst=src_lst,
                     stx_lst=stx_lst,
                     src_file_name=file, display=True)
    ##cF.open("cmdtest")
        
    root.mainloop()