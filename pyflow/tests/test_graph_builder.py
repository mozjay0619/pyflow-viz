import pytest

from pyflow import GraphBuilder

def adding(a, b):
    return a + b

def test_simple_graph():

	G = GraphBuilder()
	x = G.add(adding)(2, 2)
	assert(x.get() == 4)
