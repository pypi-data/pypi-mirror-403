import math
import time
from typing import Annotated

# This file includes a partial translation of Martin Birgmeier's implementation of the
# rand48 pseudorandom number generator from C into Python.
#
# /*
#  * Copyright (c) 1993 Martin Birgmeier
#  * All rights reserved.
#  *
#  * You may redistribute unmodified or modified versions of this source
#  * code provided that the above copyright notice and this and the
#  * following conditions are retained.
#  *
#  * This software is provided ``as is'', and comes with no warranties
#  * of any kind. I shall in no event be liable for anything that happens
#  * to anyone/anything when using this software.
#  */
#


class Rand48:
    RAND48_SEED_0 = 0x330E
    RAND48_SEED_1 = 0xABCD
    RAND48_SEED_2 = 0x1234
    RAND48_MULT_0 = 0xE66D
    RAND48_MULT_1 = 0xDEEC
    RAND48_MULT_2 = 0x0005
    RAND48_ADD = 0x000B

    _rand48_seed = [
        RAND48_SEED_0,
        RAND48_SEED_1,
        RAND48_SEED_2,
    ]

    _rand48_mult = [
        RAND48_MULT_0,
        RAND48_MULT_1,
        RAND48_MULT_2,
    ]

    _rand48_add = RAND48_ADD

    def __init__(self, seed=None):
        if seed is None:
            seed = int(time.time())
        self.srand48(seed)

    # unsigned short xseed[3]
    # XXX: This is void in Martin Birgmeier's C code. I return the modified xseed
    #      here to allow jrand48 to consume it.
    def _dorand48(self, xseed: Annotated[list[int], 3]) -> Annotated[list[int], 3]:
        temp = [0, 0]

        accu = self._rand48_mult[0] * xseed[0] + self._rand48_add
        temp[0] = accu & 0xFFFF  # lower 16 bits
        accu >>= 16
        accu += self._rand48_mult[0] * xseed[1] + self._rand48_mult[1] * xseed[0]
        temp[1] = accu & 0xFFFF  # middle 16 bits
        accu >>= 16
        accu += (
            self._rand48_mult[0] * xseed[2]
            + self._rand48_mult[1] * xseed[1]
            + self._rand48_mult[2] * xseed[0]
        )
        xseed[0] = temp[0]
        xseed[1] = temp[1]
        xseed[2] = accu & 0xFFFF
        return xseed

    # long int seed
    def srand48(self, seed: int) -> None:
        self._rand48_seed[0] = self.RAND48_SEED_0
        self._rand48_seed[1] = seed & 0xFFFF
        self._rand48_seed[2] = (seed >> 16) & 0xFFFF
        self._rand48_mult[0] = self.RAND48_MULT_0
        self._rand48_mult[1] = self.RAND48_MULT_1
        self._rand48_mult[2] = self.RAND48_MULT_2
        self._rand48_add = self.RAND48_ADD

    # unsigned short xseed[3]
    def erand48(self, xseed: Annotated[list[int], 3]) -> float:
        self._dorand48(xseed)
        return (
            math.ldexp(float(xseed[0]), -48)
            + math.ldexp(float(xseed[1]), -32)
            + math.ldexp(float(xseed[2]), -16)
        )

    # unsigned short xseed[3]
    def jrand48(self, xseed: Annotated[list[int], 3]) -> int:
        xseed = self._dorand48(xseed)
        return (((xseed[2] << 16) + xseed[1] + (1 << 31)) % (1 << 32)) - (1 << 31)

    def drand48(self) -> float:
        return self.erand48(self._rand48_seed)

    def mrand48(self) -> int:
        return self.jrand48(self._rand48_seed)

    def lrand48(self) -> int:
        self._dorand48(self._rand48_seed)
        return (self._rand48_seed[2] << 15) + (self._rand48_seed[1] >> 1)
