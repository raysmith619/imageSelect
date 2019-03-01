# select_play.py
import os
from tkinter import *
import random    
import time
from datetime import datetime  
from datetime import timedelta
import copy  

from select_fun import *
from select_trace import SlTrace
from select_error import SelectError
from player_control import PlayerControl        
from select_command_play import SelectCommandPlay
from select_command_manager import SelectCommandManager
from select_part import SelectPart
from select_player import SelectPlayer
from select_message import SelectMessage
from active_check import ActiveCheck        
from docutils.nodes import Part
from select_score_window import ScoreWindow

class SelectPlay:
    def __init__(self, board=None, mw=None,
                 score_win=None,
                 start_run=True,
                 on_end=None,
                 on_exit=None,
                 run_check_ms=10,
                 auto_play_check_ms=10,
                 cmd_stream=None,
                 btmove=.1, player_control=None, move_first=None,
                 before_move=None, after_move=None):
        """ Setup play
        :board: playing board (SelectSquares)
        :mw: Instance of Tk, if one, else created here
        :score_win: preexisting score window - left on exit
        :start_run: Start running default: True
        :run_check_ms: Time for running loop check
                default = 10mec
        :on_exit: function to call on exit / window destroy
        :on_end: function, if present, to call at end of game
        :before_move: function, if any, to call before move
        :after_move: function, if any, to call after move
        """
        self.playing = True     # Hack to suppress activity on exit event
        self.score_window = None    # Set iff window displayed
        self.board = board
        self.cmd_stream = cmd_stream
        self.command_manager = SelectCommandManager(self)
        SelectCommandPlay.set_management(self.command_manager, self)
        if mw is None:
            mw = Tk()
        self.mw = mw
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        self.score_win = score_win       # iff not None score win
        if score_win is not None:
            self.preexisting_score_win = True
        else:
            self.preexisting_score_win = False
        self.in_game = False
        self.running = False
        self.run_check_ms = run_check_ms
        self.start_run = start_run
        self.on_exit = on_exit
        self.auto_play_check_ms = auto_play_check_ms
        self.auto_delay_waiting = False
        self.manual_moves = []          # Initialize empty list

        self.btmove = btmove
        if player_control is None:
            player_control = PlayerControl(display=False)
        self.player_control = player_control
        self.player_index = 0
        self.msg = None         # message widget, if any
        self.messages = []      # Command messages, if any
        self.first_time = True       # flag showing first time
        self.moves = []
        board.add_down_click_call(self.down_click)
        board.add_new_edge_call(self.new_edge)
        self.cur_message = None # Currently displaying message, if any
        self.select_cmd = None
        self.before_move = before_move
        self.after_move = after_move
        self.clear_mods()
        self.move_no_label = None       # Move no label, if displayed
        self.waiting_for_message = False
        ###self.mw.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.mw.bind("<KeyPress>", self.key_press)
        self.mw.bind("<KeyRelease>", self.key_release)
        ###self.board.set_down_click_call(self.down_click_made)
        """ Keyboard command control
        """
        self.keycmd_edge = False
        self.keycmd_args = []
        self.keycmd_edge_mark = None        # Current marker edge
        self.multi_key_cmd_str = None       # Current multi key cmd str
        self.on_end = on_end
        if self.start_run:
            self.mw.after(self.run_check_ms, self.running_loop)


    def running_loop(self, run_check_ms=None):
        """ Run game (loop) untill self.running set false
        :run_check_ms: loop checking time default: current checking time
        """
        self.running = True     # Still in game
        self.run = True         # progressing (not paused)
        self.first_time = True 
        if run_check_ms is not None:
            self.run_check_ms = run_check_ms
        while self.running:
            if ActiveCheck.not_active():
                break
            self.mw.update_idletasks()
            self.mw.update()        
            if self.run:
                if self.first_time:
                    self.start_game()
                    self.first_time = False
                else:
                    if self.start_move():
                        self.next_move_no()



        
        
    def user_cmd(self, cmd):
        """ User level command, by which the user/operators
        interact with the game
        Initially to facilitate command file processing but
        may provide a single point of control to facitate simulation
        and testing.
        :cmd: User level command specification
        """
        keysym = cmd.name
        if keysym == "undo": keysym = "u"
        if keysym == "redo": keysym = "r"
        if re.match(r'Up|Down|Left|Right|Enter|Plus|Minus'
                    + r'i|j|u|r', keysym):
            self.key_press_cmd(ec_keysym=keysym)
        else:
            raise SelectError("Don't recognize cmd: %s"
                              % cmd)
        self.show_display()


    def key_press(self, event):
        self.key_press_event(event)


    def key_press_event(self, event):
        """ Keyboard key press processor
        """
        if not SlTrace.trace("keycmd"):
            return
        
        ec = event.char
        ec_code = event.keycode
        ec_keysym = event.keysym
        self.key_press_cmd(ec, ec_code, ec_keysym)

        
    def key_press_cmd(self, ec=None,
                      ec_code=None,
                      ec_keysym=None):
        """ Keyboard key press / command processor
        """
        if ec is None:
            ec = -1
        if ec_code is None:
            ec_code = -1
        if ec_keysym is None:
            ec_keysym = "NA"
        SlTrace.lg("key press: '%s' %s(x%02X)" % (ec, ec_keysym, ec_code))
        if self.multi_key_cmd is None:
            if ec_keysym == "m":
                self.multi_key_cmd_str = ec_keysym
        if self.multi_key_cmd_str is not None:
            if ec_keysym == ";" or ec_keysym == " " or ec_keysym == "Return":
                self.multi_key_cmd()
                return
            
            self.multi_key_cmd_str += ec_keysym
            return
            
        if SlTrace.trace("selected"):
            self.list_selected("key_press_cmd:" + ec_keysym)
        if ec == "j":       # Info (e.g. "i" for current edge position
            edge = self.get_keycmd_edge()
            if edge is None:
                self.beep()
                return
                
            SlTrace.lg("    %s\n%s" % (edge, edge.str_edges()))
            return

        if ec_keysym == "Return":
            edge = self.get_keycmd_edge()
            if edge is None:
                self.beep()
                return
            
            if edge.is_turned_on():
                self.beep()
                return
            
            edge.highlight_clear()
            return self.make_new_edge(edge=edge)
            
        if (ec_keysym == "Up"
                or ec_keysym == "Down"
                or ec_keysym == "Left"
                or ec_keysym == "Right"
                or ec_keysym == "plus"
                or ec_keysym == "minus"):
            res = self.keycmd_move_edge(ec_keysym)
            return res
        

        if self.keycmd_edge:
            try:
                arg = int(ec)
            except:
                self.keycmd_edge = False
                return
            
            self.keycmd_args.append(arg)
            if len(self.keycmd_args) >= 2:
                self.make_new_edge(dir=self.keycmd_edge_dir, rowcols=self.keycmd_args)
                self.keycmd_edge = False
            return

        if ec_keysym == "l":
            part_ids = list(self.board.area.highlights)
            SlTrace.lg("Highlighted parts(%d):" % len(part_ids))
            for part_id in part_ids:
                part = self.get_part(id=part_id)
                SlTrace.lg("    %s" % part)
            return

        if ec_keysym == "s":        # List those selected
            self.list_selected()
            return

        if ec_keysym == "t":        # List those turned on
            part_ids = list(self.board.area.parts_by_id)
            n_on = 0
            for part_id in part_ids:
                part = self.get_part(id=part_id)
                if part.is_turned_on():
                    n_on += 1
            SlTrace.lg("parts turned on(%d of %d):" % (n_on, len(part_ids)))
            for part_id in part_ids:
                part = self.get_part(id=part_id)
                if part.is_turned_on():
                    SlTrace.lg("    %s" % part)
            return

            
        if ec == "v" or ec == "h":
            self.keycmd_edge = True
            self.keycmd_edge_dir = ec
            self.keycmd_args = []
            return
        
        if ec == "r":
            self.redo()
            return
        
        if ec_keysym == "g":       # Do info on squares(regions) touching current edge
            edge = self.get_keycmd_edge()
            SlTrace.lg("%s" % edge.str_adjacents())
            return
        
        if ec_keysym == "u":
            self.undo()
            return
        
            
        x,y = self.get_xy()
        parts = self.get_parts_at(x,y)
        if parts:
            SlTrace.lg("x=%d y=%d" % (x,y))
            for part in parts:
                if ec == "i":
                    SlTrace.lg("    %s\n%s" % (part, part.str_edges()))
                elif ec == "d":
                    part.display()
                elif ec == "c":
                    part.display_clear()        # clear display
                elif ec == "n":                 # turn on
                    part.turn_on(player=self.get_player())
                elif ec == "f":                 # turn off
                    part.turn_off()

    
    def list_selected(self, prefix=None):
        self.board.area.list_selected(prefix=prefix)


    def keycmd_move_edge(self, keysym):
        """ Adjust marker based on current marker state and latest keyboard input symbol
            User remains the same.
            Movement rules:
            1. If keysym is (up,down,left,right) new edge will retain the same orientation and
            move one row/colum in the direction specified by the keysym,
            keep the same direction and move one in the keysym direction.
            2. The new edge, wraps around to the opposite side, if the new loction is our of bounds.
            3. If the keysym is (plus,minus) the new edge will be +/- 90 degrees clockwize
            from the left corner of the original edge
            4. If the (plus,minus) rotation would place an edge outside the latice, the rotation is reversed. 
             
        :keysym:  keyboard key symbol(up,down,left,right,plus,minus) specifying the location of the new edge
        """
        if SlTrace.trace("selected"):
            self.list_selected("keycmd_move_edge before:" + keysym)
        edge = self.get_keycmd_edge()
        edge_dir = edge.sub_type()
        next_dir = edge_dir
        next_row = edge.row 
        next_col = edge.col 

        if keysym == "plus":
            if edge_dir == "h":
                next_dir = "v"
            else:
                next_dir = "h"
                next_col -= 1
        elif keysym == "minus":
            if edge_dir == "h":
                next_dir = "v"
                next_row -= 1
            else:
                next_dir = "h"
        elif keysym == "Up":
            next_row -= 1
        elif keysym == "Down":
            next_row += 1
        elif keysym == "Left":
            next_col -= 1
        elif keysym == "Right":
            next_col += 1

        if next_row < 1:
            next_row = self.board.nrows
        if next_row > self.board.nrows+1 or (next_row > self.board.nrows and next_dir == "v"):
            next_row = 1
        if next_col < 1:
            next_col = self.board.ncols
        if next_col > self.board.ncols+1 or (next_col > self.board.ncols and next_dir == "h"):
            next_col = 1

        next_edge = self.get_part(type="edge", sub_type=next_dir, row=next_row, col=next_col)
        SlTrace.lg("keycmd_move_edge edge(%s) row=%d, col=%d"
                   % (next_dir, next_row, next_col))
        if next_edge is None:
            raise SelectError("keycmd_move_edge no edge(%s) row=%d, col=%d"
                              % (next_dir, next_row, next_col))
        self.move_edge_cmd(edge, next_edge)


    def move_edge_cmd(self, edge, next_edge):
        """ Move between edges cmd
         - change selection
        :edge: current edge
        :next_edge: new edge
        """
        if SlTrace.trace("track_move_edge"):
            SlTrace.lg("before move_edge_cmd:\nedge:%s\nnext_edge:%s"
                       % (edge, next_edge))
        self.get_cmd("move_edge", undo_unit=True)   # Undo unit
        self.cmd_select_clear(edge)
        self.cmd_select_set(next_edge)
        self.do_cmd()
        if SlTrace.trace("track_move_edge"):
            SlTrace.lg("after move_edge_cmd:\nedge:%s\nnext_edge:%s"
                       % (edge, next_edge))


    def multi_key_cmd(self):
        """ Execute multi-key command
        """
        if self.multi_key_cmd_str == "md":  """ Display all parts """
            
            
        
    def new_edge_mark(self, edge, highlight=True):
        """ Set new position (edge)
        :edge: location
        :highlight: True highlight edge default: True
        """
        if self.keycmd_edge_mark is not None:
            self.keycmd_edge_mark.highlight_clear()     # Clear previous
            
        if highlight:
            edge.highlight_set()
        self.keycmd_edge_mark = edge
        
        
    def make_new_edge(self, edge=None, dir=None, rowcols=None):
        if edge is not None:
            self.new_edge(edge)
            return
        
        row = rowcols[0]
        col = rowcols[1]
        SlTrace.lg("make_new_edge: %s row=%d col=%d" % (dir, row, col))
        edge = self.get_part(type="edge", sub_type=dir, row=row, col=col)
        if edge is None:
            SlTrace.lg("No edge(%s) at row=%d col=%d" % (dir, row, col))
            self.beep()
            return
        
        self.new_edge(edge)


    def get_keycmd_edge(self):
        """ Get current marker direction, (row, col)
        """
        ####edge = self.keycmd_edge_mark
        edge = self.get_selected_part()
        if edge is None:
            edge = self.get_part(type="edge", sub_type="h", row=1, col=1)
        return edge


    def get_keycmd_marker(self):
        """ Get current marker direction, (row, col)
        """
        edge = self.get_keycmd_edge()
        dir = edge.sub_type()
        row = edge.row 
        col = edge.col
        return dir, [row,col]
    
    
    def update_keycmd_edge_mark(self, prev_edge_mark, new_edge_mark):
        """ Update edge mark
        :prev_edge_mark:  previous edge mark None if none
        :new_edge_mark:   new edge mark, None if none
        """
        if prev_edge_mark is not None:
            prev_edge_mark.highlight_clear()
        if new_edge_mark is not None:
            new_edge_mark.highlight_set()
        self.keycmd_edge_mark = new_edge_mark
        
                
    def get_xy(self):
        """ get current mouse position (or last one recongnized
        :returns: x,y on area canvas, None if never been anywhere
        """
        return self.board.get_xy()


    def get_part(self, id=None, type=None, sub_type=None, row=None, col=None):
        """ Get basic part
        :id: unique part id
        :returns: part, None if not found
        """
        return self.board.get_part(id=id, type=type, sub_type=sub_type, row=row, col=col)
    
    
    def get_selects(self):
        """ GEt list of selected parts
        :returns: list, empty if none
        """
        return self.board.get_selects()


    def get_selected_part(self):
        """ Get selected part
        :returns: part, None if none selected
        """
        return self.board.get_selected_part()
                
    
    def get_parts_at(self, x, y, sz_type=SelectPart.SZ_SELECT):
        """ Check if any part is at canvas location provided
        If found list of parts
        :Returns: SelectPart[]
        """
        return self.board.get_parts_at(x,y,sz_type=sz_type)


    def run_cmd(self):
        """ Run / continue game
        """
        self.run = True
    
    
    def pause_cmd(self):
        """ Pause game
        """
        self.run = False
                    
                
            

    def key_release(self, event):
        """ Keyboard key release processor
        """
        SlTrace.lg("key_release %s" % event.char, "keybd")
        
    def annotate_squares(self, squares, player=None):
        """ Annotate squares in board with players info
        Updates select_cmd: prev_parts, new_parts as appropriate
        :squares: list of squares to annotate
        :player: player whos info is used
                Default: use current player
        """
        if player is None:
            player = self.get_player()
        if not isinstance(squares, list):
            squares = [squares]
        for square in squares:
            square.part_check(prefix="annotate_squares")
        for square in squares:
            sc = select_copy(square)
            self.add_prev_parts(square)
            sc.set_centered_text(player.label,
                                     color=player.color,
                                     color_bg=player.color_bg)
            if SlTrace.trace("annotate_square"):
                SlTrace.lg("annotate_square: %s\n%s"
                         % (sc, sc.str_edges()))
            self.add_new_parts(sc)

        return

    def show_display(self):
        self.mw.update_idletasks()

        
    def setup_score_window(self):
        """ Setup interaction with Move/Undo/Redo
        """
        if self.score_window is not None:
            self.score_window.destroy()
                        
        self.score_window = ScoreWindow(self)


    def close_score_window(self):
        """ close score window
        """
        if self.score_window is None:        
            return
        
        self.score_window.destroy()
        self.score_window = None
        
        

    def get_canvas(self):
        return self.board.canvas

    def get_height(self):
        return self.get_canvas().winfo_height()

    def get_width(self):
        canvas = self.get_canvas()
        if canvas is None:
            return 0

        return canvas.winfo_width()

    def announce_player(self, tag):
        """ Announce current player, execute command
        Begins move
        """
        player = self.get_player()
        prev_player = self.get_prev_player()
        if player != prev_player:
            was_str = " was %s" % prev_player
        else:
            was_str = ""
        SlTrace.lg("announce_player: %s %s%s"
                    % (tag, player, was_str), "execute")
        scmd = self.get_cmd("announce_player", has_prompt=True)
        self.set_prev_player(prev_player)
        self.set_new_player(player)
        text = "It's %s's turn." % player.name
        self.trace_scores("announce_player:")
        SlTrace.lg(text)
        self.add_message(text, color=player.color)
        self.do_cmd()       # Must display now
        if self.before_move is not None:
            self.before_move(scmd)
        self.enable_moves()
        self.trace_scores("announce_player before auto:")
        if player.auto:
            self.auto_play_pause()


    def add_message(self, text, color=None, font_size=40,
                   time_sec=None):
        """ Put message up. If time is present bring it down after time seconds    
        :time: time for message
                default: leave message there till next message
        """
        if not isinstance(text, str):
            raise SelectError("add_message: text is not str - "
                              + str(text))
        scmd = self.select_cmd
        if scmd is None:
            raise SelectError("add_message with no SelectCommand")
        message = SelectMessage(text, color=color,
                                  font_size=font_size,
                                  time_sec=time_sec)
        scmd.add_message(message)



       
    def delete_window(self):
        """ Process Trace Control window close
        """
        self.mw.eval('::ttk::CancelRepeat')
        SlTrace.lg("Closing windows")
        '''    
        ActiveCheck.clear_active()  # Disable activities
        if self.score_win is not None:
            self.score_win.destroy()
            self.score_win = None
        if self.mw is not None and self.mw.winfo_exists():
            self.mw.quit()
            self.mw.destroy()
            self.mw = None
        '''
        if self.on_exit is not None:
            self.on_exit()
        
        sys.exit()      # Else quit
        
        
    def disable_moves(self):
        """ Disable(ignore) moves by user
        """
        self.board.disable_moves()
        
        
    def enable_moves(self):
        """ Enable moves by user
        """
        self.board.enable_moves()


    def display_print(self, tag, trace):
        SlTrace.lg("display_print: " + tag, trace)
        

    def display_update(self):
        SlTrace.lg("display_update: ", "execute")
    
    def select_print(self, tag, trace):
        SlTrace.lg("select_print: "  + tag, trace)    


    def display_messages(self, messages):
        """ Display cmd messages
        :messages:  messages to be displayed in order
        """
        if self.mw is None:
            return
        
        for message in messages:
            self.do_message(message)
    
    
    def show_score_window(self):
        if self.mw is None:
            return
        if self.score_window is None:
            self.score_window = ScoreWindow(self)
            self.preexisting_score_win = False            
        self.score_window.update_window()
    
    
    def clear_score_window(self):
        if self.mw is None:
            return
        
        if self.score_window is not None:
            self.score_window.delete_window()
    
    
    def update_score_window(self):
        if self.mw is None:
            return
        
        if self.score_window is None:
            return
        
        self.score_window.update_window()
        
        
    def wait_message(self, message=None):
        """ Wait till message completed
        :message: message being displayed
                default: current message
        """
        if not self.mw.winfo_exists():
            return
        
        self.waiting_for_message = True
        if message is None:
            message = self.cur_message
        if (message is not None
                and message.end_time is not None):
            while True:
                now = datetime.now()
                if  now >= message.end_time:
                    self.cur_message = None
                    SlTrace.lg("End of message waiting")
                    break
                if self.mw is not None and self.mw.winfo_exists():
                    self.mw.update()
                time.sleep(.01)
        self.waiting_for_message = False


    def is_waiting_for_message(self):            
        """ Check if waiting for message
        Used to ignore to fast actions
        """
        return self.waiting_for_message


    def ignore_if_busy(self):
        """ beep if we're too busy to proceed
        :returns: True if busy
        """
        if self.is_waiting_for_message():
            self.beep()
            return True
        return False


    def beep(self):
        import winsound
        winsound.Beep(500, 500)

    
    def do_message(self, message):
        """ Put message up. If time is present bring it down after time seconds    
        :time: time for message
                default: leave message there till next message
        :cmd: Add to cmd if one open
        """
        SlTrace.lg("do_message(%s)" % (message.text), "execute")
        if not self.run:
            return
        
        if self.mw is None or not self.mw.winfo_exists():
            return
        
        self.wait_message()
        text = message.text
        color = message.color
        font_size = message.font_size
        if font_size is None:
            font_size=40
        time_sec = message.time_sec
        
        if self.mw is None or not self.mw.winfo_exists():
            return
        
        if self.mw is not None and self.mw.winfo_exists():
            if self.msg is not None:
                self.msg.destroy()
                self.msg = None
        width = self.get_width()
        if width < 500:
            width = 500
        self.msg = Message(self.mw, text=text, width=width) # Seems to be pixels!
        self.msg.config(fg=color, bg='white',
                        font=('times', font_size, 'italic'))
        self.msg.pack()
        if time_sec is not None:
            end_time = datetime.now() + timedelta(seconds=time_sec)
            message.end_time = end_time
            self.cur_message = message


    def end_message(self):
        """ End current message, if any
        Used to speed up such things as redo/undo
        """
        if self.cur_message is not None:
            self.cur_message.end_time = datetime.now()
            self.wait_message()
 
            
    def mark_edge(self, edge, player, move_no=None):
        """ Mark edge
        :edge: edge being marked
        :player: player selecting edge
        """
        edge.highlight_clear()
        edge.turn_on(player=player, move_no=move_no)
        return
    
    
    def message_delete(self):
        """ Delete message if present
        Usually called after wait time
        """
        SlTrace.lg("Destroying timed message")
        if self.msg is not None:
            SlTrace.lg("Found message to destroy")
            self.msg.destroy()
            self.msg = None

    def get_messages(self):
        """ Get current message, if any
        else returns None
        """
        return self.messages


    def displayPrint(self):
        SlTrace.lg("do_cmd(%s) display TBD"  % ("cmd???"), "execute")
        


    def selectPrint(self):
        SlTrace.lg("do_cmd(%s) select TBD"  % (self.action), "execute")

    

    def get_cmd(self, action=None, has_prompt=False, undo_unit=False):
        """ Get current command, else new command
        :action: - start new command with this action name
                defalt use current cmd
        :has_prompt: True cmd contains prompt, starting cmd sequence
        :undo_unit: True - this command is single undoable unit
                    default: False
        """
        if action is None:
            cmd = self.select_cmd
            if cmd is None:
                raise SelectError("get_cmd: No name for SelectCommand")
            return cmd
        else:
            if self.select_cmd is not None:
                raise SelectError("get_cmd: previous cmd(%s) not completed"
                                   % self.select_cmd)
        self.select_cmd = SelectCommandPlay(action, has_prompt=has_prompt,
                                             undo_unit=undo_unit)
        return self.select_cmd


    def get_last_cmd(self):
        """ Get executed or redone
        """
        return self.command_manager.get_last_command()


    def get_undo_cmd(self):
        """ Get most recent undo cmd
        """
        return self.command_manager.get_undo_cmd()
    
    
    def is_in_cmd(self):
        """ Check if building a command
        """
        return self.select_cmd is not None
    
    
    def check_mod(self, part, mod_type=None, desc=None):
        """ Part modification notification
        Modifications are stored for later use/inspection in
        self.prev_mods for MOD_BEFORE
        self.new_mods for MOD_AFTER
        :part: part modified
        :mod_type: SelectPart.MOD_BEFORE, .MOD_AFTER
        :desc: description of modification e.g., turn_on
        """
        SlTrace.lg("check_mod: %s %s %d"
                    % (part, desc, mod_type), "execute")
        if mod_type == SelectPart.MOD_BEFORE:
            self.add_prev_mods(part)
        else:
            self.add_new_mods(part)

    def add_prev_mods(self, parts):
        """ Add part before any modifications
        :parts: part or list before modification
        """
        if not isinstance(parts, list):
            parts = [parts]
        for part in parts:
            self.prev_mods.append(select_copy(part))

    def add_new_mods(self, parts):
        """ Add parts before any modifications
        :parts: one or list before modification
        """
        if not isinstance(parts, list):
            parts = [parts]
        for part in parts:
            self.new_mods.append(select_copy(part))
        
        
    def clear_mods(self):
        """ Clear modifications
        """
        self.prev_mods = []
        self.new_mods = []
        
        
    def cmd_select_clear(self, parts=None):
        """ Select part(s)
        :parts: part or list of parts
                default: all selected
        """
        scmd = self.get_cmd()
        scmd.select_clear(parts)


    def cmd_select_set(self, parts, keep=False):
        """ Select part(s)
        :parts: part(s) to select/deselect
        :keep: keep previous selected
                default = falsu
        """
        scmd = self.get_cmd()
        scmd.select_set(parts, keep=keep)
        
        
    def select_clear(self, parts=None):
        """ Select part(s)
        :parts: part or list of parts
                default: all selected
        """
        self.board.area.select_clear(parts=parts)


    def select_set(self, parts=None, keep=False):
        """ Select part(s)
        :parts: part(s) to select/deselect
        """
        self.board.area.select_set(parts=parts, keep=keep)
        

    def set_new_player(self, player):
        scmd = self.select_cmd
        if scmd is None:
            raise SelectError("set_new_player with no SelectCommand")
        scmd.set_new_player(player)
            

    def set_prev_player(self, player):
        scmd = self.select_cmd
        if scmd is None:
            raise SelectError("set_prev_player with no SelectCommand")
        scmd.set_prev_player(player)
    
    
    def set_stroke_move(self, use_stroke=True):
        """ Enable/Disable use of stroke moves
        Generally for use in touch screens
        """
        self.board.set_stroke_move(use_stroke)
            
    
    def add_prev_parts(self, parts):
        scmd = self.select_cmd
        if scmd is None:
            raise SelectError("add_prev_parts with no SelectCommand")
        scmd.add_prev_parts(parts)
    
    
    def add_new_parts(self, parts):
        scmd = self.select_cmd
        if scmd is None:
            raise SelectError("add_new_parts with no SelectCommand")
        scmd.add_new_parts(parts)


    def undo(self):
        """ Undo most recent command
        :returns: True iff successful
        """
        while self.is_waiting_for_message():
            self.end_message()
            
        if self.ignore_if_busy():
            return False

        return self.command_manager.undo()


    def redo(self):
        """ Undo most recent command
        :returns: True iff successful
        """
        while self.is_waiting_for_message():
            self.end_message()
            
        if self.ignore_if_busy():
            return False
        
        return self.command_manager.redo()
        
    
    
    def do_cmd(self):
        if self.select_cmd is None:
            raise SelectError("do_cmd with no SelectCommand")
        self.select_cmd.do_cmd()
        if self.after_move is not None:
            self.after_move(self.select_cmd)

        self.select_cmd = None      # Clear for next time
        
        
    def complete_cmd(self):
        """ Complete command if one in progress
        """
        if self.select_cmd is not None:
            self.do_cmd()


    def auto_play_pause(self):
        """ Pause for auto player
        Returns after delay
        """
        if ActiveCheck.not_active():
            return
        
        if not self.playing:
            return              # Suppress activity

        player = self.get_player()
        if not player.auto:
            return
        self.auto_delay_waiting = True
        pause = player.pause
        delay_ms = int(pause*1000)
        self.mw.after(delay_ms)
        return


    def manual_play(self, player):
        """ Do manual play, checking for action
        :player: player to move
        :returns: return True iff a move was sensed, else False
        """
        if self.manual_moves:
            move = self.manual_moves.pop()
            self.new_edge(move)
            return True
        
        return False
            
    def auto_play(self, player):
        """ Do automatic move based on "level" of player
        """
        SlTrace.lg("auto_play player: %s" % self.get_player(), "player_trace")
        self.trace_scores("auto_play:")
        legal_moves = self.get_legal_moves()
        if len(legal_moves) == 0:
            self.end_game("No more moves!")
            return False
        SlTrace.lg("auto_play player: %s" % self.get_player(), "player_trace")
        
        level = self.adjust_level_to_stay_even(player)
        SlTrace.lg("auto_play player: %s" % self.get_player(), "player_trace")
        if level > 0:
            self.auto_play_positive(player)
        elif level < 0:
            self.auto_play_negative(player)
        else:
            self.auto_play_random(player)
        SlTrace.lg("auto_play player END: %s" % self.get_player())
        return True                         # Next move number


    def adjust_level_to_stay_even(self, player):
        """ Adjust playing level to stay even, if steven != 0
        :player: current player - us
            player.steven:
                0 - no checking
                > 0 reverse level if you score is to high
                < 0 reverse level if you score is to low
                abs() < 1 use fraction as fraction advantage
                        e.g. stay_even==.1 if score > .1*opponent
                abs() >= 1 use stay_even as number advantage
                        e.g. stay_even==2 if score > 2 + opponent

        """
        SlTrace.lg("adjust_level_to_stay_even player: %s" % self.get_player(), "player_trace")
        level = player.level
        steven = player.steven
        if steven == 0:
            return level        # No adjustment wanted
        SlTrace.lg("adjust_level_to_stay_even player: %s" % self.get_player(), "player_trace")
       
        our_score = player.get_score()
        SlTrace.lg("adjust_level_to_stay_even player: %s" % self.get_player(), "player_trace")
        next_player = self.get_next_player(set_player=False)
        SlTrace.lg("adjust_level_to_stay_even player: %s" % self.get_player(), "player_trace")
        next_score = next_player.get_score()
        SlTrace.lg("adjust_level_to_stay_even player: %s" % self.get_player(), "player_trace")
        diff = abs(our_score - next_score)
        steven_abs = abs(steven)
        diff_limit = steven_abs
        if steven_abs < 1:
            diff_limit = steven_abs * (our_score+next_score)/2
        
        if diff > diff_limit:
            if our_score > next_score:
                level = -abs(level)     # reduce our level
            elif our_score < next_score:
                level = abs(level)
        SlTrace.lg("adjust_level_to_stay_even player: %s" % self.get_player(), "player_trace")
        return level


    def auto_play_positive(self, player):
        """ Positive player - trying to "win"
        """
        level = player.level
        LEVEL_SQUARE = 1                # Complete a square
        LEVEL_NO_GIVE_SQUARE = 2        # Provide possible square to next play
        legal_moves = self.get_legal_moves()
        if level >= LEVEL_SQUARE:
            squares = []
            square_moves = []
            for move in legal_moves:
                if self.is_square_complete(move, squares, ifadd=True):
                    square_moves.append(move)
            if len(square_moves) > 0:
                nr = random.randint(0, len(square_moves)-1)
                next_move = square_moves[nr]
                self.new_edge(next_move)
                SlTrace.lg("positive play move for %s: %s" % (player, next_move), "play_strategy")
                return

        if level >= LEVEL_NO_GIVE_SQUARE:
            safe_square_moves = []
            for move in legal_moves:
                if self.square_complete_distance(move) > 2:
                    safe_square_moves.append(move)  # One move 
            if len(safe_square_moves) > 0:
                nr = random.randint(0, len(safe_square_moves)-1)
                next_move = safe_square_moves[nr]
                self.new_edge(next_move)
                SlTrace.lg("positive play safe move for %s: %s" % (player, next_move), "play_strategy")
                return
                   
        self.auto_play_random(player)         # Default - just play one


    def auto_play_negative(self, player=None):
        """ Negative player - trying to "loose"
        """
        if player is None:
            player = self.get_player()

        level = player.level
        LEVEL_SQUARE = 1                # Complete a square
        LEVEL_NO_GIVE_SQUARE = 2        # Provide possible square to next play
        legal_moves = self.get_legal_moves()
        if abs(level) >= LEVEL_SQUARE:
            squares = []
            not_square_moves = []
            not_safe_moves = []     # give win to next player
            for move in legal_moves:
                if not self.is_square_complete(move, squares, ifadd=True):
                    not_square_moves.append(move)
                    if self.square_complete_distance(move) <= 2:
                        not_safe_moves.append(move)
            if abs(level) >= LEVEL_NO_GIVE_SQUARE:
                if len(not_safe_moves) > 0:
                    nr = random.randint(0, len(not_safe_moves)-1)
                    next_move = not_safe_moves[nr]
                    self.new_edge(next_move)
                    SlTrace.lg("negative play safe for %s: %s" % (player, next_move), "play_strategy")
                    return
                    
            if len(not_square_moves) > 0:
                nr = random.randint(0, len(not_square_moves)-1)
                next_move = not_square_moves[nr]
                self.new_edge(next_move)
                SlTrace.lg("negative play square for %s: %s" % (player, next_move), "play_strategy")
                return
            
            
            
        self.auto_play_random(player)
    

    def auto_play_random(self, player=None):
        """ Play the random next legal move
        """
        if player is None:
            player = self.get_player()
        legal_moves = self.get_legal_moves()
        nr = random.randint(0, len(legal_moves)-1)
        next_move = legal_moves[nr]
        self.new_edge(next_move)
        
        
    def get_legal_moves(self, ):
        return self.board.get_legal_moves()
        
        
    def start_move(self):
        """ Start move
        :returns: True iff move has been made, and next move is coming
        """
        if not self.run:
            return False
        
        legal_moves = self.get_legal_moves()
        if len(legal_moves) == 0:
            self.end_game("NO more legal moves!")
            return False       
        
        if self.new_move:
            self.announce_player("start_move")
            if SlTrace.trace("selected"):
                self.list_selected("After start_move")
            self.new_move = False
        player = self.get_player()
        if player.auto:
            self.auto_play_pause()
            if self.auto_play(player):
                return True
        else:
            if self.manual_play(player):
                return True
        
        return False        # No move -no new move


    def end_game(self, msg=None):
        """ End the game
        :msg: message /reason
        """
        SlTrace.lg("end of game")
        self.score_game()

        scmd = self.get_cmd("end_of_game")
        if msg is None:
            self.add_message("End of Game",
                         time_sec=1)
            
        self.add_message("Game Over")
        self.do_cmd()
        self.pause_cmd()
        if self.on_end is not None:
            ###self.on_end()
            self.mw.after(0, self.on_end)


    def score_game(self):
        """ Score current game, updating statistics
        played: number of games played
        wins: number of games with top score (or tie)
        """
        players = self.player_control.get_players()
        if len(players) == 0:
            return      # No players
        
        top_score = players[0].get_score()
        for player in players:
            if player.get_score() > top_score:
                top_score = player.get_score()
                
        for player in players:
            player_score = player.get_score()
            player_played = player.get_played()
            player_wins = player.get_wins()
            player.set_played(player_played+1)
            if  player_score >= top_score:
                player.set_wins(player_wins+1)
        self.update_score_window()

            
    def start_game(self):
        self.in_game = True
        self.new_move = True
        self.manual_moves = []          # Initialize empty list
        self.player_control.set_all_scores(0, only_playing=True)
        SlTrace.lg("start_game", "execute")
        self.set_move_no(0)
        self.get_cmd("start_game")
        self.add_message("It's A New Game",
                         time_sec=1)
        ###self.set_move_no(1)
        self.do_cmd()
        self.set_move_no(1)


    def set_move_no(self, move_no):
        self.command_manager.set_move_no(move_no)
        
        
    def next_move_no(self):
        self.new_move = True
        self.command_manager.next_move_no()
        
        

    def is_square_complete(self, edge, squares=None, ifadd=False):
        """ Determine if this edge completes a square(s)
        :edge: - potential completing edge
        :squares: list, to which any completed squares(regions) are added
                Default: no regions are added
        :returns: True iff one or more squares are completed
        """
        return self.board.is_square_complete(edge, squares=squares, ifadd=ifadd)


    def square_complete_distance(self, edge,
                                  squares_distances=None):
        """ Determine minimum number of moves, including this
        move to complete a square
        :edge: - potential completing edge
        :squares_distances: list, of (distance, square) pairs
                Default: no entries returned
                if no connected squares - empty list returned
        :returns: closest distance, NOT_CLOSE if no squares
        """
        return self.board.square_complete_distance(edge, squares_distances=squares_distances)


    def down_click(self, part, event=None):
        """ Process down_click
        :part: on which down click occured
        :returns: True if event processed
        """
        if part.is_turned_on():
            return False
        
        if part.is_edge():
            self.manual_moves.append(part)
            return True
        
        return False
    
    

    def new_edge(self, edge):
        """ Process new edge selection
                1. Adjust edge apperance appropriately
                2. Announced new edge creation by user
        :edge: updated edge component
        """
        SlTrace.lg("new_edge player: %s" % self.get_player(), "player_trace")
        if not edge.connecteds:
            SlTrace.lg("new_edge id=%d no connecteds" % edge.part_id)
            return
        
        self.disable_moves()                    # Disable input till ready
        self.clear_redo()
        prev_player = self.get_player()
        self.trace_scores("new_edge:")
        SlTrace.lg("New edge %s by %s"
                    % (edge, prev_player), "new_edge")
        self.complete_cmd()                     # Complet current command if one
        scmd = self.get_cmd("new_edge")
        scmd.set_prev_player(prev_player)
        scmd.add_prev_parts(edge)               # Save previous edge state 
        self.mark_edge(edge, prev_player, move_no=scmd.move_no)
        self.add_new_parts(edge)
        self.cmd_select_set(edge)
        self.do_cmd()                               # move complete
        if SlTrace.trace("selected"):
            self.list_selected("After new_edge")
        self.clear_mods()

        scmd = self.get_cmd("after_edge")
        prev_player = self.get_player()
        next_player = prev_player                    # Change if appropriate
        regions = []
        if self.is_square_complete(edge, regions):
            self.add_prev_parts(edge)
            edge.highlight_clear()          # ??? Should we just set flag??
            self.completed_square(edge, regions)
            if len(regions) == 1:
                plu = ""
            else:
                plu = "s" 
            SlTrace.lg("Square%s Completed" % (plu))
        else:
            next_player = self.get_next_player()      # Advance to next player
            SlTrace.lg("Next player: %s" % next_player, "player_trace")
        if SlTrace.trace("selected"):
            self.list_selected("After square check")

        scmd.set_new_player(next_player)
        self.do_cmd()
        if SlTrace.trace("selected"):
            self.list_selected("After next_player set")
        self.enable_moves()
        self.trace_scores("new_edge end:")
        SlTrace.lg("new_edge END player: %s" % self.get_player(), "player_trace")
       

    def clear_redo(self):
        """ Clear redo (i.e. undo_stack for possible redo)
        """
        self.command_manager.clear_redo()
        
        

    def player_control(self):
        """ Setup player control
        """
        self.board.player_control()

    def get_next_player(self, set_player=True):
        """ Get next player to move
        :set: True set this as the player
        """
        return self.player_control.get_next_player(set_player=set_player)
    
    def get_player(self):
        """ Get current player to move
        """
        return self.player_control.get_player()

        
    
    def get_players(self, all=False):
        """ Get players
        :all: all players default: just currently playing
        """
        return self.player_control.get_players(all=all)


    def get_prev_player(self):
        """ Get previous player, i.e. player of most recent move
        """
        prev_cmd = self.get_last_cmd()
        if prev_cmd is None:
            return None         # No previous player
        prev_player = prev_cmd.new_player
        return prev_player
    
    
    
    def set_player(self, player):
        self.player_control.set_player(player)
        
        
    
    def completed_square(self, edge, squares):
        player = self.get_player()
        player_name = player.name
        player_label = player.label
        if len(squares) == 1:
            text = ("%s completed a square with label %s"
                     % (player_name, player_label))
        else:
            text = ("%s completed %d squares with label %s"
                    % (player_name, len(squares), player_label))
        SlTrace.lg(text)
        SlTrace.lg("completing edge: %s" % edge)
        self.annotate_squares(squares, player=player)
        self.update_score(player, squares=squares)
        self.trace_scores("after self.update_score")
        self.add_message(text, font_size=20, time_sec=1)
        text = ("%s gets another turn." % player_name)
        SlTrace.lg(text)
        self.add_message(text, font_size=20, time_sec=1)
        SlTrace.lg("completed_square_end", "execute")
        self.trace_scores("completed_square end")

    def trace_scores(self, prefix=None):
        """ Trace(log) playing scores
        :prefix: leading text to identify place
                default: none
        """
        if not SlTrace.trace("trace_scores"):
            return
        
        if prefix is None:
            prefix = "trace_scores"
        if not prefix.endswith(":"):
            prefix += ":"
        for player in self.get_players():
            SlTrace.lg("%sscore: %d for %s"
                        % (prefix, player.score, player))
        

    def set_score(self, score, player=None):
        """ Set player score
        :score: New score
        :player: player to update default: current player
        NOTE: There is a problem using player.set_score directly - update is lost
        """
        if player is None:
            player = self.get_player()
        plr = self.player_control.get_player(player.position)
        plr.set_score(score)
        
        
            
    def update_score(self, player, squares):
        """ Update player's score based on squares completed
        :squares:  completed squares
        """
        if not isinstance(squares, list):
            squares = [squares]
        scmd = self.get_cmd()
        prev_score = player.get_score()
        new_score = prev_score + len(squares)
        SlTrace.lg("prev_score:%d new_score:%d %s" % (prev_score, new_score, player))
        self.set_score(new_score, player)
        self.trace_scores("after set_score(%d, %s)" % (new_score, player))
        scmd.add_prev_score(player, prev_score)
        scmd.add_new_score(player, new_score)
        self.update_score_window()
    
    
    def update_score_from_cmd(self, new_score, prev_score):
        """ Update score from command execution
        :new_score: player, score tupple if one
        :prev_score: previous player, score tupple - ignored
        """
        if new_score is None:
            return          # No change
        
        player = new_score[0]
        score = new_score[1]
        player.set_score(score)
            
                
    def remove_parts(self, parts):
        """ Remove deleted or changed parts
        :parts: parts to be removed
        """
        self.board.remove_parts(parts)
    
    
    def insert_parts(self, parts):
        """ Add new or changed parts
        :parts: parts to be env_added
        """
        self.board.insert_parts(parts)
            