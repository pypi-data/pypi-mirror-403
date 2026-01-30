"""Generated from lda_c_gombas.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
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
  a1 = -0.0357

  a2 = 0.0562

  b1 = -0.0311

  b2 = 2.39

  functional_body = lambda rs, zeta=None: a1 / (1 + a2 * rs / f.RS_FACTOR) + b1 * jnp.log((rs / f.RS_FACTOR + b2) / (rs / f.RS_FACTOR))

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  a1 = -0.0357

  a2 = 0.0562

  b1 = -0.0311

  b2 = 2.39

  functional_body = lambda rs, zeta=None: a1 / (1 + a2 * rs / f.RS_FACTOR) + b1 * jnp.log((rs / f.RS_FACTOR + b2) / (rs / f.RS_FACTOR))

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t3 = 0.1e1 / t2
  t5 = 0.1e1 + 0.56200000000000000000000000000000000000000000000000e-1 * t3
  t8 = t3 + 0.239e1
  t10 = jnp.log(t8 * t2)
  t12 = t5 ** 2
  t19 = t2 ** 2
  vrho_0_ = -0.357e-1 / t5 - 0.311e-1 * t10 + t1 * (-0.66877999999999999999999999999999999999999999999999e-3 / t12 / t2 / t1 - 0.311e-1 * (-0.1e1 / t1 / 0.3e1 + t8 / t19 / 0.3e1) / t8 * t3)
  vrho_1_ = vrho_0_

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / t1
  t4 = 0.1e1 + 0.56200000000000000000000000000000000000000000000000e-1 * t2
  t7 = t2 + 0.239e1
  t9 = jnp.log(t7 * t1)
  t11 = t4 ** 2
  t18 = t1 ** 2
  vrho_0_ = -0.357e-1 / t4 - 0.311e-1 * t9 + r0 * (-0.66877999999999999999999999999999999999999999999999e-3 / t11 / t1 / r0 - 0.311e-1 * (-0.1e1 / r0 / 0.3e1 + t7 / t18 / 0.3e1) / t7 * t2)

  res = {'vrho': vrho_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t3 = 0.1e1 / t2
  t5 = 0.1e1 + 0.56200000000000000000000000000000000000000000000000e-1 * t3
  t6 = t5 ** 2
  t7 = 0.1e1 / t6
  t9 = 0.1e1 / t2 / t1
  t13 = t3 + 0.239e1
  t14 = t2 ** 2
  t18 = -0.1e1 / t1 / 0.3e1 + t13 / t14 / 0.3e1
  t19 = 0.1e1 / t13
  t20 = t18 * t19
  t25 = t1 ** 2
  t36 = 0.1e1 / t14 / t1
  t43 = t13 ** 2
  d11 = -0.13375600000000000000000000000000000000000000000000e-2 * t7 * t9 - 0.622e-1 * t20 * t3 + t1 * (-0.25056957333333333333333333333333333333333333333333e-4 / t6 / t5 / t14 / t25 + 0.89170666666666666666666666666666666666666666666665e-3 * t7 / t2 / t25 - 0.311e-1 * (0.2e1 / 0.9e1 / t25 - 0.2e1 / 0.9e1 * t13 * t36) * t19 * t3 - 0.10366666666666666666666666666666666666666666666667e-1 * t18 / t43 * t36 + 0.10366666666666666666666666666666666666666666666667e-1 * t20 * t9)
  d12 = d11
  d22 = d12
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / t1
  t4 = 0.1e1 + 0.56200000000000000000000000000000000000000000000000e-1 * t2
  t5 = t4 ** 2
  t6 = 0.1e1 / t5
  t8 = 0.1e1 / t1 / r0
  t12 = t2 + 0.239e1
  t13 = t1 ** 2
  t17 = -0.1e1 / r0 / 0.3e1 + t12 / t13 / 0.3e1
  t18 = 0.1e1 / t12
  t19 = t17 * t18
  t24 = r0 ** 2
  t35 = 0.1e1 / t13 / r0
  t42 = t12 ** 2
  v2rho2_0_ = -0.13375600000000000000000000000000000000000000000000e-2 * t6 * t8 - 0.622e-1 * t19 * t2 + r0 * (-0.25056957333333333333333333333333333333333333333333e-4 / t5 / t4 / t13 / t24 + 0.89170666666666666666666666666666666666666666666665e-3 * t6 / t1 / t24 - 0.311e-1 * (0.2e1 / 0.9e1 / t24 - 0.2e1 / 0.9e1 * t12 * t35) * t18 * t2 - 0.10366666666666666666666666666666666666666666666667e-1 * t17 / t42 * t35 + 0.10366666666666666666666666666666666666666666666667e-1 * t19 * t8)
  res = {'v2rho2': v2rho2_0_}
  return res
