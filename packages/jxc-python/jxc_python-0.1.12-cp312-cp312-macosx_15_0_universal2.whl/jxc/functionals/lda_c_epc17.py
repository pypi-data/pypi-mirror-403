"""Generated from lda_c_epc17.mpl."""

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

  epc17_E = lambda rho_ep: -rho_ep / (params_a - params_b * jnp.sqrt(rho_ep) + params_c * rho_ep)

  f_epc17 = lambda rs, zeta: f.my_piecewise3(jnp.logical_and(f.screen_dens(rs, zeta), f.screen_dens(rs, -zeta)), 0, epc17_E(f.n_spin(rs, f.z_thr(zeta)) * f.n_spin(rs, f.z_thr(-zeta))) / f.n_total(rs))

  functional_body = lambda rs, zeta: f_epc17(rs, zeta)

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

  epc17_E = lambda rho_ep: -rho_ep / (params_a - params_b * jnp.sqrt(rho_ep) + params_c * rho_ep)

  f_epc17 = lambda rs, zeta: f.my_piecewise3(jnp.logical_and(f.screen_dens(rs, zeta), f.screen_dens(rs, -zeta)), 0, epc17_E(f.n_spin(rs, f.z_thr(zeta)) * f.n_spin(rs, f.z_thr(-zeta))) / f.n_total(rs))

  functional_body = lambda rs, zeta: f_epc17(rs, zeta)

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
  t21 = t4 ** 2
  t22 = t17 * t21
  t24 = jnp.sqrt(t22 * t20)
  t27 = params.c * t17
  t28 = t21 * t20
  t31 = params.a - params.b * t24 / 0.2e1 + t27 * t28 / 0.4e1
  t32 = 0.1e1 / t31
  t33 = t20 * t32
  t36 = f.my_piecewise3(t3, 0, -t18 * t33 / 0.4e1)
  t38 = t14 / t21
  t39 = t5 - t38
  t40 = f.my_piecewise5(t8, 0, t12, 0, t39)
  t44 = t17 * t20 * t32
  t46 = f.my_piecewise5(t12, 0, t8, 0, -t39)
  t49 = t31 ** 2
  t51 = t20 / t49
  t53 = params.b / t24
  t57 = 0.2e1 * t18 * t20
  t67 = t27 * t4 * t20 / 0.2e1
  t76 = f.my_piecewise3(t3, 0, -t40 * t4 * t33 / 0.4e1 - t44 / 0.4e1 - t18 * t46 * t32 / 0.4e1 + t18 * t51 * (-t53 * (t40 * t21 * t20 + t22 * t46 + t57) / 0.4e1 + params.c * t40 * t28 / 0.4e1 + t67 + t27 * t21 * t46 / 0.4e1) / 0.4e1)
  vrho_0_ = t4 * t76 + t36
  t78 = -t5 - t38
  t79 = f.my_piecewise5(t8, 0, t12, 0, t78)
  t83 = f.my_piecewise5(t12, 0, t8, 0, -t78)
  t103 = f.my_piecewise3(t3, 0, -t79 * t4 * t33 / 0.4e1 - t44 / 0.4e1 - t18 * t83 * t32 / 0.4e1 + t18 * t51 * (-t53 * (t79 * t21 * t20 + t22 * t83 + t57) / 0.4e1 + params.c * t79 * t28 / 0.4e1 + t67 + t27 * t21 * t83 / 0.4e1) / 0.4e1)
  vrho_1_ = t4 * t103 + t36

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
  t8 = (0.1e1 + t6) ** 2
  t9 = t8 * r0
  t10 = r0 ** 2
  t12 = jnp.sqrt(t8 * t10)
  t15 = params.c * t8
  t18 = params.a - params.b * t12 / 0.2e1 + t15 * t10 / 0.4e1
  t19 = 0.1e1 / t18
  t22 = f.my_piecewise3(t2, 0, -t9 * t19 / 0.4e1)
  t24 = t18 ** 2
  t36 = f.my_piecewise3(t2, 0, -t8 * t19 / 0.4e1 + t9 / t24 * (-params.b / t12 * t9 / 0.2e1 + t15 * r0 / 0.2e1) / 0.4e1)
  vrho_0_ = r0 * t36 + t22

  res = {'vrho': vrho_0_}
  return res
