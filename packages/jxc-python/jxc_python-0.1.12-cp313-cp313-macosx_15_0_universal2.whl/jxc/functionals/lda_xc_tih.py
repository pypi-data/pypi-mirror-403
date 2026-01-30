"""Generated from lda_xc_tih.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import numpy as np
from jax.numpy import array as array
from jax.numpy import int32 as int32
from jax.numpy import nan as nan
from typing import Callable, Optional
from .utils import *

def pol(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  tih_par = np.array([np.nan, -1.0953, -0.0334789, 0.414661, -0.152399, -0.354691, 0.0390837, -0.0748531, -0.136598, -1.41063, 0.00496577, 0.48315, 4.02905, -0.420166, 0.0104352, -1.47409, -0.442455, 0.625039, 1.30351, 1.37026, -1.29598, -1.04305, -0.909651, -0.991782, -0.915745, 1.95026], dtype=np.float64)

  tih_zj = lambda j, n: jnp.tanh(tih_par[2 * j - 1] + tih_par[2 * j] * n)

  tih_vxc = lambda n: tih_par[17] + jnp.sum(jnp.array([tih_par[i] * tih_zj(i - 17, n) for i in range(18, 25 + 1)]), axis=0)

  functional_body = lambda rs, z=None: tih_vxc(f.n_total(rs))
  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )

  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  tih_par = np.array([np.nan, -1.0953, -0.0334789, 0.414661, -0.152399, -0.354691, 0.0390837, -0.0748531, -0.136598, -1.41063, 0.00496577, 0.48315, 4.02905, -0.420166, 0.0104352, -1.47409, -0.442455, 0.625039, 1.30351, 1.37026, -1.29598, -1.04305, -0.909651, -0.991782, -0.915745, 1.95026], dtype=np.float64)

  tih_zj = lambda j, n: jnp.tanh(tih_par[2 * j - 1] + tih_par[2 * j] * n)

  tih_vxc = lambda n: tih_par[17] + jnp.sum(jnp.array([tih_par[i] * tih_zj(i - 17, n) for i in range(18, 25 + 1)]), axis=0)

  functional_body = lambda rs, z=None: tih_vxc(f.n_total(rs))
  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )

  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  tih_par = np.array([np.nan, -1.0953, -0.0334789, 0.414661, -0.152399, -0.354691, 0.0390837, -0.0748531, -0.136598, -1.41063, 0.00496577, 0.48315, 4.02905, -0.420166, 0.0104352, -1.47409, -0.442455, 0.625039, 1.30351, 1.37026, -1.29598, -1.04305, -0.909651, -0.991782, -0.915745, 1.95026], dtype=np.float64)

  tih_zj = lambda j, n: jnp.tanh(tih_par[2 * j - 1] + tih_par[2 * j] * n)

  tih_vxc = lambda n: tih_par[17] + jnp.sum(jnp.array([tih_par[i] * tih_zj(i - 17, n) for i in range(18, 25 + 1)]), axis=0)

  functional_body = lambda rs, z=None: tih_vxc(f.n_total(rs))

  t4 = jnp.tanh(0.10953e1 + 0.334789e-1 * r0 + 0.334789e-1 * r1)
  t9 = jnp.tanh(-0.414661e0 + 0.152399e0 * r0 + 0.152399e0 * r1)
  t14 = jnp.tanh(-0.354691e0 + 0.390837e-1 * r0 + 0.390837e-1 * r1)
  t19 = jnp.tanh(0.748531e-1 + 0.136598e0 * r0 + 0.136598e0 * r1)
  t24 = jnp.tanh(-0.141063e1 + 0.496577e-2 * r0 + 0.496577e-2 * r1)
  t29 = jnp.tanh(0.48315e0 + 0.402905e1 * r0 + 0.402905e1 * r1)
  t34 = jnp.tanh(-0.420166e0 + 0.104352e-1 * r0 + 0.104352e-1 * r1)
  t39 = jnp.tanh(0.147409e1 + 0.442455e0 * r0 + 0.442455e0 * r1)
  t42 = t4 ** 2
  t44 = t9 ** 2
  t46 = t14 ** 2
  t48 = t19 ** 2
  t50 = t24 ** 2
  t52 = t29 ** 2
  t54 = t34 ** 2
  t56 = t39 ** 2
  vrho_0_ = 0.625039e0 - 0.130351e1 * t4 - 0.137026e1 * t9 - 0.129598e1 * t14 + 0.104305e1 * t19 - 0.909651e0 * t24 - 0.991782e0 * t29 - 0.915745e0 * t34 - 0.195026e1 * t39 + (r0 + r1) * (-0.503355413957527e1 + 0.43640080939e-1 * t42 + 0.20882625374e0 * t44 + 0.50651693526e-1 * t46 - 0.14247854390e0 * t48 + 0.451711764627e-2 * t50 + 0.399593926710e1 * t52 + 0.95559822240e-2 * t54 + 0.86290228830e0 * t56)
  vrho_1_ = vrho_0_
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  tih_par = np.array([np.nan, -1.0953, -0.0334789, 0.414661, -0.152399, -0.354691, 0.0390837, -0.0748531, -0.136598, -1.41063, 0.00496577, 0.48315, 4.02905, -0.420166, 0.0104352, -1.47409, -0.442455, 0.625039, 1.30351, 1.37026, -1.29598, -1.04305, -0.909651, -0.991782, -0.915745, 1.95026], dtype=np.float64)

  tih_zj = lambda j, n: jnp.tanh(tih_par[2 * j - 1] + tih_par[2 * j] * n)

  tih_vxc = lambda n: tih_par[17] + jnp.sum(jnp.array([tih_par[i] * tih_zj(i - 17, n) for i in range(18, 25 + 1)]), axis=0)

  functional_body = lambda rs, z=None: tih_vxc(f.n_total(rs))

  t3 = jnp.tanh(0.10953e1 + 0.334789e-1 * r0)
  t7 = jnp.tanh(-0.414661e0 + 0.152399e0 * r0)
  t11 = jnp.tanh(-0.354691e0 + 0.390837e-1 * r0)
  t15 = jnp.tanh(0.748531e-1 + 0.136598e0 * r0)
  t19 = jnp.tanh(-0.141063e1 + 0.496577e-2 * r0)
  t23 = jnp.tanh(0.48315e0 + 0.402905e1 * r0)
  t27 = jnp.tanh(-0.420166e0 + 0.104352e-1 * r0)
  t31 = jnp.tanh(0.147409e1 + 0.442455e0 * r0)
  t33 = t3 ** 2
  t35 = t7 ** 2
  t37 = t11 ** 2
  t39 = t15 ** 2
  t41 = t19 ** 2
  t43 = t23 ** 2
  t45 = t27 ** 2
  t47 = t31 ** 2
  vrho_0_ = 0.625039e0 - 0.130351e1 * t3 - 0.137026e1 * t7 - 0.129598e1 * t11 + 0.104305e1 * t15 - 0.909651e0 * t19 - 0.991782e0 * t23 - 0.915745e0 * t27 - 0.195026e1 * t31 + r0 * (-0.503355413957527e1 + 0.43640080939e-1 * t33 + 0.20882625374e0 * t35 + 0.50651693526e-1 * t37 - 0.14247854390e0 * t39 + 0.451711764627e-2 * t41 + 0.399593926710e1 * t43 + 0.95559822240e-2 * t45 + 0.86290228830e0 * t47)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t4 = jnp.tanh(0.10953e1 + 0.334789e-1 * r0 + 0.334789e-1 * r1)
  t5 = t4 ** 2
  t10 = jnp.tanh(-0.414661e0 + 0.152399e0 * r0 + 0.152399e0 * r1)
  t11 = t10 ** 2
  t16 = jnp.tanh(-0.354691e0 + 0.390837e-1 * r0 + 0.390837e-1 * r1)
  t17 = t16 ** 2
  t22 = jnp.tanh(0.748531e-1 + 0.136598e0 * r0 + 0.136598e0 * r1)
  t23 = t22 ** 2
  t28 = jnp.tanh(-0.141063e1 + 0.496577e-2 * r0 + 0.496577e-2 * r1)
  t29 = t28 ** 2
  t34 = jnp.tanh(0.48315e0 + 0.402905e1 * r0 + 0.402905e1 * r1)
  t35 = t34 ** 2
  t40 = jnp.tanh(-0.420166e0 + 0.104352e-1 * r0 + 0.104352e-1 * r1)
  t41 = t40 ** 2
  t46 = jnp.tanh(0.147409e1 + 0.442455e0 * r0 + 0.442455e0 * r1)
  t47 = t46 ** 2
  d11 = -0.1006710827915054e2 + 0.87280161878e-1 * t5 + 0.41765250748e0 * t11 + 0.101303387052e0 * t17 - 0.28495708780e0 * t23 + 0.903423529254e-2 * t29 + 0.799187853420e1 * t35 + 0.191119644480e-1 * t41 + 0.172580457660e1 * t47 + (r0 + r1) * (0.87280161878e-1 * t4 * (0.334789e-1 - 0.334789e-1 * t5) + 0.41765250748e0 * t10 * (0.152399e0 - 0.152399e0 * t11) + 0.101303387052e0 * t16 * (0.390837e-1 - 0.390837e-1 * t17) - 0.28495708780e0 * t22 * (0.136598e0 - 0.136598e0 * t23) + 0.903423529254e-2 * t28 * (0.496577e-2 - 0.496577e-2 * t29) + 0.799187853420e1 * t34 * (0.402905e1 - 0.402905e1 * t35) + 0.191119644480e-1 * t40 * (0.104352e-1 - 0.104352e-1 * t41) + 0.172580457660e1 * t46 * (0.442455e0 - 0.442455e0 * t47))
  d12 = d11
  d22 = d12
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t3 = jnp.tanh(0.10953e1 + 0.334789e-1 * r0)
  t4 = t3 ** 2
  t8 = jnp.tanh(-0.414661e0 + 0.152399e0 * r0)
  t9 = t8 ** 2
  t13 = jnp.tanh(-0.354691e0 + 0.390837e-1 * r0)
  t14 = t13 ** 2
  t18 = jnp.tanh(0.748531e-1 + 0.136598e0 * r0)
  t19 = t18 ** 2
  t23 = jnp.tanh(-0.141063e1 + 0.496577e-2 * r0)
  t24 = t23 ** 2
  t28 = jnp.tanh(0.48315e0 + 0.402905e1 * r0)
  t29 = t28 ** 2
  t33 = jnp.tanh(-0.420166e0 + 0.104352e-1 * r0)
  t34 = t33 ** 2
  t38 = jnp.tanh(0.147409e1 + 0.442455e0 * r0)
  t39 = t38 ** 2
  v2rho2_0_ = -0.1006710827915054e2 + 0.87280161878e-1 * t4 + 0.41765250748e0 * t9 + 0.101303387052e0 * t14 - 0.28495708780e0 * t19 + 0.903423529254e-2 * t24 + 0.799187853420e1 * t29 + 0.191119644480e-1 * t34 + 0.172580457660e1 * t39 + r0 * (0.87280161878e-1 * t3 * (0.334789e-1 - 0.334789e-1 * t4) + 0.41765250748e0 * t8 * (0.152399e0 - 0.152399e0 * t9) + 0.101303387052e0 * t13 * (0.390837e-1 - 0.390837e-1 * t14) - 0.28495708780e0 * t18 * (0.136598e0 - 0.136598e0 * t19) + 0.903423529254e-2 * t23 * (0.496577e-2 - 0.496577e-2 * t24) + 0.799187853420e1 * t28 * (0.402905e1 - 0.402905e1 * t29) + 0.191119644480e-1 * t33 * (0.104352e-1 - 0.104352e-1 * t34) + 0.172580457660e1 * t38 * (0.442455e0 - 0.442455e0 * t39))
  res = {'v2rho2': v2rho2_0_}
  return res

