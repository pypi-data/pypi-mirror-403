"""Generated from lda_c_1d_csc.mpl."""

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
  params_ferro_raw = params.ferro
  if isinstance(params_ferro_raw, (str, bytes, dict)):
    params_ferro = params_ferro_raw
  else:
    try:
      params_ferro_seq = list(params_ferro_raw)
    except TypeError:
      params_ferro = params_ferro_raw
    else:
      params_ferro_seq = np.asarray(params_ferro_seq, dtype=np.float64)
      params_ferro = np.concatenate((np.array([np.nan], dtype=np.float64), params_ferro_seq))
  params_para_raw = params.para
  if isinstance(params_para_raw, (str, bytes, dict)):
    params_para = params_para_raw
  else:
    try:
      params_para_seq = list(params_para_raw)
    except TypeError:
      params_para = params_para_raw
    else:
      params_para_seq = np.asarray(params_para_seq, dtype=np.float64)
      params_para = np.concatenate((np.array([np.nan], dtype=np.float64), params_para_seq))

  f_aux = lambda a, rs: -(rs + a[5] * rs ** 2) * jnp.log(1 + a[8] * rs + a[9] * rs ** a[10]) / (2 * (a[1] + a[2] * rs + a[3] * rs ** a[6] + a[4] * rs ** a[7]))

  functional_body = lambda rs, z: f_aux(params_para, rs) + (f_aux(params_ferro, rs) - f_aux(params_para, rs)) * z ** 2

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res


