"""Generated from hyb_mgga_x_pjs18.mpl."""

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
  tm_lambda = 0.6866

  tm_beta = 79.873

  tm_p = lambda x: (X2S * x) ** 2

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  attenuation_erf_f20 = lambda a: 1 + 24 * a ** 2 * ((20 * a ** 2 - 64 * a ** 4) * jnp.exp(-1 / (4 * a ** 2)) - 3 - 36 * a ** 2 + 64 * a ** 4 + 10 * a * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a)))

  attenuation_erf_f30 = lambda a: 1 + 8 / 7 * a * ((-8 * a + 256 * a ** 3 - 576 * a ** 5 + 3840 * a ** 7 - 122880 * a ** 9) * jnp.exp(-1 / (4 * a ** 2)) + 24 * a ** 3 * (-35 + 224 * a ** 2 - 1440 * a ** 4 + 5120 * a ** 6) + 2 * jnp.sqrt(jnp.pi) * (-2 + 60 * a ** 2) * jax.lax.erf(1 / (2 * a)))

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  js18_G = lambda x, t: (3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72) - (t - K_FACTOR_C) + 7 / 18 * (2 * tm_lambda - 1) ** 2 * x ** 2) / K_FACTOR_C

  tm_y = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  js18_H = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  attenuation_erf_f2 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.27, lambda _aval: -1 / 3511556992918352140755776405766144000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 46 + 1 / 33929038000650146833571361325056000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 44 - 1 / 341095116070365837848137621831680000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 42 + 1 / 3573852336994573837102806466560000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 40 - 1 / 39097165634742908368485089280000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 38 + 1 / 447473103488807905221672960000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 36 - 1 / 5369745537516410492682240000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 34 + 1 / 67726520292999771979776000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 32 - 1 / 900231674141645733888000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 30 + 1 / 12648942844388573184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 28 - 1 / 188514051721003008000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 26 + 1 / 2991700272218112000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 24 - 1 / 50785035485184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 22 + 1 / 927028425523200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 20 - 1 / 18311911833600 * (1.0 / jnp.maximum(_aval, 0.27)) ** 18 + 1 / 394474291200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 16 - 1 / 9358540800 * (1.0 / jnp.maximum(_aval, 0.27)) ** 14 + 1 / 247726080 * (1.0 / jnp.maximum(_aval, 0.27)) ** 12 - 1 / 7454720 * (1.0 / jnp.maximum(_aval, 0.27)) ** 10 + 3 / 788480 * (1.0 / jnp.maximum(_aval, 0.27)) ** 8 - 1 / 11520 * (1.0 / jnp.maximum(_aval, 0.27)) ** 6 + 3 / 2240 * (1.0 / jnp.maximum(_aval, 0.27)) ** 4, lambda _aval: attenuation_erf_f20(jnp.minimum(_aval, 0.27)))

  attenuation_erf_f3 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.32, lambda _aval: -1 / 2104209454461863328391867505049600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 38 + 1 / 22046293272414372635684634624000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 36 - 1 / 241191070393445437962977280000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 34 + 1 / 2760851680179343645999104000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 32 - 1 / 33139778504339333578752000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 30 + 1 / 418174050435486229463040 * (1.0 / jnp.maximum(_aval, 0.32)) ** 28 - 1 / 5562511054710453043200 * (1.0 / jnp.maximum(_aval, 0.32)) ** 26 + 1 / 78244468658012160000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 24 - 1 / 1168055816159232000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 22 + 1 / 18582706166169600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 20 - 1 / 316612955602944 * (1.0 / jnp.maximum(_aval, 0.32)) ** 18 + 1 / 5811921223680 * (1.0 / jnp.maximum(_aval, 0.32)) ** 16 - 1 / 115811942400 * (1.0 / jnp.maximum(_aval, 0.32)) ** 14 + 1 / 2530344960 * (1.0 / jnp.maximum(_aval, 0.32)) ** 12 - 1 / 61501440 * (1.0 / jnp.maximum(_aval, 0.32)) ** 10 + 5 / 8515584 * (1.0 / jnp.maximum(_aval, 0.32)) ** 8 - 1 / 56448 * (1.0 / jnp.maximum(_aval, 0.32)) ** 6 + 3 / 7840 * (1.0 / jnp.maximum(_aval, 0.32)) ** 4, lambda _aval: attenuation_erf_f30(jnp.minimum(_aval, 0.32)))

  tm_f0 = lambda x: (1 + 10 * (70 * tm_y(x) / 27) + tm_beta * tm_y(x) ** 2) ** (1 / 10)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  js18_A = lambda rs, z, x: jnp.maximum(1e-10, a_cnst * rs / (tm_f0(x) * f.opz_pow_n(z, 1 / 3)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  js18_DME_SR = lambda rs, z, x, t: +attenuation_erf(js18_A(rs, z, x)) / tm_f0(x) ** 2 + attenuation_erf_f2(js18_A(rs, z, x)) * 7 * js18_G(x, t) / (9 * tm_f0(x) ** 4) + attenuation_erf_f3(js18_A(rs, z, x)) * 245 * js18_H(x) / (54 * tm_f0(x) ** 4)

  pjs18_f = lambda rs, z, x, u, t: js18_DME_SR(rs, z, x, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, pjs18_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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

  att_erf_aux1 = lambda a: jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a))

  att_erf_aux2 = lambda a: jnp.exp(-1 / (4 * a ** 2)) - 1

  attenuation_erf_f20 = lambda a: 1 + 24 * a ** 2 * ((20 * a ** 2 - 64 * a ** 4) * jnp.exp(-1 / (4 * a ** 2)) - 3 - 36 * a ** 2 + 64 * a ** 4 + 10 * a * jnp.sqrt(jnp.pi) * jax.lax.erf(1 / (2 * a)))

  attenuation_erf_f30 = lambda a: 1 + 8 / 7 * a * ((-8 * a + 256 * a ** 3 - 576 * a ** 5 + 3840 * a ** 7 - 122880 * a ** 9) * jnp.exp(-1 / (4 * a ** 2)) + 24 * a ** 3 * (-35 + 224 * a ** 2 - 1440 * a ** 4 + 5120 * a ** 6) + 2 * jnp.sqrt(jnp.pi) * (-2 + 60 * a ** 2) * jax.lax.erf(1 / (2 * a)))

  a_cnst = (4 / (9 * jnp.pi)) ** (1 / 3) * f.p.cam_omega / 2

  js18_G = lambda x, t: (3 * (tm_lambda ** 2 - tm_lambda + 1 / 2) * (t - K_FACTOR_C - x ** 2 / 72) - (t - K_FACTOR_C) + 7 / 18 * (2 * tm_lambda - 1) ** 2 * x ** 2) / K_FACTOR_C

  tm_y = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  js18_H = lambda x: (2 * tm_lambda - 1) ** 2 * tm_p(x)

  att_erf_aux3 = lambda a: 2 * a ** 2 * att_erf_aux2(a) + 1 / 2

  attenuation_erf_f2 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.27, lambda _aval: -1 / 3511556992918352140755776405766144000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 46 + 1 / 33929038000650146833571361325056000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 44 - 1 / 341095116070365837848137621831680000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 42 + 1 / 3573852336994573837102806466560000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 40 - 1 / 39097165634742908368485089280000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 38 + 1 / 447473103488807905221672960000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 36 - 1 / 5369745537516410492682240000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 34 + 1 / 67726520292999771979776000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 32 - 1 / 900231674141645733888000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 30 + 1 / 12648942844388573184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 28 - 1 / 188514051721003008000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 26 + 1 / 2991700272218112000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 24 - 1 / 50785035485184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 22 + 1 / 927028425523200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 20 - 1 / 18311911833600 * (1.0 / jnp.maximum(_aval, 0.27)) ** 18 + 1 / 394474291200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 16 - 1 / 9358540800 * (1.0 / jnp.maximum(_aval, 0.27)) ** 14 + 1 / 247726080 * (1.0 / jnp.maximum(_aval, 0.27)) ** 12 - 1 / 7454720 * (1.0 / jnp.maximum(_aval, 0.27)) ** 10 + 3 / 788480 * (1.0 / jnp.maximum(_aval, 0.27)) ** 8 - 1 / 11520 * (1.0 / jnp.maximum(_aval, 0.27)) ** 6 + 3 / 2240 * (1.0 / jnp.maximum(_aval, 0.27)) ** 4, lambda _aval: attenuation_erf_f20(jnp.minimum(_aval, 0.27)))

  attenuation_erf_f3 = lambda a: apply_piecewise(a, lambda _aval: _aval >= 0.32, lambda _aval: -1 / 2104209454461863328391867505049600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 38 + 1 / 22046293272414372635684634624000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 36 - 1 / 241191070393445437962977280000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 34 + 1 / 2760851680179343645999104000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 32 - 1 / 33139778504339333578752000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 30 + 1 / 418174050435486229463040 * (1.0 / jnp.maximum(_aval, 0.32)) ** 28 - 1 / 5562511054710453043200 * (1.0 / jnp.maximum(_aval, 0.32)) ** 26 + 1 / 78244468658012160000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 24 - 1 / 1168055816159232000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 22 + 1 / 18582706166169600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 20 - 1 / 316612955602944 * (1.0 / jnp.maximum(_aval, 0.32)) ** 18 + 1 / 5811921223680 * (1.0 / jnp.maximum(_aval, 0.32)) ** 16 - 1 / 115811942400 * (1.0 / jnp.maximum(_aval, 0.32)) ** 14 + 1 / 2530344960 * (1.0 / jnp.maximum(_aval, 0.32)) ** 12 - 1 / 61501440 * (1.0 / jnp.maximum(_aval, 0.32)) ** 10 + 5 / 8515584 * (1.0 / jnp.maximum(_aval, 0.32)) ** 8 - 1 / 56448 * (1.0 / jnp.maximum(_aval, 0.32)) ** 6 + 3 / 7840 * (1.0 / jnp.maximum(_aval, 0.32)) ** 4, lambda _aval: attenuation_erf_f30(jnp.minimum(_aval, 0.32)))

  tm_f0 = lambda x: (1 + 10 * (70 * tm_y(x) / 27) + tm_beta * tm_y(x) ** 2) ** (1 / 10)

  attenuation_erf0 = lambda a: 1 - 8 / 3 * a * (att_erf_aux1(a) + 2 * a * (att_erf_aux2(a) - att_erf_aux3(a)))

  js18_A = lambda rs, z, x: jnp.maximum(1e-10, a_cnst * rs / (tm_f0(x) * f.opz_pow_n(z, 1 / 3)))

  attenuation_erf = lambda a: apply_piecewise(a, lambda _aval: _aval >= 1.35, lambda _aval: -1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2, lambda _aval: attenuation_erf0(jnp.minimum(_aval, 1.35)))

  js18_DME_SR = lambda rs, z, x, t: +attenuation_erf(js18_A(rs, z, x)) / tm_f0(x) ** 2 + attenuation_erf_f2(js18_A(rs, z, x)) * 7 * js18_G(x, t) / (9 * tm_f0(x) ** 4) + attenuation_erf_f3(js18_A(rs, z, x)) * 245 * js18_H(x) / (54 * tm_f0(x) ** 4)

  pjs18_f = lambda rs, z, x, u, t: js18_DME_SR(rs, z, x, t)

  functional_body = lambda rs, z, xt, xs0, xs1, u0, u1, t0, t1: mgga_exchange_nsp(f, params, pjs18_f, rs, z, xs0, xs1, u0, u1, t0, t1)

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