"""Generated from lda_c_w20.mpl."""

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
  w20_a0 = lambda z: (1 - jnp.log(2)) / jnp.pi ** 2 if z == 0 else (1 - jnp.log(2)) / (2 * jnp.pi ** 2)

  w20_a1 = lambda z: (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (7 * jnp.pi ** 2 / 6 - 12 * jnp.log(2) - 1) if z == 0 else 2 ** (-4 / 3) * (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (13 * jnp.pi ** 2 / 12 - 12 * jnp.log(2) + 1 / 2)

  w20_b0 = lambda z: -0.0711 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942 if z == 0 else -0.049917 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942

  w20_b1 = lambda z: -0.01 if z == 0 else 0

  w20_f0 = -0.9

  w20_f1 = 1.5

  w20_f2 = 0

  w20_cs = lambda z: 3 / 10 * (9 * jnp.pi / 4) ** (2 / 3) * 1 / 2 * ((1 + z) ** (5 / 3) + (1 - z) ** (5 / 3))

  w20_cx = lambda z: -3 / (4 * jnp.pi) * (9 * jnp.pi / 4) ** (1 / 3) * 1 / 2 * ((1 + z) ** (4 / 3) + (1 - z) ** (4 / 3))

  w20_DF = lambda rs, z, cfterm: jnp.exp(-2 * w20_b0(z) / w20_a0(z)) - 2 * (1 - jnp.exp(-(rs / 100) ** 2)) * (cfterm / w20_a0(z) + 1 / 2 * jnp.exp(-2 * w20_b0(z) / w20_a0(z)))

  w20_G = lambda rs, z: rs * jnp.exp(-(rs / 100) ** 2) / (jnp.exp(-(rs / 100) ** 2) + 10 * rs ** (5 / 4)) * (-w20_a1(z) * jnp.log(1 + 1 / rs) + w20_b1(z))

  w20_E = lambda rs, z: -2 * (1 - jnp.exp(-(rs / 100) ** 2)) * w20_f1 / w20_a0(z)

  w20_ec = lambda rs, z: -w20_a0(z) / 2 * jnp.log(1 + w20_DF(rs, z, w20_f0 - w20_cx(z)) / rs + w20_E(rs, z) / rs ** (3 / 2) + w20_DF(rs, z, w20_f2 - w20_cs(z)) / rs ** 2) + w20_G(rs, z)

  f_w20 = lambda rs, zeta: w20_ec(rs, 0) + (w20_ec(rs, 1) - w20_ec(rs, 0)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_w20(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )

  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  w20_a0 = lambda z: (1 - jnp.log(2)) / jnp.pi ** 2 if z == 0 else (1 - jnp.log(2)) / (2 * jnp.pi ** 2)

  w20_a1 = lambda z: (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (7 * jnp.pi ** 2 / 6 - 12 * jnp.log(2) - 1) if z == 0 else 2 ** (-4 / 3) * (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (13 * jnp.pi ** 2 / 12 - 12 * jnp.log(2) + 1 / 2)

  w20_b0 = lambda z: -0.0711 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942 if z == 0 else -0.049917 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942

  w20_b1 = lambda z: -0.01 if z == 0 else 0

  w20_f0 = -0.9

  w20_f1 = 1.5

  w20_f2 = 0

  w20_cs = lambda z: 3 / 10 * (9 * jnp.pi / 4) ** (2 / 3) * 1 / 2 * ((1 + z) ** (5 / 3) + (1 - z) ** (5 / 3))

  w20_cx = lambda z: -3 / (4 * jnp.pi) * (9 * jnp.pi / 4) ** (1 / 3) * 1 / 2 * ((1 + z) ** (4 / 3) + (1 - z) ** (4 / 3))

  w20_DF = lambda rs, z, cfterm: jnp.exp(-2 * w20_b0(z) / w20_a0(z)) - 2 * (1 - jnp.exp(-(rs / 100) ** 2)) * (cfterm / w20_a0(z) + 1 / 2 * jnp.exp(-2 * w20_b0(z) / w20_a0(z)))

  w20_G = lambda rs, z: rs * jnp.exp(-(rs / 100) ** 2) / (jnp.exp(-(rs / 100) ** 2) + 10 * rs ** (5 / 4)) * (-w20_a1(z) * jnp.log(1 + 1 / rs) + w20_b1(z))

  w20_E = lambda rs, z: -2 * (1 - jnp.exp(-(rs / 100) ** 2)) * w20_f1 / w20_a0(z)

  w20_ec = lambda rs, z: -w20_a0(z) / 2 * jnp.log(1 + w20_DF(rs, z, w20_f0 - w20_cx(z)) / rs + w20_E(rs, z) / rs ** (3 / 2) + w20_DF(rs, z, w20_f2 - w20_cs(z)) / rs ** 2) + w20_G(rs, z)

  f_w20 = lambda rs, zeta: w20_ec(rs, 0) + (w20_ec(rs, 1) - w20_ec(rs, 0)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_w20(rs, zeta)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )

  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  w20_a0 = lambda z: (1 - jnp.log(2)) / jnp.pi ** 2 if z == 0 else (1 - jnp.log(2)) / (2 * jnp.pi ** 2)

  w20_a1 = lambda z: (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (7 * jnp.pi ** 2 / 6 - 12 * jnp.log(2) - 1) if z == 0 else 2 ** (-4 / 3) * (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (13 * jnp.pi ** 2 / 12 - 12 * jnp.log(2) + 1 / 2)

  w20_b0 = lambda z: -0.0711 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942 if z == 0 else -0.049917 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942

  w20_b1 = lambda z: -0.01 if z == 0 else 0

  w20_f0 = -0.9

  w20_f1 = 1.5

  w20_f2 = 0

  w20_cs = lambda z: 3 / 10 * (9 * jnp.pi / 4) ** (2 / 3) * 1 / 2 * ((1 + z) ** (5 / 3) + (1 - z) ** (5 / 3))

  w20_cx = lambda z: -3 / (4 * jnp.pi) * (9 * jnp.pi / 4) ** (1 / 3) * 1 / 2 * ((1 + z) ** (4 / 3) + (1 - z) ** (4 / 3))

  w20_DF = lambda rs, z, cfterm: jnp.exp(-2 * w20_b0(z) / w20_a0(z)) - 2 * (1 - jnp.exp(-(rs / 100) ** 2)) * (cfterm / w20_a0(z) + 1 / 2 * jnp.exp(-2 * w20_b0(z) / w20_a0(z)))

  w20_G = lambda rs, z: rs * jnp.exp(-(rs / 100) ** 2) / (jnp.exp(-(rs / 100) ** 2) + 10 * rs ** (5 / 4)) * (-w20_a1(z) * jnp.log(1 + 1 / rs) + w20_b1(z))

  w20_E = lambda rs, z: -2 * (1 - jnp.exp(-(rs / 100) ** 2)) * w20_f1 / w20_a0(z)

  w20_ec = lambda rs, z: -w20_a0(z) / 2 * jnp.log(1 + w20_DF(rs, z, w20_f0 - w20_cx(z)) / rs + w20_E(rs, z) / rs ** (3 / 2) + w20_DF(rs, z, w20_f2 - w20_cs(z)) / rs ** 2) + w20_G(rs, z)

  f_w20 = lambda rs, zeta: w20_ec(rs, 0) + (w20_ec(rs, 1) - w20_ec(rs, 0)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_w20(rs, zeta)

  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  w20_a0 = lambda z: (1 - jnp.log(2)) / jnp.pi ** 2 if z == 0 else (1 - jnp.log(2)) / (2 * jnp.pi ** 2)

  w20_a1 = lambda z: (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (7 * jnp.pi ** 2 / 6 - 12 * jnp.log(2) - 1) if z == 0 else 2 ** (-4 / 3) * (9 * jnp.pi / 4) ** (-1 / 3) * 1 / (4 * jnp.pi ** 3) * (13 * jnp.pi ** 2 / 12 - 12 * jnp.log(2) + 1 / 2)

  w20_b0 = lambda z: -0.0711 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942 if z == 0 else -0.049917 + jnp.log(2) / 6 - 3 / (4 * jnp.pi ** 2) * 1.2020569031595942

  w20_b1 = lambda z: -0.01 if z == 0 else 0

  w20_f0 = -0.9

  w20_f1 = 1.5

  w20_f2 = 0

  w20_cs = lambda z: 3 / 10 * (9 * jnp.pi / 4) ** (2 / 3) * 1 / 2 * ((1 + z) ** (5 / 3) + (1 - z) ** (5 / 3))

  w20_cx = lambda z: -3 / (4 * jnp.pi) * (9 * jnp.pi / 4) ** (1 / 3) * 1 / 2 * ((1 + z) ** (4 / 3) + (1 - z) ** (4 / 3))

  w20_DF = lambda rs, z, cfterm: jnp.exp(-2 * w20_b0(z) / w20_a0(z)) - 2 * (1 - jnp.exp(-(rs / 100) ** 2)) * (cfterm / w20_a0(z) + 1 / 2 * jnp.exp(-2 * w20_b0(z) / w20_a0(z)))

  w20_G = lambda rs, z: rs * jnp.exp(-(rs / 100) ** 2) / (jnp.exp(-(rs / 100) ** 2) + 10 * rs ** (5 / 4)) * (-w20_a1(z) * jnp.log(1 + 1 / rs) + w20_b1(z))

  w20_E = lambda rs, z: -2 * (1 - jnp.exp(-(rs / 100) ** 2)) * w20_f1 / w20_a0(z)

  w20_ec = lambda rs, z: -w20_a0(z) / 2 * jnp.log(1 + w20_DF(rs, z, w20_f0 - w20_cx(z)) / rs + w20_E(rs, z) / rs ** (3 / 2) + w20_DF(rs, z, w20_f2 - w20_cs(z)) / rs ** 2) + w20_G(rs, z)

  f_w20 = lambda rs, zeta: w20_ec(rs, 0) + (w20_ec(rs, 1) - w20_ec(rs, 0)) * f.f_zeta(zeta)

  functional_body = lambda rs, zeta: f_w20(rs, zeta)

  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  

  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  _tmp_res = {'v2rho2': jnp.stack([_b(d11), _b(d12), _b(d22)], axis=-1) if 'd12' in locals() else _b(d11), 'v2rhosigma': jnp.stack([_b(d13), _b(d14), _b(d15), _b(d23), _b(d24), _b(d25)], axis=-1) if 'd13' in locals() else None, 'v2sigma2': jnp.stack([_b(d33), _b(d34), _b(d35), _b(d44), _b(d45), _b(d55)], axis=-1) if 'd33' in locals() else None, 'v2rholapl': jnp.stack([_b(d16), _b(d17), _b(d26), _b(d27)], axis=-1) if 'd16' in locals() else None, 'v2rhotau': jnp.stack([_b(d18), _b(d19), _b(d28), _b(d29)], axis=-1) if 'd18' in locals() else None, 'v2sigmalapl': jnp.stack([_b(d36), _b(d37), _b(d46), _b(d47), _b(d56), _b(d57)], axis=-1) if 'd36' in locals() else None, 'v2sigmatau': jnp.stack([_b(d38), _b(d39), _b(d48), _b(d49), _b(d58), _b(d59)], axis=-1) if 'd38' in locals() else None, 'v2lapl2': jnp.stack([_b(d66), _b(d67), _b(d77)], axis=-1) if 'd66' in locals() else None, 'v2lapltau': jnp.stack([_b(d68), _b(d69), _b(d78), _b(d79)], axis=-1) if 'd68' in locals() else None, 'v2tau2': jnp.stack([_b(d88), _b(d89), _b(d99)], axis=-1) if 'd88' in locals() else None}
  res = {k: v for (k, v) in _tmp_res.items() if v is not None}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  

  res = {'v2rho2': v2rho2_0_}
  return res
