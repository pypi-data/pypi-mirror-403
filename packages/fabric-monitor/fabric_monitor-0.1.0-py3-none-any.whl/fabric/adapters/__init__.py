"""Framework adapters module"""

from fabric.adapters.base import BaseAdapter

__all__ = [
    "BaseAdapter",
]


def get_fastapi_adapter():
    """Lazy import FastAPI adapter"""
    from fabric.adapters.fastapi import FastAPIAdapter
    return FastAPIAdapter


def get_flask_adapter():
    """Lazy import Flask adapter"""
    from fabric.adapters.flask import FlaskAdapter
    return FlaskAdapter
