# select_command_play.py    12Nov2018

import copy

from select_fun import *
from select_trace import SlTrace
from active_check import ActiveCheck
from select_error import SelectError
from select_command import SelectCommand
from select_command_manager import SelectCommandManager

"""
Command processing, especially undo/Redo
"""
import player_control

"""
Command Definition
"""
class SelectCommandPlay(SelectCommand):
    @classmethod
    def set_management(cls, command_manager, user_module):
        cls.command_manager = command_manager
        cls.user_module = user_module


    def __deepcopy__(self, memo=None):
        """ provide deep copy as a custimized "constructor",
        reducing recusion
        """
        new_copy = SelectCommandPlay(self.action,  has_prompt=self.has_prompt, undo_unit=self.undo_unit)
        new_copy.prev_move_no = self.prev_move_no
        new_copy.new_move_no = self.new_move_no
        new_copy.prev_keycmd_edge_mark = self.prev_keycmd_edge_mark   # Usually no action
        new_copy.new_keycmd_edge_mark = self.new_keycmd_edge_mark
        new_copy.prev_messages = self.prev_messages
        new_copy.new_messages = self.new_messages
        new_copy.prev_player = select_copy(self.prev_player)
        new_copy.new_player = select_copy(self.new_player)
        new_copy.prev_selects = select_copy(self.prev_selects)
        new_copy.new_selects = select_copy(self.new_selects)
        new_copy.prev_parts = select_copy(self.prev_parts)    # Hash by id of previous part values
        new_copy.new_parts = select_copy(self.new_parts)     # Hash by id of new part values
        new_copy.prev_score = None
        new_copy.new_score = None
        return new_copy

       
    """ Command object, sufficient to contain do/undo
    for SelectPlay
    """
    def __init__(self, action_or_cmd, has_prompt=False, undo_unit=False):
        """ Initialize do/undo Structure
        :action_or_cmd:
            str - type of command:
                "move" - player move
        :cmd: command
        :has_prompt: True - contains move prompt
                    default: False
        :undo_unit:  True - completes an undoable sequence
                    default: False
        """
        SelectCommand.__init__(self, action_or_cmd, has_prompt=has_prompt,
                               undo_unit=undo_unit)
        if isinstance(action_or_cmd, str):
            self.prev_move_no = None
            self.new_move_no = None
            self.prev_keycmd_edge_mark = None   # Usually no action
            self.new_keycmd_edge_mark = None
            self.prev_messages = []
            self.new_messages = []
            self.prev_player = self.user_module.get_player()
            self.new_player = select_copy(self.prev_player)
            self.prev_selects = self.command_manager.user_module.get_selects()
            self.new_selects = self.prev_selects
            self.prev_parts = {}    # Hash by id of previous part values
            self.new_parts = {}     # Hash by id of new part values
            self.prev_score = None  # previous (player,score) if any change
            self.new_score = None   # new (player,score) if any change
        else:
            """ Hack because super does not appear to populate self """
            no = self.no
            self = select_copy(action_or_cmd)
            self.no = no
            

    def __str__(self):
        st = "\n cmd[" + str(self.no) + "]:" + self.action
        st += " move: %d" % self.move_no
        if self.has_prompt:
            st += " has_prompt"
        if self.undo_unit:
            st += " undo_unit"
        if self.prev_selects:
            st += "\n  prev_selects:"
            for part in self.prev_selects.values():
                st += "\n    %s" % part
        if self.new_selects:
            st += "\n  new_selects:"
            for part in self.new_selects.values():
                st += "\n    %s" % part
        ###st += (" new_player:" + str(self.new_player))
        st += "\n  prev_player: " + str(self.prev_player)
        st += "\n  new_player: " + str(self.new_player)
        if self.prev_score is not None:
            st += "\n  prev_score:%d %s" % (self.prev_score[1], self.prev_score[0])
        if self.new_score is not None:
            st += "\n  new_score:%d %s" % (self.new_score[1], self.new_score[0])
        if self.prev_parts:
            st += "\n  prev_parts:%d" % len(self.prev_parts)
            for part in self.prev_parts.values():
                st += "\n   " + str(part)
        if self.new_parts:
            st += "\n  new_parts:%d" % len(self.new_parts)
            for part in self.new_parts.values():
                st += "\n   " + str(part)
        if self.prev_messages:
            st += "\n  prev_messages:%d" % len(self.prev_messages)
            for message in self.prev_messages:
                st += "\n    %s" % str(message)
        if self.new_messages:
            st += "\n  new_messages:%d" % len(self.new_messages)
            for message in self.new_messages:
                st += "\n    %s" % str(message)
        """ Check for duplicate entries
        """
        parts_by_id = {}
        for part in self.prev_parts.values():
            if part.part_id in parts_by_id:
                SlTrace.lg("Duplicate in prev_parts id=%d       %s"
                            % (part.part_id, st.replace("\n", "\n        ")))
                return st
            parts_by_id[part.part_id] = part
        part_by_id = {}
        for part in self.new_parts.values():
            if part in part_by_id:
                SlTrace.lg("Duplicate in new_parts id=%d      %s"
                            % (part.part_id, st.replace("\n", "\n        ")))
                return st
            parts_by_id[part.part_id] = part
                
        return st


    def select_copy(self, levels=None):
        return copy.copy(self)
    
            
    def set_new_player(self, player):
        self.new_player = select_copy(player)
    
    
            
    def set_prev_player(self, player):
        self.prev_player = select_copy(player)
        
                    
    def add_message(self, message):
        self.new_messages.append(message)
        

    def set_can_undo(self, can=True):
        self.can_undo_ = can 

    def show_display(self):
        """ Show display at current time
        - mostly for debugging
        """
        self.user_module.show_display()
        

    def do_cmd(self):
        """
        Do command, storing it, if command can be undone or repeated, for redo,repeat
        """
        self.display_print()
        self.select_print()
        self.cmd_stack_print("do_cmd(%s)"
                                        % (self.action), "execute_stack")
        res = self.execute()
        if res:
            if self.can_undo() or self.can_repeat():
                SlTrace.lg("add to commandStack", "execute_stack")
                self.command_manager.save_command(self)
            else:
                SlTrace.lg("do_cmd(%s) can't undo/repeat"
                           % (self.action), "execute")
                return False
        return res


    def cmd_stack_print(self, tag, trace):
        self.command_manager.cmd_stack_print(tag, trace)

    def display_print(self):
        SlTrace.lg("do_cmd: display_print", "execute_print")


    def select_print(self):
        SlTrace.lg("do_cmd: select_print", "execute_select")


    def select_clear(self, parts):
        if not isinstance(parts, list):
            parts = [parts]
        for part in parts:
            self.prev_selects[part.part_id] = part


    def select_set(self, parts, keep=False):
        """ Select parts
        :parts: part(s) to select
        :keep: keep previously selected
                default: False
        """
        if not isinstance(parts, list):
            parts = [parts]
        if keep:
            new_selects = select_copy(self.new_selects)
        else:
            new_selects = {}
        for part in parts:
            new_selects[part.part_id] = part
        self.new_selects = new_selects

    def add_new_parts(self, parts):
        """ add one or a list of parts to new
        :parts: one or list of parts
        """
        if not isinstance(parts, list):
            parts = [parts]
        for part in parts:
            if part.part_id in self.new_parts:
                SlTrace.lg("Duplicate in add_new_parts id=%d       %s"
                            % (part.part_id, str(part).replace("\n", "\n        ")))
                continue
            self.new_parts[part.part_id] = select_copy(part)


    def add_prev_parts(self, parts):
        """ add one or a list of parts to previous
        Only unique id is kept
        :parts: one or list of parts
        """
        if not isinstance(parts, list):
            parts = [parts]
        for part in parts:
            if part.part_id in self.prev_parts:
                SlTrace.lg("Duplicate in add_prev_parts id=%d       %s"
                            % (part.part_id, str(part).replace("\n", "\n        ")))
                continue
            
            self.prev_parts[part.part_id] = select_copy(part)


    def add_prev_score(self, player, score):
        """ Add previous player, score tupple
        :player: whos score changed
        :score: new score
        """
        self.prev_score = (player, score)


    def add_new_score(self, player, score):
        """ Add new player, score tupple
        :player: whos score changed
        :score: new score
        """
        self.new_score = (player, score)
        
        

    def save_cmd(self):
        self.command_manager.save_cmd(self)


    def display_update(self):
        """ Update display after command
        Optimize - should have same effect as displaying whole
                    new set of parts
         1. clear all prev_parts, if not in new, and present
         2. display all new_parts (includes pre-clearing)
        """
        ###return          # TFD - see if still displays
        if ActiveCheck.not_active():
            return
        
        command_manager = self.command_manager
        user_module = command_manager.user_module
        user_module.update_score_window()
 
        for part_id in self.prev_parts:
            part = user_module.get_part(part_id)
            part.display_clear()
        
        prev_selects = list(self.prev_selects.values())
        new_selects = list(self.new_selects.values())
        if SlTrace.trace("selected"):
            self.list_cmd("display_update before select_clear")
            self.list_selected("display_update before select_clear")
        prev_selects_save = copy.copy(self.prev_selects)  # HACK because of changes       
        user_module.select_clear(prev_selects)
        self.prev_selects = prev_selects_save
        if SlTrace.trace("selected"):
            self.list_cmd("display_update before select_set")
            self.list_selected("display_update before select_set")        
        user_module.select_set(new_selects)
        if SlTrace.trace("selected"):
            self.list_cmd("display_update after select_set")
            self.list_selected("display_update after select_set")        
        display_parts = list(self.new_parts.values())
        """ Add in selection changes if not already in display list """
        for part in self.prev_parts.values():
            if part.part_id not in display_parts:
                display_parts.append(part)
        for part in prev_selects:
            if part.part_id not in display_parts:
                display_parts.append(part)
        for part in new_selects:
            if part.part_id not in display_parts:
                display_parts.append(part)
        pdos = self.display_order(display_parts)    # Order display
        for new_part in pdos:
            part_id = new_part.part_id
            if not new_part.connecteds:
                SlTrace.lg("new_part no connecteds")
                continue 
            part = user_module.get_part(part_id)
            part.display()


    def display_order(self, parts):
        """ return parts in display order: Do all regions, then edges, then corners
         so corners are not blocked by regions
        """
        if len(parts) < 2:
            return parts    # No ordering required
        
        sel_area = parts[0].sel_area    # anyone is ok
        return sel_area.display_order(parts) 
    
            
    def execute(self):
        """
        Execute constructed command
        without modifying commandStack.
        All commands capable of undo/redo call this
        without storing it for redo
        """
        if self.user_module is None:
            return
        
        SlTrace.lg("\n execute(%s)" % self, "execute")
        self.user_module.trace_scores("execute")
        if SlTrace.trace("selected"):
            self.list_selected("execute")
        ###if SlTrace.trace("execute_edge_change"):
            ###execute_prev_keycmd_edge_mark = copy.copy(
            ###    self.user_module.keycmd_edge_mark)
        if SlTrace.trace("execute_part_change"):
            execute_prev_parts = {}
            for part_id, part in self.prev_parts.items():
                execute_prev_parts[part_id] = copy.copy(part)
            execute_orig_new_parts = {}
            for part_id, part in self.new_parts.items():
                execute_orig_new_parts[part_id] = copy.copy(part)
        self.command_manager.current_command = self
        if (self.prev_keycmd_edge_mark != None
            or self.new_keycmd_edge_mark != None):
            self.user_module.update_keycmd_edge_mark(
                self.prev_keycmd_edge_mark, self.new_keycmd_edge_mark)
        self.user_module.set_player(self.new_player)
        self.user_module.remove_parts(self.prev_parts.values())
        self.user_module.insert_parts(self.new_parts.values())
        self.user_module.display_messages(self.new_messages)
        if self.new_score is not None:
            SlTrace.lg("new_score %d: %s" % (self.new_score[1], self.new_score[0]), "score")
        self.user_module.update_score_from_cmd(self.new_score, self.prev_score)    
        self.display_update()
        self.user_module.display_print("execute(%s) AFTER"
                                          % (self.action), "execute_stack")
        SlTrace.lg("player=%s" % str(self.user_module.get_player()), "execute")
        self.user_module.select_print("execute(%s) AFTER"
                                         % (self.action), "execute_print")
        self.command_manager.cmd_stack_print("execute(%s) AFTER"
                                        % (self.action), "execute_stack")
        self.user_module.trace_scores("execute AFTER")
        '''
        if SlTrace.trace("execute_edge_change"):
            if (self.user_module.keycmd_edge_mark is not None
                and execute_prev_keycmd_edge_mark is not None
                and self.user_module.keycmd_edge_mark != execute_prev_keycmd_edge_mark):
                SlTrace.lg("    diff edge_mark: %s"
                            % execute_prev_keycmd_edge_mark.diff(self.user_module.keycmd_edge_mark))
        '''
        if SlTrace.trace("execute_part_change"):
            for part_id, part in execute_prev_parts.items():
                post_part = self.user_module.get_part(part_id)
                SlTrace.lg("    diff prev %d: %s %s"
                            % (part_id, part.part_type,
                                part.diff(post_part)))
            for part_id, part in execute_orig_new_parts.items():
                post_part = self.user_module.get_part(part_id)
                SlTrace.lg("    diff new %d: %s %s"
                           % (part_id, part.part_type,
                               part.diff(post_part)))
        if SlTrace.trace("selected"):
            self.list_selected("execute AFTER")
        return True

    
    def list_cmd(self, prefix=None):
        """ List selected parts
        :prefix: optional identifying string
        """
        if prefix is None:
            prefix = ""
        cmdstr = "%s" % self
        cmdstr = cmdstr.replace("\n", "\n" + "    ")
        SlTrace.lg("%scmd:    %s" % (prefix, cmdstr))

    
    def list_selected(self, prefix=None):
        """ List selected parts
        :prefix: optional identifying string
        """
        self.user_module.list_selected(prefix=prefix)


    def redo(self):
        """ Redo cmd
        """
        return self.do_cmd()
        
        
  
    def undo(self):
        """
        Remove the effects of the most recently done command
          1. remove command from commandStack
          2. add command to undoStack
          3. reverse changes caused by the command
          4. return true iff could undo
        Non destructive execution of command
        """

        try:
            cmd = select_copy(self)
            
        except:
            SlTrace.lg("SelectCommandPlay failure")
            return False
        self.command_manager.set_move_no(cmd.new_move_no)
        temp = cmd.new_move_no
        cmd.new_move_no = cmd.prev_move_no
        cmd.prev_move_no = temp
        
        temp = cmd.new_keycmd_edge_mark
        cmd.new_keycmd_edge_mark = cmd.prev_keycmd_edge_mark
        cmd.prev_keycmd_edge_mark = temp
        
        temp = cmd.new_player
        cmd.new_player = cmd.prev_player
        cmd.prev_player = temp
        
        temp = cmd.new_score
        cmd.new_score = cmd.prev_score
        cmd.prev_score = temp
        
        temp = select_copy(cmd.new_parts)
        cmd.new_parts = select_copy(cmd.prev_parts)
        cmd.prev_parts = temp
        
        temp_sel = cmd.new_selects
        cmd.new_selects = cmd.prev_selects
        cmd.prev_selects = temp_sel
        
        res = cmd.execute()
        if res:
            self.command_manager.undo_stack.append(self)
        return res
      