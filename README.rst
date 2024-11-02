=====
jwlib
=====


.. image:: https://img.shields.io/pypi/v/jwlib.svg
        :target: https://pypi.python.org/pypi/jwlib

.. image:: https://img.shields.io/travis/allejok96/jwlib.svg
        :target: https://travis-ci.com/allejok96/jwlib

.. image:: https://readthedocs.org/projects/jwlib/badge/?version=latest
        :target: https://jwlib.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


Python wrappers for a few JW.ORG_ APIs.

* Documentation: https://jwlib.readthedocs.io.


.. note::

    This is project is currently in beta stage.

------------
Installation
------------

This is the preferred method to install jwlib is using pip, as it will always install the most recent stable release.

.. code-block:: console

    $ pip install jwlib

-----
Usage
-----

.. code-block:: console

    TODO

------------
Development
------------

Download the source code from the `repo`_ or by using git.

.. code-block:: console

    $ git clone git://github.com/allejok96/jwlib

jwlib uses `hatch`_ as its build system and it comes with some nice features, but it's not strictly needed.
If you want to take a simpler approach using regular old `venv` you can stop right here.

Otherwise let's go ahead and install `hatch`_. Here's one way you can do it:

.. code-block:: console

    $ pip install --user pipx
    $ pipx ensurepath
    $ pipx install hatch

Then do a test run to download all dependencies and create a virtual environment.

.. code-block:: console

    $ cd jwlib
    $ hatch run test

If you're using an IDE like PyCharm probably want to configure it to use the virtual environment that hatch just
created. You can find it somewhere in the `hatch data directory`_.  On Linux this will be something like
`~/.local/share/hatch/env/virtual/jwlib/3onyU7Va/jwlib`.

Now if you want to run a command from the terminal in the virtual environment you have to do it like so:

.. code-block:: console

    $ hatch run python somefile.py

When you're satisfied with your changes, run the tests again.

.. code-block:: console

    $ hatch run test

This will probably fail because jwlib uses `pytest-recording`_ to record all interactions with the server and store
them offline for testing. If the code tries to make a request that has not been recorded, the test will fail.
In that case you must update the cassettes using the command below (this might take a while).

.. code-block:: console

    $ hatch run record

A list of other development related commands can be obtained with:

.. code-block:: console

    $ hatch run help

.. _JW.ORG: https://www.jw.org/
.. _hatch: https://hatch.pypa.io/dev/install
.. _repo: https://github.com/allejok96/jwlib
.. _hatch data directory: https://hatch.pypa.io/dev/config/hatch/#data
.. _pytest-recording: https://github.com/kiwicom/pytest-recording