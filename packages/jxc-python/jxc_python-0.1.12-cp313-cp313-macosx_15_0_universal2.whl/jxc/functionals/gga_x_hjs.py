"""Generated from gga_x_hjs.mpl."""

import functools
import jax
import jax.lax as lax
import jax.numpy as jnp
import numpy as np
from jax.numpy import array as array
from jax.numpy import int32 as int32
from jax.numpy import nan as nan
from typing import Callable, Optional
from jxc.functionals.utils import *

def _pol_impl(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
      f.xt(r0, r1, s0, s1, s2),
      f.xs0(r0, r1, s0, s2),
      f.xs1(r0, r1, s0, s2),
  )
  return res

def _unpol_impl(p, r, s=None, l=None, tau=None):
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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
      f.xt(r0 / 2, r0 / 2, s0 / 4, s0 / 4, s0 / 4),
      f.xs0(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
      f.xs1(r0 / 2, r0 / 2, s0 / 4, s0 / 4),
  )
  return res


def _normalize_sigma_tuple(sig):
  if sig is None:
    return (None, None, None)
  return sig


def _normalize_lapl_tuple(lapl):
  if lapl is None:
    return (None, None)
  return lapl


def _normalize_tau_tuple(tau):
  if tau is None:
    return (None, None)
  return tau


