"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Hashed password (SHA-256)")
    is_active: bool = Field(True, description="Whether user is active")

class Project(BaseModel):
    """
    Housing projects schema
    Collection name: "project"
    """
    title: str = Field(..., description="Project title")
    description: Optional[str] = Field(None, description="Project description")
    status: str = Field("upcoming", description="Status: upcoming | ongoing | completed")
    cover_image: Optional[str] = Field(None, description="Image URL")

class Plot(BaseModel):
    """
    Plot details schema
    Collection name: "plot"
    """
    plot_no: str = Field(..., description="Plot number or ID")
    size: str = Field(..., description="Size, e.g., 5 Marla, 10 Marla")
    sector: Optional[str] = Field(None, description="Sector/Block name")
    price: Optional[float] = Field(None, ge=0, description="Price in PKR")
    status: str = Field("available", description="available | booked | sold")
