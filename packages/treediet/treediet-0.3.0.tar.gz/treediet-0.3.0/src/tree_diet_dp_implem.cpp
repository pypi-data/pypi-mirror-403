#include <pybind11/stl.h>
#include <pybind11/pybind11.h>
#include <map>
#include <math.h>
#include <utility>
#include <functional>
#include <list>
#include <set>
#include <iostream>
#include <string>

#define GREEN 1
#define ORANGE 2
#define RED 3
#define DEBUG 1

using namespace std;
namespace py = pybind11;

// typedefs for convenience
typedef map<int, set<int>> adjacency;
typedef set<int> subset;
typedef map<int, set<int>> set_of_subsets;

void print_spaces(int depth)
{
    for (int i = 0; i < depth; i++)
    {
        cout << "    "; 
    }
}

void print_graph(adjacency adj, int size)
{
    for (int i = 0; i < size; i++)
    {
        for (auto j : adj[i])
        {
            cout << i << " " << j << endl;
        }
    }
}


struct bag
{
    list<int> vertices;
    int id_tag;   
 
    list<bag*> children;

    // constructor
    bag(list<int> &vertices, int id_tag) : vertices(vertices), id_tag(id_tag) { }

    // adding children
    void add_child(bag* child) { children.push_back(child); }
};

typedef pair<int, map<int,int>> table_entry;

bool not_enough(bag i, map<int, int> f, int target_width)
{
    int size = (int) i.vertices.size();

    int int_num_suppr = 0;

    for (auto const & u : i.vertices)
    {
        if (f[u] > 1) int_num_suppr += 1;
    }

    if (int_num_suppr < size - target_width - 1) 
    {
        return true;
    }
    else
    {
        return false;
    }
}

struct enum_node
{
    int vertex;
    struct enum_node *child;
    list<int> possibilities;    
    bool is_set_child;   
 
    enum_node(int vertex, list<int> &possibilities, bool is_set_child) 
                : vertex(vertex), possibilities(possibilities), is_set_child(is_set_child) 
                { } 

    void setChild(enum_node * child_) 
    { 
        child = child_;
        is_set_child = true;
    } 
};

void dfs_fill(enum_node node, 
              map<int,int> partial_f, 
              list<map<int,int>> &global_list)
{
    for (auto const & p : node.possibilities)
    {
        partial_f[node.vertex] = p;

        if (!node.is_set_child) 
        {
            global_list.push_back(partial_f);
        }
        else
        {
            dfs_fill(*node.child, partial_f, global_list);
        }
    }
}


list<map<int,int>> orange_maps(bag &i, const map<int, int> &f)
{

    list<map<int,int>> return_list;

    list<int> orange_vertices;

    for (auto const & u : i.vertices)
    {
        bool is_present_children = false;
        for (auto const & j : i.children)
        {
            if (find((*j).vertices.begin(), (*j).vertices.end(), u)!=(*j).vertices.end())
            {
                is_present_children = true;
            }
        }

//        cerr << "10";
//        cerr.flush();
        if ((f.at(u)==ORANGE) && is_present_children) orange_vertices.push_back(u);
    }
    
    if (orange_vertices.size()==0)
    {
        map<int,int> empty_map;
        return_list.push_back(empty_map);
        return return_list;
    }

    vector<enum_node> nodes;

    for (auto const & u : orange_vertices)
    {
        list<int> possibilities;

        for (auto const & j : i.children)
        {
            if (find((*j).vertices.begin(), (*j).vertices.end(), u)!=(*j).vertices.end())
            {
                possibilities.push_back((*j).id_tag);
            }
        }
        
        nodes.push_back(enum_node(u, possibilities, false));
    }

    if (nodes.size() > 0)
    {
        for (size_t k = 0; k < nodes.size()-1; k++)
        {
            nodes[k].setChild(&nodes[k+1]);
        }

        map<int, int> partial_m;

        dfs_fill(nodes[0], partial_m, return_list);
    }

    return return_list;
}



