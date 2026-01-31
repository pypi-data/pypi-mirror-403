from graph_classes import Graph, Bag
from tree_diet import tree_diet

def test_tiny_big():

    G = Graph()

    for i in range(5):
        G.add_vertex(i)

    G.add_edge(0,1)
    G.add_edge(0,2)
    G.add_edge(0,3)

    G.add_edge(1,2)
    G.add_edge(1,3)

    G.add_edge(2,3)

    G.add_edge(1,4)
    G.add_edge(2,4)
    G.add_edge(3,4)

    R = Bag([])

    B1 = Bag([0])
    B2 = Bag([0,1])
    B3 = Bag([0,1,2])
    B4 = Bag([0,1,2,3])
    B5 = Bag([1,2,3,4])

    R.add_child(B1)
    B1.add_child(B2)
    B2.add_child(B3)
    B3.add_child(B4)
    B4.add_child(B5)

    OPT, real_edges, color_dict = tree_diet(R, G.adj, 2, [])

    assert(OPT==7)

def test_tiny():

    
    G = Graph()

    for i in range(4):
        G.add_vertex(i)

    G.add_edge(0,1)
    G.add_edge(1,2)
    G.add_edge(2,3)

    G.add_edge(0,2)
    G.add_edge(1,3)

    R = Bag([])

    B1 = Bag([0])
    B2 = Bag([0,1])
    B3 = Bag([0,1,2])
    B4 = Bag([1,2,3])

    R.add_child(B1)
    B1.add_child(B2)
    B2.add_child(B3)
    B3.add_child(B4)

    must_have_edges = [(0,1),(1,2),(2,3)]

    OPT, real_edges, color_dict = tree_diet(R, G.adj, 2, must_have_edges)

    for e in must_have_edges:
        assert(e in real_edges)
   
    assert(len(real_edges)==5) 
