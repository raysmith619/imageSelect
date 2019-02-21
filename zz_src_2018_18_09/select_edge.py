# select_edge.py        

from select_error import SelectError
from select_loc import SelectLoc
from select_part import SelectPart

class SelectEdge(SelectPart):
    width_display = 5      # Default edge display line width in pixels
    width_select = 3      # Default edge select line width in pixels
    width_standoff = 5     # Default edge buffer for adjacent parts
    width_enlarge = 2      # Enlarge number, added to width
    fill = "blue"   # Default edge color
    fill_highlight = "purple"   # Default edge highlight color

    
    def __init__(self, rect=None):
        SelectPart.__init__(self, "edge", rect=None)
        self.loc = SelectLoc(rect=rect)


    def get_nodes(self, indexes=None):
        """ Find nodes/points of part
        return pairs (index, node)
        """
        nodes = []
        if indexes is None:
            nodes = [(0,self.loc.coord[0]), (1,self.loc.coord[1])]
        else:
            if not isinstance(indexes, list):
                indexes = [indexes]     # Make a list of one
            for index in indexes:
                nodes.append((index,self.loc.coord[index]))
        return nodes


    def set_node(self, index, node):
        """ Set node to new value
        """
        self.loc.coord[index] = node


    def edge_dxy(self):
        """ Get "edge direction" as x-increment, y-increment pair
        """
        loc = self.loc
        rect = loc.coord
        p1 = rect[0]
        p2 = rect[1]
        edx = p2[0] - p1[0]             # Find edge direction
        edy = p2[1] - p1[1]
        
                     
