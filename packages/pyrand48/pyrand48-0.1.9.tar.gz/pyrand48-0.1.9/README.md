pyrand48
========

`pyrand48` is a partial implementation in Python of the rand48 linear congruential
generator. We currently omit `seed48()`, `lcong48()`, and `nrand48()`, but suggestions
or implementations are welcome.

Please note: `pyrand48` is deterministic. It is *not* cryptographically secure
even with a good choice of starting seed. It is intended
for use by people who need uniformly distributed pseudo-random numbers in a
deterministic sequence.


Usage
-----

```python
from pyrand48.rand48 import Rand48

prng = Rand48(42)                    # seeds with int(time.time()) if no seed provided
random_float = prng.drand48()        # 0 <= r < 1
random_unsigned_int = prng.lrand48() # 0 <= r < 2**31
random_signed_int = prng.mrand48()   # -(2**31) <= r < 2**31

d6 = [1, 2, 3, 4, 5, 6]
d6_roll = d6[int(prng.drand48() * len(d6)]
```

Background
----------

Linear congruential generators are pseudo-random number generators
that convert an initial seed $X_0$ into a sequence of pseudo-random
numbers $(X_0, X_1, X_2, ...)$ via the formula

$$X_{n+1} = (a X_n + c)\pmod{m}$$

Thus the *multiplier* $a$, the *addend* $c$, and the *modulus* $m$ uniquely
specify a linear congruential generator. All computations are to be performed
with integers modulo $m$.

[The POSIX specification for rand48](https://pubs.opengroup.org/onlinepubs/9699919799/functions/drand48.html) specifies that rand48 is the linear congruential generator with

$$a = 5deece66d_{16},\quad c = b_{16},\quad m = 2^{48}.$$

The POSIX specification for rand48 specifies the following functions:

```C
void srand48(long seedval);
unsigned short *seed48(unsigned short seed16v[3]);
void lcong48(unsigned short param[7]);
double drand48(void);
double erand48(unsigned short xsubi[3]);
long lrand48(void);
long nrand48(unsigned short xsubi[3]);
long mrand48(void);
long jrand48(unsigned short xsubi[3]);
```

This module prioritizes the rand48 linear congruential generator, with an expectation
of seeding with `srand48`. Consequently, we aim to make our functions conform with the
specification, but we do not aim for complete coverage of the functions available.

In particular:
* We omit `seed48()` because of its use of an internal buffer.
* We omit `lcong48` because we believe a generic linear congruential generator should 
be preferred for this use.
* Additionally, we omit `nrand48()`.

We include the C program [generate_pyrand48_test.c](tests/generate_pyrand48_test.c)
which we used to generate conformance tests in Pytest.

License
-------

Copyright (C) 2024 MLE Slone. Licensed under the [MIT license](LICENSE.md).

This module includes a partial translation of Martin Birgmeier's implementation of the
rand48 pseudorandom number generator from C into Python.

```C
/*
 * Copyright (c) 1993 Martin Birgmeier
 * All rights reserved.
 *
 * You may redistribute unmodified or modified versions of this source
 * code provided that the above copyright notice and this and the
 * following conditions are retained.
 *
 * This software is provided ``as is'', and comes with no warranties
 * of any kind. I shall in no event be liable for anything that happens
 * to anyone/anything when using this software.
 */
```
