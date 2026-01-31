from itertools import combinations
import random
import numpy as np


# IMPORTANT CLASSES

class Graph:
    """
    simple graph class, just used for producing its adjacency dictionary.
    
    """

    def __init__(self, list_vertices=None):
        """
        Graph constructor: optionally takes a list of vertices as input to initialize the vertex set.

        :param list_vertices: Optional list of vertices for the graph, defaults to None
        :type list_vertices: list, optional
        """

        #: (**dict**) - initialized at {} by __init__. Adjacency dictionary for the graph. The keys are vertices (usually integers) and the values are lists of vertices. The purpose of the graph class is basically to form this dictionary. 
        self.adj = {}
        
        #: (**int**) - initialized at 0 by __init__. Number of vertices. Updated by add_vertex. Equal at all times to the number of entries in adj.
        self.n = 0

        if list_vertices:
            self.n = len(list_vertices)

            for i in list_vertices:
                self.adj[i] = set()
        
    def add_vertex(self, i):
        """
        Adds a vertex to the graph

        :param i: Integer to add as new vertex of the graph. If the vertex is already present nothing happens.
        :type i: **int**
        """

        try:
            self.adj[i]
        except KeyError:
            self.adj[i] = set()
            self.n += 1
            

    def add_edge(self, i, j):
        """
        Adds an edge between two vertices

        :param i: an integer describing a vertex.
        :type i: **int**
        :param j: an integer describing a vertex.
        :type j: **int**
        """

        if i >= self.n:
            return
        if i == j:
            return

        self.adj[i].add(j)
        self.adj[j].add(i)

def impossible_diet(R, target_width, important_edges):
    """
    Detects the presence of a specific kind of obstacle to the existence
    of a diet achieving target width while preserving all
    elements of important_edges.
 
    The obstacle detected here is the presence of a too large number
    of "problematic vertices" in a bag. A problematic vertex is involved
    in at least two important edges, such that they are realized
    on different sides of one of the edges of the bag. This situation implies that
    removing the vertex from the bag breaks at least one of these
    two important edges.

    If this function returns true, then a diet achieving target_width without
    breaking important edges is definitely impossible.
    If this function returns false, then the existence of a diet achieving 
    target width without breaking important edges is maybe possible but
    not guaranteed (the obstacle does not catch (yet ?) all important
    edge breaking scenari)

    :param R: A **bag**, the root of the tree decomposition.
    :type R: **bag** 

    :param target_width: the target width of the diet
    :type target_width: **integer**   

    :param important_edges: A list of important edges, i.e a list of 2-uples
    of vertices.
    :type important_edges: **list** of 2-uples of vertices.
    """

    # switching to adjacency representation of TD:
    bag_adj = {}

    queue = [R]
    
    while len(queue)>0:
        B = queue.pop()
        for c in B.children:
            try:
                bag_adj[B].append(c)
            except KeyError:
                bag_adj[B] = [c]
            try:
                bag_adj[c].append(B)
            except KeyError:
                bag_adj[c] = [B]

            queue.append(c)

    # auxiliary function: finding on the other side of which sep of B is u.
    def find_sep(B,u):
        assert(u not in B.vertices)
        queue = []

        marked = {}
        for BB in bag_adj.keys():
            marked[BB] = False

        for N in bag_adj[B]:
            sep = frozenset(set(B.vertices).intersection(set(N.vertices)))
            queue.append((N,sep))
            marked[N] = True
        
        while len(queue) > 0:
            C, sep = queue.pop()
            marked[C] = True
            if u in C.vertices:
                return sep
            for N in bag_adj[C]:
                if not marked[N]:
                    queue.append((N,sep))
        
    
    # Going through the tree looking for bags for which diet implies necesarily
    # breaking important edges.
    
    queue = [R]

    while len(queue) > 0:
        B = queue.pop()

        count_problematic = 0
        for u in B.vertices:
            seps_involved = set([]) # seps separating u, v important edge. 

            for e in important_edges:
                if e[0]==u or e[1]==u:
                    if e[0]==u:
                        v=e[1]
                    if e[1]==u:
                        v=e[0]

                    if v not in B.vertices:
                        seps_involved.add(find_sep(B, v))

            if len(seps_involved) > 1:
                count_problematic += 1

#        print(B.vertices, "count_problematic: ", count_problematic)
        if count_problematic > target_width+1:
            return True

        for C in B.children:
            queue.append(C)

    #If survived all checks for all bags
    return False
        

        

                    

            



class Bag:
    """
    Bag class for constructing tree decompositions.
    There is no tree decomposition class. A tree decomposition
    will be represented by its root bag. 
    """
    def __init__(self, vertices):
        """
        Creates a bag containing the vertices given as parameter.
    
        :param vertices: list of vertices to include in the bag.
        :type vertices: **list** 
        """

        #: (**list**) list of vertices, describing the content of the bag.
        self.vertices = vertices

        #: (**list** <Bag>) list of bags, describing the **children** of the bag in the tree decomposition. There is no Tree Decomposition class. All connectivity information between bags is contained in the **children** fields. 
        self.children = []

    def add_child(self, child):
        """
        Adds a connection to an existing Bag, which becomes a **child**. Simple call to self.children.append.

        :param child: **child** Bag to connect.
        :type child: Bag
        """

        self.children.append(child)

    def make_nice(self, child):

        self.children.remove(child)

        inter = [u for u in self.vertices if u in child.vertices]
        
        to_introduce = [v for v in self.vertices if v not in inter]
        to_forget = [v for v in child.vertices if v not in inter]

        seq = []

        cur_vertices = self.vertices

        for u in to_introduce[::-1]:

            if u == to_introduce[-1]:
                continue

            seq.append(py_bag([v for v in cur_vertices if v!= u]))

            cur_vertices = [v for v in cur_vertices if v!= u]

        if len(self.vertices) > 0:
            seq.append(py_bag(list(inter)))
        cur_vertices = inter

        for u in to_forget[::-1]:

            if u == to_forget[0]:
                continue

            cur_vertices.append(u)
            seq.append(py_bag([u for u in cur_vertices]))

        self.add_child(seq[0])
        for k in range(1,len(seq),1):
            seq[k-1].add_child(seq[k])

        seq[-1].add_child(child) 

    def dupli_nice(self):

        if len(self.children) > 2:

            duplicate = py_bag([u for u in self.vertices])

            for i in range(1, len(self.children),1):
                duplicate.add_child(self.children[i])

            self.children = [self.children[0]]

            self.add_child(duplicate)
            

def nicify(R):

    queue = [R]

    while len(queue) > 0:

        u = queue.pop()

        children = [c for c in u.children]
        for c in children:
            queue.append(c)
            u.make_nice(c)        

    queue = [R]

    while len(queue) > 0:

        u = queue.pop()

        n_children = len(u.children)

        if n_children > 2:

            for _ in range(n_children-2):
                u.dupli_nice()

        for c in u.children:
            queue.append(c)           
 
    return R
   


def recurse_print(b, depth, tags=None):

    for _ in range(depth):
        print("   ", end="")

    if tags:
        print("tag ", tags[b], end=" ")    

    print(b, b.vertices)
    for c in b.children:
        recurse_print(c, depth+1, tags=tags)    
