"""Generated from lda_c_rpa.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import numpy as np
from jax.numpy import array as array
from jax.numpy import int32 as int32
from jax.numpy import nan as nan
from typing import Callable, Optional
from jxc.functionals.utils import *

def pol(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  functional_body = lambda rs, zeta=None: (0.0622 * jnp.log(rs) - 0.096 + rs * (0.018 * jnp.log(rs) - 0.036)) / 2

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  functional_body = lambda rs, zeta=None: (0.0622 * jnp.log(rs) - 0.096 + rs * (0.018 * jnp.log(rs) - 0.036)) / 2

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  functional_body = lambda rs, zeta=None: (0.0622 * jnp.log(rs) - 0.096 + rs * (0.018 * jnp.log(rs) - 0.036)) / 2

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t10 = t6 / t8
  t13 = jnp.log(t4 * t10 / 0.4e1)
  t16 = 0.18e-1 * t13 - 0.36e-1
  t24 = t6 / t8 / t7
  vrho_0_ = 0.31100000000000000000000000000000000000000000000000e-1 * t13 - 0.48000000000000000000000000000000000000000000000000e-1 + t4 * t10 * t16 / 0.8e1 + t7 * (-0.10366666666666666666666666666666666666666666666667e-1 / t7 - t4 * t24 * t16 / 0.24e2 - 0.75000000000000000000000000000000000000000000000000e-3 * t4 * t24)
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
  functional_body = lambda rs, zeta=None: (0.0622 * jnp.log(rs) - 0.096 + rs * (0.018 * jnp.log(rs) - 0.036)) / 2

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t9 = t6 / t7
  t12 = jnp.log(t4 * t9 / 0.4e1)
  t15 = 0.18e-1 * t12 - 0.36e-1
  t23 = t6 / t7 / r0
  vrho_0_ = 0.31100000000000000000000000000000000000000000000000e-1 * t12 - 0.48000000000000000000000000000000000000000000000000e-1 + t4 * t9 * t15 / 0.8e1 + r0 * (-0.10366666666666666666666666666666666666666666666667e-1 / r0 - t4 * t23 * t15 / 0.24e2 - 0.75000000000000000000000000000000000000000000000000e-3 * t4 * t23)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t3 = 3 ** (0.1e1 / 0.3e1)
  t5 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t6 = t3 * t5
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = r0 ** (0.1e1 / 0.3e1)
  t12 = t8 / t9 / r0
  t17 = jnp.log(t6 * t8 / t9 / 0.4e1)
  t19 = 0.18e-1 * t17 - 0.36e-1
  t25 = r0 ** 2
  t30 = t8 / t9 / t25
  v2rho2_0_ = -0.20733333333333333333333333333333333333333333333334e-1 / r0 - t6 * t12 * t19 / 0.12e2 - 0.15000000000000000000000000000000000000000000000000e-2 * t6 * t12 + r0 * (0.10366666666666666666666666666666666666666666666667e-1 / t25 + t6 * t30 * t19 / 0.18e2 + 0.12500000000000000000000000000000000000000000000000e-2 * t6 * t30)
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** 2
  t4 = 3 ** (0.1e1 / 0.3e1)
  t6 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = t4 * t6
  t8 = 4 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = r0 ** (0.1e1 / 0.3e1)
  t13 = t9 / t10 / t1
  t18 = jnp.log(t7 * t9 / t10 / 0.4e1)
  t20 = 0.18e-1 * t18 - 0.36e-1
  t26 = t1 * r0
  t31 = t9 / t10 / t26
  v3rho3_0_ = 0.31100000000000000000000000000000000000000000000001e-1 / t1 + t7 * t13 * t20 / 0.6e1 + 0.37500000000000000000000000000000000000000000000000e-2 * t7 * t13 + r0 * (-0.20733333333333333333333333333333333333333333333334e-1 / t26 - 0.7e1 / 0.54e2 * t7 * t31 * t20 - 0.32500000000000000000000000000000000000000000000000e-2 * t7 * t31)

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** 2
  t2 = t1 * r0
  t5 = 3 ** (0.1e1 / 0.3e1)
  t7 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t8 = t5 * t7
  t9 = 4 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = r0 ** (0.1e1 / 0.3e1)
  t14 = t10 / t11 / t2
  t19 = jnp.log(t8 * t10 / t11 / 0.4e1)
  t21 = 0.18e-1 * t19 - 0.36e-1
  t27 = t1 ** 2
  t32 = t10 / t11 / t27
  v4rho4_0_ = -0.82933333333333333333333333333333333333333333333336e-1 / t2 - 0.14e2 / 0.27e2 * t8 * t14 * t21 - 0.13000000000000000000000000000000000000000000000000e-1 * t8 * t14 + r0 * (0.62200000000000000000000000000000000000000000000002e-1 / t27 + 0.35e2 / 0.81e2 * t8 * t32 * t21 + 0.11611111111111111111111111111111111111111111111111e-1 * t8 * t32)

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t4 = 3 ** (0.1e1 / 0.3e1)
  t6 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t7 = t4 * t6
  t8 = 4 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = t1 ** (0.1e1 / 0.3e1)
  t13 = t9 / t10 / t1
  t18 = jnp.log(t7 * t9 / t10 / 0.4e1)
  t20 = 0.18e-1 * t18 - 0.36e-1
  t26 = t1 ** 2
  t31 = t9 / t10 / t26
  d11 = -0.20733333333333333333333333333333333333333333333334e-1 / t1 - t7 * t13 * t20 / 0.12e2 - 0.15000000000000000000000000000000000000000000000000e-2 * t7 * t13 + t1 * (0.10366666666666666666666666666666666666666666666667e-1 / t26 + t7 * t31 * t20 / 0.18e2 + 0.12500000000000000000000000000000000000000000000000e-2 * t7 * t31)
  d12 = d11
  d22 = d12
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** 2
  t5 = 3 ** (0.1e1 / 0.3e1)
  t7 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t8 = t5 * t7
  t9 = 4 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = t1 ** (0.1e1 / 0.3e1)
  t14 = t10 / t11 / t2
  t19 = jnp.log(t8 * t10 / t11 / 0.4e1)
  t21 = 0.18e-1 * t19 - 0.36e-1
  t27 = t2 * t1
  t32 = t10 / t11 / t27
  d111 = 0.31100000000000000000000000000000000000000000000001e-1 / t2 + t8 * t14 * t21 / 0.6e1 + 0.37500000000000000000000000000000000000000000000000e-2 * t8 * t14 + t1 * (-0.20733333333333333333333333333333333333333333333334e-1 / t27 - 0.7e1 / 0.54e2 * t8 * t32 * t21 - 0.32500000000000000000000000000000000000000000000000e-2 * t8 * t32)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** 2
  t3 = t2 * t1
  t6 = 3 ** (0.1e1 / 0.3e1)
  t8 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t9 = t6 * t8
  t10 = 4 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = t1 ** (0.1e1 / 0.3e1)
  t15 = t11 / t12 / t3
  t20 = jnp.log(t9 * t11 / t12 / 0.4e1)
  t22 = 0.18e-1 * t20 - 0.36e-1
  t28 = t2 ** 2
  t33 = t11 / t12 / t28
  d1111 = -0.82933333333333333333333333333333333333333333333336e-1 / t3 - 0.14e2 / 0.27e2 * t9 * t15 * t22 - 0.13000000000000000000000000000000000000000000000000e-1 * t9 * t15 + t1 * (0.62200000000000000000000000000000000000000000000002e-1 / t28 + 0.35e2 / 0.81e2 * t9 * t33 * t22 + 0.11611111111111111111111111111111111111111111111111e-1 * t9 * t33)

  res = {'v4rho4': d1111}
  return res
