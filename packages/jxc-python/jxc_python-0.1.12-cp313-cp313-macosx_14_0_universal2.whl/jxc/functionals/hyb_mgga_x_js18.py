"""Generated from hyb_mgga_x_js18.mpl."""

import jax
import jax.lax as lax
import jax.numpy as jnp
import jax.scipy.special as jsp_special
import scipy.special as sp_special
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
  tm_lambda = 0.6866

  tm_beta = 79.873

  tm_p = lambda x: (X2S * x) ** 2

  tm_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tm_tratio = lambda x, t: jnp.minimum(1.0, x ** 2 / (8 * t))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  attenuation_erf_f20 = lambda a: 1 + 24 * a ** 2 * ((20 * a ** 2 - 64 * a ** 4) * jnp.exp(-1 / (4 * a ** 2)) - 3 - 36 * a ** 2 + 64 * a ** 4 + 10 * a * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a)))

  attenuation_erf_f30 = lambda a: 1 + 8 / 7 * a * ((-8 * a + 256 * a ** 3 - 576 * a ** 5 + 3840 * a ** 7 - 122880 * a ** 9) * jnp.exp(-1 / (4 * a ** 2)) + 24 * a ** 3 * (-35 + 224 * a ** 2 - 1440 * a ** 4 + 5120 * a ** 6) + 2 * jnp.sqrt(jnp.pi) * (-2 + 60 * a ** 2) * jax.lax.erf(1 / (2 * a)))

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  js18_G = lambda x, t: (3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72) - (t - K_FACTOR_C) + 7 / 18 * (2 * tm_lambda - 1) ** 2 * x ** 2) / K_FACTOR_C

  tm_y = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_R = lambda x, t: 1 + 595 * (2 * tm_lambda - 1) ** 2 * tm_p(x) / 54 - (t - 3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72)) / K_FACTOR_C

  js18_H = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_qtilde = lambda x, t: 9 / 20 * (tm_alpha(x, t) - 1) + 2 * tm_p(x) / 3

  tm_w = lambda x, t: (tm_tratio(x, t) ** 2 + 3 * tm_tratio(x, t) ** 3) / (1 + tm_tratio(x, t) ** 3) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  attenuation_erf_f2 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.27, lambda _aval: -1 / 3511556992918352140755776405766144000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 46 + 1 / 33929038000650146833571361325056000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 44 - 1 / 341095116070365837848137621831680000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 42 + 1 / 3573852336994573837102806466560000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 40 - 1 / 39097165634742908368485089280000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 38 + 1 / 447473103488807905221672960000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 36 - 1 / 5369745537516410492682240000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 34 + 1 / 67726520292999771979776000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 32 - 1 / 900231674141645733888000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 30 + 1 / 12648942844388573184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 28 - 1 / 188514051721003008000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 26 + 1 / 2991700272218112000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 24 - 1 / 50785035485184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 22 + 1 / 927028425523200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 20 - 1 / 18311911833600 * (1.0 / jnp.maximum(_aval, 0.27)) ** 18 + 1 / 394474291200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 16 - 1 / 9358540800 * (1.0 / jnp.maximum(_aval, 0.27)) ** 14 + 1 / 247726080 * (1.0 / jnp.maximum(_aval, 0.27)) ** 12 - 1 / 7454720 * (1.0 / jnp.maximum(_aval, 0.27)) ** 10 + 3 / 788480 * (1.0 / jnp.maximum(_aval, 0.27)) ** 8 - 1 / 11520 * (1.0 / jnp.maximum(_aval, 0.27)) ** 6 + 3 / 2240 * (1.0 / jnp.maximum(_aval, 0.27)) ** 4, lambda _aval: attenuation_erf_f20(jnp.minimum(_aval, 0.27)))

  attenuation_erf_f3 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.32, lambda _aval: -1 / 2104209454461863328391867505049600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 38 + 1 / 22046293272414372635684634624000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 36 - 1 / 241191070393445437962977280000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 34 + 1 / 2760851680179343645999104000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 32 - 1 / 33139778504339333578752000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 30 + 1 / 418174050435486229463040 * (1.0 / jnp.maximum(_aval, 0.32)) ** 28 - 1 / 5562511054710453043200 * (1.0 / jnp.maximum(_aval, 0.32)) ** 26 + 1 / 78244468658012160000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 24 - 1 / 1168055816159232000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 22 + 1 / 18582706166169600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 20 - 1 / 316612955602944 * (1.0 / jnp.maximum(_aval, 0.32)) ** 18 + 1 / 5811921223680 * (1.0 / jnp.maximum(_aval, 0.32)) ** 16 - 1 / 115811942400 * (1.0 / jnp.maximum(_aval, 0.32)) ** 14 + 1 / 2530344960 * (1.0 / jnp.maximum(_aval, 0.32)) ** 12 - 1 / 61501440 * (1.0 / jnp.maximum(_aval, 0.32)) ** 10 + 5 / 8515584 * (1.0 / jnp.maximum(_aval, 0.32)) ** 8 - 1 / 56448 * (1.0 / jnp.maximum(_aval, 0.32)) ** 6 + 3 / 7840 * (1.0 / jnp.maximum(_aval, 0.32)) ** 4, lambda _aval: attenuation_erf_f30(jnp.minimum(_aval, 0.32)))

  tm_f0 = lambda x: (1 + 10 * (70 * tm_y(x) / 27) + tm_beta * tm_y(x) ** 2) ** (1 / 10)

  tm_fx_SC = lambda x, t: (1 + 10 * (+(MU_GE + 50 * tm_p(x) / 729) * tm_p(x) + 146 * tm_qtilde(x, t) ** 2 / 2025 - 73 * tm_qtilde(x, t) / 405 * (3 / 5 * tm_tratio(x, t)) * (1 - tm_tratio(x, t)))) ** (1 / 10)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  tm_fx_DME = lambda x, t: 1 / tm_f0(x) ** 2 + 7 * tm_R(x, t) / (9 * tm_f0(x) ** 4)

  js18_A = lambda rs, z, x: jnp.maximum(1e-10, a_cnst * rs / (tm_f0(x) * f.opz_pow_n(z, 1 / 3)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  tm_f = lambda x, u, t: tm_w(x, t) * tm_fx_DME(x, t) + (1 - tm_w(x, t)) * tm_fx_SC(x, t)

  js18_DME_SR = lambda rs, z, x, t: +attenuation_erf(js18_A(rs, z, x)) / tm_f0(x) ** 2 + attenuation_erf_f2(js18_A(rs, z, x)) * 7 * js18_G(x, t) / (9 * tm_f0(x) ** 4) + attenuation_erf_f3(js18_A(rs, z, x)) * 245 * js18_H(x) / (54 * tm_f0(x) ** 4)

  js18_f_SR = lambda rs, z, x, t: tm_w(x, t) * js18_DME_SR(rs, z, x, t) + (1 - tm_w(x, t)) * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3)) * tm_fx_SC(x, t)

  js18_f = lambda rs, z, x, u, t: -f.p.cam_beta * js18_f_SR(rs, z, x, t) + tm_f(x, u, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, js18_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  tm_lambda = 0.6866

  tm_beta = 79.873

  tm_p = lambda x: (X2S * x) ** 2

  tm_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tm_tratio = lambda x, t: jnp.minimum(1.0, x ** 2 / (8 * t))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  attenuation_erf_f20 = lambda a: 1 + 24 * a ** 2 * ((20 * a ** 2 - 64 * a ** 4) * jnp.exp(-1 / (4 * a ** 2)) - 3 - 36 * a ** 2 + 64 * a ** 4 + 10 * a * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a)))

  attenuation_erf_f30 = lambda a: 1 + 8 / 7 * a * ((-8 * a + 256 * a ** 3 - 576 * a ** 5 + 3840 * a ** 7 - 122880 * a ** 9) * jnp.exp(-1 / (4 * a ** 2)) + 24 * a ** 3 * (-35 + 224 * a ** 2 - 1440 * a ** 4 + 5120 * a ** 6) + 2 * jnp.sqrt(jnp.pi) * (-2 + 60 * a ** 2) * jax.lax.erf(1 / (2 * a)))

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  js18_G = lambda x, t: (3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72) - (t - K_FACTOR_C) + 7 / 18 * (2 * tm_lambda - 1) ** 2 * x ** 2) / K_FACTOR_C

  tm_y = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_R = lambda x, t: 1 + 595 * (2 * tm_lambda - 1) ** 2 * tm_p(x) / 54 - (t - 3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72)) / K_FACTOR_C

  js18_H = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_qtilde = lambda x, t: 9 / 20 * (tm_alpha(x, t) - 1) + 2 * tm_p(x) / 3

  tm_w = lambda x, t: (tm_tratio(x, t) ** 2 + 3 * tm_tratio(x, t) ** 3) / (1 + tm_tratio(x, t) ** 3) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  attenuation_erf_f2 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.27, lambda _aval: -1 / 3511556992918352140755776405766144000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 46 + 1 / 33929038000650146833571361325056000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 44 - 1 / 341095116070365837848137621831680000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 42 + 1 / 3573852336994573837102806466560000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 40 - 1 / 39097165634742908368485089280000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 38 + 1 / 447473103488807905221672960000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 36 - 1 / 5369745537516410492682240000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 34 + 1 / 67726520292999771979776000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 32 - 1 / 900231674141645733888000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 30 + 1 / 12648942844388573184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 28 - 1 / 188514051721003008000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 26 + 1 / 2991700272218112000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 24 - 1 / 50785035485184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 22 + 1 / 927028425523200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 20 - 1 / 18311911833600 * (1.0 / jnp.maximum(_aval, 0.27)) ** 18 + 1 / 394474291200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 16 - 1 / 9358540800 * (1.0 / jnp.maximum(_aval, 0.27)) ** 14 + 1 / 247726080 * (1.0 / jnp.maximum(_aval, 0.27)) ** 12 - 1 / 7454720 * (1.0 / jnp.maximum(_aval, 0.27)) ** 10 + 3 / 788480 * (1.0 / jnp.maximum(_aval, 0.27)) ** 8 - 1 / 11520 * (1.0 / jnp.maximum(_aval, 0.27)) ** 6 + 3 / 2240 * (1.0 / jnp.maximum(_aval, 0.27)) ** 4, lambda _aval: attenuation_erf_f20(jnp.minimum(_aval, 0.27)))

  attenuation_erf_f3 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.32, lambda _aval: -1 / 2104209454461863328391867505049600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 38 + 1 / 22046293272414372635684634624000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 36 - 1 / 241191070393445437962977280000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 34 + 1 / 2760851680179343645999104000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 32 - 1 / 33139778504339333578752000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 30 + 1 / 418174050435486229463040 * (1.0 / jnp.maximum(_aval, 0.32)) ** 28 - 1 / 5562511054710453043200 * (1.0 / jnp.maximum(_aval, 0.32)) ** 26 + 1 / 78244468658012160000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 24 - 1 / 1168055816159232000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 22 + 1 / 18582706166169600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 20 - 1 / 316612955602944 * (1.0 / jnp.maximum(_aval, 0.32)) ** 18 + 1 / 5811921223680 * (1.0 / jnp.maximum(_aval, 0.32)) ** 16 - 1 / 115811942400 * (1.0 / jnp.maximum(_aval, 0.32)) ** 14 + 1 / 2530344960 * (1.0 / jnp.maximum(_aval, 0.32)) ** 12 - 1 / 61501440 * (1.0 / jnp.maximum(_aval, 0.32)) ** 10 + 5 / 8515584 * (1.0 / jnp.maximum(_aval, 0.32)) ** 8 - 1 / 56448 * (1.0 / jnp.maximum(_aval, 0.32)) ** 6 + 3 / 7840 * (1.0 / jnp.maximum(_aval, 0.32)) ** 4, lambda _aval: attenuation_erf_f30(jnp.minimum(_aval, 0.32)))

  tm_f0 = lambda x: (1 + 10 * (70 * tm_y(x) / 27) + tm_beta * tm_y(x) ** 2) ** (1 / 10)

  tm_fx_SC = lambda x, t: (1 + 10 * (+(MU_GE + 50 * tm_p(x) / 729) * tm_p(x) + 146 * tm_qtilde(x, t) ** 2 / 2025 - 73 * tm_qtilde(x, t) / 405 * (3 / 5 * tm_tratio(x, t)) * (1 - tm_tratio(x, t)))) ** (1 / 10)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  tm_fx_DME = lambda x, t: 1 / tm_f0(x) ** 2 + 7 * tm_R(x, t) / (9 * tm_f0(x) ** 4)

  js18_A = lambda rs, z, x: jnp.maximum(1e-10, a_cnst * rs / (tm_f0(x) * f.opz_pow_n(z, 1 / 3)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  tm_f = lambda x, u, t: tm_w(x, t) * tm_fx_DME(x, t) + (1 - tm_w(x, t)) * tm_fx_SC(x, t)

  js18_DME_SR = lambda rs, z, x, t: +attenuation_erf(js18_A(rs, z, x)) / tm_f0(x) ** 2 + attenuation_erf_f2(js18_A(rs, z, x)) * 7 * js18_G(x, t) / (9 * tm_f0(x) ** 4) + attenuation_erf_f3(js18_A(rs, z, x)) * 245 * js18_H(x) / (54 * tm_f0(x) ** 4)

  js18_f_SR = lambda rs, z, x, t: tm_w(x, t) * js18_DME_SR(rs, z, x, t) + (1 - tm_w(x, t)) * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3)) * tm_fx_SC(x, t)

  js18_f = lambda rs, z, x, u, t: -f.p.cam_beta * js18_f_SR(rs, z, x, t) + tm_f(x, u, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, js18_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  tm_lambda = 0.6866

  tm_beta = 79.873

  tm_p = lambda x: (X2S * x) ** 2

  tm_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tm_tratio = lambda x, t: jnp.minimum(1.0, x ** 2 / (8 * t))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  attenuation_erf_f20 = lambda a: 1 + 24 * a ** 2 * ((20 * a ** 2 - 64 * a ** 4) * jnp.exp(-1 / (4 * a ** 2)) - 3 - 36 * a ** 2 + 64 * a ** 4 + 10 * a * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a)))

  attenuation_erf_f30 = lambda a: 1 + 8 / 7 * a * ((-8 * a + 256 * a ** 3 - 576 * a ** 5 + 3840 * a ** 7 - 122880 * a ** 9) * jnp.exp(-1 / (4 * a ** 2)) + 24 * a ** 3 * (-35 + 224 * a ** 2 - 1440 * a ** 4 + 5120 * a ** 6) + 2 * jnp.sqrt(jnp.pi) * (-2 + 60 * a ** 2) * jax.lax.erf(1 / (2 * a)))

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  js18_G = lambda x, t: (3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72) - (t - K_FACTOR_C) + 7 / 18 * (2 * tm_lambda - 1) ** 2 * x ** 2) / K_FACTOR_C

  tm_y = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_R = lambda x, t: 1 + 595 * (2 * tm_lambda - 1) ** 2 * tm_p(x) / 54 - (t - 3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72)) / K_FACTOR_C

  js18_H = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_qtilde = lambda x, t: 9 / 20 * (tm_alpha(x, t) - 1) + 2 * tm_p(x) / 3

  tm_w = lambda x, t: (tm_tratio(x, t) ** 2 + 3 * tm_tratio(x, t) ** 3) / (1 + tm_tratio(x, t) ** 3) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  attenuation_erf_f2 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.27, lambda _aval: -1 / 3511556992918352140755776405766144000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 46 + 1 / 33929038000650146833571361325056000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 44 - 1 / 341095116070365837848137621831680000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 42 + 1 / 3573852336994573837102806466560000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 40 - 1 / 39097165634742908368485089280000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 38 + 1 / 447473103488807905221672960000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 36 - 1 / 5369745537516410492682240000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 34 + 1 / 67726520292999771979776000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 32 - 1 / 900231674141645733888000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 30 + 1 / 12648942844388573184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 28 - 1 / 188514051721003008000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 26 + 1 / 2991700272218112000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 24 - 1 / 50785035485184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 22 + 1 / 927028425523200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 20 - 1 / 18311911833600 * (1.0 / jnp.maximum(_aval, 0.27)) ** 18 + 1 / 394474291200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 16 - 1 / 9358540800 * (1.0 / jnp.maximum(_aval, 0.27)) ** 14 + 1 / 247726080 * (1.0 / jnp.maximum(_aval, 0.27)) ** 12 - 1 / 7454720 * (1.0 / jnp.maximum(_aval, 0.27)) ** 10 + 3 / 788480 * (1.0 / jnp.maximum(_aval, 0.27)) ** 8 - 1 / 11520 * (1.0 / jnp.maximum(_aval, 0.27)) ** 6 + 3 / 2240 * (1.0 / jnp.maximum(_aval, 0.27)) ** 4, lambda _aval: attenuation_erf_f20(jnp.minimum(_aval, 0.27)))

  attenuation_erf_f3 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.32, lambda _aval: -1 / 2104209454461863328391867505049600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 38 + 1 / 22046293272414372635684634624000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 36 - 1 / 241191070393445437962977280000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 34 + 1 / 2760851680179343645999104000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 32 - 1 / 33139778504339333578752000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 30 + 1 / 418174050435486229463040 * (1.0 / jnp.maximum(_aval, 0.32)) ** 28 - 1 / 5562511054710453043200 * (1.0 / jnp.maximum(_aval, 0.32)) ** 26 + 1 / 78244468658012160000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 24 - 1 / 1168055816159232000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 22 + 1 / 18582706166169600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 20 - 1 / 316612955602944 * (1.0 / jnp.maximum(_aval, 0.32)) ** 18 + 1 / 5811921223680 * (1.0 / jnp.maximum(_aval, 0.32)) ** 16 - 1 / 115811942400 * (1.0 / jnp.maximum(_aval, 0.32)) ** 14 + 1 / 2530344960 * (1.0 / jnp.maximum(_aval, 0.32)) ** 12 - 1 / 61501440 * (1.0 / jnp.maximum(_aval, 0.32)) ** 10 + 5 / 8515584 * (1.0 / jnp.maximum(_aval, 0.32)) ** 8 - 1 / 56448 * (1.0 / jnp.maximum(_aval, 0.32)) ** 6 + 3 / 7840 * (1.0 / jnp.maximum(_aval, 0.32)) ** 4, lambda _aval: attenuation_erf_f30(jnp.minimum(_aval, 0.32)))

  tm_f0 = lambda x: (1 + 10 * (70 * tm_y(x) / 27) + tm_beta * tm_y(x) ** 2) ** (1 / 10)

  tm_fx_SC = lambda x, t: (1 + 10 * (+(MU_GE + 50 * tm_p(x) / 729) * tm_p(x) + 146 * tm_qtilde(x, t) ** 2 / 2025 - 73 * tm_qtilde(x, t) / 405 * (3 / 5 * tm_tratio(x, t)) * (1 - tm_tratio(x, t)))) ** (1 / 10)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  tm_fx_DME = lambda x, t: 1 / tm_f0(x) ** 2 + 7 * tm_R(x, t) / (9 * tm_f0(x) ** 4)

  js18_A = lambda rs, z, x: jnp.maximum(1e-10, a_cnst * rs / (tm_f0(x) * f.opz_pow_n(z, 1 / 3)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  tm_f = lambda x, u, t: tm_w(x, t) * tm_fx_DME(x, t) + (1 - tm_w(x, t)) * tm_fx_SC(x, t)

  js18_DME_SR = lambda rs, z, x, t: +attenuation_erf(js18_A(rs, z, x)) / tm_f0(x) ** 2 + attenuation_erf_f2(js18_A(rs, z, x)) * 7 * js18_G(x, t) / (9 * tm_f0(x) ** 4) + attenuation_erf_f3(js18_A(rs, z, x)) * 245 * js18_H(x) / (54 * tm_f0(x) ** 4)

  js18_f_SR = lambda rs, z, x, t: tm_w(x, t) * js18_DME_SR(rs, z, x, t) + (1 - tm_w(x, t)) * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3)) * tm_fx_SC(x, t)

  js18_f = lambda rs, z, x, u, t: -f.p.cam_beta * js18_f_SR(rs, z, x, t) + tm_f(x, u, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, js18_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t28 = 0.1e1 / r0
  t29 = s0 * t28
  t30 = 0.1e1 / tau0
  t32 = t29 * t30 / 0.8e1
  t33 = t32 < 0.10e1
  t34 = f.my_piecewise3(t33, t32, 0.10e1)
  t35 = t34 ** 2
  t36 = t35 * t34
  t38 = t35 + 0.3e1 * t36
  t39 = 0.1e1 + t36
  t40 = t39 ** 2
  t41 = 0.1e1 / t40
  t42 = t38 * t41
  t43 = 9 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t46 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = t44 * t47
  t49 = t48 * f.p.cam_omega
  t50 = 0.1e1 / t26
  t51 = t2 * t50
  t52 = 6 ** (0.1e1 / 0.3e1)
  t53 = jnp.pi ** 2
  t54 = t53 ** (0.1e1 / 0.3e1)
  t55 = t54 ** 2
  t56 = 0.1e1 / t55
  t57 = t52 * t56
  t58 = r0 ** 2
  t59 = r0 ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t62 = 0.1e1 / t60 / t58
  t63 = s0 * t62
  t64 = t57 * t63
  t66 = t52 ** 2
  t69 = t66 / t54 / t53
  t70 = s0 ** 2
  t71 = t58 ** 2
  t74 = 0.1e1 / t59 / t71 / r0
  t78 = 0.1e1 + 0.15045488888888888888888888888888888888888888888889e0 * t64 + 0.26899490462262948000000000000000000000000000000000e-2 * t69 * t70 * t74
  t79 = t78 ** (0.1e1 / 0.10e2)
  t80 = 0.1e1 / t79
  t82 = 0.1e1 + t17 <= f.p.zeta_threshold
  t84 = 0.1e1 - t17 <= f.p.zeta_threshold
  t85 = f.my_piecewise5(t82, t11, t84, t15, t17)
  t86 = 0.1e1 + t85
  t87 = t86 <= f.p.zeta_threshold
  t88 = t86 ** (0.1e1 / 0.3e1)
  t89 = f.my_piecewise3(t87, t21, t88)
  t90 = 0.1e1 / t89
  t91 = t80 * t90
  t94 = t49 * t51 * t91 / 0.18e2
  t95 = t94 < 0.1e-9
  t96 = f.my_piecewise3(t95, 0.1e-9, t94)
  t97 = 0.135e1 <= t96
  t98 = 0.135e1 < t96
  t99 = f.my_piecewise3(t98, t96, 0.135e1)
  t100 = t99 ** 2
  t103 = t100 ** 2
  t106 = t103 * t100
  t109 = t103 ** 2
  t121 = t109 ** 2
  t125 = f.my_piecewise3(t98, 0.135e1, t96)
  t126 = jnp.sqrt(jnp.pi)
  t127 = 0.1e1 / t125
  t129 = jax.lax.erf(t127 / 0.2e1)
  t131 = t125 ** 2
  t132 = 0.1e1 / t131
  t134 = jnp.exp(-t132 / 0.4e1)
  t135 = t134 - 0.1e1
  t138 = t134 - 0.3e1 / 0.2e1 - 0.2e1 * t131 * t135
  t141 = 0.2e1 * t125 * t138 + t126 * t129
  t145 = f.my_piecewise3(t97, 0.1e1 / t100 / 0.36e2 - 0.1e1 / t103 / 0.960e3 + 0.1e1 / t106 / 0.26880e5 - 0.1e1 / t109 / 0.829440e6 + 0.1e1 / t109 / t100 / 0.28385280e8 - 0.1e1 / t109 / t103 / 0.1073479680e10 + 0.1e1 / t109 / t106 / 0.44590694400e11 - 0.1e1 / t121 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t125 * t141)
  t146 = t78 ** (0.1e1 / 0.5e1)
  t147 = 0.1e1 / t146
  t149 = 0.27e0 <= t96
  t150 = 0.27e0 < t96
  t151 = f.my_piecewise3(t150, t96, 0.27e0)
  t152 = t151 ** 2
  t153 = t152 ** 2
  t154 = t153 ** 2
  t155 = t154 * t153
  t156 = t154 ** 2
  t157 = t156 ** 2
  t161 = t153 * t152
  t162 = t154 * t161
  t172 = t154 * t152
  t187 = 0.1e1 / t157 / t155 / 0.33929038000650146833571361325056000000e38 - 0.1e1 / t157 / t162 / 0.3511556992918352140755776405766144000000e40 + 0.3e1 / 0.2240e4 / t153 - 0.1e1 / t161 / 0.11520e5 + 0.3e1 / 0.788480e6 / t154 - 0.1e1 / t172 / 0.7454720e7 + 0.1e1 / t155 / 0.247726080e9 - 0.1e1 / t162 / 0.9358540800e10 + 0.1e1 / t156 / 0.394474291200e12 - 0.1e1 / t156 / t152 / 0.18311911833600e14 + 0.1e1 / t156 / t153 / 0.927028425523200e15
  t220 = -0.1e1 / t156 / t161 / 0.50785035485184000e17 + 0.1e1 / t156 / t154 / 0.2991700272218112000e19 - 0.1e1 / t156 / t172 / 0.188514051721003008000e21 + 0.1e1 / t156 / t155 / 0.12648942844388573184000e23 - 0.1e1 / t156 / t162 / 0.900231674141645733888000e24 + 0.1e1 / t157 / 0.67726520292999771979776000e26 - 0.1e1 / t157 / t152 / 0.5369745537516410492682240000e28 + 0.1e1 / t157 / t153 / 0.447473103488807905221672960000e30 - 0.1e1 / t157 / t161 / 0.39097165634742908368485089280000e32 + 0.1e1 / t157 / t154 / 0.3573852336994573837102806466560000e34 - 0.1e1 / t157 / t172 / 0.341095116070365837848137621831680000e36
  t222 = f.my_piecewise3(t150, 0.27e0, t96)
  t223 = t222 ** 2
  t225 = t223 ** 2
  t226 = 0.64e2 * t225
  t227 = 0.20e2 * t223 - t226
  t230 = jnp.exp(-0.1e1 / t223 / 0.4e1)
  t234 = 0.1e1 / t222
  t236 = jax.lax.erf(t234 / 0.2e1)
  t239 = 0.10e2 * t222 * t126 * t236 + t227 * t230 - 0.36e2 * t223 + t226 - 0.3e1
  t243 = f.my_piecewise3(t149, t187 + t220, 0.24e2 * t223 * t239 + 0.1e1)
  t245 = 0.1e1 / t60 / r0
  t246 = tau0 * t245
  t247 = 0.14554132000000000000000000000000000000000000000000e0 * t246
  t248 = t66 * t55
  t249 = 0.4366239600000000000000000000000000000000000000000e-1 * t248
  t251 = -t247 + t249 + 0.42296278333333333333333333333333333333333333333333e-1 * t63
  t252 = t243 * t251
  t253 = t146 ** 2
  t254 = 0.1e1 / t253
  t255 = t57 * t254
  t258 = 0.32e0 <= t96
  t259 = 0.32e0 < t96
  t260 = f.my_piecewise3(t259, t96, 0.32e0)
  t261 = t260 ** 2
  t262 = t261 ** 2
  t265 = t262 * t261
  t268 = t262 ** 2
  t271 = t268 * t261
  t274 = t268 * t262
  t277 = t268 * t265
  t280 = t268 ** 2
  t304 = t280 ** 2
  t316 = 0.3e1 / 0.7840e4 / t262 - 0.1e1 / t265 / 0.56448e5 + 0.5e1 / 0.8515584e7 / t268 - 0.1e1 / t271 / 0.61501440e8 + 0.1e1 / t274 / 0.2530344960e10 - 0.1e1 / t277 / 0.115811942400e12 + 0.1e1 / t280 / 0.5811921223680e13 - 0.1e1 / t280 / t261 / 0.316612955602944e15 + 0.1e1 / t280 / t262 / 0.18582706166169600e17 - 0.1e1 / t280 / t265 / 0.1168055816159232000e19 + 0.1e1 / t280 / t268 / 0.78244468658012160000e20 - 0.1e1 / t280 / t271 / 0.5562511054710453043200e22 + 0.1e1 / t280 / t274 / 0.418174050435486229463040e24 - 0.1e1 / t280 / t277 / 0.33139778504339333578752000e26 + 0.1e1 / t304 / 0.2760851680179343645999104000e28 - 0.1e1 / t304 / t261 / 0.241191070393445437962977280000e30 + 0.1e1 / t304 / t262 / 0.22046293272414372635684634624000e32 - 0.1e1 / t304 / t265 / 0.2104209454461863328391867505049600e34
  t317 = f.my_piecewise3(t259, 0.32e0, t96)
  t319 = t317 ** 2
  t320 = t319 * t317
  t322 = t319 ** 2
  t323 = t322 * t317
  t327 = t322 ** 2
  t330 = -0.122880e6 * t327 * t317 + 0.3840e4 * t322 * t320 - 0.8e1 * t317 + 0.256e3 * t320 - 0.576e3 * t323
  t331 = 0.1e1 / t319
  t333 = jnp.exp(-t331 / 0.4e1)
  t337 = t322 * t319
  t339 = -0.35e2 + 0.224e3 * t319 - 0.1440e4 * t322 + 0.5120e4 * t337
  t343 = -0.2e1 + 0.60e2 * t319
  t347 = jax.lax.erf(0.1e1 / t317 / 0.2e1)
  t350 = 0.2e1 * t126 * t343 * t347 + 0.24e2 * t320 * t339 + t330 * t333
  t354 = f.my_piecewise3(t258, t316, 0.1e1 + 0.8e1 / 0.7e1 * t317 * t350)
  t355 = t354 * t52
  t356 = t355 * t56
  t357 = t63 * t254
  t360 = t145 * t147 + 0.35e2 / 0.81e2 * t252 * t255 + 0.26329605555555555555555555555555555555555555555556e-1 * t356 * t357
  t362 = 0.1e1 - t42
  t365 = t49 * t51 * t90 / 0.18e2
  t366 = 0.135e1 <= t365
  t367 = 0.135e1 < t365
  t368 = f.my_piecewise3(t367, t365, 0.135e1)
  t369 = t368 ** 2
  t372 = t369 ** 2
  t375 = t372 * t369
  t378 = t372 ** 2
  t390 = t378 ** 2
  t394 = f.my_piecewise3(t367, 0.135e1, t365)
  t395 = 0.1e1 / t394
  t397 = jax.lax.erf(t395 / 0.2e1)
  t399 = t394 ** 2
  t400 = 0.1e1 / t399
  t402 = jnp.exp(-t400 / 0.4e1)
  t403 = t402 - 0.1e1
  t406 = t402 - 0.3e1 / 0.2e1 - 0.2e1 * t399 * t403
  t409 = t126 * t397 + 0.2e1 * t394 * t406
  t413 = f.my_piecewise3(t366, 0.1e1 / t369 / 0.36e2 - 0.1e1 / t372 / 0.960e3 + 0.1e1 / t375 / 0.26880e5 - 0.1e1 / t378 / 0.829440e6 + 0.1e1 / t378 / t369 / 0.28385280e8 - 0.1e1 / t378 / t372 / 0.1073479680e10 + 0.1e1 / t378 / t375 / 0.44590694400e11 - 0.1e1 / t390 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t394 * t409)
  t414 = t362 * t413
  t417 = (0.10e2 / 0.81e2 + 0.25e2 / 0.8748e4 * t64) * t52
  t418 = t56 * s0
  t425 = (t246 - t63 / 0.8e1) * t52 * t56
  t428 = t425 / 0.4e1 - 0.9e1 / 0.20e2 + t64 / 0.36e2
  t429 = t428 ** 2
  t433 = 0.73e2 / 0.1620e4 * t425 - 0.73e2 / 0.900e3 + 0.73e2 / 0.14580e5 * t64
  t434 = t433 * t34
  t435 = 0.1e1 - t34
  t439 = (0.1e1 + 0.5e1 / 0.12e2 * t417 * t418 * t62 + 0.292e3 / 0.405e3 * t429 - 0.6e1 * t434 * t435) ** (0.1e1 / 0.10e2)
  t444 = 0.25633760400000000000000000000000000000000000000000e0 * t248
  t450 = 0.7e1 + 0.44760329444444444444444444444444444444444444444445e0 * t64 - 0.35e2 / 0.9e1 * (t247 + t444 + 0.11867481666666666666666666666666666666666666666667e-1 * t63) * t52 * t56
  t453 = t147 + t450 * t254 / 0.9e1
  t456 = -f.p.cam_beta * (t42 * t360 + t414 * t439) + t42 * t453 + t362 * t439
  t460 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t456)
  t461 = r1 <= f.p.dens_threshold
  t462 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t463 = 0.1e1 + t462
  t464 = t463 <= f.p.zeta_threshold
  t465 = t463 ** (0.1e1 / 0.3e1)
  t467 = f.my_piecewise3(t464, t22, t465 * t463)
  t468 = t467 * t26
  t469 = 0.1e1 / r1
  t470 = s2 * t469
  t471 = 0.1e1 / tau1
  t473 = t470 * t471 / 0.8e1
  t474 = t473 < 0.10e1
  t475 = f.my_piecewise3(t474, t473, 0.10e1)
  t476 = t475 ** 2
  t477 = t476 * t475
  t479 = t476 + 0.3e1 * t477
  t480 = 0.1e1 + t477
  t481 = t480 ** 2
  t482 = 0.1e1 / t481
  t483 = t479 * t482
  t484 = r1 ** 2
  t485 = r1 ** (0.1e1 / 0.3e1)
  t486 = t485 ** 2
  t488 = 0.1e1 / t486 / t484
  t489 = s2 * t488
  t490 = t57 * t489
  t492 = s2 ** 2
  t493 = t484 ** 2
  t496 = 0.1e1 / t485 / t493 / r1
  t500 = 0.1e1 + 0.15045488888888888888888888888888888888888888888889e0 * t490 + 0.26899490462262948000000000000000000000000000000000e-2 * t69 * t492 * t496
  t501 = t500 ** (0.1e1 / 0.10e2)
  t502 = 0.1e1 / t501
  t503 = f.my_piecewise5(t84, t11, t82, t15, -t17)
  t504 = 0.1e1 + t503
  t505 = t504 <= f.p.zeta_threshold
  t506 = t504 ** (0.1e1 / 0.3e1)
  t507 = f.my_piecewise3(t505, t21, t506)
  t508 = 0.1e1 / t507
  t509 = t502 * t508
  t512 = t49 * t51 * t509 / 0.18e2
  t513 = t512 < 0.1e-9
  t514 = f.my_piecewise3(t513, 0.1e-9, t512)
  t515 = 0.135e1 <= t514
  t516 = 0.135e1 < t514
  t517 = f.my_piecewise3(t516, t514, 0.135e1)
  t518 = t517 ** 2
  t521 = t518 ** 2
  t524 = t521 * t518
  t527 = t521 ** 2
  t539 = t527 ** 2
  t543 = f.my_piecewise3(t516, 0.135e1, t514)
  t544 = 0.1e1 / t543
  t546 = jax.lax.erf(t544 / 0.2e1)
  t548 = t543 ** 2
  t549 = 0.1e1 / t548
  t551 = jnp.exp(-t549 / 0.4e1)
  t552 = t551 - 0.1e1
  t555 = t551 - 0.3e1 / 0.2e1 - 0.2e1 * t548 * t552
  t558 = t126 * t546 + 0.2e1 * t543 * t555
  t562 = f.my_piecewise3(t515, 0.1e1 / t518 / 0.36e2 - 0.1e1 / t521 / 0.960e3 + 0.1e1 / t524 / 0.26880e5 - 0.1e1 / t527 / 0.829440e6 + 0.1e1 / t527 / t518 / 0.28385280e8 - 0.1e1 / t527 / t521 / 0.1073479680e10 + 0.1e1 / t527 / t524 / 0.44590694400e11 - 0.1e1 / t539 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t543 * t558)
  t563 = t500 ** (0.1e1 / 0.5e1)
  t564 = 0.1e1 / t563
  t566 = 0.27e0 <= t514
  t567 = 0.27e0 < t514
  t568 = f.my_piecewise3(t567, t514, 0.27e0)
  t569 = t568 ** 2
  t570 = t569 ** 2
  t571 = t570 ** 2
  t572 = t571 * t570
  t573 = t571 ** 2
  t574 = t573 ** 2
  t578 = t570 * t569
  t579 = t571 * t578
  t589 = t571 * t569
  t604 = 0.1e1 / t574 / t572 / 0.33929038000650146833571361325056000000e38 - 0.1e1 / t574 / t579 / 0.3511556992918352140755776405766144000000e40 + 0.3e1 / 0.2240e4 / t570 - 0.1e1 / t578 / 0.11520e5 + 0.3e1 / 0.788480e6 / t571 - 0.1e1 / t589 / 0.7454720e7 + 0.1e1 / t572 / 0.247726080e9 - 0.1e1 / t579 / 0.9358540800e10 + 0.1e1 / t573 / 0.394474291200e12 - 0.1e1 / t573 / t569 / 0.18311911833600e14 + 0.1e1 / t573 / t570 / 0.927028425523200e15
  t637 = -0.1e1 / t573 / t578 / 0.50785035485184000e17 + 0.1e1 / t573 / t571 / 0.2991700272218112000e19 - 0.1e1 / t573 / t589 / 0.188514051721003008000e21 + 0.1e1 / t573 / t572 / 0.12648942844388573184000e23 - 0.1e1 / t573 / t579 / 0.900231674141645733888000e24 + 0.1e1 / t574 / 0.67726520292999771979776000e26 - 0.1e1 / t574 / t569 / 0.5369745537516410492682240000e28 + 0.1e1 / t574 / t570 / 0.447473103488807905221672960000e30 - 0.1e1 / t574 / t578 / 0.39097165634742908368485089280000e32 + 0.1e1 / t574 / t571 / 0.3573852336994573837102806466560000e34 - 0.1e1 / t574 / t589 / 0.341095116070365837848137621831680000e36
  t639 = f.my_piecewise3(t567, 0.27e0, t514)
  t640 = t639 ** 2
  t642 = t640 ** 2
  t643 = 0.64e2 * t642
  t644 = 0.20e2 * t640 - t643
  t647 = jnp.exp(-0.1e1 / t640 / 0.4e1)
  t651 = 0.1e1 / t639
  t653 = jax.lax.erf(t651 / 0.2e1)
  t656 = 0.10e2 * t639 * t126 * t653 + t644 * t647 - 0.36e2 * t640 + t643 - 0.3e1
  t660 = f.my_piecewise3(t566, t604 + t637, 0.24e2 * t640 * t656 + 0.1e1)
  t662 = 0.1e1 / t486 / r1
  t663 = tau1 * t662
  t664 = 0.14554132000000000000000000000000000000000000000000e0 * t663
  t666 = -t664 + t249 + 0.42296278333333333333333333333333333333333333333333e-1 * t489
  t667 = t660 * t666
  t668 = t563 ** 2
  t669 = 0.1e1 / t668
  t670 = t57 * t669
  t673 = 0.32e0 <= t514
  t674 = 0.32e0 < t514
  t675 = f.my_piecewise3(t674, t514, 0.32e0)
  t676 = t675 ** 2
  t677 = t676 ** 2
  t680 = t677 * t676
  t683 = t677 ** 2
  t686 = t683 * t676
  t689 = t683 * t677
  t692 = t683 * t680
  t695 = t683 ** 2
  t719 = t695 ** 2
  t731 = 0.3e1 / 0.7840e4 / t677 - 0.1e1 / t680 / 0.56448e5 + 0.5e1 / 0.8515584e7 / t683 - 0.1e1 / t686 / 0.61501440e8 + 0.1e1 / t689 / 0.2530344960e10 - 0.1e1 / t692 / 0.115811942400e12 + 0.1e1 / t695 / 0.5811921223680e13 - 0.1e1 / t695 / t676 / 0.316612955602944e15 + 0.1e1 / t695 / t677 / 0.18582706166169600e17 - 0.1e1 / t695 / t680 / 0.1168055816159232000e19 + 0.1e1 / t695 / t683 / 0.78244468658012160000e20 - 0.1e1 / t695 / t686 / 0.5562511054710453043200e22 + 0.1e1 / t695 / t689 / 0.418174050435486229463040e24 - 0.1e1 / t695 / t692 / 0.33139778504339333578752000e26 + 0.1e1 / t719 / 0.2760851680179343645999104000e28 - 0.1e1 / t719 / t676 / 0.241191070393445437962977280000e30 + 0.1e1 / t719 / t677 / 0.22046293272414372635684634624000e32 - 0.1e1 / t719 / t680 / 0.2104209454461863328391867505049600e34
  t732 = f.my_piecewise3(t674, 0.32e0, t514)
  t734 = t732 ** 2
  t735 = t734 * t732
  t737 = t734 ** 2
  t738 = t737 * t732
  t742 = t737 ** 2
  t745 = -0.122880e6 * t742 * t732 + 0.3840e4 * t737 * t735 - 0.8e1 * t732 + 0.256e3 * t735 - 0.576e3 * t738
  t746 = 0.1e1 / t734
  t748 = jnp.exp(-t746 / 0.4e1)
  t752 = t737 * t734
  t754 = -0.35e2 + 0.224e3 * t734 - 0.1440e4 * t737 + 0.5120e4 * t752
  t758 = -0.2e1 + 0.60e2 * t734
  t762 = jax.lax.erf(0.1e1 / t732 / 0.2e1)
  t765 = 0.2e1 * t126 * t758 * t762 + 0.24e2 * t735 * t754 + t745 * t748
  t769 = f.my_piecewise3(t673, t731, 0.1e1 + 0.8e1 / 0.7e1 * t732 * t765)
  t770 = t769 * t52
  t771 = t770 * t56
  t772 = t489 * t669
  t775 = t562 * t564 + 0.35e2 / 0.81e2 * t667 * t670 + 0.26329605555555555555555555555555555555555555555556e-1 * t771 * t772
  t777 = 0.1e1 - t483
  t780 = t49 * t51 * t508 / 0.18e2
  t781 = 0.135e1 <= t780
  t782 = 0.135e1 < t780
  t783 = f.my_piecewise3(t782, t780, 0.135e1)
  t784 = t783 ** 2
  t787 = t784 ** 2
  t790 = t787 * t784
  t793 = t787 ** 2
  t805 = t793 ** 2
  t809 = f.my_piecewise3(t782, 0.135e1, t780)
  t810 = 0.1e1 / t809
  t812 = jax.lax.erf(t810 / 0.2e1)
  t814 = t809 ** 2
  t815 = 0.1e1 / t814
  t817 = jnp.exp(-t815 / 0.4e1)
  t818 = t817 - 0.1e1
  t821 = t817 - 0.3e1 / 0.2e1 - 0.2e1 * t814 * t818
  t824 = t126 * t812 + 0.2e1 * t809 * t821
  t828 = f.my_piecewise3(t781, 0.1e1 / t784 / 0.36e2 - 0.1e1 / t787 / 0.960e3 + 0.1e1 / t790 / 0.26880e5 - 0.1e1 / t793 / 0.829440e6 + 0.1e1 / t793 / t784 / 0.28385280e8 - 0.1e1 / t793 / t787 / 0.1073479680e10 + 0.1e1 / t793 / t790 / 0.44590694400e11 - 0.1e1 / t805 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t809 * t824)
  t829 = t777 * t828
  t832 = (0.10e2 / 0.81e2 + 0.25e2 / 0.8748e4 * t490) * t52
  t833 = t56 * s2
  t840 = (t663 - t489 / 0.8e1) * t52 * t56
  t843 = t840 / 0.4e1 - 0.9e1 / 0.20e2 + t490 / 0.36e2
  t844 = t843 ** 2
  t848 = 0.73e2 / 0.1620e4 * t840 - 0.73e2 / 0.900e3 + 0.73e2 / 0.14580e5 * t490
  t849 = t848 * t475
  t850 = 0.1e1 - t475
  t854 = (0.1e1 + 0.5e1 / 0.12e2 * t832 * t833 * t488 + 0.292e3 / 0.405e3 * t844 - 0.6e1 * t849 * t850) ** (0.1e1 / 0.10e2)
  t864 = 0.7e1 + 0.44760329444444444444444444444444444444444444444445e0 * t490 - 0.35e2 / 0.9e1 * (t664 + t444 + 0.11867481666666666666666666666666666666666666666667e-1 * t489) * t52 * t56
  t867 = t564 + t864 * t669 / 0.9e1
  t870 = -f.p.cam_beta * (t483 * t775 + t829 * t854) + t483 * t867 + t777 * t854
  t874 = f.my_piecewise3(t461, 0, -0.3e1 / 0.8e1 * t5 * t468 * t870)
  t875 = t6 ** 2
  t877 = t16 / t875
  t878 = t7 - t877
  t879 = f.my_piecewise5(t10, 0, t14, 0, t878)
  t882 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t879)
  t887 = t26 ** 2
  t888 = 0.1e1 / t887
  t892 = t5 * t25 * t888 * t456 / 0.8e1
  t897 = f.my_piecewise3(t33, -s0 / t58 * t30 / 0.8e1, 0)
  t900 = t35 * t897
  t903 = (0.2e1 * t34 * t897 + 0.9e1 * t900) * t41
  t907 = t38 / t40 / t39
  t908 = t360 * t35
  t912 = t100 * t99
  t913 = 0.1e1 / t912
  t916 = t2 / t26 / t6
  t919 = t49 * t916 * t91 / 0.54e2
  t921 = t48 * f.p.cam_omega * t2
  t924 = t50 / t79 / t78
  t927 = 0.1e1 / t60 / t58 / r0
  t928 = s0 * t927
  t929 = t57 * t928
  t935 = t69 * t70 / t59 / t71 / t58
  t937 = -0.40121303703703703703703703703703703703703703703704e0 * t929 - 0.14346394913206905600000000000000000000000000000000e-1 * t935
  t942 = t50 * t80
  t943 = t89 ** 2
  t944 = 0.1e1 / t943
  t945 = t88 ** 2
  t946 = 0.1e1 / t945
  t947 = f.my_piecewise5(t82, 0, t84, 0, t878)
  t950 = f.my_piecewise3(t87, 0, t946 * t947 / 0.3e1)
  t951 = t944 * t950
  t956 = f.my_piecewise3(t95, 0, -t919 - t921 * t924 * t90 * t937 / 0.180e3 - t921 * t942 * t951 / 0.18e2)
  t957 = f.my_piecewise3(t98, t956, 0)
  t960 = t103 * t99
  t961 = 0.1e1 / t960
  t964 = t103 * t912
  t965 = 0.1e1 / t964
  t969 = 0.1e1 / t109 / t99
  t973 = 0.1e1 / t109 / t912
  t977 = 0.1e1 / t109 / t960
  t981 = 0.1e1 / t109 / t964
  t985 = 0.1e1 / t121 / t99
  t989 = f.my_piecewise3(t98, 0, t956)
  t991 = t134 * t132
  t996 = 0.1e1 / t131 / t125
  t1000 = t125 * t135
  t1012 = f.my_piecewise3(t97, -t913 * t957 / 0.18e2 + t961 * t957 / 0.240e3 - t965 * t957 / 0.4480e4 + t969 * t957 / 0.103680e6 - t973 * t957 / 0.2838528e7 + t977 * t957 / 0.89456640e8 - t981 * t957 / 0.3185049600e10 + t985 * t957 / 0.126340300800e12, -0.8e1 / 0.3e1 * t989 * t141 - 0.8e1 / 0.3e1 * t125 * (-t991 * t989 + 0.2e1 * t989 * t138 + 0.2e1 * t125 * (t996 * t989 * t134 / 0.2e1 - 0.4e1 * t1000 * t989 - t127 * t989 * t134)))
  t1015 = 0.1e1 / t146 / t78
  t1016 = t145 * t1015
  t1019 = t153 * t151
  t1020 = t154 * t1019
  t1022 = 0.1e1 / t157 / t1020
  t1023 = f.my_piecewise3(t150, t956, 0)
  t1026 = t152 * t151
  t1027 = t153 * t1026
  t1028 = t154 * t1027
  t1030 = 0.1e1 / t157 / t1028
  t1033 = 0.1e1 / t1019
  t1036 = 0.1e1 / t1027
  t1039 = t154 * t151
  t1040 = 0.1e1 / t1039
  t1043 = t154 * t1026
  t1044 = 0.1e1 / t1043
  t1047 = 0.1e1 / t1020
  t1050 = 0.1e1 / t1028
  t1054 = 0.1e1 / t156 / t151
  t1058 = 0.1e1 / t156 / t1026
  t1062 = 0.1e1 / t156 / t1019
  t1065 = -t1022 * t1023 / 0.771114500014776064399349121024000000e36 + t1030 * t1023 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t1033 * t1023 + t1036 * t1023 / 0.1920e4 - 0.3e1 / 0.98560e5 * t1040 * t1023 + t1044 * t1023 / 0.745472e6 - t1047 * t1023 / 0.20643840e8 + t1050 * t1023 / 0.668467200e9 - t1054 * t1023 / 0.24654643200e11 + t1058 * t1023 / 0.1017328435200e13 - t1062 * t1023 / 0.46351421276160e14
  t1067 = 0.1e1 / t156 / t1027
  t1071 = 0.1e1 / t156 / t1039
  t1075 = 0.1e1 / t156 / t1043
  t1079 = 0.1e1 / t156 / t1020
  t1083 = 0.1e1 / t156 / t1028
  t1087 = 0.1e1 / t157 / t151
  t1091 = 0.1e1 / t157 / t1026
  t1095 = 0.1e1 / t157 / t1019
  t1099 = 0.1e1 / t157 / t1027
  t1103 = 0.1e1 / t157 / t1039
  t1107 = 0.1e1 / t157 / t1043
  t1110 = t1067 * t1023 / 0.2308410703872000e16 - t1071 * t1023 / 0.124654178009088000e18 + t1075 * t1023 / 0.7250540450807808000e19 - t1079 * t1023 / 0.451747958728163328000e21 + t1083 * t1023 / 0.30007722471388191129600e23 - t1087 * t1023 / 0.2116453759156242874368000e25 + t1091 * t1023 / 0.157933692279894426255360000e27 - t1095 * t1023 / 0.12429808430244664033935360000e29 + t1099 * t1023 / 0.1028872779861655483381186560000e31 - t1103 * t1023 / 0.89346308424864345927570161664000e32 + t1107 * t1023 / 0.8121312287389662805908038615040000e34
  t1112 = t222 * t239
  t1113 = f.my_piecewise3(t150, 0, t956)
  t1116 = t222 * t1113
  t1118 = t223 * t222
  t1120 = 0.256e3 * t1118 * t1113
  t1124 = t227 / t1118
  t1132 = t234 * t230
  t1139 = f.my_piecewise3(t149, t1065 + t1110, 0.48e2 * t1112 * t1113 + 0.24e2 * t223 * ((0.40e2 * t1116 - t1120) * t230 + t1124 * t1113 * t230 / 0.2e1 - 0.72e2 * t1116 + t1120 + 0.10e2 * t1113 * t126 * t236 - 0.10e2 * t1132 * t1113))
  t1143 = tau0 * t62
  t1144 = 0.24256886666666666666666666666666666666666666666667e0 * t1143
  t1150 = t252 * t52
  t1152 = 0.1e1 / t253 / t78
  t1153 = t56 * t1152
  t1157 = t262 * t260
  t1158 = 0.1e1 / t1157
  t1159 = f.my_piecewise3(t259, t956, 0)
  t1162 = t261 * t260
  t1163 = t262 * t1162
  t1164 = 0.1e1 / t1163
  t1167 = t268 * t260
  t1168 = 0.1e1 / t1167
  t1171 = t268 * t1162
  t1172 = 0.1e1 / t1171
  t1175 = t268 * t1157
  t1176 = 0.1e1 / t1175
  t1179 = t268 * t1163
  t1180 = 0.1e1 / t1179
  t1184 = 0.1e1 / t280 / t260
  t1188 = 0.1e1 / t280 / t1162
  t1192 = 0.1e1 / t280 / t1157
  t1196 = 0.1e1 / t280 / t1163
  t1200 = 0.1e1 / t280 / t1167
  t1204 = 0.1e1 / t280 / t1171
  t1208 = 0.1e1 / t280 / t1175
  t1212 = 0.1e1 / t280 / t1179
  t1216 = 0.1e1 / t304 / t260
  t1220 = 0.1e1 / t304 / t1162
  t1224 = 0.1e1 / t304 / t1157
  t1228 = 0.1e1 / t304 / t1163
  t1231 = -0.3e1 / 0.1960e4 * t1158 * t1159 + t1164 * t1159 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t1168 * t1159 + t1172 * t1159 / 0.6150144e7 - t1176 * t1159 / 0.210862080e9 + t1180 * t1159 / 0.8272281600e10 - t1184 * t1159 / 0.363245076480e12 + t1188 * t1159 / 0.17589608644608e14 - t1192 * t1159 / 0.929135308308480e15 + t1196 * t1159 / 0.53093446189056000e17 - t1200 * t1159 / 0.3260186194083840000e19 + t1204 * t1159 / 0.213942732873478963200e21 - t1208 * t1159 / 0.14934787515553079623680e23 + t1212 * t1159 / 0.1104659283477977785958400e25 - t1216 * t1159 / 0.86276615005604488937472000e26 + t1220 * t1159 / 0.7093855011571924645969920000e28 - t1224 * t1159 / 0.612397035344843684324573184000e30 + t1228 * t1159 / 0.55373933012154298115575460659200e32
  t1232 = f.my_piecewise3(t259, 0, t956)
  t1246 = t330 / t320
  t1250 = t319 * t339
  t1262 = t126 * t317
  t1266 = t343 * t333
  t1274 = f.my_piecewise3(t258, t1231, 0.8e1 / 0.7e1 * t1232 * t350 + 0.8e1 / 0.7e1 * t317 * ((0.768e3 * t319 * t1232 - 0.2880e4 * t322 * t1232 - 0.1105920e7 * t327 * t1232 + 0.26880e5 * t337 * t1232 - 0.8e1 * t1232) * t333 + t1246 * t1232 * t333 / 0.2e1 + 0.72e2 * t1250 * t1232 + 0.24e2 * t320 * (0.448e3 * t317 * t1232 - 0.5760e4 * t320 * t1232 + 0.30720e5 * t323 * t1232) + 0.240e3 * t1262 * t1232 * t347 - 0.2e1 * t1266 * t331 * t1232))
  t1290 = 0.6e1 * t907 * t900 - t903
  t1293 = t369 * t368
  t1294 = 0.1e1 / t1293
  t1297 = t49 * t916 * t90 / 0.54e2
  t1301 = -t1297 - t49 * t51 * t951 / 0.18e2
  t1302 = f.my_piecewise3(t367, t1301, 0)
  t1305 = t372 * t368
  t1306 = 0.1e1 / t1305
  t1309 = t372 * t1293
  t1310 = 0.1e1 / t1309
  t1314 = 0.1e1 / t378 / t368
  t1318 = 0.1e1 / t378 / t1293
  t1322 = 0.1e1 / t378 / t1305
  t1326 = 0.1e1 / t378 / t1309
  t1330 = 0.1e1 / t390 / t368
  t1334 = f.my_piecewise3(t367, 0, t1301)
  t1336 = t402 * t400
  t1341 = 0.1e1 / t399 / t394
  t1345 = t394 * t403
  t1357 = f.my_piecewise3(t366, -t1294 * t1302 / 0.18e2 + t1306 * t1302 / 0.240e3 - t1310 * t1302 / 0.4480e4 + t1314 * t1302 / 0.103680e6 - t1318 * t1302 / 0.2838528e7 + t1322 * t1302 / 0.89456640e8 - t1326 * t1302 / 0.3185049600e10 + t1330 * t1302 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1334 * t409 - 0.8e1 / 0.3e1 * t394 * (-t1336 * t1334 + 0.2e1 * t1334 * t406 + 0.2e1 * t394 * (t1341 * t1334 * t402 / 0.2e1 - 0.4e1 * t1345 * t1334 - t395 * t1334 * t402)))
  t1360 = t439 ** 2
  t1361 = t1360 ** 2
  t1362 = t1361 ** 2
  t1364 = 0.1e1 / t1362 / t439
  t1373 = (-0.5e1 / 0.3e1 * t1143 + t928 / 0.3e1) * t52 * t56
  t1390 = -0.125e3 / 0.39366e5 * t935 - 0.10e2 / 0.9e1 * t417 * t418 * t927 + 0.584e3 / 0.405e3 * t428 * (t1373 / 0.4e1 - 0.2e1 / 0.27e2 * t929) - 0.6e1 * (0.73e2 / 0.1620e4 * t1373 - 0.146e3 / 0.10935e5 * t929) * t34 * t435 - 0.6e1 * t433 * t897 * t435 + 0.6e1 * t434 * t897
  t1397 = t453 * t35
  t1412 = t450 * t1152
  t1418 = t362 * t1364
  t1426 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t882 * t26 * t456 - t892 - 0.3e1 / 0.8e1 * t5 * t27 * (-f.p.cam_beta * (t903 * t360 - 0.6e1 * t907 * t908 * t897 + t42 * (t1012 * t147 - t1016 * t937 / 0.5e1 + 0.35e2 / 0.81e2 * t1139 * t251 * t255 + 0.35e2 / 0.81e2 * t243 * (t1144 - 0.11279007555555555555555555555555555555555555555555e0 * t928) * t255 - 0.14e2 / 0.81e2 * t1150 * t1153 * t937 + 0.26329605555555555555555555555555555555555555555556e-1 * t1274 * t52 * t56 * t357 - 0.70212281481481481481481481481481481481481481481483e-1 * t356 * t928 * t254 - 0.10531842222222222222222222222222222222222222222222e-1 * t356 * t63 * t1152 * t937) + t1290 * t413 * t439 + t362 * t1357 * t439 + t414 * t1364 * t1390 / 0.10e2) + t903 * t453 - 0.6e1 * t907 * t1397 * t897 + t42 * (-t1015 * t937 / 0.5e1 + (-0.11936087851851851851851851851851851851851851851852e1 * t929 - 0.35e2 / 0.9e1 * (-t1144 - 0.31646617777777777777777777777777777777777777777779e-1 * t928) * t52 * t56) * t254 / 0.9e1 - 0.2e1 / 0.45e2 * t1412 * t937) + t1290 * t439 + t1418 * t1390 / 0.10e2))
  t1427 = -t878
  t1428 = f.my_piecewise5(t14, 0, t10, 0, t1427)
  t1431 = f.my_piecewise3(t464, 0, 0.4e1 / 0.3e1 * t465 * t1428)
  t1439 = t5 * t467 * t888 * t870 / 0.8e1
  t1441 = t26 * f.p.cam_beta
  t1442 = t518 * t517
  t1443 = 0.1e1 / t1442
  t1446 = t49 * t916 * t509 / 0.54e2
  t1447 = t50 * t502
  t1448 = t507 ** 2
  t1449 = 0.1e1 / t1448
  t1450 = t506 ** 2
  t1451 = 0.1e1 / t1450
  t1452 = f.my_piecewise5(t84, 0, t82, 0, t1427)
  t1455 = f.my_piecewise3(t505, 0, t1451 * t1452 / 0.3e1)
  t1456 = t1449 * t1455
  t1461 = f.my_piecewise3(t513, 0, -t1446 - t921 * t1447 * t1456 / 0.18e2)
  t1462 = f.my_piecewise3(t516, t1461, 0)
  t1465 = t521 * t517
  t1466 = 0.1e1 / t1465
  t1469 = t521 * t1442
  t1470 = 0.1e1 / t1469
  t1474 = 0.1e1 / t527 / t517
  t1478 = 0.1e1 / t527 / t1442
  t1482 = 0.1e1 / t527 / t1465
  t1486 = 0.1e1 / t527 / t1469
  t1490 = 0.1e1 / t539 / t517
  t1494 = f.my_piecewise3(t516, 0, t1461)
  t1496 = t551 * t549
  t1501 = 0.1e1 / t548 / t543
  t1505 = t543 * t552
  t1517 = f.my_piecewise3(t515, -t1443 * t1462 / 0.18e2 + t1466 * t1462 / 0.240e3 - t1470 * t1462 / 0.4480e4 + t1474 * t1462 / 0.103680e6 - t1478 * t1462 / 0.2838528e7 + t1482 * t1462 / 0.89456640e8 - t1486 * t1462 / 0.3185049600e10 + t1490 * t1462 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1494 * t558 - 0.8e1 / 0.3e1 * t543 * (-t1496 * t1494 + 0.2e1 * t1494 * t555 + 0.2e1 * t543 * (t1501 * t1494 * t551 / 0.2e1 - 0.4e1 * t1505 * t1494 - t544 * t1494 * t551)))
  t1519 = t570 * t568
  t1520 = t571 * t1519
  t1522 = 0.1e1 / t574 / t1520
  t1523 = f.my_piecewise3(t567, t1461, 0)
  t1526 = t569 * t568
  t1527 = t570 * t1526
  t1528 = t571 * t1527
  t1530 = 0.1e1 / t574 / t1528
  t1533 = 0.1e1 / t1519
  t1536 = 0.1e1 / t1527
  t1539 = t571 * t568
  t1540 = 0.1e1 / t1539
  t1543 = t571 * t1526
  t1544 = 0.1e1 / t1543
  t1547 = 0.1e1 / t1520
  t1550 = 0.1e1 / t1528
  t1554 = 0.1e1 / t573 / t568
  t1558 = 0.1e1 / t573 / t1526
  t1562 = 0.1e1 / t573 / t1519
  t1565 = -t1522 * t1523 / 0.771114500014776064399349121024000000e36 + t1530 * t1523 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t1533 * t1523 + t1536 * t1523 / 0.1920e4 - 0.3e1 / 0.98560e5 * t1540 * t1523 + t1544 * t1523 / 0.745472e6 - t1547 * t1523 / 0.20643840e8 + t1550 * t1523 / 0.668467200e9 - t1554 * t1523 / 0.24654643200e11 + t1558 * t1523 / 0.1017328435200e13 - t1562 * t1523 / 0.46351421276160e14
  t1567 = 0.1e1 / t573 / t1527
  t1571 = 0.1e1 / t573 / t1539
  t1575 = 0.1e1 / t573 / t1543
  t1579 = 0.1e1 / t573 / t1520
  t1583 = 0.1e1 / t573 / t1528
  t1587 = 0.1e1 / t574 / t568
  t1591 = 0.1e1 / t574 / t1526
  t1595 = 0.1e1 / t574 / t1519
  t1599 = 0.1e1 / t574 / t1527
  t1603 = 0.1e1 / t574 / t1539
  t1607 = 0.1e1 / t574 / t1543
  t1610 = t1567 * t1523 / 0.2308410703872000e16 - t1571 * t1523 / 0.124654178009088000e18 + t1575 * t1523 / 0.7250540450807808000e19 - t1579 * t1523 / 0.451747958728163328000e21 + t1583 * t1523 / 0.30007722471388191129600e23 - t1587 * t1523 / 0.2116453759156242874368000e25 + t1591 * t1523 / 0.157933692279894426255360000e27 - t1595 * t1523 / 0.12429808430244664033935360000e29 + t1599 * t1523 / 0.1028872779861655483381186560000e31 - t1603 * t1523 / 0.89346308424864345927570161664000e32 + t1607 * t1523 / 0.8121312287389662805908038615040000e34
  t1612 = t639 * t656
  t1613 = f.my_piecewise3(t567, 0, t1461)
  t1616 = t639 * t1613
  t1618 = t640 * t639
  t1620 = 0.256e3 * t1618 * t1613
  t1624 = t644 / t1618
  t1632 = t651 * t647
  t1639 = f.my_piecewise3(t566, t1565 + t1610, 0.48e2 * t1612 * t1613 + 0.24e2 * t640 * ((0.40e2 * t1616 - t1620) * t647 + t1624 * t1613 * t647 / 0.2e1 - 0.72e2 * t1616 + t1620 + 0.10e2 * t1613 * t126 * t653 - 0.10e2 * t1632 * t1613))
  t1643 = t677 * t675
  t1644 = 0.1e1 / t1643
  t1645 = f.my_piecewise3(t674, t1461, 0)
  t1648 = t676 * t675
  t1649 = t677 * t1648
  t1650 = 0.1e1 / t1649
  t1653 = t683 * t675
  t1654 = 0.1e1 / t1653
  t1657 = t683 * t1648
  t1658 = 0.1e1 / t1657
  t1661 = t683 * t1643
  t1662 = 0.1e1 / t1661
  t1665 = t683 * t1649
  t1666 = 0.1e1 / t1665
  t1670 = 0.1e1 / t695 / t675
  t1674 = 0.1e1 / t695 / t1648
  t1678 = 0.1e1 / t695 / t1643
  t1682 = 0.1e1 / t695 / t1649
  t1686 = 0.1e1 / t695 / t1653
  t1690 = 0.1e1 / t695 / t1657
  t1694 = 0.1e1 / t695 / t1661
  t1698 = 0.1e1 / t695 / t1665
  t1702 = 0.1e1 / t719 / t675
  t1706 = 0.1e1 / t719 / t1648
  t1710 = 0.1e1 / t719 / t1643
  t1714 = 0.1e1 / t719 / t1649
  t1717 = -0.3e1 / 0.1960e4 * t1644 * t1645 + t1650 * t1645 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t1654 * t1645 + t1658 * t1645 / 0.6150144e7 - t1662 * t1645 / 0.210862080e9 + t1666 * t1645 / 0.8272281600e10 - t1670 * t1645 / 0.363245076480e12 + t1674 * t1645 / 0.17589608644608e14 - t1678 * t1645 / 0.929135308308480e15 + t1682 * t1645 / 0.53093446189056000e17 - t1686 * t1645 / 0.3260186194083840000e19 + t1690 * t1645 / 0.213942732873478963200e21 - t1694 * t1645 / 0.14934787515553079623680e23 + t1698 * t1645 / 0.1104659283477977785958400e25 - t1702 * t1645 / 0.86276615005604488937472000e26 + t1706 * t1645 / 0.7093855011571924645969920000e28 - t1710 * t1645 / 0.612397035344843684324573184000e30 + t1714 * t1645 / 0.55373933012154298115575460659200e32
  t1718 = f.my_piecewise3(t674, 0, t1461)
  t1732 = t745 / t735
  t1736 = t734 * t754
  t1748 = t126 * t732
  t1752 = t758 * t748
  t1760 = f.my_piecewise3(t673, t1717, 0.8e1 / 0.7e1 * t1718 * t765 + 0.8e1 / 0.7e1 * t732 * ((0.768e3 * t734 * t1718 - 0.2880e4 * t737 * t1718 - 0.1105920e7 * t742 * t1718 + 0.26880e5 * t752 * t1718 - 0.8e1 * t1718) * t748 + t1732 * t1718 * t748 / 0.2e1 + 0.72e2 * t1736 * t1718 + 0.24e2 * t735 * (0.448e3 * t732 * t1718 - 0.5760e4 * t735 * t1718 + 0.30720e5 * t738 * t1718) + 0.240e3 * t1748 * t1718 * t762 - 0.2e1 * t1752 * t746 * t1718))
  t1767 = t784 * t783
  t1768 = 0.1e1 / t1767
  t1771 = t49 * t916 * t508 / 0.54e2
  t1775 = -t1771 - t49 * t51 * t1456 / 0.18e2
  t1776 = f.my_piecewise3(t782, t1775, 0)
  t1779 = t787 * t783
  t1780 = 0.1e1 / t1779
  t1783 = t787 * t1767
  t1784 = 0.1e1 / t1783
  t1788 = 0.1e1 / t793 / t783
  t1792 = 0.1e1 / t793 / t1767
  t1796 = 0.1e1 / t793 / t1779
  t1800 = 0.1e1 / t793 / t1783
  t1804 = 0.1e1 / t805 / t783
  t1808 = f.my_piecewise3(t782, 0, t1775)
  t1810 = t817 * t815
  t1815 = 0.1e1 / t814 / t809
  t1819 = t809 * t818
  t1831 = f.my_piecewise3(t781, -t1768 * t1776 / 0.18e2 + t1780 * t1776 / 0.240e3 - t1784 * t1776 / 0.4480e4 + t1788 * t1776 / 0.103680e6 - t1792 * t1776 / 0.2838528e7 + t1796 * t1776 / 0.89456640e8 - t1800 * t1776 / 0.3185049600e10 + t1804 * t1776 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1808 * t824 - 0.8e1 / 0.3e1 * t809 * (-t1810 * t1808 + 0.2e1 * t1808 * t821 + 0.2e1 * t809 * (t1815 * t1808 * t817 / 0.2e1 - 0.4e1 * t1819 * t1808 - t810 * t1808 * t817)))
  t1839 = f.my_piecewise3(t461, 0, -0.3e1 / 0.8e1 * t5 * t1431 * t26 * t870 - t1439 + 0.3e1 / 0.8e1 * t5 * t467 * t1441 * (t483 * (t1517 * t564 + 0.35e2 / 0.81e2 * t1639 * t666 * t670 + 0.26329605555555555555555555555555555555555555555556e-1 * t1760 * t52 * t56 * t772) + t777 * t1831 * t854))
  vrho_0_ = t460 + t874 + t6 * (t1426 + t1839)
  t1842 = -t7 - t877
  t1843 = f.my_piecewise5(t10, 0, t14, 0, t1842)
  t1846 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t1843)
  t1852 = f.my_piecewise5(t82, 0, t84, 0, t1842)
  t1855 = f.my_piecewise3(t87, 0, t946 * t1852 / 0.3e1)
  t1856 = t944 * t1855
  t1861 = f.my_piecewise3(t95, 0, -t919 - t921 * t942 * t1856 / 0.18e2)
  t1862 = f.my_piecewise3(t98, t1861, 0)
  t1880 = f.my_piecewise3(t98, 0, t1861)
  t1899 = f.my_piecewise3(t97, -t913 * t1862 / 0.18e2 + t961 * t1862 / 0.240e3 - t965 * t1862 / 0.4480e4 + t969 * t1862 / 0.103680e6 - t973 * t1862 / 0.2838528e7 + t977 * t1862 / 0.89456640e8 - t981 * t1862 / 0.3185049600e10 + t985 * t1862 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1880 * t141 - 0.8e1 / 0.3e1 * t125 * (-t991 * t1880 + 0.2e1 * t1880 * t138 + 0.2e1 * t125 * (t996 * t1880 * t134 / 0.2e1 - 0.4e1 * t1000 * t1880 - t127 * t1880 * t134)))
  t1901 = f.my_piecewise3(t150, t1861, 0)
  t1924 = -t1022 * t1901 / 0.771114500014776064399349121024000000e36 + t1030 * t1901 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t1033 * t1901 + t1036 * t1901 / 0.1920e4 - 0.3e1 / 0.98560e5 * t1040 * t1901 + t1044 * t1901 / 0.745472e6 - t1047 * t1901 / 0.20643840e8 + t1050 * t1901 / 0.668467200e9 - t1054 * t1901 / 0.24654643200e11 + t1058 * t1901 / 0.1017328435200e13 - t1062 * t1901 / 0.46351421276160e14
  t1947 = t1067 * t1901 / 0.2308410703872000e16 - t1071 * t1901 / 0.124654178009088000e18 + t1075 * t1901 / 0.7250540450807808000e19 - t1079 * t1901 / 0.451747958728163328000e21 + t1083 * t1901 / 0.30007722471388191129600e23 - t1087 * t1901 / 0.2116453759156242874368000e25 + t1091 * t1901 / 0.157933692279894426255360000e27 - t1095 * t1901 / 0.12429808430244664033935360000e29 + t1099 * t1901 / 0.1028872779861655483381186560000e31 - t1103 * t1901 / 0.89346308424864345927570161664000e32 + t1107 * t1901 / 0.8121312287389662805908038615040000e34
  t1949 = f.my_piecewise3(t150, 0, t1861)
  t1952 = t222 * t1949
  t1955 = 0.256e3 * t1118 * t1949
  t1971 = f.my_piecewise3(t149, t1924 + t1947, 0.48e2 * t1112 * t1949 + 0.24e2 * t223 * ((0.40e2 * t1952 - t1955) * t230 + t1124 * t1949 * t230 / 0.2e1 - 0.72e2 * t1952 + t1955 + 0.10e2 * t1949 * t126 * t236 - 0.10e2 * t1132 * t1949))
  t1975 = f.my_piecewise3(t259, t1861, 0)
  t2012 = -0.3e1 / 0.1960e4 * t1158 * t1975 + t1164 * t1975 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t1168 * t1975 + t1172 * t1975 / 0.6150144e7 - t1176 * t1975 / 0.210862080e9 + t1180 * t1975 / 0.8272281600e10 - t1184 * t1975 / 0.363245076480e12 + t1188 * t1975 / 0.17589608644608e14 - t1192 * t1975 / 0.929135308308480e15 + t1196 * t1975 / 0.53093446189056000e17 - t1200 * t1975 / 0.3260186194083840000e19 + t1204 * t1975 / 0.213942732873478963200e21 - t1208 * t1975 / 0.14934787515553079623680e23 + t1212 * t1975 / 0.1104659283477977785958400e25 - t1216 * t1975 / 0.86276615005604488937472000e26 + t1220 * t1975 / 0.7093855011571924645969920000e28 - t1224 * t1975 / 0.612397035344843684324573184000e30 + t1228 * t1975 / 0.55373933012154298115575460659200e32
  t2013 = f.my_piecewise3(t259, 0, t1861)
  t2050 = f.my_piecewise3(t258, t2012, 0.8e1 / 0.7e1 * t2013 * t350 + 0.8e1 / 0.7e1 * t317 * ((0.768e3 * t319 * t2013 - 0.2880e4 * t322 * t2013 - 0.1105920e7 * t327 * t2013 + 0.26880e5 * t337 * t2013 - 0.8e1 * t2013) * t333 + t1246 * t2013 * t333 / 0.2e1 + 0.72e2 * t1250 * t2013 + 0.24e2 * t320 * (0.448e3 * t317 * t2013 - 0.5760e4 * t320 * t2013 + 0.30720e5 * t323 * t2013) + 0.240e3 * t1262 * t2013 * t347 - 0.2e1 * t1266 * t331 * t2013))
  t2060 = -t1297 - t49 * t51 * t1856 / 0.18e2
  t2061 = f.my_piecewise3(t367, t2060, 0)
  t2079 = f.my_piecewise3(t367, 0, t2060)
  t2098 = f.my_piecewise3(t366, -t1294 * t2061 / 0.18e2 + t1306 * t2061 / 0.240e3 - t1310 * t2061 / 0.4480e4 + t1314 * t2061 / 0.103680e6 - t1318 * t2061 / 0.2838528e7 + t1322 * t2061 / 0.89456640e8 - t1326 * t2061 / 0.3185049600e10 + t1330 * t2061 / 0.126340300800e12, -0.8e1 / 0.3e1 * t2079 * t409 - 0.8e1 / 0.3e1 * t394 * (-t1336 * t2079 + 0.2e1 * t2079 * t406 + 0.2e1 * t394 * (t1341 * t2079 * t402 / 0.2e1 - 0.4e1 * t1345 * t2079 - t395 * t2079 * t402)))
  t2106 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t1846 * t26 * t456 - t892 + 0.3e1 / 0.8e1 * t5 * t25 * t1441 * (t42 * (t1899 * t147 + 0.35e2 / 0.81e2 * t1971 * t251 * t255 + 0.26329605555555555555555555555555555555555555555556e-1 * t2050 * t52 * t56 * t357) + t362 * t2098 * t439))
  t2107 = -t1842
  t2108 = f.my_piecewise5(t14, 0, t10, 0, t2107)
  t2111 = f.my_piecewise3(t464, 0, 0.4e1 / 0.3e1 * t465 * t2108)
  t2120 = f.my_piecewise3(t474, -s2 / t484 * t471 / 0.8e1, 0)
  t2123 = t476 * t2120
  t2126 = (0.2e1 * t475 * t2120 + 0.9e1 * t2123) * t482
  t2130 = t479 / t481 / t480
  t2131 = t775 * t476
  t2137 = t50 / t501 / t500
  t2140 = 0.1e1 / t486 / t484 / r1
  t2141 = s2 * t2140
  t2142 = t57 * t2141
  t2148 = t69 * t492 / t485 / t493 / t484
  t2150 = -0.40121303703703703703703703703703703703703703703704e0 * t2142 - 0.14346394913206905600000000000000000000000000000000e-1 * t2148
  t2155 = f.my_piecewise5(t84, 0, t82, 0, t2107)
  t2158 = f.my_piecewise3(t505, 0, t1451 * t2155 / 0.3e1)
  t2159 = t1449 * t2158
  t2164 = f.my_piecewise3(t513, 0, -t1446 - t921 * t2137 * t508 * t2150 / 0.180e3 - t921 * t1447 * t2159 / 0.18e2)
  t2165 = f.my_piecewise3(t516, t2164, 0)
  t2183 = f.my_piecewise3(t516, 0, t2164)
  t2202 = f.my_piecewise3(t515, -t1443 * t2165 / 0.18e2 + t1466 * t2165 / 0.240e3 - t1470 * t2165 / 0.4480e4 + t1474 * t2165 / 0.103680e6 - t1478 * t2165 / 0.2838528e7 + t1482 * t2165 / 0.89456640e8 - t1486 * t2165 / 0.3185049600e10 + t1490 * t2165 / 0.126340300800e12, -0.8e1 / 0.3e1 * t2183 * t558 - 0.8e1 / 0.3e1 * t543 * (-t1496 * t2183 + 0.2e1 * t2183 * t555 + 0.2e1 * t543 * (t1501 * t2183 * t551 / 0.2e1 - 0.4e1 * t1505 * t2183 - t544 * t2183 * t551)))
  t2205 = 0.1e1 / t563 / t500
  t2206 = t562 * t2205
  t2209 = f.my_piecewise3(t567, t2164, 0)
  t2232 = -t1522 * t2209 / 0.771114500014776064399349121024000000e36 + t1530 * t2209 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t1533 * t2209 + t1536 * t2209 / 0.1920e4 - 0.3e1 / 0.98560e5 * t1540 * t2209 + t1544 * t2209 / 0.745472e6 - t1547 * t2209 / 0.20643840e8 + t1550 * t2209 / 0.668467200e9 - t1554 * t2209 / 0.24654643200e11 + t1558 * t2209 / 0.1017328435200e13 - t1562 * t2209 / 0.46351421276160e14
  t2255 = t1567 * t2209 / 0.2308410703872000e16 - t1571 * t2209 / 0.124654178009088000e18 + t1575 * t2209 / 0.7250540450807808000e19 - t1579 * t2209 / 0.451747958728163328000e21 + t1583 * t2209 / 0.30007722471388191129600e23 - t1587 * t2209 / 0.2116453759156242874368000e25 + t1591 * t2209 / 0.157933692279894426255360000e27 - t1595 * t2209 / 0.12429808430244664033935360000e29 + t1599 * t2209 / 0.1028872779861655483381186560000e31 - t1603 * t2209 / 0.89346308424864345927570161664000e32 + t1607 * t2209 / 0.8121312287389662805908038615040000e34
  t2257 = f.my_piecewise3(t567, 0, t2164)
  t2260 = t639 * t2257
  t2263 = 0.256e3 * t1618 * t2257
  t2279 = f.my_piecewise3(t566, t2232 + t2255, 0.48e2 * t1612 * t2257 + 0.24e2 * t640 * ((0.40e2 * t2260 - t2263) * t647 + t1624 * t2257 * t647 / 0.2e1 - 0.72e2 * t2260 + t2263 + 0.10e2 * t2257 * t126 * t653 - 0.10e2 * t1632 * t2257))
  t2283 = tau1 * t488
  t2284 = 0.24256886666666666666666666666666666666666666666667e0 * t2283
  t2290 = t667 * t52
  t2292 = 0.1e1 / t668 / t500
  t2293 = t56 * t2292
  t2297 = f.my_piecewise3(t674, t2164, 0)
  t2334 = -0.3e1 / 0.1960e4 * t1644 * t2297 + t1650 * t2297 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t1654 * t2297 + t1658 * t2297 / 0.6150144e7 - t1662 * t2297 / 0.210862080e9 + t1666 * t2297 / 0.8272281600e10 - t1670 * t2297 / 0.363245076480e12 + t1674 * t2297 / 0.17589608644608e14 - t1678 * t2297 / 0.929135308308480e15 + t1682 * t2297 / 0.53093446189056000e17 - t1686 * t2297 / 0.3260186194083840000e19 + t1690 * t2297 / 0.213942732873478963200e21 - t1694 * t2297 / 0.14934787515553079623680e23 + t1698 * t2297 / 0.1104659283477977785958400e25 - t1702 * t2297 / 0.86276615005604488937472000e26 + t1706 * t2297 / 0.7093855011571924645969920000e28 - t1710 * t2297 / 0.612397035344843684324573184000e30 + t1714 * t2297 / 0.55373933012154298115575460659200e32
  t2335 = f.my_piecewise3(t674, 0, t2164)
  t2372 = f.my_piecewise3(t673, t2334, 0.8e1 / 0.7e1 * t2335 * t765 + 0.8e1 / 0.7e1 * t732 * ((0.768e3 * t734 * t2335 - 0.2880e4 * t737 * t2335 - 0.1105920e7 * t742 * t2335 + 0.26880e5 * t752 * t2335 - 0.8e1 * t2335) * t748 + t1732 * t2335 * t748 / 0.2e1 + 0.72e2 * t1736 * t2335 + 0.24e2 * t735 * (0.448e3 * t732 * t2335 - 0.5760e4 * t735 * t2335 + 0.30720e5 * t738 * t2335) + 0.240e3 * t1748 * t2335 * t762 - 0.2e1 * t1752 * t746 * t2335))
  t2388 = 0.6e1 * t2130 * t2123 - t2126
  t2394 = -t1771 - t49 * t51 * t2159 / 0.18e2
  t2395 = f.my_piecewise3(t782, t2394, 0)
  t2413 = f.my_piecewise3(t782, 0, t2394)
  t2432 = f.my_piecewise3(t781, -t1768 * t2395 / 0.18e2 + t1780 * t2395 / 0.240e3 - t1784 * t2395 / 0.4480e4 + t1788 * t2395 / 0.103680e6 - t1792 * t2395 / 0.2838528e7 + t1796 * t2395 / 0.89456640e8 - t1800 * t2395 / 0.3185049600e10 + t1804 * t2395 / 0.126340300800e12, -0.8e1 / 0.3e1 * t2413 * t824 - 0.8e1 / 0.3e1 * t809 * (-t1810 * t2413 + 0.2e1 * t2413 * t821 + 0.2e1 * t809 * (t1815 * t2413 * t817 / 0.2e1 - 0.4e1 * t1819 * t2413 - t810 * t2413 * t817)))
  t2435 = t854 ** 2
  t2436 = t2435 ** 2
  t2437 = t2436 ** 2
  t2439 = 0.1e1 / t2437 / t854
  t2448 = (-0.5e1 / 0.3e1 * t2283 + t2141 / 0.3e1) * t52 * t56
  t2465 = -0.125e3 / 0.39366e5 * t2148 - 0.10e2 / 0.9e1 * t832 * t833 * t2140 + 0.584e3 / 0.405e3 * t843 * (t2448 / 0.4e1 - 0.2e1 / 0.27e2 * t2142) - 0.6e1 * (0.73e2 / 0.1620e4 * t2448 - 0.146e3 / 0.10935e5 * t2142) * t475 * t850 - 0.6e1 * t848 * t2120 * t850 + 0.6e1 * t849 * t2120
  t2472 = t867 * t476
  t2487 = t864 * t2292
  t2493 = t777 * t2439
  t2501 = f.my_piecewise3(t461, 0, -0.3e1 / 0.8e1 * t5 * t2111 * t26 * t870 - t1439 - 0.3e1 / 0.8e1 * t5 * t468 * (-f.p.cam_beta * (t2126 * t775 - 0.6e1 * t2130 * t2131 * t2120 + t483 * (t2202 * t564 - t2206 * t2150 / 0.5e1 + 0.35e2 / 0.81e2 * t2279 * t666 * t670 + 0.35e2 / 0.81e2 * t660 * (t2284 - 0.11279007555555555555555555555555555555555555555555e0 * t2141) * t670 - 0.14e2 / 0.81e2 * t2290 * t2293 * t2150 + 0.26329605555555555555555555555555555555555555555556e-1 * t2372 * t52 * t56 * t772 - 0.70212281481481481481481481481481481481481481481483e-1 * t771 * t2141 * t669 - 0.10531842222222222222222222222222222222222222222222e-1 * t771 * t489 * t2292 * t2150) + t2388 * t828 * t854 + t777 * t2432 * t854 + t829 * t2439 * t2465 / 0.10e2) + t2126 * t867 - 0.6e1 * t2130 * t2472 * t2120 + t483 * (-t2205 * t2150 / 0.5e1 + (-0.11936087851851851851851851851851851851851851851852e1 * t2142 - 0.35e2 / 0.9e1 * (-t2284 - 0.31646617777777777777777777777777777777777777777779e-1 * t2141) * t52 * t56) * t669 / 0.9e1 - 0.2e1 / 0.45e2 * t2487 * t2150) + t2388 * t854 + t2493 * t2465 / 0.10e2))
  vrho_1_ = t460 + t874 + t6 * (t2106 + t2501)
  t2506 = f.my_piecewise3(t33, t28 * t30 / 0.8e1, 0)
  t2509 = t35 * t2506
  t2512 = (0.2e1 * t34 * t2506 + 0.9e1 * t2509) * t41
  t2520 = t69 * s0 * t74
  t2522 = 0.15045488888888888888888888888888888888888888888889e0 * t57 * t62 + 0.53798980924525896000000000000000000000000000000000e-2 * t2520
  t2527 = f.my_piecewise3(t95, 0, -t921 * t924 * t90 * t2522 / 0.180e3)
  t2528 = f.my_piecewise3(t98, t2527, 0)
  t2546 = f.my_piecewise3(t98, 0, t2527)
  t2565 = f.my_piecewise3(t97, -t913 * t2528 / 0.18e2 + t961 * t2528 / 0.240e3 - t965 * t2528 / 0.4480e4 + t969 * t2528 / 0.103680e6 - t973 * t2528 / 0.2838528e7 + t977 * t2528 / 0.89456640e8 - t981 * t2528 / 0.3185049600e10 + t985 * t2528 / 0.126340300800e12, -0.8e1 / 0.3e1 * t2546 * t141 - 0.8e1 / 0.3e1 * t125 * (-t991 * t2546 + 0.2e1 * t2546 * t138 + 0.2e1 * t125 * (t996 * t2546 * t134 / 0.2e1 - 0.4e1 * t1000 * t2546 - t127 * t2546 * t134)))
  t2569 = f.my_piecewise3(t150, t2527, 0)
  t2592 = -t1022 * t2569 / 0.771114500014776064399349121024000000e36 + t1030 * t2569 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t1033 * t2569 + t1036 * t2569 / 0.1920e4 - 0.3e1 / 0.98560e5 * t1040 * t2569 + t1044 * t2569 / 0.745472e6 - t1047 * t2569 / 0.20643840e8 + t1050 * t2569 / 0.668467200e9 - t1054 * t2569 / 0.24654643200e11 + t1058 * t2569 / 0.1017328435200e13 - t1062 * t2569 / 0.46351421276160e14
  t2615 = t1067 * t2569 / 0.2308410703872000e16 - t1071 * t2569 / 0.124654178009088000e18 + t1075 * t2569 / 0.7250540450807808000e19 - t1079 * t2569 / 0.451747958728163328000e21 + t1083 * t2569 / 0.30007722471388191129600e23 - t1087 * t2569 / 0.2116453759156242874368000e25 + t1091 * t2569 / 0.157933692279894426255360000e27 - t1095 * t2569 / 0.12429808430244664033935360000e29 + t1099 * t2569 / 0.1028872779861655483381186560000e31 - t1103 * t2569 / 0.89346308424864345927570161664000e32 + t1107 * t2569 / 0.8121312287389662805908038615040000e34
  t2617 = f.my_piecewise3(t150, 0, t2527)
  t2620 = t222 * t2617
  t2623 = 0.256e3 * t1118 * t2617
  t2639 = f.my_piecewise3(t149, t2592 + t2615, 0.48e2 * t1112 * t2617 + 0.24e2 * t223 * ((0.40e2 * t2620 - t2623) * t230 + t1124 * t2617 * t230 / 0.2e1 - 0.72e2 * t2620 + t2623 + 0.10e2 * t2617 * t126 * t236 - 0.10e2 * t1132 * t2617))
  t2649 = f.my_piecewise3(t259, t2527, 0)
  t2686 = -0.3e1 / 0.1960e4 * t1158 * t2649 + t1164 * t2649 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t1168 * t2649 + t1172 * t2649 / 0.6150144e7 - t1176 * t2649 / 0.210862080e9 + t1180 * t2649 / 0.8272281600e10 - t1184 * t2649 / 0.363245076480e12 + t1188 * t2649 / 0.17589608644608e14 - t1192 * t2649 / 0.929135308308480e15 + t1196 * t2649 / 0.53093446189056000e17 - t1200 * t2649 / 0.3260186194083840000e19 + t1204 * t2649 / 0.213942732873478963200e21 - t1208 * t2649 / 0.14934787515553079623680e23 + t1212 * t2649 / 0.1104659283477977785958400e25 - t1216 * t2649 / 0.86276615005604488937472000e26 + t1220 * t2649 / 0.7093855011571924645969920000e28 - t1224 * t2649 / 0.612397035344843684324573184000e30 + t1228 * t2649 / 0.55373933012154298115575460659200e32
  t2687 = f.my_piecewise3(t259, 0, t2527)
  t2724 = f.my_piecewise3(t258, t2686, 0.8e1 / 0.7e1 * t2687 * t350 + 0.8e1 / 0.7e1 * t317 * ((0.768e3 * t319 * t2687 - 0.2880e4 * t322 * t2687 - 0.1105920e7 * t327 * t2687 + 0.26880e5 * t337 * t2687 - 0.8e1 * t2687) * t333 + t1246 * t2687 * t333 / 0.2e1 + 0.72e2 * t1250 * t2687 + 0.24e2 * t320 * (0.448e3 * t317 * t2687 - 0.5760e4 * t320 * t2687 + 0.30720e5 * t323 * t2687) + 0.240e3 * t1262 * t2687 * t347 - 0.2e1 * t1266 * t331 * t2687))
  t2729 = t56 * t62
  t2741 = 0.6e1 * t907 * t2509 - t2512
  t2759 = 0.125e3 / 0.104976e6 * t2520 + 0.5e1 / 0.12e2 * t417 * t2729 - 0.73e2 / 0.14580e5 * t428 * t52 * t2729 + 0.73e2 / 0.19440e5 * t57 * t62 * t34 * t435 - 0.6e1 * t433 * t2506 * t435 + 0.6e1 * t434 * t2506
  t2785 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-f.p.cam_beta * (t2512 * t360 - 0.6e1 * t907 * t908 * t2506 + t42 * (t2565 * t147 - t1016 * t2522 / 0.5e1 + 0.35e2 / 0.81e2 * t2639 * t251 * t255 + 0.18276169650205761316872427983539094650205761316872e-1 * t243 * t62 * t255 - 0.14e2 / 0.81e2 * t1150 * t1153 * t2522 + 0.26329605555555555555555555555555555555555555555556e-1 * t2724 * t52 * t56 * t357 + 0.26329605555555555555555555555555555555555555555556e-1 * t355 * t2729 * t254 - 0.10531842222222222222222222222222222222222222222222e-1 * t356 * t63 * t1152 * t2522) + t2741 * t413 * t439 + t414 * t1364 * t2759 / 0.10e2) + t2512 * t453 - 0.6e1 * t907 * t1397 * t2506 + t42 * (-t1015 * t2522 / 0.5e1 + 0.44605775205761316872427983539094650205761316872429e-1 * t57 * t62 * t254 - 0.2e1 / 0.45e2 * t1412 * t2522) + t2741 * t439 + t1418 * t2759 / 0.10e2))
  vsigma_0_ = t6 * t2785
  vsigma_1_ = 0.0e0
  t2788 = f.my_piecewise3(t474, t469 * t471 / 0.8e1, 0)
  t2791 = t476 * t2788
  t2794 = (0.2e1 * t475 * t2788 + 0.9e1 * t2791) * t482
  t2802 = t69 * s2 * t496
  t2804 = 0.15045488888888888888888888888888888888888888888889e0 * t57 * t488 + 0.53798980924525896000000000000000000000000000000000e-2 * t2802
  t2809 = f.my_piecewise3(t513, 0, -t921 * t2137 * t508 * t2804 / 0.180e3)
  t2810 = f.my_piecewise3(t516, t2809, 0)
  t2828 = f.my_piecewise3(t516, 0, t2809)
  t2847 = f.my_piecewise3(t515, -t1443 * t2810 / 0.18e2 + t1466 * t2810 / 0.240e3 - t1470 * t2810 / 0.4480e4 + t1474 * t2810 / 0.103680e6 - t1478 * t2810 / 0.2838528e7 + t1482 * t2810 / 0.89456640e8 - t1486 * t2810 / 0.3185049600e10 + t1490 * t2810 / 0.126340300800e12, -0.8e1 / 0.3e1 * t2828 * t558 - 0.8e1 / 0.3e1 * t543 * (-t1496 * t2828 + 0.2e1 * t2828 * t555 + 0.2e1 * t543 * (t1501 * t2828 * t551 / 0.2e1 - 0.4e1 * t1505 * t2828 - t544 * t2828 * t551)))
  t2851 = f.my_piecewise3(t567, t2809, 0)
  t2874 = -t1522 * t2851 / 0.771114500014776064399349121024000000e36 + t1530 * t2851 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t1533 * t2851 + t1536 * t2851 / 0.1920e4 - 0.3e1 / 0.98560e5 * t1540 * t2851 + t1544 * t2851 / 0.745472e6 - t1547 * t2851 / 0.20643840e8 + t1550 * t2851 / 0.668467200e9 - t1554 * t2851 / 0.24654643200e11 + t1558 * t2851 / 0.1017328435200e13 - t1562 * t2851 / 0.46351421276160e14
  t2897 = t1567 * t2851 / 0.2308410703872000e16 - t1571 * t2851 / 0.124654178009088000e18 + t1575 * t2851 / 0.7250540450807808000e19 - t1579 * t2851 / 0.451747958728163328000e21 + t1583 * t2851 / 0.30007722471388191129600e23 - t1587 * t2851 / 0.2116453759156242874368000e25 + t1591 * t2851 / 0.157933692279894426255360000e27 - t1595 * t2851 / 0.12429808430244664033935360000e29 + t1599 * t2851 / 0.1028872779861655483381186560000e31 - t1603 * t2851 / 0.89346308424864345927570161664000e32 + t1607 * t2851 / 0.8121312287389662805908038615040000e34
  t2899 = f.my_piecewise3(t567, 0, t2809)
  t2902 = t639 * t2899
  t2905 = 0.256e3 * t1618 * t2899
  t2921 = f.my_piecewise3(t566, t2874 + t2897, 0.48e2 * t1612 * t2899 + 0.24e2 * t640 * ((0.40e2 * t2902 - t2905) * t647 + t1624 * t2899 * t647 / 0.2e1 - 0.72e2 * t2902 + t2905 + 0.10e2 * t2899 * t126 * t653 - 0.10e2 * t1632 * t2899))
  t2931 = f.my_piecewise3(t674, t2809, 0)
  t2968 = -0.3e1 / 0.1960e4 * t1644 * t2931 + t1650 * t2931 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t1654 * t2931 + t1658 * t2931 / 0.6150144e7 - t1662 * t2931 / 0.210862080e9 + t1666 * t2931 / 0.8272281600e10 - t1670 * t2931 / 0.363245076480e12 + t1674 * t2931 / 0.17589608644608e14 - t1678 * t2931 / 0.929135308308480e15 + t1682 * t2931 / 0.53093446189056000e17 - t1686 * t2931 / 0.3260186194083840000e19 + t1690 * t2931 / 0.213942732873478963200e21 - t1694 * t2931 / 0.14934787515553079623680e23 + t1698 * t2931 / 0.1104659283477977785958400e25 - t1702 * t2931 / 0.86276615005604488937472000e26 + t1706 * t2931 / 0.7093855011571924645969920000e28 - t1710 * t2931 / 0.612397035344843684324573184000e30 + t1714 * t2931 / 0.55373933012154298115575460659200e32
  t2969 = f.my_piecewise3(t674, 0, t2809)
  t3006 = f.my_piecewise3(t673, t2968, 0.8e1 / 0.7e1 * t2969 * t765 + 0.8e1 / 0.7e1 * t732 * ((0.768e3 * t734 * t2969 - 0.2880e4 * t737 * t2969 - 0.1105920e7 * t742 * t2969 + 0.26880e5 * t752 * t2969 - 0.8e1 * t2969) * t748 + t1732 * t2969 * t748 / 0.2e1 + 0.72e2 * t1736 * t2969 + 0.24e2 * t735 * (0.448e3 * t732 * t2969 - 0.5760e4 * t735 * t2969 + 0.30720e5 * t738 * t2969) + 0.240e3 * t1748 * t2969 * t762 - 0.2e1 * t1752 * t746 * t2969))
  t3011 = t56 * t488
  t3023 = 0.6e1 * t2130 * t2791 - t2794
  t3041 = 0.125e3 / 0.104976e6 * t2802 + 0.5e1 / 0.12e2 * t832 * t3011 - 0.73e2 / 0.14580e5 * t843 * t52 * t3011 + 0.73e2 / 0.19440e5 * t57 * t488 * t475 * t850 - 0.6e1 * t848 * t2788 * t850 + 0.6e1 * t849 * t2788
  t3067 = f.my_piecewise3(t461, 0, -0.3e1 / 0.8e1 * t5 * t468 * (-f.p.cam_beta * (t2794 * t775 - 0.6e1 * t2130 * t2131 * t2788 + t483 * (t2847 * t564 - t2206 * t2804 / 0.5e1 + 0.35e2 / 0.81e2 * t2921 * t666 * t670 + 0.18276169650205761316872427983539094650205761316872e-1 * t660 * t488 * t670 - 0.14e2 / 0.81e2 * t2290 * t2293 * t2804 + 0.26329605555555555555555555555555555555555555555556e-1 * t3006 * t52 * t56 * t772 + 0.26329605555555555555555555555555555555555555555556e-1 * t770 * t3011 * t669 - 0.10531842222222222222222222222222222222222222222222e-1 * t771 * t489 * t2292 * t2804) + t3023 * t828 * t854 + t829 * t2439 * t3041 / 0.10e2) + t2794 * t867 - 0.6e1 * t2130 * t2472 * t2788 + t483 * (-t2205 * t2804 / 0.5e1 + 0.44605775205761316872427983539094650205761316872429e-1 * t57 * t488 * t669 - 0.2e1 / 0.45e2 * t2487 * t2804) + t3023 * t854 + t2493 * t3041 / 0.10e2))
  vsigma_2_ = t6 * t3067
  vlapl_0_ = 0.0e0
  vlapl_1_ = 0.0e0
  t3068 = tau0 ** 2
  t3072 = f.my_piecewise3(t33, -t29 / t3068 / 0.8e1, 0)
  t3075 = t35 * t3072
  t3078 = (0.2e1 * t34 * t3072 + 0.9e1 * t3075) * t41
  t3084 = t245 * t52
  t3091 = 0.6e1 * t907 * t3075 - t3078
  t3106 = 0.146e3 / 0.405e3 * t428 * t245 * t57 - 0.73e2 / 0.270e3 * t3084 * t56 * t34 * t435 - 0.6e1 * t433 * t3072 * t435 + 0.6e1 * t434 * t3072
  t3126 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-f.p.cam_beta * (t3078 * t360 - 0.6e1 * t907 * t908 * t3072 - 0.62888224691358024691358024691358024691358024691358e-1 * t42 * t243 * t3084 * t56 * t254 + t3091 * t413 * t439 + t414 * t1364 * t3106 / 0.10e2) + t3078 * t453 - 0.6e1 * t907 * t1397 * t3072 - 0.62888224691358024691358024691358024691358024691358e-1 * t42 * t245 * t255 + t3091 * t439 + t1418 * t3106 / 0.10e2))
  vtau_0_ = t6 * t3126
  t3127 = tau1 ** 2
  t3131 = f.my_piecewise3(t474, -t470 / t3127 / 0.8e1, 0)
  t3134 = t476 * t3131
  t3137 = (0.2e1 * t475 * t3131 + 0.9e1 * t3134) * t482
  t3143 = t662 * t52
  t3150 = 0.6e1 * t2130 * t3134 - t3137
  t3165 = 0.146e3 / 0.405e3 * t843 * t662 * t57 - 0.73e2 / 0.270e3 * t3143 * t56 * t475 * t850 - 0.6e1 * t848 * t3131 * t850 + 0.6e1 * t849 * t3131
  t3185 = f.my_piecewise3(t461, 0, -0.3e1 / 0.8e1 * t5 * t468 * (-f.p.cam_beta * (t3137 * t775 - 0.6e1 * t2130 * t2131 * t3131 - 0.62888224691358024691358024691358024691358024691358e-1 * t483 * t660 * t3143 * t56 * t669 + t3150 * t828 * t854 + t829 * t2439 * t3165 / 0.10e2) + t3137 * t867 - 0.6e1 * t2130 * t2472 * t3131 - 0.62888224691358024691358024691358024691358024691358e-1 * t483 * t662 * t670 + t3150 * t854 + t2493 * t3165 / 0.10e2))
  vtau_1_ = t6 * t3185
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
  tm_lambda = 0.6866

  tm_beta = 79.873

  tm_p = lambda x: (X2S * x) ** 2

  tm_alpha = lambda x, t: (t - x ** 2 / 8) / K_FACTOR_C

  tm_tratio = lambda x, t: jnp.minimum(1.0, x ** 2 / (8 * t))

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  attenuation_erf_f20 = lambda a: 1 + 24 * a ** 2 * ((20 * a ** 2 - 64 * a ** 4) * jnp.exp(-1 / (4 * a ** 2)) - 3 - 36 * a ** 2 + 64 * a ** 4 + 10 * a * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a)))

  attenuation_erf_f30 = lambda a: 1 + 8 / 7 * a * ((-8 * a + 256 * a ** 3 - 576 * a ** 5 + 3840 * a ** 7 - 122880 * a ** 9) * jnp.exp(-1 / (4 * a ** 2)) + 24 * a ** 3 * (-35 + 224 * a ** 2 - 1440 * a ** 4 + 5120 * a ** 6) + 2 * jnp.sqrt(jnp.pi) * (-2 + 60 * a ** 2) * jax.lax.erf(1 / (2 * a)))

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  js18_G = lambda x, t: (3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72) - (t - K_FACTOR_C) + 7 / 18 * (2 * tm_lambda - 1) ** 2 * x ** 2) / K_FACTOR_C

  tm_y = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_R = lambda x, t: 1 + 595 * (2 * tm_lambda - 1) ** 2 * tm_p(x) / 54 - (t - 3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72)) / K_FACTOR_C

  js18_H = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  tm_qtilde = lambda x, t: 9 / 20 * (tm_alpha(x, t) - 1) + 2 * tm_p(x) / 3

  tm_w = lambda x, t: (tm_tratio(x, t) ** 2 + 3 * tm_tratio(x, t) ** 3) / (1 + tm_tratio(x, t) ** 3) ** 2

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  attenuation_erf_f2 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.27, lambda _aval: -1 / 3511556992918352140755776405766144000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 46 + 1 / 33929038000650146833571361325056000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 44 - 1 / 341095116070365837848137621831680000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 42 + 1 / 3573852336994573837102806466560000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 40 - 1 / 39097165634742908368485089280000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 38 + 1 / 447473103488807905221672960000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 36 - 1 / 5369745537516410492682240000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 34 + 1 / 67726520292999771979776000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 32 - 1 / 900231674141645733888000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 30 + 1 / 12648942844388573184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 28 - 1 / 188514051721003008000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 26 + 1 / 2991700272218112000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 24 - 1 / 50785035485184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 22 + 1 / 927028425523200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 20 - 1 / 18311911833600 * (1.0 / jnp.maximum(_aval, 0.27)) ** 18 + 1 / 394474291200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 16 - 1 / 9358540800 * (1.0 / jnp.maximum(_aval, 0.27)) ** 14 + 1 / 247726080 * (1.0 / jnp.maximum(_aval, 0.27)) ** 12 - 1 / 7454720 * (1.0 / jnp.maximum(_aval, 0.27)) ** 10 + 3 / 788480 * (1.0 / jnp.maximum(_aval, 0.27)) ** 8 - 1 / 11520 * (1.0 / jnp.maximum(_aval, 0.27)) ** 6 + 3 / 2240 * (1.0 / jnp.maximum(_aval, 0.27)) ** 4, lambda _aval: attenuation_erf_f20(jnp.minimum(_aval, 0.27)))

  attenuation_erf_f3 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.32, lambda _aval: -1 / 2104209454461863328391867505049600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 38 + 1 / 22046293272414372635684634624000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 36 - 1 / 241191070393445437962977280000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 34 + 1 / 2760851680179343645999104000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 32 - 1 / 33139778504339333578752000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 30 + 1 / 418174050435486229463040 * (1.0 / jnp.maximum(_aval, 0.32)) ** 28 - 1 / 5562511054710453043200 * (1.0 / jnp.maximum(_aval, 0.32)) ** 26 + 1 / 78244468658012160000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 24 - 1 / 1168055816159232000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 22 + 1 / 18582706166169600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 20 - 1 / 316612955602944 * (1.0 / jnp.maximum(_aval, 0.32)) ** 18 + 1 / 5811921223680 * (1.0 / jnp.maximum(_aval, 0.32)) ** 16 - 1 / 115811942400 * (1.0 / jnp.maximum(_aval, 0.32)) ** 14 + 1 / 2530344960 * (1.0 / jnp.maximum(_aval, 0.32)) ** 12 - 1 / 61501440 * (1.0 / jnp.maximum(_aval, 0.32)) ** 10 + 5 / 8515584 * (1.0 / jnp.maximum(_aval, 0.32)) ** 8 - 1 / 56448 * (1.0 / jnp.maximum(_aval, 0.32)) ** 6 + 3 / 7840 * (1.0 / jnp.maximum(_aval, 0.32)) ** 4, lambda _aval: attenuation_erf_f30(jnp.minimum(_aval, 0.32)))

  tm_f0 = lambda x: (1 + 10 * (70 * tm_y(x) / 27) + tm_beta * tm_y(x) ** 2) ** (1 / 10)

  tm_fx_SC = lambda x, t: (1 + 10 * (+(MU_GE + 50 * tm_p(x) / 729) * tm_p(x) + 146 * tm_qtilde(x, t) ** 2 / 2025 - 73 * tm_qtilde(x, t) / 405 * (3 / 5 * tm_tratio(x, t)) * (1 - tm_tratio(x, t)))) ** (1 / 10)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  tm_fx_DME = lambda x, t: 1 / tm_f0(x) ** 2 + 7 * tm_R(x, t) / (9 * tm_f0(x) ** 4)

  js18_A = lambda rs, z, x: jnp.maximum(1e-10, a_cnst * rs / (tm_f0(x) * f.opz_pow_n(z, 1 / 3)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  tm_f = lambda x, u, t: tm_w(x, t) * tm_fx_DME(x, t) + (1 - tm_w(x, t)) * tm_fx_SC(x, t)

  js18_DME_SR = lambda rs, z, x, t: +attenuation_erf(js18_A(rs, z, x)) / tm_f0(x) ** 2 + attenuation_erf_f2(js18_A(rs, z, x)) * 7 * js18_G(x, t) / (9 * tm_f0(x) ** 4) + attenuation_erf_f3(js18_A(rs, z, x)) * 245 * js18_H(x) / (54 * tm_f0(x) ** 4)

  js18_f_SR = lambda rs, z, x, t: tm_w(x, t) * js18_DME_SR(rs, z, x, t) + (1 - tm_w(x, t)) * attenuation_erf(a_cnst * rs / f.opz_pow_n(z, 1 / 3)) * tm_fx_SC(x, t)

  js18_f = lambda rs, z, x, u, t: -f.p.cam_beta * js18_f_SR(rs, z, x, t) + tm_f(x, u, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, js18_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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
  t20 = 0.1e1 / r0
  t21 = s0 * t20
  t22 = 0.1e1 / tau0
  t24 = t21 * t22 / 0.8e1
  t25 = t24 < 0.10e1
  t26 = f.my_piecewise3(t25, t24, 0.10e1)
  t27 = t26 ** 2
  t28 = t27 * t26
  t30 = t27 + 0.3e1 * t28
  t31 = 0.1e1 + t28
  t32 = t31 ** 2
  t33 = 0.1e1 / t32
  t34 = t30 * t33
  t35 = 9 ** (0.1e1 / 0.3e1)
  t36 = t35 ** 2
  t38 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t39 = t38 ** 2
  t40 = t36 * t39
  t41 = t40 * f.p.cam_omega
  t42 = 0.1e1 / t18
  t43 = t3 * t42
  t44 = 6 ** (0.1e1 / 0.3e1)
  t45 = jnp.pi ** 2
  t46 = t45 ** (0.1e1 / 0.3e1)
  t47 = t46 ** 2
  t48 = 0.1e1 / t47
  t49 = t44 * t48
  t50 = 2 ** (0.1e1 / 0.3e1)
  t51 = t50 ** 2
  t52 = s0 * t51
  t53 = r0 ** 2
  t54 = t18 ** 2
  t56 = 0.1e1 / t54 / t53
  t57 = t52 * t56
  t58 = t49 * t57
  t60 = t44 ** 2
  t63 = t60 / t46 / t45
  t64 = s0 ** 2
  t65 = t64 * t50
  t66 = t53 ** 2
  t69 = 0.1e1 / t18 / t66 / r0
  t73 = 0.1e1 + 0.15045488888888888888888888888888888888888888888889e0 * t58 + 0.53798980924525896000000000000000000000000000000000e-2 * t63 * t65 * t69
  t74 = t73 ** (0.1e1 / 0.10e2)
  t76 = f.my_piecewise3(t12, t13, t15)
  t77 = 0.1e1 / t76
  t78 = 0.1e1 / t74 * t77
  t81 = t41 * t43 * t78 / 0.18e2
  t82 = t81 < 0.1e-9
  t83 = f.my_piecewise3(t82, 0.1e-9, t81)
  t84 = 0.135e1 <= t83
  t85 = 0.135e1 < t83
  t86 = f.my_piecewise3(t85, t83, 0.135e1)
  t87 = t86 ** 2
  t90 = t87 ** 2
  t93 = t90 * t87
  t96 = t90 ** 2
  t108 = t96 ** 2
  t112 = f.my_piecewise3(t85, 0.135e1, t83)
  t113 = jnp.sqrt(jnp.pi)
  t114 = 0.1e1 / t112
  t116 = jax.lax.erf(t114 / 0.2e1)
  t118 = t112 ** 2
  t119 = 0.1e1 / t118
  t121 = jnp.exp(-t119 / 0.4e1)
  t122 = t121 - 0.1e1
  t125 = t121 - 0.3e1 / 0.2e1 - 0.2e1 * t118 * t122
  t128 = 0.2e1 * t112 * t125 + t113 * t116
  t132 = f.my_piecewise3(t84, 0.1e1 / t87 / 0.36e2 - 0.1e1 / t90 / 0.960e3 + 0.1e1 / t93 / 0.26880e5 - 0.1e1 / t96 / 0.829440e6 + 0.1e1 / t96 / t87 / 0.28385280e8 - 0.1e1 / t96 / t90 / 0.1073479680e10 + 0.1e1 / t96 / t93 / 0.44590694400e11 - 0.1e1 / t108 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t112 * t128)
  t133 = t73 ** (0.1e1 / 0.5e1)
  t134 = 0.1e1 / t133
  t136 = 0.27e0 <= t83
  t137 = 0.27e0 < t83
  t138 = f.my_piecewise3(t137, t83, 0.27e0)
  t139 = t138 ** 2
  t140 = t139 ** 2
  t141 = t140 ** 2
  t142 = t141 * t140
  t143 = t141 ** 2
  t144 = t143 ** 2
  t148 = t140 * t139
  t149 = t141 * t148
  t159 = t141 * t139
  t174 = 0.1e1 / t144 / t142 / 0.33929038000650146833571361325056000000e38 - 0.1e1 / t144 / t149 / 0.3511556992918352140755776405766144000000e40 + 0.3e1 / 0.2240e4 / t140 - 0.1e1 / t148 / 0.11520e5 + 0.3e1 / 0.788480e6 / t141 - 0.1e1 / t159 / 0.7454720e7 + 0.1e1 / t142 / 0.247726080e9 - 0.1e1 / t149 / 0.9358540800e10 + 0.1e1 / t143 / 0.394474291200e12 - 0.1e1 / t143 / t139 / 0.18311911833600e14 + 0.1e1 / t143 / t140 / 0.927028425523200e15
  t207 = -0.1e1 / t143 / t148 / 0.50785035485184000e17 + 0.1e1 / t143 / t141 / 0.2991700272218112000e19 - 0.1e1 / t143 / t159 / 0.188514051721003008000e21 + 0.1e1 / t143 / t142 / 0.12648942844388573184000e23 - 0.1e1 / t143 / t149 / 0.900231674141645733888000e24 + 0.1e1 / t144 / 0.67726520292999771979776000e26 - 0.1e1 / t144 / t139 / 0.5369745537516410492682240000e28 + 0.1e1 / t144 / t140 / 0.447473103488807905221672960000e30 - 0.1e1 / t144 / t148 / 0.39097165634742908368485089280000e32 + 0.1e1 / t144 / t141 / 0.3573852336994573837102806466560000e34 - 0.1e1 / t144 / t159 / 0.341095116070365837848137621831680000e36
  t209 = f.my_piecewise3(t137, 0.27e0, t83)
  t210 = t209 ** 2
  t212 = t210 ** 2
  t213 = 0.64e2 * t212
  t214 = 0.20e2 * t210 - t213
  t217 = jnp.exp(-0.1e1 / t210 / 0.4e1)
  t221 = 0.1e1 / t209
  t223 = jax.lax.erf(t221 / 0.2e1)
  t226 = 0.10e2 * t209 * t113 * t223 + t214 * t217 - 0.36e2 * t210 + t213 - 0.3e1
  t230 = f.my_piecewise3(t136, t174 + t207, 0.24e2 * t210 * t226 + 0.1e1)
  t231 = tau0 * t51
  t233 = 0.1e1 / t54 / r0
  t234 = t231 * t233
  t235 = 0.14554132000000000000000000000000000000000000000000e0 * t234
  t236 = t60 * t47
  t239 = -t235 + 0.4366239600000000000000000000000000000000000000000e-1 * t236 + 0.42296278333333333333333333333333333333333333333333e-1 * t57
  t240 = t230 * t239
  t241 = t133 ** 2
  t242 = 0.1e1 / t241
  t243 = t49 * t242
  t246 = 0.32e0 <= t83
  t247 = 0.32e0 < t83
  t248 = f.my_piecewise3(t247, t83, 0.32e0)
  t249 = t248 ** 2
  t250 = t249 ** 2
  t253 = t250 * t249
  t256 = t250 ** 2
  t259 = t256 * t249
  t262 = t256 * t250
  t265 = t256 * t253
  t268 = t256 ** 2
  t292 = t268 ** 2
  t304 = 0.3e1 / 0.7840e4 / t250 - 0.1e1 / t253 / 0.56448e5 + 0.5e1 / 0.8515584e7 / t256 - 0.1e1 / t259 / 0.61501440e8 + 0.1e1 / t262 / 0.2530344960e10 - 0.1e1 / t265 / 0.115811942400e12 + 0.1e1 / t268 / 0.5811921223680e13 - 0.1e1 / t268 / t249 / 0.316612955602944e15 + 0.1e1 / t268 / t250 / 0.18582706166169600e17 - 0.1e1 / t268 / t253 / 0.1168055816159232000e19 + 0.1e1 / t268 / t256 / 0.78244468658012160000e20 - 0.1e1 / t268 / t259 / 0.5562511054710453043200e22 + 0.1e1 / t268 / t262 / 0.418174050435486229463040e24 - 0.1e1 / t268 / t265 / 0.33139778504339333578752000e26 + 0.1e1 / t292 / 0.2760851680179343645999104000e28 - 0.1e1 / t292 / t249 / 0.241191070393445437962977280000e30 + 0.1e1 / t292 / t250 / 0.22046293272414372635684634624000e32 - 0.1e1 / t292 / t253 / 0.2104209454461863328391867505049600e34
  t305 = f.my_piecewise3(t247, 0.32e0, t83)
  t307 = t305 ** 2
  t308 = t307 * t305
  t310 = t307 ** 2
  t311 = t310 * t305
  t315 = t310 ** 2
  t318 = -0.122880e6 * t315 * t305 + 0.3840e4 * t310 * t308 - 0.8e1 * t305 + 0.256e3 * t308 - 0.576e3 * t311
  t319 = 0.1e1 / t307
  t321 = jnp.exp(-t319 / 0.4e1)
  t325 = t310 * t307
  t327 = -0.35e2 + 0.224e3 * t307 - 0.1440e4 * t310 + 0.5120e4 * t325
  t331 = -0.2e1 + 0.60e2 * t307
  t335 = jax.lax.erf(0.1e1 / t305 / 0.2e1)
  t338 = 0.2e1 * t113 * t331 * t335 + 0.24e2 * t308 * t327 + t318 * t321
  t342 = f.my_piecewise3(t246, t304, 0.1e1 + 0.8e1 / 0.7e1 * t305 * t338)
  t343 = t342 * t44
  t344 = t343 * t48
  t346 = t52 * t56 * t242
  t349 = t132 * t134 + 0.35e2 / 0.81e2 * t240 * t243 + 0.26329605555555555555555555555555555555555555555556e-1 * t344 * t346
  t351 = 0.1e1 - t34
  t354 = t41 * t43 * t77 / 0.18e2
  t355 = 0.135e1 <= t354
  t356 = 0.135e1 < t354
  t357 = f.my_piecewise3(t356, t354, 0.135e1)
  t358 = t357 ** 2
  t361 = t358 ** 2
  t364 = t361 * t358
  t367 = t361 ** 2
  t379 = t367 ** 2
  t383 = f.my_piecewise3(t356, 0.135e1, t354)
  t384 = 0.1e1 / t383
  t386 = jax.lax.erf(t384 / 0.2e1)
  t388 = t383 ** 2
  t389 = 0.1e1 / t388
  t391 = jnp.exp(-t389 / 0.4e1)
  t392 = t391 - 0.1e1
  t395 = t391 - 0.3e1 / 0.2e1 - 0.2e1 * t388 * t392
  t398 = t113 * t386 + 0.2e1 * t383 * t395
  t402 = f.my_piecewise3(t355, 0.1e1 / t358 / 0.36e2 - 0.1e1 / t361 / 0.960e3 + 0.1e1 / t364 / 0.26880e5 - 0.1e1 / t367 / 0.829440e6 + 0.1e1 / t367 / t358 / 0.28385280e8 - 0.1e1 / t367 / t361 / 0.1073479680e10 + 0.1e1 / t367 / t364 / 0.44590694400e11 - 0.1e1 / t379 / 0.2021444812800e13, 0.1e1 - 0.8e1 / 0.3e1 * t383 * t398)
  t403 = t351 * t402
  t406 = (0.10e2 / 0.81e2 + 0.25e2 / 0.8748e4 * t58) * t44
  t407 = t406 * t48
  t413 = (t234 - t57 / 0.8e1) * t44 * t48
  t416 = t413 / 0.4e1 - 0.9e1 / 0.20e2 + t58 / 0.36e2
  t417 = t416 ** 2
  t421 = 0.73e2 / 0.1620e4 * t413 - 0.73e2 / 0.900e3 + 0.73e2 / 0.14580e5 * t58
  t422 = t421 * t26
  t423 = 0.1e1 - t26
  t427 = (0.1e1 + 0.5e1 / 0.12e2 * t407 * t57 + 0.292e3 / 0.405e3 * t417 - 0.6e1 * t422 * t423) ** (0.1e1 / 0.10e2)
  t438 = 0.7e1 + 0.44760329444444444444444444444444444444444444444445e0 * t58 - 0.35e2 / 0.9e1 * (t235 + 0.25633760400000000000000000000000000000000000000000e0 * t236 + 0.11867481666666666666666666666666666666666666666667e-1 * t57) * t44 * t48
  t441 = t134 + t438 * t242 / 0.9e1
  t444 = -f.p.cam_beta * (t34 * t349 + t403 * t427) + t34 * t441 + t351 * t427
  t448 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t444)
  t458 = f.my_piecewise3(t25, -s0 / t53 * t22 / 0.8e1, 0)
  t461 = t27 * t458
  t464 = (0.2e1 * t26 * t458 + 0.9e1 * t461) * t33
  t468 = t30 / t32 / t31
  t469 = t349 * t27
  t473 = t87 * t86
  t474 = 0.1e1 / t473
  t477 = t3 / t18 / r0
  t482 = t40 * f.p.cam_omega * t3
  t485 = t42 / t74 / t73
  t488 = 0.1e1 / t54 / t53 / r0
  t489 = t52 * t488
  t490 = t49 * t489
  t496 = t63 * t65 / t18 / t66 / t53
  t498 = -0.40121303703703703703703703703703703703703703703704e0 * t490 - 0.28692789826413811200000000000000000000000000000000e-1 * t496
  t504 = f.my_piecewise3(t82, 0, -t41 * t477 * t78 / 0.54e2 - t482 * t485 * t77 * t498 / 0.180e3)
  t505 = f.my_piecewise3(t85, t504, 0)
  t508 = t90 * t86
  t509 = 0.1e1 / t508
  t512 = t90 * t473
  t513 = 0.1e1 / t512
  t517 = 0.1e1 / t96 / t86
  t521 = 0.1e1 / t96 / t473
  t525 = 0.1e1 / t96 / t508
  t529 = 0.1e1 / t96 / t512
  t533 = 0.1e1 / t108 / t86
  t537 = f.my_piecewise3(t85, 0, t504)
  t539 = t121 * t119
  t544 = 0.1e1 / t118 / t112
  t548 = t112 * t122
  t560 = f.my_piecewise3(t84, -t474 * t505 / 0.18e2 + t509 * t505 / 0.240e3 - t513 * t505 / 0.4480e4 + t517 * t505 / 0.103680e6 - t521 * t505 / 0.2838528e7 + t525 * t505 / 0.89456640e8 - t529 * t505 / 0.3185049600e10 + t533 * t505 / 0.126340300800e12, -0.8e1 / 0.3e1 * t537 * t128 - 0.8e1 / 0.3e1 * t112 * (-t539 * t537 + 0.2e1 * t537 * t125 + 0.2e1 * t112 * (t544 * t537 * t121 / 0.2e1 - 0.4e1 * t548 * t537 - t114 * t537 * t121)))
  t563 = 0.1e1 / t133 / t73
  t564 = t132 * t563
  t567 = t140 * t138
  t568 = t141 * t567
  t570 = 0.1e1 / t144 / t568
  t571 = f.my_piecewise3(t137, t504, 0)
  t574 = t139 * t138
  t575 = t140 * t574
  t576 = t141 * t575
  t578 = 0.1e1 / t144 / t576
  t581 = 0.1e1 / t567
  t584 = 0.1e1 / t575
  t587 = t141 * t138
  t588 = 0.1e1 / t587
  t591 = t141 * t574
  t592 = 0.1e1 / t591
  t595 = 0.1e1 / t568
  t598 = 0.1e1 / t576
  t602 = 0.1e1 / t143 / t138
  t606 = 0.1e1 / t143 / t574
  t610 = 0.1e1 / t143 / t567
  t613 = -t570 * t571 / 0.771114500014776064399349121024000000e36 + t578 * t571 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t581 * t571 + t584 * t571 / 0.1920e4 - 0.3e1 / 0.98560e5 * t588 * t571 + t592 * t571 / 0.745472e6 - t595 * t571 / 0.20643840e8 + t598 * t571 / 0.668467200e9 - t602 * t571 / 0.24654643200e11 + t606 * t571 / 0.1017328435200e13 - t610 * t571 / 0.46351421276160e14
  t615 = 0.1e1 / t143 / t575
  t619 = 0.1e1 / t143 / t587
  t623 = 0.1e1 / t143 / t591
  t627 = 0.1e1 / t143 / t568
  t631 = 0.1e1 / t143 / t576
  t635 = 0.1e1 / t144 / t138
  t639 = 0.1e1 / t144 / t574
  t643 = 0.1e1 / t144 / t567
  t647 = 0.1e1 / t144 / t575
  t651 = 0.1e1 / t144 / t587
  t655 = 0.1e1 / t144 / t591
  t658 = t615 * t571 / 0.2308410703872000e16 - t619 * t571 / 0.124654178009088000e18 + t623 * t571 / 0.7250540450807808000e19 - t627 * t571 / 0.451747958728163328000e21 + t631 * t571 / 0.30007722471388191129600e23 - t635 * t571 / 0.2116453759156242874368000e25 + t639 * t571 / 0.157933692279894426255360000e27 - t643 * t571 / 0.12429808430244664033935360000e29 + t647 * t571 / 0.1028872779861655483381186560000e31 - t651 * t571 / 0.89346308424864345927570161664000e32 + t655 * t571 / 0.8121312287389662805908038615040000e34
  t660 = t209 * t226
  t661 = f.my_piecewise3(t137, 0, t504)
  t664 = t209 * t661
  t666 = t210 * t209
  t668 = 0.256e3 * t666 * t661
  t672 = t214 / t666
  t680 = t221 * t217
  t687 = f.my_piecewise3(t136, t613 + t658, 0.48e2 * t660 * t661 + 0.24e2 * t210 * ((0.40e2 * t664 - t668) * t217 + t672 * t661 * t217 / 0.2e1 - 0.72e2 * t664 + t668 + 0.10e2 * t661 * t113 * t223 - 0.10e2 * t680 * t661))
  t691 = t231 * t56
  t692 = 0.24256886666666666666666666666666666666666666666667e0 * t691
  t698 = t240 * t44
  t700 = 0.1e1 / t241 / t73
  t701 = t48 * t700
  t705 = t250 * t248
  t706 = 0.1e1 / t705
  t707 = f.my_piecewise3(t247, t504, 0)
  t710 = t249 * t248
  t711 = t250 * t710
  t712 = 0.1e1 / t711
  t715 = t256 * t248
  t716 = 0.1e1 / t715
  t719 = t256 * t710
  t720 = 0.1e1 / t719
  t723 = t256 * t705
  t724 = 0.1e1 / t723
  t727 = t256 * t711
  t728 = 0.1e1 / t727
  t732 = 0.1e1 / t268 / t248
  t736 = 0.1e1 / t268 / t710
  t740 = 0.1e1 / t268 / t705
  t744 = 0.1e1 / t268 / t711
  t748 = 0.1e1 / t268 / t715
  t752 = 0.1e1 / t268 / t719
  t756 = 0.1e1 / t268 / t723
  t760 = 0.1e1 / t268 / t727
  t764 = 0.1e1 / t292 / t248
  t768 = 0.1e1 / t292 / t710
  t772 = 0.1e1 / t292 / t705
  t776 = 0.1e1 / t292 / t711
  t779 = -0.3e1 / 0.1960e4 * t706 * t707 + t712 * t707 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t716 * t707 + t720 * t707 / 0.6150144e7 - t724 * t707 / 0.210862080e9 + t728 * t707 / 0.8272281600e10 - t732 * t707 / 0.363245076480e12 + t736 * t707 / 0.17589608644608e14 - t740 * t707 / 0.929135308308480e15 + t744 * t707 / 0.53093446189056000e17 - t748 * t707 / 0.3260186194083840000e19 + t752 * t707 / 0.213942732873478963200e21 - t756 * t707 / 0.14934787515553079623680e23 + t760 * t707 / 0.1104659283477977785958400e25 - t764 * t707 / 0.86276615005604488937472000e26 + t768 * t707 / 0.7093855011571924645969920000e28 - t772 * t707 / 0.612397035344843684324573184000e30 + t776 * t707 / 0.55373933012154298115575460659200e32
  t780 = f.my_piecewise3(t247, 0, t504)
  t794 = t318 / t308
  t798 = t307 * t327
  t810 = t113 * t305
  t814 = t331 * t321
  t822 = f.my_piecewise3(t246, t779, 0.8e1 / 0.7e1 * t780 * t338 + 0.8e1 / 0.7e1 * t305 * ((0.768e3 * t307 * t780 - 0.2880e4 * t310 * t780 - 0.1105920e7 * t315 * t780 + 0.26880e5 * t325 * t780 - 0.8e1 * t780) * t321 + t794 * t780 * t321 / 0.2e1 + 0.72e2 * t798 * t780 + 0.24e2 * t308 * (0.448e3 * t305 * t780 - 0.5760e4 * t308 * t780 + 0.30720e5 * t311 * t780) + 0.240e3 * t810 * t780 * t335 - 0.2e1 * t814 * t319 * t780))
  t832 = t343 * t48 * s0
  t833 = t51 * t56
  t842 = 0.6e1 * t468 * t461 - t464
  t845 = t358 * t357
  t849 = t41 * t477 * t77 / 0.54e2
  t850 = f.my_piecewise3(t356, -t849, 0)
  t853 = t361 * t357
  t857 = t361 * t845
  t882 = f.my_piecewise3(t356, 0, -t849)
  t905 = f.my_piecewise3(t355, -0.1e1 / t845 * t850 / 0.18e2 + 0.1e1 / t853 * t850 / 0.240e3 - 0.1e1 / t857 * t850 / 0.4480e4 + 0.1e1 / t367 / t357 * t850 / 0.103680e6 - 0.1e1 / t367 / t845 * t850 / 0.2838528e7 + 0.1e1 / t367 / t853 * t850 / 0.89456640e8 - 0.1e1 / t367 / t857 * t850 / 0.3185049600e10 + 0.1e1 / t379 / t357 * t850 / 0.126340300800e12, -0.8e1 / 0.3e1 * t882 * t398 - 0.8e1 / 0.3e1 * t383 * (-t391 * t389 * t882 + 0.2e1 * t882 * t395 + 0.2e1 * t383 * (0.1e1 / t388 / t383 * t882 * t391 / 0.2e1 - 0.4e1 * t383 * t392 * t882 - t384 * t882 * t391)))
  t908 = t427 ** 2
  t909 = t908 ** 2
  t910 = t909 ** 2
  t912 = 0.1e1 / t910 / t427
  t920 = (-0.5e1 / 0.3e1 * t691 + t489 / 0.3e1) * t44 * t48
  t937 = -0.125e3 / 0.19683e5 * t496 - 0.10e2 / 0.9e1 * t407 * t489 + 0.584e3 / 0.405e3 * t416 * (t920 / 0.4e1 - 0.2e1 / 0.27e2 * t490) - 0.6e1 * (0.73e2 / 0.1620e4 * t920 - 0.146e3 / 0.10935e5 * t490) * t26 * t423 - 0.6e1 * t421 * t458 * t423 + 0.6e1 * t422 * t458
  t944 = t441 * t27
  t959 = t438 * t700
  t965 = t351 * t912
  t973 = f.my_piecewise3(t2, 0, -t6 * t17 / t54 * t444 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (-f.p.cam_beta * (t464 * t349 - 0.6e1 * t468 * t469 * t458 + t34 * (t560 * t134 - t564 * t498 / 0.5e1 + 0.35e2 / 0.81e2 * t687 * t239 * t243 + 0.35e2 / 0.81e2 * t230 * (t692 - 0.11279007555555555555555555555555555555555555555555e0 * t489) * t243 - 0.14e2 / 0.81e2 * t698 * t701 * t498 + 0.26329605555555555555555555555555555555555555555556e-1 * t822 * t44 * t48 * t346 - 0.70212281481481481481481481481481481481481481481483e-1 * t344 * t52 * t488 * t242 - 0.10531842222222222222222222222222222222222222222222e-1 * t832 * t833 * t700 * t498) + t842 * t402 * t427 + t351 * t905 * t427 + t403 * t912 * t937 / 0.10e2) + t464 * t441 - 0.6e1 * t468 * t944 * t458 + t34 * (-t563 * t498 / 0.5e1 + (-0.11936087851851851851851851851851851851851851851852e1 * t490 - 0.35e2 / 0.9e1 * (-t692 - 0.31646617777777777777777777777777777777777777777779e-1 * t489) * t44 * t48) * t242 / 0.9e1 - 0.2e1 / 0.45e2 * t959 * t498) + t842 * t427 + t965 * t937 / 0.10e2))
  vrho_0_ = 0.2e1 * r0 * t973 + 0.2e1 * t448
  t978 = f.my_piecewise3(t25, t20 * t22 / 0.8e1, 0)
  t981 = t27 * t978
  t984 = (0.2e1 * t26 * t978 + 0.9e1 * t981) * t33
  t993 = t63 * s0 * t50 * t69
  t995 = 0.15045488888888888888888888888888888888888888888889e0 * t49 * t833 + 0.10759796184905179200000000000000000000000000000000e-1 * t993
  t1000 = f.my_piecewise3(t82, 0, -t482 * t485 * t77 * t995 / 0.180e3)
  t1001 = f.my_piecewise3(t85, t1000, 0)
  t1019 = f.my_piecewise3(t85, 0, t1000)
  t1038 = f.my_piecewise3(t84, -t474 * t1001 / 0.18e2 + t509 * t1001 / 0.240e3 - t513 * t1001 / 0.4480e4 + t517 * t1001 / 0.103680e6 - t521 * t1001 / 0.2838528e7 + t525 * t1001 / 0.89456640e8 - t529 * t1001 / 0.3185049600e10 + t533 * t1001 / 0.126340300800e12, -0.8e1 / 0.3e1 * t1019 * t128 - 0.8e1 / 0.3e1 * t112 * (-t539 * t1019 + 0.2e1 * t1019 * t125 + 0.2e1 * t112 * (t544 * t1019 * t121 / 0.2e1 - 0.4e1 * t548 * t1019 - t114 * t1019 * t121)))
  t1042 = f.my_piecewise3(t137, t1000, 0)
  t1065 = -t570 * t1042 / 0.771114500014776064399349121024000000e36 + t578 * t1042 / 0.76338195498225046538169052299264000000e38 - 0.3e1 / 0.560e3 * t581 * t1042 + t584 * t1042 / 0.1920e4 - 0.3e1 / 0.98560e5 * t588 * t1042 + t592 * t1042 / 0.745472e6 - t595 * t1042 / 0.20643840e8 + t598 * t1042 / 0.668467200e9 - t602 * t1042 / 0.24654643200e11 + t606 * t1042 / 0.1017328435200e13 - t610 * t1042 / 0.46351421276160e14
  t1088 = t615 * t1042 / 0.2308410703872000e16 - t619 * t1042 / 0.124654178009088000e18 + t623 * t1042 / 0.7250540450807808000e19 - t627 * t1042 / 0.451747958728163328000e21 + t631 * t1042 / 0.30007722471388191129600e23 - t635 * t1042 / 0.2116453759156242874368000e25 + t639 * t1042 / 0.157933692279894426255360000e27 - t643 * t1042 / 0.12429808430244664033935360000e29 + t647 * t1042 / 0.1028872779861655483381186560000e31 - t651 * t1042 / 0.89346308424864345927570161664000e32 + t655 * t1042 / 0.8121312287389662805908038615040000e34
  t1090 = f.my_piecewise3(t137, 0, t1000)
  t1093 = t209 * t1090
  t1096 = 0.256e3 * t666 * t1090
  t1112 = f.my_piecewise3(t136, t1065 + t1088, 0.48e2 * t660 * t1090 + 0.24e2 * t210 * ((0.40e2 * t1093 - t1096) * t217 + t672 * t1090 * t217 / 0.2e1 - 0.72e2 * t1093 + t1096 + 0.10e2 * t1090 * t113 * t223 - 0.10e2 * t680 * t1090))
  t1116 = t230 * t51
  t1123 = f.my_piecewise3(t247, t1000, 0)
  t1160 = -0.3e1 / 0.1960e4 * t706 * t1123 + t712 * t1123 / 0.9408e4 - 0.5e1 / 0.1064448e7 * t716 * t1123 + t720 * t1123 / 0.6150144e7 - t724 * t1123 / 0.210862080e9 + t728 * t1123 / 0.8272281600e10 - t732 * t1123 / 0.363245076480e12 + t736 * t1123 / 0.17589608644608e14 - t740 * t1123 / 0.929135308308480e15 + t744 * t1123 / 0.53093446189056000e17 - t748 * t1123 / 0.3260186194083840000e19 + t752 * t1123 / 0.213942732873478963200e21 - t756 * t1123 / 0.14934787515553079623680e23 + t760 * t1123 / 0.1104659283477977785958400e25 - t764 * t1123 / 0.86276615005604488937472000e26 + t768 * t1123 / 0.7093855011571924645969920000e28 - t772 * t1123 / 0.612397035344843684324573184000e30 + t776 * t1123 / 0.55373933012154298115575460659200e32
  t1161 = f.my_piecewise3(t247, 0, t1000)
  t1198 = f.my_piecewise3(t246, t1160, 0.8e1 / 0.7e1 * t1161 * t338 + 0.8e1 / 0.7e1 * t305 * ((0.768e3 * t307 * t1161 - 0.2880e4 * t310 * t1161 - 0.1105920e7 * t315 * t1161 + 0.26880e5 * t325 * t1161 - 0.8e1 * t1161) * t321 + t794 * t1161 * t321 / 0.2e1 + 0.72e2 * t798 * t1161 + 0.24e2 * t308 * (0.448e3 * t305 * t1161 - 0.5760e4 * t308 * t1161 + 0.30720e5 * t311 * t1161) + 0.240e3 * t810 * t1161 * t335 - 0.2e1 * t814 * t319 * t1161))
  t1203 = t833 * t242
  t1214 = 0.6e1 * t468 * t981 - t984
  t1219 = t48 * t51 * t56
  t1235 = 0.125e3 / 0.52488e5 * t993 + 0.5e1 / 0.12e2 * t406 * t1219 - 0.73e2 / 0.14580e5 * t416 * t44 * t1219 + 0.73e2 / 0.19440e5 * t49 * t51 * t56 * t26 * t423 - 0.6e1 * t421 * t978 * t423 + 0.6e1 * t422 * t978
  t1260 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-f.p.cam_beta * (t984 * t349 - 0.6e1 * t468 * t469 * t978 + t34 * (t1038 * t134 - t564 * t995 / 0.5e1 + 0.35e2 / 0.81e2 * t1112 * t239 * t243 + 0.18276169650205761316872427983539094650205761316872e-1 * t1116 * t56 * t243 - 0.14e2 / 0.81e2 * t698 * t701 * t995 + 0.26329605555555555555555555555555555555555555555556e-1 * t1198 * t44 * t48 * t346 + 0.26329605555555555555555555555555555555555555555556e-1 * t344 * t1203 - 0.10531842222222222222222222222222222222222222222222e-1 * t832 * t833 * t700 * t995) + t1214 * t402 * t427 + t403 * t912 * t1235 / 0.10e2) + t984 * t441 - 0.6e1 * t468 * t944 * t978 + t34 * (-t563 * t995 / 0.5e1 + 0.44605775205761316872427983539094650205761316872429e-1 * t49 * t1203 - 0.2e1 / 0.45e2 * t959 * t995) + t1214 * t427 + t965 * t1235 / 0.10e2))
  vsigma_0_ = 0.2e1 * r0 * t1260
  vlapl_0_ = 0.0e0
  t1262 = tau0 ** 2
  t1266 = f.my_piecewise3(t25, -t21 / t1262 / 0.8e1, 0)
  t1269 = t27 * t1266
  t1272 = (0.2e1 * t26 * t1266 + 0.9e1 * t1269) * t33
  t1278 = t233 * t44
  t1280 = t1278 * t48 * t242
  t1285 = 0.6e1 * t468 * t1269 - t1272
  t1303 = 0.146e3 / 0.405e3 * t416 * t51 * t1278 * t48 - 0.73e2 / 0.270e3 * t51 * t233 * t44 * t48 * t26 * t423 - 0.6e1 * t421 * t1266 * t423 + 0.6e1 * t422 * t1266
  t1323 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-f.p.cam_beta * (t1272 * t349 - 0.6e1 * t468 * t469 * t1266 - 0.62888224691358024691358024691358024691358024691358e-1 * t34 * t1116 * t1280 + t1285 * t402 * t427 + t403 * t912 * t1303 / 0.10e2) + t1272 * t441 - 0.6e1 * t468 * t944 * t1266 - 0.62888224691358024691358024691358024691358024691358e-1 * t34 * t51 * t1280 + t1285 * t427 + t965 * t1303 / 0.10e2))
  vtau_0_ = 0.2e1 * r0 * t1323
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vsigma_0_ = _b(vsigma_0_)
  vlapl_0_ = _b(vlapl_0_)
  vtau_0_ = _b(vtau_0_)
  res = {'vrho': vrho_0_, 'vsigma': vsigma_0_, 'vlapl': vlapl_0_, 'vtau':  vtau_0_}
  return res

