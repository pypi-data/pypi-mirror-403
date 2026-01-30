Installation
============

Requirements
------------

- Python 3.9 or higher
- analytic-continuation package
- FastAPI and uvicorn

Basic Installation
------------------

Install from PyPI::

    pip install analytic-continuation-server

With Domain Coloring Support
----------------------------

To enable domain coloring image generation::

    pip install analytic-continuation-server[domaincolor]

This installs py-domaincolor, numpy, and pillow for image generation.

Development Installation
------------------------

For development with testing and documentation tools::

    pip install analytic-continuation-server[dev]

Or install all optional dependencies::

    pip install analytic-continuation-server[all]

From Source
-----------

Clone the repository and install in editable mode::

    git clone https://github.com/example/analytic-continuation-server.git
    cd analytic-continuation-server
    pip install -e ".[dev]"

Using uv
--------

If you're using uv for package management::

    uv add analytic-continuation-server
    uv add analytic-continuation-server[domaincolor]  # with domain coloring

Verifying Installation
----------------------

After installation, verify by running::

    python -c "from analytic_continuation_server import app; print('OK')"

Or start the server::

    serve-analytic-continuation --help
