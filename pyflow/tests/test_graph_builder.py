import pytest

from pyflow import GraphBuilder

def adding(a, b):
    return a + b

def multioutput_adding(a, b):
    return a + b, a

def adding_kwarg(a, b, c=4):
    
    return a + b + c

def test_simple_graph():
    """GraphBuilder instance taking raw inputs"""

    G = GraphBuilder(persist=False)
    x = G.add(adding)(2, 2)
    assert(x.get() == 4)
    
def test_complex_graph():
    """GraphBuilder instance taking DataNode objects as inputs"""
    
    G = GraphBuilder(persist=False)
    a1 = G.add(adding)(2, 2)
    a2 = G.add(adding)(2, 2)
    a3 = G.add(adding)(a1, a2)
    assert(a3.get() == 8)

def test_deactivation():
    """Test the OperationNode deactivation"""
    
    G = GraphBuilder(persist=False)
    a1 = G.add(adding)(2, 2)
    a2 = G.add(adding)(2, 2)
    a3 = G.add(adding)(a1, a2)
    a3.get()
    
    assert(~G.strong_ref_dict['adding_0'].is_active)
    assert(~G.strong_ref_dict['adding_4'].is_active)
    assert(~G.strong_ref_dict['adding_8'].is_active)
    
def test_memory_release():
    """Test that intermediate DataNode memories were released"""
    
    G = GraphBuilder(persist=False)
    a1 = G.add(adding)(2, 2)
    a2 = G.add(adding)(2, 2)
    a3 = G.add(adding)(a1, a2)
    a3.get()
    
    assert(~a1.has_value())
    assert(~a2.has_value())
    
def test_persistance():
    """Test persist parameter at GraphBuilder level"""
    
    G = GraphBuilder(persist=True)
    a1 = G.add(adding)(2, 2)
    a2 = G.add(adding)(2, 2)
    a3 = G.add(adding)(a1, a2)
    a3.get()
    
    assert(a1.has_value())
    assert(a2.has_value())
    
def test_manual_memory_release():
    """Test manual memory release"""
    
    G = GraphBuilder(persist=True)
    a1 = G.add(adding)(2, 2)
    a2 = G.add(adding)(2, 2)
    a3 = G.add(adding)(a1, a2)
    a3.get()
    
    a1.release_memory()
    assert(~a1.has_value())
    
    a2.release_memory()
    assert(~a2.has_value())
    
    a3.release_memory()
    assert(~a3.has_value())

def test_multioutput_method_support():
    """Test n_out > 1"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2, a3 = G.add(multioutput_adding, n_out=2)(a1, 3)

    assert(a2.get()==6)
    assert(a3.get()==3)

def test_node_removal():
    """Test remove method"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding)(a1, a2)

    G.remove()

    assert(a1() is not None)
    assert(a2() is not None)
    assert(a3() is None)

def test_node_removal():
    """Test remove method with arguments"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding)(a1, a2)

    G.remove(2)

    assert(a1() is not None)
    assert(a2() is None)
    assert(a3() is None)

def run_method():
    """Test run method"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2, a3 = G.add(multioutput_adding, n_out=2)(a1, 3)

    G.run()

    assert(~a1.has_value())
    assert(a2.has_value())
    assert(a3.has_value())

def test_multi_graph():
    """Test multiple graph paradigm"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding)(a1, a2)

    H = GraphBuilder()
    a4 = H.add(adding)(a3, 1)
    a5 = H.add(adding)(a4, 2)
    a6 = H.add(adding)(a4, a5)

    assert(a6.get() == 20)

def test_multi_graph_with_persist():
    """Test the persistence of prior graph persisted node"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding, persist=True)(a1, a2)

    H = GraphBuilder()
    a4 = H.add(adding)(a3, 1)
    a5 = H.add(adding)(a4, 2)
    a6 = H.add(adding)(a4, a5)

    a6.get()

    assert(~a1.has_value())
    assert(~a2.has_value())
    assert(a3.has_value())

    assert(~a4.has_value())
    assert(~a5.has_value())
    assert(a6.has_value())
    
def test_default_kwargs():
    """Test default keyword arguments"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding_kwarg)(a1, a2)

    assert(a3.get() == 12)
    
def test_kwargs_arguments():
    """Test passing in keyword arguments"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding_kwarg)(a=a1, b=a2, c=10)

    assert(a3.get() == 18)
    
def test_kwargs_None_arguments():
    """Test None keyword argument input"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding_kwarg)(a=a1, b=a2, c=None)

    assert(a3.get() == 8)
    
def test_args_None_arguments():
    """Test None positional argument input"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding_kwarg)(a1, a2, None)

    assert(a3.get() == 8)
    
def test_kwargs_None_arguments_multi_graph():
    """Test None keyword/positional argument input in multiple graph paradigm"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding_kwarg)(a=a1, b=a2, c=None)

    H = GraphBuilder()
    a4 = H.add(adding)(a3, 1)
    a5 = H.add(adding)(a4, 2)
    a6 = G.add(adding_kwarg)(a4, a5, None)

    assert(a6.get() == 20)
    
def test_kwargs_None_arguments_multi_graph_with_persist():
    """Test None keyword argument input in multiple graph paradigm with persist"""

    G = GraphBuilder()
    a1 = G.add(adding)(1, 2)
    a2 = G.add(adding)(a1, 2)
    a3 = G.add(adding_kwarg, persist=True)(a=a1, b=a2, c=None)

    H = GraphBuilder()
    a4 = H.add(adding)(a3, 1)
    a5 = H.add(adding)(a4, 2)
    a6 = H.add(adding)(a4, a5)

    a6.get()

    assert(~a1.has_value())
    assert(~a2.has_value())
    assert(a3.has_value())

    assert(~a4.has_value())
    assert(~a5.has_value())
    assert(a6.has_value())

    assert(a6.get() == 20)
    