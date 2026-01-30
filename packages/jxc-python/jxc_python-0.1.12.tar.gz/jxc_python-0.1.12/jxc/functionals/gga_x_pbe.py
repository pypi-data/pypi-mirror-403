"""Generated from gga_x_pbe.mpl."""

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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbe_f, rs, z, xs0, xs1)

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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbe_f, rs, z, xs0, xs1)

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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbe_f, rs, z, xs0, xs1)

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
  t28 = 6 ** (0.1e1 / 0.3e1)
  t29 = params.mu * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t33 * s0
  t35 = r0 ** 2
  t36 = r0 ** (0.1e1 / 0.3e1)
  t37 = t36 ** 2
  t39 = 0.1e1 / t37 / t35
  t43 = params.kappa + t29 * t34 * t39 / 0.24e2
  t48 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t43)
  t52 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t48)
  t53 = r1 <= f.p.dens_threshold
  t54 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t55 = 0.1e1 + t54
  t56 = t55 <= f.p.zeta_threshold
  t57 = t55 ** (0.1e1 / 0.3e1)
  t59 = f.my_piecewise3(t56, t22, t57 * t55)
  t60 = t59 * t26
  t61 = t33 * s2
  t62 = r1 ** 2
  t63 = r1 ** (0.1e1 / 0.3e1)
  t64 = t63 ** 2
  t66 = 0.1e1 / t64 / t62
  t70 = params.kappa + t29 * t61 * t66 / 0.24e2
  t75 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t70)
  t79 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t60 * t75)
  t80 = t6 ** 2
  t82 = t16 / t80
  t83 = t7 - t82
  t84 = f.my_piecewise5(t10, 0, t14, 0, t83)
  t87 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t84)
  t92 = t26 ** 2
  t93 = 0.1e1 / t92
  t97 = t5 * t25 * t93 * t48 / 0.8e1
  t98 = params.kappa ** 2
  t100 = t5 * t27 * t98
  t101 = t43 ** 2
  t103 = 0.1e1 / t101 * params.mu
  t113 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t87 * t26 * t48 - t97 + t100 * t103 * t28 * t34 / t37 / t35 / r0 / 0.24e2)
  t115 = f.my_piecewise5(t14, 0, t10, 0, -t83)
  t118 = f.my_piecewise3(t56, 0, 0.4e1 / 0.3e1 * t57 * t115)
  t126 = t5 * t59 * t93 * t75 / 0.8e1
  t128 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t118 * t26 * t75 - t126)
  vrho_0_ = t52 + t79 + t6 * (t113 + t128)
  t131 = -t7 - t82
  t132 = f.my_piecewise5(t10, 0, t14, 0, t131)
  t135 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t132)
  t141 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t135 * t26 * t48 - t97)
  t143 = f.my_piecewise5(t14, 0, t10, 0, -t131)
  t146 = f.my_piecewise3(t56, 0, 0.4e1 / 0.3e1 * t57 * t143)
  t152 = t5 * t60 * t98
  t153 = t70 ** 2
  t155 = 0.1e1 / t153 * params.mu
  t165 = f.my_piecewise3(t53, 0, -0.3e1 / 0.8e1 * t5 * t146 * t26 * t75 - t126 + t152 * t155 * t28 * t61 / t64 / t62 / r1 / 0.24e2)
  vrho_1_ = t52 + t79 + t6 * (t141 + t165)
  t168 = t28 * t33
  t173 = f.my_piecewise3(t1, 0, -t100 * t103 * t168 * t39 / 0.64e2)
  vsigma_0_ = t6 * t173
  vsigma_1_ = 0.0e0
  t178 = f.my_piecewise3(t53, 0, -t152 * t155 * t168 * t66 / 0.64e2)
  vsigma_2_ = t6 * t178
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
  params_kappa_raw = params.kappa
  if isinstance(params_kappa_raw, (str, bytes, dict)):
    params_kappa = params_kappa_raw
  else:
    try:
      params_kappa_seq = list(params_kappa_raw)
    except TypeError:
      params_kappa = params_kappa_raw
    else:
      params_kappa_seq = np.asarray(params_kappa_seq, dtype=np.float64)
      params_kappa = np.concatenate((np.array([np.nan], dtype=np.float64), params_kappa_seq))
  params_mu_raw = params.mu
  if isinstance(params_mu_raw, (str, bytes, dict)):
    params_mu = params_mu_raw
  else:
    try:
      params_mu_seq = list(params_mu_raw)
    except TypeError:
      params_mu = params_mu_raw
    else:
      params_mu_seq = np.asarray(params_mu_seq, dtype=np.float64)
      params_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_mu_seq))

  pbe_f0 = lambda s: 1 + params_kappa * (1 - params_kappa / (params_kappa + params_mu * s ** 2))

  pbe_f = lambda x: pbe_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, pbe_f, rs, z, xs0, xs1)

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
  t20 = 6 ** (0.1e1 / 0.3e1)
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = t23 ** 2
  t25 = 0.1e1 / t24
  t27 = 2 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t30 = r0 ** 2
  t31 = t18 ** 2
  t37 = params.kappa + params.mu * t20 * t25 * s0 * t28 / t31 / t30 / 0.24e2
  t42 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t37)
  t46 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t17 * t18 * t42)
  t56 = params.kappa ** 2
  t59 = t37 ** 2
  t61 = 0.1e1 / t59 * params.mu
  t69 = f.my_piecewise3(t2, 0, -t6 * t17 / t31 * t42 / 0.8e1 + t6 * t17 / t18 / t30 / r0 * t56 * t61 * t20 * t25 * s0 * t28 / 0.24e2)
  vrho_0_ = 0.2e1 * r0 * t69 + 0.2e1 * t46
  t82 = f.my_piecewise3(t2, 0, -t6 * t17 / t18 / t30 * t56 * t61 * t20 * t25 * t28 / 0.64e2)
  vsigma_0_ = 0.2e1 * r0 * t82
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  r0 = r
  pol = pol_fxc(p, (r0/2, r0/2), (s/4 if s is not None else None, s/4 if s is not None else None, s/4 if s is not None else None), (None, None), (None, None))
  res = {}
  # Extract v2rho2 from polarized output
  v2rho2_pol = pol.get('v2rho2', None)
  if v2rho2_pol is not None:
    d11, d12, d22 = v2rho2_pol[..., 0], v2rho2_pol[..., 1], v2rho2_pol[..., 2]
    res['v2rho2'] = 0.25 * (d11 + 2*d12 + d22)
  # Extract v2rhosigma from polarized output
  v2rhosigma_pol = pol.get('v2rhosigma', None)
  if v2rhosigma_pol is not None:
    # Broadcast scalars to match array shape (Maple may emit some derivatives as scalar 0)
    d13 = jnp.asarray(v2rhosigma_pol[..., 0]) + jnp.zeros_like(r0)
    d14 = jnp.asarray(v2rhosigma_pol[..., 1]) + jnp.zeros_like(r0)
    d15 = jnp.asarray(v2rhosigma_pol[..., 2]) + jnp.zeros_like(r0)
    d23 = jnp.asarray(v2rhosigma_pol[..., 3]) + jnp.zeros_like(r0)
    d24 = jnp.asarray(v2rhosigma_pol[..., 4]) + jnp.zeros_like(r0)
    d25 = jnp.asarray(v2rhosigma_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2rhosigma'] = (1/8) * (d13 + d14 + d15 + d23 + d24 + d25)
  # Extract v2sigma2 from polarized output
  v2sigma2_pol = pol.get('v2sigma2', None)
  if v2sigma2_pol is not None:
    # Broadcast scalars to match array shape
    d33 = jnp.asarray(v2sigma2_pol[..., 0]) + jnp.zeros_like(r0)
    d34 = jnp.asarray(v2sigma2_pol[..., 1]) + jnp.zeros_like(r0)
    d35 = jnp.asarray(v2sigma2_pol[..., 2]) + jnp.zeros_like(r0)
    d44 = jnp.asarray(v2sigma2_pol[..., 3]) + jnp.zeros_like(r0)
    d45 = jnp.asarray(v2sigma2_pol[..., 4]) + jnp.zeros_like(r0)
    d55 = jnp.asarray(v2sigma2_pol[..., 5]) + jnp.zeros_like(r0)
    res['v2sigma2'] = (1/16) * (d33 + 2*d34 + 2*d35 + d44 + 2*d45 + d55)
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
  t23 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t33 = r0 ** 2
  t35 = 0.1e1 / t19 / t33
  t39 = params.kappa + params.mu * t23 * t28 * s0 * t31 * t35 / 0.24e2
  t44 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t39)
  t48 = t33 ** 2
  t52 = params.kappa ** 2
  t55 = t39 ** 2
  t61 = 0.1e1 / t55 * params.mu * t23 * t28 * s0 * t31
  t72 = params.mu ** 2
  t74 = t23 ** 2
  t78 = s0 ** 2
  t81 = 0.1e1 / t55 / t39 * t72 * t74 / t26 / t25 * t78 * t30
  t85 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t44 / 0.12e2 - t6 * t17 / t18 / t48 * t52 * t61 / 0.8e1 + t6 * t17 / t48 / t33 / r0 * t52 * t81 / 0.54e2)
  t99 = t48 ** 2
  t106 = t25 ** 2
  t115 = t55 ** 2
  t125 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t35 * t44 + 0.115e3 / 0.216e3 * t6 * t17 / t18 / t48 / r0 * t52 * t61 - 0.5e1 / 0.27e2 * t6 * t17 / t99 * t52 * t81 + 0.2e1 / 0.27e2 * t3 / t4 / t106 * t17 / t19 / t99 / t33 * t52 / t115 * t72 * params.mu * t78 * s0)
  v3rho3_0_ = 0.2e1 * r0 * t125 + 0.6e1 * t85

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
  t24 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t37 = params.kappa + params.mu * t24 * t29 * s0 * t32 * t22 / 0.24e2
  t42 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t37)
  t46 = t18 ** 2
  t51 = params.kappa ** 2
  t54 = t37 ** 2
  t60 = 0.1e1 / t54 * params.mu * t24 * t29 * s0 * t32
  t63 = t46 ** 2
  t70 = params.mu ** 2
  t72 = t24 ** 2
  t76 = s0 ** 2
  t79 = 0.1e1 / t54 / t37 * t70 * t72 / t27 / t26 * t76 * t31
  t82 = t26 ** 2
  t85 = t3 / t4 / t82
  t91 = t54 ** 2
  t97 = t51 / t91 * t70 * params.mu * t76 * s0
  t101 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t22 * t42 + 0.115e3 / 0.216e3 * t6 * t17 / t19 / t46 / r0 * t51 * t60 - 0.5e1 / 0.27e2 * t6 * t17 / t63 * t51 * t79 + 0.2e1 / 0.27e2 * t85 * t17 / t20 / t63 / t18 * t97)
  t103 = t18 * r0
  t110 = t46 * t18
  t140 = t70 ** 2
  t142 = t76 ** 2
  t150 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 / t20 / t103 * t42 - 0.305e3 / 0.108e3 * t6 * t17 / t19 / t110 * t51 * t60 + 0.835e3 / 0.486e3 * t6 * t17 / t63 / r0 * t51 * t79 - 0.124e3 / 0.81e2 * t85 * t17 / t20 / t63 / t103 * t97 + 0.8e1 / 0.243e3 * t85 * t17 / t19 / t63 / t110 * t51 / t91 / t37 * t140 * t142 * t24 * t29 * t32)
  v4rho4_0_ = 0.2e1 * r0 * t150 + 0.8e1 * t101

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
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = params.mu * t32
  t34 = jnp.pi ** 2
  t35 = t34 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = 0.1e1 / t36
  t38 = t37 * s0
  t39 = r0 ** 2
  t40 = r0 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t47 = params.kappa + t33 * t38 / t41 / t39 / 0.24e2
  t52 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t47)
  t56 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t57 = t56 * f.p.zeta_threshold
  t59 = f.my_piecewise3(t20, t57, t21 * t19)
  t60 = t30 ** 2
  t61 = 0.1e1 / t60
  t62 = t59 * t61
  t65 = t5 * t62 * t52 / 0.8e1
  t67 = params.kappa ** 2
  t69 = t5 * t59 * t30 * t67
  t70 = t47 ** 2
  t73 = 0.1e1 / t70 * params.mu * t32
  t74 = t39 * r0
  t78 = t73 * t38 / t41 / t74
  t82 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t52 - t65 + t69 * t78 / 0.24e2)
  t84 = r1 <= f.p.dens_threshold
  t85 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t86 = 0.1e1 + t85
  t87 = t86 <= f.p.zeta_threshold
  t88 = t86 ** (0.1e1 / 0.3e1)
  t90 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t93 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t88 * t90)
  t94 = t93 * t30
  t95 = t37 * s2
  t96 = r1 ** 2
  t97 = r1 ** (0.1e1 / 0.3e1)
  t98 = t97 ** 2
  t104 = params.kappa + t33 * t95 / t98 / t96 / 0.24e2
  t109 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t104)
  t114 = f.my_piecewise3(t87, t57, t88 * t86)
  t115 = t114 * t61
  t118 = t5 * t115 * t109 / 0.8e1
  t120 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t94 * t109 - t118)
  t122 = t21 ** 2
  t123 = 0.1e1 / t122
  t124 = t26 ** 2
  t129 = t16 / t22 / t6
  t131 = -0.2e1 * t23 + 0.2e1 * t129
  t132 = f.my_piecewise5(t10, 0, t14, 0, t131)
  t136 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t123 * t124 + 0.4e1 / 0.3e1 * t21 * t132)
  t143 = t5 * t29 * t61 * t52
  t150 = 0.1e1 / t60 / t6
  t154 = t5 * t59 * t150 * t52 / 0.12e2
  t157 = t5 * t62 * t67 * t78
  t161 = params.mu ** 2
  t163 = t32 ** 2
  t166 = 0.1e1 / t35 / t34
  t167 = s0 ** 2
  t169 = t39 ** 2
  t184 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t136 * t30 * t52 - t143 / 0.4e1 + t5 * t31 * t67 * t78 / 0.12e2 + t154 + t157 / 0.36e2 + t69 / t70 / t47 * t161 * t163 * t166 * t167 / t40 / t169 / t74 / 0.108e3 - 0.11e2 / 0.72e2 * t69 * t73 * t38 / t41 / t169)
  t185 = t88 ** 2
  t186 = 0.1e1 / t185
  t187 = t90 ** 2
  t191 = f.my_piecewise5(t14, 0, t10, 0, -t131)
  t195 = f.my_piecewise3(t87, 0, 0.4e1 / 0.9e1 * t186 * t187 + 0.4e1 / 0.3e1 * t88 * t191)
  t202 = t5 * t93 * t61 * t109
  t207 = t5 * t114 * t150 * t109 / 0.12e2
  t209 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t195 * t30 * t109 - t202 / 0.4e1 + t207)
  d11 = 0.2e1 * t82 + 0.2e1 * t120 + t6 * (t184 + t209)
  t212 = -t7 - t24
  t213 = f.my_piecewise5(t10, 0, t14, 0, t212)
  t216 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t213)
  t217 = t216 * t30
  t222 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t217 * t52 - t65)
  t224 = f.my_piecewise5(t14, 0, t10, 0, -t212)
  t227 = f.my_piecewise3(t87, 0, 0.4e1 / 0.3e1 * t88 * t224)
  t228 = t227 * t30
  t234 = t5 * t114 * t30 * t67
  t235 = t104 ** 2
  t238 = 0.1e1 / t235 * params.mu * t32
  t239 = t96 * r1
  t243 = t238 * t95 / t98 / t239
  t247 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t228 * t109 - t118 + t234 * t243 / 0.24e2)
  t251 = 0.2e1 * t129
  t252 = f.my_piecewise5(t10, 0, t14, 0, t251)
  t256 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t123 * t213 * t26 + 0.4e1 / 0.3e1 * t21 * t252)
  t263 = t5 * t216 * t61 * t52
  t272 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t256 * t30 * t52 - t263 / 0.8e1 + t5 * t217 * t67 * t78 / 0.24e2 - t143 / 0.8e1 + t154 + t157 / 0.72e2)
  t276 = f.my_piecewise5(t14, 0, t10, 0, -t251)
  t280 = f.my_piecewise3(t87, 0, 0.4e1 / 0.9e1 * t186 * t224 * t90 + 0.4e1 / 0.3e1 * t88 * t276)
  t287 = t5 * t227 * t61 * t109
  t296 = t5 * t115 * t67 * t243
  t299 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t280 * t30 * t109 - t287 / 0.8e1 - t202 / 0.8e1 + t207 + t5 * t94 * t67 * t243 / 0.24e2 + t296 / 0.72e2)
  d12 = t82 + t120 + t222 + t247 + t6 * (t272 + t299)
  t304 = t213 ** 2
  t308 = 0.2e1 * t23 + 0.2e1 * t129
  t309 = f.my_piecewise5(t10, 0, t14, 0, t308)
  t313 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t123 * t304 + 0.4e1 / 0.3e1 * t21 * t309)
  t320 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t313 * t30 * t52 - t263 / 0.4e1 + t154)
  t321 = t224 ** 2
  t325 = f.my_piecewise5(t14, 0, t10, 0, -t308)
  t329 = f.my_piecewise3(t87, 0, 0.4e1 / 0.9e1 * t186 * t321 + 0.4e1 / 0.3e1 * t88 * t325)
  t344 = s2 ** 2
  t346 = t96 ** 2
  t361 = f.my_piecewise3(t84, 0, -0.3e1 / 0.8e1 * t5 * t329 * t30 * t109 - t287 / 0.4e1 + t5 * t228 * t67 * t243 / 0.12e2 + t207 + t296 / 0.36e2 + t234 / t235 / t104 * t161 * t163 * t166 * t344 / t97 / t346 / t239 / 0.108e3 - 0.11e2 / 0.72e2 * t234 * t238 * t95 / t98 / t346)
  d22 = 0.2e1 * t222 + 0.2e1 * t247 + t6 * (t320 + t361)
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
  t28 = params.kappa ** 2
  t30 = t5 * t25 * t26 * t28
  t31 = 6 ** (0.1e1 / 0.3e1)
  t32 = params.mu * t31
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = 0.1e1 / t35
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t46 = params.kappa + t32 * t36 * s0 * t42 / 0.24e2
  t47 = t46 ** 2
  t49 = 0.1e1 / t47 * params.mu
  t50 = t31 * t36
  t52 = t49 * t50 * t42
  t55 = f.my_piecewise3(t1, 0, -t30 * t52 / 0.64e2)
  t56 = t6 ** 2
  t59 = t7 - t16 / t56
  t60 = f.my_piecewise5(t10, 0, t14, 0, t59)
  t63 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t60)
  t69 = t26 ** 2
  t70 = 0.1e1 / t69
  t78 = params.mu ** 2
  t80 = t31 ** 2
  t84 = t38 ** 2
  t101 = f.my_piecewise3(t1, 0, -t5 * t63 * t26 * t28 * t52 / 0.64e2 - t5 * t25 * t70 * t28 * t52 / 0.192e3 - t30 / t47 / t46 * t78 * t80 / t34 / t33 / t39 / t84 / t38 * s0 / 0.288e3 + t30 * t49 * t50 / t40 / t38 / r0 / 0.24e2)
  d13 = t6 * t101 + t55
  d14 = 0.0e0
  t103 = r1 <= f.p.dens_threshold
  t104 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t105 = 0.1e1 + t104
  t106 = t105 <= f.p.zeta_threshold
  t107 = t105 ** (0.1e1 / 0.3e1)
  t109 = f.my_piecewise3(t106, t22, t107 * t105)
  t114 = r1 ** 2
  t115 = r1 ** (0.1e1 / 0.3e1)
  t116 = t115 ** 2
  t118 = 0.1e1 / t116 / t114
  t123 = (params.kappa + t32 * t36 * s2 * t118 / 0.24e2) ** 2
  t127 = 0.1e1 / t123 * params.mu * t50 * t118
  t130 = f.my_piecewise3(t103, 0, -t5 * t109 * t26 * t28 * t127 / 0.64e2)
  t132 = f.my_piecewise5(t14, 0, t10, 0, -t59)
  t135 = f.my_piecewise3(t106, 0, 0.4e1 / 0.3e1 * t107 * t132)
  t147 = f.my_piecewise3(t103, 0, -t5 * t135 * t26 * t28 * t127 / 0.64e2 - t5 * t109 * t70 * t28 * t127 / 0.192e3)
  d15 = t6 * t147 + t130
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
  t28 = params.kappa ** 2
  t31 = 6 ** (0.1e1 / 0.3e1)
  t32 = params.mu * t31
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = 0.1e1 / t35
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t47 = (params.kappa + t32 * t36 * s0 * t42 / 0.24e2) ** 2
  t50 = t31 * t36
  t52 = 0.1e1 / t47 * params.mu * t50 * t42
  t55 = f.my_piecewise3(t1, 0, -t5 * t25 * t26 * t28 * t52 / 0.64e2)
  t56 = t6 ** 2
  t59 = -t7 - t16 / t56
  t60 = f.my_piecewise5(t10, 0, t14, 0, t59)
  t63 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t60)
  t69 = t26 ** 2
  t70 = 0.1e1 / t69
  t77 = f.my_piecewise3(t1, 0, -t5 * t63 * t26 * t28 * t52 / 0.64e2 - t5 * t25 * t70 * t28 * t52 / 0.192e3)
  d23 = t6 * t77 + t55
  d24 = 0.0e0
  t79 = r1 <= f.p.dens_threshold
  t80 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t81 = 0.1e1 + t80
  t82 = t81 <= f.p.zeta_threshold
  t83 = t81 ** (0.1e1 / 0.3e1)
  t85 = f.my_piecewise3(t82, t22, t83 * t81)
  t88 = t5 * t85 * t26 * t28
  t90 = r1 ** 2
  t91 = r1 ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t94 = 0.1e1 / t92 / t90
  t98 = params.kappa + t32 * t36 * s2 * t94 / 0.24e2
  t99 = t98 ** 2
  t101 = 0.1e1 / t99 * params.mu
  t103 = t101 * t50 * t94
  t106 = f.my_piecewise3(t79, 0, -t88 * t103 / 0.64e2)
  t108 = f.my_piecewise5(t14, 0, t10, 0, -t59)
  t111 = f.my_piecewise3(t82, 0, 0.4e1 / 0.3e1 * t83 * t108)
  t124 = params.mu ** 2
  t126 = t31 ** 2
  t130 = t90 ** 2
  t147 = f.my_piecewise3(t79, 0, -t5 * t111 * t26 * t28 * t103 / 0.64e2 - t5 * t85 * t70 * t28 * t103 / 0.192e3 - t88 / t99 / t98 * t124 * t126 / t34 / t33 / t91 / t130 / t90 * s2 / 0.288e3 + t88 * t101 * t50 / t92 / t90 / r1 / 0.24e2)
  d25 = t6 * t147 + t106
  t1 = r0 + r1
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 / t1
  t11 = f.p.zeta_threshold - 0.1e1
  t18 = f.my_piecewise5(0.2e1 * r0 * t7 <= f.p.zeta_threshold, t11, 0.2e1 * r1 * t7 <= f.p.zeta_threshold, -t11, (r0 - r1) * t7)
  t19 = 0.1e1 + t18
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t19 <= f.p.zeta_threshold, t21 * f.p.zeta_threshold, t23 * t19)
  t26 = t1 ** (0.1e1 / 0.3e1)
  t28 = params.kappa ** 2
  t31 = 6 ** (0.1e1 / 0.3e1)
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t46 = params.kappa + params.mu * t31 / t35 * s0 / t40 / t38 / 0.24e2
  t47 = t46 ** 2
  t50 = params.mu ** 2
  t52 = t31 ** 2
  t56 = t38 ** 2
  t64 = f.my_piecewise3(r0 <= f.p.dens_threshold, 0, t3 / t4 * t25 * t26 * t28 / t47 / t46 * t50 * t52 / t34 / t33 / t39 / t56 / r0 / 0.768e3)
  d33 = t1 * t64
  d34 = 0.0e0
  d35 = 0.0e0
  d44 = 0.0e0
  d45 = 0.0e0
  t1 = r0 + r1
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = 0.1e1 / t1
  t11 = f.p.zeta_threshold - 0.1e1
  t18 = f.my_piecewise5(0.2e1 * r1 * t7 <= f.p.zeta_threshold, t11, 0.2e1 * r0 * t7 <= f.p.zeta_threshold, -t11, -(r0 - r1) * t7)
  t19 = 0.1e1 + t18
  t21 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t19 ** (0.1e1 / 0.3e1)
  t25 = f.my_piecewise3(t19 <= f.p.zeta_threshold, t21 * f.p.zeta_threshold, t23 * t19)
  t26 = t1 ** (0.1e1 / 0.3e1)
  t28 = params.kappa ** 2
  t31 = 6 ** (0.1e1 / 0.3e1)
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t38 = r1 ** 2
  t39 = r1 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t46 = params.kappa + params.mu * t31 / t35 * s2 / t40 / t38 / 0.24e2
  t47 = t46 ** 2
  t50 = params.mu ** 2
  t52 = t31 ** 2
  t56 = t38 ** 2
  t64 = f.my_piecewise3(r1 <= f.p.dens_threshold, 0, t3 / t4 * t25 * t26 * t28 / t47 / t46 * t50 * t52 / t34 / t33 / t39 / t56 / r1 / 0.768e3)
  d55 = t1 * t64
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
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
  t44 = 6 ** (0.1e1 / 0.3e1)
  t45 = params.mu * t44
  t46 = jnp.pi ** 2
  t47 = t46 ** (0.1e1 / 0.3e1)
  t48 = t47 ** 2
  t49 = 0.1e1 / t48
  t50 = t49 * s0
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t59 = params.kappa + t45 * t50 / t53 / t51 / 0.24e2
  t64 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t59)
  t70 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t71 = t42 ** 2
  t72 = 0.1e1 / t71
  t73 = t70 * t72
  t78 = params.kappa ** 2
  t80 = t5 * t70 * t42 * t78
  t81 = t59 ** 2
  t84 = 0.1e1 / t81 * params.mu * t44
  t85 = t51 * r0
  t89 = t84 * t50 / t53 / t85
  t92 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t93 = t92 * f.p.zeta_threshold
  t95 = f.my_piecewise3(t20, t93, t21 * t19)
  t97 = 0.1e1 / t71 / t6
  t98 = t95 * t97
  t104 = t5 * t95 * t72 * t78
  t107 = t95 * t42
  t109 = t5 * t107 * t78
  t112 = params.mu ** 2
  t114 = t44 ** 2
  t115 = 0.1e1 / t81 / t59 * t112 * t114
  t118 = s0 ** 2
  t119 = 0.1e1 / t47 / t46 * t118
  t120 = t51 ** 2
  t125 = t115 * t119 / t52 / t120 / t85
  t131 = t84 * t50 / t53 / t120
  t135 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t64 - t5 * t73 * t64 / 0.4e1 + t80 * t89 / 0.12e2 + t5 * t98 * t64 / 0.12e2 + t104 * t89 / 0.36e2 + t109 * t125 / 0.108e3 - 0.11e2 / 0.72e2 * t109 * t131)
  t137 = r1 <= f.p.dens_threshold
  t138 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t139 = 0.1e1 + t138
  t140 = t139 <= f.p.zeta_threshold
  t141 = t139 ** (0.1e1 / 0.3e1)
  t142 = t141 ** 2
  t143 = 0.1e1 / t142
  t145 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t146 = t145 ** 2
  t150 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t154 = f.my_piecewise3(t140, 0, 0.4e1 / 0.9e1 * t143 * t146 + 0.4e1 / 0.3e1 * t141 * t150)
  t157 = r1 ** 2
  t158 = r1 ** (0.1e1 / 0.3e1)
  t159 = t158 ** 2
  t170 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + t45 * t49 * s2 / t159 / t157 / 0.24e2))
  t176 = f.my_piecewise3(t140, 0, 0.4e1 / 0.3e1 * t141 * t145)
  t182 = f.my_piecewise3(t140, t93, t141 * t139)
  t188 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t154 * t42 * t170 - t5 * t176 * t72 * t170 / 0.4e1 + t5 * t182 * t97 * t170 / 0.12e2)
  t201 = t120 ** 2
  t218 = t24 ** 2
  t222 = 0.6e1 * t33 - 0.6e1 * t16 / t218
  t223 = f.my_piecewise5(t10, 0, t14, 0, t222)
  t227 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t223)
  t249 = 0.1e1 / t71 / t24
  t254 = t46 ** 2
  t259 = t81 ** 2
  t277 = t104 * t125 / 0.108e3 + 0.77e2 / 0.108e3 * t109 * t84 * t50 / t53 / t120 / r0 - 0.11e2 / 0.72e2 * t104 * t131 - 0.11e2 / 0.108e3 * t109 * t115 * t119 / t52 / t201 - 0.11e2 / 0.24e2 * t80 * t131 - 0.3e1 / 0.8e1 * t5 * t227 * t42 * t64 + t5 * t43 * t78 * t89 / 0.8e1 + t5 * t73 * t78 * t89 / 0.12e2 - 0.3e1 / 0.8e1 * t5 * t41 * t72 * t64 + t5 * t70 * t97 * t64 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t95 * t249 * t64 + t2 / t3 / t254 * t107 * t78 / t259 * t112 * params.mu * t118 * s0 / t201 / t85 / 0.54e2 + t80 * t125 / 0.36e2 - t5 * t98 * t78 * t89 / 0.36e2
  t278 = f.my_piecewise3(t1, 0, t277)
  t288 = f.my_piecewise5(t14, 0, t10, 0, -t222)
  t292 = f.my_piecewise3(t140, 0, -0.8e1 / 0.27e2 / t142 / t139 * t146 * t145 + 0.4e1 / 0.3e1 * t143 * t145 * t150 + 0.4e1 / 0.3e1 * t141 * t288)
  t310 = f.my_piecewise3(t137, 0, -0.3e1 / 0.8e1 * t5 * t292 * t42 * t170 - 0.3e1 / 0.8e1 * t5 * t154 * t72 * t170 + t5 * t176 * t97 * t170 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t182 * t249 * t170)
  d111 = 0.3e1 * t135 + 0.3e1 * t188 + t6 * (t278 + t310)

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
  t26 = t6 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t29 = 0.1e1 / t27 / t6
  t31 = params.kappa ** 2
  t33 = t5 * t25 * t29 * t31
  t34 = 6 ** (0.1e1 / 0.3e1)
  t35 = params.mu * t34
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t39 * s0
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t49 = params.kappa + t35 * t40 / t43 / t41 / 0.24e2
  t50 = t49 ** 2
  t53 = 0.1e1 / t50 * params.mu * t34
  t54 = t41 * r0
  t58 = t53 * t40 / t43 / t54
  t61 = 0.1e1 / t27
  t62 = t25 * t61
  t64 = t5 * t62 * t31
  t67 = params.mu ** 2
  t69 = t34 ** 2
  t70 = 0.1e1 / t50 / t49 * t67 * t69
  t73 = s0 ** 2
  t74 = 0.1e1 / t37 / t36 * t73
  t75 = t41 ** 2
  t80 = t70 * t74 / t42 / t75 / t54
  t83 = t25 * t26
  t84 = t83 * t31
  t85 = t5 * t84
  t90 = t53 * t40 / t43 / t75 / r0
  t96 = t53 * t40 / t43 / t75
  t99 = t75 ** 2
  t103 = t70 * t74 / t42 / t99
  t106 = t6 ** 2
  t107 = 0.1e1 / t106
  t109 = -t16 * t107 + t7
  t110 = f.my_piecewise5(t10, 0, t14, 0, t109)
  t113 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t110)
  t114 = t113 * t26
  t116 = t5 * t114 * t31
  t119 = t23 ** 2
  t121 = 0.1e1 / t119 / t19
  t122 = t110 ** 2
  t126 = 0.1e1 / t119
  t127 = t126 * t110
  t128 = t106 * t6
  t129 = 0.1e1 / t128
  t132 = 0.2e1 * t16 * t129 - 0.2e1 * t107
  t133 = f.my_piecewise5(t10, 0, t14, 0, t132)
  t136 = t106 ** 2
  t137 = 0.1e1 / t136
  t140 = -0.6e1 * t16 * t137 + 0.6e1 * t129
  t141 = f.my_piecewise5(t10, 0, t14, 0, t140)
  t145 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t121 * t122 * t110 + 0.4e1 / 0.3e1 * t127 * t133 + 0.4e1 / 0.3e1 * t23 * t141)
  t146 = t145 * t26
  t151 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / t49)
  t160 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t126 * t122 + 0.4e1 / 0.3e1 * t23 * t133)
  t163 = t5 * t160 * t26 * t31
  t168 = t5 * t113 * t61 * t31
  t171 = t160 * t61
  t175 = t113 * t29
  t180 = 0.1e1 / t27 / t106
  t181 = t25 * t180
  t185 = t36 ** 2
  t188 = t2 / t3 / t185
  t189 = t188 * t83
  t190 = t50 ** 2
  t192 = t31 / t190
  t195 = t67 * params.mu * t73 * s0
  t199 = t192 * t195 / t99 / t54
  t204 = -t33 * t58 / 0.36e2 + t64 * t80 / 0.108e3 + 0.77e2 / 0.108e3 * t85 * t90 - 0.11e2 / 0.72e2 * t64 * t96 - 0.11e2 / 0.108e3 * t85 * t103 - 0.11e2 / 0.24e2 * t116 * t96 - 0.3e1 / 0.8e1 * t5 * t146 * t151 + t163 * t58 / 0.8e1 + t168 * t58 / 0.12e2 - 0.3e1 / 0.8e1 * t5 * t171 * t151 + t5 * t175 * t151 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t181 * t151 + t189 * t199 / 0.54e2 + t116 * t80 / 0.36e2
  t205 = f.my_piecewise3(t1, 0, t204)
  t207 = r1 <= f.p.dens_threshold
  t208 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t209 = 0.1e1 + t208
  t210 = t209 <= f.p.zeta_threshold
  t211 = t209 ** (0.1e1 / 0.3e1)
  t212 = t211 ** 2
  t214 = 0.1e1 / t212 / t209
  t216 = f.my_piecewise5(t14, 0, t10, 0, -t109)
  t217 = t216 ** 2
  t221 = 0.1e1 / t212
  t222 = t221 * t216
  t224 = f.my_piecewise5(t14, 0, t10, 0, -t132)
  t228 = f.my_piecewise5(t14, 0, t10, 0, -t140)
  t232 = f.my_piecewise3(t210, 0, -0.8e1 / 0.27e2 * t214 * t217 * t216 + 0.4e1 / 0.3e1 * t222 * t224 + 0.4e1 / 0.3e1 * t211 * t228)
  t235 = r1 ** 2
  t236 = r1 ** (0.1e1 / 0.3e1)
  t237 = t236 ** 2
  t248 = 0.1e1 + params.kappa * (0.1e1 - params.kappa / (params.kappa + t35 * t39 * s2 / t237 / t235 / 0.24e2))
  t257 = f.my_piecewise3(t210, 0, 0.4e1 / 0.9e1 * t221 * t217 + 0.4e1 / 0.3e1 * t211 * t224)
  t264 = f.my_piecewise3(t210, 0, 0.4e1 / 0.3e1 * t211 * t216)
  t270 = f.my_piecewise3(t210, t22, t211 * t209)
  t276 = f.my_piecewise3(t207, 0, -0.3e1 / 0.8e1 * t5 * t232 * t26 * t248 - 0.3e1 / 0.8e1 * t5 * t257 * t61 * t248 + t5 * t264 * t29 * t248 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t270 * t180 * t248)
  t283 = 0.1e1 / t27 / t128
  t288 = t19 ** 2
  t291 = t122 ** 2
  t297 = t133 ** 2
  t306 = -0.24e2 * t137 + 0.24e2 * t16 / t136 / t6
  t307 = f.my_piecewise5(t10, 0, t14, 0, t306)
  t311 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t119 / t288 * t291 - 0.16e2 / 0.9e1 * t121 * t122 * t133 + 0.4e1 / 0.3e1 * t126 * t297 + 0.16e2 / 0.9e1 * t127 * t141 + 0.4e1 / 0.3e1 * t23 * t307)
  t342 = -0.5e1 / 0.9e1 * t5 * t113 * t180 * t151 + 0.10e2 / 0.27e2 * t5 * t25 * t283 * t151 - 0.3e1 / 0.8e1 * t5 * t311 * t26 * t151 - t5 * t145 * t61 * t151 / 0.2e1 + t5 * t160 * t29 * t151 / 0.2e1 - 0.11e2 / 0.18e2 * t168 * t96 - 0.11e2 / 0.27e2 * t116 * t103 - 0.11e2 / 0.12e2 * t163 * t96 + t5 * t146 * t31 * t58 / 0.6e1 - t5 * t175 * t31 * t58 / 0.9e1 - t33 * t80 / 0.81e2 + t168 * t80 / 0.27e2
  t347 = t75 * t41
  t369 = t67 ** 2
  t371 = t73 ** 2
  t402 = t5 * t171 * t31 * t58 / 0.6e1 - 0.1309e4 / 0.324e3 * t85 * t53 * t40 / t43 / t347 + 0.11e2 / 0.54e2 * t33 * t96 - 0.11e2 / 0.81e2 * t64 * t103 + 0.77e2 / 0.81e2 * t64 * t90 + 0.5e1 / 0.81e2 * t5 * t181 * t31 * t58 + t163 * t80 / 0.18e2 + 0.2e1 / 0.243e3 * t188 * t84 / t190 / t49 * t369 * t371 / t43 / t99 / t347 * t34 * t39 + 0.77e2 / 0.27e2 * t116 * t90 + 0.979e3 / 0.972e3 * t85 * t70 * t74 / t42 / t99 / r0 + 0.2e1 / 0.81e2 * t188 * t62 * t199 - 0.11e2 / 0.27e2 * t189 * t192 * t195 / t99 / t75 + 0.2e1 / 0.27e2 * t188 * t114 * t199
  t404 = f.my_piecewise3(t1, 0, t342 + t402)
  t405 = t209 ** 2
  t408 = t217 ** 2
  t414 = t224 ** 2
  t420 = f.my_piecewise5(t14, 0, t10, 0, -t306)
  t424 = f.my_piecewise3(t210, 0, 0.40e2 / 0.81e2 / t212 / t405 * t408 - 0.16e2 / 0.9e1 * t214 * t217 * t224 + 0.4e1 / 0.3e1 * t221 * t414 + 0.16e2 / 0.9e1 * t222 * t228 + 0.4e1 / 0.3e1 * t211 * t420)
  t446 = f.my_piecewise3(t207, 0, -0.3e1 / 0.8e1 * t5 * t424 * t26 * t248 - t5 * t232 * t61 * t248 / 0.2e1 + t5 * t257 * t29 * t248 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t264 * t180 * t248 + 0.10e2 / 0.27e2 * t5 * t270 * t283 * t248)
  d1111 = 0.4e1 * t205 + 0.4e1 * t276 + t6 * (t404 + t446)

  res = {'v4rho4': d1111}
  return res