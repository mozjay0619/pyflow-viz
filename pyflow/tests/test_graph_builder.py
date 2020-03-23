import pytest

from pyflow import GraphBuilder

def adding(a, b):
    return a + b

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
    
    