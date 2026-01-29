import jax.numpy as jnp
import pytest
from jax.nn import softplus

from paramax.utils import inv_softplus


def test_inv_softplus():
    x = jnp.arange(3) + 1
    y = softplus(x)
    x_reconstructed = inv_softplus(y)
    assert pytest.approx(x) == x_reconstructed