def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_ferro_raw = params.ferro
  if isinstance(params_ferro_raw, (str, bytes, dict)):
    params_ferro = params_ferro_raw
  else:
    try:
      params_ferro_seq = list(params_ferro_raw)
    except TypeError:
      params_ferro = params_ferro_raw
    else:
      params_ferro_seq = np.asarray(params_ferro_seq, dtype=np.float64)
      params_ferro = np.concatenate((np.array([np.nan], dtype=np.float64), params_ferro_seq))
  params_para_raw = params.para
  if isinstance(params_para_raw, (str, bytes, dict)):
    params_para = params_para_raw
  else:
    try:
      params_para_seq = list(params_para_raw)
    except TypeError:
      params_para = params_para_raw
    else:
      params_para_seq = np.asarray(params_para_seq, dtype=np.float64)
      params_para = np.concatenate((np.array([np.nan], dtype=np.float64), params_para_seq))

  f_aux = lambda a, rs: -(rs + a[5] * rs ** 2) * jnp.log(1 + a[8] * rs + a[9] * rs ** a[10]) / (2 * (a[1] + a[2] * rs + a[3] * rs ** a[6] + a[4] * rs ** a[7]))

  functional_body = lambda rs, z: f_aux(params_para, rs) + (f_aux(params_ferro, rs) - f_aux(params_para, rs)) * z ** 2

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
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 + r1
  t8 = t7 ** (0.1e1 / 0.3e1)
  t9 = 0.1e1 / t8
  t11 = t4 * t6 * t9
  t13 = t1 ** 2
  t14 = params.para[4] * t13
  t15 = t3 ** 2
  t16 = t15 * t5
  t17 = t8 ** 2
  t19 = t16 / t17
  t22 = t14 * t19 / 0.4e1 + t11 / 0.4e1
  t24 = params.para[7] * t1
  t25 = t3 * t6
  t26 = t25 * t9
  t30 = t11 / 0.4e1
  t31 = params.para[9]
  t32 = t30 ** t31
  t33 = params.para[8] * t32
  t34 = 0.1e1 + t24 * t26 / 0.4e1 + t33
  t35 = jnp.log(t34)
  t36 = t22 * t35
  t40 = params.para[1] * t1
  t44 = params.para[5]
  t45 = t30 ** t44
  t46 = params.para[2] * t45
  t49 = params.para[6]
  t50 = t30 ** t49
  t51 = params.para[3] * t50
  t53 = 0.2e1 * params.para[0] + t40 * t26 / 0.2e1 + 0.2e1 * t46 + 0.2e1 * t51
  t54 = 0.1e1 / t53
  t55 = t36 * t54
  t57 = params.ferro[4] * t13
  t60 = t57 * t19 / 0.4e1 + t11 / 0.4e1
  t62 = params.ferro[7] * t1
  t66 = params.ferro[9]
  t67 = t30 ** t66
  t68 = params.ferro[8] * t67
  t69 = 0.1e1 + t62 * t26 / 0.4e1 + t68
  t70 = jnp.log(t69)
  t71 = t60 * t70
  t75 = params.ferro[1] * t1
  t79 = params.ferro[5]
  t80 = t30 ** t79
  t81 = params.ferro[2] * t80
  t84 = params.ferro[6]
  t85 = t30 ** t84
  t86 = params.ferro[3] * t85
  t88 = 0.2e1 * params.ferro[0] + t75 * t26 / 0.2e1 + 0.2e1 * t81 + 0.2e1 * t86
  t89 = 0.1e1 / t88
  t91 = -t71 * t89 + t55
  t92 = r0 - r1
  t93 = t92 ** 2
  t94 = t91 * t93
  t95 = t7 ** 2
  t96 = 0.1e1 / t95
  t97 = t94 * t96
  t99 = 0.1e1 / t8 / t7
  t102 = t4 * t6 * t99 / 0.12e2
  t105 = t16 / t17 / t7
  t110 = (-t102 - t14 * t105 / 0.6e1) * t35 * t54
  t111 = t25 * t99
  t114 = 0.1e1 / t7
  t122 = t22 * (-t24 * t111 / 0.12e2 - t33 * t31 * t114 / 0.3e1) / t34 * t54
  t123 = t53 ** 2
  t135 = t36 / t123 * (-t40 * t111 / 0.6e1 - 0.2e1 / 0.3e1 * t46 * t44 * t114 - 0.2e1 / 0.3e1 * t51 * t49 * t114)
  t151 = t88 ** 2
  t166 = (-(-t102 - t57 * t105 / 0.6e1) * t70 * t89 - t60 * (-t62 * t111 / 0.12e2 - t68 * t66 * t114 / 0.3e1) / t69 * t89 + t71 / t151 * (-t75 * t111 / 0.6e1 - 0.2e1 / 0.3e1 * t81 * t79 * t114 - 0.2e1 / 0.3e1 * t86 * t84 * t114) + t110 + t122 - t135) * t93 * t96
  t169 = 0.2e1 * t91 * t92 * t96
  t173 = 0.2e1 * t94 / t95 / t7
  vrho_0_ = -t55 + t97 + t7 * (-t110 - t122 + t135 + t166 + t169 - t173)
  vrho_1_ = -t55 + t97 + t7 * (-t110 - t122 + t135 + t166 - t169 - t173)

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 3 ** (0.1e1 / 0.3e1)
  t3 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t4 = t1 * t3
  t5 = 4 ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t7 = r0 ** (0.1e1 / 0.3e1)
  t8 = 0.1e1 / t7
  t10 = t4 * t6 * t8
  t12 = t1 ** 2
  t13 = params.para[4] * t12
  t14 = t3 ** 2
  t15 = t14 * t5
  t16 = t7 ** 2
  t21 = t10 / 0.4e1 + t13 * t15 / t16 / 0.4e1
  t23 = params.para[7] * t1
  t24 = t3 * t6
  t25 = t24 * t8
  t29 = t10 / 0.4e1
  t30 = params.para[9]
  t31 = t29 ** t30
  t32 = params.para[8] * t31
  t33 = 0.1e1 + t23 * t25 / 0.4e1 + t32
  t34 = jnp.log(t33)
  t39 = params.para[1] * t1
  t43 = params.para[5]
  t44 = t29 ** t43
  t45 = params.para[2] * t44
  t48 = params.para[6]
  t49 = t29 ** t48
  t50 = params.para[3] * t49
  t52 = 0.2e1 * params.para[0] + t39 * t25 / 0.2e1 + 0.2e1 * t45 + 0.2e1 * t50
  t53 = 0.1e1 / t52
  t56 = 0.1e1 / t7 / r0
  t69 = r0 * t21
  t70 = t24 * t56
  t73 = 0.1e1 / r0
  t82 = t52 ** 2
  vrho_0_ = -t21 * t34 * t53 - r0 * (-t4 * t6 * t56 / 0.12e2 - t13 * t15 / t16 / r0 / 0.6e1) * t34 * t53 - t69 * (-t23 * t70 / 0.12e2 - t32 * t30 * t73 / 0.3e1) / t33 * t53 + t69 * t34 / t82 * (-t39 * t70 / 0.6e1 - 0.2e1 / 0.3e1 * t45 * t43 * t73 - 0.2e1 / 0.3e1 * t50 * t48 * t73)

  res = {'vrho': vrho_0_}
  return res
