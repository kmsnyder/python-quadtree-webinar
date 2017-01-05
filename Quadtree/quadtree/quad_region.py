"""
    Quadtree implementation for storing points using integer-coordinate regions.
    
    Every Quad Node has four children, partitioning space accordingly based on 
    NE, NW, SW, SE quadrants. Each Node evenly divides quadrants. Each node 
    represents a square collection of points, evenly subdivided into four 
    children nodes, until leaf nodes representing an individual point. 
    
    The Quadtree implements set-semantics. This means there are no duplicate 
    (x, y) points in a quadtree.
    
    Actual point objects only exist within the leaf nodes.
    
    Note that this data structure is not suitable for collision detection of
    two-dimensional shapes. It offers an alternative approach for decomposing
    collection of points in two-dimensional region. This structure has been used
    for data compression of black/white pixel-based images, where a pixel is 
    either on (black) or off (white).
"""

import math
from adk.region import X, Y, Region

# Quadrant constants
NE = 0
NW = 1
SW = 2
SE = 3

def smaller2k(n):
    """
    Returns power of 2 which is smaller than n. Handles negative numbers.
    """
    if n == 0: return 0
    if n < 0:
        return -2**math.ceil(math.log2(-n))
    else:
        return 2**math.floor(math.log2(n))
    
def larger2k(n):
    """
    Returns power of 2 which is larger than n. Handles negative numbers.
    """
    if n == 0: return 0
    if n < 0:
        return -2**math.floor(math.log2(-n))
    else:
        return 2**math.ceil(math.log2(n))

def containsPoint(region, point):
    """Returns True if point contained in rectangle, closed on min, open on max."""
    if point[X] < region.x_min: return False
    if point[X] >= region.x_max: return False
    if point[Y] < region.y_min: return False
    if point[Y] >= region.y_max: return False
    
    return True

class QuadNode:
    
    def __init__(self, region, isFull = False):
        """Create empty QuadNode centered on origin of given region."""
        self.region = region
        self.origin = (region.x_min + (region.x_max - region.x_min)//2, 
                       region.y_min + (region.y_max - region.y_min)//2) 
        self.children = [None] * 4
        self.full = isFull
       
    def isPoint(self):
        """Determine if associated region is a single point. Region is closed on min, open on max."""
        return self.region.x_min + 1 == self.region.x_max and self.region.y_min + 1 == self.region.y_max
    
    def add(self, pt):
        """Add pt to QuadNode, creating and merging QuadNodes as needed."""
         
        # Find quadrant into which point is to be inserted and create if empty
        q = self.quadrant (pt)
        
        if self.children[q] == None:
            self.children[q] = QuadNode(self.subregion(q))
            if self.children[q].isPoint():
                self.children[q].full = True
            else:
                self.children[q].add(pt)
        else:
            # If we cannot add point to child, we are done
            if not self.children[q].add(pt):
                return False  
            
        # We have added pt to one of node's children. Perhaps we are full?
        if self.childrenFull():
            self.full = True
            self.children = [None] * 4   
        
        return True

    def remove(self, pt):
        """
        Remove pt from QuadNode. Eventually get to single point node or a full node 
        that contains this point.
        """
        if self.isPoint():
            return (None, True)
        
        q = self.quadrant(pt)
        if self.full:
            self.subdivide()
            self.full = False
            
        self.children[q],updated = self.children[q].remove(pt)
        if self.childrenNull():
            return (None,updated)
        return (self,updated)
    
    def childrenFull(self):
        """Determine if all children are full."""
        if self.children[NE] is None or not self.children[NE].full: return False
        if self.children[NW] is None or not self.children[NW].full: return False
        if self.children[SW] is None or not self.children[SW].full: return False
        if self.children[SE] is None or not self.children[SE].full: return False
        
        return True
    
    def childrenNull(self):
        """Determine if all children are None."""
        if self.children[NE] is not None: return False
        if self.children[NW] is not None: return False
        if self.children[SW] is not None: return False
        if self.children[SE] is not None: return False
        
        return True
    
    def subregion(self, q):
        """Return region associated with given quadrant."""
        r = self.region
        if q is NE:
            return Region(self.origin[X], self.origin[Y], r.x_max,        r.y_max)
        if q is NW:
            return Region(r.x_min,        self.origin[Y], self.origin[X], r.y_max)
        if q is SW:
            return Region(r.x_min,        r.y_min,        self.origin[X], self.origin[Y])
        if q is SE:
            return Region(self.origin[X], r.y_min,        r.x_max,        self.origin[Y])
    
    def subdivide(self):
        """Add four children nodes to node, and retain full status of parent."""
        self.children[NE] = QuadNode(self.subregion(NE), self.full)
        self.children[NW] = QuadNode(self.subregion(NW), self.full)
        self.children[SW] = QuadNode(self.subregion(SW), self.full)
        self.children[SE] = QuadNode(self.subregion(SE), self.full)
    
    def quadrant(self, pt):
        """Determine quadrant in which point exists."""
        if pt[X] >= self.origin[X]:
            if pt[Y] >= self.origin[Y]:
                return NE
            else:
                return SE
        else:
            if pt[Y] >= self.origin[Y]:
                return NW
            else:
                return SW
     
    def preorder(self):
        """Pre-order traversal of tree rooted at given node."""
        yield self

        for node in self.children:
            if node:
                for n in node.preorder():
                    yield n

    def __str__(self):
        """toString representation."""
        return "[{} ({}): {},{},{},{}]".format(self.region, self.status, self.children[NE], self.children[NW], self.children[SW], self.children[SE])

class QuadTree:

    def __init__(self, region):
        """
        Create QuadTree defined over existing rectangular region. Assume that (0,0) is
        the lower left coordinate and the half-length side of any square in quadtree
        is power of 2. If incoming region is too small, this expands accordingly.    
        """
        self.root = None
        self.region = region.copy()
        
        xmin2k = smaller2k(self.region.x_min)
        ymin2k = smaller2k(self.region.y_min)
        xmax2k = larger2k(self.region.x_max)
        ymax2k = larger2k(self.region.y_max)
        
        self.region.x_min = self.region.y_min = min(xmin2k, ymin2k)
        self.region.x_max = self.region.y_max = max(xmax2k, ymax2k)
        
    def add(self, pt):
        """Add point to QuadTree. Return False if outside region or already exists."""
        # Doesn't belong in this region, leave now
        if not containsPoint (self.region, pt):
            return False
        
        if self.root is None:
            self.root = QuadNode(self.region)
            
        return self.root.add (pt)
    
    def remove(self, pt):
        """Remove pt should it exist in tree. Return True if was removed, else False."""
        if self.root is None:
            return False
        
        if not containsPoint (self.region, pt):
            return False
        
        self.root,updated = self.root.remove(pt)
        return updated
    
    def __contains__(self, pt):
        """Check whether exact point appears in QuadTree."""
        if not containsPoint (self.region, pt):
            return False
        
        n = self.root
        while n:
            if n.full:
                return True

            q = n.quadrant(pt)
            n = n.children[q]
    
        return False
    
    def __iter__(self):
        """Pre-order traversal of elements in the tree."""
        if self.root:
            # This gives QUADNODES which we need to check for FULL status.
            for n in self.root.preorder():
                if n.full:
                    # yield each pt in region, one at a time.
                    for x in range(n.region.x_min, n.region.x_max):
                        for y in range(n.region.y_min, n.region.y_max):
                            yield (x,y)
                elif n.isPoint():
                    yield (n.region.x_min, n.region.y_min)
