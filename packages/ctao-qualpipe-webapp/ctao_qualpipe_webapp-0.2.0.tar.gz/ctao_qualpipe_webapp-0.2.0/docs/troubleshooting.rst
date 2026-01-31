
.. _troubleshooting:

🛠️ Troubleshooting
============================

Import errors with generated models?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    pixi run generate-codegen  # Regenerate models


.. _tests-failing:

Tests failing?
~~~~~~~~~~~~~~

.. code:: bash

    # Ensure models and schemas are generated before running tests
    pixi run generate-codegen
    pixi run generate-frontend-schema
    pixi run all-tests


Pixi environment issues?
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    pixi clean              # Clean cache
    source ./setup-env.sh   # Resource environment
    pixi run dev-setup      # Complete reinstall + code generation
    pixi run dev-up         # Run development environment

Port already in use?
~~~~~~~~~~~~~~~~~~~~

If you see errors like ``bind: address already in use``:

.. code:: bash

    # Find process using port 8080
    lsof -i :8080

    # Kill the process
    kill -9 <PID>

    # Or delete and recreate cluster
    make kind-delete
    make dev-up

..

   ⚠️ To be updated once ports will become configurable with env variable in next releases.

Application not accessible
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Check if pods are running:**

   .. code:: bash

      kubectl get pods -n $NAMESPACE

   All pods should be ``Running`` with ``READY 1/1``.

2. **Check Ingress:**

   .. code:: bash

      kubectl get ingress -n $NAMESPACE

   A ``qualpipe-webapp-ingress`` Ingress resource should be present with hosts and ports configured.

3. **Check Ingress Controller:**

   .. code:: bash

      kubectl get pods -n ingress-nginx

   The ``ingress-nginx-controller-*`` pod should have STATUS:
   ``Running``.

4. **Manual port-forward (fallback):** Try to setup a manual port
   forward with:

   .. code:: bash

      make dev-forward

   Then try to access: http://localhost:8080/ . If this works, then the
   issue is with the extraPortMappings with the Ingress Controller.

All these checks (except the manual port forward) are automated with:

.. code:: bash

   make dev-debug-network


Logs not showing Inspect last logs with:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

   # Backend logs
   kubectl logs -n default -l app.kubernetes.io/component=backend --tail=50

   # Frontend logs
   kubectl logs -n default -l app.kubernetes.io/component=frontend --tail=50

   # Nginx logs
   kubectl logs -n default -l app.kubernetes.io/component=nginx --tail=50

   # Ingress Controller logs
   kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=50


.. _playwright-browser-fail:

Playwright test are failing for a specific browser?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can execute Playwright tests on a specific browser (chromium, firefox, webkit)

.. code:: bash

    npx playwright test --project=chromium

..

    ⚠️ **Note:** WebKit browser generally works only with the latest MacOS update.


Some tests about validation are failing?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure you have generated models and schema before running tests (sse section :ref:`tests-failing` for more details).


All test failing with ERR_CONNECTION_REFUSED?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verify that the WebApp is running with:

.. code:: bash

   pixi run dev-health

Or you can open a browser and navigate to http://qualpipe.local:8080/home . If you can't display the page, the WebApp is not running.

.. seealso::
   See :ref:`installation <developers-workflow>` instruction.