list<map<int,int>> compatible(const map<int, int> &f, 
                              const map<int, int> &m, 
                              bag &i,
                              bag &j,
                              int index_j)
{

    vector<enum_node> nodes;

    for (auto const & u : j.vertices)
    {
        list<int> possibilities;

        if (f.find(u) == f.end()) 
        {
            possibilities.push_back(GREEN); // green
            possibilities.push_back(ORANGE); // orange
           // possibilities.push_back(RED); // red
        }
        else
        {
//            cerr << "0";
//            cerr.flush();
            switch (f.at(u))
            {
                case RED :
                {
                    possibilities.push_back(RED);
                    break;
                } 
                case GREEN :
                {
                    possibilities.push_back(GREEN); // green
                    possibilities.push_back(RED); // red
                    break;
                }
                case ORANGE :
                {
//                    cerr << "1";
//                    cerr <<"m:{ ";
//                    for (map<int,int>::const_iterator iter=m.begin(); iter!= m.end();iter++)
//                    {
//                       cerr << iter->first; 
//                       cerr << ":" << iter->second <<","; 
//                    }
//                    cerr << "}";
//                    cerr.flush();
                    if (m.at(u)==j.id_tag)
                    {
                        possibilities.push_back(GREEN); // green
                        possibilities.push_back(ORANGE); // orange
                    }
                    else
                    {
                        possibilities.push_back(RED); // red
                    }
                    break;
                }                     
            }
        }

        nodes.push_back(enum_node(u, possibilities, false));
    }

    for (size_t k = 0; k < j.vertices.size()-1; k++)
    {
        nodes[k].setChild(&nodes[k+1]);
    }
    
    list<map<int,int>> return_list;
    map<int, int> partial_f;

    dfs_fill(nodes[0], partial_f, return_list);

//    cout << "parent vertices : ";
//    for (auto const& u : i.vertices)
//    {
//        cout << u << " ("<<f[u]<<")";
//    }
//    cout << endl;
//    
//    cout << "child vertices : ";
//    for (auto const& u : j.vertices)
//    {
//        cout << u << " ";
//    }
//    cout << endl;
//
//    for (auto const& fj : return_list)
//    {
//         map<int,int> fmap = fj;
//        for (auto const & u : j.vertices)
//        {
//            cout << u << ": " << fmap[u] << " | ";
//        }
//        cout << endl;
//    }
//
//    if (i.children.size()>1)
//    {
//        getchar();
//    }

    return return_list;    
}

int count_weight(const map<int, int> &f, 
                                 const map<int, int> &fj, 
                                 const adjacency &adj, 
                                 const vector<pair<int,int>> &must_have_edges)
{
    
  
//    cout << "BEGIN f " << endl;
//    for(std::map<int,int>::const_iterator iter = f.begin(); iter != f.end(); ++iter)
//    {
//        cout << iter->first << ": " << iter->second << ", ";
//    }
//    cout << "END f " << endl;
//    
//    cout << "BEGIN fj " << endl;
//    for(std::map<int,int>::const_iterator iter = fj.begin(); iter != fj.end(); ++iter)
//    {
//        cout << iter->first << ": " << iter->second << ", ";
//    }
//    cout << "END fj " << endl;

    vector<pair<int,int>> edge_list;

    for(std::map<int,int>::const_iterator iter = fj.begin(); iter != fj.end(); ++iter)
    {
        int vertex = iter->first;
        int color = iter->second;

        for (auto const & v : adj.at(vertex))
        {
            if (fj.find(v)!=fj.end())
            {
//                cerr << "2";
//                cerr.flush();
                const int & color_v = fj.at(v);

                if ((color==GREEN) && (color_v==GREEN))
                {
                    if (vertex < v) edge_list.push_back(make_pair(vertex,v));
                }
            }
        }
    }
    
    int weight = 0; 

//    cout << "looping over child-green-green edges" << endl;

    for (size_t index = 0; index < edge_list.size(); index++)
    {
        int u = min(edge_list[index].first, edge_list[index].second);
        int v = max(edge_list[index].first, edge_list[index].second);

//        cout << "u " << u << " v " << v << endl;

        bool gg_in_parent = false;

        if ((f.find(u)!=f.end()) && (f.find(v)!=f.end()))
        {
//            cerr << "3";
//            cerr.flush();
            int color_u = f.at(u);        
            int color_v = f.at(v);        

            if ((color_u==1) && (color_v==1))
            {
                gg_in_parent = true;
            }
        }

        if (!gg_in_parent)
        {
            bool found_edge = false;
            for (size_t index = 0; index < must_have_edges.size(); index++)
            {
                pair<int, int> mh_edge = must_have_edges[index];

                if (u==mh_edge.first && v==mh_edge.second)
                {
                    found_edge = true;
                    break;
                }
                if (u==mh_edge.second && v==mh_edge.first)
                {
                    found_edge = true;
                    break;
                }
                
            }
            if (found_edge)
            {
//                cout << "counting " << u << " " << v << " 10000" << endl;
                weight += 10000; 
            }   
            else
            {
//                cout << "counting " << u << " " << v << " 1" << endl;
                weight += 1;
            }
        }
    }
//    getchar();
    return weight;
    
}

