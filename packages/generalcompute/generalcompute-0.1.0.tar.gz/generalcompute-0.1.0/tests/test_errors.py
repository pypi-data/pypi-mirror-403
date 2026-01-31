"""Tests for error classes."""

import pytest
from generalcompute._errors import (
    APIError,
    AuthenticationError,
    RateLimitError,
    BadRequestError,
    NotFoundError,
    InternalServerError,
    create_error_from_response,
)


def test_api_error():
    error = APIError("Test error")
    assert isinstance(error, Exception)
    assert error.message == "Test error"


def test_api_error_with_details():
    error = APIError("Test error", status=500, code="internal_error")
    assert error.status == 500
    assert error.code == "internal_error"


def test_authentication_error():
    error = AuthenticationError()
    assert isinstance(error, APIError)
    assert error.status == 401


def test_authentication_error_custom_message():
    error = AuthenticationError("Invalid API key")
    assert error.message == "Invalid API key"


def test_rate_limit_error():
    error = RateLimitError()
    assert isinstance(error, APIError)
    assert error.status == 429


def test_bad_request_error():
    error = BadRequestError()
    assert isinstance(error, APIError)
    assert error.status == 400


def test_bad_request_error_with_param():
    error = BadRequestError("Invalid param", param="model")
    assert error.param == "model"


def test_not_found_error():
    error = NotFoundError()
    assert isinstance(error, APIError)
    assert error.status == 404


def test_internal_server_error():
    error = InternalServerError()
    assert isinstance(error, APIError)
    assert error.status == 500


def test_create_error_from_response_401():
    error = create_error_from_response(401, "Unauthorized")
    assert isinstance(error, AuthenticationError)


def test_create_error_from_response_429():
    error = create_error_from_response(429, "Too many requests")
    assert isinstance(error, RateLimitError)


def test_create_error_from_response_400():
    error = create_error_from_response(400, "Invalid request")
    assert isinstance(error, BadRequestError)


def test_create_error_from_response_404():
    error = create_error_from_response(404, "Not found")
    assert isinstance(error, NotFoundError)


def test_create_error_from_response_500():
    error = create_error_from_response(500, "Server error")
    assert isinstance(error, InternalServerError)


def test_create_error_from_response_unknown():
    error = create_error_from_response(418, "I am a teapot")
    assert isinstance(error, APIError)
    assert error.status == 418
