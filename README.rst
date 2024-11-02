=====
jwlib
=====


.. image:: https://img.shields.io/pypi/v/jwlib.svg
        :target: https://pypi.python.org/pypi/jwlib

.. image:: https://github.com/allejok96/jwlib/actions/workflows/build.yml/badge.svg
        :target: https://github.com/allejok96/jwlib/actions/workflows/build.yml
        :alt: Build Status

.. image:: https://readthedocs.org/projects/jwlib/badge/?version=latest
        :target: https://jwlib.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status


Python wrappers for a few JW.ORG_ APIs.

.. note:: This is project is in beta stage.

Install the most recent release using pip.

.. code-block:: console

    pip install jwlib

Here's how you might use jwlib a script:

.. code-block:: python

    import jwlib.media as jw

    # Select Swedish
    session = jw.Session(language='Z')

    # Fetch the JW Broadcasting category
    studio_category = session.get_category('VODStudio')

    # Iterate through all its subcategories
    # (this will make more API requests as needed)
    for subcategory in studio_category.get_subcategories():

        # Print a category header
        print(f'\n{subcategory.name}\n-----------')

        # Print title and URL of all media items
        for media in subcategory.get_media():
            print(media.title)
            print(media.get_file().url)

See the documentation_ for more details.

------------
Development
------------

This is only if you intend to

jwlib uses `hatch`_ as its build system. You don't necessarily need it to work on jwlib. I use it mostly for the test
features and to build documentation.

Here's an example on how you might set up a development environment with hatch:

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

.. _JW.ORG: https://www.jw.org/
.. _documentation: https://jwlib.readthedocs.io/en/latest
.. _hatch: https://hatch.pypa.io/dev/install
.. _repo: https://github.com/allejok96/jwlib
.. _hatch data directory: https://hatch.pypa.io/dev/config/hatch/#data
.. _pytest-recording: https://github.com/kiwicom/pytest-recording