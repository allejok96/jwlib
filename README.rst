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

Video API
---------

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

Publication API
---------------

TODO

Search API
----------

TODO

Language API
------------

TODO

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

