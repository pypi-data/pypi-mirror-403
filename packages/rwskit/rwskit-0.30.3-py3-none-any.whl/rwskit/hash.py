################################################################################
# Copyright (c) 2023 - 2025 Reid Swanson. All Rights Reserved                  #
#                                                                              #
# File: /src/rwskit/hash.py                                                    #
# Created Date: 24-04-2025T07:27 pm -07:00                                     #
# Author: Reid Swanson                                                         #
#                                                                              #
# Unauthorized copying of this file, via any medium is strictly prohibited     #
# proprietary and confidential.                                                #
################################################################################
"""Hash utilities."""

# Future Library
from __future__ import annotations

# Standard Library
import logging

from typing import Any, Callable, Literal, Optional, TypeVar

# 3rd Party Library
import xxhash

from icontract import require

# msgpack can't handle integers greater than 64bits!
# It's been a feature request for almost 10 years:
# https://github.com/msgpack/msgpack/issues/206
# from msgspec import msgpack as msgproto
from msgspec import json, msgpack

# 1st Party Library
from rwskit.collections_ import recursive_sort
from rwskit.numeric import to_signed

log = logging.getLogger(__name__)

E = TypeVar("E", json.Encoder, msgpack.Encoder)
HashSize = Literal[32, 64, 128]


class ObjectHasher:
    """Hash objects using xxHash.

    The only requirement is that the object be ``msgpack`` serializable.
    """

    _hashers: dict[HashSize, Callable] = {
        32: xxhash.xxh32,
        64: xxhash.xxh3_64,
        128: xxhash.xxh3_128,
    }

    @require(lambda hash_size: hash_size in (32, 64, 128))
    def __init__(
        self,
        hash_size: HashSize = 128,
        signed: bool = False,
        encoder: Optional[E] = None,
    ):
        self._hash_size: HashSize = hash_size
        self._hasher = self._hashers[hash_size]
        self._signed = signed

        if encoder is not None:
            self._encoder = encoder
        elif hash_size < 128:
            self._encoder = msgpack.Encoder()
        else:
            self._encoder = json.Encoder()

    @property
    def hash_size(self) -> HashSize:
        """Get integer size of the returned hash values this hasher produces."""
        return self._hash_size

    @require(lambda self, signed: not signed or self._hash_size < 128)
    def hash(self, obj: Any, signed: Optional[bool] = None) -> int:
        """
        Hash the object using the hash size specified in the constructor.

        ``xxHash`` returns an unsigned value, but it can be converted to a
        signed value if the hash size is less than 128 bits.

        ..note::
            Only values supported by
            `msgpack <https://jcristharif.com/msgspec/supported-types.html>`__
            can be hashed.

        ..note::
            This can only hash integers up to 64-bits.

        Parameters
        ----------
        obj : Any
            The object to hash
        signed : bool, default = False
            Whether to convert the value to a signed integer using
            :meth:`~rwskit.numeric.to_signed`.

        Returns
        -------
        int
            An integer representing the hash of the object.

        Raises
        ------
        OverflowError
            If the data contains an integer that is outside the range
            -2^63 to 2^64-1.
        """
        signed = signed or self._signed
        data = self._encoder.encode(obj)
        unsigned_value = self._hasher(data).intdigest()

        return to_signed(unsigned_value) if signed else unsigned_value

    @require(lambda self, signed: not signed or self._hash_size < 128)
    def hash_sorted(self, obj: Any, signed: Optional[bool] = None) -> int:
        """Sort a collection using :func:`~rwskit.collections_.recursive_sort` and hash the result.

        This should provide a more robust hash that should return the same
        value for collections containing the same data, but in a different
        order.
        """

        signed = signed or self._signed
        return self.hash(recursive_sort(obj), signed=signed)
