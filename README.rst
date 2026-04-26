=====
jwlib
=====

|build| |version| |docs|

Python wrappers for a few jw.org_ APIs.

Installation
============

.. code-block:: bash

    pip install jwlib

Usage
=====

Browsing JW Broadcasting
------------------------

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

See the media_ documentation for more details.

Searching at jw.org
-------------------

.. code-block:: python

    import jwlib.search as jw

    # Search for videos only
    page = jw.search('Caleb', filter_type=jw.FILTER_VIDEO, language='S')
    for result in page.results:
        print(result.title, result.url_jw)

    # Print page number info
    print(page.pagination_label)

    # Continue on next page
    if page.next:
        next_page = page.next.open()
        for result in next_page.results:
            print(result.title, result.url_jw)

See the search_ documentation for more details.

Downloading publications
------------------------

Alpha version, may be subject to change.

Listing languages
-----------------

Alpha version, may be subject to change.

Development
===========

An example on how to setup the dev environment:

.. code-block:: shell

    # Create a virtual Python environment
    python -m venv venv
    . venv/bin/activate

    # Install dependencies
    # -e keeps the installed jwlib in sync with your changes
    # [dev] installs the dependencies for testing
    # [dev,docs] if you also want to build documentation
    pip install -e '.[dev]'

    # Run the tests
    make test

    # Show more convenience functions
    make help


.. |build| image:: https://github.com/allejok96/jwlib/actions/workflows/build.yml/badge.svg
    :target: https://github.com/allejok96/jwlib/actions/workflows/build.yml
    :alt: Build Status
.. |version| image:: https://img.shields.io/pypi/v/jwlib.svg
    :target: https://pypi.python.org/pypi/jwlib
    :alt: Package Status
.. |docs| image:: https://readthedocs.org/projects/jwlib/badge/?version=latest
    :target: https://jwlib.readthedocs.io/en/latest/?version=latest
    :alt: Documentation Status

.. _jw.org: https://www.jw.org/
.. _media: https://jwlib.readthedocs.io/en/latest/jwlib.media.html
.. _search: https://jwlib.readthedocs.io/en/latest/jwlib.search.html