list<pair<int,int>> count_set(map<int, int> f, map<int, int> fj, adjacency &adj)
{
    vector<pair<int,int>> edge_list;

    for(std::map<int,int>::iterator iter = fj.begin(); iter != fj.end(); ++iter)
    {
        int vertex = iter->first;
        int color = iter->second;

        for (auto const & v : adj[vertex])
        {
            if (color==1 && fj[v]==1)
            {
                if (vertex < v) edge_list.push_back(make_pair(vertex,v));
            }
        }
    }

    list<pair<int,int>> return_set;

    for (size_t index = 0; index < edge_list.size(); index++)
    {
        int u = edge_list[index].first;
        int v = edge_list[index].second;
        
        if (f[u]==1 and f[v]==1)
        {
            continue;
        }   
        return_set.push_back(make_pair(u,v));
    }

    return return_set;
}

struct cmpBags
{
    bool operator()(const bag& i, const bag& j) const
    {
        return i.id_tag < j.id_tag;
    }
};

struct cmpColoredBags 
{
    bool operator()(const table_entry& i_f, const table_entry& j_h) const
    {
        if (i_f.first != j_h.first)
        {
            return i_f.first < j_h.first;
        }
//        // Now we now they have the same composition

        vector<int> vertices;
        map<int,int> f = i_f.second;
        map<int,int> h = j_h.second;
        for(std::map<int,int>::iterator iter = f.begin(); iter != f.end(); ++iter)
        {
            vertices.push_back(iter->first);
        }

        for (size_t index = 0; index < vertices.size(); index++)
        {
            int c1 = f[vertices[index]];
            int c2 = h[vertices[index]];
    
            if (c1!=c2)
            {
                return (c1 < c2);
            }
        }
        return 0;
            
//        sort(vertices.begin(), vertices.end());
//        int hash_i_f = 0;
//        int hash_j_h = 0;
//        for (size_t index = 0; index < vertices.size(); index++)
//        {
//            hash_i_f += f[vertices[index]]*pow(4,index);
//            hash_j_h += h[vertices[index]]*pow(4,index);
//        }
//        return hash_i_f < hash_j_h; 
    }    
};

