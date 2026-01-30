"""Generated from mgga_k_csk.mpl."""

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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE

  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 20 / 9 * q - 40 / 27 * p

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I = lambda z: f.my_piecewise5(z < -csk_I_cutoff_large, 0, z > -csk_I_cutoff_small, 1, csk_I_negz(jnp.maximum(jnp.minimum(z, -csk_I_cutoff_small), -csk_I_cutoff_large)))

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE

  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 20 / 9 * q - 40 / 27 * p

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I = lambda z: f.my_piecewise5(z < -csk_I_cutoff_large, 0, z > -csk_I_cutoff_small, 1, csk_I_negz(jnp.maximum(jnp.minimum(z, -csk_I_cutoff_small), -csk_I_cutoff_large)))

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE
  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 20 / 9 * q - 40 / 27 * p

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  t37 = t32 / t35
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t44 = t37 * s0 * t42
  t47 = 0.1e1 / t40 / r0
  t52 = 0.5e1 / 0.54e2 * t37 * l0 * t47 - 0.5e1 / 0.81e2 * t44
  t54 = jnp.log(0.1e1 - DBL_EPSILON)
  t55 = 0.1e1 / params.csk_a
  t56 = (-t54) ** (-t55)
  t57 = t52 < -t56
  t58 = jnp.log(DBL_EPSILON)
  t59 = (-t58) ** (-t55)
  t60 = -t59 < t52
  t61 = f.my_piecewise3(t60, -t59, t52)
  t62 = -t56 < t61
  t63 = f.my_piecewise3(t62, t61, -t56)
  t64 = abs(t63)
  t65 = t64 ** params.csk_a
  t66 = 0.1e1 / t65
  t67 = jnp.exp(-t66)
  t68 = 0.1e1 - t67
  t69 = t68 ** t55
  t70 = f.my_piecewise5(t57, 0, t60, 1, t69)
  t72 = 0.1e1 + 0.5e1 / 0.72e2 * t44 + t52 * t70
  t76 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t72)
  t77 = r1 <= f.p.dens_threshold
  t78 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t79 = 0.1e1 + t78
  t80 = t79 <= f.p.zeta_threshold
  t81 = t79 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t84 = f.my_piecewise3(t80, t24, t82 * t79)
  t85 = t84 * t30
  t86 = r1 ** 2
  t87 = r1 ** (0.1e1 / 0.3e1)
  t88 = t87 ** 2
  t90 = 0.1e1 / t88 / t86
  t92 = t37 * s2 * t90
  t95 = 0.1e1 / t88 / r1
  t100 = 0.5e1 / 0.54e2 * t37 * l1 * t95 - 0.5e1 / 0.81e2 * t92
  t101 = t100 < -t56
  t102 = -t59 < t100
  t103 = f.my_piecewise3(t102, -t59, t100)
  t104 = -t56 < t103
  t105 = f.my_piecewise3(t104, t103, -t56)
  t106 = abs(t105)
  t107 = t106 ** params.csk_a
  t108 = 0.1e1 / t107
  t109 = jnp.exp(-t108)
  t110 = 0.1e1 - t109
  t111 = t110 ** t55
  t112 = f.my_piecewise5(t101, 0, t102, 1, t111)
  t114 = 0.1e1 + 0.5e1 / 0.72e2 * t92 + t100 * t112
  t118 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t85 * t114)
  t119 = t7 ** 2
  t121 = t17 / t119
  t122 = t8 - t121
  t123 = f.my_piecewise5(t11, 0, t15, 0, t122)
  t126 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t123)
  t131 = 0.1e1 / t29
  t135 = t6 * t28 * t131 * t72 / 0.10e2
  t140 = t37 * s0 / t40 / t38 / r0
  t146 = -0.25e2 / 0.162e3 * t37 * l0 * t42 + 0.40e2 / 0.243e3 * t140
  t149 = jnp.abs(1 - t63)
  t150 = t69 * t66 * t149
  t151 = f.my_piecewise3(t60, 0, t146)
  t152 = f.my_piecewise3(t62, t151, 0)
  t153 = 0.1e1 / t64
  t156 = t67 / t68
  t159 = f.my_piecewise5(t57, 0, t60, 0, -t150 * t152 * t153 * t156)
  t166 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t126 * t30 * t72 + t135 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.5e1 / 0.27e2 * t140 + t146 * t70 + t52 * t159))
  t168 = f.my_piecewise5(t15, 0, t11, 0, -t122)
  t171 = f.my_piecewise3(t80, 0, 0.5e1 / 0.3e1 * t82 * t168)
  t179 = t6 * t84 * t131 * t114 / 0.10e2
  t181 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t171 * t30 * t114 + t179)
  vrho_0_ = t76 + t118 + t7 * (t166 + t181)
  t184 = -t8 - t121
  t185 = f.my_piecewise5(t11, 0, t15, 0, t184)
  t188 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t185)
  t194 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t188 * t30 * t72 + t135)
  t196 = f.my_piecewise5(t15, 0, t11, 0, -t184)
  t199 = f.my_piecewise3(t80, 0, 0.5e1 / 0.3e1 * t82 * t196)
  t208 = t37 * s2 / t88 / t86 / r1
  t214 = -0.25e2 / 0.162e3 * t37 * l1 * t90 + 0.40e2 / 0.243e3 * t208
  t217 = jnp.abs(1 - t105)
  t218 = t111 * t108 * t217
  t219 = f.my_piecewise3(t102, 0, t214)
  t220 = f.my_piecewise3(t104, t219, 0)
  t221 = 0.1e1 / t106
  t224 = t109 / t110
  t227 = f.my_piecewise5(t101, 0, t102, 0, -t218 * t220 * t221 * t224)
  t234 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t199 * t30 * t114 + t179 + 0.3e1 / 0.20e2 * t6 * t85 * (-0.5e1 / 0.27e2 * t208 + t214 * t112 + t100 * t227))
  vrho_1_ = t76 + t118 + t7 * (t194 + t234)
  t237 = t37 * t42
  t243 = f.my_piecewise3(t60, 0, -0.5e1 / 0.81e2 * t237)
  t244 = f.my_piecewise3(t62, t243, 0)
  t248 = f.my_piecewise5(t57, 0, t60, 0, -t150 * t244 * t153 * t156)
  t254 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.72e2 * t237 - 0.5e1 / 0.81e2 * t37 * t42 * t70 + t52 * t248))
  vsigma_0_ = t7 * t254
  vsigma_1_ = 0.0e0
  t255 = t37 * t90
  t261 = f.my_piecewise3(t102, 0, -0.5e1 / 0.81e2 * t255)
  t262 = f.my_piecewise3(t104, t261, 0)
  t266 = f.my_piecewise5(t101, 0, t102, 0, -t218 * t262 * t221 * t224)
  t272 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t85 * (0.5e1 / 0.72e2 * t255 - 0.5e1 / 0.81e2 * t37 * t90 * t112 + t100 * t266))
  vsigma_2_ = t7 * t272
  t278 = f.my_piecewise3(t60, 0, 0.5e1 / 0.54e2 * t37 * t47)
  t279 = f.my_piecewise3(t62, t278, 0)
  t283 = f.my_piecewise5(t57, 0, t60, 0, -t150 * t279 * t153 * t156)
  t289 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.54e2 * t37 * t47 * t70 + t52 * t283))
  vlapl_0_ = t7 * t289
  t295 = f.my_piecewise3(t102, 0, 0.5e1 / 0.54e2 * t37 * t95)
  t296 = f.my_piecewise3(t104, t295, 0)
  t300 = f.my_piecewise5(t101, 0, t102, 0, -t218 * t296 * t221 * t224)
  t306 = f.my_piecewise3(t77, 0, 0.3e1 / 0.20e2 * t6 * t85 * (0.5e1 / 0.54e2 * t37 * t95 * t112 + t100 * t300))
  vlapl_1_ = t7 * t306
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
  CSK_P_SCALE = np.float64(0.11183527356860551)
  params_csk_a_raw = params.csk_a
  if isinstance(params_csk_a_raw, (str, bytes, dict)):
    params_csk_a = params_csk_a_raw
  else:
    try:
      params_csk_a_seq = list(params_csk_a_raw)
    except TypeError:
      params_csk_a = params_csk_a_raw
    else:
      params_csk_a_seq = np.asarray(params_csk_a_seq, dtype=np.float64)
      params_csk_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_csk_a_seq))

  csk_p = lambda x: X2S ** 2 * x ** 2 * CSK_P_SCALE
  csk_q = lambda u: jnp.zeros_like(u)

  csk_z = lambda p, q: 20 / 9 * q - 40 / 27 * p

  csk_I_negz = lambda z: (1 - jnp.exp(-1 / jnp.abs(z) ** params_csk_a)) ** (1 / params_csk_a)

  csk_I_cutoff_small = (-jnp.log(DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_I_cutoff_large = (-jnp.log(1 - DBL_EPSILON)) ** (-1 / params_csk_a)

  csk_f0 = lambda p, q, z: 1 + 5 * p / 3 + z * csk_I(z)

  csk_f = lambda x, u: csk_f0(csk_p(x), csk_q(u), csk_z(csk_p(x), csk_q(u)))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0=None, t1=None: mgga_kinetic(f, params, csk_f, rs, z, xs0, xs1, u0, u1)

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
  t29 = t24 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t22 / t33
  t37 = t29 * t32 * t35
  t39 = l0 * t31
  t41 = 0.1e1 / t22 / r0
  t46 = 0.5e1 / 0.54e2 * t29 * t39 * t41 - 0.5e1 / 0.81e2 * t37
  t48 = jnp.log(0.1e1 - DBL_EPSILON)
  t49 = 0.1e1 / params.csk_a
  t50 = (-t48) ** (-t49)
  t51 = t46 < -t50
  t52 = jnp.log(DBL_EPSILON)
  t53 = (-t52) ** (-t49)
  t54 = -t53 < t46
  t55 = f.my_piecewise3(t54, -t53, t46)
  t56 = -t50 < t55
  t57 = f.my_piecewise3(t56, t55, -t50)
  t58 = abs(t57)
  t59 = t58 ** params.csk_a
  t60 = 0.1e1 / t59
  t61 = jnp.exp(-t60)
  t62 = 0.1e1 - t61
  t63 = t62 ** t49
  t64 = f.my_piecewise5(t51, 0, t54, 1, t63)
  t66 = 0.1e1 + 0.5e1 / 0.72e2 * t37 + t46 * t64
  t70 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t66)
  t80 = t29 * t32 / t22 / t33 / r0
  t86 = -0.25e2 / 0.162e3 * t29 * t39 * t35 + 0.40e2 / 0.243e3 * t80
  t89 = jnp.abs(1 - t57)
  t90 = t63 * t60 * t89
  t91 = f.my_piecewise3(t54, 0, t86)
  t92 = f.my_piecewise3(t56, t91, 0)
  t93 = 0.1e1 / t58
  t96 = t61 / t62
  t99 = f.my_piecewise5(t51, 0, t54, 0, -t90 * t92 * t93 * t96)
  t106 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t66 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.5e1 / 0.27e2 * t80 + t86 * t64 + t46 * t99))
  vrho_0_ = 0.2e1 * r0 * t106 + 0.2e1 * t70
  t109 = t31 * t35
  t110 = t29 * t109
  t116 = f.my_piecewise3(t54, 0, -0.5e1 / 0.81e2 * t110)
  t117 = f.my_piecewise3(t56, t116, 0)
  t121 = f.my_piecewise5(t51, 0, t54, 0, -t90 * t117 * t93 * t96)
  t127 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.72e2 * t110 - 0.5e1 / 0.81e2 * t29 * t109 * t64 + t46 * t121))
  vsigma_0_ = 0.2e1 * r0 * t127
  t129 = t31 * t41
  t135 = f.my_piecewise3(t54, 0, 0.5e1 / 0.54e2 * t29 * t129)
  t136 = f.my_piecewise3(t56, t135, 0)
  t140 = f.my_piecewise5(t51, 0, t54, 0, -t90 * t136 * t93 * t96)
  t146 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.54e2 * t29 * t129 * t64 + t46 * t140))
  vlapl_0_ = 0.2e1 * r0 * t146
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
  t29 = t24 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t21 ** 2
  t36 = 0.1e1 / t34 / t33
  t38 = t29 * t32 * t36
  t40 = l0 * t31
  t47 = 0.5e1 / 0.54e2 * t29 * t40 / t34 / r0 - 0.5e1 / 0.81e2 * t38
  t49 = jnp.log(0.1e1 - DBL_EPSILON)
  t50 = 0.1e1 / params.csk_a
  t51 = (-t49) ** (-t50)
  t52 = t47 < -t51
  t53 = jnp.log(DBL_EPSILON)
  t54 = (-t53) ** (-t50)
  t55 = -t54 < t47
  t56 = f.my_piecewise3(t55, -t54, t47)
  t57 = -t51 < t56
  t58 = f.my_piecewise3(t57, t56, -t51)
  t59 = abs(t58)
  t60 = t59 ** params.csk_a
  t61 = 0.1e1 / t60
  t62 = jnp.exp(-t61)
  t63 = 0.1e1 - t62
  t64 = t63 ** t50
  t65 = f.my_piecewise5(t52, 0, t55, 1, t64)
  t67 = 0.1e1 + 0.5e1 / 0.72e2 * t38 + t47 * t65
  t71 = t20 * t34
  t74 = 0.1e1 / t34 / t33 / r0
  t76 = t29 * t32 * t74
  t82 = -0.25e2 / 0.162e3 * t29 * t40 * t36 + 0.40e2 / 0.243e3 * t76
  t84 = t64 * t61
  t85 = jnp.abs(1 - t58)
  t86 = t84 * t85
  t87 = f.my_piecewise3(t55, 0, t82)
  t88 = f.my_piecewise3(t57, t87, 0)
  t89 = 0.1e1 / t59
  t91 = 0.1e1 / t63
  t92 = t62 * t91
  t93 = t88 * t89 * t92
  t95 = f.my_piecewise5(t52, 0, t55, 0, -t86 * t93)
  t97 = -0.5e1 / 0.27e2 * t76 + t82 * t65 + t47 * t95
  t102 = f.my_piecewise3(t2, 0, t7 * t23 * t67 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t71 * t97)
  t113 = t33 ** 2
  t117 = t29 * t32 / t34 / t113
  t123 = 0.100e3 / 0.243e3 * t29 * t40 * t74 - 0.440e3 / 0.729e3 * t117
  t127 = t60 ** 2
  t129 = t64 / t127
  t130 = t85 ** 2
  t132 = t88 ** 2
  t133 = t59 ** 2
  t134 = 0.1e1 / t133
  t135 = t132 * t134
  t136 = t62 ** 2
  t137 = t63 ** 2
  t138 = 0.1e1 / t137
  t142 = t130 * t132
  t146 = t134 * t62 * t91 * params.csk_a
  t148 = signum(1, t58)
  t151 = f.my_piecewise3(t55, 0, t123)
  t152 = f.my_piecewise3(t57, t151, 0)
  t159 = t129 * t142
  t166 = f.my_piecewise5(t52, 0, t55, 0, t129 * t130 * t135 * t136 * t138 - t159 * t134 * t136 * t138 * params.csk_a + t84 * t130 * t135 * t92 - t86 * t152 * t89 * t92 + t84 * t142 * t146 - t84 * t148 * t93 - t159 * t146)
  t173 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t67 / 0.30e2 + t7 * t23 * t97 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t71 * (0.55e2 / 0.81e2 * t117 + t123 * t65 + 0.2e1 * t82 * t95 + t47 * t166))
  v2rho2_0_ = 0.2e1 * r0 * t173 + 0.4e1 * t102
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
  t30 = t25 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t37 = 0.1e1 / t35 / t34
  t39 = t30 * t33 * t37
  t41 = l0 * t32
  t48 = 0.5e1 / 0.54e2 * t30 * t41 / t35 / r0 - 0.5e1 / 0.81e2 * t39
  t50 = jnp.log(0.1e1 - DBL_EPSILON)
  t51 = 0.1e1 / params.csk_a
  t52 = (-t50) ** (-t51)
  t53 = t48 < -t52
  t54 = jnp.log(DBL_EPSILON)
  t55 = (-t54) ** (-t51)
  t56 = -t55 < t48
  t57 = f.my_piecewise3(t56, -t55, t48)
  t58 = -t52 < t57
  t59 = f.my_piecewise3(t58, t57, -t52)
  t60 = abs(t59)
  t61 = t60 ** params.csk_a
  t62 = 0.1e1 / t61
  t63 = jnp.exp(-t62)
  t64 = 0.1e1 - t63
  t65 = t64 ** t51
  t66 = f.my_piecewise5(t53, 0, t56, 1, t65)
  t68 = 0.1e1 + 0.5e1 / 0.72e2 * t39 + t48 * t66
  t73 = t20 / t21
  t76 = 0.1e1 / t35 / t34 / r0
  t78 = t30 * t33 * t76
  t84 = -0.25e2 / 0.162e3 * t30 * t41 * t37 + 0.40e2 / 0.243e3 * t78
  t86 = t65 * t62
  t87 = abs(1, t59)
  t88 = t86 * t87
  t89 = f.my_piecewise3(t56, 0, t84)
  t90 = f.my_piecewise3(t58, t89, 0)
  t91 = 0.1e1 / t60
  t93 = 0.1e1 / t64
  t94 = t63 * t93
  t95 = t90 * t91 * t94
  t97 = f.my_piecewise5(t53, 0, t56, 0, -t88 * t95)
  t99 = -0.5e1 / 0.27e2 * t78 + t84 * t66 + t48 * t97
  t103 = t20 * t35
  t104 = t34 ** 2
  t106 = 0.1e1 / t35 / t104
  t108 = t30 * t33 * t106
  t114 = 0.100e3 / 0.243e3 * t30 * t41 * t76 - 0.440e3 / 0.729e3 * t108
  t118 = t61 ** 2
  t120 = t65 / t118
  t121 = t87 ** 2
  t123 = t90 ** 2
  t124 = t60 ** 2
  t125 = 0.1e1 / t124
  t126 = t123 * t125
  t127 = t63 ** 2
  t128 = t64 ** 2
  t129 = 0.1e1 / t128
  t130 = t127 * t129
  t133 = t121 * t123
  t135 = t125 * t63
  t136 = t93 * params.csk_a
  t137 = t135 * t136
  t139 = signum(1, t59)
  t140 = t86 * t139
  t141 = t140 * t95
  t142 = f.my_piecewise3(t56, 0, t114)
  t143 = f.my_piecewise3(t58, t142, 0)
  t145 = t143 * t91 * t94
  t150 = t120 * t133
  t152 = t125 * t127
  t153 = t129 * params.csk_a
  t157 = f.my_piecewise5(t53, 0, t56, 0, t120 * t121 * t126 * t130 + t86 * t121 * t126 * t94 + t86 * t133 * t137 - t150 * t152 * t153 - t150 * t137 - t88 * t145 - t141)
  t159 = 0.55e2 / 0.81e2 * t108 + t114 * t66 + 0.2e1 * t84 * t97 + t48 * t157
  t164 = f.my_piecewise3(t2, 0, -t7 * t24 * t68 / 0.30e2 + t7 * t73 * t99 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t103 * t159)
  t182 = t30 * t33 / t35 / t104 / r0
  t188 = -0.1100e4 / 0.729e3 * t30 * t41 * t106 + 0.6160e4 / 0.2187e4 * t182
  t194 = t139 * t123
  t195 = t120 * t194
  t196 = t125 * params.csk_a
  t202 = t121 * t143
  t203 = t120 * t202
  t209 = t87 * t123
  t215 = t121 * t90
  t229 = t121 * t87
  t231 = t123 * t90
  t233 = 0.1e1 / t124 / t60
  t234 = t231 * t233
  t244 = t65 / t118 / t61
  t246 = t127 * t63
  t248 = 0.1e1 / t128 / t64
  t254 = f.my_piecewise3(t56, 0, t188)
  t255 = f.my_piecewise3(t58, t254, 0)
  t259 = t229 * t231
  t260 = t244 * t259
  t261 = params.csk_a ** 2
  t263 = t233 * t261 * t130
  t266 = -0.3e1 * t195 * t196 * t87 * t63 * t93 - 0.3e1 * t203 * t196 * t90 * t63 * t93 + 0.3e1 * t86 * t209 * t135 * t136 * t139 + 0.3e1 * t86 * t215 * t135 * t136 * t143 - 0.3e1 * t195 * t152 * t153 * t87 - 0.3e1 * t203 * t152 * t153 * t90 - t141 - 0.3e1 * t120 * t229 * t234 * t130 - 0.2e1 * t86 * t229 * t234 * t94 - t244 * t229 * t234 * t246 * t248 - 0.2e1 * t140 * t145 - t88 * t255 * t91 * t94 - 0.3e1 * t260 * t263
  t267 = t233 * t246
  t286 = t120 * t259
  t290 = t233 * params.csk_a * t94
  t293 = t86 * t259
  t312 = t233 * t63 * t93 * t261
  t317 = 0.3e1 * t120 * t209 * t152 * t129 * t139 + 0.3e1 * t120 * t215 * t152 * t129 * t143 + 0.3e1 * t86 * t194 * t135 * t93 * t87 + 0.3e1 * t86 * t202 * t135 * t93 * t90 + 0.3e1 * t260 * t233 * t127 * t153 - 0.2e1 * t260 * t267 * t248 * t261 + 0.3e1 * t260 * t267 * t248 * params.csk_a - t260 * t312 + 0.3e1 * t286 * t263 + 0.3e1 * t286 * t290 + 0.3e1 * t286 * t312 - 0.3e1 * t293 * t290 - t293 * t312
  t319 = f.my_piecewise5(t53, 0, t56, 0, t266 + t317)
  t326 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t68 - t7 * t24 * t99 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t73 * t159 + 0.3e1 / 0.20e2 * t7 * t103 * (-0.770e3 / 0.243e3 * t182 + t188 * t66 + 0.3e1 * t114 * t97 + 0.3e1 * t84 * t157 + t48 * t319))
  v3rho3_0_ = 0.2e1 * r0 * t326 + 0.6e1 * t164

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
  t31 = t26 / t29
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = t22 ** 2
  t37 = 0.1e1 / t35 / t21
  t39 = t31 * t34 * t37
  t41 = l0 * t33
  t48 = 0.5e1 / 0.54e2 * t31 * t41 / t35 / r0 - 0.5e1 / 0.81e2 * t39
  t50 = jnp.log(0.1e1 - DBL_EPSILON)
  t51 = 0.1e1 / params.csk_a
  t52 = (-t50) ** (-t51)
  t53 = t48 < -t52
  t54 = jnp.log(DBL_EPSILON)
  t55 = (-t54) ** (-t51)
  t56 = -t55 < t48
  t57 = f.my_piecewise3(t56, -t55, t48)
  t58 = -t52 < t57
  t59 = f.my_piecewise3(t58, t57, -t52)
  t60 = abs(t59)
  t61 = t60 ** params.csk_a
  t62 = 0.1e1 / t61
  t63 = jnp.exp(-t62)
  t64 = 0.1e1 - t63
  t65 = t64 ** t51
  t66 = f.my_piecewise5(t53, 0, t56, 1, t65)
  t68 = 0.1e1 + 0.5e1 / 0.72e2 * t39 + t48 * t66
  t74 = t20 / t22 / r0
  t75 = t21 * r0
  t77 = 0.1e1 / t35 / t75
  t79 = t31 * t34 * t77
  t85 = -0.25e2 / 0.162e3 * t31 * t41 * t37 + 0.40e2 / 0.243e3 * t79
  t87 = t65 * t62
  t88 = abs(1, t59)
  t89 = t87 * t88
  t90 = f.my_piecewise3(t56, 0, t85)
  t91 = f.my_piecewise3(t58, t90, 0)
  t92 = 0.1e1 / t60
  t94 = 0.1e1 / t64
  t95 = t63 * t94
  t96 = t91 * t92 * t95
  t98 = f.my_piecewise5(t53, 0, t56, 0, -t89 * t96)
  t100 = -0.5e1 / 0.27e2 * t79 + t85 * t66 + t48 * t98
  t105 = t20 / t22
  t106 = t21 ** 2
  t108 = 0.1e1 / t35 / t106
  t110 = t31 * t34 * t108
  t116 = 0.100e3 / 0.243e3 * t31 * t41 * t77 - 0.440e3 / 0.729e3 * t110
  t120 = t61 ** 2
  t122 = t65 / t120
  t123 = t88 ** 2
  t124 = t122 * t123
  t125 = t91 ** 2
  t126 = t60 ** 2
  t127 = 0.1e1 / t126
  t128 = t125 * t127
  t129 = t63 ** 2
  t130 = t64 ** 2
  t131 = 0.1e1 / t130
  t132 = t129 * t131
  t133 = t128 * t132
  t135 = t123 * t125
  t137 = t127 * t63
  t138 = t94 * params.csk_a
  t139 = t137 * t138
  t141 = signum(1, t59)
  t142 = t87 * t141
  t143 = t142 * t96
  t144 = f.my_piecewise3(t56, 0, t116)
  t145 = f.my_piecewise3(t58, t144, 0)
  t147 = t145 * t92 * t95
  t149 = t87 * t123
  t150 = t128 * t95
  t152 = t122 * t135
  t154 = t127 * t129
  t155 = t131 * params.csk_a
  t156 = t154 * t155
  t159 = f.my_piecewise5(t53, 0, t56, 0, t87 * t135 * t139 + t124 * t133 - t152 * t139 - t89 * t147 + t149 * t150 - t152 * t156 - t143)
  t161 = 0.55e2 / 0.81e2 * t110 + t116 * t66 + 0.2e1 * t85 * t98 + t48 * t159
  t165 = t20 * t35
  t168 = 0.1e1 / t35 / t106 / r0
  t170 = t31 * t34 * t168
  t176 = -0.1100e4 / 0.729e3 * t31 * t41 * t108 + 0.6160e4 / 0.2187e4 * t170
  t184 = t65 / t120 / t61
  t185 = t123 * t88
  t186 = t125 * t91
  t187 = t185 * t186
  t188 = t184 * t187
  t190 = 0.1e1 / t126 / t60
  t191 = params.csk_a ** 2
  t192 = t190 * t191
  t193 = t192 * t132
  t196 = t129 * t63
  t197 = t190 * t196
  t199 = 0.1e1 / t130 / t64
  t200 = t199 * t191
  t204 = t88 * t125
  t206 = t131 * t141
  t208 = t122 * t204 * t154 * t206
  t210 = t123 * t91
  t211 = t122 * t210
  t212 = t131 * t145
  t216 = t199 * params.csk_a
  t220 = t122 * t187
  t223 = t190 * params.csk_a
  t224 = t223 * t95
  t227 = t87 * t187
  t230 = t141 * t125
  t232 = t94 * t88
  t234 = t87 * t230 * t137 * t232
  t236 = t123 * t145
  t239 = t137 * t94 * t91
  t242 = t190 * t129
  t246 = t190 * t63
  t247 = t94 * t191
  t248 = t246 * t247
  t252 = 0.3e1 * t211 * t154 * t212 + 0.3e1 * t188 * t242 * t155 - 0.2e1 * t188 * t197 * t200 + 0.3e1 * t188 * t197 * t216 + 0.3e1 * t87 * t236 * t239 - 0.3e1 * t188 * t193 + 0.3e1 * t220 * t193 + 0.3e1 * t220 * t224 + 0.3e1 * t220 * t248 - 0.3e1 * t227 * t224 - t227 * t248 + 0.3e1 * t208 + 0.3e1 * t234
  t255 = t186 * t190
  t264 = t196 * t199
  t267 = t142 * t147
  t269 = f.my_piecewise3(t56, 0, t176)
  t270 = f.my_piecewise3(t58, t269, 0)
  t272 = t270 * t92 * t95
  t274 = t122 * t236
  t275 = t127 * params.csk_a
  t278 = t275 * t91 * t63 * t94
  t284 = t87 * t204 * t137 * t138 * t141
  t286 = t87 * t210
  t287 = t138 * t145
  t291 = t122 * t230
  t294 = t291 * t154 * t155 * t88
  t297 = t154 * t155 * t91
  t303 = t291 * t275 * t88 * t63 * t94
  t305 = -0.3e1 * t122 * t185 * t255 * t132 - t184 * t185 * t255 * t264 - 0.2e1 * t87 * t185 * t255 * t95 + 0.3e1 * t286 * t137 * t287 - t188 * t248 - t89 * t272 - 0.3e1 * t274 * t278 - 0.3e1 * t274 * t297 - t143 - 0.2e1 * t267 + 0.3e1 * t284 - 0.3e1 * t294 - 0.3e1 * t303
  t307 = f.my_piecewise5(t53, 0, t56, 0, t252 + t305)
  t309 = -0.770e3 / 0.243e3 * t170 + t176 * t66 + 0.3e1 * t116 * t98 + 0.3e1 * t85 * t159 + t48 * t307
  t314 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t68 - t7 * t74 * t100 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t105 * t161 + 0.3e1 / 0.20e2 * t7 * t165 * t309)
  t335 = t31 * t34 / t35 / t106 / t21
  t341 = 0.15400e5 / 0.2187e4 * t31 * t41 * t168 - 0.104720e6 / 0.6561e4 * t335
  t349 = t185 * t125
  t350 = t87 * t349
  t351 = t246 * t287
  t354 = t141 * t91
  t360 = t184 * t349
  t361 = t199 * t145
  t366 = t123 * t186
  t367 = t122 * t366
  t368 = t131 * t191
  t370 = t242 * t368 * t141
  t373 = t122 * t349
  t375 = t242 * t368 * t145
  t378 = t95 * t141
  t379 = t223 * t378
  t384 = t184 * t366
  t395 = t246 * t247 * t145
  t398 = t192 * t378
  t407 = t87 * t366
  t410 = t88 * t91
  t419 = t122 * t354 * t127
  t420 = params.csk_a * t88
  t429 = t123 ** 2
  t430 = t125 ** 2
  t431 = t429 * t430
  t432 = t122 * t431
  t433 = t126 ** 2
  t434 = 0.1e1 / t433
  t435 = t434 * t129
  t436 = t191 * params.csk_a
  t438 = t435 * t131 * t436
  t442 = t434 * t191 * t95
  t445 = 0.14e2 * t87 * t410 * t127 * t95 * params.csk_a * t141 * t145 - 0.14e2 * t419 * t132 * t420 * t145 - 0.14e2 * t419 * t420 * t95 * t145 - 0.6e1 * t350 * t395 - 0.6e1 * t360 * t395 + 0.18e2 * t367 * t398 + 0.18e2 * t373 * t395 - 0.18e2 * t407 * t379 - 0.6e1 * t384 * t398 - 0.7e1 * t432 * t438 - 0.18e2 * t432 * t442
  t447 = t184 * t431
  t450 = t87 * t431
  t455 = t434 * t63 * t94 * t436
  t461 = t120 ** 2
  t463 = t65 / t461
  t464 = t463 * t431
  t469 = t434 * t196
  t470 = t469 * t216
  t473 = t435 * t368
  t477 = t434 * params.csk_a * t95
  t495 = t435 * t155
  t498 = t145 ** 2
  t499 = t123 * t498
  t500 = t122 * t499
  t503 = t141 ** 2
  t504 = t503 * t125
  t505 = t122 * t504
  t519 = t469 * t199 * t436
  t522 = -0.12e2 * t87 * t141 * t186 * t246 * t94 * t123 - 0.12e2 * t87 * t185 * t145 * t246 * t94 * t125 + 0.3e1 * t87 * t499 * t139 + 0.3e1 * t87 * t504 * t139 - 0.3e1 * t500 * t139 - 0.3e1 * t505 * t139 - 0.3e1 * t500 * t156 + 0.18e2 * t447 * t438 - 0.18e2 * t447 * t495 + 0.12e2 * t447 * t519 + 0.11e2 * t450 * t477
  t525 = t469 * t200
  t537 = t123 * t270
  t547 = t129 ** 2
  t548 = t434 * t547
  t549 = t130 ** 2
  t550 = 0.1e1 / t549
  t560 = t199 * t141
  t582 = 0.4e1 * t211 * t154 * t131 * t270 - 0.6e1 * t464 * t548 * t550 * t436 - 0.6e1 * t464 * t548 * t550 * params.csk_a - 0.6e1 * t360 * t197 * t361 - 0.6e1 * t384 * t197 * t560 - 0.3e1 * t142 * t272 - 0.3e1 * t505 * t156 - t143 + 0.4e1 * t208 + 0.4e1 * t234 - 0.3e1 * t267
  t584 = f.my_piecewise3(t56, 0, t341)
  t585 = f.my_piecewise3(t58, t584, 0)
  t592 = t498 * t127
  t603 = t430 * t434
  t641 = t122 * t537
  t655 = 0.14e2 * t122 * t410 * t154 * t206 * t145 + 0.4e1 * t286 * t137 * t138 * t270 + 0.18e2 * t384 * t197 * t560 * params.csk_a + 0.18e2 * t384 * t242 * t206 * params.csk_a + 0.18e2 * t360 * t242 * t212 * params.csk_a - 0.4e1 * t641 * t278 - 0.4e1 * t641 * t297 - 0.6e1 * t407 * t398 + 0.4e1 * t284 - 0.4e1 * t294 - 0.4e1 * t303
  t659 = f.my_piecewise5(t53, 0, t56, 0, -0.11e2 * t432 * t473 - 0.11e2 * t432 * t477 - 0.18e2 * t360 * t375 + 0.18e2 * t367 * t370 + 0.18e2 * t373 * t375 + 0.18e2 * t367 * t379 + 0.18e2 * t373 * t351 - 0.18e2 * t384 * t370 - 0.18e2 * t350 * t351 + 0.6e1 * t447 * t442 + 0.6e1 * t450 * t442 + t450 * t455 - 0.7e1 * t432 * t455 + 0.6e1 * t447 * t455 - t464 * t455 - 0.12e2 * t447 * t470 - 0.6e1 * t447 * t525 - 0.7e1 * t464 * t438 + 0.7e1 * t464 * t473 + 0.7e1 * t432 * t495 - 0.6e1 * t464 * t470 + 0.18e2 * t464 * t525 - 0.12e2 * t464 * t519 + t445 + t582 + t522 - t89 * t585 * t92 * t95 + 0.11e2 * t122 * t429 * t603 * t132 + 0.6e1 * t87 * t429 * t603 * t95 + 0.6e1 * t184 * t429 * t603 * t264 - 0.12e2 * t360 * t197 * t200 * t145 - 0.12e2 * t384 * t197 * t200 * t141 + 0.11e2 * t464 * t548 * t550 * t191 + 0.18e2 * t360 * t197 * t361 * params.csk_a + 0.14e2 * t87 * t354 * t137 * t232 * t145 + t463 * t429 * t603 * t547 * t550 + 0.3e1 * t87 * t503 * t150 + 0.3e1 * t149 * t592 * t95 + 0.3e1 * t122 * t503 * t133 + 0.3e1 * t124 * t592 * t132 - 0.18e2 * t373 * t242 * t212 - 0.18e2 * t367 * t242 * t206 + 0.4e1 * t87 * t537 * t239 + t655)
  t666 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t75 * t68 + 0.8e1 / 0.45e2 * t7 * t25 * t100 - t7 * t74 * t161 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t105 * t309 + 0.3e1 / 0.20e2 * t7 * t165 * (0.13090e5 / 0.729e3 * t335 + t341 * t66 + 0.4e1 * t176 * t98 + 0.6e1 * t116 * t159 + 0.4e1 * t85 * t307 + t48 * t659))
  v4rho4_0_ = 0.2e1 * r0 * t666 + 0.8e1 * t314

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
  t40 = t35 / t38
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t47 = t40 * s0 * t45
  t55 = 0.5e1 / 0.54e2 * t40 * l0 / t43 / r0 - 0.5e1 / 0.81e2 * t47
  t57 = jnp.log(0.1e1 - DBL_EPSILON)
  t58 = 0.1e1 / params.csk_a
  t59 = (-t57) ** (-t58)
  t60 = t55 < -t59
  t61 = jnp.log(DBL_EPSILON)
  t62 = (-t61) ** (-t58)
  t63 = -t62 < t55
  t64 = f.my_piecewise3(t63, -t62, t55)
  t65 = -t59 < t64
  t66 = f.my_piecewise3(t65, t64, -t59)
  t67 = abs(t66)
  t68 = t67 ** params.csk_a
  t69 = 0.1e1 / t68
  t70 = jnp.exp(-t69)
  t71 = 0.1e1 - t70
  t72 = t71 ** t58
  t73 = f.my_piecewise5(t60, 0, t63, 1, t72)
  t75 = 0.1e1 + 0.5e1 / 0.72e2 * t47 + t55 * t73
  t79 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t81 = t80 * f.p.zeta_threshold
  t83 = f.my_piecewise3(t21, t81, t23 * t20)
  t84 = 0.1e1 / t32
  t85 = t83 * t84
  t88 = t6 * t85 * t75 / 0.10e2
  t89 = t83 * t33
  t92 = 0.1e1 / t43 / t41 / r0
  t94 = t40 * s0 * t92
  t100 = -0.25e2 / 0.162e3 * t40 * l0 * t45 + 0.40e2 / 0.243e3 * t94
  t102 = t72 * t69
  t103 = jnp.abs(1 - t66)
  t104 = t102 * t103
  t105 = f.my_piecewise3(t63, 0, t100)
  t106 = f.my_piecewise3(t65, t105, 0)
  t107 = 0.1e1 / t67
  t109 = 0.1e1 / t71
  t110 = t70 * t109
  t111 = t106 * t107 * t110
  t113 = f.my_piecewise5(t60, 0, t63, 0, -t104 * t111)
  t115 = -0.5e1 / 0.27e2 * t94 + t100 * t73 + t55 * t113
  t120 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t75 + t88 + 0.3e1 / 0.20e2 * t6 * t89 * t115)
  t122 = r1 <= f.p.dens_threshold
  t123 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t124 = 0.1e1 + t123
  t125 = t124 <= f.p.zeta_threshold
  t126 = t124 ** (0.1e1 / 0.3e1)
  t127 = t126 ** 2
  t129 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t132 = f.my_piecewise3(t125, 0, 0.5e1 / 0.3e1 * t127 * t129)
  t133 = t132 * t33
  t134 = r1 ** 2
  t135 = r1 ** (0.1e1 / 0.3e1)
  t136 = t135 ** 2
  t138 = 0.1e1 / t136 / t134
  t140 = t40 * s2 * t138
  t148 = 0.5e1 / 0.54e2 * t40 * l1 / t136 / r1 - 0.5e1 / 0.81e2 * t140
  t149 = t148 < -t59
  t150 = -t62 < t148
  t151 = f.my_piecewise3(t150, -t62, t148)
  t152 = -t59 < t151
  t153 = f.my_piecewise3(t152, t151, -t59)
  t154 = abs(t153)
  t155 = t154 ** params.csk_a
  t156 = 0.1e1 / t155
  t157 = jnp.exp(-t156)
  t158 = 0.1e1 - t157
  t159 = t158 ** t58
  t160 = f.my_piecewise5(t149, 0, t150, 1, t159)
  t162 = 0.1e1 + 0.5e1 / 0.72e2 * t140 + t148 * t160
  t167 = f.my_piecewise3(t125, t81, t127 * t124)
  t168 = t167 * t84
  t171 = t6 * t168 * t162 / 0.10e2
  t173 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t133 * t162 + t171)
  t175 = 0.1e1 / t22
  t176 = t28 ** 2
  t181 = t17 / t24 / t7
  t183 = -0.2e1 * t25 + 0.2e1 * t181
  t184 = f.my_piecewise5(t11, 0, t15, 0, t183)
  t188 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t175 * t176 + 0.5e1 / 0.3e1 * t23 * t184)
  t195 = t6 * t31 * t84 * t75
  t201 = 0.1e1 / t32 / t7
  t205 = t6 * t83 * t201 * t75 / 0.30e2
  t207 = t6 * t85 * t115
  t209 = t41 ** 2
  t213 = t40 * s0 / t43 / t209
  t219 = 0.100e3 / 0.243e3 * t40 * l0 * t92 - 0.440e3 / 0.729e3 * t213
  t223 = t68 ** 2
  t225 = t72 / t223
  t226 = t103 ** 2
  t228 = t106 ** 2
  t229 = t67 ** 2
  t230 = 0.1e1 / t229
  t231 = t228 * t230
  t232 = t70 ** 2
  t233 = t71 ** 2
  t234 = 0.1e1 / t233
  t238 = t226 * t228
  t242 = t230 * t70 * t109 * params.csk_a
  t244 = signum(1, t66)
  t247 = f.my_piecewise3(t63, 0, t219)
  t248 = f.my_piecewise3(t65, t247, 0)
  t255 = t225 * t238
  t262 = f.my_piecewise5(t60, 0, t63, 0, t225 * t226 * t231 * t232 * t234 - t255 * t230 * t232 * t234 * params.csk_a + t102 * t226 * t231 * t110 - t104 * t248 * t107 * t110 - t102 * t244 * t111 + t102 * t238 * t242 - t255 * t242)
  t269 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t188 * t33 * t75 + t195 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t115 - t205 + t207 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t89 * (0.55e2 / 0.81e2 * t213 + t219 * t73 + 0.2e1 * t100 * t113 + t55 * t262))
  t270 = 0.1e1 / t126
  t271 = t129 ** 2
  t275 = f.my_piecewise5(t15, 0, t11, 0, -t183)
  t279 = f.my_piecewise3(t125, 0, 0.10e2 / 0.9e1 * t270 * t271 + 0.5e1 / 0.3e1 * t127 * t275)
  t286 = t6 * t132 * t84 * t162
  t291 = t6 * t167 * t201 * t162 / 0.30e2
  t293 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t279 * t33 * t162 + t286 / 0.5e1 - t291)
  d11 = 0.2e1 * t120 + 0.2e1 * t173 + t7 * (t269 + t293)
  t296 = -t8 - t26
  t297 = f.my_piecewise5(t11, 0, t15, 0, t296)
  t300 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t297)
  t301 = t300 * t33
  t306 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t301 * t75 + t88)
  t308 = f.my_piecewise5(t15, 0, t11, 0, -t296)
  t311 = f.my_piecewise3(t125, 0, 0.5e1 / 0.3e1 * t127 * t308)
  t312 = t311 * t33
  t316 = t167 * t33
  t319 = 0.1e1 / t136 / t134 / r1
  t321 = t40 * s2 * t319
  t327 = -0.25e2 / 0.162e3 * t40 * l1 * t138 + 0.40e2 / 0.243e3 * t321
  t329 = t159 * t156
  t330 = jnp.abs(1 - t153)
  t331 = t329 * t330
  t332 = f.my_piecewise3(t150, 0, t327)
  t333 = f.my_piecewise3(t152, t332, 0)
  t334 = 0.1e1 / t154
  t336 = 0.1e1 / t158
  t337 = t157 * t336
  t338 = t333 * t334 * t337
  t340 = f.my_piecewise5(t149, 0, t150, 0, -t331 * t338)
  t342 = -0.5e1 / 0.27e2 * t321 + t327 * t160 + t148 * t340
  t347 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t312 * t162 + t171 + 0.3e1 / 0.20e2 * t6 * t316 * t342)
  t351 = 0.2e1 * t181
  t352 = f.my_piecewise5(t11, 0, t15, 0, t351)
  t356 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t175 * t297 * t28 + 0.5e1 / 0.3e1 * t23 * t352)
  t363 = t6 * t300 * t84 * t75
  t371 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t356 * t33 * t75 + t363 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t301 * t115 + t195 / 0.10e2 - t205 + t207 / 0.10e2)
  t375 = f.my_piecewise5(t15, 0, t11, 0, -t351)
  t379 = f.my_piecewise3(t125, 0, 0.10e2 / 0.9e1 * t270 * t308 * t129 + 0.5e1 / 0.3e1 * t127 * t375)
  t386 = t6 * t311 * t84 * t162
  t393 = t6 * t168 * t342
  t396 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t379 * t33 * t162 + t386 / 0.10e2 + t286 / 0.10e2 - t291 + 0.3e1 / 0.20e2 * t6 * t133 * t342 + t393 / 0.10e2)
  d12 = t120 + t173 + t306 + t347 + t7 * (t371 + t396)
  t401 = t297 ** 2
  t405 = 0.2e1 * t25 + 0.2e1 * t181
  t406 = f.my_piecewise5(t11, 0, t15, 0, t405)
  t410 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t175 * t401 + 0.5e1 / 0.3e1 * t23 * t406)
  t417 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t410 * t33 * t75 + t363 / 0.5e1 - t205)
  t418 = t308 ** 2
  t422 = f.my_piecewise5(t15, 0, t11, 0, -t405)
  t426 = f.my_piecewise3(t125, 0, 0.10e2 / 0.9e1 * t270 * t418 + 0.5e1 / 0.3e1 * t127 * t422)
  t436 = t134 ** 2
  t440 = t40 * s2 / t136 / t436
  t446 = 0.100e3 / 0.243e3 * t40 * l1 * t319 - 0.440e3 / 0.729e3 * t440
  t450 = t155 ** 2
  t452 = t159 / t450
  t453 = t330 ** 2
  t455 = t333 ** 2
  t456 = t154 ** 2
  t457 = 0.1e1 / t456
  t458 = t455 * t457
  t459 = t157 ** 2
  t460 = t158 ** 2
  t461 = 0.1e1 / t460
  t465 = t453 * t455
  t469 = t457 * t157 * t336 * params.csk_a
  t471 = signum(1, t153)
  t474 = f.my_piecewise3(t150, 0, t446)
  t475 = f.my_piecewise3(t152, t474, 0)
  t482 = t452 * t465
  t489 = f.my_piecewise5(t149, 0, t150, 0, t452 * t453 * t458 * t459 * t461 - t482 * t457 * t459 * t461 * params.csk_a + t329 * t453 * t458 * t337 - t331 * t475 * t334 * t337 - t329 * t471 * t338 + t329 * t465 * t469 - t482 * t469)
  t496 = f.my_piecewise3(t122, 0, 0.3e1 / 0.20e2 * t6 * t426 * t33 * t162 + t386 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t312 * t342 - t291 + t393 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t316 * (0.55e2 / 0.81e2 * t440 + t446 * t160 + 0.2e1 * t327 * t340 + t148 * t489))
  d22 = 0.2e1 * t306 + 0.2e1 * t347 + t7 * (t417 + t496)
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
  t51 = t46 / t49
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t58 = t51 * s0 * t56
  t66 = 0.5e1 / 0.54e2 * t51 * l0 / t54 / r0 - 0.5e1 / 0.81e2 * t58
  t68 = jnp.log(0.1e1 - DBL_EPSILON)
  t69 = 0.1e1 / params.csk_a
  t70 = (-t68) ** (-t69)
  t71 = t66 < -t70
  t72 = jnp.log(DBL_EPSILON)
  t73 = (-t72) ** (-t69)
  t74 = -t73 < t66
  t75 = f.my_piecewise3(t74, -t73, t66)
  t76 = -t70 < t75
  t77 = f.my_piecewise3(t76, t75, -t70)
  t78 = abs(t77)
  t79 = t78 ** params.csk_a
  t80 = 0.1e1 / t79
  t81 = jnp.exp(-t80)
  t82 = 0.1e1 - t81
  t83 = t82 ** t69
  t84 = f.my_piecewise5(t71, 0, t74, 1, t83)
  t86 = 0.1e1 + 0.5e1 / 0.72e2 * t58 + t66 * t84
  t92 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t93 = 0.1e1 / t43
  t94 = t92 * t93
  t98 = t92 * t44
  t101 = 0.1e1 / t54 / t52 / r0
  t103 = t51 * s0 * t101
  t109 = -0.25e2 / 0.162e3 * t51 * l0 * t56 + 0.40e2 / 0.243e3 * t103
  t111 = t83 * t80
  t112 = abs(1, t77)
  t113 = t111 * t112
  t114 = f.my_piecewise3(t74, 0, t109)
  t115 = f.my_piecewise3(t76, t114, 0)
  t116 = 0.1e1 / t78
  t118 = 0.1e1 / t82
  t119 = t81 * t118
  t120 = t115 * t116 * t119
  t122 = f.my_piecewise5(t71, 0, t74, 0, -t113 * t120)
  t124 = -0.5e1 / 0.27e2 * t103 + t109 * t84 + t66 * t122
  t128 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t129 = t128 ** 2
  t130 = t129 * f.p.zeta_threshold
  t132 = f.my_piecewise3(t21, t130, t32 * t20)
  t134 = 0.1e1 / t43 / t7
  t135 = t132 * t134
  t139 = t132 * t93
  t143 = t132 * t44
  t144 = t52 ** 2
  t146 = 0.1e1 / t54 / t144
  t148 = t51 * s0 * t146
  t154 = 0.100e3 / 0.243e3 * t51 * l0 * t101 - 0.440e3 / 0.729e3 * t148
  t158 = t79 ** 2
  t160 = t83 / t158
  t161 = t112 ** 2
  t163 = t115 ** 2
  t164 = t78 ** 2
  t165 = 0.1e1 / t164
  t166 = t163 * t165
  t167 = t81 ** 2
  t168 = t82 ** 2
  t169 = 0.1e1 / t168
  t170 = t167 * t169
  t173 = t161 * t163
  t175 = t165 * t81
  t176 = t118 * params.csk_a
  t177 = t175 * t176
  t179 = signum(1, t77)
  t180 = t111 * t179
  t181 = t180 * t120
  t182 = f.my_piecewise3(t74, 0, t154)
  t183 = f.my_piecewise3(t76, t182, 0)
  t185 = t183 * t116 * t119
  t190 = t160 * t173
  t192 = t165 * t167
  t193 = t169 * params.csk_a
  t197 = f.my_piecewise5(t71, 0, t74, 0, t111 * t161 * t166 * t119 + t160 * t161 * t166 * t170 + t111 * t173 * t177 - t190 * t192 * t193 - t113 * t185 - t190 * t177 - t181)
  t199 = 0.55e2 / 0.81e2 * t148 + t154 * t84 + 0.2e1 * t109 * t122 + t66 * t197
  t204 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t86 + t6 * t94 * t86 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t98 * t124 - t6 * t135 * t86 / 0.30e2 + t6 * t139 * t124 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t143 * t199)
  t206 = r1 <= f.p.dens_threshold
  t207 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t208 = 0.1e1 + t207
  t209 = t208 <= f.p.zeta_threshold
  t210 = t208 ** (0.1e1 / 0.3e1)
  t211 = 0.1e1 / t210
  t213 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t214 = t213 ** 2
  t217 = t210 ** 2
  t219 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t223 = f.my_piecewise3(t209, 0, 0.10e2 / 0.9e1 * t211 * t214 + 0.5e1 / 0.3e1 * t217 * t219)
  t225 = r1 ** 2
  t226 = r1 ** (0.1e1 / 0.3e1)
  t227 = t226 ** 2
  t231 = t51 * s2 / t227 / t225
  t239 = 0.5e1 / 0.54e2 * t51 * l1 / t227 / r1 - 0.5e1 / 0.81e2 * t231
  t241 = -t73 < t239
  t242 = f.my_piecewise3(t241, -t73, t239)
  t244 = f.my_piecewise3(-t70 < t242, t242, -t70)
  t245 = abs(t244)
  t246 = t245 ** params.csk_a
  t248 = jnp.exp(-0.1e1 / t246)
  t250 = (0.1e1 - t248) ** t69
  t251 = f.my_piecewise5(t239 < -t70, 0, t241, 1, t250)
  t253 = 0.1e1 + 0.5e1 / 0.72e2 * t231 + t239 * t251
  t259 = f.my_piecewise3(t209, 0, 0.5e1 / 0.3e1 * t217 * t213)
  t265 = f.my_piecewise3(t209, t130, t217 * t208)
  t271 = f.my_piecewise3(t206, 0, 0.3e1 / 0.20e2 * t6 * t223 * t44 * t253 + t6 * t259 * t93 * t253 / 0.5e1 - t6 * t265 * t134 * t253 / 0.30e2)
  t281 = t24 ** 2
  t285 = 0.6e1 * t34 - 0.6e1 * t17 / t281
  t286 = f.my_piecewise5(t11, 0, t15, 0, t285)
  t290 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t286)
  t313 = 0.1e1 / t43 / t24
  t328 = t51 * s0 / t54 / t144 / r0
  t334 = -0.1100e4 / 0.729e3 * t51 * l0 * t146 + 0.6160e4 / 0.2187e4 * t328
  t342 = t83 / t158 / t79
  t343 = t161 * t112
  t345 = t163 * t115
  t347 = 0.1e1 / t164 / t78
  t348 = t345 * t347
  t349 = t167 * t81
  t351 = 0.1e1 / t168 / t82
  t357 = f.my_piecewise3(t74, 0, t334)
  t358 = f.my_piecewise3(t76, t357, 0)
  t370 = t343 * t345
  t371 = t111 * t370
  t372 = t347 * t81
  t373 = t372 * t176
  t376 = t179 * t163
  t382 = t161 * t183
  t388 = t342 * t370
  t393 = params.csk_a ** 2
  t395 = t372 * t118 * t393
  t397 = t160 * t370
  t401 = 0.3e1 * t111 * t376 * t175 * t118 * t112 + 0.3e1 * t111 * t382 * t175 * t118 * t115 - t342 * t343 * t348 * t349 * t351 - 0.2e1 * t111 * t343 * t348 * t119 - t113 * t358 * t116 * t119 - 0.3e1 * t160 * t343 * t348 * t170 + 0.3e1 * t388 * t347 * t167 * t193 - 0.2e1 * t180 * t185 - 0.3e1 * t371 * t373 - t371 * t395 - t388 * t395 + 0.3e1 * t397 * t395 - t181
  t405 = t347 * t393 * t170
  t408 = t347 * t349
  t413 = t112 * t163
  t419 = t161 * t115
  t431 = t160 * t376
  t436 = t160 * t382
  t441 = t165 * params.csk_a
  t462 = 0.3e1 * t111 * t413 * t175 * t176 * t179 + 0.3e1 * t111 * t419 * t175 * t176 * t183 - 0.3e1 * t431 * t441 * t112 * t81 * t118 - 0.3e1 * t436 * t441 * t115 * t81 * t118 + 0.3e1 * t160 * t413 * t192 * t169 * t179 + 0.3e1 * t160 * t419 * t192 * t169 * t183 - 0.3e1 * t431 * t192 * t193 * t112 - 0.3e1 * t436 * t192 * t193 * t115 - 0.2e1 * t388 * t408 * t351 * t393 + 0.3e1 * t388 * t408 * t351 * params.csk_a + 0.3e1 * t397 * t373 - 0.3e1 * t388 * t405 + 0.3e1 * t397 * t405
  t464 = f.my_piecewise5(t71, 0, t74, 0, t401 + t462)
  t471 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t290 * t44 * t86 + 0.3e1 / 0.10e2 * t6 * t42 * t93 * t86 + 0.9e1 / 0.20e2 * t6 * t45 * t124 - t6 * t92 * t134 * t86 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t94 * t124 + 0.9e1 / 0.20e2 * t6 * t98 * t199 + 0.2e1 / 0.45e2 * t6 * t132 * t313 * t86 - t6 * t135 * t124 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t139 * t199 + 0.3e1 / 0.20e2 * t6 * t143 * (-0.770e3 / 0.243e3 * t328 + t334 * t84 + 0.3e1 * t154 * t122 + 0.3e1 * t109 * t197 + t66 * t464))
  t481 = f.my_piecewise5(t15, 0, t11, 0, -t285)
  t485 = f.my_piecewise3(t209, 0, -0.10e2 / 0.27e2 / t210 / t208 * t214 * t213 + 0.10e2 / 0.3e1 * t211 * t213 * t219 + 0.5e1 / 0.3e1 * t217 * t481)
  t503 = f.my_piecewise3(t206, 0, 0.3e1 / 0.20e2 * t6 * t485 * t44 * t253 + 0.3e1 / 0.10e2 * t6 * t223 * t93 * t253 - t6 * t259 * t134 * t253 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t265 * t313 * t253)
  d111 = 0.3e1 * t204 + 0.3e1 * t271 + t7 * (t471 + t503)

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
  t63 = t58 / t61
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t70 = t63 * s0 * t68
  t78 = 0.5e1 / 0.54e2 * t63 * l0 / t66 / r0 - 0.5e1 / 0.81e2 * t70
  t80 = jnp.log(0.1e1 - DBL_EPSILON)
  t81 = 0.1e1 / params.csk_a
  t82 = (-t80) ** (-t81)
  t83 = t78 < -t82
  t84 = jnp.log(DBL_EPSILON)
  t85 = (-t84) ** (-t81)
  t86 = -t85 < t78
  t87 = f.my_piecewise3(t86, -t85, t78)
  t88 = -t82 < t87
  t89 = f.my_piecewise3(t88, t87, -t82)
  t90 = abs(t89)
  t91 = t90 ** params.csk_a
  t92 = 0.1e1 / t91
  t93 = jnp.exp(-t92)
  t94 = 0.1e1 - t93
  t95 = t94 ** t81
  t96 = f.my_piecewise5(t83, 0, t86, 1, t95)
  t98 = 0.1e1 + 0.5e1 / 0.72e2 * t70 + t78 * t96
  t107 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t108 = 0.1e1 / t55
  t109 = t107 * t108
  t113 = t107 * t56
  t116 = 0.1e1 / t66 / t64 / r0
  t118 = t63 * s0 * t116
  t124 = -0.25e2 / 0.162e3 * t63 * l0 * t68 + 0.40e2 / 0.243e3 * t118
  t126 = t95 * t92
  t127 = abs(1, t89)
  t128 = t126 * t127
  t129 = f.my_piecewise3(t86, 0, t124)
  t130 = f.my_piecewise3(t88, t129, 0)
  t131 = 0.1e1 / t90
  t133 = 0.1e1 / t94
  t134 = t93 * t133
  t135 = t130 * t131 * t134
  t137 = f.my_piecewise5(t83, 0, t86, 0, -t128 * t135)
  t139 = -0.5e1 / 0.27e2 * t118 + t124 * t96 + t78 * t137
  t145 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t147 = 0.1e1 / t55 / t7
  t148 = t145 * t147
  t152 = t145 * t108
  t156 = t145 * t56
  t157 = t64 ** 2
  t159 = 0.1e1 / t66 / t157
  t161 = t63 * s0 * t159
  t167 = 0.100e3 / 0.243e3 * t63 * l0 * t116 - 0.440e3 / 0.729e3 * t161
  t171 = t91 ** 2
  t173 = t95 / t171
  t174 = t127 ** 2
  t175 = t173 * t174
  t176 = t130 ** 2
  t177 = t90 ** 2
  t178 = 0.1e1 / t177
  t179 = t176 * t178
  t180 = t93 ** 2
  t181 = t94 ** 2
  t182 = 0.1e1 / t181
  t183 = t180 * t182
  t184 = t179 * t183
  t186 = t174 * t176
  t188 = t178 * t93
  t189 = t133 * params.csk_a
  t190 = t188 * t189
  t192 = signum(1, t89)
  t193 = t126 * t192
  t194 = t193 * t135
  t195 = f.my_piecewise3(t86, 0, t167)
  t196 = f.my_piecewise3(t88, t195, 0)
  t198 = t196 * t131 * t134
  t200 = t126 * t174
  t201 = t179 * t134
  t203 = t173 * t186
  t205 = t178 * t180
  t206 = t182 * params.csk_a
  t207 = t205 * t206
  t210 = f.my_piecewise5(t83, 0, t86, 0, t126 * t186 * t190 - t128 * t198 + t175 * t184 - t203 * t190 + t200 * t201 - t203 * t207 - t194)
  t212 = 0.55e2 / 0.81e2 * t161 + t167 * t96 + 0.2e1 * t124 * t137 + t78 * t210
  t216 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t217 = t216 ** 2
  t218 = t217 * f.p.zeta_threshold
  t220 = f.my_piecewise3(t21, t218, t44 * t20)
  t222 = 0.1e1 / t55 / t25
  t223 = t220 * t222
  t227 = t220 * t147
  t231 = t220 * t108
  t235 = t220 * t56
  t238 = 0.1e1 / t66 / t157 / r0
  t240 = t63 * s0 * t238
  t246 = -0.1100e4 / 0.729e3 * t63 * l0 * t159 + 0.6160e4 / 0.2187e4 * t240
  t254 = t95 / t171 / t91
  t255 = t174 * t127
  t257 = t176 * t130
  t259 = 0.1e1 / t177 / t90
  t260 = t257 * t259
  t261 = t180 * t93
  t263 = 0.1e1 / t181 / t94
  t264 = t261 * t263
  t267 = t193 * t198
  t269 = f.my_piecewise3(t86, 0, t246)
  t270 = f.my_piecewise3(t88, t269, 0)
  t272 = t270 * t131 * t134
  t282 = t255 * t257
  t283 = t173 * t282
  t284 = t259 * params.csk_a
  t285 = t284 * t134
  t288 = t254 * t282
  t289 = params.csk_a ** 2
  t290 = t259 * t289
  t291 = t290 * t183
  t294 = t259 * t261
  t295 = t263 * t289
  t299 = t127 * t176
  t301 = t182 * t192
  t303 = t173 * t299 * t205 * t301
  t305 = t174 * t130
  t306 = t173 * t305
  t307 = t182 * t196
  t311 = t126 * t282
  t312 = t259 * t93
  t313 = t133 * t289
  t314 = t312 * t313
  t318 = -0.2e1 * t126 * t255 * t260 * t134 - 0.3e1 * t173 * t255 * t260 * t183 - t254 * t255 * t260 * t264 + 0.3e1 * t306 * t205 * t307 - 0.2e1 * t288 * t294 * t295 - t128 * t272 + 0.3e1 * t283 * t285 + 0.3e1 * t283 * t314 - 0.3e1 * t288 * t291 - t311 * t314 - t194 - 0.2e1 * t267 + 0.3e1 * t303
  t320 = t263 * params.csk_a
  t328 = t192 * t176
  t330 = t133 * t127
  t332 = t126 * t328 * t188 * t330
  t334 = t174 * t196
  t337 = t188 * t133 * t130
  t340 = t259 * t180
  t344 = t173 * t334
  t345 = t178 * params.csk_a
  t347 = t130 * t93 * t133
  t348 = t345 * t347
  t352 = t189 * t192
  t354 = t126 * t299 * t188 * t352
  t361 = t173 * t328
  t364 = t361 * t205 * t206 * t127
  t367 = t205 * t206 * t130
  t373 = t361 * t345 * t127 * t93 * t133
  t375 = 0.3e1 * t126 * t305 * t188 * t189 * t196 + 0.3e1 * t126 * t334 * t337 + 0.3e1 * t288 * t340 * t206 + 0.3e1 * t288 * t294 * t320 + 0.3e1 * t283 * t291 - 0.3e1 * t311 * t285 - t288 * t314 - 0.3e1 * t344 * t348 - 0.3e1 * t344 * t367 + 0.3e1 * t332 + 0.3e1 * t354 - 0.3e1 * t364 - 0.3e1 * t373
  t377 = f.my_piecewise5(t83, 0, t86, 0, t318 + t375)
  t379 = -0.770e3 / 0.243e3 * t240 + t246 * t96 + 0.3e1 * t167 * t137 + 0.3e1 * t124 * t210 + t78 * t377
  t384 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t98 + 0.3e1 / 0.10e2 * t6 * t109 * t98 + 0.9e1 / 0.20e2 * t6 * t113 * t139 - t6 * t148 * t98 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t152 * t139 + 0.9e1 / 0.20e2 * t6 * t156 * t212 + 0.2e1 / 0.45e2 * t6 * t223 * t98 - t6 * t227 * t139 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t231 * t212 + 0.3e1 / 0.20e2 * t6 * t235 * t379)
  t386 = r1 <= f.p.dens_threshold
  t387 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t388 = 0.1e1 + t387
  t389 = t388 <= f.p.zeta_threshold
  t390 = t388 ** (0.1e1 / 0.3e1)
  t392 = 0.1e1 / t390 / t388
  t394 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t395 = t394 ** 2
  t399 = 0.1e1 / t390
  t400 = t399 * t394
  t402 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t405 = t390 ** 2
  t407 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t411 = f.my_piecewise3(t389, 0, -0.10e2 / 0.27e2 * t392 * t395 * t394 + 0.10e2 / 0.3e1 * t400 * t402 + 0.5e1 / 0.3e1 * t405 * t407)
  t413 = r1 ** 2
  t414 = r1 ** (0.1e1 / 0.3e1)
  t415 = t414 ** 2
  t419 = t63 * s2 / t415 / t413
  t427 = 0.5e1 / 0.54e2 * t63 * l1 / t415 / r1 - 0.5e1 / 0.81e2 * t419
  t429 = -t85 < t427
  t430 = f.my_piecewise3(t429, -t85, t427)
  t432 = f.my_piecewise3(-t82 < t430, t430, -t82)
  t433 = abs(t432)
  t434 = t433 ** params.csk_a
  t436 = jnp.exp(-0.1e1 / t434)
  t438 = (0.1e1 - t436) ** t81
  t439 = f.my_piecewise5(t427 < -t82, 0, t429, 1, t438)
  t441 = 0.1e1 + 0.5e1 / 0.72e2 * t419 + t427 * t439
  t450 = f.my_piecewise3(t389, 0, 0.10e2 / 0.9e1 * t399 * t395 + 0.5e1 / 0.3e1 * t405 * t402)
  t457 = f.my_piecewise3(t389, 0, 0.5e1 / 0.3e1 * t405 * t394)
  t463 = f.my_piecewise3(t389, t218, t405 * t388)
  t469 = f.my_piecewise3(t386, 0, 0.3e1 / 0.20e2 * t6 * t411 * t56 * t441 + 0.3e1 / 0.10e2 * t6 * t450 * t108 * t441 - t6 * t457 * t147 * t441 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t463 * t222 * t441)
  t487 = t63 * s0 / t66 / t157 / t64
  t493 = 0.15400e5 / 0.2187e4 * t63 * l0 * t238 - 0.104720e6 / 0.6561e4 * t487
  t501 = t192 * t196
  t502 = t501 * t178
  t503 = t173 * t502
  t504 = params.csk_a * t127
  t505 = t504 * t347
  t516 = f.my_piecewise3(t86, 0, t493)
  t517 = f.my_piecewise3(t88, t516, 0)
  t521 = t174 ** 2
  t523 = t176 ** 2
  t524 = t177 ** 2
  t525 = 0.1e1 / t524
  t526 = t523 * t525
  t538 = t171 ** 2
  t540 = t95 / t538
  t542 = t180 ** 2
  t543 = t181 ** 2
  t544 = 0.1e1 / t543
  t551 = t192 ** 2
  t555 = t196 ** 2
  t556 = t555 * t178
  t566 = t255 * t176
  t567 = t173 * t566
  t568 = t182 * t289
  t570 = t340 * t568 * t196
  t573 = t174 * t257
  t574 = t126 * t573
  t589 = t174 * t270
  t590 = t173 * t589
  t593 = t254 * t573
  t598 = 0.14e2 * t173 * t127 * t130 * t205 * t301 * t196 + 0.14e2 * t126 * t501 * t188 * t330 * t130 + 0.18e2 * t593 * t340 * t301 * params.csk_a + 0.3e1 * t126 * t551 * t201 + 0.3e1 * t200 * t556 * t134 + 0.3e1 * t173 * t551 * t184 + 0.3e1 * t175 * t556 * t183 - 0.18e2 * t574 * t312 * t352 - 0.3e1 * t193 * t272 - 0.4e1 * t590 * t367 + 0.18e2 * t567 * t570
  t600 = t126 * t589
  t605 = t255 * t196
  t609 = t312 * t133 * t176 * params.csk_a
  t623 = t290 * t134 * t192
  t626 = t254 * t566
  t628 = t290 * t134 * t196
  t636 = t290 * t183 * t192
  t644 = t126 * t566
  t659 = t173 * t573
  t664 = t263 * t192
  t675 = t521 * t523
  t676 = t540 * t675
  t677 = t525 * t261
  t678 = t677 * t320
  t681 = -0.12e2 * t644 * t312 * t133 * t196 - 0.12e2 * t593 * t294 * t295 * t192 - 0.12e2 * t626 * t294 * t295 * t196 + 0.18e2 * t626 * t294 * t320 * t196 + 0.18e2 * t593 * t294 * t664 * params.csk_a + 0.18e2 * t567 * t628 - 0.6e1 * t574 * t623 + 0.18e2 * t659 * t623 - 0.6e1 * t644 * t628 + 0.18e2 * t659 * t636 - 0.6e1 * t676 * t678
  t684 = t254 * t675
  t685 = t525 * t180
  t686 = t685 * t206
  t689 = t677 * t295
  t692 = t289 * params.csk_a
  t694 = t677 * t263 * t692
  t697 = t525 * t542
  t708 = t525 * t692
  t709 = t708 * t183
  t712 = t173 * t675
  t713 = t685 * t568
  t716 = t708 * t134
  t723 = t126 * t675
  t724 = t525 * t93
  t725 = t724 * t189
  t732 = t724 * t313
  t747 = -0.6e1 * t593 * t294 * t664 + 0.6e1 * t684 * t716 + 0.6e1 * t684 * t732 + 0.7e1 * t712 * t686 - 0.7e1 * t712 * t709 - 0.7e1 * t712 * t716 - 0.11e2 * t712 * t725 - 0.18e2 * t712 * t732 + t723 * t716 + 0.11e2 * t723 * t725 + 0.6e1 * t723 * t732
  t757 = t551 * t176
  t758 = t173 * t757
  t761 = t174 * t555
  t762 = t173 * t761
  t803 = -0.12e2 * t574 * t312 * t133 * t192 - 0.18e2 * t659 * t340 * t301 - 0.18e2 * t567 * t340 * t307 - 0.12e2 * t676 * t694 + 0.7e1 * t676 * t713 + 0.18e2 * t684 * t709 + 0.4e1 * t303 + 0.4e1 * t332 + 0.4e1 * t354 - 0.4e1 * t364 - 0.4e1 * t373
  t807 = f.my_piecewise5(t83, 0, t86, 0, t803 + t598 + 0.6e1 * t126 * t521 * t526 * t134 + 0.18e2 * t626 * t340 * t206 * t196 + 0.11e2 * t676 * t697 * t544 * t289 - 0.6e1 * t676 * t697 * t544 * t692 - 0.6e1 * t626 * t294 * t263 * t196 - 0.6e1 * t676 * t697 * t544 * params.csk_a + 0.4e1 * t306 * t205 * t182 * t270 - 0.14e2 * t503 * t183 * t504 * t130 - t128 * t517 * t131 * t134 + 0.6e1 * t254 * t521 * t526 * t264 + 0.11e2 * t173 * t521 * t526 * t183 + t681 - 0.3e1 * t267 - 0.3e1 * t762 * t190 - 0.3e1 * t758 * t207 - 0.3e1 * t762 * t207 + 0.4e1 * t600 * t337 - 0.3e1 * t758 * t190 - 0.11e2 * t712 * t713 - t676 * t716 - 0.12e2 * t684 * t678 - 0.6e1 * t684 * t689 + 0.12e2 * t684 * t694 + 0.18e2 * t676 * t689 - 0.7e1 * t676 * t709 - 0.18e2 * t684 * t686 - 0.18e2 * t593 * t636 - 0.18e2 * t626 * t570 - 0.6e1 * t593 * t623 - 0.6e1 * t626 * t628 + 0.4e1 * t600 * t348 - 0.4e1 * t590 * t348 - 0.14e2 * t503 * t505 - t194 + t540 * t521 * t526 * t542 * t544 + 0.3e1 * t126 * t761 * t190 + 0.3e1 * t126 * t757 * t190 + 0.14e2 * t126 * t502 * t505 - 0.18e2 * t126 * t605 * t609 + 0.18e2 * t173 * t605 * t609 + 0.18e2 * t173 * t192 * t257 * t284 * t174 * t93 * t133 + t747)
  t813 = t20 ** 2
  t816 = t30 ** 2
  t822 = t41 ** 2
  t831 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t832 = f.my_piecewise5(t11, 0, t15, 0, t831)
  t836 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t813 * t816 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t822 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t832)
  t869 = 0.1e1 / t55 / t36
  t874 = 0.3e1 / 0.5e1 * t6 * t156 * t379 + 0.8e1 / 0.45e2 * t6 * t223 * t139 - t6 * t227 * t212 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t231 * t379 + 0.3e1 / 0.20e2 * t6 * t235 * (0.13090e5 / 0.729e3 * t487 + t493 * t96 + 0.4e1 * t246 * t137 + 0.6e1 * t167 * t210 + 0.4e1 * t124 * t377 + t78 * t807) + 0.3e1 / 0.20e2 * t6 * t836 * t56 * t98 + 0.3e1 / 0.5e1 * t6 * t57 * t139 + 0.6e1 / 0.5e1 * t6 * t109 * t139 + 0.9e1 / 0.10e2 * t6 * t113 * t212 - 0.2e1 / 0.5e1 * t6 * t148 * t139 + 0.6e1 / 0.5e1 * t6 * t152 * t212 + 0.2e1 / 0.5e1 * t6 * t54 * t108 * t98 - t6 * t107 * t147 * t98 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t145 * t222 * t98 - 0.14e2 / 0.135e3 * t6 * t220 * t869 * t98
  t875 = f.my_piecewise3(t1, 0, t874)
  t876 = t388 ** 2
  t879 = t395 ** 2
  t885 = t402 ** 2
  t891 = f.my_piecewise5(t15, 0, t11, 0, -t831)
  t895 = f.my_piecewise3(t389, 0, 0.40e2 / 0.81e2 / t390 / t876 * t879 - 0.20e2 / 0.9e1 * t392 * t395 * t402 + 0.10e2 / 0.3e1 * t399 * t885 + 0.40e2 / 0.9e1 * t400 * t407 + 0.5e1 / 0.3e1 * t405 * t891)
  t917 = f.my_piecewise3(t386, 0, 0.3e1 / 0.20e2 * t6 * t895 * t56 * t441 + 0.2e1 / 0.5e1 * t6 * t411 * t108 * t441 - t6 * t450 * t147 * t441 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t457 * t222 * t441 - 0.14e2 / 0.135e3 * t6 * t463 * t869 * t441)
  d1111 = 0.4e1 * t384 + 0.4e1 * t469 + t7 * (t875 + t917)

  res = {'v4rho4': d1111}
  return res
