# tree-diet

Implementation of the tree diet algorithm, reducing the treewidth of a graph through min cardinality edge deletion.
Code used for numerical experiments in companion paper: https://hal.inria.fr/hal-03206132/.
Source code documentation available at: https://bmarchand-perso.gitlab.io/tree-diet/.

## Installation
The package is on pypi: https://pypi.org/project/treediet/
```
pip install treediet
```

## Usage

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

## build and publishing
```
cibuildwheel --output-dir dist
python3 -m build --sdist
```

## (old) Manual install (Linux, MacOS)

Cloning:

    git clone https://gitlab.inria.fr/amibio/tree-diet.git
    cd tree-diet

Installing dependencies (pybind11, numpy, pytest) and setting up the environment:

    python3 -m pip install -r requirements.txt
    . ./setenv.sh 

Then, if you are on linux: 

    make

If you are on mac:

    make macos

Finally, in either case:

    make check

to launch the tests. If they all pass, you are good to go.

## Source code documentation

A Sphinx-based source code documentation, with minimal execution examples, is
available at: https://bmarchand-perso.gitlab.io/tree-diet/.
