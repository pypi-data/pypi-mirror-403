TMG ETL pipeline
==================================

TMG ETL pipeline is the base structure of our ETL pipelines.
Any pipeline should inherit from TMGETLPipeline class and implement the necessary methods.


Quick Start
-----------

Installation
~~~~~~~~~~~~

Install this library in a `virtualenv`_ using pip. `virtualenv`_ is a tool to
create isolated Python environments. The basic problem it addresses is one of
dependencies and versions, and indirectly permissions.

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
    <your-env>/bin/pip install tmg-etl-pipeline

Example Usage
-------------

.. code:: python

    from tmg_etl_pipeline.etl import TMGETLPipeline


    class MyETL(TMGETLPipeline):

        def run(self):
            # your ETL logic goes here
            # access the configs
            # self.config['some-config-variable']
            # access the secrets
            # self.secrets['some-secret-variable']

        def cleanup(self):
            # your clean up code goes here

    etl = MyETL(app_name='your-app-name', config_path='path/to-the-config-file')
    etl.execute()
