"""Generated from lda_c_epc18.mpl."""

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
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))

  epc18_beta = lambda rho_e, rho_p: rho_e ** (1 / 3) + rho_p ** (1 / 3)

  epc18_E = lambda rho_e, rho_p: -(rho_e * rho_p) / (params_a - params_b * epc18_beta(rho_e, rho_p) ** 3 + params_c * epc18_beta(rho_e, rho_p) ** 6)

  f_epc18 = lambda rs, zeta: f.my_piecewise3(jnp.logical_and(f.screen_dens(rs, zeta), f.screen_dens(rs, -zeta)), 0, epc18_E(f.n_spin(rs, f.z_thr(zeta)), f.n_spin(rs, f.z_thr(-zeta))) / f.n_total(rs))

  functional_body = lambda rs, zeta: f_epc18(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res


def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_a_raw = params.a
  if isinstance(params_a_raw, (str, bytes, dict)):
    params_a = params_a_raw
  else:
    try:
      params_a_seq = list(params_a_raw)
    except TypeError:
      params_a = params_a_raw
    else:
      params_a_seq = np.asarray(params_a_seq, dtype=np.float64)
      params_a = np.concatenate((np.array([np.nan], dtype=np.float64), params_a_seq))
  params_b_raw = params.b
  if isinstance(params_b_raw, (str, bytes, dict)):
    params_b = params_b_raw
  else:
    try:
      params_b_seq = list(params_b_raw)
    except TypeError:
      params_b = params_b_raw
    else:
      params_b_seq = np.asarray(params_b_seq, dtype=np.float64)
      params_b = np.concatenate((np.array([np.nan], dtype=np.float64), params_b_seq))
  params_c_raw = params.c
  if isinstance(params_c_raw, (str, bytes, dict)):
    params_c = params_c_raw
  else:
    try:
      params_c_seq = list(params_c_raw)
    except TypeError:
      params_c = params_c_raw
    else:
      params_c_seq = np.asarray(params_c_seq, dtype=np.float64)
      params_c = np.concatenate((np.array([np.nan], dtype=np.float64), params_c_seq))

  epc18_beta = lambda rho_e, rho_p: rho_e ** (1 / 3) + rho_p ** (1 / 3)

  epc18_E = lambda rho_e, rho_p: -(rho_e * rho_p) / (params_a - params_b * epc18_beta(rho_e, rho_p) ** 3 + params_c * epc18_beta(rho_e, rho_p) ** 6)

  f_epc18 = lambda rs, zeta: f.my_piecewise3(jnp.logical_and(f.screen_dens(rs, zeta), f.screen_dens(rs, -zeta)), 0, epc18_E(f.n_spin(rs, f.z_thr(zeta)), f.n_spin(rs, f.z_thr(-zeta))) / f.n_total(rs))

  functional_body = lambda rs, zeta: f_epc18(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t3 = jnp.logical_and(r0 <= f.p.dens_threshold, r1 <= f.p.dens_threshold)
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
  t18 = t17 * t4
  t19 = f.my_piecewise5(t12, t9, t8, t13, -t15)
  t20 = 0.1e1 + t19
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = t18 ** (0.1e1 / 0.3e1)
  t26 = (t20 * t4) ** (0.1e1 / 0.3e1)
  t29 = t22 * t23 / 0.2e1 + t22 * t26 / 0.2e1
  t30 = t29 ** 2
  t33 = t30 ** 2
  t36 = -params.b * t30 * t29 + params.c * t33 * t30 + params.a
  t37 = 0.1e1 / t36
  t38 = t20 * t37
  t41 = f.my_piecewise3(t3, 0, -t18 * t38 / 0.4e1)
  t42 = t4 ** 2
  t44 = t14 / t42
  t45 = t5 - t44
  t46 = f.my_piecewise5(t8, 0, t12, 0, t45)
  t47 = t46 * t4
  t50 = t17 * t20 * t37
  t52 = f.my_piecewise5(t12, 0, t8, 0, -t45)
  t55 = t36 ** 2
  t57 = t20 / t55
  t58 = params.b * t30
  t59 = t23 ** 2
  t61 = t22 / t59
  t64 = t26 ** 2
  t66 = t22 / t64
  t71 = t61 * (t47 + 0.1e1 + t16) / 0.6e1 + t66 * (t52 * t4 + t19 + 0.1e1) / 0.6e1
  t75 = params.c * t33 * t29
  t83 = f.my_piecewise3(t3, 0, -t47 * t38 / 0.4e1 - t50 / 0.4e1 - t18 * t52 * t37 / 0.4e1 + t18 * t57 * (-0.3e1 * t58 * t71 + 0.6e1 * t75 * t71) / 0.4e1)
  vrho_0_ = t4 * t83 + t41
  t85 = -t5 - t44
  t86 = f.my_piecewise5(t8, 0, t12, 0, t85)
  t87 = t86 * t4
  t90 = f.my_piecewise5(t12, 0, t8, 0, -t85)
  t99 = t61 * (t87 + 0.1e1 + t16) / 0.6e1 + t66 * (t90 * t4 + t19 + 0.1e1) / 0.6e1
  t109 = f.my_piecewise3(t3, 0, -t87 * t38 / 0.4e1 - t50 / 0.4e1 - t18 * t90 * t37 / 0.4e1 + t18 * t57 * (-0.3e1 * t58 * t99 + 0.6e1 * t75 * t99) / 0.4e1)
  vrho_1_ = t4 * t109 + t41

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t8 = t7 ** 2
  t9 = t8 * r0
  t10 = params.b * t7
  t13 = params.c * t8
  t14 = r0 ** 2
  t17 = -0.4e1 * t10 * r0 + 0.16e2 * t13 * t14 + params.a
  t18 = 0.1e1 / t17
  t21 = f.my_piecewise3(t2, 0, -t9 * t18 / 0.4e1)
  t23 = t17 ** 2
  t33 = f.my_piecewise3(t2, 0, -t8 * t18 / 0.4e1 + t9 / t23 * (0.32e2 * t13 * r0 - 0.4e1 * t10) / 0.4e1)
  vrho_0_ = r0 * t33 + t21

  res = {'vrho': vrho_0_}
  return res
