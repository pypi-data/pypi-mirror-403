🔌 Installation
=====================

📜 Prerequisites
-----------------

Make sure these software are already installed on your system:

-  **Docker** (`Installation
   Guide <https://docs.docker.com/engine/install/>`__)
-  **Pixi** (`Installation
   Guide <https://pixi.sh/latest/installation/>`__)

If you are on a Mac, these dependencies can be quickly installed via
homebrew executing:

.. code:: bash

   brew install docker pixi

and verify the installation

.. code:: bash

   docker version
   pixi -V

.. _rocket-quick-start:

🚀 Quick Start
--------------

The package is under active development. To install QualPipe package you need to clone the source code from gitlab:

.. code:: bash

   git clone https://gitlab.cta-observatory.org/cta-computing/dpps/qualpipe/qualpipe-webapp.git
   cd qualpipe-webapp
   git submodule update --init --recursive


Next, follow the installation instructions for
:ref:`developers <developers>`.

.. _developers:

Installation for *developers*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _developers-setup:

Setup (*first time only*)
^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Setup environment**:
""""""""""""""""""""""""""

.. code:: bash

   pixi run dev-setup

This will:

-  ✅ Create an isolate Python environment with pixi
-  ✅ Install all dependencies from pyproject.toml (frontend, test, doc,
   dev)
-  ✅ Install the ``ctao-qualpipe-webapp`` package in editable mode
-  ✅ Generate data models
-  ✅ Compile backend and frontend requirements
-  ✅ Generate javascript schema
-  ✅ Install node dependencies
-  ✅ Install pre-commit hooks

.. note::

   **Pixi Environments**: The project defines three environments in ``pixi.toml``:

   -  ``default`` - Uses development dependencies (same as ``qualpipe-webapp-dev``)
   -  ``qualpipe-webapp`` - Production environment with minimal dependencies
   -  ``qualpipe-webapp-dev`` - Development environment with all dev/test dependencies

   You can specify which environment to use with ``pixi run -e <environment> <task>`` or use the default environment. For development work, the default environment is recommended.

.. tip::

   **Development Shell**: For a fully configurable development environment, use:

   .. code:: bash

      pixi shell

   This activates the Pixi environment and is recommended for:

   -  Making commits (pre-commit hooks will be available)
   -  Log inspection and debugging
   -  Running any commands from this guide that don't start with ``pixi run``

   **Best Practice**: Run ``pixi run`` commands from a separate shell (not inside ``pixi shell``) to avoid shell termination issues, as running ``pixi run`` tasks within an active ``pixi shell`` can terminate the shell environment.

   To clean your pixi environment you can execute ``pixi clean``.

.. _2-configure-host:

2. Configure host
"""""""""""""""""

To add ``qualpipe.local`` hostname to the ``/etc/hosts`` file execute:

.. code:: bash

   echo "127.0.0.1 qualpipe.local" | sudo tee -a /etc/hosts

.. _3-start-the-local-development-environment:

3. Start the local development environment
""""""""""""""""""""""""""""""""""""""""""

To deploy the app and start the local development environment execute:

.. code:: bash

   pixi run dev-up

-  ✅ Create a kind cluster with port mappings
-  ✅ Build Docker images (backend + frontend)
-  ✅ Install NGINX Ingress Controller
-  ✅ Deploy the application via Helm

⏳ **Wait** for all pods to be ready (can take 2-3 minutes).

.. _4-access-the-application:

4. Access the application
""""""""""""""""""""""""""

**No port-forward needed!** The kind cluster exposes ports directly via
``extraPortMappings``.

Open in your browser:

-  **Frontend**: http://qualpipe.local:8080/home
-  **Backend API**: http://qualpipe.local:8080/api/docs


--------------

.. _developers-workflow:

Dev Workflow (*after the first time*)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note::

   The local kubernetes cluster should be running already, if not execute ``pixi run dev-up``.
   If you changed any dependency or modified code that requires model regeneration re-execute ``pixi run dev-setup``.


Are images *changed*?
""""""""""""""""""""""

Rebuild images and restart services with:

.. code:: bash

   pixi run dev-restart

Are images *NOT changed*?
"""""""""""""""""""""""""

Upgrade only Helm chart with:

.. code:: bash

   pixi run helm-dev-upgrade

View logs
"""""""""

To display logs from both *backend* and *frontend* containers execute:

.. code:: bash

   pixi run kind-logs

To stop logs, you can soft-kill them with :kbd:`CTRL+C`.


--------------


Verify installation
^^^^^^^^^^^^^^^^^^^

To check that the app is correctly deployed and properly set up, execute this command:

.. code:: bash

   pixi run dev-health

.. seealso::

   If something is not ``✅ OK`` check the cluster status with:

   .. code:: bash

      pixi run kind-status

   or see :ref:`troubleshooting`

Useful Links
------------

-  `pre-commit documentation <https://pre-commit.com/>`__
-  `Mocha documentation <https://mochajs.org/>`__
-  `Playwright documentation <https://playwright.dev/>`__
-  `Pytest documentation <https://docs.pytest.org/>`__