def _energy_unpol_sum(p, r, s=None, l=None, tau=None):
  val = unpol(p, r, s, l, tau)
  import jax.numpy as jnp
  import jax.scipy.special as jsp_special
  import scipy.special as sp_special
  return jnp.sum(val)

def unpol_fxc(p, r, s=None, l=None, tau=None):
  import jax
  v2rho2 = jax.jacfwd(jax.grad(_energy_unpol_sum, argnums=1), argnums=1)(p, r, s, l, tau)
  return {'v2rho2': v2rho2}

def unpol_kxc(p, r, s=None, l=None, tau=None):
  import jax
  d1 = jax.grad(_energy_unpol_sum, argnums=1)
  d2 = jax.jacfwd(d1, argnums=1)
  d3 = jax.jacfwd(lambda pp, rr, ss, ll=None, tt=None: d2(pp, rr, ss, ll, tt), argnums=1)
  v3rho3 = d3(p, r, s, l, tau)
  return {'v3rho3': v3rho3}

def unpol_lxc(p, r, s=None, l=None, tau=None):
  import jax
  d1 = jax.grad(_energy_unpol_sum, argnums=1)
  d2 = jax.jacfwd(d1, argnums=1)
  d3 = jax.jacfwd(lambda pp, rr, ss=None, ll=None, tt=None: d2(pp, rr, ss, ll, tt), argnums=1)
  d4 = jax.jacfwd(lambda pp, rr, ss=None, ll=None, tt=None: d3(pp, rr, ss, ll, tt), argnums=1)
  v4rho4 = d4(p, r, s, l, tau)
  return {'v4rho4': v4rho4}
