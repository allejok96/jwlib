===========
Development
===========

This section is mostly relevant if you intend to fix a bug or add a feature to jwlib.

Here's an example on how you might set up your environment:

.. code-block:: console

    # Download the jwlib source code
    git clone git://github.com/allejok96/jwlib
    cd jwlib

    # Create a virtual environment
    python -m venv venv
    . venv/bin/activate

    # Install jwlib in editable mode with development dependencies
    pip install -e ".[dev,docs]"

    # Run the tests
    make test

Once you've made your changes, you should test everything with ``make test``.
This will probably fail because jwlib uses `pytest-recording`_ to record all interactions with the server and
store them offline for testing. If the code tries to make a request that has not been recorded, the test will fail.
In that case you must update the cassettes using ``make record`` (this might take a while).

.. _pytest-recording: https://github.com/kiwicom/pytest-recording