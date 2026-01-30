"""Generated from lda_x_1d_soft.mpl."""

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

  x1d_inter = lambda x: 2.0 * BesselK(0, x)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselK = lambda order, value: (
      bessel_k0(value)
      if order == 0
      else (
          bessel_k1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselK order: {order}")
      )
  )

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

  x1d_inter = lambda x: 2.0 * BesselK(0, x)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselK = lambda order, value: (
      bessel_k0(value)
      if order == 0
      else (
          bessel_k1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselK order: {order}")
      )
  )

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

  x1d_inter = lambda x: 2.0 * BesselK(0, x)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselK = lambda order, value: (
      bessel_k0(value)
      if order == 0
      else (
          bessel_k1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselK order: {order}")
      )
  )

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

  x1d_inter = lambda x: 2.0 * BesselK(0, x)

  x1d_R = lambda rs: jnp.pi * params_beta / (2 * rs)

  x1d_fs = lambda rs, z: -((1 + z) * int1((1 + z) * x1d_R(rs)) - int2((1 + z) * x1d_R(rs)) / x1d_R(rs)) / (4.0 * jnp.pi * params_beta)

  x1d_f = lambda rs, z: +f.my_piecewise3(f.screen_dens_zeta(rs, z), 0, x1d_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens_zeta(rs, -z), 0, x1d_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: x1d_f(rs, z)

  int1 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  int2 = lambda arg: integrate_adaptive(lambda t: x1d_inter(jnp.clip(t, 1e-20, None)) * jnp.clip(t, 1e-20, None), 1e-20, arg, epsabs=1e-13, epsrel=1e-13, max_depth=32)

  _raise_value_error = lambda msg: (_ for _ in ()).throw(ValueError(msg))

  BesselK = lambda order, value: (
      bessel_k0(value)
      if order == 0
      else (
          bessel_k1(value)
          if order == 1
          else _raise_value_error(f"Unsupported BesselK order: {order}")
      )
  )

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
  t22 = t8 * jnp.pi * params.beta * t12 * t15 * t17 * t18 / 0.6e1
  t23 = int2(t22)
  t24 = jnp.pi ** 2
  t27 = params.beta ** 2
  t29 = t23 / t24 / t27
  t30 = t11 * t14
  t31 = t17 ** 2
  t38 = f.my_piecewise3(t4, 0, -0.41666666666666666666666666666666666666666666666667e-1 * t29 * t30 * t31 / t18 / r0)
  t40 = t8 ** 2
  t43 = t18 ** 2
  t47 = scipy.special.k0(t22)
  t51 = r0 ** 2
  t59 = f.my_piecewise3(t4, 0, -0.92592592592592592592592592592592592592592592592592e-2 * t40 * t12 * t15 * t17 / t43 / r0 * t47 + 0.55555555555555555555555555555555555555555555555556e-1 * t29 * t30 * t31 / t18 / t51)
  v2rho2_0_ = 0.2e1 * r0 * t59 + 0.4e1 * t38
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
  t29 = t8 * jnp.pi * params.beta * t11 * t15 * t17 * t18 / 0.6e1
  t30 = scipy.special.k0(t29)
  t34 = int2(t29)
  t35 = jnp.pi ** 2
  t38 = params.beta ** 2
  t40 = t34 / t35 / t38
  t41 = t10 * t14
  t42 = t17 ** 2
  t43 = r0 ** 2
  t45 = 0.1e1 / t18 / t43
  t51 = f.my_piecewise3(t4, 0, -0.92592592592592592592592592592592592592592592592592e-2 * t16 * t17 / t19 / r0 * t30 + 0.55555555555555555555555555555555555555555555555556e-1 * t40 * t41 * t42 * t45)
  t61 = t14 ** 2
  t65 = scipy.special.k1(t29)
  t79 = f.my_piecewise3(t4, 0, 0.27777777777777777777777777777777777777777777777778e-1 * t16 * t17 / t19 / t43 * t30 + 0.15432098765432098765432098765432098765432098765432e-2 * t9 * t8 * t10 / t61 * t42 * t45 * t65 * jnp.pi * params.beta - 0.12962962962962962962962962962962962962962962962963e0 * t40 * t41 * t42 / t18 / t43 / r0)
  v3rho3_0_ = 0.2e1 * r0 * t79 + 0.6e1 * t51

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
  t13 = 0.1e1 / jnp.pi
  t14 = t13 ** (0.1e1 / 0.3e1)
  t15 = 0.1e1 / t14
  t16 = t9 * t11 * t15
  t17 = 4 ** (0.1e1 / 0.3e1)
  t18 = r0 ** 2
  t19 = r0 ** (0.1e1 / 0.3e1)
  t20 = t19 ** 2
  t30 = t8 * jnp.pi * params.beta * t11 * t15 * t17 * t19 / 0.6e1
  t31 = scipy.special.k0(t30)
  t37 = t14 ** 2
  t39 = t17 ** 2
  t41 = t9 * t8 * t10 / t37 * t39
  t44 = scipy.special.k1(t30)
  t46 = jnp.pi * params.beta
  t50 = int2(t30)
  t51 = jnp.pi ** 2
  t54 = params.beta ** 2
  t56 = t50 / t51 / t54
  t57 = t10 * t14
  t58 = t18 * r0
  t60 = 0.1e1 / t19 / t58
  t66 = f.my_piecewise3(t4, 0, 0.27777777777777777777777777777777777777777777777778e-1 * t16 * t17 / t20 / t18 * t31 + 0.15432098765432098765432098765432098765432098765432e-2 * t41 / t19 / t18 * t44 * t46 - 0.12962962962962962962962962962962962962962962962963e0 * t56 * t57 * t39 * t60)
  t78 = t9 ** 2
  t98 = t18 ** 2
  t106 = f.my_piecewise3(t4, 0, -0.10288065843621399176954732510288065843621399176955e0 * t16 * t17 / t20 / t58 * t31 - 0.82304526748971193415637860082304526748971193415638e-2 * t41 * t60 * t44 * t46 + 0.10288065843621399176954732510288065843621399176955e-2 * t78 * t51 * jnp.pi / t58 * (-t31 - 0.1e1 / t8 * t13 / params.beta * t10 * t14 * t39 / t19 * t44 / 0.2e1) * t54 + 0.43209876543209876543209876543209876543209876543210e0 * t56 * t57 * t39 / t19 / t98)
  v4rho4_0_ = 0.2e1 * r0 * t106 + 0.8e1 * t66

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
  t96 = scipy.special.k0(t33)
  t100 = t19 * t4
  t102 = 0.66666666666666666666666666666666666666666666666667e0 * t94 * t96 * t100
  t106 = t40 * t41 / t29 / t11
  t108 = 0.2e1 / 0.9e1 * t39 * t106
  t113 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t82 * t34 + 0.20e1 * t15 * t94 * t96 + t102 - t108) * t24 * t38)
  t115 = f.my_piecewise5(t10, 0, t7, 0, -t81)
  t122 = t61 * t91 / 0.18e2
  t123 = t57 * jnp.pi * params.beta * t31 / 0.6e1 + t122
  t125 = scipy.special.k0(t63)
  t129 = t59 * t4
  t131 = 0.66666666666666666666666666666666666666666666666667e0 * t123 * t125 * t129
  t133 = 0.2e1 / 0.9e1 * t68 * t106
  t138 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t115 * t64 + 0.20e1 * t57 * t123 * t125 + t131 - t133) * t24 * t38)
  d11 = 0.2e1 * t52 + 0.2e1 * t75 + t3 * (t113 + t138)
  t141 = -t4 - t13
  t142 = f.my_piecewise5(t7, 0, t10, 0, t141)
  t148 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t142 * t34 + t47) * t24 * t38)
  t150 = f.my_piecewise5(t10, 0, t7, 0, -t141)
  t156 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t150 * t64 + t70) * t24 * t38)
  t157 = 0.2e1 * t79
  t158 = f.my_piecewise5(t7, 0, t10, 0, t157)
  t167 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t158 * t34 + 0.20e1 * t142 * t94 * t96 + t102 - t108) * t24 * t38)
  t168 = f.my_piecewise5(t10, 0, t7, 0, -t157)
  t177 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t168 * t64 + 0.20e1 * t150 * t123 * t125 + t131 - t133) * t24 * t38)
  d12 = t52 + t75 + t148 + t156 + t3 * (t167 + t177)
  t183 = 0.2e1 * t12 + 0.2e1 * t79
  t184 = f.my_piecewise5(t7, 0, t10, 0, t183)
  t190 = t142 * jnp.pi * params.beta * t31 / 0.6e1 + t93
  t201 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t184 * t34 + 0.20e1 * t142 * t190 * t96 + 0.66666666666666666666666666666666666666666666666667e0 * t190 * t96 * t100 - t108) * t24 * t38)
  t203 = f.my_piecewise5(t10, 0, t7, 0, -t183)
  t209 = t150 * jnp.pi * params.beta * t31 / 0.6e1 + t122
  t220 = f.my_piecewise3(t55, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t203 * t64 + 0.20e1 * t150 * t209 * t125 + 0.66666666666666666666666666666666666666666666666667e0 * t209 * t125 * t129 - t133) * t24 * t38)
  d22 = 0.2e1 * t148 + 0.2e1 * t156 + t3 * (t201 + t220)
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
  t49 = t30 * t31 / t46
  t52 = t43 * t34 / 0.6e1 + t24 * t49 / 0.18e2
  t54 = scipy.special.k0(t36)
  t57 = t52 * t54
  t58 = t22 * t4
  t61 = int2(t36)
  t63 = 0.1e1 / params.beta
  t64 = t61 * t27 * t63
  t65 = t25 * t28
  t66 = t31 ** 2
  t70 = t65 * t66 / t32 / t11
  t77 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t18 * t37 + 0.20e1 * t41 * t52 * t54 + 0.66666666666666666666666666666666666666666666666667e0 * t57 * t58 - 0.2e1 / 0.9e1 * t64 * t70) * t27 * t63)
  t80 = r1 <= f.p.dens_threshold or t10
  t82 = f.my_piecewise5(t10, 0, t7, 0, -t17)
  t83 = f.my_piecewise5(t10, t19, t7, t20, -t5)
  t84 = 0.1e1 + t83
  t86 = t84 * jnp.pi * params.beta
  t88 = t86 * t34 / 0.6e1
  t89 = int1(t88)
  t92 = f.my_piecewise5(t10, 0, t7, 0, -t40)
  t94 = t92 * jnp.pi * params.beta
  t99 = t94 * t34 / 0.6e1 + t86 * t49 / 0.18e2
  t101 = scipy.special.k0(t88)
  t104 = t99 * t101
  t105 = t84 * t4
  t108 = int2(t88)
  t110 = t108 * t27 * t63
  t117 = f.my_piecewise3(t80, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t82 * t89 + 0.20e1 * t92 * t99 * t101 + 0.66666666666666666666666666666666666666666666666667e0 * t104 * t105 - 0.2e1 / 0.9e1 * t110 * t70) * t27 * t63)
  t119 = t11 ** 2
  t123 = 0.6e1 * t14 - 0.6e1 * t2 / t119
  t124 = f.my_piecewise5(t7, 0, t10, 0, t123)
  t138 = t30 * t31 / t46 / t3
  t141 = t18 * jnp.pi * params.beta * t34 / 0.6e1 + t43 * t49 / 0.9e1 - t24 * t138 / 0.27e2
  t145 = t52 ** 2
  t147 = scipy.special.k1(t36)
  t165 = t65 * t66 / t32 / t13
  t172 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t124 * t37 + 0.40e1 * t18 * t52 * t54 + 0.20e1 * t41 * t141 * t54 - 0.20e1 * t41 * t145 * t147 + 0.66666666666666666666666666666666666666666666666667e0 * t141 * t54 * t58 - 0.66666666666666666666666666666666666666666666666667e0 * t145 * t147 * t58 + 0.66666666666666666666666666666666666666666666666667e0 * t57 * t41 * t4 - 0.15555555555555555555555555555555555555555555555556e1 * t57 * t22 * t12 + 0.14e2 / 0.27e2 * t64 * t165) * t27 * t63)
  t174 = f.my_piecewise5(t10, 0, t7, 0, -t123)
  t187 = t82 * jnp.pi * params.beta * t34 / 0.6e1 + t94 * t49 / 0.9e1 - t86 * t138 / 0.27e2
  t191 = t99 ** 2
  t193 = scipy.special.k1(t88)
  t214 = f.my_piecewise3(t80, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t174 * t89 + 0.40e1 * t82 * t99 * t101 + 0.20e1 * t92 * t187 * t101 - 0.20e1 * t92 * t191 * t193 + 0.66666666666666666666666666666666666666666666666667e0 * t187 * t101 * t105 - 0.66666666666666666666666666666666666666666666666667e0 * t191 * t193 * t105 + 0.66666666666666666666666666666666666666666666666667e0 * t104 * t92 * t4 - 0.15555555555555555555555555555555555555555555555556e1 * t104 * t84 * t12 + 0.14e2 / 0.27e2 * t110 * t165) * t27 * t63)
  d111 = 0.3e1 * t77 + 0.3e1 * t117 + t3 * (t172 + t214)

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
  t55 = t31 * t32 / t52
  t58 = t49 * t35 / 0.6e1 + t25 * t55 / 0.18e2
  t60 = scipy.special.k0(t37)
  t64 = t44 * jnp.pi * params.beta
  t72 = t31 * t32 / t52 / t3
  t75 = t64 * t35 / 0.6e1 + t49 * t55 / 0.9e1 - t25 * t72 / 0.27e2
  t76 = t47 * t75
  t79 = t58 ** 2
  t81 = scipy.special.k1(t37)
  t84 = t75 * t60
  t85 = t23 * t4
  t88 = t79 * t81
  t91 = t58 * t60
  t92 = t47 * t4
  t95 = t23 * t40
  t98 = int2(t37)
  t100 = 0.1e1 / params.beta
  t101 = t98 * t28 * t100
  t102 = t26 * t29
  t103 = t32 ** 2
  t107 = t102 * t103 / t33 / t12
  t114 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t19 * t38 + 0.40e1 * t44 * t58 * t60 + 0.20e1 * t76 * t60 - 0.20e1 * t47 * t79 * t81 + 0.66666666666666666666666666666666666666666666666667e0 * t84 * t85 - 0.66666666666666666666666666666666666666666666666667e0 * t88 * t85 + 0.66666666666666666666666666666666666666666666666667e0 * t91 * t92 - 0.15555555555555555555555555555555555555555555555556e1 * t91 * t95 + 0.14e2 / 0.27e2 * t101 * t107) * t28 * t100)
  t117 = r1 <= f.p.dens_threshold or t10
  t119 = f.my_piecewise5(t10, 0, t7, 0, -t18)
  t120 = f.my_piecewise5(t10, t20, t7, t21, -t5)
  t121 = 0.1e1 + t120
  t123 = t121 * jnp.pi * params.beta
  t125 = t123 * t35 / 0.6e1
  t126 = int1(t125)
  t129 = f.my_piecewise5(t10, 0, t7, 0, -t43)
  t131 = f.my_piecewise5(t10, 0, t7, 0, -t46)
  t133 = t131 * jnp.pi * params.beta
  t138 = t133 * t35 / 0.6e1 + t123 * t55 / 0.18e2
  t140 = scipy.special.k0(t125)
  t144 = t129 * jnp.pi * params.beta
  t151 = t144 * t35 / 0.6e1 + t133 * t55 / 0.9e1 - t123 * t72 / 0.27e2
  t152 = t131 * t151
  t155 = t138 ** 2
  t157 = scipy.special.k1(t125)
  t160 = t151 * t140
  t161 = t121 * t4
  t164 = t155 * t157
  t167 = t138 * t140
  t168 = t131 * t4
  t171 = t121 * t40
  t174 = int2(t125)
  t176 = t174 * t28 * t100
  t183 = f.my_piecewise3(t117, 0, -0.25000000000000000000000000000000000000000000000000e0 * (t119 * t126 + 0.40e1 * t129 * t138 * t140 + 0.20e1 * t152 * t140 - 0.20e1 * t131 * t155 * t157 + 0.66666666666666666666666666666666666666666666666667e0 * t160 * t161 - 0.66666666666666666666666666666666666666666666666667e0 * t164 * t161 + 0.66666666666666666666666666666666666666666666666667e0 * t167 * t168 - 0.15555555555555555555555555555555555555555555555556e1 * t167 * t171 + 0.14e2 / 0.27e2 * t176 * t107) * t28 * t100)
  t188 = t102 * t103 / t33 / t14
  t195 = -0.24e2 * t15 + 0.24e2 * t2 / t14 / t3
  t196 = f.my_piecewise5(t7, 0, t10, 0, t195)
  t207 = t79 * t58
  t210 = t100 * t26
  t212 = t29 * t103
  t213 = 0.1e1 / t33
  t218 = -t60 - 0.1e1 / t23 * t28 * t210 * t212 * t213 * t81 / 0.2e1
  t245 = t31 * t32 / t52 / t11
  t248 = t19 * jnp.pi * params.beta * t35 / 0.6e1 + t64 * t55 / 0.6e1 - t49 * t72 / 0.9e1 + 0.5e1 / 0.81e2 * t25 * t245
  t271 = -0.140e3 / 0.81e2 * t101 * t188 + t196 * t38 - 0.22222222222222222222222222222222222222222222222223e1 * t84 * t95 - 0.20000000000000000000000000000000000000000000000000e1 * t75 * t81 * t58 * t23 * t4 + 0.22222222222222222222222222222222222222222222222223e1 * t88 * t95 - 0.66666666666666666666666666666666666666666666666667e0 * t207 * t218 * t85 - 0.22222222222222222222222222222222222222222222222223e1 * t91 * t47 * t40 + 0.51851851851851851851851851851851851851851851851853e1 * t91 * t23 * t13 - 0.60e1 * t76 * t81 * t58 - 0.20e1 * t47 * t207 * t218 + 0.66666666666666666666666666666666666666666666666667e0 * t248 * t60 * t85 + 0.13333333333333333333333333333333333333333333333333e1 * t84 * t92 - 0.13333333333333333333333333333333333333333333333333e1 * t88 * t92 + 0.66666666666666666666666666666666666666666666666667e0 * t91 * t44 * t4 + 0.60e1 * t19 * t58 * t60 + 0.60e1 * t44 * t75 * t60 - 0.60e1 * t44 * t79 * t81 + 0.20e1 * t47 * t248 * t60
  t275 = f.my_piecewise3(t8, 0, -0.25000000000000000000000000000000000000000000000000e0 * t271 * t28 * t100)
  t279 = f.my_piecewise5(t10, 0, t7, 0, -t195)
  t290 = t155 * t138
  t298 = -t140 - 0.1e1 / t121 * t28 * t210 * t212 * t213 * t157 / 0.2e1
  t324 = t119 * jnp.pi * params.beta * t35 / 0.6e1 + t144 * t55 / 0.6e1 - t133 * t72 / 0.9e1 + 0.5e1 / 0.81e2 * t123 * t245
  t347 = -0.140e3 / 0.81e2 * t176 * t188 + t279 * t126 - 0.22222222222222222222222222222222222222222222222223e1 * t160 * t171 - 0.20000000000000000000000000000000000000000000000000e1 * t151 * t157 * t138 * t121 * t4 + 0.22222222222222222222222222222222222222222222222223e1 * t164 * t171 - 0.66666666666666666666666666666666666666666666666667e0 * t290 * t298 * t161 - 0.22222222222222222222222222222222222222222222222223e1 * t167 * t131 * t40 + 0.51851851851851851851851851851851851851851851851853e1 * t167 * t121 * t13 - 0.60e1 * t152 * t157 * t138 - 0.20e1 * t131 * t290 * t298 + 0.66666666666666666666666666666666666666666666666667e0 * t324 * t140 * t161 + 0.13333333333333333333333333333333333333333333333333e1 * t160 * t168 - 0.13333333333333333333333333333333333333333333333333e1 * t164 * t168 + 0.66666666666666666666666666666666666666666666666667e0 * t167 * t129 * t4 + 0.60e1 * t119 * t138 * t140 + 0.60e1 * t129 * t151 * t140 - 0.60e1 * t129 * t155 * t157 + 0.20e1 * t131 * t324 * t140
  t351 = f.my_piecewise3(t117, 0, -0.25000000000000000000000000000000000000000000000000e0 * t347 * t28 * t100)
  d1111 = 0.4e1 * t114 + 0.4e1 * t183 + t3 * (t275 + t351)

  res = {'v4rho4': d1111}
  return res
