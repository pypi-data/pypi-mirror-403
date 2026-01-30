"""Generated from lda_x_1d_exponential.mpl."""

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  x1d_inter = lambda x: xc_E1_scaled(x ** 2)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  x1d_inter = lambda x: xc_E1_scaled(x ** 2)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  x1d_inter = lambda x: xc_E1_scaled(x ** 2)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t8 = r0 <= f.p.dens_threshold or t7
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = 0.1e1 - t5 <= f.p.zeta_threshold
  t12 = -t9
  t13 = f.my_piecewise5(t7, t9, t11, t12, t5)
  t14 = 0.1e1 + t13
  t17 = 3 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t19 = 0.1e1 / jnp.pi
  t20 = t19 ** (0.1e1 / 0.3e1)
  t23 = 4 ** (0.1e1 / 0.3e1)
  t24 = t3 ** (0.1e1 / 0.3e1)
  t26 = t18 / t20 * t23 * t24
  t28 = t14 * jnp.pi * params.beta * t26 / 0.6e1
  t29 = int1(t28)
  t31 = int2(t28)
  t33 = 0.1e1 / params.beta
  t34 = t31 * t19 * t33
  t35 = t17 * t20
  t36 = t23 ** 2
  t39 = t35 * t36 / t24
  t46 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t14 * t29 - t34 * t39 / 0.2e1) * t19 * t33)
  t48 = r1 <= f.p.dens_threshold or t11
  t49 = f.my_piecewise5(t11, t9, t7, t12, -t5)
  t50 = 0.1e1 + t49
  t54 = t50 * jnp.pi * params.beta * t26 / 0.6e1
  t55 = int1(t54)
  t57 = int2(t54)
  t59 = t57 * t19 * t33
  t66 = f.my_piecewise3(t48, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t50 * t55 - t59 * t39 / 0.2e1) * t19 * t33)
  t67 = t3 ** 2
  t69 = t2 / t67
  t70 = t4 - t69
  t71 = f.my_piecewise5(t7, 0, t11, 0, t70)
  t76 = t35 * t36 / t24 / t3
  t78 = t34 * t76 / 0.6e1
  t83 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t71 * t29 + t78) * t19 * t33)
  t85 = f.my_piecewise5(t11, 0, t7, 0, -t70)
  t88 = t59 * t76 / 0.6e1
  t93 = f.my_piecewise3(t48, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t85 * t55 + t88) * t19 * t33)
  vrho_0_ = t46 + t66 + t3 * (t83 + t93)
  t96 = -t4 - t69
  t97 = f.my_piecewise5(t7, 0, t11, 0, t96)
  t103 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t97 * t29 + t78) * t19 * t33)
  t105 = f.my_piecewise5(t11, 0, t7, 0, -t96)
  t111 = f.my_piecewise3(t48, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t105 * t55 + t88) * t19 * t33)
  vrho_1_ = t46 + t66 + t3 * (t103 + t111)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  x1d_inter = lambda x: xc_E1_scaled(x ** 2)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = f.p.zeta_threshold - 0.1e1
  t7 = f.my_piecewise5(t3, t5, t3, -t5, 0)
  t8 = 0.1e1 + t7
  t11 = 3 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t13 = 0.1e1 / jnp.pi
  t14 = t13 ** (0.1e1 / 0.3e1)
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t22 = t8 * jnp.pi * params.beta * t12 / t14 * t17 * t18 / 0.6e1
  t23 = int1(t22)
  t25 = int2(t22)
  t27 = 0.1e1 / params.beta
  t29 = t11 * t14
  t30 = t17 ** 2
  t40 = f.my_piecewise3(t4, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t8 * t23 - t25 * t13 * t27 * t29 * t30 / t18 / 0.2e1) * t13 * t27)
  t41 = jnp.pi ** 2
  t44 = params.beta ** 2
  t53 = f.my_piecewise3(t4, 0, -0.41666666666666666666666666666666666666666666666667e-1 * t25 / t41 / t44 * t29 * t30 / t18 / r0)
  vrho_0_ = 0.2e1 * r0 * t53 + 0.2e1 * t40
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = f.p.zeta_threshold - 0.1e1
  t7 = f.my_piecewise5(t3, t5, t3, -t5, 0)
  t8 = 0.1e1 + t7
  t11 = 3 ** (0.1e1 / 0.3e1)
  t12 = t11 ** 2
  t14 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t14
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t23 = int2(t8 * jnp.pi * params.beta * t12 * t15 * t17 * t18 / 0.6e1)
  t24 = jnp.pi ** 2
  t27 = params.beta ** 2
  t29 = t23 / t24 / t27
  t30 = t11 * t14
  t31 = t17 ** 2
  t38 = f.my_piecewise3(t4, 0, -0.41666666666666666666666666666666666666666666666667e-1 * t29 * t30 * t31 / t18 / r0)
  t40 = t8 ** 2
  t43 = t18 ** 2
  t49 = t14 ** 2
  t56 = xc_E1_scaled(t40 * t24 * t27 * t11 / t49 * t31 * t43 / 0.12e2)
  t60 = r0 ** 2
  t68 = f.my_piecewise3(t4, 0, -0.46296296296296296296296296296296296296296296296297e-2 * t40 * t12 * t15 * t17 / t43 / r0 * t56 + 0.55555555555555555555555555555555555555555555555556e-1 * t29 * t30 * t31 / t18 / t60)
  v2rho2_0_ = 0.2e1 * r0 * t68 + 0.4e1 * t38
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = f.p.zeta_threshold - 0.1e1
  t7 = f.my_piecewise5(t3, t5, t3, -t5, 0)
  t8 = 0.1e1 + t7
  t9 = t8 ** 2
  t10 = 3 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t14 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t14
  t16 = t9 * t11 * t15
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t23 = jnp.pi ** 2
  t25 = params.beta ** 2
  t27 = t14 ** 2
  t30 = t17 ** 2
  t35 = xc_E1_scaled(t9 * t23 * t25 * t10 / t27 * t30 * t19 / 0.12e2)
  t46 = int2(t8 * jnp.pi * params.beta * t11 * t15 * t17 * t18 / 0.6e1)
  t47 = 0.1e1 / t23
  t49 = 0.1e1 / t25
  t50 = t46 * t47 * t49
  t51 = t10 * t14
  t52 = r0 ** 2
  t60 = f.my_piecewise3(t4, 0, -0.46296296296296296296296296296296296296296296296297e-2 * t16 * t17 / t19 / r0 * t35 + 0.55555555555555555555555555555555555555555555555556e-1 * t50 * t51 * t30 / t18 / t52)
  t68 = t9 ** 2
  t93 = f.my_piecewise3(t4, 0, 0.13888888888888888888888888888888888888888888888889e-1 * t16 * t17 / t19 / t52 * t35 - 0.30864197530864197530864197530864197530864197530865e-2 * t68 * t23 * jnp.pi / t52 * (t35 - 0.1e1 / t9 * t47 * t49 * t11 * t27 * t17 / t19) * t25 - 0.12962962962962962962962962962962962962962962962963e0 * t50 * t51 * t30 / t18 / t52 / r0)
  v3rho3_0_ = 0.2e1 * r0 * t93 + 0.6e1 * t60

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = r0 / 0.2e1 <= f.p.dens_threshold or t3
  t5 = f.p.zeta_threshold - 0.1e1
  t7 = f.my_piecewise5(t3, t5, t3, -t5, 0)
  t8 = 0.1e1 + t7
  t9 = t8 ** 2
  t10 = 3 ** (0.1e1 / 0.3e1)
  t11 = t10 ** 2
  t14 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t14
  t16 = t9 * t11 * t15
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t24 = jnp.pi ** 2
  t26 = params.beta ** 2
  t28 = t14 ** 2
  t30 = t10 / t28
  t31 = t17 ** 2
  t36 = xc_E1_scaled(t9 * t24 * t26 * t30 * t31 * t20 / 0.12e2)
  t40 = t9 ** 2
  t42 = t40 * t24 * jnp.pi
  t43 = 0.1e1 / t18
  t45 = 0.1e1 / t24
  t47 = 0.1e1 / t26
  t48 = 0.1e1 / t9 * t45 * t47
  t49 = t11 * t28
  t54 = t36 - t48 * t49 * t17 / t20
  t66 = int2(t8 * jnp.pi * params.beta * t11 * t15 * t17 * t19 / 0.6e1)
  t68 = t66 * t45 * t47
  t69 = t10 * t14
  t70 = t18 * r0
  t78 = f.my_piecewise3(t4, 0, 0.13888888888888888888888888888888888888888888888889e-1 * t16 * t17 / t20 / t18 * t36 - 0.30864197530864197530864197530864197530864197530865e-2 * t42 * t43 * t54 * t26 - 0.12962962962962962962962962962962962962962962962963e0 * t68 * t69 * t31 / t19 / t70)
  t110 = t18 ** 2
  t118 = f.my_piecewise3(t4, 0, -0.51440329218106995884773662551440329218106995884774e-1 * t16 * t17 / t20 / t70 * t36 + 0.15432098765432098765432098765432098765432098765432e-1 * t42 / t70 * t54 * t26 - 0.30864197530864197530864197530864197530864197530865e-2 * t42 * t43 * (t54 * t9 * t24 * t26 * t30 * t31 / t19 / 0.18e2 + 0.2e1 / 0.3e1 * t48 * t49 * t17 / t20 / r0) * t26 + 0.43209876543209876543209876543209876543209876543210e0 * t68 * t69 * t31 / t19 / t110)
  v4rho4_0_ = 0.2e1 * r0 * t118 + 0.8e1 * t78

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t8 = r0 <= f.p.dens_threshold or t7
  t10 = 0.1e1 - t5 <= f.p.zeta_threshold
  t11 = t3 ** 2
  t12 = 0.1e1 / t11
  t13 = t2 * t12
  t14 = t4 - t13
  t15 = f.my_piecewise5(t7, 0, t10, 0, t14)
  t16 = f.p.zeta_threshold - 0.1e1
  t17 = -t16
  t18 = f.my_piecewise5(t7, t16, t10, t17, t5)
  t19 = 0.1e1 + t18
  t21 = t19 * jnp.pi * params.beta
  t22 = 3 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = 0.1e1 / jnp.pi
  t25 = t24 ** (0.1e1 / 0.3e1)
  t27 = t23 / t25
  t28 = 4 ** (0.1e1 / 0.3e1)
  t29 = t3 ** (0.1e1 / 0.3e1)
  t31 = t27 * t28 * t29
  t33 = t21 * t31 / 0.6e1
  t34 = int1(t33)
  t36 = int2(t33)
  t38 = 0.1e1 / params.beta
  t39 = t36 * t24 * t38
  t40 = t22 * t25
  t41 = t28 ** 2
  t45 = t40 * t41 / t29 / t3
  t47 = t39 * t45 / 0.6e1
  t52 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t15 * t34 + t47) * t24 * t38)
  t55 = r1 <= f.p.dens_threshold or t10
  t57 = f.my_piecewise5(t10, 0, t7, 0, -t14)
  t58 = f.my_piecewise5(t10, t16, t7, t17, -t5)
  t59 = 0.1e1 + t58
  t61 = t59 * jnp.pi * params.beta
  t63 = t61 * t31 / 0.6e1
  t64 = int1(t63)
  t66 = int2(t63)
  t68 = t66 * t24 * t38
  t70 = t68 * t45 / 0.6e1
  t75 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t57 * t64 + t70) * t24 * t38)
  t79 = t2 / t11 / t3
  t81 = -0.2e1 * t12 + 0.2e1 * t79
  t82 = f.my_piecewise5(t7, 0, t10, 0, t81)
  t88 = t29 ** 2
  t91 = t27 * t28 / t88
  t93 = t21 * t91 / 0.18e2
  t94 = t15 * jnp.pi * params.beta * t31 / 0.6e1 + t93
  t96 = t19 ** 2
  t97 = jnp.pi ** 2
  t99 = params.beta ** 2
  t101 = t25 ** 2
  t105 = t22 / t101 * t41 * t88
  t108 = xc_E1_scaled(t96 * t97 * t99 * t105 / 0.12e2)
  t111 = t19 * t4
  t113 = t94 * t108 * t111 / 0.3e1
  t117 = t40 * t41 / t29 / t11
  t119 = 0.2e1 / 0.9e1 * t39 * t117
  t124 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t15 * t94 * t108 + t82 * t34 + t113 - t119) * t24 * t38)
  t126 = f.my_piecewise5(t10, 0, t7, 0, -t81)
  t133 = t61 * t91 / 0.18e2
  t134 = t57 * jnp.pi * params.beta * t31 / 0.6e1 + t133
  t136 = t59 ** 2
  t141 = xc_E1_scaled(t136 * t97 * t99 * t105 / 0.12e2)
  t144 = t59 * t4
  t146 = t134 * t141 * t144 / 0.3e1
  t148 = 0.2e1 / 0.9e1 * t68 * t117
  t153 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t57 * t134 * t141 + t126 * t64 + t146 - t148) * t24 * t38)
  d11 = 0.2e1 * t52 + 0.2e1 * t75 + t3 * (t124 + t153)
  t156 = -t4 - t13
  t157 = f.my_piecewise5(t7, 0, t10, 0, t156)
  t163 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t157 * t34 + t47) * t24 * t38)
  t165 = f.my_piecewise5(t10, 0, t7, 0, -t156)
  t171 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t165 * t64 + t70) * t24 * t38)
  t172 = 0.2e1 * t79
  t173 = f.my_piecewise5(t7, 0, t10, 0, t172)
  t181 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t157 * t94 * t108 + t173 * t34 + t113 - t119) * t24 * t38)
  t182 = f.my_piecewise5(t10, 0, t7, 0, -t172)
  t190 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t165 * t134 * t141 + t182 * t64 + t146 - t148) * t24 * t38)
  d12 = t52 + t75 + t163 + t171 + t3 * (t181 + t190)
  t196 = 0.2e1 * t12 + 0.2e1 * t79
  t197 = f.my_piecewise5(t7, 0, t10, 0, t196)
  t203 = t157 * jnp.pi * params.beta * t31 / 0.6e1 + t93
  t213 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t197 * t34 + t157 * t203 * t108 + t203 * t108 * t111 / 0.3e1 - t119) * t24 * t38)
  t215 = f.my_piecewise5(t10, 0, t7, 0, -t196)
  t221 = t165 * jnp.pi * params.beta * t31 / 0.6e1 + t133
  t231 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t215 * t64 + t165 * t221 * t141 + t221 * t141 * t144 / 0.3e1 - t148) * t24 * t38)
  d22 = 0.2e1 * t163 + 0.2e1 * t171 + t3 * (t213 + t231)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t8 = r0 <= f.p.dens_threshold or t7
  t10 = 0.1e1 - t5 <= f.p.zeta_threshold
  t11 = t3 ** 2
  t12 = 0.1e1 / t11
  t13 = t11 * t3
  t14 = 0.1e1 / t13
  t17 = 0.2e1 * t2 * t14 - 0.2e1 * t12
  t18 = f.my_piecewise5(t7, 0, t10, 0, t17)
  t19 = f.p.zeta_threshold - 0.1e1
  t20 = -t19
  t21 = f.my_piecewise5(t7, t19, t10, t20, t5)
  t22 = 0.1e1 + t21
  t24 = t22 * jnp.pi * params.beta
  t25 = 3 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t27 = 0.1e1 / jnp.pi
  t28 = t27 ** (0.1e1 / 0.3e1)
  t30 = t26 / t28
  t31 = 4 ** (0.1e1 / 0.3e1)
  t32 = t3 ** (0.1e1 / 0.3e1)
  t34 = t30 * t31 * t32
  t36 = t24 * t34 / 0.6e1
  t37 = int1(t36)
  t40 = -t2 * t12 + t4
  t41 = f.my_piecewise5(t7, 0, t10, 0, t40)
  t43 = t41 * jnp.pi * params.beta
  t46 = t32 ** 2
  t48 = t31 / t46
  t49 = t30 * t48
  t52 = t43 * t34 / 0.6e1 + t24 * t49 / 0.18e2
  t53 = t41 * t52
  t54 = t22 ** 2
  t55 = jnp.pi ** 2
  t57 = params.beta ** 2
  t58 = t54 * t55 * t57
  t59 = t28 ** 2
  t60 = 0.1e1 / t59
  t61 = t25 * t60
  t62 = t31 ** 2
  t64 = t61 * t62 * t46
  t67 = xc_E1_scaled(t58 * t64 / 0.12e2)
  t69 = t52 * t67
  t70 = t22 * t4
  t73 = int2(t36)
  t75 = 0.1e1 / params.beta
  t76 = t73 * t27 * t75
  t77 = t25 * t28
  t81 = t77 * t62 / t32 / t11
  t88 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t18 * t37 + t53 * t67 + t69 * t70 / 0.3e1 - 0.2e1 / 0.9e1 * t76 * t81) * t27 * t75)
  t91 = r1 <= f.p.dens_threshold or t10
  t93 = f.my_piecewise5(t10, 0, t7, 0, -t17)
  t94 = f.my_piecewise5(t10, t19, t7, t20, -t5)
  t95 = 0.1e1 + t94
  t97 = t95 * jnp.pi * params.beta
  t99 = t97 * t34 / 0.6e1
  t100 = int1(t99)
  t103 = f.my_piecewise5(t10, 0, t7, 0, -t40)
  t105 = t103 * jnp.pi * params.beta
  t110 = t105 * t34 / 0.6e1 + t97 * t49 / 0.18e2
  t111 = t103 * t110
  t112 = t95 ** 2
  t114 = t112 * t55 * t57
  t117 = xc_E1_scaled(t114 * t64 / 0.12e2)
  t119 = t110 * t117
  t120 = t95 * t4
  t123 = int2(t99)
  t125 = t123 * t27 * t75
  t132 = f.my_piecewise3(t91, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t93 * t100 + t111 * t117 + t119 * t120 / 0.3e1 - 0.2e1 / 0.9e1 * t125 * t81) * t27 * t75)
  t134 = t11 ** 2
  t138 = 0.6e1 * t14 - 0.6e1 * t2 / t134
  t139 = f.my_piecewise5(t7, 0, t10, 0, t138)
  t153 = t30 * t31 / t46 / t3
  t156 = t18 * jnp.pi * params.beta * t34 / 0.6e1 + t43 * t49 / 0.9e1 - t24 * t153 / 0.27e2
  t160 = 0.1e1 / t55
  t162 = 0.1e1 / t57
  t165 = t26 * t59 * t48
  t167 = t67 - 0.1e1 / t54 * t160 * t162 * t165
  t169 = t57 * t25
  t171 = t60 * t62
  t178 = t61 * t62 / t32
  t181 = t22 * t55 * t169 * t171 * t46 * t41 / 0.6e1 + t58 * t178 / 0.18e2
  t201 = t77 * t62 / t32 / t13
  t208 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t139 * t37 + 0.2e1 * t18 * t52 * t67 + t41 * t156 * t67 + t53 * t167 * t181 + t156 * t67 * t70 / 0.3e1 + t52 * t167 * t181 * t22 * t4 / 0.3e1 + t69 * t41 * t4 / 0.3e1 - 0.7e1 / 0.9e1 * t69 * t22 * t12 + 0.14e2 / 0.27e2 * t76 * t201) * t27 * t75)
  t210 = f.my_piecewise5(t10, 0, t7, 0, -t138)
  t223 = t93 * jnp.pi * params.beta * t34 / 0.6e1 + t105 * t49 / 0.9e1 - t97 * t153 / 0.27e2
  t230 = t117 - 0.1e1 / t112 * t160 * t162 * t165
  t239 = t95 * t55 * t169 * t171 * t46 * t103 / 0.6e1 + t114 * t178 / 0.18e2
  t262 = f.my_piecewise3(t91, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t210 * t100 + 0.2e1 * t93 * t110 * t117 + t103 * t223 * t117 + t111 * t230 * t239 + t223 * t117 * t120 / 0.3e1 + t110 * t230 * t239 * t95 * t4 / 0.3e1 + t119 * t103 * t4 / 0.3e1 - 0.7e1 / 0.9e1 * t119 * t95 * t12 + 0.14e2 / 0.27e2 * t125 * t201) * t27 * t75)
  d111 = 0.3e1 * t88 + 0.3e1 * t132 + t3 * (t208 + t262)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t8 = r0 <= f.p.dens_threshold or t7
  t10 = 0.1e1 - t5 <= f.p.zeta_threshold
  t11 = t3 ** 2
  t12 = t11 * t3
  t13 = 0.1e1 / t12
  t14 = t11 ** 2
  t15 = 0.1e1 / t14
  t18 = -0.6e1 * t2 * t15 + 0.6e1 * t13
  t19 = f.my_piecewise5(t7, 0, t10, 0, t18)
  t20 = f.p.zeta_threshold - 0.1e1
  t21 = -t20
  t22 = f.my_piecewise5(t7, t20, t10, t21, t5)
  t23 = 0.1e1 + t22
  t25 = t23 * jnp.pi * params.beta
  t26 = 3 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / jnp.pi
  t29 = t28 ** (0.1e1 / 0.3e1)
  t31 = t27 / t29
  t32 = 4 ** (0.1e1 / 0.3e1)
  t33 = t3 ** (0.1e1 / 0.3e1)
  t35 = t31 * t32 * t33
  t37 = t25 * t35 / 0.6e1
  t38 = int1(t37)
  t40 = 0.1e1 / t11
  t43 = 0.2e1 * t2 * t13 - 0.2e1 * t40
  t44 = f.my_piecewise5(t7, 0, t10, 0, t43)
  t46 = -t2 * t40 + t4
  t47 = f.my_piecewise5(t7, 0, t10, 0, t46)
  t49 = t47 * jnp.pi * params.beta
  t52 = t33 ** 2
  t53 = 0.1e1 / t52
  t54 = t32 * t53
  t55 = t31 * t54
  t58 = t49 * t35 / 0.6e1 + t25 * t55 / 0.18e2
  t59 = t44 * t58
  t60 = t23 ** 2
  t61 = jnp.pi ** 2
  t63 = params.beta ** 2
  t64 = t60 * t61 * t63
  t65 = t29 ** 2
  t66 = 0.1e1 / t65
  t67 = t26 * t66
  t68 = t32 ** 2
  t70 = t67 * t68 * t52
  t73 = xc_E1_scaled(t64 * t70 / 0.12e2)
  t77 = t44 * jnp.pi * params.beta
  t84 = t32 / t52 / t3
  t85 = t31 * t84
  t88 = t77 * t35 / 0.6e1 + t49 * t55 / 0.9e1 - t25 * t85 / 0.27e2
  t89 = t47 * t88
  t91 = t47 * t58
  t93 = 0.1e1 / t61
  t95 = 0.1e1 / t63
  t96 = 0.1e1 / t60 * t93 * t95
  t97 = t27 * t65
  t98 = t97 * t54
  t100 = -t96 * t98 + t73
  t102 = t63 * t26
  t103 = t23 * t61 * t102
  t104 = t66 * t68
  t109 = 0.1e1 / t33
  t111 = t67 * t68 * t109
  t114 = t103 * t104 * t52 * t47 / 0.6e1 + t64 * t111 / 0.18e2
  t115 = t100 * t114
  t117 = t88 * t73
  t118 = t23 * t4
  t121 = t58 * t100
  t122 = t114 * t23
  t123 = t122 * t4
  t126 = t58 * t73
  t127 = t47 * t4
  t130 = t23 * t40
  t133 = int2(t37)
  t135 = 0.1e1 / params.beta
  t136 = t133 * t28 * t135
  t137 = t26 * t29
  t141 = t137 * t68 / t33 / t12
  t148 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t19 * t38 + 0.2e1 * t59 * t73 + t89 * t73 + t91 * t115 + t117 * t118 / 0.3e1 + t121 * t123 / 0.3e1 + t126 * t127 / 0.3e1 - 0.7e1 / 0.9e1 * t126 * t130 + 0.14e2 / 0.27e2 * t136 * t141) * t28 * t135)
  t151 = r1 <= f.p.dens_threshold or t10
  t153 = f.my_piecewise5(t10, 0, t7, 0, -t18)
  t154 = f.my_piecewise5(t10, t20, t7, t21, -t5)
  t155 = 0.1e1 + t154
  t157 = t155 * jnp.pi * params.beta
  t159 = t157 * t35 / 0.6e1
  t160 = int1(t159)
  t163 = f.my_piecewise5(t10, 0, t7, 0, -t43)
  t165 = f.my_piecewise5(t10, 0, t7, 0, -t46)
  t167 = t165 * jnp.pi * params.beta
  t172 = t167 * t35 / 0.6e1 + t157 * t55 / 0.18e2
  t173 = t163 * t172
  t174 = t155 ** 2
  t176 = t174 * t61 * t63
  t179 = xc_E1_scaled(t176 * t70 / 0.12e2)
  t183 = t163 * jnp.pi * params.beta
  t190 = t183 * t35 / 0.6e1 + t167 * t55 / 0.9e1 - t157 * t85 / 0.27e2
  t191 = t165 * t190
  t193 = t165 * t172
  t196 = 0.1e1 / t174 * t93 * t95
  t198 = -t196 * t98 + t179
  t200 = t155 * t61 * t102
  t207 = t200 * t104 * t52 * t165 / 0.6e1 + t176 * t111 / 0.18e2
  t208 = t198 * t207
  t210 = t190 * t179
  t211 = t155 * t4
  t214 = t172 * t198
  t215 = t207 * t155
  t216 = t215 * t4
  t219 = t172 * t179
  t220 = t165 * t4
  t223 = t155 * t40
  t226 = int2(t159)
  t228 = t226 * t28 * t135
  t235 = f.my_piecewise3(t151, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t153 * t160 + 0.2e1 * t173 * t179 + t191 * t179 + t193 * t208 + t210 * t211 / 0.3e1 + t214 * t216 / 0.3e1 + t219 * t220 / 0.3e1 - 0.7e1 / 0.9e1 * t219 * t223 + 0.14e2 / 0.27e2 * t228 * t141) * t28 * t135)
  t240 = t137 * t68 / t33 / t14
  t247 = -0.24e2 * t15 + 0.24e2 * t2 / t14 / t3
  t248 = f.my_piecewise5(t7, 0, t10, 0, t247)
  t258 = t95 * t27
  t260 = t65 * t32
  t265 = t97 * t84
  t268 = t115 + 0.2e1 / t60 / t23 * t93 * t258 * t260 * t53 * t47 + 0.2e1 / 0.3e1 * t96 * t265
  t272 = t47 ** 2
  t288 = t67 * t68 / t33 / t3
  t291 = t272 * t61 * t63 * t70 / 0.6e1 + 0.2e1 / 0.9e1 * t103 * t104 * t109 * t47 + t103 * t104 * t52 * t44 / 0.6e1 - t64 * t288 / 0.54e2
  t325 = t31 * t32 / t52 / t11
  t328 = t19 * jnp.pi * params.beta * t35 / 0.6e1 + t77 * t55 / 0.6e1 - t49 * t85 / 0.9e1 + 0.5e1 / 0.81e2 * t25 * t325
  t348 = -0.140e3 / 0.81e2 * t136 * t240 + t248 * t38 - 0.10e2 / 0.9e1 * t117 * t130 + 0.2e1 / 0.3e1 * t88 * t100 * t123 + t58 * t268 * t123 / 0.3e1 + t121 * t291 * t23 * t4 / 0.3e1 + 0.2e1 / 0.3e1 * t121 * t114 * t47 * t4 - 0.10e2 / 0.9e1 * t126 * t47 * t40 + 0.70e2 / 0.27e2 * t126 * t23 * t13 + 0.3e1 * t59 * t115 + 0.2e1 * t89 * t115 + t91 * t268 * t114 + t91 * t100 * t291 + t328 * t73 * t118 / 0.3e1 + 0.2e1 / 0.3e1 * t117 * t127 + t126 * t44 * t4 / 0.3e1 + 0.3e1 * t19 * t58 * t73 + 0.3e1 * t44 * t88 * t73 + t47 * t328 * t73 - 0.10e2 / 0.9e1 * t121 * t122 * t40
  t352 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * t348 * t28 * t135)
  t356 = f.my_piecewise5(t10, 0, t7, 0, -t247)
  t373 = t208 + 0.2e1 / t174 / t155 * t93 * t258 * t260 * t53 * t165 + 0.2e1 / 0.3e1 * t196 * t265
  t377 = t165 ** 2
  t392 = t377 * t61 * t63 * t70 / 0.6e1 + 0.2e1 / 0.9e1 * t200 * t104 * t109 * t165 + t200 * t104 * t52 * t163 / 0.6e1 - t176 * t288 / 0.54e2
  t425 = t153 * jnp.pi * params.beta * t35 / 0.6e1 + t183 * t55 / 0.6e1 - t167 * t85 / 0.9e1 + 0.5e1 / 0.81e2 * t157 * t325
  t445 = -0.140e3 / 0.81e2 * t228 * t240 + t356 * t160 - 0.10e2 / 0.9e1 * t210 * t223 + 0.2e1 / 0.3e1 * t190 * t198 * t216 + t172 * t373 * t216 / 0.3e1 + t214 * t392 * t155 * t4 / 0.3e1 + 0.2e1 / 0.3e1 * t214 * t207 * t165 * t4 - 0.10e2 / 0.9e1 * t219 * t165 * t40 + 0.70e2 / 0.27e2 * t219 * t155 * t13 + 0.3e1 * t173 * t208 + 0.2e1 * t191 * t208 + t193 * t373 * t207 + t193 * t198 * t392 + t425 * t179 * t211 / 0.3e1 + 0.2e1 / 0.3e1 * t210 * t220 + t219 * t163 * t4 / 0.3e1 + 0.3e1 * t153 * t172 * t179 + 0.3e1 * t163 * t190 * t179 + t165 * t425 * t179 - 0.10e2 / 0.9e1 * t214 * t215 * t40
  t449 = f.my_piecewise3(t151, 0, -0.25000000000000000000000000000000000000000000000000e0 * t445 * t28 * t135)
  d1111 = 0.4e1 * t148 + 0.4e1 * t235 + t3 * (t352 + t449)

  res = {'v4rho4': d1111}
  return res
