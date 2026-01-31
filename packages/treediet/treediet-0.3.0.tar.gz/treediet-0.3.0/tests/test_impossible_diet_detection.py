from graph_classes import Graph, Bag
from graph_classes import impossible_diet 

def test_tiny_obstacle():

    R = Bag([0,1,2,3])
    
    B1 = Bag([3,5])
    B2 = Bag([3,4])

    R.add_child(B1)
    R.add_child(B2)

    important_edges = [(3,5),(3,4)]
    target_width = 2

    assert(impossible_diet(R, target_width, important_edges))

    
if __name__=="__main__":
    test_tiny_obstacle()
