#!/usr/bin/env python
import requests

__all__ = ["ZenodoHTTPStatus"]


class HTTPStatusError(Exception):
    pass


class ZenodoHTTPStatus:
    status_codes = {
        200: {
            "name": "OK",
            "description": "Request succeeded. Response included. Usually sent for GET/PUT/PATCH requests.",
        },
        201: {
            "name": "Created",
            "description": "Request succeeded. Response included. Usually sent for POST requests.",
        },
        202: {
            "name": "Accepted",
            "description": "Request succeeded. Response included. Usually sent for POST requests,"
            "where background processing is needed to fulfill the request.",
        },
        204: {
            "name": "No Content",
            "description": "Request succeeded. No response included. Usually sent for DELETE requests",
        },
        400: {"name": "Bad Request", "description": "Request failed. Error response included."},
        401: {
            "name": "Unauthorized",
            "description": "Request failed, due to an invalid access token. Error response included.",
        },
        403: {
            "name": "Forbidden",
            "description": "Request failed, due to missing authorization"
            "(e.g. deleting an already submitted upload or missing scopes for your access token)."
            "Error response included.",
        },
        404: {
            "name": "Not Found",
            "description": "Request failed, due to the resource not being found. Error response included.",
        },
        405: {
            "name": "Method Not Allowed",
            "description": "Request failed, due to unsupported HTTP method. Error response included.",
        },
        409: {
            "name": "Conflict",
            "description": "Request failed, due to the current state of the resource"
            "(e.g. edit a deopsition which is not fully integrated)."
            "Error response included.",
        },
        410: {
            "name": "Deleted",
            "description": "PID has been deleted",
        },
        415: {
            "name": "Unsupported Media Type",
            "description": "Request failed, due to missing or invalid request header Content-Type."
            "Error response included.",
        },
        429: {
            "name": "Too Many Requests",
            "description": "Request failed, due to rate limiting.Error response included.",
        },
        500: {
            "name": "Internal Server Error",
            "description": "Request failed, due to an internal server error. Error response NOT included."
            "Don’t worry, Zenodo admins have been notified and will be dealing with the problem ASAP.",
        },
    }

    def __init__(self, response):
        self.code = response.status_code
        try:
            self.json = response.json()
        except requests.exceptions.JSONDecodeError:
            self.json = None
        if self.code not in self.status_codes.keys():
            response.raise_for_status()
        if self.is_error():
            self.raise_error()

    def __str__(self):
        return f"HTTP Status Code: {self.code} - {self.name}.\n{self.description}"

    def __repr__(self):
        return f"ZenodoHttpStatus({self.code})"

    def is_error(self):
        return self.code >= 400

    @property
    def name(self):
        if self.code in self.status_codes.keys():
            return self.status_codes[self.code]["name"]
        else:
            return None

    @property
    def description(self):
        if self.code in self.status_codes.keys():
            return self.status_codes[self.code]["description"]
        else:
            return None

    def raise_error(self):
        """
        Raise an HTTPStatusError if the status code corresponds to an error
        """
        if self.is_error():
            msg = f"{self.__str__()}"
            if self.json:
                msg += f"\n{self.json}"
            raise HTTPStatusError(msg)
