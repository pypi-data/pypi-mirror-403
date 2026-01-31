from graph_classes import Graph, Bag, recurse_print
from tree_diet import tree_diet

def test_buggy():

    
    G = Graph()

    for u in range(6):
        G.add_vertex(u)

    G.add_edge(1,2)
    G.add_edge(2,3)

    G.add_edge(2,5)

    R = Bag([])


    B1 = Bag([4])
    B2 = Bag([3,4])
    B3 = Bag([0,3,4])
    B4 = Bag([0,3,4,5])
    B5 = Bag([0,1,2,3,5])

    R.add_child(B1)
    B1.add_child(B2)
    B2.add_child(B3)
    B3.add_child(B4)
    B4.add_child(B5)

    must_have_edges = [(1,2),(2,3)]

    recurse_print(R, 0)

    OPT, real_edges, _ = tree_diet(R, G.adj, 2, must_have_edges)

    for e in must_have_edges:
        assert(e in real_edges)
  
    assert(len(real_edges)==2) 

if __name__=='__main__':
    test_buggy()
