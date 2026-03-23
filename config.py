"""Application configuration classes for PFMS Pro."""

from __future__ import annotations

import os


class Config:
    """Default Flask configuration for local and PythonAnywhere deployment."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = "sqlite:///pfms.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
