# select_corner.py        

from select_error import SelectError
from select_loc import SelectLoc
from select_part import SelectPart

class SelectCorner(SelectPart):
    corner_width_display = 8    # Default display size of corner in pixels
    corner_width_select = 8    # Default select size of corner in pixels
    corner_width_standoff = 10    # Default standoff size of corner in pixels
    corner_fill = "red" # Default corner color
    corner_fill_highlight = "pink"      # Default corner highlight color

    
    def __init__(self, part_type, point=None):
        SelectPart.__init__(self, "corner", point=point)
        self.loc = SelectLoc(point=point)


    def get_nodes(self, indexes=None):
        """ Find nodes/points of part
        return pairs (index, node)
        """
        return [(0,self.loc.coord)]


    def set_node(self, index, node):
        """ Set node to new value
        """
        if index != 0:
            raise SelectError("set_node %s non-zero index %d"
                              % (self, index))
        self.loc.coord = node


    def edge_dxy(self):
        """ Get "edge direction" as x-increment, y-increment pair
        """
        return 0,0                  # No change
        
                     
