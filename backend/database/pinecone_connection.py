"""Pinecone index connection."""

import os

from pinecone import Pinecone

from database.config import required_env


def get_pinecone_client():
    return Pinecone(api_key=required_env("PINECONE_API_KEY"))


def get_course_index(index_name=None):
    return get_pinecone_client().Index(index_name or os.getenv("PINECONE_INDEX", "courses"))
