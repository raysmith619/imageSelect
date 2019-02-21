# select_part.py        

import math
    
from select_error import SelectError
from select_loc import SelectLoc

class SelectPart(object):
    
    SZ_DISPLAY  = 1             # Size for display
    SZ_SELECT = 2               # Size for selection
    SZ_STANDOFF = 3             # Size for standoff
    
    edge_width_display = 5      # Default edge display line width in pixels
    edge_width_select = 3      # Default edge select line width in pixels
    edge_width_standoff = 5     # Default edge buffer for adjacent parts
    edge_width_enlarge = 2      # Enlarge number, added to width
    edge_fill = "blue"   # Default edge color
    edge_fill_highlight = "purple"   # Default edge highlight color
    corner_width_display = 8    # Default display size of corner in pixels
    corner_width_select = 8    # Default select size of corner in pixels
    corner_width_standoff = 10    # Default standoff size of corner in pixels
    corner_fill = "red" # Default corner color
    corner_fill_highlight = "pink"      # Default corner highlight color
    region_fill = "clear"   # Default edge color
    region_fill_highlight = "lightgray"   # Default edge highlight color

    id = 0          # Unique handle ID
            
            
    @staticmethod
    def is_point_equal(pt1, pt2):
        """ Check if points are equal
        """
        if pt1[0] == pt2[0] and pt1[1] == pt2[1]:
            return True
        
        return False
    

    @staticmethod
    def get_olaps(parts, sz_type=None, enlarge=False):
        """ Get overlapping rectangle, if any, of a list of parts
        """
        if len(parts) < 2:
            return None
        
        part1 = parts.pop()
        for part in parts:
            olap_rect = part1.get_overlap(part, sz_type=sz_type, enlarge=enlarge)
            if olap_rect is None:
                return None
            
            part1 = SelectPart("region", rect=olap_rect)
        return olap_rect

    @classmethod
    def get_edge_width(cls, sz_type=SZ_DISPLAY):
        """ Return class edge width
        :sz_type:  size type
        """
        width = cls.edge_width_display
        if sz_type == cls.SZ_SELECT:
            width = cls.edge_width_select
        elif sz_type == cls.SZ_STANDOFF:
            width = cls.edge_width_standoff
            
        return width
    
    
    @classmethod
    def get_corner_rect_at_pt(cls, pt, sztype=None, enlarge=False):
        """ Get corner rectangle at given point
        """
        if sztype is None:
            sztype=cls.SZ_DISPLAY
        corner_width = cls.corner_width_display
        if sztype == SelectPart.SZ_DISPLAY:
            corner_width = cls.corner_width_display
        elif sztype == SelectPart.SZ_SELECT:
            corner_width = cls.corner_width_select
        elif sztype == SelectPart.SZ_STANDOFF:
            corner_width = cls.corner_width_standoff
            
        c1x = pt[0]
        if c1x >= corner_width/2:
            c1x -= corner_width/2
        c1y = pt[1]                 # inside upper left  corner
        if c1y >= corner_width/2:
            c1y -= corner_width/2
        if isinstance(c1x, list):
            print("c1x is a list")
        c3 = (c1x + corner_width, c1y + corner_width)
        c3x = c3[0]
        c3y = c3[1]
                                                    # Enlarge a bit
        if enlarge:
            el = 2                  # enlarge number of pixels
            c1x -= el
            c1y -= el
            c3x += el
            c3y += el
        
        """ Ensure uL to left and above lR """
        return SelectLoc.order_ul_lr(c1x,c1y,c3x,c3y)

    
    def __init__(self, part_type, point=None, rect=None, tag=None, xy=None):
        SelectPart.id += 1
        self.id = SelectPart.id
        self.connecteds = []            # Start with none connected
        self.part_type = part_type
        self.highlighted = False
        self.highlight_tag = None
        self.display_tag = tag
        if point is not None:
            self.loc = SelectLoc(point=point)
        elif rect is not None:
            self.loc = SelectLoc(rect=rect)
        else:
            raise SelectError("SelectPart: neither point nor rect type")


    def __str__(self):
        """ Provide reasonable view of part
        """
        return self.part_type + " id=%d" % self.id + " at %s" % self.loc 


    def get_nodes(self, indexes=None):
        """ Find nodes/points of part
        return pairs (index, node)
        """
        if self.is_corner():
            return [(0,self.loc.coord)]
        elif self.is_edge():
            nodes = []
            if indexes is None:
                nodes = [(0,self.loc.coord[0]), (1,self.loc.coord[1])]
            else:
                if not isinstance(indexes, list):
                    indexes = [indexes]     # Make a list of one
                for index in indexes:
                    nodes.append((index,self.loc.coord[index]))
            return nodes
        else:
            return []


    def set_node(self, index, node):
        """ Set node to new value
        """
        if self.is_corner():
            if index != 0:
                raise SelectError("set_node %s non-zero index %d"
                                  % (self, index))
            self.loc.coord = node
        elif self.is_edge():
            self.loc.coord[index] = node
        elif self.is_region():
            self.loc.coord[index] = node
        else:
            raise SelectError("set_node: % Unrecognized part type:%d" 
                              % (self, self.part_type))             
    def edge_dxy(self):
        """ Get "edge direction" as x-increment, y-increment pair
        """
        loc = self.loc
        if loc.type == SelectLoc.LOC_POINT:
            return 0,0                  # No change
        elif loc.type == SelectLoc.LOC_RECT:
            rect = loc.coord
            p1 = rect[0]
            p2 = rect[1]
            edx = p2[0] - p1[0]             # Find edge direction
            edy = p2[1] - p1[1]
        else:
            raise SelectError("edge_dxy: unrecognized loc type")
        return edx, edy

        
    def highlight_clear(self, tag=None):
        self.highlighted = False
        self.highlight_tag = tag

        
    def highlight_set(self, tag=None):
        self.highlighted = True
        self.highlight_tag = tag


    def is_highlighted(self):
        return self.highlighted
    
    
    def get_connected_index(self, part):
        """ Get connected part index (end), to which we are connected
        0, 1 for edges, 0 for others
        """
        is_connected = False           # Set True if find a connection
        for eci, connected in enumerate(part.connecteds):
            if self.is_same(connected):
                is_connected = True
                break     # Got corner's end of edge
        if not is_connected:
            return None
        
        return eci
    
    
    def get_connected_loc_indexes(self, part):
        """ Get connected part's location index which we share
        Returns pair our index, other index
        """
        is_connected = False           # Set True if find a connection
        our_type = self.part_type
        our_loc = self.loc
        our_coord = our_loc.coord
        part_type = part.part_type
        part_loc = part.loc
        part_coord = part_loc.coord
        
        if isinstance(our_coord, list):
            our_coords = our_coord
        else:
            our_coords = [our_coord]
        
        if isinstance(part_coord, list):
            part_coords = part_coord
        else:
            part_coords = [part_coord]
                
        for oc in our_coords:
            for pci, pc in enumerate(part_coords):
                try:
                    if oc[0] == pc[0] and oc[1] == pc[1]:
                        pcio = 1 - pci      # only two 
                        return pci, pcio
                except:
                    raise SelectError("oc,pc compare failed")
                 
        return 0,0
    
    
    def get_unconnected_index(self, part):
        """ Get unconnected part index (far end), to which we are connected
        0, 1 for edges, 0 for others
        """
        is_not_connected = False           # Set True if find a connection
        for eci, connected in enumerate(part.connecteds):
            if not self.is_same(connected):
                is_not_connected = True
                break     # Got corner's far end of edge
        if not is_not_connected:
            return None
        
        return eci

    def get_points(self):
        """ return p1, p2 of edge
        """
        nodes = self.get_nodes()
        points = []
        for node in nodes:
            points.append(node[1])
        return points
    
    

    def get_rect(self, sz_type=None, enlarge=False):
        """ Return selectable  rectangle for this part
        """
        if sz_type is None:
            sz_type=SelectPart.SZ_DISPLAY
        if self.is_corner():
            return self.get_corner_rect(sz_type=sz_type, enlarge=enlarge)
        if self.is_edge():
            return self.get_edge_rect(sz_type=sz_type, enlarge=enlarge)
        if self.is_region():
            return self.get_region_rect(sz_type=sz_type, enlarge=enlarge)
        return 0,0,1,1        # minute 


    def get_corner_rect(self, sz_type=None, enlarge=False):
        """ Get upper left x,y and lower right x,y of corner display
        If rectangle, we provide small rectangle at that point
        :handle: - SelectPart for corner
        """
        if sz_type is None:
            sz_type=SelectPart.SZ_DISPLAY
        loc = self.loc
        if loc.type == SelectLoc.LOC_POINT:
            pt = loc.coord
        elif loc.type == SelectLoc.LOC_RECT:
            pt = loc.coord[0]
        else:
            raise SelectError("Unsupported loc.type %d in (%s)"
                              % (loc.type, self))
        if isinstance(pt[0], list):
            print("pt1[0] is a list")
        return SelectPart.get_corner_rect_at_pt(pt, enlarge=enlarge)


    def get_corner_width(self, sz_type=None):
        if sz_type is None:
            sz_type=SelectPart.SZ_DISPLAY
        width = SelectPart.corner_width_display
        if sz_type == SelectPart.SZ_SELECT:
            width = SelectPart.corner_width_select
        elif sz_type == SelectPart.SZ_STANDOFF:
            width = SelectPart.corner_width_standoff

    
    def get_edge_rect(self, sz_type=None, enlarge=False):
        """ Get rectangle containing edge handle
        Use connected corners
        Coordinates returned are ordered ulx, uly, lrx,lry so ulx<=lrx, uly<=lry
        We leave room for the corners at each end
        :edge - selected edge
        :enlarge - True - enlarge rectangle
        """
        if sz_type is None:
            sz_type=SelectPart.SZ_DISPLAY
        c1x = self.loc.coord[0][0]
        c1y = self.loc.coord[0][1]
        c3x = self.loc.coord[1][0]
        c3y = self.loc.coord[1][1]
        c1x,c1y,c3x,c3y = SelectLoc.order_ul_lr(c1x,c1y,c3x,c3y)
        """ Leave room at each end for corner """
        dir_x, dir_y = self.edge_dxy()
        wlen = self.get_edge_width(sz_type)/2
        if dir_y != 0:          # Check if in y direction
            if c1x >= wlen:     # Yes - widen the orthogonal dimension
                c1x -= wlen
            c3x += wlen
            c1y += wlen         # Yes - shorten ends to avoid corner
            c3y -= wlen
        if dir_x != 0:          # Check if in x direction
            if c1y >= wlen:     # Yes - widen the orthogonal dimension
                c1y -= wlen
            c3y += wlen
            c1x += wlen         # Yes - shorten ends to avoid corner
            c3x -= wlen
        if enlarge:
            wenlarge = SelectPart.edge_width_enlarge
            if dir_y != 0:
                c1x -= wenlarge
                c3x += wenlarge
            if dir_x != 0:
                c1y -= wenlarge 
                c3y += wenlarge
                
        return c1x,c1y,c3x,c3y


    def get_overlap(self, part, sz_type=None, enlarge=False):
        """ return rectangle normalized (p1,p2) which part we and part overlap, None if no overlap
        Note: get_rect returns normalized rectangles
        :part: possibly overlapping part
        :sz_type:  size type Default:  SelectPart.SZ_SELECT
        :enlarge:  True  - part is enlarged(highlighted)
        :returns: overlap rectangle if any overlap, None if no overlap
        """
        if sz_type is None:
            sz_type = SelectPart.SZ_SELECT
        self_xyxy = self.get_rect(sz_type=sz_type)
        part_xyxy = part.get_rect(sz_type=sz_type, enlarge=enlarge)
        X1 = 0
        Y1 = 1           # Mnemonic
        X2 = 2
        Y2 = 3
        """ Find left most rectangle """
        left_x = self_xyxy[X1]
        left_xyxy = self_xyxy
        right_xyxy = part_xyxy
        if part_xyxy[X1] < left_x:
            left_x = part_xyxy[X1]
            left_xyxy = part_xyxy
            right_xyxy = self_xyxy
        if right_xyxy[X1] > left_xyxy[X2]:
            return None         # left rectangle totally left of right
        
        olap_x1 = right_xyxy[X1]      # left edge of right rectangle
        if right_xyxy[X2] > left_xyxy[X2]:
            olap_x2 = left_xyxy[X2]       # limited by left rectangle
        else:
            olap_x2 = right_xyxy[X2]      # limited by right rectangle  

        """ Find top most rectangle """
        upper_y = self_xyxy[Y1]
        upper_xyxy = self_xyxy
        lower_xyxy = part_xyxy
        if part_xyxy[Y1] < upper_y:
            upper_y = part_xyxy[Y1]
            upper_xyxy = part_xyxy
            lower_xyxy = self_xyxy
        if lower_xyxy[Y1] > upper_xyxy[Y2]:
            return None         # upper rectangle totally above of lower
        
        olap_y1 = lower_xyxy[Y1]      # upper edge of lower rectangle
        if lower_xyxy[Y2] > upper_xyxy[Y2]:
            olap_y2 = upper_xyxy[Y2]       # limited by upper rectangle
        else:
            olap_y2 = lower_xyxy[Y2]      # limited by lower rectangle  


        return [(olap_x1,olap_y1), (olap_x2, olap_y2)]
        
    def get_region_rect(self, sz_type=None, enlarge=False):
        """ Get upper left x,y and lower right x,y region
        :handle: region's SelectPart
        Region is a set of parts, with the corners being the boundary
        """
        if sz_type is None:
            sz_type=SelectPart.SZ_DISPLAY
        corners = []
        for part in self.connecteds:
            if part.is_corner():
                corners.append(part)
        if len(corners) < 4:
            ###print("Region with %d corners %s" % (len(corners), self))
            co = self.loc.coord
            c1x = co[0][0]
            c1y = co[0][1]
            c3x = co[1][0]
            c3y = co[1][1]
        else:
            c1x = corners[0].loc.coord[0]
            c1y = corners[0].loc.coord[1]
            c3x = corners[2].loc.coord[0]
            c3y = corners[2].loc.coord[1]
        c1x,c1y,c3x,c3y = SelectLoc.order_ul_lr(c1x,c1y,c3x,c3y)
        wlen = self.get_edge_width(sz_type)
        c1x += wlen
        c1y += wlen
        c3x -= wlen
        c3y -= wlen
        if enlarge:
            c1x -= self.edge_width_enlarge
            c1y -= self.edge_width_enlarge 
            c3x += self.edge_width_enlarge
            c3y += self.edge_width_enlarge
        return c1x,c1y,c3x,c3y
        
        
    def get_x(self):
        return self.get_xy()[0]

    
    def get_y(self):
        return self.get_xy()[1]
    
        
    def get_xy(self):
        return self.loc_to_xy()    


    def is_over(self, x, y, sz_type=None, enlarge=False):
        """ Return True if part is over (x,y) ie. point (x,y) is within
        our part
        :x,y: - x,y coordinates on canvas
        :enlarge: - enlarged rectangle (highlighted part)
        """
        if sz_type is None:
            sz_type=SelectPart.SZ_SELECT
        try:
            c1x,c1y,c3x,c3y = self.get_rect(sz_type=sz_type, enlarge=enlarge)
        except:
            print("bad get_rect call")
        if x >= c1x and x <= c3x and y >= c1y and y <= c3y:
            print("is_over: %s : c1x:%d, c1y:%d, c3x:%d, c3y:%d" % (self, c1x,c1y,c3x,c3y))
            return True
        
        return False
    
    
    def loc_to_xy(self, loc=None):
        """ Convert handle object location to associated point
        Upper left corner
        """
        if loc is None:
            loc = self.loc
        loc_type = loc.type
        if loc_type == SelectPart.LOC_POINT:
            pt = loc.coord
            return (pt[0],pt[1])
        elif loc_type == SelectPart.LOC_RECT:
            rect = loc.coord
            p1 = rect[0]
            p1x = p1[0]
            p1y = p1[1]
            return (p1x, p1y)
        else:
            raise SelectError("loc_to_xy: unrecognized loc type %d(%s)" % (loc_type, loc))

                        
    def set_xy(self, xy=None):
        self.xy = xy 

    def is_corner(self):
        if self.part_type == "corner":
            return True
        return False

    def is_edge(self):
        if self.part_type == "edge":
            return True
        return False

    def is_region(self):
        if self.part_type == "region":
            return True
        return False
    
            
    def add_connected(self, handle):
        """ Add to list of connected, parts affected by changes
        to this handle
        """
        if not self.is_connected(handle):
            self.connecteds.append(handle)
        return handle
    
    
    def is_connected(self, handle):
        """ Test if handle already connected to us
        """
        for con in self.connecteds:
            if handle.id == con.id:
                return True

    def is_covering(self, part):
        """ Check if parts cover each other
        :returns:  True if same rectangle
        """
        if self.get_rect() == part.get_rect():
            return True
        
        return False
        
    
    def is_same(self, handle):
        """ Determine if handle is same as us
        """
        if self.id == handle.id:
            return True
        return False
        
                     