int optim_num_real_edges(bag &i,
                          const map<int, int> &f,
                          int target_width,
                          map<table_entry, int, cmpColoredBags> &c,
                          adjacency &adj,
                          const vector<pair<int,int>> &must_have_edges,
                          int depth)
{

//    print_spaces(depth);
//    cout <<"bag " << i.id_tag << "..";
//    print_spaces(depth);
//    for (auto const & u : i.vertices)
//    {
//        cout << u << " : " << f.at(u) << " ";
//    }
//    cout << endl;
//    cout << "children: ";
//    for (auto const & j : i.children)
//    {
//        cout << (*j).id_tag << " ";
//    }
//    cout << endl;
    int infty = pow(10, 9);

    table_entry i_f = make_pair(i.id_tag, f);

    if (c.find(i_f) != c.end()) 
    {
//        print_spaces(depth);
//        cout << "OUT 1" << endl;
//        cerr << "4";
//        cerr.flush();
        return c.at(i_f);
    }

    // START COMPUTE

    if (not_enough(i, f, target_width))
    {
        c[i_f] = - infty;
//        print_spaces(depth);
//        cout << "OUT 2: not enough" << endl;
//        cerr << "5";
//        cerr.flush();
        return c.at(i_f);
    } 
    
    if (i.children.size() == 0)
    {
        c[i_f] = 0;
//        print_spaces(depth);
//        cout << "OUT 3: leaf" << endl;
//        cerr << "6";
//        cerr.flush();
        return c.at(i_f);
    }

    int ans = - infty;
    
    list<map<int,int>> omaps = orange_maps(i,f);


    if (omaps.size()==0)
    {
        throw "omaps needs at least one element, even an empty one.";
    }

    for (auto const & m : omaps)
    {
        map<bag, int, cmpBags> ans_j;
            
        int index_j = 0;
        for (auto const & j : i.children)
        {
            int ansj = -infty;
 
            for (auto const & fj : compatible(f, m, i, *j, index_j))
            {
                int num = 0;
                num += optim_num_real_edges(*j, 
                                            fj, 
                                            target_width, 
                                            c, 
                                            adj, 
                                            must_have_edges,
                                            depth+1);

                num += count_weight(f, fj, adj, must_have_edges);
                 
                if (num > ansj)
                {   
                    ansj = num;
                }
            } 

            ans_j[*j] = ansj;
 
            index_j += 1;
        }

        int sum = 0;
        
        for (auto const & j : i.children) 
        {
//            cerr << "7";
//            cerr.flush();
            sum += ans_j.at(*j);
        }
        if (sum > ans)
        {
            ans = sum;
        }     

    }
    
    //END COMPUTE
    c[i_f] = ans;
//    print_spaces(depth);
//    cout << "OUT 4: end of function --> " << ans << endl;
//        cerr << "8";
//        cerr.flush();
    return c.at(i_f);
}

