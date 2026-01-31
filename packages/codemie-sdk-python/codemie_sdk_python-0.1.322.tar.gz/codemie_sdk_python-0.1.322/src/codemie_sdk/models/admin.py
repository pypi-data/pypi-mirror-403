"""Admin models for managing applications/projects."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field


class ApplicationsListResponse(BaseModel):
    """Response model for list applications endpoint."""

    model_config = ConfigDict(extra="ignore")

    applications: List[str] = Field(..., description="List of application names")


class ApplicationCreateRequest(BaseModel):
    """Request model for creating an application/project."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Application/project name")


class ApplicationCreateResponse(BaseModel):
    """Response model for create application endpoint."""

    model_config = ConfigDict(extra="ignore")

    message: str = Field(..., description="Created application name")
