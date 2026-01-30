"""Generated from gga_k_rational_p.mpl."""

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
  params_C2_raw = params.C2
  if isinstance(params_C2_raw, (str, bytes, dict)):
    params_C2 = params_C2_raw
  else:
    try:
      params_C2_seq = list(params_C2_raw)
    except TypeError:
      params_C2 = params_C2_raw
    else:
      params_C2_seq = np.asarray(params_C2_seq, dtype=np.float64)
      params_C2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C2_seq))
  params_p_raw = params.p
  if isinstance(params_p_raw, (str, bytes, dict)):
    params_p = params_p_raw
  else:
    try:
      params_p_seq = list(params_p_raw)
    except TypeError:
      params_p = params_p_raw
    else:
      params_p_seq = np.asarray(params_p_seq, dtype=np.float64)
      params_p = np.concatenate((np.array([np.nan], dtype=np.float64), params_p_seq))

  rational_p_f0 = lambda s: (1 + params_C2 / params_p * s ** 2) ** (-params_p)

  rational_p_f = lambda x: rational_p_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, rational_p_f, rs, z, xs0, xs1)

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
  params_C2_raw = params.C2
  if isinstance(params_C2_raw, (str, bytes, dict)):
    params_C2 = params_C2_raw
  else:
    try:
      params_C2_seq = list(params_C2_raw)
    except TypeError:
      params_C2 = params_C2_raw
    else:
      params_C2_seq = np.asarray(params_C2_seq, dtype=np.float64)
      params_C2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C2_seq))
  params_p_raw = params.p
  if isinstance(params_p_raw, (str, bytes, dict)):
    params_p = params_p_raw
  else:
    try:
      params_p_seq = list(params_p_raw)
    except TypeError:
      params_p = params_p_raw
    else:
      params_p_seq = np.asarray(params_p_seq, dtype=np.float64)
      params_p = np.concatenate((np.array([np.nan], dtype=np.float64), params_p_seq))

  rational_p_f0 = lambda s: (1 + params_C2 / params_p * s ** 2) ** (-params_p)

  rational_p_f = lambda x: rational_p_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, rational_p_f, rs, z, xs0, xs1)

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
  params_C2_raw = params.C2
  if isinstance(params_C2_raw, (str, bytes, dict)):
    params_C2 = params_C2_raw
  else:
    try:
      params_C2_seq = list(params_C2_raw)
    except TypeError:
      params_C2 = params_C2_raw
    else:
      params_C2_seq = np.asarray(params_C2_seq, dtype=np.float64)
      params_C2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C2_seq))
  params_p_raw = params.p
  if isinstance(params_p_raw, (str, bytes, dict)):
    params_p = params_p_raw
  else:
    try:
      params_p_seq = list(params_p_raw)
    except TypeError:
      params_p = params_p_raw
    else:
      params_p_seq = np.asarray(params_p_seq, dtype=np.float64)
      params_p = np.concatenate((np.array([np.nan], dtype=np.float64), params_p_seq))

  rational_p_f0 = lambda s: (1 + params_C2 / params_p * s ** 2) ** (-params_p)

  rational_p_f = lambda x: rational_p_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, rational_p_f, rs, z, xs0, xs1)

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
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = params.C2 / params.p * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t49 = 0.1e1 + t35 * t39 * s0 * t45 / 0.24e2
  t50 = t49 ** (-params.p)
  t52 = t6 * t28 * t30 * t50
  t54 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t52)
  t55 = r1 <= f.p.dens_threshold
  t56 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t57 = 0.1e1 + t56
  t58 = t57 <= f.p.zeta_threshold
  t59 = t57 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t62 = f.my_piecewise3(t58, t24, t60 * t57)
  t65 = r1 ** 2
  t66 = r1 ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t69 = 0.1e1 / t67 / t65
  t73 = 0.1e1 + t35 * t39 * s2 * t69 / 0.24e2
  t74 = t73 ** (-params.p)
  t76 = t6 * t62 * t30 * t74
  t78 = f.my_piecewise3(t55, 0, 0.3e1 / 0.20e2 * t76)
  t79 = t7 ** 2
  t81 = t17 / t79
  t82 = t8 - t81
  t83 = f.my_piecewise5(t11, 0, t15, 0, t82)
  t86 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t83)
  t91 = 0.1e1 / t29
  t95 = t6 * t28 * t91 * t50 / 0.10e2
  t96 = params.C2 * t34
  t97 = t96 * t39
  t102 = 0.1e1 / t49
  t108 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t86 * t30 * t50 + t95 + t52 * t97 * s0 / t43 / t41 / r0 * t102 / 0.60e2)
  t110 = f.my_piecewise5(t15, 0, t11, 0, -t82)
  t113 = f.my_piecewise3(t58, 0, 0.5e1 / 0.3e1 * t60 * t110)
  t121 = t6 * t62 * t91 * t74 / 0.10e2
  t123 = f.my_piecewise3(t55, 0, 0.3e1 / 0.20e2 * t6 * t113 * t30 * t74 + t121)
  vrho_0_ = t54 + t78 + t7 * (t108 + t123)
  t126 = -t8 - t81
  t127 = f.my_piecewise5(t11, 0, t15, 0, t126)
  t130 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t127)
  t136 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t130 * t30 * t50 + t95)
  t138 = f.my_piecewise5(t15, 0, t11, 0, -t126)
  t141 = f.my_piecewise3(t58, 0, 0.5e1 / 0.3e1 * t60 * t138)
  t150 = 0.1e1 / t73
  t156 = f.my_piecewise3(t55, 0, 0.3e1 / 0.20e2 * t6 * t141 * t30 * t74 + t121 + t76 * t97 * s2 / t67 / t65 / r1 * t150 / 0.60e2)
  vrho_1_ = t54 + t78 + t7 * (t136 + t156)
  t164 = f.my_piecewise3(t1, 0, -t52 * t96 * t39 * t45 * t102 / 0.160e3)
  vsigma_0_ = t7 * t164
  vsigma_1_ = 0.0e0
  t170 = f.my_piecewise3(t55, 0, -t76 * t96 * t39 * t69 * t150 / 0.160e3)
  vsigma_2_ = t7 * t170
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
  params_C2_raw = params.C2
  if isinstance(params_C2_raw, (str, bytes, dict)):
    params_C2 = params_C2_raw
  else:
    try:
      params_C2_seq = list(params_C2_raw)
    except TypeError:
      params_C2 = params_C2_raw
    else:
      params_C2_seq = np.asarray(params_C2_seq, dtype=np.float64)
      params_C2 = np.concatenate((np.array([np.nan], dtype=np.float64), params_C2_seq))
  params_p_raw = params.p
  if isinstance(params_p_raw, (str, bytes, dict)):
    params_p = params_p_raw
  else:
    try:
      params_p_seq = list(params_p_raw)
    except TypeError:
      params_p = params_p_raw
    else:
      params_p_seq = np.asarray(params_p_seq, dtype=np.float64)
      params_p = np.concatenate((np.array([np.nan], dtype=np.float64), params_p_seq))

  rational_p_f0 = lambda s: (1 + params_C2 / params_p * s ** 2) ** (-params_p)

  rational_p_f = lambda x: rational_p_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, rational_p_f, rs, z, xs0, xs1)

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
  t26 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = 0.1e1 / t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = r0 ** 2
  t42 = 0.1e1 + params.C2 / params.p * t26 * t31 * s0 * t34 / t22 / t35 / 0.24e2
  t43 = t42 ** (-params.p)
  t47 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t20 * t22 * t43)
  t58 = params.C2 * t26
  t61 = 0.1e1 / t42
  t67 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t43 / 0.10e2 + t7 * t20 / t35 / r0 * t43 * t58 * t31 * s0 * t34 * t61 / 0.60e2)
  vrho_0_ = 0.2e1 * r0 * t67 + 0.2e1 * t47
  t79 = f.my_piecewise3(t2, 0, -t7 * t20 / t35 * t43 * t58 * t31 * t34 * t61 / 0.160e3)
  vsigma_0_ = 0.2e1 * r0 * t79
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
  t24 = 0.1e1 / params.p
  t26 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = 0.1e1 / t30
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = r0 ** 2
  t36 = t21 ** 2
  t43 = 0.1e1 + params.C2 * t24 * t26 * t31 * s0 * t34 / t36 / t35 / 0.24e2
  t44 = t43 ** (-params.p)
  t52 = t7 * t20 / t35 / r0 * t44
  t53 = params.C2 * t26
  t56 = 0.1e1 / t43
  t58 = t53 * t31 * s0 * t34 * t56
  t62 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t44 / 0.10e2 + t52 * t58 / 0.60e2)
  t70 = t35 ** 2
  t79 = 0.1e1 / t36 / t70 / t35
  t83 = params.C2 ** 2
  t84 = t26 ** 2
  t85 = t83 * t84
  t87 = 0.1e1 / t29 / t28
  t88 = t85 * t87
  t89 = s0 ** 2
  t91 = t43 ** 2
  t92 = 0.1e1 / t91
  t97 = t7 * t20
  t101 = t84 * t87
  t104 = t33 * t92 * t24
  t109 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t44 / 0.30e2 - 0.7e1 / 0.180e3 * t7 * t20 / t70 * t44 * t58 + t7 * t20 * t79 * t44 * t88 * t89 * t33 * t92 / 0.270e3 + t97 * t79 * t44 * t83 * t101 * t89 * t104 / 0.270e3)
  v2rho2_0_ = 0.2e1 * r0 * t109 + 0.4e1 * t62
  t118 = t53 * t31 * t34 * t56
  t121 = f.my_piecewise3(t2, 0, -t7 * t20 / t35 * t44 * t118 / 0.160e3)
  t126 = 0.1e1 / t36 / t70 / r0
  t145 = f.my_piecewise3(t2, 0, t52 * t118 / 0.80e2 - t7 * t20 * t126 * t44 * t88 * s0 * t33 * t92 / 0.720e3 - t97 * t126 * t44 * t83 * t101 * t33 * t92 * t24 * s0 / 0.720e3)
  v2rhosigma_0_ = 0.2e1 * r0 * t145 + 0.2e1 * t121
  t152 = t7 * t20 / t36 / t70 * t44
  t161 = f.my_piecewise3(t2, 0, t152 * t85 * t87 * t33 * t92 / 0.1920e4 + t152 * t88 * t104 / 0.1920e4)
  v2sigma2_0_ = 0.2e1 * r0 * t161
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
  t25 = 0.1e1 / params.p
  t27 = 6 ** (0.1e1 / 0.3e1)
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = 0.1e1 / t31
  t34 = 2 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = r0 ** 2
  t37 = t21 ** 2
  t44 = 0.1e1 + params.C2 * t25 * t27 * t32 * s0 * t35 / t37 / t36 / 0.24e2
  t45 = t44 ** (-params.p)
  t49 = t36 ** 2
  t59 = params.C2 * t27 * t32 * s0 * t35 / t44
  t64 = 0.1e1 / t37 / t49 / t36
  t68 = params.C2 ** 2
  t69 = t27 ** 2
  t72 = 0.1e1 / t30 / t29
  t74 = s0 ** 2
  t76 = t44 ** 2
  t77 = 0.1e1 / t76
  t79 = t68 * t69 * t72 * t74 * t34 * t77
  t82 = t7 * t20
  t90 = t69 * t72 * t74 * t34 * t77 * t25
  t94 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t45 / 0.30e2 - 0.7e1 / 0.180e3 * t7 * t20 / t49 * t45 * t59 + t7 * t20 * t64 * t45 * t79 / 0.270e3 + t82 * t64 * t45 * t68 * t90 / 0.270e3)
  t112 = 0.1e1 / t37 / t49 / t36 / r0
  t123 = t5 ** 2
  t127 = t49 ** 2
  t132 = t4 / t123 / t29 * t20 / t21 / t127 / t36
  t134 = t45 * t68 * params.C2
  t138 = t74 * s0 / t76 / t44
  t146 = params.p ** 2
  t153 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t36 * t45 + 0.41e2 / 0.270e3 * t7 * t20 / t49 / r0 * t45 * t59 - t7 * t20 * t112 * t45 * t79 / 0.30e2 - t82 * t112 * t45 * t68 * t90 / 0.30e2 + 0.2e1 / 0.405e3 * t132 * t134 * t138 + 0.2e1 / 0.135e3 * t132 * t134 * t138 * t25 + 0.4e1 / 0.405e3 * t132 * t134 * t138 / t146)
  v3rho3_0_ = 0.2e1 * r0 * t153 + 0.6e1 * t94

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
  t26 = 0.1e1 / params.p
  t28 = 6 ** (0.1e1 / 0.3e1)
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t35 = 2 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = t22 ** 2
  t44 = 0.1e1 + params.C2 * t26 * t28 * t33 * s0 * t36 / t37 / t21 / 0.24e2
  t45 = t44 ** (-params.p)
  t49 = t21 ** 2
  t60 = params.C2 * t28 * t33 * s0 * t36 / t44
  t63 = t21 * r0
  t66 = 0.1e1 / t37 / t49 / t63
  t70 = params.C2 ** 2
  t71 = t28 ** 2
  t74 = 0.1e1 / t31 / t30
  t76 = s0 ** 2
  t78 = t44 ** 2
  t79 = 0.1e1 / t78
  t81 = t70 * t71 * t74 * t76 * t35 * t79
  t84 = t7 * t20
  t92 = t71 * t74 * t76 * t35 * t79 * t26
  t95 = t5 ** 2
  t98 = t4 / t95 / t30
  t99 = t49 ** 2
  t104 = t98 * t20 / t22 / t99 / t21
  t106 = t45 * t70 * params.C2
  t110 = t76 * s0 / t78 / t44
  t111 = t106 * t110
  t115 = t106 * t110 * t26
  t118 = params.p ** 2
  t119 = 0.1e1 / t118
  t121 = t106 * t110 * t119
  t125 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t22 / t21 * t45 + 0.41e2 / 0.270e3 * t7 * t20 / t49 / r0 * t45 * t60 - t7 * t20 * t66 * t45 * t81 / 0.30e2 - t84 * t66 * t45 * t70 * t92 / 0.30e2 + 0.2e1 / 0.405e3 * t104 * t111 + 0.2e1 / 0.135e3 * t104 * t115 + 0.4e1 / 0.405e3 * t104 * t121)
  t133 = t49 * t21
  t141 = 0.1e1 / t37 / t99
  t156 = t98 * t20 / t22 / t99 / t63
  t164 = 0.1e1 / t99 / t133
  t168 = t70 ** 2
  t171 = t76 ** 2
  t173 = t78 ** 2
  t174 = 0.1e1 / t173
  t182 = t98 * t20 * t164 * t45 * t168
  t183 = t171 * t174
  t186 = t28 * t33 * t36
  t200 = -0.14e2 / 0.135e3 * t7 * t20 / t22 / t63 * t45 - 0.611e3 / 0.810e3 * t7 * t20 / t133 * t45 * t60 + 0.703e3 / 0.2430e4 * t7 * t20 * t141 * t45 * t81 + 0.703e3 / 0.2430e4 * t84 * t141 * t45 * t70 * t92 - 0.116e3 / 0.1215e4 * t156 * t111 - 0.116e3 / 0.405e3 * t156 * t115 - 0.232e3 / 0.1215e4 * t156 * t121 + 0.2e1 / 0.3645e4 * t98 * t20 * t164 * t45 * t168 * t28 * t33 * t171 * t36 * t174 + 0.4e1 / 0.1215e4 * t182 * t183 * t26 * t186 + 0.22e2 / 0.3645e4 * t182 * t183 * t119 * t186 + 0.4e1 / 0.1215e4 * t182 * t183 / t118 / params.p * t186
  t201 = f.my_piecewise3(t2, 0, t200)
  v4rho4_0_ = 0.2e1 * r0 * t201 + 0.8e1 * t125

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
  t35 = 0.1e1 / params.p
  t37 = 6 ** (0.1e1 / 0.3e1)
  t38 = params.C2 * t35 * t37
  t39 = jnp.pi ** 2
  t40 = t39 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t42 = 0.1e1 / t41
  t44 = r0 ** 2
  t45 = r0 ** (0.1e1 / 0.3e1)
  t46 = t45 ** 2
  t52 = 0.1e1 + t38 * t42 * s0 / t46 / t44 / 0.24e2
  t53 = t52 ** (-params.p)
  t55 = t6 * t31 * t33 * t53
  t57 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t58 = t57 ** 2
  t59 = t58 * f.p.zeta_threshold
  t61 = f.my_piecewise3(t21, t59, t23 * t20)
  t62 = 0.1e1 / t32
  t65 = t6 * t61 * t62 * t53
  t66 = t65 / 0.10e2
  t69 = t6 * t61 * t33 * t53
  t71 = params.C2 * t37 * t42
  t72 = t44 * r0
  t76 = 0.1e1 / t52
  t78 = t71 * s0 / t46 / t72 * t76
  t82 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t55 + t66 + t69 * t78 / 0.60e2)
  t84 = r1 <= f.p.dens_threshold
  t85 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t86 = 0.1e1 + t85
  t87 = t86 <= f.p.zeta_threshold
  t88 = t86 ** (0.1e1 / 0.3e1)
  t89 = t88 ** 2
  t91 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t94 = f.my_piecewise3(t87, 0, 0.5e1 / 0.3e1 * t89 * t91)
  t97 = r1 ** 2
  t98 = r1 ** (0.1e1 / 0.3e1)
  t99 = t98 ** 2
  t105 = 0.1e1 + t38 * t42 * s2 / t99 / t97 / 0.24e2
  t106 = t105 ** (-params.p)
  t108 = t6 * t94 * t33 * t106
  t111 = f.my_piecewise3(t87, t59, t89 * t86)
  t114 = t6 * t111 * t62 * t106
  t115 = t114 / 0.10e2
  t117 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t108 + t115)
  t119 = 0.1e1 / t22
  t120 = t28 ** 2
  t125 = t17 / t24 / t7
  t127 = -0.2e1 * t25 + 0.2e1 * t125
  t128 = f.my_piecewise5(t11, 0, t15, 0, t127)
  t132 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t119 * t120 + 0.5e1 / 0.3e1 * t23 * t128)
  t139 = t6 * t31 * t62 * t53
  t144 = 0.1e1 / t32 / t7
  t148 = t6 * t61 * t144 * t53 / 0.30e2
  t149 = t65 * t78
  t151 = params.C2 ** 2
  t152 = t37 ** 2
  t155 = 0.1e1 / t40 / t39
  t156 = t151 * t152 * t155
  t157 = s0 ** 2
  t158 = t44 ** 2
  t161 = 0.1e1 / t45 / t158 / t72
  t163 = t52 ** 2
  t164 = 0.1e1 / t163
  t180 = t152 * t155
  t188 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t132 * t33 * t53 + t139 / 0.5e1 + t55 * t78 / 0.30e2 - t148 + t149 / 0.45e2 + t69 * t156 * t157 * t161 * t164 / 0.540e3 - 0.11e2 / 0.180e3 * t69 * t71 * s0 / t46 / t158 * t76 + t6 * t61 * t33 * t53 * t151 * t180 * t157 * t161 * t164 * t35 / 0.540e3)
  t189 = 0.1e1 / t88
  t190 = t91 ** 2
  t194 = f.my_piecewise5(t15, 0, t11, 0, -t127)
  t198 = f.my_piecewise3(t87, 0, 0.10e2 / 0.9e1 * t189 * t190 + 0.5e1 / 0.3e1 * t89 * t194)
  t205 = t6 * t94 * t62 * t106
  t210 = t6 * t111 * t144 * t106 / 0.30e2
  t212 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t6 * t198 * t33 * t106 + t205 / 0.5e1 - t210)
  d11 = 0.2e1 * t82 + 0.2e1 * t117 + t7 * (t188 + t212)
  t215 = -t8 - t26
  t216 = f.my_piecewise5(t11, 0, t15, 0, t215)
  t219 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t216)
  t222 = t6 * t219 * t33 * t53
  t225 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t222 + t66)
  t227 = f.my_piecewise5(t15, 0, t11, 0, -t215)
  t230 = f.my_piecewise3(t87, 0, 0.5e1 / 0.3e1 * t89 * t227)
  t233 = t6 * t230 * t33 * t106
  t237 = t6 * t111 * t33 * t106
  t238 = t97 * r1
  t242 = 0.1e1 / t105
  t244 = t71 * s2 / t99 / t238 * t242
  t248 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t233 + t115 + t237 * t244 / 0.60e2)
  t252 = 0.2e1 * t125
  t253 = f.my_piecewise5(t11, 0, t15, 0, t252)
  t257 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t119 * t216 * t28 + 0.5e1 / 0.3e1 * t23 * t253)
  t264 = t6 * t219 * t62 * t53
  t271 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t257 * t33 * t53 + t264 / 0.10e2 + t222 * t78 / 0.60e2 + t139 / 0.10e2 - t148 + t149 / 0.90e2)
  t275 = f.my_piecewise5(t15, 0, t11, 0, -t252)
  t279 = f.my_piecewise3(t87, 0, 0.10e2 / 0.9e1 * t189 * t227 * t91 + 0.5e1 / 0.3e1 * t89 * t275)
  t286 = t6 * t230 * t62 * t106
  t291 = t114 * t244
  t294 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t6 * t279 * t33 * t106 + t286 / 0.10e2 + t205 / 0.10e2 - t210 + t108 * t244 / 0.60e2 + t291 / 0.90e2)
  d12 = t82 + t117 + t225 + t248 + t7 * (t271 + t294)
  t299 = t216 ** 2
  t303 = 0.2e1 * t25 + 0.2e1 * t125
  t304 = f.my_piecewise5(t11, 0, t15, 0, t303)
  t308 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t119 * t299 + 0.5e1 / 0.3e1 * t23 * t304)
  t315 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t308 * t33 * t53 + t264 / 0.5e1 - t148)
  t316 = t227 ** 2
  t320 = f.my_piecewise5(t15, 0, t11, 0, -t303)
  t324 = f.my_piecewise3(t87, 0, 0.10e2 / 0.9e1 * t189 * t316 + 0.5e1 / 0.3e1 * t89 * t320)
  t333 = s2 ** 2
  t334 = t97 ** 2
  t337 = 0.1e1 / t98 / t334 / t238
  t339 = t105 ** 2
  t340 = 0.1e1 / t339
  t363 = f.my_piecewise3(t84, 0, 0.3e1 / 0.20e2 * t6 * t324 * t33 * t106 + t286 / 0.5e1 + t233 * t244 / 0.30e2 - t210 + t291 / 0.45e2 + t237 * t156 * t333 * t337 * t340 / 0.540e3 - 0.11e2 / 0.180e3 * t237 * t71 * s2 / t99 / t334 * t242 + t6 * t111 * t33 * t106 * t151 * t180 * t333 * t337 * t340 * t35 / 0.540e3)
  d22 = 0.2e1 * t225 + 0.2e1 * t248 + t7 * (t315 + t363)
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
  t46 = 0.1e1 / params.p
  t48 = 6 ** (0.1e1 / 0.3e1)
  t49 = params.C2 * t46 * t48
  t50 = jnp.pi ** 2
  t51 = t50 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t53 = 0.1e1 / t52
  t55 = r0 ** 2
  t56 = r0 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t63 = 0.1e1 + t49 * t53 * s0 / t57 / t55 / 0.24e2
  t64 = t63 ** (-params.p)
  t66 = t6 * t42 * t44 * t64
  t70 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t71 = 0.1e1 / t43
  t74 = t6 * t70 * t71 * t64
  t78 = t6 * t70 * t44 * t64
  t80 = params.C2 * t48 * t53
  t81 = t55 * r0
  t85 = 0.1e1 / t63
  t87 = t80 * s0 / t57 / t81 * t85
  t90 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t91 = t90 ** 2
  t92 = t91 * f.p.zeta_threshold
  t94 = f.my_piecewise3(t21, t92, t32 * t20)
  t96 = 0.1e1 / t43 / t7
  t99 = t6 * t94 * t96 * t64
  t103 = t6 * t94 * t71 * t64
  t106 = t94 * t44
  t107 = t106 * t64
  t108 = t6 * t107
  t109 = params.C2 ** 2
  t110 = t48 ** 2
  t113 = 0.1e1 / t51 / t50
  t114 = t109 * t110 * t113
  t115 = s0 ** 2
  t116 = t55 ** 2
  t119 = 0.1e1 / t56 / t116 / t81
  t121 = t63 ** 2
  t122 = 0.1e1 / t121
  t124 = t114 * t115 * t119 * t122
  t131 = t80 * s0 / t57 / t116 * t85
  t134 = t6 * t94
  t136 = t44 * t64 * t109
  t137 = t134 * t136
  t139 = t110 * t113 * t115
  t142 = t139 * t119 * t122 * t46
  t146 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t66 + t74 / 0.5e1 + t78 * t87 / 0.30e2 - t99 / 0.30e2 + t103 * t87 / 0.45e2 + t108 * t124 / 0.540e3 - 0.11e2 / 0.180e3 * t108 * t131 + t137 * t142 / 0.540e3)
  t148 = r1 <= f.p.dens_threshold
  t149 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t150 = 0.1e1 + t149
  t151 = t150 <= f.p.zeta_threshold
  t152 = t150 ** (0.1e1 / 0.3e1)
  t153 = 0.1e1 / t152
  t155 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t156 = t155 ** 2
  t159 = t152 ** 2
  t161 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t165 = f.my_piecewise3(t151, 0, 0.10e2 / 0.9e1 * t153 * t156 + 0.5e1 / 0.3e1 * t159 * t161)
  t168 = r1 ** 2
  t169 = r1 ** (0.1e1 / 0.3e1)
  t170 = t169 ** 2
  t177 = (0.1e1 + t49 * t53 * s2 / t170 / t168 / 0.24e2) ** (-params.p)
  t183 = f.my_piecewise3(t151, 0, 0.5e1 / 0.3e1 * t159 * t155)
  t189 = f.my_piecewise3(t151, t92, t159 * t150)
  t195 = f.my_piecewise3(t148, 0, 0.3e1 / 0.20e2 * t6 * t165 * t44 * t177 + t6 * t183 * t71 * t177 / 0.5e1 - t6 * t189 * t96 * t177 / 0.30e2)
  t197 = t116 ** 2
  t199 = 0.1e1 / t56 / t197
  t231 = t4 ** 2
  t234 = t3 / t231 / t50
  t236 = t109 * params.C2
  t238 = t115 * s0
  t240 = 0.1e1 / t197 / t81
  t243 = 0.1e1 / t121 / t63
  t266 = t24 ** 2
  t270 = 0.6e1 * t34 - 0.6e1 * t17 / t266
  t271 = f.my_piecewise5(t11, 0, t15, 0, t270)
  t275 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t271)
  t280 = t234 * t107
  t281 = t236 * t238
  t282 = t240 * t243
  t287 = params.p ** 2
  t302 = 0.1e1 / t43 / t24
  t307 = -0.11e2 / 0.540e3 * t108 * t114 * t115 * t199 * t122 + 0.77e2 / 0.270e3 * t108 * t80 * s0 / t57 / t116 / r0 * t85 - 0.11e2 / 0.540e3 * t137 * t139 * t199 * t122 * t46 - 0.11e2 / 0.60e2 * t78 * t131 + t6 * t70 * t136 * t142 / 0.180e3 - 0.11e2 / 0.90e2 * t103 * t131 + t134 * t71 * t64 * t109 * t142 / 0.270e3 + t234 * t106 * t64 * t236 * t238 * t240 * t243 / 0.810e3 + t66 * t87 / 0.20e2 + t74 * t87 / 0.15e2 + t78 * t124 / 0.180e3 - t99 * t87 / 0.90e2 + t103 * t124 / 0.270e3 + 0.3e1 / 0.20e2 * t6 * t275 * t44 * t64 + t280 * t281 * t282 * t46 / 0.270e3 + t280 * t281 * t282 / t287 / 0.405e3 + 0.3e1 / 0.10e2 * t6 * t42 * t71 * t64 - t6 * t70 * t96 * t64 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t94 * t302 * t64
  t308 = f.my_piecewise3(t1, 0, t307)
  t318 = f.my_piecewise5(t15, 0, t11, 0, -t270)
  t322 = f.my_piecewise3(t151, 0, -0.10e2 / 0.27e2 / t152 / t150 * t156 * t155 + 0.10e2 / 0.3e1 * t153 * t155 * t161 + 0.5e1 / 0.3e1 * t159 * t318)
  t340 = f.my_piecewise3(t148, 0, 0.3e1 / 0.20e2 * t6 * t322 * t44 * t177 + 0.3e1 / 0.10e2 * t6 * t165 * t71 * t177 - t6 * t183 * t96 * t177 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t189 * t302 * t177)
  d111 = 0.3e1 * t146 + 0.3e1 * t195 + t7 * (t308 + t340)

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
  t22 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t23 * f.p.zeta_threshold
  t25 = t20 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = f.my_piecewise3(t21, t24, t26 * t20)
  t29 = t7 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = t28 * t30
  t32 = 0.1e1 / params.p
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = params.C2 * t32 * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t49 = 0.1e1 + t35 * t39 * s0 / t43 / t41 / 0.24e2
  t50 = t49 ** (-params.p)
  t51 = t31 * t50
  t52 = t6 * t51
  t53 = params.C2 ** 2
  t54 = t34 ** 2
  t57 = 0.1e1 / t37 / t36
  t58 = t53 * t54 * t57
  t59 = s0 ** 2
  t60 = t41 ** 2
  t61 = t60 ** 2
  t63 = 0.1e1 / t42 / t61
  t65 = t49 ** 2
  t66 = 0.1e1 / t65
  t68 = t58 * t59 * t63 * t66
  t72 = params.C2 * t34 * t39
  t77 = 0.1e1 / t49
  t79 = t72 * s0 / t43 / t60 / r0 * t77
  t82 = t6 * t28
  t83 = t30 * t50
  t84 = t83 * t53
  t85 = t82 * t84
  t87 = t54 * t57 * t59
  t90 = t87 * t63 * t66 * t32
  t93 = t7 ** 2
  t94 = 0.1e1 / t93
  t96 = -t17 * t94 + t8
  t97 = f.my_piecewise5(t11, 0, t15, 0, t96)
  t100 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t97)
  t101 = t100 * t30
  t102 = t101 * t50
  t103 = t6 * t102
  t108 = t72 * s0 / t43 / t60 * t77
  t111 = t6 * t100
  t112 = t111 * t84
  t113 = t41 * r0
  t116 = 0.1e1 / t42 / t60 / t113
  t119 = t87 * t116 * t66 * t32
  t122 = 0.1e1 / t29
  t123 = t28 * t122
  t124 = t123 * t50
  t125 = t6 * t124
  t129 = t122 * t50 * t53
  t130 = t82 * t129
  t133 = t4 ** 2
  t136 = t3 / t133 / t36
  t137 = t136 * t31
  t138 = t53 * params.C2
  t139 = t50 * t138
  t140 = t59 * s0
  t142 = 0.1e1 / t61 / t113
  t145 = 0.1e1 / t65 / t49
  t147 = t139 * t140 * t142 * t145
  t150 = 0.1e1 / t25
  t151 = t97 ** 2
  t154 = t93 * t7
  t155 = 0.1e1 / t154
  t158 = 0.2e1 * t17 * t155 - 0.2e1 * t94
  t159 = f.my_piecewise5(t11, 0, t15, 0, t158)
  t163 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t150 * t151 + 0.5e1 / 0.3e1 * t26 * t159)
  t166 = t6 * t163 * t30 * t50
  t171 = t72 * s0 / t43 / t113 * t77
  t176 = t6 * t100 * t122 * t50
  t181 = t58 * t59 * t116 * t66
  t185 = 0.1e1 / t29 / t7
  t188 = t6 * t28 * t185 * t50
  t194 = 0.1e1 / t25 / t20
  t198 = t150 * t97
  t201 = t93 ** 2
  t202 = 0.1e1 / t201
  t205 = -0.6e1 * t17 * t202 + 0.6e1 * t155
  t206 = f.my_piecewise5(t11, 0, t15, 0, t205)
  t210 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t194 * t151 * t97 + 0.10e2 / 0.3e1 * t198 * t159 + 0.5e1 / 0.3e1 * t26 * t206)
  t213 = t6 * t210 * t30 * t50
  t215 = t136 * t51
  t216 = t138 * t140
  t217 = t142 * t145
  t219 = t216 * t217 * t32
  t222 = params.p ** 2
  t223 = 0.1e1 / t222
  t225 = t216 * t217 * t223
  t230 = t6 * t163 * t122 * t50
  t234 = t6 * t100 * t185 * t50
  t237 = 0.1e1 / t29 / t93
  t240 = t6 * t28 * t237 * t50
  t242 = -0.11e2 / 0.540e3 * t52 * t68 + 0.77e2 / 0.270e3 * t52 * t79 - 0.11e2 / 0.540e3 * t85 * t90 - 0.11e2 / 0.60e2 * t103 * t108 + t112 * t119 / 0.180e3 - 0.11e2 / 0.90e2 * t125 * t108 + t130 * t119 / 0.270e3 + t137 * t147 / 0.810e3 + t166 * t171 / 0.20e2 + t176 * t171 / 0.15e2 + t103 * t181 / 0.180e3 - t188 * t171 / 0.90e2 + t125 * t181 / 0.270e3 + 0.3e1 / 0.20e2 * t213 + t215 * t219 / 0.270e3 + t215 * t225 / 0.405e3 + 0.3e1 / 0.10e2 * t230 - t234 / 0.10e2 + 0.2e1 / 0.45e2 * t240
  t243 = f.my_piecewise3(t1, 0, t242)
  t245 = r1 <= f.p.dens_threshold
  t246 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t247 = 0.1e1 + t246
  t248 = t247 <= f.p.zeta_threshold
  t249 = t247 ** (0.1e1 / 0.3e1)
  t251 = 0.1e1 / t249 / t247
  t253 = f.my_piecewise5(t15, 0, t11, 0, -t96)
  t254 = t253 ** 2
  t258 = 0.1e1 / t249
  t259 = t258 * t253
  t261 = f.my_piecewise5(t15, 0, t11, 0, -t158)
  t264 = t249 ** 2
  t266 = f.my_piecewise5(t15, 0, t11, 0, -t205)
  t270 = f.my_piecewise3(t248, 0, -0.10e2 / 0.27e2 * t251 * t254 * t253 + 0.10e2 / 0.3e1 * t259 * t261 + 0.5e1 / 0.3e1 * t264 * t266)
  t273 = r1 ** 2
  t274 = r1 ** (0.1e1 / 0.3e1)
  t275 = t274 ** 2
  t282 = (0.1e1 + t35 * t39 * s2 / t275 / t273 / 0.24e2) ** (-params.p)
  t291 = f.my_piecewise3(t248, 0, 0.10e2 / 0.9e1 * t258 * t254 + 0.5e1 / 0.3e1 * t264 * t261)
  t298 = f.my_piecewise3(t248, 0, 0.5e1 / 0.3e1 * t264 * t253)
  t304 = f.my_piecewise3(t248, t24, t264 * t247)
  t310 = f.my_piecewise3(t245, 0, 0.3e1 / 0.20e2 * t6 * t270 * t30 * t282 + 0.3e1 / 0.10e2 * t6 * t291 * t122 * t282 - t6 * t298 * t185 * t282 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t304 * t237 * t282)
  t312 = t20 ** 2
  t315 = t151 ** 2
  t321 = t159 ** 2
  t330 = -0.24e2 * t202 + 0.24e2 * t17 / t201 / t7
  t331 = f.my_piecewise5(t11, 0, t15, 0, t330)
  t335 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t25 / t312 * t315 - 0.20e2 / 0.9e1 * t194 * t151 * t159 + 0.10e2 / 0.3e1 * t150 * t321 + 0.40e2 / 0.9e1 * t198 * t206 + 0.5e1 / 0.3e1 * t26 * t331)
  t353 = 0.1e1 / t29 / t154
  t358 = t136 * t124
  t362 = 0.1e1 / t61 / t60
  t363 = t362 * t145
  t372 = t136 * t102
  t380 = t53 ** 2
  t382 = t136 * t28 * t83 * t380
  t383 = t59 ** 2
  t384 = t60 * t41
  t389 = t65 ** 2
  t391 = t383 / t43 / t61 / t384 / t389
  t405 = 0.1e1 / t42 / t61 / r0
  t433 = 0.3e1 / 0.20e2 * t6 * t335 * t30 * t50 + 0.2e1 / 0.5e1 * t6 * t210 * t122 * t50 - t6 * t163 * t185 * t50 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t100 * t237 * t50 - 0.14e2 / 0.135e3 * t6 * t28 * t353 * t50 + 0.8e1 / 0.1215e4 * t358 * t225 - 0.11e2 / 0.135e3 * t215 * t216 * t363 * t32 - 0.22e2 / 0.405e3 * t215 * t216 * t363 * t223 + 0.2e1 / 0.135e3 * t372 * t219 + 0.4e1 / 0.405e3 * t372 * t225 + 0.4e1 / 0.405e3 * t358 * t219 + t382 * t391 * t32 * t34 * t39 / 0.1215e4 - 0.11e2 / 0.135e3 * t112 * t90 + t6 * t163 * t84 * t119 / 0.90e2 + 0.979e3 / 0.4860e4 * t85 * t87 * t405 * t66 * t32 - t82 * t185 * t50 * t53 * t119 / 0.405e3 + 0.2e1 / 0.135e3 * t111 * t129 * t119 - 0.22e2 / 0.405e3 * t130 * t90 + t382 * t391 / t222 / params.p * t34 * t39 / 0.1215e4 + 0.11e2 / 0.7290e4 * t382 * t391 * t223 * t34 * t39
  t490 = 0.4e1 / 0.1215e4 * t136 * t123 * t147 - 0.11e2 / 0.405e3 * t137 * t139 * t140 * t362 * t145 + 0.2e1 / 0.405e3 * t136 * t101 * t147 + 0.8e1 / 0.405e3 * t240 * t171 + 0.2e1 / 0.15e2 * t230 * t171 - 0.2e1 / 0.45e2 * t234 * t171 - 0.22e2 / 0.45e2 * t176 * t108 + 0.11e2 / 0.135e3 * t188 * t108 - 0.22e2 / 0.405e3 * t125 * t68 + 0.979e3 / 0.4860e4 * t52 * t58 * t59 * t405 * t66 + 0.308e3 / 0.405e3 * t125 * t79 - 0.1309e4 / 0.810e3 * t52 * t72 * s0 / t43 / t384 * t77 + 0.2e1 / 0.135e3 * t176 * t181 - t188 * t181 / 0.405e3 + t215 * t380 * t34 * t39 * t391 / 0.7290e4 + t213 * t171 / 0.15e2 + t166 * t181 / 0.90e2 - 0.11e2 / 0.135e3 * t103 * t68 + 0.154e3 / 0.135e3 * t103 * t79 - 0.11e2 / 0.30e2 * t166 * t108
  t492 = f.my_piecewise3(t1, 0, t433 + t490)
  t493 = t247 ** 2
  t496 = t254 ** 2
  t502 = t261 ** 2
  t508 = f.my_piecewise5(t15, 0, t11, 0, -t330)
  t512 = f.my_piecewise3(t248, 0, 0.40e2 / 0.81e2 / t249 / t493 * t496 - 0.20e2 / 0.9e1 * t251 * t254 * t261 + 0.10e2 / 0.3e1 * t258 * t502 + 0.40e2 / 0.9e1 * t259 * t266 + 0.5e1 / 0.3e1 * t264 * t508)
  t534 = f.my_piecewise3(t245, 0, 0.3e1 / 0.20e2 * t6 * t512 * t30 * t282 + 0.2e1 / 0.5e1 * t6 * t270 * t122 * t282 - t6 * t291 * t185 * t282 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t298 * t237 * t282 - 0.14e2 / 0.135e3 * t6 * t304 * t353 * t282)
  d1111 = 0.4e1 * t243 + 0.4e1 * t310 + t7 * (t492 + t534)

  res = {'v4rho4': d1111}
  return res
