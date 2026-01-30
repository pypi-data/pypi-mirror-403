"""Generated from mgga_x_rlda.mpl."""

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
  params_prefactor_raw = params.prefactor
  if isinstance(params_prefactor_raw, (str, bytes, dict)):
    params_prefactor = params_prefactor_raw
  else:
    try:
      params_prefactor_seq = list(params_prefactor_raw)
    except TypeError:
      params_prefactor = params_prefactor_raw
    else:
      params_prefactor_seq = np.asarray(params_prefactor_seq, dtype=np.float64)
      params_prefactor = np.concatenate((np.array([np.nan], dtype=np.float64), params_prefactor_seq))

  rlda_a1 = 5 / 4 * 3 * jnp.pi * params_prefactor / X_FACTOR_C

  rlda_f = lambda x, u, t: rlda_a1 / (2 * t - u / 4)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rlda_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_prefactor_raw = params.prefactor
  if isinstance(params_prefactor_raw, (str, bytes, dict)):
    params_prefactor = params_prefactor_raw
  else:
    try:
      params_prefactor_seq = list(params_prefactor_raw)
    except TypeError:
      params_prefactor = params_prefactor_raw
    else:
      params_prefactor_seq = np.asarray(params_prefactor_seq, dtype=np.float64)
      params_prefactor = np.concatenate((np.array([np.nan], dtype=np.float64), params_prefactor_seq))

  rlda_a1 = 5 / 4 * 3 * jnp.pi * params_prefactor / X_FACTOR_C

  rlda_f = lambda x, u, t: rlda_a1 / (2 * t - u / 4)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rlda_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_prefactor_raw = params.prefactor
  if isinstance(params_prefactor_raw, (str, bytes, dict)):
    params_prefactor = params_prefactor_raw
  else:
    try:
      params_prefactor_seq = list(params_prefactor_raw)
    except TypeError:
      params_prefactor = params_prefactor_raw
    else:
      params_prefactor_seq = np.asarray(params_prefactor_seq, dtype=np.float64)
      params_prefactor = np.concatenate((np.array([np.nan], dtype=np.float64), params_prefactor_seq))

  rlda_a1 = 5 / 4 * 3 * jnp.pi * params_prefactor / X_FACTOR_C

  rlda_f = lambda x, u, t: rlda_a1 / (2 * t - u / 4)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rlda_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t1 = r0 <= f.p.dens_threshold
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t20 = t19 * f.p.zeta_threshold
  t21 = t17 ** (0.1e1 / 0.3e1)
  t23 = f.my_piecewise3(t18, t20, t21 * t17)
  t24 = t3 * t23
  t25 = t4 ** (0.1e1 / 0.3e1)
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t29 = 0.1e1 / t28
  t30 = params.prefactor * t29
  t31 = 4 ** (0.1e1 / 0.3e1)
  t32 = r0 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t35 = 0.1e1 / t33 / r0
  t40 = 0.2e1 * tau0 * t35 - l0 * t35 / 0.4e1
  t43 = t30 * t31 / t40
  t46 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t24 * t25 * t43)
  t47 = r1 <= f.p.dens_threshold
  t48 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t49 = 0.1e1 + t48
  t50 = t49 <= f.p.zeta_threshold
  t51 = t49 ** (0.1e1 / 0.3e1)
  t53 = f.my_piecewise3(t50, t20, t51 * t49)
  t54 = t3 * t53
  t56 = r1 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t59 = 0.1e1 / t57 / r1
  t64 = 0.2e1 * tau1 * t59 - l1 * t59 / 0.4e1
  t67 = t30 * t31 / t64
  t70 = f.my_piecewise3(t47, 0, -0.15e2 / 0.16e2 * t54 * t25 * t67)
  t71 = t4 ** 2
  t73 = t14 / t71
  t74 = t5 - t73
  t75 = f.my_piecewise5(t8, 0, t12, 0, t74)
  t78 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t21 * t75)
  t83 = t25 ** 2
  t84 = 0.1e1 / t83
  t87 = 0.5e1 / 0.16e2 * t24 * t84 * t43
  t88 = t25 * params.prefactor
  t89 = t24 * t88
  t90 = t29 * t31
  t91 = t40 ** 2
  t92 = 0.1e1 / t91
  t93 = r0 ** 2
  t95 = 0.1e1 / t33 / t93
  t106 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t3 * t78 * t25 * t43 - t87 + 0.15e2 / 0.16e2 * t89 * t90 * t92 * (-0.10e2 / 0.3e1 * tau0 * t95 + 0.5e1 / 0.12e2 * l0 * t95))
  t108 = f.my_piecewise5(t12, 0, t8, 0, -t74)
  t111 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t108)
  t118 = 0.5e1 / 0.16e2 * t54 * t84 * t67
  t120 = f.my_piecewise3(t47, 0, -0.15e2 / 0.16e2 * t3 * t111 * t25 * t67 - t118)
  vrho_0_ = t46 + t70 + t4 * (t106 + t120)
  t123 = -t5 - t73
  t124 = f.my_piecewise5(t8, 0, t12, 0, t123)
  t127 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t21 * t124)
  t133 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t3 * t127 * t25 * t43 - t87)
  t135 = f.my_piecewise5(t12, 0, t8, 0, -t123)
  t138 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t135)
  t143 = t54 * t88
  t144 = t64 ** 2
  t145 = 0.1e1 / t144
  t146 = r1 ** 2
  t148 = 0.1e1 / t57 / t146
  t159 = f.my_piecewise3(t47, 0, -0.15e2 / 0.16e2 * t3 * t138 * t25 * t67 - t118 + 0.15e2 / 0.16e2 * t143 * t90 * t145 * (-0.10e2 / 0.3e1 * tau1 * t148 + 0.5e1 / 0.12e2 * l1 * t148))
  vrho_1_ = t46 + t70 + t4 * (t133 + t159)
  vsigma_0_ = 0.0e0
  vsigma_1_ = 0.0e0
  vsigma_2_ = 0.0e0
  t164 = t89 * t90 * t92 * t35
  t166 = f.my_piecewise3(t1, 0, -0.15e2 / 0.64e2 * t164)
  vlapl_0_ = t4 * t166
  t169 = t143 * t90 * t145 * t59
  t171 = f.my_piecewise3(t47, 0, -0.15e2 / 0.64e2 * t169)
  vlapl_1_ = t4 * t171
  t173 = f.my_piecewise3(t1, 0, 0.15e2 / 0.8e1 * t164)
  vtau_0_ = t4 * t173
  t175 = f.my_piecewise3(t47, 0, 0.15e2 / 0.8e1 * t169)
  vtau_1_ = t4 * t175
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
  params_prefactor_raw = params.prefactor
  if isinstance(params_prefactor_raw, (str, bytes, dict)):
    params_prefactor = params_prefactor_raw
  else:
    try:
      params_prefactor_seq = list(params_prefactor_raw)
    except TypeError:
      params_prefactor = params_prefactor_raw
    else:
      params_prefactor_seq = np.asarray(params_prefactor_seq, dtype=np.float64)
      params_prefactor = np.concatenate((np.array([np.nan], dtype=np.float64), params_prefactor_seq))

  rlda_a1 = 5 / 4 * 3 * jnp.pi * params_prefactor / X_FACTOR_C

  rlda_f = lambda x, u, t: rlda_a1 / (2 * t - u / 4)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, rlda_f, rs, z, xs0, xs1, u0, u1, t0, t1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = 0.1e1 <= f.p.zeta_threshold
  t6 = f.p.zeta_threshold - 0.1e1
  t8 = f.my_piecewise5(t5, t6, t5, -t6, 0)
  t9 = 0.1e1 + t8
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t9 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t9 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, t13 * t9)
  t16 = t4 * t15
  t17 = r0 ** (0.1e1 / 0.3e1)
  t20 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t21 = 0.1e1 / t20
  t23 = 4 ** (0.1e1 / 0.3e1)
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t26 = tau0 * t25
  t27 = t17 ** 2
  t29 = 0.1e1 / t27 / r0
  t32 = l0 * t25
  t35 = 0.2e1 * t26 * t29 - t32 * t29 / 0.4e1
  t38 = params.prefactor * t21 * t23 / t35
  t41 = f.my_piecewise3(t2, 0, -0.15e2 / 0.16e2 * t16 * t17 * t38)
  t48 = t21 * t23
  t49 = t35 ** 2
  t50 = 0.1e1 / t49
  t51 = r0 ** 2
  t53 = 0.1e1 / t27 / t51
  t64 = f.my_piecewise3(t2, 0, -0.5e1 / 0.16e2 * t16 / t27 * t38 + 0.15e2 / 0.16e2 * t16 * t17 * params.prefactor * t48 * t50 * (-0.10e2 / 0.3e1 * t26 * t53 + 0.5e1 / 0.12e2 * t32 * t53))
  vrho_0_ = 0.2e1 * r0 * t64 + 0.2e1 * t41
  vsigma_0_ = 0.0e0
  t73 = t16 / t17 / r0 * params.prefactor * t48 * t50 * t25
  t75 = f.my_piecewise3(t2, 0, -0.15e2 / 0.64e2 * t73)
  vlapl_0_ = 0.2e1 * r0 * t75
  t78 = f.my_piecewise3(t2, 0, 0.15e2 / 0.8e1 * t73)
  vtau_0_ = 0.2e1 * r0 * t78
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
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = 0.1e1 <= f.p.zeta_threshold
  t6 = f.p.zeta_threshold - 0.1e1
  t8 = f.my_piecewise5(t5, t6, t5, -t6, 0)
  t9 = 0.1e1 + t8
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t9 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t9 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, t13 * t9)
  t16 = t4 * t15
  t17 = r0 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t19 = 0.1e1 / t18
  t22 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t23 = 0.1e1 / t22
  t25 = 4 ** (0.1e1 / 0.3e1)
  t26 = 2 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = tau0 * t27
  t30 = 0.1e1 / t18 / r0
  t33 = l0 * t27
  t36 = 0.2e1 * t28 * t30 - t33 * t30 / 0.4e1
  t39 = params.prefactor * t23 * t25 / t36
  t43 = t16 * t17 * params.prefactor
  t44 = t23 * t25
  t45 = t36 ** 2
  t46 = 0.1e1 / t45
  t47 = r0 ** 2
  t49 = 0.1e1 / t18 / t47
  t54 = -0.10e2 / 0.3e1 * t28 * t49 + 0.5e1 / 0.12e2 * t33 * t49
  t56 = t44 * t46 * t54
  t60 = f.my_piecewise3(t2, 0, -0.5e1 / 0.16e2 * t16 * t19 * t39 + 0.15e2 / 0.16e2 * t43 * t56)
  t71 = t54 ** 2
  t78 = 0.1e1 / t18 / t47 / r0
  t89 = f.my_piecewise3(t2, 0, 0.5e1 / 0.24e2 * t16 * t30 * t39 + 0.5e1 / 0.8e1 * t16 * t19 * params.prefactor * t56 - 0.15e2 / 0.8e1 * t43 * t44 / t45 / t36 * t71 + 0.15e2 / 0.16e2 * t43 * t44 * t46 * (0.80e2 / 0.9e1 * t28 * t78 - 0.10e2 / 0.9e1 * t33 * t78))
  v2rho2_0_ = 0.2e1 * r0 * t89 + 0.4e1 * t60
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = 0.1e1 <= f.p.zeta_threshold
  t6 = f.p.zeta_threshold - 0.1e1
  t8 = f.my_piecewise5(t5, t6, t5, -t6, 0)
  t9 = 0.1e1 + t8
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t9 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t9 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, t13 * t9)
  t16 = t4 * t15
  t17 = r0 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = 0.1e1 / t18 / r0
  t23 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t23
  t26 = 4 ** (0.1e1 / 0.3e1)
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = tau0 * t28
  t32 = l0 * t28
  t35 = 0.2e1 * t29 * t20 - t32 * t20 / 0.4e1
  t38 = params.prefactor * t24 * t26 / t35
  t43 = t16 / t18 * params.prefactor
  t44 = t24 * t26
  t45 = t35 ** 2
  t46 = 0.1e1 / t45
  t47 = r0 ** 2
  t49 = 0.1e1 / t18 / t47
  t54 = -0.10e2 / 0.3e1 * t29 * t49 + 0.5e1 / 0.12e2 * t32 * t49
  t56 = t44 * t46 * t54
  t60 = t16 * t17 * params.prefactor
  t62 = 0.1e1 / t45 / t35
  t63 = t54 ** 2
  t65 = t44 * t62 * t63
  t70 = 0.1e1 / t18 / t47 / r0
  t75 = 0.80e2 / 0.9e1 * t29 * t70 - 0.10e2 / 0.9e1 * t32 * t70
  t77 = t44 * t46 * t75
  t81 = f.my_piecewise3(t2, 0, 0.5e1 / 0.24e2 * t16 * t20 * t38 + 0.5e1 / 0.8e1 * t43 * t56 - 0.15e2 / 0.8e1 * t60 * t65 + 0.15e2 / 0.16e2 * t60 * t77)
  t94 = t45 ** 2
  t106 = t47 ** 2
  t108 = 0.1e1 / t18 / t106
  t119 = f.my_piecewise3(t2, 0, -0.25e2 / 0.72e2 * t16 * t49 * t38 - 0.5e1 / 0.8e1 * t16 * t20 * params.prefactor * t56 - 0.15e2 / 0.8e1 * t43 * t65 + 0.15e2 / 0.16e2 * t43 * t77 + 0.45e2 / 0.8e1 * t60 * t44 / t94 * t63 * t54 - 0.45e2 / 0.8e1 * t60 * t44 * t62 * t54 * t75 + 0.15e2 / 0.16e2 * t60 * t44 * t46 * (-0.880e3 / 0.27e2 * t29 * t108 + 0.110e3 / 0.27e2 * t32 * t108))
  v3rho3_0_ = 0.2e1 * r0 * t119 + 0.6e1 * t81

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = jnp.pi ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = 0.1e1 <= f.p.zeta_threshold
  t6 = f.p.zeta_threshold - 0.1e1
  t8 = f.my_piecewise5(t5, t6, t5, -t6, 0)
  t9 = 0.1e1 + t8
  t11 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t13 = t9 ** (0.1e1 / 0.3e1)
  t15 = f.my_piecewise3(t9 <= f.p.zeta_threshold, t11 * f.p.zeta_threshold, t13 * t9)
  t16 = t4 * t15
  t17 = r0 ** 2
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = 0.1e1 / t19 / t17
  t24 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t25 = 0.1e1 / t24
  t27 = 4 ** (0.1e1 / 0.3e1)
  t28 = 2 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = tau0 * t29
  t32 = 0.1e1 / t19 / r0
  t35 = l0 * t29
  t38 = 0.2e1 * t30 * t32 - t35 * t32 / 0.4e1
  t41 = params.prefactor * t25 * t27 / t38
  t45 = t16 * t32 * params.prefactor
  t46 = t25 * t27
  t47 = t38 ** 2
  t48 = 0.1e1 / t47
  t53 = -0.10e2 / 0.3e1 * t30 * t21 + 0.5e1 / 0.12e2 * t35 * t21
  t55 = t46 * t48 * t53
  t60 = t16 / t19 * params.prefactor
  t62 = 0.1e1 / t47 / t38
  t63 = t53 ** 2
  t65 = t46 * t62 * t63
  t70 = 0.1e1 / t19 / t17 / r0
  t75 = 0.80e2 / 0.9e1 * t30 * t70 - 0.10e2 / 0.9e1 * t35 * t70
  t77 = t46 * t48 * t75
  t81 = t16 * t18 * params.prefactor
  t82 = t47 ** 2
  t83 = 0.1e1 / t82
  t86 = t46 * t83 * t63 * t53
  t89 = t62 * t53
  t91 = t46 * t89 * t75
  t94 = t17 ** 2
  t96 = 0.1e1 / t19 / t94
  t101 = -0.880e3 / 0.27e2 * t30 * t96 + 0.110e3 / 0.27e2 * t35 * t96
  t103 = t46 * t48 * t101
  t107 = f.my_piecewise3(t2, 0, -0.25e2 / 0.72e2 * t16 * t21 * t41 - 0.5e1 / 0.8e1 * t45 * t55 - 0.15e2 / 0.8e1 * t60 * t65 + 0.15e2 / 0.16e2 * t60 * t77 + 0.45e2 / 0.8e1 * t81 * t86 - 0.45e2 / 0.8e1 * t81 * t91 + 0.15e2 / 0.16e2 * t81 * t103)
  t128 = t63 ** 2
  t138 = t75 ** 2
  t149 = 0.1e1 / t19 / t94 / r0
  t159 = 0.25e2 / 0.27e2 * t16 * t70 * t41 + 0.25e2 / 0.18e2 * t16 * t21 * params.prefactor * t55 + 0.5e1 / 0.2e1 * t45 * t65 - 0.5e1 / 0.4e1 * t45 * t77 + 0.15e2 / 0.2e1 * t60 * t86 - 0.15e2 / 0.2e1 * t60 * t91 + 0.5e1 / 0.4e1 * t60 * t103 - 0.45e2 / 0.2e1 * t81 * t46 / t82 / t38 * t128 + 0.135e3 / 0.4e1 * t81 * t46 * t83 * t63 * t75 - 0.45e2 / 0.8e1 * t81 * t46 * t62 * t138 - 0.15e2 / 0.2e1 * t81 * t46 * t89 * t101 + 0.15e2 / 0.16e2 * t81 * t46 * t48 * (0.12320e5 / 0.81e2 * t30 * t149 - 0.1540e4 / 0.81e2 * t35 * t149)
  t160 = f.my_piecewise3(t2, 0, t159)
  v4rho4_0_ = 0.2e1 * r0 * t160 + 0.8e1 * t107

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = t17 ** (0.1e1 / 0.3e1)
  t20 = t4 ** 2
  t21 = 0.1e1 / t20
  t22 = t14 * t21
  t23 = t5 - t22
  t24 = f.my_piecewise5(t8, 0, t12, 0, t23)
  t27 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t19 * t24)
  t28 = t3 * t27
  t29 = t4 ** (0.1e1 / 0.3e1)
  t32 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t33 = 0.1e1 / t32
  t34 = params.prefactor * t33
  t35 = 4 ** (0.1e1 / 0.3e1)
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / r0
  t44 = 0.2e1 * tau0 * t39 - l0 * t39 / 0.4e1
  t47 = t34 * t35 / t44
  t50 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t51 = t50 * f.p.zeta_threshold
  t53 = f.my_piecewise3(t18, t51, t19 * t17)
  t54 = t3 * t53
  t55 = t29 ** 2
  t56 = 0.1e1 / t55
  t59 = 0.5e1 / 0.16e2 * t54 * t56 * t47
  t60 = t29 * params.prefactor
  t61 = t54 * t60
  t62 = t33 * t35
  t63 = t44 ** 2
  t64 = 0.1e1 / t63
  t65 = r0 ** 2
  t67 = 0.1e1 / t37 / t65
  t72 = -0.10e2 / 0.3e1 * tau0 * t67 + 0.5e1 / 0.12e2 * l0 * t67
  t74 = t62 * t64 * t72
  t78 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t28 * t29 * t47 - t59 + 0.15e2 / 0.16e2 * t61 * t74)
  t80 = r1 <= f.p.dens_threshold
  t81 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t82 = 0.1e1 + t81
  t83 = t82 <= f.p.zeta_threshold
  t84 = t82 ** (0.1e1 / 0.3e1)
  t86 = f.my_piecewise5(t12, 0, t8, 0, -t23)
  t89 = f.my_piecewise3(t83, 0, 0.4e1 / 0.3e1 * t84 * t86)
  t90 = t3 * t89
  t92 = r1 ** (0.1e1 / 0.3e1)
  t93 = t92 ** 2
  t95 = 0.1e1 / t93 / r1
  t100 = 0.2e1 * tau1 * t95 - l1 * t95 / 0.4e1
  t103 = t34 * t35 / t100
  t107 = f.my_piecewise3(t83, t51, t84 * t82)
  t108 = t3 * t107
  t111 = 0.5e1 / 0.16e2 * t108 * t56 * t103
  t113 = f.my_piecewise3(t80, 0, -0.15e2 / 0.16e2 * t90 * t29 * t103 - t111)
  t115 = t19 ** 2
  t116 = 0.1e1 / t115
  t117 = t24 ** 2
  t122 = t14 / t20 / t4
  t124 = -0.2e1 * t21 + 0.2e1 * t122
  t125 = f.my_piecewise5(t8, 0, t12, 0, t124)
  t129 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t116 * t117 + 0.4e1 / 0.3e1 * t19 * t125)
  t135 = t28 * t56 * t47
  t141 = 0.1e1 / t55 / t4
  t144 = 0.5e1 / 0.24e2 * t54 * t141 * t47
  t145 = t56 * params.prefactor
  t147 = t54 * t145 * t74
  t151 = t72 ** 2
  t158 = 0.1e1 / t37 / t65 / r0
  t169 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t3 * t129 * t29 * t47 - 0.5e1 / 0.8e1 * t135 + 0.15e2 / 0.8e1 * t28 * t60 * t74 + t144 + 0.5e1 / 0.8e1 * t147 - 0.15e2 / 0.8e1 * t61 * t62 / t63 / t44 * t151 + 0.15e2 / 0.16e2 * t61 * t62 * t64 * (0.80e2 / 0.9e1 * tau0 * t158 - 0.10e2 / 0.9e1 * l0 * t158))
  t170 = t84 ** 2
  t171 = 0.1e1 / t170
  t172 = t86 ** 2
  t176 = f.my_piecewise5(t12, 0, t8, 0, -t124)
  t180 = f.my_piecewise3(t83, 0, 0.4e1 / 0.9e1 * t171 * t172 + 0.4e1 / 0.3e1 * t84 * t176)
  t186 = t90 * t56 * t103
  t190 = 0.5e1 / 0.24e2 * t108 * t141 * t103
  t192 = f.my_piecewise3(t80, 0, -0.15e2 / 0.16e2 * t3 * t180 * t29 * t103 - 0.5e1 / 0.8e1 * t186 + t190)
  d11 = 0.2e1 * t78 + 0.2e1 * t113 + t4 * (t169 + t192)
  t195 = -t5 - t22
  t196 = f.my_piecewise5(t8, 0, t12, 0, t195)
  t199 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t19 * t196)
  t200 = t3 * t199
  t205 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t200 * t29 * t47 - t59)
  t207 = f.my_piecewise5(t12, 0, t8, 0, -t195)
  t210 = f.my_piecewise3(t83, 0, 0.4e1 / 0.3e1 * t84 * t207)
  t211 = t3 * t210
  t215 = t108 * t60
  t216 = t100 ** 2
  t217 = 0.1e1 / t216
  t218 = r1 ** 2
  t220 = 0.1e1 / t93 / t218
  t225 = -0.10e2 / 0.3e1 * tau1 * t220 + 0.5e1 / 0.12e2 * l1 * t220
  t227 = t62 * t217 * t225
  t231 = f.my_piecewise3(t80, 0, -0.15e2 / 0.16e2 * t211 * t29 * t103 - t111 + 0.15e2 / 0.16e2 * t215 * t227)
  t235 = 0.2e1 * t122
  t236 = f.my_piecewise5(t8, 0, t12, 0, t235)
  t240 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t116 * t196 * t24 + 0.4e1 / 0.3e1 * t19 * t236)
  t246 = t200 * t56 * t47
  t254 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t3 * t240 * t29 * t47 - 0.5e1 / 0.16e2 * t246 + 0.15e2 / 0.16e2 * t200 * t60 * t74 - 0.5e1 / 0.16e2 * t135 + t144 + 0.5e1 / 0.16e2 * t147)
  t258 = f.my_piecewise5(t12, 0, t8, 0, -t235)
  t262 = f.my_piecewise3(t83, 0, 0.4e1 / 0.9e1 * t171 * t207 * t86 + 0.4e1 / 0.3e1 * t84 * t258)
  t268 = t211 * t56 * t103
  t275 = t108 * t145 * t227
  t278 = f.my_piecewise3(t80, 0, -0.15e2 / 0.16e2 * t3 * t262 * t29 * t103 - 0.5e1 / 0.16e2 * t268 - 0.5e1 / 0.16e2 * t186 + t190 + 0.15e2 / 0.16e2 * t90 * t60 * t227 + 0.5e1 / 0.16e2 * t275)
  d12 = t78 + t113 + t205 + t231 + t4 * (t254 + t278)
  t283 = t196 ** 2
  t287 = 0.2e1 * t21 + 0.2e1 * t122
  t288 = f.my_piecewise5(t8, 0, t12, 0, t287)
  t292 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t116 * t283 + 0.4e1 / 0.3e1 * t19 * t288)
  t299 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t3 * t292 * t29 * t47 - 0.5e1 / 0.8e1 * t246 + t144)
  t300 = t207 ** 2
  t304 = f.my_piecewise5(t12, 0, t8, 0, -t287)
  t308 = f.my_piecewise3(t83, 0, 0.4e1 / 0.9e1 * t171 * t300 + 0.4e1 / 0.3e1 * t84 * t304)
  t320 = t225 ** 2
  t327 = 0.1e1 / t93 / t218 / r1
  t338 = f.my_piecewise3(t80, 0, -0.15e2 / 0.16e2 * t3 * t308 * t29 * t103 - 0.5e1 / 0.8e1 * t268 + 0.15e2 / 0.8e1 * t211 * t60 * t227 + t190 + 0.5e1 / 0.8e1 * t275 - 0.15e2 / 0.8e1 * t215 * t62 / t216 / t100 * t320 + 0.15e2 / 0.16e2 * t215 * t62 * t217 * (0.80e2 / 0.9e1 * tau1 * t327 - 0.10e2 / 0.9e1 * l1 * t327))
  d22 = 0.2e1 * t205 + 0.2e1 * t231 + t4 * (t299 + t338)
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
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = t17 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t21 = 0.1e1 / t20
  t22 = t4 ** 2
  t23 = 0.1e1 / t22
  t25 = -t14 * t23 + t5
  t26 = f.my_piecewise5(t8, 0, t12, 0, t25)
  t27 = t26 ** 2
  t31 = 0.1e1 / t22 / t4
  t34 = 0.2e1 * t14 * t31 - 0.2e1 * t23
  t35 = f.my_piecewise5(t8, 0, t12, 0, t34)
  t39 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t21 * t27 + 0.4e1 / 0.3e1 * t19 * t35)
  t40 = t3 * t39
  t41 = t4 ** (0.1e1 / 0.3e1)
  t44 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t45 = 0.1e1 / t44
  t46 = params.prefactor * t45
  t47 = 4 ** (0.1e1 / 0.3e1)
  t48 = r0 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t51 = 0.1e1 / t49 / r0
  t56 = 0.2e1 * tau0 * t51 - l0 * t51 / 0.4e1
  t59 = t46 * t47 / t56
  t64 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t19 * t26)
  t65 = t3 * t64
  t66 = t41 ** 2
  t67 = 0.1e1 / t66
  t71 = t41 * params.prefactor
  t72 = t65 * t71
  t73 = t45 * t47
  t74 = t56 ** 2
  t75 = 0.1e1 / t74
  t76 = r0 ** 2
  t78 = 0.1e1 / t49 / t76
  t83 = -0.10e2 / 0.3e1 * tau0 * t78 + 0.5e1 / 0.12e2 * l0 * t78
  t85 = t73 * t75 * t83
  t88 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t89 = t88 * f.p.zeta_threshold
  t91 = f.my_piecewise3(t18, t89, t19 * t17)
  t92 = t3 * t91
  t94 = 0.1e1 / t66 / t4
  t98 = t67 * params.prefactor
  t99 = t92 * t98
  t102 = t92 * t71
  t104 = 0.1e1 / t74 / t56
  t105 = t83 ** 2
  t107 = t73 * t104 * t105
  t112 = 0.1e1 / t49 / t76 / r0
  t117 = 0.80e2 / 0.9e1 * tau0 * t112 - 0.10e2 / 0.9e1 * l0 * t112
  t119 = t73 * t75 * t117
  t123 = f.my_piecewise3(t1, 0, -0.15e2 / 0.16e2 * t40 * t41 * t59 - 0.5e1 / 0.8e1 * t65 * t67 * t59 + 0.15e2 / 0.8e1 * t72 * t85 + 0.5e1 / 0.24e2 * t92 * t94 * t59 + 0.5e1 / 0.8e1 * t99 * t85 - 0.15e2 / 0.8e1 * t102 * t107 + 0.15e2 / 0.16e2 * t102 * t119)
  t125 = r1 <= f.p.dens_threshold
  t126 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t127 = 0.1e1 + t126
  t128 = t127 <= f.p.zeta_threshold
  t129 = t127 ** (0.1e1 / 0.3e1)
  t130 = t129 ** 2
  t131 = 0.1e1 / t130
  t133 = f.my_piecewise5(t12, 0, t8, 0, -t25)
  t134 = t133 ** 2
  t138 = f.my_piecewise5(t12, 0, t8, 0, -t34)
  t142 = f.my_piecewise3(t128, 0, 0.4e1 / 0.9e1 * t131 * t134 + 0.4e1 / 0.3e1 * t129 * t138)
  t143 = t3 * t142
  t145 = r1 ** (0.1e1 / 0.3e1)
  t146 = t145 ** 2
  t148 = 0.1e1 / t146 / r1
  t156 = t46 * t47 / (0.2e1 * tau1 * t148 - l1 * t148 / 0.4e1)
  t161 = f.my_piecewise3(t128, 0, 0.4e1 / 0.3e1 * t129 * t133)
  t162 = t3 * t161
  t167 = f.my_piecewise3(t128, t89, t129 * t127)
  t168 = t3 * t167
  t173 = f.my_piecewise3(t125, 0, -0.15e2 / 0.16e2 * t143 * t41 * t156 - 0.5e1 / 0.8e1 * t162 * t67 * t156 + 0.5e1 / 0.24e2 * t168 * t94 * t156)
  t177 = t76 ** 2
  t179 = 0.1e1 / t49 / t177
  t204 = 0.1e1 / t66 / t22
  t220 = t22 ** 2
  t224 = 0.6e1 * t31 - 0.6e1 * t14 / t220
  t225 = f.my_piecewise5(t8, 0, t12, 0, t224)
  t229 = f.my_piecewise3(t18, 0, -0.8e1 / 0.27e2 / t20 / t17 * t27 * t26 + 0.4e1 / 0.3e1 * t21 * t26 * t35 + 0.4e1 / 0.3e1 * t19 * t225)
  t238 = t74 ** 2
  t250 = 0.15e2 / 0.16e2 * t99 * t119 + 0.15e2 / 0.16e2 * t102 * t73 * t75 * (-0.880e3 / 0.27e2 * tau0 * t179 + 0.110e3 / 0.27e2 * l0 * t179) - 0.15e2 / 0.16e2 * t40 * t67 * t59 + 0.45e2 / 0.16e2 * t40 * t71 * t85 + 0.5e1 / 0.8e1 * t65 * t94 * t59 + 0.15e2 / 0.8e1 * t65 * t98 * t85 + 0.45e2 / 0.16e2 * t72 * t119 - 0.25e2 / 0.72e2 * t92 * t204 * t59 - 0.5e1 / 0.8e1 * t92 * t94 * params.prefactor * t85 - 0.15e2 / 0.16e2 * t3 * t229 * t41 * t59 - 0.45e2 / 0.8e1 * t72 * t107 - 0.15e2 / 0.8e1 * t99 * t107 + 0.45e2 / 0.8e1 * t102 * t73 / t238 * t105 * t83 - 0.45e2 / 0.8e1 * t102 * t73 * t104 * t83 * t117
  t251 = f.my_piecewise3(t1, 0, t250)
  t261 = f.my_piecewise5(t12, 0, t8, 0, -t224)
  t265 = f.my_piecewise3(t128, 0, -0.8e1 / 0.27e2 / t130 / t127 * t134 * t133 + 0.4e1 / 0.3e1 * t131 * t133 * t138 + 0.4e1 / 0.3e1 * t129 * t261)
  t280 = f.my_piecewise3(t125, 0, -0.15e2 / 0.16e2 * t3 * t265 * t41 * t156 - 0.15e2 / 0.16e2 * t143 * t67 * t156 + 0.5e1 / 0.8e1 * t162 * t94 * t156 - 0.25e2 / 0.72e2 * t168 * t204 * t156)
  d111 = 0.3e1 * t123 + 0.3e1 * t173 + t4 * (t251 + t280)

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
  t2 = jnp.pi ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = r0 + r1
  t5 = 0.1e1 / t4
  t8 = 0.2e1 * r0 * t5 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = 0.2e1 * r1 * t5 <= f.p.zeta_threshold
  t13 = -t9
  t14 = r0 - r1
  t15 = t14 * t5
  t16 = f.my_piecewise5(t8, t9, t12, t13, t15)
  t17 = 0.1e1 + t16
  t18 = t17 <= f.p.zeta_threshold
  t19 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t20 = t19 * f.p.zeta_threshold
  t21 = t17 ** (0.1e1 / 0.3e1)
  t23 = f.my_piecewise3(t18, t20, t21 * t17)
  t24 = t3 * t23
  t25 = t4 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / t26
  t28 = t27 * params.prefactor
  t29 = t24 * t28
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t32 * t33
  t35 = r0 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = 0.1e1 / t36 / r0
  t43 = 0.2e1 * tau0 * t38 - l0 * t38 / 0.4e1
  t44 = t43 ** 2
  t45 = 0.1e1 / t44
  t46 = r0 ** 2
  t49 = 0.1e1 / t36 / t46 / r0
  t54 = 0.80e2 / 0.9e1 * tau0 * t49 - 0.10e2 / 0.9e1 * l0 * t49
  t56 = t34 * t45 * t54
  t59 = t25 * params.prefactor
  t60 = t24 * t59
  t61 = t46 ** 2
  t63 = 0.1e1 / t36 / t61
  t68 = -0.880e3 / 0.27e2 * tau0 * t63 + 0.110e3 / 0.27e2 * l0 * t63
  t70 = t34 * t45 * t68
  t73 = t21 ** 2
  t74 = 0.1e1 / t73
  t75 = t4 ** 2
  t76 = 0.1e1 / t75
  t78 = -t14 * t76 + t5
  t79 = f.my_piecewise5(t8, 0, t12, 0, t78)
  t80 = t79 ** 2
  t83 = t75 * t4
  t84 = 0.1e1 / t83
  t87 = 0.2e1 * t14 * t84 - 0.2e1 * t76
  t88 = f.my_piecewise5(t8, 0, t12, 0, t87)
  t92 = f.my_piecewise3(t18, 0, 0.4e1 / 0.9e1 * t74 * t80 + 0.4e1 / 0.3e1 * t21 * t88)
  t93 = t3 * t92
  t95 = params.prefactor * t32
  t98 = t95 * t33 / t43
  t101 = t93 * t59
  t103 = 0.1e1 / t36 / t46
  t108 = -0.10e2 / 0.3e1 * tau0 * t103 + 0.5e1 / 0.12e2 * l0 * t103
  t110 = t34 * t45 * t108
  t115 = f.my_piecewise3(t18, 0, 0.4e1 / 0.3e1 * t21 * t79)
  t116 = t3 * t115
  t118 = 0.1e1 / t26 / t4
  t122 = t116 * t28
  t125 = t116 * t59
  t129 = 0.1e1 / t26 / t75
  t133 = t118 * params.prefactor
  t134 = t24 * t133
  t138 = 0.1e1 / t73 / t17
  t142 = t74 * t79
  t145 = t75 ** 2
  t146 = 0.1e1 / t145
  t149 = -0.6e1 * t14 * t146 + 0.6e1 * t84
  t150 = f.my_piecewise5(t8, 0, t12, 0, t149)
  t154 = f.my_piecewise3(t18, 0, -0.8e1 / 0.27e2 * t138 * t80 * t79 + 0.4e1 / 0.3e1 * t142 * t88 + 0.4e1 / 0.3e1 * t21 * t150)
  t155 = t3 * t154
  t160 = 0.1e1 / t44 / t43
  t161 = t108 ** 2
  t163 = t34 * t160 * t161
  t168 = t44 ** 2
  t169 = 0.1e1 / t168
  t172 = t34 * t169 * t161 * t108
  t177 = t34 * t160 * t108 * t54
  t180 = 0.15e2 / 0.16e2 * t29 * t56 + 0.15e2 / 0.16e2 * t60 * t70 - 0.15e2 / 0.16e2 * t93 * t27 * t98 + 0.45e2 / 0.16e2 * t101 * t110 + 0.5e1 / 0.8e1 * t116 * t118 * t98 + 0.15e2 / 0.8e1 * t122 * t110 + 0.45e2 / 0.16e2 * t125 * t56 - 0.25e2 / 0.72e2 * t24 * t129 * t98 - 0.5e1 / 0.8e1 * t134 * t110 - 0.15e2 / 0.16e2 * t155 * t25 * t98 - 0.45e2 / 0.8e1 * t125 * t163 - 0.15e2 / 0.8e1 * t29 * t163 + 0.45e2 / 0.8e1 * t60 * t172 - 0.45e2 / 0.8e1 * t60 * t177
  t181 = f.my_piecewise3(t1, 0, t180)
  t183 = r1 <= f.p.dens_threshold
  t184 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t185 = 0.1e1 + t184
  t186 = t185 <= f.p.zeta_threshold
  t187 = t185 ** (0.1e1 / 0.3e1)
  t188 = t187 ** 2
  t190 = 0.1e1 / t188 / t185
  t192 = f.my_piecewise5(t12, 0, t8, 0, -t78)
  t193 = t192 ** 2
  t197 = 0.1e1 / t188
  t198 = t197 * t192
  t200 = f.my_piecewise5(t12, 0, t8, 0, -t87)
  t204 = f.my_piecewise5(t12, 0, t8, 0, -t149)
  t208 = f.my_piecewise3(t186, 0, -0.8e1 / 0.27e2 * t190 * t193 * t192 + 0.4e1 / 0.3e1 * t198 * t200 + 0.4e1 / 0.3e1 * t187 * t204)
  t209 = t3 * t208
  t211 = r1 ** (0.1e1 / 0.3e1)
  t212 = t211 ** 2
  t214 = 0.1e1 / t212 / r1
  t222 = t95 * t33 / (0.2e1 * tau1 * t214 - l1 * t214 / 0.4e1)
  t230 = f.my_piecewise3(t186, 0, 0.4e1 / 0.9e1 * t197 * t193 + 0.4e1 / 0.3e1 * t187 * t200)
  t231 = t3 * t230
  t237 = f.my_piecewise3(t186, 0, 0.4e1 / 0.3e1 * t187 * t192)
  t238 = t3 * t237
  t243 = f.my_piecewise3(t186, t20, t187 * t185)
  t244 = t3 * t243
  t249 = f.my_piecewise3(t183, 0, -0.15e2 / 0.16e2 * t209 * t25 * t222 - 0.15e2 / 0.16e2 * t231 * t27 * t222 + 0.5e1 / 0.8e1 * t238 * t118 * t222 - 0.25e2 / 0.72e2 * t244 * t129 * t222)
  t268 = t161 ** 2
  t273 = t54 ** 2
  t289 = 0.15e2 / 0.4e1 * t155 * t59 * t110 - 0.5e1 / 0.4e1 * t134 * t56 - 0.45e2 / 0.4e1 * t101 * t163 - 0.15e2 / 0.2e1 * t122 * t163 + 0.5e1 / 0.2e1 * t134 * t163 + 0.45e2 / 0.2e1 * t125 * t172 + 0.15e2 / 0.2e1 * t29 * t172 - 0.45e2 / 0.2e1 * t60 * t34 / t168 / t43 * t268 - 0.45e2 / 0.8e1 * t60 * t34 * t160 * t273 + 0.45e2 / 0.8e1 * t101 * t56 - 0.5e1 / 0.2e1 * t116 * t133 * t110 + 0.25e2 / 0.18e2 * t24 * t129 * params.prefactor * t110 + 0.15e2 / 0.4e1 * t122 * t56
  t296 = 0.1e1 / t36 / t61 / r0
  t313 = 0.1e1 / t26 / t83
  t323 = t17 ** 2
  t326 = t80 ** 2
  t332 = t88 ** 2
  t341 = -0.24e2 * t146 + 0.24e2 * t14 / t145 / t4
  t342 = f.my_piecewise5(t8, 0, t12, 0, t341)
  t346 = f.my_piecewise3(t18, 0, 0.40e2 / 0.81e2 / t73 / t323 * t326 - 0.16e2 / 0.9e1 * t138 * t80 * t88 + 0.4e1 / 0.3e1 * t74 * t332 + 0.16e2 / 0.9e1 * t142 * t150 + 0.4e1 / 0.3e1 * t21 * t342)
  t365 = 0.5e1 / 0.4e1 * t29 * t70 + 0.15e2 / 0.4e1 * t125 * t70 + 0.15e2 / 0.16e2 * t60 * t34 * t45 * (0.12320e5 / 0.81e2 * tau0 * t296 - 0.1540e4 / 0.81e2 * l0 * t296) + 0.15e2 / 0.4e1 * t93 * t28 * t110 - 0.25e2 / 0.18e2 * t116 * t129 * t98 + 0.25e2 / 0.27e2 * t24 * t313 * t98 + 0.5e1 / 0.4e1 * t93 * t118 * t98 - 0.5e1 / 0.4e1 * t155 * t27 * t98 - 0.15e2 / 0.16e2 * t3 * t346 * t25 * t98 - 0.15e2 / 0.2e1 * t29 * t177 - 0.15e2 / 0.2e1 * t60 * t34 * t160 * t68 * t108 - 0.45e2 / 0.2e1 * t125 * t177 + 0.135e3 / 0.4e1 * t60 * t34 * t169 * t161 * t54
  t367 = f.my_piecewise3(t1, 0, t289 + t365)
  t368 = t185 ** 2
  t371 = t193 ** 2
  t377 = t200 ** 2
  t383 = f.my_piecewise5(t12, 0, t8, 0, -t341)
  t387 = f.my_piecewise3(t186, 0, 0.40e2 / 0.81e2 / t188 / t368 * t371 - 0.16e2 / 0.9e1 * t190 * t193 * t200 + 0.4e1 / 0.3e1 * t197 * t377 + 0.16e2 / 0.9e1 * t198 * t204 + 0.4e1 / 0.3e1 * t187 * t383)
  t405 = f.my_piecewise3(t183, 0, -0.15e2 / 0.16e2 * t3 * t387 * t25 * t222 - 0.5e1 / 0.4e1 * t209 * t27 * t222 + 0.5e1 / 0.4e1 * t231 * t118 * t222 - 0.25e2 / 0.18e2 * t238 * t129 * t222 + 0.25e2 / 0.27e2 * t244 * t313 * t222)
  d1111 = 0.4e1 * t181 + 0.4e1 * t249 + t4 * (t367 + t405)

  res = {'v4rho4': d1111}
  return res
