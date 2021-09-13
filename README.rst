.. -*- mode: rst -*-

|CICD| |VERSION| |LICENCE| |PythonVersion|

.. |CICD| image:: https://img.shields.io/circleci/build/github/mozjay0619/pyflow-viz?label=circleci&token=93f5878e444e751d779f2954eb5fce9bc9ab5b3e
	:alt: CircleCI
.. |LICENCE| image:: https://img.shields.io/pypi/l/pyflow-viz
	:alt: PyPI - License
.. |VERSION| image:: https://img.shields.io/pypi/v/pyflow-viz?color=sucess&label=pypi%20version
	:alt: PyPI
.. |PythonVersion| image:: https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-blue
.. _PythonVersion: https://img.shields.io/badge/python-3.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-blue





Pyflow
======

Pyflow is a light weight library that lets the user construct a directed acyclic computation graph (DAG) that evaluates lazily. It can cache intermediate results, only compute the parts of the graph that has data dependency, and immediately release memory of data whose dependecy is no longer required. Pyflow is simple and light, built purely on Python, using the weak references for memory management and doubly linked list for DAG construction. 

Unlike computation graph based engines such as Dask or PySpark, Pyflow is not meant to be a parallel data processor, or to change the way computation resources are used. Instead, it is meant to be a light weight tool for code organization in the form of DAG and for graph visualization that can be used on top of Dask or PySpark. 

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

At this point, no evaluation has occurred. The outputs ``a1``, ``a2``, and ``a3`` are ``DataNode`` objects. The methods that we just added are ``OperationNode`` objects of the DAG.

You can easily visualize the resulting DAG using ``view`` method:

.. code:: python

	G.view()

.. figure:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/simple_dag.png

The default setting of the ``view`` method will only visualize the operation nodes. But ``view`` can do much more, as we will learn shortly.

You can execute the computation graph by invoking the ``run`` method:

.. code:: python

	G.run()  # will run all the operation nodes

You can pass in data nodes to get the desired results back this way:

.. code:: python

	a1_result, a3_result = G.run(a1, a3)  # will run all the operation nodes, and return the result data values of a1, a3

But what if you don't want to run every method in the DAG? There is ``run_only`` method for that, which we will learn shortly.

A couple notes:

1. The API was inspired by that of the `Keras functional API <https://keras.io/getting-started/functional-api-guide/>`_
2. For demo, we are using a simple method of adding two integers, but the input method can be any python function, including instance methods, with arbitrary inputs such as numpy array, pandas dataframe or Spark dataframe.

Multi-output methods
--------------------

What if we have a python function with multiple outputs? Due to dynamic nature of python, it is impossible to determine the number of outputs before the function is actually ran. In such a case, you **must** specify the number of outputs by ``n_out`` argument. Otherwise, Pyflow will deem the output to be a single output whose value is a list of multiple elements. Here is an example of how to do use ``n_out`` parameter to create multiple child output nodes: 

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

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/multi_output.png


Visualizing data flow
---------------------

The ``view`` function actually has the ability to summarize the DAG by only showing the user the ``OperationNodes``, which it does by default. We can override this default setting by using the ``summary`` parameter of the function:

.. code:: python

	G.view(summary=False)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/summary_false.png

With the summary functionality turned off, the complete DAG visualization will includes ``DataNodes`` as well as the ``OperationNodes``. You may be wondering what the extra records with ``(1, )`` written inside are. They signal the data persistence. We will discuss what this is, and how this works, in greater detail later. 

But that graph image is a little too big. We can shrink the gap between the nodes with handy the ``gap`` parameter:

.. code:: python

	G.view(summary=False, gap=0.2)  # the default value is 0.415

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/gapped_graph.png

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

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/queryingA.png

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

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/queryingB.png


But then we might want to make the DAG a little shorter, especially if we are to add more and more intermediate steps. We can control more detailed aesthetics with ``graph_attributes`` (the ``gap`` is simply the short cut parameter for this!):

.. code:: python

	graph_attributes = {'graph_ranksep': 0.25}

	G.view(graph_attributes=graph_attributes)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/shortGraph.png

You can take a look and play around with the rest of the configurations: 

.. code:: python

	G.graph_attributes 

	# the default settings are found at:
	G.default_graph_attributes

	# 'data_node_fontsize': 10, 
	# 'data_node_shape': 'box',
	# 'data_node_color': None,
	# 'op_node_fontsize': 12,
	# 'op_node_shape': 'box',
	# 'op_node_color': 'white',
	# 'graph_ranksep': 0.475,
	# 'graph_node_fontsize': 12.85,
	# 'graph_node_shape': 'box3d',
	# 'graph_node_color': 'white',
	# 'graph_node_shapesize': 0.574,
	# 'persist_record_shape': True



Finally, you can set the alias of the nodes by passing in ``method_alias`` and/or ``output_alias`` in the ``add`` method. The ``method_alias`` will set the alias of the operation node being added, and ``output_alias`` will set the alias of the child data node of that operation node. 

