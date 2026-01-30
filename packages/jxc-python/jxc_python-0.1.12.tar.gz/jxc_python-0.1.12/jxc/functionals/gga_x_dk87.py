"""Generated from gga_x_dk87.mpl."""

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))

  dk87_betag = 7 / (432 * jnp.pi * (6 * jnp.pi ** 2) ** (1 / 3)) / X_FACTOR_C

  dk87_f = lambda x: 1 + dk87_betag * x ** 2 * (1 + params_a1 * x ** params_alpha) / (1 + params_b1 * x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, dk87_f, rs, z, xs0, xs1)

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))

  dk87_betag = 7 / (432 * jnp.pi * (6 * jnp.pi ** 2) ** (1 / 3)) / X_FACTOR_C

  dk87_f = lambda x: 1 + dk87_betag * x ** 2 * (1 + params_a1 * x ** params_alpha) / (1 + params_b1 * x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, dk87_f, rs, z, xs0, xs1)

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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))

  dk87_betag = 7 / (432 * jnp.pi * (6 * jnp.pi ** 2) ** (1 / 3)) / X_FACTOR_C

  dk87_f = lambda x: 1 + dk87_betag * x ** 2 * (1 + params_a1 * x ** params_alpha) / (1 + params_b1 * x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, dk87_f, rs, z, xs0, xs1)

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
  t28 = 0.1e1 / jnp.pi
  t29 = 6 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = t28 * t30
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t35 = t2 ** 2
  t36 = t34 * t35
  t37 = t28 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t37
  t40 = t31 * t36 * t38
  t41 = 4 ** (0.1e1 / 0.3e1)
  t42 = t41 * s0
  t43 = r0 ** 2
  t44 = r0 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t47 = 0.1e1 / t45 / t43
  t48 = jnp.sqrt(s0)
  t52 = (t48 / t44 / r0) ** params.alpha
  t54 = params.a1 * t52 + 0.1e1
  t58 = params.b1 * s0 * t47 + 0.1e1
  t59 = 0.1e1 / t58
  t60 = t47 * t54 * t59
  t64 = 0.1e1 + 0.7e1 / 0.11664e5 * t40 * t42 * t60
  t68 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t64)
  t69 = r1 <= f.p.dens_threshold
  t70 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t71 = 0.1e1 + t70
  t72 = t71 <= f.p.zeta_threshold
  t73 = t71 ** (0.1e1 / 0.3e1)
  t75 = f.my_piecewise3(t72, t22, t73 * t71)
  t76 = t75 * t26
  t77 = t41 * s2
  t78 = r1 ** 2
  t79 = r1 ** (0.1e1 / 0.3e1)
  t80 = t79 ** 2
  t82 = 0.1e1 / t80 / t78
  t83 = jnp.sqrt(s2)
  t87 = (t83 / t79 / r1) ** params.alpha
  t89 = params.a1 * t87 + 0.1e1
  t93 = params.b1 * s2 * t82 + 0.1e1
  t94 = 0.1e1 / t93
  t95 = t82 * t89 * t94
  t99 = 0.1e1 + 0.7e1 / 0.11664e5 * t40 * t77 * t95
  t103 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t76 * t99)
  t104 = t6 ** 2
  t106 = t16 / t104
  t107 = t7 - t106
  t108 = f.my_piecewise5(t10, 0, t14, 0, t107)
  t111 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t108)
  t116 = t26 ** 2
  t117 = 0.1e1 / t116
  t121 = t5 * t25 * t117 * t64 / 0.8e1
  t124 = 0.1e1 / t45 / t43 / r0
  t133 = t31 * t34 * t35 * t38 * t41
  t137 = t52 * params.alpha * t59
  t141 = s0 ** 2
  t143 = t43 ** 2
  t148 = t58 ** 2
  t151 = t54 / t148 * params.b1
  t160 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t111 * t26 * t64 - t121 - 0.3e1 / 0.8e1 * t5 * t27 * (-0.7e1 / 0.4374e4 * t40 * t42 * t124 * t54 * t59 - 0.7e1 / 0.8748e4 * t133 * s0 * t124 * params.a1 * t137 + 0.7e1 / 0.4374e4 * t40 * t41 * t141 / t44 / t143 / t43 * t151))
  t162 = f.my_piecewise5(t14, 0, t10, 0, -t107)
  t165 = f.my_piecewise3(t72, 0, 0.4e1 / 0.3e1 * t73 * t162)
  t173 = t5 * t75 * t117 * t99 / 0.8e1
  t175 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t165 * t26 * t99 - t173)
  vrho_0_ = t68 + t103 + t6 * (t160 + t175)
  t178 = -t7 - t106
  t179 = f.my_piecewise5(t10, 0, t14, 0, t178)
  t182 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t179)
  t188 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t182 * t26 * t64 - t121)
  t190 = f.my_piecewise5(t14, 0, t10, 0, -t178)
  t193 = f.my_piecewise3(t72, 0, 0.4e1 / 0.3e1 * t73 * t190)
  t200 = 0.1e1 / t80 / t78 / r1
  t209 = t87 * params.alpha * t94
  t213 = s2 ** 2
  t215 = t78 ** 2
  t220 = t93 ** 2
  t223 = t89 / t220 * params.b1
  t232 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t193 * t26 * t99 - t173 - 0.3e1 / 0.8e1 * t5 * t76 * (-0.7e1 / 0.4374e4 * t40 * t77 * t200 * t89 * t94 - 0.7e1 / 0.8748e4 * t133 * s2 * t200 * params.a1 * t209 + 0.7e1 / 0.4374e4 * t40 * t41 * t213 / t79 / t215 / t78 * t223))
  vrho_1_ = t68 + t103 + t6 * (t188 + t232)
  t235 = t31 * t36
  t236 = t38 * t41
  t256 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (0.7e1 / 0.11664e5 * t235 * t236 * t60 + 0.7e1 / 0.23328e5 * t40 * t41 * t47 * params.a1 * t137 - 0.7e1 / 0.11664e5 * t40 * t42 / t44 / t143 / r0 * t151))
  vsigma_0_ = t6 * t256
  vsigma_1_ = 0.0e0
  t276 = f.my_piecewise3(t69, 0, -0.3e1 / 0.8e1 * t5 * t76 * (0.7e1 / 0.11664e5 * t235 * t236 * t95 + 0.7e1 / 0.23328e5 * t40 * t41 * t82 * params.a1 * t209 - 0.7e1 / 0.11664e5 * t40 * t77 / t79 / t215 / r1 * t223))
  vsigma_2_ = t6 * t276
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
  params_a1_raw = params.a1
  if isinstance(params_a1_raw, (str, bytes, dict)):
    params_a1 = params_a1_raw
  else:
    try:
      params_a1_seq = list(params_a1_raw)
    except TypeError:
      params_a1 = params_a1_raw
    else:
      params_a1_seq = np.asarray(params_a1_seq, dtype=np.float64)
      params_a1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_a1_seq))
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
  params_b1_raw = params.b1
  if isinstance(params_b1_raw, (str, bytes, dict)):
    params_b1 = params_b1_raw
  else:
    try:
      params_b1_seq = list(params_b1_raw)
    except TypeError:
      params_b1 = params_b1_raw
    else:
      params_b1_seq = np.asarray(params_b1_seq, dtype=np.float64)
      params_b1 = np.concatenate((np.array([np.nan], dtype=np.float64), params_b1_seq))

  dk87_betag = 7 / (432 * jnp.pi * (6 * jnp.pi ** 2) ** (1 / 3)) / X_FACTOR_C

  dk87_f = lambda x: 1 + dk87_betag * x ** 2 * (1 + params_a1 * x ** params_alpha) / (1 + params_b1 * x ** 2)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, dk87_f, rs, z, xs0, xs1)

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
  t20 = 0.1e1 / jnp.pi
  t21 = 6 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = t20 * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = t3 ** 2
  t29 = t20 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t29
  t32 = t23 * t26 * t27 * t30
  t33 = 4 ** (0.1e1 / 0.3e1)
  t35 = 2 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = t33 * s0 * t36
  t38 = r0 ** 2
  t39 = t18 ** 2
  t41 = 0.1e1 / t39 / t38
  t42 = jnp.sqrt(s0)
  t47 = (t42 * t35 / t18 / r0) ** params.alpha
  t48 = params.a1 * t47
  t49 = 0.1e1 + t48
  t52 = t36 * t41
  t54 = params.b1 * s0 * t52 + 0.1e1
  t55 = 0.1e1 / t54
  t56 = t41 * t49 * t55
  t60 = 0.1e1 + 0.7e1 / 0.11664e5 * t32 * t37 * t56
  t64 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t60)
  t72 = 0.1e1 / t39 / t38 / r0
  t81 = t23 * t26 * t27 * t30 * t33
  t89 = s0 ** 2
  t91 = t38 ** 2
  t96 = t54 ** 2
  t99 = t49 / t96 * params.b1
  t108 = f.my_piecewise3(t2, 0, -t6 * t17 / t39 * t60 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-0.7e1 / 0.4374e4 * t32 * t37 * t72 * t49 * t55 - 0.7e1 / 0.8748e4 * t81 * s0 * t36 * t72 * t48 * params.alpha * t55 + 0.7e1 / 0.2187e4 * t81 * t89 * t35 / t18 / t91 / t38 * t99))
  vrho_0_ = 0.2e1 * r0 * t108 + 0.2e1 * t64
  t133 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (0.7e1 / 0.11664e5 * t32 * t33 * t36 * t56 + 0.7e1 / 0.23328e5 * t81 * t52 * params.a1 * t47 * params.alpha * t55 - 0.7e1 / 0.5832e4 * t81 * s0 * t35 / t18 / t91 / r0 * t99))
  vsigma_0_ = 0.2e1 * r0 * t133
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
  t21 = t17 / t19
  t22 = 0.1e1 / jnp.pi
  t23 = 6 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = t22 * t24
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = 0.1e1 / t27
  t29 = t3 ** 2
  t31 = t22 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t34 = t25 * t28 * t29 * t32
  t35 = 4 ** (0.1e1 / 0.3e1)
  t36 = t35 * s0
  t37 = 2 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = t36 * t38
  t40 = r0 ** 2
  t42 = 0.1e1 / t19 / t40
  t43 = jnp.sqrt(s0)
  t48 = (t43 * t37 / t18 / r0) ** params.alpha
  t49 = params.a1 * t48
  t50 = 0.1e1 + t49
  t52 = params.b1 * s0
  t53 = t38 * t42
  t55 = t52 * t53 + 0.1e1
  t56 = 0.1e1 / t55
  t57 = t42 * t50 * t56
  t61 = 0.1e1 + 0.7e1 / 0.11664e5 * t34 * t39 * t57
  t65 = t17 * t18
  t66 = t40 * r0
  t68 = 0.1e1 / t19 / t66
  t70 = t68 * t50 * t56
  t74 = t25 * t28
  t75 = t29 * t32
  t77 = t74 * t75 * t35
  t78 = s0 * t38
  t81 = t49 * params.alpha * t56
  t85 = s0 ** 2
  t86 = t85 * t37
  t87 = t40 ** 2
  t90 = 0.1e1 / t18 / t87 / t40
  t92 = t55 ** 2
  t93 = 0.1e1 / t92
  t95 = t50 * t93 * params.b1
  t99 = -0.7e1 / 0.4374e4 * t34 * t39 * t70 - 0.7e1 / 0.8748e4 * t77 * t78 * t68 * t81 + 0.7e1 / 0.2187e4 * t77 * t86 * t90 * t95
  t104 = f.my_piecewise3(t2, 0, -t6 * t21 * t61 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t65 * t99)
  t116 = 0.1e1 / t19 / t87
  t122 = t78 * t116
  t128 = 0.1e1 / t18 / t87 / t66
  t133 = params.alpha ** 2
  t139 = t35 * t85
  t144 = t48 * params.alpha
  t145 = t93 * params.b1
  t146 = t144 * t145
  t152 = t87 ** 2
  t159 = params.b1 ** 2
  t160 = t50 / t92 / t55 * t159
  t169 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t61 / 0.12e2 - t6 * t21 * t99 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t65 * (0.77e2 / 0.13122e5 * t34 * t39 * t116 * t50 * t56 + 0.133e3 / 0.26244e5 * t77 * t122 * t81 - 0.7e1 / 0.243e3 * t77 * t86 * t128 * t95 + 0.7e1 / 0.6561e4 * t77 * t122 * t49 * t133 * t56 - 0.56e2 / 0.6561e4 * t74 * t75 * t139 * t37 * t128 * params.a1 * t146 + 0.224e3 / 0.6561e4 * t34 * t35 * t85 * s0 / t152 / t40 * t160))
  v2rho2_0_ = 0.2e1 * r0 * t169 + 0.4e1 * t104
  t172 = t35 * t38
  t176 = t53 * params.a1
  t177 = t144 * t56
  t184 = 0.1e1 / t18 / t87 / r0
  t189 = 0.7e1 / 0.11664e5 * t34 * t172 * t57 + 0.7e1 / 0.23328e5 * t77 * t176 * t177 - 0.7e1 / 0.5832e4 * t77 * s0 * t37 * t184 * t95
  t193 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t65 * t189)
  t201 = t38 * t68 * params.a1
  t211 = t48 * t133
  t216 = t35 * t37
  t237 = f.my_piecewise3(t2, 0, -t6 * t21 * t189 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t65 * (-0.7e1 / 0.4374e4 * t34 * t172 * t70 - 0.7e1 / 0.4374e4 * t77 * t201 * t177 + 0.7e1 / 0.729e3 * t77 * t37 * t90 * t50 * t145 * s0 - 0.7e1 / 0.17496e5 * t77 * t201 * t211 * t56 + 0.7e1 / 0.2187e4 * t74 * t75 * t216 * t90 * params.a1 * t48 * params.alpha * t93 * t52 - 0.28e2 / 0.2187e4 * t34 * t139 / t152 / r0 * t160))
  v2rhosigma_0_ = 0.2e1 * r0 * t237 + 0.2e1 * t193
  t241 = 0.1e1 / s0 * t56
  t268 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t65 * (0.7e1 / 0.23328e5 * t77 * t176 * t144 * t241 - 0.7e1 / 0.2916e4 * t34 * t216 * t184 * t95 + 0.7e1 / 0.46656e5 * t77 * t176 * t211 * t241 - 0.7e1 / 0.5832e4 * t77 * t37 * t184 * params.a1 * t146 + 0.7e1 / 0.1458e4 * t34 * t36 / t152 * t160))
  v2sigma2_0_ = 0.2e1 * r0 * t268
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
  t22 = t17 / t19 / r0
  t23 = 0.1e1 / jnp.pi
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = t23 * t25
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t28
  t30 = t3 ** 2
  t32 = t23 ** (0.1e1 / 0.3e1)
  t33 = 0.1e1 / t32
  t35 = t26 * t29 * t30 * t33
  t36 = 4 ** (0.1e1 / 0.3e1)
  t38 = 2 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = t36 * s0 * t39
  t41 = r0 ** 2
  t43 = 0.1e1 / t19 / t41
  t44 = jnp.sqrt(s0)
  t49 = (t44 * t38 / t18 / r0) ** params.alpha
  t50 = params.a1 * t49
  t51 = 0.1e1 + t50
  t56 = params.b1 * s0 * t39 * t43 + 0.1e1
  t57 = 0.1e1 / t56
  t62 = 0.1e1 + 0.7e1 / 0.11664e5 * t35 * t40 * t43 * t51 * t57
  t67 = t17 / t19
  t68 = t41 * r0
  t70 = 0.1e1 / t19 / t68
  t76 = t26 * t29
  t77 = t30 * t33
  t79 = t76 * t77 * t36
  t80 = s0 * t39
  t83 = t50 * params.alpha * t57
  t87 = s0 ** 2
  t88 = t87 * t38
  t89 = t41 ** 2
  t94 = t56 ** 2
  t95 = 0.1e1 / t94
  t97 = t51 * t95 * params.b1
  t101 = -0.7e1 / 0.4374e4 * t35 * t40 * t70 * t51 * t57 - 0.7e1 / 0.8748e4 * t79 * t80 * t70 * t83 + 0.7e1 / 0.2187e4 * t79 * t88 / t18 / t89 / t41 * t97
  t105 = t17 * t18
  t107 = 0.1e1 / t19 / t89
  t113 = t80 * t107
  t119 = 0.1e1 / t18 / t89 / t68
  t124 = params.alpha ** 2
  t126 = t50 * t124 * t57
  t132 = t76 * t77 * t36 * t87
  t135 = t49 * params.alpha
  t136 = t95 * params.b1
  t137 = t135 * t136
  t141 = t87 * s0
  t142 = t36 * t141
  t143 = t89 ** 2
  t148 = 0.1e1 / t94 / t56
  t150 = params.b1 ** 2
  t151 = t51 * t148 * t150
  t155 = 0.77e2 / 0.13122e5 * t35 * t40 * t107 * t51 * t57 + 0.133e3 / 0.26244e5 * t79 * t113 * t83 - 0.7e1 / 0.243e3 * t79 * t88 * t119 * t97 + 0.7e1 / 0.6561e4 * t79 * t113 * t126 - 0.56e2 / 0.6561e4 * t132 * t38 * t119 * params.a1 * t137 + 0.224e3 / 0.6561e4 * t35 * t142 / t143 / t41 * t151
  t160 = f.my_piecewise3(t2, 0, t6 * t22 * t62 / 0.12e2 - t6 * t67 * t101 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t105 * t155)
  t172 = t89 * r0
  t174 = 0.1e1 / t19 / t172
  t180 = t80 * t174
  t185 = 0.1e1 / t18 / t143
  t194 = t38 * t185 * params.a1
  t199 = 0.1e1 / t143 / t68
  t222 = t87 ** 2
  t228 = t94 ** 2
  t241 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t43 * t62 + t6 * t22 * t101 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t67 * t155 - 0.3e1 / 0.8e1 * t6 * t105 * (-0.539e3 / 0.19683e5 * t35 * t40 * t174 * t51 * t57 - 0.413e3 / 0.13122e5 * t79 * t180 * t83 + 0.4774e4 / 0.19683e5 * t79 * t88 * t185 * t97 - 0.77e2 / 0.6561e4 * t79 * t180 * t126 + 0.280e3 / 0.2187e4 * t132 * t194 * t137 - 0.4256e4 / 0.6561e4 * t35 * t142 * t199 * t151 - 0.28e2 / 0.19683e5 * t79 * t180 * t50 * t124 * params.alpha * t57 + 0.112e3 / 0.6561e4 * t132 * t194 * t49 * t124 * t136 - 0.896e3 / 0.6561e4 * t79 * t141 * t199 * params.a1 * t135 * t148 * t150 + 0.1792e4 / 0.6561e4 * t79 * t222 / t19 / t143 / t172 * t51 / t228 * t150 * params.b1 * t39))
  v3rho3_0_ = 0.2e1 * r0 * t241 + 0.6e1 * t160

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
  t23 = t17 * t22
  t24 = 0.1e1 / jnp.pi
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = t24 * t26
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = 0.1e1 / t29
  t31 = t3 ** 2
  t33 = t24 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t36 = t27 * t30 * t31 * t34
  t37 = 4 ** (0.1e1 / 0.3e1)
  t39 = 2 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t41 = t37 * s0 * t40
  t42 = jnp.sqrt(s0)
  t47 = (t42 * t39 / t19 / r0) ** params.alpha
  t48 = params.a1 * t47
  t49 = 0.1e1 + t48
  t54 = params.b1 * s0 * t40 * t22 + 0.1e1
  t55 = 0.1e1 / t54
  t60 = 0.1e1 + 0.7e1 / 0.11664e5 * t36 * t41 * t22 * t49 * t55
  t66 = t17 / t20 / r0
  t67 = t18 * r0
  t69 = 0.1e1 / t20 / t67
  t75 = t27 * t30
  t76 = t31 * t34
  t78 = t75 * t76 * t37
  t79 = s0 * t40
  t82 = t48 * params.alpha * t55
  t86 = s0 ** 2
  t87 = t86 * t39
  t88 = t18 ** 2
  t89 = t88 * t18
  t93 = t54 ** 2
  t94 = 0.1e1 / t93
  t96 = t49 * t94 * params.b1
  t100 = -0.7e1 / 0.4374e4 * t36 * t41 * t69 * t49 * t55 - 0.7e1 / 0.8748e4 * t78 * t79 * t69 * t82 + 0.7e1 / 0.2187e4 * t78 * t87 / t19 / t89 * t96
  t105 = t17 / t20
  t107 = 0.1e1 / t20 / t88
  t113 = t79 * t107
  t119 = 0.1e1 / t19 / t88 / t67
  t124 = params.alpha ** 2
  t126 = t48 * t124 * t55
  t132 = t75 * t76 * t37 * t86
  t135 = t47 * params.alpha
  t136 = t94 * params.b1
  t137 = t135 * t136
  t141 = t86 * s0
  t142 = t37 * t141
  t143 = t88 ** 2
  t148 = 0.1e1 / t93 / t54
  t150 = params.b1 ** 2
  t151 = t49 * t148 * t150
  t155 = 0.77e2 / 0.13122e5 * t36 * t41 * t107 * t49 * t55 + 0.133e3 / 0.26244e5 * t78 * t113 * t82 - 0.7e1 / 0.243e3 * t78 * t87 * t119 * t96 + 0.7e1 / 0.6561e4 * t78 * t113 * t126 - 0.56e2 / 0.6561e4 * t132 * t39 * t119 * params.a1 * t137 + 0.224e3 / 0.6561e4 * t36 * t142 / t143 / t18 * t151
  t159 = t17 * t19
  t160 = t88 * r0
  t162 = 0.1e1 / t20 / t160
  t168 = t79 * t162
  t173 = 0.1e1 / t19 / t143
  t182 = t39 * t173 * params.a1
  t187 = 0.1e1 / t143 / t67
  t192 = t124 * params.alpha
  t194 = t48 * t192 * t55
  t198 = t47 * t124
  t199 = t198 * t136
  t205 = t148 * t150
  t206 = t135 * t205
  t210 = t86 ** 2
  t216 = t93 ** 2
  t217 = 0.1e1 / t216
  t218 = t150 * params.b1
  t220 = t217 * t218 * t40
  t224 = -0.539e3 / 0.19683e5 * t36 * t41 * t162 * t49 * t55 - 0.413e3 / 0.13122e5 * t78 * t168 * t82 + 0.4774e4 / 0.19683e5 * t78 * t87 * t173 * t96 - 0.77e2 / 0.6561e4 * t78 * t168 * t126 + 0.280e3 / 0.2187e4 * t132 * t182 * t137 - 0.4256e4 / 0.6561e4 * t36 * t142 * t187 * t151 - 0.28e2 / 0.19683e5 * t78 * t168 * t194 + 0.112e3 / 0.6561e4 * t132 * t182 * t199 - 0.896e3 / 0.6561e4 * t78 * t141 * t187 * params.a1 * t206 + 0.1792e4 / 0.6561e4 * t78 * t210 / t20 / t143 / t160 * t49 * t220
  t229 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t60 + t6 * t66 * t100 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t105 * t155 - 0.3e1 / 0.8e1 * t6 * t159 * t224)
  t245 = 0.1e1 / t20 / t89
  t246 = t79 * t245
  t251 = 0.1e1 / t143 / t88
  t253 = t141 * t251 * params.a1
  t257 = t124 ** 2
  t275 = 0.1e1 / t20 / t143 / t89
  t282 = t143 ** 2
  t290 = t150 ** 2
  t303 = 0.1e1 / t19 / t143 / r0
  t309 = t39 * t303 * params.a1
  t336 = 0.1400e4 / 0.59049e5 * t78 * t246 * t194 + 0.73472e5 / 0.19683e5 * t78 * t253 * t206 + 0.112e3 / 0.59049e5 * t78 * t246 * t48 * t257 * t55 + 0.7168e4 / 0.19683e5 * t78 * t253 * t198 * t205 + 0.2135e4 / 0.19683e5 * t78 * t246 * t126 + 0.25375e5 / 0.118098e6 * t78 * t246 * t82 - 0.175616e6 / 0.19683e5 * t78 * t210 * t275 * t49 * t220 + 0.114688e6 / 0.19683e5 * t78 * t210 * s0 / t19 / t282 / r0 * t49 / t216 / t54 * t290 * t39 + 0.9163e4 / 0.59049e5 * t36 * t41 * t245 * t49 * t55 - 0.42658e5 / 0.19683e5 * t78 * t87 * t303 * t96 - 0.92008e5 / 0.59049e5 * t132 * t309 * t137 - 0.2464e4 / 0.6561e4 * t132 * t309 * t199 - 0.1792e4 / 0.59049e5 * t132 * t309 * t47 * t192 * t136 - 0.28672e5 / 0.19683e5 * t75 * t76 * t37 * t210 * t275 * params.a1 * t47 * params.alpha * t217 * t218 * t40 + 0.574112e6 / 0.59049e5 * t36 * t142 * t251 * t151
  t341 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t69 * t60 - 0.5e1 / 0.9e1 * t6 * t23 * t100 + t6 * t66 * t155 / 0.2e1 - t6 * t105 * t224 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t159 * t336)
  v4rho4_0_ = 0.2e1 * r0 * t341 + 0.8e1 * t229

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
  t32 = 0.1e1 / jnp.pi
  t33 = 6 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = t32 * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = 0.1e1 / t37
  t39 = t2 ** 2
  t41 = t32 ** (0.1e1 / 0.3e1)
  t42 = 0.1e1 / t41
  t44 = t35 * t38 * t39 * t42
  t45 = 4 ** (0.1e1 / 0.3e1)
  t46 = t45 * s0
  t47 = r0 ** 2
  t48 = r0 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t51 = 0.1e1 / t49 / t47
  t52 = jnp.sqrt(s0)
  t56 = (t52 / t48 / r0) ** params.alpha
  t58 = params.a1 * t56 + 0.1e1
  t62 = params.b1 * s0 * t51 + 0.1e1
  t63 = 0.1e1 / t62
  t68 = 0.1e1 + 0.7e1 / 0.11664e5 * t44 * t46 * t51 * t58 * t63
  t72 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t73 = t72 * f.p.zeta_threshold
  t75 = f.my_piecewise3(t20, t73, t21 * t19)
  t76 = t30 ** 2
  t77 = 0.1e1 / t76
  t78 = t75 * t77
  t81 = t5 * t78 * t68 / 0.8e1
  t82 = t75 * t30
  t83 = t47 * r0
  t85 = 0.1e1 / t49 / t83
  t94 = t35 * t38 * t39 * t42 * t45
  t97 = t56 * params.alpha
  t98 = t97 * t63
  t102 = s0 ** 2
  t103 = t45 * t102
  t104 = t47 ** 2
  t109 = t62 ** 2
  t110 = 0.1e1 / t109
  t112 = t58 * t110 * params.b1
  t116 = -0.7e1 / 0.4374e4 * t44 * t46 * t85 * t58 * t63 - 0.7e1 / 0.8748e4 * t94 * s0 * t85 * params.a1 * t98 + 0.7e1 / 0.4374e4 * t44 * t103 / t48 / t104 / t47 * t112
  t121 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t68 - t81 - 0.3e1 / 0.8e1 * t5 * t82 * t116)
  t123 = r1 <= f.p.dens_threshold
  t124 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t125 = 0.1e1 + t124
  t126 = t125 <= f.p.zeta_threshold
  t127 = t125 ** (0.1e1 / 0.3e1)
  t129 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t132 = f.my_piecewise3(t126, 0, 0.4e1 / 0.3e1 * t127 * t129)
  t133 = t132 * t30
  t134 = t45 * s2
  t135 = r1 ** 2
  t136 = r1 ** (0.1e1 / 0.3e1)
  t137 = t136 ** 2
  t139 = 0.1e1 / t137 / t135
  t140 = jnp.sqrt(s2)
  t144 = (t140 / t136 / r1) ** params.alpha
  t146 = params.a1 * t144 + 0.1e1
  t150 = params.b1 * s2 * t139 + 0.1e1
  t151 = 0.1e1 / t150
  t156 = 0.1e1 + 0.7e1 / 0.11664e5 * t44 * t134 * t139 * t146 * t151
  t161 = f.my_piecewise3(t126, t73, t127 * t125)
  t162 = t161 * t77
  t165 = t5 * t162 * t156 / 0.8e1
  t167 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t5 * t133 * t156 - t165)
  t169 = t21 ** 2
  t170 = 0.1e1 / t169
  t171 = t26 ** 2
  t176 = t16 / t22 / t6
  t178 = -0.2e1 * t23 + 0.2e1 * t176
  t179 = f.my_piecewise5(t10, 0, t14, 0, t178)
  t183 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t170 * t171 + 0.4e1 / 0.3e1 * t21 * t179)
  t190 = t5 * t29 * t77 * t68
  t196 = 0.1e1 / t76 / t6
  t200 = t5 * t75 * t196 * t68 / 0.12e2
  t202 = t5 * t78 * t116
  t205 = 0.1e1 / t49 / t104
  t212 = s0 * t205 * params.a1
  t218 = 0.1e1 / t48 / t104 / t83
  t223 = params.alpha ** 2
  t238 = t104 ** 2
  t245 = params.b1 ** 2
  t255 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t183 * t30 * t68 - t190 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t116 + t200 - t202 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t82 * (0.77e2 / 0.13122e5 * t44 * t46 * t205 * t58 * t63 + 0.133e3 / 0.26244e5 * t94 * t212 * t98 - 0.7e1 / 0.486e3 * t44 * t103 * t218 * t112 + 0.7e1 / 0.6561e4 * t94 * t212 * t56 * t223 * t63 - 0.28e2 / 0.6561e4 * t94 * t102 * t218 * params.a1 * t97 * t110 * params.b1 + 0.56e2 / 0.6561e4 * t44 * t45 * t102 * s0 / t238 / t47 * t58 / t109 / t62 * t245))
  t256 = t127 ** 2
  t257 = 0.1e1 / t256
  t258 = t129 ** 2
  t262 = f.my_piecewise5(t14, 0, t10, 0, -t178)
  t266 = f.my_piecewise3(t126, 0, 0.4e1 / 0.9e1 * t257 * t258 + 0.4e1 / 0.3e1 * t127 * t262)
  t273 = t5 * t132 * t77 * t156
  t278 = t5 * t161 * t196 * t156 / 0.12e2
  t280 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t5 * t266 * t30 * t156 - t273 / 0.4e1 + t278)
  d11 = 0.2e1 * t121 + 0.2e1 * t167 + t6 * (t255 + t280)
  t283 = -t7 - t24
  t284 = f.my_piecewise5(t10, 0, t14, 0, t283)
  t287 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t284)
  t288 = t287 * t30
  t293 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t288 * t68 - t81)
  t295 = f.my_piecewise5(t14, 0, t10, 0, -t283)
  t298 = f.my_piecewise3(t126, 0, 0.4e1 / 0.3e1 * t127 * t295)
  t299 = t298 * t30
  t303 = t161 * t30
  t304 = t135 * r1
  t306 = 0.1e1 / t137 / t304
  t314 = t144 * params.alpha
  t315 = t314 * t151
  t319 = s2 ** 2
  t320 = t45 * t319
  t321 = t135 ** 2
  t326 = t150 ** 2
  t327 = 0.1e1 / t326
  t329 = t146 * t327 * params.b1
  t333 = -0.7e1 / 0.4374e4 * t44 * t134 * t306 * t146 * t151 - 0.7e1 / 0.8748e4 * t94 * s2 * t306 * params.a1 * t315 + 0.7e1 / 0.4374e4 * t44 * t320 / t136 / t321 / t135 * t329
  t338 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t5 * t299 * t156 - t165 - 0.3e1 / 0.8e1 * t5 * t303 * t333)
  t342 = 0.2e1 * t176
  t343 = f.my_piecewise5(t10, 0, t14, 0, t342)
  t347 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t170 * t284 * t26 + 0.4e1 / 0.3e1 * t21 * t343)
  t354 = t5 * t287 * t77 * t68
  t362 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t347 * t30 * t68 - t354 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t288 * t116 - t190 / 0.8e1 + t200 - t202 / 0.8e1)
  t366 = f.my_piecewise5(t14, 0, t10, 0, -t342)
  t370 = f.my_piecewise3(t126, 0, 0.4e1 / 0.9e1 * t257 * t295 * t129 + 0.4e1 / 0.3e1 * t127 * t366)
  t377 = t5 * t298 * t77 * t156
  t384 = t5 * t162 * t333
  t387 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t5 * t370 * t30 * t156 - t377 / 0.8e1 - t273 / 0.8e1 + t278 - 0.3e1 / 0.8e1 * t5 * t133 * t333 - t384 / 0.8e1)
  d12 = t121 + t167 + t293 + t338 + t6 * (t362 + t387)
  t392 = t284 ** 2
  t396 = 0.2e1 * t23 + 0.2e1 * t176
  t397 = f.my_piecewise5(t10, 0, t14, 0, t396)
  t401 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t170 * t392 + 0.4e1 / 0.3e1 * t21 * t397)
  t408 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t401 * t30 * t68 - t354 / 0.4e1 + t200)
  t409 = t295 ** 2
  t413 = f.my_piecewise5(t14, 0, t10, 0, -t396)
  t417 = f.my_piecewise3(t126, 0, 0.4e1 / 0.9e1 * t257 * t409 + 0.4e1 / 0.3e1 * t127 * t413)
  t428 = 0.1e1 / t137 / t321
  t435 = s2 * t428 * params.a1
  t441 = 0.1e1 / t136 / t321 / t304
  t460 = t321 ** 2
  t476 = f.my_piecewise3(t123, 0, -0.3e1 / 0.8e1 * t5 * t417 * t30 * t156 - t377 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t299 * t333 + t278 - t384 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t303 * (0.77e2 / 0.13122e5 * t44 * t134 * t428 * t146 * t151 + 0.133e3 / 0.26244e5 * t94 * t435 * t315 - 0.7e1 / 0.486e3 * t44 * t320 * t441 * t329 + 0.7e1 / 0.6561e4 * t94 * t435 * t144 * t223 * t151 - 0.28e2 / 0.6561e4 * t94 * t319 * t441 * params.a1 * t314 * t327 * params.b1 + 0.56e2 / 0.6561e4 * t44 * t45 * t319 * s2 / t460 / t135 * t146 / t326 / t150 * t245))
  d22 = 0.2e1 * t293 + 0.2e1 * t338 + t6 * (t408 + t476)
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
  t43 = t41 * t42
  t44 = 0.1e1 / jnp.pi
  t45 = 6 ** (0.1e1 / 0.3e1)
  t46 = t45 ** 2
  t47 = t44 * t46
  t48 = jnp.pi ** 2
  t49 = t48 ** (0.1e1 / 0.3e1)
  t50 = 0.1e1 / t49
  t51 = t2 ** 2
  t53 = t44 ** (0.1e1 / 0.3e1)
  t54 = 0.1e1 / t53
  t56 = t47 * t50 * t51 * t54
  t57 = 4 ** (0.1e1 / 0.3e1)
  t58 = t57 * s0
  t59 = r0 ** 2
  t60 = r0 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t63 = 0.1e1 / t61 / t59
  t64 = jnp.sqrt(s0)
  t68 = (t64 / t60 / r0) ** params.alpha
  t70 = params.a1 * t68 + 0.1e1
  t74 = params.b1 * s0 * t63 + 0.1e1
  t75 = 0.1e1 / t74
  t80 = 0.1e1 + 0.7e1 / 0.11664e5 * t56 * t58 * t63 * t70 * t75
  t86 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t87 = t42 ** 2
  t88 = 0.1e1 / t87
  t89 = t86 * t88
  t93 = t86 * t42
  t94 = t59 * r0
  t96 = 0.1e1 / t61 / t94
  t105 = t47 * t50 * t51 * t54 * t57
  t108 = t68 * params.alpha
  t109 = t108 * t75
  t113 = s0 ** 2
  t114 = t57 * t113
  t115 = t59 ** 2
  t120 = t74 ** 2
  t121 = 0.1e1 / t120
  t123 = t70 * t121 * params.b1
  t127 = -0.7e1 / 0.4374e4 * t56 * t58 * t96 * t70 * t75 - 0.7e1 / 0.8748e4 * t105 * s0 * t96 * params.a1 * t109 + 0.7e1 / 0.4374e4 * t56 * t114 / t60 / t115 / t59 * t123
  t131 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t132 = t131 * f.p.zeta_threshold
  t134 = f.my_piecewise3(t20, t132, t21 * t19)
  t136 = 0.1e1 / t87 / t6
  t137 = t134 * t136
  t141 = t134 * t88
  t145 = t134 * t42
  t147 = 0.1e1 / t61 / t115
  t154 = s0 * t147 * params.a1
  t160 = 0.1e1 / t60 / t115 / t94
  t165 = params.alpha ** 2
  t166 = t68 * t165
  t167 = t166 * t75
  t173 = t121 * params.b1
  t174 = t108 * t173
  t178 = t113 * s0
  t179 = t57 * t178
  t180 = t115 ** 2
  t185 = 0.1e1 / t120 / t74
  t187 = params.b1 ** 2
  t188 = t70 * t185 * t187
  t192 = 0.77e2 / 0.13122e5 * t56 * t58 * t147 * t70 * t75 + 0.133e3 / 0.26244e5 * t105 * t154 * t109 - 0.7e1 / 0.486e3 * t56 * t114 * t160 * t123 + 0.7e1 / 0.6561e4 * t105 * t154 * t167 - 0.28e2 / 0.6561e4 * t105 * t113 * t160 * params.a1 * t174 + 0.56e2 / 0.6561e4 * t56 * t179 / t180 / t59 * t188
  t197 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t80 - t5 * t89 * t80 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t93 * t127 + t5 * t137 * t80 / 0.12e2 - t5 * t141 * t127 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t145 * t192)
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
  t219 = r1 ** 2
  t220 = r1 ** (0.1e1 / 0.3e1)
  t221 = t220 ** 2
  t223 = 0.1e1 / t221 / t219
  t224 = jnp.sqrt(s2)
  t228 = (t224 / t220 / r1) ** params.alpha
  t240 = 0.1e1 + 0.7e1 / 0.11664e5 * t56 * t57 * s2 * t223 * (params.a1 * t228 + 0.1e1) / (params.b1 * s2 * t223 + 0.1e1)
  t246 = f.my_piecewise3(t202, 0, 0.4e1 / 0.3e1 * t203 * t207)
  t252 = f.my_piecewise3(t202, t132, t203 * t201)
  t258 = f.my_piecewise3(t199, 0, -0.3e1 / 0.8e1 * t5 * t216 * t42 * t240 - t5 * t246 * t88 * t240 / 0.4e1 + t5 * t252 * t136 * t240 / 0.12e2)
  t268 = t24 ** 2
  t272 = 0.6e1 * t33 - 0.6e1 * t16 / t268
  t273 = f.my_piecewise5(t10, 0, t14, 0, t272)
  t277 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t273)
  t300 = 0.1e1 / t87 / t24
  t311 = t115 * r0
  t313 = 0.1e1 / t61 / t311
  t320 = s0 * t313 * params.a1
  t325 = 0.1e1 / t60 / t180
  t334 = t113 * t325 * params.a1
  t339 = 0.1e1 / t180 / t94
  t361 = t113 ** 2
  t367 = t120 ** 2
  t380 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t277 * t42 * t80 - 0.3e1 / 0.8e1 * t5 * t41 * t88 * t80 - 0.9e1 / 0.8e1 * t5 * t43 * t127 + t5 * t86 * t136 * t80 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t89 * t127 - 0.9e1 / 0.8e1 * t5 * t93 * t192 - 0.5e1 / 0.36e2 * t5 * t134 * t300 * t80 + t5 * t137 * t127 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t141 * t192 - 0.3e1 / 0.8e1 * t5 * t145 * (-0.539e3 / 0.19683e5 * t56 * t58 * t313 * t70 * t75 - 0.413e3 / 0.13122e5 * t105 * t320 * t109 + 0.2387e4 / 0.19683e5 * t56 * t114 * t325 * t123 - 0.77e2 / 0.6561e4 * t105 * t320 * t167 + 0.140e3 / 0.2187e4 * t105 * t334 * t174 - 0.1064e4 / 0.6561e4 * t56 * t179 * t339 * t188 - 0.28e2 / 0.19683e5 * t105 * t320 * t68 * t165 * params.alpha * t75 + 0.56e2 / 0.6561e4 * t105 * t334 * t166 * t173 - 0.224e3 / 0.6561e4 * t105 * t178 * t339 * params.a1 * t108 * t185 * t187 + 0.448e3 / 0.6561e4 * t56 * t57 * t361 / t61 / t180 / t311 * t70 / t367 * t187 * params.b1))
  t390 = f.my_piecewise5(t14, 0, t10, 0, -t272)
  t394 = f.my_piecewise3(t202, 0, -0.8e1 / 0.27e2 / t204 / t201 * t208 * t207 + 0.4e1 / 0.3e1 * t205 * t207 * t212 + 0.4e1 / 0.3e1 * t203 * t390)
  t412 = f.my_piecewise3(t199, 0, -0.3e1 / 0.8e1 * t5 * t394 * t42 * t240 - 0.3e1 / 0.8e1 * t5 * t216 * t88 * t240 + t5 * t246 * t136 * t240 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t252 * t300 * t240)
  d111 = 0.3e1 * t197 + 0.3e1 * t258 + t6 * (t380 + t412)

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
  t56 = 0.1e1 / jnp.pi
  t57 = 6 ** (0.1e1 / 0.3e1)
  t58 = t57 ** 2
  t59 = t56 * t58
  t60 = jnp.pi ** 2
  t61 = t60 ** (0.1e1 / 0.3e1)
  t62 = 0.1e1 / t61
  t63 = t2 ** 2
  t65 = t56 ** (0.1e1 / 0.3e1)
  t66 = 0.1e1 / t65
  t68 = t59 * t62 * t63 * t66
  t69 = 4 ** (0.1e1 / 0.3e1)
  t70 = t69 * s0
  t71 = r0 ** 2
  t72 = r0 ** (0.1e1 / 0.3e1)
  t73 = t72 ** 2
  t75 = 0.1e1 / t73 / t71
  t76 = jnp.sqrt(s0)
  t80 = (t76 / t72 / r0) ** params.alpha
  t82 = params.a1 * t80 + 0.1e1
  t86 = params.b1 * s0 * t75 + 0.1e1
  t87 = 0.1e1 / t86
  t92 = 0.1e1 + 0.7e1 / 0.11664e5 * t68 * t70 * t75 * t82 * t87
  t101 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t102 = t54 ** 2
  t103 = 0.1e1 / t102
  t104 = t101 * t103
  t108 = t101 * t54
  t109 = t71 * r0
  t111 = 0.1e1 / t73 / t109
  t120 = t59 * t62 * t63 * t66 * t69
  t123 = t80 * params.alpha
  t124 = t123 * t87
  t128 = s0 ** 2
  t129 = t69 * t128
  t130 = t71 ** 2
  t131 = t130 * t71
  t135 = t86 ** 2
  t136 = 0.1e1 / t135
  t138 = t82 * t136 * params.b1
  t142 = -0.7e1 / 0.4374e4 * t68 * t70 * t111 * t82 * t87 - 0.7e1 / 0.8748e4 * t120 * s0 * t111 * params.a1 * t124 + 0.7e1 / 0.4374e4 * t68 * t129 / t72 / t131 * t138
  t148 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t150 = 0.1e1 / t102 / t6
  t151 = t148 * t150
  t155 = t148 * t103
  t159 = t148 * t54
  t161 = 0.1e1 / t73 / t130
  t168 = s0 * t161 * params.a1
  t174 = 0.1e1 / t72 / t130 / t109
  t179 = params.alpha ** 2
  t180 = t80 * t179
  t181 = t180 * t87
  t187 = t136 * params.b1
  t188 = t123 * t187
  t192 = t128 * s0
  t193 = t69 * t192
  t194 = t130 ** 2
  t199 = 0.1e1 / t135 / t86
  t201 = params.b1 ** 2
  t202 = t82 * t199 * t201
  t206 = 0.77e2 / 0.13122e5 * t68 * t70 * t161 * t82 * t87 + 0.133e3 / 0.26244e5 * t120 * t168 * t124 - 0.7e1 / 0.486e3 * t68 * t129 * t174 * t138 + 0.7e1 / 0.6561e4 * t120 * t168 * t181 - 0.28e2 / 0.6561e4 * t120 * t128 * t174 * params.a1 * t188 + 0.56e2 / 0.6561e4 * t68 * t193 / t194 / t71 * t202
  t210 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t211 = t210 * f.p.zeta_threshold
  t213 = f.my_piecewise3(t20, t211, t21 * t19)
  t215 = 0.1e1 / t102 / t25
  t216 = t213 * t215
  t220 = t213 * t150
  t224 = t213 * t103
  t228 = t213 * t54
  t229 = t130 * r0
  t231 = 0.1e1 / t73 / t229
  t238 = s0 * t231 * params.a1
  t243 = 0.1e1 / t72 / t194
  t252 = t128 * t243 * params.a1
  t257 = 0.1e1 / t194 / t109
  t263 = t80 * t179 * params.alpha
  t264 = t263 * t87
  t268 = t180 * t187
  t274 = t199 * t201
  t275 = t123 * t274
  t279 = t128 ** 2
  t280 = t69 * t279
  t285 = t135 ** 2
  t286 = 0.1e1 / t285
  t288 = t201 * params.b1
  t289 = t82 * t286 * t288
  t293 = -0.539e3 / 0.19683e5 * t68 * t70 * t231 * t82 * t87 - 0.413e3 / 0.13122e5 * t120 * t238 * t124 + 0.2387e4 / 0.19683e5 * t68 * t129 * t243 * t138 - 0.77e2 / 0.6561e4 * t120 * t238 * t181 + 0.140e3 / 0.2187e4 * t120 * t252 * t188 - 0.1064e4 / 0.6561e4 * t68 * t193 * t257 * t202 - 0.28e2 / 0.19683e5 * t120 * t238 * t264 + 0.56e2 / 0.6561e4 * t120 * t252 * t268 - 0.224e3 / 0.6561e4 * t120 * t192 * t257 * params.a1 * t275 + 0.448e3 / 0.6561e4 * t68 * t280 / t73 / t194 / t229 * t289
  t298 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t92 - 0.3e1 / 0.8e1 * t5 * t104 * t92 - 0.9e1 / 0.8e1 * t5 * t108 * t142 + t5 * t151 * t92 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t155 * t142 - 0.9e1 / 0.8e1 * t5 * t159 * t206 - 0.5e1 / 0.36e2 * t5 * t216 * t92 + t5 * t220 * t142 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t224 * t206 - 0.3e1 / 0.8e1 * t5 * t228 * t293)
  t300 = r1 <= f.p.dens_threshold
  t301 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t302 = 0.1e1 + t301
  t303 = t302 <= f.p.zeta_threshold
  t304 = t302 ** (0.1e1 / 0.3e1)
  t305 = t304 ** 2
  t307 = 0.1e1 / t305 / t302
  t309 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t310 = t309 ** 2
  t314 = 0.1e1 / t305
  t315 = t314 * t309
  t317 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t321 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t325 = f.my_piecewise3(t303, 0, -0.8e1 / 0.27e2 * t307 * t310 * t309 + 0.4e1 / 0.3e1 * t315 * t317 + 0.4e1 / 0.3e1 * t304 * t321)
  t328 = r1 ** 2
  t329 = r1 ** (0.1e1 / 0.3e1)
  t330 = t329 ** 2
  t332 = 0.1e1 / t330 / t328
  t333 = jnp.sqrt(s2)
  t337 = (t333 / t329 / r1) ** params.alpha
  t349 = 0.1e1 + 0.7e1 / 0.11664e5 * t68 * t69 * s2 * t332 * (params.a1 * t337 + 0.1e1) / (params.b1 * s2 * t332 + 0.1e1)
  t358 = f.my_piecewise3(t303, 0, 0.4e1 / 0.9e1 * t314 * t310 + 0.4e1 / 0.3e1 * t304 * t317)
  t365 = f.my_piecewise3(t303, 0, 0.4e1 / 0.3e1 * t304 * t309)
  t371 = f.my_piecewise3(t303, t211, t304 * t302)
  t377 = f.my_piecewise3(t300, 0, -0.3e1 / 0.8e1 * t5 * t325 * t54 * t349 - 0.3e1 / 0.8e1 * t5 * t358 * t103 * t349 + t5 * t365 * t150 * t349 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t371 * t215 * t349)
  t379 = t19 ** 2
  t382 = t30 ** 2
  t388 = t41 ** 2
  t397 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t398 = f.my_piecewise5(t10, 0, t14, 0, t397)
  t402 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t379 * t382 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t388 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t398)
  t434 = 0.1e1 / t194 / t130
  t436 = t192 * t434 * params.a1
  t443 = 0.1e1 / t73 / t194 / t131
  t453 = 0.1e1 / t72 / t194 / r0
  t455 = t128 * t453 * params.a1
  t470 = 0.1e1 / t73 / t131
  t472 = s0 * t470 * params.a1
  t476 = t179 ** 2
  t507 = t194 ** 2
  t515 = t201 ** 2
  t520 = 0.1792e4 / 0.19683e5 * t120 * t436 * t180 * t274 - 0.7168e4 / 0.19683e5 * t120 * t279 * t443 * params.a1 * t123 * t286 * t288 - 0.896e3 / 0.59049e5 * t120 * t455 * t263 * t187 - 0.1232e4 / 0.6561e4 * t120 * t455 * t268 + 0.18368e5 / 0.19683e5 * t120 * t436 * t275 - 0.46004e5 / 0.59049e5 * t120 * t455 * t188 + 0.1400e4 / 0.59049e5 * t120 * t472 * t264 + 0.112e3 / 0.59049e5 * t120 * t472 * t80 * t476 * t87 + 0.25375e5 / 0.118098e6 * t120 * t472 * t124 + 0.2135e4 / 0.19683e5 * t120 * t472 * t181 + 0.9163e4 / 0.59049e5 * t68 * t70 * t470 * t82 * t87 - 0.21329e5 / 0.19683e5 * t68 * t129 * t453 * t138 + 0.143528e6 / 0.59049e5 * t68 * t193 * t434 * t202 - 0.43904e5 / 0.19683e5 * t68 * t280 * t443 * t289 + 0.14336e5 / 0.19683e5 * t68 * t69 * t279 * s0 / t72 / t507 / r0 * t82 / t285 / t86 * t515
  t537 = 0.1e1 / t102 / t36
  t542 = -0.3e1 / 0.8e1 * t5 * t402 * t54 * t92 - 0.3e1 / 0.2e1 * t5 * t55 * t142 - 0.3e1 / 0.2e1 * t5 * t104 * t142 - 0.9e1 / 0.4e1 * t5 * t108 * t206 + t5 * t151 * t142 - 0.3e1 / 0.2e1 * t5 * t155 * t206 - 0.3e1 / 0.2e1 * t5 * t159 * t293 - 0.5e1 / 0.9e1 * t5 * t216 * t142 + t5 * t220 * t206 / 0.2e1 - t5 * t224 * t293 / 0.2e1 - 0.3e1 / 0.8e1 * t5 * t228 * t520 - t5 * t53 * t103 * t92 / 0.2e1 + t5 * t101 * t150 * t92 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t148 * t215 * t92 + 0.10e2 / 0.27e2 * t5 * t213 * t537 * t92
  t543 = f.my_piecewise3(t1, 0, t542)
  t544 = t302 ** 2
  t547 = t310 ** 2
  t553 = t317 ** 2
  t559 = f.my_piecewise5(t14, 0, t10, 0, -t397)
  t563 = f.my_piecewise3(t303, 0, 0.40e2 / 0.81e2 / t305 / t544 * t547 - 0.16e2 / 0.9e1 * t307 * t310 * t317 + 0.4e1 / 0.3e1 * t314 * t553 + 0.16e2 / 0.9e1 * t315 * t321 + 0.4e1 / 0.3e1 * t304 * t559)
  t585 = f.my_piecewise3(t300, 0, -0.3e1 / 0.8e1 * t5 * t563 * t54 * t349 - t5 * t325 * t103 * t349 / 0.2e1 + t5 * t358 * t150 * t349 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t365 * t215 * t349 + 0.10e2 / 0.27e2 * t5 * t371 * t537 * t349)
  d1111 = 0.4e1 * t298 + 0.4e1 * t377 + t6 * (t543 + t585)

  res = {'v4rho4': d1111}
  return res
