"""Generated from gga_c_ccdf.mpl."""

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))
  params_c4_raw = params.c4
  if isinstance(params_c4_raw, (str, bytes, dict)):
    params_c4 = params_c4_raw
  else:
    try:
      params_c4_seq = list(params_c4_raw)
    except TypeError:
      params_c4 = params_c4_raw
    else:
      params_c4_seq = np.asarray(params_c4_seq, dtype=np.float64)
      params_c4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c4_seq))
  params_c5_raw = params.c5
  if isinstance(params_c5_raw, (str, bytes, dict)):
    params_c5 = params_c5_raw
  else:
    try:
      params_c5_seq = list(params_c5_raw)
    except TypeError:
      params_c5 = params_c5_raw
    else:
      params_c5_seq = np.asarray(params_c5_seq, dtype=np.float64)
      params_c5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c5_seq))

  f_ccdf = lambda rs, z, xt, xs0=None, xs1=None: params_c1 / (1 + params_c2 * f.n_total(rs) ** (-1 / 3)) * (1 - params_c3 / (1 + jnp.exp(-params_c4 * (2 ** (1 / 3) * X2S * xt - params_c5))))

  functional_body = lambda rs, z, xt, xs0, xs1: f_ccdf(rs, z, xt, xs0, xs1)

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))
  params_c4_raw = params.c4
  if isinstance(params_c4_raw, (str, bytes, dict)):
    params_c4 = params_c4_raw
  else:
    try:
      params_c4_seq = list(params_c4_raw)
    except TypeError:
      params_c4 = params_c4_raw
    else:
      params_c4_seq = np.asarray(params_c4_seq, dtype=np.float64)
      params_c4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c4_seq))
  params_c5_raw = params.c5
  if isinstance(params_c5_raw, (str, bytes, dict)):
    params_c5 = params_c5_raw
  else:
    try:
      params_c5_seq = list(params_c5_raw)
    except TypeError:
      params_c5 = params_c5_raw
    else:
      params_c5_seq = np.asarray(params_c5_seq, dtype=np.float64)
      params_c5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c5_seq))

  f_ccdf = lambda rs, z, xt, xs0=None, xs1=None: params_c1 / (1 + params_c2 * f.n_total(rs) ** (-1 / 3)) * (1 - params_c3 / (1 + jnp.exp(-params_c4 * (2 ** (1 / 3) * X2S * xt - params_c5))))

  functional_body = lambda rs, z, xt, xs0, xs1: f_ccdf(rs, z, xt, xs0, xs1)

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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))
  params_c4_raw = params.c4
  if isinstance(params_c4_raw, (str, bytes, dict)):
    params_c4 = params_c4_raw
  else:
    try:
      params_c4_seq = list(params_c4_raw)
    except TypeError:
      params_c4 = params_c4_raw
    else:
      params_c4_seq = np.asarray(params_c4_seq, dtype=np.float64)
      params_c4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c4_seq))
  params_c5_raw = params.c5
  if isinstance(params_c5_raw, (str, bytes, dict)):
    params_c5 = params_c5_raw
  else:
    try:
      params_c5_seq = list(params_c5_raw)
    except TypeError:
      params_c5 = params_c5_raw
    else:
      params_c5_seq = np.asarray(params_c5_seq, dtype=np.float64)
      params_c5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c5_seq))

  f_ccdf = lambda rs, z, xt, xs0=None, xs1=None: params_c1 / (1 + params_c2 * f.n_total(rs) ** (-1 / 3)) * (1 - params_c3 / (1 + jnp.exp(-params_c4 * (2 ** (1 / 3) * X2S * xt - params_c5))))

  functional_body = lambda rs, z, xt, xs0, xs1: f_ccdf(rs, z, xt, xs0, xs1)

  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t3 = 0.1e1 / t2
  t5 = params.c2 * t3 + 0.1e1
  t6 = 0.1e1 / t5
  t8 = 2 ** (0.1e1 / 0.3e1)
  t9 = 6 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t12 = jnp.pi ** 2
  t13 = t12 ** (0.1e1 / 0.3e1)
  t14 = 0.1e1 / t13
  t17 = jnp.sqrt(s0 + 0.2e1 * s1 + s2)
  t18 = t14 * t17
  t20 = 0.1e1 / t2 / t1
  t26 = jnp.exp(-params.c4 * (t8 * t10 * t18 * t20 / 0.12e2 - params.c5))
  t27 = 0.1e1 + t26
  t30 = 0.1e1 - params.c3 / t27
  t32 = t3 * params.c1
  t33 = t5 ** 2
  t41 = t27 ** 2
  t43 = t6 * params.c3 / t41
  t46 = params.c4 * t8 * t10
  vrho_0_ = params.c1 * t6 * t30 + t32 / t33 * t30 * params.c2 / 0.3e1 + t20 * params.c1 * t43 * t46 * t18 * t26 / 0.9e1
  vrho_1_ = vrho_0_
  t56 = t32 * t43 * t46 * t14 / t17 * t26
  vsigma_0_ = -t56 / 0.24e2
  vsigma_1_ = -t56 / 0.12e2
  vsigma_2_ = vsigma_0_
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
  params_c1_raw = params.c1
  if isinstance(params_c1_raw, (str, bytes, dict)):
    params_c1 = params_c1_raw
  else:
    try:
      params_c1_seq = list(params_c1_raw)
    except TypeError:
      params_c1 = params_c1_raw
    else:
      params_c1_seq = np.asarray(params_c1_seq, dtype=np.float64)
      params_c1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c1_seq))
  params_c2_raw = params.c2
  if isinstance(params_c2_raw, (str, bytes, dict)):
    params_c2 = params_c2_raw
  else:
    try:
      params_c2_seq = list(params_c2_raw)
    except TypeError:
      params_c2 = params_c2_raw
    else:
      params_c2_seq = np.asarray(params_c2_seq, dtype=np.float64)
      params_c2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c2_seq))
  params_c3_raw = params.c3
  if isinstance(params_c3_raw, (str, bytes, dict)):
    params_c3 = params_c3_raw
  else:
    try:
      params_c3_seq = list(params_c3_raw)
    except TypeError:
      params_c3 = params_c3_raw
    else:
      params_c3_seq = np.asarray(params_c3_seq, dtype=np.float64)
      params_c3 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c3_seq))
  params_c4_raw = params.c4
  if isinstance(params_c4_raw, (str, bytes, dict)):
    params_c4 = params_c4_raw
  else:
    try:
      params_c4_seq = list(params_c4_raw)
    except TypeError:
      params_c4 = params_c4_raw
    else:
      params_c4_seq = np.asarray(params_c4_seq, dtype=np.float64)
      params_c4 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c4_seq))
  params_c5_raw = params.c5
  if isinstance(params_c5_raw, (str, bytes, dict)):
    params_c5 = params_c5_raw
  else:
    try:
      params_c5_seq = list(params_c5_raw)
    except TypeError:
      params_c5 = params_c5_raw
    else:
      params_c5_seq = np.asarray(params_c5_seq, dtype=np.float64)
      params_c5 = np.concatenate((np.array([np.nan], dtype=np.float64), params_c5_seq))

  f_ccdf = lambda rs, z, xt, xs0=None, xs1=None: params_c1 / (1 + params_c2 * f.n_total(rs) ** (-1 / 3)) * (1 - params_c3 / (1 + jnp.exp(-params_c4 * (2 ** (1 / 3) * X2S * xt - params_c5))))

  functional_body = lambda rs, z, xt, xs0, xs1: f_ccdf(rs, z, xt, xs0, xs1)

  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / t1
  t4 = params.c2 * t2 + 0.1e1
  t5 = 0.1e1 / t4
  t7 = 2 ** (0.1e1 / 0.3e1)
  t8 = 6 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t11 = jnp.pi ** 2
  t12 = t11 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / t12
  t14 = jnp.sqrt(s0)
  t15 = t13 * t14
  t17 = 0.1e1 / t1 / r0
  t23 = jnp.exp(-params.c4 * (t7 * t9 * t15 * t17 / 0.12e2 - params.c5))
  t24 = 0.1e1 + t23
  t27 = 0.1e1 - params.c3 / t24
  t29 = t2 * params.c1
  t30 = t4 ** 2
  t38 = t24 ** 2
  t40 = t5 * params.c3 / t38
  t43 = params.c4 * t7 * t9
  vrho_0_ = params.c1 * t5 * t27 + t29 / t30 * t27 * params.c2 / 0.3e1 + t17 * params.c1 * t40 * t43 * t15 * t23 / 0.9e1
  vsigma_0_ = -t29 * t40 * t43 * t13 / t14 * t23 / 0.24e2
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = r0 ** (0.1e1 / 0.3e1)
  t2 = 0.1e1 / t1
  t4 = params.c2 * t2 + 0.1e1
  t5 = t4 ** 2
  t6 = 0.1e1 / t5
  t8 = 2 ** (0.1e1 / 0.3e1)
  t9 = 6 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = t8 * t10
  t12 = jnp.pi ** 2
  t13 = t12 ** (0.1e1 / 0.3e1)
  t14 = 0.1e1 / t13
  t15 = jnp.sqrt(s0)
  t18 = 0.1e1 / t1 / r0
  t24 = jnp.exp(-params.c4 * (t11 * t14 * t15 * t18 / 0.12e2 - params.c5))
  t25 = 0.1e1 + t24
  t28 = 0.1e1 - params.c3 / t25
  t33 = 0.1e1 / t4
  t35 = t25 ** 2
  t36 = 0.1e1 / t35
  t38 = params.c3 * t36 * params.c4
  t40 = t11 * t14
  t41 = r0 ** 2
  t49 = t1 ** 2
  t52 = 0.1e1 / t49 / r0 * params.c1
  t56 = params.c2 ** 2
  t62 = 0.1e1 / t49 / t41 * params.c1
  t73 = 0.1e1 / t49 / t41 / r0 * params.c1
  t74 = t33 * params.c3
  t77 = t74 / t35 / t25
  t79 = params.c4 ** 2
  t80 = t8 ** 2
  t81 = t79 * t80
  t82 = t81 * t9
  t83 = t13 ** 2
  t84 = 0.1e1 / t83
  t85 = t84 * s0
  t86 = t24 ** 2
  t91 = t74 * t36
  v2rho2_0_ = 0.2e1 / 0.9e1 * params.c1 * t6 * t28 * params.c2 * t18 - params.c1 * t33 * t38 * t40 * t15 / t1 / t41 * t24 / 0.27e2 + 0.2e1 / 0.9e1 * t52 / t5 / t4 * t28 * t56 + 0.2e1 / 0.27e2 * t62 * t6 * t38 * t40 * t15 * t24 * params.c2 - 0.4e1 / 0.27e2 * t73 * t77 * t82 * t85 * t86 + 0.2e1 / 0.27e2 * t73 * t91 * t82 * t85 * t24
  t100 = params.c4 * t8 * t10
  t101 = 0.1e1 / t15
  t115 = t9 * t84
  v2rhosigma_0_ = t18 * params.c1 * t91 * t100 * t14 * t101 * t24 / 0.72e2 - t52 * t6 * t38 * t40 * t101 * t24 * params.c2 / 0.72e2 + t62 * t77 * t81 * t115 * t86 / 0.18e2 - t62 * t91 * t81 * t115 * t24 / 0.36e2
  t127 = t84 / s0
  v2sigma2_0_ = -t52 * t77 * t82 * t127 * t86 / 0.48e2 + t2 * params.c1 * t91 * t100 * t14 / t15 / s0 * t24 / 0.48e2 + t52 * t91 * t82 * t127 * t24 / 0.96e2
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 + params.c2 / t1
  t5 = t4 ** 2
  t7 = 0.1e1 / t5 / t4
  t9 = 2 ** (0.1e1 / 0.3e1)
  t10 = 6 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = t9 * t11
  t13 = jnp.pi ** 2
  t14 = t13 ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t14
  t16 = jnp.sqrt(s0)
  t25 = jnp.exp(-params.c4 * (t12 * t15 * t16 / t1 / r0 / 0.12e2 - params.c5))
  t26 = 0.1e1 + t25
  t29 = 0.1e1 - params.c3 / t26
  t30 = params.c2 ** 2
  t32 = r0 ** 2
  t33 = t1 ** 2
  t39 = 0.1e1 / t5
  t40 = params.c1 * t39
  t42 = t26 ** 2
  t43 = 0.1e1 / t42
  t49 = t32 * r0
  t63 = 0.1e1 / t4
  t64 = params.c1 * t63
  t66 = 0.1e1 / t42 / t26
  t68 = params.c4 ** 2
  t69 = params.c3 * t66 * t68
  t71 = t9 ** 2
  t73 = t14 ** 2
  t75 = t71 * t10 / t73
  t76 = t32 ** 2
  t79 = s0 / t33 / t76
  t80 = t25 ** 2
  t85 = params.c3 * t43
  t86 = t85 * params.c4
  t88 = t12 * t15
  t96 = t85 * t68
  t104 = t5 ** 2
  t123 = 0.1e1 / t76 / r0 * params.c1 * t39
  t140 = 0.1e1 / t76 / t32 * params.c1 * t63 * params.c3
  t141 = t42 ** 2
  t143 = t68 * params.c4
  t147 = 0.1e1 / t13 * t16 * s0
  v3rho3_0_ = -0.2e1 / 0.9e1 * params.c1 * t7 * t29 * t30 / t33 / t32 - 0.5e1 / 0.27e2 * t40 * params.c3 * t43 * params.c4 * t9 * t11 * t15 * t16 / t33 / t49 * t25 * params.c2 - 0.8e1 / 0.27e2 * t40 * t29 * params.c2 / t1 / t32 + 0.16e2 / 0.27e2 * t64 * t69 * t75 * t79 * t80 + 0.7e1 / 0.81e2 * t64 * t86 * t88 * t16 / t1 / t49 * t25 - 0.8e1 / 0.27e2 * t64 * t96 * t75 * t79 * t25 + 0.2e1 / 0.9e1 / t49 * params.c1 / t104 * t29 * t30 * params.c2 + 0.2e1 / 0.27e2 / t76 * params.c1 * t7 * t86 * t88 * t16 * t25 * t30 - 0.4e1 / 0.27e2 * t123 * t69 * t75 * s0 * t80 * params.c2 + 0.2e1 / 0.27e2 * t123 * t96 * t75 * s0 * t25 * params.c2 + 0.16e2 / 0.27e2 * t140 / t141 * t143 * t147 * t80 * t25 - 0.16e2 / 0.27e2 * t140 * t66 * t143 * t147 * t80 + 0.8e1 / 0.81e2 * t140 * t43 * t143 * t147 * t25

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = r0 ** (0.1e1 / 0.3e1)
  t4 = 0.1e1 + params.c2 / t1
  t5 = 0.1e1 / t4
  t6 = params.c1 * t5
  t7 = 2 ** (0.1e1 / 0.3e1)
  t8 = 6 ** (0.1e1 / 0.3e1)
  t9 = t8 ** 2
  t10 = t7 * t9
  t11 = jnp.pi ** 2
  t12 = t11 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / t12
  t14 = jnp.sqrt(s0)
  t23 = jnp.exp(-params.c4 * (t10 * t13 * t14 / t1 / r0 / 0.12e2 - params.c5))
  t24 = 0.1e1 + t23
  t25 = t24 ** 2
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = params.c3 * t27
  t30 = params.c4 ** 2
  t32 = 0.1e1 / t11
  t33 = t30 * params.c4 * t32
  t34 = t14 * s0
  t35 = r0 ** 2
  t36 = t35 * r0
  t37 = t35 ** 2
  t38 = t37 * t36
  t40 = t34 / t38
  t41 = t23 ** 2
  t42 = t41 * t23
  t48 = 0.1e1 / t25 / t24
  t49 = params.c3 * t48
  t55 = 0.1e1 / t25
  t56 = params.c3 * t55
  t64 = 0.1e1 / t1 / t38 * params.c1
  t65 = t4 ** 2
  t66 = 0.1e1 / t65
  t67 = t66 * params.c3
  t89 = t65 ** 2
  t90 = 0.1e1 / t89
  t94 = 0.1e1 - params.c3 / t24
  t95 = params.c2 ** 2
  t96 = t95 * params.c2
  t103 = 0.1e1 / t1 / t37
  t108 = t95 ** 2
  t113 = 0.1e1 / t65 / t4
  t114 = params.c1 * t113
  t116 = t1 ** 2
  t122 = params.c1 * t66
  t131 = t55 * params.c4 * t7
  t133 = t9 * t13
  t134 = t133 * t14
  t135 = t37 * r0
  t142 = t122 * params.c3
  t144 = t7 ** 2
  t147 = t12 ** 2
  t148 = 0.1e1 / t147
  t150 = t8 * t148 * s0
  t151 = t37 * t35
  t152 = 0.1e1 / t151
  t158 = -0.160e3 / 0.27e2 * t6 * t28 * t33 * t40 * t42 + 0.160e3 / 0.27e2 * t6 * t49 * t33 * t40 * t41 - 0.80e2 / 0.81e2 * t6 * t56 * t33 * t40 * t23 + 0.64e2 / 0.81e2 * t64 * t67 * t27 * t33 * t34 * t42 * params.c2 - 0.64e2 / 0.81e2 * t64 * t67 * t48 * t33 * t34 * t41 * params.c2 + 0.32e2 / 0.243e3 * t64 * t67 * t55 * t33 * t34 * t23 * params.c2 - 0.8e1 / 0.9e1 * params.c1 * t90 * t94 * t96 / t37 + 0.8e1 / 0.27e2 * t103 * params.c1 / t89 / t4 * t94 * t108 + 0.32e2 / 0.81e2 * t114 * t94 * t95 / t116 / t36 + 0.56e2 / 0.81e2 * t122 * t94 * params.c2 / t1 / t36 - 0.4e1 / 0.9e1 * t114 * params.c3 * t131 * t134 / t135 * t23 * t95 + 0.32e2 / 0.27e2 * t142 * t48 * t30 * t144 * t150 * t152 * t41 * params.c2
  t167 = t49 * t30
  t170 = t144 * t8 * t148
  t173 = s0 / t116 / t135
  t178 = t56 * params.c4
  t180 = t10 * t13
  t199 = 0.1e1 / t1 / t151 * params.c1 * t113
  t206 = t56 * t30
  t213 = t37 ** 2
  t217 = 0.1e1 / t1 / t213 * params.c1 * t5
  t221 = t30 ** 2
  t224 = s0 ** 2
  t225 = t32 * t224
  t226 = t41 ** 2
  t263 = -0.16e2 / 0.27e2 * t142 * t55 * t30 * t144 * t150 * t152 * t23 * params.c2 - 0.700e3 / 0.243e3 * t6 * t167 * t170 * t173 * t41 - 0.70e2 / 0.243e3 * t6 * t178 * t180 * t14 * t103 * t23 + 0.8e1 / 0.81e2 / t1 / t135 * params.c1 * t90 * t178 * t180 * t14 * t23 * t96 - 0.16e2 / 0.81e2 * t199 * t167 * t170 * s0 * t41 * t95 + 0.8e1 / 0.81e2 * t199 * t206 * t170 * s0 * t23 * t95 - 0.64e2 / 0.243e3 * t217 * params.c3 / t26 / t24 * t221 * t225 * t226 * t180 + 0.32e2 / 0.81e2 * t217 * t28 * t221 * t225 * t42 * t180 - 0.112e3 / 0.729e3 * t217 * t49 * t221 * t225 * t41 * t180 + 0.8e1 / 0.729e3 * t217 * t56 * t221 * t225 * t7 * t133 * t23 + 0.350e3 / 0.243e3 * t6 * t206 * t170 * t173 * t23 + 0.164e3 / 0.243e3 * t142 * t131 * t134 / t116 / t37 * t23 * params.c2
  v4rho4_0_ = t158 + t263

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 + params.c2 / t2
  t6 = t5 ** 2
  t7 = 0.1e1 / t6
  t9 = 2 ** (0.1e1 / 0.3e1)
  t10 = 6 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = t9 * t11
  t13 = jnp.pi ** 2
  t14 = t13 ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t14
  t17 = s0 + 0.2e1 * s1 + s2
  t18 = jnp.sqrt(t17)
  t21 = 0.1e1 / t2 / t1
  t27 = jnp.exp(-params.c4 * (t12 * t15 * t18 * t21 / 0.12e2 - params.c5))
  t28 = 0.1e1 + t27
  t31 = 0.1e1 - params.c3 / t28
  t36 = 0.1e1 / t5
  t38 = t28 ** 2
  t39 = 0.1e1 / t38
  t41 = params.c3 * t39 * params.c4
  t43 = t12 * t15
  t44 = t1 ** 2
  t52 = t2 ** 2
  t59 = params.c2 ** 2
  t76 = 0.1e1 / t52 / t44 / t1 * params.c1
  t77 = t36 * params.c3
  t82 = params.c4 ** 2
  t83 = t9 ** 2
  t85 = t82 * t83 * t10
  t86 = t14 ** 2
  t88 = 0.1e1 / t86 * t17
  t89 = t27 ** 2
  d11 = 0.2e1 / 0.9e1 * params.c1 * t7 * t31 * params.c2 * t21 - params.c1 * t36 * t41 * t43 * t18 / t2 / t44 * t27 / 0.27e2 + 0.2e1 / 0.9e1 / t52 / t1 * params.c1 / t6 / t5 * t31 * t59 + 0.2e1 / 0.27e2 / t52 / t44 * params.c1 * t7 * t41 * t43 * t18 * t27 * params.c2 - 0.4e1 / 0.27e2 * t76 * t77 / t38 / t28 * t85 * t88 * t89 + 0.2e1 / 0.27e2 * t76 * t77 * t39 * t85 * t88 * t27
  d12 = d11
  d22 = d12
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

  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 + params.c2 / t2
  t6 = t5 ** 2
  t8 = 0.1e1 / t6 / t5
  t10 = 2 ** (0.1e1 / 0.3e1)
  t11 = 6 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t13 = t10 * t12
  t14 = jnp.pi ** 2
  t15 = t14 ** (0.1e1 / 0.3e1)
  t16 = 0.1e1 / t15
  t18 = s0 + 0.2e1 * s1 + s2
  t19 = jnp.sqrt(t18)
  t28 = jnp.exp(-params.c4 * (t13 * t16 * t19 / t2 / t1 / 0.12e2 - params.c5))
  t29 = 0.1e1 + t28
  t32 = 0.1e1 - params.c3 / t29
  t33 = params.c2 ** 2
  t35 = t1 ** 2
  t36 = t2 ** 2
  t42 = 0.1e1 / t6
  t43 = params.c1 * t42
  t45 = t29 ** 2
  t46 = 0.1e1 / t45
  t52 = t35 * t1
  t66 = 0.1e1 / t5
  t67 = params.c1 * t66
  t69 = 0.1e1 / t45 / t29
  t71 = params.c4 ** 2
  t72 = params.c3 * t69 * t71
  t74 = t10 ** 2
  t76 = t15 ** 2
  t78 = t74 * t11 / t76
  t79 = t35 ** 2
  t82 = t18 / t36 / t79
  t83 = t28 ** 2
  t88 = params.c3 * t46
  t89 = t88 * params.c4
  t91 = t13 * t16
  t99 = t88 * t71
  t107 = t6 ** 2
  t126 = 0.1e1 / t79 / t1 * params.c1 * t42
  t143 = 0.1e1 / t79 / t35 * params.c1 * t66 * params.c3
  t144 = t45 ** 2
  t146 = t71 * params.c4
  t150 = 0.1e1 / t14 * t19 * t18
  d111 = -0.2e1 / 0.9e1 * params.c1 * t8 * t32 * t33 / t36 / t35 - 0.5e1 / 0.27e2 * t43 * params.c3 * t46 * params.c4 * t10 * t12 * t16 * t19 / t36 / t52 * t28 * params.c2 - 0.8e1 / 0.27e2 * t43 * t32 * params.c2 / t2 / t35 + 0.16e2 / 0.27e2 * t67 * t72 * t78 * t82 * t83 + 0.7e1 / 0.81e2 * t67 * t89 * t91 * t19 / t2 / t52 * t28 - 0.8e1 / 0.27e2 * t67 * t99 * t78 * t82 * t28 + 0.2e1 / 0.9e1 / t52 * params.c1 / t107 * t32 * t33 * params.c2 + 0.2e1 / 0.27e2 / t79 * params.c1 * t8 * t89 * t91 * t19 * t28 * t33 - 0.4e1 / 0.27e2 * t126 * t72 * t78 * t18 * t83 * params.c2 + 0.2e1 / 0.27e2 * t126 * t99 * t78 * t18 * t28 * params.c2 + 0.16e2 / 0.27e2 * t143 / t144 * t146 * t150 * t83 * t28 - 0.16e2 / 0.27e2 * t143 * t69 * t146 * t150 * t83 + 0.8e1 / 0.81e2 * t143 * t46 * t146 * t150 * t28

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

  t1 = r0 + r1
  t2 = t1 ** (0.1e1 / 0.3e1)
  t5 = 0.1e1 + params.c2 / t2
  t6 = 0.1e1 / t5
  t7 = params.c1 * t6
  t8 = 2 ** (0.1e1 / 0.3e1)
  t9 = 6 ** (0.1e1 / 0.3e1)
  t10 = t9 ** 2
  t11 = t8 * t10
  t12 = jnp.pi ** 2
  t13 = t12 ** (0.1e1 / 0.3e1)
  t14 = 0.1e1 / t13
  t16 = s0 + 0.2e1 * s1 + s2
  t17 = jnp.sqrt(t16)
  t26 = jnp.exp(-params.c4 * (t11 * t14 * t17 / t2 / t1 / 0.12e2 - params.c5))
  t27 = 0.1e1 + t26
  t28 = t27 ** 2
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = params.c3 * t30
  t33 = params.c4 ** 2
  t35 = 0.1e1 / t12
  t36 = t33 * params.c4 * t35
  t37 = t17 * t16
  t38 = t1 ** 2
  t39 = t38 * t1
  t40 = t38 ** 2
  t41 = t40 * t39
  t43 = t37 / t41
  t44 = t26 ** 2
  t45 = t44 * t26
  t51 = 0.1e1 / t28 / t27
  t52 = params.c3 * t51
  t58 = 0.1e1 / t28
  t59 = params.c3 * t58
  t67 = 0.1e1 / t2 / t41 * params.c1
  t68 = t5 ** 2
  t69 = 0.1e1 / t68
  t70 = t69 * params.c3
  t92 = t68 ** 2
  t93 = 0.1e1 / t92
  t97 = 0.1e1 - params.c3 / t27
  t98 = params.c2 ** 2
  t99 = t98 * params.c2
  t106 = 0.1e1 / t2 / t40
  t111 = t98 ** 2
  t116 = 0.1e1 / t68 / t5
  t117 = params.c1 * t116
  t119 = t2 ** 2
  t125 = params.c1 * t69
  t134 = t58 * params.c4 * t8
  t136 = t10 * t14
  t137 = t136 * t17
  t138 = t40 * t1
  t145 = t125 * params.c3
  t147 = t8 ** 2
  t150 = t13 ** 2
  t151 = 0.1e1 / t150
  t153 = t9 * t151 * t16
  t154 = t40 * t38
  t155 = 0.1e1 / t154
  t161 = -0.160e3 / 0.27e2 * t7 * t31 * t36 * t43 * t45 + 0.160e3 / 0.27e2 * t7 * t52 * t36 * t43 * t44 - 0.80e2 / 0.81e2 * t7 * t59 * t36 * t43 * t26 + 0.64e2 / 0.81e2 * t67 * t70 * t30 * t36 * t37 * t45 * params.c2 - 0.64e2 / 0.81e2 * t67 * t70 * t51 * t36 * t37 * t44 * params.c2 + 0.32e2 / 0.243e3 * t67 * t70 * t58 * t36 * t37 * t26 * params.c2 - 0.8e1 / 0.9e1 * params.c1 * t93 * t97 * t99 / t40 + 0.8e1 / 0.27e2 * t106 * params.c1 / t92 / t5 * t97 * t111 + 0.32e2 / 0.81e2 * t117 * t97 * t98 / t119 / t39 + 0.56e2 / 0.81e2 * t125 * t97 * params.c2 / t2 / t39 - 0.4e1 / 0.9e1 * t117 * params.c3 * t134 * t137 / t138 * t26 * t98 + 0.32e2 / 0.27e2 * t145 * t51 * t33 * t147 * t153 * t155 * t44 * params.c2
  t170 = t52 * t33
  t173 = t147 * t9 * t151
  t176 = t16 / t119 / t138
  t181 = t59 * params.c4
  t183 = t11 * t14
  t202 = 0.1e1 / t2 / t154 * params.c1 * t116
  t209 = t59 * t33
  t216 = t40 ** 2
  t220 = 0.1e1 / t2 / t216 * params.c1 * t6
  t224 = t33 ** 2
  t227 = t16 ** 2
  t228 = t35 * t227
  t229 = t44 ** 2
  t266 = -0.16e2 / 0.27e2 * t145 * t58 * t33 * t147 * t153 * t155 * t26 * params.c2 - 0.700e3 / 0.243e3 * t7 * t170 * t173 * t176 * t44 - 0.70e2 / 0.243e3 * t7 * t181 * t183 * t17 * t106 * t26 + 0.8e1 / 0.81e2 / t2 / t138 * params.c1 * t93 * t181 * t183 * t17 * t26 * t99 - 0.16e2 / 0.81e2 * t202 * t170 * t173 * t16 * t44 * t98 + 0.8e1 / 0.81e2 * t202 * t209 * t173 * t16 * t26 * t98 - 0.64e2 / 0.243e3 * t220 * params.c3 / t29 / t27 * t224 * t228 * t229 * t183 + 0.32e2 / 0.81e2 * t220 * t31 * t224 * t228 * t45 * t183 - 0.112e3 / 0.729e3 * t220 * t52 * t224 * t228 * t44 * t183 + 0.8e1 / 0.729e3 * t220 * t59 * t224 * t228 * t8 * t136 * t26 + 0.350e3 / 0.243e3 * t7 * t209 * t173 * t176 * t26 + 0.164e3 / 0.243e3 * t145 * t134 * t137 / t119 / t40 * t26 * params.c2
  d1111 = t161 + t266

  res = {'v4rho4': d1111}
  return res
