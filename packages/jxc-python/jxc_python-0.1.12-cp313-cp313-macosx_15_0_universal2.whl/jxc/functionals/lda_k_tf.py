"""Generated from lda_k_tf.mpl."""

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
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))

  f_zeta_k = lambda z: 1 / 2 * (f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3))

  functional_body = lambda rs, zeta: params_ax * f_zeta_k(zeta) / rs ** 2

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))

  f_zeta_k = lambda z: 1 / 2 * (f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3))

  functional_body = lambda rs, zeta: params_ax * f_zeta_k(zeta) / rs ** 2

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))

  f_zeta_k = lambda z: 1 / 2 * (f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3))

  functional_body = lambda rs, zeta: params_ax * f_zeta_k(zeta) / rs ** 2

  t1 = r0 - r1
  t2 = r0 + r1
  t3 = 0.1e1 / t2
  t4 = t1 * t3
  t5 = 0.1e1 + t4
  t6 = t5 <= f.p.zeta_threshold
  t7 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t9 = t8 * f.p.zeta_threshold
  t10 = t5 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t13 = f.my_piecewise3(t6, t9, t11 * t5)
  t14 = 0.1e1 - t4
  t15 = t14 <= f.p.zeta_threshold
  t16 = t14 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  t19 = f.my_piecewise3(t15, t9, t17 * t14)
  t23 = 3 ** (0.1e1 / 0.3e1)
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t32 = t2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t36 = 0.5e1 / 0.9e1 * params.ax * (t13 / 0.2e1 + t19 / 0.2e1) * t23 * t28 * t30 * t33
  t38 = t33 * t2 * params.ax
  t39 = t2 ** 2
  t41 = t1 / t39
  t42 = t3 - t41
  t45 = f.my_piecewise3(t6, 0, 0.5e1 / 0.3e1 * t11 * t42)
  t49 = f.my_piecewise3(t15, 0, -0.5e1 / 0.3e1 * t17 * t42)
  t54 = t23 * t28 * t30
  vrho_0_ = t36 + t38 * (t45 / 0.2e1 + t49 / 0.2e1) * t54 / 0.3e1
  t57 = -t3 - t41
  t60 = f.my_piecewise3(t6, 0, 0.5e1 / 0.3e1 * t11 * t57)
  t64 = f.my_piecewise3(t15, 0, -0.5e1 / 0.3e1 * t17 * t57)
  vrho_1_ = t36 + t38 * (t60 / 0.2e1 + t64 / 0.2e1) * t54 / 0.3e1
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_ax_raw = params.ax
  if isinstance(params_ax_raw, (str, bytes, dict)):
    params_ax = params_ax_raw
  else:
    try:
      params_ax_seq = list(params_ax_raw)
    except TypeError:
      params_ax = params_ax_raw
    else:
      params_ax_seq = np.asarray(params_ax_seq, dtype=np.float64)
      params_ax = np.concatenate((np.array([np.nan], dtype=np.float64), params_ax_seq))

  f_zeta_k = lambda z: 1 / 2 * (f.opz_pow_n(z, 5 / 3) + f.opz_pow_n(-z, 5 / 3))

  functional_body = lambda rs, zeta: params_ax * f_zeta_k(zeta) / rs ** 2

  t2 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t5 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t3 * f.p.zeta_threshold, 1)
  t7 = 3 ** (0.1e1 / 0.3e1)
  t10 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t13 = 4 ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t16 = r0 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  vrho_0_ = 0.5e1 / 0.9e1 * params.ax * t5 * t7 / t11 * t14 * t17
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = r0 ** (0.1e1 / 0.3e1)
  t5 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t6 = t5 ** 2
  t8 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t6 * f.p.zeta_threshold, 1)
  t10 = 3 ** (0.1e1 / 0.3e1)
  t12 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t13 = t12 ** 2
  t16 = 4 ** (0.1e1 / 0.3e1)
  t17 = t16 ** 2
  v2rho2_0_ = 0.10e2 / 0.27e2 / t1 * params.ax * t8 * t10 / t13 * t17
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** (0.1e1 / 0.3e1)
  t6 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t7 = t6 ** 2
  t9 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t7 * f.p.zeta_threshold, 1)
  t11 = 3 ** (0.1e1 / 0.3e1)
  t13 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  v3rho3_0_ = -0.10e2 / 0.81e2 / t1 / r0 * params.ax * t9 * t11 / t14 * t18

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** 2
  t2 = r0 ** (0.1e1 / 0.3e1)
  t7 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t8 = t7 ** 2
  t10 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t8 * f.p.zeta_threshold, 1)
  t12 = 3 ** (0.1e1 / 0.3e1)
  t14 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t18 = 4 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  v4rho4_0_ = 0.40e2 / 0.243e3 / t2 / t1 * params.ax * t10 * t12 / t15 * t19

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t5 = r0 - r1
  t6 = 0.1e1 / t1
  t7 = t5 * t6
  t8 = 0.1e1 + t7
  t9 = t8 <= f.p.zeta_threshold
  t10 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = t11 * f.p.zeta_threshold
  t13 = t8 ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t16 = f.my_piecewise3(t9, t12, t14 * t8)
  t17 = 0.1e1 - t7
  t18 = t17 <= f.p.zeta_threshold
  t19 = t17 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = f.my_piecewise3(t18, t12, t20 * t17)
  t26 = 3 ** (0.1e1 / 0.3e1)
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t32 = 4 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = t26 / t29 * t33
  t36 = 0.10e2 / 0.27e2 / t2 * params.ax * (t16 / 0.2e1 + t22 / 0.2e1) * t34
  t37 = t2 ** 2
  t38 = t37 * params.ax
  t39 = t1 ** 2
  t40 = 0.1e1 / t39
  t41 = t5 * t40
  t42 = t6 - t41
  t45 = f.my_piecewise3(t9, 0, 0.5e1 / 0.3e1 * t14 * t42)
  t46 = -t42
  t49 = f.my_piecewise3(t18, 0, 0.5e1 / 0.3e1 * t20 * t46)
  t53 = t38 * (t45 / 0.2e1 + t49 / 0.2e1) * t34
  t56 = t37 * t1 * params.ax
  t57 = 0.1e1 / t13
  t58 = t42 ** 2
  t62 = 0.1e1 / t39 / t1
  t63 = t5 * t62
  t65 = -0.2e1 * t40 + 0.2e1 * t63
  t69 = f.my_piecewise3(t9, 0, 0.10e2 / 0.9e1 * t57 * t58 + 0.5e1 / 0.3e1 * t14 * t65)
  t70 = 0.1e1 / t19
  t71 = t46 ** 2
  t78 = f.my_piecewise3(t18, 0, 0.10e2 / 0.9e1 * t70 * t71 - 0.5e1 / 0.3e1 * t20 * t65)
  d11 = t36 + 0.10e2 / 0.9e1 * t53 + t56 * (t69 / 0.2e1 + t78 / 0.2e1) * t34 / 0.3e1
  t85 = -t6 - t41
  t88 = f.my_piecewise3(t9, 0, 0.5e1 / 0.3e1 * t14 * t85)
  t89 = -t85
  t92 = f.my_piecewise3(t18, 0, 0.5e1 / 0.3e1 * t20 * t89)
  t96 = t38 * (t88 / 0.2e1 + t92 / 0.2e1) * t34
  t105 = f.my_piecewise3(t9, 0, 0.10e2 / 0.9e1 * t57 * t85 * t42 + 0.10e2 / 0.3e1 * t14 * t5 * t62)
  t113 = f.my_piecewise3(t18, 0, 0.10e2 / 0.9e1 * t70 * t89 * t46 - 0.10e2 / 0.3e1 * t20 * t5 * t62)
  d12 = t36 + 0.5e1 / 0.9e1 * t53 + 0.5e1 / 0.9e1 * t96 + t56 * (t105 / 0.2e1 + t113 / 0.2e1) * t34 / 0.3e1
  t120 = t85 ** 2
  t124 = 0.2e1 * t40 + 0.2e1 * t63
  t128 = f.my_piecewise3(t9, 0, 0.10e2 / 0.9e1 * t57 * t120 + 0.5e1 / 0.3e1 * t14 * t124)
  t129 = t89 ** 2
  t136 = f.my_piecewise3(t18, 0, 0.10e2 / 0.9e1 * t70 * t129 - 0.5e1 / 0.3e1 * t20 * t124)
  d22 = t36 + 0.10e2 / 0.9e1 * t96 + t56 * (t128 / 0.2e1 + t136 / 0.2e1) * t34 / 0.3e1
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t6 = r0 - r1
  t7 = 0.1e1 / t1
  t8 = t6 * t7
  t9 = 0.1e1 + t8
  t10 = t9 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t13 = t12 * f.p.zeta_threshold
  t14 = t9 ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = f.my_piecewise3(t10, t13, t15 * t9)
  t18 = 0.1e1 - t8
  t19 = t18 <= f.p.zeta_threshold
  t20 = t18 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = f.my_piecewise3(t19, t13, t21 * t18)
  t27 = 3 ** (0.1e1 / 0.3e1)
  t29 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = t27 / t30 * t34
  t40 = t1 ** 2
  t41 = 0.1e1 / t40
  t43 = -t6 * t41 + t7
  t46 = f.my_piecewise3(t10, 0, 0.5e1 / 0.3e1 * t15 * t43)
  t47 = -t43
  t50 = f.my_piecewise3(t19, 0, 0.5e1 / 0.3e1 * t21 * t47)
  t56 = t2 ** 2
  t58 = 0.1e1 / t14
  t59 = t43 ** 2
  t63 = 0.1e1 / t40 / t1
  t66 = 0.2e1 * t6 * t63 - 0.2e1 * t41
  t70 = f.my_piecewise3(t10, 0, 0.10e2 / 0.9e1 * t58 * t59 + 0.5e1 / 0.3e1 * t15 * t66)
  t71 = 0.1e1 / t20
  t72 = t47 ** 2
  t75 = -t66
  t79 = f.my_piecewise3(t19, 0, 0.10e2 / 0.9e1 * t71 * t72 + 0.5e1 / 0.3e1 * t21 * t75)
  t95 = t40 ** 2
  t99 = 0.6e1 * t63 - 0.6e1 * t6 / t95
  t103 = f.my_piecewise3(t10, 0, -0.10e2 / 0.27e2 / t14 / t9 * t59 * t43 + 0.10e2 / 0.3e1 * t58 * t43 * t66 + 0.5e1 / 0.3e1 * t15 * t99)
  t116 = f.my_piecewise3(t19, 0, -0.10e2 / 0.27e2 / t20 / t18 * t72 * t47 + 0.10e2 / 0.3e1 * t71 * t47 * t75 - 0.5e1 / 0.3e1 * t21 * t99)
  d111 = -0.10e2 / 0.81e2 / t2 / t1 * params.ax * (t17 / 0.2e1 + t23 / 0.2e1) * t35 + 0.10e2 / 0.9e1 / t2 * params.ax * (t46 / 0.2e1 + t50 / 0.2e1) * t35 + 0.5e1 / 0.3e1 * t56 * params.ax * (t70 / 0.2e1 + t79 / 0.2e1) * t35 + t56 * t1 * params.ax * (t103 / 0.2e1 + t116 / 0.2e1) * t35 / 0.3e1

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 + r1
  t2 = t1 ** 2
  t3 = t1 ** (0.1e1 / 0.3e1)
  t7 = r0 - r1
  t8 = 0.1e1 / t1
  t9 = t7 * t8
  t10 = 0.1e1 + t9
  t11 = t10 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t12 ** 2
  t14 = t13 * f.p.zeta_threshold
  t15 = t10 ** (0.1e1 / 0.3e1)
  t16 = t15 ** 2
  t18 = f.my_piecewise3(t11, t14, t16 * t10)
  t19 = 0.1e1 - t9
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t24 = f.my_piecewise3(t20, t14, t22 * t19)
  t28 = 3 ** (0.1e1 / 0.3e1)
  t30 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = t28 / t31 * t35
  t42 = 0.1e1 / t2
  t44 = -t7 * t42 + t8
  t47 = f.my_piecewise3(t11, 0, 0.5e1 / 0.3e1 * t16 * t44)
  t48 = -t44
  t51 = f.my_piecewise3(t20, 0, 0.5e1 / 0.3e1 * t22 * t48)
  t59 = 0.1e1 / t15
  t60 = t44 ** 2
  t64 = 0.1e1 / t2 / t1
  t67 = 0.2e1 * t7 * t64 - 0.2e1 * t42
  t71 = f.my_piecewise3(t11, 0, 0.10e2 / 0.9e1 * t59 * t60 + 0.5e1 / 0.3e1 * t16 * t67)
  t72 = 0.1e1 / t21
  t73 = t48 ** 2
  t76 = -t67
  t80 = f.my_piecewise3(t20, 0, 0.10e2 / 0.9e1 * t72 * t73 + 0.5e1 / 0.3e1 * t22 * t76)
  t86 = t3 ** 2
  t89 = 0.1e1 / t15 / t10
  t93 = t59 * t44
  t96 = t2 ** 2
  t97 = 0.1e1 / t96
  t100 = -0.6e1 * t7 * t97 + 0.6e1 * t64
  t104 = f.my_piecewise3(t11, 0, -0.10e2 / 0.27e2 * t89 * t60 * t44 + 0.10e2 / 0.3e1 * t93 * t67 + 0.5e1 / 0.3e1 * t16 * t100)
  t106 = 0.1e1 / t21 / t19
  t110 = t72 * t48
  t113 = -t100
  t117 = f.my_piecewise3(t20, 0, -0.10e2 / 0.27e2 * t106 * t73 * t48 + 0.10e2 / 0.3e1 * t110 * t76 + 0.5e1 / 0.3e1 * t22 * t113)
  t125 = t10 ** 2
  t128 = t60 ** 2
  t134 = t67 ** 2
  t143 = -0.24e2 * t97 + 0.24e2 * t7 / t96 / t1
  t147 = f.my_piecewise3(t11, 0, 0.40e2 / 0.81e2 / t15 / t125 * t128 - 0.20e2 / 0.9e1 * t89 * t60 * t67 + 0.10e2 / 0.3e1 * t59 * t134 + 0.40e2 / 0.9e1 * t93 * t100 + 0.5e1 / 0.3e1 * t16 * t143)
  t148 = t19 ** 2
  t151 = t73 ** 2
  t157 = t76 ** 2
  t166 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t21 / t148 * t151 - 0.20e2 / 0.9e1 * t106 * t73 * t76 + 0.10e2 / 0.3e1 * t72 * t157 + 0.40e2 / 0.9e1 * t110 * t113 - 0.5e1 / 0.3e1 * t22 * t143)
  d1111 = 0.40e2 / 0.243e3 / t3 / t2 * params.ax * (t18 / 0.2e1 + t24 / 0.2e1) * t36 - 0.40e2 / 0.81e2 / t3 / t1 * params.ax * (t47 / 0.2e1 + t51 / 0.2e1) * t36 + 0.20e2 / 0.9e1 / t3 * params.ax * (t71 / 0.2e1 + t80 / 0.2e1) * t36 + 0.20e2 / 0.9e1 * t86 * params.ax * (t104 / 0.2e1 + t117 / 0.2e1) * t36 + t86 * t1 * params.ax * (t147 / 0.2e1 + t166 / 0.2e1) * t36 / 0.3e1

  res = {'v4rho4': d1111}
  return res
