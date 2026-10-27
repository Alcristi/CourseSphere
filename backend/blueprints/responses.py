"""Shared HTTP response helpers."""

from flask import jsonify


def success_response(data, code):
    return jsonify(data), code


def error_response(error, code):
    return jsonify({"error": error}), code
