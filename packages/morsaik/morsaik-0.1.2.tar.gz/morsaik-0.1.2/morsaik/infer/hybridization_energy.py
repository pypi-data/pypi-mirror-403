from typing import Union
import numpy as np
import warnings
import itertools

"""
For a segment, the hybridization energy is computed by 2x2 blocks.
The hybridization energy of a 2x2 block is given by one of the following
hybridization energy parameters:
    0 dG_4_2Match_mean
    1 dG_4_1Match
    2 dG_4_0Match
    3 dG_3_1Match_mean
    4 dG_3_0Match
    5 ddG_4_2Match_alternating
    6 ddG_3_1Match_alternating
They are stored in the hybridization_energy_parameters vector
"""
def segemnt_hybridization_energy(
        segment,
        hybridization_energy_parameters
        ):
    segment_shape = (len(alphabet),)*(2*motiflength//2)


import jax
import jax.numpy as jnp

def build_coefficient_tensor_lookup(f_lookup, n):
    """
    f_lookup: integer array of shape (n+1,) giving f(i).
    Output: coefficient array C[ii,jj,kk,ll,k] with shape (n+1,n+1,n+1,n+1,7)
    """
    f_lookup = jnp.asarray(f_lookup)

    idx = jnp.arange(n + 1)
    ii, jj, kk, ll = jnp.meshgrid(idx, idx, idx, idx, indexing="ij")

    ii0 = (ii == 0)
    jj0 = (jj == 0)
    kk0 = (kk == 0)
    ll0 = (ll == 0)
    num_zero = ii0 + jj0 + kk0 + ll0

    # vectorized f
    f_ii = f_lookup[ii]
    f_kk = f_lookup[kk]

    cond_fii_eq_jj = (f_ii == jj)
    cond_fkk_eq_ll = (f_kk == ll)

    C = jnp.zeros((n+1, n+1, n+1, n+1, 7), dtype=jnp.float32)

    # CASE 1 (exactly one zero)
    case1 = (num_zero == 1)

    # g31 branch (k=3) vs g30 branch (k=4)
    g31_branch = (cond_fii_eq_jj | cond_fkk_eq_ll) & case1
    g30_branch = (~(cond_fii_eq_jj | cond_fkk_eq_ll)) & case1

    C = C.at[...,3].set(g31_branch.astype(jnp.float32))
    C = C.at[...,4].set(g30_branch.astype(jnp.float32))

    # g31a correction (k=6)
    pos_cond = (
        ((ii != kk) & (~ii0) & (~kk0)) |
        ((jj != ll) & (~jj0) & (~ll0))
    ) & g31_branch

    neg_cond = (
        ((ii == kk) & (~ii0)) |
        ((jj == ll) & (~jj0))
    ) & g31_branch

    C = C.at[...,6].set(
        jnp.where(pos_cond,  0.5,
        jnp.where(neg_cond, -0.5, 0.0))
    )

    # CASE 2 (no zeros)
    case2 = (num_zero == 0)

    g40_case = (~(cond_fii_eq_jj | cond_fkk_eq_ll)) & case2
    g41_case = (cond_fii_eq_jj ^ cond_fkk_eq_ll) & case2
    g42_case = (cond_fii_eq_jj & cond_fkk_eq_ll) & case2

    C = C.at[...,2].set(g40_case.astype(jnp.float32))
    C = C.at[...,1].set(g41_case.astype(jnp.float32))
    C = C.at[...,0].set(g42_case.astype(jnp.float32))

    # g42a correction (k=5)
    g42a_corr = jnp.where(ii == kk, -0.5, 0.5)
    C = C.at[...,5].set(jnp.where(g42_case, g42a_corr, 0.0))

    return C
