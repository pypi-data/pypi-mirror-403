"""Generated from lda_x.mpl."""

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

  f_lda_x = lambda rs, z: +params_alpha * f.my_piecewise3(f.screen_dens(rs, z), 0, f.lda_x_spin(rs, z)) + params_alpha * f.my_piecewise3(f.screen_dens(rs, -z), 0, f.lda_x_spin(rs, -z))

  functional_body = lambda rs, z: f_lda_x(rs, z)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
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

  f_lda_x = lambda rs, z: +params_alpha * f.my_piecewise3(f.screen_dens(rs, z), 0, f.lda_x_spin(rs, z)) + params_alpha * f.my_piecewise3(f.screen_dens(rs, -z), 0, f.lda_x_spin(rs, -z))

  functional_body = lambda rs, z: f_lda_x(rs, z)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t8 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t10 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t8 * f.p.zeta_threshold, 1)
  t11 = r0 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t17 = f.my_piecewise3(t2, 0, -t6 * t10 / t12 / 0.8e1)
  t26 = f.my_piecewise3(t2, 0, t6 * t10 / t12 / r0 / 0.12e2)
  v2rho2_0_ = 0.2e1 * r0 * params.alpha * t26 + 0.4e1 * params.alpha * t17
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t8 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t10 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t8 * f.p.zeta_threshold, 1)
  t11 = r0 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t18 = f.my_piecewise3(t2, 0, t6 * t10 / t12 / r0 / 0.12e2)
  t22 = r0 ** 2
  t28 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t10 / t12 / t22)
  v3rho3_0_ = 0.2e1 * r0 * params.alpha * t28 + 0.6e1 * params.alpha * t18

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
  t8 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t10 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t8 * f.p.zeta_threshold, 1)
  t11 = r0 ** 2
  t12 = r0 ** (0.1e1 / 0.3e1)
  t13 = t12 ** 2
  t19 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t10 / t13 / t11)
  t29 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t10 / t13 / t11 / r0)
  v4rho4_0_ = 0.2e1 * r0 * params.alpha * t29 + 0.8e1 * params.alpha * t19

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
  t8 = r0 * t7
  t10 = 0.2e1 * t8 <= f.p.zeta_threshold
  t11 = 2 ** (0.1e1 / 0.3e1)
  t12 = t11 * t7
  t13 = t8 ** (0.1e1 / 0.3e1)
  t16 = t11 * r0
  t17 = t6 ** 2
  t18 = 0.1e1 / t17
  t21 = 0.2e1 * t16 * t18 * t13
  t22 = t13 ** 2
  t23 = 0.1e1 / t22
  t24 = t7 * t23
  t26 = -r0 * t18 + t7
  t31 = f.my_piecewise3(t10, 0, 0.2e1 * t12 * t13 - t21 + 0.2e1 / 0.3e1 * t16 * t24 * t26)
  t32 = t6 ** (0.1e1 / 0.3e1)
  t36 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t37 = t36 * f.p.zeta_threshold
  t41 = f.my_piecewise3(t10, t37, 0.2e1 * t16 * t7 * t13)
  t42 = t32 ** 2
  t43 = 0.1e1 / t42
  t46 = t5 * t41 * t43 / 0.8e1
  t48 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t32 - t46)
  t49 = params.alpha * t48
  t51 = r1 <= f.p.dens_threshold
  t52 = r1 * t7
  t54 = 0.2e1 * t52 <= f.p.zeta_threshold
  t55 = t11 * r1
  t56 = t52 ** (0.1e1 / 0.3e1)
  t59 = 0.2e1 * t55 * t18 * t56
  t60 = r1 ** 2
  t61 = t11 * t60
  t63 = 0.1e1 / t17 / t6
  t64 = t56 ** 2
  t65 = 0.1e1 / t64
  t70 = f.my_piecewise3(t54, 0, -t59 - 0.2e1 / 0.3e1 * t61 * t63 * t65)
  t77 = f.my_piecewise3(t54, t37, 0.2e1 * t55 * t7 * t56)
  t80 = t5 * t77 * t43 / 0.8e1
  t82 = f.my_piecewise3(t51, 0, -0.3e1 / 0.8e1 * t5 * t70 * t32 - t80)
  t83 = params.alpha * t82
  t85 = t11 * t18
  t86 = t85 * t13
  t93 = 0.4e1 * t16 * t63 * t13
  t96 = t16 * t18 * t23 * t26
  t99 = 0.1e1 / t22 / t8
  t101 = t26 ** 2
  t112 = f.my_piecewise3(t10, 0, -0.4e1 * t86 + 0.4e1 / 0.3e1 * t12 * t23 * t26 + t93 - 0.4e1 / 0.3e1 * t96 - 0.4e1 / 0.9e1 * t16 * t7 * t99 * t101 + 0.2e1 / 0.3e1 * t16 * t24 * (0.2e1 * r0 * t63 - 0.2e1 * t18))
  t117 = t5 * t31 * t43
  t120 = 0.1e1 / t42 / t6
  t123 = t5 * t41 * t120 / 0.12e2
  t125 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t112 * t32 - t117 / 0.4e1 + t123)
  t129 = 0.4e1 * t55 * t63 * t56
  t130 = t17 ** 2
  t131 = 0.1e1 / t130
  t133 = t61 * t131 * t65
  t138 = 0.1e1 / t130 / t6
  t140 = 0.1e1 / t64 / t52
  t145 = f.my_piecewise3(t54, 0, t129 + 0.8e1 / 0.3e1 * t133 - 0.4e1 / 0.9e1 * t11 * t60 * r1 * t138 * t140)
  t150 = t5 * t70 * t43
  t154 = t5 * t77 * t120 / 0.12e2
  t156 = f.my_piecewise3(t51, 0, -0.3e1 / 0.8e1 * t5 * t145 * t32 - t150 / 0.4e1 + t154)
  d11 = 0.2e1 * t49 + 0.2e1 * t83 + t6 * (params.alpha * t125 + params.alpha * t156)
  t160 = r0 ** 2
  t161 = t11 * t160
  t162 = t63 * t23
  t166 = f.my_piecewise3(t10, 0, -t21 - 0.2e1 / 0.3e1 * t161 * t162)
  t171 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t166 * t32 - t46)
  t172 = params.alpha * t171
  t175 = t7 * t65
  t177 = -r1 * t18 + t7
  t182 = f.my_piecewise3(t54, 0, 0.2e1 * t12 * t56 - t59 + 0.2e1 / 0.3e1 * t55 * t175 * t177)
  t187 = f.my_piecewise3(t51, 0, -0.3e1 / 0.8e1 * t5 * t182 * t32 - t80)
  t188 = params.alpha * t187
  t194 = t161 * t131 * t23
  t201 = f.my_piecewise3(t10, 0, -0.2e1 * t86 + t93 - 0.2e1 / 0.3e1 * t96 - 0.4e1 / 0.3e1 * t16 * t162 + 0.2e1 * t194 + 0.4e1 / 0.9e1 * t161 * t63 * t99 * t26)
  t206 = t5 * t166 * t43
  t210 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t201 * t32 - t206 / 0.8e1 - t117 / 0.8e1 + t123)
  t212 = t85 * t56
  t221 = t55 * t18 * t65 * t177
  t227 = r1 * t63
  t234 = f.my_piecewise3(t54, 0, -0.2e1 * t212 - 0.2e1 / 0.3e1 * t11 * t63 * t65 * r1 + t129 + 0.2e1 / 0.3e1 * t133 - 0.2e1 / 0.3e1 * t221 + 0.4e1 / 0.9e1 * t61 * t63 * t140 * t177 + 0.2e1 / 0.3e1 * t55 * t175 * (-t18 + 0.2e1 * t227))
  t239 = t5 * t182 * t43
  t243 = f.my_piecewise3(t51, 0, -0.3e1 / 0.8e1 * t5 * t234 * t32 - t239 / 0.8e1 - t150 / 0.8e1 + t154)
  d12 = t49 + t83 + t172 + t188 + t6 * (params.alpha * t210 + params.alpha * t243)
  t256 = f.my_piecewise3(t10, 0, t93 + 0.8e1 / 0.3e1 * t194 - 0.4e1 / 0.9e1 * t11 * t160 * r0 * t138 * t99)
  t262 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t256 * t32 - t206 / 0.4e1 + t123)
  t270 = t177 ** 2
  t280 = f.my_piecewise3(t54, 0, -0.4e1 * t212 + 0.4e1 / 0.3e1 * t12 * t65 * t177 + t129 - 0.4e1 / 0.3e1 * t221 - 0.4e1 / 0.9e1 * t55 * t7 * t140 * t270 + 0.2e1 / 0.3e1 * t55 * t175 * (-0.2e1 * t18 + 0.2e1 * t227))
  t286 = f.my_piecewise3(t51, 0, -0.3e1 / 0.8e1 * t5 * t280 * t32 - t239 / 0.4e1 + t154)
  d22 = 0.2e1 * t172 + 0.2e1 * t188 + t6 * (params.alpha * t262 + params.alpha * t286)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t8 = r0 * t7
  t10 = 0.2e1 * t8 <= f.p.zeta_threshold
  t11 = 2 ** (0.1e1 / 0.3e1)
  t12 = t6 ** 2
  t13 = 0.1e1 / t12
  t14 = t11 * t13
  t15 = t8 ** (0.1e1 / 0.3e1)
  t18 = t11 * t7
  t19 = t15 ** 2
  t20 = 0.1e1 / t19
  t22 = -r0 * t13 + t7
  t23 = t20 * t22
  t26 = t11 * r0
  t27 = t12 * t6
  t28 = 0.1e1 / t27
  t32 = t13 * t20
  t37 = 0.1e1 / t19 / t8
  t39 = t22 ** 2
  t43 = t7 * t20
  t46 = 0.2e1 * r0 * t28 - 0.2e1 * t13
  t51 = f.my_piecewise3(t10, 0, -0.4e1 * t14 * t15 + 0.4e1 / 0.3e1 * t18 * t23 + 0.4e1 * t26 * t28 * t15 - 0.4e1 / 0.3e1 * t26 * t32 * t22 - 0.4e1 / 0.9e1 * t26 * t7 * t37 * t39 + 0.2e1 / 0.3e1 * t26 * t43 * t46)
  t52 = t6 ** (0.1e1 / 0.3e1)
  t65 = f.my_piecewise3(t10, 0, 0.2e1 * t18 * t15 - 0.2e1 * t26 * t13 * t15 + 0.2e1 / 0.3e1 * t26 * t43 * t22)
  t66 = t52 ** 2
  t67 = 0.1e1 / t66
  t71 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t72 = t71 * f.p.zeta_threshold
  t76 = f.my_piecewise3(t10, t72, 0.2e1 * t26 * t7 * t15)
  t78 = 0.1e1 / t66 / t6
  t83 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t51 * t52 - t5 * t65 * t67 / 0.4e1 + t5 * t76 * t78 / 0.12e2)
  t86 = r1 <= f.p.dens_threshold
  t87 = r1 * t7
  t89 = 0.2e1 * t87 <= f.p.zeta_threshold
  t90 = t11 * r1
  t91 = t87 ** (0.1e1 / 0.3e1)
  t95 = r1 ** 2
  t96 = t11 * t95
  t97 = t12 ** 2
  t98 = 0.1e1 / t97
  t99 = t91 ** 2
  t100 = 0.1e1 / t99
  t105 = t11 * t95 * r1
  t107 = 0.1e1 / t97 / t6
  t109 = 0.1e1 / t99 / t87
  t114 = f.my_piecewise3(t89, 0, 0.4e1 * t90 * t28 * t91 + 0.8e1 / 0.3e1 * t96 * t98 * t100 - 0.4e1 / 0.9e1 * t105 * t107 * t109)
  t125 = f.my_piecewise3(t89, 0, -0.2e1 * t90 * t13 * t91 - 0.2e1 / 0.3e1 * t96 * t28 * t100)
  t132 = f.my_piecewise3(t89, t72, 0.2e1 * t90 * t7 * t91)
  t137 = f.my_piecewise3(t86, 0, -0.3e1 / 0.8e1 * t5 * t114 * t52 - t5 * t125 * t67 / 0.4e1 + t5 * t132 * t78 / 0.12e2)
  t165 = r0 ** 2
  t185 = 0.12e2 * t11 * t28 * t15 - 0.4e1 * t14 * t23 - 0.4e1 / 0.3e1 * t18 * t37 * t39 + 0.2e1 * t18 * t20 * t46 - 0.12e2 * t26 * t98 * t15 + 0.4e1 * t26 * t28 * t20 * t22 + 0.4e1 / 0.3e1 * t26 * t13 * t37 * t39 - 0.2e1 * t26 * t32 * t46 + 0.20e2 / 0.27e2 * t26 * t7 / t19 / t165 / t13 * t39 * t22 - 0.4e1 / 0.3e1 * t26 * t7 * t37 * t22 * t46 + 0.2e1 / 0.3e1 * t26 * t43 * (-0.6e1 * r0 * t98 + 0.6e1 * t28)
  t186 = f.my_piecewise3(t10, 0, t185)
  t197 = 0.1e1 / t66 / t12
  t202 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t186 * t52 - 0.3e1 / 0.8e1 * t5 * t51 * t67 + t5 * t65 * t78 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t76 * t197)
  t215 = t95 ** 2
  t226 = f.my_piecewise3(t89, 0, -0.12e2 * t90 * t98 * t91 - 0.12e2 * t96 * t107 * t100 + 0.4e1 * t105 / t97 / t12 * t109 - 0.20e2 / 0.27e2 * t11 * t215 / t97 / t27 / t99 / t95 / t13)
  t240 = f.my_piecewise3(t86, 0, -0.3e1 / 0.8e1 * t5 * t226 * t52 - 0.3e1 / 0.8e1 * t5 * t114 * t67 + t5 * t125 * t78 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t132 * t197)
  d111 = 0.3e1 * params.alpha * t83 + 0.3e1 * params.alpha * t137 + t6 * (params.alpha * t202 + params.alpha * t240)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t8 = r0 * t7
  t10 = 0.2e1 * t8 <= f.p.zeta_threshold
  t11 = 2 ** (0.1e1 / 0.3e1)
  t12 = t6 ** 2
  t13 = t12 * t6
  t14 = 0.1e1 / t13
  t15 = t11 * t14
  t16 = t8 ** (0.1e1 / 0.3e1)
  t19 = 0.1e1 / t12
  t20 = t11 * t19
  t21 = t16 ** 2
  t22 = 0.1e1 / t21
  t24 = -r0 * t19 + t7
  t25 = t22 * t24
  t28 = t11 * t7
  t30 = 0.1e1 / t21 / t8
  t31 = t24 ** 2
  t32 = t30 * t31
  t37 = 0.2e1 * r0 * t14 - 0.2e1 * t19
  t38 = t22 * t37
  t41 = t11 * r0
  t42 = t12 ** 2
  t43 = 0.1e1 / t42
  t47 = t14 * t22
  t55 = t19 * t22
  t59 = r0 ** 2
  t62 = 0.1e1 / t21 / t59 / t19
  t64 = t31 * t24
  t68 = t41 * t7
  t69 = t30 * t24
  t70 = t69 * t37
  t73 = t7 * t22
  t76 = -0.6e1 * r0 * t43 + 0.6e1 * t14
  t80 = 0.12e2 * t15 * t16 - 0.4e1 * t20 * t25 - 0.4e1 / 0.3e1 * t28 * t32 + 0.2e1 * t28 * t38 - 0.12e2 * t41 * t43 * t16 + 0.4e1 * t41 * t47 * t24 + 0.4e1 / 0.3e1 * t41 * t19 * t30 * t31 - 0.2e1 * t41 * t55 * t37 + 0.20e2 / 0.27e2 * t41 * t7 * t62 * t64 - 0.4e1 / 0.3e1 * t68 * t70 + 0.2e1 / 0.3e1 * t41 * t73 * t76
  t81 = f.my_piecewise3(t10, 0, t80)
  t82 = t6 ** (0.1e1 / 0.3e1)
  t96 = t7 * t30
  t104 = f.my_piecewise3(t10, 0, -0.4e1 * t20 * t16 + 0.4e1 / 0.3e1 * t28 * t25 + 0.4e1 * t41 * t14 * t16 - 0.4e1 / 0.3e1 * t41 * t55 * t24 - 0.4e1 / 0.9e1 * t41 * t96 * t31 + 0.2e1 / 0.3e1 * t41 * t73 * t37)
  t105 = t82 ** 2
  t106 = 0.1e1 / t105
  t119 = f.my_piecewise3(t10, 0, 0.2e1 * t28 * t16 - 0.2e1 * t41 * t19 * t16 + 0.2e1 / 0.3e1 * t41 * t73 * t24)
  t121 = 0.1e1 / t105 / t6
  t125 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t126 = t125 * f.p.zeta_threshold
  t130 = f.my_piecewise3(t10, t126, 0.2e1 * t41 * t7 * t16)
  t132 = 0.1e1 / t105 / t12
  t137 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t81 * t82 - 0.3e1 / 0.8e1 * t5 * t104 * t106 + t5 * t119 * t121 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t130 * t132)
  t140 = r1 <= f.p.dens_threshold
  t141 = r1 * t7
  t143 = 0.2e1 * t141 <= f.p.zeta_threshold
  t144 = t11 * r1
  t145 = t141 ** (0.1e1 / 0.3e1)
  t149 = r1 ** 2
  t150 = t11 * t149
  t152 = 0.1e1 / t42 / t6
  t153 = t145 ** 2
  t154 = 0.1e1 / t153
  t158 = t149 * r1
  t159 = t11 * t158
  t161 = 0.1e1 / t42 / t12
  t163 = 0.1e1 / t153 / t141
  t167 = t149 ** 2
  t168 = t11 * t167
  t170 = 0.1e1 / t42 / t13
  t173 = 0.1e1 / t153 / t149 / t19
  t178 = f.my_piecewise3(t143, 0, -0.12e2 * t144 * t43 * t145 - 0.12e2 * t150 * t152 * t154 + 0.4e1 * t159 * t161 * t163 - 0.20e2 / 0.27e2 * t168 * t170 * t173)
  t192 = f.my_piecewise3(t143, 0, 0.4e1 * t144 * t14 * t145 + 0.8e1 / 0.3e1 * t150 * t43 * t154 - 0.4e1 / 0.9e1 * t159 * t152 * t163)
  t203 = f.my_piecewise3(t143, 0, -0.2e1 * t144 * t19 * t145 - 0.2e1 / 0.3e1 * t150 * t14 * t154)
  t210 = f.my_piecewise3(t143, t126, 0.2e1 * t144 * t7 * t145)
  t215 = f.my_piecewise3(t140, 0, -0.3e1 / 0.8e1 * t5 * t178 * t82 - 0.3e1 / 0.8e1 * t5 * t192 * t106 + t5 * t203 * t121 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t210 * t132)
  t270 = t31 ** 2
  t278 = t37 ** 2
  t285 = 0.16e2 / 0.3e1 * t20 * t32 + 0.80e2 / 0.27e2 * t28 * t62 * t64 - 0.16e2 / 0.3e1 * t28 * t70 + 0.48e2 * t41 * t152 * t16 - 0.16e2 * t41 * t43 * t22 * t24 + 0.8e1 * t41 * t47 * t37 - 0.8e1 / 0.3e1 * t41 * t55 * t76 + 0.2e1 / 0.3e1 * t41 * t73 * (0.24e2 * r0 * t152 - 0.24e2 * t43) - 0.48e2 * t11 * t43 * t16 + 0.16e2 * t15 * t25 - 0.8e1 * t20 * t38 + 0.8e1 / 0.3e1 * t28 * t22 * t76 - 0.16e2 / 0.3e1 * t41 * t14 * t30 * t31 - 0.80e2 / 0.27e2 * t41 * t19 * t62 * t64 + 0.16e2 / 0.3e1 * t41 * t19 * t70 - 0.160e3 / 0.81e2 * t41 * t7 / t21 / t59 / r0 / t14 * t270 + 0.40e2 / 0.9e1 * t68 * t62 * t31 * t37 - 0.4e1 / 0.3e1 * t41 * t96 * t278 - 0.16e2 / 0.9e1 * t68 * t69 * t76
  t286 = f.my_piecewise3(t10, 0, t285)
  t300 = 0.1e1 / t105 / t13
  t305 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t286 * t82 - t5 * t81 * t106 / 0.2e1 + t5 * t104 * t121 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t119 * t132 + 0.10e2 / 0.27e2 * t5 * t130 * t300)
  t316 = t42 ** 2
  t332 = f.my_piecewise3(t143, 0, 0.48e2 * t144 * t152 * t145 + 0.64e2 * t150 * t161 * t154 - 0.32e2 * t159 * t170 * t163 + 0.320e3 / 0.27e2 * t168 / t316 * t173 - 0.160e3 / 0.81e2 * t11 * t167 * r1 / t316 / t6 / t153 / t158 / t14)
  t349 = f.my_piecewise3(t140, 0, -0.3e1 / 0.8e1 * t5 * t332 * t82 - t5 * t178 * t106 / 0.2e1 + t5 * t192 * t121 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t203 * t132 + 0.10e2 / 0.27e2 * t5 * t210 * t300)
  d1111 = 0.4e1 * params.alpha * t137 + 0.4e1 * params.alpha * t215 + t6 * (params.alpha * t305 + params.alpha * t349)

  res = {'v4rho4': d1111}
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

  f_lda_x = lambda rs, z: +params_alpha * f.my_piecewise3(f.screen_dens(rs, z), 0, f.lda_x_spin(rs, z)) + params_alpha * f.my_piecewise3(f.screen_dens(rs, -z), 0, f.lda_x_spin(rs, -z))

  functional_body = lambda rs, z: f_lda_x(rs, z)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t5 = t2 / t3
  t6 = r0 + r1
  t7 = 0.1e1 / t6
  t8 = r0 * t7
  t10 = 0.2e1 * t8 <= f.p.zeta_threshold
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t12 = t11 * f.p.zeta_threshold
  t13 = 2 ** (0.1e1 / 0.3e1)
  t14 = t13 * r0
  t15 = t8 ** (0.1e1 / 0.3e1)
  t19 = f.my_piecewise3(t10, t12, 0.2e1 * t14 * t7 * t15)
  t20 = t6 ** (0.1e1 / 0.3e1)
  t24 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t19 * t20)
  t25 = params.alpha * t24
  t26 = r1 <= f.p.dens_threshold
  t27 = r1 * t7
  t29 = 0.2e1 * t27 <= f.p.zeta_threshold
  t30 = t13 * r1
  t31 = t27 ** (0.1e1 / 0.3e1)
  t35 = f.my_piecewise3(t29, t12, 0.2e1 * t30 * t7 * t31)
  t39 = f.my_piecewise3(t26, 0, -0.3e1 / 0.8e1 * t5 * t35 * t20)
  t40 = params.alpha * t39
  t41 = t13 * t7
  t44 = t6 ** 2
  t45 = 0.1e1 / t44
  t48 = 0.2e1 * t14 * t45 * t15
  t49 = t15 ** 2
  t50 = 0.1e1 / t49
  t58 = f.my_piecewise3(t10, 0, 0.2e1 * t41 * t15 - t48 + 0.2e1 / 0.3e1 * t14 * t7 * t50 * (-r0 * t45 + t7))
  t62 = t20 ** 2
  t63 = 0.1e1 / t62
  t66 = t5 * t19 * t63 / 0.8e1
  t68 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t58 * t20 - t66)
  t72 = 0.2e1 * t30 * t45 * t31
  t73 = r1 ** 2
  t76 = 0.1e1 / t44 / t6
  t77 = t31 ** 2
  t78 = 0.1e1 / t77
  t83 = f.my_piecewise3(t29, 0, -t72 - 0.2e1 / 0.3e1 * t13 * t73 * t76 * t78)
  t89 = t5 * t35 * t63 / 0.8e1
  t91 = f.my_piecewise3(t26, 0, -0.3e1 / 0.8e1 * t5 * t83 * t20 - t89)
  vrho_0_ = t25 + t40 + t6 * (params.alpha * t68 + params.alpha * t91)
  t95 = r0 ** 2
  t101 = f.my_piecewise3(t10, 0, -t48 - 0.2e1 / 0.3e1 * t13 * t95 * t76 * t50)
  t106 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t101 * t20 - t66)
  t117 = f.my_piecewise3(t29, 0, 0.2e1 * t41 * t31 - t72 + 0.2e1 / 0.3e1 * t30 * t7 * t78 * (-r1 * t45 + t7))
  t122 = f.my_piecewise3(t26, 0, -0.3e1 / 0.8e1 * t5 * t117 * t20 - t89)
  vrho_1_ = t25 + t40 + t6 * (params.alpha * t106 + params.alpha * t122)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
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

  f_lda_x = lambda rs, z: +params_alpha * f.my_piecewise3(f.screen_dens(rs, z), 0, f.lda_x_spin(rs, z)) + params_alpha * f.my_piecewise3(f.screen_dens(rs, -z), 0, f.lda_x_spin(rs, -z))

  functional_body = lambda rs, z: f_lda_x(rs, z)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t8 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t10 = f.my_piecewise3(0.1e1 <= f.p.zeta_threshold, t8 * f.p.zeta_threshold, 1)
  t11 = r0 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t10 * t11)
  t18 = t11 ** 2
  t23 = f.my_piecewise3(t2, 0, -t6 * t10 / t18 / 0.8e1)
  vrho_0_ = 0.2e1 * r0 * params.alpha * t23 + 0.2e1 * params.alpha * t15
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res