OC PYTHON SDK
==============
Quickstart
----------

Install package

.. code-block:: bash

    pip install -i https://test.pypi.org/simple/ oc-python-sdk  # Install test package
    pip install oc-python-sdk  # Install released package

Compatibility
-------------

This SDK uses Pydantic v2 for model validation (requires ``pydantic>=2,<3`` and Python >= 3.8).

Migration notes
---------------

- Pydantic v2 deprecates ``BaseModel.json()``; for plain models use ``model_dump_json()``.
- Validation errors are produced by Pydantic v2 with updated error messages and structure.
