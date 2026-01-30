"""Generated from lda_c_hl.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
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
  params_hl_c_raw = params.hl_c
  if isinstance(params_hl_c_raw, (str, bytes, dict)):
    params_hl_c = params_hl_c_raw
  else:
    try:
      params_hl_c_seq = list(params_hl_c_raw)
    except TypeError:
      params_hl_c = params_hl_c_raw
    else:
      params_hl_c_seq = np.asarray(params_hl_c_seq, dtype=np.float64)
      params_hl_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_hl_c_seq))
  params_hl_r_raw = params.hl_r
  if isinstance(params_hl_r_raw, (str, bytes, dict)):
    params_hl_r = params_hl_r_raw
  else:
    try:
      params_hl_r_seq = list(params_hl_r_raw)
    except TypeError:
      params_hl_r = params_hl_r_raw
    else:
      params_hl_r_seq = np.asarray(params_hl_r_seq, dtype=np.float64)
      params_hl_r = np.concatenate((np.array([np.nan], dtype=np.float64), params_hl_r_seq))

  hl_xx = lambda k, rs: rs / params_hl_r[k]

  hl_f0 = lambda k, rs: -params_hl_c[k] * ((1 + hl_xx(k, rs) ** 3) * jnp.log(1 + 1 / hl_xx(k, rs)) - hl_xx(k, rs) ** 2 + 1 / 2 * hl_xx(k, rs) - 1 / 3)

  hl_f = lambda rs, zeta: hl_f0(1, rs) + f.f_zeta(zeta) * (hl_f0(2, rs) - hl_f0(1, rs))

  functional_body = lambda rs, zeta: hl_f(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_hl_c_raw = params.hl_c
  if isinstance(params_hl_c_raw, (str, bytes, dict)):
    params_hl_c = params_hl_c_raw
  else:
    try:
      params_hl_c_seq = list(params_hl_c_raw)
    except TypeError:
      params_hl_c = params_hl_c_raw
    else:
      params_hl_c_seq = np.asarray(params_hl_c_seq, dtype=np.float64)
      params_hl_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_hl_c_seq))
  params_hl_r_raw = params.hl_r
  if isinstance(params_hl_r_raw, (str, bytes, dict)):
    params_hl_r = params_hl_r_raw
  else:
    try:
      params_hl_r_seq = list(params_hl_r_raw)
    except TypeError:
      params_hl_r = params_hl_r_raw
    else:
      params_hl_r_seq = np.asarray(params_hl_r_seq, dtype=np.float64)
      params_hl_r = np.concatenate((np.array([np.nan], dtype=np.float64), params_hl_r_seq))

  hl_xx = lambda k, rs: rs / params_hl_r[k]

  hl_f0 = lambda k, rs: -params_hl_c[k] * ((1 + hl_xx(k, rs) ** 3) * jnp.log(1 + 1 / hl_xx(k, rs)) - hl_xx(k, rs) ** 2 + 1 / 2 * hl_xx(k, rs) - 1 / 3)

  hl_f = lambda rs, zeta: hl_f0(1, rs) + f.f_zeta(zeta) * (hl_f0(2, rs) - hl_f0(1, rs))

  functional_body = lambda rs, zeta: hl_f(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t1 = params.hl_c[0]
  t2 = 0.1e1 / jnp.pi
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t6 = params.hl_r[0]
  t7 = t6 ** 2
  t9 = 0.1e1 / t7 / t6
  t12 = 0.1e1 + 0.3e1 / 0.4e1 * t5 * t9
  t13 = 3 ** (0.1e1 / 0.3e1)
  t14 = t13 ** 2
  t15 = t2 ** (0.1e1 / 0.3e1)
  t16 = 0.1e1 / t15
  t17 = t14 * t16
  t18 = 4 ** (0.1e1 / 0.3e1)
  t19 = t3 ** (0.1e1 / 0.3e1)
  t20 = t18 * t19
  t24 = 0.1e1 + t17 * t20 * t6 / 0.3e1
  t25 = jnp.log(t24)
  t27 = t15 ** 2
  t28 = t14 * t27
  t29 = t19 ** 2
  t31 = t18 / t29
  t32 = 0.1e1 / t7
  t36 = t13 * t15
  t37 = t18 ** 2
  t39 = t37 / t19
  t40 = 0.1e1 / t6
  t45 = t1 * (t12 * t25 - t28 * t31 * t32 / 0.4e1 + t36 * t39 * t40 / 0.8e1 - 0.1e1 / 0.3e1)
  t46 = r0 - r1
  t47 = t46 * t4
  t48 = 0.1e1 + t47
  t49 = t48 <= f.p.zeta_threshold
  t50 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t51 = t50 * f.p.zeta_threshold
  t52 = t48 ** (0.1e1 / 0.3e1)
  t54 = f.my_piecewise3(t49, t51, t52 * t48)
  t55 = 0.1e1 - t47
  t56 = t55 <= f.p.zeta_threshold
  t57 = t55 ** (0.1e1 / 0.3e1)
  t59 = f.my_piecewise3(t56, t51, t57 * t55)
  t61 = 2 ** (0.1e1 / 0.3e1)
  t64 = 0.1e1 / (0.2e1 * t61 - 0.2e1)
  t65 = (t54 + t59 - 0.2e1) * t64
  t66 = params.hl_c[1]
  t67 = params.hl_r[1]
  t68 = t67 ** 2
  t70 = 0.1e1 / t68 / t67
  t73 = 0.1e1 + 0.3e1 / 0.4e1 * t5 * t70
  t77 = 0.1e1 + t17 * t20 * t67 / 0.3e1
  t78 = jnp.log(t77)
  t80 = 0.1e1 / t68
  t84 = 0.1e1 / t67
  t90 = -t66 * (t73 * t78 - t28 * t31 * t80 / 0.4e1 + t36 * t39 * t84 / 0.8e1 - 0.1e1 / 0.3e1) + t45
  t91 = t65 * t90
  t92 = t3 ** 2
  t93 = 0.1e1 / t92
  t94 = t2 * t93
  t107 = t18 / t29 / t3
  t113 = t37 / t19 / t3
  t118 = t1 * (-0.3e1 / 0.4e1 * t94 * t9 * t25 + t12 * t14 * t16 * t31 * t6 / t24 / 0.9e1 + t28 * t107 * t32 / 0.6e1 - t36 * t113 * t40 / 0.24e2)
  t119 = t46 * t93
  t120 = t4 - t119
  t123 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t52 * t120)
  t127 = f.my_piecewise3(t56, 0, -0.4e1 / 0.3e1 * t57 * t120)
  t150 = t65 * (-t66 * (-0.3e1 / 0.4e1 * t94 * t70 * t78 + t73 * t14 * t16 * t31 * t67 / t77 / 0.9e1 + t28 * t107 * t80 / 0.6e1 - t36 * t113 * t84 / 0.24e2) + t118)
  vrho_0_ = -t45 + t91 + t3 * (-t118 + (t123 + t127) * t64 * t90 + t150)
  t153 = -t4 - t119
  t156 = f.my_piecewise3(t49, 0, 0.4e1 / 0.3e1 * t52 * t153)
  t160 = f.my_piecewise3(t56, 0, -0.4e1 / 0.3e1 * t57 * t153)
  vrho_1_ = -t45 + t91 + t3 * (-t118 + (t156 + t160) * t64 * t90 + t150)

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = params.hl_c[0]
  t2 = 0.1e1 / jnp.pi
  t4 = t2 / r0
  t5 = params.hl_r[0]
  t6 = t5 ** 2
  t8 = 0.1e1 / t6 / t5
  t11 = 0.1e1 + 0.3e1 / 0.4e1 * t4 * t8
  t12 = 3 ** (0.1e1 / 0.3e1)
  t13 = t12 ** 2
  t14 = t2 ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t14
  t16 = t13 * t15
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t23 = 0.1e1 + t16 * t19 * t5 / 0.3e1
  t24 = jnp.log(t23)
  t26 = t14 ** 2
  t27 = t13 * t26
  t28 = t18 ** 2
  t30 = t17 / t28
  t31 = 0.1e1 / t6
  t35 = t12 * t14
  t36 = t17 ** 2
  t38 = t36 / t18
  t39 = 0.1e1 / t5
  t44 = t1 * (t11 * t24 - t27 * t30 * t31 / 0.4e1 + t35 * t38 * t39 / 0.8e1 - 0.1e1 / 0.3e1)
  t46 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t48 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t46 * f.p.zeta_threshold, 1)
  t51 = 2 ** (0.1e1 / 0.3e1)
  t55 = (0.2e1 * t48 - 0.2e1) / (0.2e1 * t51 - 0.2e1)
  t56 = params.hl_c[1]
  t57 = params.hl_r[1]
  t58 = t57 ** 2
  t60 = 0.1e1 / t58 / t57
  t63 = 0.1e1 + 0.3e1 / 0.4e1 * t4 * t60
  t67 = 0.1e1 + t16 * t19 * t57 / 0.3e1
  t68 = jnp.log(t67)
  t70 = 0.1e1 / t58
  t74 = 0.1e1 / t57
  t82 = r0 ** 2
  t84 = t2 / t82
  t97 = t17 / t28 / r0
  t103 = t36 / t18 / r0
  t108 = t1 * (-0.3e1 / 0.4e1 * t84 * t8 * t24 + t11 * t13 * t15 * t30 * t5 / t23 / 0.9e1 + t27 * t97 * t31 / 0.6e1 - t35 * t103 * t39 / 0.24e2)
  vrho_0_ = -t44 + t55 * (-t56 * (t63 * t68 - t27 * t30 * t70 / 0.4e1 + t35 * t38 * t74 / 0.8e1 - 0.1e1 / 0.3e1) + t44) + r0 * (-t108 + t55 * (-t56 * (-0.3e1 / 0.4e1 * t84 * t60 * t68 + t63 * t13 * t15 * t30 * t57 / t67 / 0.9e1 + t27 * t97 * t70 / 0.6e1 - t35 * t103 * t74 / 0.24e2) + t108))

  res = {'vrho': vrho_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = params.hl_c[0]
  t2 = 0.1e1 / jnp.pi
  t3 = r0 + r1
  t4 = t3 ** 2
  t5 = 0.1e1 / t4
  t6 = t2 * t5
  t7 = params.hl_r[0]
  t8 = t7 ** 2
  t10 = 0.1e1 / t8 / t7
  t11 = 3 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t13 = t2 ** (0.1e1 / 0.3e1)
  t14 = 0.1e1 / t13
  t15 = t12 * t14
  t16 = 4 ** (0.1e1 / 0.3e1)
  t17 = t3 ** (0.1e1 / 0.3e1)
  t18 = t16 * t17
  t22 = 0.1e1 + t15 * t18 * t7 / 0.3e1
  t23 = jnp.log(t22)
  t24 = t10 * t23
  t27 = 0.1e1 / t3
  t28 = t2 * t27
  t31 = 0.1e1 + 0.3e1 / 0.4e1 * t28 * t10
  t33 = t31 * t12 * t14
  t34 = t17 ** 2
  t36 = t16 / t34
  t37 = 0.1e1 / t22
  t38 = t7 * t37
  t42 = t13 ** 2
  t43 = t12 * t42
  t46 = t16 / t34 / t3
  t47 = 0.1e1 / t8
  t51 = t11 * t13
  t52 = t16 ** 2
  t55 = t52 / t17 / t3
  t56 = 0.1e1 / t7
  t61 = t1 * (-0.3e1 / 0.4e1 * t6 * t24 + t33 * t36 * t38 / 0.9e1 + t43 * t46 * t47 / 0.6e1 - t51 * t55 * t56 / 0.24e2)
  t62 = 0.2e1 * t61
  t63 = r0 - r1
  t64 = t63 * t27
  t65 = 0.1e1 + t64
  t66 = t65 <= f.p.zeta_threshold
  t67 = t65 ** (0.1e1 / 0.3e1)
  t68 = t63 * t5
  t69 = t27 - t68
  t72 = f.my_piecewise3(t66, 0, 0.4e1 / 0.3e1 * t67 * t69)
  t73 = 0.1e1 - t64
  t74 = t73 <= f.p.zeta_threshold
  t75 = t73 ** (0.1e1 / 0.3e1)
  t76 = -t69
  t79 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t76)
  t81 = 2 ** (0.1e1 / 0.3e1)
  t84 = 0.1e1 / (0.2e1 * t81 - 0.2e1)
  t85 = (t72 + t79) * t84
  t86 = params.hl_c[1]
  t87 = params.hl_r[1]
  t88 = t87 ** 2
  t90 = 0.1e1 / t88 / t87
  t93 = 0.1e1 + 0.3e1 / 0.4e1 * t28 * t90
  t97 = 0.1e1 + t15 * t18 * t87 / 0.3e1
  t98 = jnp.log(t97)
  t100 = 0.1e1 / t88
  t105 = t52 / t17
  t106 = 0.1e1 / t87
  t121 = -t86 * (t93 * t98 - t43 * t36 * t100 / 0.4e1 + t51 * t105 * t106 / 0.8e1 - 0.1e1 / 0.3e1) + t1 * (t31 * t23 - t43 * t36 * t47 / 0.4e1 + t51 * t105 * t56 / 0.8e1 - 0.1e1 / 0.3e1)
  t122 = t85 * t121
  t124 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t125 = t124 * f.p.zeta_threshold
  t127 = f.my_piecewise3(t66, t125, t67 * t65)
  t129 = f.my_piecewise3(t74, t125, t75 * t73)
  t131 = (t127 + t129 - 0.2e1) * t84
  t132 = t90 * t98
  t136 = t93 * t12 * t14
  t137 = 0.1e1 / t97
  t138 = t87 * t137
  t150 = -t86 * (-0.3e1 / 0.4e1 * t6 * t132 + t136 * t36 * t138 / 0.9e1 + t43 * t46 * t100 / 0.6e1 - t51 * t55 * t106 / 0.24e2) + t61
  t152 = 0.2e1 * t131 * t150
  t154 = 0.1e1 / t4 / t3
  t155 = t2 * t154
  t159 = 0.1e1 / t34 / t4
  t160 = t2 * t159
  t170 = 0.1e1 / t42
  t172 = t22 ** 2
  t178 = t16 * t159
  t184 = t52 / t17 / t4
  t189 = t1 * (0.3e1 / 0.2e1 * t155 * t24 - t160 * t47 * t15 * t16 * t37 / 0.6e1 - 0.2e1 / 0.27e2 * t33 * t46 * t38 - t31 * t11 * t170 * t55 * t8 / t172 / 0.27e2 - 0.5e1 / 0.18e2 * t43 * t178 * t47 + t51 * t184 * t56 / 0.18e2)
  t190 = t67 ** 2
  t191 = 0.1e1 / t190
  t192 = t69 ** 2
  t195 = t63 * t154
  t197 = -0.2e1 * t5 + 0.2e1 * t195
  t201 = f.my_piecewise3(t66, 0, 0.4e1 / 0.9e1 * t191 * t192 + 0.4e1 / 0.3e1 * t67 * t197)
  t202 = t75 ** 2
  t203 = 0.1e1 / t202
  t204 = t76 ** 2
  t211 = f.my_piecewise3(t74, 0, 0.4e1 / 0.9e1 * t203 * t204 - 0.4e1 / 0.3e1 * t75 * t197)
  t215 = t85 * t150
  t229 = t97 ** 2
  t244 = t131 * (-t86 * (0.3e1 / 0.2e1 * t155 * t132 - t160 * t100 * t15 * t16 * t137 / 0.6e1 - 0.2e1 / 0.27e2 * t136 * t46 * t138 - t93 * t11 * t170 * t55 * t88 / t229 / 0.27e2 - 0.5e1 / 0.18e2 * t43 * t178 * t100 + t51 * t184 * t106 / 0.18e2) + t189)
  d11 = -t62 + 0.2e1 * t122 + t152 + t3 * (-t189 + (t201 + t211) * t84 * t121 + 0.2e1 * t215 + t244)
  t247 = -t27 - t68
  t250 = f.my_piecewise3(t66, 0, 0.4e1 / 0.3e1 * t67 * t247)
  t251 = -t247
  t254 = f.my_piecewise3(t74, 0, 0.4e1 / 0.3e1 * t75 * t251)
  t256 = (t250 + t254) * t84
  t257 = t256 * t121
  t265 = f.my_piecewise3(t66, 0, 0.4e1 / 0.9e1 * t191 * t247 * t69 + 0.8e1 / 0.3e1 * t67 * t63 * t154)
  t273 = f.my_piecewise3(t74, 0, 0.4e1 / 0.9e1 * t203 * t251 * t76 - 0.8e1 / 0.3e1 * t75 * t63 * t154)
  t277 = t256 * t150
  d12 = -t62 + t122 + t152 + t257 + t3 * (-t189 + (t265 + t273) * t84 * t121 + t277 + t215 + t244)
  t281 = t247 ** 2
  t285 = 0.2e1 * t5 + 0.2e1 * t195
  t289 = f.my_piecewise3(t66, 0, 0.4e1 / 0.9e1 * t191 * t281 + 0.4e1 / 0.3e1 * t67 * t285)
  t290 = t251 ** 2
  t297 = f.my_piecewise3(t74, 0, 0.4e1 / 0.9e1 * t203 * t290 - 0.4e1 / 0.3e1 * t75 * t285)
  d22 = -t62 + 0.2e1 * t257 + t152 + t3 * (-t189 + (t289 + t297) * t84 * t121 + 0.2e1 * t277 + t244)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t1 = params.hl_c[0]
  t2 = 0.1e1 / jnp.pi
  t3 = r0 ** 2
  t5 = t2 / t3
  t6 = params.hl_r[0]
  t7 = t6 ** 2
  t9 = 0.1e1 / t7 / t6
  t10 = 3 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t12 = t2 ** (0.1e1 / 0.3e1)
  t13 = 0.1e1 / t12
  t14 = t11 * t13
  t15 = 4 ** (0.1e1 / 0.3e1)
  t16 = r0 ** (0.1e1 / 0.3e1)
  t17 = t15 * t16
  t21 = 0.1e1 + t14 * t17 * t6 / 0.3e1
  t22 = jnp.log(t21)
  t23 = t9 * t22
  t27 = t2 / r0
  t30 = 0.1e1 + 0.3e1 / 0.4e1 * t27 * t9
  t32 = t30 * t11 * t13
  t33 = t16 ** 2
  t35 = t15 / t33
  t36 = 0.1e1 / t21
  t37 = t6 * t36
  t41 = t12 ** 2
  t42 = t11 * t41
  t45 = t15 / t33 / r0
  t46 = 0.1e1 / t7
  t50 = t10 * t12
  t51 = t15 ** 2
  t54 = t51 / t16 / r0
  t55 = 0.1e1 / t6
  t60 = t1 * (-0.3e1 / 0.4e1 * t5 * t23 + t32 * t35 * t37 / 0.9e1 + t42 * t45 * t46 / 0.6e1 - t50 * t54 * t55 / 0.24e2)
  t63 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t65 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t63 * f.p.zeta_threshold, 1)
  t68 = 2 ** (0.1e1 / 0.3e1)
  t72 = (0.2e1 * t65 - 0.2e1) / (0.2e1 * t68 - 0.2e1)
  t73 = params.hl_c[1]
  t74 = params.hl_r[1]
  t75 = t74 ** 2
  t77 = 0.1e1 / t75 / t74
  t81 = 0.1e1 + t14 * t17 * t74 / 0.3e1
  t82 = jnp.log(t81)
  t83 = t77 * t82
  t88 = 0.1e1 + 0.3e1 / 0.4e1 * t27 * t77
  t90 = t88 * t11 * t13
  t91 = 0.1e1 / t81
  t92 = t74 * t91
  t96 = 0.1e1 / t75
  t100 = 0.1e1 / t74
  t111 = t2 / t3 / r0
  t115 = 0.1e1 / t33 / t3
  t116 = t2 * t115
  t126 = 0.1e1 / t41
  t128 = t21 ** 2
  t134 = t15 * t115
  t140 = t51 / t16 / t3
  t145 = t1 * (0.3e1 / 0.2e1 * t111 * t23 - t116 * t46 * t14 * t15 * t36 / 0.6e1 - 0.2e1 / 0.27e2 * t32 * t45 * t37 - t30 * t10 * t126 * t54 * t7 / t128 / 0.27e2 - 0.5e1 / 0.18e2 * t42 * t134 * t46 + t50 * t140 * t55 / 0.18e2)
  t158 = t81 ** 2
  v2rho2_0_ = -0.2e1 * t60 + 0.2e1 * t72 * (-t73 * (-0.3e1 / 0.4e1 * t5 * t83 + t90 * t35 * t92 / 0.9e1 + t42 * t45 * t96 / 0.6e1 - t50 * t54 * t100 / 0.24e2) + t60) + r0 * (-t145 + t72 * (-t73 * (0.3e1 / 0.2e1 * t111 * t83 - t116 * t96 * t14 * t15 * t91 / 0.6e1 - 0.2e1 / 0.27e2 * t90 * t45 * t92 - t88 * t10 * t126 * t54 * t75 / t158 / 0.27e2 - 0.5e1 / 0.18e2 * t42 * t134 * t96 + t50 * t140 * t100 / 0.18e2) + t145))
  res = {'v2rho2': v2rho2_0_}
  return res
