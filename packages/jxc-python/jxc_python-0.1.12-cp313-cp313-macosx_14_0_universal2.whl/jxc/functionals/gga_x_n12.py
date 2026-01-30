"""Generated from gga_x_n12.mpl."""

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
  params_CC_0__raw = params.CC[0]
  if isinstance(params_CC_0__raw, (str, bytes, dict)):
    params_CC_0_ = params_CC_0__raw
  else:
    try:
      params_CC_0__seq = list(params_CC_0__raw)
    except TypeError:
      params_CC_0_ = params_CC_0__raw
    else:
      params_CC_0__seq = np.asarray(params_CC_0__seq, dtype=np.float64)
      params_CC_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_0__seq))
  params_CC_1__raw = params.CC[1]
  if isinstance(params_CC_1__raw, (str, bytes, dict)):
    params_CC_1_ = params_CC_1__raw
  else:
    try:
      params_CC_1__seq = list(params_CC_1__raw)
    except TypeError:
      params_CC_1_ = params_CC_1__raw
    else:
      params_CC_1__seq = np.asarray(params_CC_1__seq, dtype=np.float64)
      params_CC_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_1__seq))
  params_CC_2__raw = params.CC[2]
  if isinstance(params_CC_2__raw, (str, bytes, dict)):
    params_CC_2_ = params_CC_2__raw
  else:
    try:
      params_CC_2__seq = list(params_CC_2__raw)
    except TypeError:
      params_CC_2_ = params_CC_2__raw
    else:
      params_CC_2__seq = np.asarray(params_CC_2__seq, dtype=np.float64)
      params_CC_2_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_2__seq))
  params_CC_3__raw = params.CC[3]
  if isinstance(params_CC_3__raw, (str, bytes, dict)):
    params_CC_3_ = params_CC_3__raw
  else:
    try:
      params_CC_3__seq = list(params_CC_3__raw)
    except TypeError:
      params_CC_3_ = params_CC_3__raw
    else:
      params_CC_3__seq = np.asarray(params_CC_3__seq, dtype=np.float64)
      params_CC_3_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_3__seq))

  n12_omega_x = 2.5

  n12_gamma_x = 0.004

  n12_rss = lambda rs, z: rs * 2 ** (1 / 3) * f.opz_pow_n(z, -1 / 3)

  n12_vx = lambda rs: 1 / (1 + 1 / (f.RS_FACTOR * n12_omega_x) * rs)

  n12_ux = lambda x: n12_gamma_x * x ** 2 / (1 + n12_gamma_x * x ** 2)

  n12_FN12 = lambda rs, z, x: +jnp.sum(jnp.array([params_CC_0_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) + jnp.sum(jnp.array([params_CC_1_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) + jnp.sum(jnp.array([params_CC_2_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 2 + jnp.sum(jnp.array([params_CC_3_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, n12_FN12, rs, z, xs0, xs1)

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
  params_CC_0__raw = params.CC[0]
  if isinstance(params_CC_0__raw, (str, bytes, dict)):
    params_CC_0_ = params_CC_0__raw
  else:
    try:
      params_CC_0__seq = list(params_CC_0__raw)
    except TypeError:
      params_CC_0_ = params_CC_0__raw
    else:
      params_CC_0__seq = np.asarray(params_CC_0__seq, dtype=np.float64)
      params_CC_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_0__seq))
  params_CC_1__raw = params.CC[1]
  if isinstance(params_CC_1__raw, (str, bytes, dict)):
    params_CC_1_ = params_CC_1__raw
  else:
    try:
      params_CC_1__seq = list(params_CC_1__raw)
    except TypeError:
      params_CC_1_ = params_CC_1__raw
    else:
      params_CC_1__seq = np.asarray(params_CC_1__seq, dtype=np.float64)
      params_CC_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_1__seq))
  params_CC_2__raw = params.CC[2]
  if isinstance(params_CC_2__raw, (str, bytes, dict)):
    params_CC_2_ = params_CC_2__raw
  else:
    try:
      params_CC_2__seq = list(params_CC_2__raw)
    except TypeError:
      params_CC_2_ = params_CC_2__raw
    else:
      params_CC_2__seq = np.asarray(params_CC_2__seq, dtype=np.float64)
      params_CC_2_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_2__seq))
  params_CC_3__raw = params.CC[3]
  if isinstance(params_CC_3__raw, (str, bytes, dict)):
    params_CC_3_ = params_CC_3__raw
  else:
    try:
      params_CC_3__seq = list(params_CC_3__raw)
    except TypeError:
      params_CC_3_ = params_CC_3__raw
    else:
      params_CC_3__seq = np.asarray(params_CC_3__seq, dtype=np.float64)
      params_CC_3_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_3__seq))

  n12_omega_x = 2.5

  n12_gamma_x = 0.004

  n12_rss = lambda rs, z: rs * 2 ** (1 / 3) * f.opz_pow_n(z, -1 / 3)

  n12_vx = lambda rs: 1 / (1 + 1 / (f.RS_FACTOR * n12_omega_x) * rs)

  n12_ux = lambda x: n12_gamma_x * x ** 2 / (1 + n12_gamma_x * x ** 2)

  n12_FN12 = lambda rs, z, x: +jnp.sum(jnp.array([params_CC_0_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) + jnp.sum(jnp.array([params_CC_1_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) + jnp.sum(jnp.array([params_CC_2_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 2 + jnp.sum(jnp.array([params_CC_3_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, n12_FN12, rs, z, xs0, xs1)

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
  params_CC_0__raw = params.CC[0]
  if isinstance(params_CC_0__raw, (str, bytes, dict)):
    params_CC_0_ = params_CC_0__raw
  else:
    try:
      params_CC_0__seq = list(params_CC_0__raw)
    except TypeError:
      params_CC_0_ = params_CC_0__raw
    else:
      params_CC_0__seq = np.asarray(params_CC_0__seq, dtype=np.float64)
      params_CC_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_0__seq))
  params_CC_1__raw = params.CC[1]
  if isinstance(params_CC_1__raw, (str, bytes, dict)):
    params_CC_1_ = params_CC_1__raw
  else:
    try:
      params_CC_1__seq = list(params_CC_1__raw)
    except TypeError:
      params_CC_1_ = params_CC_1__raw
    else:
      params_CC_1__seq = np.asarray(params_CC_1__seq, dtype=np.float64)
      params_CC_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_1__seq))
  params_CC_2__raw = params.CC[2]
  if isinstance(params_CC_2__raw, (str, bytes, dict)):
    params_CC_2_ = params_CC_2__raw
  else:
    try:
      params_CC_2__seq = list(params_CC_2__raw)
    except TypeError:
      params_CC_2_ = params_CC_2__raw
    else:
      params_CC_2__seq = np.asarray(params_CC_2__seq, dtype=np.float64)
      params_CC_2_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_2__seq))
  params_CC_3__raw = params.CC[3]
  if isinstance(params_CC_3__raw, (str, bytes, dict)):
    params_CC_3_ = params_CC_3__raw
  else:
    try:
      params_CC_3__seq = list(params_CC_3__raw)
    except TypeError:
      params_CC_3_ = params_CC_3__raw
    else:
      params_CC_3__seq = np.asarray(params_CC_3__seq, dtype=np.float64)
      params_CC_3_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_3__seq))

  n12_omega_x = 2.5

  n12_gamma_x = 0.004

  n12_rss = lambda rs, z: rs * 2 ** (1 / 3) * f.opz_pow_n(z, -1 / 3)

  n12_vx = lambda rs: 1 / (1 + 1 / (f.RS_FACTOR * n12_omega_x) * rs)

  n12_ux = lambda x: n12_gamma_x * x ** 2 / (1 + n12_gamma_x * x ** 2)

  n12_FN12 = lambda rs, z, x: +jnp.sum(jnp.array([params_CC_0_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) + jnp.sum(jnp.array([params_CC_1_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) + jnp.sum(jnp.array([params_CC_2_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 2 + jnp.sum(jnp.array([params_CC_3_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, n12_FN12, rs, z, xs0, xs1)

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
  t27 = t25 * t26
  t28 = params_CC_0_[0]
  t29 = params_CC_0_[1]
  t30 = t29 * s0
  t31 = r0 ** 2
  t32 = r0 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t35 = 0.1e1 / t33 / t31
  t38 = 0.1e1 + 0.4e-2 * s0 * t35
  t39 = 0.1e1 / t38
  t40 = t35 * t39
  t43 = params_CC_0_[2]
  t44 = s0 ** 2
  t45 = t43 * t44
  t46 = t31 ** 2
  t50 = t38 ** 2
  t51 = 0.1e1 / t50
  t52 = 0.1e1 / t32 / t46 / r0 * t51
  t55 = params_CC_0_[3]
  t56 = t44 * s0
  t57 = t55 * t56
  t58 = t46 ** 2
  t61 = 0.1e1 / t50 / t38
  t62 = 0.1e1 / t58 * t61
  t65 = params_CC_1_[0]
  t66 = params_CC_1_[1]
  t67 = t66 * s0
  t70 = params_CC_1_[2]
  t71 = t70 * t44
  t74 = params_CC_1_[3]
  t75 = t74 * t56
  t78 = t65 + 0.4e-2 * t67 * t40 + 0.16e-4 * t71 * t52 + 0.64e-7 * t75 * t62
  t80 = 2 ** (0.1e1 / 0.3e1)
  t81 = 0.1e1 / t26 * t80
  t83 = 0.1e1 + t17 <= f.p.zeta_threshold
  t85 = 0.1e1 - t17 <= f.p.zeta_threshold
  t86 = f.my_piecewise5(t83, t11, t85, t15, t17)
  t87 = 0.1e1 + t86
  t88 = t87 <= f.p.zeta_threshold
  t89 = 0.1e1 / t21
  t90 = t87 ** (0.1e1 / 0.3e1)
  t92 = f.my_piecewise3(t88, t89, 0.1e1 / t90)
  t95 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t81 * t92
  t96 = 0.1e1 / t95
  t98 = params_CC_2_[0]
  t99 = params_CC_2_[1]
  t100 = t99 * s0
  t103 = params_CC_2_[2]
  t104 = t103 * t44
  t107 = params_CC_2_[3]
  t108 = t107 * t56
  t111 = t98 + 0.4e-2 * t100 * t40 + 0.16e-4 * t104 * t52 + 0.64e-7 * t108 * t62
  t112 = t95 ** 2
  t113 = 0.1e1 / t112
  t115 = params_CC_3_[0]
  t116 = params_CC_3_[1]
  t117 = t116 * s0
  t120 = params_CC_3_[2]
  t121 = t120 * t44
  t124 = params_CC_3_[3]
  t125 = t124 * t56
  t128 = t115 + 0.4e-2 * t117 * t40 + 0.16e-4 * t121 * t52 + 0.64e-7 * t125 * t62
  t130 = 0.1e1 / t112 / t95
  t132 = t28 + 0.4e-2 * t30 * t40 + 0.16e-4 * t45 * t52 + 0.64e-7 * t57 * t62 + t78 * t96 + t111 * t113 + t128 * t130
  t136 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t132)
  t137 = r1 <= f.p.dens_threshold
  t138 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t139 = 0.1e1 + t138
  t140 = t139 <= f.p.zeta_threshold
  t141 = t139 ** (0.1e1 / 0.3e1)
  t143 = f.my_piecewise3(t140, t22, t141 * t139)
  t144 = t143 * t26
  t145 = t29 * s2
  t146 = r1 ** 2
  t147 = r1 ** (0.1e1 / 0.3e1)
  t148 = t147 ** 2
  t150 = 0.1e1 / t148 / t146
  t153 = 0.1e1 + 0.4e-2 * s2 * t150
  t154 = 0.1e1 / t153
  t155 = t150 * t154
  t158 = s2 ** 2
  t159 = t43 * t158
  t160 = t146 ** 2
  t164 = t153 ** 2
  t165 = 0.1e1 / t164
  t166 = 0.1e1 / t147 / t160 / r1 * t165
  t169 = t158 * s2
  t170 = t55 * t169
  t171 = t160 ** 2
  t174 = 0.1e1 / t164 / t153
  t175 = 0.1e1 / t171 * t174
  t178 = t66 * s2
  t181 = t70 * t158
  t184 = t74 * t169
  t187 = t65 + 0.4e-2 * t178 * t155 + 0.16e-4 * t181 * t166 + 0.64e-7 * t184 * t175
  t188 = f.my_piecewise5(t85, t11, t83, t15, -t17)
  t189 = 0.1e1 + t188
  t190 = t189 <= f.p.zeta_threshold
  t191 = t189 ** (0.1e1 / 0.3e1)
  t193 = f.my_piecewise3(t190, t89, 0.1e1 / t191)
  t196 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t81 * t193
  t197 = 0.1e1 / t196
  t199 = t99 * s2
  t202 = t103 * t158
  t205 = t107 * t169
  t208 = t98 + 0.4e-2 * t199 * t155 + 0.16e-4 * t202 * t166 + 0.64e-7 * t205 * t175
  t209 = t196 ** 2
  t210 = 0.1e1 / t209
  t212 = t116 * s2
  t215 = t120 * t158
  t218 = t124 * t169
  t221 = t115 + 0.4e-2 * t212 * t155 + 0.16e-4 * t215 * t166 + 0.64e-7 * t218 * t175
  t223 = 0.1e1 / t209 / t196
  t225 = t28 + 0.4e-2 * t145 * t155 + 0.16e-4 * t159 * t166 + 0.64e-7 * t170 * t175 + t187 * t197 + t208 * t210 + t221 * t223
  t229 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t144 * t225)
  t230 = t6 ** 2
  t232 = t16 / t230
  t233 = t7 - t232
  t234 = f.my_piecewise5(t10, 0, t14, 0, t233)
  t237 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t234)
  t242 = t26 ** 2
  t243 = 0.1e1 / t242
  t247 = t5 * t25 * t243 * t132 / 0.8e1
  t248 = t31 * r0
  t251 = 0.1e1 / t33 / t248 * t39
  t258 = 0.1e1 / t32 / t46 / t31 * t51
  t266 = 0.1e1 / t58 / r0 * t61
  t271 = t44 ** 2
  t276 = t50 ** 2
  t277 = 0.1e1 / t276
  t278 = 0.1e1 / t33 / t58 / t248 * t277
  t298 = t78 * t113
  t301 = 0.1e1 / t26 / t6 * t80
  t303 = 0.13333333333333333333333333333333333333333333333333e0 * t301 * t92
  t305 = 0.1e1 / t90 / t87
  t306 = f.my_piecewise5(t83, 0, t85, 0, t233)
  t309 = f.my_piecewise3(t88, 0, -t305 * t306 / 0.3e1)
  t312 = -t303 + 0.39999999999999999999999999999999999999999999999998e0 * t81 * t309
  t331 = t111 * t130
  t351 = t112 ** 2
  t353 = t128 / t351
  t356 = -0.10666666666666666666666666666666666666666666666667e-1 * t30 * t251 + 0.42666666666666666666666666666666666666666666666668e-4 * t29 * t44 * t258 - 0.85333333333333333333333333333333333333333333333333e-4 * t45 * t258 + 0.34133333333333333333333333333333333333333333333334e-6 * t43 * t56 * t266 - 0.512e-6 * t57 * t266 + 0.20480000000000000000000000000000000000000000000001e-8 * t55 * t271 * t278 + (-0.10666666666666666666666666666666666666666666666667e-1 * t67 * t251 + 0.42666666666666666666666666666666666666666666666668e-4 * t66 * t44 * t258 - 0.85333333333333333333333333333333333333333333333333e-4 * t71 * t258 + 0.34133333333333333333333333333333333333333333333334e-6 * t70 * t56 * t266 - 0.512e-6 * t75 * t266 + 0.20480000000000000000000000000000000000000000000001e-8 * t74 * t271 * t278) * t96 - t298 * t312 + (-0.10666666666666666666666666666666666666666666666667e-1 * t100 * t251 + 0.42666666666666666666666666666666666666666666666668e-4 * t99 * t44 * t258 - 0.85333333333333333333333333333333333333333333333333e-4 * t104 * t258 + 0.34133333333333333333333333333333333333333333333334e-6 * t103 * t56 * t266 - 0.512e-6 * t108 * t266 + 0.20480000000000000000000000000000000000000000000001e-8 * t107 * t271 * t278) * t113 - 0.2e1 * t331 * t312 + (-0.10666666666666666666666666666666666666666666666667e-1 * t117 * t251 + 0.42666666666666666666666666666666666666666666666668e-4 * t116 * t44 * t258 - 0.85333333333333333333333333333333333333333333333333e-4 * t121 * t258 + 0.34133333333333333333333333333333333333333333333334e-6 * t120 * t56 * t266 - 0.512e-6 * t125 * t266 + 0.20480000000000000000000000000000000000000000000001e-8 * t124 * t271 * t278) * t130 - 0.3e1 * t353 * t312
  t361 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t237 * t26 * t132 - t247 - 0.3e1 / 0.8e1 * t5 * t27 * t356)
  t362 = -t233
  t363 = f.my_piecewise5(t14, 0, t10, 0, t362)
  t366 = f.my_piecewise3(t140, 0, 0.4e1 / 0.3e1 * t141 * t363)
  t374 = t5 * t143 * t243 * t225 / 0.8e1
  t375 = t187 * t210
  t377 = 0.13333333333333333333333333333333333333333333333333e0 * t301 * t193
  t379 = 0.1e1 / t191 / t189
  t380 = f.my_piecewise5(t85, 0, t83, 0, t362)
  t383 = f.my_piecewise3(t190, 0, -t379 * t380 / 0.3e1)
  t386 = -t377 + 0.39999999999999999999999999999999999999999999999998e0 * t81 * t383
  t388 = t208 * t223
  t391 = t209 ** 2
  t393 = t221 / t391
  t401 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t366 * t26 * t225 - t374 - 0.3e1 / 0.8e1 * t5 * t144 * (-t375 * t386 - 0.2e1 * t388 * t386 - 0.3e1 * t393 * t386))
  vrho_0_ = t136 + t229 + t6 * (t361 + t401)
  t404 = -t7 - t232
  t405 = f.my_piecewise5(t10, 0, t14, 0, t404)
  t408 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t405)
  t413 = f.my_piecewise5(t83, 0, t85, 0, t404)
  t416 = f.my_piecewise3(t88, 0, -t305 * t413 / 0.3e1)
  t419 = -t303 + 0.39999999999999999999999999999999999999999999999998e0 * t81 * t416
  t430 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t408 * t26 * t132 - t247 - 0.3e1 / 0.8e1 * t5 * t27 * (-t298 * t419 - 0.2e1 * t331 * t419 - 0.3e1 * t353 * t419))
  t431 = -t404
  t432 = f.my_piecewise5(t14, 0, t10, 0, t431)
  t435 = f.my_piecewise3(t140, 0, 0.4e1 / 0.3e1 * t141 * t432)
  t440 = t146 * r1
  t443 = 0.1e1 / t148 / t440 * t154
  t450 = 0.1e1 / t147 / t160 / t146 * t165
  t458 = 0.1e1 / t171 / r1 * t174
  t463 = t158 ** 2
  t468 = t164 ** 2
  t469 = 0.1e1 / t468
  t470 = 0.1e1 / t148 / t171 / t440 * t469
  t490 = f.my_piecewise5(t85, 0, t83, 0, t431)
  t493 = f.my_piecewise3(t190, 0, -t379 * t490 / 0.3e1)
  t496 = -t377 + 0.39999999999999999999999999999999999999999999999998e0 * t81 * t493
  t536 = -0.10666666666666666666666666666666666666666666666667e-1 * t145 * t443 + 0.42666666666666666666666666666666666666666666666668e-4 * t29 * t158 * t450 - 0.85333333333333333333333333333333333333333333333333e-4 * t159 * t450 + 0.34133333333333333333333333333333333333333333333334e-6 * t43 * t169 * t458 - 0.512e-6 * t170 * t458 + 0.20480000000000000000000000000000000000000000000001e-8 * t55 * t463 * t470 + (-0.10666666666666666666666666666666666666666666666667e-1 * t178 * t443 + 0.42666666666666666666666666666666666666666666666668e-4 * t66 * t158 * t450 - 0.85333333333333333333333333333333333333333333333333e-4 * t181 * t450 + 0.34133333333333333333333333333333333333333333333334e-6 * t70 * t169 * t458 - 0.512e-6 * t184 * t458 + 0.20480000000000000000000000000000000000000000000001e-8 * t74 * t463 * t470) * t197 - t375 * t496 + (-0.10666666666666666666666666666666666666666666666667e-1 * t199 * t443 + 0.42666666666666666666666666666666666666666666666668e-4 * t99 * t158 * t450 - 0.85333333333333333333333333333333333333333333333333e-4 * t202 * t450 + 0.34133333333333333333333333333333333333333333333334e-6 * t103 * t169 * t458 - 0.512e-6 * t205 * t458 + 0.20480000000000000000000000000000000000000000000001e-8 * t107 * t463 * t470) * t210 - 0.2e1 * t388 * t496 + (-0.10666666666666666666666666666666666666666666666667e-1 * t212 * t443 + 0.42666666666666666666666666666666666666666666666668e-4 * t116 * t158 * t450 - 0.85333333333333333333333333333333333333333333333333e-4 * t215 * t450 + 0.34133333333333333333333333333333333333333333333334e-6 * t120 * t169 * t458 - 0.512e-6 * t218 * t458 + 0.20480000000000000000000000000000000000000000000001e-8 * t124 * t463 * t470) * t223 - 0.3e1 * t393 * t496
  t541 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t435 * t26 * t225 - t374 - 0.3e1 / 0.8e1 * t5 * t144 * t536)
  vrho_1_ = t136 + t229 + t6 * (t430 + t541)
  t560 = 0.1e1 / t33 / t58 / t31 * t277
  t618 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.4e-2 * t29 * t35 * t39 - 0.16e-4 * t30 * t52 + 0.32e-4 * t43 * s0 * t52 - 0.128e-6 * t45 * t62 + 0.192e-6 * t55 * t44 * t62 - 0.768e-9 * t57 * t560 + (0.4e-2 * t66 * t35 * t39 - 0.16e-4 * t67 * t52 + 0.32e-4 * t70 * s0 * t52 - 0.128e-6 * t71 * t62 + 0.192e-6 * t74 * t44 * t62 - 0.768e-9 * t75 * t560) * t96 + (0.4e-2 * t99 * t35 * t39 - 0.16e-4 * t100 * t52 + 0.32e-4 * t103 * s0 * t52 - 0.128e-6 * t104 * t62 + 0.192e-6 * t107 * t44 * t62 - 0.768e-9 * t108 * t560) * t113 + (0.4e-2 * t116 * t35 * t39 - 0.16e-4 * t117 * t52 + 0.32e-4 * t120 * s0 * t52 - 0.128e-6 * t121 * t62 + 0.192e-6 * t124 * t44 * t62 - 0.768e-9 * t125 * t560) * t130))
  vsigma_0_ = t6 * t618
  vsigma_1_ = 0.0e0
  t635 = 0.1e1 / t148 / t171 / t146 * t469
  t693 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t144 * (0.4e-2 * t29 * t150 * t154 - 0.16e-4 * t145 * t166 + 0.32e-4 * t43 * s2 * t166 - 0.128e-6 * t159 * t175 + 0.192e-6 * t55 * t158 * t175 - 0.768e-9 * t170 * t635 + (0.4e-2 * t66 * t150 * t154 - 0.16e-4 * t178 * t166 + 0.32e-4 * t70 * s2 * t166 - 0.128e-6 * t181 * t175 + 0.192e-6 * t74 * t158 * t175 - 0.768e-9 * t184 * t635) * t197 + (0.4e-2 * t99 * t150 * t154 - 0.16e-4 * t199 * t166 + 0.32e-4 * t103 * s2 * t166 - 0.128e-6 * t202 * t175 + 0.192e-6 * t107 * t158 * t175 - 0.768e-9 * t205 * t635) * t210 + (0.4e-2 * t116 * t150 * t154 - 0.16e-4 * t212 * t166 + 0.32e-4 * t120 * s2 * t166 - 0.128e-6 * t215 * t175 + 0.192e-6 * t124 * t158 * t175 - 0.768e-9 * t218 * t635) * t223))
  vsigma_2_ = t6 * t693
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
  params_CC_0__raw = params.CC[0]
  if isinstance(params_CC_0__raw, (str, bytes, dict)):
    params_CC_0_ = params_CC_0__raw
  else:
    try:
      params_CC_0__seq = list(params_CC_0__raw)
    except TypeError:
      params_CC_0_ = params_CC_0__raw
    else:
      params_CC_0__seq = np.asarray(params_CC_0__seq, dtype=np.float64)
      params_CC_0_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_0__seq))
  params_CC_1__raw = params.CC[1]
  if isinstance(params_CC_1__raw, (str, bytes, dict)):
    params_CC_1_ = params_CC_1__raw
  else:
    try:
      params_CC_1__seq = list(params_CC_1__raw)
    except TypeError:
      params_CC_1_ = params_CC_1__raw
    else:
      params_CC_1__seq = np.asarray(params_CC_1__seq, dtype=np.float64)
      params_CC_1_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_1__seq))
  params_CC_2__raw = params.CC[2]
  if isinstance(params_CC_2__raw, (str, bytes, dict)):
    params_CC_2_ = params_CC_2__raw
  else:
    try:
      params_CC_2__seq = list(params_CC_2__raw)
    except TypeError:
      params_CC_2_ = params_CC_2__raw
    else:
      params_CC_2__seq = np.asarray(params_CC_2__seq, dtype=np.float64)
      params_CC_2_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_2__seq))
  params_CC_3__raw = params.CC[3]
  if isinstance(params_CC_3__raw, (str, bytes, dict)):
    params_CC_3_ = params_CC_3__raw
  else:
    try:
      params_CC_3__seq = list(params_CC_3__raw)
    except TypeError:
      params_CC_3_ = params_CC_3__raw
    else:
      params_CC_3__seq = np.asarray(params_CC_3__seq, dtype=np.float64)
      params_CC_3_ = np.concatenate((np.array([np.nan], dtype=np.float64), params_CC_3__seq))

  n12_omega_x = 2.5

  n12_gamma_x = 0.004

  n12_rss = lambda rs, z: rs * 2 ** (1 / 3) * f.opz_pow_n(z, -1 / 3)

  n12_vx = lambda rs: 1 / (1 + 1 / (f.RS_FACTOR * n12_omega_x) * rs)

  n12_ux = lambda x: n12_gamma_x * x ** 2 / (1 + n12_gamma_x * x ** 2)

  n12_FN12 = lambda rs, z, x: +jnp.sum(jnp.array([params_CC_0_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) + jnp.sum(jnp.array([params_CC_1_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) + jnp.sum(jnp.array([params_CC_2_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 2 + jnp.sum(jnp.array([params_CC_3_[i + 1] * n12_ux(x) ** i for i in range(0, 3 + 1)]), axis=0) * n12_vx(n12_rss(rs, z)) ** 3

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, n12_FN12, rs, z, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t21 = params_CC_0_[1]
  t22 = t21 * s0
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = r0 ** 2
  t26 = t18 ** 2
  t28 = 0.1e1 / t26 / t25
  t33 = 0.1e1 + 0.4e-2 * s0 * t24 * t28
  t34 = 0.1e1 / t33
  t35 = t24 * t28 * t34
  t38 = params_CC_0_[2]
  t39 = s0 ** 2
  t40 = t38 * t39
  t41 = t25 ** 2
  t46 = t33 ** 2
  t47 = 0.1e1 / t46
  t48 = t23 / t18 / t41 / r0 * t47
  t51 = params_CC_0_[3]
  t52 = t39 * s0
  t53 = t51 * t52
  t54 = t41 ** 2
  t57 = 0.1e1 / t46 / t33
  t58 = 0.1e1 / t54 * t57
  t62 = params_CC_1_[1]
  t63 = t62 * s0
  t66 = params_CC_1_[2]
  t67 = t66 * t39
  t70 = params_CC_1_[3]
  t71 = t70 * t52
  t74 = params_CC_1_[0] + 0.4e-2 * t63 * t35 + 0.32e-4 * t67 * t48 + 0.256e-6 * t71 * t58
  t79 = f.my_piecewise3(t12, 0.1e1 / t13, 0.1e1 / t15)
  t82 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 / t18 * t23 * t79
  t83 = 0.1e1 / t82
  t86 = params_CC_2_[1]
  t87 = t86 * s0
  t90 = params_CC_2_[2]
  t91 = t90 * t39
  t94 = params_CC_2_[3]
  t95 = t94 * t52
  t98 = params_CC_2_[0] + 0.4e-2 * t87 * t35 + 0.32e-4 * t91 * t48 + 0.256e-6 * t95 * t58
  t99 = t82 ** 2
  t100 = 0.1e1 / t99
  t103 = params_CC_3_[1]
  t104 = t103 * s0
  t107 = params_CC_3_[2]
  t108 = t107 * t39
  t111 = params_CC_3_[3]
  t112 = t111 * t52
  t115 = params_CC_3_[0] + 0.4e-2 * t104 * t35 + 0.32e-4 * t108 * t48 + 0.256e-6 * t112 * t58
  t117 = 0.1e1 / t99 / t82
  t119 = params_CC_0_[0] + 0.4e-2 * t22 * t35 + 0.32e-4 * t40 * t48 + 0.256e-6 * t53 * t58 + t74 * t83 + t98 * t100 + t115 * t117
  t123 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t119)
  t129 = t25 * r0
  t133 = t24 / t26 / t129 * t34
  t141 = t23 / t18 / t41 / t25 * t47
  t149 = 0.1e1 / t54 / r0 * t57
  t154 = t39 ** 2
  t159 = t46 ** 2
  t160 = 0.1e1 / t159
  t162 = 0.1e1 / t26 / t54 / t129 * t160 * t24
  t186 = 0.1e1 / t18 / r0 * t23 * t79
  t226 = t99 ** 2
  t231 = -0.10666666666666666666666666666666666666666666666667e-1 * t22 * t133 + 0.85333333333333333333333333333333333333333333333336e-4 * t21 * t39 * t141 - 0.17066666666666666666666666666666666666666666666667e-3 * t40 * t141 + 0.13653333333333333333333333333333333333333333333334e-5 * t38 * t52 * t149 - 0.2048e-5 * t53 * t149 + 0.81920000000000000000000000000000000000000000000003e-8 * t51 * t154 * t162 + (-0.10666666666666666666666666666666666666666666666667e-1 * t63 * t133 + 0.85333333333333333333333333333333333333333333333336e-4 * t62 * t39 * t141 - 0.17066666666666666666666666666666666666666666666667e-3 * t67 * t141 + 0.13653333333333333333333333333333333333333333333334e-5 * t66 * t52 * t149 - 0.2048e-5 * t71 * t149 + 0.81920000000000000000000000000000000000000000000003e-8 * t70 * t154 * t162) * t83 + 0.13333333333333333333333333333333333333333333333333e0 * t74 * t100 * t186 + (-0.10666666666666666666666666666666666666666666666667e-1 * t87 * t133 + 0.85333333333333333333333333333333333333333333333336e-4 * t86 * t39 * t141 - 0.17066666666666666666666666666666666666666666666667e-3 * t91 * t141 + 0.13653333333333333333333333333333333333333333333334e-5 * t90 * t52 * t149 - 0.2048e-5 * t95 * t149 + 0.81920000000000000000000000000000000000000000000003e-8 * t94 * t154 * t162) * t100 + 0.26666666666666666666666666666666666666666666666666e0 * t98 * t117 * t186 + (-0.10666666666666666666666666666666666666666666666667e-1 * t104 * t133 + 0.85333333333333333333333333333333333333333333333336e-4 * t103 * t39 * t141 - 0.17066666666666666666666666666666666666666666666667e-3 * t108 * t141 + 0.13653333333333333333333333333333333333333333333334e-5 * t107 * t52 * t149 - 0.2048e-5 * t112 * t149 + 0.81920000000000000000000000000000000000000000000003e-8 * t111 * t154 * t162) * t117 + 0.39999999999999999999999999999999999999999999999999e0 * t115 / t226 * t186
  t236 = f.my_piecewise3(t2, 0, -t6 * t17 / t26 * t119 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * t231)
  vrho_0_ = 0.2e1 * r0 * t236 + 0.2e1 * t123
  t240 = t28 * t34
  t257 = 0.1e1 / t26 / t54 / t25 * t160 * t24
  t315 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.4e-2 * t21 * t24 * t240 - 0.32e-4 * t22 * t48 + 0.64e-4 * t38 * s0 * t48 - 0.512e-6 * t40 * t58 + 0.768e-6 * t51 * t39 * t58 - 0.3072e-8 * t53 * t257 + (0.4e-2 * t62 * t24 * t240 - 0.32e-4 * t63 * t48 + 0.64e-4 * t66 * s0 * t48 - 0.512e-6 * t67 * t58 + 0.768e-6 * t70 * t39 * t58 - 0.3072e-8 * t71 * t257) * t83 + (0.4e-2 * t86 * t24 * t240 - 0.32e-4 * t87 * t48 + 0.64e-4 * t90 * s0 * t48 - 0.512e-6 * t91 * t58 + 0.768e-6 * t94 * t39 * t58 - 0.3072e-8 * t95 * t257) * t100 + (0.4e-2 * t103 * t24 * t240 - 0.32e-4 * t104 * t48 + 0.64e-4 * t107 * s0 * t48 - 0.512e-6 * t108 * t58 + 0.768e-6 * t111 * t39 * t58 - 0.3072e-8 * t112 * t257) * t117))
  vsigma_0_ = 0.2e1 * r0 * t315
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
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = t17 / t19
  t23 = params_CC_0_[1]
  t24 = t23 * s0
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = r0 ** 2
  t29 = 0.1e1 / t19 / t27
  t30 = t26 * t29
  t34 = 0.1e1 + 0.4e-2 * s0 * t26 * t29
  t35 = 0.1e1 / t34
  t36 = t30 * t35
  t39 = params_CC_0_[2]
  t40 = s0 ** 2
  t41 = t39 * t40
  t42 = t27 ** 2
  t43 = t42 * r0
  t45 = 0.1e1 / t18 / t43
  t47 = t34 ** 2
  t48 = 0.1e1 / t47
  t49 = t25 * t45 * t48
  t52 = params_CC_0_[3]
  t53 = t40 * s0
  t54 = t52 * t53
  t55 = t42 ** 2
  t58 = 0.1e1 / t47 / t34
  t59 = 0.1e1 / t55 * t58
  t63 = params_CC_1_[1]
  t64 = t63 * s0
  t67 = params_CC_1_[2]
  t68 = t67 * t40
  t71 = params_CC_1_[3]
  t72 = t71 * t53
  t75 = params_CC_1_[0] + 0.4e-2 * t64 * t36 + 0.32e-4 * t68 * t49 + 0.256e-6 * t72 * t59
  t80 = f.my_piecewise3(t12, 0.1e1 / t13, 0.1e1 / t15)
  t83 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 / t18 * t25 * t80
  t84 = 0.1e1 / t83
  t87 = params_CC_2_[1]
  t88 = t87 * s0
  t91 = params_CC_2_[2]
  t92 = t91 * t40
  t95 = params_CC_2_[3]
  t96 = t95 * t53
  t99 = params_CC_2_[0] + 0.4e-2 * t88 * t36 + 0.32e-4 * t92 * t49 + 0.256e-6 * t96 * t59
  t100 = t83 ** 2
  t101 = 0.1e1 / t100
  t104 = params_CC_3_[1]
  t105 = t104 * s0
  t108 = params_CC_3_[2]
  t109 = t108 * t40
  t112 = params_CC_3_[3]
  t113 = t112 * t53
  t116 = params_CC_3_[0] + 0.4e-2 * t105 * t36 + 0.32e-4 * t109 * t49 + 0.256e-6 * t113 * t59
  t118 = 0.1e1 / t100 / t83
  t120 = params_CC_0_[0] + 0.4e-2 * t24 * t36 + 0.32e-4 * t41 * t49 + 0.256e-6 * t54 * t59 + t75 * t84 + t99 * t101 + t116 * t118
  t124 = t17 * t18
  t125 = t27 * r0
  t127 = 0.1e1 / t19 / t125
  t129 = t26 * t127 * t35
  t132 = t23 * t40
  t133 = t42 * t27
  t135 = 0.1e1 / t18 / t133
  t137 = t25 * t135 * t48
  t142 = t39 * t53
  t145 = 0.1e1 / t55 / r0 * t58
  t150 = t40 ** 2
  t151 = t52 * t150
  t155 = t47 ** 2
  t156 = 0.1e1 / t155
  t158 = 0.1e1 / t19 / t55 / t125 * t156 * t26
  t163 = t63 * t40
  t168 = t67 * t53
  t173 = t71 * t150
  t176 = -0.10666666666666666666666666666666666666666666666667e-1 * t64 * t129 + 0.85333333333333333333333333333333333333333333333336e-4 * t163 * t137 - 0.17066666666666666666666666666666666666666666666667e-3 * t68 * t137 + 0.13653333333333333333333333333333333333333333333334e-5 * t168 * t145 - 0.2048e-5 * t72 * t145 + 0.81920000000000000000000000000000000000000000000003e-8 * t173 * t158
  t178 = t75 * t101
  t182 = 0.1e1 / t18 / r0 * t25 * t80
  t187 = t87 * t40
  t192 = t91 * t53
  t197 = t95 * t150
  t200 = -0.10666666666666666666666666666666666666666666666667e-1 * t88 * t129 + 0.85333333333333333333333333333333333333333333333336e-4 * t187 * t137 - 0.17066666666666666666666666666666666666666666666667e-3 * t92 * t137 + 0.13653333333333333333333333333333333333333333333334e-5 * t192 * t145 - 0.2048e-5 * t96 * t145 + 0.81920000000000000000000000000000000000000000000003e-8 * t197 * t158
  t202 = t99 * t118
  t207 = t104 * t40
  t212 = t108 * t53
  t217 = t112 * t150
  t220 = -0.10666666666666666666666666666666666666666666666667e-1 * t105 * t129 + 0.85333333333333333333333333333333333333333333333336e-4 * t207 * t137 - 0.17066666666666666666666666666666666666666666666667e-3 * t109 * t137 + 0.13653333333333333333333333333333333333333333333334e-5 * t212 * t145 - 0.2048e-5 * t113 * t145 + 0.81920000000000000000000000000000000000000000000003e-8 * t217 * t158
  t222 = t100 ** 2
  t223 = 0.1e1 / t222
  t224 = t116 * t223
  t227 = -0.10666666666666666666666666666666666666666666666667e-1 * t24 * t129 + 0.85333333333333333333333333333333333333333333333336e-4 * t132 * t137 - 0.17066666666666666666666666666666666666666666666667e-3 * t41 * t137 + 0.13653333333333333333333333333333333333333333333334e-5 * t142 * t145 - 0.2048e-5 * t54 * t145 + 0.81920000000000000000000000000000000000000000000003e-8 * t151 * t158 + t176 * t84 + 0.13333333333333333333333333333333333333333333333333e0 * t178 * t182 + t200 * t101 + 0.26666666666666666666666666666666666666666666666666e0 * t202 * t182 + t220 * t118 + 0.39999999999999999999999999999999999999999999999999e0 * t224 * t182
  t232 = f.my_piecewise3(t2, 0, -t6 * t21 * t120 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t124 * t227)
  t246 = t26 / t19 / t42 * t35
  t249 = t42 * t125
  t253 = t25 / t18 / t249 * t48
  t257 = t55 * t27
  t259 = 0.1e1 / t257 * t58
  t271 = 0.1e1 / t19 / t55 / t42 * t156 * t26
  t278 = t150 * s0
  t284 = 0.1e1 / t155 / t34
  t286 = 0.1e1 / t18 / t55 / t249 * t284 * t25
  t349 = 0.1e1 / t18 / t27 * t25 * t80
  t373 = t80 ** 2
  t374 = t30 * t373
  t391 = -0.76800000000000000000000000000000000000000000000003e-3 * t132 * t253 + 0.43690666666666666666666666666666666666666666666670e-7 * t39 * t150 * t271 + 0.18432e-4 * t54 * t259 - 0.16110933333333333333333333333333333333333333333334e-6 * t151 * t271 + 0.69905066666666666666666666666666666666666666666671e-9 * t52 * t278 * t286 + 0.26666666666666666666666666666666666666666666666666e0 * t176 * t101 * t182 + 0.35555555555555555555555555555555555555555555555554e-1 * t75 * t118 * t374 + 0.53333333333333333333333333333333333333333333333332e0 * t200 * t118 * t182 + 0.10666666666666666666666666666666666666666666666666e0 * t99 * t223 * t374 + 0.79999999999999999999999999999999999999999999999998e0 * t220 * t223 * t182 + 0.21333333333333333333333333333333333333333333333332e0 * t116 / t222 / t83 * t374
  t397 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t120 / 0.12e2 - t6 * t21 * t227 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t124 * ((0.39111111111111111111111111111111111111111111111112e-1 * t64 * t246 - 0.76800000000000000000000000000000000000000000000003e-3 * t163 * t253 + 0.36408888888888888888888888888888888888888888888891e-5 * t63 * t53 * t259 + 0.10808888888888888888888888888888888888888888888889e-2 * t68 * t253 - 0.19569777777777777777777777777777777777777777777779e-4 * t168 * t259 + 0.43690666666666666666666666666666666666666666666670e-7 * t67 * t150 * t271 + 0.18432e-4 * t72 * t259 - 0.16110933333333333333333333333333333333333333333334e-6 * t173 * t271 + 0.69905066666666666666666666666666666666666666666671e-9 * t71 * t278 * t286) * t84 + (0.39111111111111111111111111111111111111111111111112e-1 * t88 * t246 - 0.76800000000000000000000000000000000000000000000003e-3 * t187 * t253 + 0.36408888888888888888888888888888888888888888888891e-5 * t87 * t53 * t259 + 0.10808888888888888888888888888888888888888888888889e-2 * t92 * t253 - 0.19569777777777777777777777777777777777777777777779e-4 * t192 * t259 + 0.43690666666666666666666666666666666666666666666670e-7 * t91 * t150 * t271 + 0.18432e-4 * t96 * t259 - 0.16110933333333333333333333333333333333333333333334e-6 * t197 * t271 + 0.69905066666666666666666666666666666666666666666671e-9 * t95 * t278 * t286) * t101 + (0.39111111111111111111111111111111111111111111111112e-1 * t105 * t246 - 0.76800000000000000000000000000000000000000000000003e-3 * t207 * t253 + 0.36408888888888888888888888888888888888888888888891e-5 * t104 * t53 * t259 + 0.10808888888888888888888888888888888888888888888889e-2 * t109 * t253 - 0.19569777777777777777777777777777777777777777777779e-4 * t212 * t259 + 0.43690666666666666666666666666666666666666666666670e-7 * t108 * t150 * t271 + 0.18432e-4 * t113 * t259 - 0.16110933333333333333333333333333333333333333333334e-6 * t217 * t271 + 0.69905066666666666666666666666666666666666666666671e-9 * t112 * t278 * t286) * t118 + 0.36408888888888888888888888888888888888888888888891e-5 * t23 * t53 * t259 - 0.19569777777777777777777777777777777777777777777779e-4 * t142 * t259 + 0.39111111111111111111111111111111111111111111111112e-1 * t24 * t246 + 0.10808888888888888888888888888888888888888888888889e-2 * t41 * t253 - 0.17777777777777777777777777777777777777777777777777e0 * t178 * t349 - 0.35555555555555555555555555555555555555555555555555e0 * t202 * t349 - 0.53333333333333333333333333333333333333333333333332e0 * t224 * t349 + t391))
  v2rho2_0_ = 0.2e1 * r0 * t397 + 0.4e1 * t232
  t400 = t23 * t26
  t401 = t29 * t35
  t406 = t39 * s0
  t411 = t52 * t40
  t417 = 0.1e1 / t19 / t257 * t156 * t26
  t420 = t63 * t26
  t425 = t67 * s0
  t430 = t71 * t40
  t435 = 0.4e-2 * t420 * t401 - 0.32e-4 * t64 * t49 + 0.64e-4 * t425 * t49 - 0.512e-6 * t68 * t59 + 0.768e-6 * t430 * t59 - 0.3072e-8 * t72 * t417
  t437 = t87 * t26
  t442 = t91 * s0
  t447 = t95 * t40
  t452 = 0.4e-2 * t437 * t401 - 0.32e-4 * t88 * t49 + 0.64e-4 * t442 * t49 - 0.512e-6 * t92 * t59 + 0.768e-6 * t447 * t59 - 0.3072e-8 * t96 * t417
  t454 = t104 * t26
  t459 = t108 * s0
  t464 = t112 * t40
  t469 = 0.4e-2 * t454 * t401 - 0.32e-4 * t105 * t49 + 0.64e-4 * t459 * t49 - 0.512e-6 * t109 * t59 + 0.768e-6 * t464 * t59 - 0.3072e-8 * t113 * t417
  t471 = 0.4e-2 * t400 * t401 - 0.32e-4 * t24 * t49 + 0.64e-4 * t406 * t49 - 0.512e-6 * t41 * t59 + 0.768e-6 * t411 * t59 - 0.3072e-8 * t54 * t417 + t435 * t84 + t452 * t101 + t469 * t118
  t475 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t124 * t471)
  t479 = t127 * t35
  t482 = t23 * t25
  t484 = t135 * t48 * s0
  t503 = 0.1e1 / t18 / t55 / t133 * t284 * t25
  t508 = t63 * t25
  t532 = t87 * t25
  t556 = t104 * t25
  t578 = -0.10666666666666666666666666666666666666666666666667e-1 * t400 * t479 + 0.25600000000000000000000000000000000000000000000001e-3 * t482 * t484 - 0.13653333333333333333333333333333333333333333333334e-5 * t132 * t145 - 0.34133333333333333333333333333333333333333333333333e-3 * t406 * t137 + 0.68266666666666666666666666666666666666666666666668e-5 * t41 * t145 - 0.16384000000000000000000000000000000000000000000001e-7 * t142 * t158 - 0.6144e-5 * t411 * t145 + 0.57344000000000000000000000000000000000000000000001e-7 * t54 * t158 - 0.26214400000000000000000000000000000000000000000001e-9 * t151 * t503 + (-0.10666666666666666666666666666666666666666666666667e-1 * t420 * t479 + 0.25600000000000000000000000000000000000000000000001e-3 * t508 * t484 - 0.13653333333333333333333333333333333333333333333334e-5 * t163 * t145 - 0.34133333333333333333333333333333333333333333333333e-3 * t425 * t137 + 0.68266666666666666666666666666666666666666666666668e-5 * t68 * t145 - 0.16384000000000000000000000000000000000000000000001e-7 * t168 * t158 - 0.6144e-5 * t430 * t145 + 0.57344000000000000000000000000000000000000000000001e-7 * t72 * t158 - 0.26214400000000000000000000000000000000000000000001e-9 * t173 * t503) * t84 + 0.13333333333333333333333333333333333333333333333333e0 * t435 * t101 * t182 + (-0.10666666666666666666666666666666666666666666666667e-1 * t437 * t479 + 0.25600000000000000000000000000000000000000000000001e-3 * t532 * t484 - 0.13653333333333333333333333333333333333333333333334e-5 * t187 * t145 - 0.34133333333333333333333333333333333333333333333333e-3 * t442 * t137 + 0.68266666666666666666666666666666666666666666666668e-5 * t92 * t145 - 0.16384000000000000000000000000000000000000000000001e-7 * t192 * t158 - 0.6144e-5 * t447 * t145 + 0.57344000000000000000000000000000000000000000000001e-7 * t96 * t158 - 0.26214400000000000000000000000000000000000000000001e-9 * t197 * t503) * t101 + 0.26666666666666666666666666666666666666666666666666e0 * t452 * t118 * t182 + (-0.10666666666666666666666666666666666666666666666667e-1 * t454 * t479 + 0.25600000000000000000000000000000000000000000000001e-3 * t556 * t484 - 0.13653333333333333333333333333333333333333333333334e-5 * t207 * t145 - 0.34133333333333333333333333333333333333333333333333e-3 * t459 * t137 + 0.68266666666666666666666666666666666666666666666668e-5 * t109 * t145 - 0.16384000000000000000000000000000000000000000000001e-7 * t212 * t158 - 0.6144e-5 * t464 * t145 + 0.57344000000000000000000000000000000000000000000001e-7 * t113 * t158 - 0.26214400000000000000000000000000000000000000000001e-9 * t217 * t503) * t118 + 0.39999999999999999999999999999999999999999999999999e0 * t469 * t223 * t182
  t583 = f.my_piecewise3(t2, 0, -t6 * t21 * t471 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t124 * t578)
  v2rhosigma_0_ = 0.2e1 * r0 * t583 + 0.2e1 * t475
  t586 = t45 * t48
  t607 = 0.1e1 / t18 / t55 / t43 * t284 * t25
  t670 = -0.64e-4 * t482 * t586 + 0.512e-6 * t24 * t59 + 0.64e-4 * t39 * t25 * t586 - 0.2048e-5 * t406 * t59 + 0.6144e-8 * t41 * t417 + 0.1536e-5 * t52 * s0 * t59 - 0.18432e-7 * t411 * t417 + 0.98304e-10 * t54 * t607 + (-0.64e-4 * t508 * t586 + 0.512e-6 * t64 * t59 + 0.64e-4 * t67 * t25 * t586 - 0.2048e-5 * t425 * t59 + 0.6144e-8 * t68 * t417 + 0.1536e-5 * t71 * s0 * t59 - 0.18432e-7 * t430 * t417 + 0.98304e-10 * t72 * t607) * t84 + (-0.64e-4 * t532 * t586 + 0.512e-6 * t88 * t59 + 0.64e-4 * t91 * t25 * t586 - 0.2048e-5 * t442 * t59 + 0.6144e-8 * t92 * t417 + 0.1536e-5 * t95 * s0 * t59 - 0.18432e-7 * t447 * t417 + 0.98304e-10 * t96 * t607) * t101 + (-0.64e-4 * t556 * t586 + 0.512e-6 * t105 * t59 + 0.64e-4 * t108 * t25 * t586 - 0.2048e-5 * t459 * t59 + 0.6144e-8 * t109 * t417 + 0.1536e-5 * t112 * s0 * t59 - 0.18432e-7 * t464 * t417 + 0.98304e-10 * t113 * t607) * t118
  t674 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t124 * t670)
  v2sigma2_0_ = 0.2e1 * r0 * t674
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
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t22 = t17 / t19 / r0
  t24 = params.CC_0_[1]
  t25 = t24 * s0
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = r0 ** 2
  t30 = 0.1e1 / t19 / t28
  t31 = t27 * t30
  t35 = 0.1e1 + 0.4e-2 * s0 * t27 * t30
  t36 = 0.1e1 / t35
  t37 = t31 * t36
  t40 = params.CC_0_[2]
  t41 = s0 ** 2
  t42 = t40 * t41
  t43 = t28 ** 2
  t44 = t43 * r0
  t48 = t35 ** 2
  t49 = 0.1e1 / t48
  t50 = t26 / t18 / t44 * t49
  t53 = params.CC_0_[3]
  t54 = t41 * s0
  t55 = t53 * t54
  t56 = t43 ** 2
  t59 = 0.1e1 / t48 / t35
  t60 = 0.1e1 / t56 * t59
  t64 = params.CC_1_[1]
  t65 = t64 * s0
  t68 = params.CC_1_[2]
  t69 = t68 * t41
  t72 = params.CC_1_[3]
  t73 = t72 * t54
  t76 = params.CC_1_[0] + 0.4e-2 * t65 * t37 + 0.32e-4 * t69 * t50 + 0.256e-6 * t73 * t60
  t81 = f.my_piecewise3(t12, 0.1e1 / t13, 0.1e1 / t15)
  t84 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 / t18 * t26 * t81
  t85 = 0.1e1 / t84
  t88 = params.CC_2_[1]
  t89 = t88 * s0
  t92 = params.CC_2_[2]
  t93 = t92 * t41
  t96 = params.CC_2_[3]
  t97 = t96 * t54
  t100 = params.CC_2_[0] + 0.4e-2 * t89 * t37 + 0.32e-4 * t93 * t50 + 0.256e-6 * t97 * t60
  t101 = t84 ** 2
  t102 = 0.1e1 / t101
  t105 = params.CC_3_[1]
  t106 = t105 * s0
  t109 = params.CC_3_[2]
  t110 = t109 * t41
  t113 = params.CC_3_[3]
  t114 = t113 * t54
  t117 = params.CC_3_[0] + 0.4e-2 * t106 * t37 + 0.32e-4 * t110 * t50 + 0.256e-6 * t114 * t60
  t119 = 0.1e1 / t101 / t84
  t121 = params.CC_0_[0] + 0.4e-2 * t25 * t37 + 0.32e-4 * t42 * t50 + 0.256e-6 * t55 * t60 + t76 * t85 + t100 * t102 + t117 * t119
  t126 = t17 / t19
  t127 = t28 * r0
  t130 = t27 / t19 / t127
  t131 = t130 * t36
  t134 = t24 * t41
  t139 = t26 / t18 / t43 / t28 * t49
  t144 = t40 * t54
  t147 = 0.1e1 / t56 / r0 * t59
  t152 = t41 ** 2
  t153 = t53 * t152
  t154 = t56 * t127
  t157 = t48 ** 2
  t158 = 0.1e1 / t157
  t160 = 0.1e1 / t19 / t154 * t158 * t27
  t165 = t64 * t41
  t170 = t68 * t54
  t175 = t72 * t152
  t178 = -0.10666666666666666666666666666666666666666666666667e-1 * t65 * t131 + 0.85333333333333333333333333333333333333333333333336e-4 * t165 * t139 - 0.17066666666666666666666666666666666666666666666667e-3 * t69 * t139 + 0.13653333333333333333333333333333333333333333333334e-5 * t170 * t147 - 0.2048e-5 * t73 * t147 + 0.81920000000000000000000000000000000000000000000003e-8 * t175 * t160
  t180 = t76 * t102
  t184 = 0.1e1 / t18 / r0 * t26 * t81
  t189 = t88 * t41
  t194 = t92 * t54
  t199 = t96 * t152
  t202 = -0.10666666666666666666666666666666666666666666666667e-1 * t89 * t131 + 0.85333333333333333333333333333333333333333333333336e-4 * t189 * t139 - 0.17066666666666666666666666666666666666666666666667e-3 * t93 * t139 + 0.13653333333333333333333333333333333333333333333334e-5 * t194 * t147 - 0.2048e-5 * t97 * t147 + 0.81920000000000000000000000000000000000000000000003e-8 * t199 * t160
  t204 = t100 * t119
  t209 = t105 * t41
  t214 = t109 * t54
  t219 = t113 * t152
  t222 = -0.10666666666666666666666666666666666666666666666667e-1 * t106 * t131 + 0.85333333333333333333333333333333333333333333333336e-4 * t209 * t139 - 0.17066666666666666666666666666666666666666666666667e-3 * t110 * t139 + 0.13653333333333333333333333333333333333333333333334e-5 * t214 * t147 - 0.2048e-5 * t114 * t147 + 0.81920000000000000000000000000000000000000000000003e-8 * t219 * t160
  t224 = t101 ** 2
  t225 = 0.1e1 / t224
  t226 = t117 * t225
  t229 = -0.10666666666666666666666666666666666666666666666667e-1 * t25 * t131 + 0.85333333333333333333333333333333333333333333333336e-4 * t134 * t139 - 0.17066666666666666666666666666666666666666666666667e-3 * t42 * t139 + 0.13653333333333333333333333333333333333333333333334e-5 * t144 * t147 - 0.2048e-5 * t55 * t147 + 0.81920000000000000000000000000000000000000000000003e-8 * t153 * t160 + t178 * t85 + 0.13333333333333333333333333333333333333333333333333e0 * t180 * t184 + t202 * t102 + 0.26666666666666666666666666666666666666666666666666e0 * t204 * t184 + t222 * t119 + 0.39999999999999999999999999999999999999999999999999e0 * t226 * t184
  t233 = t17 * t18
  t237 = t27 / t19 / t43 * t36
  t240 = t43 * t127
  t244 = t26 / t18 / t240 * t49
  t247 = t64 * t54
  t250 = 0.1e1 / t56 / t28 * t59
  t257 = t68 * t152
  t262 = 0.1e1 / t19 / t56 / t43 * t158 * t27
  t269 = t152 * s0
  t270 = t72 * t269
  t275 = 0.1e1 / t157 / t35
  t277 = 0.1e1 / t18 / t56 / t240 * t275 * t26
  t280 = 0.39111111111111111111111111111111111111111111111112e-1 * t65 * t237 - 0.76800000000000000000000000000000000000000000000003e-3 * t165 * t244 + 0.36408888888888888888888888888888888888888888888891e-5 * t247 * t250 + 0.10808888888888888888888888888888888888888888888889e-2 * t69 * t244 - 0.19569777777777777777777777777777777777777777777779e-4 * t170 * t250 + 0.43690666666666666666666666666666666666666666666670e-7 * t257 * t262 + 0.18432e-4 * t73 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t175 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t270 * t277
  t286 = t88 * t54
  t293 = t92 * t152
  t300 = t96 * t269
  t303 = 0.39111111111111111111111111111111111111111111111112e-1 * t89 * t237 - 0.76800000000000000000000000000000000000000000000003e-3 * t189 * t244 + 0.36408888888888888888888888888888888888888888888891e-5 * t286 * t250 + 0.10808888888888888888888888888888888888888888888889e-2 * t93 * t244 - 0.19569777777777777777777777777777777777777777777779e-4 * t194 * t250 + 0.43690666666666666666666666666666666666666666666670e-7 * t293 * t262 + 0.18432e-4 * t97 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t199 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t300 * t277
  t309 = t105 * t54
  t316 = t109 * t152
  t323 = t113 * t269
  t326 = 0.39111111111111111111111111111111111111111111111112e-1 * t106 * t237 - 0.76800000000000000000000000000000000000000000000003e-3 * t209 * t244 + 0.36408888888888888888888888888888888888888888888891e-5 * t309 * t250 + 0.10808888888888888888888888888888888888888888888889e-2 * t110 * t244 - 0.19569777777777777777777777777777777777777777777779e-4 * t214 * t250 + 0.43690666666666666666666666666666666666666666666670e-7 * t316 * t262 + 0.18432e-4 * t114 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t219 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t323 * t277
  t328 = t24 * t54
  t340 = 0.1e1 / t18 / t28 * t26 * t81
  t350 = t40 * t152
  t357 = t53 * t269
  t360 = t178 * t102
  t363 = t76 * t119
  t364 = t81 ** 2
  t365 = t31 * t364
  t368 = t202 * t119
  t371 = t100 * t225
  t374 = t222 * t225
  t378 = 0.1e1 / t224 / t84
  t379 = t117 * t378
  t382 = -0.76800000000000000000000000000000000000000000000003e-3 * t134 * t244 + 0.43690666666666666666666666666666666666666666666670e-7 * t350 * t262 + 0.18432e-4 * t55 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t153 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t357 * t277 + 0.26666666666666666666666666666666666666666666666666e0 * t360 * t184 + 0.35555555555555555555555555555555555555555555555554e-1 * t363 * t365 + 0.53333333333333333333333333333333333333333333333332e0 * t368 * t184 + 0.10666666666666666666666666666666666666666666666666e0 * t371 * t365 + 0.79999999999999999999999999999999999999999999999998e0 * t374 * t184 + 0.21333333333333333333333333333333333333333333333332e0 * t379 * t365
  t383 = t280 * t85 + t303 * t102 + t326 * t119 + 0.36408888888888888888888888888888888888888888888891e-5 * t328 * t250 - 0.19569777777777777777777777777777777777777777777779e-4 * t144 * t250 + 0.39111111111111111111111111111111111111111111111112e-1 * t25 * t237 + 0.10808888888888888888888888888888888888888888888889e-2 * t42 * t244 - 0.17777777777777777777777777777777777777777777777777e0 * t180 * t340 - 0.35555555555555555555555555555555555555555555555555e0 * t204 * t340 - 0.53333333333333333333333333333333333333333333333332e0 * t226 * t340 + t382
  t388 = f.my_piecewise3(t2, 0, t6 * t22 * t121 / 0.12e2 - t6 * t126 * t229 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t233 * t383)
  t408 = 0.1e1 / t19 / t56 / t44 * t158 * t27
  t416 = t26 / t18 / t56 * t49
  t426 = t56 ** 2
  t430 = 0.1e1 / t18 / t426 * t275 * t26
  t436 = 0.1e1 / t18 / t127 * t26 * t81
  t442 = t27 / t19 / t44 * t36
  t451 = t130 * t364
  t461 = 0.12000000000000000000000000000000000000000000000000e1 * t326 * t225 * t184 + 0.11650844444444444444444444444444444444444444444445e-6 * t24 * t152 * t408 - 0.11796480000000000000000000000000000000000000000001e-5 * t350 * t408 + 0.64663703703703703703703703703703703703703703703706e-2 * t134 * t416 + 0.39999999999999999999999999999999999999999999999999e0 * t280 * t102 * t184 + 0.31999999999999999999999999999999999999999999999998e0 * t202 * t225 * t365 + 0.37282702222222222222222222222222222222222222222226e-8 * t40 * t269 * t430 + 0.12444444444444444444444444444444444444444444444444e1 * t226 * t436 - 0.18251851851851851851851851851851851851851851851852e0 * t25 * t442 - 0.79265185185185185185185185185185185185185185185186e-2 * t42 * t416 + 0.41481481481481481481481481481481481481481481481480e0 * t180 * t436 - 0.10666666666666666666666666666666666666666666666666e1 * t368 * t340 - 0.42666666666666666666666666666666666666666666666665e0 * t371 * t451 - 0.15999999999999999999999999999999999999999999999999e1 * t374 * t340 - 0.85333333333333333333333333333333333333333333333328e0 * t379 * t451 + 0.79999999999999999999999999999999999999999999999998e0 * t303 * t119 * t184
  t483 = 0.1e1 / t154 * t59
  t504 = t152 * t41
  t510 = 0.1e1 / t426 / t127 / t157 / t48
  t513 = -0.18251851851851851851851851851851851851851851851852e0 * t89 * t442 + 0.64663703703703703703703703703703703703703703703706e-2 * t189 * t416 - 0.69176888888888888888888888888888888888888888888893e-4 * t286 * t483 + 0.11650844444444444444444444444444444444444444444445e-6 * t88 * t152 * t408 - 0.79265185185185185185185185185185185185185185185186e-2 * t93 * t416 + 0.24181570370370370370370370370370370370370370370372e-3 * t194 * t483 - 0.11796480000000000000000000000000000000000000000001e-5 * t293 * t408 + 0.37282702222222222222222222222222222222222222222226e-8 * t92 * t269 * t430 - 0.184320e-3 * t97 * t483 + 0.26305422222222222222222222222222222222222222222223e-5 * t199 * t408 - 0.24466773333333333333333333333333333333333333333335e-7 * t300 * t430 + 0.74565404444444444444444444444444444444444444444451e-10 * t96 * t504 * t510
  t542 = -0.18251851851851851851851851851851851851851851851852e0 * t106 * t442 + 0.64663703703703703703703703703703703703703703703706e-2 * t209 * t416 - 0.69176888888888888888888888888888888888888888888893e-4 * t309 * t483 + 0.11650844444444444444444444444444444444444444444445e-6 * t105 * t152 * t408 - 0.79265185185185185185185185185185185185185185185186e-2 * t110 * t416 + 0.24181570370370370370370370370370370370370370370372e-3 * t214 * t483 - 0.11796480000000000000000000000000000000000000000001e-5 * t316 * t408 + 0.37282702222222222222222222222222222222222222222226e-8 * t109 * t269 * t430 - 0.184320e-3 * t114 * t483 + 0.26305422222222222222222222222222222222222222222223e-5 * t219 * t408 - 0.24466773333333333333333333333333333333333333333335e-7 * t323 * t430 + 0.74565404444444444444444444444444444444444444444451e-10 * t113 * t504 * t510
  t571 = -0.18251851851851851851851851851851851851851851851852e0 * t65 * t442 + 0.64663703703703703703703703703703703703703703703706e-2 * t165 * t416 - 0.69176888888888888888888888888888888888888888888893e-4 * t247 * t483 + 0.11650844444444444444444444444444444444444444444445e-6 * t64 * t152 * t408 - 0.79265185185185185185185185185185185185185185185186e-2 * t69 * t416 + 0.24181570370370370370370370370370370370370370370372e-3 * t170 * t483 - 0.11796480000000000000000000000000000000000000000001e-5 * t257 * t408 + 0.37282702222222222222222222222222222222222222222226e-8 * t68 * t269 * t430 - 0.184320e-3 * t73 * t483 + 0.26305422222222222222222222222222222222222222222223e-5 * t175 * t408 - 0.24466773333333333333333333333333333333333333333335e-7 * t270 * t430 + 0.74565404444444444444444444444444444444444444444451e-10 * t72 * t504 * t510
  t576 = 0.1e1 / t43 * t364 * t81
  t596 = 0.26305422222222222222222222222222222222222222222223e-5 * t153 * t408 - 0.24466773333333333333333333333333333333333333333335e-7 * t357 * t430 + 0.10666666666666666666666666666666666666666666666666e0 * t178 * t119 * t365 - 0.53333333333333333333333333333333333333333333333332e0 * t360 * t340 - 0.14222222222222222222222222222222222222222222222222e0 * t363 * t451 + 0.63999999999999999999999999999999999999999999999997e0 * t222 * t378 * t365 + 0.82962962962962962962962962962962962962962962962962e0 * t204 * t436 + t513 * t102 + t542 * t119 + t571 * t85 + 0.11377777777777777777777777777777777777777777777776e0 * t100 * t378 * t576 - 0.184320e-3 * t55 * t483 - 0.69176888888888888888888888888888888888888888888893e-4 * t328 * t483 + 0.24181570370370370370370370370370370370370370370372e-3 * t144 * t483 + 0.28444444444444444444444444444444444444444444444442e0 * t117 / t224 / t101 * t576 + 0.74565404444444444444444444444444444444444444444451e-10 * t53 * t504 * t510 + 0.28444444444444444444444444444444444444444444444442e-1 * t76 * t225 * t576
  t602 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t30 * t121 + t6 * t22 * t229 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t126 * t383 - 0.3e1 / 0.8e1 * t6 * t233 * (t461 + t596))
  v3rho3_0_ = 0.2e1 * r0 * t602 + 0.6e1 * t388

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
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t22 = 0.1e1 / t20 / t18
  t23 = t17 * t22
  t25 = params.CC_0_[1]
  t26 = t25 * s0
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = t28 * t22
  t33 = 0.1e1 + 0.4e-2 * s0 * t28 * t22
  t34 = 0.1e1 / t33
  t35 = t29 * t34
  t38 = params.CC_0_[2]
  t39 = s0 ** 2
  t40 = t38 * t39
  t41 = t18 ** 2
  t42 = t41 * r0
  t44 = 0.1e1 / t19 / t42
  t46 = t33 ** 2
  t47 = 0.1e1 / t46
  t48 = t27 * t44 * t47
  t51 = params.CC_0_[3]
  t52 = t39 * s0
  t53 = t51 * t52
  t54 = t41 ** 2
  t56 = t46 * t33
  t57 = 0.1e1 / t56
  t58 = 0.1e1 / t54 * t57
  t62 = params.CC_1_[1]
  t63 = t62 * s0
  t66 = params.CC_1_[2]
  t67 = t66 * t39
  t70 = params.CC_1_[3]
  t71 = t70 * t52
  t74 = params.CC_1_[0] + 0.4e-2 * t63 * t35 + 0.32e-4 * t67 * t48 + 0.256e-6 * t71 * t58
  t79 = f.my_piecewise3(t12, 0.1e1 / t13, 0.1e1 / t15)
  t82 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 / t19 * t27 * t79
  t83 = 0.1e1 / t82
  t86 = params.CC_2_[1]
  t87 = t86 * s0
  t90 = params.CC_2_[2]
  t91 = t90 * t39
  t94 = params.CC_2_[3]
  t95 = t94 * t52
  t98 = params.CC_2_[0] + 0.4e-2 * t87 * t35 + 0.32e-4 * t91 * t48 + 0.256e-6 * t95 * t58
  t99 = t82 ** 2
  t100 = 0.1e1 / t99
  t103 = params.CC_3_[1]
  t104 = t103 * s0
  t107 = params.CC_3_[2]
  t108 = t107 * t39
  t111 = params.CC_3_[3]
  t112 = t111 * t52
  t115 = params.CC_3_[0] + 0.4e-2 * t104 * t35 + 0.32e-4 * t108 * t48 + 0.256e-6 * t112 * t58
  t116 = t99 * t82
  t117 = 0.1e1 / t116
  t119 = params.CC_0_[0] + 0.4e-2 * t26 * t35 + 0.32e-4 * t40 * t48 + 0.256e-6 * t53 * t58 + t74 * t83 + t98 * t100 + t115 * t117
  t125 = t17 / t20 / r0
  t126 = t18 * r0
  t128 = 0.1e1 / t20 / t126
  t129 = t28 * t128
  t130 = t129 * t34
  t133 = t25 * t39
  t134 = t41 * t18
  t138 = t27 / t19 / t134 * t47
  t143 = t38 * t52
  t144 = t54 * r0
  t146 = 0.1e1 / t144 * t57
  t151 = t39 ** 2
  t152 = t51 * t151
  t153 = t54 * t126
  t156 = t46 ** 2
  t157 = 0.1e1 / t156
  t159 = 0.1e1 / t20 / t153 * t157 * t28
  t164 = t62 * t39
  t169 = t66 * t52
  t174 = t70 * t151
  t177 = -0.10666666666666666666666666666666666666666666666667e-1 * t63 * t130 + 0.85333333333333333333333333333333333333333333333336e-4 * t164 * t138 - 0.17066666666666666666666666666666666666666666666667e-3 * t67 * t138 + 0.13653333333333333333333333333333333333333333333334e-5 * t169 * t146 - 0.2048e-5 * t71 * t146 + 0.81920000000000000000000000000000000000000000000003e-8 * t174 * t159
  t179 = t74 * t100
  t183 = 0.1e1 / t19 / r0 * t27 * t79
  t188 = t86 * t39
  t193 = t90 * t52
  t198 = t94 * t151
  t201 = -0.10666666666666666666666666666666666666666666666667e-1 * t87 * t130 + 0.85333333333333333333333333333333333333333333333336e-4 * t188 * t138 - 0.17066666666666666666666666666666666666666666666667e-3 * t91 * t138 + 0.13653333333333333333333333333333333333333333333334e-5 * t193 * t146 - 0.2048e-5 * t95 * t146 + 0.81920000000000000000000000000000000000000000000003e-8 * t198 * t159
  t203 = t98 * t117
  t208 = t103 * t39
  t213 = t107 * t52
  t218 = t111 * t151
  t221 = -0.10666666666666666666666666666666666666666666666667e-1 * t104 * t130 + 0.85333333333333333333333333333333333333333333333336e-4 * t208 * t138 - 0.17066666666666666666666666666666666666666666666667e-3 * t108 * t138 + 0.13653333333333333333333333333333333333333333333334e-5 * t213 * t146 - 0.2048e-5 * t112 * t146 + 0.81920000000000000000000000000000000000000000000003e-8 * t218 * t159
  t223 = t99 ** 2
  t224 = 0.1e1 / t223
  t225 = t115 * t224
  t228 = -0.10666666666666666666666666666666666666666666666667e-1 * t26 * t130 + 0.85333333333333333333333333333333333333333333333336e-4 * t133 * t138 - 0.17066666666666666666666666666666666666666666666667e-3 * t40 * t138 + 0.13653333333333333333333333333333333333333333333334e-5 * t143 * t146 - 0.2048e-5 * t53 * t146 + 0.81920000000000000000000000000000000000000000000003e-8 * t152 * t159 + t177 * t83 + 0.13333333333333333333333333333333333333333333333333e0 * t179 * t183 + t201 * t100 + 0.26666666666666666666666666666666666666666666666666e0 * t203 * t183 + t221 * t117 + 0.39999999999999999999999999999999999999999999999999e0 * t225 * t183
  t233 = t17 / t20
  t236 = t28 / t20 / t41
  t237 = t236 * t34
  t240 = t41 * t126
  t244 = t27 / t19 / t240 * t47
  t247 = t62 * t52
  t250 = 0.1e1 / t54 / t18 * t57
  t257 = t66 * t151
  t258 = t54 * t41
  t262 = 0.1e1 / t20 / t258 * t157 * t28
  t269 = t151 * s0
  t270 = t70 * t269
  t275 = 0.1e1 / t156 / t33
  t277 = 0.1e1 / t19 / t54 / t240 * t275 * t27
  t280 = 0.39111111111111111111111111111111111111111111111112e-1 * t63 * t237 - 0.76800000000000000000000000000000000000000000000003e-3 * t164 * t244 + 0.36408888888888888888888888888888888888888888888891e-5 * t247 * t250 + 0.10808888888888888888888888888888888888888888888889e-2 * t67 * t244 - 0.19569777777777777777777777777777777777777777777779e-4 * t169 * t250 + 0.43690666666666666666666666666666666666666666666670e-7 * t257 * t262 + 0.18432e-4 * t71 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t174 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t270 * t277
  t286 = t86 * t52
  t293 = t90 * t151
  t300 = t94 * t269
  t303 = 0.39111111111111111111111111111111111111111111111112e-1 * t87 * t237 - 0.76800000000000000000000000000000000000000000000003e-3 * t188 * t244 + 0.36408888888888888888888888888888888888888888888891e-5 * t286 * t250 + 0.10808888888888888888888888888888888888888888888889e-2 * t91 * t244 - 0.19569777777777777777777777777777777777777777777779e-4 * t193 * t250 + 0.43690666666666666666666666666666666666666666666670e-7 * t293 * t262 + 0.18432e-4 * t95 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t198 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t300 * t277
  t309 = t103 * t52
  t316 = t107 * t151
  t323 = t111 * t269
  t326 = 0.39111111111111111111111111111111111111111111111112e-1 * t104 * t237 - 0.76800000000000000000000000000000000000000000000003e-3 * t208 * t244 + 0.36408888888888888888888888888888888888888888888891e-5 * t309 * t250 + 0.10808888888888888888888888888888888888888888888889e-2 * t108 * t244 - 0.19569777777777777777777777777777777777777777777779e-4 * t213 * t250 + 0.43690666666666666666666666666666666666666666666670e-7 * t316 * t262 + 0.18432e-4 * t112 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t218 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t323 * t277
  t328 = t25 * t52
  t340 = 0.1e1 / t19 / t18 * t27 * t79
  t350 = t38 * t151
  t357 = t51 * t269
  t360 = t177 * t100
  t363 = t74 * t117
  t364 = t79 ** 2
  t365 = t29 * t364
  t368 = t201 * t117
  t371 = t98 * t224
  t374 = t221 * t224
  t378 = 0.1e1 / t223 / t82
  t379 = t115 * t378
  t382 = -0.76800000000000000000000000000000000000000000000003e-3 * t133 * t244 + 0.43690666666666666666666666666666666666666666666670e-7 * t350 * t262 + 0.18432e-4 * t53 * t250 - 0.16110933333333333333333333333333333333333333333334e-6 * t152 * t262 + 0.69905066666666666666666666666666666666666666666671e-9 * t357 * t277 + 0.26666666666666666666666666666666666666666666666666e0 * t360 * t183 + 0.35555555555555555555555555555555555555555555555554e-1 * t363 * t365 + 0.53333333333333333333333333333333333333333333333332e0 * t368 * t183 + 0.10666666666666666666666666666666666666666666666666e0 * t371 * t365 + 0.79999999999999999999999999999999999999999999999998e0 * t374 * t183 + 0.21333333333333333333333333333333333333333333333332e0 * t379 * t365
  t383 = t280 * t83 + t303 * t100 + t326 * t117 + 0.36408888888888888888888888888888888888888888888891e-5 * t328 * t250 - 0.19569777777777777777777777777777777777777777777779e-4 * t143 * t250 + 0.39111111111111111111111111111111111111111111111112e-1 * t26 * t237 + 0.10808888888888888888888888888888888888888888888889e-2 * t40 * t244 - 0.17777777777777777777777777777777777777777777777777e0 * t179 * t340 - 0.35555555555555555555555555555555555555555555555555e0 * t203 * t340 - 0.53333333333333333333333333333333333333333333333332e0 * t225 * t340 + t382
  t387 = t17 * t19
  t389 = 0.1e1 / t223 / t99
  t390 = t115 * t389
  t392 = t364 * t79
  t393 = 0.1e1 / t41 * t392
  t396 = t151 * t39
  t397 = t51 * t396
  t398 = t54 ** 2
  t402 = 0.1e1 / t156 / t46
  t403 = 0.1e1 / t398 / t126 * t402
  t406 = t74 * t224
  t409 = t98 * t378
  t413 = 0.1e1 / t153 * t57
  t420 = t129 * t364
  t423 = t326 * t224
  t426 = t25 * t151
  t431 = 0.1e1 / t20 / t54 / t42 * t157 * t28
  t439 = t27 / t19 / t54 * t47
  t442 = t280 * t100
  t445 = t201 * t224
  t448 = t38 * t269
  t452 = 0.1e1 / t19 / t398 * t275 * t27
  t457 = 0.28444444444444444444444444444444444444444444444442e0 * t390 * t393 + 0.74565404444444444444444444444444444444444444444451e-10 * t397 * t403 + 0.28444444444444444444444444444444444444444444444442e-1 * t406 * t393 + 0.11377777777777777777777777777777777777777777777776e0 * t409 * t393 - 0.184320e-3 * t53 * t413 - 0.69176888888888888888888888888888888888888888888893e-4 * t328 * t413 + 0.24181570370370370370370370370370370370370370370372e-3 * t143 * t413 - 0.42666666666666666666666666666666666666666666666665e0 * t371 * t420 + 0.12000000000000000000000000000000000000000000000000e1 * t423 * t183 + 0.11650844444444444444444444444444444444444444444445e-6 * t426 * t431 - 0.11796480000000000000000000000000000000000000000001e-5 * t350 * t431 + 0.64663703703703703703703703703703703703703703703706e-2 * t133 * t439 + 0.39999999999999999999999999999999999999999999999999e0 * t442 * t183 + 0.31999999999999999999999999999999999999999999999998e0 * t445 * t365 + 0.37282702222222222222222222222222222222222222222226e-8 * t448 * t452 + 0.26305422222222222222222222222222222222222222222223e-5 * t152 * t431
  t460 = t177 * t117
  t467 = t221 * t378
  t473 = 0.1e1 / t19 / t126 * t27 * t79
  t481 = t28 / t20 / t42 * t34
  t492 = t303 * t117
  t503 = t62 * t151
  t512 = t66 * t269
  t521 = t70 * t396
  t524 = -0.18251851851851851851851851851851851851851851851852e0 * t63 * t481 + 0.64663703703703703703703703703703703703703703703706e-2 * t164 * t439 - 0.69176888888888888888888888888888888888888888888893e-4 * t247 * t413 + 0.11650844444444444444444444444444444444444444444445e-6 * t503 * t431 - 0.79265185185185185185185185185185185185185185185186e-2 * t67 * t439 + 0.24181570370370370370370370370370370370370370370372e-3 * t169 * t413 - 0.11796480000000000000000000000000000000000000000001e-5 * t257 * t431 + 0.37282702222222222222222222222222222222222222222226e-8 * t512 * t452 - 0.184320e-3 * t71 * t413 + 0.26305422222222222222222222222222222222222222222223e-5 * t174 * t431 - 0.24466773333333333333333333333333333333333333333335e-7 * t270 * t452 + 0.74565404444444444444444444444444444444444444444451e-10 * t521 * t403
  t532 = t86 * t151
  t541 = t90 * t269
  t550 = t94 * t396
  t553 = -0.18251851851851851851851851851851851851851851851852e0 * t87 * t481 + 0.64663703703703703703703703703703703703703703703706e-2 * t188 * t439 - 0.69176888888888888888888888888888888888888888888893e-4 * t286 * t413 + 0.11650844444444444444444444444444444444444444444445e-6 * t532 * t431 - 0.79265185185185185185185185185185185185185185185186e-2 * t91 * t439 + 0.24181570370370370370370370370370370370370370370372e-3 * t193 * t413 - 0.11796480000000000000000000000000000000000000000001e-5 * t293 * t431 + 0.37282702222222222222222222222222222222222222222226e-8 * t541 * t452 - 0.184320e-3 * t95 * t413 + 0.26305422222222222222222222222222222222222222222223e-5 * t198 * t431 - 0.24466773333333333333333333333333333333333333333335e-7 * t300 * t452 + 0.74565404444444444444444444444444444444444444444451e-10 * t550 * t403
  t561 = t103 * t151
  t570 = t107 * t269
  t579 = t111 * t396
  t582 = -0.18251851851851851851851851851851851851851851851852e0 * t104 * t481 + 0.64663703703703703703703703703703703703703703703706e-2 * t208 * t439 - 0.69176888888888888888888888888888888888888888888893e-4 * t309 * t413 + 0.11650844444444444444444444444444444444444444444445e-6 * t561 * t431 - 0.79265185185185185185185185185185185185185185185186e-2 * t108 * t439 + 0.24181570370370370370370370370370370370370370370372e-3 * t213 * t413 - 0.11796480000000000000000000000000000000000000000001e-5 * t316 * t431 + 0.37282702222222222222222222222222222222222222222226e-8 * t570 * t452 - 0.184320e-3 * t112 * t413 + 0.26305422222222222222222222222222222222222222222223e-5 * t218 * t431 - 0.24466773333333333333333333333333333333333333333335e-7 * t323 * t452 + 0.74565404444444444444444444444444444444444444444451e-10 * t579 * t403
  t584 = -0.24466773333333333333333333333333333333333333333335e-7 * t357 * t452 + 0.10666666666666666666666666666666666666666666666666e0 * t460 * t365 - 0.10666666666666666666666666666666666666666666666666e1 * t368 * t340 - 0.14222222222222222222222222222222222222222222222222e0 * t363 * t420 + 0.63999999999999999999999999999999999999999999999997e0 * t467 * t365 + 0.82962962962962962962962962962962962962962962962962e0 * t203 * t473 + 0.12444444444444444444444444444444444444444444444444e1 * t225 * t473 - 0.18251851851851851851851851851851851851851851851852e0 * t26 * t481 - 0.79265185185185185185185185185185185185185185185186e-2 * t40 * t439 + 0.41481481481481481481481481481481481481481481481480e0 * t179 * t473 - 0.15999999999999999999999999999999999999999999999999e1 * t374 * t340 - 0.85333333333333333333333333333333333333333333333328e0 * t379 * t420 + 0.79999999999999999999999999999999999999999999999998e0 * t492 * t183 - 0.53333333333333333333333333333333333333333333333332e0 * t360 * t340 + t524 * t83 + t553 * t100 + t582 * t117
  t585 = t457 + t584
  t590 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t119 + t6 * t125 * t228 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t233 * t383 - 0.3e1 / 0.8e1 * t6 * t387 * t585)
  t612 = 0.1e1 / t19 / t398 / r0 * t275 * t27
  t624 = t364 ** 2
  t626 = t44 * t624 * t27
  t633 = 0.1e1 / t20 / t54 / t134 * t157 * t28
  t647 = 0.12800000000000000000000000000000000000000000000000e1 * t326 * t378 * t365 + 0.62409690074074074074074074074074074074074074074078e-6 * t357 * t612 + 0.99420539259259259259259259259259259259259259259267e-8 * t25 * t269 * t612 - 0.16155837629629629629629629629629629629629629629631e-6 * t448 * t612 + 0.53333333333333333333333333333333333333333333333332e0 * t524 * t100 * t183 + 0.75851851851851851851851851851851851851851851851838e-1 * t98 * t389 * t626 - 0.41848983703703703703703703703703703703703703703705e-4 * t152 * t633 - 0.10666666666666666666666666666666666666666666666666e1 * t442 * t340 - 0.56888888888888888888888888888888888888888888888887e0 * t460 * t420 - 0.38059425185185185185185185185185185185185185185188e-5 * t426 * t633 + 0.23859958518518518518518518518518518518518518518520e-4 * t350 * t633 + 0.16000000000000000000000000000000000000000000000000e1 * t582 * t224 * t183
  t648 = t236 * t364
  t654 = t27 / t19 / t144 * t47
  t664 = 0.1e1 / t42 * t392
  t668 = 0.1e1 / t258 * t57
  t679 = 0.1e1 / t398 / t41 * t402
  t687 = 0.37925925925925925925925925925925925925925925925924e1 * t379 * t648 - 0.57780148148148148148148148148148148148148148148150e-1 * t133 * t654 + 0.10666666666666666666666666666666666666666666666666e1 * t553 * t117 * t183 + 0.45511111111111111111111111111111111111111111111105e0 * t201 * t378 * t393 - 0.91022222222222222222222222222222222222222222222210e0 * t409 * t664 + 0.2027520e-2 * t53 * t668 + 0.10368442469135802469135802469135802469135802469136e-2 * t328 * t668 - 0.29981708641975308641975308641975308641975308641977e-2 * t143 * t668 - 0.22755555555555555555555555555555555555555555555554e1 * t390 * t664 - 0.40265318400000000000000000000000000000000000000004e-8 * t397 * t679 - 0.22755555555555555555555555555555555555555555555554e0 * t406 * t664 + 0.39768215703703703703703703703703703703703703703709e-9 * t38 * t396 * t679
  t704 = 0.1e1 / t19 / t41 * t27 * t79
  t712 = t28 / t20 / t134 * t34
  t723 = 0.11377777777777777777777777777777777777777777777777e1 * t221 * t389 * t393 + 0.11377777777777777777777777777777777777777777777777e0 * t177 * t224 * t393 + 0.18962962962962962962962962962962962962962962962962e1 * t371 * t648 + 0.49777777777777777777777777777777777777777777777775e1 * t374 * t473 - 0.21333333333333333333333333333333333333333333333332e1 * t492 * t340 - 0.27654320987654320987654320987654320987654320987654e1 * t203 * t704 - 0.41481481481481481481481481481481481481481481481480e1 * t225 * t704 + 0.10342716049382716049382716049382716049382716049383e1 * t26 * t712 + 0.66054320987654320987654320987654320987654320987655e-1 * t40 * t654 - 0.13827160493827160493827160493827160493827160493827e1 * t179 * t704 + 0.63209876543209876543209876543209876543209876543208e0 * t363 * t648 - 0.34133333333333333333333333333333333333333333333332e1 * t467 * t420
  t733 = t151 * t52
  t741 = 0.1e1 / t20 / t398 / t134 / t156 / t56 * t28
  t790 = 0.10342716049382716049382716049382716049382716049383e1 * t87 * t712 - 0.57780148148148148148148148148148148148148148148150e-1 * t188 * t654 + 0.10368442469135802469135802469135802469135802469136e-2 * t286 * t668 - 0.38059425185185185185185185185185185185185185185188e-5 * t532 * t633 + 0.99420539259259259259259259259259259259259259259267e-8 * t86 * t269 * t612 + 0.66054320987654320987654320987654320987654320987655e-1 * t91 * t654 - 0.29981708641975308641975308641975308641975308641977e-2 * t193 * t668 + 0.23859958518518518518518518518518518518518518518520e-4 * t293 * t633 - 0.16155837629629629629629629629629629629629629629631e-6 * t541 * t612 + 0.39768215703703703703703703703703703703703703703709e-9 * t90 * t396 * t679 + 0.2027520e-2 * t95 * t668 - 0.41848983703703703703703703703703703703703703703705e-4 * t198 * t633 + 0.62409690074074074074074074074074074074074074074078e-6 * t300 * t612 - 0.40265318400000000000000000000000000000000000000004e-8 * t550 * t679 + 0.47721858844444444444444444444444444444444444444450e-11 * t94 * t733 * t741
  t825 = 0.10342716049382716049382716049382716049382716049383e1 * t63 * t712 - 0.57780148148148148148148148148148148148148148148150e-1 * t164 * t654 + 0.10368442469135802469135802469135802469135802469136e-2 * t247 * t668 - 0.38059425185185185185185185185185185185185185185188e-5 * t503 * t633 + 0.99420539259259259259259259259259259259259259259267e-8 * t62 * t269 * t612 + 0.66054320987654320987654320987654320987654320987655e-1 * t67 * t654 - 0.29981708641975308641975308641975308641975308641977e-2 * t169 * t668 + 0.23859958518518518518518518518518518518518518518520e-4 * t257 * t633 - 0.16155837629629629629629629629629629629629629629631e-6 * t512 * t612 + 0.39768215703703703703703703703703703703703703703709e-9 * t66 * t396 * t679 + 0.2027520e-2 * t71 * t668 - 0.41848983703703703703703703703703703703703703703705e-4 * t174 * t633 + 0.62409690074074074074074074074074074074074074074078e-6 * t270 * t612 - 0.40265318400000000000000000000000000000000000000004e-8 * t521 * t679 + 0.47721858844444444444444444444444444444444444444450e-11 * t70 * t733 * t741
  t860 = 0.10342716049382716049382716049382716049382716049383e1 * t104 * t712 - 0.57780148148148148148148148148148148148148148148150e-1 * t208 * t654 + 0.10368442469135802469135802469135802469135802469136e-2 * t309 * t668 - 0.38059425185185185185185185185185185185185185185188e-5 * t561 * t633 + 0.99420539259259259259259259259259259259259259259267e-8 * t103 * t269 * t612 + 0.66054320987654320987654320987654320987654320987655e-1 * t108 * t654 - 0.29981708641975308641975308641975308641975308641977e-2 * t213 * t668 + 0.23859958518518518518518518518518518518518518518520e-4 * t316 * t633 - 0.16155837629629629629629629629629629629629629629631e-6 * t570 * t612 + 0.39768215703703703703703703703703703703703703703709e-9 * t107 * t396 * t679 + 0.2027520e-2 * t112 * t668 - 0.41848983703703703703703703703703703703703703703705e-4 * t218 * t633 + 0.62409690074074074074074074074074074074074074074078e-6 * t323 * t612 - 0.40265318400000000000000000000000000000000000000004e-8 * t579 * t679 + 0.47721858844444444444444444444444444444444444444450e-11 * t111 * t733 * t741
  t862 = 0.16592592592592592592592592592592592592592592592592e1 * t360 * t473 + 0.33185185185185185185185185185185185185185185185183e1 * t368 * t473 + 0.22755555555555555555555555555555555555555555555553e0 * t115 / t223 / t116 * t626 + 0.47721858844444444444444444444444444444444444444450e-11 * t51 * t733 * t741 + 0.15170370370370370370370370370370370370370370370369e-1 * t74 * t378 * t626 - 0.17066666666666666666666666666666666666666666666666e1 * t445 * t420 + 0.21333333333333333333333333333333333333333333333332e0 * t280 * t117 * t365 + 0.63999999999999999999999999999999999999999999999996e0 * t303 * t224 * t365 - 0.31999999999999999999999999999999999999999999999999e1 * t423 * t340 + t790 * t100 + t825 * t83 + t860 * t117
  t869 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t128 * t119 - 0.5e1 / 0.9e1 * t6 * t23 * t228 + t6 * t125 * t383 / 0.2e1 - t6 * t233 * t585 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t387 * (t647 + t687 + t723 + t862))
  v4rho4_0_ = 0.2e1 * r0 * t869 + 0.8e1 * t590

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
  t32 = params_CC_0_[0]
  t33 = params_CC_0_[1]
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t42 = 0.1e1 + 0.4e-2 * s0 * t39
  t43 = 0.1e1 / t42
  t44 = t39 * t43
  t47 = params_CC_0_[2]
  t48 = s0 ** 2
  t49 = t47 * t48
  t50 = t35 ** 2
  t54 = t42 ** 2
  t55 = 0.1e1 / t54
  t56 = 0.1e1 / t36 / t50 / r0 * t55
  t59 = params_CC_0_[3]
  t60 = t48 * s0
  t61 = t59 * t60
  t62 = t50 ** 2
  t65 = 0.1e1 / t54 / t42
  t66 = 0.1e1 / t62 * t65
  t69 = params_CC_1_[0]
  t70 = params_CC_1_[1]
  t71 = t70 * s0
  t74 = params_CC_1_[2]
  t75 = t74 * t48
  t78 = params_CC_1_[3]
  t79 = t78 * t60
  t82 = t69 + 0.4e-2 * t71 * t44 + 0.16e-4 * t75 * t56 + 0.64e-7 * t79 * t66
  t84 = 2 ** (0.1e1 / 0.3e1)
  t85 = 0.1e1 / t30 * t84
  t87 = 0.1e1 + t17 <= f.p.zeta_threshold
  t89 = 0.1e1 - t17 <= f.p.zeta_threshold
  t90 = f.my_piecewise5(t87, t11, t89, t15, t17)
  t91 = 0.1e1 + t90
  t92 = t91 <= f.p.zeta_threshold
  t93 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t94 = 0.1e1 / t93
  t95 = t91 ** (0.1e1 / 0.3e1)
  t97 = f.my_piecewise3(t92, t94, 0.1e1 / t95)
  t100 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t97
  t101 = 0.1e1 / t100
  t103 = params_CC_2_[0]
  t104 = params_CC_2_[1]
  t105 = t104 * s0
  t108 = params_CC_2_[2]
  t109 = t108 * t48
  t112 = params_CC_2_[3]
  t113 = t112 * t60
  t116 = t103 + 0.4e-2 * t105 * t44 + 0.16e-4 * t109 * t56 + 0.64e-7 * t113 * t66
  t117 = t100 ** 2
  t118 = 0.1e1 / t117
  t120 = params_CC_3_[0]
  t121 = params_CC_3_[1]
  t122 = t121 * s0
  t125 = params_CC_3_[2]
  t126 = t125 * t48
  t129 = params_CC_3_[3]
  t130 = t129 * t60
  t133 = t120 + 0.4e-2 * t122 * t44 + 0.16e-4 * t126 * t56 + 0.64e-7 * t130 * t66
  t135 = 0.1e1 / t117 / t100
  t137 = t32 + 0.4e-2 * t34 * t44 + 0.16e-4 * t49 * t56 + 0.64e-7 * t61 * t66 + t82 * t101 + t116 * t118 + t133 * t135
  t141 = t93 * f.p.zeta_threshold
  t143 = f.my_piecewise3(t20, t141, t21 * t19)
  t144 = t30 ** 2
  t145 = 0.1e1 / t144
  t146 = t143 * t145
  t149 = t5 * t146 * t137 / 0.8e1
  t150 = t143 * t30
  t151 = t35 * r0
  t154 = 0.1e1 / t37 / t151 * t43
  t157 = t33 * t48
  t161 = 0.1e1 / t36 / t50 / t35 * t55
  t166 = t47 * t60
  t169 = 0.1e1 / t62 / r0 * t65
  t174 = t48 ** 2
  t175 = t59 * t174
  t179 = t54 ** 2
  t180 = 0.1e1 / t179
  t181 = 0.1e1 / t37 / t62 / t151 * t180
  t186 = t70 * t48
  t191 = t74 * t60
  t196 = t78 * t174
  t199 = -0.10666666666666666666666666666666666666666666666667e-1 * t71 * t154 + 0.42666666666666666666666666666666666666666666666668e-4 * t186 * t161 - 0.85333333333333333333333333333333333333333333333333e-4 * t75 * t161 + 0.34133333333333333333333333333333333333333333333334e-6 * t191 * t169 - 0.512e-6 * t79 * t169 + 0.20480000000000000000000000000000000000000000000001e-8 * t196 * t181
  t201 = t82 * t118
  t204 = 0.1e1 / t30 / t6 * t84
  t206 = 0.13333333333333333333333333333333333333333333333333e0 * t204 * t97
  t208 = 0.1e1 / t95 / t91
  t209 = f.my_piecewise5(t87, 0, t89, 0, t25)
  t212 = f.my_piecewise3(t92, 0, -t208 * t209 / 0.3e1)
  t215 = -t206 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t212
  t219 = t104 * t48
  t224 = t108 * t60
  t229 = t112 * t174
  t232 = -0.10666666666666666666666666666666666666666666666667e-1 * t105 * t154 + 0.42666666666666666666666666666666666666666666666668e-4 * t219 * t161 - 0.85333333333333333333333333333333333333333333333333e-4 * t109 * t161 + 0.34133333333333333333333333333333333333333333333334e-6 * t224 * t169 - 0.512e-6 * t113 * t169 + 0.20480000000000000000000000000000000000000000000001e-8 * t229 * t181
  t234 = t116 * t135
  t239 = t121 * t48
  t244 = t125 * t60
  t249 = t129 * t174
  t252 = -0.10666666666666666666666666666666666666666666666667e-1 * t122 * t154 + 0.42666666666666666666666666666666666666666666666668e-4 * t239 * t161 - 0.85333333333333333333333333333333333333333333333333e-4 * t126 * t161 + 0.34133333333333333333333333333333333333333333333334e-6 * t244 * t169 - 0.512e-6 * t130 * t169 + 0.20480000000000000000000000000000000000000000000001e-8 * t249 * t181
  t254 = t117 ** 2
  t255 = 0.1e1 / t254
  t256 = t133 * t255
  t259 = -0.10666666666666666666666666666666666666666666666667e-1 * t34 * t154 + 0.42666666666666666666666666666666666666666666666668e-4 * t157 * t161 - 0.85333333333333333333333333333333333333333333333333e-4 * t49 * t161 + 0.34133333333333333333333333333333333333333333333334e-6 * t166 * t169 - 0.512e-6 * t61 * t169 + 0.20480000000000000000000000000000000000000000000001e-8 * t175 * t181 + t199 * t101 - t201 * t215 + t232 * t118 - 0.2e1 * t234 * t215 + t252 * t135 - 0.3e1 * t256 * t215
  t264 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t137 - t149 - 0.3e1 / 0.8e1 * t5 * t150 * t259)
  t266 = r1 <= f.p.dens_threshold
  t267 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t268 = 0.1e1 + t267
  t269 = t268 <= f.p.zeta_threshold
  t270 = t268 ** (0.1e1 / 0.3e1)
  t271 = -t25
  t272 = f.my_piecewise5(t14, 0, t10, 0, t271)
  t275 = f.my_piecewise3(t269, 0, 0.4e1 / 0.3e1 * t270 * t272)
  t276 = t275 * t30
  t277 = t33 * s2
  t278 = r1 ** 2
  t279 = r1 ** (0.1e1 / 0.3e1)
  t280 = t279 ** 2
  t282 = 0.1e1 / t280 / t278
  t285 = 0.1e1 + 0.4e-2 * s2 * t282
  t286 = 0.1e1 / t285
  t287 = t282 * t286
  t290 = s2 ** 2
  t291 = t47 * t290
  t292 = t278 ** 2
  t296 = t285 ** 2
  t297 = 0.1e1 / t296
  t298 = 0.1e1 / t279 / t292 / r1 * t297
  t301 = t290 * s2
  t302 = t59 * t301
  t303 = t292 ** 2
  t306 = 0.1e1 / t296 / t285
  t307 = 0.1e1 / t303 * t306
  t310 = t70 * s2
  t313 = t74 * t290
  t316 = t78 * t301
  t319 = t69 + 0.4e-2 * t310 * t287 + 0.16e-4 * t313 * t298 + 0.64e-7 * t316 * t307
  t320 = f.my_piecewise5(t89, t11, t87, t15, -t17)
  t321 = 0.1e1 + t320
  t322 = t321 <= f.p.zeta_threshold
  t323 = t321 ** (0.1e1 / 0.3e1)
  t325 = f.my_piecewise3(t322, t94, 0.1e1 / t323)
  t328 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t325
  t329 = 0.1e1 / t328
  t331 = t104 * s2
  t334 = t108 * t290
  t337 = t112 * t301
  t340 = t103 + 0.4e-2 * t331 * t287 + 0.16e-4 * t334 * t298 + 0.64e-7 * t337 * t307
  t341 = t328 ** 2
  t342 = 0.1e1 / t341
  t344 = t121 * s2
  t347 = t125 * t290
  t350 = t129 * t301
  t353 = t120 + 0.4e-2 * t344 * t287 + 0.16e-4 * t347 * t298 + 0.64e-7 * t350 * t307
  t355 = 0.1e1 / t341 / t328
  t357 = t32 + 0.4e-2 * t277 * t287 + 0.16e-4 * t291 * t298 + 0.64e-7 * t302 * t307 + t319 * t329 + t340 * t342 + t353 * t355
  t362 = f.my_piecewise3(t269, t141, t270 * t268)
  t363 = t362 * t145
  t366 = t5 * t363 * t357 / 0.8e1
  t367 = t362 * t30
  t368 = t319 * t342
  t370 = 0.13333333333333333333333333333333333333333333333333e0 * t204 * t325
  t372 = 0.1e1 / t323 / t321
  t373 = f.my_piecewise5(t89, 0, t87, 0, t271)
  t376 = f.my_piecewise3(t322, 0, -t372 * t373 / 0.3e1)
  t379 = -t370 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t376
  t381 = t340 * t355
  t384 = t341 ** 2
  t385 = 0.1e1 / t384
  t386 = t353 * t385
  t389 = -t368 * t379 - 0.2e1 * t381 * t379 - 0.3e1 * t386 * t379
  t394 = f.my_piecewise3(t266, 0, -0.3e1 / 0.8e1 * t5 * t276 * t357 - t366 - 0.3e1 / 0.8e1 * t5 * t367 * t389)
  t396 = t21 ** 2
  t397 = 0.1e1 / t396
  t398 = t26 ** 2
  t403 = t16 / t22 / t6
  t405 = -0.2e1 * t23 + 0.2e1 * t403
  t406 = f.my_piecewise5(t10, 0, t14, 0, t405)
  t410 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t397 * t398 + 0.4e1 / 0.3e1 * t21 * t406)
  t417 = t5 * t29 * t145 * t137
  t423 = 0.1e1 / t144 / t6
  t427 = t5 * t143 * t423 * t137 / 0.12e2
  t429 = t5 * t146 * t259
  t433 = t133 / t254 / t100
  t434 = t215 ** 2
  t437 = t116 * t255
  t440 = t82 * t135
  t443 = t50 * t151
  t446 = 0.1e1 / t36 / t443 * t55
  t452 = 0.1e1 / t62 / t35 * t65
  t461 = 0.1e1 / t37 / t62 / t50 * t180
  t466 = t174 * s0
  t473 = 0.1e1 / t36 / t62 / t443 / t179 / t42
  t478 = 0.1e1 / t37 / t50 * t43
  t549 = t252 * t255
  t554 = 0.1e1 / t30 / t22 * t84
  t556 = 0.17777777777777777777777777777777777777777777777777e0 * t554 * t97
  t557 = t204 * t212
  t559 = t91 ** 2
  t561 = 0.1e1 / t95 / t559
  t562 = t209 ** 2
  t565 = f.my_piecewise5(t87, 0, t89, 0, t405)
  t569 = f.my_piecewise3(t92, 0, 0.4e1 / 0.9e1 * t561 * t562 - t208 * t565 / 0.3e1)
  t572 = t556 - 0.26666666666666666666666666666666666666666666666666e0 * t557 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t569
  t575 = t232 * t135
  t580 = t199 * t118
  t590 = (0.39111111111111111111111111111111111111111111111112e-1 * t71 * t478 - 0.38400000000000000000000000000000000000000000000001e-3 * t186 * t446 + 0.91022222222222222222222222222222222222222222222228e-6 * t70 * t60 * t452 + 0.54044444444444444444444444444444444444444444444444e-3 * t75 * t446 - 0.48924444444444444444444444444444444444444444444446e-5 * t191 * t452 + 0.10922666666666666666666666666666666666666666666667e-7 * t74 * t174 * t461 + 0.4608e-5 * t79 * t452 - 0.40277333333333333333333333333333333333333333333336e-7 * t196 * t461 + 0.87381333333333333333333333333333333333333333333340e-10 * t78 * t466 * t473) * t101 + (0.39111111111111111111111111111111111111111111111112e-1 * t105 * t478 - 0.38400000000000000000000000000000000000000000000001e-3 * t219 * t446 + 0.91022222222222222222222222222222222222222222222228e-6 * t104 * t60 * t452 + 0.54044444444444444444444444444444444444444444444444e-3 * t109 * t446 - 0.48924444444444444444444444444444444444444444444446e-5 * t224 * t452 + 0.10922666666666666666666666666666666666666666666667e-7 * t108 * t174 * t461 + 0.4608e-5 * t113 * t452 - 0.40277333333333333333333333333333333333333333333336e-7 * t229 * t461 + 0.87381333333333333333333333333333333333333333333340e-10 * t112 * t466 * t473) * t118 - 0.6e1 * t549 * t215 - 0.3e1 * t256 * t572 - 0.4e1 * t575 * t215 - 0.2e1 * t234 * t572 - 0.2e1 * t580 * t215 - t201 * t572 + 0.39111111111111111111111111111111111111111111111112e-1 * t34 * t478 + 0.54044444444444444444444444444444444444444444444444e-3 * t49 * t446 + 0.4608e-5 * t61 * t452
  t596 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t410 * t30 * t137 - t417 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t259 + t427 - t429 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t150 * (0.12e2 * t433 * t434 + 0.6e1 * t437 * t434 + 0.2e1 * t440 * t434 - 0.38400000000000000000000000000000000000000000000001e-3 * t157 * t446 + 0.91022222222222222222222222222222222222222222222228e-6 * t33 * t60 * t452 - 0.48924444444444444444444444444444444444444444444446e-5 * t166 * t452 + 0.10922666666666666666666666666666666666666666666667e-7 * t47 * t174 * t461 - 0.40277333333333333333333333333333333333333333333336e-7 * t175 * t461 + 0.87381333333333333333333333333333333333333333333340e-10 * t59 * t466 * t473 + (0.39111111111111111111111111111111111111111111111112e-1 * t122 * t478 - 0.38400000000000000000000000000000000000000000000001e-3 * t239 * t446 + 0.91022222222222222222222222222222222222222222222228e-6 * t121 * t60 * t452 + 0.54044444444444444444444444444444444444444444444444e-3 * t126 * t446 - 0.48924444444444444444444444444444444444444444444446e-5 * t244 * t452 + 0.10922666666666666666666666666666666666666666666667e-7 * t125 * t174 * t461 + 0.4608e-5 * t130 * t452 - 0.40277333333333333333333333333333333333333333333336e-7 * t249 * t461 + 0.87381333333333333333333333333333333333333333333340e-10 * t129 * t466 * t473) * t135 + t590))
  t597 = t270 ** 2
  t598 = 0.1e1 / t597
  t599 = t272 ** 2
  t602 = -t405
  t603 = f.my_piecewise5(t14, 0, t10, 0, t602)
  t607 = f.my_piecewise3(t269, 0, 0.4e1 / 0.9e1 * t598 * t599 + 0.4e1 / 0.3e1 * t270 * t603)
  t614 = t5 * t275 * t145 * t357
  t622 = t5 * t362 * t423 * t357 / 0.12e2
  t624 = t5 * t363 * t389
  t626 = t319 * t355
  t627 = t379 ** 2
  t631 = 0.17777777777777777777777777777777777777777777777777e0 * t554 * t325
  t632 = t204 * t376
  t634 = t321 ** 2
  t636 = 0.1e1 / t323 / t634
  t637 = t373 ** 2
  t640 = f.my_piecewise5(t89, 0, t87, 0, t602)
  t644 = f.my_piecewise3(t322, 0, 0.4e1 / 0.9e1 * t636 * t637 - t372 * t640 / 0.3e1)
  t647 = t631 - 0.26666666666666666666666666666666666666666666666666e0 * t632 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t644
  t649 = t340 * t385
  t656 = t353 / t384 / t328
  t666 = f.my_piecewise3(t266, 0, -0.3e1 / 0.8e1 * t5 * t607 * t30 * t357 - t614 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t276 * t389 + t622 - t624 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t367 * (-t368 * t647 - 0.2e1 * t381 * t647 - 0.3e1 * t386 * t647 + 0.2e1 * t626 * t627 + 0.6e1 * t649 * t627 + 0.12e2 * t656 * t627))
  d11 = 0.2e1 * t264 + 0.2e1 * t394 + t6 * (t596 + t666)
  t669 = -t7 - t24
  t670 = f.my_piecewise5(t10, 0, t14, 0, t669)
  t673 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t670)
  t674 = t673 * t30
  t678 = f.my_piecewise5(t87, 0, t89, 0, t669)
  t681 = f.my_piecewise3(t92, 0, -t208 * t678 / 0.3e1)
  t684 = -t206 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t681
  t690 = -t201 * t684 - 0.2e1 * t234 * t684 - 0.3e1 * t256 * t684
  t695 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t674 * t137 - t149 - 0.3e1 / 0.8e1 * t5 * t150 * t690)
  t696 = -t669
  t697 = f.my_piecewise5(t14, 0, t10, 0, t696)
  t700 = f.my_piecewise3(t269, 0, 0.4e1 / 0.3e1 * t270 * t697)
  t701 = t700 * t30
  t705 = t278 * r1
  t708 = 0.1e1 / t280 / t705 * t286
  t711 = t33 * t290
  t715 = 0.1e1 / t279 / t292 / t278 * t297
  t720 = t47 * t301
  t723 = 0.1e1 / t303 / r1 * t306
  t728 = t290 ** 2
  t729 = t59 * t728
  t733 = t296 ** 2
  t734 = 0.1e1 / t733
  t735 = 0.1e1 / t280 / t303 / t705 * t734
  t740 = t70 * t290
  t745 = t74 * t301
  t750 = t78 * t728
  t753 = -0.10666666666666666666666666666666666666666666666667e-1 * t310 * t708 + 0.42666666666666666666666666666666666666666666666668e-4 * t740 * t715 - 0.85333333333333333333333333333333333333333333333333e-4 * t313 * t715 + 0.34133333333333333333333333333333333333333333333334e-6 * t745 * t723 - 0.512e-6 * t316 * t723 + 0.20480000000000000000000000000000000000000000000001e-8 * t750 * t735
  t755 = f.my_piecewise5(t89, 0, t87, 0, t696)
  t758 = f.my_piecewise3(t322, 0, -t372 * t755 / 0.3e1)
  t761 = -t370 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t758
  t765 = t104 * t290
  t770 = t108 * t301
  t775 = t112 * t728
  t778 = -0.10666666666666666666666666666666666666666666666667e-1 * t331 * t708 + 0.42666666666666666666666666666666666666666666666668e-4 * t765 * t715 - 0.85333333333333333333333333333333333333333333333333e-4 * t334 * t715 + 0.34133333333333333333333333333333333333333333333334e-6 * t770 * t723 - 0.512e-6 * t337 * t723 + 0.20480000000000000000000000000000000000000000000001e-8 * t775 * t735
  t784 = t121 * t290
  t789 = t125 * t301
  t794 = t129 * t728
  t797 = -0.10666666666666666666666666666666666666666666666667e-1 * t344 * t708 + 0.42666666666666666666666666666666666666666666666668e-4 * t784 * t715 - 0.85333333333333333333333333333333333333333333333333e-4 * t347 * t715 + 0.34133333333333333333333333333333333333333333333334e-6 * t789 * t723 - 0.512e-6 * t350 * t723 + 0.20480000000000000000000000000000000000000000000001e-8 * t794 * t735
  t801 = -0.10666666666666666666666666666666666666666666666667e-1 * t277 * t708 + 0.42666666666666666666666666666666666666666666666668e-4 * t711 * t715 - 0.85333333333333333333333333333333333333333333333333e-4 * t291 * t715 + 0.34133333333333333333333333333333333333333333333334e-6 * t720 * t723 - 0.512e-6 * t302 * t723 + 0.20480000000000000000000000000000000000000000000001e-8 * t729 * t735 + t753 * t329 - t368 * t761 + t778 * t342 - 0.2e1 * t381 * t761 + t797 * t355 - 0.3e1 * t386 * t761
  t806 = f.my_piecewise3(t266, 0, -0.3e1 / 0.8e1 * t5 * t701 * t357 - t366 - 0.3e1 / 0.8e1 * t5 * t367 * t801)
  t810 = 0.2e1 * t403
  t811 = f.my_piecewise5(t10, 0, t14, 0, t810)
  t815 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t397 * t670 * t26 + 0.4e1 / 0.3e1 * t21 * t811)
  t822 = t5 * t673 * t145 * t137
  t833 = t5 * t146 * t690
  t836 = t684 * t215
  t840 = t204 * t681
  t845 = f.my_piecewise5(t87, 0, t89, 0, t810)
  t849 = f.my_piecewise3(t92, 0, 0.4e1 / 0.9e1 * t561 * t678 * t209 - t208 * t845 / 0.3e1)
  t852 = t556 - 0.13333333333333333333333333333333333333333333333333e0 * t557 - 0.13333333333333333333333333333333333333333333333333e0 * t840 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t849
  t871 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t815 * t30 * t137 - t822 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t674 * t259 - t417 / 0.8e1 + t427 - t429 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t31 * t690 - t833 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t150 * (-t201 * t852 - 0.2e1 * t234 * t852 - 0.3e1 * t256 * t852 + 0.12e2 * t433 * t836 + 0.6e1 * t437 * t836 + 0.2e1 * t440 * t836 - 0.3e1 * t549 * t684 - 0.2e1 * t575 * t684 - t580 * t684))
  t875 = f.my_piecewise5(t14, 0, t10, 0, -t810)
  t879 = f.my_piecewise3(t269, 0, 0.4e1 / 0.9e1 * t598 * t697 * t272 + 0.4e1 / 0.3e1 * t270 * t875)
  t886 = t5 * t700 * t145 * t357
  t897 = t5 * t363 * t801
  t899 = t753 * t342
  t901 = t761 * t379
  t905 = t204 * t758
  t910 = f.my_piecewise5(t89, 0, t87, 0, -t810)
  t914 = f.my_piecewise3(t322, 0, 0.4e1 / 0.9e1 * t636 * t755 * t373 - t372 * t910 / 0.3e1)
  t917 = t631 - 0.13333333333333333333333333333333333333333333333333e0 * t632 - 0.13333333333333333333333333333333333333333333333333e0 * t905 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t914
  t919 = t778 * t355
  t926 = t797 * t385
  t938 = f.my_piecewise3(t266, 0, -0.3e1 / 0.8e1 * t5 * t879 * t30 * t357 - t886 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t701 * t389 - t614 / 0.8e1 + t622 - t624 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t276 * t801 - t897 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t367 * (-t368 * t917 - t899 * t379 - 0.2e1 * t919 * t379 - 0.3e1 * t926 * t379 - 0.2e1 * t381 * t917 - 0.3e1 * t386 * t917 + 0.2e1 * t626 * t901 + 0.6e1 * t649 * t901 + 0.12e2 * t656 * t901))
  d12 = t264 + t394 + t695 + t806 + t6 * (t871 + t938)
  t943 = t670 ** 2
  t947 = 0.2e1 * t23 + 0.2e1 * t403
  t948 = f.my_piecewise5(t10, 0, t14, 0, t947)
  t952 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t397 * t943 + 0.4e1 / 0.3e1 * t21 * t948)
  t962 = t684 ** 2
  t966 = t678 ** 2
  t969 = f.my_piecewise5(t87, 0, t89, 0, t947)
  t973 = f.my_piecewise3(t92, 0, 0.4e1 / 0.9e1 * t561 * t966 - t208 * t969 / 0.3e1)
  t976 = t556 - 0.26666666666666666666666666666666666666666666666666e0 * t840 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t973
  t991 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t952 * t30 * t137 - t822 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t674 * t690 + t427 - t833 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t150 * (-t201 * t976 - 0.2e1 * t234 * t976 - 0.3e1 * t256 * t976 + 0.12e2 * t433 * t962 + 0.6e1 * t437 * t962 + 0.2e1 * t440 * t962))
  t992 = t697 ** 2
  t995 = -t947
  t996 = f.my_piecewise5(t14, 0, t10, 0, t995)
  t1000 = f.my_piecewise3(t269, 0, 0.4e1 / 0.9e1 * t598 * t992 + 0.4e1 / 0.3e1 * t270 * t996)
  t1013 = t755 ** 2
  t1016 = f.my_piecewise5(t89, 0, t87, 0, t995)
  t1020 = f.my_piecewise3(t322, 0, 0.4e1 / 0.9e1 * t636 * t1013 - t372 * t1016 / 0.3e1)
  t1023 = t631 - 0.26666666666666666666666666666666666666666666666666e0 * t905 + 0.39999999999999999999999999999999999999999999999998e0 * t85 * t1020
  t1035 = 0.1e1 / t280 / t292 * t286
  t1038 = t292 * t705
  t1041 = 0.1e1 / t279 / t1038 * t297
  t1047 = 0.1e1 / t303 / t278 * t306
  t1058 = 0.1e1 / t280 / t303 / t292 * t734
  t1065 = t728 * s2
  t1072 = 0.1e1 / t279 / t303 / t1038 / t733 / t285
  t1123 = t761 ** 2
  t1152 = 0.6e1 * t649 * t1123 + 0.2e1 * t626 * t1123 - 0.38400000000000000000000000000000000000000000000001e-3 * t711 * t1041 + 0.91022222222222222222222222222222222222222222222228e-6 * t33 * t301 * t1047 - 0.48924444444444444444444444444444444444444444444446e-5 * t720 * t1047 + 0.10922666666666666666666666666666666666666666666667e-7 * t47 * t728 * t1058 - 0.40277333333333333333333333333333333333333333333336e-7 * t729 * t1058 + 0.87381333333333333333333333333333333333333333333340e-10 * t59 * t1065 * t1072 + 0.4608e-5 * t302 * t1047 + 0.54044444444444444444444444444444444444444444444444e-3 * t291 * t1041 + 0.39111111111111111111111111111111111111111111111112e-1 * t277 * t1035
  t1158 = f.my_piecewise3(t266, 0, -0.3e1 / 0.8e1 * t5 * t1000 * t30 * t357 - t886 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t701 * t801 + t622 - t897 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t367 * (-0.6e1 * t926 * t761 - 0.3e1 * t386 * t1023 - 0.4e1 * t919 * t761 - 0.2e1 * t381 * t1023 - 0.2e1 * t899 * t761 - t368 * t1023 + (0.39111111111111111111111111111111111111111111111112e-1 * t331 * t1035 - 0.38400000000000000000000000000000000000000000000001e-3 * t765 * t1041 + 0.91022222222222222222222222222222222222222222222228e-6 * t104 * t301 * t1047 + 0.54044444444444444444444444444444444444444444444444e-3 * t334 * t1041 - 0.48924444444444444444444444444444444444444444444446e-5 * t770 * t1047 + 0.10922666666666666666666666666666666666666666666667e-7 * t108 * t728 * t1058 + 0.4608e-5 * t337 * t1047 - 0.40277333333333333333333333333333333333333333333336e-7 * t775 * t1058 + 0.87381333333333333333333333333333333333333333333340e-10 * t112 * t1065 * t1072) * t342 + (0.39111111111111111111111111111111111111111111111112e-1 * t344 * t1035 - 0.38400000000000000000000000000000000000000000000001e-3 * t784 * t1041 + 0.91022222222222222222222222222222222222222222222228e-6 * t121 * t301 * t1047 + 0.54044444444444444444444444444444444444444444444444e-3 * t347 * t1041 - 0.48924444444444444444444444444444444444444444444446e-5 * t789 * t1047 + 0.10922666666666666666666666666666666666666666666667e-7 * t125 * t728 * t1058 + 0.4608e-5 * t350 * t1047 - 0.40277333333333333333333333333333333333333333333336e-7 * t794 * t1058 + 0.87381333333333333333333333333333333333333333333340e-10 * t129 * t1065 * t1072) * t355 + (0.39111111111111111111111111111111111111111111111112e-1 * t310 * t1035 - 0.38400000000000000000000000000000000000000000000001e-3 * t740 * t1041 + 0.91022222222222222222222222222222222222222222222228e-6 * t70 * t301 * t1047 + 0.54044444444444444444444444444444444444444444444444e-3 * t313 * t1041 - 0.48924444444444444444444444444444444444444444444446e-5 * t745 * t1047 + 0.10922666666666666666666666666666666666666666666667e-7 * t74 * t728 * t1058 + 0.4608e-5 * t316 * t1047 - 0.40277333333333333333333333333333333333333333333336e-7 * t750 * t1058 + 0.87381333333333333333333333333333333333333333333340e-10 * t78 * t1065 * t1072) * t329 + 0.12e2 * t656 * t1123 + t1152))
  d22 = 0.2e1 * t695 + 0.2e1 * t806 + t6 * (t991 + t1158)
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
  t32 = t24 * t6
  t33 = 0.1e1 / t32
  t36 = 0.2e1 * t16 * t33 - 0.2e1 * t25
  t37 = f.my_piecewise5(t10, 0, t14, 0, t36)
  t41 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t23 * t29 + 0.4e1 / 0.3e1 * t21 * t37)
  t42 = t6 ** (0.1e1 / 0.3e1)
  t43 = t41 * t42
  t44 = params.CC_0_[0]
  t45 = params.CC_0_[1]
  t46 = t45 * s0
  t47 = r0 ** 2
  t48 = r0 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t51 = 0.1e1 / t49 / t47
  t54 = 0.1e1 + 0.4e-2 * s0 * t51
  t55 = 0.1e1 / t54
  t56 = t51 * t55
  t59 = params.CC_0_[2]
  t60 = s0 ** 2
  t61 = t59 * t60
  t62 = t47 ** 2
  t63 = t62 * r0
  t66 = t54 ** 2
  t67 = 0.1e1 / t66
  t68 = 0.1e1 / t48 / t63 * t67
  t71 = params.CC_0_[3]
  t72 = t60 * s0
  t73 = t71 * t72
  t74 = t62 ** 2
  t77 = 0.1e1 / t66 / t54
  t78 = 0.1e1 / t74 * t77
  t81 = params.CC_1_[0]
  t82 = params.CC_1_[1]
  t83 = t82 * s0
  t86 = params.CC_1_[2]
  t87 = t86 * t60
  t90 = params.CC_1_[3]
  t91 = t90 * t72
  t94 = t81 + 0.4e-2 * t83 * t56 + 0.16e-4 * t87 * t68 + 0.64e-7 * t91 * t78
  t96 = 2 ** (0.1e1 / 0.3e1)
  t97 = 0.1e1 / t42 * t96
  t99 = 0.1e1 + t17 <= f.p.zeta_threshold
  t101 = 0.1e1 - t17 <= f.p.zeta_threshold
  t102 = f.my_piecewise5(t99, t11, t101, t15, t17)
  t103 = 0.1e1 + t102
  t104 = t103 <= f.p.zeta_threshold
  t105 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t106 = 0.1e1 / t105
  t107 = t103 ** (0.1e1 / 0.3e1)
  t109 = f.my_piecewise3(t104, t106, 0.1e1 / t107)
  t112 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t109
  t113 = 0.1e1 / t112
  t115 = params.CC_2_[0]
  t116 = params.CC_2_[1]
  t117 = t116 * s0
  t120 = params.CC_2_[2]
  t121 = t120 * t60
  t124 = params.CC_2_[3]
  t125 = t124 * t72
  t128 = t115 + 0.4e-2 * t117 * t56 + 0.16e-4 * t121 * t68 + 0.64e-7 * t125 * t78
  t129 = t112 ** 2
  t130 = 0.1e1 / t129
  t132 = params.CC_3_[0]
  t133 = params.CC_3_[1]
  t134 = t133 * s0
  t137 = params.CC_3_[2]
  t138 = t137 * t60
  t141 = params.CC_3_[3]
  t142 = t141 * t72
  t145 = t132 + 0.4e-2 * t134 * t56 + 0.16e-4 * t138 * t68 + 0.64e-7 * t142 * t78
  t147 = 0.1e1 / t129 / t112
  t149 = t44 + 0.4e-2 * t46 * t56 + 0.16e-4 * t61 * t68 + 0.64e-7 * t73 * t78 + t94 * t113 + t128 * t130 + t145 * t147
  t155 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t156 = t42 ** 2
  t157 = 0.1e1 / t156
  t158 = t155 * t157
  t162 = t155 * t42
  t163 = t47 * r0
  t166 = 0.1e1 / t49 / t163 * t55
  t169 = t45 * t60
  t173 = 0.1e1 / t48 / t62 / t47 * t67
  t178 = t59 * t72
  t181 = 0.1e1 / t74 / r0 * t77
  t186 = t60 ** 2
  t187 = t71 * t186
  t188 = t74 * t163
  t191 = t66 ** 2
  t192 = 0.1e1 / t191
  t193 = 0.1e1 / t49 / t188 * t192
  t198 = t82 * t60
  t203 = t86 * t72
  t208 = t90 * t186
  t211 = -0.10666666666666666666666666666666666666666666666667e-1 * t83 * t166 + 0.42666666666666666666666666666666666666666666666668e-4 * t198 * t173 - 0.85333333333333333333333333333333333333333333333333e-4 * t87 * t173 + 0.34133333333333333333333333333333333333333333333334e-6 * t203 * t181 - 0.512e-6 * t91 * t181 + 0.20480000000000000000000000000000000000000000000001e-8 * t208 * t193
  t213 = t94 * t130
  t216 = 0.1e1 / t42 / t6 * t96
  t220 = 0.1e1 / t107 / t103
  t221 = f.my_piecewise5(t99, 0, t101, 0, t27)
  t224 = f.my_piecewise3(t104, 0, -t220 * t221 / 0.3e1)
  t227 = -0.13333333333333333333333333333333333333333333333333e0 * t216 * t109 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t224
  t231 = t116 * t60
  t236 = t120 * t72
  t241 = t124 * t186
  t244 = -0.10666666666666666666666666666666666666666666666667e-1 * t117 * t166 + 0.42666666666666666666666666666666666666666666666668e-4 * t231 * t173 - 0.85333333333333333333333333333333333333333333333333e-4 * t121 * t173 + 0.34133333333333333333333333333333333333333333333334e-6 * t236 * t181 - 0.512e-6 * t125 * t181 + 0.20480000000000000000000000000000000000000000000001e-8 * t241 * t193
  t246 = t128 * t147
  t251 = t133 * t60
  t256 = t137 * t72
  t261 = t141 * t186
  t264 = -0.10666666666666666666666666666666666666666666666667e-1 * t134 * t166 + 0.42666666666666666666666666666666666666666666666668e-4 * t251 * t173 - 0.85333333333333333333333333333333333333333333333333e-4 * t138 * t173 + 0.34133333333333333333333333333333333333333333333334e-6 * t256 * t181 - 0.512e-6 * t142 * t181 + 0.20480000000000000000000000000000000000000000000001e-8 * t261 * t193
  t266 = t129 ** 2
  t267 = 0.1e1 / t266
  t268 = t145 * t267
  t271 = -0.10666666666666666666666666666666666666666666666667e-1 * t46 * t166 + 0.42666666666666666666666666666666666666666666666668e-4 * t169 * t173 - 0.85333333333333333333333333333333333333333333333333e-4 * t61 * t173 + 0.34133333333333333333333333333333333333333333333334e-6 * t178 * t181 - 0.512e-6 * t73 * t181 + 0.20480000000000000000000000000000000000000000000001e-8 * t187 * t193 + t211 * t113 - t213 * t227 + t244 * t130 - 0.2e1 * t246 * t227 + t264 * t147 - 0.3e1 * t268 * t227
  t275 = t105 * f.p.zeta_threshold
  t277 = f.my_piecewise3(t20, t275, t21 * t19)
  t279 = 0.1e1 / t156 / t6
  t280 = t277 * t279
  t284 = t277 * t157
  t288 = t277 * t42
  t290 = 0.1e1 / t266 / t112
  t291 = t145 * t290
  t292 = t227 ** 2
  t295 = t128 * t267
  t298 = t94 * t147
  t301 = t62 * t163
  t304 = 0.1e1 / t48 / t301 * t67
  t307 = t45 * t72
  t310 = 0.1e1 / t74 / t47 * t77
  t315 = t59 * t186
  t319 = 0.1e1 / t49 / t74 / t62 * t192
  t324 = t186 * s0
  t325 = t71 * t324
  t330 = 0.1e1 / t191 / t54
  t331 = 0.1e1 / t48 / t74 / t301 * t330
  t336 = 0.1e1 / t49 / t62 * t55
  t341 = t133 * t72
  t348 = t137 * t186
  t355 = t141 * t324
  t358 = 0.39111111111111111111111111111111111111111111111112e-1 * t134 * t336 - 0.38400000000000000000000000000000000000000000000001e-3 * t251 * t304 + 0.91022222222222222222222222222222222222222222222228e-6 * t341 * t310 + 0.54044444444444444444444444444444444444444444444444e-3 * t138 * t304 - 0.48924444444444444444444444444444444444444444444446e-5 * t256 * t310 + 0.10922666666666666666666666666666666666666666666667e-7 * t348 * t319 + 0.4608e-5 * t142 * t310 - 0.40277333333333333333333333333333333333333333333336e-7 * t261 * t319 + 0.87381333333333333333333333333333333333333333333340e-10 * t355 * t331
  t365 = t82 * t72
  t372 = t86 * t186
  t379 = t90 * t324
  t382 = 0.39111111111111111111111111111111111111111111111112e-1 * t83 * t336 - 0.38400000000000000000000000000000000000000000000001e-3 * t198 * t304 + 0.91022222222222222222222222222222222222222222222228e-6 * t365 * t310 + 0.54044444444444444444444444444444444444444444444444e-3 * t87 * t304 - 0.48924444444444444444444444444444444444444444444446e-5 * t203 * t310 + 0.10922666666666666666666666666666666666666666666667e-7 * t372 * t319 + 0.4608e-5 * t91 * t310 - 0.40277333333333333333333333333333333333333333333336e-7 * t208 * t319 + 0.87381333333333333333333333333333333333333333333340e-10 * t379 * t331
  t388 = t116 * t72
  t395 = t120 * t186
  t402 = t124 * t324
  t405 = 0.39111111111111111111111111111111111111111111111112e-1 * t117 * t336 - 0.38400000000000000000000000000000000000000000000001e-3 * t231 * t304 + 0.91022222222222222222222222222222222222222222222228e-6 * t388 * t310 + 0.54044444444444444444444444444444444444444444444444e-3 * t121 * t304 - 0.48924444444444444444444444444444444444444444444446e-5 * t236 * t310 + 0.10922666666666666666666666666666666666666666666667e-7 * t395 * t319 + 0.4608e-5 * t125 * t310 - 0.40277333333333333333333333333333333333333333333336e-7 * t241 * t319 + 0.87381333333333333333333333333333333333333333333340e-10 * t402 * t331
  t407 = t264 * t267
  t412 = 0.1e1 / t42 / t24 * t96
  t417 = t103 ** 2
  t419 = 0.1e1 / t107 / t417
  t420 = t221 ** 2
  t423 = f.my_piecewise5(t99, 0, t101, 0, t36)
  t427 = f.my_piecewise3(t104, 0, 0.4e1 / 0.9e1 * t419 * t420 - t220 * t423 / 0.3e1)
  t430 = 0.17777777777777777777777777777777777777777777777777e0 * t412 * t109 - 0.26666666666666666666666666666666666666666666666666e0 * t216 * t224 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t427
  t433 = t244 * t147
  t438 = t211 * t130
  t448 = t382 * t113 + t405 * t130 - 0.6e1 * t407 * t227 - 0.3e1 * t268 * t430 - 0.4e1 * t433 * t227 - 0.2e1 * t246 * t430 - 0.2e1 * t438 * t227 - t213 * t430 + 0.39111111111111111111111111111111111111111111111112e-1 * t46 * t336 + 0.54044444444444444444444444444444444444444444444444e-3 * t61 * t304 + 0.4608e-5 * t73 * t310
  t449 = 0.12e2 * t291 * t292 + 0.6e1 * t295 * t292 + 0.2e1 * t298 * t292 - 0.38400000000000000000000000000000000000000000000001e-3 * t169 * t304 + 0.91022222222222222222222222222222222222222222222228e-6 * t307 * t310 - 0.48924444444444444444444444444444444444444444444446e-5 * t178 * t310 + 0.10922666666666666666666666666666666666666666666667e-7 * t315 * t319 - 0.40277333333333333333333333333333333333333333333336e-7 * t187 * t319 + 0.87381333333333333333333333333333333333333333333340e-10 * t325 * t331 + t358 * t147 + t448
  t454 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t149 - t5 * t158 * t149 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t162 * t271 + t5 * t280 * t149 / 0.12e2 - t5 * t284 * t271 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t288 * t449)
  t456 = r1 <= f.p.dens_threshold
  t457 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t458 = 0.1e1 + t457
  t459 = t458 <= f.p.zeta_threshold
  t460 = t458 ** (0.1e1 / 0.3e1)
  t461 = t460 ** 2
  t462 = 0.1e1 / t461
  t463 = -t27
  t464 = f.my_piecewise5(t14, 0, t10, 0, t463)
  t465 = t464 ** 2
  t468 = -t36
  t469 = f.my_piecewise5(t14, 0, t10, 0, t468)
  t473 = f.my_piecewise3(t459, 0, 0.4e1 / 0.9e1 * t462 * t465 + 0.4e1 / 0.3e1 * t460 * t469)
  t474 = t473 * t42
  t476 = r1 ** 2
  t477 = r1 ** (0.1e1 / 0.3e1)
  t478 = t477 ** 2
  t480 = 0.1e1 / t478 / t476
  t483 = 0.1e1 + 0.4e-2 * s2 * t480
  t485 = t480 / t483
  t488 = s2 ** 2
  t490 = t476 ** 2
  t494 = t483 ** 2
  t496 = 0.1e1 / t477 / t490 / r1 / t494
  t499 = t488 * s2
  t501 = t490 ** 2
  t505 = 0.1e1 / t501 / t494 / t483
  t517 = t81 + 0.4e-2 * t82 * s2 * t485 + 0.16e-4 * t86 * t488 * t496 + 0.64e-7 * t90 * t499 * t505
  t518 = f.my_piecewise5(t101, t11, t99, t15, -t17)
  t519 = 0.1e1 + t518
  t520 = t519 <= f.p.zeta_threshold
  t521 = t519 ** (0.1e1 / 0.3e1)
  t523 = f.my_piecewise3(t520, t106, 0.1e1 / t521)
  t526 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t523
  t538 = t115 + 0.4e-2 * t116 * s2 * t485 + 0.16e-4 * t120 * t488 * t496 + 0.64e-7 * t124 * t499 * t505
  t539 = t526 ** 2
  t540 = 0.1e1 / t539
  t551 = t132 + 0.4e-2 * t133 * s2 * t485 + 0.16e-4 * t137 * t488 * t496 + 0.64e-7 * t141 * t499 * t505
  t553 = 0.1e1 / t539 / t526
  t555 = t44 + 0.4e-2 * t45 * s2 * t485 + 0.16e-4 * t59 * t488 * t496 + 0.64e-7 * t71 * t499 * t505 + t517 / t526 + t538 * t540 + t551 * t553
  t561 = f.my_piecewise3(t459, 0, 0.4e1 / 0.3e1 * t460 * t464)
  t562 = t561 * t157
  t566 = t561 * t42
  t567 = t517 * t540
  t571 = 0.1e1 / t521 / t519
  t572 = f.my_piecewise5(t101, 0, t99, 0, t463)
  t575 = f.my_piecewise3(t520, 0, -t571 * t572 / 0.3e1)
  t578 = -0.13333333333333333333333333333333333333333333333333e0 * t216 * t523 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t575
  t580 = t538 * t553
  t583 = t539 ** 2
  t584 = 0.1e1 / t583
  t585 = t551 * t584
  t588 = -t567 * t578 - 0.2e1 * t580 * t578 - 0.3e1 * t585 * t578
  t593 = f.my_piecewise3(t459, t275, t460 * t458)
  t594 = t593 * t279
  t598 = t593 * t157
  t602 = t593 * t42
  t603 = t517 * t553
  t604 = t578 ** 2
  t611 = t519 ** 2
  t613 = 0.1e1 / t521 / t611
  t614 = t572 ** 2
  t617 = f.my_piecewise5(t101, 0, t99, 0, t468)
  t621 = f.my_piecewise3(t520, 0, 0.4e1 / 0.9e1 * t613 * t614 - t571 * t617 / 0.3e1)
  t624 = 0.17777777777777777777777777777777777777777777777777e0 * t412 * t523 - 0.26666666666666666666666666666666666666666666666666e0 * t216 * t575 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t621
  t626 = t538 * t584
  t632 = 0.1e1 / t583 / t526
  t633 = t551 * t632
  t638 = -t567 * t624 - 0.2e1 * t580 * t624 - 0.3e1 * t585 * t624 + 0.2e1 * t603 * t604 + 0.6e1 * t626 * t604 + 0.12e2 * t633 * t604
  t643 = f.my_piecewise3(t456, 0, -0.3e1 / 0.8e1 * t5 * t474 * t555 - t5 * t562 * t555 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t566 * t588 + t5 * t594 * t555 / 0.12e2 - t5 * t598 * t588 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t602 * t638)
  t653 = t24 ** 2
  t657 = 0.6e1 * t33 - 0.6e1 * t16 / t653
  t658 = f.my_piecewise5(t10, 0, t14, 0, t657)
  t662 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t658)
  t685 = 0.1e1 / t156 / t24
  t698 = 0.1e1 / t48 / t74 * t67
  t702 = 0.1e1 / t188 * t77
  t705 = t186 * t60
  t707 = t74 ** 2
  t712 = 0.1e1 / t707 / t163 / t191 / t66
  t715 = t227 * t430
  t726 = 0.1e1 / t49 / t74 / t63 * t192
  t740 = 0.1e1 / t48 / t707 * t330
  t749 = 0.1e1 / t49 / t63 * t55
  t779 = -0.18251851851851851851851851851851851851851851851852e0 * t83 * t749 + 0.32331851851851851851851851851851851851851851851853e-2 * t198 * t698 - 0.17294222222222222222222222222222222222222222222223e-4 * t365 * t702 + 0.29127111111111111111111111111111111111111111111114e-7 * t82 * t186 * t726 - 0.39632592592592592592592592592592592592592592592592e-2 * t87 * t698 + 0.60453925925925925925925925925925925925925925925928e-4 * t203 * t702 - 0.29491200000000000000000000000000000000000000000001e-6 * t372 * t726 + 0.46603377777777777777777777777777777777777777777781e-9 * t86 * t324 * t740 - 0.46080e-4 * t91 * t702 + 0.65763555555555555555555555555555555555555555555559e-6 * t208 * t726 - 0.30583466666666666666666666666666666666666666666669e-8 * t379 * t740 + 0.46603377777777777777777777777777777777777777777783e-11 * t90 * t705 * t712
  t781 = -0.39632592592592592592592592592592592592592592592592e-2 * t61 * t698 - 0.46080e-4 * t73 * t702 + 0.46603377777777777777777777777777777777777777777783e-11 * t71 * t705 * t712 + 0.18e2 * t295 * t715 + 0.6e1 * t298 * t715 - 0.17294222222222222222222222222222222222222222222223e-4 * t307 * t702 + 0.29127111111111111111111111111111111111111111111114e-7 * t45 * t186 * t726 - 0.29491200000000000000000000000000000000000000000001e-6 * t315 * t726 + 0.32331851851851851851851851851851851851851851851853e-2 * t169 * t698 + 0.60453925925925925925925925925925925925925925925928e-4 * t178 * t702 + 0.65763555555555555555555555555555555555555555555559e-6 * t187 * t726 + 0.46603377777777777777777777777777777777777777777781e-9 * t59 * t324 * t740 - 0.30583466666666666666666666666666666666666666666669e-8 * t325 * t740 + 0.36e2 * t291 * t715 - 0.18251851851851851851851851851851851851851851851852e0 * t46 * t749 + t779 * t113
  t809 = -0.18251851851851851851851851851851851851851851851852e0 * t117 * t749 + 0.32331851851851851851851851851851851851851851851853e-2 * t231 * t698 - 0.17294222222222222222222222222222222222222222222223e-4 * t388 * t702 + 0.29127111111111111111111111111111111111111111111114e-7 * t116 * t186 * t726 - 0.39632592592592592592592592592592592592592592592592e-2 * t121 * t698 + 0.60453925925925925925925925925925925925925925925928e-4 * t236 * t702 - 0.29491200000000000000000000000000000000000000000001e-6 * t395 * t726 + 0.46603377777777777777777777777777777777777777777781e-9 * t120 * t324 * t740 - 0.46080e-4 * t125 * t702 + 0.65763555555555555555555555555555555555555555555559e-6 * t241 * t726 - 0.30583466666666666666666666666666666666666666666669e-8 * t402 * t740 + 0.46603377777777777777777777777777777777777777777783e-11 * t124 * t705 * t712
  t838 = -0.18251851851851851851851851851851851851851851851852e0 * t134 * t749 + 0.32331851851851851851851851851851851851851851851853e-2 * t251 * t698 - 0.17294222222222222222222222222222222222222222222223e-4 * t341 * t702 + 0.29127111111111111111111111111111111111111111111114e-7 * t133 * t186 * t726 - 0.39632592592592592592592592592592592592592592592592e-2 * t138 * t698 + 0.60453925925925925925925925925925925925925925925928e-4 * t256 * t702 - 0.29491200000000000000000000000000000000000000000001e-6 * t348 * t726 + 0.46603377777777777777777777777777777777777777777781e-9 * t137 * t324 * t740 - 0.46080e-4 * t142 * t702 + 0.65763555555555555555555555555555555555555555555559e-6 * t261 * t726 - 0.30583466666666666666666666666666666666666666666669e-8 * t355 * t740 + 0.46603377777777777777777777777777777777777777777783e-11 * t141 * t705 * t712
  t844 = 0.1e1 / t42 / t32 * t96
  t860 = f.my_piecewise5(t99, 0, t101, 0, t657)
  t864 = f.my_piecewise3(t104, 0, -0.28e2 / 0.27e2 / t107 / t417 / t103 * t420 * t221 + 0.4e1 / 0.3e1 * t419 * t221 * t423 - t220 * t860 / 0.3e1)
  t867 = -0.41481481481481481481481481481481481481481481481480e0 * t844 * t109 + 0.53333333333333333333333333333333333333333333333332e0 * t412 * t224 - 0.39999999999999999999999999999999999999999999999999e0 * t216 * t427 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t864
  t893 = t292 * t227
  t907 = t809 * t130 + t838 * t147 - 0.6e1 * t433 * t430 - 0.2e1 * t246 * t867 - 0.3e1 * t268 * t867 - 0.6e1 * t405 * t147 * t227 - 0.9e1 * t407 * t430 - 0.3e1 * t382 * t130 * t227 - 0.9e1 * t358 * t267 * t227 + 0.6e1 * t211 * t147 * t292 + 0.36e2 * t264 * t290 * t292 + 0.18e2 * t244 * t267 * t292 - 0.24e2 * t128 * t290 * t893 - 0.6e1 * t94 * t267 * t893 - 0.60e2 * t145 / t266 / t129 * t893 - 0.3e1 * t438 * t430 - t213 * t867
  t913 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t662 * t42 * t149 - 0.3e1 / 0.8e1 * t5 * t41 * t157 * t149 - 0.9e1 / 0.8e1 * t5 * t43 * t271 + t5 * t155 * t279 * t149 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t158 * t271 - 0.9e1 / 0.8e1 * t5 * t162 * t449 - 0.5e1 / 0.36e2 * t5 * t277 * t685 * t149 + t5 * t280 * t271 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t284 * t449 - 0.3e1 / 0.8e1 * t5 * t288 * (t781 + t907))
  t922 = -t657
  t923 = f.my_piecewise5(t14, 0, t10, 0, t922)
  t927 = f.my_piecewise3(t459, 0, -0.8e1 / 0.27e2 / t461 / t458 * t465 * t464 + 0.4e1 / 0.3e1 * t462 * t464 * t469 + 0.4e1 / 0.3e1 * t460 * t923)
  t960 = t604 * t578
  t963 = t578 * t624
  t981 = f.my_piecewise5(t101, 0, t99, 0, t922)
  t985 = f.my_piecewise3(t520, 0, -0.28e2 / 0.27e2 / t521 / t611 / t519 * t614 * t572 + 0.4e1 / 0.3e1 * t613 * t572 * t617 - t571 * t981 / 0.3e1)
  t988 = -0.41481481481481481481481481481481481481481481481480e0 * t844 * t523 + 0.53333333333333333333333333333333333333333333333332e0 * t412 * t575 - 0.39999999999999999999999999999999999999999999999999e0 * t216 * t621 + 0.39999999999999999999999999999999999999999999999998e0 * t97 * t985
  t1011 = f.my_piecewise3(t456, 0, -0.3e1 / 0.8e1 * t5 * t927 * t42 * t555 - 0.3e1 / 0.8e1 * t5 * t473 * t157 * t555 - 0.9e1 / 0.8e1 * t5 * t474 * t588 + t5 * t561 * t279 * t555 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t562 * t588 - 0.9e1 / 0.8e1 * t5 * t566 * t638 - 0.5e1 / 0.36e2 * t5 * t593 * t685 * t555 + t5 * t594 * t588 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t598 * t638 - 0.3e1 / 0.8e1 * t5 * t602 * (-0.6e1 * t517 * t584 * t960 + 0.6e1 * t603 * t963 - t567 * t988 - 0.24e2 * t538 * t632 * t960 + 0.18e2 * t626 * t963 - 0.2e1 * t580 * t988 - 0.60e2 * t551 / t583 / t539 * t960 + 0.36e2 * t633 * t963 - 0.3e1 * t585 * t988))
  d111 = 0.3e1 * t454 + 0.3e1 * t643 + t6 * (t913 + t1011)

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
  t56 = params.CC_0_[0]
  t57 = params.CC_0_[1]
  t58 = t57 * s0
  t59 = r0 ** 2
  t60 = r0 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t63 = 0.1e1 / t61 / t59
  t66 = 0.1e1 + 0.4e-2 * s0 * t63
  t67 = 0.1e1 / t66
  t68 = t63 * t67
  t71 = params.CC_0_[2]
  t72 = s0 ** 2
  t73 = t71 * t72
  t74 = t59 ** 2
  t75 = t74 * r0
  t78 = t66 ** 2
  t79 = 0.1e1 / t78
  t80 = 0.1e1 / t60 / t75 * t79
  t83 = params.CC_0_[3]
  t84 = t72 * s0
  t85 = t83 * t84
  t86 = t74 ** 2
  t88 = t78 * t66
  t89 = 0.1e1 / t88
  t90 = 0.1e1 / t86 * t89
  t93 = params.CC_1_[0]
  t94 = params.CC_1_[1]
  t95 = t94 * s0
  t98 = params.CC_1_[2]
  t99 = t98 * t72
  t102 = params.CC_1_[3]
  t103 = t102 * t84
  t106 = t93 + 0.4e-2 * t95 * t68 + 0.16e-4 * t99 * t80 + 0.64e-7 * t103 * t90
  t108 = 2 ** (0.1e1 / 0.3e1)
  t109 = 0.1e1 / t54 * t108
  t111 = 0.1e1 + t17 <= f.p.zeta_threshold
  t113 = 0.1e1 - t17 <= f.p.zeta_threshold
  t114 = f.my_piecewise5(t111, t11, t113, t15, t17)
  t115 = 0.1e1 + t114
  t116 = t115 <= f.p.zeta_threshold
  t117 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t118 = 0.1e1 / t117
  t119 = t115 ** (0.1e1 / 0.3e1)
  t121 = f.my_piecewise3(t116, t118, 0.1e1 / t119)
  t124 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t121
  t125 = 0.1e1 / t124
  t127 = params.CC_2_[0]
  t128 = params.CC_2_[1]
  t129 = t128 * s0
  t132 = params.CC_2_[2]
  t133 = t132 * t72
  t136 = params.CC_2_[3]
  t137 = t136 * t84
  t140 = t127 + 0.4e-2 * t129 * t68 + 0.16e-4 * t133 * t80 + 0.64e-7 * t137 * t90
  t141 = t124 ** 2
  t142 = 0.1e1 / t141
  t144 = params.CC_3_[0]
  t145 = params.CC_3_[1]
  t146 = t145 * s0
  t149 = params.CC_3_[2]
  t150 = t149 * t72
  t153 = params.CC_3_[3]
  t154 = t153 * t84
  t157 = t144 + 0.4e-2 * t146 * t68 + 0.16e-4 * t150 * t80 + 0.64e-7 * t154 * t90
  t158 = t141 * t124
  t159 = 0.1e1 / t158
  t161 = t56 + 0.4e-2 * t58 * t68 + 0.16e-4 * t73 * t80 + 0.64e-7 * t85 * t90 + t106 * t125 + t140 * t142 + t157 * t159
  t170 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t171 = t54 ** 2
  t172 = 0.1e1 / t171
  t173 = t170 * t172
  t177 = t170 * t54
  t178 = t59 * r0
  t181 = 0.1e1 / t61 / t178 * t67
  t184 = t57 * t72
  t185 = t74 * t59
  t188 = 0.1e1 / t60 / t185 * t79
  t193 = t71 * t84
  t194 = t86 * r0
  t196 = 0.1e1 / t194 * t89
  t201 = t72 ** 2
  t202 = t83 * t201
  t203 = t86 * t178
  t206 = t78 ** 2
  t207 = 0.1e1 / t206
  t208 = 0.1e1 / t61 / t203 * t207
  t213 = t94 * t72
  t218 = t98 * t84
  t223 = t102 * t201
  t226 = -0.10666666666666666666666666666666666666666666666667e-1 * t95 * t181 + 0.42666666666666666666666666666666666666666666666668e-4 * t213 * t188 - 0.85333333333333333333333333333333333333333333333333e-4 * t99 * t188 + 0.34133333333333333333333333333333333333333333333334e-6 * t218 * t196 - 0.512e-6 * t103 * t196 + 0.20480000000000000000000000000000000000000000000001e-8 * t223 * t208
  t228 = t106 * t142
  t231 = 0.1e1 / t54 / t6 * t108
  t235 = 0.1e1 / t119 / t115
  t236 = f.my_piecewise5(t111, 0, t113, 0, t28)
  t239 = f.my_piecewise3(t116, 0, -t235 * t236 / 0.3e1)
  t242 = -0.13333333333333333333333333333333333333333333333333e0 * t231 * t121 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t239
  t246 = t128 * t72
  t251 = t132 * t84
  t256 = t136 * t201
  t259 = -0.10666666666666666666666666666666666666666666666667e-1 * t129 * t181 + 0.42666666666666666666666666666666666666666666666668e-4 * t246 * t188 - 0.85333333333333333333333333333333333333333333333333e-4 * t133 * t188 + 0.34133333333333333333333333333333333333333333333334e-6 * t251 * t196 - 0.512e-6 * t137 * t196 + 0.20480000000000000000000000000000000000000000000001e-8 * t256 * t208
  t261 = t140 * t159
  t266 = t145 * t72
  t271 = t149 * t84
  t276 = t153 * t201
  t279 = -0.10666666666666666666666666666666666666666666666667e-1 * t146 * t181 + 0.42666666666666666666666666666666666666666666666668e-4 * t266 * t188 - 0.85333333333333333333333333333333333333333333333333e-4 * t150 * t188 + 0.34133333333333333333333333333333333333333333333334e-6 * t271 * t196 - 0.512e-6 * t154 * t196 + 0.20480000000000000000000000000000000000000000000001e-8 * t276 * t208
  t281 = t141 ** 2
  t282 = 0.1e1 / t281
  t283 = t157 * t282
  t286 = -0.10666666666666666666666666666666666666666666666667e-1 * t58 * t181 + 0.42666666666666666666666666666666666666666666666668e-4 * t184 * t188 - 0.85333333333333333333333333333333333333333333333333e-4 * t73 * t188 + 0.34133333333333333333333333333333333333333333333334e-6 * t193 * t196 - 0.512e-6 * t85 * t196 + 0.20480000000000000000000000000000000000000000000001e-8 * t202 * t208 + t226 * t125 - t228 * t242 + t259 * t142 - 0.2e1 * t261 * t242 + t279 * t159 - 0.3e1 * t283 * t242
  t292 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t294 = 0.1e1 / t171 / t6
  t295 = t292 * t294
  t299 = t292 * t172
  t303 = t292 * t54
  t305 = 0.1e1 / t281 / t124
  t306 = t157 * t305
  t307 = t242 ** 2
  t310 = t140 * t282
  t313 = t106 * t159
  t316 = t74 * t178
  t319 = 0.1e1 / t60 / t316 * t79
  t322 = t57 * t84
  t325 = 0.1e1 / t86 / t59 * t89
  t330 = t71 * t201
  t331 = t86 * t74
  t334 = 0.1e1 / t61 / t331 * t207
  t339 = t201 * s0
  t340 = t83 * t339
  t345 = 0.1e1 / t206 / t66
  t346 = 0.1e1 / t60 / t86 / t316 * t345
  t351 = 0.1e1 / t61 / t74 * t67
  t356 = t128 * t84
  t363 = t132 * t201
  t370 = t136 * t339
  t373 = 0.39111111111111111111111111111111111111111111111112e-1 * t129 * t351 - 0.38400000000000000000000000000000000000000000000001e-3 * t246 * t319 + 0.91022222222222222222222222222222222222222222222228e-6 * t356 * t325 + 0.54044444444444444444444444444444444444444444444444e-3 * t133 * t319 - 0.48924444444444444444444444444444444444444444444446e-5 * t251 * t325 + 0.10922666666666666666666666666666666666666666666667e-7 * t363 * t334 + 0.4608e-5 * t137 * t325 - 0.40277333333333333333333333333333333333333333333336e-7 * t256 * t334 + 0.87381333333333333333333333333333333333333333333340e-10 * t370 * t346
  t380 = t145 * t84
  t387 = t149 * t201
  t394 = t153 * t339
  t397 = 0.39111111111111111111111111111111111111111111111112e-1 * t146 * t351 - 0.38400000000000000000000000000000000000000000000001e-3 * t266 * t319 + 0.91022222222222222222222222222222222222222222222228e-6 * t380 * t325 + 0.54044444444444444444444444444444444444444444444444e-3 * t150 * t319 - 0.48924444444444444444444444444444444444444444444446e-5 * t271 * t325 + 0.10922666666666666666666666666666666666666666666667e-7 * t387 * t334 + 0.4608e-5 * t154 * t325 - 0.40277333333333333333333333333333333333333333333336e-7 * t276 * t334 + 0.87381333333333333333333333333333333333333333333340e-10 * t394 * t346
  t403 = t94 * t84
  t410 = t98 * t201
  t417 = t102 * t339
  t420 = 0.39111111111111111111111111111111111111111111111112e-1 * t95 * t351 - 0.38400000000000000000000000000000000000000000000001e-3 * t213 * t319 + 0.91022222222222222222222222222222222222222222222228e-6 * t403 * t325 + 0.54044444444444444444444444444444444444444444444444e-3 * t99 * t319 - 0.48924444444444444444444444444444444444444444444446e-5 * t218 * t325 + 0.10922666666666666666666666666666666666666666666667e-7 * t410 * t334 + 0.4608e-5 * t103 * t325 - 0.40277333333333333333333333333333333333333333333336e-7 * t223 * t334 + 0.87381333333333333333333333333333333333333333333340e-10 * t417 * t346
  t422 = t279 * t282
  t427 = 0.1e1 / t54 / t25 * t108
  t432 = t115 ** 2
  t434 = 0.1e1 / t119 / t432
  t435 = t236 ** 2
  t438 = f.my_piecewise5(t111, 0, t113, 0, t40)
  t442 = f.my_piecewise3(t116, 0, 0.4e1 / 0.9e1 * t434 * t435 - t235 * t438 / 0.3e1)
  t445 = 0.17777777777777777777777777777777777777777777777777e0 * t427 * t121 - 0.26666666666666666666666666666666666666666666666666e0 * t231 * t239 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t442
  t448 = t259 * t159
  t453 = t226 * t142
  t463 = t397 * t159 + t420 * t125 - 0.6e1 * t422 * t242 - 0.3e1 * t283 * t445 - 0.4e1 * t448 * t242 - 0.2e1 * t261 * t445 - 0.2e1 * t453 * t242 - t228 * t445 + 0.39111111111111111111111111111111111111111111111112e-1 * t58 * t351 + 0.54044444444444444444444444444444444444444444444444e-3 * t73 * t319 + 0.4608e-5 * t85 * t325
  t464 = 0.12e2 * t306 * t307 + 0.6e1 * t310 * t307 + 0.2e1 * t313 * t307 - 0.38400000000000000000000000000000000000000000000001e-3 * t184 * t319 + 0.91022222222222222222222222222222222222222222222228e-6 * t322 * t325 - 0.48924444444444444444444444444444444444444444444446e-5 * t193 * t325 + 0.10922666666666666666666666666666666666666666666667e-7 * t330 * t334 - 0.40277333333333333333333333333333333333333333333336e-7 * t202 * t334 + 0.87381333333333333333333333333333333333333333333340e-10 * t340 * t346 + t373 * t142 + t463
  t468 = t117 * f.p.zeta_threshold
  t470 = f.my_piecewise3(t20, t468, t21 * t19)
  t472 = 0.1e1 / t171 / t25
  t473 = t470 * t472
  t477 = t470 * t294
  t481 = t470 * t172
  t485 = t470 * t54
  t488 = 0.1e1 / t61 / t75 * t67
  t493 = 0.1e1 / t60 / t86 * t79
  t497 = 0.1e1 / t203 * t89
  t500 = t94 * t201
  t504 = 0.1e1 / t61 / t86 / t75 * t207
  t513 = t98 * t339
  t514 = t86 ** 2
  t517 = 0.1e1 / t60 / t514 * t345
  t526 = t201 * t72
  t527 = t102 * t526
  t531 = 0.1e1 / t206 / t78
  t532 = 0.1e1 / t514 / t178 * t531
  t535 = -0.18251851851851851851851851851851851851851851851852e0 * t95 * t488 + 0.32331851851851851851851851851851851851851851851853e-2 * t213 * t493 - 0.17294222222222222222222222222222222222222222222223e-4 * t403 * t497 + 0.29127111111111111111111111111111111111111111111114e-7 * t500 * t504 - 0.39632592592592592592592592592592592592592592592592e-2 * t99 * t493 + 0.60453925925925925925925925925925925925925925925928e-4 * t218 * t497 - 0.29491200000000000000000000000000000000000000000001e-6 * t410 * t504 + 0.46603377777777777777777777777777777777777777777781e-9 * t513 * t517 - 0.46080e-4 * t103 * t497 + 0.65763555555555555555555555555555555555555555555559e-6 * t223 * t504 - 0.30583466666666666666666666666666666666666666666669e-8 * t417 * t517 + 0.46603377777777777777777777777777777777777777777783e-11 * t527 * t532
  t543 = t128 * t201
  t552 = t132 * t339
  t561 = t136 * t526
  t564 = -0.18251851851851851851851851851851851851851851851852e0 * t129 * t488 + 0.32331851851851851851851851851851851851851851851853e-2 * t246 * t493 - 0.17294222222222222222222222222222222222222222222223e-4 * t356 * t497 + 0.29127111111111111111111111111111111111111111111114e-7 * t543 * t504 - 0.39632592592592592592592592592592592592592592592592e-2 * t133 * t493 + 0.60453925925925925925925925925925925925925925925928e-4 * t251 * t497 - 0.29491200000000000000000000000000000000000000000001e-6 * t363 * t504 + 0.46603377777777777777777777777777777777777777777781e-9 * t552 * t517 - 0.46080e-4 * t137 * t497 + 0.65763555555555555555555555555555555555555555555559e-6 * t256 * t504 - 0.30583466666666666666666666666666666666666666666669e-8 * t370 * t517 + 0.46603377777777777777777777777777777777777777777783e-11 * t561 * t532
  t572 = t145 * t201
  t581 = t149 * t339
  t590 = t153 * t526
  t593 = -0.18251851851851851851851851851851851851851851851852e0 * t146 * t488 + 0.32331851851851851851851851851851851851851851851853e-2 * t266 * t493 - 0.17294222222222222222222222222222222222222222222223e-4 * t380 * t497 + 0.29127111111111111111111111111111111111111111111114e-7 * t572 * t504 - 0.39632592592592592592592592592592592592592592592592e-2 * t150 * t493 + 0.60453925925925925925925925925925925925925925925928e-4 * t271 * t497 - 0.29491200000000000000000000000000000000000000000001e-6 * t387 * t504 + 0.46603377777777777777777777777777777777777777777781e-9 * t581 * t517 - 0.46080e-4 * t154 * t497 + 0.65763555555555555555555555555555555555555555555559e-6 * t276 * t504 - 0.30583466666666666666666666666666666666666666666669e-8 * t394 * t517 + 0.46603377777777777777777777777777777777777777777783e-11 * t590 * t532
  t595 = t242 * t445
  t612 = t57 * t201
  t617 = t71 * t339
  t622 = t83 * t526
  t625 = t535 * t125 + t564 * t142 + t593 * t159 + 0.36e2 * t306 * t595 + 0.18e2 * t310 * t595 + 0.65763555555555555555555555555555555555555555555559e-6 * t202 * t504 + 0.32331851851851851851851851851851851851851851851853e-2 * t184 * t493 + 0.60453925925925925925925925925925925925925925925928e-4 * t193 * t497 - 0.18251851851851851851851851851851851851851851851852e0 * t58 * t488 - 0.39632592592592592592592592592592592592592592592592e-2 * t73 * t493 - 0.46080e-4 * t85 * t497 + 0.29127111111111111111111111111111111111111111111114e-7 * t612 * t504 - 0.29491200000000000000000000000000000000000000000001e-6 * t330 * t504 + 0.46603377777777777777777777777777777777777777777781e-9 * t617 * t517 - 0.30583466666666666666666666666666666666666666666669e-8 * t340 * t517 + 0.46603377777777777777777777777777777777777777777783e-11 * t622 * t532
  t630 = t373 * t159
  t633 = t226 * t159
  t636 = t279 * t305
  t639 = t259 * t282
  t642 = t106 * t282
  t643 = t307 * t242
  t647 = 0.1e1 / t281 / t141
  t648 = t157 * t647
  t651 = t140 * t305
  t658 = 0.1e1 / t54 / t36 * t108
  t667 = 0.1e1 / t119 / t432 / t115
  t671 = t434 * t236
  t674 = f.my_piecewise5(t111, 0, t113, 0, t48)
  t678 = f.my_piecewise3(t116, 0, -0.28e2 / 0.27e2 * t667 * t435 * t236 + 0.4e1 / 0.3e1 * t671 * t438 - t235 * t674 / 0.3e1)
  t681 = -0.41481481481481481481481481481481481481481481481480e0 * t658 * t121 + 0.53333333333333333333333333333333333333333333333332e0 * t427 * t239 - 0.39999999999999999999999999999999999999999999999999e0 * t231 * t442 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t678
  t689 = t420 * t142
  t694 = t397 * t282
  t697 = 0.6e1 * t313 * t595 - 0.17294222222222222222222222222222222222222222222223e-4 * t322 * t497 - 0.6e1 * t630 * t242 + 0.6e1 * t633 * t307 + 0.36e2 * t636 * t307 + 0.18e2 * t639 * t307 - 0.6e1 * t642 * t643 - 0.60e2 * t648 * t643 - 0.24e2 * t651 * t643 - 0.3e1 * t453 * t445 - t228 * t681 - 0.6e1 * t448 * t445 - 0.2e1 * t261 * t681 - 0.3e1 * t283 * t681 - 0.3e1 * t689 * t242 - 0.9e1 * t422 * t445 - 0.9e1 * t694 * t242
  t698 = t625 + t697
  t703 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t161 - 0.3e1 / 0.8e1 * t5 * t173 * t161 - 0.9e1 / 0.8e1 * t5 * t177 * t286 + t5 * t295 * t161 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t299 * t286 - 0.9e1 / 0.8e1 * t5 * t303 * t464 - 0.5e1 / 0.36e2 * t5 * t473 * t161 + t5 * t477 * t286 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t481 * t464 - 0.3e1 / 0.8e1 * t5 * t485 * t698)
  t705 = r1 <= f.p.dens_threshold
  t706 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t707 = 0.1e1 + t706
  t708 = t707 <= f.p.zeta_threshold
  t709 = t707 ** (0.1e1 / 0.3e1)
  t710 = t709 ** 2
  t712 = 0.1e1 / t710 / t707
  t713 = -t28
  t714 = f.my_piecewise5(t14, 0, t10, 0, t713)
  t715 = t714 ** 2
  t719 = 0.1e1 / t710
  t720 = t719 * t714
  t721 = -t40
  t722 = f.my_piecewise5(t14, 0, t10, 0, t721)
  t725 = -t48
  t726 = f.my_piecewise5(t14, 0, t10, 0, t725)
  t730 = f.my_piecewise3(t708, 0, -0.8e1 / 0.27e2 * t712 * t715 * t714 + 0.4e1 / 0.3e1 * t720 * t722 + 0.4e1 / 0.3e1 * t709 * t726)
  t731 = t730 * t54
  t733 = r1 ** 2
  t734 = r1 ** (0.1e1 / 0.3e1)
  t735 = t734 ** 2
  t737 = 0.1e1 / t735 / t733
  t740 = 0.1e1 + 0.4e-2 * s2 * t737
  t742 = t737 / t740
  t745 = s2 ** 2
  t747 = t733 ** 2
  t751 = t740 ** 2
  t753 = 0.1e1 / t734 / t747 / r1 / t751
  t756 = t745 * s2
  t758 = t747 ** 2
  t762 = 0.1e1 / t758 / t751 / t740
  t774 = t93 + 0.4e-2 * t94 * s2 * t742 + 0.16e-4 * t98 * t745 * t753 + 0.64e-7 * t102 * t756 * t762
  t775 = f.my_piecewise5(t113, t11, t111, t15, -t17)
  t776 = 0.1e1 + t775
  t777 = t776 <= f.p.zeta_threshold
  t778 = t776 ** (0.1e1 / 0.3e1)
  t780 = f.my_piecewise3(t777, t118, 0.1e1 / t778)
  t783 = 0.1e1 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t780
  t795 = t127 + 0.4e-2 * t128 * s2 * t742 + 0.16e-4 * t132 * t745 * t753 + 0.64e-7 * t136 * t756 * t762
  t796 = t783 ** 2
  t797 = 0.1e1 / t796
  t808 = t144 + 0.4e-2 * t145 * s2 * t742 + 0.16e-4 * t149 * t745 * t753 + 0.64e-7 * t153 * t756 * t762
  t809 = t796 * t783
  t810 = 0.1e1 / t809
  t812 = t56 + 0.4e-2 * t57 * s2 * t742 + 0.16e-4 * t71 * t745 * t753 + 0.64e-7 * t83 * t756 * t762 + t774 / t783 + t795 * t797 + t808 * t810
  t821 = f.my_piecewise3(t708, 0, 0.4e1 / 0.9e1 * t719 * t715 + 0.4e1 / 0.3e1 * t709 * t722)
  t822 = t821 * t172
  t826 = t821 * t54
  t827 = t774 * t797
  t831 = 0.1e1 / t778 / t776
  t832 = f.my_piecewise5(t113, 0, t111, 0, t713)
  t835 = f.my_piecewise3(t777, 0, -t831 * t832 / 0.3e1)
  t838 = -0.13333333333333333333333333333333333333333333333333e0 * t231 * t780 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t835
  t840 = t795 * t810
  t843 = t796 ** 2
  t844 = 0.1e1 / t843
  t845 = t808 * t844
  t848 = -t827 * t838 - 0.2e1 * t840 * t838 - 0.3e1 * t845 * t838
  t854 = f.my_piecewise3(t708, 0, 0.4e1 / 0.3e1 * t709 * t714)
  t855 = t854 * t294
  t859 = t854 * t172
  t863 = t854 * t54
  t864 = t774 * t810
  t865 = t838 ** 2
  t872 = t776 ** 2
  t874 = 0.1e1 / t778 / t872
  t875 = t832 ** 2
  t878 = f.my_piecewise5(t113, 0, t111, 0, t721)
  t882 = f.my_piecewise3(t777, 0, 0.4e1 / 0.9e1 * t874 * t875 - t831 * t878 / 0.3e1)
  t885 = 0.17777777777777777777777777777777777777777777777777e0 * t427 * t780 - 0.26666666666666666666666666666666666666666666666666e0 * t231 * t835 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t882
  t887 = t795 * t844
  t893 = 0.1e1 / t843 / t783
  t894 = t808 * t893
  t899 = -t827 * t885 - 0.2e1 * t840 * t885 - 0.3e1 * t845 * t885 + 0.2e1 * t864 * t865 + 0.6e1 * t887 * t865 + 0.12e2 * t894 * t865
  t904 = f.my_piecewise3(t708, t468, t709 * t707)
  t905 = t904 * t472
  t909 = t904 * t294
  t913 = t904 * t172
  t917 = t904 * t54
  t918 = t774 * t844
  t919 = t865 * t838
  t922 = t838 * t885
  t933 = 0.1e1 / t778 / t872 / t776
  t937 = t874 * t832
  t940 = f.my_piecewise5(t113, 0, t111, 0, t725)
  t944 = f.my_piecewise3(t777, 0, -0.28e2 / 0.27e2 * t933 * t875 * t832 + 0.4e1 / 0.3e1 * t937 * t878 - t831 * t940 / 0.3e1)
  t947 = -0.41481481481481481481481481481481481481481481481480e0 * t658 * t780 + 0.53333333333333333333333333333333333333333333333332e0 * t427 * t835 - 0.39999999999999999999999999999999999999999999999999e0 * t231 * t882 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t944
  t949 = t795 * t893
  t957 = 0.1e1 / t843 / t796
  t958 = t808 * t957
  t965 = -t827 * t947 - 0.2e1 * t840 * t947 - 0.3e1 * t845 * t947 + 0.6e1 * t864 * t922 + 0.18e2 * t887 * t922 + 0.36e2 * t894 * t922 - 0.6e1 * t918 * t919 - 0.24e2 * t949 * t919 - 0.60e2 * t958 * t919
  t970 = f.my_piecewise3(t705, 0, -0.3e1 / 0.8e1 * t5 * t731 * t812 - 0.3e1 / 0.8e1 * t5 * t822 * t812 - 0.9e1 / 0.8e1 * t5 * t826 * t848 + t5 * t855 * t812 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t859 * t848 - 0.9e1 / 0.8e1 * t5 * t863 * t899 - 0.5e1 / 0.36e2 * t5 * t905 * t812 + t5 * t909 * t848 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t913 * t899 - 0.3e1 / 0.8e1 * t5 * t917 * t965)
  t992 = 0.1e1 / t171 / t36
  t997 = t19 ** 2
  t1000 = t30 ** 2
  t1006 = t41 ** 2
  t1015 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t1016 = f.my_piecewise5(t10, 0, t14, 0, t1015)
  t1020 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t997 * t1000 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t1006 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t1016)
  t1046 = 0.1e1 / t61 / t185 * t67
  t1051 = 0.1e1 / t60 / t194 * t79
  t1055 = 0.1e1 / t331 * t89
  t1061 = 0.1e1 / t61 / t86 / t185 * t207
  t1068 = 0.1e1 / t60 / t514 / r0 * t345
  t1082 = 0.1e1 / t514 / t74 * t531
  t1093 = t201 * t84
  t1100 = 0.1e1 / t61 / t514 / t185 / t206 / t88
  t1103 = 0.10342716049382716049382716049382716049382716049383e1 * t95 * t1046 - 0.28890074074074074074074074074074074074074074074075e-1 * t213 * t1051 + 0.25921106172839506172839506172839506172839506172840e-3 * t403 * t1055 - 0.95148562962962962962962962962962962962962962962971e-6 * t500 * t1061 + 0.12427567407407407407407407407407407407407407407409e-8 * t94 * t339 * t1068 + 0.33027160493827160493827160493827160493827160493827e-1 * t99 * t1051 - 0.74954271604938271604938271604938271604938271604941e-3 * t218 * t1055 + 0.59649896296296296296296296296296296296296296296299e-5 * t410 * t1061 - 0.20194797037037037037037037037037037037037037037038e-7 * t513 * t1068 + 0.24855134814814814814814814814814814814814814814817e-10 * t98 * t526 * t1082 + 0.506880e-3 * t103 * t1055 - 0.10462245925925925925925925925925925925925925925926e-4 * t223 * t1061 + 0.78012112592592592592592592592592592592592592592598e-7 * t417 * t1068 - 0.25165824000000000000000000000000000000000000000003e-9 * t527 * t1082 + 0.29826161777777777777777777777777777777777777777782e-12 * t102 * t1093 * t1100
  t1138 = 0.10342716049382716049382716049382716049382716049383e1 * t129 * t1046 - 0.28890074074074074074074074074074074074074074074075e-1 * t246 * t1051 + 0.25921106172839506172839506172839506172839506172840e-3 * t356 * t1055 - 0.95148562962962962962962962962962962962962962962971e-6 * t543 * t1061 + 0.12427567407407407407407407407407407407407407407409e-8 * t128 * t339 * t1068 + 0.33027160493827160493827160493827160493827160493827e-1 * t133 * t1051 - 0.74954271604938271604938271604938271604938271604941e-3 * t251 * t1055 + 0.59649896296296296296296296296296296296296296296299e-5 * t363 * t1061 - 0.20194797037037037037037037037037037037037037037038e-7 * t552 * t1068 + 0.24855134814814814814814814814814814814814814814817e-10 * t132 * t526 * t1082 + 0.506880e-3 * t137 * t1055 - 0.10462245925925925925925925925925925925925925925926e-4 * t256 * t1061 + 0.78012112592592592592592592592592592592592592592598e-7 * t370 * t1068 - 0.25165824000000000000000000000000000000000000000003e-9 * t561 * t1082 + 0.29826161777777777777777777777777777777777777777782e-12 * t136 * t1093 * t1100
  t1173 = 0.10342716049382716049382716049382716049382716049383e1 * t146 * t1046 - 0.28890074074074074074074074074074074074074074074075e-1 * t266 * t1051 + 0.25921106172839506172839506172839506172839506172840e-3 * t380 * t1055 - 0.95148562962962962962962962962962962962962962962971e-6 * t572 * t1061 + 0.12427567407407407407407407407407407407407407407409e-8 * t145 * t339 * t1068 + 0.33027160493827160493827160493827160493827160493827e-1 * t150 * t1051 - 0.74954271604938271604938271604938271604938271604941e-3 * t271 * t1055 + 0.59649896296296296296296296296296296296296296296299e-5 * t387 * t1061 - 0.20194797037037037037037037037037037037037037037038e-7 * t581 * t1068 + 0.24855134814814814814814814814814814814814814814817e-10 * t149 * t526 * t1082 + 0.506880e-3 * t154 * t1055 - 0.10462245925925925925925925925925925925925925925926e-4 * t276 * t1061 + 0.78012112592592592592592592592592592592592592592598e-7 * t394 * t1068 - 0.25165824000000000000000000000000000000000000000003e-9 * t590 * t1082 + 0.29826161777777777777777777777777777777777777777782e-12 * t153 * t1093 * t1100
  t1176 = t307 ** 2
  t1189 = t445 ** 2
  t1194 = 0.1e1 / t54 / t44 * t108
  t1203 = t432 ** 2
  t1206 = t435 ** 2
  t1212 = t438 ** 2
  t1217 = f.my_piecewise5(t111, 0, t113, 0, t1015)
  t1221 = f.my_piecewise3(t116, 0, 0.280e3 / 0.81e2 / t119 / t1203 * t1206 - 0.56e2 / 0.9e1 * t667 * t435 * t438 + 0.4e1 / 0.3e1 * t434 * t1212 + 0.16e2 / 0.9e1 * t671 * t674 - t235 * t1217 / 0.3e1)
  t1224 = 0.13827160493827160493827160493827160493827160493827e1 * t1194 * t121 - 0.16592592592592592592592592592592592592592592592592e1 * t658 * t239 + 0.10666666666666666666666666666666666666666666666666e1 * t427 * t442 - 0.53333333333333333333333333333333333333333333333332e0 * t231 * t678 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t1221
  t1227 = t242 * t681
  t1230 = t307 * t445
  t1235 = t1103 * t125 + t1138 * t142 + t1173 * t159 + 0.24e2 * t106 * t305 * t1176 + 0.360e3 * t157 / t281 / t158 * t1176 - 0.4e1 * t453 * t681 - 0.240e3 * t279 * t647 * t643 + 0.18e2 * t310 * t1189 - 0.3e1 * t283 * t1224 + 0.48e2 * t306 * t1227 - 0.144e3 * t651 * t1230 + 0.506880e-3 * t85 * t1055
  t1264 = -0.36e2 * t642 * t1230 - 0.360e3 * t648 * t1230 - 0.10462245925925925925925925925925925925925925925926e-4 * t202 * t1061 - 0.28890074074074074074074074074074074074074074074075e-1 * t184 * t1051 - 0.74954271604938271604938271604938271604938271604941e-3 * t193 * t1055 + 0.10342716049382716049382716049382716049382716049383e1 * t58 * t1046 + 0.33027160493827160493827160493827160493827160493827e-1 * t73 * t1051 + 0.24e2 * t310 * t1227 + 0.144e3 * t636 * t595 - 0.95148562962962962962962962962962962962962962962971e-6 * t612 * t1061 + 0.12427567407407407407407407407407407407407407407409e-8 * t57 * t339 * t1068 - 0.20194797037037037037037037037037037037037037037038e-7 * t617 * t1068 + 0.24855134814814814814814814814814814814814814814817e-10 * t71 * t526 * t1082
  t1296 = -0.25165824000000000000000000000000000000000000000003e-9 * t622 * t1082 + 0.29826161777777777777777777777777777777777777777782e-12 * t83 * t1093 * t1100 + 0.24e2 * t633 * t595 + 0.8e1 * t313 * t1227 + 0.78012112592592592592592592592592592592592592592598e-7 * t340 * t1068 + 0.25921106172839506172839506172839506172839506172840e-3 * t322 * t1055 + 0.59649896296296296296296296296296296296296296296299e-5 * t330 * t1061 + 0.72e2 * t639 * t595 + 0.36e2 * t373 * t282 * t307 + 0.12e2 * t420 * t159 * t307 + 0.36e2 * t306 * t1189 - 0.6e1 * t689 * t445 - 0.4e1 * t535 * t142 * t242
  t1328 = 0.120e3 * t140 * t647 * t1176 - 0.8e1 * t564 * t159 * t242 - 0.24e2 * t226 * t282 * t643 - 0.12e2 * t593 * t282 * t242 - 0.96e2 * t259 * t305 * t643 + 0.72e2 * t397 * t305 * t307 + 0.6e1 * t313 * t1189 - t228 * t1224 - 0.2e1 * t261 * t1224 - 0.12e2 * t422 * t681 - 0.12e2 * t630 * t445 - 0.18e2 * t694 * t445 - 0.8e1 * t448 * t681
  t1334 = t5 * t170 * t294 * t161 / 0.2e1 + t5 * t295 * t286 - 0.3e1 / 0.2e1 * t5 * t173 * t286 - 0.9e1 / 0.4e1 * t5 * t177 * t464 - 0.3e1 / 0.2e1 * t5 * t299 * t464 - t5 * t53 * t172 * t161 / 0.2e1 + 0.10e2 / 0.27e2 * t5 * t470 * t992 * t161 - 0.3e1 / 0.8e1 * t5 * t1020 * t54 * t161 - 0.3e1 / 0.2e1 * t5 * t55 * t286 - t5 * t481 * t698 / 0.2e1 + t5 * t477 * t464 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t473 * t286 - 0.3e1 / 0.2e1 * t5 * t303 * t698 - 0.5e1 / 0.9e1 * t5 * t292 * t472 * t161 - 0.3e1 / 0.8e1 * t5 * t485 * (t1235 + t1264 + t1296 + t1328)
  t1335 = f.my_piecewise3(t1, 0, t1334)
  t1345 = t707 ** 2
  t1348 = t715 ** 2
  t1354 = t722 ** 2
  t1359 = -t1015
  t1360 = f.my_piecewise5(t14, 0, t10, 0, t1359)
  t1364 = f.my_piecewise3(t708, 0, 0.40e2 / 0.81e2 / t710 / t1345 * t1348 - 0.16e2 / 0.9e1 * t712 * t715 * t722 + 0.4e1 / 0.3e1 * t719 * t1354 + 0.16e2 / 0.9e1 * t720 * t726 + 0.4e1 / 0.3e1 * t709 * t1360)
  t1403 = t865 ** 2
  t1406 = t865 * t885
  t1409 = t885 ** 2
  t1412 = t838 * t947
  t1423 = t872 ** 2
  t1426 = t875 ** 2
  t1432 = t878 ** 2
  t1437 = f.my_piecewise5(t113, 0, t111, 0, t1359)
  t1441 = f.my_piecewise3(t777, 0, 0.280e3 / 0.81e2 / t778 / t1423 * t1426 - 0.56e2 / 0.9e1 * t933 * t875 * t878 + 0.4e1 / 0.3e1 * t874 * t1432 + 0.16e2 / 0.9e1 * t937 * t940 - t831 * t1437 / 0.3e1)
  t1444 = 0.13827160493827160493827160493827160493827160493827e1 * t1194 * t780 - 0.16592592592592592592592592592592592592592592592592e1 * t658 * t835 + 0.10666666666666666666666666666666666666666666666666e1 * t427 * t882 - 0.53333333333333333333333333333333333333333333333332e0 * t231 * t944 + 0.39999999999999999999999999999999999999999999999998e0 * t109 * t1441
  t1470 = 0.24e2 * t774 * t893 * t1403 - 0.36e2 * t918 * t1406 + 0.6e1 * t864 * t1409 + 0.8e1 * t864 * t1412 - t827 * t1444 + 0.120e3 * t795 * t957 * t1403 - 0.144e3 * t949 * t1406 + 0.18e2 * t887 * t1409 + 0.24e2 * t887 * t1412 - 0.2e1 * t840 * t1444 + 0.360e3 * t808 / t843 / t809 * t1403 - 0.360e3 * t958 * t1406 + 0.36e2 * t894 * t1409 + 0.48e2 * t894 * t1412 - 0.3e1 * t845 * t1444
  t1474 = -0.3e1 / 0.2e1 * t5 * t863 * t965 - 0.5e1 / 0.9e1 * t5 * t905 * t848 + t5 * t909 * t899 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t1364 * t54 * t812 - 0.3e1 / 0.2e1 * t5 * t731 * t848 - 0.3e1 / 0.2e1 * t5 * t822 * t848 - 0.9e1 / 0.4e1 * t5 * t826 * t899 + t5 * t855 * t848 - 0.3e1 / 0.2e1 * t5 * t859 * t899 + 0.10e2 / 0.27e2 * t5 * t904 * t992 * t812 - t5 * t730 * t172 * t812 / 0.2e1 + t5 * t821 * t294 * t812 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t854 * t472 * t812 - t5 * t913 * t965 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t917 * t1470
  t1475 = f.my_piecewise3(t705, 0, t1474)
  d1111 = 0.4e1 * t703 + 0.4e1 * t970 + t6 * (t1335 + t1475)

  res = {'v4rho4': d1111}
  return res
