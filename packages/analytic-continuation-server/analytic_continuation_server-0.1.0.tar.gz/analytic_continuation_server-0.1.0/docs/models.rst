Pydantic Models
===============

This document describes all Pydantic models used for request/response
validation in the API.

.. automodule:: analytic_continuation_server.models
   :members:
   :undoc-members:
   :show-inheritance:

Base Models
-----------

PointModel
~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.PointModel
   :members:
   :show-inheritance:

ComplexModel
~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.ComplexModel
   :members:
   :show-inheritance:

TransformParamsModel
~~~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.TransformParamsModel
   :members:
   :show-inheritance:

SingularityModel
~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.SingularityModel
   :members:
   :show-inheritance:

Request Models
--------------

TransformPointRequest
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.TransformPointRequest
   :members:
   :show-inheritance:

MeromorphicRequest
~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.MeromorphicRequest
   :members:
   :show-inheritance:

LaurentFitRequest
~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.LaurentFitRequest
   :members:
   :show-inheritance:

WebGLRenderDataRequest
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.WebGLRenderDataRequest
   :members:
   :show-inheritance:

Response Models
---------------

MeromorphicResponse
~~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.MeromorphicResponse
   :members:
   :show-inheritance:

LaurentFitResponse
~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.LaurentFitResponse
   :members:
   :show-inheritance:

WebGLRenderDataResponse
~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.WebGLRenderDataResponse
   :members:
   :show-inheritance:

ContinuationDefinition
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: analytic_continuation_server.models.ContinuationDefinition
   :members:
   :show-inheritance:
