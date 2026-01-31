🧹 Cleanup
===============

When you have done with your development you can execute a :ref:`soft
clean <soft-clean>` or a :ref:`full clean <full-clean>`.

.. _soft-clean:

Soft clean
----------

To stop only the pods, preserving the cluster, execute:

.. code:: bash

   pixi run stop

.. note:: To restart your development workflow then execute one of the following command, upon your case:

   - With images rebuilding:

   .. code:: bash

      pixi run dev-restart

   - Without images rebuilding:

   .. code:: bash

      pixi run dev-restart-no-build


.. _full-clean:

Full clean
----------

To stop the pods and remove the cluster execute:

.. code:: bash

   pixi run stop-and-delete

.. note:: To restart your development workflow then execute one of the following command, upon your case:

   - With images rebuilding:

   .. code:: bash

      pixi run dev-up-no-build

   - Without images rebuilding:

   .. code:: bash

      pixi run dev-up


Docker clean
------------

You can remove the unused Docker containers with:

.. code:: bash

   pixi run prune

If you want to clean everything (stop pods, remove cluster, remove docker images) you can execute:

.. code:: bash

   pixi run clean-all

.. note:: To restart your development workflow after the ``clean-all`` command you can execute:

   .. code:: bash

      pixi run dev-up
