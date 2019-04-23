# dots_commands.py
"""
Python command support  for dots game for python file Execution
"""
import sys
import traceback

from select_error import SelectError
from select_trace import SlTrace

dC = None               # Global reference, set by CommandFile
class DotsCommands:
    """ The hook from commands expressed via python command files to 
    the dots frame worker
    """
    @classmethod
    def get_DotsCommands(cls):
        return dC
    
        
    def __init__(self, cmd_stream, play_control=None):
        """
        :cmd_stream: link to command input file/stream REQUIRED
        :play_control: link to game commands
        """
        global dC                       # Static link to dots commands
        self.cmd_stream = cmd_stream
        self.play_control = play_control
        self.debugging = False
        self.debugging_res = True       # Default debugging
        self.new_file = True
        dC = self                       # set link to dots commands


    def set_play_control(self, play_control, cmd_stream_proc):
        """ Connect command stream processing to game control
        :play_control:  game control
        :cmd_stream_proc: adjunct cmd processor
        """
        self.play_control = play_control
        self.cmd_stream_proc = cmd_stream_proc

        
    def ck(self):
        """ Check command.
        Executed at beginning of each language command
        Check with hasattr because attribute is only
        created when called with links
        :returns: True if should SKIP rest of this cmd processing
        """
        if dC is None or not hasattr(dC, "cmd_stream"):
            raise SelectError("Missing required cmd_stream")
        
        if self.cmd_stream.src_lst:
            if self.new_file:
                with open(self.cmd_stream.src_file_path) as f:
                    self.src_lines = f.readlines()
                    self.src_line_prev = -1 # previously listed
                    self.new_file = False
            """ List portion of source file, after previous(index) to and including
            the line in the source file found in the stack
            """
            ###etype, evalue, tb = sys.exc_info()
            ###tbs = traceback.extract_tb(tb)
            tbs = traceback.extract_stack()
            src_lineno = None       # set if found
            for tbfr in tbs:         # skip bottom (in dots_commands.py)
                if tbfr.filename == self.cmd_stream.src_file_path:
                    src_lineno = tbfr.lineno
            if src_lineno is not None:
                src_line_index = src_lineno-1
                for idx in range(self.src_line_prev+1, src_line_index+1):
                    if idx >= len(self.src_lines):
                        break
                    lineno = idx + 1
                    src_line = self.src_lines[idx].rstrip()
                    SlTrace.lg("   %4d: %s" % (lineno, src_line))
                    self.src_line_prev = idx        # Update as printed
        if self.debugging:
            return True            # Skip action because debugging        
        
        if self.play_control is None:
            raise SelectError("DotsCommands play_control link is missing")
        
        return False                # No reason to skip rest, do it
    
    
    def ck_res(self):
        """ debugging ck return
        """
        return self.debugging_res

    def set_debugging(self, debugging = True):
        """ Set to debug command language, elimiting
        action requiring full game
        """
        self.debugging = debugging
        DotsCommands.play_control = None    # Suppress ck eror
        
    
    """
    Dots commands
    """
    
    def lg(self, *args, **kwargs):
        self.ck()  # No debugging
        return SlTrace.lg(*args, **kwargs)
    
    def set_playing(self, *args, **kwargs):
        if self.ck():
            return self.ck_res()    # Debugging short circuit
        
        return self.cmd_stream_proc.set_playing(*args, **kwargs)

    def enter(self):
        if self.ck():
            return self.ck_res()    # Debugging short circuit
        
        return self.cmd_stream_proc.enter()
     
    def select(self, *args, **kwargs):
        if self.ck():
            return self.ck_res()    # Debugging short circuit
        return self.cmd_stream_proc.select(*args, **kwargs)
    
    def set_player(self, *args, **kwargs):
        if self.ck():
            return self.ck_res()    # Debugging short circuit

        return self.cmd_stream_proc.set_player(*args, **kwargs)


"""
language commands
"""

def enter():
    return dC.enter()

def lg(*args):
    return dC.lg(*args)

def select(*args, **kwargs):
    return dC.select(*args, **kwargs)

def set_playing(*args, **kwargs):
    return dC.set_playing(*args, **kwargs)

def set_player(*args, **kwargs):
    return dC.set_player(*args, **kwargs)

from multiprocessing.pool import worker
       