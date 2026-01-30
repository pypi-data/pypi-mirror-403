"""Generated from gga_x_kt.mpl."""

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
  params_delta_raw = params.delta
  if isinstance(params_delta_raw, (str, bytes, dict)):
    params_delta = params_delta_raw
  else:
    try:
      params_delta_seq = list(params_delta_raw)
    except TypeError:
      params_delta = params_delta_raw
    else:
      params_delta_seq = np.asarray(params_delta_seq, dtype=np.float64)
      params_delta = np.concatenate((np.array([np.nan], dtype=np.float64), params_delta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  kt_fx = lambda rs, z, xs: 1 - params_gamma / X_FACTOR_C * f.n_spin(rs, z) ** (4 / 3) * xs ** 2 / (f.n_spin(rs, z) ** (4 / 3) + params_delta)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, kt_fx, rs, zeta, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_delta_raw = params.delta
  if isinstance(params_delta_raw, (str, bytes, dict)):
    params_delta = params_delta_raw
  else:
    try:
      params_delta_seq = list(params_delta_raw)
    except TypeError:
      params_delta = params_delta_raw
    else:
      params_delta_seq = np.asarray(params_delta_seq, dtype=np.float64)
      params_delta = np.concatenate((np.array([np.nan], dtype=np.float64), params_delta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  kt_fx = lambda rs, z, xs: 1 - params_gamma / X_FACTOR_C * f.n_spin(rs, z) ** (4 / 3) * xs ** 2 / (f.n_spin(rs, z) ** (4 / 3) + params_delta)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, kt_fx, rs, zeta, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_delta_raw = params.delta
  if isinstance(params_delta_raw, (str, bytes, dict)):
    params_delta = params_delta_raw
  else:
    try:
      params_delta_seq = list(params_delta_raw)
    except TypeError:
      params_delta = params_delta_raw
    else:
      params_delta_seq = np.asarray(params_delta_seq, dtype=np.float64)
      params_delta = np.concatenate((np.array([np.nan], dtype=np.float64), params_delta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  kt_fx = lambda rs, z, xs: 1 - params_gamma / X_FACTOR_C * f.n_spin(rs, z) ** (4 / 3) * xs ** 2 / (f.n_spin(rs, z) ** (4 / 3) + params_delta)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, kt_fx, rs, zeta, xs0, xs1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t20, t22, t23 * t19)
  t26 = t6 ** (0.1e1 / 0.3e1)
  t27 = t25 * t26
  t28 = t2 ** 2
  t29 = params.gamma * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t35 = t29 * t34
  t36 = 2 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t38 = t19 * t6
  t39 = t38 ** (0.1e1 / 0.3e1)
  t40 = t39 * t38
  t41 = t37 * t40
  t42 = r0 ** 2
  t43 = r0 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t46 = 0.1e1 / t44 / t42
  t49 = t41 / 0.4e1 + params.delta
  t50 = 0.1e1 / t49
  t55 = 0.1e1 - t35 * t41 * s0 * t46 * t50 / 0.18e2
  t59 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t55)
  t60 = r1 <= f.p.dens_threshold
  t61 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t62 = 0.1e1 + t61
  t63 = t62 <= f.p.zeta_threshold
  t64 = t62 ** (0.1e1 / 0.3e1)
  t66 = f.my_piecewise3(t63, t22, t64 * t62)
  t67 = t66 * t26
  t68 = t62 * t6
  t69 = t68 ** (0.1e1 / 0.3e1)
  t70 = t69 * t68
  t71 = t37 * t70
  t72 = r1 ** 2
  t73 = r1 ** (0.1e1 / 0.3e1)
  t74 = t73 ** 2
  t76 = 0.1e1 / t74 / t72
  t79 = t71 / 0.4e1 + params.delta
  t80 = 0.1e1 / t79
  t85 = 0.1e1 - t35 * t71 * s2 * t76 * t80 / 0.18e2
  t89 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t67 * t85)
  t90 = t6 ** 2
  t92 = t16 / t90
  t93 = t7 - t92
  t94 = f.my_piecewise5(t10, 0, t14, 0, t93)
  t97 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t94)
  t102 = t26 ** 2
  t103 = 0.1e1 / t102
  t107 = t5 * t25 * t103 * t55 / 0.8e1
  t109 = t29 * t34 * t37
  t110 = t39 * s0
  t111 = t46 * t50
  t113 = t94 * t6 + t18 + 0.1e1
  t127 = t29 * t34 * t36
  t128 = t39 ** 2
  t130 = t128 * t38 * s0
  t131 = t49 ** 2
  t133 = t46 / t131
  t143 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t97 * t26 * t55 - t107 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.2e1 / 0.27e2 * t109 * t110 * t111 * t113 + 0.4e1 / 0.27e2 * t35 * t41 * s0 / t44 / t42 / r0 * t50 + t127 * t130 * t133 * t113 / 0.27e2))
  t145 = f.my_piecewise5(t14, 0, t10, 0, -t93)
  t148 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t145)
  t156 = t5 * t66 * t103 * t85 / 0.8e1
  t157 = t69 * s2
  t158 = t76 * t80
  t160 = t145 * t6 + t61 + 0.1e1
  t165 = t69 ** 2
  t167 = t165 * t68 * s2
  t168 = t79 ** 2
  t170 = t76 / t168
  t180 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t148 * t26 * t85 - t156 - 0.3e1 / 0.8e1 * t5 * t67 * (-0.2e1 / 0.27e2 * t109 * t157 * t158 * t160 + t127 * t167 * t170 * t160 / 0.27e2))
  vrho_0_ = t59 + t89 + t6 * (t143 + t180)
  t183 = -t7 - t92
  t184 = f.my_piecewise5(t10, 0, t14, 0, t183)
  t187 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t184)
  t193 = t184 * t6 + t18 + 0.1e1
  t207 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t187 * t26 * t55 - t107 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.2e1 / 0.27e2 * t109 * t110 * t111 * t193 + t127 * t130 * t133 * t193 / 0.27e2))
  t209 = f.my_piecewise5(t14, 0, t10, 0, -t183)
  t212 = f.my_piecewise3(t63, 0, 0.4e1 / 0.3e1 * t64 * t209)
  t218 = t209 * t6 + t61 + 0.1e1
  t240 = f.my_piecewise3(t60, 0, -0.3e1 / 0.8e1 * t5 * t212 * t26 * t85 - t156 - 0.3e1 / 0.8e1 * t5 * t67 * (-0.2e1 / 0.27e2 * t109 * t157 * t158 * t218 + 0.4e1 / 0.27e2 * t35 * t71 * s2 / t74 / t72 / r1 * t80 + t127 * t167 * t170 * t218 / 0.27e2))
  vrho_1_ = t59 + t89 + t6 * (t207 + t240)
  t245 = t26 * params.gamma * t32
  t247 = t33 * t37
  t253 = f.my_piecewise3(t1, 0, t4 * t25 * t245 * t247 * t40 * t46 * t50 / 0.16e2)
  vsigma_0_ = t6 * t253
  vsigma_1_ = 0.0e0
  t261 = f.my_piecewise3(t60, 0, t4 * t66 * t245 * t247 * t70 * t76 * t80 / 0.16e2)
  vsigma_2_ = t6 * t261
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_delta_raw = params.delta
  if isinstance(params_delta_raw, (str, bytes, dict)):
    params_delta = params_delta_raw
  else:
    try:
      params_delta_seq = list(params_delta_raw)
    except TypeError:
      params_delta = params_delta_raw
    else:
      params_delta_seq = np.asarray(params_delta_seq, dtype=np.float64)
      params_delta = np.concatenate((np.array([np.nan], dtype=np.float64), params_delta_seq))
  params_gamma_raw = params.gamma
  if isinstance(params_gamma_raw, (str, bytes, dict)):
    params_gamma = params_gamma_raw
  else:
    try:
      params_gamma_seq = list(params_gamma_raw)
    except TypeError:
      params_gamma = params_gamma_raw
    else:
      params_gamma_seq = np.asarray(params_gamma_seq, dtype=np.float64)
      params_gamma = np.concatenate((np.array([np.nan], dtype=np.float64), params_gamma_seq))

  kt_fx = lambda rs, z, xs: 1 - params_gamma / X_FACTOR_C * f.n_spin(rs, z) ** (4 / 3) * xs ** 2 / (f.n_spin(rs, z) ** (4 / 3) + params_delta)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_exchange_nsp(f, params, kt_fx, rs, zeta, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t6 = t3 * t5
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t20 = t3 ** 2
  t21 = params.gamma * t20
  t23 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t25 = 4 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t23 * t25
  t27 = t21 * t26
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t11 * r0
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 * t29
  t32 = t28 * t31
  t33 = r0 ** 2
  t34 = t18 ** 2
  t36 = 0.1e1 / t34 / t33
  t38 = t28 ** 2
  t41 = t38 * t31 / 0.4e1 + params.delta
  t42 = 0.1e1 / t41
  t47 = 0.1e1 - t27 * t32 * s0 * t36 * t42 / 0.9e1
  t51 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t47)
  t73 = t30 ** 2
  t76 = t41 ** 2
  t88 = f.my_piecewise3(t2, 0, -t6 * t17 / t34 * t47 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.4e1 / 0.27e2 * t21 * t26 * t28 * t30 * s0 * t36 * t42 * t11 + 0.8e1 / 0.27e2 * t27 * t32 * s0 / t34 / t33 / r0 * t42 + 0.2e1 / 0.27e2 * t27 * t73 * t29 * s0 * t36 / t76 * t11))
  vrho_0_ = 0.2e1 * r0 * t88 + 0.2e1 * t51
  t100 = f.my_piecewise3(t2, 0, t5 * t17 / t18 / t33 * params.gamma * t26 * t32 * t42 / 0.8e1)
  vsigma_0_ = 0.2e1 * r0 * t100
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 / t4
  t6 = t3 * t5
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t20 = 0.1e1 / t19
  t21 = t17 * t20
  t22 = t3 ** 2
  t23 = params.gamma * t22
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = 4 ** (0.1e1 / 0.3e1)
  t28 = t26 * t27
  t29 = t23 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t11 * r0
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = t32 * t31
  t34 = t30 * t33
  t35 = r0 ** 2
  t37 = 0.1e1 / t19 / t35
  t39 = t30 ** 2
  t42 = t39 * t33 / 0.4e1 + params.delta
  t43 = 0.1e1 / t42
  t48 = 0.1e1 - t29 * t34 * s0 * t37 * t43 / 0.9e1
  t52 = t17 * t18
  t54 = t23 * t28 * t30
  t55 = t32 * s0
  t56 = t37 * t43
  t61 = t35 * r0
  t63 = 0.1e1 / t19 / t61
  t69 = t32 ** 2
  t70 = t69 * t31
  t71 = t70 * s0
  t72 = t42 ** 2
  t73 = 0.1e1 / t72
  t74 = t37 * t73
  t79 = -0.4e1 / 0.27e2 * t54 * t55 * t56 * t11 + 0.8e1 / 0.27e2 * t29 * t34 * s0 * t63 * t43 + 0.2e1 / 0.27e2 * t29 * t71 * t74 * t11
  t84 = f.my_piecewise3(t2, 0, -t6 * t21 * t48 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t52 * t79)
  t97 = t11 ** 2
  t112 = t35 ** 2
  t125 = t97 ** 2
  t139 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t48 / 0.12e2 - t6 * t21 * t79 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t52 * (-0.4e1 / 0.81e2 * t54 / t69 * s0 * t56 * t97 + 0.64e2 / 0.81e2 * t54 * t55 * t63 * t43 * t11 + 0.2e1 / 0.9e1 * t29 * t69 * s0 * t74 * t97 - 0.88e2 / 0.81e2 * t29 * t34 * s0 / t19 / t112 * t43 - 0.32e2 / 0.81e2 * t29 * t71 * t63 * t73 * t11 - 0.4e1 / 0.81e2 * t29 * t125 * t20 * s0 / t72 / t42 * t39))
  v2rho2_0_ = 0.2e1 * r0 * t139 + 0.4e1 * t84
  t142 = t5 * t17
  t145 = 0.1e1 / t18 / t35 * params.gamma
  t146 = t142 * t145
  t148 = t28 * t34 * t43
  t151 = f.my_piecewise3(t2, 0, t146 * t148 / 0.8e1)
  t172 = f.my_piecewise3(t2, 0, -0.7e1 / 0.24e2 * t142 / t18 / t61 * params.gamma * t148 + t142 * t145 * t26 * t27 * t30 * t32 * t43 * t11 / 0.6e1 - t146 * t28 * t70 * t73 * t11 / 0.12e2)
  v2rhosigma_0_ = 0.2e1 * r0 * t172 + 0.2e1 * t151
  v2sigma2_0_ = 0.0e0
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = 0.1e1 / t19 / r0
  t22 = t17 * t21
  t23 = t3 ** 2
  t24 = params.gamma * t23
  t26 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t26 * t28
  t30 = t24 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t11 * r0
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = t33 * t32
  t35 = t31 * t34
  t36 = r0 ** 2
  t38 = 0.1e1 / t19 / t36
  t40 = t31 ** 2
  t43 = t40 * t34 / 0.4e1 + params.delta
  t44 = 0.1e1 / t43
  t49 = 0.1e1 - t30 * t35 * s0 * t38 * t44 / 0.9e1
  t53 = 0.1e1 / t19
  t54 = t17 * t53
  t56 = t24 * t29 * t31
  t57 = t33 * s0
  t58 = t38 * t44
  t65 = 0.1e1 / t19 / t36 / r0
  t71 = t33 ** 2
  t72 = t71 * t32
  t73 = t72 * s0
  t74 = t43 ** 2
  t75 = 0.1e1 / t74
  t76 = t38 * t75
  t81 = -0.4e1 / 0.27e2 * t56 * t57 * t58 * t11 + 0.8e1 / 0.27e2 * t30 * t35 * s0 * t65 * t44 + 0.2e1 / 0.27e2 * t30 * t73 * t76 * t11
  t85 = t17 * t18
  t87 = 0.1e1 / t71 * s0
  t88 = t11 ** 2
  t93 = t65 * t44
  t98 = t71 * s0
  t103 = t36 ** 2
  t105 = 0.1e1 / t19 / t103
  t111 = t65 * t75
  t116 = t88 ** 2
  t121 = s0 / t74 / t43 * t40
  t125 = -0.4e1 / 0.81e2 * t56 * t87 * t58 * t88 + 0.64e2 / 0.81e2 * t56 * t57 * t93 * t11 + 0.2e1 / 0.9e1 * t30 * t98 * t76 * t88 - 0.88e2 / 0.81e2 * t30 * t35 * s0 * t105 * t44 - 0.32e2 / 0.81e2 * t30 * t73 * t111 * t11 - 0.4e1 / 0.81e2 * t30 * t116 * t53 * t121
  t130 = f.my_piecewise3(t2, 0, t6 * t22 * t49 / 0.12e2 - t6 * t54 * t81 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t85 * t125)
  t144 = t88 * t11
  t189 = t74 ** 2
  t201 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t38 * t49 + t6 * t22 * t81 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t54 * t125 - 0.3e1 / 0.8e1 * t6 * t85 * (0.8e1 / 0.243e3 * t56 / t72 * s0 * t58 * t144 + 0.32e2 / 0.81e2 * t56 * t87 * t93 * t88 + 0.44e2 / 0.243e3 * t30 / t33 * s0 * t76 * t144 - 0.352e3 / 0.81e2 * t56 * t57 * t105 * t44 * t11 - 0.16e2 / 0.9e1 * t30 * t98 * t111 * t88 + 0.4e1 / 0.27e2 * t30 * t116 * t21 * t121 + 0.1232e4 / 0.243e3 * t30 * t35 * s0 / t19 / t103 / r0 * t44 + 0.176e3 / 0.81e2 * t30 * t73 * t105 * t75 * t11 + 0.8e1 / 0.81e2 * t24 * t29 * t116 * t11 * t53 * s0 / t189 * t31 * t33))
  v3rho3_0_ = 0.2e1 * r0 * t201 + 0.6e1 * t130

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / t18
  t23 = t17 * t22
  t24 = t3 ** 2
  t25 = params.gamma * t24
  t27 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t27 * t29
  t31 = t25 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t11 * r0
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 * t33
  t36 = t32 * t35
  t37 = s0 * t22
  t38 = t32 ** 2
  t41 = t38 * t35 / 0.4e1 + params.delta
  t42 = 0.1e1 / t41
  t47 = 0.1e1 - t31 * t36 * t37 * t42 / 0.9e1
  t52 = 0.1e1 / t20 / r0
  t53 = t17 * t52
  t55 = t25 * t30 * t32
  t56 = t34 * s0
  t57 = t22 * t42
  t64 = 0.1e1 / t20 / t18 / r0
  t70 = t34 ** 2
  t71 = t70 * t33
  t72 = t71 * s0
  t73 = t41 ** 2
  t74 = 0.1e1 / t73
  t75 = t22 * t74
  t80 = -0.4e1 / 0.27e2 * t55 * t56 * t57 * t11 + 0.8e1 / 0.27e2 * t31 * t36 * s0 * t64 * t42 + 0.2e1 / 0.27e2 * t31 * t72 * t75 * t11
  t84 = 0.1e1 / t20
  t85 = t17 * t84
  t86 = 0.1e1 / t70
  t87 = t86 * s0
  t88 = t11 ** 2
  t93 = t64 * t42
  t98 = t70 * s0
  t103 = t18 ** 2
  t105 = 0.1e1 / t20 / t103
  t111 = t64 * t74
  t116 = t88 ** 2
  t119 = 0.1e1 / t73 / t41
  t121 = s0 * t119 * t38
  t125 = -0.4e1 / 0.81e2 * t55 * t87 * t57 * t88 + 0.64e2 / 0.81e2 * t55 * t56 * t93 * t11 + 0.2e1 / 0.9e1 * t31 * t98 * t75 * t88 - 0.88e2 / 0.81e2 * t31 * t36 * s0 * t105 * t42 - 0.32e2 / 0.81e2 * t31 * t72 * t111 * t11 - 0.4e1 / 0.81e2 * t31 * t116 * t84 * t121
  t129 = t17 * t19
  t131 = 0.1e1 / t71 * s0
  t132 = t88 * t11
  t142 = 0.1e1 / t34 * s0
  t147 = t105 * t42
  t162 = 0.1e1 / t20 / t103 / r0
  t168 = t105 * t74
  t175 = t25 * t30 * t116 * t11
  t176 = t84 * s0
  t177 = t73 ** 2
  t179 = 0.1e1 / t177 * t32
  t180 = t179 * t34
  t184 = 0.8e1 / 0.243e3 * t55 * t131 * t57 * t132 + 0.32e2 / 0.81e2 * t55 * t87 * t93 * t88 + 0.44e2 / 0.243e3 * t31 * t142 * t75 * t132 - 0.352e3 / 0.81e2 * t55 * t56 * t147 * t11 - 0.16e2 / 0.9e1 * t31 * t98 * t111 * t88 + 0.4e1 / 0.27e2 * t31 * t116 * t52 * t121 + 0.1232e4 / 0.243e3 * t31 * t36 * s0 * t162 * t42 + 0.176e3 / 0.81e2 * t31 * t72 * t168 * t11 + 0.8e1 / 0.81e2 * t175 * t176 * t180
  t189 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t47 + t6 * t53 * t80 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t85 * t125 - 0.3e1 / 0.8e1 * t6 * t129 * t184)
  t237 = t116 * t88
  t276 = -0.20944e5 / 0.729e3 * t31 * t36 * s0 / t20 / t103 / t18 * t42 - 0.88e2 / 0.243e3 * t175 * t52 * s0 * t180 - 0.40e2 / 0.729e3 * t55 / t70 / t88 / t18 * s0 * t57 * t116 - 0.256e3 / 0.729e3 * t55 * t131 * t93 * t132 - 0.704e3 / 0.243e3 * t55 * t87 * t147 * t88 + 0.19712e5 / 0.729e3 * t55 * t56 * t162 * t42 * t11 + 0.8e1 / 0.243e3 * t25 * t30 * t237 * t176 * t179 * t86 - 0.20e2 / 0.243e3 * t31 / t35 * s0 * t75 * t116 - 0.1408e4 / 0.729e3 * t31 * t142 * t111 * t132 - 0.460e3 / 0.729e3 * t31 * t37 * t119 * t116 * t38 + 0.352e3 / 0.27e2 * t31 * t98 * t168 * t88 - 0.9856e4 / 0.729e3 * t31 * t72 * t162 * t74 * t11 - 0.64e2 / 0.243e3 * t31 * t237 * t84 * s0 / t177 / t41 * t70
  t281 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t64 * t47 - 0.5e1 / 0.9e1 * t6 * t23 * t80 + t6 * t53 * t125 / 0.2e1 - t6 * t85 * t184 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t129 * t276)
  v4rho4_0_ = 0.2e1 * r0 * t281 + 0.8e1 * t189

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t6 ** 2
  t23 = 0.1e1 / t22
  t24 = t16 * t23
  t25 = t7 - t24
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t6 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t32 = t2 ** 2
  t33 = params.gamma * t32
  t35 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t37 = 4 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t35 * t37
  t39 = t33 * t38
  t40 = 2 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = t19 * t6
  t43 = t42 ** (0.1e1 / 0.3e1)
  t45 = t41 * t43 * t42
  t46 = r0 ** 2
  t47 = r0 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t50 = 0.1e1 / t48 / t46
  t53 = t45 / 0.4e1 + params.delta
  t54 = 0.1e1 / t53
  t59 = 0.1e1 - t39 * t45 * s0 * t50 * t54 / 0.18e2
  t63 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t64 = t63 * f.p.zeta_threshold
  t66 = f.my_piecewise3(t20, t64, t21 * t19)
  t67 = t30 ** 2
  t68 = 0.1e1 / t67
  t69 = t66 * t68
  t72 = t5 * t69 * t59 / 0.8e1
  t73 = t66 * t30
  t75 = t33 * t38 * t41
  t76 = t43 * s0
  t77 = t50 * t54
  t79 = t26 * t6 + t18 + 0.1e1
  t86 = 0.1e1 / t48 / t46 / r0
  t93 = t33 * t38 * t40
  t94 = t43 ** 2
  t96 = t94 * t42 * s0
  t97 = t53 ** 2
  t98 = 0.1e1 / t97
  t99 = t50 * t98
  t104 = -0.2e1 / 0.27e2 * t75 * t76 * t77 * t79 + 0.4e1 / 0.27e2 * t39 * t45 * s0 * t86 * t54 + t93 * t96 * t99 * t79 / 0.27e2
  t109 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t59 - t72 - 0.3e1 / 0.8e1 * t5 * t73 * t104)
  t111 = r1 <= f.p.dens_threshold
  t112 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t113 = 0.1e1 + t112
  t114 = t113 <= f.p.zeta_threshold
  t115 = t113 ** (0.1e1 / 0.3e1)
  t117 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t120 = f.my_piecewise3(t114, 0, 0.4e1 / 0.3e1 * t115 * t117)
  t121 = t120 * t30
  t122 = t113 * t6
  t123 = t122 ** (0.1e1 / 0.3e1)
  t125 = t41 * t123 * t122
  t126 = r1 ** 2
  t127 = r1 ** (0.1e1 / 0.3e1)
  t128 = t127 ** 2
  t130 = 0.1e1 / t128 / t126
  t133 = t125 / 0.4e1 + params.delta
  t134 = 0.1e1 / t133
  t139 = 0.1e1 - t39 * t125 * s2 * t130 * t134 / 0.18e2
  t144 = f.my_piecewise3(t114, t64, t115 * t113)
  t145 = t144 * t68
  t148 = t5 * t145 * t139 / 0.8e1
  t149 = t144 * t30
  t150 = t123 * s2
  t151 = t130 * t134
  t153 = t117 * t6 + t112 + 0.1e1
  t158 = t123 ** 2
  t160 = t158 * t122 * s2
  t161 = t133 ** 2
  t162 = 0.1e1 / t161
  t163 = t130 * t162
  t168 = -0.2e1 / 0.27e2 * t75 * t150 * t151 * t153 + t93 * t160 * t163 * t153 / 0.27e2
  t173 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t121 * t139 - t148 - 0.3e1 / 0.8e1 * t5 * t149 * t168)
  t175 = t21 ** 2
  t176 = 0.1e1 / t175
  t177 = t26 ** 2
  t182 = t16 / t22 / t6
  t184 = -0.2e1 * t23 + 0.2e1 * t182
  t185 = f.my_piecewise5(t10, 0, t14, 0, t184)
  t189 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t176 * t177 + 0.4e1 / 0.3e1 * t21 * t185)
  t196 = t5 * t29 * t68 * t59
  t202 = 0.1e1 / t67 / t6
  t206 = t5 * t66 * t202 * t59 / 0.12e2
  t208 = t5 * t69 * t104
  t211 = 0.1e1 / t94 * s0
  t212 = t79 ** 2
  t217 = t86 * t54
  t222 = t94 * s0
  t229 = t185 * t6 + 0.2e1 * t26
  t234 = t46 ** 2
  t242 = t86 * t98
  t247 = t19 ** 2
  t249 = t33 * t38 * t247
  t250 = t22 * s0
  t252 = 0.1e1 / t97 / t53
  t253 = t50 * t252
  t267 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t189 * t30 * t59 - t196 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t104 + t206 - t208 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t73 * (-0.2e1 / 0.81e2 * t75 * t211 * t77 * t212 + 0.32e2 / 0.81e2 * t75 * t76 * t217 * t79 + t93 * t222 * t99 * t212 / 0.9e1 - 0.2e1 / 0.27e2 * t75 * t76 * t77 * t229 - 0.44e2 / 0.81e2 * t39 * t45 * s0 / t48 / t234 * t54 - 0.16e2 / 0.81e2 * t93 * t96 * t242 * t79 - 0.4e1 / 0.81e2 * t249 * t250 * t253 * t212 + t93 * t96 * t99 * t229 / 0.27e2))
  t268 = t115 ** 2
  t269 = 0.1e1 / t268
  t270 = t117 ** 2
  t274 = f.my_piecewise5(t14, 0, t10, 0, -t184)
  t278 = f.my_piecewise3(t114, 0, 0.4e1 / 0.9e1 * t269 * t270 + 0.4e1 / 0.3e1 * t115 * t274)
  t285 = t5 * t120 * t68 * t139
  t293 = t5 * t144 * t202 * t139 / 0.12e2
  t295 = t5 * t145 * t168
  t298 = 0.1e1 / t158 * s2
  t299 = t153 ** 2
  t304 = t158 * s2
  t311 = t274 * t6 + 0.2e1 * t117
  t316 = t113 ** 2
  t318 = t33 * t38 * t316
  t319 = t22 * s2
  t321 = 0.1e1 / t161 / t133
  t322 = t130 * t321
  t336 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t278 * t30 * t139 - t285 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t121 * t168 + t293 - t295 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t149 * (-0.2e1 / 0.81e2 * t75 * t298 * t151 * t299 + t93 * t304 * t163 * t299 / 0.9e1 - 0.2e1 / 0.27e2 * t75 * t150 * t151 * t311 - 0.4e1 / 0.81e2 * t318 * t319 * t322 * t299 + t93 * t160 * t163 * t311 / 0.27e2))
  d11 = 0.2e1 * t109 + 0.2e1 * t173 + t6 * (t267 + t336)
  t339 = -t7 - t24
  t340 = f.my_piecewise5(t10, 0, t14, 0, t339)
  t343 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t340)
  t344 = t343 * t30
  t349 = t340 * t6 + t18 + 0.1e1
  t358 = -0.2e1 / 0.27e2 * t75 * t76 * t77 * t349 + t93 * t96 * t99 * t349 / 0.27e2
  t363 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t344 * t59 - t72 - 0.3e1 / 0.8e1 * t5 * t73 * t358)
  t365 = f.my_piecewise5(t14, 0, t10, 0, -t339)
  t368 = f.my_piecewise3(t114, 0, 0.4e1 / 0.3e1 * t115 * t365)
  t369 = t368 * t30
  t374 = t365 * t6 + t112 + 0.1e1
  t381 = 0.1e1 / t128 / t126 / r1
  t391 = -0.2e1 / 0.27e2 * t75 * t150 * t151 * t374 + 0.4e1 / 0.27e2 * t39 * t125 * s2 * t381 * t134 + t93 * t160 * t163 * t374 / 0.27e2
  t396 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t369 * t139 - t148 - 0.3e1 / 0.8e1 * t5 * t149 * t391)
  t400 = 0.2e1 * t182
  t401 = f.my_piecewise5(t10, 0, t14, 0, t400)
  t405 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t176 * t340 * t26 + 0.4e1 / 0.3e1 * t21 * t401)
  t412 = t5 * t343 * t68 * t59
  t423 = t5 * t69 * t358
  t442 = t401 * t6 + t26 + t340
  t466 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t405 * t30 * t59 - t412 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t344 * t104 - t196 / 0.8e1 + t206 - t208 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t31 * t358 - t423 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t73 * (-0.2e1 / 0.81e2 * t75 * t211 * t50 * t54 * t349 * t79 + 0.16e2 / 0.81e2 * t75 * t76 * t217 * t349 + t93 * t222 * t50 * t98 * t349 * t79 / 0.9e1 - 0.2e1 / 0.27e2 * t75 * t76 * t77 * t442 - 0.8e1 / 0.81e2 * t93 * t96 * t242 * t349 - 0.4e1 / 0.81e2 * t249 * t250 * t50 * t252 * t349 * t79 + t93 * t96 * t99 * t442 / 0.27e2))
  t470 = f.my_piecewise5(t14, 0, t10, 0, -t400)
  t474 = f.my_piecewise3(t114, 0, 0.4e1 / 0.9e1 * t269 * t365 * t117 + 0.4e1 / 0.3e1 * t115 * t470)
  t481 = t5 * t368 * t68 * t139
  t492 = t5 * t145 * t391
  t507 = t470 * t6 + t117 + t365
  t512 = t381 * t134
  t517 = t381 * t162
  t537 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t474 * t30 * t139 - t481 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t369 * t168 - t285 / 0.8e1 + t293 - t295 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t121 * t391 - t492 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t149 * (-0.2e1 / 0.81e2 * t75 * t298 * t130 * t134 * t374 * t153 + t93 * t304 * t130 * t162 * t374 * t153 / 0.9e1 - 0.2e1 / 0.27e2 * t75 * t150 * t151 * t507 + 0.16e2 / 0.81e2 * t75 * t150 * t512 * t153 - 0.8e1 / 0.81e2 * t93 * t160 * t517 * t153 - 0.4e1 / 0.81e2 * t318 * t319 * t130 * t321 * t374 * t153 + t93 * t160 * t163 * t507 / 0.27e2))
  d12 = t109 + t173 + t363 + t396 + t6 * (t466 + t537)
  t542 = t340 ** 2
  t546 = 0.2e1 * t23 + 0.2e1 * t182
  t547 = f.my_piecewise5(t10, 0, t14, 0, t546)
  t551 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t176 * t542 + 0.4e1 / 0.3e1 * t21 * t547)
  t561 = t349 ** 2
  t572 = t547 * t6 + 0.2e1 * t340
  t590 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t551 * t30 * t59 - t412 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t344 * t358 + t206 - t423 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t73 * (-0.2e1 / 0.81e2 * t75 * t211 * t77 * t561 + t93 * t222 * t99 * t561 / 0.9e1 - 0.2e1 / 0.27e2 * t75 * t76 * t77 * t572 - 0.4e1 / 0.81e2 * t249 * t250 * t253 * t561 + t93 * t96 * t99 * t572 / 0.27e2))
  t591 = t365 ** 2
  t595 = f.my_piecewise5(t14, 0, t10, 0, -t546)
  t599 = f.my_piecewise3(t114, 0, 0.4e1 / 0.9e1 * t269 * t591 + 0.4e1 / 0.3e1 * t115 * t595)
  t609 = t374 ** 2
  t624 = t595 * t6 + 0.2e1 * t365
  t629 = t126 ** 2
  t654 = f.my_piecewise3(t111, 0, -0.3e1 / 0.8e1 * t5 * t599 * t30 * t139 - t481 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t369 * t391 + t293 - t492 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t149 * (-0.2e1 / 0.81e2 * t75 * t298 * t151 * t609 + 0.32e2 / 0.81e2 * t75 * t150 * t512 * t374 + t93 * t304 * t163 * t609 / 0.9e1 - 0.2e1 / 0.27e2 * t75 * t150 * t151 * t624 - 0.44e2 / 0.81e2 * t39 * t125 * s2 / t128 / t629 * t134 - 0.16e2 / 0.81e2 * t93 * t160 * t517 * t374 - 0.4e1 / 0.81e2 * t318 * t319 * t322 * t609 + t93 * t160 * t163 * t624 / 0.27e2))
  d22 = 0.2e1 * t363 + 0.2e1 * t396 + t6 * (t590 + t654)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r
  s0 = s[0] if s is not None else None
  s1 = s[1] if s is not None else None
  s2 = s[2] if s is not None else None
  l0 = l[0] if l is not None else None
  l1 = l[1] if l is not None else None
  tau0 = tau[0] if tau is not None else None
  tau1 = tau[1] if tau is not None else None

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = 0.1e1 / t22
  t24 = t6 ** 2
  t25 = 0.1e1 / t24
  t27 = -t16 * t25 + t7
  t28 = f.my_piecewise5(t10, 0, t14, 0, t27)
  t29 = t28 ** 2
  t33 = 0.1e1 / t24 / t6
  t36 = 0.2e1 * t16 * t33 - 0.2e1 * t25
  t37 = f.my_piecewise5(t10, 0, t14, 0, t36)
  t41 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t23 * t29 + 0.4e1 / 0.3e1 * t21 * t37)
  t42 = t6 ** (0.1e1 / 0.3e1)
  t43 = t41 * t42
  t44 = t2 ** 2
  t45 = params.gamma * t44
  t47 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t48 = 0.1e1 / t47
  t49 = 4 ** (0.1e1 / 0.3e1)
  t50 = t48 * t49
  t51 = t45 * t50
  t52 = 2 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t54 = t19 * t6
  t55 = t54 ** (0.1e1 / 0.3e1)
  t57 = t53 * t55 * t54
  t58 = r0 ** 2
  t59 = r0 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t62 = 0.1e1 / t60 / t58
  t63 = s0 * t62
  t65 = t57 / 0.4e1 + params.delta
  t66 = 0.1e1 / t65
  t71 = 0.1e1 - t51 * t57 * t63 * t66 / 0.18e2
  t77 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t78 = t42 ** 2
  t79 = 0.1e1 / t78
  t80 = t77 * t79
  t84 = t77 * t42
  t86 = t45 * t50 * t53
  t87 = t55 * s0
  t88 = t62 * t66
  t90 = t28 * t6 + t18 + 0.1e1
  t97 = 0.1e1 / t60 / t58 / r0
  t104 = t45 * t50 * t52
  t105 = t55 ** 2
  t106 = t105 * t54
  t107 = t106 * s0
  t108 = t65 ** 2
  t109 = 0.1e1 / t108
  t110 = t62 * t109
  t115 = -0.2e1 / 0.27e2 * t86 * t87 * t88 * t90 + 0.4e1 / 0.27e2 * t51 * t57 * s0 * t97 * t66 + t104 * t107 * t110 * t90 / 0.27e2
  t119 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t120 = t119 * f.p.zeta_threshold
  t122 = f.my_piecewise3(t20, t120, t21 * t19)
  t124 = 0.1e1 / t78 / t6
  t125 = t122 * t124
  t129 = t122 * t79
  t133 = t122 * t42
  t135 = 0.1e1 / t105 * s0
  t136 = t90 ** 2
  t141 = t97 * t66
  t146 = t105 * s0
  t153 = t37 * t6 + 0.2e1 * t28
  t158 = t58 ** 2
  t160 = 0.1e1 / t60 / t158
  t166 = t97 * t109
  t171 = t19 ** 2
  t173 = t45 * t50 * t171
  t174 = t24 * s0
  t176 = 0.1e1 / t108 / t65
  t177 = t62 * t176
  t178 = t177 * t136
  t186 = -0.2e1 / 0.81e2 * t86 * t135 * t88 * t136 + 0.32e2 / 0.81e2 * t86 * t87 * t141 * t90 + t104 * t146 * t110 * t136 / 0.9e1 - 0.2e1 / 0.27e2 * t86 * t87 * t88 * t153 - 0.44e2 / 0.81e2 * t51 * t57 * s0 * t160 * t66 - 0.16e2 / 0.81e2 * t104 * t107 * t166 * t90 - 0.4e1 / 0.81e2 * t173 * t174 * t178 + t104 * t107 * t110 * t153 / 0.27e2
  t191 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t71 - t5 * t80 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t84 * t115 + t5 * t125 * t71 / 0.12e2 - t5 * t129 * t115 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t133 * t186)
  t193 = r1 <= f.p.dens_threshold
  t194 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t195 = 0.1e1 + t194
  t196 = t195 <= f.p.zeta_threshold
  t197 = t195 ** (0.1e1 / 0.3e1)
  t198 = t197 ** 2
  t199 = 0.1e1 / t198
  t201 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t202 = t201 ** 2
  t206 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t210 = f.my_piecewise3(t196, 0, 0.4e1 / 0.9e1 * t199 * t202 + 0.4e1 / 0.3e1 * t197 * t206)
  t211 = t210 * t42
  t212 = t195 * t6
  t213 = t212 ** (0.1e1 / 0.3e1)
  t215 = t53 * t213 * t212
  t216 = r1 ** 2
  t217 = r1 ** (0.1e1 / 0.3e1)
  t218 = t217 ** 2
  t220 = 0.1e1 / t218 / t216
  t221 = s2 * t220
  t223 = t215 / 0.4e1 + params.delta
  t224 = 0.1e1 / t223
  t229 = 0.1e1 - t51 * t215 * t221 * t224 / 0.18e2
  t235 = f.my_piecewise3(t196, 0, 0.4e1 / 0.3e1 * t197 * t201)
  t236 = t235 * t79
  t240 = t235 * t42
  t241 = t213 * s2
  t242 = t220 * t224
  t244 = t201 * t6 + t194 + 0.1e1
  t249 = t213 ** 2
  t250 = t249 * t212
  t251 = t250 * s2
  t252 = t223 ** 2
  t253 = 0.1e1 / t252
  t254 = t220 * t253
  t259 = -0.2e1 / 0.27e2 * t86 * t241 * t242 * t244 + t104 * t251 * t254 * t244 / 0.27e2
  t264 = f.my_piecewise3(t196, t120, t197 * t195)
  t265 = t264 * t124
  t269 = t264 * t79
  t273 = t264 * t42
  t275 = 0.1e1 / t249 * s2
  t276 = t244 ** 2
  t281 = t249 * s2
  t288 = t206 * t6 + 0.2e1 * t201
  t293 = t195 ** 2
  t295 = t45 * t50 * t293
  t296 = t24 * s2
  t298 = 0.1e1 / t252 / t223
  t299 = t220 * t298
  t300 = t299 * t276
  t308 = -0.2e1 / 0.81e2 * t86 * t275 * t242 * t276 + t104 * t281 * t254 * t276 / 0.9e1 - 0.2e1 / 0.27e2 * t86 * t241 * t242 * t288 - 0.4e1 / 0.81e2 * t295 * t296 * t300 + t104 * t251 * t254 * t288 / 0.27e2
  t313 = f.my_piecewise3(t193, 0, -0.3e1 / 0.8e1 * t5 * t211 * t229 - t5 * t236 * t229 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t240 * t259 + t5 * t265 * t229 / 0.12e2 - t5 * t269 * t259 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t273 * t308)
  t323 = t24 ** 2
  t327 = 0.6e1 * t33 - 0.6e1 * t16 / t323
  t328 = f.my_piecewise5(t10, 0, t14, 0, t327)
  t332 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t328)
  t355 = 0.1e1 / t78 / t24
  t367 = t45 * t50 * t19
  t368 = t174 * t62
  t374 = t6 * s0
  t396 = t136 * t90
  t411 = t45 * t48
  t415 = t108 ** 2
  t425 = t328 * t6 + 0.3e1 * t37
  t474 = -0.8e1 / 0.81e2 * t367 * t368 * t176 * t136 * t28 - 0.8e1 / 0.81e2 * t173 * t374 * t178 - 0.4e1 / 0.27e2 * t173 * t368 * t176 * t90 * t153 - 0.176e3 / 0.81e2 * t86 * t87 * t160 * t66 * t90 + t104 * t146 * t62 * t109 * t90 * t153 / 0.3e1 + 0.4e1 / 0.243e3 * t86 / t106 * s0 * t88 * t396 + 0.16e2 / 0.81e2 * t86 * t135 * t141 * t136 - 0.2e1 / 0.27e2 * t86 * t135 * t62 * t66 * t90 * t153 + 0.4e1 / 0.81e2 * t411 * t49 * t171 * t24 * t63 / t415 * t396 * t53 * t55 + t104 * t107 * t110 * t425 / 0.27e2 - 0.4e1 / 0.27e2 * t367 * t374 * t177 * t396 - 0.2e1 / 0.27e2 * t86 * t87 * t88 * t425 + 0.616e3 / 0.243e3 * t51 * t57 * s0 / t60 / t158 / r0 * t66 + 0.88e2 / 0.81e2 * t104 * t107 * t160 * t109 * t90 - 0.8e1 / 0.27e2 * t104 * t107 * t166 * t153 + 0.32e2 / 0.81e2 * t173 * t174 * t97 * t176 * t136 + 0.22e2 / 0.243e3 * t104 / t55 * s0 * t110 * t396 + 0.16e2 / 0.27e2 * t86 * t87 * t141 * t153 - 0.8e1 / 0.9e1 * t104 * t146 * t166 * t136
  t479 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t332 * t42 * t71 - 0.3e1 / 0.8e1 * t5 * t41 * t79 * t71 - 0.9e1 / 0.8e1 * t5 * t43 * t115 + t5 * t77 * t124 * t71 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t80 * t115 - 0.9e1 / 0.8e1 * t5 * t84 * t186 - 0.5e1 / 0.36e2 * t5 * t122 * t355 * t71 + t5 * t125 * t115 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t129 * t186 - 0.3e1 / 0.8e1 * t5 * t133 * t474)
  t489 = f.my_piecewise5(t14, 0, t10, 0, -t327)
  t493 = f.my_piecewise3(t196, 0, -0.8e1 / 0.27e2 / t198 / t195 * t202 * t201 + 0.4e1 / 0.3e1 * t199 * t201 * t206 + 0.4e1 / 0.3e1 * t197 * t489)
  t527 = t276 * t244
  t545 = t45 * t50 * t195
  t546 = t6 * s2
  t559 = t489 * t6 + 0.3e1 * t206
  t564 = t296 * t220
  t576 = t252 ** 2
  t593 = 0.4e1 / 0.243e3 * t86 / t250 * s2 * t242 * t527 + 0.22e2 / 0.243e3 * t104 / t213 * s2 * t254 * t527 - 0.2e1 / 0.27e2 * t86 * t275 * t220 * t224 * t244 * t288 - 0.4e1 / 0.27e2 * t545 * t546 * t299 * t527 + t104 * t281 * t220 * t253 * t244 * t288 / 0.3e1 - 0.2e1 / 0.27e2 * t86 * t241 * t242 * t559 - 0.8e1 / 0.81e2 * t545 * t564 * t298 * t276 * t201 - 0.8e1 / 0.81e2 * t295 * t546 * t300 + 0.4e1 / 0.81e2 * t411 * t49 * t293 * t24 * t221 / t576 * t527 * t53 * t213 - 0.4e1 / 0.27e2 * t295 * t564 * t298 * t244 * t288 + t104 * t251 * t254 * t559 / 0.27e2
  t598 = f.my_piecewise3(t193, 0, -0.3e1 / 0.8e1 * t5 * t493 * t42 * t229 - 0.3e1 / 0.8e1 * t5 * t210 * t79 * t229 - 0.9e1 / 0.8e1 * t5 * t211 * t259 + t5 * t235 * t124 * t229 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t236 * t259 - 0.9e1 / 0.8e1 * t5 * t240 * t308 - 0.5e1 / 0.36e2 * t5 * t264 * t355 * t229 + t5 * t265 * t259 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t269 * t308 - 0.3e1 / 0.8e1 * t5 * t273 * t593)
  d111 = 0.3e1 * t191 + 0.3e1 * t313 + t6 * (t479 + t598)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r
  s0 = s[0] if s is not None else None
  s1 = s[1] if s is not None else None
  s2 = s[2] if s is not None else None
  l0 = l[0] if l is not None else None
  l1 = l[1] if l is not None else None
  tau0 = tau[0] if tau is not None else None
  tau1 = tau[1] if tau is not None else None

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t10 = 0.2e1 * r0 * t7 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold - 0.1e1
  t14 = 0.2e1 * r1 * t7 <= f.p.zeta_threshold
  t15 = -t11
  t16 = r0 - r1
  t17 = t16 * t7
  t18 = f.my_piecewise5(t10, t11, t14, t15, t17)
  t19 = 0.1e1 + t18
  t20 = t19 <= f.p.zeta_threshold
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t24 = 0.1e1 / t22 / t19
  t25 = t6 ** 2
  t26 = 0.1e1 / t25
  t28 = -t16 * t26 + t7
  t29 = f.my_piecewise5(t10, 0, t14, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t6
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t16 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t10, 0, t14, 0, t40)
  t44 = t25 ** 2
  t45 = 0.1e1 / t44
  t48 = -0.6e1 * t16 * t45 + 0.6e1 * t37
  t49 = f.my_piecewise5(t10, 0, t14, 0, t48)
  t53 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t24 * t30 * t29 + 0.4e1 / 0.3e1 * t35 * t41 + 0.4e1 / 0.3e1 * t21 * t49)
  t54 = t6 ** (0.1e1 / 0.3e1)
  t55 = t53 * t54
  t56 = t2 ** 2
  t57 = params.gamma * t56
  t59 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t60 = 0.1e1 / t59
  t61 = 4 ** (0.1e1 / 0.3e1)
  t62 = t60 * t61
  t63 = t57 * t62
  t64 = 2 ** (0.1e1 / 0.3e1)
  t65 = t64 ** 2
  t66 = t19 * t6
  t67 = t66 ** (0.1e1 / 0.3e1)
  t68 = t67 * t66
  t69 = t65 * t68
  t70 = r0 ** 2
  t71 = r0 ** (0.1e1 / 0.3e1)
  t72 = t71 ** 2
  t74 = 0.1e1 / t72 / t70
  t75 = s0 * t74
  t77 = t69 / 0.4e1 + params.delta
  t78 = 0.1e1 / t77
  t83 = 0.1e1 - t63 * t69 * t75 * t78 / 0.18e2
  t92 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t93 = t54 ** 2
  t94 = 0.1e1 / t93
  t95 = t92 * t94
  t99 = t92 * t54
  t101 = t57 * t62 * t65
  t102 = t67 * s0
  t103 = t74 * t78
  t105 = t29 * t6 + t18 + 0.1e1
  t112 = 0.1e1 / t72 / t70 / r0
  t113 = s0 * t112
  t119 = t57 * t62 * t64
  t120 = t67 ** 2
  t121 = t120 * t66
  t122 = t121 * s0
  t123 = t77 ** 2
  t124 = 0.1e1 / t123
  t125 = t74 * t124
  t130 = -0.2e1 / 0.27e2 * t101 * t102 * t103 * t105 + 0.4e1 / 0.27e2 * t63 * t69 * t113 * t78 + t119 * t122 * t125 * t105 / 0.27e2
  t136 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t138 = 0.1e1 / t93 / t6
  t139 = t136 * t138
  t143 = t136 * t94
  t147 = t136 * t54
  t148 = 0.1e1 / t120
  t149 = t148 * s0
  t150 = t105 ** 2
  t155 = t112 * t78
  t160 = t120 * s0
  t167 = t41 * t6 + 0.2e1 * t29
  t172 = t70 ** 2
  t174 = 0.1e1 / t72 / t172
  t180 = t112 * t124
  t185 = t19 ** 2
  t187 = t57 * t62 * t185
  t188 = t25 * s0
  t190 = 0.1e1 / t123 / t77
  t191 = t74 * t190
  t192 = t191 * t150
  t193 = t188 * t192
  t200 = -0.2e1 / 0.81e2 * t101 * t149 * t103 * t150 + 0.32e2 / 0.81e2 * t101 * t102 * t155 * t105 + t119 * t160 * t125 * t150 / 0.9e1 - 0.2e1 / 0.27e2 * t101 * t102 * t103 * t167 - 0.44e2 / 0.81e2 * t63 * t69 * s0 * t174 * t78 - 0.16e2 / 0.81e2 * t119 * t122 * t180 * t105 - 0.4e1 / 0.81e2 * t187 * t193 + t119 * t122 * t125 * t167 / 0.27e2
  t204 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t205 = t204 * f.p.zeta_threshold
  t207 = f.my_piecewise3(t20, t205, t21 * t19)
  t209 = 0.1e1 / t93 / t25
  t210 = t207 * t209
  t214 = t207 * t138
  t218 = t207 * t94
  t222 = t207 * t54
  t224 = t57 * t62 * t19
  t225 = t188 * t74
  t226 = t190 * t150
  t227 = t226 * t29
  t231 = t6 * s0
  t235 = t190 * t105
  t236 = t235 * t167
  t240 = t174 * t78
  t245 = t160 * t74
  t246 = t124 * t105
  t247 = t246 * t167
  t252 = 0.1e1 / t121 * s0
  t253 = t150 * t105
  t262 = t149 * t74
  t263 = t78 * t105
  t264 = t263 * t167
  t268 = t57 * t60
  t269 = t61 * t185
  t271 = t268 * t269 * t25
  t272 = t123 ** 2
  t273 = 0.1e1 / t272
  t274 = t75 * t273
  t276 = t253 * t65 * t67
  t277 = t274 * t276
  t282 = t49 * t6 + 0.3e1 * t41
  t287 = t191 * t253
  t288 = t231 * t287
  t297 = 0.1e1 / t72 / t172 / r0
  t303 = t174 * t124
  t312 = t112 * t190
  t313 = t312 * t150
  t318 = 0.1e1 / t67 * s0
  t331 = -0.8e1 / 0.81e2 * t224 * t225 * t227 - 0.8e1 / 0.81e2 * t187 * t231 * t192 - 0.4e1 / 0.27e2 * t187 * t225 * t236 - 0.176e3 / 0.81e2 * t101 * t102 * t240 * t105 + t119 * t245 * t247 / 0.3e1 + 0.4e1 / 0.243e3 * t101 * t252 * t103 * t253 + 0.16e2 / 0.81e2 * t101 * t149 * t155 * t150 - 0.2e1 / 0.27e2 * t101 * t262 * t264 + 0.4e1 / 0.81e2 * t271 * t277 + t119 * t122 * t125 * t282 / 0.27e2 - 0.4e1 / 0.27e2 * t224 * t288 - 0.2e1 / 0.27e2 * t101 * t102 * t103 * t282 + 0.616e3 / 0.243e3 * t63 * t69 * s0 * t297 * t78 + 0.88e2 / 0.81e2 * t119 * t122 * t303 * t105 - 0.8e1 / 0.27e2 * t119 * t122 * t180 * t167 + 0.32e2 / 0.81e2 * t187 * t188 * t313 + 0.22e2 / 0.243e3 * t119 * t318 * t125 * t253 + 0.16e2 / 0.27e2 * t101 * t102 * t155 * t167 - 0.8e1 / 0.9e1 * t119 * t160 * t180 * t150
  t336 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t83 - 0.3e1 / 0.8e1 * t5 * t95 * t83 - 0.9e1 / 0.8e1 * t5 * t99 * t130 + t5 * t139 * t83 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t143 * t130 - 0.9e1 / 0.8e1 * t5 * t147 * t200 - 0.5e1 / 0.36e2 * t5 * t210 * t83 + t5 * t214 * t130 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t218 * t200 - 0.3e1 / 0.8e1 * t5 * t222 * t331)
  t338 = r1 <= f.p.dens_threshold
  t339 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t340 = 0.1e1 + t339
  t341 = t340 <= f.p.zeta_threshold
  t342 = t340 ** (0.1e1 / 0.3e1)
  t343 = t342 ** 2
  t345 = 0.1e1 / t343 / t340
  t347 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t348 = t347 ** 2
  t352 = 0.1e1 / t343
  t353 = t352 * t347
  t355 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t359 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t363 = f.my_piecewise3(t341, 0, -0.8e1 / 0.27e2 * t345 * t348 * t347 + 0.4e1 / 0.3e1 * t353 * t355 + 0.4e1 / 0.3e1 * t342 * t359)
  t364 = t363 * t54
  t365 = t340 * t6
  t366 = t365 ** (0.1e1 / 0.3e1)
  t367 = t366 * t365
  t368 = t65 * t367
  t369 = r1 ** 2
  t370 = r1 ** (0.1e1 / 0.3e1)
  t371 = t370 ** 2
  t373 = 0.1e1 / t371 / t369
  t374 = s2 * t373
  t376 = t368 / 0.4e1 + params.delta
  t377 = 0.1e1 / t376
  t382 = 0.1e1 - t63 * t368 * t374 * t377 / 0.18e2
  t391 = f.my_piecewise3(t341, 0, 0.4e1 / 0.9e1 * t352 * t348 + 0.4e1 / 0.3e1 * t342 * t355)
  t392 = t391 * t94
  t396 = t391 * t54
  t397 = t366 * s2
  t398 = t373 * t377
  t400 = t347 * t6 + t339 + 0.1e1
  t405 = t366 ** 2
  t406 = t405 * t365
  t407 = t406 * s2
  t408 = t376 ** 2
  t409 = 0.1e1 / t408
  t410 = t373 * t409
  t415 = -0.2e1 / 0.27e2 * t101 * t397 * t398 * t400 + t119 * t407 * t410 * t400 / 0.27e2
  t421 = f.my_piecewise3(t341, 0, 0.4e1 / 0.3e1 * t342 * t347)
  t422 = t421 * t138
  t426 = t421 * t94
  t430 = t421 * t54
  t431 = 0.1e1 / t405
  t432 = t431 * s2
  t433 = t400 ** 2
  t438 = t405 * s2
  t445 = t355 * t6 + 0.2e1 * t347
  t450 = t340 ** 2
  t452 = t57 * t62 * t450
  t453 = t25 * s2
  t455 = 0.1e1 / t408 / t376
  t456 = t373 * t455
  t457 = t456 * t433
  t458 = t453 * t457
  t465 = -0.2e1 / 0.81e2 * t101 * t432 * t398 * t433 + t119 * t438 * t410 * t433 / 0.9e1 - 0.2e1 / 0.27e2 * t101 * t397 * t398 * t445 - 0.4e1 / 0.81e2 * t452 * t458 + t119 * t407 * t410 * t445 / 0.27e2
  t470 = f.my_piecewise3(t341, t205, t342 * t340)
  t471 = t470 * t209
  t475 = t470 * t138
  t479 = t470 * t94
  t483 = t470 * t54
  t485 = 0.1e1 / t406 * s2
  t486 = t433 * t400
  t492 = 0.1e1 / t366 * s2
  t497 = t432 * t373
  t498 = t377 * t400
  t504 = t57 * t62 * t340
  t505 = t6 * s2
  t506 = t456 * t486
  t507 = t505 * t506
  t510 = t438 * t373
  t511 = t409 * t400
  t518 = t359 * t6 + 0.3e1 * t355
  t523 = t453 * t373
  t524 = t455 * t433
  t525 = t524 * t347
  t532 = t61 * t450
  t534 = t268 * t532 * t25
  t535 = t408 ** 2
  t537 = t374 / t535
  t540 = t537 * t486 * t65 * t366
  t543 = t455 * t400
  t544 = t543 * t445
  t552 = 0.4e1 / 0.243e3 * t101 * t485 * t398 * t486 + 0.22e2 / 0.243e3 * t119 * t492 * t410 * t486 - 0.2e1 / 0.27e2 * t101 * t497 * t498 * t445 - 0.4e1 / 0.27e2 * t504 * t507 + t119 * t510 * t511 * t445 / 0.3e1 - 0.2e1 / 0.27e2 * t101 * t397 * t398 * t518 - 0.8e1 / 0.81e2 * t504 * t523 * t525 - 0.8e1 / 0.81e2 * t452 * t505 * t457 + 0.4e1 / 0.81e2 * t534 * t540 - 0.4e1 / 0.27e2 * t452 * t523 * t544 + t119 * t407 * t410 * t518 / 0.27e2
  t557 = f.my_piecewise3(t338, 0, -0.3e1 / 0.8e1 * t5 * t364 * t382 - 0.3e1 / 0.8e1 * t5 * t392 * t382 - 0.9e1 / 0.8e1 * t5 * t396 * t415 + t5 * t422 * t382 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t426 * t415 - 0.9e1 / 0.8e1 * t5 * t430 * t465 - 0.5e1 / 0.36e2 * t5 * t471 * t382 + t5 * t475 * t415 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t479 * t465 - 0.3e1 / 0.8e1 * t5 * t483 * t552)
  t582 = t231 * t74
  t618 = t188 * t112
  t622 = -0.8e1 / 0.81e2 * t101 * t262 * t263 * t282 + 0.4e1 / 0.9e1 * t119 * t245 * t246 * t282 - 0.8e1 / 0.9e1 * t224 * t582 * t226 * t167 + 0.8e1 / 0.81e2 * t101 * t252 * t74 * t78 * t150 * t167 + 0.64e2 / 0.81e2 * t101 * t149 * t112 * t264 - 0.40e2 / 0.81e2 * t187 * t582 * t236 - 0.16e2 / 0.81e2 * t187 * t225 * t235 * t282 - 0.8e1 / 0.81e2 * t224 * t225 * t226 * t41 + 0.44e2 / 0.81e2 * t119 * t318 * t74 * t124 * t150 * t167 - 0.32e2 / 0.9e1 * t119 * t160 * t112 * t247 + 0.128e3 / 0.81e2 * t187 * t618 * t236
  t630 = t65 * t67
  t635 = t61 * t19
  t637 = t268 * t635 * t25
  t643 = t150 ** 2
  t652 = t643 * t65
  t685 = -0.32e2 / 0.81e2 * t224 * t582 * t227 + 0.256e3 / 0.243e3 * t224 * t618 * t227 + 0.8e1 / 0.27e2 * t271 * t274 * t150 * t167 * t630 + 0.16e2 / 0.81e2 * t637 * t274 * t253 * t29 * t630 - 0.88e2 / 0.729e3 * t63 * t75 * t190 * t643 - 0.128e3 / 0.243e3 * t271 * t113 * t273 * t276 + 0.4e1 / 0.243e3 * t271 * t274 * t652 * t148 - 0.32e2 / 0.243e3 * t271 * t75 / t272 / t77 * t643 * t64 * t120 + 0.4e1 / 0.27e2 * t268 * t635 * t6 * t274 * t652 * t67 - 0.40e2 / 0.81e2 * t637 * t75 * t190 * t105 * t29 * t167 + 0.16e2 / 0.81e2 * t268 * t269 * t6 * t277 - 0.352e3 / 0.81e2 * t101 * t102 * t240 * t167
  t725 = t167 ** 2
  t741 = 0.176e3 / 0.27e2 * t119 * t160 * t303 * t150 - 0.10e2 / 0.243e3 * t119 / t68 * s0 * t125 * t643 - 0.704e3 / 0.729e3 * t119 * t318 * t180 * t253 - 0.32e2 / 0.81e2 * t119 * t122 * t180 * t282 + 0.128e3 / 0.81e2 * t224 * t231 * t312 * t253 + 0.64e2 / 0.81e2 * t101 * t102 * t155 * t282 - 0.20e2 / 0.729e3 * t101 / t120 / t185 / t25 * s0 * t103 * t643 - 0.128e3 / 0.729e3 * t101 * t252 * t155 * t253 - 0.2e1 / 0.27e2 * t101 * t149 * t103 * t725 + 0.256e3 / 0.243e3 * t187 * t231 * t313 - 0.4e1 / 0.27e2 * t187 * t188 * t191 * t725 - 0.352e3 / 0.243e3 * t101 * t149 * t240 * t150
  t773 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t774 = f.my_piecewise5(t10, 0, t14, 0, t773)
  t777 = t774 * t6 + 0.4e1 * t49
  t806 = 0.9856e4 / 0.729e3 * t101 * t102 * t297 * t78 * t105 + t119 * t160 * t125 * t725 / 0.3e1 - 0.8e1 / 0.81e2 * t57 * t62 * t30 * t193 - 0.4928e4 / 0.729e3 * t119 * t122 * t297 * t124 * t105 + 0.176e3 / 0.81e2 * t119 * t122 * t303 * t167 - 0.704e3 / 0.243e3 * t187 * t188 * t174 * t190 * t150 + t119 * t122 * t125 * t777 / 0.27e2 - 0.4e1 / 0.27e2 * t57 * t62 * t29 * t288 - 0.2e1 / 0.27e2 * t101 * t102 * t103 * t777 - 0.10472e5 / 0.729e3 * t63 * t69 * s0 / t72 / t172 / t70 * t78 - 0.4e1 / 0.27e2 * t63 * t19 * s0 * t287 - 0.8e1 / 0.81e2 * t63 * t185 * s0 * t192
  t814 = t30 ** 2
  t820 = t41 ** 2
  t828 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t185 * t814 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t820 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t774)
  t857 = 0.1e1 / t93 / t36
  t862 = -0.3e1 / 0.2e1 * t5 * t143 * t200 - 0.3e1 / 0.2e1 * t5 * t147 * t331 - 0.5e1 / 0.9e1 * t5 * t210 * t130 + t5 * t214 * t200 / 0.2e1 - t5 * t218 * t331 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t222 * (t622 + t685 + t741 + t806) - 0.3e1 / 0.8e1 * t5 * t828 * t54 * t83 - 0.3e1 / 0.2e1 * t5 * t55 * t130 - 0.3e1 / 0.2e1 * t5 * t95 * t130 - 0.9e1 / 0.4e1 * t5 * t99 * t200 + t5 * t139 * t130 - t5 * t53 * t94 * t83 / 0.2e1 + t5 * t92 * t138 * t83 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t136 * t209 * t83 + 0.10e2 / 0.27e2 * t5 * t207 * t857 * t83
  t863 = f.my_piecewise3(t1, 0, t862)
  t864 = t505 * t373
  t903 = t61 * t340
  t905 = t268 * t903 * t25
  t918 = t433 ** 2
  t925 = t918 * t65
  t934 = -0.8e1 / 0.9e1 * t504 * t864 * t524 * t445 + 0.4e1 / 0.9e1 * t119 * t510 * t511 * t518 + 0.8e1 / 0.81e2 * t101 * t485 * t373 * t377 * t433 * t445 + 0.44e2 / 0.81e2 * t119 * t492 * t373 * t409 * t433 * t445 - 0.32e2 / 0.81e2 * t504 * t864 * t525 - 0.8e1 / 0.81e2 * t504 * t523 * t524 * t355 - 0.40e2 / 0.81e2 * t452 * t864 * t544 - 0.16e2 / 0.81e2 * t452 * t523 * t543 * t518 - 0.8e1 / 0.81e2 * t101 * t497 * t498 * t518 + 0.16e2 / 0.81e2 * t905 * t537 * t486 * t347 * t65 * t366 + 0.8e1 / 0.27e2 * t534 * t537 * t433 * t65 * t366 * t445 - 0.88e2 / 0.729e3 * t63 * t374 * t455 * t918 + 0.4e1 / 0.27e2 * t268 * t903 * t6 * t537 * t925 * t366 + 0.4e1 / 0.243e3 * t534 * t537 * t925 * t431
  t953 = t445 ** 2
  t967 = f.my_piecewise5(t14, 0, t10, 0, -t773)
  t970 = t967 * t6 + 0.4e1 * t359
  t1009 = -0.40e2 / 0.81e2 * t905 * t374 * t455 * t400 * t347 * t445 + 0.16e2 / 0.81e2 * t268 * t532 * t6 * t540 - 0.32e2 / 0.243e3 * t534 * t374 / t535 / t376 * t918 * t64 * t405 + t119 * t438 * t410 * t953 / 0.3e1 - 0.20e2 / 0.729e3 * t101 / t405 / t450 / t25 * s2 * t398 * t918 + t119 * t407 * t410 * t970 / 0.27e2 - 0.10e2 / 0.243e3 * t119 / t367 * s2 * t410 * t918 - 0.4e1 / 0.27e2 * t57 * t62 * t347 * t507 - 0.2e1 / 0.27e2 * t101 * t397 * t398 * t970 - 0.8e1 / 0.81e2 * t57 * t62 * t348 * t458 - 0.4e1 / 0.27e2 * t452 * t453 * t456 * t953 - 0.2e1 / 0.27e2 * t101 * t432 * t398 * t953 - 0.8e1 / 0.81e2 * t63 * t450 * s2 * t457 - 0.4e1 / 0.27e2 * t63 * t340 * s2 * t506
  t1016 = t348 ** 2
  t1022 = t355 ** 2
  t1030 = f.my_piecewise3(t341, 0, 0.40e2 / 0.81e2 / t343 / t450 * t1016 - 0.16e2 / 0.9e1 * t345 * t348 * t355 + 0.4e1 / 0.3e1 * t352 * t1022 + 0.16e2 / 0.9e1 * t353 * t359 + 0.4e1 / 0.3e1 * t342 * t967)
  t1077 = -0.3e1 / 0.8e1 * t5 * t483 * (t934 + t1009) - 0.3e1 / 0.8e1 * t5 * t1030 * t54 * t382 - 0.3e1 / 0.2e1 * t5 * t364 * t415 - 0.3e1 / 0.2e1 * t5 * t392 * t415 - 0.9e1 / 0.4e1 * t5 * t396 * t465 + t5 * t422 * t415 - 0.3e1 / 0.2e1 * t5 * t426 * t465 - 0.3e1 / 0.2e1 * t5 * t430 * t552 - 0.5e1 / 0.9e1 * t5 * t471 * t415 + t5 * t475 * t465 / 0.2e1 - t5 * t479 * t552 / 0.2e1 - t5 * t363 * t94 * t382 / 0.2e1 + t5 * t391 * t138 * t382 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t421 * t209 * t382 + 0.10e2 / 0.27e2 * t5 * t470 * t857 * t382
  t1078 = f.my_piecewise3(t338, 0, t1077)
  d1111 = 0.4e1 * t336 + 0.4e1 * t557 + t6 * (t863 + t1078)

  res = {'v4rho4': d1111}
  return res
