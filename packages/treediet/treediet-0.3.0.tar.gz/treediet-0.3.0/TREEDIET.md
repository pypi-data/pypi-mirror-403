This package contains an implementation of an algorithm that reduces the 
width of a given tree decomposition while removing a minimum number of edges.
An example of use is:

```python
    from treediet.graph_classes import Graph, Bag
    from treediet.tree_diet import tree_diet
        
    # Graph Definition
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

    # Tree Decomposition construction
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

    # Calling Dynamic Programming tree-diet algorithm
    OPT, real_edges, color_dictionary = tree_diet(R, G.adj, 2, [])

    print(OPT,real_edges, color_dictionary)
```

The output should be:

```
    >> 7, [(0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (1, 4), (3, 4)], {1: {0: 1}, 2: {0: 1, 1: 1}, 3: {0: 1, 1: 1, 2: 1}, 4: {0: 1, 1: 1, 2: 3, 3: 1}, 5: {1: 1, 2: 3, 3: 1, 4: 1}}

```

## Source code documentation
 
[https://bmarchand-perso.gitlab.io/tree-diet/](https://bmarchand-perso.gitlab.io/tree-diet/)
