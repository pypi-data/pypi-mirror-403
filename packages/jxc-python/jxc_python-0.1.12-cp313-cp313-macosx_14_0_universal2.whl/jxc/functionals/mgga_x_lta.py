"""Generated from mgga_x_lta.mpl."""

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
  params_ltafrac_raw = params.ltafrac
  if isinstance(params_ltafrac_raw, (str, bytes, dict)):
    params_ltafrac = params_ltafrac_raw
  else:
    try:
      params_ltafrac_seq = list(params_ltafrac_raw)
    except TypeError:
      params_ltafrac = params_ltafrac_raw
    else:
      params_ltafrac_seq = np.asarray(params_ltafrac_seq, dtype=np.float64)
      params_ltafrac = np.concatenate((np.array([np.nan], dtype=np.float64), params_ltafrac_seq))

  lta_f = lambda x, u, t: (t / K_FACTOR_C) ** (4 * params_ltafrac / 5)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, lta_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_ltafrac_raw = params.ltafrac
  if isinstance(params_ltafrac_raw, (str, bytes, dict)):
    params_ltafrac = params_ltafrac_raw
  else:
    try:
      params_ltafrac_seq = list(params_ltafrac_raw)
    except TypeError:
      params_ltafrac = params_ltafrac_raw
    else:
      params_ltafrac_seq = np.asarray(params_ltafrac_seq, dtype=np.float64)
      params_ltafrac = np.concatenate((np.array([np.nan], dtype=np.float64), params_ltafrac_seq))

  lta_f = lambda x, u, t: (t / K_FACTOR_C) ** (4 * params_ltafrac / 5)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, lta_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  params_ltafrac_raw = params.ltafrac
  if isinstance(params_ltafrac_raw, (str, bytes, dict)):
    params_ltafrac = params_ltafrac_raw
  else:
    try:
      params_ltafrac_seq = list(params_ltafrac_raw)
    except TypeError:
      params_ltafrac = params_ltafrac_raw
    else:
      params_ltafrac_seq = np.asarray(params_ltafrac_seq, dtype=np.float64)
      params_ltafrac = np.concatenate((np.array([np.nan], dtype=np.float64), params_ltafrac_seq))

  lta_f = lambda x, u, t: (t / K_FACTOR_C) ** (4 * params_ltafrac / 5)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, lta_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = r0 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t33 = 6 ** (0.1e1 / 0.3e1)
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = t33 / t36
  t41 = 0.4e1 / 0.5e1 * params.ltafrac
  t42 = (0.5e1 / 0.9e1 * tau0 / t29 / r0 * t38) ** t41
  t46 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t25 * t26 * t42)
  t47 = r1 <= f.p.dens_threshold
  t48 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t49 = 0.1e1 + t48
  t50 = t49 <= f.p.zeta_threshold
  t51 = t49 ** (0.1e1 / 0.3e1)
  t53 = f.my_piecewise3(t50, t22, t51 * t49)
  t55 = r1 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t62 = (0.5e1 / 0.9e1 * tau1 / t56 / r1 * t38) ** t41
  t66 = f.my_piecewise3(t47, 0, -0.3e1 / 0.8e1 * t5 * t53 * t26 * t62)
  t67 = t6 ** 2
  t69 = t16 / t67
  t70 = t7 - t69
  t71 = f.my_piecewise5(t10, 0, t14, 0, t70)
  t74 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t71)
  t79 = t26 ** 2
  t80 = 0.1e1 / t79
  t84 = t5 * t25 * t80 * t42 / 0.8e1
  t85 = t5 * t25
  t86 = t26 * t42
  t93 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t74 * t26 * t42 - t84 + t85 * t86 * params.ltafrac / r0 / 0.2e1)
  t95 = f.my_piecewise5(t14, 0, t10, 0, -t70)
  t98 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t95)
  t106 = t5 * t53 * t80 * t62 / 0.8e1
  t108 = f.my_piecewise3(t47, 0, -0.3e1 / 0.8e1 * t5 * t98 * t26 * t62 - t106)
  vrho_0_ = t46 + t66 + t6 * (t93 + t108)
  t111 = -t7 - t69
  t112 = f.my_piecewise5(t10, 0, t14, 0, t111)
  t115 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t112)
  t121 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t115 * t26 * t42 - t84)
  t123 = f.my_piecewise5(t14, 0, t10, 0, -t111)
  t126 = f.my_piecewise3(t50, 0, 0.4e1 / 0.3e1 * t51 * t123)
  t131 = t5 * t53
  t132 = t26 * t62
  t139 = f.my_piecewise3(t47, 0, -0.3e1 / 0.8e1 * t5 * t126 * t26 * t62 - t106 + t131 * t132 * params.ltafrac / r1 / 0.2e1)
  vrho_1_ = t46 + t66 + t6 * (t121 + t139)
  vsigma_0_ = 0.0e0
  vsigma_1_ = 0.0e0
  vsigma_2_ = 0.0e0
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t147 = f.my_piecewise3(t1, 0, -0.3e1 / 0.10e2 * t85 * t86 * params.ltafrac / tau0)
  vtau_0_ = t6 * t147
  t153 = f.my_piecewise3(t47, 0, -0.3e1 / 0.10e2 * t131 * t132 * params.ltafrac / tau1)
  vtau_1_ = t6 * t153
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
  params_ltafrac_raw = params.ltafrac
  if isinstance(params_ltafrac_raw, (str, bytes, dict)):
    params_ltafrac = params_ltafrac_raw
  else:
    try:
      params_ltafrac_seq = list(params_ltafrac_raw)
    except TypeError:
      params_ltafrac = params_ltafrac_raw
    else:
      params_ltafrac_seq = np.asarray(params_ltafrac_seq, dtype=np.float64)
      params_ltafrac = np.concatenate((np.array([np.nan], dtype=np.float64), params_ltafrac_seq))

  lta_f = lambda x, u, t: (t / K_FACTOR_C) ** (4 * params_ltafrac / 5)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange(f, params, lta_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = 2 ** (0.1e1 / 0.3e1)
  t21 = t20 ** 2
  t23 = t18 ** 2
  t26 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t36 = (0.5e1 / 0.9e1 * tau0 * t21 / t23 / r0 * t26 / t30) ** (0.4e1 / 0.5e1 * params.ltafrac)
  t40 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t36)
  t41 = 0.1e1 / t23
  t46 = t6 * t17
  t52 = f.my_piecewise3(t2, 0, -t6 * t17 * t41 * t36 / 0.8e1 + t46 * t41 * t36 * params.ltafrac / 0.2e1)
  vrho_0_ = 0.2e1 * r0 * t52 + 0.2e1 * t40
  vsigma_0_ = 0.0e0
  vlapl_0_ = 0.0e0
  t61 = f.my_piecewise3(t2, 0, -0.3e1 / 0.10e2 * t46 * t18 * t36 * params.ltafrac / tau0)
  vtau_0_ = 0.2e1 * r0 * t61
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
  t20 = 0.1e1 / t19
  t22 = 2 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t26 = 0.1e1 / t19 / r0
  t27 = 6 ** (0.1e1 / 0.3e1)
  t29 = jnp.pi ** 2
  t30 = t29 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t37 = (0.5e1 / 0.9e1 * tau0 * t23 * t26 * t27 / t31) ** (0.4e1 / 0.5e1 * params.ltafrac)
  t41 = t6 * t17
  t47 = f.my_piecewise3(t2, 0, -t6 * t17 * t20 * t37 / 0.8e1 + t41 * t20 * t37 * params.ltafrac / 0.2e1)
  t53 = t26 * t37
  t57 = params.ltafrac ** 2
  t62 = f.my_piecewise3(t2, 0, t6 * t17 * t26 * t37 / 0.12e2 - t41 * t53 * params.ltafrac / 0.6e1 - 0.2e1 / 0.3e1 * t41 * t53 * t57)
  v2rho2_0_ = 0.2e1 * r0 * t62 + 0.4e1 * t47
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
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = 0.1e1 / t19 / r0
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t26 = 6 ** (0.1e1 / 0.3e1)
  t28 = jnp.pi ** 2
  t29 = t28 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t36 = (0.5e1 / 0.9e1 * tau0 * t24 * t21 * t26 / t30) ** (0.4e1 / 0.5e1 * params.ltafrac)
  t40 = t6 * t17
  t41 = t21 * t36
  t45 = params.ltafrac ** 2
  t50 = f.my_piecewise3(t2, 0, t6 * t17 * t21 * t36 / 0.12e2 - t40 * t41 * params.ltafrac / 0.6e1 - 0.2e1 / 0.3e1 * t40 * t41 * t45)
  t52 = r0 ** 2
  t54 = 0.1e1 / t19 / t52
  t59 = t54 * t36
  t71 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t54 * t36 + t40 * t59 * params.ltafrac / 0.6e1 + 0.4e1 / 0.3e1 * t40 * t59 * t45 + 0.8e1 / 0.9e1 * t40 * t59 * t45 * params.ltafrac)
  v3rho3_0_ = 0.2e1 * r0 * t71 + 0.6e1 * t50

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
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t24 ** 2
  t29 = 6 ** (0.1e1 / 0.3e1)
  t31 = jnp.pi ** 2
  t32 = t31 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t39 = (0.5e1 / 0.9e1 * tau0 * t25 / t20 / r0 * t29 / t33) ** (0.4e1 / 0.5e1 * params.ltafrac)
  t43 = t6 * t17
  t44 = t22 * t39
  t48 = params.ltafrac ** 2
  t52 = t48 * params.ltafrac
  t57 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t39 + t43 * t44 * params.ltafrac / 0.6e1 + 0.4e1 / 0.3e1 * t43 * t44 * t48 + 0.8e1 / 0.9e1 * t43 * t44 * t52)
  t61 = 0.1e1 / t20 / t18 / r0
  t66 = t61 * t39
  t76 = t48 ** 2
  t81 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t61 * t39 - 0.7e1 / 0.27e2 * t43 * t66 * params.ltafrac - 0.34e2 / 0.9e1 * t43 * t66 * t48 - 0.112e3 / 0.27e2 * t43 * t66 * t52 - 0.32e2 / 0.27e2 * t43 * t66 * t76)
  v4rho4_0_ = 0.2e1 * r0 * t81 + 0.8e1 * t57

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
  t32 = r0 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t37 = 6 ** (0.1e1 / 0.3e1)
  t38 = jnp.pi ** 2
  t39 = t38 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = t37 / t40
  t45 = 0.4e1 / 0.5e1 * params.ltafrac
  t46 = (0.5e1 / 0.9e1 * tau0 / t33 / r0 * t42) ** t45
  t50 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t51 = t50 * f.p.zeta_threshold
  t53 = f.my_piecewise3(t20, t51, t21 * t19)
  t54 = t30 ** 2
  t55 = 0.1e1 / t54
  t59 = t5 * t53 * t55 * t46 / 0.8e1
  t60 = t5 * t53
  t61 = t30 * t46
  t63 = params.ltafrac / r0
  t64 = t61 * t63
  t68 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t29 * t30 * t46 - t59 + t60 * t64 / 0.2e1)
  t70 = r1 <= f.p.dens_threshold
  t71 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t72 = 0.1e1 + t71
  t73 = t72 <= f.p.zeta_threshold
  t74 = t72 ** (0.1e1 / 0.3e1)
  t76 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t79 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t74 * t76)
  t81 = r1 ** (0.1e1 / 0.3e1)
  t82 = t81 ** 2
  t88 = (0.5e1 / 0.9e1 * tau1 / t82 / r1 * t42) ** t45
  t93 = f.my_piecewise3(t73, t51, t74 * t72)
  t97 = t5 * t93 * t55 * t88 / 0.8e1
  t99 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t79 * t30 * t88 - t97)
  t101 = t21 ** 2
  t102 = 0.1e1 / t101
  t103 = t26 ** 2
  t108 = t16 / t22 / t6
  t110 = -0.2e1 * t23 + 0.2e1 * t108
  t111 = f.my_piecewise5(t10, 0, t14, 0, t110)
  t115 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t102 * t103 + 0.4e1 / 0.3e1 * t21 * t111)
  t122 = t5 * t29 * t55 * t46
  t127 = 0.1e1 / t54 / t6
  t131 = t5 * t53 * t127 * t46 / 0.12e2
  t134 = t60 * t55 * t46 * t63
  t136 = params.ltafrac ** 2
  t137 = r0 ** 2
  t138 = 0.1e1 / t137
  t148 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t115 * t30 * t46 - t122 / 0.4e1 + t5 * t29 * t64 + t131 + t134 / 0.3e1 - 0.2e1 / 0.3e1 * t60 * t61 * t136 * t138 - t60 * t61 * params.ltafrac * t138 / 0.2e1)
  t149 = t74 ** 2
  t150 = 0.1e1 / t149
  t151 = t76 ** 2
  t155 = f.my_piecewise5(t14, 0, t10, 0, -t110)
  t159 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t150 * t151 + 0.4e1 / 0.3e1 * t74 * t155)
  t166 = t5 * t79 * t55 * t88
  t171 = t5 * t93 * t127 * t88 / 0.12e2
  t173 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t159 * t30 * t88 - t166 / 0.4e1 + t171)
  d11 = 0.2e1 * t68 + 0.2e1 * t99 + t6 * (t148 + t173)
  t176 = -t7 - t24
  t177 = f.my_piecewise5(t10, 0, t14, 0, t176)
  t180 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t177)
  t186 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t180 * t30 * t46 - t59)
  t188 = f.my_piecewise5(t14, 0, t10, 0, -t176)
  t191 = f.my_piecewise3(t73, 0, 0.4e1 / 0.3e1 * t74 * t188)
  t196 = t5 * t93
  t197 = t30 * t88
  t199 = params.ltafrac / r1
  t200 = t197 * t199
  t204 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t191 * t30 * t88 - t97 + t196 * t200 / 0.2e1)
  t208 = 0.2e1 * t108
  t209 = f.my_piecewise5(t10, 0, t14, 0, t208)
  t213 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t102 * t177 * t26 + 0.4e1 / 0.3e1 * t21 * t209)
  t220 = t5 * t180 * t55 * t46
  t228 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t213 * t30 * t46 - t220 / 0.8e1 + t5 * t180 * t64 / 0.2e1 - t122 / 0.8e1 + t131 + t134 / 0.6e1)
  t232 = f.my_piecewise5(t14, 0, t10, 0, -t208)
  t236 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t150 * t188 * t76 + 0.4e1 / 0.3e1 * t74 * t232)
  t243 = t5 * t191 * t55 * t88
  t251 = t196 * t55 * t88 * t199
  t254 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t236 * t30 * t88 - t243 / 0.8e1 - t166 / 0.8e1 + t171 + t5 * t79 * t200 / 0.2e1 + t251 / 0.6e1)
  d12 = t68 + t99 + t186 + t204 + t6 * (t228 + t254)
  t259 = t177 ** 2
  t263 = 0.2e1 * t23 + 0.2e1 * t108
  t264 = f.my_piecewise5(t10, 0, t14, 0, t263)
  t268 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t102 * t259 + 0.4e1 / 0.3e1 * t21 * t264)
  t275 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t268 * t30 * t46 - t220 / 0.4e1 + t131)
  t276 = t188 ** 2
  t280 = f.my_piecewise5(t14, 0, t10, 0, -t263)
  t284 = f.my_piecewise3(t73, 0, 0.4e1 / 0.9e1 * t150 * t276 + 0.4e1 / 0.3e1 * t74 * t280)
  t293 = r1 ** 2
  t294 = 0.1e1 / t293
  t304 = f.my_piecewise3(t70, 0, -0.3e1 / 0.8e1 * t5 * t284 * t30 * t88 - t243 / 0.4e1 + t5 * t191 * t200 + t171 + t251 / 0.3e1 - 0.2e1 / 0.3e1 * t196 * t197 * t136 * t294 - t196 * t197 * params.ltafrac * t294 / 0.2e1)
  d22 = 0.2e1 * t186 + 0.2e1 * t204 + t6 * (t275 + t304)
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
  t44 = r0 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t49 = 6 ** (0.1e1 / 0.3e1)
  t50 = jnp.pi ** 2
  t51 = t50 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t54 = t49 / t52
  t57 = 0.4e1 / 0.5e1 * params.ltafrac
  t58 = (0.5e1 / 0.9e1 * tau0 / t45 / r0 * t54) ** t57
  t64 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t65 = t42 ** 2
  t66 = 0.1e1 / t65
  t71 = t5 * t64
  t72 = t42 * t58
  t74 = params.ltafrac / r0
  t75 = t72 * t74
  t77 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t78 = t77 * f.p.zeta_threshold
  t80 = f.my_piecewise3(t20, t78, t21 * t19)
  t82 = 0.1e1 / t65 / t6
  t87 = t5 * t80
  t88 = t66 * t58
  t89 = t88 * t74
  t92 = params.ltafrac ** 2
  t93 = r0 ** 2
  t94 = 0.1e1 / t93
  t95 = t92 * t94
  t96 = t72 * t95
  t99 = params.ltafrac * t94
  t100 = t72 * t99
  t104 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t41 * t42 * t58 - t5 * t64 * t66 * t58 / 0.4e1 + t71 * t75 + t5 * t80 * t82 * t58 / 0.12e2 + t87 * t89 / 0.3e1 - 0.2e1 / 0.3e1 * t87 * t96 - t87 * t100 / 0.2e1)
  t106 = r1 <= f.p.dens_threshold
  t107 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t108 = 0.1e1 + t107
  t109 = t108 <= f.p.zeta_threshold
  t110 = t108 ** (0.1e1 / 0.3e1)
  t111 = t110 ** 2
  t112 = 0.1e1 / t111
  t114 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t115 = t114 ** 2
  t119 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t123 = f.my_piecewise3(t109, 0, 0.4e1 / 0.9e1 * t112 * t115 + 0.4e1 / 0.3e1 * t110 * t119)
  t125 = r1 ** (0.1e1 / 0.3e1)
  t126 = t125 ** 2
  t132 = (0.5e1 / 0.9e1 * tau1 / t126 / r1 * t54) ** t57
  t138 = f.my_piecewise3(t109, 0, 0.4e1 / 0.3e1 * t110 * t114)
  t144 = f.my_piecewise3(t109, t78, t110 * t108)
  t150 = f.my_piecewise3(t106, 0, -0.3e1 / 0.8e1 * t5 * t123 * t42 * t132 - t5 * t138 * t66 * t132 / 0.4e1 + t5 * t144 * t82 * t132 / 0.12e2)
  t154 = 0.1e1 / t93 / r0
  t180 = t24 ** 2
  t184 = 0.6e1 * t33 - 0.6e1 * t16 / t180
  t185 = f.my_piecewise5(t10, 0, t14, 0, t184)
  t189 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t185)
  t215 = 0.1e1 / t65 / t24
  t220 = 0.8e1 / 0.9e1 * t87 * t72 * t92 * params.ltafrac * t154 + 0.3e1 / 0.2e1 * t5 * t41 * t75 + t71 * t89 - 0.2e1 * t71 * t96 - t87 * t82 * t58 * t74 / 0.3e1 - 0.2e1 / 0.3e1 * t87 * t88 * t95 - 0.3e1 / 0.8e1 * t5 * t189 * t42 * t58 - 0.3e1 / 0.2e1 * t71 * t100 - t87 * t88 * t99 / 0.2e1 + 0.2e1 * t87 * t72 * t92 * t154 + t87 * t72 * params.ltafrac * t154 - 0.3e1 / 0.8e1 * t5 * t41 * t66 * t58 + t5 * t64 * t82 * t58 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t80 * t215 * t58
  t221 = f.my_piecewise3(t1, 0, t220)
  t231 = f.my_piecewise5(t14, 0, t10, 0, -t184)
  t235 = f.my_piecewise3(t109, 0, -0.8e1 / 0.27e2 / t111 / t108 * t115 * t114 + 0.4e1 / 0.3e1 * t112 * t114 * t119 + 0.4e1 / 0.3e1 * t110 * t231)
  t253 = f.my_piecewise3(t106, 0, -0.3e1 / 0.8e1 * t5 * t235 * t42 * t132 - 0.3e1 / 0.8e1 * t5 * t123 * t66 * t132 + t5 * t138 * t82 * t132 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t144 * t215 * t132)
  d111 = 0.3e1 * t104 + 0.3e1 * t150 + t6 * (t221 + t253)

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
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t22 = t21 * f.p.zeta_threshold
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t20, t22, t23 * t19)
  t26 = t5 * t25
  t27 = t6 ** (0.1e1 / 0.3e1)
  t28 = r0 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t33 = 6 ** (0.1e1 / 0.3e1)
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = t33 / t36
  t41 = 0.4e1 / 0.5e1 * params.ltafrac
  t42 = (0.5e1 / 0.9e1 * tau0 / t29 / r0 * t38) ** t41
  t43 = t27 * t42
  t44 = params.ltafrac ** 2
  t45 = t44 * params.ltafrac
  t46 = r0 ** 2
  t48 = 0.1e1 / t46 / r0
  t49 = t45 * t48
  t50 = t43 * t49
  t53 = t23 ** 2
  t54 = 0.1e1 / t53
  t55 = t6 ** 2
  t56 = 0.1e1 / t55
  t58 = -t16 * t56 + t7
  t59 = f.my_piecewise5(t10, 0, t14, 0, t58)
  t60 = t59 ** 2
  t63 = t55 * t6
  t64 = 0.1e1 / t63
  t67 = 0.2e1 * t16 * t64 - 0.2e1 * t56
  t68 = f.my_piecewise5(t10, 0, t14, 0, t67)
  t72 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t54 * t60 + 0.4e1 / 0.3e1 * t23 * t68)
  t73 = t5 * t72
  t75 = params.ltafrac / r0
  t76 = t43 * t75
  t81 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t59)
  t82 = t5 * t81
  t83 = t27 ** 2
  t84 = 0.1e1 / t83
  t85 = t84 * t42
  t86 = t85 * t75
  t88 = 0.1e1 / t46
  t89 = t44 * t88
  t90 = t43 * t89
  t94 = 0.1e1 / t83 / t6
  t95 = t94 * t42
  t96 = t95 * t75
  t99 = t85 * t89
  t103 = 0.1e1 / t53 / t19
  t107 = t54 * t59
  t110 = t55 ** 2
  t111 = 0.1e1 / t110
  t114 = -0.6e1 * t16 * t111 + 0.6e1 * t64
  t115 = f.my_piecewise5(t10, 0, t14, 0, t114)
  t119 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t103 * t60 * t59 + 0.4e1 / 0.3e1 * t107 * t68 + 0.4e1 / 0.3e1 * t23 * t115)
  t124 = params.ltafrac * t48
  t125 = t43 * t124
  t127 = params.ltafrac * t88
  t128 = t43 * t127
  t131 = t85 * t127
  t134 = t44 * t48
  t135 = t43 * t134
  t147 = 0.1e1 / t83 / t55
  t152 = 0.8e1 / 0.9e1 * t26 * t50 + 0.3e1 / 0.2e1 * t73 * t76 + t82 * t86 - 0.2e1 * t82 * t90 - t26 * t96 / 0.3e1 - 0.2e1 / 0.3e1 * t26 * t99 - 0.3e1 / 0.8e1 * t5 * t119 * t27 * t42 + t26 * t125 - 0.3e1 / 0.2e1 * t82 * t128 - t26 * t131 / 0.2e1 + 0.2e1 * t26 * t135 - 0.3e1 / 0.8e1 * t5 * t72 * t84 * t42 + t5 * t81 * t94 * t42 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t25 * t147 * t42
  t153 = f.my_piecewise3(t1, 0, t152)
  t155 = r1 <= f.p.dens_threshold
  t156 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t157 = 0.1e1 + t156
  t158 = t157 <= f.p.zeta_threshold
  t159 = t157 ** (0.1e1 / 0.3e1)
  t160 = t159 ** 2
  t162 = 0.1e1 / t160 / t157
  t164 = f.my_piecewise5(t14, 0, t10, 0, -t58)
  t165 = t164 ** 2
  t169 = 0.1e1 / t160
  t170 = t169 * t164
  t172 = f.my_piecewise5(t14, 0, t10, 0, -t67)
  t176 = f.my_piecewise5(t14, 0, t10, 0, -t114)
  t180 = f.my_piecewise3(t158, 0, -0.8e1 / 0.27e2 * t162 * t165 * t164 + 0.4e1 / 0.3e1 * t170 * t172 + 0.4e1 / 0.3e1 * t159 * t176)
  t182 = r1 ** (0.1e1 / 0.3e1)
  t183 = t182 ** 2
  t189 = (0.5e1 / 0.9e1 * tau1 / t183 / r1 * t38) ** t41
  t198 = f.my_piecewise3(t158, 0, 0.4e1 / 0.9e1 * t169 * t165 + 0.4e1 / 0.3e1 * t159 * t172)
  t205 = f.my_piecewise3(t158, 0, 0.4e1 / 0.3e1 * t159 * t164)
  t211 = f.my_piecewise3(t158, t22, t159 * t157)
  t217 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t180 * t27 * t189 - 0.3e1 / 0.8e1 * t5 * t198 * t84 * t189 + t5 * t205 * t94 * t189 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t211 * t147 * t189)
  t219 = t19 ** 2
  t222 = t60 ** 2
  t228 = t68 ** 2
  t237 = -0.24e2 * t111 + 0.24e2 * t16 / t110 / t6
  t238 = f.my_piecewise5(t10, 0, t14, 0, t237)
  t242 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t53 / t219 * t222 - 0.16e2 / 0.9e1 * t103 * t60 * t68 + 0.4e1 / 0.3e1 * t54 * t228 + 0.16e2 / 0.9e1 * t107 * t115 + 0.4e1 / 0.3e1 * t23 * t238)
  t260 = 0.1e1 / t83 / t63
  t274 = t46 ** 2
  t275 = 0.1e1 / t274
  t289 = -0.3e1 / 0.8e1 * t5 * t242 * t27 * t42 - t5 * t119 * t84 * t42 / 0.2e1 + t5 * t72 * t94 * t42 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t81 * t147 * t42 + 0.10e2 / 0.27e2 * t5 * t25 * t260 * t42 + 0.2e1 / 0.3e1 * t26 * t95 * t127 + 0.8e1 / 0.3e1 * t26 * t85 * t134 + 0.4e1 / 0.3e1 * t26 * t85 * t124 - 0.3e1 * t26 * t43 * params.ltafrac * t275 + 0.32e2 / 0.27e2 * t26 * t85 * t49 - 0.16e2 / 0.3e1 * t26 * t43 * t45 * t275 + 0.2e1 * t73 * t86
  t304 = t44 ** 2
  t325 = -0.3e1 * t73 * t128 - 0.4e1 / 0.3e1 * t82 * t96 - 0.2e1 * t82 * t131 + 0.4e1 * t82 * t125 - 0.22e2 / 0.3e1 * t26 * t43 * t44 * t275 + 0.32e2 / 0.9e1 * t82 * t50 - 0.32e2 / 0.27e2 * t26 * t43 * t304 * t275 + 0.2e1 * t5 * t119 * t76 - 0.4e1 * t73 * t90 - 0.8e1 / 0.3e1 * t82 * t99 + 0.8e1 / 0.9e1 * t26 * t95 * t89 + 0.8e1 * t82 * t135 + 0.20e2 / 0.27e2 * t26 * t147 * t42 * t75
  t327 = f.my_piecewise3(t1, 0, t289 + t325)
  t328 = t157 ** 2
  t331 = t165 ** 2
  t337 = t172 ** 2
  t343 = f.my_piecewise5(t14, 0, t10, 0, -t237)
  t347 = f.my_piecewise3(t158, 0, 0.40e2 / 0.81e2 / t160 / t328 * t331 - 0.16e2 / 0.9e1 * t162 * t165 * t172 + 0.4e1 / 0.3e1 * t169 * t337 + 0.16e2 / 0.9e1 * t170 * t176 + 0.4e1 / 0.3e1 * t159 * t343)
  t369 = f.my_piecewise3(t155, 0, -0.3e1 / 0.8e1 * t5 * t347 * t27 * t189 - t5 * t180 * t84 * t189 / 0.2e1 + t5 * t198 * t94 * t189 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t205 * t147 * t189 + 0.10e2 / 0.27e2 * t5 * t211 * t260 * t189)
  d1111 = 0.4e1 * t153 + 0.4e1 * t217 + t6 * (t327 + t369)

  res = {'v4rho4': d1111}
  return res
