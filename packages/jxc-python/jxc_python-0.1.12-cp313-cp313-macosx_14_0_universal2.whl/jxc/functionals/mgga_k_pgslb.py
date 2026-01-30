"""Generated from mgga_k_pgslb.mpl."""

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
  params_pgslb_beta_raw = params.pgslb_beta
  if isinstance(params_pgslb_beta_raw, (str, bytes, dict)):
    params_pgslb_beta = params_pgslb_beta_raw
  else:
    try:
      params_pgslb_beta_seq = list(params_pgslb_beta_raw)
    except TypeError:
      params_pgslb_beta = params_pgslb_beta_raw
    else:
      params_pgslb_beta_seq = np.asarray(params_pgslb_beta_seq, dtype=np.float64)
      params_pgslb_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_beta_seq))
  params_pgslb_mu_raw = params.pgslb_mu
  if isinstance(params_pgslb_mu_raw, (str, bytes, dict)):
    params_pgslb_mu = params_pgslb_mu_raw
  else:
    try:
      params_pgslb_mu_seq = list(params_pgslb_mu_raw)
    except TypeError:
      params_pgslb_mu = params_pgslb_mu_raw
    else:
      params_pgslb_mu_seq = np.asarray(params_pgslb_mu_seq, dtype=np.float64)
      params_pgslb_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_mu_seq))

  pgslb_f0 = lambda s, q: 5 / 3 * s ** 2 + jnp.exp(-params_pgslb_mu * s ** 2) + params_pgslb_beta * q ** 2

  pgslb_f = lambda x, u: pgslb_f0(X2S * x, jnp.zeros_like(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pgslb_f, rs, z, xs0, xs1, u0, u1)

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
  params_pgslb_beta_raw = params.pgslb_beta
  if isinstance(params_pgslb_beta_raw, (str, bytes, dict)):
    params_pgslb_beta = params_pgslb_beta_raw
  else:
    try:
      params_pgslb_beta_seq = list(params_pgslb_beta_raw)
    except TypeError:
      params_pgslb_beta = params_pgslb_beta_raw
    else:
      params_pgslb_beta_seq = np.asarray(params_pgslb_beta_seq, dtype=np.float64)
      params_pgslb_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_beta_seq))
  params_pgslb_mu_raw = params.pgslb_mu
  if isinstance(params_pgslb_mu_raw, (str, bytes, dict)):
    params_pgslb_mu = params_pgslb_mu_raw
  else:
    try:
      params_pgslb_mu_seq = list(params_pgslb_mu_raw)
    except TypeError:
      params_pgslb_mu = params_pgslb_mu_raw
    else:
      params_pgslb_mu_seq = np.asarray(params_pgslb_mu_seq, dtype=np.float64)
      params_pgslb_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_mu_seq))

  pgslb_f0 = lambda s, q: 5 / 3 * s ** 2 + jnp.exp(-params_pgslb_mu * s ** 2) + params_pgslb_beta * q ** 2

  pgslb_f = lambda x, u: pgslb_f0(X2S * x, jnp.zeros_like(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pgslb_f, rs, z, xs0, xs1, u0, u1)

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
  params_pgslb_beta_raw = params.pgslb_beta
  if isinstance(params_pgslb_beta_raw, (str, bytes, dict)):
    params_pgslb_beta = params_pgslb_beta_raw
  else:
    try:
      params_pgslb_beta_seq = list(params_pgslb_beta_raw)
    except TypeError:
      params_pgslb_beta = params_pgslb_beta_raw
    else:
      params_pgslb_beta_seq = np.asarray(params_pgslb_beta_seq, dtype=np.float64)
      params_pgslb_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_beta_seq))
  params_pgslb_mu_raw = params.pgslb_mu
  if isinstance(params_pgslb_mu_raw, (str, bytes, dict)):
    params_pgslb_mu = params_pgslb_mu_raw
  else:
    try:
      params_pgslb_mu_seq = list(params_pgslb_mu_raw)
    except TypeError:
      params_pgslb_mu = params_pgslb_mu_raw
    else:
      params_pgslb_mu_seq = np.asarray(params_pgslb_mu_seq, dtype=np.float64)
      params_pgslb_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_mu_seq))

  pgslb_f0 = lambda s, q: 5 / 3 * s ** 2 + jnp.exp(-params_pgslb_mu * s ** 2) + params_pgslb_beta * q ** 2
  pgslb_f = lambda x, u: pgslb_f0(X2S * x, jnp.zeros_like(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pgslb_f, rs, z, xs0, xs1, u0, u1)

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
  t31 = t28 * t30
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = 0.1e1 / t35
  t37 = t32 * t36
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t46 = params.pgslb_mu * t32
  t51 = jnp.exp(-t46 * t36 * s0 * t42 / 0.24e2)
  t52 = t32 ** 2
  t53 = params.pgslb_beta * t52
  t55 = 0.1e1 / t34 / t33
  t56 = l0 ** 2
  t57 = t55 * t56
  t58 = t38 * r0
  t60 = 0.1e1 / t39 / t58
  t64 = 0.5e1 / 0.72e2 * t37 * s0 * t42 + t51 + t53 * t57 * t60 / 0.576e3
  t68 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t64)
  t69 = r1 <= f.p.dens_threshold
  t70 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t71 = 0.1e1 + t70
  t72 = t71 <= f.p.zeta_threshold
  t73 = t71 ** (0.1e1 / 0.3e1)
  t74 = t73 ** 2
  t76 = f.my_piecewise3(t72, t24, t74 * t71)
  t77 = t76 * t30
  t78 = r1 ** 2
  t79 = r1 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t82 = 0.1e1 / t80 / t78
  t90 = jnp.exp(-t46 * t36 * s2 * t82 / 0.24e2)
  t91 = l1 ** 2
  t92 = t55 * t91
  t93 = t78 * r1
  t95 = 0.1e1 / t79 / t93
  t99 = 0.5e1 / 0.72e2 * t37 * s2 * t82 + t90 + t53 * t92 * t95 / 0.576e3
  t103 = f.my_piecewise3(t69, 0, 0.3e1 / 0.20e2 * t6 * t77 * t99)
  t104 = t7 ** 2
  t106 = t17 / t104
  t107 = t8 - t106
  t108 = f.my_piecewise5(t11, 0, t15, 0, t107)
  t111 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t108)
  t116 = 0.1e1 / t29
  t120 = t6 * t28 * t116 * t64 / 0.10e2
  t123 = s0 / t40 / t58
  t126 = t46 * t36
  t130 = t38 ** 2
  t141 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t111 * t30 * t64 + t120 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.5e1 / 0.27e2 * t37 * t123 + t126 * t123 * t51 / 0.9e1 - 0.5e1 / 0.864e3 * t53 * t57 / t39 / t130))
  t143 = f.my_piecewise5(t15, 0, t11, 0, -t107)
  t146 = f.my_piecewise3(t72, 0, 0.5e1 / 0.3e1 * t74 * t143)
  t154 = t6 * t76 * t116 * t99 / 0.10e2
  t156 = f.my_piecewise3(t69, 0, 0.3e1 / 0.20e2 * t6 * t146 * t30 * t99 + t154)
  vrho_0_ = t68 + t103 + t7 * (t141 + t156)
  t159 = -t8 - t106
  t160 = f.my_piecewise5(t11, 0, t15, 0, t159)
  t163 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t160)
  t169 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t163 * t30 * t64 + t120)
  t171 = f.my_piecewise5(t15, 0, t11, 0, -t159)
  t174 = f.my_piecewise3(t72, 0, 0.5e1 / 0.3e1 * t74 * t171)
  t181 = s2 / t80 / t93
  t187 = t78 ** 2
  t198 = f.my_piecewise3(t69, 0, 0.3e1 / 0.20e2 * t6 * t174 * t30 * t99 + t154 + 0.3e1 / 0.20e2 * t6 * t77 * (-0.5e1 / 0.27e2 * t37 * t181 + t126 * t181 * t90 / 0.9e1 - 0.5e1 / 0.864e3 * t53 * t92 / t79 / t187))
  vrho_1_ = t68 + t103 + t7 * (t169 + t198)
  t211 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.72e2 * t37 * t42 - t46 * t36 * t42 * t51 / 0.24e2))
  vsigma_0_ = t7 * t211
  vsigma_1_ = 0.0e0
  t222 = f.my_piecewise3(t69, 0, 0.3e1 / 0.20e2 * t6 * t77 * (0.5e1 / 0.72e2 * t37 * t82 - t46 * t36 * t82 * t90 / 0.24e2))
  vsigma_2_ = t7 * t222
  t229 = f.my_piecewise3(t1, 0, t6 * t31 * t53 * t55 * l0 * t60 / 0.1920e4)
  vlapl_0_ = t7 * t229
  t236 = f.my_piecewise3(t69, 0, t6 * t77 * t53 * t55 * l1 * t95 / 0.1920e4)
  vlapl_1_ = t7 * t236
  vtau_0_ = 0.0e0
  vtau_1_ = 0.0e0
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
  params_pgslb_beta_raw = params.pgslb_beta
  if isinstance(params_pgslb_beta_raw, (str, bytes, dict)):
    params_pgslb_beta = params_pgslb_beta_raw
  else:
    try:
      params_pgslb_beta_seq = list(params_pgslb_beta_raw)
    except TypeError:
      params_pgslb_beta = params_pgslb_beta_raw
    else:
      params_pgslb_beta_seq = np.asarray(params_pgslb_beta_seq, dtype=np.float64)
      params_pgslb_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_beta_seq))
  params_pgslb_mu_raw = params.pgslb_mu
  if isinstance(params_pgslb_mu_raw, (str, bytes, dict)):
    params_pgslb_mu = params_pgslb_mu_raw
  else:
    try:
      params_pgslb_mu_seq = list(params_pgslb_mu_raw)
    except TypeError:
      params_pgslb_mu = params_pgslb_mu_raw
    else:
      params_pgslb_mu_seq = np.asarray(params_pgslb_mu_seq, dtype=np.float64)
      params_pgslb_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pgslb_mu_seq))

  pgslb_f0 = lambda s, q: 5 / 3 * s ** 2 + jnp.exp(-params_pgslb_mu * s ** 2) + params_pgslb_beta * q ** 2
  pgslb_f = lambda x, u: pgslb_f0(X2S * x, jnp.zeros_like(u))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, pgslb_f, rs, z, xs0, xs1, u0, u1)

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
  t23 = t20 * t22
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t22 / t33
  t36 = t32 * t35
  t40 = params.pgslb_mu * t24 * t28
  t43 = jnp.exp(-t40 * t36 / 0.24e2)
  t44 = t24 ** 2
  t45 = params.pgslb_beta * t44
  t47 = 0.1e1 / t26 / t25
  t48 = t45 * t47
  t49 = l0 ** 2
  t50 = t49 * t30
  t51 = t33 * r0
  t57 = 0.5e1 / 0.72e2 * t29 * t36 + t43 + t48 * t50 / t21 / t51 / 0.288e3
  t61 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t57)
  t68 = 0.1e1 / t22 / t51
  t76 = t33 ** 2
  t87 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t57 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.5e1 / 0.27e2 * t29 * t32 * t68 + t40 * t32 * t68 * t43 / 0.9e1 - 0.5e1 / 0.432e3 * t48 * t50 / t21 / t76))
  vrho_0_ = 0.2e1 * r0 * t87 + 0.2e1 * t61
  t90 = t31 * t35
  t100 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.72e2 * t29 * t90 - t40 * t90 * t43 / 0.24e2))
  vsigma_0_ = 0.2e1 * r0 * t100
  t109 = f.my_piecewise3(t2, 0, t7 * t20 * t35 * t45 * t47 * l0 * t30 / 0.960e3)
  vlapl_0_ = 0.2e1 * r0 * t109
  vtau_0_ = 0.0e0
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
  t23 = t20 / t21
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t21 ** 2
  t37 = t32 / t34 / t33
  t41 = params.pgslb_mu * t24 * t28
  t44 = jnp.exp(-t41 * t37 / 0.24e2)
  t45 = t24 ** 2
  t48 = 0.1e1 / t26 / t25
  t49 = params.pgslb_beta * t45 * t48
  t50 = l0 ** 2
  t51 = t50 * t30
  t52 = t33 * r0
  t58 = 0.5e1 / 0.72e2 * t29 * t37 + t44 + t49 * t51 / t21 / t52 / 0.288e3
  t62 = t20 * t34
  t64 = 0.1e1 / t34 / t52
  t72 = t33 ** 2
  t78 = -0.5e1 / 0.27e2 * t29 * t32 * t64 + t41 * t32 * t64 * t44 / 0.9e1 - 0.5e1 / 0.432e3 * t49 * t51 / t21 / t72
  t83 = f.my_piecewise3(t2, 0, t7 * t23 * t58 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t62 * t78)
  t95 = 0.1e1 / t34 / t72
  t103 = params.pgslb_mu ** 2
  t106 = s0 ** 2
  t126 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t58 / 0.30e2 + t7 * t23 * t78 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t62 * (0.55e2 / 0.81e2 * t29 * t32 * t95 - 0.11e2 / 0.27e2 * t41 * t32 * t95 * t44 + 0.2e1 / 0.81e2 * t103 * t45 * t48 * t106 * t30 / t21 / t72 / t52 * t44 + 0.65e2 / 0.1296e4 * t49 * t51 / t21 / t72 / r0))
  v2rho2_0_ = 0.2e1 * r0 * t126 + 0.4e1 * t83
  res = {'v2rho2': v2rho2_0_}
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
  t24 = t20 / t21 / r0
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = t25 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t38 = t33 / t35 / t34
  t42 = params.pgslb_mu * t25 * t29
  t45 = jnp.exp(-t42 * t38 / 0.24e2)
  t46 = t25 ** 2
  t49 = 0.1e1 / t27 / t26
  t50 = params.pgslb_beta * t46 * t49
  t51 = l0 ** 2
  t52 = t51 * t31
  t53 = t34 * r0
  t59 = 0.5e1 / 0.72e2 * t30 * t38 + t45 + t50 * t52 / t21 / t53 / 0.288e3
  t64 = t20 / t21
  t66 = 0.1e1 / t35 / t53
  t74 = t34 ** 2
  t80 = -0.5e1 / 0.27e2 * t30 * t33 * t66 + t42 * t33 * t66 * t45 / 0.9e1 - 0.5e1 / 0.432e3 * t50 * t52 / t21 / t74
  t84 = t20 * t35
  t86 = 0.1e1 / t35 / t74
  t94 = params.pgslb_mu ** 2
  t96 = t94 * t46 * t49
  t97 = s0 ** 2
  t98 = t97 * t31
  t106 = t74 * r0
  t112 = 0.55e2 / 0.81e2 * t30 * t33 * t86 - 0.11e2 / 0.27e2 * t42 * t33 * t86 * t45 + 0.2e1 / 0.81e2 * t96 * t98 / t21 / t74 / t53 * t45 + 0.65e2 / 0.1296e4 * t50 * t52 / t21 / t106
  t117 = f.my_piecewise3(t2, 0, -t7 * t24 * t59 / 0.30e2 + t7 * t64 * t80 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t84 * t112)
  t132 = 0.1e1 / t35 / t106
  t140 = t74 ** 2
  t148 = t26 ** 2
  t169 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t59 - t7 * t24 * t80 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t64 * t112 + 0.3e1 / 0.20e2 * t7 * t84 * (-0.770e3 / 0.243e3 * t30 * t33 * t132 + 0.154e3 / 0.81e2 * t42 * t33 * t132 * t45 - 0.22e2 / 0.81e2 * t96 * t98 / t21 / t140 * t45 + 0.8e1 / 0.243e3 * t94 * params.pgslb_mu / t148 * t97 * s0 / t140 / t53 * t45 - 0.65e2 / 0.243e3 * t50 * t52 / t21 / t74 / t34))
  v3rho3_0_ = 0.2e1 * r0 * t169 + 0.6e1 * t117

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
  t25 = t20 / t22 / t21
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = t26 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = t22 ** 2
  t38 = t34 / t35 / t21
  t42 = params.pgslb_mu * t26 * t30
  t45 = jnp.exp(-t42 * t38 / 0.24e2)
  t46 = t26 ** 2
  t49 = 0.1e1 / t28 / t27
  t50 = params.pgslb_beta * t46 * t49
  t51 = l0 ** 2
  t52 = t51 * t32
  t53 = t21 * r0
  t55 = 0.1e1 / t22 / t53
  t59 = 0.5e1 / 0.72e2 * t31 * t38 + t45 + t50 * t52 * t55 / 0.288e3
  t65 = t20 / t22 / r0
  t67 = 0.1e1 / t35 / t53
  t75 = t21 ** 2
  t81 = -0.5e1 / 0.27e2 * t31 * t34 * t67 + t42 * t34 * t67 * t45 / 0.9e1 - 0.5e1 / 0.432e3 * t50 * t52 / t22 / t75
  t86 = t20 / t22
  t88 = 0.1e1 / t35 / t75
  t96 = params.pgslb_mu ** 2
  t98 = t96 * t46 * t49
  t99 = s0 ** 2
  t100 = t99 * t32
  t103 = 0.1e1 / t22 / t75 / t53
  t108 = t75 * r0
  t114 = 0.55e2 / 0.81e2 * t31 * t34 * t88 - 0.11e2 / 0.27e2 * t42 * t34 * t88 * t45 + 0.2e1 / 0.81e2 * t98 * t100 * t103 * t45 + 0.65e2 / 0.1296e4 * t50 * t52 / t22 / t108
  t118 = t20 * t35
  t120 = 0.1e1 / t35 / t108
  t128 = t75 ** 2
  t136 = t27 ** 2
  t137 = 0.1e1 / t136
  t138 = t96 * params.pgslb_mu * t137
  t139 = t99 * s0
  t146 = t75 * t21
  t152 = -0.770e3 / 0.243e3 * t31 * t34 * t120 + 0.154e3 / 0.81e2 * t42 * t34 * t120 * t45 - 0.22e2 / 0.81e2 * t98 * t100 / t22 / t128 * t45 + 0.8e1 / 0.243e3 * t138 * t139 / t128 / t53 * t45 - 0.65e2 / 0.243e3 * t50 * t52 / t22 / t146
  t157 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t59 - t7 * t65 * t81 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t86 * t114 + 0.3e1 / 0.20e2 * t7 * t118 * t152)
  t173 = 0.1e1 / t35 / t146
  t194 = t96 ** 2
  t196 = t99 ** 2
  t214 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 * t55 * t59 + 0.8e1 / 0.45e2 * t7 * t25 * t81 - t7 * t65 * t114 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t86 * t152 + 0.3e1 / 0.20e2 * t7 * t118 * (0.13090e5 / 0.729e3 * t31 * t34 * t173 - 0.2618e4 / 0.243e3 * t42 * t34 * t173 * t45 + 0.1958e4 / 0.729e3 * t98 * t100 / t22 / t128 / r0 * t45 - 0.176e3 / 0.243e3 * t138 * t139 / t128 / t75 * t45 + 0.8e1 / 0.2187e4 * t194 * t137 * t196 / t35 / t128 / t146 * t31 * t33 * t45 + 0.1235e4 / 0.729e3 * t50 * t52 * t103))
  v4rho4_0_ = 0.2e1 * r0 * t214 + 0.8e1 * t157

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
  t34 = t31 * t33
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t35 * t39
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t49 = params.pgslb_mu * t35
  t54 = jnp.exp(-t49 * t39 * s0 * t45 / 0.24e2)
  t55 = t35 ** 2
  t56 = params.pgslb_beta * t55
  t58 = 0.1e1 / t37 / t36
  t59 = l0 ** 2
  t60 = t58 * t59
  t61 = t41 * r0
  t67 = 0.5e1 / 0.72e2 * t40 * s0 * t45 + t54 + t56 * t60 / t42 / t61 / 0.576e3
  t71 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t72 = t71 ** 2
  t73 = t72 * f.p.zeta_threshold
  t75 = f.my_piecewise3(t21, t73, t23 * t20)
  t76 = 0.1e1 / t32
  t77 = t75 * t76
  t80 = t6 * t77 * t67 / 0.10e2
  t81 = t75 * t33
  t84 = s0 / t43 / t61
  t87 = t49 * t39
  t91 = t41 ** 2
  t97 = -0.5e1 / 0.27e2 * t40 * t84 + t87 * t84 * t54 / 0.9e1 - 0.5e1 / 0.864e3 * t56 * t60 / t42 / t91
  t102 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t67 + t80 + 0.3e1 / 0.20e2 * t6 * t81 * t97)
  t104 = r1 <= f.p.dens_threshold
  t105 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t106 = 0.1e1 + t105
  t107 = t106 <= f.p.zeta_threshold
  t108 = t106 ** (0.1e1 / 0.3e1)
  t109 = t108 ** 2
  t111 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t114 = f.my_piecewise3(t107, 0, 0.5e1 / 0.3e1 * t109 * t111)
  t115 = t114 * t33
  t116 = r1 ** 2
  t117 = r1 ** (0.1e1 / 0.3e1)
  t118 = t117 ** 2
  t120 = 0.1e1 / t118 / t116
  t128 = jnp.exp(-t49 * t39 * s2 * t120 / 0.24e2)
  t129 = l1 ** 2
  t130 = t58 * t129
  t131 = t116 * r1
  t137 = 0.5e1 / 0.72e2 * t40 * s2 * t120 + t128 + t56 * t130 / t117 / t131 / 0.576e3
  t142 = f.my_piecewise3(t107, t73, t109 * t106)
  t143 = t142 * t76
  t146 = t6 * t143 * t137 / 0.10e2
  t148 = f.my_piecewise3(t104, 0, 0.3e1 / 0.20e2 * t6 * t115 * t137 + t146)
  t150 = 0.1e1 / t22
  t151 = t28 ** 2
  t156 = t17 / t24 / t7
  t158 = -0.2e1 * t25 + 0.2e1 * t156
  t159 = f.my_piecewise5(t11, 0, t15, 0, t158)
  t163 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t150 * t151 + 0.5e1 / 0.3e1 * t23 * t159)
  t170 = t6 * t31 * t76 * t67
  t176 = 0.1e1 / t32 / t7
  t180 = t6 * t75 * t176 * t67 / 0.30e2
  t182 = t6 * t77 * t97
  t186 = s0 / t43 / t91
  t192 = params.pgslb_mu ** 2
  t194 = t192 * t55 * t58
  t195 = s0 ** 2
  t214 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t163 * t33 * t67 + t170 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t97 - t180 + t182 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t81 * (0.55e2 / 0.81e2 * t40 * t186 - 0.11e2 / 0.27e2 * t87 * t186 * t54 + t194 * t195 / t42 / t91 / t61 * t54 / 0.81e2 + 0.65e2 / 0.2592e4 * t56 * t60 / t42 / t91 / r0))
  t215 = 0.1e1 / t108
  t216 = t111 ** 2
  t220 = f.my_piecewise5(t15, 0, t11, 0, -t158)
  t224 = f.my_piecewise3(t107, 0, 0.10e2 / 0.9e1 * t215 * t216 + 0.5e1 / 0.3e1 * t109 * t220)
  t231 = t6 * t114 * t76 * t137
  t236 = t6 * t142 * t176 * t137 / 0.30e2
  t238 = f.my_piecewise3(t104, 0, 0.3e1 / 0.20e2 * t6 * t224 * t33 * t137 + t231 / 0.5e1 - t236)
  d11 = 0.2e1 * t102 + 0.2e1 * t148 + t7 * (t214 + t238)
  t241 = -t8 - t26
  t242 = f.my_piecewise5(t11, 0, t15, 0, t241)
  t245 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t242)
  t246 = t245 * t33
  t251 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t246 * t67 + t80)
  t253 = f.my_piecewise5(t15, 0, t11, 0, -t241)
  t256 = f.my_piecewise3(t107, 0, 0.5e1 / 0.3e1 * t109 * t253)
  t257 = t256 * t33
  t261 = t142 * t33
  t264 = s2 / t118 / t131
  t270 = t116 ** 2
  t276 = -0.5e1 / 0.27e2 * t40 * t264 + t87 * t264 * t128 / 0.9e1 - 0.5e1 / 0.864e3 * t56 * t130 / t117 / t270
  t281 = f.my_piecewise3(t104, 0, 0.3e1 / 0.20e2 * t6 * t257 * t137 + t146 + 0.3e1 / 0.20e2 * t6 * t261 * t276)
  t285 = 0.2e1 * t156
  t286 = f.my_piecewise5(t11, 0, t15, 0, t285)
  t290 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t150 * t242 * t28 + 0.5e1 / 0.3e1 * t23 * t286)
  t297 = t6 * t245 * t76 * t67
  t305 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t290 * t33 * t67 + t297 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t246 * t97 + t170 / 0.10e2 - t180 + t182 / 0.10e2)
  t309 = f.my_piecewise5(t15, 0, t11, 0, -t285)
  t313 = f.my_piecewise3(t107, 0, 0.10e2 / 0.9e1 * t215 * t253 * t111 + 0.5e1 / 0.3e1 * t109 * t309)
  t320 = t6 * t256 * t76 * t137
  t327 = t6 * t143 * t276
  t330 = f.my_piecewise3(t104, 0, 0.3e1 / 0.20e2 * t6 * t313 * t33 * t137 + t320 / 0.10e2 + t231 / 0.10e2 - t236 + 0.3e1 / 0.20e2 * t6 * t115 * t276 + t327 / 0.10e2)
  d12 = t102 + t148 + t251 + t281 + t7 * (t305 + t330)
  t335 = t242 ** 2
  t339 = 0.2e1 * t25 + 0.2e1 * t156
  t340 = f.my_piecewise5(t11, 0, t15, 0, t339)
  t344 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t150 * t335 + 0.5e1 / 0.3e1 * t23 * t340)
  t351 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t344 * t33 * t67 + t297 / 0.5e1 - t180)
  t352 = t253 ** 2
  t356 = f.my_piecewise5(t15, 0, t11, 0, -t339)
  t360 = f.my_piecewise3(t107, 0, 0.10e2 / 0.9e1 * t215 * t352 + 0.5e1 / 0.3e1 * t109 * t356)
  t372 = s2 / t118 / t270
  t378 = s2 ** 2
  t397 = f.my_piecewise3(t104, 0, 0.3e1 / 0.20e2 * t6 * t360 * t33 * t137 + t320 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t257 * t276 - t236 + t327 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t261 * (0.55e2 / 0.81e2 * t40 * t372 - 0.11e2 / 0.27e2 * t87 * t372 * t128 + t194 * t378 / t117 / t270 / t131 * t128 / 0.81e2 + 0.65e2 / 0.2592e4 * t56 * t130 / t117 / t270 / r1))
  d22 = 0.2e1 * t251 + 0.2e1 * t281 + t7 * (t351 + t397)
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
  t45 = t42 * t44
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t60 = params.pgslb_mu * t46
  t65 = jnp.exp(-t60 * t50 * s0 * t56 / 0.24e2)
  t66 = t46 ** 2
  t67 = params.pgslb_beta * t66
  t69 = 0.1e1 / t48 / t47
  t70 = l0 ** 2
  t71 = t69 * t70
  t72 = t52 * r0
  t78 = 0.5e1 / 0.72e2 * t51 * s0 * t56 + t65 + t67 * t71 / t53 / t72 / 0.576e3
  t84 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t85 = 0.1e1 / t43
  t86 = t84 * t85
  t90 = t84 * t44
  t93 = s0 / t54 / t72
  t96 = t60 * t50
  t100 = t52 ** 2
  t106 = -0.5e1 / 0.27e2 * t51 * t93 + t96 * t93 * t65 / 0.9e1 - 0.5e1 / 0.864e3 * t67 * t71 / t53 / t100
  t110 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t111 = t110 ** 2
  t112 = t111 * f.p.zeta_threshold
  t114 = f.my_piecewise3(t21, t112, t32 * t20)
  t116 = 0.1e1 / t43 / t7
  t117 = t114 * t116
  t121 = t114 * t85
  t125 = t114 * t44
  t128 = s0 / t54 / t100
  t134 = params.pgslb_mu ** 2
  t136 = t134 * t66 * t69
  t137 = s0 ** 2
  t145 = t100 * r0
  t151 = 0.55e2 / 0.81e2 * t51 * t128 - 0.11e2 / 0.27e2 * t96 * t128 * t65 + t136 * t137 / t53 / t100 / t72 * t65 / 0.81e2 + 0.65e2 / 0.2592e4 * t67 * t71 / t53 / t145
  t156 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t78 + t6 * t86 * t78 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t90 * t106 - t6 * t117 * t78 / 0.30e2 + t6 * t121 * t106 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t125 * t151)
  t158 = r1 <= f.p.dens_threshold
  t159 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t160 = 0.1e1 + t159
  t161 = t160 <= f.p.zeta_threshold
  t162 = t160 ** (0.1e1 / 0.3e1)
  t163 = 0.1e1 / t162
  t165 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t166 = t165 ** 2
  t169 = t162 ** 2
  t171 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t175 = f.my_piecewise3(t161, 0, 0.10e2 / 0.9e1 * t163 * t166 + 0.5e1 / 0.3e1 * t169 * t171)
  t177 = r1 ** 2
  t178 = r1 ** (0.1e1 / 0.3e1)
  t179 = t178 ** 2
  t181 = 0.1e1 / t179 / t177
  t189 = jnp.exp(-t60 * t50 * s2 * t181 / 0.24e2)
  t190 = l1 ** 2
  t198 = 0.5e1 / 0.72e2 * t51 * s2 * t181 + t189 + t67 * t69 * t190 / t178 / t177 / r1 / 0.576e3
  t204 = f.my_piecewise3(t161, 0, 0.5e1 / 0.3e1 * t169 * t165)
  t210 = f.my_piecewise3(t161, t112, t169 * t160)
  t216 = f.my_piecewise3(t158, 0, 0.3e1 / 0.20e2 * t6 * t175 * t44 * t198 + t6 * t204 * t85 * t198 / 0.5e1 - t6 * t210 * t116 * t198 / 0.30e2)
  t226 = t24 ** 2
  t230 = 0.6e1 * t34 - 0.6e1 * t17 / t226
  t231 = f.my_piecewise5(t11, 0, t15, 0, t230)
  t235 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t231)
  t258 = 0.1e1 / t43 / t24
  t271 = s0 / t54 / t145
  t277 = t100 ** 2
  t285 = t47 ** 2
  t306 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t235 * t44 * t78 + 0.3e1 / 0.10e2 * t6 * t42 * t85 * t78 + 0.9e1 / 0.20e2 * t6 * t45 * t106 - t6 * t84 * t116 * t78 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t86 * t106 + 0.9e1 / 0.20e2 * t6 * t90 * t151 + 0.2e1 / 0.45e2 * t6 * t114 * t258 * t78 - t6 * t117 * t106 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t121 * t151 + 0.3e1 / 0.20e2 * t6 * t125 * (-0.770e3 / 0.243e3 * t51 * t271 + 0.154e3 / 0.81e2 * t96 * t271 * t65 - 0.11e2 / 0.81e2 * t136 * t137 / t53 / t277 * t65 + 0.2e1 / 0.243e3 * t134 * params.pgslb_mu / t285 * t137 * s0 / t277 / t72 * t65 - 0.65e2 / 0.486e3 * t67 * t71 / t53 / t100 / t52))
  t316 = f.my_piecewise5(t15, 0, t11, 0, -t230)
  t320 = f.my_piecewise3(t161, 0, -0.10e2 / 0.27e2 / t162 / t160 * t166 * t165 + 0.10e2 / 0.3e1 * t163 * t165 * t171 + 0.5e1 / 0.3e1 * t169 * t316)
  t338 = f.my_piecewise3(t158, 0, 0.3e1 / 0.20e2 * t6 * t320 * t44 * t198 + 0.3e1 / 0.10e2 * t6 * t175 * t85 * t198 - t6 * t204 * t116 * t198 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t210 * t258 * t198)
  d111 = 0.3e1 * t156 + 0.3e1 * t216 + t7 * (t306 + t338)

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
  t24 = 0.1e1 / t22 / t20
  t25 = t7 ** 2
  t26 = 0.1e1 / t25
  t28 = -t17 * t26 + t8
  t29 = f.my_piecewise5(t11, 0, t15, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t7
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t17 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t11, 0, t15, 0, t40)
  t44 = t22 ** 2
  t45 = t25 ** 2
  t46 = 0.1e1 / t45
  t49 = -0.6e1 * t17 * t46 + 0.6e1 * t37
  t50 = f.my_piecewise5(t11, 0, t15, 0, t49)
  t54 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t24 * t30 * t29 + 0.10e2 / 0.3e1 * t35 * t41 + 0.5e1 / 0.3e1 * t44 * t50)
  t55 = t7 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = t54 * t56
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t62 = 0.1e1 / t61
  t63 = t58 * t62
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t72 = params.pgslb_mu * t58
  t77 = jnp.exp(-t72 * t62 * s0 * t68 / 0.24e2)
  t78 = t58 ** 2
  t79 = params.pgslb_beta * t78
  t81 = 0.1e1 / t60 / t59
  t82 = l0 ** 2
  t83 = t81 * t82
  t84 = t64 * r0
  t90 = 0.5e1 / 0.72e2 * t63 * s0 * t68 + t77 + t79 * t83 / t65 / t84 / 0.576e3
  t99 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t100 = 0.1e1 / t55
  t101 = t99 * t100
  t105 = t99 * t56
  t108 = s0 / t66 / t84
  t111 = t72 * t62
  t115 = t64 ** 2
  t121 = -0.5e1 / 0.27e2 * t63 * t108 + t111 * t108 * t77 / 0.9e1 - 0.5e1 / 0.864e3 * t79 * t83 / t65 / t115
  t127 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t129 = 0.1e1 / t55 / t7
  t130 = t127 * t129
  t134 = t127 * t100
  t138 = t127 * t56
  t141 = s0 / t66 / t115
  t147 = params.pgslb_mu ** 2
  t149 = t147 * t78 * t81
  t150 = s0 ** 2
  t153 = 0.1e1 / t65 / t115 / t84
  t158 = t115 * r0
  t164 = 0.55e2 / 0.81e2 * t63 * t141 - 0.11e2 / 0.27e2 * t111 * t141 * t77 + t149 * t150 * t153 * t77 / 0.81e2 + 0.65e2 / 0.2592e4 * t79 * t83 / t65 / t158
  t168 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t169 = t168 ** 2
  t170 = t169 * f.p.zeta_threshold
  t172 = f.my_piecewise3(t21, t170, t44 * t20)
  t174 = 0.1e1 / t55 / t25
  t175 = t172 * t174
  t179 = t172 * t129
  t183 = t172 * t100
  t187 = t172 * t56
  t190 = s0 / t66 / t158
  t196 = t115 ** 2
  t204 = t59 ** 2
  t205 = 0.1e1 / t204
  t206 = t147 * params.pgslb_mu * t205
  t207 = t150 * s0
  t214 = t115 * t64
  t220 = -0.770e3 / 0.243e3 * t63 * t190 + 0.154e3 / 0.81e2 * t111 * t190 * t77 - 0.11e2 / 0.81e2 * t149 * t150 / t65 / t196 * t77 + 0.2e1 / 0.243e3 * t206 * t207 / t196 / t84 * t77 - 0.65e2 / 0.486e3 * t79 * t83 / t65 / t214
  t225 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t90 + 0.3e1 / 0.10e2 * t6 * t101 * t90 + 0.9e1 / 0.20e2 * t6 * t105 * t121 - t6 * t130 * t90 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t134 * t121 + 0.9e1 / 0.20e2 * t6 * t138 * t164 + 0.2e1 / 0.45e2 * t6 * t175 * t90 - t6 * t179 * t121 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t183 * t164 + 0.3e1 / 0.20e2 * t6 * t187 * t220)
  t227 = r1 <= f.p.dens_threshold
  t228 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t229 = 0.1e1 + t228
  t230 = t229 <= f.p.zeta_threshold
  t231 = t229 ** (0.1e1 / 0.3e1)
  t233 = 0.1e1 / t231 / t229
  t235 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t236 = t235 ** 2
  t240 = 0.1e1 / t231
  t241 = t240 * t235
  t243 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t246 = t231 ** 2
  t248 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t252 = f.my_piecewise3(t230, 0, -0.10e2 / 0.27e2 * t233 * t236 * t235 + 0.10e2 / 0.3e1 * t241 * t243 + 0.5e1 / 0.3e1 * t246 * t248)
  t254 = r1 ** 2
  t255 = r1 ** (0.1e1 / 0.3e1)
  t256 = t255 ** 2
  t258 = 0.1e1 / t256 / t254
  t266 = jnp.exp(-t72 * t62 * s2 * t258 / 0.24e2)
  t267 = l1 ** 2
  t275 = 0.5e1 / 0.72e2 * t63 * s2 * t258 + t266 + t79 * t81 * t267 / t255 / t254 / r1 / 0.576e3
  t284 = f.my_piecewise3(t230, 0, 0.10e2 / 0.9e1 * t240 * t236 + 0.5e1 / 0.3e1 * t246 * t243)
  t291 = f.my_piecewise3(t230, 0, 0.5e1 / 0.3e1 * t246 * t235)
  t297 = f.my_piecewise3(t230, t170, t246 * t229)
  t303 = f.my_piecewise3(t227, 0, 0.3e1 / 0.20e2 * t6 * t252 * t56 * t275 + 0.3e1 / 0.10e2 * t6 * t284 * t100 * t275 - t6 * t291 * t129 * t275 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t297 * t174 * t275)
  t328 = s0 / t66 / t214
  t347 = t147 ** 2
  t349 = t150 ** 2
  t366 = t20 ** 2
  t369 = t30 ** 2
  t375 = t41 ** 2
  t384 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t385 = f.my_piecewise5(t11, 0, t15, 0, t384)
  t389 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t366 * t369 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t375 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t385)
  t413 = 0.1e1 / t55 / t36
  t418 = 0.9e1 / 0.10e2 * t6 * t105 * t164 - 0.2e1 / 0.5e1 * t6 * t130 * t121 + 0.6e1 / 0.5e1 * t6 * t134 * t164 + 0.3e1 / 0.5e1 * t6 * t138 * t220 + 0.8e1 / 0.45e2 * t6 * t175 * t121 - t6 * t179 * t164 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t183 * t220 + 0.3e1 / 0.20e2 * t6 * t187 * (0.13090e5 / 0.729e3 * t63 * t328 - 0.2618e4 / 0.243e3 * t111 * t328 * t77 + 0.979e3 / 0.729e3 * t149 * t150 / t65 / t196 / r0 * t77 - 0.44e2 / 0.243e3 * t206 * t207 / t196 / t115 * t77 + 0.2e1 / 0.2187e4 * t347 * t205 * t349 / t66 / t196 / t214 * t58 * t62 * t77 + 0.1235e4 / 0.1458e4 * t79 * t83 * t153) + 0.3e1 / 0.20e2 * t6 * t389 * t56 * t90 + 0.3e1 / 0.5e1 * t6 * t57 * t121 + 0.6e1 / 0.5e1 * t6 * t101 * t121 + 0.2e1 / 0.5e1 * t6 * t54 * t100 * t90 - t6 * t99 * t129 * t90 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t127 * t174 * t90 - 0.14e2 / 0.135e3 * t6 * t172 * t413 * t90
  t419 = f.my_piecewise3(t1, 0, t418)
  t420 = t229 ** 2
  t423 = t236 ** 2
  t429 = t243 ** 2
  t435 = f.my_piecewise5(t15, 0, t11, 0, -t384)
  t439 = f.my_piecewise3(t230, 0, 0.40e2 / 0.81e2 / t231 / t420 * t423 - 0.20e2 / 0.9e1 * t233 * t236 * t243 + 0.10e2 / 0.3e1 * t240 * t429 + 0.40e2 / 0.9e1 * t241 * t248 + 0.5e1 / 0.3e1 * t246 * t435)
  t461 = f.my_piecewise3(t227, 0, 0.3e1 / 0.20e2 * t6 * t439 * t56 * t275 + 0.2e1 / 0.5e1 * t6 * t252 * t100 * t275 - t6 * t284 * t129 * t275 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t291 * t174 * t275 - 0.14e2 / 0.135e3 * t6 * t297 * t413 * t275)
  d1111 = 0.4e1 * t225 + 0.4e1 * t303 + t7 * (t419 + t461)

  res = {'v4rho4': d1111}
  return res
