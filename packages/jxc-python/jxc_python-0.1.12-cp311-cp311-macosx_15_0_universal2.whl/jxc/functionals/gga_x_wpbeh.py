"""Generated from gga_x_wpbeh.mpl."""

import functools
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

WPBEH_A = jnp.float64(1.0161144)
WPBEH_B = jnp.float64(-0.37170836)
WPBEH_C = jnp.float64(-0.077215461)
WPBEH_D = jnp.float64(0.57786348)
WPBEH_E = jnp.float64(-0.051955731)
EGSCUT = jnp.float64(0.08)
WCUTOFF = jnp.float64(14.0)
WPBEH_HA1 = jnp.float64(0.00979681)
WPBEH_HA2 = jnp.float64(0.0410834)
WPBEH_HA3 = jnp.float64(0.18744)
WPBEH_HA4 = jnp.float64(0.00120824)
WPBEH_HA5 = jnp.float64(0.0347188)
WPBEH_FC1 = jnp.float64(6.4753871)
WPBEH_FC2 = jnp.float64(0.4796583)
WPBEH_EGA1 = jnp.float64(-0.0262841788)
WPBEH_EGA2 = jnp.float64(-0.07117647788)
WPBEH_EGA3 = jnp.float64(0.08534541323)
EB1_SHORT = jnp.float64(1.455915450052607)
EA1 = jnp.float64(-1.128223946706117)
EA2 = jnp.float64(1.452736265762971)
EA3 = jnp.float64(-1.243162299390327)
EA4 = jnp.float64(0.971824836115601)
EA5 = jnp.float64(-0.568861079687373)
EA6 = jnp.float64(0.246880514820192)
EA7 = jnp.float64(-0.065032363850763)
EA8 = jnp.float64(0.008401793031216)


def wpbeh_H(s):
  s = jnp.asarray(s, dtype=jnp.float64)
  num = WPBEH_HA1 * s**2 + WPBEH_HA2 * s**4
  den = 1.0 + WPBEH_HA3 * s**4 + WPBEH_HA4 * s**5 + WPBEH_HA5 * s**6
  return num / den


def wpbeh_F(s):
  return WPBEH_FC1 * wpbeh_H(s) + WPBEH_FC2


def eb1(w):
  w = jnp.asarray(w, dtype=jnp.float64)
  return jnp.where(w < WCUTOFF, EB1_SHORT, jnp.float64(2.0))


def aux1(s):
  s_arr = jnp.asarray(s, dtype=jnp.float64)
  return WPBEH_D + s_arr**2 * wpbeh_H(s_arr)


def aux2(s):
  s_arr = jnp.asarray(s, dtype=jnp.float64)
  return 9.0 * wpbeh_H(s_arr) * s_arr**2 / (4.0 * WPBEH_A)


def aux3(w, s):
  return aux1(s) + jnp.asarray(w, dtype=jnp.float64) ** 2


def aux4(w, s):
  w_arr = jnp.asarray(w, dtype=jnp.float64)
  s_arr = jnp.asarray(s, dtype=jnp.float64)
  return s_arr**2 * wpbeh_H(s_arr) + eb1(w_arr) * w_arr**2


def aux5(w, s):
  return 9.0 * aux4(w, s) / (4.0 * WPBEH_A)


def aux6(w, s):
  return WPBEH_D + aux4(w, s)


def _Ga(s):
  s_arr = jnp.asarray(s, dtype=jnp.float64)
  a1 = aux1(s_arr)
  term = (
    15.0 * WPBEH_E
    + 6.0 * WPBEH_C * (1.0 + wpbeh_F(s_arr) * s_arr**2) * a1
    + 4.0 * WPBEH_B * a1**2
    + 8.0 * WPBEH_A * a1**3
  )
  part1 = jnp.sqrt(jnp.pi) * term / (16.0 * a1**(3.5))
  expo = aux2(s_arr)
  part2 = (3.0 * jnp.pi / 4.0) * jnp.sqrt(WPBEH_A) * jnp.exp(expo) * (1.0 - jsp_special.erf(jnp.sqrt(expo)))
  return part1 - part2


def _Gb(s):
  s_arr = jnp.asarray(s, dtype=jnp.float64)
  return 15.0 * jnp.sqrt(jnp.pi) * s_arr**2 / (16.0 * aux1(s_arr) ** 3.5)


def wpbeh_EG(s):
  s_arr = jnp.asarray(s, dtype=jnp.float64)
  large = - (3.0 * jnp.pi / 4.0 + _Ga(s_arr)) / _Gb(s_arr)
  small = WPBEH_EGA1 + WPBEH_EGA2 * s_arr**2 + WPBEH_EGA3 * s_arr**4
  return jnp.where(s_arr > EGSCUT, large, small)


def np1(w):
  w_arr = jnp.asarray(w, dtype=jnp.float64)
  return (
    -1.5 * EA1 * jnp.sqrt(WPBEH_A) * w_arr
    + 27.0 * EA3 * w_arr**3 / (8.0 * jnp.sqrt(WPBEH_A))
    - 243.0 * EA5 * w_arr**5 / (32.0 * WPBEH_A ** 1.5)
    + 2187.0 * EA7 * w_arr**7 / (128.0 * WPBEH_A ** 2.5)
  )


def np2(w):
  w_arr = jnp.asarray(w, dtype=jnp.float64)
  return (
    -WPBEH_A
    + 9.0 * EA2 * w_arr**2 / 4.0
    - 81.0 * EA4 * w_arr**4 / (16.0 * WPBEH_A)
    + 729.0 * EA6 * w_arr**6 / (64.0 * WPBEH_A**2)
    - 6561.0 * EA8 * w_arr**8 / (256.0 * WPBEH_A**3)
  )

