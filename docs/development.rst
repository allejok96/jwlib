===========
Development
===========

This page is mostly relevant if you intend to fix a bug or add a feature to jwlib.

jwlib uses `hatch`_ as its build system. It's not really a requirement for development,
but it can be good for running tests before making a pull request.

Here's an example on how you might set it up:

.. code-block:: console

    # Install hatch using pipx
    pip install --user pipx
    pipx ensurepath
    pipx install hatch

    # Download the jwlib source code
    git clone git://github.com/allejok96/jwlib
    cd jwlib

    # Do a test run to initialize the environment
    hatch run test

    # List a few other handy commands
    hatch run help

If you're using an IDE like PyCharm probably want to configure it to use the virtual environment that hatch just
created. You can find it somewhere in the `hatch data directory`_.  On Linux this will be something like
``~/.local/share/hatch/env/virtual/jwlib/3onyU7Va/jwlib``.

If you want to run a python file in the virtual environment you'd call ``hatch run python somefile.py``.

Once you've made your changes, you should test everything with ``hatch run test``.
This will probably fail because jwlib uses `pytest-recording`_ to record all interactions with the server and
store them offline for testing. If the code tries to make a request that has not been recorded, the test will fail.
In that case you must update the cassettes using ``hatch run record`` (this might take a while).

.. _hatch: https://hatch.pypa.io/dev/install
.. _hatch data directory: https://hatch.pypa.io/dev/config/hatch/#data
.. _pytest-recording: https://github.com/kiwicom/pytest-recording