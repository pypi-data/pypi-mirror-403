"""Cursor-based pagination helper for the billing.io SDK."""

from __future__ import annotations

from typing import Any, Callable, Generator


def auto_paginate(
    method: Callable[..., Any],
    **kwargs: Any,
) -> Generator[Any, None, None]:
    """Lazily iterate through every item across all pages.

    ``method`` must be a resource method that returns an object with
    ``data`` (list), ``has_more`` (bool), and ``next_cursor`` (str | None)
    attributes -- i.e., any of the SDK's ``*.list()`` methods.

    Parameters
    ----------
    method:
        A bound ``list`` method such as ``client.checkouts.list``.
    **kwargs:
        Extra keyword arguments forwarded to *method* on every call.  The
        ``cursor`` parameter is managed automatically.

    Yields
    ------
    object
        Individual items (e.g. :class:`~billingio.types.Checkout`).

    Example
    -------
    ::

        from billingio.pagination import auto_paginate

        for checkout in auto_paginate(client.checkouts.list, status="confirmed"):
            print(checkout.checkout_id)
    """

    cursor = kwargs.pop("cursor", None)

    while True:
        page = method(cursor=cursor, **kwargs)
        yield from page.data

        if not page.has_more or page.next_cursor is None:
            break

        cursor = page.next_cursor
