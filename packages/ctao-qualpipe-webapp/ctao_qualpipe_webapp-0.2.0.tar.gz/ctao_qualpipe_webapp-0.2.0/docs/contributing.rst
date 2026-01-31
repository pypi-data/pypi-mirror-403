👩‍💻 Contributing
=====================

If you want to contribute in developing the code, be aware that we are
using ``pre-commit``, ``code-spell`` and ``ruff`` tools for automatic
adherence to the code style. To enforce running these tools whenever you
make a commit, setup the
`pre-commit hook <https://pre-commit.com/>`__ executing:

::

   pre-commit install

The ``pre-commit hook`` will then execute the tools with the same
settings as when a merge request is checked on GitLab, and if any
problems are reported the commit will be rejected. You then have to fix
the reported issues before tying to commit again.

.. _page_facing_up-license:

📄 License
----------

This project is licensed under the BSD 3-Clause License. See the LICENSE
file for details.
