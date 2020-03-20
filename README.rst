
Pyflow-Viz
==========

Pyflow is a light weight library that lets the user construct a memory efficient directed acyclic computation graph (DAG) that evaluates lazily. It can cache intermediate results, and only computes the parts of the graph that has data dependency. 

Install
-------



Getting started
---------------

Let's construct a simple computation graph: (Note the similarity of API to that of Keras functional API!)

.. code:: python

	from pyflow import GraphBuilder

	def adding(a, b):
		return a + b

	G = GraphBuilder()
	a1 = G.add(adding)(2, 2)  # you add methods with `add` instance method.
	a2 = G.add(adding)(3, a1)
	a3 = G.add(adding)(a1, a2)

At this point, no evaluation has occurred. Also, the outputs ``a1``, ``a2``, and ``a3`` are ``DataNode`` objects (well, more precisely, weak references to the ``DataNode`` objects, but more on this later!)
You can kick off the evaluation by invoking ``get`` method from any of the output objects:

.. code:: python

	print(a3.get())  # 11

You can also easily visualize the DAG using ``view`` method:

.. code:: python

	G.view()

.. figure:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/simple_dag.png