from tkinter import *


class Dialog(Toplevel):

    def __init__(self, parent, title = None,modal=True):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = Frame(self)
        #register validators
        ''' 
        self.validatePosInt = (body.register(self.OnValidatePosInt), 
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.initial_focus = self.body(body)   #this calls the body function which is overridden, and which draws the dialog
        body.grid()
        self.buttonbox()
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+50,
                                  parent.winfo_rooty()+50))
        self.initial_focus.focus_set()
        '''

        if modal:
            self.wait_window(self)
            
    if __name__ == "__main__":
        from dialog_test import Dialog
        mw = Tk()
        Dialog(parent=mw, title="testing Dialog")  