.. code:: python

	G = GraphBuilder()
	dfa = G.add(query_dataframe_A, rank=0, shape='cylinder', color='lightblue', output_alias='df_A')()
	dfb = G.add(query_dataframe_B, rank=0, shape='cylinder', color='lightblue', output_alias='df_B')()
	dfa1 = G.add(product_transform)(dfa)
	dfb1 = G.add(product_transform)(dfb)
	# note the list of alias for n_out = 2
	dfa, dfb = G.add(split_transform, n_out=2, output_alias=['first_out', 'second_out'])(dfa1)
	joined_df = G.add(join_transform, output_alias='final_data')(dfb1, dfa)

	graph_attributes = {'graph_ranksep': 0.25}
	G.view(summary=False, graph_attributes=graph_attributes)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/aliasingGraph.png


The default alias for operation node is the String name of the method being passed in, and the default alias for data node is simply "data". We do not include the example of setting ``method_alias`` to discourage its use. Setting method alias different from the method name will make look up of graph node in the code base very difficult. 


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


.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/no_output_.png


This is a more realistic shape of the DAG in the actual use case of data preprocessing. 



Executing parts of graph
------------------------

The ``run`` method will execute all nodes in the graph, but what if you don't want to run every node in the graph to save yourself time? Let's look at an example:

.. code:: python

	from pyflow import GraphBuilder

	def query_dataA():
	    return 1
	def query_dataB():
	    return 2
	def query_dataC():
	    return 3
	def transform_dataA(a):
	    return a
	def transform_dataB(a):
	    return a
	def transform_dataC(a):
	    return a
	def join_dataAB(a, b):
	    return a + b
	def save_dataAB(ab):
	    pass
	def join_dataC(a, c):
	    return a + c

	G = GraphBuilder()    
	a = G.add(query_dataA, rank=0)()
	b = G.add(query_dataB, rank=0)()
	c = G.add(query_dataC, rank=0)()
	a = G.add(transform_dataA)(a)
	b = G.add(transform_dataB)(b)
	c = G.add(transform_dataC)(c)
	ab = G.add(join_dataAB)(a, b)
	G.add(save_dataAB)(ab)
	abc = G.add(join_dataC)(ab, c)

	G.view(gap=0.25)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/for_partial1.png

From the above graph, let's say you want to test the ``transform_dataA`` method. For this purpose, you only need to run ``query_dataA`` and ``transform_dataA``. In such a case, you can use the ``run_only`` method, instead of ``run`` method, which will execute every node in the graph:

.. code:: python

	a_result = G.run_only(a)  # 1

When you invoke the ``run_only`` method, Pyflow will only execute parts of the graph that has the data dependency to the asked node. 

This time, let's say you are testing the ``save_dataAB`` method. But this node does not have data node that we can use to pass into the ``run_only`` method. That's why you can also pass in the string of the node names into the ``run_only`` method:

.. code:: python

	a_result = G.run_only(a, 'save_dataAB') 

In the above code, only the result for ``a`` node is returned because ``save_dataAB`` does not have a return statement. 


Visualizing computation dependency
----------------------------------

Pyflow will only execute parts of the graph that has data dependency. We can visualize this dependency with ``view_dependency`` method. We will use the same graph from the previous example:

.. code:: python

	G.view_dependency('save_dataAB') 

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/dep.png

You can pass in several arguments, just as you can with ``run_only`` method for execution:

.. code:: python

	G.view_dependency('save_dataAB', c) 

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/dep2.png

This method also supports other parameters of ``view`` method:

.. code:: python

	G.view_dependency('save_dataAB', c, summary=False, gap=0.2) 

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/dep3.png


Grafting graphs together
------------------------

When the computation graph becomes too big, the size of the visualized graph can actually end up becoming a hinderance to clean data flow documentation. Not only that, we could also benefit at the conceptual code organization level, if we had the ability to define multiple graphs and combine them together flexibly. I.e. we could treat a graph as if it was just another operation node. As of version ``0.7``, we can do this. Let's look at an example:

.. code:: python

	from pyflow import GraphBuilder

	def adding(a, b):
		return a+b

	G = GraphBuilder(alias='First Graph')  # notice alias at graph level!
	a1 = G.add(adding)(1, 2)
	a2 = G.add(adding)(a1, 2)
	a3 = G.add(adding, output_alias='leaving!')(a1, a2)

	G.view()

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/graft1.png

Let's look at the unsummarized version to take notice of the output_alias of the last data node:

.. code:: python
	
	# let's make it a little shorter with ranksep parameter we talked about earlier!
	G.view(summary=False, graph_attributes={'graph_ranksep': 0.3})

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/graft2.png

In the above code, we have created one graph. But we can create another graph, and graft the ``First Graph`` graph to the new graph:

.. code:: python

	H = GraphBuilder(alias='Second Graph')

	b1 = H.add(adding)(1, 3)
	b2 = H.add(adding)(b1, a3)
	b3 = H.add(adding)(b1, b2)

	H.view(summary=False)  # notice that the output_alias from previous graph is also preserved! 

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/graft3_.png

