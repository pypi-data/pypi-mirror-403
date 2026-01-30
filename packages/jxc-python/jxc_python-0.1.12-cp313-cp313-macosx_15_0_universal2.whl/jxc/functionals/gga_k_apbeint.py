"""Generated from gga_k_apbeint.mpl."""

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbeint_f, rs, z, xs0, xs1)

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbeint_f, rs, z, xs0, xs1)

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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbeint_f, rs, z, xs0, xs1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t23 * f.p.zeta_threshold
  t25 = t20 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = f.my_piecewise3(t21, t24, t26 * t20)
  t29 = t7 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
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
  t69 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t28 * t30 * t65)
  t70 = r1 <= f.p.dens_threshold
  t71 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t72 = 0.1e1 + t71
  t73 = t72 <= f.p.zeta_threshold
  t74 = t72 ** (0.1e1 / 0.3e1)
  t75 = t74 ** 2
  t77 = f.my_piecewise3(t73, t24, t75 * t72)
  t79 = t39 * s2
  t80 = r1 ** 2
  t81 = r1 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t84 = 0.1e1 / t82 / t80
  t85 = t79 * t84
  t88 = 0.1e1 + t46 * t85 / 0.24e2
  t89 = 0.1e1 / t88
  t95 = (params.muGE + t35 * t79 * t84 * t89 / 0.24e2) * t34
  t98 = params.kappa + t95 * t85 / 0.24e2
  t103 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t98)
  t107 = f.my_piecewise3(t70, 0, 0.3e1 / 0.20e2 * t6 * t77 * t30 * t103)
  t108 = t7 ** 2
  t110 = t17 / t108
  t111 = t8 - t110
  t112 = f.my_piecewise5(t11, 0, t15, 0, t111)
  t115 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t112)
  t120 = 0.1e1 / t29
  t124 = t6 * t28 * t120 * t65 / 0.10e2
  t125 = t6 * t28
  t126 = params.kappa ** 2
  t127 = t30 * t126
  t128 = t60 ** 2
  t129 = 0.1e1 / t128
  t132 = 0.1e1 / t43 / t41 / r0
  t137 = params.alpha ** 2
  t139 = t34 ** 2
  t140 = t32 * t137 * t139
  t142 = 0.1e1 / t37 / t36
  t143 = s0 ** 2
  t145 = t41 ** 2
  t149 = t50 ** 2
  t150 = 0.1e1 / t149
  t168 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t115 * t30 * t65 + t124 + 0.3e1 / 0.20e2 * t125 * t127 * t129 * ((-t35 * t40 * t132 * t51 / 0.9e1 + t140 * t142 * t143 / t42 / t145 / t41 * t150 / 0.216e3) * t34 * t47 / 0.24e2 - t57 * t40 * t132 / 0.9e1))
  t170 = f.my_piecewise5(t15, 0, t11, 0, -t111)
  t173 = f.my_piecewise3(t73, 0, 0.5e1 / 0.3e1 * t75 * t170)
  t181 = t6 * t77 * t120 * t103 / 0.10e2
  t183 = f.my_piecewise3(t70, 0, 0.3e1 / 0.20e2 * t6 * t173 * t30 * t103 + t181)
  vrho_0_ = t69 + t107 + t7 * (t168 + t183)
  t186 = -t8 - t110
  t187 = f.my_piecewise5(t11, 0, t15, 0, t186)
  t190 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t187)
  t196 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t190 * t30 * t65 + t124)
  t198 = f.my_piecewise5(t15, 0, t11, 0, -t186)
  t201 = f.my_piecewise3(t73, 0, 0.5e1 / 0.3e1 * t75 * t198)
  t206 = t6 * t77
  t207 = t98 ** 2
  t208 = 0.1e1 / t207
  t211 = 0.1e1 / t82 / t80 / r1
  t216 = s2 ** 2
  t218 = t80 ** 2
  t222 = t88 ** 2
  t223 = 0.1e1 / t222
  t241 = f.my_piecewise3(t70, 0, 0.3e1 / 0.20e2 * t6 * t201 * t30 * t103 + t181 + 0.3e1 / 0.20e2 * t206 * t127 * t208 * ((-t35 * t79 * t211 * t89 / 0.9e1 + t140 * t142 * t216 / t81 / t218 / t80 * t223 / 0.216e3) * t34 * t85 / 0.24e2 - t95 * t79 * t211 / 0.9e1))
  vrho_1_ = t69 + t107 + t7 * (t196 + t241)
  t244 = t39 * t45
  t266 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t125 * t127 * t129 * ((t35 * t244 * t51 / 0.24e2 - t140 * t142 * s0 / t42 / t145 / r0 * t150 / 0.576e3) * t34 * t47 / 0.24e2 + t57 * t244 / 0.24e2))
  vsigma_0_ = t7 * t266
  vsigma_1_ = 0.0e0
  t267 = t39 * t84
  t289 = f.my_piecewise3(t70, 0, 0.3e1 / 0.20e2 * t206 * t127 * t208 * ((t35 * t267 * t89 / 0.24e2 - t140 * t142 * s2 / t81 / t218 / r1 * t223 / 0.576e3) * t34 * t85 / 0.24e2 + t95 * t267 / 0.24e2))
  vsigma_2_ = t7 * t289
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

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pbeint_f, rs, z, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t24 = params.muPBE - params.muGE
  t25 = t24 * params.alpha
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t32 = t25 * t26 * t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = s0 * t34
  t36 = r0 ** 2
  t38 = 0.1e1 / t22 / t36
  t41 = t35 * t38
  t44 = 0.1e1 + params.alpha * t26 * t30 * t41 / 0.24e2
  t45 = 0.1e1 / t44
  t46 = t38 * t45
  t51 = (params.muGE + t32 * t35 * t46 / 0.24e2) * t26
  t52 = t51 * t30
  t55 = params.kappa + t52 * t41 / 0.24e2
  t60 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t55)
  t64 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t20 * t22 * t60)
  t70 = t7 * t20
  t71 = params.kappa ** 2
  t72 = t22 * t71
  t73 = t55 ** 2
  t74 = 0.1e1 / t73
  t77 = 0.1e1 / t22 / t36 / r0
  t82 = params.alpha ** 2
  t84 = t26 ** 2
  t88 = t24 * t82 * t84 / t28 / t27
  t89 = s0 ** 2
  t91 = t36 ** 2
  t95 = t44 ** 2
  t96 = 0.1e1 / t95
  t115 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t60 / 0.10e2 + 0.3e1 / 0.20e2 * t70 * t72 * t74 * ((-t32 * t35 * t77 * t45 / 0.9e1 + t88 * t89 * t33 / t21 / t91 / t36 * t96 / 0.108e3) * t26 * t30 * t41 / 0.24e2 - t52 * t35 * t77 / 0.9e1))
  vrho_0_ = 0.2e1 * r0 * t115 + 0.2e1 * t64
  t119 = t30 * t34
  t143 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t70 * t72 * t74 * ((t25 * t26 * t119 * t46 / 0.24e2 - t88 * s0 * t33 / t21 / t91 / r0 * t96 / 0.288e3) * t26 * t30 * t41 / 0.24e2 + t51 * t119 * t38 / 0.24e2))
  vsigma_0_ = 0.2e1 * r0 * t143
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
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t22 = 0.1e1 / t21
  t24 = params.muPBE - params.muGE
  t25 = t24 * params.alpha
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t32 = t25 * t26 * t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = s0 * t34
  t36 = r0 ** 2
  t37 = t21 ** 2
  t39 = 0.1e1 / t37 / t36
  t42 = t35 * t39
  t45 = 0.1e1 + params.alpha * t26 * t30 * t42 / 0.24e2
  t46 = 0.1e1 / t45
  t47 = t39 * t46
  t52 = (params.muGE + t32 * t35 * t47 / 0.24e2) * t26
  t53 = t52 * t30
  t56 = params.kappa + t53 * t42 / 0.24e2
  t61 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t56)
  t65 = t7 * t20
  t66 = params.kappa ** 2
  t67 = t37 * t66
  t68 = t56 ** 2
  t69 = 0.1e1 / t68
  t70 = t36 * r0
  t72 = 0.1e1 / t37 / t70
  t73 = t72 * t46
  t77 = params.alpha ** 2
  t78 = t24 * t77
  t79 = t26 ** 2
  t81 = 0.1e1 / t28 / t27
  t83 = t78 * t79 * t81
  t84 = s0 ** 2
  t85 = t84 * t33
  t86 = t36 ** 2
  t89 = 0.1e1 / t21 / t86 / t36
  t90 = t45 ** 2
  t91 = 0.1e1 / t90
  t97 = (-t32 * t35 * t73 / 0.9e1 + t83 * t85 * t89 * t91 / 0.108e3) * t26
  t98 = t97 * t30
  t101 = t35 * t72
  t104 = t98 * t42 / 0.24e2 - t53 * t101 / 0.9e1
  t105 = t69 * t104
  t110 = f.my_piecewise3(t2, 0, t7 * t20 * t22 * t61 / 0.10e2 + 0.3e1 / 0.20e2 * t65 * t67 * t105)
  t118 = t22 * t66
  t123 = 0.1e1 / t68 / t56
  t124 = t104 ** 2
  t130 = 0.1e1 / t37 / t86
  t144 = t27 ** 2
  t146 = t24 * t77 * params.alpha / t144
  t148 = t86 ** 2
  t153 = 0.1e1 / t90 / t45
  t173 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t61 / 0.30e2 + t65 * t118 * t105 / 0.5e1 - 0.3e1 / 0.10e2 * t65 * t67 * t123 * t124 + 0.3e1 / 0.20e2 * t65 * t67 * t69 * ((0.11e2 / 0.27e2 * t32 * t35 * t130 * t46 - t83 * t85 / t21 / t86 / t70 * t91 / 0.12e2 + 0.2e1 / 0.81e2 * t146 * t84 * s0 / t148 / t36 * t153) * t26 * t30 * t42 / 0.24e2 - 0.2e1 / 0.9e1 * t98 * t101 + 0.11e2 / 0.27e2 * t53 * t35 * t130))
  v2rho2_0_ = 0.2e1 * r0 * t173 + 0.4e1 * t110
  t176 = t25 * t26
  t177 = t30 * t34
  t185 = 0.1e1 / t21 / t86 / r0 * t91
  t190 = (t176 * t177 * t47 / 0.24e2 - t83 * s0 * t33 * t185 / 0.288e3) * t26
  t191 = t190 * t30
  t193 = t177 * t39
  t196 = t191 * t42 / 0.24e2 + t52 * t193 / 0.24e2
  t197 = t69 * t196
  t201 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t65 * t67 * t197)
  t244 = f.my_piecewise3(t2, 0, t65 * t118 * t197 / 0.10e2 - 0.3e1 / 0.10e2 * t7 * t20 * t37 * t66 * t123 * t196 * t104 + 0.3e1 / 0.20e2 * t65 * t67 * t69 * ((-t176 * t177 * t73 / 0.9e1 + t83 * t33 * t89 * t91 * s0 / 0.36e2 - t146 * t84 / t148 / r0 * t153 / 0.108e3) * t26 * t30 * t42 / 0.24e2 - t191 * t101 / 0.9e1 + t97 * t193 / 0.24e2 - t52 * t177 * t72 / 0.9e1))
  v2rhosigma_0_ = 0.2e1 * r0 * t244 + 0.2e1 * t201
  t247 = t196 ** 2
  t275 = f.my_piecewise3(t2, 0, -0.3e1 / 0.10e2 * t65 * t67 * t123 * t247 + 0.3e1 / 0.20e2 * t65 * t67 * t69 * ((-t78 * t79 * t81 * t33 * t185 / 0.144e3 + t146 * s0 / t148 * t153 / 0.288e3) * t26 * t30 * t42 / 0.24e2 + t190 * t193 / 0.12e2))
  v2sigma2_0_ = 0.2e1 * r0 * t275
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t23 = 0.1e1 / t21 / r0
  t25 = params.muPBE - params.muGE
  t27 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = 0.1e1 / t30
  t32 = t27 * t31
  t33 = t25 * params.alpha * t32
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = s0 * t35
  t37 = r0 ** 2
  t38 = t21 ** 2
  t40 = 0.1e1 / t38 / t37
  t43 = t36 * t40
  t46 = 0.1e1 + params.alpha * t27 * t31 * t43 / 0.24e2
  t47 = 0.1e1 / t46
  t54 = (params.muGE + t33 * t36 * t40 * t47 / 0.24e2) * t27 * t31
  t57 = params.kappa + t54 * t43 / 0.24e2
  t62 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t57)
  t66 = t7 * t20
  t68 = params.kappa ** 2
  t69 = 0.1e1 / t21 * t68
  t70 = t57 ** 2
  t71 = 0.1e1 / t70
  t72 = t37 * r0
  t74 = 0.1e1 / t38 / t72
  t79 = params.alpha ** 2
  t81 = t27 ** 2
  t85 = t25 * t79 * t81 / t29 / t28
  t86 = s0 ** 2
  t87 = t86 * t34
  t88 = t37 ** 2
  t92 = t46 ** 2
  t93 = 0.1e1 / t92
  t100 = (-t33 * t36 * t74 * t47 / 0.9e1 + t85 * t87 / t21 / t88 / t37 * t93 / 0.108e3) * t27 * t31
  t103 = t36 * t74
  t106 = t100 * t43 / 0.24e2 - t54 * t103 / 0.9e1
  t107 = t71 * t106
  t111 = t38 * t68
  t113 = 0.1e1 / t70 / t57
  t114 = t106 ** 2
  t115 = t113 * t114
  t120 = 0.1e1 / t38 / t88
  t134 = t28 ** 2
  t135 = 0.1e1 / t134
  t136 = t25 * t79 * params.alpha * t135
  t137 = t86 * s0
  t138 = t88 ** 2
  t143 = 0.1e1 / t92 / t46
  t149 = (0.11e2 / 0.27e2 * t33 * t36 * t120 * t47 - t85 * t87 / t21 / t88 / t72 * t93 / 0.12e2 + 0.2e1 / 0.81e2 * t136 * t137 / t138 / t37 * t143) * t27 * t31
  t154 = t36 * t120
  t157 = t149 * t43 / 0.24e2 - 0.2e1 / 0.9e1 * t100 * t103 + 0.11e2 / 0.27e2 * t54 * t154
  t158 = t71 * t157
  t163 = f.my_piecewise3(t2, 0, -t7 * t20 * t23 * t62 / 0.30e2 + t66 * t69 * t107 / 0.5e1 - 0.3e1 / 0.10e2 * t66 * t111 * t115 + 0.3e1 / 0.20e2 * t66 * t111 * t158)
  t181 = t70 ** 2
  t195 = t88 * r0
  t197 = 0.1e1 / t38 / t195
  t214 = t79 ** 2
  t216 = t86 ** 2
  t222 = t92 ** 2
  t247 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t37 * t62 - t66 * t23 * t68 * t107 / 0.10e2 - 0.3e1 / 0.5e1 * t66 * t69 * t115 + 0.3e1 / 0.10e2 * t66 * t69 * t158 + 0.9e1 / 0.10e2 * t66 * t111 / t181 * t114 * t106 - 0.9e1 / 0.10e2 * t7 * t20 * t38 * t68 * t113 * t106 * t157 + 0.3e1 / 0.20e2 * t66 * t111 * t71 * ((-0.154e3 / 0.81e2 * t33 * t36 * t197 * t47 + 0.341e3 / 0.486e3 * t85 * t87 / t21 / t138 * t93 - 0.38e2 / 0.81e2 * t136 * t137 / t138 / t72 * t143 + 0.2e1 / 0.243e3 * t25 * t214 * t135 * t216 / t38 / t138 / t195 / t222 * t32 * t35) * t27 * t31 * t43 / 0.24e2 - t149 * t103 / 0.3e1 + 0.11e2 / 0.9e1 * t100 * t154 - 0.154e3 / 0.81e2 * t54 * t36 * t197))
  v3rho3_0_ = 0.2e1 * r0 * t247 + 0.6e1 * t163

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** 2
  t22 = r0 ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t22 / t21
  t26 = params.muPBE - params.muGE
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = 0.1e1 / t31
  t33 = t28 * t32
  t34 = t26 * params.alpha * t33
  t35 = 2 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = s0 * t36
  t38 = t22 ** 2
  t40 = 0.1e1 / t38 / t21
  t43 = t37 * t40
  t46 = 0.1e1 + params.alpha * t28 * t32 * t43 / 0.24e2
  t47 = 0.1e1 / t46
  t54 = (params.muGE + t34 * t37 * t40 * t47 / 0.24e2) * t28 * t32
  t57 = params.kappa + t54 * t43 / 0.24e2
  t62 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t57)
  t66 = t7 * t20
  t69 = params.kappa ** 2
  t70 = 0.1e1 / t22 / r0 * t69
  t71 = t57 ** 2
  t72 = 0.1e1 / t71
  t73 = t21 * r0
  t75 = 0.1e1 / t38 / t73
  t80 = params.alpha ** 2
  t82 = t28 ** 2
  t85 = t82 / t30 / t29
  t86 = t26 * t80 * t85
  t87 = s0 ** 2
  t88 = t87 * t35
  t89 = t21 ** 2
  t90 = t89 * t21
  t93 = t46 ** 2
  t94 = 0.1e1 / t93
  t101 = (-t34 * t37 * t75 * t47 / 0.9e1 + t86 * t88 / t22 / t90 * t94 / 0.108e3) * t28 * t32
  t104 = t37 * t75
  t107 = t101 * t43 / 0.24e2 - t54 * t104 / 0.9e1
  t108 = t72 * t107
  t112 = 0.1e1 / t22
  t113 = t112 * t69
  t115 = 0.1e1 / t71 / t57
  t116 = t107 ** 2
  t117 = t115 * t116
  t122 = 0.1e1 / t38 / t89
  t136 = t29 ** 2
  t137 = 0.1e1 / t136
  t138 = t26 * t80 * params.alpha * t137
  t139 = t87 * s0
  t140 = t89 ** 2
  t145 = 0.1e1 / t93 / t46
  t151 = (0.11e2 / 0.27e2 * t34 * t37 * t122 * t47 - t86 * t88 / t22 / t89 / t73 * t94 / 0.12e2 + 0.2e1 / 0.81e2 * t138 * t139 / t140 / t21 * t145) * t28 * t32
  t156 = t37 * t122
  t159 = t151 * t43 / 0.24e2 - 0.2e1 / 0.9e1 * t101 * t104 + 0.11e2 / 0.27e2 * t54 * t156
  t160 = t72 * t159
  t164 = t38 * t69
  t165 = t71 ** 2
  t166 = 0.1e1 / t165
  t168 = t166 * t116 * t107
  t173 = t7 * t20 * t38
  t174 = t69 * t115
  t176 = t174 * t107 * t159
  t179 = t89 * r0
  t181 = 0.1e1 / t38 / t179
  t198 = t80 ** 2
  t200 = t87 ** 2
  t202 = t26 * t198 * t137 * t200
  t206 = t93 ** 2
  t207 = 0.1e1 / t206
  t209 = t33 * t36
  t215 = (-0.154e3 / 0.81e2 * t34 * t37 * t181 * t47 + 0.341e3 / 0.486e3 * t86 * t88 / t22 / t140 * t94 - 0.38e2 / 0.81e2 * t138 * t139 / t140 / t73 * t145 + 0.2e1 / 0.243e3 * t202 / t38 / t140 / t179 * t207 * t209) * t28 * t32
  t222 = t37 * t181
  t225 = t215 * t43 / 0.24e2 - t151 * t104 / 0.3e1 + 0.11e2 / 0.9e1 * t101 * t156 - 0.154e3 / 0.81e2 * t54 * t222
  t226 = t72 * t225
  t231 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 * t24 * t62 - t66 * t70 * t108 / 0.10e2 - 0.3e1 / 0.5e1 * t66 * t113 * t117 + 0.3e1 / 0.10e2 * t66 * t113 * t160 + 0.9e1 / 0.10e2 * t66 * t164 * t168 - 0.9e1 / 0.10e2 * t173 * t176 + 0.3e1 / 0.20e2 * t66 * t164 * t226)
  t261 = t116 ** 2
  t271 = t159 ** 2
  t281 = 0.1e1 / t38 / t90
  t311 = t140 ** 2
  t341 = -0.14e2 / 0.135e3 * t7 * t20 / t22 / t73 * t62 + 0.8e1 / 0.45e2 * t66 * t24 * t69 * t108 + 0.2e1 / 0.5e1 * t66 * t70 * t117 - t66 * t70 * t160 / 0.5e1 + 0.12e2 / 0.5e1 * t66 * t113 * t168 - 0.12e2 / 0.5e1 * t7 * t20 * t112 * t176 + 0.2e1 / 0.5e1 * t66 * t113 * t226 - 0.18e2 / 0.5e1 * t66 * t164 / t165 / t57 * t261 + 0.27e2 / 0.5e1 * t173 * t69 * t166 * t116 * t159 - 0.9e1 / 0.10e2 * t66 * t164 * t115 * t271 - 0.6e1 / 0.5e1 * t173 * t174 * t107 * t225 + 0.3e1 / 0.20e2 * t66 * t164 * t72 * ((0.2618e4 / 0.243e3 * t34 * t37 * t281 * t47 - 0.3047e4 / 0.486e3 * t86 * t88 / t22 / t140 / r0 * t94 + 0.5126e4 / 0.729e3 * t138 * t139 / t140 / t89 * t145 - 0.196e3 / 0.729e3 * t202 / t38 / t140 / t90 * t207 * t209 + 0.16e2 / 0.2187e4 * t26 * t198 * params.alpha * t137 * t200 * s0 / t22 / t311 / r0 / t206 / t46 * t85 * t35) * t28 * t32 * t43 / 0.24e2 - 0.4e1 / 0.9e1 * t215 * t104 + 0.22e2 / 0.9e1 * t151 * t156 - 0.616e3 / 0.81e2 * t101 * t222 + 0.2618e4 / 0.243e3 * t54 * t37 * t281)
  t342 = f.my_piecewise3(t2, 0, t341)
  v4rho4_0_ = 0.2e1 * r0 * t342 + 0.8e1 * t231

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t26 = t17 * t25
  t27 = t8 - t26
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t31 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t28)
  t32 = t7 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t35 = params.muPBE - params.muGE
  t37 = 6 ** (0.1e1 / 0.3e1)
  t38 = t35 * params.alpha * t37
  t39 = jnp.pi ** 2
  t40 = t39 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t43 = t42 * s0
  t44 = r0 ** 2
  t45 = r0 ** (0.1e1 / 0.3e1)
  t46 = t45 ** 2
  t48 = 0.1e1 / t46 / t44
  t49 = params.alpha * t37
  t50 = t43 * t48
  t53 = 0.1e1 + t49 * t50 / 0.24e2
  t54 = 0.1e1 / t53
  t60 = (params.muGE + t38 * t43 * t48 * t54 / 0.24e2) * t37
  t63 = params.kappa + t60 * t50 / 0.24e2
  t68 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t63)
  t72 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t73 = t72 ** 2
  t74 = t73 * f.p.zeta_threshold
  t76 = f.my_piecewise3(t21, t74, t23 * t20)
  t77 = 0.1e1 / t32
  t81 = t6 * t76 * t77 * t68 / 0.10e2
  t82 = t6 * t76
  t83 = params.kappa ** 2
  t84 = t33 * t83
  t85 = t63 ** 2
  t86 = 0.1e1 / t85
  t87 = t44 * r0
  t89 = 0.1e1 / t46 / t87
  t94 = params.alpha ** 2
  t96 = t37 ** 2
  t97 = t35 * t94 * t96
  t99 = 0.1e1 / t40 / t39
  t100 = s0 ** 2
  t101 = t99 * t100
  t102 = t44 ** 2
  t106 = t53 ** 2
  t107 = 0.1e1 / t106
  t113 = (-t38 * t43 * t89 * t54 / 0.9e1 + t97 * t101 / t45 / t102 / t44 * t107 / 0.216e3) * t37
  t116 = t43 * t89
  t119 = t113 * t50 / 0.24e2 - t60 * t116 / 0.9e1
  t120 = t86 * t119
  t121 = t84 * t120
  t125 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t33 * t68 + t81 + 0.3e1 / 0.20e2 * t82 * t121)
  t127 = r1 <= f.p.dens_threshold
  t128 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t129 = 0.1e1 + t128
  t130 = t129 <= f.p.zeta_threshold
  t131 = t129 ** (0.1e1 / 0.3e1)
  t132 = t131 ** 2
  t134 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t137 = f.my_piecewise3(t130, 0, 0.5e1 / 0.3e1 * t132 * t134)
  t139 = t42 * s2
  t140 = r1 ** 2
  t141 = r1 ** (0.1e1 / 0.3e1)
  t142 = t141 ** 2
  t144 = 0.1e1 / t142 / t140
  t145 = t139 * t144
  t148 = 0.1e1 + t49 * t145 / 0.24e2
  t149 = 0.1e1 / t148
  t155 = (params.muGE + t38 * t139 * t144 * t149 / 0.24e2) * t37
  t158 = params.kappa + t155 * t145 / 0.24e2
  t163 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t158)
  t168 = f.my_piecewise3(t130, t74, t132 * t129)
  t172 = t6 * t168 * t77 * t163 / 0.10e2
  t174 = f.my_piecewise3(t127, 0, 0.3e1 / 0.20e2 * t6 * t137 * t33 * t163 + t172)
  t176 = 0.1e1 / t22
  t177 = t28 ** 2
  t182 = t17 / t24 / t7
  t184 = -0.2e1 * t25 + 0.2e1 * t182
  t185 = f.my_piecewise5(t11, 0, t15, 0, t184)
  t189 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t176 * t177 + 0.5e1 / 0.3e1 * t23 * t185)
  t196 = t6 * t31 * t77 * t68
  t202 = 0.1e1 / t32 / t7
  t206 = t6 * t76 * t202 * t68 / 0.30e2
  t207 = t77 * t83
  t209 = t82 * t207 * t120
  t213 = t119 ** 2
  t219 = 0.1e1 / t46 / t102
  t233 = t39 ** 2
  t235 = t35 * t94 * params.alpha / t233
  t237 = t102 ** 2
  t261 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t189 * t33 * t68 + t196 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t31 * t121 - t206 + t209 / 0.5e1 - 0.3e1 / 0.10e2 * t82 * t84 / t85 / t63 * t213 + 0.3e1 / 0.20e2 * t82 * t84 * t86 * ((0.11e2 / 0.27e2 * t38 * t43 * t219 * t54 - t97 * t101 / t45 / t102 / t87 * t107 / 0.24e2 + t235 * t100 * s0 / t237 / t44 / t106 / t53 / 0.162e3) * t37 * t50 / 0.24e2 - 0.2e1 / 0.9e1 * t113 * t116 + 0.11e2 / 0.27e2 * t60 * t43 * t219))
  t262 = 0.1e1 / t131
  t263 = t134 ** 2
  t267 = f.my_piecewise5(t15, 0, t11, 0, -t184)
  t271 = f.my_piecewise3(t130, 0, 0.10e2 / 0.9e1 * t262 * t263 + 0.5e1 / 0.3e1 * t132 * t267)
  t278 = t6 * t137 * t77 * t163
  t283 = t6 * t168 * t202 * t163 / 0.30e2
  t285 = f.my_piecewise3(t127, 0, 0.3e1 / 0.20e2 * t6 * t271 * t33 * t163 + t278 / 0.5e1 - t283)
  d11 = 0.2e1 * t125 + 0.2e1 * t174 + t7 * (t261 + t285)
  t288 = -t8 - t26
  t289 = f.my_piecewise5(t11, 0, t15, 0, t288)
  t292 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t289)
  t298 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t292 * t33 * t68 + t81)
  t300 = f.my_piecewise5(t15, 0, t11, 0, -t288)
  t303 = f.my_piecewise3(t130, 0, 0.5e1 / 0.3e1 * t132 * t300)
  t308 = t6 * t168
  t309 = t158 ** 2
  t310 = 0.1e1 / t309
  t311 = t140 * r1
  t313 = 0.1e1 / t142 / t311
  t318 = s2 ** 2
  t319 = t99 * t318
  t320 = t140 ** 2
  t324 = t148 ** 2
  t325 = 0.1e1 / t324
  t331 = (-t38 * t139 * t313 * t149 / 0.9e1 + t97 * t319 / t141 / t320 / t140 * t325 / 0.216e3) * t37
  t334 = t139 * t313
  t337 = t331 * t145 / 0.24e2 - t155 * t334 / 0.9e1
  t338 = t310 * t337
  t339 = t84 * t338
  t343 = f.my_piecewise3(t127, 0, 0.3e1 / 0.20e2 * t6 * t303 * t33 * t163 + t172 + 0.3e1 / 0.20e2 * t308 * t339)
  t347 = 0.2e1 * t182
  t348 = f.my_piecewise5(t11, 0, t15, 0, t347)
  t352 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t176 * t289 * t28 + 0.5e1 / 0.3e1 * t23 * t348)
  t359 = t6 * t292 * t77 * t68
  t367 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t352 * t33 * t68 + t359 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t292 * t121 + t196 / 0.10e2 - t206 + t209 / 0.10e2)
  t371 = f.my_piecewise5(t15, 0, t11, 0, -t347)
  t375 = f.my_piecewise3(t130, 0, 0.10e2 / 0.9e1 * t262 * t300 * t134 + 0.5e1 / 0.3e1 * t132 * t371)
  t382 = t6 * t303 * t77 * t163
  t389 = t308 * t207 * t338
  t392 = f.my_piecewise3(t127, 0, 0.3e1 / 0.20e2 * t6 * t375 * t33 * t163 + t382 / 0.10e2 + t278 / 0.10e2 - t283 + 0.3e1 / 0.20e2 * t6 * t137 * t339 + t389 / 0.10e2)
  d12 = t125 + t174 + t298 + t343 + t7 * (t367 + t392)
  t397 = t289 ** 2
  t401 = 0.2e1 * t25 + 0.2e1 * t182
  t402 = f.my_piecewise5(t11, 0, t15, 0, t401)
  t406 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t176 * t397 + 0.5e1 / 0.3e1 * t23 * t402)
  t413 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t406 * t33 * t68 + t359 / 0.5e1 - t206)
  t414 = t300 ** 2
  t418 = f.my_piecewise5(t15, 0, t11, 0, -t401)
  t422 = f.my_piecewise3(t130, 0, 0.10e2 / 0.9e1 * t262 * t414 + 0.5e1 / 0.3e1 * t132 * t418)
  t434 = t337 ** 2
  t440 = 0.1e1 / t142 / t320
  t453 = t320 ** 2
  t477 = f.my_piecewise3(t127, 0, 0.3e1 / 0.20e2 * t6 * t422 * t33 * t163 + t382 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t303 * t339 - t283 + t389 / 0.5e1 - 0.3e1 / 0.10e2 * t308 * t84 / t309 / t158 * t434 + 0.3e1 / 0.20e2 * t308 * t84 * t310 * ((0.11e2 / 0.27e2 * t38 * t139 * t440 * t149 - t97 * t319 / t141 / t320 / t311 * t325 / 0.24e2 + t235 * t318 * s2 / t453 / t140 / t324 / t148 / 0.162e3) * t37 * t145 / 0.24e2 - 0.2e1 / 0.9e1 * t331 * t334 + 0.11e2 / 0.27e2 * t155 * t139 * t440))
  d22 = 0.2e1 * t298 + 0.2e1 * t343 + t7 * (t413 + t477)
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
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = 0.1e1 / t22
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t27 = -t17 * t25 + t8
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t29 = t28 ** 2
  t32 = t22 ** 2
  t34 = 0.1e1 / t24 / t7
  t37 = 0.2e1 * t17 * t34 - 0.2e1 * t25
  t38 = f.my_piecewise5(t11, 0, t15, 0, t37)
  t42 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t23 * t29 + 0.5e1 / 0.3e1 * t32 * t38)
  t43 = t7 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t46 = params.muPBE - params.muGE
  t48 = 6 ** (0.1e1 / 0.3e1)
  t49 = t46 * params.alpha * t48
  t50 = jnp.pi ** 2
  t51 = t50 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t54 = t53 * s0
  t55 = r0 ** 2
  t56 = r0 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t59 = 0.1e1 / t57 / t55
  t60 = params.alpha * t48
  t61 = t54 * t59
  t64 = 0.1e1 + t60 * t61 / 0.24e2
  t65 = 0.1e1 / t64
  t71 = (params.muGE + t49 * t54 * t59 * t65 / 0.24e2) * t48
  t74 = params.kappa + t71 * t61 / 0.24e2
  t79 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t74)
  t85 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t86 = 0.1e1 / t43
  t91 = t6 * t85
  t92 = params.kappa ** 2
  t93 = t44 * t92
  t94 = t74 ** 2
  t95 = 0.1e1 / t94
  t96 = t55 * r0
  t98 = 0.1e1 / t57 / t96
  t103 = params.alpha ** 2
  t105 = t48 ** 2
  t106 = t46 * t103 * t105
  t109 = s0 ** 2
  t110 = 0.1e1 / t51 / t50 * t109
  t111 = t55 ** 2
  t115 = t64 ** 2
  t116 = 0.1e1 / t115
  t122 = (-t49 * t54 * t98 * t65 / 0.9e1 + t106 * t110 / t56 / t111 / t55 * t116 / 0.216e3) * t48
  t125 = t54 * t98
  t128 = t122 * t61 / 0.24e2 - t71 * t125 / 0.9e1
  t129 = t95 * t128
  t130 = t93 * t129
  t133 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t134 = t133 ** 2
  t135 = t134 * f.p.zeta_threshold
  t137 = f.my_piecewise3(t21, t135, t32 * t20)
  t139 = 0.1e1 / t43 / t7
  t144 = t6 * t137
  t145 = t86 * t92
  t146 = t145 * t129
  t150 = 0.1e1 / t94 / t74
  t151 = t128 ** 2
  t152 = t150 * t151
  t153 = t93 * t152
  t157 = 0.1e1 / t57 / t111
  t171 = t50 ** 2
  t172 = 0.1e1 / t171
  t173 = t46 * t103 * params.alpha * t172
  t174 = t109 * s0
  t175 = t111 ** 2
  t180 = 0.1e1 / t115 / t64
  t185 = (0.11e2 / 0.27e2 * t49 * t54 * t157 * t65 - t106 * t110 / t56 / t111 / t96 * t116 / 0.24e2 + t173 * t174 / t175 / t55 * t180 / 0.162e3) * t48
  t190 = t54 * t157
  t193 = t185 * t61 / 0.24e2 - 0.2e1 / 0.9e1 * t122 * t125 + 0.11e2 / 0.27e2 * t71 * t190
  t194 = t95 * t193
  t195 = t93 * t194
  t199 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t42 * t44 * t79 + t6 * t85 * t86 * t79 / 0.5e1 + 0.3e1 / 0.10e2 * t91 * t130 - t6 * t137 * t139 * t79 / 0.30e2 + t144 * t146 / 0.5e1 - 0.3e1 / 0.10e2 * t144 * t153 + 0.3e1 / 0.20e2 * t144 * t195)
  t201 = r1 <= f.p.dens_threshold
  t202 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t203 = 0.1e1 + t202
  t204 = t203 <= f.p.zeta_threshold
  t205 = t203 ** (0.1e1 / 0.3e1)
  t206 = 0.1e1 / t205
  t208 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t209 = t208 ** 2
  t212 = t205 ** 2
  t214 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t218 = f.my_piecewise3(t204, 0, 0.10e2 / 0.9e1 * t206 * t209 + 0.5e1 / 0.3e1 * t212 * t214)
  t220 = t53 * s2
  t221 = r1 ** 2
  t222 = r1 ** (0.1e1 / 0.3e1)
  t223 = t222 ** 2
  t225 = 0.1e1 / t223 / t221
  t226 = t220 * t225
  t244 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + (params.muGE + t49 * t220 * t225 / (0.1e1 + t60 * t226 / 0.24e2) / 0.24e2) * t48 * t226 / 0.24e2))
  t250 = f.my_piecewise3(t204, 0, 0.5e1 / 0.3e1 * t212 * t208)
  t256 = f.my_piecewise3(t204, t135, t212 * t203)
  t262 = f.my_piecewise3(t201, 0, 0.3e1 / 0.20e2 * t6 * t218 * t44 * t244 + t6 * t250 * t86 * t244 / 0.5e1 - t6 * t256 * t139 * t244 / 0.30e2)
  t275 = t111 * r0
  t277 = 0.1e1 / t57 / t275
  t294 = t103 ** 2
  t296 = t109 ** 2
  t302 = t115 ** 2
  t336 = t24 ** 2
  t340 = 0.6e1 * t34 - 0.6e1 * t17 / t336
  t341 = f.my_piecewise5(t11, 0, t15, 0, t340)
  t345 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t341)
  t355 = t94 ** 2
  t378 = 0.1e1 / t43 / t24
  t383 = 0.3e1 / 0.5e1 * t91 * t146 + 0.9e1 / 0.20e2 * t91 * t195 - t144 * t139 * t92 * t129 / 0.10e2 + 0.3e1 / 0.10e2 * t144 * t145 * t194 + 0.3e1 / 0.20e2 * t144 * t93 * t95 * ((-0.154e3 / 0.81e2 * t49 * t54 * t277 * t65 + 0.341e3 / 0.972e3 * t106 * t110 / t56 / t175 * t116 - 0.19e2 / 0.162e3 * t173 * t174 / t175 / t96 * t180 + t46 * t294 * t172 * t296 / t57 / t175 / t275 / t302 * t48 * t53 / 0.486e3) * t48 * t61 / 0.24e2 - t185 * t125 / 0.3e1 + 0.11e2 / 0.9e1 * t122 * t190 - 0.154e3 / 0.81e2 * t71 * t54 * t277) + 0.9e1 / 0.20e2 * t6 * t42 * t130 + 0.3e1 / 0.20e2 * t6 * t345 * t44 * t79 - 0.9e1 / 0.10e2 * t91 * t153 - 0.3e1 / 0.5e1 * t144 * t145 * t152 + 0.9e1 / 0.10e2 * t144 * t93 / t355 * t151 * t128 - 0.9e1 / 0.10e2 * t6 * t137 * t44 * t92 * t150 * t128 * t193 + 0.3e1 / 0.10e2 * t6 * t42 * t86 * t79 - t6 * t85 * t139 * t79 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t137 * t378 * t79
  t384 = f.my_piecewise3(t1, 0, t383)
  t394 = f.my_piecewise5(t15, 0, t11, 0, -t340)
  t398 = f.my_piecewise3(t204, 0, -0.10e2 / 0.27e2 / t205 / t203 * t209 * t208 + 0.10e2 / 0.3e1 * t206 * t208 * t214 + 0.5e1 / 0.3e1 * t212 * t394)
  t416 = f.my_piecewise3(t201, 0, 0.3e1 / 0.20e2 * t6 * t398 * t44 * t244 + 0.3e1 / 0.10e2 * t6 * t218 * t86 * t244 - t6 * t250 * t139 * t244 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t256 * t378 * t244)
  d111 = 0.3e1 * t199 + 0.3e1 * t262 + t7 * (t384 + t416)

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
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t27 = -t17 * t25 + t8
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t31 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t28)
  t32 = t6 * t31
  t33 = t7 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t35 = params.kappa ** 2
  t36 = t34 * t35
  t37 = params.muPBE - params.muGE
  t39 = 6 ** (0.1e1 / 0.3e1)
  t40 = t37 * params.alpha * t39
  t41 = jnp.pi ** 2
  t42 = t41 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t44 = 0.1e1 / t43
  t45 = t44 * s0
  t46 = r0 ** 2
  t47 = r0 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t50 = 0.1e1 / t48 / t46
  t51 = params.alpha * t39
  t52 = t45 * t50
  t55 = 0.1e1 + t51 * t52 / 0.24e2
  t56 = 0.1e1 / t55
  t62 = (params.muGE + t40 * t45 * t50 * t56 / 0.24e2) * t39
  t65 = params.kappa + t62 * t52 / 0.24e2
  t66 = t65 ** 2
  t67 = 0.1e1 / t66
  t68 = t46 * r0
  t70 = 0.1e1 / t48 / t68
  t75 = params.alpha ** 2
  t77 = t39 ** 2
  t78 = t37 * t75 * t77
  t80 = 0.1e1 / t42 / t41
  t81 = s0 ** 2
  t82 = t80 * t81
  t83 = t46 ** 2
  t84 = t83 * t46
  t87 = t55 ** 2
  t88 = 0.1e1 / t87
  t94 = (-t40 * t45 * t70 * t56 / 0.9e1 + t78 * t82 / t47 / t84 * t88 / 0.216e3) * t39
  t97 = t45 * t70
  t100 = t94 * t52 / 0.24e2 - t62 * t97 / 0.9e1
  t101 = t67 * t100
  t102 = t36 * t101
  t105 = t33 ** 2
  t106 = t105 * t35
  t108 = 0.1e1 / t48 / t83
  t122 = t41 ** 2
  t123 = 0.1e1 / t122
  t124 = t37 * t75 * params.alpha * t123
  t125 = t81 * s0
  t126 = t83 ** 2
  t131 = 0.1e1 / t87 / t55
  t136 = (0.11e2 / 0.27e2 * t40 * t45 * t108 * t56 - t78 * t82 / t47 / t83 / t68 * t88 / 0.24e2 + t124 * t125 / t126 / t46 * t131 / 0.162e3) * t39
  t141 = t45 * t108
  t144 = t136 * t52 / 0.24e2 - 0.2e1 / 0.9e1 * t94 * t97 + 0.11e2 / 0.27e2 * t62 * t141
  t145 = t67 * t144
  t146 = t106 * t145
  t149 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t150 = t149 ** 2
  t151 = t150 * f.p.zeta_threshold
  t153 = f.my_piecewise3(t21, t151, t23 * t20)
  t154 = t6 * t153
  t156 = 0.1e1 / t33 / t7
  t157 = t156 * t35
  t158 = t157 * t101
  t161 = t36 * t145
  t164 = t83 * r0
  t166 = 0.1e1 / t48 / t164
  t183 = t75 ** 2
  t185 = t81 ** 2
  t187 = t37 * t183 * t123 * t185
  t191 = t87 ** 2
  t192 = 0.1e1 / t191
  t194 = t39 * t44
  t199 = (-0.154e3 / 0.81e2 * t40 * t45 * t166 * t56 + 0.341e3 / 0.972e3 * t78 * t82 / t47 / t126 * t88 - 0.19e2 / 0.162e3 * t124 * t125 / t126 / t68 * t131 + t187 / t48 / t126 / t164 * t192 * t194 / 0.486e3) * t39
  t206 = t45 * t166
  t209 = t199 * t52 / 0.24e2 - t136 * t97 / 0.3e1 + 0.11e2 / 0.9e1 * t94 * t141 - 0.154e3 / 0.81e2 * t62 * t206
  t210 = t67 * t209
  t211 = t106 * t210
  t214 = 0.1e1 / t22
  t215 = t28 ** 2
  t218 = t24 * t7
  t219 = 0.1e1 / t218
  t222 = 0.2e1 * t17 * t219 - 0.2e1 * t25
  t223 = f.my_piecewise5(t11, 0, t15, 0, t222)
  t227 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t214 * t215 + 0.5e1 / 0.3e1 * t23 * t223)
  t228 = t6 * t227
  t229 = t106 * t101
  t233 = 0.1e1 / t22 / t20
  t237 = t214 * t28
  t240 = t24 ** 2
  t241 = 0.1e1 / t240
  t244 = -0.6e1 * t17 * t241 + 0.6e1 * t219
  t245 = f.my_piecewise5(t11, 0, t15, 0, t244)
  t249 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t233 * t215 * t28 + 0.10e2 / 0.3e1 * t237 * t223 + 0.5e1 / 0.3e1 * t23 * t245)
  t255 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t65)
  t260 = 0.1e1 / t66 / t65
  t261 = t100 ** 2
  t262 = t260 * t261
  t263 = t106 * t262
  t266 = t36 * t262
  t269 = t66 ** 2
  t270 = 0.1e1 / t269
  t272 = t270 * t261 * t100
  t273 = t106 * t272
  t277 = t6 * t153 * t105
  t278 = t35 * t260
  t280 = t278 * t100 * t144
  t292 = 0.1e1 / t33 / t24
  t297 = 0.3e1 / 0.5e1 * t32 * t102 + 0.9e1 / 0.20e2 * t32 * t146 - t154 * t158 / 0.10e2 + 0.3e1 / 0.10e2 * t154 * t161 + 0.3e1 / 0.20e2 * t154 * t211 + 0.9e1 / 0.20e2 * t228 * t229 + 0.3e1 / 0.20e2 * t6 * t249 * t105 * t255 - 0.9e1 / 0.10e2 * t32 * t263 - 0.3e1 / 0.5e1 * t154 * t266 + 0.9e1 / 0.10e2 * t154 * t273 - 0.9e1 / 0.10e2 * t277 * t280 + 0.3e1 / 0.10e2 * t6 * t227 * t34 * t255 - t6 * t31 * t156 * t255 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t153 * t292 * t255
  t298 = f.my_piecewise3(t1, 0, t297)
  t300 = r1 <= f.p.dens_threshold
  t301 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t302 = 0.1e1 + t301
  t303 = t302 <= f.p.zeta_threshold
  t304 = t302 ** (0.1e1 / 0.3e1)
  t306 = 0.1e1 / t304 / t302
  t308 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t309 = t308 ** 2
  t313 = 0.1e1 / t304
  t314 = t313 * t308
  t316 = f.my_piecewise5(t15, 0, t11, 0, -t222)
  t319 = t304 ** 2
  t321 = f.my_piecewise5(t15, 0, t11, 0, -t244)
  t325 = f.my_piecewise3(t303, 0, -0.10e2 / 0.27e2 * t306 * t309 * t308 + 0.10e2 / 0.3e1 * t314 * t316 + 0.5e1 / 0.3e1 * t319 * t321)
  t327 = t44 * s2
  t328 = r1 ** 2
  t329 = r1 ** (0.1e1 / 0.3e1)
  t330 = t329 ** 2
  t332 = 0.1e1 / t330 / t328
  t333 = t327 * t332
  t351 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + (params.muGE + t40 * t327 * t332 / (0.1e1 + t51 * t333 / 0.24e2) / 0.24e2) * t39 * t333 / 0.24e2))
  t360 = f.my_piecewise3(t303, 0, 0.10e2 / 0.9e1 * t313 * t309 + 0.5e1 / 0.3e1 * t319 * t316)
  t367 = f.my_piecewise3(t303, 0, 0.5e1 / 0.3e1 * t319 * t308)
  t373 = f.my_piecewise3(t303, t151, t319 * t302)
  t379 = f.my_piecewise3(t300, 0, 0.3e1 / 0.20e2 * t6 * t325 * t105 * t351 + 0.3e1 / 0.10e2 * t6 * t360 * t34 * t351 - t6 * t367 * t156 * t351 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t373 * t292 * t351)
  t382 = 0.1e1 / t48 / t84
  t412 = t126 ** 2
  t469 = 0.3e1 / 0.20e2 * t154 * t106 * t67 * ((0.2618e4 / 0.243e3 * t40 * t45 * t382 * t56 - 0.3047e4 / 0.972e3 * t78 * t82 / t47 / t126 / r0 * t88 + 0.2563e4 / 0.1458e4 * t124 * t125 / t126 / t83 * t131 - 0.49e2 / 0.729e3 * t187 / t48 / t126 / t84 * t192 * t194 + 0.2e1 / 0.2187e4 * t37 * t183 * params.alpha * t123 * t185 * s0 / t47 / t412 / r0 / t191 / t55 * t77 * t80) * t39 * t52 / 0.24e2 - 0.4e1 / 0.9e1 * t199 * t97 + 0.22e2 / 0.9e1 * t136 * t141 - 0.616e3 / 0.81e2 * t94 * t206 + 0.2618e4 / 0.243e3 * t62 * t45 * t382) + 0.6e1 / 0.5e1 * t228 * t102 + 0.9e1 / 0.10e2 * t228 * t146 + 0.3e1 / 0.5e1 * t32 * t211 + 0.2e1 / 0.5e1 * t154 * t157 * t262 + 0.18e2 / 0.5e1 * t32 * t273 - t154 * t157 * t145 / 0.5e1 + 0.2e1 / 0.5e1 * t154 * t36 * t210 + 0.3e1 / 0.5e1 * t6 * t249 * t229 + 0.6e1 / 0.5e1 * t32 * t161 - 0.9e1 / 0.5e1 * t228 * t263 - 0.2e1 / 0.5e1 * t32 * t158 - 0.12e2 / 0.5e1 * t32 * t266
  t479 = t261 ** 2
  t484 = t144 ** 2
  t502 = 0.1e1 / t33 / t218
  t507 = t20 ** 2
  t510 = t215 ** 2
  t516 = t223 ** 2
  t525 = -0.24e2 * t241 + 0.24e2 * t17 / t240 / t7
  t526 = f.my_piecewise5(t11, 0, t15, 0, t525)
  t530 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t507 * t510 - 0.20e2 / 0.9e1 * t233 * t215 * t223 + 0.10e2 / 0.3e1 * t214 * t516 + 0.40e2 / 0.9e1 * t237 * t245 + 0.5e1 / 0.3e1 * t23 * t526)
  t552 = 0.8e1 / 0.45e2 * t154 * t292 * t35 * t101 + 0.12e2 / 0.5e1 * t154 * t36 * t272 - 0.18e2 / 0.5e1 * t154 * t106 / t269 / t65 * t479 - 0.9e1 / 0.10e2 * t154 * t106 * t260 * t484 + 0.2e1 / 0.5e1 * t6 * t249 * t34 * t255 - t6 * t227 * t156 * t255 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t31 * t292 * t255 - 0.14e2 / 0.135e3 * t6 * t153 * t502 * t255 + 0.3e1 / 0.20e2 * t6 * t530 * t105 * t255 - 0.6e1 / 0.5e1 * t277 * t278 * t209 * t100 + 0.27e2 / 0.5e1 * t277 * t35 * t270 * t261 * t144 - 0.18e2 / 0.5e1 * t6 * t31 * t105 * t280 - 0.12e2 / 0.5e1 * t6 * t153 * t34 * t280
  t554 = f.my_piecewise3(t1, 0, t469 + t552)
  t555 = t302 ** 2
  t558 = t309 ** 2
  t564 = t316 ** 2
  t570 = f.my_piecewise5(t15, 0, t11, 0, -t525)
  t574 = f.my_piecewise3(t303, 0, 0.40e2 / 0.81e2 / t304 / t555 * t558 - 0.20e2 / 0.9e1 * t306 * t309 * t316 + 0.10e2 / 0.3e1 * t313 * t564 + 0.40e2 / 0.9e1 * t314 * t321 + 0.5e1 / 0.3e1 * t319 * t570)
  t596 = f.my_piecewise3(t300, 0, 0.3e1 / 0.20e2 * t6 * t574 * t105 * t351 + 0.2e1 / 0.5e1 * t6 * t325 * t34 * t351 - t6 * t360 * t156 * t351 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t367 * t292 * t351 - 0.14e2 / 0.135e3 * t6 * t373 * t502 * t351)
  d1111 = 0.4e1 * t298 + 0.4e1 * t379 + t7 * (t554 + t596)

  res = {'v4rho4': d1111}
  return res