@functools.partial(jax.custom_vjp, nondiff_argnums=(0,))
def pol(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  return _pol_impl(p, r, s, l, tau)


def _pol_fwd(p, r, s, l, tau):
  res = _pol_impl(p, r, s, l, tau)
  vxc = pol_vxc(p, r, _normalize_sigma_tuple(s), _normalize_lapl_tuple(l), _normalize_tau_tuple(tau))
  return res, (res, vxc, r)


def _pol_bwd(p_args, residual, g):
  res, vxc, r_vals = residual
  g_arr = jnp.asarray(g, dtype=jnp.float64)
  r0, r1 = r_vals
  rho_tot = jnp.asarray(r0 + r1, dtype=jnp.float64)
  rho_safe = jnp.where(rho_tot == 0.0, 1.0, rho_tot)
  vrho = jnp.asarray(vxc.get("vrho"), dtype=jnp.float64)
  deps_dr0 = (vrho[..., 0] - res) / rho_safe
  deps_dr1 = (vrho[..., 1] - res) / rho_safe
  grad_r = (g_arr * deps_dr0, g_arr * deps_dr1)
  vsigma = vxc.get("vsigma")
  if vsigma is not None:
    vs = jnp.asarray(vsigma, dtype=jnp.float64)
    grad_s = tuple(g_arr * vs[..., i] / rho_safe for i in range(vs.shape[-1]))
  else:
    grad_s = (None, None, None)
  vlapl = vxc.get("vlapl")
  if vlapl is not None:
    vl = jnp.asarray(vlapl, dtype=jnp.float64)
    grad_l = (g_arr * vl[..., 0] / rho_safe, g_arr * vl[..., 1] / rho_safe)
  else:
    grad_l = (None, None)
  vtau = vxc.get("vtau")
  if vtau is not None:
    vt = jnp.asarray(vtau, dtype=jnp.float64)
    grad_tau = (g_arr * vt[..., 0] / rho_safe, g_arr * vt[..., 1] / rho_safe)
  else:
    grad_tau = (None, None)
  return (grad_r, grad_s, grad_l, grad_tau)


pol.defvjp(_pol_fwd, _pol_bwd)


@functools.partial(jax.custom_vjp, nondiff_argnums=(0,))
def unpol(p, r, s=None, l=None, tau=None):
  return _unpol_impl(p, r, s, l, tau)


def _unpol_fwd(p, r, s, l, tau):
  res = _unpol_impl(p, r, s, l, tau)
  vxc = unpol_vxc(p, r, s, l, tau)
  return res, (res, vxc, r)


def _unpol_bwd(p_args, residual, g):
  res, vxc, rho_val = residual
  g_arr = jnp.asarray(g, dtype=jnp.float64)
  rho_safe = jnp.where(rho_val == 0.0, 1.0, rho_val)
  vrho = jnp.asarray(vxc.get("vrho"), dtype=jnp.float64)
  deps_drho = (vrho - res) / rho_safe
  grad_r = g_arr * deps_drho
  vsigma = vxc.get("vsigma")
  grad_s = g_arr * jnp.asarray(vsigma, dtype=jnp.float64) / rho_safe if vsigma is not None else None
  vlapl = vxc.get("vlapl")
  grad_l = g_arr * jnp.asarray(vlapl, dtype=jnp.float64) / rho_safe if vlapl is not None else None
  vtau = vxc.get("vtau")
  grad_tau = g_arr * jnp.asarray(vtau, dtype=jnp.float64) / rho_safe if vtau is not None else None
  return (grad_r, grad_s, grad_l, grad_tau)


unpol.defvjp(_unpol_fwd, _unpol_bwd)

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

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
  t28 = t2 ** 2
  t29 = f.p.cam_omega * t28
  t30 = jnp.pi ** 2
  t31 = t30 ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t35 = 0.1e1 + t17 <= f.p.zeta_threshold
  t37 = 0.1e1 - t17 <= f.p.zeta_threshold
  t38 = f.my_piecewise5(t35, t11, t37, t15, t17)
  t39 = 0.1e1 + t38
  t40 = t39 <= f.p.zeta_threshold
  t41 = t39 ** (0.1e1 / 0.3e1)
  t42 = f.my_piecewise3(t40, t21, t41)
  t43 = 0.1e1 / t42
  t44 = 0.1e1 / t26
  t45 = t43 * t44
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = t31 ** 2
  t48 = 0.1e1 / t47
  t49 = t46 * t48
  t50 = t49 * s0
  t51 = r0 ** 2
  t52 = r0 ** (0.1e1 / 0.3e1)
  t53 = t52 ** 2
  t55 = 0.1e1 / t53 / t51
  t57 = params.a[0] * t46
  t58 = t48 * s0
  t59 = t58 * t55
  t63 = 0.1e1 / t30
  t64 = params.a[1] * t63
  t65 = jnp.sqrt(s0)
  t66 = t65 * s0
  t67 = t51 ** 2
  t68 = 0.1e1 / t67
  t69 = t66 * t68
  t73 = t46 ** 2
  t74 = params.a[2] * t73
  t76 = 0.1e1 / t31 / t30
  t77 = s0 ** 2
  t78 = t76 * t77
  t79 = t67 * r0
  t81 = 0.1e1 / t52 / t79
  t82 = t78 * t81
  t86 = params.a[3] * t46
  t88 = 0.1e1 / t47 / t30
  t89 = t65 * t77
  t90 = t88 * t89
  t91 = t67 * t51
  t93 = 0.1e1 / t53 / t91
  t94 = t90 * t93
  t98 = t30 ** 2
  t99 = 0.1e1 / t98
  t100 = params.a[4] * t99
  t101 = t77 * s0
  t102 = t67 ** 2
  t103 = 0.1e1 / t102
  t104 = t101 * t103
  t108 = params.a[5] * t73
  t110 = 0.1e1 / t31 / t98
  t111 = t65 * t101
  t112 = t110 * t111
  t113 = t102 * r0
  t115 = 0.1e1 / t52 / t113
  t116 = t112 * t115
  t119 = t57 * t59 / 0.24e2 + t64 * t69 / 0.48e2 + t74 * t82 / 0.576e3 + t86 * t94 / 0.1152e4 + t100 * t104 / 0.2304e4 + t108 * t116 / 0.27648e5
  t120 = t55 * t119
  t122 = params.b[0] * t73
  t123 = t32 * t65
  t125 = 0.1e1 / t52 / r0
  t130 = params.b[1] * t46
  t134 = params.b[2] * t63
  t138 = params.b[3] * t73
  t142 = params.b[4] * t46
  t146 = params.b[5] * t99
  t150 = params.b[6] * t73
  t154 = params.b[7] * t46
  t156 = 0.1e1 / t47 / t98
  t157 = t77 ** 2
  t158 = t156 * t157
  t159 = t102 * t51
  t161 = 0.1e1 / t53 / t159
  t168 = params.b[8] / t98 / t30
  t169 = t65 * t157
  t171 = 0.1e1 / t102 / t67
  t175 = 0.1e1 + t122 * t123 * t125 / 0.12e2 + t130 * t59 / 0.24e2 + t134 * t69 / 0.48e2 + t138 * t82 / 0.576e3 + t142 * t94 / 0.1152e4 + t146 * t104 / 0.2304e4 + t150 * t116 / 0.27648e5 + t154 * t158 * t161 / 0.55296e5 + t168 * t169 * t171 / 0.110592e6
  t176 = 0.1e1 / t175
  t177 = t120 * t176
  t179 = t50 * t177 / 0.24e2
  t180 = 0.1e-9 < t179
  t181 = f.my_piecewise3(t180, t179, 0.1e-9)
  t182 = f.p.cam_omega ** 2
  t183 = t182 * t2
  t184 = t42 ** 2
  t185 = 0.1e1 / t184
  t186 = t48 * t185
  t187 = t26 ** 2
  t188 = 0.1e1 / t187
  t190 = t183 * t186 * t188
  t192 = 0.609650e0 + t181 + t190 / 0.3e1
  t193 = jnp.sqrt(t192)
  t194 = 0.1e1 / t193
  t196 = t33 * t45 * t194
  t198 = -0.47272888888888888888888888888888888888888888888889e-1 + 0.15757629629629629629629629629629629629629629629630e-1 * t196
  t199 = 0.609650e0 + t181
  t200 = 0.1e1 / t199
  t202 = s0 * t55
  t205 = -0.3203523e1 - 0.33370031250000000000000000000000000000000000000000e-1 * t49 * t202
  t206 = 0.1e1 / t205
  t208 = t49 * t202 * t206
  t211 = -0.26366444444444444444444444444444444444444444444444e-1 + 0.10986018518518518518518518518518518518518518518518e-2 * t208 - 0.11111111111111111111111111111111111111111111111111e0 * t181
  t213 = t182 * f.p.cam_omega * t63
  t215 = 0.1e1 / t184 / t42
  t218 = 0.1e1 / t193 / t192
  t220 = t213 * t215 * t7 * t218
  t222 = 0.2e1 - t196 + t220 / 0.3e1
  t223 = t211 * t222
  t224 = t199 ** 2
  t225 = 0.1e1 / t224
  t229 = -0.47459600000000000000000000000000000000000000000000e-1 + 0.19774833333333333333333333333333333333333333333333e-2 * t208 - 0.20000000000000000000000000000000000000000000000000e0 * t181
  t233 = t224 * t199
  t235 = jnp.sqrt(t199)
  t236 = t235 * t233
  t237 = jnp.sqrt(jnp.pi)
  t238 = 0.4e1 / 0.5e1 * t237
  t239 = jnp.sqrt(t181)
  t242 = 0.0e0 < 0.7572109999e0 + t181
  t244 = f.my_piecewise3(t242, 0.757211e0 + t181, 0.1e-9)
  t245 = jnp.sqrt(t244)
  t247 = t238 + 0.12e2 / 0.5e1 * t239 - 0.12e2 / 0.5e1 * t245
  t250 = -t229 * t199 / 0.9e1 + 0.31515259259259259259259259259259259259259259259259e-2 * t224 - 0.10096146666666666666666666666666666666666666666667e0 * t233 - t236 * t247 / 0.9e1
  t253 = t182 ** 2
  t256 = t253 * f.p.cam_omega * t2 * t88
  t257 = t184 ** 2
  t259 = 0.1e1 / t257 / t42
  t261 = 0.1e1 / t187 / t6
  t262 = t259 * t261
  t263 = t192 ** 2
  t265 = 0.1e1 / t193 / t263
  t269 = 0.8e1 - 0.5e1 * t196 + 0.10e2 / 0.3e1 * t220 - t256 * t262 * t265 / 0.3e1
  t270 = t250 * t269
  t271 = 0.1e1 / t233
  t274 = 0.3e1 * t190
  t276 = jnp.sqrt(0.9e1 * t181 + t274)
  t279 = jnp.sqrt(0.9e1 * t244 + t274)
  t281 = t276 / 0.3e1 - t279 / 0.3e1
  t285 = t32 * t43
  t287 = t29 * t285 * t44
  t289 = t287 / 0.3e1 + t276 / 0.3e1
  t291 = t287 / 0.3e1 + t193
  t292 = 0.1e1 / t291
  t294 = jnp.log(t289 * t292)
  t298 = t287 / 0.3e1 + t279 / 0.3e1
  t300 = jnp.log(t298 * t292)
  t303 = 0.757211e0 - t198 * t200 - t223 * t225 - t270 * t271 + 0.2e1 / 0.3e1 * t33 * t45 * t281 + 0.2e1 * t181 * t294 - 0.2e1 * t244 * t300
  t307 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t303)
  t308 = r1 <= f.p.dens_threshold
  t309 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t310 = 0.1e1 + t309
  t311 = t310 <= f.p.zeta_threshold
  t312 = t310 ** (0.1e1 / 0.3e1)
  t314 = f.my_piecewise3(t311, t22, t312 * t310)
  t315 = t314 * t26
  t316 = f.my_piecewise5(t37, t11, t35, t15, -t17)
  t317 = 0.1e1 + t316
  t318 = t317 <= f.p.zeta_threshold
  t319 = t317 ** (0.1e1 / 0.3e1)
  t320 = f.my_piecewise3(t318, t21, t319)
  t321 = 0.1e1 / t320
  t322 = t321 * t44
  t323 = t49 * s2
  t324 = r1 ** 2
  t325 = r1 ** (0.1e1 / 0.3e1)
  t326 = t325 ** 2
  t328 = 0.1e1 / t326 / t324
  t329 = t48 * s2
  t330 = t329 * t328
  t333 = jnp.sqrt(s2)
  t334 = t333 * s2
  t335 = t324 ** 2
  t336 = 0.1e1 / t335
  t337 = t334 * t336
  t340 = s2 ** 2
  t341 = t76 * t340
  t342 = t335 * r1
  t344 = 0.1e1 / t325 / t342
  t345 = t341 * t344
  t348 = t333 * t340
  t349 = t88 * t348
  t350 = t335 * t324
  t352 = 0.1e1 / t326 / t350
  t353 = t349 * t352
  t356 = t340 * s2
  t357 = t335 ** 2
  t358 = 0.1e1 / t357
  t359 = t356 * t358
  t362 = t333 * t356
  t363 = t110 * t362
  t364 = t357 * r1
  t366 = 0.1e1 / t325 / t364
  t367 = t363 * t366
  t370 = t57 * t330 / 0.24e2 + t64 * t337 / 0.48e2 + t74 * t345 / 0.576e3 + t86 * t353 / 0.1152e4 + t100 * t359 / 0.2304e4 + t108 * t367 / 0.27648e5
  t371 = t328 * t370
  t372 = t32 * t333
  t374 = 0.1e1 / t325 / r1
  t390 = t340 ** 2
  t391 = t156 * t390
  t392 = t357 * t324
  t394 = 0.1e1 / t326 / t392
  t398 = t333 * t390
  t400 = 0.1e1 / t357 / t335
  t404 = 0.1e1 + t122 * t372 * t374 / 0.12e2 + t130 * t330 / 0.24e2 + t134 * t337 / 0.48e2 + t138 * t345 / 0.576e3 + t142 * t353 / 0.1152e4 + t146 * t359 / 0.2304e4 + t150 * t367 / 0.27648e5 + t154 * t391 * t394 / 0.55296e5 + t168 * t398 * t400 / 0.110592e6
  t405 = 0.1e1 / t404
  t406 = t371 * t405
  t408 = t323 * t406 / 0.24e2
  t409 = 0.1e-9 < t408
  t410 = f.my_piecewise3(t409, t408, 0.1e-9)
  t411 = t320 ** 2
  t412 = 0.1e1 / t411
  t413 = t48 * t412
  t415 = t183 * t413 * t188
  t417 = 0.609650e0 + t410 + t415 / 0.3e1
  t418 = jnp.sqrt(t417)
  t419 = 0.1e1 / t418
  t421 = t33 * t322 * t419
  t423 = -0.47272888888888888888888888888888888888888888888889e-1 + 0.15757629629629629629629629629629629629629629629630e-1 * t421
  t424 = 0.609650e0 + t410
  t425 = 0.1e1 / t424
  t427 = s2 * t328
  t430 = -0.3203523e1 - 0.33370031250000000000000000000000000000000000000000e-1 * t49 * t427
  t431 = 0.1e1 / t430
  t433 = t49 * t427 * t431
  t436 = -0.26366444444444444444444444444444444444444444444444e-1 + 0.10986018518518518518518518518518518518518518518518e-2 * t433 - 0.11111111111111111111111111111111111111111111111111e0 * t410
  t438 = 0.1e1 / t411 / t320
  t441 = 0.1e1 / t418 / t417
  t443 = t213 * t438 * t7 * t441
  t445 = 0.2e1 - t421 + t443 / 0.3e1
  t446 = t436 * t445
  t447 = t424 ** 2
  t448 = 0.1e1 / t447
  t452 = -0.47459600000000000000000000000000000000000000000000e-1 + 0.19774833333333333333333333333333333333333333333333e-2 * t433 - 0.20000000000000000000000000000000000000000000000000e0 * t410
  t456 = t447 * t424
  t458 = jnp.sqrt(t424)
  t459 = t458 * t456
  t460 = jnp.sqrt(t410)
  t463 = 0.0e0 < 0.7572109999e0 + t410
  t465 = f.my_piecewise3(t463, 0.757211e0 + t410, 0.1e-9)
  t466 = jnp.sqrt(t465)
  t468 = t238 + 0.12e2 / 0.5e1 * t460 - 0.12e2 / 0.5e1 * t466
  t471 = -t452 * t424 / 0.9e1 + 0.31515259259259259259259259259259259259259259259259e-2 * t447 - 0.10096146666666666666666666666666666666666666666667e0 * t456 - t459 * t468 / 0.9e1
  t474 = t411 ** 2
  t476 = 0.1e1 / t474 / t320
  t477 = t476 * t261
  t478 = t417 ** 2
  t480 = 0.1e1 / t418 / t478
  t484 = 0.8e1 - 0.5e1 * t421 + 0.10e2 / 0.3e1 * t443 - t256 * t477 * t480 / 0.3e1
  t485 = t471 * t484
  t486 = 0.1e1 / t456
  t489 = 0.3e1 * t415
  t491 = jnp.sqrt(0.9e1 * t410 + t489)
  t494 = jnp.sqrt(0.9e1 * t465 + t489)
  t496 = t491 / 0.3e1 - t494 / 0.3e1
  t500 = t32 * t321
  t502 = t29 * t500 * t44
  t504 = t502 / 0.3e1 + t491 / 0.3e1
  t506 = t502 / 0.3e1 + t418
  t507 = 0.1e1 / t506
  t509 = jnp.log(t504 * t507)
  t513 = t502 / 0.3e1 + t494 / 0.3e1
  t515 = jnp.log(t513 * t507)
  t518 = 0.757211e0 - t423 * t425 - t446 * t448 - t485 * t486 + 0.2e1 / 0.3e1 * t33 * t322 * t496 + 0.2e1 * t410 * t509 - 0.2e1 * t465 * t515
  t522 = f.my_piecewise3(t308, 0, -0.3e1 / 0.8e1 * t5 * t315 * t518)
  t523 = t6 ** 2
  t524 = 0.1e1 / t523
  t525 = t16 * t524
  t526 = t7 - t525
  t527 = f.my_piecewise5(t10, 0, t14, 0, t526)
  t530 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t527)
  t538 = t5 * t25 * t188 * t303 / 0.8e1
  t539 = t185 * t44
  t540 = t41 ** 2
  t541 = 0.1e1 / t540
  t542 = f.my_piecewise5(t35, 0, t37, 0, t526)
  t545 = f.my_piecewise3(t40, 0, t541 * t542 / 0.3e1)
  t548 = t33 * t539 * t194 * t545
  t551 = 0.1e1 / t26 / t6
  t552 = t43 * t551
  t554 = t33 * t552 * t194
  t555 = 0.52525432098765432098765432098765432098765432098767e-2 * t554
  t556 = t51 * r0
  t558 = 0.1e1 / t53 / t556
  t563 = t58 * t558
  t567 = t66 / t79
  t571 = 0.1e1 / t52 / t91
  t572 = t78 * t571
  t578 = t90 / t53 / t67 / t556
  t582 = t101 / t113
  t587 = t112 / t52 / t159
  t595 = t175 ** 2
  t596 = 0.1e1 / t595
  t631 = f.my_piecewise3(t180, -t50 * t558 * t119 * t176 / 0.9e1 + t50 * t55 * (-t57 * t563 / 0.9e1 - t64 * t567 / 0.12e2 - t74 * t572 / 0.108e3 - 0.5e1 / 0.864e3 * t86 * t578 - t100 * t582 / 0.288e3 - 0.7e1 / 0.20736e5 * t108 * t587) * t176 / 0.24e2 - t50 * t120 * t596 * (-t122 * t123 / t52 / t51 / 0.9e1 - t130 * t563 / 0.9e1 - t134 * t567 / 0.12e2 - t138 * t572 / 0.108e3 - 0.5e1 / 0.864e3 * t142 * t578 - t146 * t582 / 0.288e3 - 0.7e1 / 0.20736e5 * t150 * t587 - t154 * t158 / t53 / t102 / t556 / 0.5184e4 - t168 * t169 / t102 / t79 / 0.9216e4) / 0.24e2, 0)
  t632 = t183 * t48
  t633 = t215 * t188
  t635 = t632 * t633 * t545
  t638 = t183 * t186 * t261
  t639 = 0.2e1 / 0.9e1 * t638
  t640 = t631 - 0.2e1 / 0.3e1 * t635 - t639
  t643 = t33 * t45 * t218 * t640
  t647 = t198 * t225
  t651 = t49 * s0 * t558 * t206
  t653 = t73 * t76
  t655 = t205 ** 2
  t656 = 0.1e1 / t655
  t658 = t653 * t77 * t571 * t656
  t664 = t554 / 0.3e1
  t667 = t213 / t257
  t668 = t7 * t218
  t670 = t667 * t668 * t545
  t673 = t213 * t215 * t524 * t218
  t674 = t673 / 0.3e1
  t675 = t213 * t215
  t676 = t7 * t265
  t678 = t675 * t676 * t640
  t699 = t235 * t224 * t247
  t702 = 0.1e1 / t239
  t704 = 0.1e1 / t245
  t705 = f.my_piecewise3(t242, t631, 0)
  t715 = 0.5e1 / 0.3e1 * t554
  t718 = 0.10e2 / 0.3e1 * t673
  t722 = 0.1e1 / t257 / t184 * t261
  t728 = 0.1e1 / t187 / t523
  t732 = 0.5e1 / 0.9e1 * t256 * t259 * t728 * t265
  t735 = 0.1e1 / t193 / t263 / t192
  t743 = t224 ** 2
  t744 = 0.1e1 / t743
  t754 = 0.2e1 / 0.9e1 * t33 * t552 * t281
  t755 = 0.1e1 / t276
  t757 = 0.6e1 * t635
  t758 = 0.2e1 * t638
  t760 = t755 * (0.9e1 * t631 - t757 - t758)
  t761 = 0.1e1 / t279
  t764 = t761 * (0.9e1 * t705 - t757 - t758)
  t774 = t33 * t539 * t545 / 0.3e1
  t777 = t29 * t285 * t551 / 0.9e1
  t781 = t291 ** 2
  t782 = 0.1e1 / t781
  t783 = t289 * t782
  t786 = -t774 - t777 + t194 * t640 / 0.2e1
  t791 = 0.1e1 / t289 * t291
  t799 = t298 * t782
  t804 = 0.1e1 / t298 * t291
  t807 = -(-0.15757629629629629629629629629629629629629629629630e-1 * t548 - t555 - 0.78788148148148148148148148148148148148148148148150e-2 * t643) * t200 + t647 * t631 - (-0.29296049382716049382716049382716049382716049382715e-2 * t651 - 0.97761008340277777777777777777777777777777777777773e-4 * t658 - 0.11111111111111111111111111111111111111111111111111e0 * t631) * t222 * t225 - t211 * (t548 + t664 + t643 / 0.2e1 - t670 - t674 - t678 / 0.2e1) * t225 + 0.2e1 * t223 * t271 * t631 - (-(-0.52732888888888888888888888888888888888888888888888e-2 * t651 - 0.17596981501250000000000000000000000000000000000000e-3 * t658 - 0.20000000000000000000000000000000000000000000000000e0 * t631) * t199 / 0.9e1 - t229 * t631 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t199 * t631 - 0.30288440000000000000000000000000000000000000000001e0 * t224 * t631 - 0.7e1 / 0.18e2 * t699 * t631 - t236 * (0.6e1 / 0.5e1 * t702 * t631 - 0.6e1 / 0.5e1 * t704 * t705) / 0.9e1) * t269 * t271 - t250 * (0.5e1 * t548 + t715 + 0.5e1 / 0.2e1 * t643 - 0.10e2 * t670 - t718 - 0.5e1 * t678 + 0.5e1 / 0.3e1 * t256 * t722 * t265 * t545 + t732 + 0.5e1 / 0.6e1 * t256 * t262 * t735 * t640) * t271 + 0.3e1 * t270 * t744 * t631 - 0.2e1 / 0.3e1 * t33 * t539 * t281 * t545 - t754 + 0.2e1 / 0.3e1 * t33 * t45 * (t760 / 0.6e1 - t764 / 0.6e1) + 0.2e1 * t631 * t294 + 0.2e1 * t181 * ((-t774 - t777 + t760 / 0.6e1) * t292 - t783 * t786) * t791 - 0.2e1 * t705 * t300 - 0.2e1 * t244 * ((-t774 - t777 + t764 / 0.6e1) * t292 - t799 * t786) * t804
  t812 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t530 * t26 * t303 - t538 - 0.3e1 / 0.8e1 * t5 * t27 * t807)
  t813 = -t526
  t814 = f.my_piecewise5(t14, 0, t10, 0, t813)
  t817 = f.my_piecewise3(t311, 0, 0.4e1 / 0.3e1 * t312 * t814)
  t825 = t5 * t314 * t188 * t518 / 0.8e1
  t826 = t412 * t44
  t827 = t319 ** 2
  t828 = 0.1e1 / t827
  t829 = f.my_piecewise5(t37, 0, t35, 0, t813)
  t832 = f.my_piecewise3(t318, 0, t828 * t829 / 0.3e1)
  t835 = t33 * t826 * t419 * t832
  t837 = t321 * t551
  t839 = t33 * t837 * t419
  t840 = 0.52525432098765432098765432098765432098765432098767e-2 * t839
  t841 = t438 * t188
  t843 = t632 * t841 * t832
  t846 = t183 * t413 * t261
  t847 = 0.2e1 / 0.9e1 * t846
  t848 = -0.2e1 / 0.3e1 * t843 - t847
  t851 = t33 * t322 * t441 * t848
  t855 = t839 / 0.3e1
  t858 = t213 / t474
  t859 = t7 * t441
  t861 = t858 * t859 * t832
  t864 = t213 * t438 * t524 * t441
  t865 = t864 / 0.3e1
  t866 = t213 * t438
  t867 = t7 * t480
  t869 = t866 * t867 * t848
  t875 = 0.5e1 / 0.3e1 * t839
  t878 = 0.10e2 / 0.3e1 * t864
  t882 = 0.1e1 / t474 / t411 * t261
  t890 = 0.5e1 / 0.9e1 * t256 * t476 * t728 * t480
  t893 = 0.1e1 / t418 / t478 / t417
  t907 = 0.2e1 / 0.9e1 * t33 * t837 * t496
  t908 = 0.1e1 / t491
  t910 = 0.2e1 * t846
  t911 = -0.6e1 * t843 - t910
  t912 = t908 * t911
  t913 = 0.1e1 / t494
  t914 = t913 * t911
  t922 = t33 * t826 * t832 / 0.3e1
  t925 = t29 * t500 * t551 / 0.9e1
  t929 = t506 ** 2
  t930 = 0.1e1 / t929
  t931 = t504 * t930
  t934 = -t922 - t925 + t419 * t848 / 0.2e1
  t939 = 0.1e1 / t504 * t506
  t945 = t513 * t930
  t950 = 0.1e1 / t513 * t506
  t958 = f.my_piecewise3(t308, 0, -0.3e1 / 0.8e1 * t5 * t817 * t26 * t518 - t825 - 0.3e1 / 0.8e1 * t5 * t315 * (-(-0.15757629629629629629629629629629629629629629629630e-1 * t835 - t840 - 0.78788148148148148148148148148148148148148148148150e-2 * t851) * t425 - t436 * (t835 + t855 + t851 / 0.2e1 - t861 - t865 - t869 / 0.2e1) * t448 - t471 * (0.5e1 * t835 + t875 + 0.5e1 / 0.2e1 * t851 - 0.10e2 * t861 - t878 - 0.5e1 * t869 + 0.5e1 / 0.3e1 * t256 * t882 * t480 * t832 + t890 + 0.5e1 / 0.6e1 * t256 * t477 * t893 * t848) * t486 - 0.2e1 / 0.3e1 * t33 * t826 * t496 * t832 - t907 + 0.2e1 / 0.3e1 * t33 * t322 * (t912 / 0.6e1 - t914 / 0.6e1) + 0.2e1 * t410 * ((-t922 - t925 + t912 / 0.6e1) * t507 - t931 * t934) * t939 - 0.2e1 * t465 * ((-t922 - t925 + t914 / 0.6e1) * t507 - t945 * t934) * t950))
  vrho_0_ = t307 + t522 + t6 * (t812 + t958)
  t961 = -t7 - t525
  t962 = f.my_piecewise5(t10, 0, t14, 0, t961)
  t965 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t962)
  t970 = f.my_piecewise5(t35, 0, t37, 0, t961)
  t973 = f.my_piecewise3(t40, 0, t541 * t970 / 0.3e1)
  t976 = t33 * t539 * t194 * t973
  t979 = t632 * t633 * t973
  t981 = -0.2e1 / 0.3e1 * t979 - t639
  t984 = t33 * t45 * t218 * t981
  t990 = t667 * t668 * t973
  t992 = t675 * t676 * t981
  t1017 = -0.6e1 * t979 - t758
  t1018 = t755 * t1017
  t1019 = t761 * t1017
  t1027 = t33 * t539 * t973 / 0.3e1
  t1033 = -t1027 - t777 + t194 * t981 / 0.2e1
  t1052 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t965 * t26 * t303 - t538 - 0.3e1 / 0.8e1 * t5 * t27 * (-(-0.15757629629629629629629629629629629629629629629630e-1 * t976 - t555 - 0.78788148148148148148148148148148148148148148148150e-2 * t984) * t200 - t211 * (t976 + t664 + t984 / 0.2e1 - t990 - t674 - t992 / 0.2e1) * t225 - t250 * (0.5e1 * t976 + t715 + 0.5e1 / 0.2e1 * t984 - 0.10e2 * t990 - t718 - 0.5e1 * t992 + 0.5e1 / 0.3e1 * t256 * t722 * t265 * t973 + t732 + 0.5e1 / 0.6e1 * t256 * t262 * t735 * t981) * t271 - 0.2e1 / 0.3e1 * t33 * t539 * t281 * t973 - t754 + 0.2e1 / 0.3e1 * t33 * t45 * (t1018 / 0.6e1 - t1019 / 0.6e1) + 0.2e1 * t181 * ((-t1027 - t777 + t1018 / 0.6e1) * t292 - t783 * t1033) * t791 - 0.2e1 * t244 * ((-t1027 - t777 + t1019 / 0.6e1) * t292 - t799 * t1033) * t804))
  t1053 = -t961
  t1054 = f.my_piecewise5(t14, 0, t10, 0, t1053)
  t1057 = f.my_piecewise3(t311, 0, 0.4e1 / 0.3e1 * t312 * t1054)
  t1062 = f.my_piecewise5(t37, 0, t35, 0, t1053)
  t1065 = f.my_piecewise3(t318, 0, t828 * t1062 / 0.3e1)
  t1068 = t33 * t826 * t419 * t1065
  t1070 = t324 * r1
  t1072 = 0.1e1 / t326 / t1070
  t1077 = t329 * t1072
  t1081 = t334 / t342
  t1085 = 0.1e1 / t325 / t350
  t1086 = t341 * t1085
  t1092 = t349 / t326 / t335 / t1070
  t1096 = t356 / t364
  t1101 = t363 / t325 / t392
  t1109 = t404 ** 2
  t1110 = 0.1e1 / t1109
  t1145 = f.my_piecewise3(t409, -t323 * t1072 * t370 * t405 / 0.9e1 + t323 * t328 * (-t57 * t1077 / 0.9e1 - t64 * t1081 / 0.12e2 - t74 * t1086 / 0.108e3 - 0.5e1 / 0.864e3 * t86 * t1092 - t100 * t1096 / 0.288e3 - 0.7e1 / 0.20736e5 * t108 * t1101) * t405 / 0.24e2 - t323 * t371 * t1110 * (-t122 * t372 / t325 / t324 / 0.9e1 - t130 * t1077 / 0.9e1 - t134 * t1081 / 0.12e2 - t138 * t1086 / 0.108e3 - 0.5e1 / 0.864e3 * t142 * t1092 - t146 * t1096 / 0.288e3 - 0.7e1 / 0.20736e5 * t150 * t1101 - t154 * t391 / t326 / t357 / t1070 / 0.5184e4 - t168 * t398 / t357 / t342 / 0.9216e4) / 0.24e2, 0)
  t1147 = t632 * t841 * t1065
  t1149 = t1145 - 0.2e1 / 0.3e1 * t1147 - t847
  t1152 = t33 * t322 * t441 * t1149
  t1156 = t423 * t448
  t1160 = t49 * s2 * t1072 * t431
  t1163 = t430 ** 2
  t1164 = 0.1e1 / t1163
  t1166 = t653 * t340 * t1085 * t1164
  t1174 = t858 * t859 * t1065
  t1176 = t866 * t867 * t1149
  t1197 = t458 * t447 * t468
  t1200 = 0.1e1 / t460
  t1202 = 0.1e1 / t466
  t1203 = f.my_piecewise3(t463, t1145, 0)
  t1227 = t447 ** 2
  t1228 = 0.1e1 / t1227
  t1237 = 0.6e1 * t1147
  t1239 = t908 * (0.9e1 * t1145 - t1237 - t910)
  t1242 = t913 * (0.9e1 * t1203 - t1237 - t910)
  t1252 = t33 * t826 * t1065 / 0.3e1
  t1258 = -t1252 - t925 + t419 * t1149 / 0.2e1
  t1274 = -(-0.15757629629629629629629629629629629629629629629630e-1 * t1068 - t840 - 0.78788148148148148148148148148148148148148148148150e-2 * t1152) * t425 + t1156 * t1145 - (-0.29296049382716049382716049382716049382716049382715e-2 * t1160 - 0.97761008340277777777777777777777777777777777777773e-4 * t1166 - 0.11111111111111111111111111111111111111111111111111e0 * t1145) * t445 * t448 - t436 * (t1068 + t855 + t1152 / 0.2e1 - t1174 - t865 - t1176 / 0.2e1) * t448 + 0.2e1 * t446 * t486 * t1145 - (-(-0.52732888888888888888888888888888888888888888888888e-2 * t1160 - 0.17596981501250000000000000000000000000000000000000e-3 * t1166 - 0.20000000000000000000000000000000000000000000000000e0 * t1145) * t424 / 0.9e1 - t452 * t1145 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t424 * t1145 - 0.30288440000000000000000000000000000000000000000001e0 * t447 * t1145 - 0.7e1 / 0.18e2 * t1197 * t1145 - t459 * (0.6e1 / 0.5e1 * t1200 * t1145 - 0.6e1 / 0.5e1 * t1202 * t1203) / 0.9e1) * t484 * t486 - t471 * (0.5e1 * t1068 + t875 + 0.5e1 / 0.2e1 * t1152 - 0.10e2 * t1174 - t878 - 0.5e1 * t1176 + 0.5e1 / 0.3e1 * t256 * t882 * t480 * t1065 + t890 + 0.5e1 / 0.6e1 * t256 * t477 * t893 * t1149) * t486 + 0.3e1 * t485 * t1228 * t1145 - 0.2e1 / 0.3e1 * t33 * t826 * t496 * t1065 - t907 + 0.2e1 / 0.3e1 * t33 * t322 * (t1239 / 0.6e1 - t1242 / 0.6e1) + 0.2e1 * t1145 * t509 + 0.2e1 * t410 * ((-t1252 - t925 + t1239 / 0.6e1) * t507 - t931 * t1258) * t939 - 0.2e1 * t1203 * t515 - 0.2e1 * t465 * ((-t1252 - t925 + t1242 / 0.6e1) * t507 - t945 * t1258) * t950
  t1279 = f.my_piecewise3(t308, 0, -0.3e1 / 0.8e1 * t5 * t1057 * t26 * t518 - t825 - 0.3e1 / 0.8e1 * t5 * t315 * t1274)
  vrho_1_ = t307 + t522 + t6 * (t1052 + t1279)
  t1285 = t48 * t55
  t1288 = t65 * t68
  t1292 = t76 * s0 * t81
  t1296 = t88 * t66 * t93
  t1299 = t77 * t103
  t1303 = t110 * t89 * t115
  t1340 = f.my_piecewise3(t180, t49 * t177 / 0.24e2 + t50 * t55 * (t57 * t1285 / 0.24e2 + t64 * t1288 / 0.32e2 + t74 * t1292 / 0.288e3 + 0.5e1 / 0.2304e4 * t86 * t1296 + t100 * t1299 / 0.768e3 + 0.7e1 / 0.55296e5 * t108 * t1303) * t176 / 0.24e2 - t50 * t120 * t596 * (t122 * t32 / t65 * t125 / 0.24e2 + t130 * t1285 / 0.24e2 + t134 * t1288 / 0.32e2 + t138 * t1292 / 0.288e3 + 0.5e1 / 0.2304e4 * t142 * t1296 + t146 * t1299 / 0.768e3 + 0.7e1 / 0.55296e5 * t150 * t1303 + t154 * t156 * t101 * t161 / 0.13824e5 + t168 * t111 * t171 / 0.24576e5) / 0.24e2, 0)
  t1347 = t49 * t55 * t206
  t1351 = t653 * s0 * t81 * t656
  t1359 = t33 * t45 * t218 * t1340
  t1361 = t675 * t676 * t1340
  t1384 = f.my_piecewise3(t242, t1340, 0)
  t1405 = t755 * t1340
  t1406 = t761 * t1384
  t1416 = t194 * t1340
  t1433 = 0.78788148148148148148148148148148148148148148148150e-2 * t29 * t285 * t44 * t218 * t1340 * t200 + t647 * t1340 - (0.10986018518518518518518518518518518518518518518518e-2 * t1347 + 0.36660378127604166666666666666666666666666666666665e-4 * t1351 - 0.11111111111111111111111111111111111111111111111111e0 * t1340) * t222 * t225 - t211 * (t1359 / 0.2e1 - t1361 / 0.2e1) * t225 + 0.2e1 * t223 * t271 * t1340 - (-(0.19774833333333333333333333333333333333333333333333e-2 * t1347 + 0.65988680629687499999999999999999999999999999999999e-4 * t1351 - 0.20000000000000000000000000000000000000000000000000e0 * t1340) * t199 / 0.9e1 - t229 * t1340 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t199 * t1340 - 0.30288440000000000000000000000000000000000000000001e0 * t224 * t1340 - 0.7e1 / 0.18e2 * t699 * t1340 - t236 * (0.6e1 / 0.5e1 * t702 * t1340 - 0.6e1 / 0.5e1 * t704 * t1384) / 0.9e1) * t269 * t271 - t250 * (0.5e1 / 0.2e1 * t1359 - 0.5e1 * t1361 + 0.5e1 / 0.6e1 * t256 * t262 * t735 * t1340) * t271 + 0.3e1 * t270 * t744 * t1340 + 0.2e1 / 0.3e1 * t33 * t45 * (0.3e1 / 0.2e1 * t1405 - 0.3e1 / 0.2e1 * t1406) + 0.2e1 * t1340 * t294 + 0.2e1 * t181 * (0.3e1 / 0.2e1 * t1405 * t292 - t783 * t1416 / 0.2e1) * t791 - 0.2e1 * t1384 * t300 - 0.2e1 * t244 * (0.3e1 / 0.2e1 * t1406 * t292 - t799 * t1416 / 0.2e1) * t804
  t1437 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t1433)
  vsigma_0_ = t6 * t1437
  vsigma_1_ = 0.0e0
  t1441 = t48 * t328
  t1444 = t333 * t336
  t1448 = t76 * s2 * t344
  t1452 = t88 * t334 * t352
  t1455 = t340 * t358
  t1459 = t110 * t348 * t366
  t1496 = f.my_piecewise3(t409, t49 * t406 / 0.24e2 + t323 * t328 * (t57 * t1441 / 0.24e2 + t64 * t1444 / 0.32e2 + t74 * t1448 / 0.288e3 + 0.5e1 / 0.2304e4 * t86 * t1452 + t100 * t1455 / 0.768e3 + 0.7e1 / 0.55296e5 * t108 * t1459) * t405 / 0.24e2 - t323 * t371 * t1110 * (t122 * t32 / t333 * t374 / 0.24e2 + t130 * t1441 / 0.24e2 + t134 * t1444 / 0.32e2 + t138 * t1448 / 0.288e3 + 0.5e1 / 0.2304e4 * t142 * t1452 + t146 * t1455 / 0.768e3 + 0.7e1 / 0.55296e5 * t150 * t1459 + t154 * t156 * t356 * t394 / 0.13824e5 + t168 * t362 * t400 / 0.24576e5) / 0.24e2, 0)
  t1503 = t49 * t328 * t431
  t1507 = t653 * s2 * t344 * t1164
  t1515 = t33 * t322 * t441 * t1496
  t1517 = t866 * t867 * t1496
  t1540 = f.my_piecewise3(t463, t1496, 0)
  t1561 = t908 * t1496
  t1562 = t913 * t1540
  t1572 = t419 * t1496
  t1589 = 0.78788148148148148148148148148148148148148148148150e-2 * t29 * t500 * t44 * t441 * t1496 * t425 + t1156 * t1496 - (0.10986018518518518518518518518518518518518518518518e-2 * t1503 + 0.36660378127604166666666666666666666666666666666665e-4 * t1507 - 0.11111111111111111111111111111111111111111111111111e0 * t1496) * t445 * t448 - t436 * (t1515 / 0.2e1 - t1517 / 0.2e1) * t448 + 0.2e1 * t446 * t486 * t1496 - (-(0.19774833333333333333333333333333333333333333333333e-2 * t1503 + 0.65988680629687499999999999999999999999999999999999e-4 * t1507 - 0.20000000000000000000000000000000000000000000000000e0 * t1496) * t424 / 0.9e1 - t452 * t1496 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t424 * t1496 - 0.30288440000000000000000000000000000000000000000001e0 * t447 * t1496 - 0.7e1 / 0.18e2 * t1197 * t1496 - t459 * (0.6e1 / 0.5e1 * t1200 * t1496 - 0.6e1 / 0.5e1 * t1202 * t1540) / 0.9e1) * t484 * t486 - t471 * (0.5e1 / 0.2e1 * t1515 - 0.5e1 * t1517 + 0.5e1 / 0.6e1 * t256 * t477 * t893 * t1496) * t486 + 0.3e1 * t485 * t1228 * t1496 + 0.2e1 / 0.3e1 * t33 * t322 * (0.3e1 / 0.2e1 * t1561 - 0.3e1 / 0.2e1 * t1562) + 0.2e1 * t1496 * t509 + 0.2e1 * t410 * (0.3e1 / 0.2e1 * t1561 * t507 - t931 * t1572 / 0.2e1) * t939 - 0.2e1 * t1540 * t515 - 0.2e1 * t465 * (0.3e1 / 0.2e1 * t1562 * t507 - t945 * t1572 / 0.2e1) * t950
  t1593 = f.my_piecewise3(t308, 0, -0.3e1 / 0.8e1 * t5 * t315 * t1589)
  vsigma_2_ = t6 * t1593
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

  hjs_AA = 0.757211

  hjs_BB = -0.106364

  hjs_CC = -0.118649

  hjs_DD = 0.60965

  hjs_fH = lambda s: jnp.sum(jnp.array([params_a[i] * s ** (1 + i) for i in range(1, 6 + 1)]), axis=0) / (1 + jnp.sum(jnp.array([params_b[i] * s ** i for i in range(1, 9 + 1)]), axis=0))

  hjs_zeta = lambda s: jnp.maximum(s ** 2 * hjs_fH(s), 1e-10)

  hjs_eta = lambda s: jnp.maximum(hjs_AA + hjs_zeta(s), 1e-10)

  hjs_lambda = lambda s: hjs_DD + hjs_zeta(s)

  hjs_fF = lambda rs, z, s: 1 - s ** 2 / (27 * hjs_CC * (1 + s ** 2 / 4)) - hjs_zeta(s) / (2 * hjs_CC)

  hjs_chi = lambda rs, z, s: f.nu(rs, z) / jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)

  hjs_fG = lambda rs, z, s: -2 / 5 * hjs_CC * hjs_fF(rs, z, s) * hjs_lambda(s) - 4 / 15 * hjs_BB * hjs_lambda(s) ** 2 - 6 / 5 * hjs_AA * hjs_lambda(s) ** 3 - hjs_lambda(s) ** (7 / 2) * (4 / 5 * jnp.sqrt(jnp.pi) + 12 / 5 * (jnp.sqrt(hjs_zeta(s)) - jnp.sqrt(hjs_eta(s))))

  hjs_f1 = lambda rs, z, s: +hjs_AA - 4 / 9 * hjs_BB * (1 - hjs_chi(rs, z, s)) / hjs_lambda(s) - 2 / 9 * hjs_CC * hjs_fF(rs, z, s) * (2 - 3 * hjs_chi(rs, z, s) + hjs_chi(rs, z, s) ** 3) / hjs_lambda(s) ** 2 - 1 / 9 * hjs_fG(rs, z, s) * (8 - 15 * hjs_chi(rs, z, s) + 10 * hjs_chi(rs, z, s) ** 3 - 3 * hjs_chi(rs, z, s) ** 5) / hjs_lambda(s) ** 3 + 2 * f.nu(rs, z) * (jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2) - jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) + 2 * hjs_zeta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_zeta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2))) - 2 * hjs_eta(s) * jnp.log((f.nu(rs, z) + jnp.sqrt(hjs_eta(s) + f.nu(rs, z) ** 2)) / (f.nu(rs, z) + jnp.sqrt(hjs_lambda(s) + f.nu(rs, z) ** 2)))

  hjs_fx = lambda rs, z, x: hjs_f1(rs, z, X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, hjs_fx, rs, z, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = 0.1e1 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = f.my_piecewise5(t7, t8, t7, -t8, 0)
  t11 = 0.1e1 + t10
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t17 * t18
  t20 = t3 ** 2
  t21 = f.p.cam_omega * t20
  t22 = jnp.pi ** 2
  t23 = t22 ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t23
  t25 = t21 * t24
  t26 = f.my_piecewise3(t12, t13, t15)
  t27 = 0.1e1 / t26
  t28 = 0.1e1 / t18
  t29 = t27 * t28
  t30 = 6 ** (0.1e1 / 0.3e1)
  t31 = t23 ** 2
  t32 = 0.1e1 / t31
  t33 = t30 * t32
  t34 = t33 * s0
  t35 = 2 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = r0 ** 2
  t38 = t18 ** 2
  t40 = 0.1e1 / t38 / t37
  t41 = t36 * t40
  t43 = params.a[0] * t30
  t44 = t43 * t32
  t45 = s0 * t36
  t46 = t45 * t40
  t50 = 0.1e1 / t22
  t51 = params.a[1] * t50
  t52 = jnp.sqrt(s0)
  t53 = t52 * s0
  t54 = t37 ** 2
  t55 = 0.1e1 / t54
  t56 = t53 * t55
  t60 = t30 ** 2
  t63 = 0.1e1 / t23 / t22
  t64 = params.a[2] * t60 * t63
  t65 = s0 ** 2
  t66 = t65 * t35
  t67 = t54 * r0
  t69 = 0.1e1 / t18 / t67
  t70 = t66 * t69
  t76 = 0.1e1 / t31 / t22
  t77 = params.a[3] * t30 * t76
  t78 = t52 * t65
  t79 = t78 * t36
  t80 = t54 * t37
  t82 = 0.1e1 / t38 / t80
  t83 = t79 * t82
  t87 = t22 ** 2
  t88 = 0.1e1 / t87
  t89 = params.a[4] * t88
  t90 = t65 * s0
  t91 = t54 ** 2
  t92 = 0.1e1 / t91
  t93 = t90 * t92
  t99 = 0.1e1 / t23 / t87
  t100 = params.a[5] * t60 * t99
  t101 = t52 * t90
  t102 = t101 * t35
  t103 = t91 * r0
  t105 = 0.1e1 / t18 / t103
  t106 = t102 * t105
  t109 = t44 * t46 / 0.24e2 + t51 * t56 / 0.24e2 + t64 * t70 / 0.288e3 + t77 * t83 / 0.576e3 + t89 * t93 / 0.576e3 + t100 * t106 / 0.6912e4
  t112 = params.b[0] * t60 * t24
  t113 = t52 * t35
  t115 = 0.1e1 / t18 / r0
  t120 = params.b[1] * t30
  t121 = t120 * t32
  t125 = params.b[2] * t50
  t130 = params.b[3] * t60 * t63
  t135 = params.b[4] * t30 * t76
  t139 = params.b[5] * t88
  t144 = params.b[6] * t60 * t99
  t151 = params.b[7] * t30 / t31 / t87
  t152 = t65 ** 2
  t153 = t152 * t36
  t154 = t91 * t37
  t156 = 0.1e1 / t38 / t154
  t163 = params.b[8] / t87 / t22
  t164 = t52 * t152
  t166 = 0.1e1 / t91 / t54
  t170 = 0.1e1 + t112 * t113 * t115 / 0.12e2 + t121 * t46 / 0.24e2 + t125 * t56 / 0.24e2 + t130 * t70 / 0.288e3 + t135 * t83 / 0.576e3 + t139 * t93 / 0.576e3 + t144 * t106 / 0.6912e4 + t151 * t153 * t156 / 0.13824e5 + t163 * t164 * t166 / 0.13824e5
  t171 = 0.1e1 / t170
  t172 = t109 * t171
  t175 = t34 * t41 * t172 / 0.24e2
  t176 = 0.1e-9 < t175
  t177 = f.my_piecewise3(t176, t175, 0.1e-9)
  t178 = f.p.cam_omega ** 2
  t179 = t178 * t3
  t180 = t26 ** 2
  t182 = t32 / t180
  t183 = 0.1e1 / t38
  t185 = t179 * t182 * t183
  t187 = 0.609650e0 + t177 + t185 / 0.3e1
  t188 = jnp.sqrt(t187)
  t189 = 0.1e1 / t188
  t191 = t25 * t29 * t189
  t193 = -0.47272888888888888888888888888888888888888888888889e-1 + 0.15757629629629629629629629629629629629629629629630e-1 * t191
  t194 = 0.609650e0 + t177
  t195 = 0.1e1 / t194
  t199 = -0.3203523e1 - 0.33370031250000000000000000000000000000000000000000e-1 * t33 * t46
  t200 = 0.1e1 / t199
  t201 = t41 * t200
  t202 = t34 * t201
  t205 = -0.26366444444444444444444444444444444444444444444444e-1 + 0.10986018518518518518518518518518518518518518518518e-2 * t202 - 0.11111111111111111111111111111111111111111111111111e0 * t177
  t207 = t178 * f.p.cam_omega * t50
  t209 = 0.1e1 / t180 / t26
  t210 = 0.1e1 / r0
  t213 = 0.1e1 / t188 / t187
  t215 = t207 * t209 * t210 * t213
  t217 = 0.2e1 - t191 + t215 / 0.3e1
  t218 = t205 * t217
  t219 = t194 ** 2
  t220 = 0.1e1 / t219
  t224 = -0.47459600000000000000000000000000000000000000000000e-1 + 0.19774833333333333333333333333333333333333333333333e-2 * t202 - 0.20000000000000000000000000000000000000000000000000e0 * t177
  t228 = t219 * t194
  t230 = jnp.sqrt(t194)
  t231 = t230 * t228
  t232 = jnp.sqrt(jnp.pi)
  t234 = jnp.sqrt(t177)
  t237 = 0.0e0 < 0.7572109999e0 + t177
  t239 = f.my_piecewise3(t237, 0.757211e0 + t177, 0.1e-9)
  t240 = jnp.sqrt(t239)
  t242 = 0.4e1 / 0.5e1 * t232 + 0.12e2 / 0.5e1 * t234 - 0.12e2 / 0.5e1 * t240
  t245 = -t224 * t194 / 0.9e1 + 0.31515259259259259259259259259259259259259259259259e-2 * t219 - 0.10096146666666666666666666666666666666666666666667e0 * t228 - t231 * t242 / 0.9e1
  t248 = t178 ** 2
  t251 = t248 * f.p.cam_omega * t3 * t76
  t252 = t180 ** 2
  t254 = 0.1e1 / t252 / t26
  t256 = 0.1e1 / t38 / r0
  t257 = t254 * t256
  t258 = t187 ** 2
  t260 = 0.1e1 / t188 / t258
  t264 = 0.8e1 - 0.5e1 * t191 + 0.10e2 / 0.3e1 * t215 - t251 * t257 * t260 / 0.3e1
  t265 = t245 * t264
  t266 = 0.1e1 / t228
  t269 = 0.3e1 * t185
  t271 = jnp.sqrt(0.9e1 * t177 + t269)
  t274 = jnp.sqrt(0.9e1 * t239 + t269)
  t276 = t271 / 0.3e1 - t274 / 0.3e1
  t280 = t24 * t27
  t282 = t21 * t280 * t28
  t284 = t282 / 0.3e1 + t271 / 0.3e1
  t286 = t282 / 0.3e1 + t188
  t287 = 0.1e1 / t286
  t289 = jnp.log(t284 * t287)
  t293 = t282 / 0.3e1 + t274 / 0.3e1
  t295 = jnp.log(t293 * t287)
  t298 = 0.757211e0 - t193 * t195 - t218 * t220 - t265 * t266 + 0.2e1 / 0.3e1 * t25 * t29 * t276 + 0.2e1 * t177 * t289 - 0.2e1 * t239 * t295
  t302 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t298)
  t307 = t27 * t115
  t309 = t25 * t307 * t189
  t311 = t37 * r0
  t313 = 0.1e1 / t38 / t311
  t314 = t36 * t313
  t318 = t45 * t313
  t322 = t53 / t67
  t326 = 0.1e1 / t18 / t80
  t327 = t66 * t326
  t333 = t79 / t38 / t54 / t311
  t337 = t90 / t103
  t342 = t102 / t18 / t154
  t350 = t33 * t45
  t351 = t40 * t109
  t352 = t170 ** 2
  t353 = 0.1e1 / t352
  t388 = f.my_piecewise3(t176, -t34 * t314 * t172 / 0.9e1 + t34 * t41 * (-t44 * t318 / 0.9e1 - t51 * t322 / 0.6e1 - t64 * t327 / 0.54e2 - 0.5e1 / 0.432e3 * t77 * t333 - t89 * t337 / 0.72e2 - 0.7e1 / 0.5184e4 * t100 * t342) * t171 / 0.24e2 - t350 * t351 * t353 * (-t112 * t113 / t18 / t37 / 0.9e1 - t121 * t318 / 0.9e1 - t125 * t322 / 0.6e1 - t130 * t327 / 0.54e2 - 0.5e1 / 0.432e3 * t135 * t333 - t139 * t337 / 0.72e2 - 0.7e1 / 0.5184e4 * t144 * t342 - t151 * t153 / t38 / t91 / t311 / 0.1296e4 - t163 * t164 / t91 / t67 / 0.1152e4) / 0.24e2, 0)
  t390 = t179 * t182 * t256
  t392 = t388 - 0.2e1 / 0.9e1 * t390
  t395 = t25 * t29 * t213 * t392
  t399 = t193 * t220
  t402 = t34 * t314 * t200
  t404 = t60 * t63
  t407 = t199 ** 2
  t408 = 0.1e1 / t407
  t410 = t404 * t65 * t35 * t326 * t408
  t421 = t207 * t209 / t37 * t213
  t423 = t207 * t209
  t424 = t210 * t260
  t426 = t423 * t424 * t392
  t447 = t230 * t219 * t242
  t450 = 0.1e1 / t234
  t452 = 0.1e1 / t240
  t453 = f.my_piecewise3(t237, t388, 0)
  t472 = 0.1e1 / t188 / t258 / t187
  t480 = t219 ** 2
  t481 = 0.1e1 / t480
  t488 = 0.1e1 / t271
  t490 = 0.2e1 * t390
  t492 = t488 * (0.9e1 * t388 - t490)
  t493 = 0.1e1 / t274
  t496 = t493 * (0.9e1 * t453 - t490)
  t506 = t21 * t280 * t115 / 0.9e1
  t510 = t286 ** 2
  t511 = 0.1e1 / t510
  t512 = t284 * t511
  t515 = -t506 + t189 * t392 / 0.2e1
  t520 = 0.1e1 / t284 * t286
  t528 = t293 * t511
  t533 = 0.1e1 / t293 * t286
  t536 = -(-0.52525432098765432098765432098765432098765432098767e-2 * t309 - 0.78788148148148148148148148148148148148148148148150e-2 * t395) * t195 + t399 * t388 - (-0.29296049382716049382716049382716049382716049382715e-2 * t402 - 0.19552201668055555555555555555555555555555555555555e-3 * t410 - 0.11111111111111111111111111111111111111111111111111e0 * t388) * t217 * t220 - t205 * (t309 / 0.3e1 + t395 / 0.2e1 - t421 / 0.3e1 - t426 / 0.2e1) * t220 + 0.2e1 * t218 * t266 * t388 - (-(-0.52732888888888888888888888888888888888888888888888e-2 * t402 - 0.35193963002499999999999999999999999999999999999999e-3 * t410 - 0.20000000000000000000000000000000000000000000000000e0 * t388) * t194 / 0.9e1 - t224 * t388 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t194 * t388 - 0.30288440000000000000000000000000000000000000000001e0 * t219 * t388 - 0.7e1 / 0.18e2 * t447 * t388 - t231 * (0.6e1 / 0.5e1 * t450 * t388 - 0.6e1 / 0.5e1 * t452 * t453) / 0.9e1) * t264 * t266 - t245 * (0.5e1 / 0.3e1 * t309 + 0.5e1 / 0.2e1 * t395 - 0.10e2 / 0.3e1 * t421 - 0.5e1 * t426 + 0.5e1 / 0.9e1 * t251 * t254 * t40 * t260 + 0.5e1 / 0.6e1 * t251 * t257 * t472 * t392) * t266 + 0.3e1 * t265 * t481 * t388 - 0.2e1 / 0.9e1 * t25 * t307 * t276 + 0.2e1 / 0.3e1 * t25 * t29 * (t492 / 0.6e1 - t496 / 0.6e1) + 0.2e1 * t388 * t289 + 0.2e1 * t177 * ((-t506 + t492 / 0.6e1) * t287 - t512 * t515) * t520 - 0.2e1 * t453 * t295 - 0.2e1 * t239 * ((-t506 + t496 / 0.6e1) * t287 - t528 * t515) * t533
  t541 = f.my_piecewise3(t2, 0, -t6 * t17 * t183 * t298 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * t536)
  vrho_0_ = 0.2e1 * r0 * t541 + 0.2e1 * t302
  t550 = t32 * t36 * t40
  t553 = t52 * t55
  t557 = s0 * t35 * t69
  t561 = t53 * t36 * t82
  t564 = t65 * t92
  t568 = t78 * t35 * t105
  t605 = f.my_piecewise3(t176, t33 * t36 * t351 * t171 / 0.24e2 + t34 * t41 * (t43 * t550 / 0.24e2 + t51 * t553 / 0.16e2 + t64 * t557 / 0.144e3 + 0.5e1 / 0.1152e4 * t77 * t561 + t89 * t564 / 0.192e3 + 0.7e1 / 0.13824e5 * t100 * t568) * t171 / 0.24e2 - t350 * t351 * t353 * (t112 / t52 * t35 * t115 / 0.24e2 + t120 * t550 / 0.24e2 + t125 * t553 / 0.16e2 + t130 * t557 / 0.144e3 + 0.5e1 / 0.1152e4 * t135 * t561 + t139 * t564 / 0.192e3 + 0.7e1 / 0.13824e5 * t144 * t568 + t151 * t90 * t36 * t156 / 0.3456e4 + t163 * t101 * t166 / 0.3072e4) / 0.24e2, 0)
  t611 = t33 * t201
  t616 = t404 * s0 * t35 * t69 * t408
  t624 = t25 * t29 * t213 * t605
  t626 = t423 * t424 * t605
  t649 = f.my_piecewise3(t237, t605, 0)
  t670 = t488 * t605
  t671 = t493 * t649
  t681 = t189 * t605
  t698 = 0.78788148148148148148148148148148148148148148148150e-2 * t21 * t280 * t28 * t213 * t605 * t195 + t399 * t605 - (0.10986018518518518518518518518518518518518518518518e-2 * t611 + 0.73320756255208333333333333333333333333333333333330e-4 * t616 - 0.11111111111111111111111111111111111111111111111111e0 * t605) * t217 * t220 - t205 * (t624 / 0.2e1 - t626 / 0.2e1) * t220 + 0.2e1 * t218 * t266 * t605 - (-(0.19774833333333333333333333333333333333333333333333e-2 * t611 + 0.13197736125937500000000000000000000000000000000000e-3 * t616 - 0.20000000000000000000000000000000000000000000000000e0 * t605) * t194 / 0.9e1 - t224 * t605 / 0.9e1 + 0.63030518518518518518518518518518518518518518518518e-2 * t194 * t605 - 0.30288440000000000000000000000000000000000000000001e0 * t219 * t605 - 0.7e1 / 0.18e2 * t447 * t605 - t231 * (0.6e1 / 0.5e1 * t450 * t605 - 0.6e1 / 0.5e1 * t452 * t649) / 0.9e1) * t264 * t266 - t245 * (0.5e1 / 0.2e1 * t624 - 0.5e1 * t626 + 0.5e1 / 0.6e1 * t251 * t257 * t472 * t605) * t266 + 0.3e1 * t265 * t481 * t605 + 0.2e1 / 0.3e1 * t25 * t29 * (0.3e1 / 0.2e1 * t670 - 0.3e1 / 0.2e1 * t671) + 0.2e1 * t605 * t289 + 0.2e1 * t177 * (0.3e1 / 0.2e1 * t670 * t287 - t512 * t681 / 0.2e1) * t520 - 0.2e1 * t649 * t295 - 0.2e1 * t239 * (0.3e1 / 0.2e1 * t671 * t287 - t528 * t681 / 0.2e1) * t533
  t702 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t698)
  vsigma_0_ = 0.2e1 * r0 * t702
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
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t20 = 0.1e1 / t19
  t21 = t17 * t20
  t22 = t3 ** 2
  t23 = f.p.cam_omega * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = t23 * t26
  t28 = f.my_piecewise3(t12, t13, t15)
  t29 = 0.1e1 / t28
  t30 = 0.1e1 / t18
  t31 = t29 * t30
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = t25 ** 2
  t34 = 0.1e1 / t33
  t35 = t32 * t34
  t36 = t35 * s0
  t37 = 2 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = r0 ** 2
  t41 = 0.1e1 / t19 / t39
  t42 = t38 * t41
  t44 = params.a[0] * t32
  t45 = t44 * t34
  t46 = s0 * t38
  t47 = t46 * t41
  t51 = 0.1e1 / t24
  t52 = params.a[1] * t51
  t53 = jnp.sqrt(s0)
  t54 = t53 * s0
  t55 = t39 ** 2
  t56 = 0.1e1 / t55
  t57 = t54 * t56
  t61 = t32 ** 2
  t62 = params.a[2] * t61
  t64 = 0.1e1 / t25 / t24
  t65 = t62 * t64
  t66 = s0 ** 2
  t67 = t66 * t37
  t68 = t55 * r0
  t70 = 0.1e1 / t18 / t68
  t71 = t67 * t70
  t77 = 0.1e1 / t33 / t24
  t78 = params.a[3] * t32 * t77
  t79 = t53 * t66
  t80 = t79 * t38
  t81 = t55 * t39
  t83 = 0.1e1 / t19 / t81
  t84 = t80 * t83
  t88 = t24 ** 2
  t89 = 0.1e1 / t88
  t90 = params.a[4] * t89
  t91 = t66 * s0
  t92 = t55 ** 2
  t93 = 0.1e1 / t92
  t94 = t91 * t93
  t100 = 0.1e1 / t25 / t88
  t101 = params.a[5] * t61 * t100
  t102 = t53 * t91
  t103 = t102 * t37
  t104 = t92 * r0
  t106 = 0.1e1 / t18 / t104
  t107 = t103 * t106
  t110 = t45 * t47 / 0.24e2 + t52 * t57 / 0.24e2 + t65 * t71 / 0.288e3 + t78 * t84 / 0.576e3 + t90 * t94 / 0.576e3 + t101 * t107 / 0.6912e4
  t113 = params.b[0] * t61 * t26
  t114 = t53 * t37
  t116 = 0.1e1 / t18 / r0
  t121 = params.b[1] * t32
  t122 = t121 * t34
  t126 = params.b[2] * t51
  t130 = params.b[3] * t61
  t131 = t130 * t64
  t136 = params.b[4] * t32 * t77
  t140 = params.b[5] * t89
  t145 = params.b[6] * t61 * t100
  t152 = params.b[7] * t32 / t33 / t88
  t153 = t66 ** 2
  t154 = t153 * t38
  t155 = t92 * t39
  t157 = 0.1e1 / t19 / t155
  t164 = params.b[8] / t88 / t24
  t165 = t53 * t153
  t166 = t92 * t55
  t167 = 0.1e1 / t166
  t171 = 0.1e1 + t113 * t114 * t116 / 0.12e2 + t122 * t47 / 0.24e2 + t126 * t57 / 0.24e2 + t131 * t71 / 0.288e3 + t136 * t84 / 0.576e3 + t140 * t94 / 0.576e3 + t145 * t107 / 0.6912e4 + t152 * t154 * t157 / 0.13824e5 + t164 * t165 * t167 / 0.13824e5
  t172 = 0.1e1 / t171
  t173 = t110 * t172
  t176 = t36 * t42 * t173 / 0.24e2
  t177 = 0.1e-9 < t176
  t178 = f.my_piecewise3(t177, t176, 0.1e-9)
  t179 = f.p.cam_omega ** 2
  t180 = t179 * t3
  t181 = t28 ** 2
  t183 = t34 / t181
  t185 = t180 * t183 * t20
  t187 = 0.609650e0 + t178 + t185 / 0.3e1
  t188 = jnp.sqrt(t187)
  t189 = 0.1e1 / t188
  t191 = t27 * t31 * t189
  t193 = 0.1e1 - t191 / 0.3e1
  t194 = 0.609650e0 + t178
  t195 = 0.1e1 / t194
  t200 = 0.1e1 + t35 * t47 / 0.96e2
  t201 = 0.1e1 / t200
  t202 = t42 * t201
  t206 = 0.1e1 + 0.13006513974354692214373571429537626752380634278782e-1 * t36 * t202 + 0.42141105276909202774570371431701910677713255063254e1 * t178
  t208 = t179 * f.p.cam_omega * t51
  t210 = 0.1e1 / t181 / t28
  t211 = 0.1e1 / r0
  t214 = 0.1e1 / t188 / t187
  t216 = t208 * t210 * t211 * t214
  t218 = 0.2e1 - t191 + t216 / 0.3e1
  t219 = t206 * t218
  t220 = t194 ** 2
  t221 = 0.1e1 / t220
  t227 = t220 * t194
  t229 = jnp.sqrt(t194)
  t230 = t229 * t227
  t231 = jnp.sqrt(jnp.pi)
  t233 = jnp.sqrt(t178)
  t236 = 0.0e0 < 0.7572109999e0 + t178
  t238 = f.my_piecewise3(t236, 0.757211e0 + t178, 0.1e-9)
  t239 = jnp.sqrt(t238)
  t241 = 0.4e1 / 0.5e1 * t231 + 0.12e2 / 0.5e1 * t233 - 0.12e2 / 0.5e1 * t239
  t243 = 0.47459600000000000000000000000000000000000000000000e-1 * t206 * t194 + 0.28363733333333333333333333333333333333333333333333e-1 * t220 - 0.90865320000000000000000000000000000000000000000000e0 * t227 - t230 * t241
  t246 = t179 ** 2
  t248 = t246 * f.p.cam_omega * t3
  t249 = t248 * t77
  t250 = t181 ** 2
  t252 = 0.1e1 / t250 / t28
  t254 = 0.1e1 / t19 / r0
  t255 = t252 * t254
  t256 = t187 ** 2
  t258 = 0.1e1 / t188 / t256
  t262 = 0.8e1 - 0.5e1 * t191 + 0.10e2 / 0.3e1 * t216 - t249 * t255 * t258 / 0.3e1
  t263 = t243 * t262
  t264 = 0.1e1 / t227
  t268 = 0.3e1 * t185
  t269 = 0.9e1 * t178 + t268
  t270 = jnp.sqrt(t269)
  t272 = 0.9e1 * t238 + t268
  t273 = jnp.sqrt(t272)
  t275 = t270 / 0.3e1 - t273 / 0.3e1
  t279 = t26 * t29
  t281 = t23 * t279 * t30
  t283 = t281 / 0.3e1 + t270 / 0.3e1
  t285 = t281 / 0.3e1 + t188
  t286 = 0.1e1 / t285
  t288 = jnp.log(t283 * t286)
  t292 = t281 / 0.3e1 + t273 / 0.3e1
  t294 = jnp.log(t292 * t286)
  t297 = 0.757211e0 + 0.47272888888888888888888888888888888888888888888889e-1 * t193 * t195 + 0.26366444444444444444444444444444444444444444444444e-1 * t219 * t221 - t263 * t264 / 0.9e1 + 0.2e1 / 0.3e1 * t27 * t31 * t275 + 0.2e1 * t178 * t288 - 0.2e1 * t238 * t294
  t301 = t17 * t18
  t302 = t29 * t116
  t304 = t27 * t302 * t189
  t306 = t39 * r0
  t308 = 0.1e1 / t19 / t306
  t309 = t38 * t308
  t313 = t46 * t308
  t316 = 0.1e1 / t68
  t317 = t54 * t316
  t321 = 0.1e1 / t18 / t81
  t322 = t67 * t321
  t325 = t55 * t306
  t327 = 0.1e1 / t19 / t325
  t328 = t80 * t327
  t331 = 0.1e1 / t104
  t332 = t91 * t331
  t336 = 0.1e1 / t18 / t155
  t337 = t103 * t336
  t340 = -t45 * t313 / 0.9e1 - t52 * t317 / 0.6e1 - t65 * t322 / 0.54e2 - 0.5e1 / 0.432e3 * t78 * t328 - t90 * t332 / 0.72e2 - 0.7e1 / 0.5184e4 * t101 * t337
  t341 = t340 * t172
  t345 = t35 * t46
  t346 = t41 * t110
  t347 = t171 ** 2
  t348 = 0.1e1 / t347
  t350 = 0.1e1 / t18 / t39
  t366 = t92 * t306
  t368 = 0.1e1 / t19 / t366
  t373 = 0.1e1 / t92 / t68
  t377 = -t113 * t114 * t350 / 0.9e1 - t122 * t313 / 0.9e1 - t126 * t317 / 0.6e1 - t131 * t322 / 0.54e2 - 0.5e1 / 0.432e3 * t136 * t328 - t140 * t332 / 0.72e2 - 0.7e1 / 0.5184e4 * t145 * t337 - t152 * t154 * t368 / 0.1296e4 - t164 * t165 * t373 / 0.1152e4
  t378 = t348 * t377
  t379 = t346 * t378
  t383 = f.my_piecewise3(t177, -t36 * t309 * t173 / 0.9e1 + t36 * t42 * t341 / 0.24e2 - t345 * t379 / 0.24e2, 0)
  t385 = t180 * t183 * t254
  t387 = t383 - 0.2e1 / 0.9e1 * t385
  t388 = t214 * t387
  t390 = t27 * t31 * t388
  t392 = t304 / 0.9e1 + t390 / 0.6e1
  t395 = t193 * t221
  t398 = t309 * t201
  t401 = t61 * t64
  t402 = t401 * t66
  t404 = t200 ** 2
  t405 = 0.1e1 / t404
  t410 = -0.34684037264945845904996190478767004673015024743419e-1 * t36 * t398 + 0.72258410968637178968742063497431259735447968215456e-3 * t402 * t37 * t321 * t405 + 0.42141105276909202774570371431701910677713255063254e1 * t383
  t411 = t410 * t218
  t416 = 0.1e1 / t39
  t419 = t208 * t210 * t416 * t214
  t421 = t208 * t210
  t422 = t211 * t258
  t424 = t421 * t422 * t387
  t426 = t304 / 0.3e1 + t390 / 0.2e1 - t419 / 0.3e1 - t424 / 0.2e1
  t427 = t206 * t426
  t430 = t264 * t383
  t441 = t229 * t220
  t442 = t441 * t241
  t445 = 0.1e1 / t233
  t447 = 0.1e1 / t239
  t448 = f.my_piecewise3(t236, t383, 0)
  t451 = 0.6e1 / 0.5e1 * t445 * t383 - 0.6e1 / 0.5e1 * t447 * t448
  t453 = 0.47459600000000000000000000000000000000000000000000e-1 * t410 * t194 + 0.47459600000000000000000000000000000000000000000000e-1 * t206 * t383 + 0.56727466666666666666666666666666666666666666666666e-1 * t194 * t383 - 0.27259596000000000000000000000000000000000000000000e1 * t220 * t383 - 0.7e1 / 0.2e1 * t442 * t383 - t230 * t451
  t454 = t453 * t262
  t461 = t252 * t41
  t467 = 0.1e1 / t188 / t256 / t187
  t468 = t467 * t387
  t472 = 0.5e1 / 0.3e1 * t304 + 0.5e1 / 0.2e1 * t390 - 0.10e2 / 0.3e1 * t419 - 0.5e1 * t424 + 0.5e1 / 0.9e1 * t249 * t461 * t258 + 0.5e1 / 0.6e1 * t249 * t255 * t468
  t473 = t243 * t472
  t476 = t220 ** 2
  t477 = 0.1e1 / t476
  t478 = t477 * t383
  t484 = 0.1e1 / t270
  t486 = 0.2e1 * t385
  t487 = 0.9e1 * t383 - t486
  t488 = t484 * t487
  t489 = 0.1e1 / t273
  t491 = 0.9e1 * t448 - t486
  t492 = t489 * t491
  t494 = t488 / 0.6e1 - t492 / 0.6e1
  t502 = t23 * t279 * t116 / 0.9e1
  t504 = -t502 + t488 / 0.6e1
  t506 = t285 ** 2
  t507 = 0.1e1 / t506
  t508 = t283 * t507
  t511 = -t502 + t189 * t387 / 0.2e1
  t513 = t504 * t286 - t508 * t511
  t514 = t178 * t513
  t515 = 0.1e1 / t283
  t516 = t515 * t285
  t522 = -t502 + t492 / 0.6e1
  t524 = t292 * t507
  t526 = t522 * t286 - t524 * t511
  t527 = t238 * t526
  t528 = 0.1e1 / t292
  t529 = t528 * t285
  t532 = 0.47272888888888888888888888888888888888888888888889e-1 * t392 * t195 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t383 + 0.26366444444444444444444444444444444444444444444444e-1 * t411 * t221 + 0.26366444444444444444444444444444444444444444444444e-1 * t427 * t221 - 0.52732888888888888888888888888888888888888888888888e-1 * t219 * t430 - t454 * t264 / 0.9e1 - t473 * t264 / 0.9e1 + t263 * t478 / 0.3e1 - 0.2e1 / 0.9e1 * t27 * t302 * t275 + 0.2e1 / 0.3e1 * t27 * t31 * t494 + 0.2e1 * t383 * t288 + 0.2e1 * t514 * t516 - 0.2e1 * t448 * t294 - 0.2e1 * t527 * t529
  t537 = f.my_piecewise3(t2, 0, -t6 * t21 * t297 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t301 * t532)
  t547 = 0.1e1 / t19 / t55
  t548 = t38 * t547
  t553 = 0.1e1 / t18 / t325
  t559 = 0.1e1 / t155
  t561 = 0.1e1 / t404 / t200
  t571 = t308 * t110
  t575 = t46 * t547
  t579 = t54 / t81
  t582 = t67 * t553
  t587 = t80 / t19 / t92
  t590 = t91 * t559
  t595 = t103 / t18 / t366
  t603 = t41 * t340
  t608 = 0.1e1 / t347 / t171
  t609 = t377 ** 2
  t647 = f.my_piecewise3(t177, 0.11e2 / 0.27e2 * t36 * t548 * t173 - 0.2e1 / 0.9e1 * t36 * t309 * t341 + 0.2e1 / 0.9e1 * t345 * t571 * t378 + t36 * t42 * (0.11e2 / 0.27e2 * t45 * t575 + 0.5e1 / 0.6e1 * t52 * t579 + 0.19e2 / 0.162e3 * t65 * t582 + 0.115e3 / 0.1296e4 * t78 * t587 + t90 * t590 / 0.8e1 + 0.217e3 / 0.15552e5 * t101 * t595) * t172 / 0.24e2 - t345 * t603 * t378 / 0.12e2 + t345 * t346 * t608 * t609 / 0.12e2 - t345 * t346 * t348 * (0.7e1 / 0.27e2 * t113 * t114 / t18 / t306 + 0.11e2 / 0.27e2 * t122 * t575 + 0.5e1 / 0.6e1 * t126 * t579 + 0.19e2 / 0.162e3 * t131 * t582 + 0.115e3 / 0.1296e4 * t136 * t587 + t140 * t590 / 0.8e1 + 0.217e3 / 0.15552e5 * t145 * t595 + 0.35e2 / 0.3888e4 * t152 * t154 / t19 / t166 + 0.13e2 / 0.1152e4 * t164 * t165 / t92 / t81) / 0.24e2, 0)
  t649 = 0.12717480330480143498498603175547901713438842405920e0 * t36 * t548 * t201 - 0.65032569871773461071867857147688133761903171393911e-2 * t402 * t37 * t553 * t405 + 0.48172273979091452645828042331620839823631978810304e-3 * t89 * t91 * t559 * t561 + 0.42141105276909202774570371431701910677713255063254e1 * t647
  t653 = t193 * t264
  t654 = t383 ** 2
  t660 = t29 * t350
  t662 = t27 * t660 * t189
  t665 = t27 * t302 * t388
  t667 = t387 ** 2
  t670 = t27 * t31 * t258 * t667
  t673 = t180 * t183 * t41
  t675 = t647 + 0.10e2 / 0.27e2 * t673
  t678 = t27 * t31 * t214 * t675
  t683 = t208 * t210 / t306 * t214
  t685 = t416 * t258
  t687 = t421 * t685 * t387
  t688 = t211 * t467
  t690 = t421 * t688 * t667
  t693 = t421 * t422 * t675
  t713 = t229 * t194 * t241
  t716 = t441 * t451
  t722 = 0.1e1 / t233 / t178
  t728 = 0.1e1 / t239 / t238
  t729 = t448 ** 2
  t732 = f.my_piecewise3(t236, t647, 0)
  t737 = 0.47459600000000000000000000000000000000000000000000e-1 * t649 * t194 + 0.94919200000000000000000000000000000000000000000000e-1 * t410 * t383 + 0.47459600000000000000000000000000000000000000000000e-1 * t206 * t647 + 0.56727466666666666666666666666666666666666666666666e-1 * t654 + 0.56727466666666666666666666666666666666666666666666e-1 * t194 * t647 - 0.54519192000000000000000000000000000000000000000000e1 * t194 * t654 - 0.27259596000000000000000000000000000000000000000000e1 * t220 * t647 - 0.35e2 / 0.4e1 * t713 * t654 - 0.7e1 * t716 * t383 - 0.7e1 / 0.2e1 * t442 * t647 - t230 * (-0.3e1 / 0.5e1 * t722 * t654 + 0.6e1 / 0.5e1 * t445 * t647 + 0.3e1 / 0.5e1 * t728 * t729 - 0.6e1 / 0.5e1 * t447 * t732)
  t759 = t256 ** 2
  t761 = 0.1e1 / t188 / t759
  t770 = -0.20e2 / 0.9e1 * t662 - 0.5e1 / 0.3e1 * t665 - 0.15e2 / 0.4e1 * t670 + 0.5e1 / 0.2e1 * t678 + 0.20e2 / 0.3e1 * t683 + 0.10e2 * t687 + 0.25e2 / 0.2e1 * t690 - 0.5e1 * t693 - 0.40e2 / 0.27e2 * t249 * t252 * t308 * t258 - 0.25e2 / 0.9e1 * t249 * t461 * t468 - 0.35e2 / 0.12e2 * t249 * t255 * t761 * t667 + 0.5e1 / 0.6e1 * t249 * t255 * t467 * t675
  t774 = t392 * t221
  t783 = 0.1e1 / t270 / t269
  t784 = t487 ** 2
  t786 = t783 * t784 / 0.12e2
  t788 = 0.10e2 / 0.3e1 * t673
  t791 = t484 * (0.9e1 * t647 + t788) / 0.6e1
  t793 = 0.1e1 / t273 / t272
  t794 = t491 ** 2
  t796 = t793 * t794 / 0.12e2
  t800 = t489 * (0.9e1 * t732 + t788) / 0.6e1
  t805 = t528 * t511
  t815 = 0.26366444444444444444444444444444444444444444444444e-1 * t649 * t218 * t221 + 0.94545777777777777777777777777777777777777777777778e-1 * t653 * t654 + 0.52732888888888888888888888888888888888888888888888e-1 * t410 * t426 * t221 + 0.26366444444444444444444444444444444444444444444444e-1 * t206 * (-0.4e1 / 0.9e1 * t662 - t665 / 0.3e1 - 0.3e1 / 0.4e1 * t670 + t678 / 0.2e1 + 0.2e1 / 0.3e1 * t683 + t687 + 0.5e1 / 0.4e1 * t690 - t693 / 0.2e1) * t221 - t737 * t262 * t264 / 0.9e1 - 0.2e1 / 0.9e1 * t453 * t472 * t264 - t243 * t770 * t264 / 0.9e1 - 0.94545777777777777777777777777777777777777777777778e-1 * t774 * t383 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t647 + 0.8e1 / 0.27e2 * t27 * t660 * t275 + 0.2e1 / 0.3e1 * t27 * t31 * (-t786 + t791 + t796 - t800) - 0.2e1 * t527 * t805 + 0.15819866666666666666666666666666666666666666666666e0 * t219 * t477 * t654 + 0.2e1 / 0.3e1 * t454 * t478 + 0.2e1 / 0.3e1 * t473 * t478
  t818 = 0.4e1 / 0.27e2 * t23 * t279 * t350
  t821 = t504 * t507
  t825 = 0.1e1 / t506 / t285
  t826 = t283 * t825
  t827 = t511 ** 2
  t834 = t818 - t214 * t667 / 0.4e1 + t189 * t675 / 0.2e1
  t846 = t292 ** 2
  t847 = 0.1e1 / t846
  t849 = t847 * t285 * t522
  t852 = t283 ** 2
  t853 = 0.1e1 / t852
  t855 = t853 * t285 * t504
  t863 = t515 * t511
  t867 = 0.1e1 / t476 / t194
  t881 = t522 * t507
  t884 = t292 * t825
  t903 = 0.2e1 * t178 * ((t818 - t786 + t791) * t286 - 0.2e1 * t821 * t511 + 0.2e1 * t826 * t827 - t508 * t834) * t516 + t263 * t477 * t647 / 0.3e1 - 0.4e1 / 0.9e1 * t27 * t302 * t494 + 0.2e1 * t527 * t849 - 0.2e1 * t514 * t855 - 0.10546577777777777777777777777777777777777777777778e0 * t427 * t430 + 0.4e1 * t383 * t513 * t516 + 0.2e1 * t514 * t863 - 0.4e1 / 0.3e1 * t263 * t867 * t654 - 0.52732888888888888888888888888888888888888888888888e-1 * t219 * t264 * t647 - 0.10546577777777777777777777777777777777777777777778e0 * t411 * t430 - 0.4e1 * t448 * t526 * t529 - 0.2e1 * t238 * ((t818 - t796 + t800) * t286 - 0.2e1 * t881 * t511 + 0.2e1 * t884 * t827 - t524 * t834) * t529 + 0.2e1 * t647 * t288 - 0.2e1 * t732 * t294 + 0.47272888888888888888888888888888888888888888888889e-1 * (-0.4e1 / 0.27e2 * t662 - t665 / 0.9e1 - t670 / 0.4e1 + t678 / 0.6e1) * t195
  t909 = f.my_piecewise3(t2, 0, t6 * t17 * t254 * t297 / 0.12e2 - t6 * t21 * t532 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t301 * (t815 + t903))
  v2rho2_0_ = 0.2e1 * r0 * t909 + 0.4e1 * t537
  t912 = t23 * t279
  t913 = t30 * t214
  t914 = t35 * t38
  t917 = t34 * t38
  t918 = t917 * t41
  t921 = t53 * t56
  t924 = s0 * t37
  t925 = t924 * t70
  t928 = t54 * t38
  t929 = t928 * t83
  t932 = t66 * t93
  t935 = t79 * t37
  t936 = t935 * t106
  t939 = t44 * t918 / 0.24e2 + t52 * t921 / 0.16e2 + t65 * t925 / 0.144e3 + 0.5e1 / 0.1152e4 * t78 * t929 + t90 * t932 / 0.192e3 + 0.7e1 / 0.13824e5 * t101 * t936
  t940 = t939 * t172
  t943 = 0.1e1 / t53
  t944 = t943 * t37
  t960 = t91 * t38
  t967 = t113 * t944 * t116 / 0.24e2 + t121 * t918 / 0.24e2 + t126 * t921 / 0.16e2 + t131 * t925 / 0.144e3 + 0.5e1 / 0.1152e4 * t136 * t929 + t140 * t932 / 0.192e3 + 0.7e1 / 0.13824e5 * t145 * t936 + t152 * t960 * t157 / 0.3456e4 + t164 * t102 * t167 / 0.3072e4
  t968 = t348 * t967
  t969 = t346 * t968
  t973 = f.my_piecewise3(t177, t914 * t346 * t172 / 0.24e2 + t36 * t42 * t940 / 0.24e2 - t345 * t969 / 0.24e2, 0)
  t974 = t973 * t195
  t984 = t37 * t70 * t405
  t988 = 0.13006513974354692214373571429537626752380634278782e-1 * t35 * t202 - 0.27096904113238942113278273811536722400792988080796e-3 * t401 * s0 * t984 + 0.42141105276909202774570371431701910677713255063254e1 * t973
  t989 = t988 * t218
  t992 = t214 * t973
  t994 = t27 * t31 * t992
  t996 = t421 * t422 * t973
  t998 = t994 / 0.2e1 - t996 / 0.2e1
  t999 = t206 * t998
  t1002 = t264 * t973
  t1009 = t194 * t973
  t1016 = f.my_piecewise3(t236, t973, 0)
  t1019 = -0.6e1 / 0.5e1 * t447 * t1016 + 0.6e1 / 0.5e1 * t445 * t973
  t1021 = 0.47459600000000000000000000000000000000000000000000e-1 * t988 * t194 + 0.47459600000000000000000000000000000000000000000000e-1 * t206 * t973 + 0.56727466666666666666666666666666666666666666666666e-1 * t1009 - 0.27259596000000000000000000000000000000000000000000e1 * t220 * t973 - 0.7e1 / 0.2e1 * t442 * t973 - t230 * t1019
  t1022 = t1021 * t262
  t1027 = t467 * t973
  t1031 = 0.5e1 / 0.2e1 * t994 - 0.5e1 * t996 + 0.5e1 / 0.6e1 * t249 * t255 * t1027
  t1032 = t243 * t1031
  t1035 = t477 * t973
  t1038 = t484 * t973
  t1039 = t489 * t1016
  t1041 = 0.3e1 / 0.2e1 * t1038 - 0.3e1 / 0.2e1 * t1039
  t1049 = t189 * t973
  t1052 = 0.3e1 / 0.2e1 * t1038 * t286 - t508 * t1049 / 0.2e1
  t1053 = t178 * t1052
  t1062 = 0.3e1 / 0.2e1 * t1039 * t286 - t524 * t1049 / 0.2e1
  t1063 = t238 * t1062
  t1066 = 0.78788148148148148148148148148148148148148148148148e-2 * t912 * t913 * t974 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t973 + 0.26366444444444444444444444444444444444444444444444e-1 * t989 * t221 + 0.26366444444444444444444444444444444444444444444444e-1 * t999 * t221 - 0.52732888888888888888888888888888888888888888888888e-1 * t219 * t1002 - t1022 * t264 / 0.9e1 - t1032 * t264 / 0.9e1 + t263 * t1035 / 0.3e1 + 0.2e1 / 0.3e1 * t27 * t31 * t1041 + 0.2e1 * t973 * t288 + 0.2e1 * t1053 * t516 - 0.2e1 * t1016 * t294 - 0.2e1 * t1063 * t529
  t1070 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t301 * t1066)
  t1081 = t30 * t258
  t1098 = t783 * t973
  t1112 = t917 * t308
  t1115 = t53 * t316
  t1118 = t924 * t321
  t1121 = t928 * t327
  t1124 = t66 * t331
  t1127 = t935 * t336
  t1135 = t41 * t939
  t1177 = f.my_piecewise3(t177, -t914 * t571 * t172 / 0.9e1 + t914 * t603 * t172 / 0.24e2 - t914 * t379 / 0.24e2 - t36 * t309 * t940 / 0.9e1 + t36 * t42 * (-t44 * t1112 / 0.9e1 - t52 * t1115 / 0.4e1 - t65 * t1118 / 0.27e2 - 0.25e2 / 0.864e3 * t78 * t1121 - t90 * t1124 / 0.24e2 - 0.49e2 / 0.10368e5 * t101 * t1127) * t172 / 0.24e2 - t345 * t1135 * t378 / 0.24e2 + t345 * t571 * t968 / 0.9e1 - t345 * t603 * t968 / 0.24e2 + t345 * t346 * t608 * t967 * t377 / 0.12e2 - t345 * t346 * t348 * (-t113 * t944 * t350 / 0.18e2 - t121 * t1112 / 0.9e1 - t126 * t1115 / 0.4e1 - t131 * t1118 / 0.27e2 - 0.25e2 / 0.864e3 * t136 * t1121 - t140 * t1124 / 0.24e2 - 0.49e2 / 0.10368e5 * t145 * t1127 - t152 * t960 * t368 / 0.324e3 - t164 * t102 * t373 / 0.256e3) / 0.24e2, 0)
  t1178 = t484 * t1177
  t1180 = t793 * t1016
  t1183 = f.my_piecewise3(t236, t1177, 0)
  t1184 = t489 * t1183
  t1214 = -0.34684037264945845904996190478767004673015024743419e-1 * t35 * t398 + 0.21677523290591153690622619049229377920634390464637e-2 * t401 * t37 * t321 * t405 * s0 - 0.18064602742159294742185515874357814933861992053864e-3 * t89 * t66 * t331 * t561 + 0.42141105276909202774570371431701910677713255063254e1 * t1177
  t1225 = t27 * t302 * t992
  t1227 = t973 * t387
  t1229 = t912 * t1081 * t1227
  t1233 = t27 * t31 * t214 * t1177
  t1236 = t421 * t685 * t973
  t1239 = t421 * t688 * t1227
  t1242 = t421 * t422 * t1177
  t1256 = t383 * t973
  t1270 = t441 * t1019
  t1285 = 0.47459600000000000000000000000000000000000000000000e-1 * t1214 * t194 + 0.47459600000000000000000000000000000000000000000000e-1 * t988 * t383 + 0.47459600000000000000000000000000000000000000000000e-1 * t410 * t973 + 0.47459600000000000000000000000000000000000000000000e-1 * t206 * t1177 + 0.56727466666666666666666666666666666666666666666666e-1 * t1256 + 0.56727466666666666666666666666666666666666666666666e-1 * t194 * t1177 - 0.54519192000000000000000000000000000000000000000000e1 * t1009 * t383 - 0.27259596000000000000000000000000000000000000000000e1 * t220 * t1177 - 0.35e2 / 0.4e1 * t713 * t1256 - 0.7e1 / 0.2e1 * t716 * t973 - 0.7e1 / 0.2e1 * t442 * t1177 - 0.7e1 / 0.2e1 * t1270 * t383 - t230 * (-0.3e1 / 0.5e1 * t722 * t973 * t383 + 0.6e1 / 0.5e1 * t445 * t1177 + 0.3e1 / 0.5e1 * t728 * t1016 * t448 - 0.6e1 / 0.5e1 * t447 * t1183)
  t1318 = 0.2e1 * t1063 * t849 - 0.2e1 * t1053 * t855 - 0.2e1 / 0.9e1 * t27 * t302 * t1041 - 0.11818222222222222222222222222222222222222222222222e-1 * t912 * t1081 * t974 * t387 - 0.78788148148148148148148148148148148148148148148148e-2 * t912 * t913 * t973 * t221 * t383 + 0.15819866666666666666666666666666666666666666666666e0 * t219 * t1035 * t383 - 0.4e1 / 0.3e1 * t263 * t867 * t973 * t383 + 0.2e1 / 0.3e1 * t27 * t31 * (-0.3e1 / 0.4e1 * t1098 * t487 + 0.3e1 / 0.2e1 * t1178 + 0.3e1 / 0.4e1 * t1180 * t491 - 0.3e1 / 0.2e1 * t1184) - 0.26262716049382716049382716049382716049382716049383e-2 * t912 * t116 * t214 * t974 + 0.78788148148148148148148148148148148148148148148148e-2 * t912 * t913 * t1177 * t195 - 0.47272888888888888888888888888888888888888888888889e-1 * t774 * t973 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t1177 + 0.26366444444444444444444444444444444444444444444444e-1 * t1214 * t218 * t221 + 0.26366444444444444444444444444444444444444444444444e-1 * t988 * t426 * t221 + 0.26366444444444444444444444444444444444444444444444e-1 * t410 * t998 * t221 + 0.26366444444444444444444444444444444444444444444444e-1 * t206 * (-t1225 / 0.6e1 - 0.3e1 / 0.4e1 * t1229 + t1233 / 0.2e1 + t1236 / 0.2e1 + 0.5e1 / 0.4e1 * t1239 - t1242 / 0.2e1) * t221 - t1285 * t262 * t264 / 0.9e1 - t1021 * t472 * t264 / 0.9e1 - t453 * t1031 * t264 / 0.9e1 - t243 * (-0.5e1 / 0.6e1 * t1225 - 0.15e2 / 0.4e1 * t1229 + 0.5e1 / 0.2e1 * t1233 + 0.5e1 * t1236 + 0.25e2 / 0.2e1 * t1239 - 0.5e1 * t1242 - 0.25e2 / 0.18e2 * t249 * t461 * t1027 - 0.35e2 / 0.12e2 * t248 * t77 * t252 * t254 * t761 * t1227 + 0.5e1 / 0.6e1 * t249 * t255 * t467 * t1177) * t264 / 0.9e1
  t1350 = t507 * t511
  t1355 = t1049 * t511
  t1357 = t992 * t387
  t1360 = t189 * t1177
  t1404 = -0.52732888888888888888888888888888888888888888888888e-1 * t411 * t1002 - 0.2e1 * t238 * (-0.3e1 / 0.4e1 * t1180 * t286 * t491 + 0.3e1 / 0.2e1 * t1184 * t286 - 0.3e1 / 0.2e1 * t1039 * t1350 - t881 * t1049 / 0.2e1 + t884 * t1355 + t524 * t1357 / 0.4e1 - t524 * t1360 / 0.2e1) * t529 - 0.2e1 * t1016 * t526 * t529 + 0.2e1 * t1053 * t863 - 0.2e1 * t1063 * t805 + t1022 * t478 / 0.3e1 + t473 * t1035 / 0.3e1 + t454 * t1035 / 0.3e1 + 0.2e1 * t178 * (-0.3e1 / 0.4e1 * t1098 * t286 * t487 + 0.3e1 / 0.2e1 * t1178 * t286 - 0.3e1 / 0.2e1 * t1038 * t1350 - t821 * t1049 / 0.2e1 + t826 * t1355 + t508 * t1357 / 0.4e1 - t508 * t1360 / 0.2e1) * t516 + t263 * t477 * t1177 / 0.3e1 - 0.2e1 * t448 * t1062 * t529
  t1411 = f.my_piecewise3(t2, 0, -t6 * t21 * t1066 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t301 * (t1318 + 0.2e1 * t1177 * t288 - 0.2e1 * t1183 * t294 + 0.2e1 * t383 * t1052 * t516 + t1032 * t478 / 0.3e1 + 0.94545777777777777777777777777777777777777777777778e-1 * t653 * t1256 - 0.52732888888888888888888888888888888888888888888888e-1 * t427 * t1002 - 0.52732888888888888888888888888888888888888888888888e-1 * t219 * t264 * t1177 - 0.52732888888888888888888888888888888888888888888888e-1 * t989 * t430 - 0.52732888888888888888888888888888888888888888888888e-1 * t999 * t430 + 0.2e1 * t973 * t513 * t516 + t1404))
  v2rhosigma_0_ = 0.2e1 * r0 * t1411 + 0.2e1 * t1070
  t1422 = t973 ** 2
  t1423 = t783 * t1422
  t1430 = t943 * t56
  t1434 = t64 * t37 * t70
  t1438 = t53 * t38 * t83
  t1441 = s0 * t93
  t1445 = t54 * t37 * t106
  t1456 = t967 ** 2
  t1489 = f.my_piecewise3(t177, t914 * t1135 * t172 / 0.12e2 - t914 * t969 / 0.12e2 + t36 * t42 * (t52 * t1430 / 0.32e2 + t62 * t1434 / 0.144e3 + 0.5e1 / 0.768e3 * t78 * t1438 + t90 * t1441 / 0.96e2 + 0.35e2 / 0.27648e5 * t101 * t1445) * t172 / 0.24e2 - t345 * t1135 * t968 / 0.12e2 + t345 * t346 * t608 * t1456 / 0.12e2 - t345 * t346 * t348 * (-t113 / t54 * t37 * t116 / 0.48e2 + t126 * t1430 / 0.32e2 + t130 * t1434 / 0.144e3 + 0.5e1 / 0.768e3 * t136 * t1438 + t140 * t1441 / 0.96e2 + 0.35e2 / 0.27648e5 * t145 * t1445 + t152 * t66 * t38 * t157 / 0.1152e4 + 0.7e1 / 0.6144e4 * t164 * t79 * t167) / 0.24e2, 0)
  t1490 = t484 * t1489
  t1492 = t1016 ** 2
  t1493 = t793 * t1492
  t1495 = f.my_piecewise3(t236, t1489, 0)
  t1496 = t489 * t1495
  t1511 = t507 * t189
  t1516 = 0.1e1 / t187 * t1422
  t1519 = t214 * t1422
  t1522 = t189 * t1489
  t1570 = t1053 * t515 * t189 * t973 + 0.3e1 * t1063 * t847 * t285 * t489 * t1016 + 0.2e1 / 0.3e1 * t27 * t31 * (-0.27e2 / 0.4e1 * t1423 + 0.3e1 / 0.2e1 * t1490 + 0.27e2 / 0.4e1 * t1493 - 0.3e1 / 0.2e1 * t1496) - 0.3e1 * t1053 * t853 * t285 * t484 * t973 - 0.2e1 * t238 * (-0.27e2 / 0.4e1 * t1493 * t286 + 0.3e1 / 0.2e1 * t1496 * t286 - 0.3e1 / 0.2e1 * t1039 * t1511 * t973 + t884 * t1516 / 0.2e1 + t524 * t1519 / 0.4e1 - t524 * t1522 / 0.2e1) * t529 + t263 * t477 * t1489 / 0.3e1 - 0.10546577777777777777777777777777777777777777777778e0 * t989 * t1002 - 0.4e1 / 0.3e1 * t263 * t867 * t1422 - 0.10546577777777777777777777777777777777777777777778e0 * t999 * t1002 - 0.52732888888888888888888888888888888888888888888888e-1 * t219 * t264 * t1489 + 0.2e1 / 0.3e1 * t1032 * t1035 + 0.4e1 * t973 * t1052 * t516 + 0.2e1 * t178 * (-0.27e2 / 0.4e1 * t1423 * t286 + 0.3e1 / 0.2e1 * t1490 * t286 - 0.3e1 / 0.2e1 * t484 * t1422 * t1511 + t826 * t1516 / 0.2e1 + t508 * t1519 / 0.4e1 - t508 * t1522 / 0.2e1) * t516 + 0.15819866666666666666666666666666666666666666666666e0 * t219 * t477 * t1422 - 0.4e1 * t1016 * t1062 * t529
  t1584 = -0.54193808226477884226556547623073444801585976161592e-3 * t401 * t984 + 0.67742260283097355283195684528841806001982470201990e-4 * t89 * s0 * t93 * t561 + 0.42141105276909202774570371431701910677713255063254e1 * t1489
  t1593 = t27 * t31 * t258 * t1422
  t1597 = t27 * t31 * t214 * t1489
  t1600 = t421 * t688 * t1422
  t1603 = t421 * t422 * t1489
  t1638 = 0.47459600000000000000000000000000000000000000000000e-1 * t1584 * t194 + 0.94919200000000000000000000000000000000000000000000e-1 * t988 * t973 + 0.47459600000000000000000000000000000000000000000000e-1 * t206 * t1489 + 0.56727466666666666666666666666666666666666666666666e-1 * t1422 + 0.56727466666666666666666666666666666666666666666666e-1 * t194 * t1489 - 0.54519192000000000000000000000000000000000000000000e1 * t194 * t1422 - 0.27259596000000000000000000000000000000000000000000e1 * t220 * t1489 - 0.35e2 / 0.4e1 * t713 * t1422 - 0.7e1 * t1270 * t973 - 0.7e1 / 0.2e1 * t442 * t1489 - t230 * (-0.3e1 / 0.5e1 * t722 * t1422 + 0.6e1 / 0.5e1 * t445 * t1489 + 0.3e1 / 0.5e1 * t728 * t1492 - 0.6e1 / 0.5e1 * t447 * t1495)
  t1680 = 0.2e1 / 0.3e1 * t1022 * t1035 + 0.94545777777777777777777777777777777777777777777778e-1 * t653 * t1422 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t1489 + 0.26366444444444444444444444444444444444444444444444e-1 * t1584 * t218 * t221 + 0.52732888888888888888888888888888888888888888888888e-1 * t988 * t998 * t221 + 0.26366444444444444444444444444444444444444444444444e-1 * t206 * (-0.3e1 / 0.4e1 * t1593 + t1597 / 0.2e1 + 0.5e1 / 0.4e1 * t1600 - t1603 / 0.2e1) * t221 - t1638 * t262 * t264 / 0.9e1 - 0.2e1 / 0.9e1 * t1021 * t1031 * t264 - t243 * (-0.15e2 / 0.4e1 * t1593 + 0.5e1 / 0.2e1 * t1597 + 0.25e2 / 0.2e1 * t1600 - 0.5e1 * t1603 - 0.35e2 / 0.12e2 * t249 * t255 * t761 * t1422 + 0.5e1 / 0.6e1 * t249 * t255 * t467 * t1489) * t264 / 0.9e1 + 0.2e1 * t1489 * t288 - 0.2e1 * t1495 * t294 - t1063 * t528 * t189 * t973 + 0.78788148148148148148148148148148148148148148148148e-2 * t912 * t913 * t1489 * t195 - 0.11818222222222222222222222222222222222222222222222e-1 * t912 * t1081 * t1422 * t195 - 0.15757629629629629629629629629629629629629629629630e-1 * t912 * t913 * t1422 * t221
  t1685 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t301 * (t1570 + t1680))
  v2sigma2_0_ = 0.2e1 * r0 * t1685

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
  t12 = t11 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t12, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = 0.1e1 / t19 / r0
  t22 = t17 * t21
  t23 = t3 ** 2
  t24 = f.p.cam_omega * t23
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = 0.1e1 / t26
  t28 = t24 * t27
  t29 = f.my_piecewise3(t12, t13, t15)
  t30 = 0.1e1 / t29
  t31 = 0.1e1 / t18
  t32 = t30 * t31
  t33 = 6 ** (0.1e1 / 0.3e1)
  t34 = t26 ** 2
  t35 = 0.1e1 / t34
  t36 = t33 * t35
  t37 = t36 * s0
  t38 = 2 ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = r0 ** 2
  t42 = 0.1e1 / t19 / t40
  t43 = t39 * t42
  t46 = params.a[0] * t33 * t35
  t47 = s0 * t39
  t48 = t47 * t42
  t52 = 0.1e1 / t25
  t53 = params.a[1] * t52
  t54 = jnp.sqrt(s0)
  t55 = t54 * s0
  t56 = t40 ** 2
  t57 = 0.1e1 / t56
  t58 = t55 * t57
  t62 = t33 ** 2
  t65 = 0.1e1 / t26 / t25
  t66 = params.a[2] * t62 * t65
  t67 = s0 ** 2
  t68 = t67 * t38
  t69 = t56 * r0
  t72 = t68 / t18 / t69
  t78 = 0.1e1 / t34 / t25
  t79 = params.a[3] * t33 * t78
  t81 = t54 * t67 * t39
  t82 = t56 * t40
  t85 = t81 / t19 / t82
  t89 = t25 ** 2
  t90 = 0.1e1 / t89
  t91 = params.a[4] * t90
  t92 = t67 * s0
  t93 = t56 ** 2
  t95 = t92 / t93
  t101 = 0.1e1 / t26 / t89
  t102 = params.a[5] * t62 * t101
  t104 = t54 * t92 * t38
  t105 = t93 * r0
  t108 = t104 / t18 / t105
  t111 = t46 * t48 / 0.24e2 + t53 * t58 / 0.24e2 + t66 * t72 / 0.288e3 + t79 * t85 / 0.576e3 + t91 * t95 / 0.576e3 + t102 * t108 / 0.6912e4
  t114 = params.b[0] * t62 * t27
  t115 = t54 * t38
  t117 = 0.1e1 / t18 / r0
  t123 = params.b[1] * t33 * t35
  t127 = params.b[2] * t52
  t132 = params.b[3] * t62 * t65
  t137 = params.b[4] * t33 * t78
  t141 = params.b[5] * t90
  t146 = params.b[6] * t62 * t101
  t153 = params.b[7] * t33 / t34 / t89
  t154 = t67 ** 2
  t155 = t154 * t39
  t156 = t93 * t40
  t165 = params.b[8] / t89 / t25
  t166 = t54 * t154
  t167 = t93 * t56
  t172 = 0.1e1 + t114 * t115 * t117 / 0.12e2 + t123 * t48 / 0.24e2 + t127 * t58 / 0.24e2 + t132 * t72 / 0.288e3 + t137 * t85 / 0.576e3 + t141 * t95 / 0.576e3 + t146 * t108 / 0.6912e4 + t153 * t155 / t19 / t156 / 0.13824e5 + t165 * t166 / t167 / 0.13824e5
  t173 = 0.1e1 / t172
  t174 = t111 * t173
  t177 = t37 * t43 * t174 / 0.24e2
  t178 = 0.1e-9 < t177
  t179 = f.my_piecewise3(t178, t177, 0.1e-9)
  t180 = f.p.cam_omega ** 2
  t181 = t180 * t3
  t182 = t29 ** 2
  t184 = t35 / t182
  t185 = 0.1e1 / t19
  t187 = t181 * t184 * t185
  t189 = 0.609650e0 + t179 + t187 / 0.3e1
  t190 = jnp.sqrt(t189)
  t191 = 0.1e1 / t190
  t193 = t28 * t32 * t191
  t195 = 0.1e1 - t193 / 0.3e1
  t196 = 0.609650e0 + t179
  t197 = 0.1e1 / t196
  t202 = 0.1e1 + t36 * t48 / 0.96e2
  t203 = 0.1e1 / t202
  t208 = 0.1e1 + 0.13006513974354692214373571429537626752380634278782e-1 * t37 * t43 * t203 + 0.42141105276909202774570371431701910677713255063254e1 * t179
  t210 = t180 * f.p.cam_omega * t52
  t212 = 0.1e1 / t182 / t29
  t213 = 0.1e1 / r0
  t216 = 0.1e1 / t190 / t189
  t218 = t210 * t212 * t213 * t216
  t220 = 0.2e1 - t193 + t218 / 0.3e1
  t221 = t208 * t220
  t222 = t196 ** 2
  t223 = 0.1e1 / t222
  t229 = t222 * t196
  t231 = jnp.sqrt(t196)
  t232 = t231 * t229
  t233 = jnp.sqrt(jnp.pi)
  t235 = jnp.sqrt(t179)
  t238 = 0.0e0 < 0.7572109999e0 + t179
  t240 = f.my_piecewise3(t238, 0.757211e0 + t179, 0.1e-9)
  t241 = jnp.sqrt(t240)
  t243 = 0.4e1 / 0.5e1 * t233 + 0.12e2 / 0.5e1 * t235 - 0.12e2 / 0.5e1 * t241
  t245 = 0.47459600000000000000000000000000000000000000000000e-1 * t208 * t196 + 0.28363733333333333333333333333333333333333333333333e-1 * t222 - 0.90865320000000000000000000000000000000000000000000e0 * t229 - t232 * t243
  t248 = t180 ** 2
  t250 = t248 * f.p.cam_omega * t3
  t251 = t250 * t78
  t252 = t182 ** 2
  t254 = 0.1e1 / t252 / t29
  t255 = t254 * t21
  t256 = t189 ** 2
  t258 = 0.1e1 / t190 / t256
  t262 = 0.8e1 - 0.5e1 * t193 + 0.10e2 / 0.3e1 * t218 - t251 * t255 * t258 / 0.3e1
  t263 = t245 * t262
  t264 = 0.1e1 / t229
  t268 = 0.3e1 * t187
  t269 = 0.9e1 * t179 + t268
  t270 = jnp.sqrt(t269)
  t272 = 0.9e1 * t240 + t268
  t273 = jnp.sqrt(t272)
  t275 = t270 / 0.3e1 - t273 / 0.3e1
  t279 = t27 * t30
  t281 = t24 * t279 * t31
  t283 = t281 / 0.3e1 + t270 / 0.3e1
  t285 = t281 / 0.3e1 + t190
  t286 = 0.1e1 / t285
  t288 = jnp.log(t283 * t286)
  t292 = t281 / 0.3e1 + t273 / 0.3e1
  t294 = jnp.log(t292 * t286)
  t297 = 0.757211e0 + 0.47272888888888888888888888888888888888888888888889e-1 * t195 * t197 + 0.26366444444444444444444444444444444444444444444444e-1 * t221 * t223 - t263 * t264 / 0.9e1 + 0.2e1 / 0.3e1 * t28 * t32 * t275 + 0.2e1 * t179 * t288 - 0.2e1 * t240 * t294
  t301 = t17 * t185
  t302 = t30 * t117
  t304 = t28 * t302 * t191
  t306 = t40 * r0
  t308 = 0.1e1 / t19 / t306
  t309 = t39 * t308
  t313 = t47 * t308
  t317 = t55 / t69
  t321 = 0.1e1 / t18 / t82
  t322 = t68 * t321
  t325 = t56 * t306
  t328 = t81 / t19 / t325
  t332 = t92 / t105
  t337 = t104 / t18 / t156
  t340 = -t46 * t313 / 0.9e1 - t53 * t317 / 0.6e1 - t66 * t322 / 0.54e2 - 0.5e1 / 0.432e3 * t79 * t328 - t91 * t332 / 0.72e2 - 0.7e1 / 0.5184e4 * t102 * t337
  t341 = t340 * t173
  t345 = t36 * t47
  t346 = t42 * t111
  t347 = t172 ** 2
  t348 = 0.1e1 / t347
  t350 = 0.1e1 / t18 / t40
  t366 = t93 * t306
  t372 = t93 * t69
  t377 = -t114 * t115 * t350 / 0.9e1 - t123 * t313 / 0.9e1 - t127 * t317 / 0.6e1 - t132 * t322 / 0.54e2 - 0.5e1 / 0.432e3 * t137 * t328 - t141 * t332 / 0.72e2 - 0.7e1 / 0.5184e4 * t146 * t337 - t153 * t155 / t19 / t366 / 0.1296e4 - t165 * t166 / t372 / 0.1152e4
  t378 = t348 * t377
  t383 = f.my_piecewise3(t178, -t37 * t309 * t174 / 0.9e1 + t37 * t43 * t341 / 0.24e2 - t345 * t346 * t378 / 0.24e2, 0)
  t385 = t181 * t184 * t21
  t387 = t383 - 0.2e1 / 0.9e1 * t385
  t388 = t216 * t387
  t390 = t28 * t32 * t388
  t392 = t304 / 0.9e1 + t390 / 0.6e1
  t395 = t195 * t223
  t402 = t62 * t65 * t67
  t404 = t202 ** 2
  t405 = 0.1e1 / t404
  t410 = -0.34684037264945845904996190478767004673015024743419e-1 * t37 * t309 * t203 + 0.72258410968637178968742063497431259735447968215456e-3 * t402 * t38 * t321 * t405 + 0.42141105276909202774570371431701910677713255063254e1 * t383
  t411 = t410 * t220
  t416 = 0.1e1 / t40
  t419 = t210 * t212 * t416 * t216
  t421 = t210 * t212
  t422 = t213 * t258
  t424 = t421 * t422 * t387
  t426 = t304 / 0.3e1 + t390 / 0.2e1 - t419 / 0.3e1 - t424 / 0.2e1
  t427 = t208 * t426
  t430 = t264 * t383
  t437 = t196 * t383
  t441 = t231 * t222
  t442 = t441 * t243
  t445 = 0.1e1 / t235
  t447 = 0.1e1 / t241
  t448 = f.my_piecewise3(t238, t383, 0)
  t451 = 0.6e1 / 0.5e1 * t445 * t383 - 0.6e1 / 0.5e1 * t447 * t448
  t453 = 0.47459600000000000000000000000000000000000000000000e-1 * t410 * t196 + 0.47459600000000000000000000000000000000000000000000e-1 * t208 * t383 + 0.56727466666666666666666666666666666666666666666666e-1 * t437 - 0.27259596000000000000000000000000000000000000000000e1 * t222 * t383 - 0.7e1 / 0.2e1 * t442 * t383 - t232 * t451
  t454 = t453 * t262
  t461 = t254 * t42
  t467 = 0.1e1 / t190 / t256 / t189
  t468 = t467 * t387
  t472 = 0.5e1 / 0.3e1 * t304 + 0.5e1 / 0.2e1 * t390 - 0.10e2 / 0.3e1 * t419 - 0.5e1 * t424 + 0.5e1 / 0.9e1 * t251 * t461 * t258 + 0.5e1 / 0.6e1 * t251 * t255 * t468
  t473 = t245 * t472
  t476 = t222 ** 2
  t477 = 0.1e1 / t476
  t478 = t477 * t383
  t484 = 0.1e1 / t270
  t486 = 0.2e1 * t385
  t487 = 0.9e1 * t383 - t486
  t488 = t484 * t487
  t489 = 0.1e1 / t273
  t491 = 0.9e1 * t448 - t486
  t492 = t489 * t491
  t494 = t488 / 0.6e1 - t492 / 0.6e1
  t502 = t24 * t279 * t117 / 0.9e1
  t504 = -t502 + t488 / 0.6e1
  t506 = t285 ** 2
  t507 = 0.1e1 / t506
  t508 = t283 * t507
  t511 = -t502 + t191 * t387 / 0.2e1
  t513 = t504 * t286 - t508 * t511
  t514 = t179 * t513
  t515 = 0.1e1 / t283
  t516 = t515 * t285
  t522 = -t502 + t492 / 0.6e1
  t524 = t292 * t507
  t526 = t522 * t286 - t524 * t511
  t527 = t240 * t526
  t528 = 0.1e1 / t292
  t529 = t528 * t285
  t532 = 0.47272888888888888888888888888888888888888888888889e-1 * t392 * t197 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t383 + 0.26366444444444444444444444444444444444444444444444e-1 * t411 * t223 + 0.26366444444444444444444444444444444444444444444444e-1 * t427 * t223 - 0.52732888888888888888888888888888888888888888888888e-1 * t221 * t430 - t454 * t264 / 0.9e1 - t473 * t264 / 0.9e1 + t263 * t478 / 0.3e1 - 0.2e1 / 0.9e1 * t28 * t302 * t275 + 0.2e1 / 0.3e1 * t28 * t32 * t494 + 0.2e1 * t383 * t288 + 0.2e1 * t514 * t516 - 0.2e1 * t448 * t294 - 0.2e1 * t527 * t529
  t536 = t17 * t18
  t539 = 0.4e1 / 0.27e2 * t24 * t279 * t350
  t541 = 0.1e1 / t270 / t269
  t542 = t487 ** 2
  t544 = t541 * t542 / 0.12e2
  t546 = 0.1e1 / t19 / t56
  t547 = t39 * t546
  t554 = t308 * t111
  t558 = t47 * t546
  t562 = t55 / t82
  t566 = 0.1e1 / t18 / t325
  t567 = t68 * t566
  t572 = t81 / t19 / t93
  t575 = 0.1e1 / t156
  t576 = t92 * t575
  t581 = t104 / t18 / t366
  t584 = 0.11e2 / 0.27e2 * t46 * t558 + 0.5e1 / 0.6e1 * t53 * t562 + 0.19e2 / 0.162e3 * t66 * t567 + 0.115e3 / 0.1296e4 * t79 * t572 + t91 * t576 / 0.8e1 + 0.217e3 / 0.15552e5 * t102 * t581
  t585 = t584 * t173
  t589 = t42 * t340
  t594 = 0.1e1 / t347 / t172
  t595 = t377 ** 2
  t596 = t594 * t595
  t601 = 0.1e1 / t18 / t306
  t627 = 0.7e1 / 0.27e2 * t114 * t115 * t601 + 0.11e2 / 0.27e2 * t123 * t558 + 0.5e1 / 0.6e1 * t127 * t562 + 0.19e2 / 0.162e3 * t132 * t567 + 0.115e3 / 0.1296e4 * t137 * t572 + t141 * t576 / 0.8e1 + 0.217e3 / 0.15552e5 * t146 * t581 + 0.35e2 / 0.3888e4 * t153 * t155 / t19 / t167 + 0.13e2 / 0.1152e4 * t165 * t166 / t93 / t82
  t628 = t348 * t627
  t633 = f.my_piecewise3(t178, 0.11e2 / 0.27e2 * t37 * t547 * t174 - 0.2e1 / 0.9e1 * t37 * t309 * t341 + 0.2e1 / 0.9e1 * t345 * t554 * t378 + t37 * t43 * t585 / 0.24e2 - t345 * t589 * t378 / 0.12e2 + t345 * t346 * t596 / 0.12e2 - t345 * t346 * t628 / 0.24e2, 0)
  t636 = t181 * t184 * t42
  t637 = 0.10e2 / 0.3e1 * t636
  t638 = 0.9e1 * t633 + t637
  t640 = t484 * t638 / 0.6e1
  t641 = t539 - t544 + t640
  t643 = t504 * t507
  t647 = 0.1e1 / t506 / t285
  t648 = t283 * t647
  t649 = t511 ** 2
  t652 = t387 ** 2
  t656 = t633 + 0.10e2 / 0.27e2 * t636
  t659 = t539 - t216 * t652 / 0.4e1 + t191 * t656 / 0.2e1
  t661 = t641 * t286 - t508 * t659 - 0.2e1 * t643 * t511 + 0.2e1 * t648 * t649
  t662 = t179 * t661
  t665 = t264 * t633
  t668 = t528 * t511
  t671 = t383 ** 2
  t672 = t477 * t671
  t677 = t383 * t513
  t681 = 0.1e1 / t273 / t272
  t682 = t491 ** 2
  t684 = t681 * t682 / 0.12e2
  t685 = f.my_piecewise3(t238, t633, 0)
  t687 = 0.9e1 * t685 + t637
  t689 = t489 * t687 / 0.6e1
  t690 = t539 - t684 + t689
  t692 = t522 * t507
  t695 = t292 * t647
  t699 = t690 * t286 - 0.2e1 * t692 * t511 - t524 * t659 + 0.2e1 * t695 * t649
  t700 = t240 * t699
  t703 = t515 * t511
  t707 = 0.1e1 / t476 / t196
  t708 = t707 * t671
  t715 = t477 * t633
  t720 = t448 * t526
  t723 = -t544 + t640 + t684 - t689
  t727 = 0.2e1 * t662 * t516 - 0.52732888888888888888888888888888888888888888888888e-1 * t221 * t665 - 0.2e1 * t527 * t668 + 0.15819866666666666666666666666666666666666666666666e0 * t221 * t672 + 0.2e1 / 0.3e1 * t454 * t478 + 0.4e1 * t677 * t516 - 0.2e1 * t700 * t529 + 0.2e1 * t514 * t703 - 0.4e1 / 0.3e1 * t263 * t708 - 0.10546577777777777777777777777777777777777777777778e0 * t411 * t430 + 0.2e1 / 0.3e1 * t473 * t478 + t263 * t715 / 0.3e1 - 0.10546577777777777777777777777777777777777777777778e0 * t427 * t430 - 0.4e1 * t720 * t529 + 0.2e1 / 0.3e1 * t28 * t32 * t723
  t731 = t283 ** 2
  t732 = 0.1e1 / t731
  t733 = t732 * t285
  t734 = t733 * t504
  t737 = t30 * t350
  t741 = t292 ** 2
  t742 = 0.1e1 / t741
  t743 = t742 * t285
  t744 = t743 * t522
  t747 = t410 * t426
  t751 = t28 * t737 * t191
  t754 = t28 * t302 * t388
  t756 = t258 * t652
  t758 = t28 * t32 * t756
  t760 = t216 * t656
  t762 = t28 * t32 * t760
  t764 = 0.1e1 / t306
  t767 = t210 * t212 * t764 * t216
  t769 = t416 * t258
  t771 = t421 * t769 * t387
  t772 = t213 * t467
  t774 = t421 * t772 * t652
  t777 = t421 * t422 * t656
  t779 = -0.4e1 / 0.9e1 * t751 - t754 / 0.3e1 - 0.3e1 / 0.4e1 * t758 + t762 / 0.2e1 + 0.2e1 / 0.3e1 * t767 + t771 + 0.5e1 / 0.4e1 * t774 - t777 / 0.2e1
  t780 = t208 * t779
  t783 = t453 * t472
  t786 = t195 * t264
  t797 = t254 * t308
  t804 = t256 ** 2
  t806 = 0.1e1 / t190 / t804
  t807 = t806 * t652
  t811 = t467 * t656
  t815 = -0.20e2 / 0.9e1 * t751 - 0.5e1 / 0.3e1 * t754 - 0.15e2 / 0.4e1 * t758 + 0.5e1 / 0.2e1 * t762 + 0.20e2 / 0.3e1 * t767 + 0.10e2 * t771 + 0.25e2 / 0.2e1 * t774 - 0.5e1 * t777 - 0.40e2 / 0.27e2 * t251 * t797 * t258 - 0.25e2 / 0.9e1 * t251 * t461 * t468 - 0.35e2 / 0.12e2 * t251 * t255 * t807 + 0.5e1 / 0.6e1 * t251 * t255 * t811
  t816 = t245 * t815
  t819 = t392 * t223
  t831 = t90 * t92
  t833 = 0.1e1 / t404 / t202
  t838 = 0.12717480330480143498498603175547901713438842405920e0 * t37 * t547 * t203 - 0.65032569871773461071867857147688133761903171393911e-2 * t402 * t38 * t566 * t405 + 0.48172273979091452645828042331620839823631978810304e-3 * t831 * t575 * t833 + 0.42141105276909202774570371431701910677713255063254e1 * t633
  t839 = t838 * t220
  t855 = t231 * t196
  t856 = t855 * t243
  t859 = t441 * t451
  t865 = 0.1e1 / t235 / t179
  t871 = 0.1e1 / t241 / t240
  t872 = t448 ** 2
  t877 = -0.3e1 / 0.5e1 * t865 * t671 + 0.6e1 / 0.5e1 * t445 * t633 + 0.3e1 / 0.5e1 * t871 * t872 - 0.6e1 / 0.5e1 * t447 * t685
  t879 = 0.47459600000000000000000000000000000000000000000000e-1 * t838 * t196 + 0.94919200000000000000000000000000000000000000000000e-1 * t410 * t383 + 0.47459600000000000000000000000000000000000000000000e-1 * t208 * t633 + 0.56727466666666666666666666666666666666666666666666e-1 * t671 + 0.56727466666666666666666666666666666666666666666666e-1 * t196 * t633 - 0.54519192000000000000000000000000000000000000000000e1 * t196 * t671 - 0.27259596000000000000000000000000000000000000000000e1 * t222 * t633 - 0.35e2 / 0.4e1 * t856 * t671 - 0.7e1 * t859 * t383 - 0.7e1 / 0.2e1 * t442 * t633 - t232 * t877
  t880 = t879 * t262
  t887 = -0.4e1 / 0.27e2 * t751 - t754 / 0.9e1 - t758 / 0.4e1 + t762 / 0.6e1
  t894 = -0.4e1 / 0.9e1 * t28 * t302 * t494 - 0.2e1 * t514 * t734 + 0.8e1 / 0.27e2 * t28 * t737 * t275 + 0.2e1 * t527 * t744 + 0.52732888888888888888888888888888888888888888888888e-1 * t747 * t223 + 0.26366444444444444444444444444444444444444444444444e-1 * t780 * t223 - 0.2e1 / 0.9e1 * t783 * t264 + 0.94545777777777777777777777777777777777777777777778e-1 * t786 * t671 - t816 * t264 / 0.9e1 - 0.94545777777777777777777777777777777777777777777778e-1 * t819 * t383 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t633 + 0.26366444444444444444444444444444444444444444444444e-1 * t839 * t223 - t880 * t264 / 0.9e1 + 0.47272888888888888888888888888888888888888888888889e-1 * t887 * t197 + 0.2e1 * t633 * t288 - 0.2e1 * t685 * t294
  t895 = t727 + t894
  t900 = f.my_piecewise3(t2, 0, t6 * t22 * t297 / 0.12e2 - t6 * t301 * t532 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t536 * t895)
  t929 = t671 * t383
  t955 = t522 ** 2
  t959 = -0.6e1 * t685 * t526 * t529 + t454 * t715 + 0.2e1 * t514 * t515 * t659 + 0.6e1 * t633 * t513 * t516 + 0.2e1 * t527 * t743 * t690 - t879 * t472 * t264 / 0.3e1 - 0.28363733333333333333333333333333333333333333333333e0 * t195 * t477 * t929 - t453 * t815 * t264 / 0.3e1 + 0.28363733333333333333333333333333333333333333333334e0 * t392 * t264 * t671 - 0.14181866666666666666666666666666666666666666666667e0 * t887 * t223 * t383 + 0.6e1 * t720 * t744 - 0.4e1 * t263 * t707 * t633 * t383 + 0.47459599999999999999999999999999999999999999999998e0 * t221 * t478 * t633 - 0.6e1 * t677 * t734 - 0.4e1 * t527 / t741 / t292 * t285 * t955
  t963 = t30 * t601
  t965 = t28 * t963 * t191
  t968 = t28 * t737 * t388
  t971 = t28 * t302 * t756
  t974 = t28 * t302 * t760
  t976 = t652 * t387
  t979 = t28 * t32 * t467 * t976
  t983 = t387 * t656
  t985 = t24 * t279 * t31 * t258 * t983
  t987 = t347 ** 2
  t1012 = 0.1e1 / t19 / t69
  t1013 = t47 * t1012
  t1017 = t55 / t325
  t1021 = 0.1e1 / t18 / t93
  t1022 = t68 * t1021
  t1027 = t81 / t19 / t105
  t1030 = 0.1e1 / t366
  t1031 = t92 * t1030
  t1036 = t104 / t18 / t167
  t1062 = 0.1e1 / t19 / t372
  t1076 = t39 * t1012
  t1098 = -t345 * t346 / t987 * t595 * t377 / 0.4e1 + t345 * t346 * t594 * t377 * t627 / 0.4e1 - 0.2e1 / 0.3e1 * t345 * t554 * t596 + t345 * t589 * t596 / 0.4e1 + 0.11e2 / 0.9e1 * t37 * t547 * t341 - t37 * t309 * t585 / 0.3e1 + t37 * t43 * (-0.154e3 / 0.81e2 * t46 * t1013 - 0.5e1 * t53 * t1017 - 0.209e3 / 0.243e3 * t66 * t1022 - 0.1495e4 / 0.1944e4 * t79 * t1027 - 0.5e1 / 0.4e1 * t91 * t1031 - 0.3689e4 / 0.23328e5 * t102 * t1036) * t173 / 0.24e2 - t345 * t346 * t348 * (-0.70e2 / 0.81e2 * t114 * t115 / t18 / t56 - 0.154e3 / 0.81e2 * t123 * t1013 - 0.5e1 * t127 * t1017 - 0.209e3 / 0.243e3 * t132 * t1022 - 0.1495e4 / 0.1944e4 * t137 * t1027 - 0.5e1 / 0.4e1 * t141 * t1031 - 0.3689e4 / 0.23328e5 * t146 * t1036 - 0.665e3 / 0.5832e4 * t153 * t155 * t1062 - 0.91e2 / 0.576e3 * t165 * t166 / t93 / t325) / 0.24e2 - 0.154e3 / 0.81e2 * t37 * t1076 * t174 - 0.11e2 / 0.9e1 * t345 * t546 * t111 * t378 + 0.2e1 / 0.3e1 * t345 * t308 * t340 * t378 + t345 * t554 * t628 / 0.3e1 - t345 * t42 * t584 * t378 / 0.8e1 - t345 * t589 * t628 / 0.8e1
  t1099 = f.my_piecewise3(t178, t1098, 0)
  t1101 = t181 * t184 * t308
  t1103 = t1099 - 0.80e2 / 0.81e2 * t1101
  t1106 = t28 * t32 * t216 * t1103
  t1110 = t210 * t212 * t57 * t216
  t1114 = t421 * t764 * t258 * t387
  t1118 = t421 * t416 * t467 * t652
  t1121 = t421 * t769 * t656
  t1125 = t421 * t213 * t806 * t976
  t1128 = t421 * t772 * t983
  t1131 = t421 * t422 * t1103
  t1133 = 0.28e2 / 0.27e2 * t965 + 0.2e1 / 0.3e1 * t968 + 0.3e1 / 0.4e1 * t971 - t974 / 0.2e1 + 0.15e2 / 0.8e1 * t979 - 0.9e1 / 0.4e1 * t985 + t1106 / 0.2e1 - 0.2e1 * t1110 - 0.3e1 * t1114 - 0.15e2 / 0.4e1 * t1118 + 0.3e1 / 0.2e1 * t1121 - 0.35e2 / 0.8e1 * t1125 + 0.15e2 / 0.4e1 * t1128 - t1131 / 0.2e1
  t1160 = 0.28e2 / 0.81e2 * t24 * t279 * t601
  t1161 = t269 ** 2
  t1166 = 0.1e1 / t270 / t1161 * t542 * t487 / 0.8e1
  t1169 = t541 * t487 * t638 / 0.4e1
  t1171 = 0.80e2 / 0.9e1 * t1101
  t1174 = t484 * (0.9e1 * t1099 - t1171) / 0.6e1
  t1185 = t506 ** 2
  t1186 = 0.1e1 / t1185
  t1188 = t649 * t511
  t1191 = t511 * t659
  t1200 = -t1160 + 0.3e1 / 0.8e1 * t258 * t976 - 0.3e1 / 0.4e1 * t388 * t656 + t191 * t1103 / 0.2e1
  t1220 = 0.79099333333333333333333333333333333333333333333332e-1 * t410 * t779 * t223 + 0.26366444444444444444444444444444444444444444444444e-1 * t208 * t1133 * t223 + 0.4e1 * t700 * t744 + 0.8e1 / 0.9e1 * t28 * t737 * t494 - 0.4e1 * t514 * t732 * t511 * t504 - 0.4e1 * t662 * t734 - 0.52732888888888888888888888888888888888888888888888e-1 * t221 * t264 * t1099 - 0.15819866666666666666666666666666666666666666666667e0 * t780 * t430 + 0.20e2 / 0.3e1 * t263 / t476 / t222 * t929 + 0.2e1 * t179 * ((-t1160 + t1166 - t1169 + t1174) * t286 - 0.3e1 * t641 * t507 * t511 + 0.6e1 * t504 * t647 * t649 - 0.3e1 * t643 * t659 - 0.6e1 * t283 * t1186 * t1188 + 0.6e1 * t648 * t1191 - t508 * t1200) * t516 + 0.4e1 * t662 * t703 - 0.15819866666666666666666666666666666666666666666667e0 * t427 * t665 - 0.15819866666666666666666666666666666666666666666667e0 * t411 * t665 + 0.6e1 * t677 * t703 - 0.2e1 * t527 * t528 * t659 + 0.6e1 * t383 * t661 * t516
  t1234 = t504 ** 2
  t1250 = t272 ** 2
  t1255 = 0.1e1 / t273 / t1250 * t682 * t491 / 0.8e1
  t1258 = t681 * t491 * t687 / 0.4e1
  t1259 = f.my_piecewise3(t238, t1099, 0)
  t1263 = t489 * (0.9e1 * t1259 - t1171) / 0.6e1
  t1290 = t383 * t633
  t1293 = -0.6e1 * t448 * t699 * t529 - 0.2e1 / 0.3e1 * t28 * t302 * t723 - 0.56e2 / 0.81e2 * t28 * t963 * t275 + 0.4e1 * t514 / t731 / t283 * t285 * t1234 - 0.4e1 * t700 * t668 + 0.47459600000000000000000000000000000000000000000000e0 * t411 * t672 + t816 * t478 - 0.63279466666666666666666666666666666666666666666664e0 * t221 * t707 * t929 - 0.4e1 * t473 * t708 - 0.31639733333333333333333333333333333333333333333334e0 * t747 * t430 - 0.2e1 * t240 * ((-t1160 + t1255 - t1258 + t1263) * t286 - 0.3e1 * t690 * t507 * t511 + 0.6e1 * t522 * t647 * t649 - 0.3e1 * t692 * t659 - 0.6e1 * t292 * t1186 * t1188 + 0.6e1 * t695 * t1191 - t524 * t1200) * t529 + t880 * t478 - 0.15819866666666666666666666666666666666666666666667e0 * t839 * t430 + 0.2e1 * t783 * t478 + t473 * t715 + 0.28363733333333333333333333333333333333333333333334e0 * t786 * t1290
  t1318 = t404 ** 2
  t1326 = -0.59348241542240669659660148152556874662714597894293e0 * t37 * t1076 * t203 + 0.54755818089567284507424541450275687932861682581045e-1 * t402 * t38 * t1021 * t405 - 0.91527320560273760027073280430079595664900759739578e-2 * t831 * t1030 * t833 + 0.40143561649242877204856701943017366519693315675253e-4 * t90 * t154 * t1062 / t1318 * t33 * t35 * t39 + 0.42141105276909202774570371431701910677713255063254e1 * t1099
  t1358 = t179 ** 2
  t1368 = t240 ** 2
  t1381 = 0.47459600000000000000000000000000000000000000000000e-1 * t1326 * t196 + 0.14237880000000000000000000000000000000000000000000e0 * t838 * t383 + 0.14237880000000000000000000000000000000000000000000e0 * t410 * t633 + 0.47459600000000000000000000000000000000000000000000e-1 * t208 * t1099 + 0.17018240000000000000000000000000000000000000000000e0 * t1290 + 0.56727466666666666666666666666666666666666666666666e-1 * t196 * t1099 - 0.54519192000000000000000000000000000000000000000000e1 * t929 - 0.16355757600000000000000000000000000000000000000000e2 * t437 * t633 - 0.27259596000000000000000000000000000000000000000000e1 * t222 * t1099 - 0.105e3 / 0.8e1 * t231 * t243 * t929 - 0.105e3 / 0.4e1 * t855 * t451 * t671 - 0.105e3 / 0.4e1 * t856 * t1290 - 0.21e2 / 0.2e1 * t441 * t877 * t383 - 0.21e2 / 0.2e1 * t859 * t633 - 0.7e1 / 0.2e1 * t442 * t1099 - t232 * (0.9e1 / 0.10e2 / t235 / t1358 * t929 - 0.9e1 / 0.5e1 * t865 * t383 * t633 + 0.6e1 / 0.5e1 * t445 * t1099 - 0.9e1 / 0.10e2 / t241 / t1368 * t872 * t448 + 0.9e1 / 0.5e1 * t871 * t448 * t685 - 0.6e1 / 0.5e1 * t447 * t1259)
  t1430 = 0.175e3 / 0.12e2 * t251 * t461 * t807 + 0.105e3 / 0.8e1 * t251 * t255 / t190 / t804 / t189 * t976 - 0.35e2 / 0.4e1 * t250 * t78 * t254 * t21 * t806 * t983 + 0.140e3 / 0.27e2 * t965 + 0.10e2 / 0.3e1 * t968 - 0.5e1 / 0.2e1 * t974 + 0.5e1 / 0.2e1 * t1106 - 0.20e2 * t1110 - 0.30e2 * t1114 + 0.15e2 * t1121 - 0.5e1 * t1131
  t1467 = -0.4e1 * t454 * t708 + t263 * t477 * t1099 / 0.3e1 + 0.47459600000000000000000000000000000000000000000000e0 * t427 * t672 - 0.6e1 * t720 * t668 - 0.2e1 * t514 * t733 * t641 - t1381 * t262 * t264 / 0.9e1 - t245 * (0.440e3 / 0.81e2 * t251 * t254 * t546 * t258 + 0.100e3 / 0.9e1 * t251 * t797 * t468 - 0.25e2 / 0.6e1 * t251 * t461 * t811 + 0.5e1 / 0.6e1 * t251 * t255 * t467 * t1103 - 0.75e2 / 0.2e1 * t1118 - 0.175e3 / 0.4e1 * t1125 + 0.75e2 / 0.2e1 * t1128 + 0.15e2 / 0.4e1 * t971 + 0.75e2 / 0.8e1 * t979 - 0.45e2 / 0.4e1 * t985 + t1430) * t264 / 0.9e1 - 0.14181866666666666666666666666666666666666666666667e0 * t819 * t633 - 0.47272888888888888888888888888888888888888888888889e-1 * t395 * t1099 + 0.26366444444444444444444444444444444444444444444444e-1 * t1326 * t220 * t223 + 0.79099333333333333333333333333333333333333333333332e-1 * t838 * t426 * t223 + 0.4e1 * t527 * t742 * t511 * t522 + 0.2e1 / 0.3e1 * t28 * t32 * (t1166 - t1169 + t1174 - t1255 + t1258 - t1263) + 0.47272888888888888888888888888888888888888888888889e-1 * (0.28e2 / 0.81e2 * t965 + 0.2e1 / 0.9e1 * t968 + t971 / 0.4e1 - t974 / 0.6e1 + 0.5e1 / 0.8e1 * t979 - 0.3e1 / 0.4e1 * t985 + t1106 / 0.6e1) * t197 + 0.2e1 * t1099 * t288 - 0.2e1 * t1259 * t294
  t1474 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t42 * t297 + t6 * t22 * t532 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t301 * t895 - 0.3e1 / 0.8e1 * t6 * t536 * (t959 + t1220 + t1293 + t1467))
  v3rho3_0_ = 0.2e1 * r0 * t1474 + 0.6e1 * t900

  res = {'v3rho3': v3rho3_0_}
  return res