def _pol_impl(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  smax = 8.572844

  wpbeh_A = 1.0161144

  wpbeh_B = -0.37170836

  wpbeh_C = -0.077215461

  wpbeh_D = 0.57786348

  wpbeh_E = -0.051955731

  EGscut = 0.08

  wcutoff = 14

  wpbeh_Ha1 = 0.00979681

  wpbeh_Ha2 = 0.0410834

  wpbeh_Ha3 = 0.18744

  wpbeh_Ha4 = 0.00120824

  wpbeh_Ha5 = 0.0347188

  wpbeh_Fc1 = 6.4753871

  wpbeh_Fc2 = 0.4796583

  wpbeh_EGa1 = -0.0262841788

  wpbeh_EGa2 = -0.07117647788

  wpbeh_EGa3 = 0.08534541323

  ea1 = -1.128223946706117

  ea2 = 1.452736265762971

  ea3 = -1.243162299390327

  ea4 = 0.971824836115601

  ea5 = -0.568861079687373

  ea6 = 0.246880514820192

  ea7 = -0.065032363850763

  ea8 = 0.008401793031216

  t1 = lambda w, s: 1 / 2 * (np1(w) * jnp.pi * xc_erfcx(jnp.sqrt(aux5(w, s))) - np2(w) * xc_E1_scaled(aux5(w, s)))

  t10 = lambda w, s: 1 / 2 * wpbeh_A * jnp.log(aux4(w, s) / aux6(w, s))

  term1_largew = lambda w, s: -1 / 2 * wpbeh_A * (-xc_E1_scaled(aux5(w, s)) + jnp.log(aux6(w, s)) - jnp.log(aux4(w, s)))

  f2 = lambda w, s: 1 / 2 * ea1 * jnp.sqrt(jnp.pi) * wpbeh_A / jnp.sqrt(aux6(w, s))

  f3 = lambda w, s: 1 / 2 * ea2 * wpbeh_A / aux6(w, s)

  f4 = lambda w, s: ea3 * jnp.sqrt(jnp.pi) * (-9 / (8 * jnp.sqrt(aux4(w, s))) + 0.25 * wpbeh_A / aux6(w, s) ** (3 / 2))

  f5 = lambda w, s: ea4 / 128 * (-144 / aux4(w, s) + 64 * wpbeh_A / aux6(w, s) ** 2)

  f6 = lambda w, s: ea5 * (3 * jnp.sqrt(jnp.pi) * (3 * aux6(w, s) ** (5 / 2) * (9 * aux4(w, s) - 2 * wpbeh_A) + 4 * aux4(w, s) ** (3 / 2) * wpbeh_A ** 2)) / (32 * aux6(w, s) ** (5 / 2) * aux4(w, s) ** (3 / 2) * wpbeh_A)

  f7 = lambda w, s: ea6 * (32 * wpbeh_A / aux6(w, s) ** 3 + (-36 + 81 * s ** 2 * wpbeh_H(s) / wpbeh_A) / aux4(w, s) ** 2) / 32

  f8 = lambda w, s: ea7 * (-3 * jnp.sqrt(jnp.pi) * (-40 * aux4(w, s) ** (5 / 2) * wpbeh_A ** 3 + 9 * aux6(w, s) ** (7 / 2) * (27 * aux4(w, s) ** 2 - 6 * aux4(w, s) * wpbeh_A + 4 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** (7 / 2) * aux4(w, s) ** (5 / 2) * wpbeh_A ** 2)

  f9 = lambda w, s: (+324 * ea6 * eb1(w) * aux6(w, s) ** 4 * aux4(w, s) * wpbeh_A + ea8 * (384 * aux4(w, s) ** 3 * wpbeh_A ** 3 + aux6(w, s) ** 4 * (-729 * aux4(w, s) ** 2 + 324 * aux4(w, s) * wpbeh_A - 288 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** 4 * aux4(w, s) ** 3 * wpbeh_A ** 2)

  term2 = lambda s: (+aux1(s) ** 2 * wpbeh_B + aux1(s) * wpbeh_C + 2 * wpbeh_E + aux1(s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 2 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 3)

  term3 = lambda w, s: -w * (+4 * aux3(w, s) ** 2 * wpbeh_B + 6 * aux3(w, s) * wpbeh_C + 15 * wpbeh_E + 6 * aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 15 * s ** 2 * wpbeh_EG(s)) / (8 * aux1(s) * aux3(w, s) ** (5 / 2))

  term4 = lambda w, s: -w ** 3 * (+aux3(w, s) * wpbeh_C + 5 * wpbeh_E + aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 5 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 2 * aux3(w, s) ** (5 / 2))

  term5 = lambda w, s: -w ** 5 * (+wpbeh_E + s ** 2 * wpbeh_EG(s)) / (aux1(s) ** 3 * aux3(w, s) ** (5 / 2))

  t2t9 = lambda w, s: +f2(w, s) * w + f3(w, s) * w ** 2 + f4(w, s) * w ** 3 + f5(w, s) * w ** 4 + f6(w, s) * w ** 5 + f7(w, s) * w ** 6 + f8(w, s) * w ** 7 + f9(w, s) * w ** 8

  term1 = lambda w, s: f.my_piecewise3(w > wcutoff, term1_largew(w, s), t1(jnp.minimum(w, wcutoff), s) + t2t9(jnp.minimum(w, wcutoff), s) + t10(jnp.minimum(w, wcutoff), s))

  f_wpbeh0 = lambda w, s: -8 / 9 * (term1(w, s) + term2(s) + term3(w, s) + term4(w, s) + term5(w, s))

  f_wpbeh = lambda rs, z, x: f_wpbeh0(f.nu(rs, z), jnp.maximum(1e-15, s_scaling_2(X2S * x)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, f_wpbeh, rs, z, xs0, xs1)

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
  smax = 8.572844

  wpbeh_A = 1.0161144

  wpbeh_B = -0.37170836

  wpbeh_C = -0.077215461

  wpbeh_D = 0.57786348

  wpbeh_E = -0.051955731

  EGscut = 0.08

  wcutoff = 14

  wpbeh_Ha1 = 0.00979681

  wpbeh_Ha2 = 0.0410834

  wpbeh_Ha3 = 0.18744

  wpbeh_Ha4 = 0.00120824

  wpbeh_Ha5 = 0.0347188

  wpbeh_Fc1 = 6.4753871

  wpbeh_Fc2 = 0.4796583

  wpbeh_EGa1 = -0.0262841788

  wpbeh_EGa2 = -0.07117647788

  wpbeh_EGa3 = 0.08534541323

  ea1 = -1.128223946706117

  ea2 = 1.452736265762971

  ea3 = -1.243162299390327

  ea4 = 0.971824836115601

  ea5 = -0.568861079687373

  ea6 = 0.246880514820192

  ea7 = -0.065032363850763

  ea8 = 0.008401793031216

  t1 = lambda w, s: 1 / 2 * (np1(w) * jnp.pi * xc_erfcx(jnp.sqrt(aux5(w, s))) - np2(w) * xc_E1_scaled(aux5(w, s)))

  t10 = lambda w, s: 1 / 2 * wpbeh_A * jnp.log(aux4(w, s) / aux6(w, s))

  term1_largew = lambda w, s: -1 / 2 * wpbeh_A * (-xc_E1_scaled(aux5(w, s)) + jnp.log(aux6(w, s)) - jnp.log(aux4(w, s)))

  f2 = lambda w, s: 1 / 2 * ea1 * jnp.sqrt(jnp.pi) * wpbeh_A / jnp.sqrt(aux6(w, s))

  f3 = lambda w, s: 1 / 2 * ea2 * wpbeh_A / aux6(w, s)

  f4 = lambda w, s: ea3 * jnp.sqrt(jnp.pi) * (-9 / (8 * jnp.sqrt(aux4(w, s))) + 0.25 * wpbeh_A / aux6(w, s) ** (3 / 2))

  f5 = lambda w, s: ea4 / 128 * (-144 / aux4(w, s) + 64 * wpbeh_A / aux6(w, s) ** 2)

  f6 = lambda w, s: ea5 * (3 * jnp.sqrt(jnp.pi) * (3 * aux6(w, s) ** (5 / 2) * (9 * aux4(w, s) - 2 * wpbeh_A) + 4 * aux4(w, s) ** (3 / 2) * wpbeh_A ** 2)) / (32 * aux6(w, s) ** (5 / 2) * aux4(w, s) ** (3 / 2) * wpbeh_A)

  f7 = lambda w, s: ea6 * (32 * wpbeh_A / aux6(w, s) ** 3 + (-36 + 81 * s ** 2 * wpbeh_H(s) / wpbeh_A) / aux4(w, s) ** 2) / 32

  f8 = lambda w, s: ea7 * (-3 * jnp.sqrt(jnp.pi) * (-40 * aux4(w, s) ** (5 / 2) * wpbeh_A ** 3 + 9 * aux6(w, s) ** (7 / 2) * (27 * aux4(w, s) ** 2 - 6 * aux4(w, s) * wpbeh_A + 4 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** (7 / 2) * aux4(w, s) ** (5 / 2) * wpbeh_A ** 2)

  f9 = lambda w, s: (+324 * ea6 * eb1(w) * aux6(w, s) ** 4 * aux4(w, s) * wpbeh_A + ea8 * (384 * aux4(w, s) ** 3 * wpbeh_A ** 3 + aux6(w, s) ** 4 * (-729 * aux4(w, s) ** 2 + 324 * aux4(w, s) * wpbeh_A - 288 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** 4 * aux4(w, s) ** 3 * wpbeh_A ** 2)

  term2 = lambda s: (+aux1(s) ** 2 * wpbeh_B + aux1(s) * wpbeh_C + 2 * wpbeh_E + aux1(s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 2 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 3)

  term3 = lambda w, s: -w * (+4 * aux3(w, s) ** 2 * wpbeh_B + 6 * aux3(w, s) * wpbeh_C + 15 * wpbeh_E + 6 * aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 15 * s ** 2 * wpbeh_EG(s)) / (8 * aux1(s) * aux3(w, s) ** (5 / 2))

  term4 = lambda w, s: -w ** 3 * (+aux3(w, s) * wpbeh_C + 5 * wpbeh_E + aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 5 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 2 * aux3(w, s) ** (5 / 2))

  term5 = lambda w, s: -w ** 5 * (+wpbeh_E + s ** 2 * wpbeh_EG(s)) / (aux1(s) ** 3 * aux3(w, s) ** (5 / 2))

  t2t9 = lambda w, s: +f2(w, s) * w + f3(w, s) * w ** 2 + f4(w, s) * w ** 3 + f5(w, s) * w ** 4 + f6(w, s) * w ** 5 + f7(w, s) * w ** 6 + f8(w, s) * w ** 7 + f9(w, s) * w ** 8

  term1 = lambda w, s: f.my_piecewise3(w > wcutoff, term1_largew(w, s), t1(jnp.minimum(w, wcutoff), s) + t2t9(jnp.minimum(w, wcutoff), s) + t10(jnp.minimum(w, wcutoff), s))

  f_wpbeh0 = lambda w, s: -8 / 9 * (term1(w, s) + term2(s) + term3(w, s) + term4(w, s) + term5(w, s))

  f_wpbeh = lambda rs, z, x: f_wpbeh0(f.nu(rs, z), jnp.maximum(1e-15, s_scaling_2(X2S * x)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, f_wpbeh, rs, z, xs0, xs1)

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
  smax = 8.572844

  wpbeh_A = 1.0161144

  wpbeh_B = -0.37170836

  wpbeh_C = -0.077215461

  wpbeh_D = 0.57786348

  wpbeh_E = -0.051955731

  EGscut = 0.08

  wcutoff = 14

  wpbeh_Ha1 = 0.00979681

  wpbeh_Ha2 = 0.0410834

  wpbeh_Ha3 = 0.18744

  wpbeh_Ha4 = 0.00120824

  wpbeh_Ha5 = 0.0347188

  wpbeh_Fc1 = 6.4753871

  wpbeh_Fc2 = 0.4796583

  wpbeh_EGa1 = -0.0262841788

  wpbeh_EGa2 = -0.07117647788

  wpbeh_EGa3 = 0.08534541323

  ea1 = -1.128223946706117

  ea2 = 1.452736265762971

  ea3 = -1.243162299390327

  ea4 = 0.971824836115601

  ea5 = -0.568861079687373

  ea6 = 0.246880514820192

  ea7 = -0.065032363850763

  ea8 = 0.008401793031216

  t1 = lambda w, s: 1 / 2 * (np1(w) * jnp.pi * xc_erfcx(jnp.sqrt(aux5(w, s))) - np2(w) * xc_E1_scaled(aux5(w, s)))

  t10 = lambda w, s: 1 / 2 * wpbeh_A * jnp.log(aux4(w, s) / aux6(w, s))

  term1_largew = lambda w, s: -1 / 2 * wpbeh_A * (-xc_E1_scaled(aux5(w, s)) + jnp.log(aux6(w, s)) - jnp.log(aux4(w, s)))

  f2 = lambda w, s: 1 / 2 * ea1 * jnp.sqrt(jnp.pi) * wpbeh_A / jnp.sqrt(aux6(w, s))

  f3 = lambda w, s: 1 / 2 * ea2 * wpbeh_A / aux6(w, s)

  f4 = lambda w, s: ea3 * jnp.sqrt(jnp.pi) * (-9 / (8 * jnp.sqrt(aux4(w, s))) + 0.25 * wpbeh_A / aux6(w, s) ** (3 / 2))

  f5 = lambda w, s: ea4 / 128 * (-144 / aux4(w, s) + 64 * wpbeh_A / aux6(w, s) ** 2)

  f6 = lambda w, s: ea5 * (3 * jnp.sqrt(jnp.pi) * (3 * aux6(w, s) ** (5 / 2) * (9 * aux4(w, s) - 2 * wpbeh_A) + 4 * aux4(w, s) ** (3 / 2) * wpbeh_A ** 2)) / (32 * aux6(w, s) ** (5 / 2) * aux4(w, s) ** (3 / 2) * wpbeh_A)

  f7 = lambda w, s: ea6 * (32 * wpbeh_A / aux6(w, s) ** 3 + (-36 + 81 * s ** 2 * wpbeh_H(s) / wpbeh_A) / aux4(w, s) ** 2) / 32

  f8 = lambda w, s: ea7 * (-3 * jnp.sqrt(jnp.pi) * (-40 * aux4(w, s) ** (5 / 2) * wpbeh_A ** 3 + 9 * aux6(w, s) ** (7 / 2) * (27 * aux4(w, s) ** 2 - 6 * aux4(w, s) * wpbeh_A + 4 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** (7 / 2) * aux4(w, s) ** (5 / 2) * wpbeh_A ** 2)

  f9 = lambda w, s: (+324 * ea6 * eb1(w) * aux6(w, s) ** 4 * aux4(w, s) * wpbeh_A + ea8 * (384 * aux4(w, s) ** 3 * wpbeh_A ** 3 + aux6(w, s) ** 4 * (-729 * aux4(w, s) ** 2 + 324 * aux4(w, s) * wpbeh_A - 288 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** 4 * aux4(w, s) ** 3 * wpbeh_A ** 2)

  term2 = lambda s: (+aux1(s) ** 2 * wpbeh_B + aux1(s) * wpbeh_C + 2 * wpbeh_E + aux1(s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 2 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 3)

  term3 = lambda w, s: -w * (+4 * aux3(w, s) ** 2 * wpbeh_B + 6 * aux3(w, s) * wpbeh_C + 15 * wpbeh_E + 6 * aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 15 * s ** 2 * wpbeh_EG(s)) / (8 * aux1(s) * aux3(w, s) ** (5 / 2))

  term4 = lambda w, s: -w ** 3 * (+aux3(w, s) * wpbeh_C + 5 * wpbeh_E + aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 5 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 2 * aux3(w, s) ** (5 / 2))

  term5 = lambda w, s: -w ** 5 * (+wpbeh_E + s ** 2 * wpbeh_EG(s)) / (aux1(s) ** 3 * aux3(w, s) ** (5 / 2))

  t2t9 = lambda w, s: +f2(w, s) * w + f3(w, s) * w ** 2 + f4(w, s) * w ** 3 + f5(w, s) * w ** 4 + f6(w, s) * w ** 5 + f7(w, s) * w ** 6 + f8(w, s) * w ** 7 + f9(w, s) * w ** 8

  term1 = lambda w, s: f.my_piecewise3(w > wcutoff, term1_largew(w, s), t1(jnp.minimum(w, wcutoff), s) + t2t9(jnp.minimum(w, wcutoff), s) + t10(jnp.minimum(w, wcutoff), s))

  f_wpbeh0 = lambda w, s: -8 / 9 * (term1(w, s) + term2(s) + term3(w, s) + term4(w, s) + term5(w, s))

  f_wpbeh = lambda rs, z, x: f_wpbeh0(f.nu(rs, z), jnp.maximum(1e-15, s_scaling_2(X2S * x)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, f_wpbeh, rs, z, xs0, xs1)

  t2 = r0 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 / t4
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t12 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t13 = f.p.zeta_threshold - 0.1e1
  t16 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t17 = -t13
  t18 = r0 - r1
  t19 = t18 * t8
  t20 = f.my_piecewise5(t12, t13, t16, t17, t19)
  t21 = 0.1e1 + t20
  t22 = t21 <= f.p.zeta_threshold
  t23 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t24 = t23 * f.p.zeta_threshold
  t25 = t21 ** (0.1e1 / 0.3e1)
  t27 = f.my_piecewise3(t22, t24, t25 * t21)
  t28 = t7 ** (0.1e1 / 0.3e1)
  t29 = t27 * t28
  t30 = t3 ** 2
  t31 = f.p.cam_omega * t30
  t32 = jnp.pi ** 2
  t33 = t32 ** (0.1e1 / 0.3e1)
  t34 = 0.1e1 / t33
  t36 = 0.1e1 + t19 <= f.p.zeta_threshold
  t38 = 0.1e1 - t19 <= f.p.zeta_threshold
  t39 = f.my_piecewise5(t36, t13, t38, t17, t19)
  t40 = 0.1e1 + t39
  t41 = t40 <= f.p.zeta_threshold
  t42 = t40 ** (0.1e1 / 0.3e1)
  t43 = f.my_piecewise3(t41, t23, t42)
  t45 = t34 / t43
  t46 = 0.1e1 / t28
  t49 = t31 * t45 * t46 / 0.3e1
  t50 = 0.14e2 < t49
  t51 = 6 ** (0.1e1 / 0.3e1)
  t52 = t51 ** 2
  t53 = t52 * t34
  t54 = jnp.sqrt(s0)
  t55 = r0 ** (0.1e1 / 0.3e1)
  t57 = 0.1e1 / t55 / r0
  t60 = t53 * t54 * t57 / 0.12e2
  t61 = t60 < 0.1e1
  t62 = 0.15e2 < t60
  t63 = f.my_piecewise3(t62, 15, t60)
  t64 = 0.1e1 < t63
  t65 = f.my_piecewise3(t64, t63, 1)
  t67 = jnp.exp(t65 - 0.8572844e1)
  t68 = 0.1e1 + t67
  t69 = jnp.log(t68)
  t71 = f.my_piecewise3(t62, 0.8572844e1, t65 - t69)
  t72 = f.my_piecewise3(t61, t60, t71)
  t73 = t72 < 0.1e-14
  t74 = f.my_piecewise3(t73, 0.1e-14, t72)
  t75 = t74 ** 2
  t77 = t75 ** 2
  t79 = 0.979681e-2 * t75 + 0.410834e-1 * t77
  t80 = t75 * t79
  t82 = t77 * t74
  t86 = 0.1e1 + 0.187440e0 * t77 + 0.120824e-2 * t82 + 0.347188e-1 * t77 * t75
  t87 = 0.1e1 / t86
  t88 = t80 * t87
  t89 = 0.22143176004591608976312116037328080381500350747908e1 * t88
  t90 = t49 < 0.14e2
  t91 = f.my_piecewise3(t90, 0.1455915450052607e1, 2)
  t92 = f.p.cam_omega ** 2
  t94 = t91 * t92 * t3
  t95 = t33 ** 2
  t96 = 0.1e1 / t95
  t97 = t43 ** 2
  t98 = 0.1e1 / t97
  t99 = t96 * t98
  t100 = t28 ** 2
  t101 = 0.1e1 / t100
  t102 = t99 * t101
  t103 = t94 * t102
  t105 = t89 + 0.73810586681972029921040386791093601271667835826361e0 * t103
  t106 = xc_E1_scaled(t105)
  t108 = t103 / 0.3e1
  t109 = 0.57786348e0 + t88 + t108
  t110 = jnp.log(t109)
  t112 = t88 + t108
  t113 = jnp.log(t112)
  t116 = f.my_piecewise3(t50, 14, t49)
  t118 = t116 ** 2
  t119 = t118 * t116
  t121 = t118 ** 2
  t122 = t121 * t116
  t124 = t121 * t119
  t127 = (0.17059169152930056820161893079623736851681581580379e1 * t116 - 0.41622705406440396564494857937193021161156977252689e1 * t119 + 0.42174370348694649002798874148142601259725702952253e1 * t122 - 0.10676080470633097775878162022430088083825040527885e1 * t124) * jnp.pi
  t128 = t116 < 0.14e2
  t129 = f.my_piecewise3(t128, 0.1455915450052607e1, 2)
  t130 = t129 * t118
  t132 = t89 + 0.22143176004591608976312116037328080381500350747908e1 * t130
  t133 = jnp.sqrt(t132)
  t134 = xc_erfcx(t133)
  t139 = t121 * t118
  t141 = t121 ** 2
  t143 = -0.10161144e1 + 0.32686565979666847500000000000000000000000000000000e1 * t118 - 0.48418398881417585091796750444634974172199508244347e1 * t121 + 0.27236365685865660550566018235682267087532882778448e1 * t139 - 0.20524577845574895866582594065457716968048160011162e0 * t141
  t144 = xc_E1_scaled(t132)
  t147 = jnp.sqrt(jnp.pi)
  t148 = 0.57786348e0 + t88 + t130
  t149 = jnp.sqrt(t148)
  t151 = t147 / t149
  t154 = 0.1e1 / t148
  t157 = t88 + t130
  t158 = jnp.sqrt(t157)
  t161 = t149 * t148
  t162 = 0.1e1 / t161
  t165 = t147 * (-0.9e1 / 0.8e1 / t158 + 0.254028600e0 * t162)
  t168 = 0.1e1 / t157
  t170 = t148 ** 2
  t171 = 0.1e1 / t170
  t173 = -0.10933029406300511250000000000000000000000000000000e1 * t168 + 0.49374260512735112037720000000000000000000000000000e0 * t171
  t175 = t149 * t170
  t178 = 0.9e1 * t88 + 0.9e1 * t130 - 0.20322288e1
  t181 = t158 * t157
  t184 = t147 * (0.3e1 * t175 * t178 + 0.412995389554944e1 * t181)
  t185 = 0.1e1 / t175
  t186 = 0.1e1 / t181
  t188 = t185 * t186 * t122
  t191 = t170 * t148
  t192 = 0.1e1 / t191
  t195 = -0.36e2 + 0.79715433616529792314723617734381089373401262692468e2 * t88
  t196 = t157 ** 2
  t197 = 0.1e1 / t196
  t200 = 0.25085884618821050196480000000000000000000000000000e0 * t192 + 0.77150160881310000000000000000000000000000000000000e-2 * t195 * t197
  t202 = t158 * t196
  t204 = t149 * t191
  t208 = 0.27e2 * t196 - 0.60966864e1 * t88 - 0.60966864e1 * t130 + 0.412995389554944e1
  t212 = t147 * (-0.41965056246038818959360e2 * t202 + 0.9e1 * t204 * t208)
  t213 = 0.1e1 / t204
  t214 = 0.1e1 / t202
  t216 = t213 * t214 * t124
  t219 = t170 ** 2
  t220 = t129 * t219
  t223 = t196 * t157
  t228 = -0.729e3 * t196 + 0.3292210656e3 * t88 + 0.3292210656e3 * t130 - 0.29735668047955968e3
  t231 = 0.812782661649802026365952e2 * t220 * t157 + 0.3384784484376541657318712689107664896e1 * t223 + 0.8401793031216e-2 * t219 * t228
  t232 = 0.1e1 / t219
  t233 = t231 * t232
  t234 = 0.1e1 / t223
  t235 = t234 * t141
  t239 = jnp.log(t157 * t154)
  t241 = t127 * t134 / 0.2e1 - t143 * t144 / 0.2e1 - 0.57320229933645902589240000000000000000000000000000e0 * t151 * t116 + 0.73807311952199090994120000000000000000000000000000e0 * t154 * t118 - 0.1243162299390327e1 * t165 * t119 + t173 * t121 - 0.52484962540331303985063099194342684248938899005860e-1 * t184 * t188 + t200 * t139 + 0.14762353927435135388626424172726290810696148649614e-2 * t212 * t216 + 0.75666704254679261017345818778596682937131877722093e-2 * t233 * t235 + 0.50805720000000000000000000000000000000000000000000e0 * t239
  t242 = f.my_piecewise3(t50, 0.50805720000000000000000000000000000000000000000000e0 * t106 - 0.50805720000000000000000000000000000000000000000000e0 * t110 + 0.50805720000000000000000000000000000000000000000000e0 * t113, t241)
  t244 = 0.57786348e0 + t88
  t245 = t244 ** 2
  t247 = 0.77215461e-1 * t88
  t248 = t244 * t75
  t251 = 0.64753871e1 * t79 * t87 + 0.47965830e0
  t254 = 0.8e-1 < t74
  t255 = 0.3e1 / 0.4e1 * jnp.pi
  t258 = -0.463292766e0 - 0.463292766e0 * t251 * t75
  t261 = t245 * t244
  t264 = t147 * (-0.779335965e0 + t258 * t244 - 0.148683344e1 * t245 + 0.81289152e1 * t261)
  t265 = jnp.sqrt(t244)
  t266 = t265 * t261
  t267 = 0.1e1 / t266
  t270 = jnp.exp(t89)
  t272 = jnp.sqrt(t88)
  t274 = jax.lax.erf(0.14880583323442535320963147261125041853685458071038e1 * t272)
  t275 = 0.1e1 - t274
  t279 = 0.1e1 / t147
  t280 = (t255 + t264 * t267 / 0.16e2 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * t270 * t275) * t279
  t281 = 0.1e1 / t75
  t282 = t281 * t266
  t288 = f.my_piecewise3(t254, -0.16e2 / 0.15e2 * t280 * t282, -0.2628417880e-1 - 0.7117647788e-1 * t75 + 0.8534541323e-1 * t77)
  t289 = t75 * t288
  t291 = -0.37170836e0 * t245 - 0.14853145700326428e0 - t247 - 0.77215461e-1 * t248 * t251 + 0.2e1 * t289
  t292 = 0.1e1 / t261
  t295 = t31 * t45
  t296 = t92 * t3
  t297 = t296 * t102
  t299 = 0.57786348e0 + t88 + t297 / 0.3e1
  t300 = t299 ** 2
  t306 = 0.346718088e1 + 0.6e1 * t88 + 0.2e1 * t297
  t307 = t306 * t75
  t311 = -0.148683344e1 * t300 - 0.104705593501958568e1 - 0.463292766e0 * t88 - 0.154430922e0 * t297 - 0.77215461e-1 * t307 * t251 + 0.15e2 * t289
  t312 = t46 * t311
  t314 = 0.462290784e1 + 0.8e1 * t88
  t315 = 0.1e1 / t314
  t316 = jnp.sqrt(t299)
  t318 = 0.1e1 / t316 / t300
  t319 = t315 * t318
  t325 = t92 * f.p.cam_omega / t32
  t327 = 0.1e1 / t97 / t43
  t328 = t325 * t327
  t330 = t299 * t75
  t334 = -0.30439865000326428e0 - t247 - 0.25738487000000000000000000000000000000000000000000e-1 * t297 - 0.77215461e-1 * t330 * t251 + 0.5e1 * t289
  t336 = 0.1e1 / t245
  t337 = t336 * t318
  t341 = t92 ** 2
  t343 = t341 * f.p.cam_omega * t3
  t345 = 0.1e1 / t95 / t32
  t346 = t97 ** 2
  t350 = t343 * t345 / t346 / t43
  t352 = 0.1e1 / t100 / t7
  t353 = -0.51955731e-1 + t289
  t354 = t352 * t353
  t355 = t292 * t318
  t359 = -0.8e1 / 0.9e1 * t242 - 0.4e1 / 0.9e1 * t291 * t292 + 0.8e1 / 0.27e2 * t295 * t312 * t319 + 0.4e1 / 0.27e2 * t328 * t8 * t334 * t337 + 0.8e1 / 0.81e2 * t350 * t354 * t355
  t363 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t29 * t359)
  t364 = r1 <= f.p.dens_threshold
  t365 = f.my_piecewise5(t16, t13, t12, t17, -t19)
  t366 = 0.1e1 + t365
  t367 = t366 <= f.p.zeta_threshold
  t368 = t366 ** (0.1e1 / 0.3e1)
  t370 = f.my_piecewise3(t367, t24, t368 * t366)
  t371 = t370 * t28
  t372 = f.my_piecewise5(t38, t13, t36, t17, -t19)
  t373 = 0.1e1 + t372
  t374 = t373 <= f.p.zeta_threshold
  t375 = t373 ** (0.1e1 / 0.3e1)
  t376 = f.my_piecewise3(t374, t23, t375)
  t378 = t34 / t376
  t381 = t31 * t378 * t46 / 0.3e1
  t382 = 0.14e2 < t381
  t383 = jnp.sqrt(s2)
  t384 = r1 ** (0.1e1 / 0.3e1)
  t386 = 0.1e1 / t384 / r1
  t389 = t53 * t383 * t386 / 0.12e2
  t390 = t389 < 0.1e1
  t391 = 0.15e2 < t389
  t392 = f.my_piecewise3(t391, 15, t389)
  t393 = 0.1e1 < t392
  t394 = f.my_piecewise3(t393, t392, 1)
  t396 = jnp.exp(t394 - 0.8572844e1)
  t397 = 0.1e1 + t396
  t398 = jnp.log(t397)
  t400 = f.my_piecewise3(t391, 0.8572844e1, t394 - t398)
  t401 = f.my_piecewise3(t390, t389, t400)
  t402 = t401 < 0.1e-14
  t403 = f.my_piecewise3(t402, 0.1e-14, t401)
  t404 = t403 ** 2
  t406 = t404 ** 2
  t408 = 0.979681e-2 * t404 + 0.410834e-1 * t406
  t409 = t404 * t408
  t411 = t406 * t403
  t415 = 0.1e1 + 0.187440e0 * t406 + 0.120824e-2 * t411 + 0.347188e-1 * t406 * t404
  t416 = 0.1e1 / t415
  t417 = t409 * t416
  t418 = 0.22143176004591608976312116037328080381500350747908e1 * t417
  t419 = t381 < 0.14e2
  t420 = f.my_piecewise3(t419, 0.1455915450052607e1, 2)
  t422 = t420 * t92 * t3
  t423 = t376 ** 2
  t424 = 0.1e1 / t423
  t425 = t96 * t424
  t426 = t425 * t101
  t427 = t422 * t426
  t429 = t418 + 0.73810586681972029921040386791093601271667835826361e0 * t427
  t430 = xc_E1_scaled(t429)
  t432 = t427 / 0.3e1
  t433 = 0.57786348e0 + t417 + t432
  t434 = jnp.log(t433)
  t436 = t417 + t432
  t437 = jnp.log(t436)
  t440 = f.my_piecewise3(t382, 14, t381)
  t442 = t440 ** 2
  t443 = t442 * t440
  t445 = t442 ** 2
  t446 = t445 * t440
  t448 = t445 * t443
  t451 = (0.17059169152930056820161893079623736851681581580379e1 * t440 - 0.41622705406440396564494857937193021161156977252689e1 * t443 + 0.42174370348694649002798874148142601259725702952253e1 * t446 - 0.10676080470633097775878162022430088083825040527885e1 * t448) * jnp.pi
  t452 = t440 < 0.14e2
  t453 = f.my_piecewise3(t452, 0.1455915450052607e1, 2)
  t454 = t453 * t442
  t456 = t418 + 0.22143176004591608976312116037328080381500350747908e1 * t454
  t457 = jnp.sqrt(t456)
  t458 = xc_erfcx(t457)
  t463 = t445 * t442
  t465 = t445 ** 2
  t467 = -0.10161144e1 + 0.32686565979666847500000000000000000000000000000000e1 * t442 - 0.48418398881417585091796750444634974172199508244347e1 * t445 + 0.27236365685865660550566018235682267087532882778448e1 * t463 - 0.20524577845574895866582594065457716968048160011162e0 * t465
  t468 = xc_E1_scaled(t456)
  t471 = 0.57786348e0 + t417 + t454
  t472 = jnp.sqrt(t471)
  t474 = t147 / t472
  t477 = 0.1e1 / t471
  t480 = t417 + t454
  t481 = jnp.sqrt(t480)
  t484 = t472 * t471
  t485 = 0.1e1 / t484
  t488 = t147 * (-0.9e1 / 0.8e1 / t481 + 0.254028600e0 * t485)
  t491 = 0.1e1 / t480
  t493 = t471 ** 2
  t494 = 0.1e1 / t493
  t496 = -0.10933029406300511250000000000000000000000000000000e1 * t491 + 0.49374260512735112037720000000000000000000000000000e0 * t494
  t498 = t472 * t493
  t501 = 0.9e1 * t417 + 0.9e1 * t454 - 0.20322288e1
  t504 = t481 * t480
  t507 = t147 * (0.3e1 * t498 * t501 + 0.412995389554944e1 * t504)
  t508 = 0.1e1 / t498
  t509 = 0.1e1 / t504
  t511 = t508 * t509 * t446
  t514 = t493 * t471
  t515 = 0.1e1 / t514
  t518 = -0.36e2 + 0.79715433616529792314723617734381089373401262692468e2 * t417
  t519 = t480 ** 2
  t520 = 0.1e1 / t519
  t523 = 0.25085884618821050196480000000000000000000000000000e0 * t515 + 0.77150160881310000000000000000000000000000000000000e-2 * t518 * t520
  t525 = t481 * t519
  t527 = t472 * t514
  t531 = 0.27e2 * t519 - 0.60966864e1 * t417 - 0.60966864e1 * t454 + 0.412995389554944e1
  t535 = t147 * (-0.41965056246038818959360e2 * t525 + 0.9e1 * t527 * t531)
  t536 = 0.1e1 / t527
  t537 = 0.1e1 / t525
  t539 = t536 * t537 * t448
  t542 = t493 ** 2
  t543 = t453 * t542
  t546 = t519 * t480
  t551 = -0.729e3 * t519 + 0.3292210656e3 * t417 + 0.3292210656e3 * t454 - 0.29735668047955968e3
  t554 = 0.812782661649802026365952e2 * t543 * t480 + 0.3384784484376541657318712689107664896e1 * t546 + 0.8401793031216e-2 * t542 * t551
  t555 = 0.1e1 / t542
  t556 = t554 * t555
  t557 = 0.1e1 / t546
  t558 = t557 * t465
  t562 = jnp.log(t480 * t477)
  t564 = t451 * t458 / 0.2e1 - t467 * t468 / 0.2e1 - 0.57320229933645902589240000000000000000000000000000e0 * t474 * t440 + 0.73807311952199090994120000000000000000000000000000e0 * t477 * t442 - 0.1243162299390327e1 * t488 * t443 + t496 * t445 - 0.52484962540331303985063099194342684248938899005860e-1 * t507 * t511 + t523 * t463 + 0.14762353927435135388626424172726290810696148649614e-2 * t535 * t539 + 0.75666704254679261017345818778596682937131877722093e-2 * t556 * t558 + 0.50805720000000000000000000000000000000000000000000e0 * t562
  t565 = f.my_piecewise3(t382, 0.50805720000000000000000000000000000000000000000000e0 * t430 - 0.50805720000000000000000000000000000000000000000000e0 * t434 + 0.50805720000000000000000000000000000000000000000000e0 * t437, t564)
  t567 = 0.57786348e0 + t417
  t568 = t567 ** 2
  t570 = 0.77215461e-1 * t417
  t571 = t567 * t404
  t574 = 0.64753871e1 * t408 * t416 + 0.47965830e0
  t577 = 0.8e-1 < t403
  t580 = -0.463292766e0 - 0.463292766e0 * t574 * t404
  t583 = t568 * t567
  t586 = t147 * (-0.779335965e0 + t580 * t567 - 0.148683344e1 * t568 + 0.81289152e1 * t583)
  t587 = jnp.sqrt(t567)
  t588 = t587 * t583
  t589 = 0.1e1 / t588
  t592 = jnp.exp(t418)
  t594 = jnp.sqrt(t417)
  t596 = jax.lax.erf(0.14880583323442535320963147261125041853685458071038e1 * t594)
  t597 = 0.1e1 - t596
  t601 = (t255 + t586 * t589 / 0.16e2 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * t592 * t597) * t279
  t602 = 0.1e1 / t404
  t603 = t602 * t588
  t609 = f.my_piecewise3(t577, -0.16e2 / 0.15e2 * t601 * t603, -0.2628417880e-1 - 0.7117647788e-1 * t404 + 0.8534541323e-1 * t406)
  t610 = t404 * t609
  t612 = -0.37170836e0 * t568 - 0.14853145700326428e0 - t570 - 0.77215461e-1 * t571 * t574 + 0.2e1 * t610
  t613 = 0.1e1 / t583
  t616 = t31 * t378
  t617 = t296 * t426
  t619 = 0.57786348e0 + t417 + t617 / 0.3e1
  t620 = t619 ** 2
  t626 = 0.346718088e1 + 0.6e1 * t417 + 0.2e1 * t617
  t627 = t626 * t404
  t631 = -0.148683344e1 * t620 - 0.104705593501958568e1 - 0.463292766e0 * t417 - 0.154430922e0 * t617 - 0.77215461e-1 * t627 * t574 + 0.15e2 * t610
  t632 = t46 * t631
  t634 = 0.462290784e1 + 0.8e1 * t417
  t635 = 0.1e1 / t634
  t636 = jnp.sqrt(t619)
  t638 = 0.1e1 / t636 / t620
  t639 = t635 * t638
  t644 = 0.1e1 / t423 / t376
  t645 = t325 * t644
  t647 = t619 * t404
  t651 = -0.30439865000326428e0 - t570 - 0.25738487000000000000000000000000000000000000000000e-1 * t617 - 0.77215461e-1 * t647 * t574 + 0.5e1 * t610
  t653 = 0.1e1 / t568
  t654 = t653 * t638
  t658 = t423 ** 2
  t662 = t343 * t345 / t658 / t376
  t663 = -0.51955731e-1 + t610
  t664 = t352 * t663
  t665 = t613 * t638
  t669 = -0.8e1 / 0.9e1 * t565 - 0.4e1 / 0.9e1 * t612 * t613 + 0.8e1 / 0.27e2 * t616 * t632 * t639 + 0.4e1 / 0.27e2 * t645 * t8 * t651 * t654 + 0.8e1 / 0.81e2 * t662 * t664 * t665
  t673 = f.my_piecewise3(t364, 0, -0.3e1 / 0.8e1 * t6 * t371 * t669)
  t674 = t7 ** 2
  t675 = 0.1e1 / t674
  t676 = t18 * t675
  t677 = t8 - t676
  t678 = f.my_piecewise5(t12, 0, t16, 0, t677)
  t681 = f.my_piecewise3(t22, 0, 0.4e1 / 0.3e1 * t25 * t678)
  t689 = t6 * t27 * t101 * t359 / 0.8e1
  t691 = t106 - 0.1e1 / t105
  t692 = t74 * t79
  t693 = r0 ** 2
  t698 = t53 * t54 / t55 / t693 / 0.9e1
  t699 = f.my_piecewise3(t62, 0, -t698)
  t700 = f.my_piecewise3(t64, t699, 0)
  t702 = 0.1e1 / t68
  t705 = f.my_piecewise3(t62, 0, -t700 * t67 * t702 + t700)
  t706 = f.my_piecewise3(t61, -t698, t705)
  t707 = f.my_piecewise3(t73, 0, t706)
  t709 = t692 * t87 * t707
  t710 = 0.44286352009183217952624232074656160763000701495816e1 * t709
  t711 = t74 * t707
  t713 = t75 * t74
  t714 = t713 * t707
  t716 = 0.1959362e-1 * t711 + 0.1643336e0 * t714
  t718 = t75 * t716 * t87
  t719 = 0.22143176004591608976312116037328080381500350747908e1 * t718
  t720 = t86 ** 2
  t721 = 0.1e1 / t720
  t727 = 0.749760e0 * t714 + 0.604120e-2 * t77 * t707 + 0.2083128e0 * t82 * t707
  t729 = t80 * t721 * t727
  t730 = 0.22143176004591608976312116037328080381500350747908e1 * t729
  t731 = f.my_piecewise3(t90, 0, 0)
  t734 = t731 * t92 * t3 * t102
  t735 = 0.73810586681972029921040386791093601271667835826361e0 * t734
  t736 = t96 * t327
  t737 = t42 ** 2
  t738 = 0.1e1 / t737
  t739 = f.my_piecewise5(t36, 0, t38, 0, t677)
  t742 = f.my_piecewise3(t41, 0, t738 * t739 / 0.3e1)
  t745 = t94 * t736 * t101 * t742
  t747 = t99 * t352
  t748 = t94 * t747
  t749 = 0.49207057787981353280693591194062400847778557217574e0 * t748
  t753 = 0.2e1 * t709
  t754 = t734 / 0.3e1
  t756 = 0.2e1 / 0.9e1 * t748
  t757 = t753 + t718 - t729 + t754 - 0.2e1 / 0.3e1 * t745 - t756
  t758 = 0.1e1 / t109
  t761 = 0.1e1 / t112
  t765 = t184 * t213
  t766 = t186 * t122
  t767 = f.my_piecewise3(t128, 0, 0)
  t768 = t767 * t118
  t769 = t129 * t116
  t770 = t31 * t34
  t771 = t98 * t46
  t776 = 0.1e1 / t28 / t7
  t779 = t31 * t45 * t776 / 0.9e1
  t781 = f.my_piecewise3(t50, 0, -t770 * t771 * t742 / 0.3e1 - t779)
  t782 = t769 * t781
  t784 = t753 + t718 - t729 + t768 + 0.2e1 * t782
  t788 = t184 * t185
  t789 = t214 * t122
  t793 = t186 * t121
  t799 = t212 / t149 / t219
  t800 = t214 * t124
  t804 = t212 * t213
  t807 = 0.1e1 / t158 / t223 * t124
  t811 = t214 * t139
  t840 = t195 * t234
  t847 = t175 * t208
  t850 = t157 * t784
  t855 = 0.60966864e1 * t768
  t866 = t231 / t219 / t148
  t870 = t196 ** 2
  t872 = 0.1e1 / t870 * t141
  t876 = t234 * t124
  t880 = 0.13121240635082825996265774798585671062234724751465e0 * t765 * t766 * t784 + 0.78727443810496955977594648791514026373408348508790e-1 * t788 * t789 * t784 - 0.26242481270165651992531549597171342124469449502930e0 * t788 * t793 * t781 - 0.51668238746022973860192484604542017837436520273649e-2 * t799 * t800 * t784 - 0.36905884818587838471566060431815727026740371624035e-2 * t804 * t807 * t784 + 0.10333647749204594772038496920908403567487304054730e-1 * t804 * t811 * t781 - (0.65373131959333695000000000000000000000000000000000e1 * t116 * t781 - 0.19367359552567034036718700177853989668879803297739e2 * t119 * t781 + 0.16341819411519396330339610941409360252519729667069e2 * t122 * t781 - 0.16419662276459916693266075252366173574438528008930e1 * t124 * t781) * t144 / 0.2e1 + (0.10933029406300511250000000000000000000000000000000e1 * t197 * t784 - 0.98748521025470224075440000000000000000000000000000e0 * t192 * t784) * t121 + (-0.75257653856463150589440000000000000000000000000000e0 * t232 * t784 + 0.77150160881310000000000000000000000000000000000000e-2 * (0.15943086723305958462944723546876217874680252538494e3 * t709 + 0.79715433616529792314723617734381089373401262692468e2 * t718 - 0.79715433616529792314723617734381089373401262692468e2 * t729) * t197 - 0.15430032176262000000000000000000000000000000000000e-1 * t840 * t784) * t139 + 0.14762353927435135388626424172726290810696148649614e-2 * t147 * (-0.10491264061509704739840000000000000000000000000000e3 * t181 * t784 + 0.63e2 / 0.2e1 * t847 * t784 + 0.9e1 * t204 * (0.54e2 * t850 - 0.121933728e2 * t709 - 0.60966864e1 * t718 + 0.60966864e1 * t729 - t855 - 0.121933728e2 * t782)) * t216 - 0.30266681701871704406938327511438673174852751088837e-1 * t866 * t235 * t784 - 0.22700011276403778305203745633579004881139563316628e-1 * t233 * t872 * t784 + 0.60533363403743408813876655022877346349705502177674e-1 * t233 * t876 * t781
  t885 = (0.2e1 * t133 * t134 - 0.2e1 * t279) / t133
  t886 = 0.22143176004591608976312116037328080381500350747908e1 * t768
  t888 = t710 + t719 - t730 + t886 + 0.44286352009183217952624232074656160763000701495816e1 * t782
  t892 = t161 * t178
  t898 = 0.9e1 * t768
  t911 = 0.812782661649802026365952e2 * t767 * t219 * t157
  t912 = t129 * t191
  t919 = t191 * t228
  t926 = 0.3292210656e3 * t768
  t935 = t147 * t162
  t939 = t118 * t781
  t943 = t157 * t171
  t949 = t200 * t122
  t952 = t173 * t119
  t967 = t143 * (t144 - 0.1e1 / t132)
  t972 = t171 * t118
  t975 = t154 * t116
  t986 = t127 * t885 * t888 / 0.4e1 - 0.52484962540331303985063099194342684248938899005860e-1 * t147 * (0.15e2 / 0.2e1 * t892 * t784 + 0.3e1 * t175 * (0.18e2 * t709 + 0.9e1 * t718 - 0.9e1 * t729 + t898 + 0.18e2 * t782) + 0.61949308433241600000000000000000000000000000000000e1 * t158 * t784) * t188 + 0.75666704254679261017345818778596682937131877722093e-2 * (t911 + 0.3251130646599208105463808e3 * t912 * t850 + 0.812782661649802026365952e2 * t220 * t784 + 0.10154353453129624971956138067322994688e2 * t196 * t784 + 0.33607172124864e-1 * t919 * t784 + 0.8401793031216e-2 * t219 * (-0.1458e4 * t850 + 0.6584421312e3 * t709 + 0.3292210656e3 * t718 - 0.3292210656e3 * t729 + t926 + 0.6584421312e3 * t782)) * t232 * t235 + 0.28660114966822951294620000000000000000000000000000e0 * t935 * t116 * t784 - 0.3729486898170981e1 * t165 * t939 + 0.50805720000000000000000000000000000000000000000000e0 * (t784 * t154 - t943 * t784) * t168 * t148 + 0.6e1 * t949 * t781 + 0.4e1 * t952 * t781 + (0.17059169152930056820161893079623736851681581580379e1 * t781 - 0.12486811621932118969348457381157906348347093175807e2 * t939 + 0.21087185174347324501399437074071300629862851476126e2 * t121 * t781 - 0.74732563294431684431147134157010616586775283695195e1 * t139 * t781) * jnp.pi * t134 / 0.2e1 - t967 * t888 / 0.2e1 - 0.57320229933645902589240000000000000000000000000000e0 * t151 * t781 - 0.73807311952199090994120000000000000000000000000000e0 * t972 * t784 + 0.14761462390439818198824000000000000000000000000000e1 * t975 * t781 - 0.1243162299390327e1 * t147 * (0.9e1 / 0.16e2 * t186 * t784 - 0.38104290000000000000000000000000000000000000000000e0 * t185 * t784) * t119
  t988 = f.my_piecewise3(t50, 0.50805720000000000000000000000000000000000000000000e0 * t691 * (t710 + t719 - t730 + t735 - 0.14762117336394405984208077358218720254333567165272e1 * t745 - t749) - 0.50805720000000000000000000000000000000000000000000e0 * t757 * t758 + 0.50805720000000000000000000000000000000000000000000e0 * t757 * t761, t880 + t986)
  t990 = t753 + t718 - t729
  t991 = t244 * t990
  t993 = 0.154430922e0 * t709
  t994 = 0.77215461e-1 * t718
  t995 = 0.77215461e-1 * t729
  t999 = t244 * t74
  t1000 = t251 * t707
  t1005 = t79 * t721
  t1008 = 0.64753871e1 * t716 * t87 - 0.64753871e1 * t1005 * t727
  t1011 = t74 * t288
  t1012 = t1011 * t707
  t1016 = t251 * t74
  t1029 = t245 ** 2
  t1031 = 0.1e1 / t265 / t1029
  t1037 = t270 * t275
  t1040 = t147 * t270
  t1042 = jnp.exp(-0.22143176004591608976312116037328080381500350747909e1 * t88)
  t1044 = t1042 / t272
  t1053 = 0.1e1 / t713 * t266
  t1058 = t281 * t265 * t245
  t1066 = f.my_piecewise3(t254, -0.16e2 / 0.15e2 * (t147 * ((-0.463292766e0 * t1008 * t75 - 0.926585532e0 * t1016 * t707) * t244 + t258 * t990 - 0.297366688e1 * t991 + 0.243867456e2 * t245 * t990) * t267 / 0.16e2 - 0.7e1 / 0.32e2 * t264 * t1031 * t990 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * (t710 + t719 - t730) * t1037 + 0.11250000000000000000000000000000000000000000000000e1 * t1040 * t1044 * t990) * t279 * t282 + 0.32e2 / 0.15e2 * t280 * t1053 * t707 - 0.56e2 / 0.15e2 * t280 * t1058 * t990, -0.14235295576e0 * t711 + 0.34138165292e0 * t714)
  t1067 = t75 * t1066
  t1072 = 0.1e1 / t1029
  t1073 = t291 * t1072
  t1077 = t31 * t34 * t98
  t1085 = 0.8e1 / 0.81e2 * t295 * t776 * t311 * t319
  t1086 = t296 * t96
  t1087 = t327 * t101
  t1089 = t1086 * t1087 * t742
  t1091 = t296 * t747
  t1092 = 0.2e1 / 0.9e1 * t1091
  t1093 = t753 + t718 - t729 - 0.2e1 / 0.3e1 * t1089 - t1092
  t1100 = 0.10295394800000000000000000000000000000000000000000e0 * t1091
  t1105 = 0.4e1 / 0.3e1 * t1091
  t1110 = t306 * t74
  t1117 = -0.297366688e1 * t299 * t1093 - 0.926585532e0 * t709 - 0.463292766e0 * t718 + 0.463292766e0 * t729 + 0.308861844e0 * t1089 + t1100 - 0.77215461e-1 * (0.12e2 * t709 + 0.6e1 * t718 - 0.6e1 * t729 - 0.4e1 * t1089 - t1105) * t75 * t251 - 0.154430922e0 * t1110 * t1000 - 0.77215461e-1 * t307 * t1008 + 0.30e2 * t1012 + 0.15e2 * t1067
  t1122 = t314 ** 2
  t1124 = 0.1e1 / t1122 * t318
  t1135 = 0.1e1 / t316 / t300 / t299
  t1136 = t315 * t1135
  t1143 = t325 / t346 * t8
  t1144 = t334 * t336
  t1152 = 0.4e1 / 0.27e2 * t328 * t675 * t334 * t337
  t1154 = 0.17158991333333333333333333333333333333333333333333e-1 * t1091
  t1158 = t299 * t74
  t1171 = t325 * t327 * t8
  t1172 = t334 * t292
  t1184 = t343 * t345 / t346 / t97
  t1190 = 0.1e1 / t100 / t674
  t1194 = 0.40e2 / 0.243e3 * t350 * t1190 * t353 * t355
  t1201 = t1072 * t318
  t1206 = t292 * t1135
  t1211 = -0.8e1 / 0.9e1 * t988 - 0.4e1 / 0.9e1 * (-0.74341672e0 * t991 - t993 - t994 + t995 - 0.77215461e-1 * t990 * t75 * t251 - 0.154430922e0 * t999 * t1000 - 0.77215461e-1 * t248 * t1008 + 0.4e1 * t1012 + 0.2e1 * t1067) * t292 + 0.4e1 / 0.3e1 * t1073 * t990 - 0.8e1 / 0.27e2 * t1077 * t312 * t319 * t742 - t1085 + 0.8e1 / 0.27e2 * t295 * t46 * t1117 * t319 - 0.8e1 / 0.27e2 * t295 * t312 * t1124 * (0.16e2 * t709 + 0.8e1 * t718 - 0.8e1 * t729) - 0.20e2 / 0.27e2 * t295 * t312 * t1136 * t1093 - 0.4e1 / 0.9e1 * t1143 * t1144 * t318 * t742 - t1152 + 0.4e1 / 0.27e2 * t328 * t8 * (-t993 - t994 + t995 + 0.51476974000000000000000000000000000000000000000000e-1 * t1089 + t1154 - 0.77215461e-1 * t1093 * t75 * t251 - 0.154430922e0 * t1158 * t1000 - 0.77215461e-1 * t330 * t1008 + 0.10e2 * t1012 + 0.5e1 * t1067) * t337 - 0.8e1 / 0.27e2 * t1171 * t1172 * t318 * t990 - 0.10e2 / 0.27e2 * t1171 * t1144 * t1135 * t1093 - 0.40e2 / 0.81e2 * t1184 * t354 * t355 * t742 - t1194 + 0.8e1 / 0.81e2 * t350 * t352 * (0.2e1 * t1012 + t1067) * t355 - 0.8e1 / 0.27e2 * t350 * t354 * t1201 * t990 - 0.20e2 / 0.81e2 * t350 * t354 * t1206 * t1093
  t1216 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t681 * t28 * t359 - t689 - 0.3e1 / 0.8e1 * t6 * t29 * t1211)
  t1217 = -t677
  t1218 = f.my_piecewise5(t16, 0, t12, 0, t1217)
  t1221 = f.my_piecewise3(t367, 0, 0.4e1 / 0.3e1 * t368 * t1218)
  t1229 = t6 * t370 * t101 * t669 / 0.8e1
  t1231 = t430 - 0.1e1 / t429
  t1232 = f.my_piecewise3(t419, 0, 0)
  t1235 = t1232 * t92 * t3 * t426
  t1236 = 0.73810586681972029921040386791093601271667835826361e0 * t1235
  t1237 = t96 * t644
  t1238 = t375 ** 2
  t1239 = 0.1e1 / t1238
  t1240 = f.my_piecewise5(t38, 0, t36, 0, t1217)
  t1243 = f.my_piecewise3(t374, 0, t1239 * t1240 / 0.3e1)
  t1246 = t422 * t1237 * t101 * t1243
  t1248 = t425 * t352
  t1249 = t422 * t1248
  t1250 = 0.49207057787981353280693591194062400847778557217574e0 * t1249
  t1254 = t1235 / 0.3e1
  t1256 = 0.2e1 / 0.9e1 * t1249
  t1257 = t1254 - 0.2e1 / 0.3e1 * t1246 - t1256
  t1258 = 0.1e1 / t433
  t1261 = 0.1e1 / t436
  t1265 = t507 * t508
  t1266 = t537 * t446
  t1267 = f.my_piecewise3(t452, 0, 0)
  t1268 = t1267 * t442
  t1269 = t453 * t440
  t1270 = t424 * t46
  t1276 = t31 * t378 * t776 / 0.9e1
  t1278 = f.my_piecewise3(t382, 0, -t770 * t1270 * t1243 / 0.3e1 - t1276)
  t1279 = t1269 * t1278
  t1281 = t1268 + 0.2e1 * t1279
  t1285 = t509 * t445
  t1291 = t535 / t472 / t542
  t1292 = t537 * t448
  t1296 = t535 * t536
  t1299 = 0.1e1 / t481 / t546 * t448
  t1303 = t537 * t463
  t1307 = t507 * t536
  t1308 = t509 * t446
  t1331 = t518 * t557
  t1336 = t147 * t485
  t1340 = t442 * t1278
  t1345 = 0.812782661649802026365952e2 * t1267 * t542 * t480
  t1346 = t453 * t514
  t1347 = t480 * t1281
  t1354 = t514 * t551
  t1358 = 0.3292210656e3 * t1268
  t1371 = (0.2e1 * t457 * t458 - 0.2e1 * t279) / t457
  t1372 = 0.22143176004591608976312116037328080381500350747908e1 * t1268
  t1374 = t1372 + 0.44286352009183217952624232074656160763000701495816e1 * t1279
  t1378 = 0.78727443810496955977594648791514026373408348508790e-1 * t1265 * t1266 * t1281 - 0.26242481270165651992531549597171342124469449502930e0 * t1265 * t1285 * t1278 - 0.51668238746022973860192484604542017837436520273649e-2 * t1291 * t1292 * t1281 - 0.36905884818587838471566060431815727026740371624035e-2 * t1296 * t1299 * t1281 + 0.10333647749204594772038496920908403567487304054730e-1 * t1296 * t1303 * t1278 + 0.13121240635082825996265774798585671062234724751465e0 * t1307 * t1308 * t1281 - (0.65373131959333695000000000000000000000000000000000e1 * t440 * t1278 - 0.19367359552567034036718700177853989668879803297739e2 * t443 * t1278 + 0.16341819411519396330339610941409360252519729667069e2 * t446 * t1278 - 0.16419662276459916693266075252366173574438528008930e1 * t448 * t1278) * t468 / 0.2e1 + (0.10933029406300511250000000000000000000000000000000e1 * t520 * t1281 - 0.98748521025470224075440000000000000000000000000000e0 * t515 * t1281) * t445 + (-0.75257653856463150589440000000000000000000000000000e0 * t555 * t1281 - 0.15430032176262000000000000000000000000000000000000e-1 * t1331 * t1281) * t463 + 0.28660114966822951294620000000000000000000000000000e0 * t1336 * t440 * t1281 - 0.3729486898170981e1 * t488 * t1340 + 0.75666704254679261017345818778596682937131877722093e-2 * (t1345 + 0.3251130646599208105463808e3 * t1346 * t1347 + 0.812782661649802026365952e2 * t543 * t1281 + 0.10154353453129624971956138067322994688e2 * t519 * t1281 + 0.33607172124864e-1 * t1354 * t1281 + 0.8401793031216e-2 * t542 * (-0.1458e4 * t1347 + t1358 + 0.6584421312e3 * t1279)) * t555 * t558 + t451 * t1371 * t1374 / 0.4e1
  t1379 = t484 * t501
  t1382 = 0.9e1 * t1268
  t1395 = t498 * t531
  t1399 = 0.60966864e1 * t1268
  t1410 = t554 / t542 / t471
  t1414 = t519 ** 2
  t1416 = 0.1e1 / t1414 * t465
  t1420 = t557 * t448
  t1425 = t480 * t494
  t1443 = t467 * (t468 - 0.1e1 / t456)
  t1448 = t494 * t442
  t1451 = t477 * t440
  t1462 = t496 * t443
  t1465 = t523 * t446
  t1468 = -0.52484962540331303985063099194342684248938899005860e-1 * t147 * (0.15e2 / 0.2e1 * t1379 * t1281 + 0.3e1 * t498 * (t1382 + 0.18e2 * t1279) + 0.61949308433241600000000000000000000000000000000000e1 * t481 * t1281) * t511 + 0.14762353927435135388626424172726290810696148649614e-2 * t147 * (-0.10491264061509704739840000000000000000000000000000e3 * t504 * t1281 + 0.63e2 / 0.2e1 * t1395 * t1281 + 0.9e1 * t527 * (0.54e2 * t1347 - t1399 - 0.121933728e2 * t1279)) * t539 - 0.30266681701871704406938327511438673174852751088837e-1 * t1410 * t558 * t1281 - 0.22700011276403778305203745633579004881139563316628e-1 * t556 * t1416 * t1281 + 0.60533363403743408813876655022877346349705502177674e-1 * t556 * t1420 * t1278 + 0.50805720000000000000000000000000000000000000000000e0 * (-t1425 * t1281 + t1281 * t477) * t491 * t471 + (0.17059169152930056820161893079623736851681581580379e1 * t1278 - 0.12486811621932118969348457381157906348347093175807e2 * t1340 + 0.21087185174347324501399437074071300629862851476126e2 * t445 * t1278 - 0.74732563294431684431147134157010616586775283695195e1 * t463 * t1278) * jnp.pi * t458 / 0.2e1 - t1443 * t1374 / 0.2e1 - 0.57320229933645902589240000000000000000000000000000e0 * t474 * t1278 - 0.73807311952199090994120000000000000000000000000000e0 * t1448 * t1281 + 0.14761462390439818198824000000000000000000000000000e1 * t1451 * t1278 - 0.1243162299390327e1 * t147 * (0.9e1 / 0.16e2 * t509 * t1281 - 0.38104290000000000000000000000000000000000000000000e0 * t508 * t1281) * t443 + 0.4e1 * t1462 * t1278 + 0.6e1 * t1465 * t1278
  t1470 = f.my_piecewise3(t382, 0.50805720000000000000000000000000000000000000000000e0 * t1231 * (t1236 - 0.14762117336394405984208077358218720254333567165272e1 * t1246 - t1250) - 0.50805720000000000000000000000000000000000000000000e0 * t1257 * t1258 + 0.50805720000000000000000000000000000000000000000000e0 * t1257 * t1261, t1378 + t1468)
  t1473 = t31 * t34 * t424
  t1481 = 0.8e1 / 0.81e2 * t616 * t776 * t631 * t639
  t1482 = t644 * t101
  t1484 = t1086 * t1482 * t1243
  t1486 = t296 * t1248
  t1487 = 0.2e1 / 0.9e1 * t1486
  t1488 = -0.2e1 / 0.3e1 * t1484 - t1487
  t1492 = 0.10295394800000000000000000000000000000000000000000e0 * t1486
  t1494 = 0.4e1 / 0.3e1 * t1486
  t1506 = 0.1e1 / t636 / t620 / t619
  t1507 = t635 * t1506
  t1514 = t325 / t658 * t8
  t1515 = t651 * t653
  t1523 = 0.4e1 / 0.27e2 * t645 * t675 * t651 * t654
  t1525 = 0.17158991333333333333333333333333333333333333333333e-1 * t1486
  t1535 = t325 * t644 * t8
  t1543 = t343 * t345 / t658 / t423
  t1551 = 0.40e2 / 0.243e3 * t662 * t1190 * t663 * t665
  t1552 = t613 * t1506
  t1557 = -0.8e1 / 0.9e1 * t1470 - 0.8e1 / 0.27e2 * t1473 * t632 * t639 * t1243 - t1481 + 0.8e1 / 0.27e2 * t616 * t46 * (-0.297366688e1 * t619 * t1488 + 0.308861844e0 * t1484 + t1492 - 0.77215461e-1 * (-0.4e1 * t1484 - t1494) * t404 * t574) * t639 - 0.20e2 / 0.27e2 * t616 * t632 * t1507 * t1488 - 0.4e1 / 0.9e1 * t1514 * t1515 * t638 * t1243 - t1523 + 0.4e1 / 0.27e2 * t645 * t8 * (0.51476974000000000000000000000000000000000000000000e-1 * t1484 + t1525 - 0.77215461e-1 * t1488 * t404 * t574) * t654 - 0.10e2 / 0.27e2 * t1535 * t1515 * t1506 * t1488 - 0.40e2 / 0.81e2 * t1543 * t664 * t665 * t1243 - t1551 - 0.20e2 / 0.81e2 * t662 * t664 * t1552 * t1488
  t1562 = f.my_piecewise3(t364, 0, -0.3e1 / 0.8e1 * t6 * t1221 * t28 * t669 - t1229 - 0.3e1 / 0.8e1 * t6 * t371 * t1557)
  vrho_0_ = t363 + t673 + t7 * (t1216 + t1562)
  t1565 = -t8 - t676
  t1566 = f.my_piecewise5(t12, 0, t16, 0, t1565)
  t1569 = f.my_piecewise3(t22, 0, 0.4e1 / 0.3e1 * t25 * t1566)
  t1574 = f.my_piecewise5(t36, 0, t38, 0, t1565)
  t1577 = f.my_piecewise3(t41, 0, t738 * t1574 / 0.3e1)
  t1580 = t94 * t736 * t101 * t1577
  t1586 = t754 - 0.2e1 / 0.3e1 * t1580 - t756
  t1596 = f.my_piecewise3(t50, 0, -t770 * t771 * t1577 / 0.3e1 - t779)
  t1597 = t769 * t1596
  t1599 = t768 + 0.2e1 * t1597
  t1623 = t157 * t1599
  t1644 = t118 * t1596
  t1668 = t886 + 0.44286352009183217952624232074656160763000701495816e1 * t1597
  t1675 = (0.10933029406300511250000000000000000000000000000000e1 * t197 * t1599 - 0.98748521025470224075440000000000000000000000000000e0 * t192 * t1599) * t121 + (-0.75257653856463150589440000000000000000000000000000e0 * t232 * t1599 - 0.15430032176262000000000000000000000000000000000000e-1 * t840 * t1599) * t139 - (0.65373131959333695000000000000000000000000000000000e1 * t116 * t1596 - 0.19367359552567034036718700177853989668879803297739e2 * t119 * t1596 + 0.16341819411519396330339610941409360252519729667069e2 * t122 * t1596 - 0.16419662276459916693266075252366173574438528008930e1 * t124 * t1596) * t144 / 0.2e1 + 0.75666704254679261017345818778596682937131877722093e-2 * (t911 + 0.3251130646599208105463808e3 * t912 * t1623 + 0.812782661649802026365952e2 * t220 * t1599 + 0.10154353453129624971956138067322994688e2 * t196 * t1599 + 0.33607172124864e-1 * t919 * t1599 + 0.8401793031216e-2 * t219 * (-0.1458e4 * t1623 + t926 + 0.6584421312e3 * t1597)) * t232 * t235 + 0.28660114966822951294620000000000000000000000000000e0 * t935 * t116 * t1599 - 0.3729486898170981e1 * t165 * t1644 + 0.4e1 * t952 * t1596 + 0.6e1 * t949 * t1596 + 0.50805720000000000000000000000000000000000000000000e0 * (t1599 * t154 - t943 * t1599) * t168 * t148 + (0.17059169152930056820161893079623736851681581580379e1 * t1596 - 0.12486811621932118969348457381157906348347093175807e2 * t1644 + 0.21087185174347324501399437074071300629862851476126e2 * t121 * t1596 - 0.74732563294431684431147134157010616586775283695195e1 * t139 * t1596) * jnp.pi * t134 / 0.2e1 - t967 * t1668 / 0.2e1 - 0.57320229933645902589240000000000000000000000000000e0 * t151 * t1596 - 0.73807311952199090994120000000000000000000000000000e0 * t972 * t1599
  t1741 = 0.14761462390439818198824000000000000000000000000000e1 * t975 * t1596 - 0.1243162299390327e1 * t147 * (0.9e1 / 0.16e2 * t186 * t1599 - 0.38104290000000000000000000000000000000000000000000e0 * t185 * t1599) * t119 + t127 * t885 * t1668 / 0.4e1 - 0.52484962540331303985063099194342684248938899005860e-1 * t147 * (0.15e2 / 0.2e1 * t892 * t1599 + 0.3e1 * t175 * (t898 + 0.18e2 * t1597) + 0.61949308433241600000000000000000000000000000000000e1 * t158 * t1599) * t188 + 0.14762353927435135388626424172726290810696148649614e-2 * t147 * (-0.10491264061509704739840000000000000000000000000000e3 * t181 * t1599 + 0.63e2 / 0.2e1 * t847 * t1599 + 0.9e1 * t204 * (0.54e2 * t1623 - t855 - 0.121933728e2 * t1597)) * t216 - 0.30266681701871704406938327511438673174852751088837e-1 * t866 * t235 * t1599 - 0.22700011276403778305203745633579004881139563316628e-1 * t233 * t872 * t1599 + 0.60533363403743408813876655022877346349705502177674e-1 * t233 * t876 * t1596 + 0.13121240635082825996265774798585671062234724751465e0 * t765 * t766 * t1599 + 0.78727443810496955977594648791514026373408348508790e-1 * t788 * t789 * t1599 - 0.26242481270165651992531549597171342124469449502930e0 * t788 * t793 * t1596 - 0.51668238746022973860192484604542017837436520273649e-2 * t799 * t800 * t1599 - 0.36905884818587838471566060431815727026740371624035e-2 * t804 * t807 * t1599 + 0.10333647749204594772038496920908403567487304054730e-1 * t804 * t811 * t1596
  t1743 = f.my_piecewise3(t50, 0.50805720000000000000000000000000000000000000000000e0 * t691 * (t735 - 0.14762117336394405984208077358218720254333567165272e1 * t1580 - t749) - 0.50805720000000000000000000000000000000000000000000e0 * t1586 * t758 + 0.50805720000000000000000000000000000000000000000000e0 * t1586 * t761, t1675 + t1741)
  t1750 = t1086 * t1087 * t1577
  t1752 = -0.2e1 / 0.3e1 * t1750 - t1092
  t1795 = -0.8e1 / 0.9e1 * t1743 - 0.8e1 / 0.27e2 * t1077 * t312 * t319 * t1577 - t1085 + 0.8e1 / 0.27e2 * t295 * t46 * (-0.297366688e1 * t299 * t1752 + 0.308861844e0 * t1750 + t1100 - 0.77215461e-1 * (-0.4e1 * t1750 - t1105) * t75 * t251) * t319 - 0.20e2 / 0.27e2 * t295 * t312 * t1136 * t1752 - 0.4e1 / 0.9e1 * t1143 * t1144 * t318 * t1577 - t1152 + 0.4e1 / 0.27e2 * t328 * t8 * (0.51476974000000000000000000000000000000000000000000e-1 * t1750 + t1154 - 0.77215461e-1 * t1752 * t75 * t251) * t337 - 0.10e2 / 0.27e2 * t1171 * t1144 * t1135 * t1752 - 0.40e2 / 0.81e2 * t1184 * t354 * t355 * t1577 - t1194 - 0.20e2 / 0.81e2 * t350 * t354 * t1206 * t1752
  t1800 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t1569 * t28 * t359 - t689 - 0.3e1 / 0.8e1 * t6 * t29 * t1795)
  t1801 = -t1565
  t1802 = f.my_piecewise5(t16, 0, t12, 0, t1801)
  t1805 = f.my_piecewise3(t367, 0, 0.4e1 / 0.3e1 * t368 * t1802)
  t1810 = t403 * t408
  t1811 = r1 ** 2
  t1816 = t53 * t383 / t384 / t1811 / 0.9e1
  t1817 = f.my_piecewise3(t391, 0, -t1816)
  t1818 = f.my_piecewise3(t393, t1817, 0)
  t1820 = 0.1e1 / t397
  t1823 = f.my_piecewise3(t391, 0, -t1818 * t396 * t1820 + t1818)
  t1824 = f.my_piecewise3(t390, -t1816, t1823)
  t1825 = f.my_piecewise3(t402, 0, t1824)
  t1827 = t1810 * t416 * t1825
  t1828 = 0.44286352009183217952624232074656160763000701495816e1 * t1827
  t1829 = t403 * t1825
  t1831 = t404 * t403
  t1832 = t1831 * t1825
  t1834 = 0.1959362e-1 * t1829 + 0.1643336e0 * t1832
  t1836 = t404 * t1834 * t416
  t1837 = 0.22143176004591608976312116037328080381500350747908e1 * t1836
  t1838 = t415 ** 2
  t1839 = 0.1e1 / t1838
  t1845 = 0.749760e0 * t1832 + 0.604120e-2 * t406 * t1825 + 0.2083128e0 * t411 * t1825
  t1847 = t409 * t1839 * t1845
  t1848 = 0.22143176004591608976312116037328080381500350747908e1 * t1847
  t1849 = f.my_piecewise5(t38, 0, t36, 0, t1801)
  t1852 = f.my_piecewise3(t374, 0, t1239 * t1849 / 0.3e1)
  t1855 = t422 * t1237 * t101 * t1852
  t1860 = 0.2e1 * t1827
  t1862 = t1860 + t1836 - t1847 + t1254 - 0.2e1 / 0.3e1 * t1855 - t1256
  t1872 = f.my_piecewise3(t382, 0, -t770 * t1270 * t1852 / 0.3e1 - t1276)
  t1873 = t1269 * t1872
  t1875 = t1860 + t1836 - t1847 + t1268 + 0.2e1 * t1873
  t1876 = t480 * t1875
  t1900 = t442 * t1872
  t1964 = 0.75666704254679261017345818778596682937131877722093e-2 * (t1345 + 0.3251130646599208105463808e3 * t1346 * t1876 + 0.812782661649802026365952e2 * t543 * t1875 + 0.10154353453129624971956138067322994688e2 * t519 * t1875 + 0.33607172124864e-1 * t1354 * t1875 + 0.8401793031216e-2 * t542 * (-0.1458e4 * t1876 + 0.6584421312e3 * t1827 + 0.3292210656e3 * t1836 - 0.3292210656e3 * t1847 + t1358 + 0.6584421312e3 * t1873)) * t555 * t558 + 0.28660114966822951294620000000000000000000000000000e0 * t1336 * t440 * t1875 - 0.3729486898170981e1 * t488 * t1900 - (0.65373131959333695000000000000000000000000000000000e1 * t440 * t1872 - 0.19367359552567034036718700177853989668879803297739e2 * t443 * t1872 + 0.16341819411519396330339610941409360252519729667069e2 * t446 * t1872 - 0.16419662276459916693266075252366173574438528008930e1 * t448 * t1872) * t468 / 0.2e1 + (0.10933029406300511250000000000000000000000000000000e1 * t520 * t1875 - 0.98748521025470224075440000000000000000000000000000e0 * t515 * t1875) * t445 + (-0.75257653856463150589440000000000000000000000000000e0 * t555 * t1875 + 0.77150160881310000000000000000000000000000000000000e-2 * (0.15943086723305958462944723546876217874680252538494e3 * t1827 + 0.79715433616529792314723617734381089373401262692468e2 * t1836 - 0.79715433616529792314723617734381089373401262692468e2 * t1847) * t520 - 0.15430032176262000000000000000000000000000000000000e-1 * t1331 * t1875) * t463 - 0.57320229933645902589240000000000000000000000000000e0 * t474 * t1872 - 0.73807311952199090994120000000000000000000000000000e0 * t1448 * t1875 + 0.14761462390439818198824000000000000000000000000000e1 * t1451 * t1872 - 0.1243162299390327e1 * t147 * (0.9e1 / 0.16e2 * t509 * t1875 - 0.38104290000000000000000000000000000000000000000000e0 * t508 * t1875) * t443 + (0.17059169152930056820161893079623736851681581580379e1 * t1872 - 0.12486811621932118969348457381157906348347093175807e2 * t1900 + 0.21087185174347324501399437074071300629862851476126e2 * t445 * t1872 - 0.74732563294431684431147134157010616586775283695195e1 * t463 * t1872) * jnp.pi * t458 / 0.2e1 + 0.50805720000000000000000000000000000000000000000000e0 * (-t1425 * t1875 + t1875 * t477) * t491 * t471 + 0.6e1 * t1465 * t1872
  t1968 = t1828 + t1837 - t1848 + t1372 + 0.44286352009183217952624232074656160763000701495816e1 * t1873
  t2032 = 0.4e1 * t1462 * t1872 - t1443 * t1968 / 0.2e1 - 0.52484962540331303985063099194342684248938899005860e-1 * t147 * (0.15e2 / 0.2e1 * t1379 * t1875 + 0.3e1 * t498 * (0.18e2 * t1827 + 0.9e1 * t1836 - 0.9e1 * t1847 + t1382 + 0.18e2 * t1873) + 0.61949308433241600000000000000000000000000000000000e1 * t481 * t1875) * t511 + t451 * t1371 * t1968 / 0.4e1 + 0.14762353927435135388626424172726290810696148649614e-2 * t147 * (-0.10491264061509704739840000000000000000000000000000e3 * t504 * t1875 + 0.63e2 / 0.2e1 * t1395 * t1875 + 0.9e1 * t527 * (0.54e2 * t1876 - 0.121933728e2 * t1827 - 0.60966864e1 * t1836 + 0.60966864e1 * t1847 - t1399 - 0.121933728e2 * t1873)) * t539 - 0.30266681701871704406938327511438673174852751088837e-1 * t1410 * t558 * t1875 - 0.22700011276403778305203745633579004881139563316628e-1 * t556 * t1416 * t1875 + 0.60533363403743408813876655022877346349705502177674e-1 * t556 * t1420 * t1872 + 0.13121240635082825996265774798585671062234724751465e0 * t1307 * t1308 * t1875 + 0.78727443810496955977594648791514026373408348508790e-1 * t1265 * t1266 * t1875 - 0.26242481270165651992531549597171342124469449502930e0 * t1265 * t1285 * t1872 - 0.51668238746022973860192484604542017837436520273649e-2 * t1291 * t1292 * t1875 - 0.36905884818587838471566060431815727026740371624035e-2 * t1296 * t1299 * t1875 + 0.10333647749204594772038496920908403567487304054730e-1 * t1296 * t1303 * t1872
  t2034 = f.my_piecewise3(t382, 0.50805720000000000000000000000000000000000000000000e0 * t1231 * (t1828 + t1837 - t1848 + t1236 - 0.14762117336394405984208077358218720254333567165272e1 * t1855 - t1250) - 0.50805720000000000000000000000000000000000000000000e0 * t1862 * t1258 + 0.50805720000000000000000000000000000000000000000000e0 * t1862 * t1261, t1964 + t2032)
  t2036 = t1860 + t1836 - t1847
  t2037 = t567 * t2036
  t2039 = 0.154430922e0 * t1827
  t2040 = 0.77215461e-1 * t1836
  t2041 = 0.77215461e-1 * t1847
  t2045 = t567 * t403
  t2046 = t574 * t1825
  t2051 = t408 * t1839
  t2054 = 0.64753871e1 * t1834 * t416 - 0.64753871e1 * t2051 * t1845
  t2057 = t403 * t609
  t2058 = t2057 * t1825
  t2062 = t574 * t403
  t2075 = t568 ** 2
  t2077 = 0.1e1 / t587 / t2075
  t2083 = t592 * t597
  t2086 = t147 * t592
  t2088 = jnp.exp(-0.22143176004591608976312116037328080381500350747909e1 * t417)
  t2090 = t2088 / t594
  t2099 = 0.1e1 / t1831 * t588
  t2104 = t602 * t587 * t568
  t2112 = f.my_piecewise3(t577, -0.16e2 / 0.15e2 * (t147 * ((-0.463292766e0 * t2054 * t404 - 0.926585532e0 * t2062 * t1825) * t567 + t580 * t2036 - 0.297366688e1 * t2037 + 0.243867456e2 * t568 * t2036) * t589 / 0.16e2 - 0.7e1 / 0.32e2 * t586 * t2077 * t2036 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * (t1828 + t1837 - t1848) * t2083 + 0.11250000000000000000000000000000000000000000000000e1 * t2086 * t2090 * t2036) * t279 * t603 + 0.32e2 / 0.15e2 * t601 * t2099 * t1825 - 0.56e2 / 0.15e2 * t601 * t2104 * t2036, -0.14235295576e0 * t1829 + 0.34138165292e0 * t1832)
  t2113 = t404 * t2112
  t2118 = 0.1e1 / t2075
  t2119 = t612 * t2118
  t2127 = t1086 * t1482 * t1852
  t2129 = t1860 + t1836 - t1847 - 0.2e1 / 0.3e1 * t2127 - t1487
  t2144 = t626 * t403
  t2151 = -0.297366688e1 * t619 * t2129 - 0.926585532e0 * t1827 - 0.463292766e0 * t1836 + 0.463292766e0 * t1847 + 0.308861844e0 * t2127 + t1492 - 0.77215461e-1 * (0.12e2 * t1827 + 0.6e1 * t1836 - 0.6e1 * t1847 - 0.4e1 * t2127 - t1494) * t404 * t574 - 0.154430922e0 * t2144 * t2046 - 0.77215461e-1 * t627 * t2054 + 0.30e2 * t2058 + 0.15e2 * t2113
  t2156 = t634 ** 2
  t2158 = 0.1e1 / t2156 * t638
  t2179 = t619 * t403
  t2191 = t651 * t613
  t2210 = t2118 * t638
  t2219 = -0.8e1 / 0.9e1 * t2034 - 0.4e1 / 0.9e1 * (-0.74341672e0 * t2037 - t2039 - t2040 + t2041 - 0.77215461e-1 * t2036 * t404 * t574 - 0.154430922e0 * t2045 * t2046 - 0.77215461e-1 * t571 * t2054 + 0.4e1 * t2058 + 0.2e1 * t2113) * t613 + 0.4e1 / 0.3e1 * t2119 * t2036 - 0.8e1 / 0.27e2 * t1473 * t632 * t639 * t1852 - t1481 + 0.8e1 / 0.27e2 * t616 * t46 * t2151 * t639 - 0.8e1 / 0.27e2 * t616 * t632 * t2158 * (0.16e2 * t1827 + 0.8e1 * t1836 - 0.8e1 * t1847) - 0.20e2 / 0.27e2 * t616 * t632 * t1507 * t2129 - 0.4e1 / 0.9e1 * t1514 * t1515 * t638 * t1852 - t1523 + 0.4e1 / 0.27e2 * t645 * t8 * (-t2039 - t2040 + t2041 + 0.51476974000000000000000000000000000000000000000000e-1 * t2127 + t1525 - 0.77215461e-1 * t2129 * t404 * t574 - 0.154430922e0 * t2179 * t2046 - 0.77215461e-1 * t647 * t2054 + 0.10e2 * t2058 + 0.5e1 * t2113) * t654 - 0.8e1 / 0.27e2 * t1535 * t2191 * t638 * t2036 - 0.10e2 / 0.27e2 * t1535 * t1515 * t1506 * t2129 - 0.40e2 / 0.81e2 * t1543 * t664 * t665 * t1852 - t1551 + 0.8e1 / 0.81e2 * t662 * t352 * (0.2e1 * t2058 + t2113) * t665 - 0.8e1 / 0.27e2 * t662 * t664 * t2210 * t2036 - 0.20e2 / 0.81e2 * t662 * t664 * t1552 * t2129
  t2224 = f.my_piecewise3(t364, 0, -0.3e1 / 0.8e1 * t6 * t1805 * t28 * t669 - t1229 - 0.3e1 / 0.8e1 * t6 * t371 * t2219)
  vrho_1_ = t363 + t673 + t7 * (t1800 + t2224)
  t2230 = t53 / t54 * t57 / 0.24e2
  t2231 = f.my_piecewise3(t62, 0, t2230)
  t2232 = f.my_piecewise3(t64, t2231, 0)
  t2236 = f.my_piecewise3(t62, 0, -t2232 * t67 * t702 + t2232)
  t2237 = f.my_piecewise3(t61, t2230, t2236)
  t2238 = f.my_piecewise3(t73, 0, t2237)
  t2240 = t692 * t87 * t2238
  t2242 = t74 * t2238
  t2244 = t713 * t2238
  t2246 = 0.1959362e-1 * t2242 + 0.1643336e0 * t2244
  t2248 = t75 * t2246 * t87
  t2255 = 0.749760e0 * t2244 + 0.604120e-2 * t77 * t2238 + 0.2083128e0 * t82 * t2238
  t2257 = t80 * t721 * t2255
  t2259 = 0.44286352009183217952624232074656160763000701495816e1 * t2240 + 0.22143176004591608976312116037328080381500350747908e1 * t2248 - 0.22143176004591608976312116037328080381500350747908e1 * t2257
  t2263 = 0.2e1 * t2240 + t2248 - t2257
  t2329 = t157 * t2263
  t2378 = t127 * t885 * t2259 / 0.4e1 - t967 * t2259 / 0.2e1 + 0.28660114966822951294620000000000000000000000000000e0 * t935 * t116 * t2263 - 0.73807311952199090994120000000000000000000000000000e0 * t972 * t2263 - 0.1243162299390327e1 * t147 * (0.9e1 / 0.16e2 * t186 * t2263 - 0.38104290000000000000000000000000000000000000000000e0 * t185 * t2263) * t119 + (0.10933029406300511250000000000000000000000000000000e1 * t197 * t2263 - 0.98748521025470224075440000000000000000000000000000e0 * t192 * t2263) * t121 - 0.52484962540331303985063099194342684248938899005860e-1 * t147 * (0.15e2 / 0.2e1 * t892 * t2263 + 0.3e1 * t175 * (0.18e2 * t2240 + 0.9e1 * t2248 - 0.9e1 * t2257) + 0.61949308433241600000000000000000000000000000000000e1 * t158 * t2263) * t188 + 0.13121240635082825996265774798585671062234724751465e0 * t765 * t766 * t2263 + 0.78727443810496955977594648791514026373408348508790e-1 * t788 * t789 * t2263 + (-0.75257653856463150589440000000000000000000000000000e0 * t232 * t2263 + 0.77150160881310000000000000000000000000000000000000e-2 * (0.15943086723305958462944723546876217874680252538494e3 * t2240 + 0.79715433616529792314723617734381089373401262692468e2 * t2248 - 0.79715433616529792314723617734381089373401262692468e2 * t2257) * t197 - 0.15430032176262000000000000000000000000000000000000e-1 * t840 * t2263) * t139 + 0.14762353927435135388626424172726290810696148649614e-2 * t147 * (-0.10491264061509704739840000000000000000000000000000e3 * t181 * t2263 + 0.63e2 / 0.2e1 * t847 * t2263 + 0.9e1 * t204 * (0.54e2 * t2329 - 0.121933728e2 * t2240 - 0.60966864e1 * t2248 + 0.60966864e1 * t2257)) * t216 - 0.51668238746022973860192484604542017837436520273649e-2 * t799 * t800 * t2263 - 0.36905884818587838471566060431815727026740371624035e-2 * t804 * t807 * t2263 + 0.75666704254679261017345818778596682937131877722093e-2 * (0.3251130646599208105463808e3 * t912 * t2329 + 0.812782661649802026365952e2 * t220 * t2263 + 0.10154353453129624971956138067322994688e2 * t196 * t2263 + 0.33607172124864e-1 * t919 * t2263 + 0.8401793031216e-2 * t219 * (-0.1458e4 * t2329 + 0.6584421312e3 * t2240 + 0.3292210656e3 * t2248 - 0.3292210656e3 * t2257)) * t232 * t235 - 0.30266681701871704406938327511438673174852751088837e-1 * t866 * t235 * t2263 - 0.22700011276403778305203745633579004881139563316628e-1 * t233 * t872 * t2263 + 0.50805720000000000000000000000000000000000000000000e0 * (t2263 * t154 - t943 * t2263) * t168 * t148
  t2379 = f.my_piecewise3(t50, 0.50805720000000000000000000000000000000000000000000e0 * t691 * t2259 - 0.50805720000000000000000000000000000000000000000000e0 * t2263 * t758 + 0.50805720000000000000000000000000000000000000000000e0 * t2263 * t761, t2378)
  t2381 = t244 * t2263
  t2383 = 0.154430922e0 * t2240
  t2384 = 0.77215461e-1 * t2248
  t2385 = 0.77215461e-1 * t2257
  t2388 = 0.77215461e-1 * t2263 * t75 * t251
  t2389 = t251 * t2238
  t2396 = 0.64753871e1 * t2246 * t87 - 0.64753871e1 * t1005 * t2255
  t2399 = t1011 * t2238
  t2438 = f.my_piecewise3(t254, -0.16e2 / 0.15e2 * (t147 * ((-0.463292766e0 * t2396 * t75 - 0.926585532e0 * t1016 * t2238) * t244 + t258 * t2263 - 0.297366688e1 * t2381 + 0.243867456e2 * t245 * t2263) * t267 / 0.16e2 - 0.7e1 / 0.32e2 * t264 * t1031 * t2263 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * t2259 * t1037 + 0.11250000000000000000000000000000000000000000000000e1 * t1040 * t1044 * t2263) * t279 * t282 + 0.32e2 / 0.15e2 * t280 * t1053 * t2238 - 0.56e2 / 0.15e2 * t280 * t1058 * t2263, -0.14235295576e0 * t2242 + 0.34138165292e0 * t2244)
  t2439 = t75 * t2438
  t2514 = -0.8e1 / 0.9e1 * t2379 - 0.4e1 / 0.9e1 * (-0.74341672e0 * t2381 - t2383 - t2384 + t2385 - t2388 - 0.154430922e0 * t999 * t2389 - 0.77215461e-1 * t248 * t2396 + 0.4e1 * t2399 + 0.2e1 * t2439) * t292 + 0.4e1 / 0.3e1 * t1073 * t2263 + 0.8e1 / 0.27e2 * t295 * t46 * (-0.297366688e1 * t299 * t2263 - 0.926585532e0 * t2240 - 0.463292766e0 * t2248 + 0.463292766e0 * t2257 - 0.77215461e-1 * (0.12e2 * t2240 + 0.6e1 * t2248 - 0.6e1 * t2257) * t75 * t251 - 0.154430922e0 * t1110 * t2389 - 0.77215461e-1 * t307 * t2396 + 0.30e2 * t2399 + 0.15e2 * t2439) * t319 - 0.8e1 / 0.27e2 * t295 * t312 * t1124 * (0.16e2 * t2240 + 0.8e1 * t2248 - 0.8e1 * t2257) - 0.20e2 / 0.27e2 * t295 * t312 * t1136 * t2263 + 0.4e1 / 0.27e2 * t328 * t8 * (-t2383 - t2384 + t2385 - t2388 - 0.154430922e0 * t1158 * t2389 - 0.77215461e-1 * t330 * t2396 + 0.10e2 * t2399 + 0.5e1 * t2439) * t337 - 0.8e1 / 0.27e2 * t1171 * t1172 * t318 * t2263 - 0.10e2 / 0.27e2 * t1171 * t1144 * t1135 * t2263 + 0.8e1 / 0.81e2 * t350 * t352 * (0.2e1 * t2399 + t2439) * t355 - 0.8e1 / 0.27e2 * t350 * t354 * t1201 * t2263 - 0.20e2 / 0.81e2 * t350 * t354 * t1206 * t2263
  t2518 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t29 * t2514)
  vsigma_0_ = t7 * t2518
  vsigma_1_ = 0.0e0
  t2522 = t53 / t383 * t386 / 0.24e2
  t2523 = f.my_piecewise3(t391, 0, t2522)
  t2524 = f.my_piecewise3(t393, t2523, 0)
  t2528 = f.my_piecewise3(t391, 0, -t2524 * t396 * t1820 + t2524)
  t2529 = f.my_piecewise3(t390, t2522, t2528)
  t2530 = f.my_piecewise3(t402, 0, t2529)
  t2532 = t1810 * t416 * t2530
  t2534 = t403 * t2530
  t2536 = t1831 * t2530
  t2538 = 0.1959362e-1 * t2534 + 0.1643336e0 * t2536
  t2540 = t404 * t2538 * t416
  t2547 = 0.749760e0 * t2536 + 0.604120e-2 * t406 * t2530 + 0.2083128e0 * t411 * t2530
  t2549 = t409 * t1839 * t2547
  t2551 = 0.44286352009183217952624232074656160763000701495816e1 * t2532 + 0.22143176004591608976312116037328080381500350747908e1 * t2540 - 0.22143176004591608976312116037328080381500350747908e1 * t2549
  t2555 = 0.2e1 * t2532 + t2540 - t2549
  t2621 = t480 * t2555
  t2670 = t451 * t1371 * t2551 / 0.4e1 - t1443 * t2551 / 0.2e1 + 0.28660114966822951294620000000000000000000000000000e0 * t1336 * t440 * t2555 - 0.73807311952199090994120000000000000000000000000000e0 * t1448 * t2555 - 0.1243162299390327e1 * t147 * (0.9e1 / 0.16e2 * t509 * t2555 - 0.38104290000000000000000000000000000000000000000000e0 * t508 * t2555) * t443 + (0.10933029406300511250000000000000000000000000000000e1 * t520 * t2555 - 0.98748521025470224075440000000000000000000000000000e0 * t515 * t2555) * t445 - 0.52484962540331303985063099194342684248938899005860e-1 * t147 * (0.15e2 / 0.2e1 * t1379 * t2555 + 0.3e1 * t498 * (0.18e2 * t2532 + 0.9e1 * t2540 - 0.9e1 * t2549) + 0.61949308433241600000000000000000000000000000000000e1 * t481 * t2555) * t511 + 0.13121240635082825996265774798585671062234724751465e0 * t1307 * t1308 * t2555 + 0.78727443810496955977594648791514026373408348508790e-1 * t1265 * t1266 * t2555 + (-0.75257653856463150589440000000000000000000000000000e0 * t555 * t2555 + 0.77150160881310000000000000000000000000000000000000e-2 * (0.15943086723305958462944723546876217874680252538494e3 * t2532 + 0.79715433616529792314723617734381089373401262692468e2 * t2540 - 0.79715433616529792314723617734381089373401262692468e2 * t2549) * t520 - 0.15430032176262000000000000000000000000000000000000e-1 * t1331 * t2555) * t463 + 0.14762353927435135388626424172726290810696148649614e-2 * t147 * (-0.10491264061509704739840000000000000000000000000000e3 * t504 * t2555 + 0.63e2 / 0.2e1 * t1395 * t2555 + 0.9e1 * t527 * (0.54e2 * t2621 - 0.121933728e2 * t2532 - 0.60966864e1 * t2540 + 0.60966864e1 * t2549)) * t539 - 0.51668238746022973860192484604542017837436520273649e-2 * t1291 * t1292 * t2555 - 0.36905884818587838471566060431815727026740371624035e-2 * t1296 * t1299 * t2555 + 0.75666704254679261017345818778596682937131877722093e-2 * (0.3251130646599208105463808e3 * t1346 * t2621 + 0.812782661649802026365952e2 * t543 * t2555 + 0.10154353453129624971956138067322994688e2 * t519 * t2555 + 0.33607172124864e-1 * t1354 * t2555 + 0.8401793031216e-2 * t542 * (-0.1458e4 * t2621 + 0.6584421312e3 * t2532 + 0.3292210656e3 * t2540 - 0.3292210656e3 * t2549)) * t555 * t558 - 0.30266681701871704406938327511438673174852751088837e-1 * t1410 * t558 * t2555 - 0.22700011276403778305203745633579004881139563316628e-1 * t556 * t1416 * t2555 + 0.50805720000000000000000000000000000000000000000000e0 * (-t1425 * t2555 + t2555 * t477) * t491 * t471
  t2671 = f.my_piecewise3(t382, 0.50805720000000000000000000000000000000000000000000e0 * t1231 * t2551 - 0.50805720000000000000000000000000000000000000000000e0 * t2555 * t1258 + 0.50805720000000000000000000000000000000000000000000e0 * t2555 * t1261, t2670)
  t2673 = t567 * t2555
  t2675 = 0.154430922e0 * t2532
  t2676 = 0.77215461e-1 * t2540
  t2677 = 0.77215461e-1 * t2549
  t2680 = 0.77215461e-1 * t2555 * t404 * t574
  t2681 = t574 * t2530
  t2688 = 0.64753871e1 * t2538 * t416 - 0.64753871e1 * t2051 * t2547
  t2691 = t2057 * t2530
  t2730 = f.my_piecewise3(t577, -0.16e2 / 0.15e2 * (t147 * ((-0.463292766e0 * t2688 * t404 - 0.926585532e0 * t2062 * t2530) * t567 + t580 * t2555 - 0.297366688e1 * t2673 + 0.243867456e2 * t568 * t2555) * t589 / 0.16e2 - 0.7e1 / 0.32e2 * t586 * t2077 * t2555 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * t2551 * t2083 + 0.11250000000000000000000000000000000000000000000000e1 * t2086 * t2090 * t2555) * t279 * t603 + 0.32e2 / 0.15e2 * t601 * t2099 * t2530 - 0.56e2 / 0.15e2 * t601 * t2104 * t2555, -0.14235295576e0 * t2534 + 0.34138165292e0 * t2536)
  t2731 = t404 * t2730
  t2806 = -0.8e1 / 0.9e1 * t2671 - 0.4e1 / 0.9e1 * (-0.74341672e0 * t2673 - t2675 - t2676 + t2677 - t2680 - 0.154430922e0 * t2045 * t2681 - 0.77215461e-1 * t571 * t2688 + 0.4e1 * t2691 + 0.2e1 * t2731) * t613 + 0.4e1 / 0.3e1 * t2119 * t2555 + 0.8e1 / 0.27e2 * t616 * t46 * (-0.297366688e1 * t619 * t2555 - 0.926585532e0 * t2532 - 0.463292766e0 * t2540 + 0.463292766e0 * t2549 - 0.77215461e-1 * (0.12e2 * t2532 + 0.6e1 * t2540 - 0.6e1 * t2549) * t404 * t574 - 0.154430922e0 * t2144 * t2681 - 0.77215461e-1 * t627 * t2688 + 0.30e2 * t2691 + 0.15e2 * t2731) * t639 - 0.8e1 / 0.27e2 * t616 * t632 * t2158 * (0.16e2 * t2532 + 0.8e1 * t2540 - 0.8e1 * t2549) - 0.20e2 / 0.27e2 * t616 * t632 * t1507 * t2555 + 0.4e1 / 0.27e2 * t645 * t8 * (-t2675 - t2676 + t2677 - t2680 - 0.154430922e0 * t2179 * t2681 - 0.77215461e-1 * t647 * t2688 + 0.10e2 * t2691 + 0.5e1 * t2731) * t654 - 0.8e1 / 0.27e2 * t1535 * t2191 * t638 * t2555 - 0.10e2 / 0.27e2 * t1535 * t1515 * t1506 * t2555 + 0.8e1 / 0.81e2 * t662 * t352 * (0.2e1 * t2691 + t2731) * t665 - 0.8e1 / 0.27e2 * t662 * t664 * t2210 * t2555 - 0.20e2 / 0.81e2 * t662 * t664 * t1552 * t2555
  t2810 = f.my_piecewise3(t364, 0, -0.3e1 / 0.8e1 * t6 * t371 * t2806)
  vsigma_2_ = t7 * t2810
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
  smax = 8.572844

  wpbeh_A = 1.0161144

  wpbeh_B = -0.37170836

  wpbeh_C = -0.077215461

  wpbeh_D = 0.57786348

  wpbeh_E = -0.051955731

  EGscut = 0.08

  wcutoff = 14

  wpbeh_Ha1 = 0.00979681

  wpbeh_Ha2 = 0.0410834

  wpbeh_Ha3 = 0.18744

  wpbeh_Ha4 = 0.00120824

  wpbeh_Ha5 = 0.0347188

  wpbeh_Fc1 = 6.4753871

  wpbeh_Fc2 = 0.4796583

  wpbeh_EGa1 = -0.0262841788

  wpbeh_EGa2 = -0.07117647788

  wpbeh_EGa3 = 0.08534541323

  ea1 = -1.128223946706117

  ea2 = 1.452736265762971

  ea3 = -1.243162299390327

  ea4 = 0.971824836115601

  ea5 = -0.568861079687373

  ea6 = 0.246880514820192

  ea7 = -0.065032363850763

  ea8 = 0.008401793031216

  t1 = lambda w, s: 1 / 2 * (np1(w) * jnp.pi * xc_erfcx(jnp.sqrt(aux5(w, s))) - np2(w) * xc_E1_scaled(aux5(w, s)))

  t10 = lambda w, s: 1 / 2 * wpbeh_A * jnp.log(aux4(w, s) / aux6(w, s))

  term1_largew = lambda w, s: -1 / 2 * wpbeh_A * (-xc_E1_scaled(aux5(w, s)) + jnp.log(aux6(w, s)) - jnp.log(aux4(w, s)))

  f2 = lambda w, s: 1 / 2 * ea1 * jnp.sqrt(jnp.pi) * wpbeh_A / jnp.sqrt(aux6(w, s))

  f3 = lambda w, s: 1 / 2 * ea2 * wpbeh_A / aux6(w, s)

  f4 = lambda w, s: ea3 * jnp.sqrt(jnp.pi) * (-9 / (8 * jnp.sqrt(aux4(w, s))) + 0.25 * wpbeh_A / aux6(w, s) ** (3 / 2))

  f5 = lambda w, s: ea4 / 128 * (-144 / aux4(w, s) + 64 * wpbeh_A / aux6(w, s) ** 2)

  f6 = lambda w, s: ea5 * (3 * jnp.sqrt(jnp.pi) * (3 * aux6(w, s) ** (5 / 2) * (9 * aux4(w, s) - 2 * wpbeh_A) + 4 * aux4(w, s) ** (3 / 2) * wpbeh_A ** 2)) / (32 * aux6(w, s) ** (5 / 2) * aux4(w, s) ** (3 / 2) * wpbeh_A)

  f7 = lambda w, s: ea6 * (32 * wpbeh_A / aux6(w, s) ** 3 + (-36 + 81 * s ** 2 * wpbeh_H(s) / wpbeh_A) / aux4(w, s) ** 2) / 32

  f8 = lambda w, s: ea7 * (-3 * jnp.sqrt(jnp.pi) * (-40 * aux4(w, s) ** (5 / 2) * wpbeh_A ** 3 + 9 * aux6(w, s) ** (7 / 2) * (27 * aux4(w, s) ** 2 - 6 * aux4(w, s) * wpbeh_A + 4 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** (7 / 2) * aux4(w, s) ** (5 / 2) * wpbeh_A ** 2)

  f9 = lambda w, s: (+324 * ea6 * eb1(w) * aux6(w, s) ** 4 * aux4(w, s) * wpbeh_A + ea8 * (384 * aux4(w, s) ** 3 * wpbeh_A ** 3 + aux6(w, s) ** 4 * (-729 * aux4(w, s) ** 2 + 324 * aux4(w, s) * wpbeh_A - 288 * wpbeh_A ** 2))) / (128 * aux6(w, s) ** 4 * aux4(w, s) ** 3 * wpbeh_A ** 2)

  term2 = lambda s: (+aux1(s) ** 2 * wpbeh_B + aux1(s) * wpbeh_C + 2 * wpbeh_E + aux1(s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 2 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 3)

  term3 = lambda w, s: -w * (+4 * aux3(w, s) ** 2 * wpbeh_B + 6 * aux3(w, s) * wpbeh_C + 15 * wpbeh_E + 6 * aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 15 * s ** 2 * wpbeh_EG(s)) / (8 * aux1(s) * aux3(w, s) ** (5 / 2))

  term4 = lambda w, s: -w ** 3 * (+aux3(w, s) * wpbeh_C + 5 * wpbeh_E + aux3(w, s) * s ** 2 * wpbeh_C * wpbeh_F(s) + 5 * s ** 2 * wpbeh_EG(s)) / (2 * aux1(s) ** 2 * aux3(w, s) ** (5 / 2))

  term5 = lambda w, s: -w ** 5 * (+wpbeh_E + s ** 2 * wpbeh_EG(s)) / (aux1(s) ** 3 * aux3(w, s) ** (5 / 2))

  t2t9 = lambda w, s: +f2(w, s) * w + f3(w, s) * w ** 2 + f4(w, s) * w ** 3 + f5(w, s) * w ** 4 + f6(w, s) * w ** 5 + f7(w, s) * w ** 6 + f8(w, s) * w ** 7 + f9(w, s) * w ** 8

  term1 = lambda w, s: f.my_piecewise3(w > wcutoff, term1_largew(w, s), t1(jnp.minimum(w, wcutoff), s) + t2t9(jnp.minimum(w, wcutoff), s) + t10(jnp.minimum(w, wcutoff), s))

  f_wpbeh0 = lambda w, s: -8 / 9 * (term1(w, s) + term2(s) + term3(w, s) + term4(w, s) + term5(w, s))

  f_wpbeh = lambda rs, z, x: f_wpbeh0(f.nu(rs, z), jnp.maximum(1e-15, s_scaling_2(X2S * x)))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange_nsp(f, params, f_wpbeh, rs, z, xs0, xs1)

  t3 = r0 / 0.2e1 <= f.p.dens_threshold
  t4 = 3 ** (0.1e1 / 0.3e1)
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 / t5
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t12 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t13 = 0.1e1 + t12
  t14 = t13 <= f.p.zeta_threshold
  t15 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t17 = t13 ** (0.1e1 / 0.3e1)
  t19 = f.my_piecewise3(t14, t15 * f.p.zeta_threshold, t17 * t13)
  t20 = r0 ** (0.1e1 / 0.3e1)
  t21 = t19 * t20
  t22 = t4 ** 2
  t23 = f.p.cam_omega * t22
  t24 = jnp.pi ** 2
  t25 = t24 ** (0.1e1 / 0.3e1)
  t26 = 0.1e1 / t25
  t27 = f.my_piecewise3(t14, t15, t17)
  t29 = t26 / t27
  t30 = 0.1e1 / t20
  t33 = t23 * t29 * t30 / 0.3e1
  t34 = 0.14e2 < t33
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t37 = t36 * t26
  t38 = jnp.sqrt(s0)
  t39 = 2 ** (0.1e1 / 0.3e1)
  t40 = t38 * t39
  t42 = 0.1e1 / t20 / r0
  t45 = t37 * t40 * t42 / 0.12e2
  t46 = t45 < 0.1e1
  t47 = 0.15e2 < t45
  t48 = f.my_piecewise3(t47, 15, t45)
  t49 = 0.1e1 < t48
  t50 = f.my_piecewise3(t49, t48, 1)
  t52 = jnp.exp(t50 - 0.8572844e1)
  t53 = 0.1e1 + t52
  t54 = jnp.log(t53)
  t56 = f.my_piecewise3(t47, 0.8572844e1, t50 - t54)
  t57 = f.my_piecewise3(t46, t45, t56)
  t58 = t57 < 0.1e-14
  t59 = f.my_piecewise3(t58, 0.1e-14, t57)
  t60 = t59 ** 2
  t62 = t60 ** 2
  t64 = 0.979681e-2 * t60 + 0.410834e-1 * t62
  t65 = t60 * t64
  t67 = t62 * t59
  t71 = 0.1e1 + 0.187440e0 * t62 + 0.120824e-2 * t67 + 0.347188e-1 * t62 * t60
  t72 = 0.1e1 / t71
  t73 = t65 * t72
  t74 = 0.22143176004591608976312116037328080381500350747908e1 * t73
  t75 = t33 < 0.14e2
  t76 = f.my_piecewise3(t75, 0.1455915450052607e1, 2)
  t77 = f.p.cam_omega ** 2
  t79 = t76 * t77 * t4
  t80 = t25 ** 2
  t82 = t27 ** 2
  t84 = 0.1e1 / t80 / t82
  t85 = t20 ** 2
  t86 = 0.1e1 / t85
  t87 = t84 * t86
  t88 = t79 * t87
  t90 = t74 + 0.73810586681972029921040386791093601271667835826361e0 * t88
  t91 = xc_E1_scaled(t90)
  t93 = t88 / 0.3e1
  t94 = 0.57786348e0 + t73 + t93
  t95 = jnp.log(t94)
  t97 = t73 + t93
  t98 = jnp.log(t97)
  t101 = f.my_piecewise3(t34, 14, t33)
  t103 = t101 ** 2
  t104 = t103 * t101
  t106 = t103 ** 2
  t107 = t106 * t101
  t109 = t106 * t104
  t112 = (0.17059169152930056820161893079623736851681581580379e1 * t101 - 0.41622705406440396564494857937193021161156977252689e1 * t104 + 0.42174370348694649002798874148142601259725702952253e1 * t107 - 0.10676080470633097775878162022430088083825040527885e1 * t109) * jnp.pi
  t113 = t101 < 0.14e2
  t114 = f.my_piecewise3(t113, 0.1455915450052607e1, 2)
  t115 = t114 * t103
  t117 = t74 + 0.22143176004591608976312116037328080381500350747908e1 * t115
  t118 = jnp.sqrt(t117)
  t119 = xc_erfcx(t118)
  t124 = t106 * t103
  t126 = t106 ** 2
  t128 = -0.10161144e1 + 0.32686565979666847500000000000000000000000000000000e1 * t103 - 0.48418398881417585091796750444634974172199508244347e1 * t106 + 0.27236365685865660550566018235682267087532882778448e1 * t124 - 0.20524577845574895866582594065457716968048160011162e0 * t126
  t129 = xc_E1_scaled(t117)
  t132 = jnp.sqrt(jnp.pi)
  t133 = 0.57786348e0 + t73 + t115
  t134 = jnp.sqrt(t133)
  t136 = t132 / t134
  t139 = 0.1e1 / t133
  t142 = t73 + t115
  t143 = jnp.sqrt(t142)
  t146 = t134 * t133
  t147 = 0.1e1 / t146
  t150 = t132 * (-0.9e1 / 0.8e1 / t143 + 0.254028600e0 * t147)
  t153 = 0.1e1 / t142
  t155 = t133 ** 2
  t156 = 0.1e1 / t155
  t158 = -0.10933029406300511250000000000000000000000000000000e1 * t153 + 0.49374260512735112037720000000000000000000000000000e0 * t156
  t160 = t134 * t155
  t163 = 0.9e1 * t73 + 0.9e1 * t115 - 0.20322288e1
  t166 = t143 * t142
  t169 = t132 * (0.3e1 * t160 * t163 + 0.412995389554944e1 * t166)
  t170 = 0.1e1 / t160
  t171 = 0.1e1 / t166
  t173 = t170 * t171 * t107
  t176 = t155 * t133
  t177 = 0.1e1 / t176
  t180 = -0.36e2 + 0.79715433616529792314723617734381089373401262692468e2 * t73
  t181 = t142 ** 2
  t182 = 0.1e1 / t181
  t185 = 0.25085884618821050196480000000000000000000000000000e0 * t177 + 0.77150160881310000000000000000000000000000000000000e-2 * t180 * t182
  t187 = t143 * t181
  t189 = t134 * t176
  t193 = 0.27e2 * t181 - 0.60966864e1 * t73 - 0.60966864e1 * t115 + 0.412995389554944e1
  t197 = t132 * (-0.41965056246038818959360e2 * t187 + 0.9e1 * t189 * t193)
  t198 = 0.1e1 / t189
  t199 = 0.1e1 / t187
  t201 = t198 * t199 * t109
  t204 = t155 ** 2
  t205 = t114 * t204
  t208 = t181 * t142
  t213 = -0.729e3 * t181 + 0.3292210656e3 * t73 + 0.3292210656e3 * t115 - 0.29735668047955968e3
  t216 = 0.812782661649802026365952e2 * t205 * t142 + 0.3384784484376541657318712689107664896e1 * t208 + 0.8401793031216e-2 * t204 * t213
  t217 = 0.1e1 / t204
  t218 = t216 * t217
  t219 = 0.1e1 / t208
  t220 = t219 * t126
  t224 = jnp.log(t142 * t139)
  t226 = t112 * t119 / 0.2e1 - t128 * t129 / 0.2e1 - 0.57320229933645902589240000000000000000000000000000e0 * t136 * t101 + 0.73807311952199090994120000000000000000000000000000e0 * t139 * t103 - 0.1243162299390327e1 * t150 * t104 + t158 * t106 - 0.52484962540331303985063099194342684248938899005860e-1 * t169 * t173 + t185 * t124 + 0.14762353927435135388626424172726290810696148649614e-2 * t197 * t201 + 0.75666704254679261017345818778596682937131877722093e-2 * t218 * t220 + 0.50805720000000000000000000000000000000000000000000e0 * t224
  t227 = f.my_piecewise3(t34, 0.50805720000000000000000000000000000000000000000000e0 * t91 - 0.50805720000000000000000000000000000000000000000000e0 * t95 + 0.50805720000000000000000000000000000000000000000000e0 * t98, t226)
  t229 = 0.57786348e0 + t73
  t230 = t229 ** 2
  t232 = 0.77215461e-1 * t73
  t233 = t229 * t60
  t236 = 0.64753871e1 * t64 * t72 + 0.47965830e0
  t239 = 0.8e-1 < t59
  t243 = -0.463292766e0 - 0.463292766e0 * t236 * t60
  t246 = t230 * t229
  t249 = t132 * (-0.779335965e0 + t243 * t229 - 0.148683344e1 * t230 + 0.81289152e1 * t246)
  t250 = jnp.sqrt(t229)
  t251 = t250 * t246
  t252 = 0.1e1 / t251
  t255 = jnp.exp(t74)
  t257 = jnp.sqrt(t73)
  t259 = jax.lax.erf(0.14880583323442535320963147261125041853685458071038e1 * t257)
  t260 = 0.1e1 - t259
  t264 = 0.1e1 / t132
  t265 = (0.3e1 / 0.4e1 * jnp.pi + t249 * t252 / 0.16e2 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * t255 * t260) * t264
  t266 = 0.1e1 / t60
  t267 = t266 * t251
  t273 = f.my_piecewise3(t239, -0.16e2 / 0.15e2 * t265 * t267, -0.2628417880e-1 - 0.7117647788e-1 * t60 + 0.8534541323e-1 * t62)
  t274 = t60 * t273
  t276 = -0.37170836e0 * t230 - 0.14853145700326428e0 - t232 - 0.77215461e-1 * t233 * t236 + 0.2e1 * t274
  t277 = 0.1e1 / t246
  t280 = t23 * t29
  t281 = t77 * t4
  t282 = t281 * t87
  t284 = 0.57786348e0 + t73 + t282 / 0.3e1
  t285 = t284 ** 2
  t291 = 0.346718088e1 + 0.6e1 * t73 + 0.2e1 * t282
  t292 = t291 * t60
  t296 = -0.148683344e1 * t285 - 0.104705593501958568e1 - 0.463292766e0 * t73 - 0.154430922e0 * t282 - 0.77215461e-1 * t292 * t236 + 0.15e2 * t274
  t297 = t30 * t296
  t299 = 0.462290784e1 + 0.8e1 * t73
  t300 = 0.1e1 / t299
  t301 = jnp.sqrt(t284)
  t303 = 0.1e1 / t301 / t285
  t304 = t300 * t303
  t310 = t77 * f.p.cam_omega / t24
  t312 = 0.1e1 / t82 / t27
  t313 = t310 * t312
  t314 = 0.1e1 / r0
  t316 = t284 * t60
  t320 = -0.30439865000326428e0 - t232 - 0.25738487000000000000000000000000000000000000000000e-1 * t282 - 0.77215461e-1 * t316 * t236 + 0.5e1 * t274
  t322 = 0.1e1 / t230
  t323 = t322 * t303
  t327 = t77 ** 2
  t332 = t82 ** 2
  t336 = t327 * f.p.cam_omega * t4 / t80 / t24 / t332 / t27
  t338 = 0.1e1 / t85 / r0
  t339 = -0.51955731e-1 + t274
  t340 = t338 * t339
  t341 = t277 * t303
  t345 = -0.8e1 / 0.9e1 * t227 - 0.4e1 / 0.9e1 * t276 * t277 + 0.8e1 / 0.27e2 * t280 * t297 * t304 + 0.4e1 / 0.27e2 * t313 * t314 * t320 * t323 + 0.8e1 / 0.81e2 * t336 * t340 * t341
  t349 = f.my_piecewise3(t3, 0, -0.3e1 / 0.8e1 * t7 * t21 * t345)
  t355 = t91 - 0.1e1 / t90
  t356 = t59 * t64
  t357 = r0 ** 2
  t362 = t37 * t40 / t20 / t357 / 0.9e1
  t363 = f.my_piecewise3(t47, 0, -t362)
  t364 = f.my_piecewise3(t49, t363, 0)
  t366 = 0.1e1 / t53
  t369 = f.my_piecewise3(t47, 0, -t364 * t52 * t366 + t364)
  t370 = f.my_piecewise3(t46, -t362, t369)
  t371 = f.my_piecewise3(t58, 0, t370)
  t373 = t356 * t72 * t371
  t374 = 0.44286352009183217952624232074656160763000701495816e1 * t373
  t375 = t59 * t371
  t377 = t60 * t59
  t378 = t377 * t371
  t380 = 0.1959362e-1 * t375 + 0.1643336e0 * t378
  t382 = t60 * t380 * t72
  t383 = 0.22143176004591608976312116037328080381500350747908e1 * t382
  t384 = t71 ** 2
  t385 = 0.1e1 / t384
  t391 = 0.749760e0 * t378 + 0.604120e-2 * t62 * t371 + 0.2083128e0 * t67 * t371
  t393 = t65 * t385 * t391
  t394 = 0.22143176004591608976312116037328080381500350747908e1 * t393
  t395 = f.my_piecewise3(t75, 0, 0)
  t398 = t395 * t77 * t4 * t87
  t400 = t84 * t338
  t401 = t79 * t400
  t406 = 0.2e1 * t373
  t409 = t406 + t382 - t393 + t398 / 0.3e1 - 0.2e1 / 0.9e1 * t401
  t410 = 0.1e1 / t94
  t413 = 0.1e1 / t97
  t421 = f.my_piecewise3(t34, 0, -t23 * t29 * t42 / 0.9e1)
  t425 = t103 * t421
  t437 = t128 * (t129 - 0.1e1 / t117)
  t438 = f.my_piecewise3(t113, 0, 0)
  t439 = t438 * t103
  t442 = t114 * t101 * t421
  t444 = t374 + t383 - t394 + 0.22143176004591608976312116037328080381500350747908e1 * t439 + 0.44286352009183217952624232074656160763000701495816e1 * t442
  t449 = t156 * t103
  t451 = t406 + t382 - t393 + t439 + 0.2e1 * t442
  t455 = t142 * t156
  t477 = t197 / t134 / t204
  t478 = t199 * t109
  t482 = t197 * t198
  t485 = 0.1e1 / t143 / t208 * t109
  t493 = t169 * t198
  t494 = t171 * t107
  t498 = 0.4e1 * t158 * t104 * t421 + (0.17059169152930056820161893079623736851681581580379e1 * t421 - 0.12486811621932118969348457381157906348347093175807e2 * t425 + 0.21087185174347324501399437074071300629862851476126e2 * t106 * t421 - 0.74732563294431684431147134157010616586775283695195e1 * t124 * t421) * jnp.pi * t119 / 0.2e1 - t437 * t444 / 0.2e1 - 0.57320229933645902589240000000000000000000000000000e0 * t136 * t421 - 0.73807311952199090994120000000000000000000000000000e0 * t449 * t451 + 0.50805720000000000000000000000000000000000000000000e0 * (t451 * t139 - t455 * t451) * t153 * t133 + 0.6e1 * t185 * t107 * t421 + 0.14761462390439818198824000000000000000000000000000e1 * t139 * t101 * t421 - 0.1243162299390327e1 * t132 * (0.9e1 / 0.16e2 * t171 * t451 - 0.38104290000000000000000000000000000000000000000000e0 * t170 * t451) * t104 - 0.51668238746022973860192484604542017837436520273649e-2 * t477 * t478 * t451 - 0.36905884818587838471566060431815727026740371624035e-2 * t482 * t485 * t451 + 0.10333647749204594772038496920908403567487304054730e-1 * t482 * t199 * t124 * t421 + 0.13121240635082825996265774798585671062234724751465e0 * t493 * t494 * t451
  t499 = t169 * t170
  t500 = t199 * t107
  t516 = t180 * t219
  t542 = (0.2e1 * t118 * t119 - 0.2e1 * t264) / t118
  t546 = t146 * t163
  t565 = t160 * t193
  t568 = t142 * t451
  t584 = t216 / t204 / t133
  t588 = t181 ** 2
  t590 = 0.1e1 / t588 * t126
  t601 = t114 * t176
  t608 = t176 * t213
  t624 = t132 * t147
  t630 = 0.78727443810496955977594648791514026373408348508790e-1 * t499 * t500 * t451 - 0.26242481270165651992531549597171342124469449502930e0 * t499 * t171 * t106 * t421 + (-0.75257653856463150589440000000000000000000000000000e0 * t217 * t451 + 0.77150160881310000000000000000000000000000000000000e-2 * (0.15943086723305958462944723546876217874680252538494e3 * t373 + 0.79715433616529792314723617734381089373401262692468e2 * t382 - 0.79715433616529792314723617734381089373401262692468e2 * t393) * t182 - 0.15430032176262000000000000000000000000000000000000e-1 * t516 * t451) * t124 + (0.10933029406300511250000000000000000000000000000000e1 * t182 * t451 - 0.98748521025470224075440000000000000000000000000000e0 * t177 * t451) * t106 - (0.65373131959333695000000000000000000000000000000000e1 * t101 * t421 - 0.19367359552567034036718700177853989668879803297739e2 * t104 * t421 + 0.16341819411519396330339610941409360252519729667069e2 * t107 * t421 - 0.16419662276459916693266075252366173574438528008930e1 * t109 * t421) * t129 / 0.2e1 + t112 * t542 * t444 / 0.4e1 - 0.52484962540331303985063099194342684248938899005860e-1 * t132 * (0.15e2 / 0.2e1 * t546 * t451 + 0.3e1 * t160 * (0.18e2 * t373 + 0.9e1 * t382 - 0.9e1 * t393 + 0.9e1 * t439 + 0.18e2 * t442) + 0.61949308433241600000000000000000000000000000000000e1 * t143 * t451) * t173 + 0.14762353927435135388626424172726290810696148649614e-2 * t132 * (-0.10491264061509704739840000000000000000000000000000e3 * t166 * t451 + 0.63e2 / 0.2e1 * t565 * t451 + 0.9e1 * t189 * (0.54e2 * t568 - 0.121933728e2 * t373 - 0.60966864e1 * t382 + 0.60966864e1 * t393 - 0.60966864e1 * t439 - 0.121933728e2 * t442)) * t201 - 0.30266681701871704406938327511438673174852751088837e-1 * t584 * t220 * t451 - 0.22700011276403778305203745633579004881139563316628e-1 * t218 * t590 * t451 + 0.60533363403743408813876655022877346349705502177674e-1 * t218 * t219 * t109 * t421 + 0.75666704254679261017345818778596682937131877722093e-2 * (0.812782661649802026365952e2 * t438 * t204 * t142 + 0.3251130646599208105463808e3 * t601 * t568 + 0.812782661649802026365952e2 * t205 * t451 + 0.10154353453129624971956138067322994688e2 * t181 * t451 + 0.33607172124864e-1 * t608 * t451 + 0.8401793031216e-2 * t204 * (-0.1458e4 * t568 + 0.6584421312e3 * t373 + 0.3292210656e3 * t382 - 0.3292210656e3 * t393 + 0.3292210656e3 * t439 + 0.6584421312e3 * t442)) * t217 * t220 + 0.28660114966822951294620000000000000000000000000000e0 * t624 * t101 * t451 - 0.3729486898170981e1 * t150 * t425
  t632 = f.my_piecewise3(t34, 0.50805720000000000000000000000000000000000000000000e0 * t355 * (t374 + t383 - t394 + 0.73810586681972029921040386791093601271667835826361e0 * t398 - 0.49207057787981353280693591194062400847778557217574e0 * t401) - 0.50805720000000000000000000000000000000000000000000e0 * t409 * t410 + 0.50805720000000000000000000000000000000000000000000e0 * t409 * t413, t498 + t630)
  t634 = t406 + t382 - t393
  t635 = t229 * t634
  t637 = 0.154430922e0 * t373
  t638 = 0.77215461e-1 * t382
  t639 = 0.77215461e-1 * t393
  t643 = t229 * t59
  t644 = t236 * t371
  t649 = t64 * t385
  t652 = 0.64753871e1 * t380 * t72 - 0.64753871e1 * t649 * t391
  t655 = t59 * t273
  t656 = t655 * t371
  t660 = t236 * t59
  t673 = t230 ** 2
  t675 = 0.1e1 / t250 / t673
  t681 = t255 * t260
  t684 = t132 * t255
  t686 = jnp.exp(-0.22143176004591608976312116037328080381500350747909e1 * t73)
  t688 = t686 / t257
  t697 = 0.1e1 / t377 * t251
  t702 = t266 * t250 * t230
  t710 = f.my_piecewise3(t239, -0.16e2 / 0.15e2 * (t132 * ((-0.463292766e0 * t652 * t60 - 0.926585532e0 * t660 * t371) * t229 + t243 * t634 - 0.297366688e1 * t635 + 0.243867456e2 * t230 * t634) * t252 / 0.16e2 - 0.7e1 / 0.32e2 * t249 * t675 * t634 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * (t374 + t383 - t394) * t681 + 0.11250000000000000000000000000000000000000000000000e1 * t684 * t688 * t634) * t264 * t267 + 0.32e2 / 0.15e2 * t265 * t697 * t371 - 0.56e2 / 0.15e2 * t265 * t702 * t634, -0.14235295576e0 * t375 + 0.34138165292e0 * t378)
  t711 = t60 * t710
  t716 = 0.1e1 / t673
  t717 = t276 * t716
  t724 = t281 * t400
  t726 = t406 + t382 - t393 - 0.2e1 / 0.9e1 * t724
  t741 = t291 * t59
  t753 = t299 ** 2
  t755 = 0.1e1 / t753 * t303
  t766 = 0.1e1 / t301 / t285 / t284
  t767 = t300 * t766
  t781 = t284 * t59
  t794 = t310 * t312 * t314
  t795 = t320 * t277
  t800 = t320 * t322
  t817 = t716 * t303
  t822 = t277 * t766
  t827 = -0.8e1 / 0.9e1 * t632 - 0.4e1 / 0.9e1 * (-0.74341672e0 * t635 - t637 - t638 + t639 - 0.77215461e-1 * t634 * t60 * t236 - 0.154430922e0 * t643 * t644 - 0.77215461e-1 * t233 * t652 + 0.4e1 * t656 + 0.2e1 * t711) * t277 + 0.4e1 / 0.3e1 * t717 * t634 - 0.8e1 / 0.81e2 * t280 * t42 * t296 * t304 + 0.8e1 / 0.27e2 * t280 * t30 * (-0.297366688e1 * t284 * t726 - 0.926585532e0 * t373 - 0.463292766e0 * t382 + 0.463292766e0 * t393 + 0.10295394800000000000000000000000000000000000000000e0 * t724 - 0.77215461e-1 * (0.12e2 * t373 + 0.6e1 * t382 - 0.6e1 * t393 - 0.4e1 / 0.3e1 * t724) * t60 * t236 - 0.154430922e0 * t741 * t644 - 0.77215461e-1 * t292 * t652 + 0.30e2 * t656 + 0.15e2 * t711) * t304 - 0.8e1 / 0.27e2 * t280 * t297 * t755 * (0.16e2 * t373 + 0.8e1 * t382 - 0.8e1 * t393) - 0.20e2 / 0.27e2 * t280 * t297 * t767 * t726 - 0.4e1 / 0.27e2 * t313 / t357 * t320 * t323 + 0.4e1 / 0.27e2 * t313 * t314 * (-t637 - t638 + t639 + 0.17158991333333333333333333333333333333333333333333e-1 * t724 - 0.77215461e-1 * t726 * t60 * t236 - 0.154430922e0 * t781 * t644 - 0.77215461e-1 * t316 * t652 + 0.10e2 * t656 + 0.5e1 * t711) * t323 - 0.8e1 / 0.27e2 * t794 * t795 * t303 * t634 - 0.10e2 / 0.27e2 * t794 * t800 * t766 * t726 - 0.40e2 / 0.243e3 * t336 / t85 / t357 * t339 * t341 + 0.8e1 / 0.81e2 * t336 * t338 * (0.2e1 * t656 + t711) * t341 - 0.8e1 / 0.27e2 * t336 * t340 * t817 * t634 - 0.20e2 / 0.81e2 * t336 * t340 * t822 * t726
  t832 = f.my_piecewise3(t3, 0, -t7 * t19 * t86 * t345 / 0.8e1 - 0.3e1 / 0.8e1 * t7 * t21 * t827)
  vrho_0_ = 0.2e1 * r0 * t832 + 0.2e1 * t349
  t839 = t37 / t38 * t39 * t42 / 0.24e2
  t840 = f.my_piecewise3(t47, 0, t839)
  t841 = f.my_piecewise3(t49, t840, 0)
  t845 = f.my_piecewise3(t47, 0, -t841 * t52 * t366 + t841)
  t846 = f.my_piecewise3(t46, t839, t845)
  t847 = f.my_piecewise3(t58, 0, t846)
  t849 = t356 * t72 * t847
  t851 = t59 * t847
  t853 = t377 * t847
  t855 = 0.1959362e-1 * t851 + 0.1643336e0 * t853
  t857 = t60 * t855 * t72
  t864 = 0.749760e0 * t853 + 0.604120e-2 * t62 * t847 + 0.2083128e0 * t67 * t847
  t866 = t65 * t385 * t864
  t868 = 0.44286352009183217952624232074656160763000701495816e1 * t849 + 0.22143176004591608976312116037328080381500350747908e1 * t857 - 0.22143176004591608976312116037328080381500350747908e1 * t866
  t872 = 0.2e1 * t849 + t857 - t866
  t938 = t142 * t872
  t987 = t112 * t542 * t868 / 0.4e1 - t437 * t868 / 0.2e1 + 0.28660114966822951294620000000000000000000000000000e0 * t624 * t101 * t872 - 0.73807311952199090994120000000000000000000000000000e0 * t449 * t872 - 0.1243162299390327e1 * t132 * (0.9e1 / 0.16e2 * t171 * t872 - 0.38104290000000000000000000000000000000000000000000e0 * t170 * t872) * t104 + (0.10933029406300511250000000000000000000000000000000e1 * t182 * t872 - 0.98748521025470224075440000000000000000000000000000e0 * t177 * t872) * t106 - 0.52484962540331303985063099194342684248938899005860e-1 * t132 * (0.15e2 / 0.2e1 * t546 * t872 + 0.3e1 * t160 * (0.18e2 * t849 + 0.9e1 * t857 - 0.9e1 * t866) + 0.61949308433241600000000000000000000000000000000000e1 * t143 * t872) * t173 + 0.13121240635082825996265774798585671062234724751465e0 * t493 * t494 * t872 + 0.78727443810496955977594648791514026373408348508790e-1 * t499 * t500 * t872 + (-0.75257653856463150589440000000000000000000000000000e0 * t217 * t872 + 0.77150160881310000000000000000000000000000000000000e-2 * (0.15943086723305958462944723546876217874680252538494e3 * t849 + 0.79715433616529792314723617734381089373401262692468e2 * t857 - 0.79715433616529792314723617734381089373401262692468e2 * t866) * t182 - 0.15430032176262000000000000000000000000000000000000e-1 * t516 * t872) * t124 + 0.14762353927435135388626424172726290810696148649614e-2 * t132 * (-0.10491264061509704739840000000000000000000000000000e3 * t166 * t872 + 0.63e2 / 0.2e1 * t565 * t872 + 0.9e1 * t189 * (0.54e2 * t938 - 0.121933728e2 * t849 - 0.60966864e1 * t857 + 0.60966864e1 * t866)) * t201 - 0.51668238746022973860192484604542017837436520273649e-2 * t477 * t478 * t872 - 0.36905884818587838471566060431815727026740371624035e-2 * t482 * t485 * t872 + 0.75666704254679261017345818778596682937131877722093e-2 * (0.3251130646599208105463808e3 * t601 * t938 + 0.812782661649802026365952e2 * t205 * t872 + 0.10154353453129624971956138067322994688e2 * t181 * t872 + 0.33607172124864e-1 * t608 * t872 + 0.8401793031216e-2 * t204 * (-0.1458e4 * t938 + 0.6584421312e3 * t849 + 0.3292210656e3 * t857 - 0.3292210656e3 * t866)) * t217 * t220 - 0.30266681701871704406938327511438673174852751088837e-1 * t584 * t220 * t872 - 0.22700011276403778305203745633579004881139563316628e-1 * t218 * t590 * t872 + 0.50805720000000000000000000000000000000000000000000e0 * (t872 * t139 - t455 * t872) * t153 * t133
  t988 = f.my_piecewise3(t34, 0.50805720000000000000000000000000000000000000000000e0 * t355 * t868 - 0.50805720000000000000000000000000000000000000000000e0 * t872 * t410 + 0.50805720000000000000000000000000000000000000000000e0 * t872 * t413, t987)
  t990 = t229 * t872
  t992 = 0.154430922e0 * t849
  t993 = 0.77215461e-1 * t857
  t994 = 0.77215461e-1 * t866
  t997 = 0.77215461e-1 * t872 * t60 * t236
  t998 = t236 * t847
  t1005 = 0.64753871e1 * t855 * t72 - 0.64753871e1 * t649 * t864
  t1008 = t655 * t847
  t1047 = f.my_piecewise3(t239, -0.16e2 / 0.15e2 * (t132 * ((-0.463292766e0 * t1005 * t60 - 0.926585532e0 * t660 * t847) * t229 + t243 * t872 - 0.297366688e1 * t990 + 0.243867456e2 * t230 * t872) * t252 / 0.16e2 - 0.7e1 / 0.32e2 * t249 * t675 * t872 - 0.75601874976749088560696379006748576140662435082885e0 * jnp.pi * t868 * t681 + 0.11250000000000000000000000000000000000000000000000e1 * t684 * t688 * t872) * t264 * t267 + 0.32e2 / 0.15e2 * t265 * t697 * t847 - 0.56e2 / 0.15e2 * t265 * t702 * t872, -0.14235295576e0 * t851 + 0.34138165292e0 * t853)
  t1048 = t60 * t1047
  t1123 = -0.8e1 / 0.9e1 * t988 - 0.4e1 / 0.9e1 * (-0.74341672e0 * t990 - t992 - t993 + t994 - t997 - 0.154430922e0 * t643 * t998 - 0.77215461e-1 * t233 * t1005 + 0.4e1 * t1008 + 0.2e1 * t1048) * t277 + 0.4e1 / 0.3e1 * t717 * t872 + 0.8e1 / 0.27e2 * t280 * t30 * (-0.297366688e1 * t284 * t872 - 0.926585532e0 * t849 - 0.463292766e0 * t857 + 0.463292766e0 * t866 - 0.77215461e-1 * (0.12e2 * t849 + 0.6e1 * t857 - 0.6e1 * t866) * t60 * t236 - 0.154430922e0 * t741 * t998 - 0.77215461e-1 * t292 * t1005 + 0.30e2 * t1008 + 0.15e2 * t1048) * t304 - 0.8e1 / 0.27e2 * t280 * t297 * t755 * (0.16e2 * t849 + 0.8e1 * t857 - 0.8e1 * t866) - 0.20e2 / 0.27e2 * t280 * t297 * t767 * t872 + 0.4e1 / 0.27e2 * t313 * t314 * (-t992 - t993 + t994 - t997 - 0.154430922e0 * t781 * t998 - 0.77215461e-1 * t316 * t1005 + 0.10e2 * t1008 + 0.5e1 * t1048) * t323 - 0.8e1 / 0.27e2 * t794 * t795 * t303 * t872 - 0.10e2 / 0.27e2 * t794 * t800 * t766 * t872 + 0.8e1 / 0.81e2 * t336 * t338 * (0.2e1 * t1008 + t1048) * t341 - 0.8e1 / 0.27e2 * t336 * t340 * t817 * t872 - 0.20e2 / 0.81e2 * t336 * t340 * t822 * t872
  t1127 = f.my_piecewise3(t3, 0, -0.3e1 / 0.8e1 * t7 * t21 * t1123)
  vsigma_0_ = 0.2e1 * r0 * t1127
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_}
  return res
