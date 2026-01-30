TMG Data Library
==================================

TMG data library has the functionalities to interact with Google Cloud services allowing to develop more reliable and standard data pipelines.

-  `Client Library Documentation`_

.. _Client Library Documentation: https://tmg-data.readthedocs.io

Quick Start
-----------

Installation
~~~~~~~~~~~~

Install this library in a `virtualenv`_ using pip.

.. _`virtualenv`: https://virtualenv.pypa.io/en/latest/

Supported Python Versions
^^^^^^^^^^^^^^^^^^^^^^^^^
Python >= 3.5

Mac/Linux
^^^^^^^^^

.. code-block:: console

    pip install virtualenv
    virtualenv <your-env>
    source <your-env>/bin/activate
    <your-env>/bin/pip install tmg-data

Example Usage
-------------

Transform from MySQL to BigQuery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: python

    from tmg.data import transfer

    transfer_client = transfer.Client(project='your-project-id')

    transfer_client.bq_to_mysql(
        connection_string='root:password@host:port/your-database',
        bq_table='your-project-id.your-dataset.your-table',
        mysql_table='your-database.your-table'
    )

