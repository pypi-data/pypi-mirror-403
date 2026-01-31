from tree_diet import tree_diet, py2cpp
from graph_classes import Bag, Graph

def test_grid():

    G = Graph()

    for i in range(9):
        G.add_vertex(i)

    G.add_edge(0,1)
    G.add_edge(1,2)

    G.add_edge(0,3)
    G.add_edge(1,4)
    G.add_edge(2,5)

    G.add_edge(3,4)
    G.add_edge(4,5)

    G.add_edge(3,6)
    G.add_edge(4,7)
    G.add_edge(5,8)

    G.add_edge(6,7)
    G.add_edge(7,8)

    R0 = Bag([])
    R = Bag([0,1,2,3])
    B1 = Bag([1,2,3,4])
    B2 = Bag([2,3,4,5])
    B3 = Bag([3,4,5,6])
    B4 = Bag([4,5,6,7])
    B5 = Bag([5,6,7,8])

    R0.add_child(R)
    R.add_child(B1)
    B1.add_child(B2)
    B2.add_child(B3)
    B3.add_child(B4)
    B4.add_child(B5)
    
    num_real, list_edges, _ = tree_diet(R0, G.adj, 2, [])
    print(num_real)
    assert(num_real==10)

def test_clique():

    R = Bag([])

    L = Bag([0,1,2,3,4])

    R.add_child(L)

    G = Graph()

    for u in range(5):
        G.add_vertex(u)

    for u in range(5):
        for v in range(5):
            G.add_edge(u,v)

    num_real, _, _ = tree_diet(R, G.adj, 4,[])
    
    assert(num_real == 10)

    num_real, list_edges, _ = tree_diet(R, G.adj, 3, [])
    assert(num_real == 6)
    assert(num_real == len(list_edges))    

    num_real, list_edges, _ = tree_diet(R, G.adj, 2, [])
    assert(num_real == 3)
    assert(num_real == len(list_edges))    

def test_clique_niceTD():

    bag_tags = {}

    R = Bag([])
    bag_tags[R] = 0
    
    G = Graph()

    for u in range(5):
        G.add_vertex(u)

    for u in range(5):
        for v in range(5):
            G.add_edge(u,v)

    B1 = Bag([0,1,2,3,4])
    B2 = Bag([0,1,2,3])
    B3 = Bag([0,1,2])
    B4 = Bag([0,1])
    B5 = Bag([1])

    R.add_child(B1)
    B1.add_child(B2)
    B2.add_child(B3)
    B3.add_child(B4)
    B4.add_child(B5)

    bag_tags[B1] = 1
    bag_tags[B2] = 2
    bag_tags[B3] = 3
    bag_tags[B4] = 4
    bag_tags[B5] = 5

    num_real, list_edges, _ = tree_diet(R, G.adj, 4, [], tags=bag_tags)
    assert(num_real == 10)
    assert(num_real == len(list_edges))    

    num_real, list_edges, _ = tree_diet(R, G.adj, 3, [])
    assert(num_real == 9)
    assert(num_real == len(list_edges))    
    
    num_real, list_edges, _ = tree_diet(R, G.adj, 2, [])
    assert(num_real == 7)
    assert(num_real == len(list_edges))    

def test_small_branching():

    G = Graph()

    for u in range(6):
        G.add_vertex(u)

    G.add_edge(0, 1)
    G.add_edge(1, 2)
    G.add_edge(0, 3)
    G.add_edge(1, 3)
    G.add_edge(1, 4)
    G.add_edge(2, 4)
    G.add_edge(3, 4)
    G.add_edge(3, 5) 
    G.add_edge(4, 5) 

    R = Bag([])

    B1 = Bag([1,3,4])
    B2 = Bag([0,1,3])
    B3 = Bag([1,2,4])
    B4 = Bag([3,4,5])

    R.add_child(B1) 
    B1.add_child(B2)
    B1.add_child(B3)
    B1.add_child(B4)

    ans = tree_diet(R, G.adj, 2, [])
    print(ans)
    num_real, list_edges, _ = ans
    assert(num_real == len(list_edges))    

    assert(num_real == 9)

def test_py2cpp():

    R = Bag([])

    B1 = Bag([1,3,4])
    B2 = Bag([0,1,3])
    B3 = Bag([1,2,4])
    B4 = Bag([3,4,5])

    R.add_child(B1) 
    B1.add_child(B2)
    B1.add_child(B3)
    B1.add_child(B4)
   
    d = py2cpp(R) 
    new_R = d[R]

    assert(len(new_R.children)==1)
    assert(len(new_R.children[0].children)==3)

if __name__=='__main__':

    test_grid()
