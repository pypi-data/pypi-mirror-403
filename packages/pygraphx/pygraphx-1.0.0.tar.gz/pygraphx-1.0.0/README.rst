pygraphx
=========

pygraphx is a Python package for the creation, manipulation,
and study of the structure, dynamics, and functions of complex networks.

- **Website (including documentation):** https://networkx.org
- **Mailing list:** https://groups.google.com/forum/#!forum/networkx-discuss
- **Source:** https://github.com/brucecarroll01/pygraphx
- **Bug reports:** https://github.com/brucecarroll01/pygraphx/issues
- **Tutorial:** https://networkx.org/documentation/latest/tutorial.html
- **GitHub Discussions:** https://github.com/brucecarroll01/pygraphx/discussions

Simple example
--------------

Find the shortest path between two nodes in an undirected graph:

.. code:: python

   >>> import pygraphx as nx
   >>> G = nx.Graph()
   >>> G.add_edge('A', 'B', weight=4)
   >>> G.add_edge('B', 'D', weight=2)
   >>> G.add_edge('A', 'C', weight=3)
   >>> G.add_edge('C', 'D', weight=4)
   >>> nx.shortest_path(G, 'A', 'D', weight='weight')
   ['A', 'B', 'D']

Install
-------

Install the latest version of pygraphx::

   $ pip install pygraphx

Install with all optional dependencies::

   $ pip install pygraphx[all]

For additional details, please see `INSTALL.rst`.

Bugs
----

Please report any bugs that you find `here <https://github.com/brucecarroll01/pygraphx/issues>`_.
Or, even better, fork the repository on `GitHub <https://github.com/brucecarroll01/pygraphx>`_
and create a pull request (PR). We welcome all changes, big or small, and we
will help you make the PR if you are new to `git`

License
-------

Released under the 3-Clause BSD license (see `LICENSE.txt`)::

   Copyright (C) 2004-2021 pygraphx Developers
   Milton Kaufman <brucecarroll011@protonmail.com>