As you can see, the previous graph is now summarized into a box. You can combine as many graphs in this way as you want. Despite this visual effect, ``b3`` is now part of one single big combined computation graph. Therefore, calling ``b3.get()`` will trigger computations in nodes that belong to both ``G`` and ``H`` as long as they are needed. As far as computation is concerned, you just have one big graph. 


Saving your DAG image
---------------------

You can easily save your DAG image by invoking ``save_view`` method, which returns the file path of the saved image:

.. code:: python

	G.save_view()

The ``save_view`` method also has ``summary`` boolean parameter. You can also set the file name and file path by passing in ``dirpath`` and ``filename`` parameter. They default to current working directory and "digraph" respectively. You can also set the file format as png or pdf by setting ``fileformat`` parameter. The default is png. 

HTML documentation of DAG
-------------------------

With the visualization of the DAG, we can see the input-output relations among the functions, but it alone does not tell what each of the function does. But you can create a single HTML documentation that tells the complete semantic story of the DAG, using ``document`` method:

.. code:: python

	from pyflow import document

	document(G)  # or document(G, H, I) etc if you have more than one graph

Doing so will create a static HTML file that displays the DAG image as well as the docstrings of each of the functions that goes into the DAG on the right side, which you can scroll through.

.. code:: python

	from pyflow import GraphBuilder
	from pyflow import document

	def methodA(elem):
		"""Some descriptions of the methodA
		
		Parameter
		---------
		elem : int
		"""
		return elem

	def methodB(elem):
		"""Some descriptions of the methodB
		
		Parameter
		---------
		elem : int
		"""
		return elem

	def methodC(elem):
		"""Some descriptions of the methodC
		
		Parameter
		---------
		elem : int
		"""
		return elem

	G = GraphBuilder()
	a = G.add(methodA)(3)
	b = G.add(methodB)(a)
	c = G.add(methodC)(b)

	document(G)

This code will produce the following HTML file:

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/document.png


Memory persistance with Pyflow
------------------------------

You have the option of either persisting all of the intermediate results, or persisting part of the intermediate results.

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

At last, we can understand the difference between ``run()`` and ``run(a1, a3)``. Even if you don't persist anything, either at the graph level or the node level, by passing in the ``a1, a3``, the graph will automatically persist their data for you, and return the persisted data by internally invoking ``get()`` on the nodes ``a1, a3``. The rest of data nodes are subject to the same immediate memory release mechanism. 

In terms of the codes, these two are equivalent:

.. code:: python

	# run() with arguments:

	from pyflow import GraphBuilder
	
	G = GraphBuilder()
	a1 = G.add(adding)(1, 2)
	a2 = G.add(adding)(a1, 3)
	a3 = G.add(adding)(a2, a1)
	
	a1_val, a3_val = G.run(a1, a3)


	# run() without arguments:

	G = GraphBuilder()
	a1 = G.add(adding, persist=True)(1, 2)
	a2 = G.add(adding)(a1, 3)
	a3 = G.add(adding)(a2, a1)

	G.run()

	a1_val = a1.get()
	a3_val = a3.get()

Also, when you persist certain nodes, this persistence request will manifest in the graph by an empty record box:

.. code:: python

	from pyflow import GraphBuilder
	
	G = GraphBuilder()
	a1 = G.add(adding)(1, 2)
	a2 = G.add(adding)(a1, 3)
	a3 = G.add(adding)(a2, a1)

	G.view()

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/record1.png

The empty box signifies that the graph is requested to persist that data, but it does not yet hold that data because it has not yet been executed. But once you run the graph, the empty record slot will be filled by the dimensionality of the resulting data. Currently it supports PySpark dataframe, numpy array, and pandas dataframe. All other data will have a default dimension of ``(1, )``. 

.. code:: python

	G.run()

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/record2.png

Now, of course, it is not the method that is being persisted but the resulting data of that op node. You can see this when you visualize the DAG with ``summary=False``:

.. code:: python

	G.run(summary=False)

.. image:: https://github.com/mozjay0619/pyflow-viz/blob/master/media/record3.png

Some notes:

1. The op node with record box is a short hand way of conveying the message that the child data node of that op node will be persisted. 
2. The raw data are automatically persisted, which is why you see the dimensionality information in the record box. This is because the raw user data inputs cannot be recomputed from the graph alone. But this will not be visible when ``summary=True``, because the op node will only show the record box for persisted child data node, and user supplied inputs will always be parent data node. 
3. Although this is not made explicitly visible, the final leaf data node are always persisted when ``run`` method is invoked. But this will not be explicitly shown in the graph unless the user manually supplies ``persist`` flag at the ``add`` method invocation. 
4. Lastly, the ``persist`` flag is interoperable with Spark when PySpark dataframe is the data type. This means, when you persist the data using the DAG, if the underlying data is a PySpark dataframe, the Pyflow will persist the dataframe for you. However, unpersisting is not done by the Pyflow. If you want to unpersist a dataframe, do so manually. 


Computation and memory efficiency of Pyflow (OUTDATED)
------------------------------------------------------

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

On the other hand, ``run`` method will activate *all* operation nodes. This will make sure that even the operation nodes that do not have children are ran. However, the immediate memory release mechanism still applies to ``run`` method, unless otherwise specified. Refer below. 


