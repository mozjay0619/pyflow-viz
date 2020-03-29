
Pyflow-Viz
==========

Pyflow is a light weight library that lets the user construct a memory efficient directed acyclic computation graph (DAG) that evaluates lazily. It can cache intermediate results, and only computes the parts of the graph that has data dependency. 

Install
-------

::

	pip install pyflow-viz

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

At this point, no evaluation has occurred. Also, the outputs ``a1``, ``a2``, and ``a3`` are ``DataNode`` objects (well, more precisely, weak references to the ``DataNode`` objects)
You can kick off the evaluation by invoking ``get`` method from any of the output objects:

.. code:: python

	print(a3.get())  # 11

You can also easily visualize the DAG using ``view`` method:

.. code:: python

	G.view()

.. figure:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/simpledag.png


A couple notes:

1. The API was inspired by that of the `Keras functional API <https://keras.io/getting-started/functional-api-guide/>`_
2. For demo, we are using a simple method of adding two integers, but the input method can be any python function, including instance methods, with arbitrary inputs such as numpy array, pandas dataframe or Spark dataframe.
3. Lastly, more often then not, you will execute the graph with ``run`` method instead of invoking ``get`` on the individual data nodes. ``run`` method will be discussed more in-depth once we understand how Pyflow manages computation and memory internally. For now, just note that you can kick off the graph this way as well, which is the preferred way:

.. code:: python

	G.run()  # will run all the operation nodes

You can also pass in data nodes to get the results back this way:

.. code:: python

	a1, a3 = G.run(a1, a3)  # will run all the operation nodes
	a1.get(), a3.get()

The difference between ``run()`` and ``run(a1, a3)`` will make more sense once we discuss the internal workings of Pyflow below. 


Multi-output methods
--------------------

What if we have a python function with multiple outputs? Due to dynamic nature of python, it is impossible to determine the number of outputs before the function is actually ran. In such a case, you need to specify the number of outputs by ``n_out`` argument:

.. code:: python

	from pyflow import GraphBuilder

	def adding(a, b):
		return a + b

	def multi_output_method(a, b):
		return a+1, b+1

	G = GraphBuilder()
	a1 = G.add(adding)(2, 2)
	a2, b2 = G.add(multi_output_method, n_out=2)(a1, 2)  # n_out argument!
	a3 = G.add(adding)(a2, 3)
	a4 = G.add(adding)(b2, a1)

	G.view()

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/multiout.png
   :width: 17pt


Visualizing data flow
---------------------

The ``view`` function actually has the ability to summarize the DAG by only showing the user the ``OperationNodes``, which it does by default. We can override this default setting by using the ``summary`` parameter of the function:

.. code:: python

	G.view(summary=False)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/summary_false.png
   :width: 17pt

With the summary functionality turned off, the complete DAG visualization will includes ``DataNodes`` as well as the ``OperationNodes``. 


Styling your DAG
----------------

Pyflow lets the user customize the DAG visuals to a certain degree, with more to come in the future. Let's take a look at some examples.

.. code:: python

	from pyflow import GraphBuilder

	def query_dataframe_A():
		return 1  # pretend this was a pandas or Spark dataframe!

	def query_dataframe_B():
		return 2

	def product_transform(inp):
		return inp*2

	def join_transform(inp1, inp2):
		return inp1 + inp2

	def split_transform(inp):
		return inp+1, inp+2

	G = GraphBuilder()
	df1 = G.add(query_dataframe_A)()
	df2 = G.add(query_dataframe_B)()
	new_df1 = G.add(product_transform)(df1)
	new_df2 = G.add(product_transform)(df2)
	dfa, dfb = G.add(split_transform, n_out=2)(new_df2)
	joined_df = G.add(join_transform)(new_df1, dfa)

	G.view()

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/queryA.png
   :width: 10pt

But since at a conceptual level, queries are similarly progenitors of new data, perhaps we want to put them side by side on top, and position is controlled by ``rank`` parameter. Also, since these are probably coming from some data storage, we might want to style their nodes accordingly, with different color.

.. code:: python

	G = GraphBuilder()
	df1 = G.add(query_dataframe_A, rank=0, shape='cylinder', color='lightblue')()
	df2 = G.add(query_dataframe_B, rank=0, shape='cylinder', color='lightblue')()
	new_df1 = G.add(product_transform)(df1)
	new_df2 = G.add(product_transform)(df2)
	dfa, dfb = G.add(split_transform, n_out=2)(new_df2)
	joined_df = G.add(join_transform)(new_df1, dfa)

	G.view()

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/queryB.png
   :width: 10pt


But then we might want to make the DAG a little shorter, especially if we are to add more and more intermediate steps. We can control more detailed aesthetics with ``graph_attributes``:

.. code:: python

	graph_attributes = {'graph_ranksep': 0.25}

	G.view(graph_attributes=graph_attributes)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/shorterGraph.png
   :width: 10pt



No output methods
-----------------

Often when we are processing data, we will end up doing something with that data, whether it is to upload it somewhere, save it somewhere, or use pass it to a model, etc. In those cases, we do not expect any return data. 

.. code:: python
	
	# this method does not have return statement
	def save_data(data):

		# save the data somewhere
		# no return statement needed
		pass

Pyflow will create graph accordingly, such that the outputless operation node is a leaf node. 

