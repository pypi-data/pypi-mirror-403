# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from .._models import BaseModel

__all__ = ["EmployeeDeleteResponse"]


class EmployeeDeleteResponse(BaseModel):
    """Employee deleted successfully"""

    message: str

    success: bool
