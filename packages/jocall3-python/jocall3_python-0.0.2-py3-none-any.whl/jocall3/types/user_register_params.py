# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["UserRegisterParams", "Address"]


class UserRegisterParams(TypedDict, total=False):
    email: Required[str]

    name: Required[str]

    password: Required[str]

    address: Address

    phone: str


class Address(TypedDict, total=False):
    city: str

    country: str

    state: str

    street: str

    zip: str
