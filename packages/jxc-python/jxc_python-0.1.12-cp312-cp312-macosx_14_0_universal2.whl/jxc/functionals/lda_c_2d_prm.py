"""Generated from lda_c_2d_prm.mpl."""

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
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))

  prm_q = 3.9274

  beta = lambda rs: prm_q / (jnp.sqrt(jnp.pi) * rs)

  phi = lambda rs: beta(rs) / (beta(rs) + jnp.sqrt(jnp.pi) / 2)

  f0 = lambda rs: +jnp.sqrt(jnp.pi) * beta(rs) * (phi(rs) - 1) / (2 * jnp.sqrt(2 + params_c)) + phi(rs) * (phi(rs) - 1) / (2 + params_c) + jnp.sqrt(jnp.pi) * phi(rs) * phi(rs) / (4 * beta(rs) * (2 + params_c) ** 1.5) + jnp.sqrt(jnp.pi) * beta(rs) * (phi(rs) - 1) / jnp.sqrt(1 + params_c) + phi(rs) / (1 + params_c)

  functional_body = lambda rs, z=None: f0(rs) * jnp.pi / (2 * prm_q * prm_q)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res


def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))

  prm_q = 3.9274

  beta = lambda rs: prm_q / (jnp.sqrt(jnp.pi) * rs)

  phi = lambda rs: beta(rs) / (beta(rs) + jnp.sqrt(jnp.pi) / 2)

  f0 = lambda rs: +jnp.sqrt(jnp.pi) * beta(rs) * (phi(rs) - 1) / (2 * jnp.sqrt(2 + params_c)) + phi(rs) * (phi(rs) - 1) / (2 + params_c) + jnp.sqrt(jnp.pi) * phi(rs) * phi(rs) / (4 * beta(rs) * (2 + params_c) ** 1.5) + jnp.sqrt(jnp.pi) * beta(rs) * (phi(rs) - 1) / jnp.sqrt(1 + params_c) + phi(rs) / (1 + params_c)

  functional_body = lambda rs, z=None: f0(rs) * jnp.pi / (2 * prm_q * prm_q)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t3 = 0.1e1 / jnp.pi
  t4 = t3 ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = t2 * t5 * t7
  t9 = r0 + r1
  t10 = t9 ** (0.1e1 / 0.3e1)
  t11 = jnp.sqrt(jnp.pi)
  t12 = 0.1e1 / t11
  t13 = t12 * t2
  t14 = t13 * t5
  t15 = t7 * t10
  t16 = t5 * t7
  t21 = 0.13091333333333333333333333333333333333333333333333e1 * t13 * t16 * t10 + t11 / 0.2e1
  t22 = 0.1e1 / t21
  t26 = 0.13091333333333333333333333333333333333333333333333e1 * t14 * t15 * t22 - 0.1e1
  t27 = t10 * t26
  t28 = 0.2e1 + params.c
  t29 = jnp.sqrt(t28)
  t30 = 0.1e1 / t29
  t34 = t13 * t16
  t35 = t10 * t22
  t36 = 0.1e1 / t28
  t37 = t26 * t36
  t41 = t21 ** 2
  t42 = 0.1e1 / t41
  t44 = t28 ** (-0.15e1)
  t48 = 0.1e1 + params.c
  t49 = jnp.sqrt(t48)
  t50 = 0.1e1 / t49
  t54 = 0.1e1 / t48
  t55 = t22 * t54
  t62 = t10 ** 2
  t63 = 0.1e1 / t62
  t64 = t63 * t26
  t68 = t7 * t63
  t72 = t3 * t1
  t73 = t4 ** 2
  t74 = 0.1e1 / t73
  t75 = t72 * t74
  t76 = t7 ** 2
  t77 = 0.1e1 / t10
  t78 = t76 * t77
  t82 = 0.43637777777777777777777777777777777777777777777777e0 * t14 * t68 * t22 - 0.17138300844444444444444444444444444444444444444444e1 * t75 * t78 * t42
  t83 = t10 * t82
  t127 = 0.21818888888888888888888888888888888888888888888888e0 * t8 * t64 * t30 + 0.65456666666666666666666666666666666666666666666665e0 * t8 * t83 * t30 + 0.43637777777777777777777777777777777777777777777777e0 * t34 * t63 * t22 * t37 - 0.17138300844444444444444444444444444444444444444444e1 * t72 * t74 * t76 * t77 * t42 * t37 + 0.13091333333333333333333333333333333333333333333333e1 * t34 * t35 * t82 * t36 + 0.10909444444444444444444444444444444444444444444444e0 * t8 * t63 * t42 * t44 - 0.85691504222222222222222222222222222222222222222217e0 * t1 * t74 * t76 * t77 / t41 / t21 * t44 * t12 + 0.43637777777777777777777777777777777777777777777777e0 * t8 * t64 * t50 + 0.13091333333333333333333333333333333333333333333333e1 * t8 * t83 * t50 + 0.43637777777777777777777777777777777777777777777777e0 * t14 * t68 * t55 - 0.17138300844444444444444444444444444444444444444444e1 * t75 * t78 * t42 * t54
  vrho_0_ = 0.32416023070084253574739831138297026406369874048113e-1 * (0.65456666666666666666666666666666666666666666666665e0 * t8 * t27 * t30 + 0.13091333333333333333333333333333333333333333333333e1 * t34 * t35 * t37 + 0.32728333333333333333333333333333333333333333333332e0 * t8 * t10 * t42 * t44 + 0.13091333333333333333333333333333333333333333333333e1 * t8 * t27 * t50 + 0.13091333333333333333333333333333333333333333333333e1 * t14 * t15 * t55) * jnp.pi + 0.32416023070084253574739831138297026406369874048113e-1 * t9 * t127 * jnp.pi
  vrho_1_ = vrho_0_

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t2 = t1 ** 2
  t3 = 0.1e1 / jnp.pi
  t4 = t3 ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t7 = 4 ** (0.1e1 / 0.3e1)
  t8 = t2 * t5 * t7
  t9 = r0 ** (0.1e1 / 0.3e1)
  t10 = jnp.sqrt(jnp.pi)
  t11 = 0.1e1 / t10
  t12 = t11 * t2
  t13 = t12 * t5
  t14 = t7 * t9
  t15 = t5 * t7
  t20 = 0.13091333333333333333333333333333333333333333333333e1 * t12 * t15 * t9 + t10 / 0.2e1
  t21 = 0.1e1 / t20
  t25 = 0.13091333333333333333333333333333333333333333333333e1 * t13 * t14 * t21 - 0.1e1
  t26 = t9 * t25
  t27 = 0.2e1 + params.c
  t28 = jnp.sqrt(t27)
  t29 = 0.1e1 / t28
  t33 = t12 * t15
  t34 = t9 * t21
  t35 = 0.1e1 / t27
  t36 = t25 * t35
  t40 = t20 ** 2
  t41 = 0.1e1 / t40
  t43 = t27 ** (-0.15e1)
  t47 = 0.1e1 + params.c
  t48 = jnp.sqrt(t47)
  t49 = 0.1e1 / t48
  t53 = 0.1e1 / t47
  t54 = t21 * t53
  t61 = t9 ** 2
  t62 = 0.1e1 / t61
  t63 = t62 * t25
  t67 = t7 * t62
  t71 = t3 * t1
  t72 = t4 ** 2
  t73 = 0.1e1 / t72
  t74 = t71 * t73
  t75 = t7 ** 2
  t76 = 0.1e1 / t9
  t77 = t75 * t76
  t81 = 0.43637777777777777777777777777777777777777777777777e0 * t13 * t67 * t21 - 0.17138300844444444444444444444444444444444444444444e1 * t74 * t77 * t41
  t82 = t9 * t81
  t126 = 0.21818888888888888888888888888888888888888888888888e0 * t8 * t63 * t29 + 0.65456666666666666666666666666666666666666666666665e0 * t8 * t82 * t29 + 0.43637777777777777777777777777777777777777777777777e0 * t33 * t62 * t21 * t36 - 0.17138300844444444444444444444444444444444444444444e1 * t71 * t73 * t75 * t76 * t41 * t36 + 0.13091333333333333333333333333333333333333333333333e1 * t33 * t34 * t81 * t35 + 0.10909444444444444444444444444444444444444444444444e0 * t8 * t62 * t41 * t43 - 0.85691504222222222222222222222222222222222222222217e0 * t1 * t73 * t75 * t76 / t40 / t20 * t43 * t11 + 0.43637777777777777777777777777777777777777777777777e0 * t8 * t63 * t49 + 0.13091333333333333333333333333333333333333333333333e1 * t8 * t82 * t49 + 0.43637777777777777777777777777777777777777777777777e0 * t13 * t67 * t54 - 0.17138300844444444444444444444444444444444444444444e1 * t74 * t77 * t41 * t53
  vrho_0_ = 0.32416023070084253574739831138297026406369874048113e-1 * (0.65456666666666666666666666666666666666666666666665e0 * t8 * t26 * t29 + 0.13091333333333333333333333333333333333333333333333e1 * t33 * t34 * t36 + 0.32728333333333333333333333333333333333333333333332e0 * t8 * t9 * t41 * t43 + 0.13091333333333333333333333333333333333333333333333e1 * t8 * t26 * t49 + 0.13091333333333333333333333333333333333333333333333e1 * t13 * t14 * t54) * jnp.pi + 0.32416023070084253574739831138297026406369874048113e-1 * r0 * t126 * jnp.pi

  res = {'vrho': vrho_0_}
  return res
