🧪 Tests
============================

Here below are listed the commands to run all the various possible tests.

Backend tests:
--------------

Unit tests
~~~~~~~~~~

To run python backend unit tests with *pytest* execute:

.. code:: bash

   pixi run test-backend

.. warning::
   ⚠️ **Some tests depend on generated models** - Always run code
   generation before testing, if your changes had an impact on the
   models, see :ref:`code generation <code-generation-workflow>`.

Frontend tests:
---------------

Python unit tests
~~~~~~~~~~~~~~~~~

To run python frontend unit tests with *pytest* execute:

.. code:: bash

   pixi run test-frontend-py

Javascript unit tests
~~~~~~~~~~~~~~~~~~~~~

To run javascript frontend unit tests with *Mocha* execute:

.. code:: bash

   pixi run test-frontend-js

To run a specific Mocha test file (e.g. :file:`base.test.js`) execute:

.. code:: bash

   npx mocha src/qualpipe_webapp/frontend/unit_tests_js/base.test.js

.. note::

   Add new unit tests in the folder:
   :file:`src/qualpipe_webapp/frontend/unit_tests_js/`

To see the coverage of your unit-tests execute:

.. code:: bash

   npm run coverage

This will create:

-  :file:`report.xml` file inside the folder :file:`/js-unittests/`,
-  the folder :file:`/coverage/` which contains all the coverage files
   (obtained using ``c8``).

To inspect in the browser the interactive html coverage files execute:

.. code:: bash

   open coverage/lcov-report/index.html

To exclude some files/folders from the coverage, properly edit the file :file:`.c8rc`

End-to-end tests
~~~~~~~~~~~~~~~~

By default the installed test browsers are ``chromium``, ``firefox``, and
``webkit`` (Safari). Other browsers can be installed modifying the file
:file:`playwright.config.ts`. To execute the tests with all browsers run:

.. code:: bash

   pixi run test-frontend-e2e

If the tests are failing for some browsers, or if you want to execute the tests only with a specific browser (e.g. Chromium), add the flag
``--project=chromium`` to the above command.

.. seealso::

   Refer to the :ref:`troubleshooting <playwright-browser-fail>` for issues.

The command automatically executes the e2e tests for the three standard
browsers, and create the folder :file:`/playwright-snapshot/` which contains
the test snapshots taken, and an :file:`index.html` report file inside the
folder :file:`/playwright-report/`. To inspect the interactive html generated
report simply execute:

.. code:: bash

   npx playwright show-report

This will serve the interactvie html report at http://localhost:9323.
Press :kbd:`CTRL+C` to quit.

Instead, to run a specific Playwright test (e.g. the :file:`lst.test.js`), with a specific browser (e.g. Chromium),
execute:

.. code:: bash

   npx playwright test src/qualpipe_webapp/frontend/tests_e2e_js/lst.test.js --project=chromium

.. note::

   Add new end-to-end tests in the folder:
   :file:`src/qualpipe_webapp/frontend/tests_e2e_js/`

All tests
---------

To run all kinds of tests execute:

.. code:: bash

   pixi run all-tests

You can always add the flag ``--project=chromium`` (or ``firefox`` or ``webkit``) at the end of the previous command.