.. code:: python

	from pyflow import GraphBuilder

	def query_dataframe_A():
		return 1  # pretend this was a pandas or Spark dataframe!

	def query_dataframe_B():
		return 2

	def product_transform(inp):
		return inp*2

	def join_transform(inp1, inp2):
		return inp1 + inp2

	def split_transform(inp):
		return inp+1, inp+2

	def save_data(data):
		# save the data somewhere
		# no return statement needed
		pass

	G = GraphBuilder()
	df1 = G.add(query_dataframe_A, rank=0, shape='cylinder', color='lightblue')()
	df2 = G.add(query_dataframe_B, rank=0, shape='cylinder', color='lightblue')()
	new_df1 = G.add(product_transform)(df1)
	new_df2 = G.add(product_transform)(df2)
	dfa, dfb = G.add(split_transform, n_out=2)(new_df2)
	joined_df = G.add(join_transform)(new_df1, dfa)
	G.add(save_data)(dfb)
	G.add(save_data)(joined_df)

	graph_attributes = {'graph_ranksep': 0.25}
	G.view(summary=False, graph_attributes=graph_attributes)


.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/realisticGraph.png
   :width: 10pt


This is a more realistic shape of the DAG in the actual use case of data preprocessing. Also, this is why ``run`` method makes more sense to use then ``get`` method. 

Saving your DAG image
---------------------

You can easily save your DAG image by invoking ``save_view`` method, which returns the file path of the saved image:

.. code:: python

	G.save_view()

The ``save_view`` method also has ``summary`` boolean parameter. You can also set the file name and file path by passing in ``dirpath`` and ``filename`` parameter. They default to current working directory and "digraph" respectively. You can also set the file format as png or pdf by setting ``fileformat`` parameter. The default is png. 


Computation and memory efficiency of Pyflow
-------------------------------------------

When you invoke ``get`` method, pyflow will only then evaluate, and it will evaluate only the parts of the graph that is needed to be evaluated. Also, as soon as an intermediate result has no dependency, it will automatically release the memory back to the operating system. Let's take a tour of the computation process to better understand this mechanism by turning on ``verbose`` parameter. 

.. code:: python

	from pyflow import GraphBuilder

	def adding(a, b):
		return a + b

	def multi_output_method(a, b):
		return a+1, b+1

	G = GraphBuilder(verbose=True)  # set verbose to True
	a1 = G.add(adding)(1, 2)
	a2, a3 = G.add(return2, n_out=2)(a1, 3)
	a4 = G.add(adding)(a1, 5)
	a5 = G.add(adding)(a4, a3)

	a5.get()

With ``verbose=True``, along with the final output, pyflow will also produce the following standard output:

::

	computing for data_12
	adding_11 activated!
	adding_8 activated!
	adding_0 activated!
	return2_4 activated!
	computing for data_10
	computing for data_3
	running adding_0
	adding_0 deactivated!
	running adding_8
	data_3 still needed at return2_4
	adding_8 deactivated!
	computing for data_7
	running return2_4
	data_3 released!
	return2_4 deactivated!
	running adding_11
	data_10 released!
	data_7 released!
	adding_11 deactivated!

Let's take the tour of this process by looking at the graph. Notice that in verbose mode, the graph will actually print out the uid's of the nodes not just their aliases (more on setting alias later!)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/verbose_.png
   :width: 10pt

As pyflow tries to compute ``data_12``, it will first activate all the ``OperationNodes`` that is needed for the computation, in our case, those are ``adding_11``, ``adding_8``, ``adding_0``, ``return2_4``. It will then follow the lineage of the graph to work on intermediate results needed to proceed down the graph. Notice that as the computation proceeds, the ``OperationNodes`` that were activated are deactivated. When it gets to ``data_3``, notice that it is needed at both ``adding_8`` and ``return2_4``. Thus, once it completes ``adding_8``, it cannot yet release the memory from ``data_3``: ``data_3 still needed at return2_4``. But as soon as ``return2_4`` is ran, it releases ``data_3`` from memory, as it is not needed anymore: ``data_3 released!``. The ``DataNodes`` with raw inputs such as integers are not released since there is no way for the graph to reconstruct them. 

By the same token, if you were to run the graph from middle, say, at ``a4``:

.. code:: python

	a4.get()

You will see:

::

	computing for data_10
	adding_8 activated!
	adding_0 activated!
	computing for data_3
	running adding_0
	adding_0 deactivated!
	running adding_8
	data_3 released!
	adding_8 deactivated!

In this case, since ``return2_4`` is not activated, the ``data_3`` does not consider its presence in deciding release of memory. 

Lastly, you have the option of either persisting all of the intermediate results, or persisting part of the intermediate results.

To persist all intermediate results, use ``persist`` parameter at ``GraphBuilder`` level:

.. code:: python

	from pyflow import GraphBuilder

	G = GraphBuilder(persist=True)  # set persist to True

	a1 = G.add(adding)(1, 2)
	a2, a3 = G.add(return2, n_out=2)(a1, 3)
	a4 = G.add(adding)(a1, 5) 
	a5 = G.add(adding)(a4, a3)

	a5.get()

With persist enabled, after running ``a5.get()``, when you try to run ``a4.get()``, the graph will not recompute anything because ``a4`` node result will have been cached in memory. The persist is turned off by default, as it is assumed that the user of the pyflow will process large amounts of data. 

To persist parts of the data, you can specify the ``persist`` parameter at ``add`` level:

.. code:: python

	from pyflow import GraphBuilder
	
	G = GraphBuilder(persist=False)  # default value

	a1 = G.add(adding)(1, 2)
	a2, a3 = G.add(return2, n_out=2)(a1, 3)
	a4 = G.add(adding, persist=True)(a1, 5)  # persist here
	a5 = G.add(adding)(a4, a3)
	
	a5.get()

Then, when you run ``a4.get()`` it will not rerun the computation as ``a4`` result has been cached in memory although all other intermediate results will have been released.  