//   list of realized edges & vertex cololing in bags
pair<list<pair<int,int>>,map<int,map<int,int>>> optim_set_real_edges(bag i, 
                                         map<int,int> f, 
                                         adjacency adj,
                                         map<table_entry, int, cmpColoredBags> &c,
                                         const vector<pair<int,int>> &must_have_edges,
                                         bool debug)
{
    // base case: leaf
    if (i.children.size()==0)
    {
        list<pair<int,int>> empty_list;
        map<int, map<int,int>> empty_map;
        return make_pair(empty_list,empty_map);
    }
    map<int, map<int,int>> best_fj;
    map<int, int> best_valj;

    list<map<int,int>> omaps = orange_maps(i,f);

    if (omaps.size()==0)
    {
        throw "omaps needs at least one element, even an empty one.";
    }

    for (auto const & m : omaps)
    {
        int index_j = 0;
        for (auto const & j : i.children)
        {
            best_valj[(*j).id_tag] = - pow(10,9);
            
            for (auto const & fj : compatible(f, m, i, *j, index_j))
            {
                table_entry j_fj = make_pair((*j).id_tag,fj);

                int weight = count_weight(f, fj, adj, must_have_edges);

                if (c[j_fj]+ weight > best_valj[(*j).id_tag])
                {
                    best_valj[(*j).id_tag] = c[j_fj] + weight;
                    best_fj[(*j).id_tag] = fj;
                }
            }
            index_j += 1;
        }
        int val_m = 0;
    
        for (auto const & j : i.children) 
        {
            int weight = count_weight(f, best_fj[(*j).id_tag], adj, must_have_edges);
            table_entry j_fj = make_pair((*j).id_tag,best_fj[(*j).id_tag]);


            val_m += weight;
            val_m += c[j_fj];
        }
        table_entry i_f = make_pair(i.id_tag,f);

        if (val_m==c[i_f])
        {
            break;
        }
    } 
    
    list<pair<int,int>> full_count_set;
    map<int, map<int,int>> full_vertex_coloring;

    for (auto const & j : i.children)
    {
        map<int,int> local_vertex_coloring;

        //printing for log parsing afterwards
        if (debug)
        {
            cout << "BAG tag: " << (*j).id_tag << " ";
            cout << "BAG children: ";
            for (auto const& k : (*j).children)
            {
                cout << " " << (*k).id_tag << " ";
            }
            cout << endl;
            cout << "best coloration :" << endl;
        }
        for (auto const & u : (*j).vertices)
        {
            local_vertex_coloring[u] = best_fj[(*j).id_tag][u];
            if (debug) cout << "vertex " << u << " color " << best_fj[(*j).id_tag][u] << endl;
        }
        if (debug) cout << "END BAG" << endl;
        list<pair<int,int>> cnt_set = count_set(f, best_fj[(*j).id_tag], adj);

        full_count_set.insert(full_count_set.end(), cnt_set.begin(), cnt_set.end());
        full_vertex_coloring[(*j).id_tag] = local_vertex_coloring;   
 
        pair<list<pair<int,int>>, map<int, map<int,int>>> recursive_result_pair;

        recursive_result_pair = optim_set_real_edges(*j, best_fj[(*j).id_tag], adj, c, must_have_edges, debug);

        list<pair<int,int>> subtree_set = recursive_result_pair.first;
        map<int, map<int,int>> recursive_coloring = recursive_result_pair.second;

        full_count_set.insert(full_count_set.end(), subtree_set.begin(), subtree_set.end());
        for (auto const& [key, val] : recursive_coloring) full_vertex_coloring[key] = val;

    }

    return make_pair(full_count_set, full_vertex_coloring);
}

tuple<int, // num of preserved edges 
      list<pair<int,int>>, // list of preserved edges
      map<int, map<int,int>>> // bag coloration
      tree_diet(bag R, 
                adjacency adj, 
                int target_width,
                const vector<pair<int,int>> &must_have_edges,
                bool debug=true)
{

    map<int, int> empty_f;

    map<table_entry, int, cmpColoredBags> c; //table

    int OPT;
 
    if (R.vertices.size() > 0)
    {
        cerr << "The root is not empty !!!" << endl;
        cerr << "returning nothing." << endl;
//        return make_pair(OPT, real_edges);
        throw invalid_argument("The root of the tree decomposition must be empty.");
    }

    OPT = optim_num_real_edges(R, 
                               empty_f, 
                               target_width, 
                               c, 
                               adj,
                               must_have_edges, 
                               0);

    // At this point, the table has been filled, time to backtrack.

    pair<list<pair<int,int>>, map<int, map<int,int>>> result_pair;

    result_pair = optim_set_real_edges(R, empty_f, adj, c, must_have_edges, debug);
    
    return make_tuple(OPT, result_pair.first, result_pair.second);

}


PYBIND11_MODULE(tree_diet_cpp, m) {
    m.doc() = "tree diet cpp implementation"; // optional module docstring


    py::class_<bag>(m, "bag")
        .def(py::init<list<int>&, int>())
        .def("add_child", &bag::add_child)
        .def_readwrite("vertices", &bag::vertices)
        .def_readwrite("id_tag", &bag::id_tag)
        .def_readwrite("children", &bag::children);                

    m.def("print_graph", 
           &print_graph, 
           "A function which prints a graph");

    m.def("optim_num_real_edges", 
           &optim_num_real_edges, 
           "");
    
    m.def("tree_diet", 
           &tree_diet, 
           "",
           py::arg("bag"),
           py::arg("adjacency"),
           py::arg("width"),
           py::arg("must_have_edges"),
           py::arg("debug")=false);
}
