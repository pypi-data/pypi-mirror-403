"""Generated from mgga_x_task.mpl."""

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
  params_task_anu_raw = params.task_anu
  if isinstance(params_task_anu_raw, (str, bytes, dict)):
    params_task_anu = params_task_anu_raw
  else:
    try:
      params_task_anu_seq = list(params_task_anu_raw)
    except TypeError:
      params_task_anu = params_task_anu_raw
    else:
      params_task_anu_seq = np.asarray(params_task_anu_seq, dtype=np.float64)
      params_task_anu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_anu_seq))
  params_task_bnu_raw = params.task_bnu
  if isinstance(params_task_bnu_raw, (str, bytes, dict)):
    params_task_bnu = params_task_bnu_raw
  else:
    try:
      params_task_bnu_seq = list(params_task_bnu_raw)
    except TypeError:
      params_task_bnu = params_task_bnu_raw
    else:
      params_task_bnu_seq = np.asarray(params_task_bnu_seq, dtype=np.float64)
      params_task_bnu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_bnu_seq))
  params_task_c_raw = params.task_c
  if isinstance(params_task_c_raw, (str, bytes, dict)):
    params_task_c = params_task_c_raw
  else:
    try:
      params_task_c_seq = list(params_task_c_raw)
    except TypeError:
      params_task_c = params_task_c_raw
    else:
      params_task_c_seq = np.asarray(params_task_c_seq, dtype=np.float64)
      params_task_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_c_seq))
  params_task_d_raw = params.task_d
  if isinstance(params_task_d_raw, (str, bytes, dict)):
    params_task_d = params_task_d_raw
  else:
    try:
      params_task_d_seq = list(params_task_d_raw)
    except TypeError:
      params_task_d = params_task_d_raw
    else:
      params_task_d_seq = np.asarray(params_task_d_seq, dtype=np.float64)
      params_task_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_d_seq))
  params_task_h0x_raw = params.task_h0x
  if isinstance(params_task_h0x_raw, (str, bytes, dict)):
    params_task_h0x = params_task_h0x_raw
  else:
    try:
      params_task_h0x_seq = list(params_task_h0x_raw)
    except TypeError:
      params_task_h0x = params_task_h0x_raw
    else:
      params_task_h0x_seq = np.asarray(params_task_h0x_seq, dtype=np.float64)
      params_task_h0x = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_h0x_seq))

  task_alpha = lambda x, t: t / K_FACTOR_C * jnp.maximum(1 - x ** 2 / (8 * t), 1e-10)

  task_gx = lambda x: 1 - f.m_recexp(x ** (1 / 4) / params_task_c)

  task_hx1 = lambda r: simplify(jnp.sum(jnp.array([params_task_anu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 2 + 1)]), axis=0))

  task_fx = lambda r: simplify(jnp.sum(jnp.array([params_task_bnu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 4 + 1)]), axis=0))

  task_f0 = lambda s, a: params_task_h0x * task_gx(s ** 2) + (1.0 - task_fx(a)) * (task_hx1(s ** 2) - params_task_h0x) * task_gx(s ** 2) ** params_task_d

  task_f = lambda x, u, t: task_f0(X2S * x, task_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, task_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_task_anu_raw = params.task_anu
  if isinstance(params_task_anu_raw, (str, bytes, dict)):
    params_task_anu = params_task_anu_raw
  else:
    try:
      params_task_anu_seq = list(params_task_anu_raw)
    except TypeError:
      params_task_anu = params_task_anu_raw
    else:
      params_task_anu_seq = np.asarray(params_task_anu_seq, dtype=np.float64)
      params_task_anu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_anu_seq))
  params_task_bnu_raw = params.task_bnu
  if isinstance(params_task_bnu_raw, (str, bytes, dict)):
    params_task_bnu = params_task_bnu_raw
  else:
    try:
      params_task_bnu_seq = list(params_task_bnu_raw)
    except TypeError:
      params_task_bnu = params_task_bnu_raw
    else:
      params_task_bnu_seq = np.asarray(params_task_bnu_seq, dtype=np.float64)
      params_task_bnu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_bnu_seq))
  params_task_c_raw = params.task_c
  if isinstance(params_task_c_raw, (str, bytes, dict)):
    params_task_c = params_task_c_raw
  else:
    try:
      params_task_c_seq = list(params_task_c_raw)
    except TypeError:
      params_task_c = params_task_c_raw
    else:
      params_task_c_seq = np.asarray(params_task_c_seq, dtype=np.float64)
      params_task_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_c_seq))
  params_task_d_raw = params.task_d
  if isinstance(params_task_d_raw, (str, bytes, dict)):
    params_task_d = params_task_d_raw
  else:
    try:
      params_task_d_seq = list(params_task_d_raw)
    except TypeError:
      params_task_d = params_task_d_raw
    else:
      params_task_d_seq = np.asarray(params_task_d_seq, dtype=np.float64)
      params_task_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_d_seq))
  params_task_h0x_raw = params.task_h0x
  if isinstance(params_task_h0x_raw, (str, bytes, dict)):
    params_task_h0x = params_task_h0x_raw
  else:
    try:
      params_task_h0x_seq = list(params_task_h0x_raw)
    except TypeError:
      params_task_h0x = params_task_h0x_raw
    else:
      params_task_h0x_seq = np.asarray(params_task_h0x_seq, dtype=np.float64)
      params_task_h0x = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_h0x_seq))

  task_alpha = lambda x, t: t / K_FACTOR_C * jnp.maximum(1 - x ** 2 / (8 * t), 1e-10)

  task_gx = lambda x: 1 - f.m_recexp(x ** (1 / 4) / params_task_c)

  task_hx1 = lambda r: simplify(jnp.sum(jnp.array([params_task_anu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 2 + 1)]), axis=0))

  task_fx = lambda r: simplify(jnp.sum(jnp.array([params_task_bnu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 4 + 1)]), axis=0))

  task_f0 = lambda s, a: params_task_h0x * task_gx(s ** 2) + (1.0 - task_fx(a)) * (task_hx1(s ** 2) - params_task_h0x) * task_gx(s ** 2) ** params_task_d

  task_f = lambda x, u, t: task_f0(X2S * x, task_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, task_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_task_anu_raw = params.task_anu
  if isinstance(params_task_anu_raw, (str, bytes, dict)):
    params_task_anu = params_task_anu_raw
  else:
    try:
      params_task_anu_seq = list(params_task_anu_raw)
    except TypeError:
      params_task_anu = params_task_anu_raw
    else:
      params_task_anu_seq = np.asarray(params_task_anu_seq, dtype=np.float64)
      params_task_anu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_anu_seq))
  params_task_bnu_raw = params.task_bnu
  if isinstance(params_task_bnu_raw, (str, bytes, dict)):
    params_task_bnu = params_task_bnu_raw
  else:
    try:
      params_task_bnu_seq = list(params_task_bnu_raw)
    except TypeError:
      params_task_bnu = params_task_bnu_raw
    else:
      params_task_bnu_seq = np.asarray(params_task_bnu_seq, dtype=np.float64)
      params_task_bnu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_bnu_seq))
  params_task_c_raw = params.task_c
  if isinstance(params_task_c_raw, (str, bytes, dict)):
    params_task_c = params_task_c_raw
  else:
    try:
      params_task_c_seq = list(params_task_c_raw)
    except TypeError:
      params_task_c = params_task_c_raw
    else:
      params_task_c_seq = np.asarray(params_task_c_seq, dtype=np.float64)
      params_task_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_c_seq))
  params_task_d_raw = params.task_d
  if isinstance(params_task_d_raw, (str, bytes, dict)):
    params_task_d = params_task_d_raw
  else:
    try:
      params_task_d_seq = list(params_task_d_raw)
    except TypeError:
      params_task_d = params_task_d_raw
    else:
      params_task_d_seq = np.asarray(params_task_d_seq, dtype=np.float64)
      params_task_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_d_seq))
  params_task_h0x_raw = params.task_h0x
  if isinstance(params_task_h0x_raw, (str, bytes, dict)):
    params_task_h0x = params_task_h0x_raw
  else:
    try:
      params_task_h0x_seq = list(params_task_h0x_raw)
    except TypeError:
      params_task_h0x = params_task_h0x_raw
    else:
      params_task_h0x_seq = np.asarray(params_task_h0x_seq, dtype=np.float64)
      params_task_h0x = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_h0x_seq))

  task_alpha = lambda x, t: t / K_FACTOR_C * jnp.maximum(1 - x ** 2 / (8 * t), 1e-10)

  task_gx = lambda x: 1 - f.m_recexp(x ** (1 / 4) / params_task_c)

  task_hx1 = lambda r: jnp.sum(jnp.array([params_task_anu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 2 + 1)]), axis=0)

  task_fx = lambda r: jnp.sum(jnp.array([params_task_bnu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 4 + 1)]), axis=0)

  task_f0 = lambda s, a: params_task_h0x * task_gx(s ** 2) + (1.0 - task_fx(a)) * (task_hx1(s ** 2) - params_task_h0x) * task_gx(s ** 2) ** params_task_d

  task_f = lambda x, u, t: task_f0(X2S * x, task_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, task_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = 24 ** (0.1e1 / 0.4e1)
  t29 = t28 ** 2
  t30 = t29 * t28
  t31 = 6 ** (0.1e1 / 0.3e1)
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = 0.1e1 / t34
  t36 = t31 * t35
  t37 = r0 ** 2
  t38 = r0 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t41 = 0.1e1 / t39 / t37
  t43 = t36 * s0 * t41
  t44 = t43 ** (0.1e1 / 0.4e1)
  t46 = 0.1e1 / params.task_c
  t48 = t30 * t44 * t46 / 0.24e2
  t49 = jnp.log(DBL_EPSILON)
  t50 = 0.1e1 / t49
  t51 = t48 <= -t50
  t52 = t48 < -t50
  t53 = f.my_piecewise3(t52, -t50, t48)
  t55 = jnp.exp(-0.1e1 / t53)
  t56 = f.my_piecewise3(t51, 0, t55)
  t57 = 0.1e1 - t56
  t59 = params.task_bnu[0]
  t61 = 0.1e1 / t39 / r0
  t62 = tau0 * t61
  t63 = 0.1e1 / r0
  t64 = s0 * t63
  t65 = 0.1e1 / tau0
  t67 = t64 * t65 / 0.8e1
  t69 = 0.0e0 < 0.9999999999e0 - t67
  t71 = f.my_piecewise3(t69, 0.1e1 - t67, 0.1e-9)
  t72 = t36 * t71
  t74 = 0.5e1 / 0.9e1 * t62 * t72
  t75 = t74 - 0.1e1
  t76 = t74 + 0.1e1
  t77 = 0.1e1 / t76
  t78 = t75 * t77
  t79 = ChebyshevT(0, t78)
  t81 = params.task_bnu[1]
  t82 = ChebyshevT(1, t78)
  t84 = params.task_bnu[2]
  t85 = ChebyshevT(2, t78)
  t87 = params.task_bnu[3]
  t88 = ChebyshevT(3, t78)
  t90 = params.task_bnu[4]
  t91 = ChebyshevT(4, t78)
  t93 = 0.10e1 - t59 * t79 - t81 * t82 - t84 * t85 - t87 * t88 - t90 * t91
  t94 = params.task_anu[0]
  t95 = t43 / 0.24e2
  t96 = t95 - 0.1e1
  t97 = t95 + 0.1e1
  t98 = 0.1e1 / t97
  t99 = t96 * t98
  t100 = ChebyshevT(0, t99)
  t102 = params.task_anu[1]
  t103 = ChebyshevT(1, t99)
  t105 = params.task_anu[2]
  t106 = ChebyshevT(2, t99)
  t108 = t94 * t100 + t102 * t103 + t105 * t106 - params.task_h0x
  t110 = t57 ** params.task_d
  t111 = t93 * t108 * t110
  t112 = params.task_h0x * t57 + t111
  t116 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t112)
  t117 = r1 <= f.p.dens_threshold
  t118 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t119 = 0.1e1 + t118
  t120 = t119 <= f.p.zeta_threshold
  t121 = t119 ** (0.1e1 / 0.3e1)
  t123 = f.my_piecewise3(t120, t22, t121 * t119)
  t124 = t123 * t26
  t125 = r1 ** 2
  t126 = r1 ** (0.1e1 / 0.3e1)
  t127 = t126 ** 2
  t129 = 0.1e1 / t127 / t125
  t131 = t36 * s2 * t129
  t132 = t131 ** (0.1e1 / 0.4e1)
  t135 = t30 * t132 * t46 / 0.24e2
  t136 = t135 <= -t50
  t137 = t135 < -t50
  t138 = f.my_piecewise3(t137, -t50, t135)
  t140 = jnp.exp(-0.1e1 / t138)
  t141 = f.my_piecewise3(t136, 0, t140)
  t142 = 0.1e1 - t141
  t145 = 0.1e1 / t127 / r1
  t146 = tau1 * t145
  t147 = 0.1e1 / r1
  t148 = s2 * t147
  t149 = 0.1e1 / tau1
  t151 = t148 * t149 / 0.8e1
  t153 = 0.0e0 < 0.9999999999e0 - t151
  t155 = f.my_piecewise3(t153, 0.1e1 - t151, 0.1e-9)
  t156 = t36 * t155
  t158 = 0.5e1 / 0.9e1 * t146 * t156
  t159 = t158 - 0.1e1
  t160 = t158 + 0.1e1
  t161 = 0.1e1 / t160
  t162 = t159 * t161
  t163 = ChebyshevT(0, t162)
  t165 = ChebyshevT(1, t162)
  t167 = ChebyshevT(2, t162)
  t169 = ChebyshevT(3, t162)
  t171 = ChebyshevT(4, t162)
  t173 = 0.10e1 - t59 * t163 - t81 * t165 - t84 * t167 - t87 * t169 - t90 * t171
  t174 = t131 / 0.24e2
  t175 = t174 - 0.1e1
  t176 = t174 + 0.1e1
  t177 = 0.1e1 / t176
  t178 = t175 * t177
  t179 = ChebyshevT(0, t178)
  t181 = ChebyshevT(1, t178)
  t183 = ChebyshevT(2, t178)
  t185 = t102 * t181 + t105 * t183 + t94 * t179 - params.task_h0x
  t187 = t142 ** params.task_d
  t188 = t173 * t185 * t187
  t189 = params.task_h0x * t142 + t188
  t193 = f.my_piecewise3(t117, 0, -0.3e1 / 0.8e1 * t5 * t124 * t189)
  t194 = t6 ** 2
  t196 = t16 / t194
  t197 = t7 - t196
  t198 = f.my_piecewise5(t10, 0, t14, 0, t197)
  t201 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t198)
  t206 = t26 ** 2
  t207 = 0.1e1 / t206
  t211 = t5 * t25 * t207 * t112 / 0.8e1
  t212 = t53 ** 2
  t213 = 0.1e1 / t212
  t214 = t44 ** 2
  t218 = t30 / t214 / t44 * t46
  t221 = 0.1e1 / t39 / t37 / r0
  t222 = s0 * t221
  t226 = f.my_piecewise3(t52, 0, -t218 * t36 * t222 / 0.36e2)
  t229 = f.my_piecewise3(t51, 0, t213 * t226 * t55)
  t238 = f.my_piecewise3(t69, s0 / t37 * t65 / 0.8e1, 0)
  t242 = -0.25e2 / 0.27e2 * tau0 * t41 * t72 + 0.5e1 / 0.9e1 * t62 * t36 * t238
  t244 = t76 ** 2
  t245 = 0.1e1 / t244
  t246 = t75 * t245
  t248 = -t246 * t242 + t242 * t77
  t250 = t75 ** 2
  t253 = 0.1e1 / (-t250 * t245 + 0.1e1)
  t254 = t253 * t82
  t257 = t253 * t79 - t78 * t254
  t260 = t253 * t85
  t263 = -0.2e1 * t78 * t260 + 0.2e1 * t254
  t266 = t253 * t88
  t269 = -0.3e1 * t78 * t266 + 0.3e1 * t260
  t275 = -0.4e1 * t78 * t253 * t91 + 0.4e1 * t266
  t282 = t97 ** 2
  t283 = 0.1e1 / t282
  t284 = t96 * t283
  t290 = t284 * t31 * t35 * s0 * t221 / 0.9e1 - t36 * t222 * t98 / 0.9e1
  t292 = t96 ** 2
  t295 = 0.1e1 / (-t292 * t283 + 0.1e1)
  t296 = t295 * t103
  t299 = t295 * t100 - t99 * t296
  t305 = -0.2e1 * t99 * t295 * t106 + 0.2e1 * t296
  t311 = 0.1e1 / t57
  t319 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t201 * t26 * t112 - t211 - 0.3e1 / 0.8e1 * t5 * t27 * (-params.task_h0x * t229 + (-t81 * t248 * t257 - t84 * t248 * t263 - t87 * t248 * t269 - t90 * t248 * t275) * t108 * t110 + t93 * (t102 * t290 * t299 + t105 * t290 * t305) * t110 - t111 * params.task_d * t229 * t311))
  t321 = f.my_piecewise5(t14, 0, t10, 0, -t197)
  t324 = f.my_piecewise3(t120, 0, 0.4e1 / 0.3e1 * t121 * t321)
  t332 = t5 * t123 * t207 * t189 / 0.8e1
  t334 = f.my_piecewise3(t117, 0, -0.3e1 / 0.8e1 * t5 * t324 * t26 * t189 - t332)
  vrho_0_ = t116 + t193 + t6 * (t319 + t334)
  t337 = -t7 - t196
  t338 = f.my_piecewise5(t10, 0, t14, 0, t337)
  t341 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t338)
  t347 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t341 * t26 * t112 - t211)
  t349 = f.my_piecewise5(t14, 0, t10, 0, -t337)
  t352 = f.my_piecewise3(t120, 0, 0.4e1 / 0.3e1 * t121 * t349)
  t357 = t138 ** 2
  t358 = 0.1e1 / t357
  t359 = t132 ** 2
  t363 = t30 / t359 / t132 * t46
  t366 = 0.1e1 / t127 / t125 / r1
  t367 = s2 * t366
  t371 = f.my_piecewise3(t137, 0, -t363 * t36 * t367 / 0.36e2)
  t374 = f.my_piecewise3(t136, 0, t358 * t371 * t140)
  t383 = f.my_piecewise3(t153, s2 / t125 * t149 / 0.8e1, 0)
  t387 = -0.25e2 / 0.27e2 * tau1 * t129 * t156 + 0.5e1 / 0.9e1 * t146 * t36 * t383
  t389 = t160 ** 2
  t390 = 0.1e1 / t389
  t391 = t159 * t390
  t393 = t387 * t161 - t391 * t387
  t395 = t159 ** 2
  t398 = 0.1e1 / (-t395 * t390 + 0.1e1)
  t399 = t398 * t165
  t402 = -t162 * t399 + t398 * t163
  t405 = t398 * t167
  t408 = -0.2e1 * t162 * t405 + 0.2e1 * t399
  t411 = t398 * t169
  t414 = -0.3e1 * t162 * t411 + 0.3e1 * t405
  t420 = -0.4e1 * t162 * t398 * t171 + 0.4e1 * t411
  t427 = t176 ** 2
  t428 = 0.1e1 / t427
  t429 = t175 * t428
  t435 = t429 * t31 * t35 * s2 * t366 / 0.9e1 - t36 * t367 * t177 / 0.9e1
  t437 = t175 ** 2
  t440 = 0.1e1 / (-t437 * t428 + 0.1e1)
  t441 = t440 * t181
  t444 = -t178 * t441 + t440 * t179
  t450 = -0.2e1 * t178 * t440 * t183 + 0.2e1 * t441
  t456 = 0.1e1 / t142
  t464 = f.my_piecewise3(t117, 0, -0.3e1 / 0.8e1 * t5 * t352 * t26 * t189 - t332 - 0.3e1 / 0.8e1 * t5 * t124 * (-params.task_h0x * t374 + (-t81 * t393 * t402 - t84 * t393 * t408 - t87 * t393 * t414 - t90 * t393 * t420) * t185 * t187 + t173 * (t102 * t435 * t444 + t105 * t435 * t450) * t187 - t188 * params.task_d * t374 * t456))
  vrho_1_ = t116 + t193 + t6 * (t347 + t464)
  t467 = t36 * t41
  t470 = f.my_piecewise3(t52, 0, t218 * t467 / 0.96e2)
  t473 = f.my_piecewise3(t51, 0, t213 * t470 * t55)
  t478 = f.my_piecewise3(t69, -t63 * t65 / 0.8e1, 0)
  t479 = t35 * t478
  t483 = t61 * t31
  t487 = -0.5e1 / 0.9e1 * t246 * tau0 * t483 * t479 + 0.5e1 / 0.9e1 * t62 * t31 * t479 * t77
  t503 = t36 * t41 * t98 / 0.24e2 - t284 * t467 / 0.24e2
  t518 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-params.task_h0x * t473 + (-t81 * t487 * t257 - t84 * t487 * t263 - t87 * t487 * t269 - t90 * t487 * t275) * t108 * t110 + t93 * (t102 * t503 * t299 + t105 * t503 * t305) * t110 - t111 * params.task_d * t473 * t311))
  vsigma_0_ = t6 * t518
  vsigma_1_ = 0.0e0
  t519 = t36 * t129
  t522 = f.my_piecewise3(t137, 0, t363 * t519 / 0.96e2)
  t525 = f.my_piecewise3(t136, 0, t358 * t522 * t140)
  t530 = f.my_piecewise3(t153, -t147 * t149 / 0.8e1, 0)
  t531 = t35 * t530
  t535 = t145 * t31
  t539 = 0.5e1 / 0.9e1 * t146 * t31 * t531 * t161 - 0.5e1 / 0.9e1 * t391 * tau1 * t535 * t531
  t555 = t36 * t129 * t177 / 0.24e2 - t429 * t519 / 0.24e2
  t570 = f.my_piecewise3(t117, 0, -0.3e1 / 0.8e1 * t5 * t124 * (-params.task_h0x * t525 + (-t81 * t539 * t402 - t84 * t539 * t408 - t87 * t539 * t414 - t90 * t539 * t420) * t185 * t187 + t173 * (t102 * t555 * t444 + t105 * t555 * t450) * t187 - t188 * params.task_d * t525 * t456))
  vsigma_2_ = t6 * t570
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t574 = tau0 ** 2
  t578 = f.my_piecewise3(t69, t64 / t574 / 0.8e1, 0)
  t582 = 0.5e1 / 0.9e1 * t483 * t35 * t71 + 0.5e1 / 0.9e1 * t62 * t36 * t578
  t585 = -t246 * t582 + t582 * t77
  t600 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * (-t81 * t585 * t257 - t84 * t585 * t263 - t87 * t585 * t269 - t90 * t585 * t275) * t108 * t110)
  vtau_0_ = t6 * t600
  t604 = tau1 ** 2
  t608 = f.my_piecewise3(t153, t148 / t604 / 0.8e1, 0)
  t612 = 0.5e1 / 0.9e1 * t146 * t36 * t608 + 0.5e1 / 0.9e1 * t535 * t35 * t155
  t615 = t612 * t161 - t391 * t612
  t630 = f.my_piecewise3(t117, 0, -0.3e1 / 0.8e1 * t5 * t123 * t26 * (-t81 * t615 * t402 - t84 * t615 * t408 - t87 * t615 * t414 - t90 * t615 * t420) * t185 * t187)
  vtau_1_ = t6 * t630
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
  params_task_anu_raw = params.task_anu
  if isinstance(params_task_anu_raw, (str, bytes, dict)):
    params_task_anu = params_task_anu_raw
  else:
    try:
      params_task_anu_seq = list(params_task_anu_raw)
    except TypeError:
      params_task_anu = params_task_anu_raw
    else:
      params_task_anu_seq = np.asarray(params_task_anu_seq, dtype=np.float64)
      params_task_anu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_anu_seq))
  params_task_bnu_raw = params.task_bnu
  if isinstance(params_task_bnu_raw, (str, bytes, dict)):
    params_task_bnu = params_task_bnu_raw
  else:
    try:
      params_task_bnu_seq = list(params_task_bnu_raw)
    except TypeError:
      params_task_bnu = params_task_bnu_raw
    else:
      params_task_bnu_seq = np.asarray(params_task_bnu_seq, dtype=np.float64)
      params_task_bnu = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_bnu_seq))
  params_task_c_raw = params.task_c
  if isinstance(params_task_c_raw, (str, bytes, dict)):
    params_task_c = params_task_c_raw
  else:
    try:
      params_task_c_seq = list(params_task_c_raw)
    except TypeError:
      params_task_c = params_task_c_raw
    else:
      params_task_c_seq = np.asarray(params_task_c_seq, dtype=np.float64)
      params_task_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_c_seq))
  params_task_d_raw = params.task_d
  if isinstance(params_task_d_raw, (str, bytes, dict)):
    params_task_d = params_task_d_raw
  else:
    try:
      params_task_d_seq = list(params_task_d_raw)
    except TypeError:
      params_task_d = params_task_d_raw
    else:
      params_task_d_seq = np.asarray(params_task_d_seq, dtype=np.float64)
      params_task_d = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_d_seq))
  params_task_h0x_raw = params.task_h0x
  if isinstance(params_task_h0x_raw, (str, bytes, dict)):
    params_task_h0x = params_task_h0x_raw
  else:
    try:
      params_task_h0x_seq = list(params_task_h0x_raw)
    except TypeError:
      params_task_h0x = params_task_h0x_raw
    else:
      params_task_h0x_seq = np.asarray(params_task_h0x_seq, dtype=np.float64)
      params_task_h0x = np.concatenate((np.array([np.nan], dtype=np.float64), params_task_h0x_seq))

  task_alpha = lambda x, t: t / K_FACTOR_C * jnp.maximum(1 - x ** 2 / (8 * t), 1e-10)

  task_gx = lambda x: 1 - f.m_recexp(x ** (1 / 4) / params_task_c)

  task_hx1 = lambda r: jnp.sum(jnp.array([params_task_anu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 2 + 1)]), axis=0)

  task_fx = lambda r: jnp.sum(jnp.array([params_task_bnu[i + 1] * ChebyshevT(i, (r - 1) / (r + 1)) for i in range(0, 4 + 1)]), axis=0)

  task_f0 = lambda s, a: params_task_h0x * task_gx(s ** 2) + (1.0 - task_fx(a)) * (task_hx1(s ** 2) - params_task_h0x) * task_gx(s ** 2) ** params_task_d

  task_f = lambda x, u, t: task_f0(X2S * x, task_alpha(x, t))

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, task_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t19 = t17 * t18
  t20 = 24 ** (0.1e1 / 0.4e1)
  t21 = t20 ** 2
  t22 = t21 * t20
  t23 = 6 ** (0.1e1 / 0.3e1)
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = t23 * t27
  t29 = 2 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t32 = r0 ** 2
  t33 = t18 ** 2
  t35 = 0.1e1 / t33 / t32
  t37 = t28 * s0 * t30 * t35
  t38 = t37 ** (0.1e1 / 0.4e1)
  t40 = 0.1e1 / params.task_c
  t42 = t22 * t38 * t40 / 0.24e2
  t43 = jnp.log(DBL_EPSILON)
  t44 = 0.1e1 / t43
  t45 = t42 <= -t44
  t46 = t42 < -t44
  t47 = f.my_piecewise3(t46, -t44, t42)
  t49 = jnp.exp(-0.1e1 / t47)
  t50 = f.my_piecewise3(t45, 0, t49)
  t51 = 0.1e1 - t50
  t54 = tau0 * t30
  t56 = 0.1e1 / t33 / r0
  t57 = t54 * t56
  t58 = 0.1e1 / r0
  t59 = s0 * t58
  t60 = 0.1e1 / tau0
  t62 = t59 * t60 / 0.8e1
  t64 = 0.0e0 < 0.9999999999e0 - t62
  t66 = f.my_piecewise3(t64, 0.1e1 - t62, 0.1e-9)
  t67 = t28 * t66
  t69 = 0.5e1 / 0.9e1 * t57 * t67
  t70 = t69 - 0.1e1
  t71 = t69 + 0.1e1
  t72 = 0.1e1 / t71
  t73 = t70 * t72
  t74 = ChebyshevT(0, t73)
  t76 = params.task_bnu[1]
  t77 = ChebyshevT(1, t73)
  t79 = params.task_bnu[2]
  t80 = ChebyshevT(2, t73)
  t82 = params.task_bnu[3]
  t83 = ChebyshevT(3, t73)
  t85 = params.task_bnu[4]
  t86 = ChebyshevT(4, t73)
  t88 = 0.10e1 - params.task_bnu[0] * t74 - t76 * t77 - t79 * t80 - t82 * t83 - t85 * t86
  t90 = t37 / 0.24e2
  t91 = t90 - 0.1e1
  t92 = t90 + 0.1e1
  t93 = 0.1e1 / t92
  t94 = t91 * t93
  t95 = ChebyshevT(0, t94)
  t97 = params.task_anu[1]
  t98 = ChebyshevT(1, t94)
  t100 = params.task_anu[2]
  t101 = ChebyshevT(2, t94)
  t103 = t100 * t101 + params.task_anu[0] * t95 + t97 * t98 - params.task_h0x
  t105 = t51 ** params.task_d
  t106 = t88 * t103 * t105
  t107 = params.task_h0x * t51 + t106
  t111 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t107)
  t117 = t47 ** 2
  t118 = 0.1e1 / t117
  t119 = t38 ** 2
  t122 = t22 / t119 / t38
  t129 = t30 / t33 / t32 / r0
  t130 = t27 * s0 * t129
  t133 = f.my_piecewise3(t46, 0, -t122 * t40 * t23 * t130 / 0.36e2)
  t136 = f.my_piecewise3(t45, 0, t118 * t133 * t49)
  t145 = f.my_piecewise3(t64, s0 / t32 * t60 / 0.8e1, 0)
  t149 = -0.25e2 / 0.27e2 * t54 * t35 * t67 + 0.5e1 / 0.9e1 * t57 * t28 * t145
  t151 = t71 ** 2
  t152 = 0.1e1 / t151
  t153 = t70 * t152
  t155 = -t153 * t149 + t149 * t72
  t157 = t70 ** 2
  t160 = 0.1e1 / (-t157 * t152 + 0.1e1)
  t161 = t160 * t77
  t164 = t160 * t74 - t73 * t161
  t167 = t160 * t80
  t170 = -0.2e1 * t73 * t167 + 0.2e1 * t161
  t173 = t160 * t83
  t176 = -0.3e1 * t73 * t173 + 0.3e1 * t167
  t182 = -0.4e1 * t73 * t160 * t86 + 0.4e1 * t173
  t190 = t92 ** 2
  t191 = 0.1e1 / t190
  t193 = t91 * t191 * t23
  t196 = -t28 * s0 * t129 * t93 / 0.9e1 + t193 * t130 / 0.9e1
  t198 = t91 ** 2
  t201 = 0.1e1 / (-t198 * t191 + 0.1e1)
  t202 = t201 * t98
  t205 = t201 * t95 - t94 * t202
  t211 = -0.2e1 * t94 * t201 * t101 + 0.2e1 * t202
  t217 = 0.1e1 / t51
  t225 = f.my_piecewise3(t2, 0, -t6 * t17 / t33 * t107 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-params.task_h0x * t136 + (-t76 * t155 * t164 - t79 * t155 * t170 - t82 * t155 * t176 - t85 * t155 * t182) * t103 * t105 + t88 * (t100 * t196 * t211 + t97 * t196 * t205) * t105 - t106 * params.task_d * t136 * t217))
  vrho_0_ = 0.2e1 * r0 * t225 + 0.2e1 * t111
  t229 = t30 * t35
  t233 = f.my_piecewise3(t46, 0, t122 * t40 * t28 * t229 / 0.96e2)
  t236 = f.my_piecewise3(t45, 0, t118 * t233 * t49)
  t240 = f.my_piecewise3(t64, -t58 * t60 / 0.8e1, 0)
  t250 = -0.5e1 / 0.9e1 * t153 * t54 * t56 * t23 * t27 * t240 + 0.5e1 / 0.9e1 * t57 * t28 * t240 * t72
  t268 = -t193 * t27 * t30 * t35 / 0.24e2 + t28 * t229 * t93 / 0.24e2
  t283 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-params.task_h0x * t236 + (-t76 * t250 * t164 - t79 * t250 * t170 - t82 * t250 * t176 - t85 * t250 * t182) * t103 * t105 + t88 * (t100 * t268 * t211 + t97 * t268 * t205) * t105 - t106 * params.task_d * t236 * t217))
  vsigma_0_ = 0.2e1 * r0 * t283
  vlapl_0_ = 0.0e0
  t288 = tau0 ** 2
  t292 = f.my_piecewise3(t64, t59 / t288 / 0.8e1, 0)
  t296 = 0.5e1 / 0.9e1 * t57 * t28 * t292 + 0.5e1 / 0.9e1 * t30 * t56 * t67
  t299 = -t153 * t296 + t296 * t72
  t314 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * (-t76 * t299 * t164 - t79 * t299 * t170 - t82 * t299 * t176 - t85 * t299 * t182) * t103 * t105)
  vtau_0_ = 0.2e1 * r0 * t314
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_, 'v2rholapl': v2rholapl_0_, 'v2sigmalapl': v2sigmalapl_0_, 'v2lapl2': v2lapl2_0_, 'v2rhotau': v2rhotau_0_, 'v2sigmatau': v2sigmatau_0_, 'v2lapltau': v2lapltau_0_, 'v2tau2': v2tau2_0_}
  return res

