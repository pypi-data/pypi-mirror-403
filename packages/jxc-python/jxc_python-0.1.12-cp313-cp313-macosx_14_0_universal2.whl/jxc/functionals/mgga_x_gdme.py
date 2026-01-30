"""Generated from mgga_x_gdme.mpl."""

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
  params_AA_raw = params.AA
  if isinstance(params_AA_raw, (str, bytes, dict)):
    params_AA = params_AA_raw
  else:
    try:
      params_AA_seq = list(params_AA_raw)
    except TypeError:
      params_AA = params_AA_raw
    else:
      params_AA_seq = np.asarray(params_AA_seq, dtype=np.float64)
      params_AA = np.concatenate((np.array([np.nan], dtype=np.float64), params_AA_seq))
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))

  gdme_at = (params_AA + 3 / 5 * params_BB) * 2 ** (1 / 3) / (X_FACTOR_C * (3 * jnp.pi ** 2) ** (2 / 3))

  gdme_bt = params_BB / (X_FACTOR_C * 2 ** (1 / 3) * (3 * jnp.pi ** 2) ** (4 / 3))

  gdme_f = lambda x, u, t: gdme_at + gdme_bt * ((params_a ** 2 - params_a + 1 / 2) * u - 2 * t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gdme_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
      f.u0(r0, r1, l0, l1),
      f.u1(r0, r1, l0, l1),
      f.tt0(r0, r1, tau0, tau1),
      f.tt1(r0, r1, tau0, tau1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_AA_raw = params.AA
  if isinstance(params_AA_raw, (str, bytes, dict)):
    params_AA = params_AA_raw
  else:
    try:
      params_AA_seq = list(params_AA_raw)
    except TypeError:
      params_AA = params_AA_raw
    else:
      params_AA_seq = np.asarray(params_AA_seq, dtype=np.float64)
      params_AA = np.concatenate((np.array([np.nan], dtype=np.float64), params_AA_seq))
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))

  gdme_at = (params_AA + 3 / 5 * params_BB) * 2 ** (1 / 3) / (X_FACTOR_C * (3 * jnp.pi ** 2) ** (2 / 3))

  gdme_bt = params_BB / (X_FACTOR_C * 2 ** (1 / 3) * (3 * jnp.pi ** 2) ** (4 / 3))

  gdme_f = lambda x, u, t: gdme_at + gdme_bt * ((params_a ** 2 - params_a + 1 / 2) * u - 2 * t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gdme_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.u0(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.u1(r0 / 2, r0 / 2, l0 / 2, l0 / 2),
      f.tt0(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
      f.tt1(r0 / 2, r0 / 2, tau0 / 2, tau0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_AA_raw = params.AA
  if isinstance(params_AA_raw, (str, bytes, dict)):
    params_AA = params_AA_raw
  else:
    try:
      params_AA_seq = list(params_AA_raw)
    except TypeError:
      params_AA = params_AA_raw
    else:
      params_AA_seq = np.asarray(params_AA_seq, dtype=np.float64)
      params_AA = np.concatenate((np.array([np.nan], dtype=np.float64), params_AA_seq))
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))

  gdme_at = (params_AA + 3 / 5 * params_BB) * 2 ** (1 / 3) / (X_FACTOR_C * (3 * jnp.pi ** 2) ** (2 / 3))

  gdme_bt = params_BB / (X_FACTOR_C * 2 ** (1 / 3) * (3 * jnp.pi ** 2) ** (4 / 3))

  gdme_f = lambda x, u, t: gdme_at + gdme_bt * ((params_a ** 2 - params_a + 1 / 2) * u - 2 * t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gdme_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t30 = 2 ** (0.1e1 / 0.3e1)
  t33 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t35 = 4 ** (0.1e1 / 0.3e1)
  t36 = t34 * t35
  t37 = jnp.pi ** 2
  t38 = t37 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t43 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t30 * t36 / t39
  t45 = params.BB * t2 * t34
  t46 = t30 ** 2
  t47 = t35 * t46
  t49 = 0.1e1 / t38 / t37
  t50 = params.a ** 2
  t51 = t50 - params.a + 0.1e1 / 0.2e1
  t52 = t51 * l0
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / r0
  t65 = t43 + t45 * t47 * t49 * (t52 * t56 - 0.2e1 * tau0 * t56) / 0.27e2
  t69 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t65)
  t70 = r1 <= f.p.dens_threshold
  t71 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t72 = 0.1e1 + t71
  t73 = t72 <= f.p.zeta_threshold
  t74 = t72 ** (0.1e1 / 0.3e1)
  t76 = f.my_piecewise3(t73, t22, t74 * t72)
  t77 = t76 * t26
  t78 = t51 * l1
  t79 = r1 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t82 = 0.1e1 / t80 / r1
  t91 = t43 + t45 * t47 * t49 * (t78 * t82 - 0.2e1 * tau1 * t82) / 0.27e2
  t95 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t77 * t91)
  t96 = t6 ** 2
  t98 = t16 / t96
  t99 = t7 - t98
  t100 = f.my_piecewise5(t10, 0, t14, 0, t99)
  t103 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t100)
  t108 = t26 ** 2
  t109 = 0.1e1 / t108
  t113 = t5 * t25 * t109 * t65 / 0.8e1
  t114 = t2 ** 2
  t115 = t114 * t4
  t117 = t115 * t27 * params.BB
  t118 = t46 * t49
  t119 = r0 ** 2
  t121 = 0.1e1 / t54 / t119
  t132 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t103 * t26 * t65 - t113 - t117 * t36 * t118 * (-0.5e1 / 0.3e1 * t52 * t121 + 0.10e2 / 0.3e1 * tau0 * t121) / 0.72e2)
  t134 = f.my_piecewise5(t14, 0, t10, 0, -t99)
  t137 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t74 * t134)
  t145 = t5 * t76 * t109 * t91 / 0.8e1
  t147 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t137 * t26 * t91 - t145)
  vrho_0_ = t69 + t95 + t6 * (t132 + t147)
  t150 = -t7 - t98
  t151 = f.my_piecewise5(t10, 0, t14, 0, t150)
  t154 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t151)
  t160 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t154 * t26 * t65 - t113)
  t162 = f.my_piecewise5(t14, 0, t10, 0, -t150)
  t165 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t74 * t162)
  t171 = t115 * t77 * params.BB
  t172 = r1 ** 2
  t174 = 0.1e1 / t80 / t172
  t185 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t165 * t26 * t91 - t145 - t171 * t36 * t118 * (-0.5e1 / 0.3e1 * t78 * t174 + 0.10e2 / 0.3e1 * tau1 * t174) / 0.72e2)
  vrho_1_ = t69 + t95 + t6 * (t160 + t185)
  vsigma_0_ = 0.0e0
  vsigma_1_ = 0.0e0
  vsigma_2_ = 0.0e0
  t188 = t36 * t46
  t189 = t49 * t51
  t194 = f.my_piecewise3(t1, 0, -t117 * t188 * t189 * t56 / 0.72e2)
  vlapl_0_ = t6 * t194
  t199 = f.my_piecewise3(t70, 0, -t171 * t188 * t189 * t82 / 0.72e2)
  vlapl_1_ = t6 * t199
  t204 = f.my_piecewise3(t1, 0, t117 * t36 * t118 * t56 / 0.36e2)
  vtau_0_ = t6 * t204
  t209 = f.my_piecewise3(t70, 0, t171 * t36 * t118 * t82 / 0.36e2)
  vtau_1_ = t6 * t209
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  vsigma_0_ = _b(vsigma_0_)
  vsigma_1_ = _b(vsigma_1_)
  vsigma_2_ = _b(vsigma_2_)
  vlapl_0_ = _b(vlapl_0_)
  vlapl_1_ = _b(vlapl_1_)
  vtau_0_ = _b(vtau_0_)
  vtau_1_ = _b(vtau_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1), 'vsigma': jnp.stack([vsigma_0_, vsigma_1_, vsigma_2_], axis=-1), 'vlapl': jnp.stack([vlapl_0_, vlapl_1_], axis=-1), 'vtau':  jnp.stack([vtau_0_, vtau_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_AA_raw = params.AA
  if isinstance(params_AA_raw, (str, bytes, dict)):
    params_AA = params_AA_raw
  else:
    try:
      params_AA_seq = list(params_AA_raw)
    except TypeError:
      params_AA = params_AA_raw
    else:
      params_AA_seq = np.asarray(params_AA_seq, dtype=np.float64)
      params_AA = np.concatenate((np.array([np.nan], dtype=np.float64), params_AA_seq))
  params_BB_raw = params.BB
  if isinstance(params_BB_raw, (str, bytes, dict)):
    params_BB = params_BB_raw
  else:
    try:
      params_BB_seq = list(params_BB_raw)
    except TypeError:
      params_BB = params_BB_raw
    else:
      params_BB_seq = np.asarray(params_BB_seq, dtype=np.float64)
      params_BB = np.concatenate((np.array([np.nan], dtype=np.float64), params_BB_seq))
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))

  gdme_at = (params_AA + 3 / 5 * params_BB) * 2 ** (1 / 3) / (X_FACTOR_C * (3 * jnp.pi ** 2) ** (2 / 3))

  gdme_bt = params_BB / (X_FACTOR_C * 2 ** (1 / 3) * (3 * jnp.pi ** 2) ** (4 / 3))

  gdme_f = lambda x, u, t: gdme_at + gdme_bt * ((params_a ** 2 - params_a + 1 / 2) * u - 2 * t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, gdme_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t22 = 2 ** (0.1e1 / 0.3e1)
  t25 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = 4 ** (0.1e1 / 0.3e1)
  t28 = t26 * t27
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t38 = t22 ** 2
  t41 = 0.1e1 / t30 / t29
  t42 = params.a ** 2
  t43 = t42 - params.a + 0.1e1 / 0.2e1
  t44 = t43 * l0
  t45 = t18 ** 2
  t47 = 0.1e1 / t45 / r0
  t50 = tau0 * t38
  t58 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t22 * t28 / t31 + params.BB * t3 * t26 * t27 * t38 * t41 * (t44 * t38 * t47 - 0.2e1 * t50 * t47) / 0.27e2
  t62 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t58)
  t68 = t3 ** 2
  t69 = t68 * t5
  t73 = r0 ** 2
  t75 = 0.1e1 / t45 / t73
  t87 = f.my_piecewise3(t2, 0, -t6 * t17 / t45 * t58 / 0.8e1 - t69 * t19 * params.BB * t28 * t38 * t41 * (-0.5e1 / 0.3e1 * t44 * t38 * t75 + 0.10e2 / 0.3e1 * t50 * t75) / 0.72e2)
  vrho_0_ = 0.2e1 * r0 * t87 + 0.2e1 * t62
  vsigma_0_ = 0.0e0
  t92 = t17 / t18 / r0
  t100 = f.my_piecewise3(t2, 0, -t69 * t92 * params.BB * t28 * t22 * t41 * t43 / 0.36e2)
  vlapl_0_ = 0.2e1 * r0 * t100
  t109 = f.my_piecewise3(t2, 0, t69 * t92 * params.BB * t26 * t27 * t22 * t41 / 0.18e2)
  vtau_0_ = 0.2e1 * r0 * t109
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
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
  t21 = t17 / t19
  t24 = 2 ** (0.1e1 / 0.3e1)
  t27 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t27
  t29 = 4 ** (0.1e1 / 0.3e1)
  t30 = t28 * t29
  t31 = jnp.pi ** 2
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t40 = t24 ** 2
  t43 = 0.1e1 / t32 / t31
  t44 = params.a ** 2
  t46 = (t44 - params.a + 0.1e1 / 0.2e1) * l0
  t48 = 0.1e1 / t19 / r0
  t51 = tau0 * t40
  t59 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t24 * t30 / t33 + params.BB * t3 * t28 * t29 * t40 * t43 * (t46 * t40 * t48 - 0.2e1 * t51 * t48) / 0.27e2
  t63 = t3 ** 2
  t64 = t63 * t5
  t67 = t64 * t17 * t18 * params.BB
  t68 = t40 * t43
  t69 = r0 ** 2
  t71 = 0.1e1 / t19 / t69
  t79 = t30 * t68 * (-0.5e1 / 0.3e1 * t46 * t40 * t71 + 0.10e2 / 0.3e1 * t51 * t71)
  t83 = f.my_piecewise3(t2, 0, -t6 * t21 * t59 / 0.8e1 - t67 * t79 / 0.72e2)
  t95 = 0.1e1 / t19 / t69 / r0
  t107 = f.my_piecewise3(t2, 0, t6 * t17 * t48 * t59 / 0.12e2 - t64 * t21 * params.BB * t79 / 0.108e3 - t67 * t30 * t68 * (0.40e2 / 0.9e1 * t46 * t40 * t95 - 0.80e2 / 0.9e1 * t51 * t95) / 0.72e2)
  v2rho2_0_ = 0.2e1 * r0 * t107 + 0.4e1 * t83
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
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
  t21 = 0.1e1 / t19 / r0
  t22 = t17 * t21
  t25 = 2 ** (0.1e1 / 0.3e1)
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t28
  t30 = 4 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t41 = t25 ** 2
  t44 = 0.1e1 / t33 / t32
  t45 = params.a ** 2
  t47 = (t45 - params.a + 0.1e1 / 0.2e1) * l0
  t50 = tau0 * t41
  t58 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t25 * t31 / t34 + params.BB * t3 * t29 * t30 * t41 * t44 * (t47 * t41 * t21 - 0.2e1 * t50 * t21) / 0.27e2
  t62 = t3 ** 2
  t63 = t62 * t5
  t67 = t63 * t17 / t19 * params.BB
  t68 = t41 * t44
  t69 = r0 ** 2
  t71 = 0.1e1 / t19 / t69
  t79 = t31 * t68 * (-0.5e1 / 0.3e1 * t47 * t41 * t71 + 0.10e2 / 0.3e1 * t50 * t71)
  t84 = t63 * t17 * t18 * params.BB
  t87 = 0.1e1 / t19 / t69 / r0
  t95 = t31 * t68 * (0.40e2 / 0.9e1 * t47 * t41 * t87 - 0.80e2 / 0.9e1 * t50 * t87)
  t99 = f.my_piecewise3(t2, 0, t6 * t22 * t58 / 0.12e2 - t67 * t79 / 0.108e3 - t84 * t95 / 0.72e2)
  t111 = t69 ** 2
  t113 = 0.1e1 / t19 / t111
  t125 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t71 * t58 + t63 * t22 * params.BB * t79 / 0.108e3 - t67 * t95 / 0.72e2 - t84 * t31 * t68 * (-0.440e3 / 0.27e2 * t47 * t41 * t113 + 0.880e3 / 0.27e2 * t50 * t113) / 0.72e2)
  v3rho3_0_ = 0.2e1 * r0 * t125 + 0.6e1 * t99

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
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
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / t18
  t23 = t17 * t22
  t26 = 2 ** (0.1e1 / 0.3e1)
  t29 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t29
  t31 = 4 ** (0.1e1 / 0.3e1)
  t32 = t30 * t31
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t42 = t26 ** 2
  t45 = 0.1e1 / t34 / t33
  t46 = params.a ** 2
  t48 = (t46 - params.a + 0.1e1 / 0.2e1) * l0
  t50 = 0.1e1 / t20 / r0
  t53 = tau0 * t42
  t61 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t26 * t32 / t35 + params.BB * t3 * t30 * t31 * t42 * t45 * (t48 * t42 * t50 - 0.2e1 * t53 * t50) / 0.27e2
  t65 = t3 ** 2
  t66 = t65 * t5
  t69 = t66 * t17 * t50 * params.BB
  t70 = t42 * t45
  t78 = t32 * t70 * (-0.5e1 / 0.3e1 * t48 * t42 * t22 + 0.10e2 / 0.3e1 * t53 * t22)
  t84 = t66 * t17 / t20 * params.BB
  t87 = 0.1e1 / t20 / t18 / r0
  t95 = t32 * t70 * (0.40e2 / 0.9e1 * t48 * t42 * t87 - 0.80e2 / 0.9e1 * t53 * t87)
  t100 = t66 * t17 * t19 * params.BB
  t101 = t18 ** 2
  t103 = 0.1e1 / t20 / t101
  t111 = t32 * t70 * (-0.440e3 / 0.27e2 * t48 * t42 * t103 + 0.880e3 / 0.27e2 * t53 * t103)
  t115 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t61 + t69 * t78 / 0.108e3 - t84 * t95 / 0.72e2 - t100 * t111 / 0.72e2)
  t131 = 0.1e1 / t20 / t101 / r0
  t143 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t87 * t61 - 0.5e1 / 0.243e3 * t66 * t23 * params.BB * t78 + t69 * t95 / 0.54e2 - t84 * t111 / 0.54e2 - t100 * t32 * t70 * (0.6160e4 / 0.81e2 * t48 * t42 * t131 - 0.12320e5 / 0.81e2 * t53 * t131) / 0.72e2)
  v4rho4_0_ = 0.2e1 * r0 * t143 + 0.8e1 * t115

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
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
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t6 ** 2
  t23 = 0.1e1 / t22
  t24 = t16 * t23
  t25 = t7 - t24
  t26 = f.my_piecewise5(t10, 0, t14, 0, t25)
  t29 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t26)
  t30 = t6 ** (0.1e1 / 0.3e1)
  t31 = t29 * t30
  t34 = 2 ** (0.1e1 / 0.3e1)
  t37 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t37
  t39 = 4 ** (0.1e1 / 0.3e1)
  t40 = t38 * t39
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t47 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t34 * t40 / t43
  t49 = params.BB * t2 * t38
  t50 = t34 ** 2
  t51 = t39 * t50
  t53 = 0.1e1 / t42 / t41
  t54 = params.a ** 2
  t55 = t54 - params.a + 0.1e1 / 0.2e1
  t56 = t55 * l0
  t57 = r0 ** (0.1e1 / 0.3e1)
  t58 = t57 ** 2
  t60 = 0.1e1 / t58 / r0
  t69 = t47 + t49 * t51 * t53 * (t56 * t60 - 0.2e1 * tau0 * t60) / 0.27e2
  t73 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t74 = t73 * f.p.zeta_threshold
  t76 = f.my_piecewise3(t20, t74, t21 * t19)
  t77 = t30 ** 2
  t78 = 0.1e1 / t77
  t79 = t76 * t78
  t82 = t5 * t79 * t69 / 0.8e1
  t83 = t2 ** 2
  t84 = t83 * t4
  t87 = t84 * t76 * t30 * params.BB
  t88 = t50 * t53
  t89 = r0 ** 2
  t91 = 0.1e1 / t58 / t89
  t98 = t40 * t88 * (-0.5e1 / 0.3e1 * t56 * t91 + 0.10e2 / 0.3e1 * tau0 * t91)
  t102 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t69 - t82 - t87 * t98 / 0.72e2)
  t104 = r1 <= f.p.dens_threshold
  t105 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t106 = 0.1e1 + t105
  t107 = t106 <= f.p.zeta_threshold
  t108 = t106 ** (0.1e1 / 0.3e1)
  t110 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t113 = f.my_piecewise3(t107, 0, 0.4e1 / 0.3e1 * t108 * t110)
  t114 = t113 * t30
  t115 = t55 * l1
  t116 = r1 ** (0.1e1 / 0.3e1)
  t117 = t116 ** 2
  t119 = 0.1e1 / t117 / r1
  t128 = t47 + t49 * t51 * t53 * (t115 * t119 - 0.2e1 * tau1 * t119) / 0.27e2
  t133 = f.my_piecewise3(t107, t74, t108 * t106)
  t134 = t133 * t78
  t137 = t5 * t134 * t128 / 0.8e1
  t139 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t5 * t114 * t128 - t137)
  t141 = t21 ** 2
  t142 = 0.1e1 / t141
  t143 = t26 ** 2
  t148 = t16 / t22 / t6
  t150 = -0.2e1 * t23 + 0.2e1 * t148
  t151 = f.my_piecewise5(t10, 0, t14, 0, t150)
  t155 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t142 * t143 + 0.4e1 / 0.3e1 * t21 * t151)
  t162 = t5 * t29 * t78 * t69
  t169 = 0.1e1 / t77 / t6
  t173 = t5 * t76 * t169 * t69 / 0.12e2
  t176 = t84 * t79 * params.BB * t98
  t180 = 0.1e1 / t58 / t89 / r0
  t191 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t155 * t30 * t69 - t162 / 0.4e1 - t84 * t31 * params.BB * t98 / 0.36e2 + t173 - t176 / 0.108e3 - t87 * t40 * t88 * (0.40e2 / 0.9e1 * t56 * t180 - 0.80e2 / 0.9e1 * tau0 * t180) / 0.72e2)
  t192 = t108 ** 2
  t193 = 0.1e1 / t192
  t194 = t110 ** 2
  t198 = f.my_piecewise5(t14, 0, t10, 0, -t150)
  t202 = f.my_piecewise3(t107, 0, 0.4e1 / 0.9e1 * t193 * t194 + 0.4e1 / 0.3e1 * t108 * t198)
  t209 = t5 * t113 * t78 * t128
  t214 = t5 * t133 * t169 * t128 / 0.12e2
  t216 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t5 * t202 * t30 * t128 - t209 / 0.4e1 + t214)
  d11 = 0.2e1 * t102 + 0.2e1 * t139 + t6 * (t191 + t216)
  t219 = -t7 - t24
  t220 = f.my_piecewise5(t10, 0, t14, 0, t219)
  t223 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t220)
  t224 = t223 * t30
  t229 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t224 * t69 - t82)
  t231 = f.my_piecewise5(t14, 0, t10, 0, -t219)
  t234 = f.my_piecewise3(t107, 0, 0.4e1 / 0.3e1 * t108 * t231)
  t235 = t234 * t30
  t241 = t84 * t133 * t30 * params.BB
  t242 = r1 ** 2
  t244 = 0.1e1 / t117 / t242
  t251 = t40 * t88 * (-0.5e1 / 0.3e1 * t115 * t244 + 0.10e2 / 0.3e1 * tau1 * t244)
  t255 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t5 * t235 * t128 - t137 - t241 * t251 / 0.72e2)
  t259 = 0.2e1 * t148
  t260 = f.my_piecewise5(t10, 0, t14, 0, t259)
  t264 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t142 * t220 * t26 + 0.4e1 / 0.3e1 * t21 * t260)
  t271 = t5 * t223 * t78 * t69
  t280 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t264 * t30 * t69 - t271 / 0.8e1 - t84 * t224 * params.BB * t98 / 0.72e2 - t162 / 0.8e1 + t173 - t176 / 0.216e3)
  t284 = f.my_piecewise5(t14, 0, t10, 0, -t259)
  t288 = f.my_piecewise3(t107, 0, 0.4e1 / 0.9e1 * t193 * t231 * t110 + 0.4e1 / 0.3e1 * t108 * t284)
  t295 = t5 * t234 * t78 * t128
  t304 = t84 * t134 * params.BB * t251
  t307 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t5 * t288 * t30 * t128 - t295 / 0.8e1 - t209 / 0.8e1 + t214 - t84 * t114 * params.BB * t251 / 0.72e2 - t304 / 0.216e3)
  d12 = t102 + t139 + t229 + t255 + t6 * (t280 + t307)
  t312 = t220 ** 2
  t316 = 0.2e1 * t23 + 0.2e1 * t148
  t317 = f.my_piecewise5(t10, 0, t14, 0, t316)
  t321 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t142 * t312 + 0.4e1 / 0.3e1 * t21 * t317)
  t328 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t321 * t30 * t69 - t271 / 0.4e1 + t173)
  t329 = t231 ** 2
  t333 = f.my_piecewise5(t14, 0, t10, 0, -t316)
  t337 = f.my_piecewise3(t107, 0, 0.4e1 / 0.9e1 * t193 * t329 + 0.4e1 / 0.3e1 * t108 * t333)
  t350 = 0.1e1 / t117 / t242 / r1
  t361 = f.my_piecewise3(t104, 0, -0.3e1 / 0.8e1 * t5 * t337 * t30 * t128 - t295 / 0.4e1 - t84 * t235 * params.BB * t251 / 0.36e2 + t214 - t304 / 0.108e3 - t241 * t40 * t88 * (0.40e2 / 0.9e1 * t115 * t350 - 0.80e2 / 0.9e1 * tau1 * t350) / 0.72e2)
  d22 = 0.2e1 * t229 + 0.2e1 * t255 + t6 * (t328 + t361)
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
  t46 = 2 ** (0.1e1 / 0.3e1)
  t49 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t50 = 0.1e1 / t49
  t51 = 4 ** (0.1e1 / 0.3e1)
  t52 = t50 * t51
  t53 = jnp.pi ** 2
  t54 = t53 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t59 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t46 * t52 / t55
  t61 = params.BB * t2 * t50
  t62 = t46 ** 2
  t63 = t51 * t62
  t65 = 0.1e1 / t54 / t53
  t66 = params.a ** 2
  t67 = t66 - params.a + 0.1e1 / 0.2e1
  t68 = t67 * l0
  t69 = r0 ** (0.1e1 / 0.3e1)
  t70 = t69 ** 2
  t72 = 0.1e1 / t70 / r0
  t81 = t59 + t61 * t63 * t65 * (t68 * t72 - 0.2e1 * tau0 * t72) / 0.27e2
  t87 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t88 = t42 ** 2
  t89 = 0.1e1 / t88
  t90 = t87 * t89
  t94 = t2 ** 2
  t95 = t94 * t4
  t98 = t95 * t87 * t42 * params.BB
  t99 = t62 * t65
  t100 = r0 ** 2
  t102 = 0.1e1 / t70 / t100
  t109 = t52 * t99 * (-0.5e1 / 0.3e1 * t68 * t102 + 0.10e2 / 0.3e1 * tau0 * t102)
  t112 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t113 = t112 * f.p.zeta_threshold
  t115 = f.my_piecewise3(t20, t113, t21 * t19)
  t117 = 0.1e1 / t88 / t6
  t118 = t115 * t117
  t124 = t95 * t115 * t89 * params.BB
  t129 = t95 * t115 * t42 * params.BB
  t132 = 0.1e1 / t70 / t100 / r0
  t139 = t52 * t99 * (0.40e2 / 0.9e1 * t68 * t132 - 0.80e2 / 0.9e1 * tau0 * t132)
  t143 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t81 - t5 * t90 * t81 / 0.4e1 - t98 * t109 / 0.36e2 + t5 * t118 * t81 / 0.12e2 - t124 * t109 / 0.108e3 - t129 * t139 / 0.72e2)
  t145 = r1 <= f.p.dens_threshold
  t146 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t147 = 0.1e1 + t146
  t148 = t147 <= f.p.zeta_threshold
  t149 = t147 ** (0.1e1 / 0.3e1)
  t150 = t149 ** 2
  t151 = 0.1e1 / t150
  t153 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t154 = t153 ** 2
  t158 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t162 = f.my_piecewise3(t148, 0, 0.4e1 / 0.9e1 * t151 * t154 + 0.4e1 / 0.3e1 * t149 * t158)
  t165 = r1 ** (0.1e1 / 0.3e1)
  t166 = t165 ** 2
  t168 = 0.1e1 / t166 / r1
  t177 = t59 + t61 * t63 * t65 * (t67 * l1 * t168 - 0.2e1 * tau1 * t168) / 0.27e2
  t183 = f.my_piecewise3(t148, 0, 0.4e1 / 0.3e1 * t149 * t153)
  t189 = f.my_piecewise3(t148, t113, t149 * t147)
  t195 = f.my_piecewise3(t145, 0, -0.3e1 / 0.8e1 * t5 * t162 * t42 * t177 - t5 * t183 * t89 * t177 / 0.4e1 + t5 * t189 * t117 * t177 / 0.12e2)
  t205 = t24 ** 2
  t209 = 0.6e1 * t33 - 0.6e1 * t16 / t205
  t210 = f.my_piecewise5(t10, 0, t14, 0, t209)
  t214 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t210)
  t238 = 0.1e1 / t88 / t24
  t249 = t100 ** 2
  t251 = 0.1e1 / t70 / t249
  t262 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t214 * t42 * t81 - 0.3e1 / 0.8e1 * t5 * t41 * t89 * t81 - t95 * t43 * params.BB * t109 / 0.24e2 + t5 * t87 * t117 * t81 / 0.4e1 - t95 * t90 * params.BB * t109 / 0.36e2 - t98 * t139 / 0.24e2 - 0.5e1 / 0.36e2 * t5 * t115 * t238 * t81 + t95 * t118 * params.BB * t109 / 0.108e3 - t124 * t139 / 0.72e2 - t129 * t52 * t99 * (-0.440e3 / 0.27e2 * t68 * t251 + 0.880e3 / 0.27e2 * tau0 * t251) / 0.72e2)
  t272 = f.my_piecewise5(t14, 0, t10, 0, -t209)
  t276 = f.my_piecewise3(t148, 0, -0.8e1 / 0.27e2 / t150 / t147 * t154 * t153 + 0.4e1 / 0.3e1 * t151 * t153 * t158 + 0.4e1 / 0.3e1 * t149 * t272)
  t294 = f.my_piecewise3(t145, 0, -0.3e1 / 0.8e1 * t5 * t276 * t42 * t177 - 0.3e1 / 0.8e1 * t5 * t162 * t89 * t177 + t5 * t183 * t117 * t177 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t189 * t238 * t177)
  d111 = 0.3e1 * t143 + 0.3e1 * t195 + t6 * (t262 + t294)

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
  t58 = 2 ** (0.1e1 / 0.3e1)
  t61 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t62 = 0.1e1 / t61
  t63 = 4 ** (0.1e1 / 0.3e1)
  t64 = t62 * t63
  t65 = jnp.pi ** 2
  t66 = t65 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t71 = 0.2e1 / 0.9e1 * (params.AA + 0.3e1 / 0.5e1 * params.BB) * t58 * t64 / t67
  t73 = params.BB * t2 * t62
  t74 = t58 ** 2
  t75 = t63 * t74
  t77 = 0.1e1 / t66 / t65
  t78 = params.a ** 2
  t79 = t78 - params.a + 0.1e1 / 0.2e1
  t80 = t79 * l0
  t81 = r0 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t84 = 0.1e1 / t82 / r0
  t93 = t71 + t73 * t75 * t77 * (t80 * t84 - 0.2e1 * tau0 * t84) / 0.27e2
  t102 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t103 = t54 ** 2
  t104 = 0.1e1 / t103
  t105 = t102 * t104
  t109 = t2 ** 2
  t110 = t109 * t4
  t113 = t110 * t102 * t54 * params.BB
  t114 = t74 * t77
  t115 = r0 ** 2
  t117 = 0.1e1 / t82 / t115
  t124 = t64 * t114 * (-0.5e1 / 0.3e1 * t80 * t117 + 0.10e2 / 0.3e1 * tau0 * t117)
  t129 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t131 = 0.1e1 / t103 / t6
  t132 = t129 * t131
  t138 = t110 * t129 * t104 * params.BB
  t143 = t110 * t129 * t54 * params.BB
  t146 = 0.1e1 / t82 / t115 / r0
  t153 = t64 * t114 * (0.40e2 / 0.9e1 * t80 * t146 - 0.80e2 / 0.9e1 * tau0 * t146)
  t156 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t157 = t156 * f.p.zeta_threshold
  t159 = f.my_piecewise3(t20, t157, t21 * t19)
  t161 = 0.1e1 / t103 / t25
  t162 = t159 * t161
  t168 = t110 * t159 * t131 * params.BB
  t173 = t110 * t159 * t104 * params.BB
  t178 = t110 * t159 * t54 * params.BB
  t179 = t115 ** 2
  t181 = 0.1e1 / t82 / t179
  t188 = t64 * t114 * (-0.440e3 / 0.27e2 * t80 * t181 + 0.880e3 / 0.27e2 * tau0 * t181)
  t192 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t93 - 0.3e1 / 0.8e1 * t5 * t105 * t93 - t113 * t124 / 0.24e2 + t5 * t132 * t93 / 0.4e1 - t138 * t124 / 0.36e2 - t143 * t153 / 0.24e2 - 0.5e1 / 0.36e2 * t5 * t162 * t93 + t168 * t124 / 0.108e3 - t173 * t153 / 0.72e2 - t178 * t188 / 0.72e2)
  t194 = r1 <= f.p.dens_threshold
  t195 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t196 = 0.1e1 + t195
  t197 = t196 <= f.p.zeta_threshold
  t198 = t196 ** (0.1e1 / 0.3e1)
  t199 = t198 ** 2
  t201 = 0.1e1 / t199 / t196
  t203 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t204 = t203 ** 2
  t208 = 0.1e1 / t199
  t209 = t208 * t203
  t211 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t215 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t219 = f.my_piecewise3(t197, 0, -0.8e1 / 0.27e2 * t201 * t204 * t203 + 0.4e1 / 0.3e1 * t209 * t211 + 0.4e1 / 0.3e1 * t198 * t215)
  t222 = r1 ** (0.1e1 / 0.3e1)
  t223 = t222 ** 2
  t225 = 0.1e1 / t223 / r1
  t234 = t71 + t73 * t75 * t77 * (t79 * l1 * t225 - 0.2e1 * tau1 * t225) / 0.27e2
  t243 = f.my_piecewise3(t197, 0, 0.4e1 / 0.9e1 * t208 * t204 + 0.4e1 / 0.3e1 * t198 * t211)
  t250 = f.my_piecewise3(t197, 0, 0.4e1 / 0.3e1 * t198 * t203)
  t256 = f.my_piecewise3(t197, t157, t198 * t196)
  t262 = f.my_piecewise3(t194, 0, -0.3e1 / 0.8e1 * t5 * t219 * t54 * t234 - 0.3e1 / 0.8e1 * t5 * t243 * t104 * t234 + t5 * t250 * t131 * t234 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t256 * t161 * t234)
  t266 = 0.1e1 / t82 / t179 / r0
  t302 = t19 ** 2
  t305 = t30 ** 2
  t311 = t41 ** 2
  t320 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t321 = f.my_piecewise5(t10, 0, t14, 0, t320)
  t325 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t302 * t305 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t311 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t321)
  t343 = 0.1e1 / t103 / t36
  t348 = -t178 * t64 * t114 * (0.6160e4 / 0.81e2 * t80 * t266 - 0.12320e5 / 0.81e2 * tau0 * t266) / 0.72e2 - t110 * t105 * params.BB * t124 / 0.18e2 - t113 * t153 / 0.12e2 + t110 * t132 * params.BB * t124 / 0.27e2 - t138 * t153 / 0.18e2 - t143 * t188 / 0.18e2 - 0.5e1 / 0.243e3 * t110 * t162 * params.BB * t124 + t168 * t153 / 0.54e2 - t173 * t188 / 0.54e2 - t110 * t55 * params.BB * t124 / 0.18e2 - 0.3e1 / 0.8e1 * t5 * t325 * t54 * t93 - t5 * t53 * t104 * t93 / 0.2e1 + t5 * t102 * t131 * t93 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t129 * t161 * t93 + 0.10e2 / 0.27e2 * t5 * t159 * t343 * t93
  t349 = f.my_piecewise3(t1, 0, t348)
  t350 = t196 ** 2
  t353 = t204 ** 2
  t359 = t211 ** 2
  t365 = f.my_piecewise5(t14, 0, t10, 0, -t320)
  t369 = f.my_piecewise3(t197, 0, 0.40e2 / 0.81e2 / t199 / t350 * t353 - 0.16e2 / 0.9e1 * t201 * t204 * t211 + 0.4e1 / 0.3e1 * t208 * t359 + 0.16e2 / 0.9e1 * t209 * t215 + 0.4e1 / 0.3e1 * t198 * t365)
  t391 = f.my_piecewise3(t194, 0, -0.3e1 / 0.8e1 * t5 * t369 * t54 * t234 - t5 * t219 * t104 * t234 / 0.2e1 + t5 * t243 * t131 * t234 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t250 * t161 * t234 + 0.10e2 / 0.27e2 * t5 * t256 * t343 * t234)
  d1111 = 0.4e1 * t192 + 0.4e1 * t262 + t6 * (t349 + t391)

  res = {'v4rho4': d1111}
  return res
