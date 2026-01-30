"""Generated from gga_x_pbeint.mpl."""

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_muGE_raw = params.muGE
  if isinstance(params_muGE_raw, (str, bytes, dict)):
    params_muGE = params_muGE_raw
  else:
    try:
      params_muGE_seq = list(params_muGE_raw)
    except TypeError:
      params_muGE = params_muGE_raw
    else:
      params_muGE_seq = np.asarray(params_muGE_seq, dtype=np.float64)
      params_muGE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muGE_seq))
  params_muPBE_raw = params.muPBE
  if isinstance(params_muPBE_raw, (str, bytes, dict)):
    params_muPBE = params_muPBE_raw
  else:
    try:
      params_muPBE_seq = list(params_muPBE_raw)
    except TypeError:
      params_muPBE = params_muPBE_raw
    else:
      params_muPBE_seq = np.asarray(params_muPBE_seq, dtype=np.float64)
      params_muPBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muPBE_seq))

  pbeint_mu = lambda s: params_muGE + (params_muPBE - params_muGE) * params_alpha * s ** 2 / (1 + params_alpha * s ** 2)

  pbeint_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + pbeint_mu(s) * s ** 2))

  pbeint_f = lambda x: pbeint_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbeint_f, rs, z, xs0, xs1)

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_muGE_raw = params.muGE
  if isinstance(params_muGE_raw, (str, bytes, dict)):
    params_muGE = params_muGE_raw
  else:
    try:
      params_muGE_seq = list(params_muGE_raw)
    except TypeError:
      params_muGE = params_muGE_raw
    else:
      params_muGE_seq = np.asarray(params_muGE_seq, dtype=np.float64)
      params_muGE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muGE_seq))
  params_muPBE_raw = params.muPBE
  if isinstance(params_muPBE_raw, (str, bytes, dict)):
    params_muPBE = params_muPBE_raw
  else:
    try:
      params_muPBE_seq = list(params_muPBE_raw)
    except TypeError:
      params_muPBE = params_muPBE_raw
    else:
      params_muPBE_seq = np.asarray(params_muPBE_seq, dtype=np.float64)
      params_muPBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muPBE_seq))

  pbeint_mu = lambda s: params_muGE + (params_muPBE - params_muGE) * params_alpha * s ** 2 / (1 + params_alpha * s ** 2)

  pbeint_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + pbeint_mu(s) * s ** 2))

  pbeint_f = lambda x: pbeint_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbeint_f, rs, z, xs0, xs1)

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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_muGE_raw = params.muGE
  if isinstance(params_muGE_raw, (str, bytes, dict)):
    params_muGE = params_muGE_raw
  else:
    try:
      params_muGE_seq = list(params_muGE_raw)
    except TypeError:
      params_muGE = params_muGE_raw
    else:
      params_muGE_seq = np.asarray(params_muGE_seq, dtype=np.float64)
      params_muGE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muGE_seq))
  params_muPBE_raw = params.muPBE
  if isinstance(params_muPBE_raw, (str, bytes, dict)):
    params_muPBE = params_muPBE_raw
  else:
    try:
      params_muPBE_seq = list(params_muPBE_raw)
    except TypeError:
      params_muPBE = params_muPBE_raw
    else:
      params_muPBE_seq = np.asarray(params_muPBE_seq, dtype=np.float64)
      params_muPBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muPBE_seq))

  pbeint_mu = lambda s: params_muGE + (params_muPBE - params_muGE) * params_alpha * s ** 2 / (1 + params_alpha * s ** 2)

  pbeint_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + pbeint_mu(s) * s ** 2))

  pbeint_f = lambda x: pbeint_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbeint_f, rs, z, xs0, xs1)

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
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t20, t22, t23 * t19)
  t26 = t6 ** (0.1e1 / 0.3e1)
  t28 = params.muPBE - params.muGE
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = t28 * params.alpha * t30
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = 0.1e1 / t34
  t36 = t35 * s0
  t37 = r0 ** 2
  t38 = r0 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t41 = 0.1e1 / t39 / t37
  t42 = params.alpha * t30
  t43 = t36 * t41
  t46 = 0.1e1 + t42 * t43 / 0.24e2
  t47 = 0.1e1 / t46
  t53 = (params.muGE + t31 * t36 * t41 * t47 / 0.24e2) * t30
  t56 = params.kappa + t53 * t43 / 0.24e2
  t61 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t56)
  t65 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t61)
  t66 = r1 <= f.p.dens_threshold
  t67 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t68 = 0.1e1 + t67
  t69 = t68 <= f.p.zeta_threshold
  t70 = t68 ** (0.1e1 / 0.3e1)
  t72 = f.my_piecewise3(t69, t22, t70 * t68)
  t74 = t35 * s2
  t75 = r1 ** 2
  t76 = r1 ** (0.1e1 / 0.3e1)
  t77 = t76 ** 2
  t79 = 0.1e1 / t77 / t75
  t80 = t74 * t79
  t83 = 0.1e1 + t42 * t80 / 0.24e2
  t84 = 0.1e1 / t83
  t90 = (params.muGE + t31 * t74 * t79 * t84 / 0.24e2) * t30
  t93 = params.kappa + t90 * t80 / 0.24e2
  t98 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t93)
  t102 = f.my_piecewise3(t66, 0, -0.3e1 / 0.8e1 * t5 * t72 * t26 * t98)
  t103 = t6 ** 2
  t105 = t16 / t103
  t106 = t7 - t105
  t107 = f.my_piecewise5(t10, 0, t14, 0, t106)
  t110 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t107)
  t115 = t26 ** 2
  t116 = 0.1e1 / t115
  t120 = t5 * t25 * t116 * t61 / 0.8e1
  t121 = t5 * t25
  t122 = params.kappa ** 2
  t123 = t26 * t122
  t124 = t56 ** 2
  t125 = 0.1e1 / t124
  t128 = 0.1e1 / t39 / t37 / r0
  t133 = params.alpha ** 2
  t135 = t30 ** 2
  t136 = t28 * t133 * t135
  t138 = 0.1e1 / t33 / t32
  t139 = s0 ** 2
  t141 = t37 ** 2
  t145 = t46 ** 2
  t146 = 0.1e1 / t145
  t164 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t110 * t26 * t61 - t120 - 0.3e1 / 0.8e1 * t121 * t123 * t125 * ((-t31 * t36 * t128 * t47 / 0.9e1 + t136 * t138 * t139 / t38 / t141 / t37 * t146 / 0.216e3) * t30 * t43 / 0.24e2 - t53 * t36 * t128 / 0.9e1))
  t166 = f.my_piecewise5(t14, 0, t10, 0, -t106)
  t169 = f.my_piecewise3(t69, 0, 0.4e1 / 0.3e1 * t70 * t166)
  t177 = t5 * t72 * t116 * t98 / 0.8e1
  t179 = f.my_piecewise3(t66, 0, -0.3e1 / 0.8e1 * t5 * t169 * t26 * t98 - t177)
  vrho_0_ = t65 + t102 + t6 * (t164 + t179)
  t182 = -t7 - t105
  t183 = f.my_piecewise5(t10, 0, t14, 0, t182)
  t186 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t183)
  t192 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t186 * t26 * t61 - t120)
  t194 = f.my_piecewise5(t14, 0, t10, 0, -t182)
  t197 = f.my_piecewise3(t69, 0, 0.4e1 / 0.3e1 * t70 * t194)
  t202 = t5 * t72
  t203 = t93 ** 2
  t204 = 0.1e1 / t203
  t207 = 0.1e1 / t77 / t75 / r1
  t212 = s2 ** 2
  t214 = t75 ** 2
  t218 = t83 ** 2
  t219 = 0.1e1 / t218
  t237 = f.my_piecewise3(t66, 0, -0.3e1 / 0.8e1 * t5 * t197 * t26 * t98 - t177 - 0.3e1 / 0.8e1 * t202 * t123 * t204 * ((-t31 * t74 * t207 * t84 / 0.9e1 + t136 * t138 * t212 / t76 / t214 / t75 * t219 / 0.216e3) * t30 * t80 / 0.24e2 - t90 * t74 * t207 / 0.9e1))
  vrho_1_ = t65 + t102 + t6 * (t192 + t237)
  t240 = t35 * t41
  t262 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t121 * t123 * t125 * ((t31 * t240 * t47 / 0.24e2 - t136 * t138 * s0 / t38 / t141 / r0 * t146 / 0.576e3) * t30 * t43 / 0.24e2 + t53 * t240 / 0.24e2))
  vsigma_0_ = t6 * t262
  vsigma_1_ = 0.0e0
  t263 = t35 * t79
  t285 = f.my_piecewise3(t66, 0, -0.3e1 / 0.8e1 * t202 * t123 * t204 * ((t31 * t263 * t84 / 0.24e2 - t136 * t138 * s2 / t76 / t214 / r1 * t219 / 0.576e3) * t30 * t80 / 0.24e2 + t90 * t263 / 0.24e2))
  vsigma_2_ = t6 * t285
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
  params_alpha_raw = params.alpha
  if isinstance(params_alpha_raw, (str, bytes, dict)):
    params_alpha = params_alpha_raw
  else:
    try:
      params_alpha_seq = list(params_alpha_raw)
    except TypeError:
      params_alpha = params_alpha_raw
    else:
      params_alpha_seq = np.asarray(params_alpha_seq, dtype=np.float64)
      params_alpha = np.concatenate((np.array([np.nan], dtype=np.float64), params_alpha_seq))
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_muGE_raw = params.muGE
  if isinstance(params_muGE_raw, (str, bytes, dict)):
    params_muGE = params_muGE_raw
  else:
    try:
      params_muGE_seq = list(params_muGE_raw)
    except TypeError:
      params_muGE = params_muGE_raw
    else:
      params_muGE_seq = np.asarray(params_muGE_seq, dtype=np.float64)
      params_muGE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muGE_seq))
  params_muPBE_raw = params.muPBE
  if isinstance(params_muPBE_raw, (str, bytes, dict)):
    params_muPBE = params_muPBE_raw
  else:
    try:
      params_muPBE_seq = list(params_muPBE_raw)
    except TypeError:
      params_muPBE = params_muPBE_raw
    else:
      params_muPBE_seq = np.asarray(params_muPBE_seq, dtype=np.float64)
      params_muPBE = np.concatenate((np.array([np.nan], dtype=np.float64), params_muPBE_seq))

  pbeint_mu = lambda s: params_muGE + (params_muPBE - params_muGE) * params_alpha * s ** 2 / (1 + params_alpha * s ** 2)

  pbeint_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + pbeint_mu(s) * s ** 2))

  pbeint_f = lambda x: pbeint_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbeint_f, rs, z, xs0, xs1)

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
  t20 = params.muPBE - params.muGE
  t21 = t20 * params.alpha
  t22 = 6 ** (0.1e1 / 0.3e1)
  t23 = jnp.pi ** 2
  t24 = t23 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = 0.1e1 / t25
  t28 = t21 * t22 * t26
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = s0 * t30
  t32 = r0 ** 2
  t33 = t18 ** 2
  t35 = 0.1e1 / t33 / t32
  t38 = t31 * t35
  t41 = 0.1e1 + params.alpha * t22 * t26 * t38 / 0.24e2
  t42 = 0.1e1 / t41
  t43 = t35 * t42
  t48 = (params.muGE + t28 * t31 * t43 / 0.24e2) * t22
  t49 = t48 * t26
  t52 = params.kappa + t49 * t38 / 0.24e2
  t57 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t52)
  t61 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t57)
  t67 = t6 * t17
  t68 = params.kappa ** 2
  t69 = t18 * t68
  t70 = t52 ** 2
  t71 = 0.1e1 / t70
  t74 = 0.1e1 / t33 / t32 / r0
  t79 = params.alpha ** 2
  t81 = t22 ** 2
  t85 = t20 * t79 * t81 / t24 / t23
  t86 = s0 ** 2
  t88 = t32 ** 2
  t92 = t41 ** 2
  t93 = 0.1e1 / t92
  t112 = f.my_piecewise3(t2, 0, -t6 * t17 / t33 * t57 / 0.8e1 - 0.3e1 / 0.8e1 * t67 * t69 * t71 * ((-t28 * t31 * t74 * t42 / 0.9e1 + t85 * t86 * t29 / t18 / t88 / t32 * t93 / 0.108e3) * t22 * t26 * t38 / 0.24e2 - t49 * t31 * t74 / 0.9e1))
  vrho_0_ = 0.2e1 * r0 * t112 + 0.2e1 * t61
  t116 = t26 * t30
  t140 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t67 * t69 * t71 * ((t21 * t22 * t116 * t43 / 0.24e2 - t85 * s0 * t29 / t18 / t88 / r0 * t93 / 0.288e3) * t22 * t26 * t38 / 0.24e2 + t48 * t116 * t35 / 0.24e2))
  vsigma_0_ = 0.2e1 * r0 * t140
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
  t20 = 0.1e1 / t19
  t22 = params.muPBE - params.muGE
  t23 = t22 * params.alpha
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t30 = t23 * t24 * t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t36 = 0.1e1 / t19 / t34
  t39 = t33 * t36
  t42 = 0.1e1 + params.alpha * t24 * t28 * t39 / 0.24e2
  t43 = 0.1e1 / t42
  t44 = t36 * t43
  t49 = (params.muGE + t30 * t33 * t44 / 0.24e2) * t24
  t50 = t49 * t28
  t53 = params.kappa + t50 * t39 / 0.24e2
  t58 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t53)
  t62 = t6 * t17
  t63 = params.kappa ** 2
  t64 = t18 * t63
  t65 = t53 ** 2
  t66 = 0.1e1 / t65
  t67 = t34 * r0
  t69 = 0.1e1 / t19 / t67
  t70 = t69 * t43
  t74 = params.alpha ** 2
  t75 = t22 * t74
  t76 = t24 ** 2
  t78 = 0.1e1 / t26 / t25
  t80 = t75 * t76 * t78
  t81 = s0 ** 2
  t82 = t81 * t31
  t83 = t34 ** 2
  t86 = 0.1e1 / t18 / t83 / t34
  t87 = t42 ** 2
  t88 = 0.1e1 / t87
  t94 = (-t30 * t33 * t70 / 0.9e1 + t80 * t82 * t86 * t88 / 0.108e3) * t24
  t95 = t94 * t28
  t98 = t33 * t69
  t101 = t95 * t39 / 0.24e2 - t50 * t98 / 0.9e1
  t102 = t66 * t101
  t107 = f.my_piecewise3(t2, 0, -t6 * t17 * t20 * t58 / 0.8e1 - 0.3e1 / 0.8e1 * t62 * t64 * t102)
  t115 = t20 * t63
  t120 = 0.1e1 / t65 / t53
  t121 = t101 ** 2
  t127 = 0.1e1 / t19 / t83
  t141 = t25 ** 2
  t143 = t22 * t74 * params.alpha / t141
  t145 = t83 ** 2
  t150 = 0.1e1 / t87 / t42
  t170 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t58 / 0.12e2 - t62 * t115 * t102 / 0.4e1 + 0.3e1 / 0.4e1 * t62 * t64 * t120 * t121 - 0.3e1 / 0.8e1 * t62 * t64 * t66 * ((0.11e2 / 0.27e2 * t30 * t33 * t127 * t43 - t80 * t82 / t18 / t83 / t67 * t88 / 0.12e2 + 0.2e1 / 0.81e2 * t143 * t81 * s0 / t145 / t34 * t150) * t24 * t28 * t39 / 0.24e2 - 0.2e1 / 0.9e1 * t95 * t98 + 0.11e2 / 0.27e2 * t50 * t33 * t127))
  v2rho2_0_ = 0.2e1 * r0 * t170 + 0.4e1 * t107
  t173 = t23 * t24
  t174 = t28 * t32
  t182 = 0.1e1 / t18 / t83 / r0 * t88
  t187 = (t173 * t174 * t44 / 0.24e2 - t80 * s0 * t31 * t182 / 0.288e3) * t24
  t188 = t187 * t28
  t190 = t174 * t36
  t193 = t188 * t39 / 0.24e2 + t49 * t190 / 0.24e2
  t194 = t66 * t193
  t198 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t62 * t64 * t194)
  t241 = f.my_piecewise3(t2, 0, -t62 * t115 * t194 / 0.8e1 + 0.3e1 / 0.4e1 * t6 * t17 * t18 * t63 * t120 * t193 * t101 - 0.3e1 / 0.8e1 * t62 * t64 * t66 * ((-t173 * t174 * t70 / 0.9e1 + t80 * t31 * t86 * t88 * s0 / 0.36e2 - t143 * t81 / t145 / r0 * t150 / 0.108e3) * t24 * t28 * t39 / 0.24e2 - t188 * t98 / 0.9e1 + t94 * t190 / 0.24e2 - t49 * t174 * t69 / 0.9e1))
  v2rhosigma_0_ = 0.2e1 * r0 * t241 + 0.2e1 * t198
  t244 = t193 ** 2
  t272 = f.my_piecewise3(t2, 0, 0.3e1 / 0.4e1 * t62 * t64 * t120 * t244 - 0.3e1 / 0.8e1 * t62 * t64 * t66 * ((-t75 * t76 * t78 * t31 * t182 / 0.144e3 + t143 * s0 / t145 * t150 / 0.288e3) * t24 * t28 * t39 / 0.24e2 + t187 * t190 / 0.12e2))
  v2sigma2_0_ = 0.2e1 * r0 * t272
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
  t23 = params.muPBE - params.muGE
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = t25 * t29
  t31 = t23 * params.alpha * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = r0 ** 2
  t37 = 0.1e1 / t19 / t35
  t40 = t34 * t37
  t43 = 0.1e1 + params.alpha * t25 * t29 * t40 / 0.24e2
  t44 = 0.1e1 / t43
  t51 = (params.muGE + t31 * t34 * t37 * t44 / 0.24e2) * t25 * t29
  t54 = params.kappa + t51 * t40 / 0.24e2
  t59 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t54)
  t63 = t6 * t17
  t65 = params.kappa ** 2
  t66 = 0.1e1 / t19 * t65
  t67 = t54 ** 2
  t68 = 0.1e1 / t67
  t69 = t35 * r0
  t71 = 0.1e1 / t19 / t69
  t76 = params.alpha ** 2
  t78 = t25 ** 2
  t82 = t23 * t76 * t78 / t27 / t26
  t83 = s0 ** 2
  t84 = t83 * t32
  t85 = t35 ** 2
  t89 = t43 ** 2
  t90 = 0.1e1 / t89
  t97 = (-t31 * t34 * t71 * t44 / 0.9e1 + t82 * t84 / t18 / t85 / t35 * t90 / 0.108e3) * t25 * t29
  t100 = t34 * t71
  t103 = t97 * t40 / 0.24e2 - t51 * t100 / 0.9e1
  t104 = t68 * t103
  t108 = t18 * t65
  t110 = 0.1e1 / t67 / t54
  t111 = t103 ** 2
  t112 = t110 * t111
  t117 = 0.1e1 / t19 / t85
  t131 = t26 ** 2
  t132 = 0.1e1 / t131
  t133 = t23 * t76 * params.alpha * t132
  t134 = t83 * s0
  t135 = t85 ** 2
  t140 = 0.1e1 / t89 / t43
  t146 = (0.11e2 / 0.27e2 * t31 * t34 * t117 * t44 - t82 * t84 / t18 / t85 / t69 * t90 / 0.12e2 + 0.2e1 / 0.81e2 * t133 * t134 / t135 / t35 * t140) * t25 * t29
  t151 = t34 * t117
  t154 = t146 * t40 / 0.24e2 - 0.2e1 / 0.9e1 * t97 * t100 + 0.11e2 / 0.27e2 * t51 * t151
  t155 = t68 * t154
  t160 = f.my_piecewise3(t2, 0, t6 * t17 * t21 * t59 / 0.12e2 - t63 * t66 * t104 / 0.4e1 + 0.3e1 / 0.4e1 * t63 * t108 * t112 - 0.3e1 / 0.8e1 * t63 * t108 * t155)
  t176 = t67 ** 2
  t190 = t85 * r0
  t192 = 0.1e1 / t19 / t190
  t209 = t76 ** 2
  t211 = t83 ** 2
  t217 = t89 ** 2
  t242 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t37 * t59 + t63 * t21 * t65 * t104 / 0.4e1 + 0.3e1 / 0.4e1 * t63 * t66 * t112 - 0.3e1 / 0.8e1 * t63 * t66 * t155 - 0.9e1 / 0.4e1 * t63 * t108 / t176 * t111 * t103 + 0.9e1 / 0.4e1 * t6 * t17 * t18 * t65 * t110 * t103 * t154 - 0.3e1 / 0.8e1 * t63 * t108 * t68 * ((-0.154e3 / 0.81e2 * t31 * t34 * t192 * t44 + 0.341e3 / 0.486e3 * t82 * t84 / t18 / t135 * t90 - 0.38e2 / 0.81e2 * t133 * t134 / t135 / t69 * t140 + 0.2e1 / 0.243e3 * t23 * t209 * t132 * t211 / t19 / t135 / t190 / t217 * t30 * t33) * t25 * t29 * t40 / 0.24e2 - t146 * t100 / 0.3e1 + 0.11e2 / 0.9e1 * t97 * t151 - 0.154e3 / 0.81e2 * t51 * t34 * t192))
  v3rho3_0_ = 0.2e1 * r0 * t242 + 0.6e1 * t160

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
  t24 = params.muPBE - params.muGE
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = t26 * t30
  t32 = t24 * params.alpha * t31
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = s0 * t34
  t38 = t35 * t22
  t41 = 0.1e1 + params.alpha * t26 * t30 * t38 / 0.24e2
  t42 = 0.1e1 / t41
  t49 = (params.muGE + t32 * t35 * t22 * t42 / 0.24e2) * t26 * t30
  t52 = params.kappa + t49 * t38 / 0.24e2
  t57 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t52)
  t61 = t6 * t17
  t64 = params.kappa ** 2
  t65 = 0.1e1 / t20 / r0 * t64
  t66 = t52 ** 2
  t67 = 0.1e1 / t66
  t68 = t18 * r0
  t70 = 0.1e1 / t20 / t68
  t75 = params.alpha ** 2
  t77 = t26 ** 2
  t80 = t77 / t28 / t27
  t81 = t24 * t75 * t80
  t82 = s0 ** 2
  t83 = t82 * t33
  t84 = t18 ** 2
  t85 = t84 * t18
  t88 = t41 ** 2
  t89 = 0.1e1 / t88
  t96 = (-t32 * t35 * t70 * t42 / 0.9e1 + t81 * t83 / t19 / t85 * t89 / 0.108e3) * t26 * t30
  t99 = t35 * t70
  t102 = t96 * t38 / 0.24e2 - t49 * t99 / 0.9e1
  t103 = t67 * t102
  t107 = 0.1e1 / t20
  t108 = t107 * t64
  t110 = 0.1e1 / t66 / t52
  t111 = t102 ** 2
  t112 = t110 * t111
  t117 = 0.1e1 / t20 / t84
  t131 = t27 ** 2
  t132 = 0.1e1 / t131
  t133 = t24 * t75 * params.alpha * t132
  t134 = t82 * s0
  t135 = t84 ** 2
  t140 = 0.1e1 / t88 / t41
  t146 = (0.11e2 / 0.27e2 * t32 * t35 * t117 * t42 - t81 * t83 / t19 / t84 / t68 * t89 / 0.12e2 + 0.2e1 / 0.81e2 * t133 * t134 / t135 / t18 * t140) * t26 * t30
  t151 = t35 * t117
  t154 = t146 * t38 / 0.24e2 - 0.2e1 / 0.9e1 * t96 * t99 + 0.11e2 / 0.27e2 * t49 * t151
  t155 = t67 * t154
  t159 = t19 * t64
  t160 = t66 ** 2
  t161 = 0.1e1 / t160
  t163 = t161 * t111 * t102
  t168 = t6 * t17 * t19
  t169 = t64 * t110
  t171 = t169 * t102 * t154
  t174 = t84 * r0
  t176 = 0.1e1 / t20 / t174
  t193 = t75 ** 2
  t195 = t82 ** 2
  t197 = t24 * t193 * t132 * t195
  t201 = t88 ** 2
  t202 = 0.1e1 / t201
  t204 = t31 * t34
  t210 = (-0.154e3 / 0.81e2 * t32 * t35 * t176 * t42 + 0.341e3 / 0.486e3 * t81 * t83 / t19 / t135 * t89 - 0.38e2 / 0.81e2 * t133 * t134 / t135 / t68 * t140 + 0.2e1 / 0.243e3 * t197 / t20 / t135 / t174 * t202 * t204) * t26 * t30
  t217 = t35 * t176
  t220 = t210 * t38 / 0.24e2 - t146 * t99 / 0.3e1 + 0.11e2 / 0.9e1 * t96 * t151 - 0.154e3 / 0.81e2 * t49 * t217
  t221 = t67 * t220
  t226 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t57 + t61 * t65 * t103 / 0.4e1 + 0.3e1 / 0.4e1 * t61 * t108 * t112 - 0.3e1 / 0.8e1 * t61 * t108 * t155 - 0.9e1 / 0.4e1 * t61 * t159 * t163 + 0.9e1 / 0.4e1 * t168 * t171 - 0.3e1 / 0.8e1 * t61 * t159 * t221)
  t253 = t111 ** 2
  t263 = t154 ** 2
  t273 = 0.1e1 / t20 / t85
  t303 = t135 ** 2
  t333 = 0.10e2 / 0.27e2 * t6 * t17 * t70 * t57 - 0.5e1 / 0.9e1 * t61 * t22 * t64 * t103 - t61 * t65 * t112 + t61 * t65 * t155 / 0.2e1 - 0.3e1 * t61 * t108 * t163 + 0.3e1 * t6 * t17 * t107 * t171 - t61 * t108 * t221 / 0.2e1 + 0.9e1 * t61 * t159 / t160 / t52 * t253 - 0.27e2 / 0.2e1 * t168 * t64 * t161 * t111 * t154 + 0.9e1 / 0.4e1 * t61 * t159 * t110 * t263 + 0.3e1 * t168 * t169 * t102 * t220 - 0.3e1 / 0.8e1 * t61 * t159 * t67 * ((0.2618e4 / 0.243e3 * t32 * t35 * t273 * t42 - 0.3047e4 / 0.486e3 * t81 * t83 / t19 / t135 / r0 * t89 + 0.5126e4 / 0.729e3 * t133 * t134 / t135 / t84 * t140 - 0.196e3 / 0.729e3 * t197 / t20 / t135 / t85 * t202 * t204 + 0.16e2 / 0.2187e4 * t24 * t193 * params.alpha * t132 * t195 * s0 / t19 / t303 / r0 / t201 / t41 * t80 * t33) * t26 * t30 * t38 / 0.24e2 - 0.4e1 / 0.9e1 * t210 * t99 + 0.22e2 / 0.9e1 * t146 * t151 - 0.616e3 / 0.81e2 * t96 * t217 + 0.2618e4 / 0.243e3 * t49 * t35 * t273)
  t334 = f.my_piecewise3(t2, 0, t333)
  v4rho4_0_ = 0.2e1 * r0 * t334 + 0.8e1 * t226

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
  t32 = params.muPBE - params.muGE
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = t32 * params.alpha * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t39 * s0
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t46 = params.alpha * t34
  t47 = t40 * t45
  t50 = 0.1e1 + t46 * t47 / 0.24e2
  t51 = 0.1e1 / t50
  t57 = (params.muGE + t35 * t40 * t45 * t51 / 0.24e2) * t34
  t60 = params.kappa + t57 * t47 / 0.24e2
  t65 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t60)
  t69 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t70 = t69 * f.p.zeta_threshold
  t72 = f.my_piecewise3(t20, t70, t21 * t19)
  t73 = t30 ** 2
  t74 = 0.1e1 / t73
  t78 = t5 * t72 * t74 * t65 / 0.8e1
  t79 = t5 * t72
  t80 = params.kappa ** 2
  t81 = t30 * t80
  t82 = t60 ** 2
  t83 = 0.1e1 / t82
  t84 = t41 * r0
  t86 = 0.1e1 / t43 / t84
  t91 = params.alpha ** 2
  t93 = t34 ** 2
  t94 = t32 * t91 * t93
  t96 = 0.1e1 / t37 / t36
  t97 = s0 ** 2
  t98 = t96 * t97
  t99 = t41 ** 2
  t103 = t50 ** 2
  t104 = 0.1e1 / t103
  t110 = (-t35 * t40 * t86 * t51 / 0.9e1 + t94 * t98 / t42 / t99 / t41 * t104 / 0.216e3) * t34
  t113 = t40 * t86
  t116 = t110 * t47 / 0.24e2 - t57 * t113 / 0.9e1
  t117 = t83 * t116
  t118 = t81 * t117
  t122 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t65 - t78 - 0.3e1 / 0.8e1 * t79 * t118)
  t124 = r1 <= f.p.dens_threshold
  t125 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t126 = 0.1e1 + t125
  t127 = t126 <= f.p.zeta_threshold
  t128 = t126 ** (0.1e1 / 0.3e1)
  t130 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t133 = f.my_piecewise3(t127, 0, 0.4e1 / 0.3e1 * t128 * t130)
  t135 = t39 * s2
  t136 = r1 ** 2
  t137 = r1 ** (0.1e1 / 0.3e1)
  t138 = t137 ** 2
  t140 = 0.1e1 / t138 / t136
  t141 = t135 * t140
  t144 = 0.1e1 + t46 * t141 / 0.24e2
  t145 = 0.1e1 / t144
  t151 = (params.muGE + t35 * t135 * t140 * t145 / 0.24e2) * t34
  t154 = params.kappa + t151 * t141 / 0.24e2
  t159 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t154)
  t164 = f.my_piecewise3(t127, t70, t128 * t126)
  t168 = t5 * t164 * t74 * t159 / 0.8e1
  t170 = f.my_piecewise3(t124, 0, -0.3e1 / 0.8e1 * t5 * t133 * t30 * t159 - t168)
  t172 = t21 ** 2
  t173 = 0.1e1 / t172
  t174 = t26 ** 2
  t179 = t16 / t22 / t6
  t181 = -0.2e1 * t23 + 0.2e1 * t179
  t182 = f.my_piecewise5(t10, 0, t14, 0, t181)
  t186 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t173 * t174 + 0.4e1 / 0.3e1 * t21 * t182)
  t193 = t5 * t29 * t74 * t65
  t199 = 0.1e1 / t73 / t6
  t203 = t5 * t72 * t199 * t65 / 0.12e2
  t204 = t74 * t80
  t206 = t79 * t204 * t117
  t210 = t116 ** 2
  t216 = 0.1e1 / t43 / t99
  t230 = t36 ** 2
  t232 = t32 * t91 * params.alpha / t230
  t234 = t99 ** 2
  t258 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t186 * t30 * t65 - t193 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t29 * t118 + t203 - t206 / 0.4e1 + 0.3e1 / 0.4e1 * t79 * t81 / t82 / t60 * t210 - 0.3e1 / 0.8e1 * t79 * t81 * t83 * ((0.11e2 / 0.27e2 * t35 * t40 * t216 * t51 - t94 * t98 / t42 / t99 / t84 * t104 / 0.24e2 + t232 * t97 * s0 / t234 / t41 / t103 / t50 / 0.162e3) * t34 * t47 / 0.24e2 - 0.2e1 / 0.9e1 * t110 * t113 + 0.11e2 / 0.27e2 * t57 * t40 * t216))
  t259 = t128 ** 2
  t260 = 0.1e1 / t259
  t261 = t130 ** 2
  t265 = f.my_piecewise5(t14, 0, t10, 0, -t181)
  t269 = f.my_piecewise3(t127, 0, 0.4e1 / 0.9e1 * t260 * t261 + 0.4e1 / 0.3e1 * t128 * t265)
  t276 = t5 * t133 * t74 * t159
  t281 = t5 * t164 * t199 * t159 / 0.12e2
  t283 = f.my_piecewise3(t124, 0, -0.3e1 / 0.8e1 * t5 * t269 * t30 * t159 - t276 / 0.4e1 + t281)
  d11 = 0.2e1 * t122 + 0.2e1 * t170 + t6 * (t258 + t283)
  t286 = -t7 - t24
  t287 = f.my_piecewise5(t10, 0, t14, 0, t286)
  t290 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t287)
  t296 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t290 * t30 * t65 - t78)
  t298 = f.my_piecewise5(t14, 0, t10, 0, -t286)
  t301 = f.my_piecewise3(t127, 0, 0.4e1 / 0.3e1 * t128 * t298)
  t306 = t5 * t164
  t307 = t154 ** 2
  t308 = 0.1e1 / t307
  t309 = t136 * r1
  t311 = 0.1e1 / t138 / t309
  t316 = s2 ** 2
  t317 = t96 * t316
  t318 = t136 ** 2
  t322 = t144 ** 2
  t323 = 0.1e1 / t322
  t329 = (-t35 * t135 * t311 * t145 / 0.9e1 + t94 * t317 / t137 / t318 / t136 * t323 / 0.216e3) * t34
  t332 = t135 * t311
  t335 = t329 * t141 / 0.24e2 - t151 * t332 / 0.9e1
  t336 = t308 * t335
  t337 = t81 * t336
  t341 = f.my_piecewise3(t124, 0, -0.3e1 / 0.8e1 * t5 * t301 * t30 * t159 - t168 - 0.3e1 / 0.8e1 * t306 * t337)
  t345 = 0.2e1 * t179
  t346 = f.my_piecewise5(t10, 0, t14, 0, t345)
  t350 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t173 * t287 * t26 + 0.4e1 / 0.3e1 * t21 * t346)
  t357 = t5 * t290 * t74 * t65
  t365 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t350 * t30 * t65 - t357 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t290 * t118 - t193 / 0.8e1 + t203 - t206 / 0.8e1)
  t369 = f.my_piecewise5(t14, 0, t10, 0, -t345)
  t373 = f.my_piecewise3(t127, 0, 0.4e1 / 0.9e1 * t260 * t298 * t130 + 0.4e1 / 0.3e1 * t128 * t369)
  t380 = t5 * t301 * t74 * t159
  t387 = t306 * t204 * t336
  t390 = f.my_piecewise3(t124, 0, -0.3e1 / 0.8e1 * t5 * t373 * t30 * t159 - t380 / 0.8e1 - t276 / 0.8e1 + t281 - 0.3e1 / 0.8e1 * t5 * t133 * t337 - t387 / 0.8e1)
  d12 = t122 + t170 + t296 + t341 + t6 * (t365 + t390)
  t395 = t287 ** 2
  t399 = 0.2e1 * t23 + 0.2e1 * t179
  t400 = f.my_piecewise5(t10, 0, t14, 0, t399)
  t404 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t173 * t395 + 0.4e1 / 0.3e1 * t21 * t400)
  t411 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t404 * t30 * t65 - t357 / 0.4e1 + t203)
  t412 = t298 ** 2
  t416 = f.my_piecewise5(t14, 0, t10, 0, -t399)
  t420 = f.my_piecewise3(t127, 0, 0.4e1 / 0.9e1 * t260 * t412 + 0.4e1 / 0.3e1 * t128 * t416)
  t432 = t335 ** 2
  t438 = 0.1e1 / t138 / t318
  t451 = t318 ** 2
  t475 = f.my_piecewise3(t124, 0, -0.3e1 / 0.8e1 * t5 * t420 * t30 * t159 - t380 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t301 * t337 + t281 - t387 / 0.4e1 + 0.3e1 / 0.4e1 * t306 * t81 / t307 / t154 * t432 - 0.3e1 / 0.8e1 * t306 * t81 * t308 * ((0.11e2 / 0.27e2 * t35 * t135 * t438 * t145 - t94 * t317 / t137 / t318 / t309 * t323 / 0.24e2 + t232 * t316 * s2 / t451 / t136 / t322 / t144 / 0.162e3) * t34 * t141 / 0.24e2 - 0.2e1 / 0.9e1 * t329 * t332 + 0.11e2 / 0.27e2 * t151 * t135 * t438))
  d22 = 0.2e1 * t296 + 0.2e1 * t341 + t6 * (t411 + t475)
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
  t44 = params.muPBE - params.muGE
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = t44 * params.alpha * t46
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = t49 ** 2
  t51 = 0.1e1 / t50
  t52 = t51 * s0
  t53 = r0 ** 2
  t54 = r0 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t57 = 0.1e1 / t55 / t53
  t58 = params.alpha * t46
  t59 = t52 * t57
  t62 = 0.1e1 + t58 * t59 / 0.24e2
  t63 = 0.1e1 / t62
  t69 = (params.muGE + t47 * t52 * t57 * t63 / 0.24e2) * t46
  t72 = params.kappa + t69 * t59 / 0.24e2
  t77 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t72)
  t83 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t84 = t42 ** 2
  t85 = 0.1e1 / t84
  t90 = t5 * t83
  t91 = params.kappa ** 2
  t92 = t42 * t91
  t93 = t72 ** 2
  t94 = 0.1e1 / t93
  t95 = t53 * r0
  t97 = 0.1e1 / t55 / t95
  t102 = params.alpha ** 2
  t104 = t46 ** 2
  t105 = t44 * t102 * t104
  t108 = s0 ** 2
  t109 = 0.1e1 / t49 / t48 * t108
  t110 = t53 ** 2
  t114 = t62 ** 2
  t115 = 0.1e1 / t114
  t121 = (-t47 * t52 * t97 * t63 / 0.9e1 + t105 * t109 / t54 / t110 / t53 * t115 / 0.216e3) * t46
  t124 = t52 * t97
  t127 = t121 * t59 / 0.24e2 - t69 * t124 / 0.9e1
  t128 = t94 * t127
  t129 = t92 * t128
  t132 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t133 = t132 * f.p.zeta_threshold
  t135 = f.my_piecewise3(t20, t133, t21 * t19)
  t137 = 0.1e1 / t84 / t6
  t142 = t5 * t135
  t143 = t85 * t91
  t144 = t143 * t128
  t148 = 0.1e1 / t93 / t72
  t149 = t127 ** 2
  t150 = t148 * t149
  t151 = t92 * t150
  t155 = 0.1e1 / t55 / t110
  t169 = t48 ** 2
  t170 = 0.1e1 / t169
  t171 = t44 * t102 * params.alpha * t170
  t172 = t108 * s0
  t173 = t110 ** 2
  t178 = 0.1e1 / t114 / t62
  t183 = (0.11e2 / 0.27e2 * t47 * t52 * t155 * t63 - t105 * t109 / t54 / t110 / t95 * t115 / 0.24e2 + t171 * t172 / t173 / t53 * t178 / 0.162e3) * t46
  t188 = t52 * t155
  t191 = t183 * t59 / 0.24e2 - 0.2e1 / 0.9e1 * t121 * t124 + 0.11e2 / 0.27e2 * t69 * t188
  t192 = t94 * t191
  t193 = t92 * t192
  t197 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t77 - t5 * t83 * t85 * t77 / 0.4e1 - 0.3e1 / 0.4e1 * t90 * t129 + t5 * t135 * t137 * t77 / 0.12e2 - t142 * t144 / 0.4e1 + 0.3e1 / 0.4e1 * t142 * t151 - 0.3e1 / 0.8e1 * t142 * t193)
  t199 = r1 <= f.p.dens_threshold
  t200 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t201 = 0.1e1 + t200
  t202 = t201 <= f.p.zeta_threshold
  t203 = t201 ** (0.1e1 / 0.3e1)
  t204 = t203 ** 2
  t205 = 0.1e1 / t204
  t207 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t208 = t207 ** 2
  t212 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t216 = f.my_piecewise3(t202, 0, 0.4e1 / 0.9e1 * t205 * t208 + 0.4e1 / 0.3e1 * t203 * t212)
  t218 = t51 * s2
  t219 = r1 ** 2
  t220 = r1 ** (0.1e1 / 0.3e1)
  t221 = t220 ** 2
  t223 = 0.1e1 / t221 / t219
  t224 = t218 * t223
  t242 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + (params.muGE + t47 * t218 * t223 / (0.1e1 + t58 * t224 / 0.24e2) / 0.24e2) * t46 * t224 / 0.24e2))
  t248 = f.my_piecewise3(t202, 0, 0.4e1 / 0.3e1 * t203 * t207)
  t254 = f.my_piecewise3(t202, t133, t203 * t201)
  t260 = f.my_piecewise3(t199, 0, -0.3e1 / 0.8e1 * t5 * t216 * t42 * t242 - t5 * t248 * t85 * t242 / 0.4e1 + t5 * t254 * t137 * t242 / 0.12e2)
  t270 = t24 ** 2
  t274 = 0.6e1 * t33 - 0.6e1 * t16 / t270
  t275 = f.my_piecewise5(t10, 0, t14, 0, t274)
  t279 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t275)
  t298 = t110 * r0
  t300 = 0.1e1 / t55 / t298
  t317 = t102 ** 2
  t319 = t108 ** 2
  t325 = t114 ** 2
  t353 = t93 ** 2
  t376 = 0.1e1 / t84 / t24
  t381 = -0.3e1 / 0.8e1 * t5 * t279 * t42 * t77 - 0.9e1 / 0.8e1 * t5 * t41 * t129 - 0.3e1 / 0.4e1 * t90 * t144 - 0.9e1 / 0.8e1 * t90 * t193 + t142 * t137 * t91 * t128 / 0.4e1 - 0.3e1 / 0.8e1 * t142 * t143 * t192 - 0.3e1 / 0.8e1 * t142 * t92 * t94 * ((-0.154e3 / 0.81e2 * t47 * t52 * t300 * t63 + 0.341e3 / 0.972e3 * t105 * t109 / t54 / t173 * t115 - 0.19e2 / 0.162e3 * t171 * t172 / t173 / t95 * t178 + t44 * t317 * t170 * t319 / t55 / t173 / t298 / t325 * t46 * t51 / 0.486e3) * t46 * t59 / 0.24e2 - t183 * t124 / 0.3e1 + 0.11e2 / 0.9e1 * t121 * t188 - 0.154e3 / 0.81e2 * t69 * t52 * t300) + 0.9e1 / 0.4e1 * t90 * t151 + 0.3e1 / 0.4e1 * t142 * t143 * t150 - 0.9e1 / 0.4e1 * t142 * t92 / t353 * t149 * t127 + 0.9e1 / 0.4e1 * t5 * t135 * t42 * t91 * t148 * t127 * t191 - 0.3e1 / 0.8e1 * t5 * t41 * t85 * t77 + t5 * t83 * t137 * t77 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t135 * t376 * t77
  t382 = f.my_piecewise3(t1, 0, t381)
  t392 = f.my_piecewise5(t14, 0, t10, 0, -t274)
  t396 = f.my_piecewise3(t202, 0, -0.8e1 / 0.27e2 / t204 / t201 * t208 * t207 + 0.4e1 / 0.3e1 * t205 * t207 * t212 + 0.4e1 / 0.3e1 * t203 * t392)
  t414 = f.my_piecewise3(t199, 0, -0.3e1 / 0.8e1 * t5 * t396 * t42 * t242 - 0.3e1 / 0.8e1 * t5 * t216 * t85 * t242 + t5 * t248 * t137 * t242 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t254 * t376 * t242)
  d111 = 0.3e1 * t197 + 0.3e1 * t260 + t6 * (t382 + t414)

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
  t56 = params.muPBE - params.muGE
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = t56 * params.alpha * t58
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t63 = 0.1e1 / t62
  t64 = t63 * s0
  t65 = r0 ** 2
  t66 = r0 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t69 = 0.1e1 / t67 / t65
  t70 = params.alpha * t58
  t71 = t64 * t69
  t74 = 0.1e1 + t70 * t71 / 0.24e2
  t75 = 0.1e1 / t74
  t81 = (params.muGE + t59 * t64 * t69 * t75 / 0.24e2) * t58
  t84 = params.kappa + t81 * t71 / 0.24e2
  t89 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t84)
  t98 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t99 = t5 * t98
  t100 = params.kappa ** 2
  t101 = t54 * t100
  t102 = t84 ** 2
  t103 = 0.1e1 / t102
  t104 = t65 * r0
  t106 = 0.1e1 / t67 / t104
  t111 = params.alpha ** 2
  t113 = t58 ** 2
  t114 = t56 * t111 * t113
  t116 = 0.1e1 / t61 / t60
  t117 = s0 ** 2
  t118 = t116 * t117
  t119 = t65 ** 2
  t120 = t119 * t65
  t123 = t74 ** 2
  t124 = 0.1e1 / t123
  t130 = (-t59 * t64 * t106 * t75 / 0.9e1 + t114 * t118 / t66 / t120 * t124 / 0.216e3) * t58
  t133 = t64 * t106
  t136 = t130 * t71 / 0.24e2 - t81 * t133 / 0.9e1
  t137 = t103 * t136
  t138 = t101 * t137
  t143 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t144 = t5 * t143
  t145 = t54 ** 2
  t146 = 0.1e1 / t145
  t147 = t146 * t100
  t148 = t147 * t137
  t152 = 0.1e1 / t67 / t119
  t166 = t60 ** 2
  t167 = 0.1e1 / t166
  t168 = t56 * t111 * params.alpha * t167
  t169 = t117 * s0
  t170 = t119 ** 2
  t175 = 0.1e1 / t123 / t74
  t180 = (0.11e2 / 0.27e2 * t59 * t64 * t152 * t75 - t114 * t118 / t66 / t119 / t104 * t124 / 0.24e2 + t168 * t169 / t170 / t65 * t175 / 0.162e3) * t58
  t185 = t64 * t152
  t188 = t180 * t71 / 0.24e2 - 0.2e1 / 0.9e1 * t130 * t133 + 0.11e2 / 0.27e2 * t81 * t185
  t189 = t103 * t188
  t190 = t101 * t189
  t193 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t194 = t193 * f.p.zeta_threshold
  t196 = f.my_piecewise3(t20, t194, t21 * t19)
  t197 = t5 * t196
  t199 = 0.1e1 / t145 / t6
  t200 = t199 * t100
  t201 = t200 * t137
  t204 = t147 * t189
  t207 = t119 * r0
  t209 = 0.1e1 / t67 / t207
  t226 = t111 ** 2
  t228 = t117 ** 2
  t230 = t56 * t226 * t167 * t228
  t234 = t123 ** 2
  t235 = 0.1e1 / t234
  t237 = t58 * t63
  t242 = (-0.154e3 / 0.81e2 * t59 * t64 * t209 * t75 + 0.341e3 / 0.972e3 * t114 * t118 / t66 / t170 * t124 - 0.19e2 / 0.162e3 * t168 * t169 / t170 / t104 * t175 + t230 / t67 / t170 / t207 * t235 * t237 / 0.486e3) * t58
  t249 = t64 * t209
  t252 = t242 * t71 / 0.24e2 - t180 * t133 / 0.3e1 + 0.11e2 / 0.9e1 * t130 * t185 - 0.154e3 / 0.81e2 * t81 * t249
  t253 = t103 * t252
  t254 = t101 * t253
  t258 = 0.1e1 / t102 / t84
  t259 = t136 ** 2
  t260 = t258 * t259
  t261 = t101 * t260
  t264 = t147 * t260
  t267 = t102 ** 2
  t268 = 0.1e1 / t267
  t270 = t268 * t259 * t136
  t271 = t101 * t270
  t275 = t5 * t196 * t54
  t276 = t100 * t258
  t278 = t276 * t136 * t188
  t290 = 0.1e1 / t145 / t25
  t295 = -0.3e1 / 0.8e1 * t5 * t53 * t54 * t89 - 0.9e1 / 0.8e1 * t99 * t138 - 0.3e1 / 0.4e1 * t144 * t148 - 0.9e1 / 0.8e1 * t144 * t190 + t197 * t201 / 0.4e1 - 0.3e1 / 0.8e1 * t197 * t204 - 0.3e1 / 0.8e1 * t197 * t254 + 0.9e1 / 0.4e1 * t144 * t261 + 0.3e1 / 0.4e1 * t197 * t264 - 0.9e1 / 0.4e1 * t197 * t271 + 0.9e1 / 0.4e1 * t275 * t278 - 0.3e1 / 0.8e1 * t5 * t98 * t146 * t89 + t5 * t143 * t199 * t89 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t196 * t290 * t89
  t296 = f.my_piecewise3(t1, 0, t295)
  t298 = r1 <= f.p.dens_threshold
  t299 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t300 = 0.1e1 + t299
  t301 = t300 <= f.p.zeta_threshold
  t302 = t300 ** (0.1e1 / 0.3e1)
  t303 = t302 ** 2
  t305 = 0.1e1 / t303 / t300
  t307 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t308 = t307 ** 2
  t312 = 0.1e1 / t303
  t313 = t312 * t307
  t315 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t319 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t323 = f.my_piecewise3(t301, 0, -0.8e1 / 0.27e2 * t305 * t308 * t307 + 0.4e1 / 0.3e1 * t313 * t315 + 0.4e1 / 0.3e1 * t302 * t319)
  t325 = t63 * s2
  t326 = r1 ** 2
  t327 = r1 ** (0.1e1 / 0.3e1)
  t328 = t327 ** 2
  t330 = 0.1e1 / t328 / t326
  t331 = t325 * t330
  t349 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + (params.muGE + t59 * t325 * t330 / (0.1e1 + t70 * t331 / 0.24e2) / 0.24e2) * t58 * t331 / 0.24e2))
  t358 = f.my_piecewise3(t301, 0, 0.4e1 / 0.9e1 * t312 * t308 + 0.4e1 / 0.3e1 * t302 * t315)
  t365 = f.my_piecewise3(t301, 0, 0.4e1 / 0.3e1 * t302 * t307)
  t371 = f.my_piecewise3(t301, t194, t302 * t300)
  t377 = f.my_piecewise3(t298, 0, -0.3e1 / 0.8e1 * t5 * t323 * t54 * t349 - 0.3e1 / 0.8e1 * t5 * t358 * t146 * t349 + t5 * t365 * t199 * t349 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t371 * t290 * t349)
  t387 = 0.1e1 / t67 / t120
  t417 = t170 ** 2
  t458 = t259 ** 2
  t463 = t188 ** 2
  t474 = t197 * t200 * t189 / 0.2e1 - t197 * t147 * t253 / 0.2e1 + t144 * t201 - 0.3e1 / 0.8e1 * t197 * t101 * t103 * ((0.2618e4 / 0.243e3 * t59 * t64 * t387 * t75 - 0.3047e4 / 0.972e3 * t114 * t118 / t66 / t170 / r0 * t124 + 0.2563e4 / 0.1458e4 * t168 * t169 / t170 / t119 * t175 - 0.49e2 / 0.729e3 * t230 / t67 / t170 / t120 * t235 * t237 + 0.2e1 / 0.2187e4 * t56 * t226 * params.alpha * t167 * t228 * s0 / t66 / t417 / r0 / t234 / t74 * t113 * t116) * t58 * t71 / 0.24e2 - 0.4e1 / 0.9e1 * t242 * t133 + 0.22e2 / 0.9e1 * t180 * t185 - 0.616e3 / 0.81e2 * t130 * t249 + 0.2618e4 / 0.243e3 * t81 * t64 * t387) - 0.9e1 / 0.4e1 * t99 * t190 - t197 * t200 * t260 - 0.3e1 / 0.2e1 * t99 * t148 - 0.3e1 / 0.2e1 * t144 * t204 - 0.3e1 / 0.2e1 * t144 * t254 + 0.9e1 * t197 * t101 / t267 / t84 * t458 + 0.9e1 / 0.4e1 * t197 * t101 * t258 * t463 + 0.3e1 * t144 * t264 - 0.5e1 / 0.9e1 * t197 * t290 * t100 * t137
  t498 = 0.1e1 / t145 / t36
  t503 = t19 ** 2
  t506 = t30 ** 2
  t512 = t41 ** 2
  t521 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t522 = f.my_piecewise5(t10, 0, t14, 0, t521)
  t526 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t503 * t506 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t512 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t522)
  t548 = -0.3e1 / 0.2e1 * t5 * t53 * t138 + 0.9e1 / 0.2e1 * t99 * t261 - 0.9e1 * t144 * t271 - 0.3e1 * t197 * t147 * t270 - t5 * t53 * t146 * t89 / 0.2e1 + t5 * t98 * t199 * t89 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t143 * t290 * t89 + 0.10e2 / 0.27e2 * t5 * t196 * t498 * t89 - 0.3e1 / 0.8e1 * t5 * t526 * t54 * t89 + 0.3e1 * t275 * t276 * t252 * t136 + 0.9e1 * t5 * t143 * t54 * t278 - 0.27e2 / 0.2e1 * t275 * t100 * t268 * t259 * t188 + 0.3e1 * t5 * t196 * t146 * t278
  t550 = f.my_piecewise3(t1, 0, t474 + t548)
  t551 = t300 ** 2
  t554 = t308 ** 2
  t560 = t315 ** 2
  t566 = f.my_piecewise5(t14, 0, t10, 0, -t521)
  t570 = f.my_piecewise3(t301, 0, 0.40e2 / 0.81e2 / t303 / t551 * t554 - 0.16e2 / 0.9e1 * t305 * t308 * t315 + 0.4e1 / 0.3e1 * t312 * t560 + 0.16e2 / 0.9e1 * t313 * t319 + 0.4e1 / 0.3e1 * t302 * t566)
  t592 = f.my_piecewise3(t298, 0, -0.3e1 / 0.8e1 * t5 * t570 * t54 * t349 - t5 * t323 * t146 * t349 / 0.2e1 + t5 * t358 * t199 * t349 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t365 * t290 * t349 + 0.10e2 / 0.27e2 * t5 * t371 * t498 * t349)
  d1111 = 0.4e1 * t296 + 0.4e1 * t377 + t6 * (t550 + t592)

  res = {'v4rho4': d1111}
  return res
