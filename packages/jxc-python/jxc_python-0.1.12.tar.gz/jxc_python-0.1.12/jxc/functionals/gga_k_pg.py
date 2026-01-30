"""Generated from gga_k_pg.mpl."""

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
  params_pg_mu_raw = params.pg_mu
  if isinstance(params_pg_mu_raw, (str, bytes, dict)):
    params_pg_mu = params_pg_mu_raw
  else:
    try:
      params_pg_mu_seq = list(params_pg_mu_raw)
    except TypeError:
      params_pg_mu = params_pg_mu_raw
    else:
      params_pg_mu_seq = np.asarray(params_pg_mu_seq, dtype=np.float64)
      params_pg_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pg_mu_seq))

  pg_f0 = lambda s: 5 / 3 * s ** 2 + jnp.exp(-params_pg_mu * s ** 2)

  pg_f = lambda x: pg_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pg_f, rs, z, xs0, xs1)

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
  params_pg_mu_raw = params.pg_mu
  if isinstance(params_pg_mu_raw, (str, bytes, dict)):
    params_pg_mu = params_pg_mu_raw
  else:
    try:
      params_pg_mu_seq = list(params_pg_mu_raw)
    except TypeError:
      params_pg_mu = params_pg_mu_raw
    else:
      params_pg_mu_seq = np.asarray(params_pg_mu_seq, dtype=np.float64)
      params_pg_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pg_mu_seq))

  pg_f0 = lambda s: 5 / 3 * s ** 2 + jnp.exp(-params_pg_mu * s ** 2)

  pg_f = lambda x: pg_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pg_f, rs, z, xs0, xs1)

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
  params_pg_mu_raw = params.pg_mu
  if isinstance(params_pg_mu_raw, (str, bytes, dict)):
    params_pg_mu = params_pg_mu_raw
  else:
    try:
      params_pg_mu_seq = list(params_pg_mu_raw)
    except TypeError:
      params_pg_mu = params_pg_mu_raw
    else:
      params_pg_mu_seq = np.asarray(params_pg_mu_seq, dtype=np.float64)
      params_pg_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pg_mu_seq))

  pg_f0 = lambda s: 5 / 3 * s ** 2 + jnp.exp(-params_pg_mu * s ** 2)

  pg_f = lambda x: pg_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pg_f, rs, z, xs0, xs1)

  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t23 * f.p.zeta_threshold
  t25 = t20 ** (0.1e1 / 0.3e1)
  t26 = t25 ** 2
  t28 = f.my_piecewise3(t21, t24, t26 * t20)
  t29 = t7 ** (0.1e1 / 0.3e1)
  t30 = t29 ** 2
  t31 = t28 * t30
  t32 = 6 ** (0.1e1 / 0.3e1)
  t33 = jnp.pi ** 2
  t34 = t33 ** (0.1e1 / 0.3e1)
  t35 = t34 ** 2
  t36 = 0.1e1 / t35
  t37 = t32 * t36
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t46 = params.pg_mu * t32
  t51 = jnp.exp(-t46 * t36 * s0 * t42 / 0.24e2)
  t52 = 0.5e1 / 0.72e2 * t37 * s0 * t42 + t51
  t56 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t52)
  t57 = r1 <= f.p.dens_threshold
  t58 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t59 = 0.1e1 + t58
  t60 = t59 <= f.p.zeta_threshold
  t61 = t59 ** (0.1e1 / 0.3e1)
  t62 = t61 ** 2
  t64 = f.my_piecewise3(t60, t24, t62 * t59)
  t65 = t64 * t30
  t66 = r1 ** 2
  t67 = r1 ** (0.1e1 / 0.3e1)
  t68 = t67 ** 2
  t70 = 0.1e1 / t68 / t66
  t78 = jnp.exp(-t46 * t36 * s2 * t70 / 0.24e2)
  t79 = 0.5e1 / 0.72e2 * t37 * s2 * t70 + t78
  t83 = f.my_piecewise3(t57, 0, 0.3e1 / 0.20e2 * t6 * t65 * t79)
  t84 = t7 ** 2
  t86 = t17 / t84
  t87 = t8 - t86
  t88 = f.my_piecewise5(t11, 0, t15, 0, t87)
  t91 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t88)
  t96 = 0.1e1 / t29
  t100 = t6 * t28 * t96 * t52 / 0.10e2
  t104 = s0 / t40 / t38 / r0
  t107 = t46 * t36
  t116 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t91 * t30 * t52 + t100 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.5e1 / 0.27e2 * t37 * t104 + t107 * t104 * t51 / 0.9e1))
  t118 = f.my_piecewise5(t15, 0, t11, 0, -t87)
  t121 = f.my_piecewise3(t60, 0, 0.5e1 / 0.3e1 * t62 * t118)
  t129 = t6 * t64 * t96 * t79 / 0.10e2
  t131 = f.my_piecewise3(t57, 0, 0.3e1 / 0.20e2 * t6 * t121 * t30 * t79 + t129)
  vrho_0_ = t56 + t83 + t7 * (t116 + t131)
  t134 = -t8 - t86
  t135 = f.my_piecewise5(t11, 0, t15, 0, t134)
  t138 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t135)
  t144 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t138 * t30 * t52 + t100)
  t146 = f.my_piecewise5(t15, 0, t11, 0, -t134)
  t149 = f.my_piecewise3(t60, 0, 0.5e1 / 0.3e1 * t62 * t146)
  t157 = s2 / t68 / t66 / r1
  t168 = f.my_piecewise3(t57, 0, 0.3e1 / 0.20e2 * t6 * t149 * t30 * t79 + t129 + 0.3e1 / 0.20e2 * t6 * t65 * (-0.5e1 / 0.27e2 * t37 * t157 + t107 * t157 * t78 / 0.9e1))
  vrho_1_ = t56 + t83 + t7 * (t144 + t168)
  t181 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.72e2 * t37 * t42 - t46 * t36 * t42 * t51 / 0.24e2))
  vsigma_0_ = t7 * t181
  vsigma_1_ = 0.0e0
  t192 = f.my_piecewise3(t57, 0, 0.3e1 / 0.20e2 * t6 * t65 * (0.5e1 / 0.72e2 * t37 * t70 - t46 * t36 * t70 * t78 / 0.24e2))
  vsigma_2_ = t7 * t192
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
  params_pg_mu_raw = params.pg_mu
  if isinstance(params_pg_mu_raw, (str, bytes, dict)):
    params_pg_mu = params_pg_mu_raw
  else:
    try:
      params_pg_mu_seq = list(params_pg_mu_raw)
    except TypeError:
      params_pg_mu = params_pg_mu_raw
    else:
      params_pg_mu_seq = np.asarray(params_pg_mu_seq, dtype=np.float64)
      params_pg_mu = np.concatenate((np.array([np.nan], dtype=np.float64), params_pg_mu_seq))

  pg_f0 = lambda s: 5 / 3 * s ** 2 + jnp.exp(-params_pg_mu * s ** 2)

  pg_f = lambda x: pg_f0(X2S * x)

  functional_body = lambda rs, z, xt, xs0, xs1: gga_kinetic(f, params, pg_f, rs, z, xs0, xs1)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t23 = t20 * t22
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t35 = 0.1e1 / t22 / t33
  t36 = t32 * t35
  t40 = params.pg_mu * t24 * t28
  t43 = jnp.exp(-t40 * t36 / 0.24e2)
  t44 = 0.5e1 / 0.72e2 * t29 * t36 + t43
  t48 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t44)
  t56 = 0.1e1 / t22 / t33 / r0
  t69 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t44 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.5e1 / 0.27e2 * t29 * t32 * t56 + t40 * t32 * t56 * t43 / 0.9e1))
  vrho_0_ = 0.2e1 * r0 * t69 + 0.2e1 * t48
  t72 = t31 * t35
  t82 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.72e2 * t29 * t72 - t40 * t72 * t43 / 0.24e2))
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
  
  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t23 = t20 / t21
  t24 = 6 ** (0.1e1 / 0.3e1)
  t25 = jnp.pi ** 2
  t26 = t25 ** (0.1e1 / 0.3e1)
  t27 = t26 ** 2
  t28 = 0.1e1 / t27
  t29 = t24 * t28
  t30 = 2 ** (0.1e1 / 0.3e1)
  t31 = t30 ** 2
  t32 = s0 * t31
  t33 = r0 ** 2
  t34 = t21 ** 2
  t36 = 0.1e1 / t34 / t33
  t37 = t32 * t36
  t41 = params.pg_mu * t24 * t28
  t44 = jnp.exp(-t41 * t37 / 0.24e2)
  t45 = 0.5e1 / 0.72e2 * t29 * t37 + t44
  t49 = t20 * t34
  t50 = t33 * r0
  t52 = 0.1e1 / t34 / t50
  t60 = -0.5e1 / 0.27e2 * t29 * t32 * t52 + t41 * t32 * t52 * t44 / 0.9e1
  t65 = f.my_piecewise3(t2, 0, t7 * t23 * t45 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t49 * t60)
  t76 = t33 ** 2
  t78 = 0.1e1 / t34 / t76
  t86 = params.pg_mu ** 2
  t87 = t24 ** 2
  t88 = t86 * t87
  t90 = 0.1e1 / t26 / t25
  t91 = t88 * t90
  t92 = s0 ** 2
  t106 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t45 / 0.30e2 + t7 * t23 * t60 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t49 * (0.55e2 / 0.81e2 * t29 * t32 * t78 - 0.11e2 / 0.27e2 * t41 * t32 * t78 * t44 + 0.2e1 / 0.81e2 * t91 * t92 * t30 / t21 / t76 / t50 * t44))
  v2rho2_0_ = 0.2e1 * r0 * t106 + 0.4e1 * t65
  t109 = t31 * t36
  t115 = 0.5e1 / 0.72e2 * t29 * t109 - t41 * t109 * t44 / 0.24e2
  t119 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t49 * t115)
  t123 = t31 * t52
  t142 = f.my_piecewise3(t2, 0, t7 * t23 * t115 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t49 * (-0.5e1 / 0.27e2 * t29 * t123 + t41 * t123 * t44 / 0.9e1 - t91 * t30 / t21 / t76 / t33 * s0 * t44 / 0.108e3))
  v2rhosigma_0_ = 0.2e1 * r0 * t142 + 0.2e1 * t119
  t152 = f.my_piecewise3(t2, 0, t7 * t20 * t78 * t88 * t90 * t30 * t44 / 0.1920e4)
  v2sigma2_0_ = 0.2e1 * r0 * t152
  res = {'v2rho2': v2rho2_0_, 'v2rhosigma': v2rhosigma_0_, 'v2sigma2': v2sigma2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** (0.1e1 / 0.3e1)
  t24 = t20 / t21 / r0
  t25 = 6 ** (0.1e1 / 0.3e1)
  t26 = jnp.pi ** 2
  t27 = t26 ** (0.1e1 / 0.3e1)
  t28 = t27 ** 2
  t29 = 0.1e1 / t28
  t30 = t25 * t29
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = s0 * t32
  t34 = r0 ** 2
  t35 = t21 ** 2
  t38 = t33 / t35 / t34
  t42 = params.pg_mu * t25 * t29
  t45 = jnp.exp(-t42 * t38 / 0.24e2)
  t46 = 0.5e1 / 0.72e2 * t30 * t38 + t45
  t51 = t20 / t21
  t52 = t34 * r0
  t54 = 0.1e1 / t35 / t52
  t62 = -0.5e1 / 0.27e2 * t30 * t33 * t54 + t42 * t33 * t54 * t45 / 0.9e1
  t66 = t20 * t35
  t67 = t34 ** 2
  t69 = 0.1e1 / t35 / t67
  t77 = params.pg_mu ** 2
  t78 = t25 ** 2
  t82 = t77 * t78 / t27 / t26
  t83 = s0 ** 2
  t84 = t83 * t31
  t92 = 0.55e2 / 0.81e2 * t30 * t33 * t69 - 0.11e2 / 0.27e2 * t42 * t33 * t69 * t45 + 0.2e1 / 0.81e2 * t82 * t84 / t21 / t67 / t52 * t45
  t97 = f.my_piecewise3(t2, 0, -t7 * t24 * t46 / 0.30e2 + t7 * t51 * t62 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t66 * t92)
  t113 = 0.1e1 / t35 / t67 / r0
  t121 = t67 ** 2
  t129 = t26 ** 2
  t144 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t46 - t7 * t24 * t62 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t51 * t92 + 0.3e1 / 0.20e2 * t7 * t66 * (-0.770e3 / 0.243e3 * t30 * t33 * t113 + 0.154e3 / 0.81e2 * t42 * t33 * t113 * t45 - 0.22e2 / 0.81e2 * t82 * t84 / t21 / t121 * t45 + 0.8e1 / 0.243e3 * t77 * params.pg_mu / t129 * t83 * s0 / t121 / t52 * t45))
  v3rho3_0_ = 0.2e1 * r0 * t144 + 0.6e1 * t97

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 3 ** (0.1e1 / 0.3e1)
  t4 = t3 ** 2
  t5 = jnp.pi ** (0.1e1 / 0.3e1)
  t7 = t4 * t5 * jnp.pi
  t8 = 0.1e1 <= f.p.zeta_threshold
  t9 = f.p.zeta_threshold - 0.1e1
  t11 = f.my_piecewise5(t8, t9, t8, -t9, 0)
  t12 = 0.1e1 + t11
  t14 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t14 ** 2
  t17 = t12 ** (0.1e1 / 0.3e1)
  t18 = t17 ** 2
  t20 = f.my_piecewise3(t12 <= f.p.zeta_threshold, t15 * f.p.zeta_threshold, t18 * t12)
  t21 = r0 ** 2
  t22 = r0 ** (0.1e1 / 0.3e1)
  t25 = t20 / t22 / t21
  t26 = 6 ** (0.1e1 / 0.3e1)
  t27 = jnp.pi ** 2
  t28 = t27 ** (0.1e1 / 0.3e1)
  t29 = t28 ** 2
  t30 = 0.1e1 / t29
  t31 = t26 * t30
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = s0 * t33
  t35 = t22 ** 2
  t38 = t34 / t35 / t21
  t42 = params.pg_mu * t26 * t30
  t45 = jnp.exp(-t42 * t38 / 0.24e2)
  t46 = 0.5e1 / 0.72e2 * t31 * t38 + t45
  t52 = t20 / t22 / r0
  t53 = t21 * r0
  t55 = 0.1e1 / t35 / t53
  t63 = -0.5e1 / 0.27e2 * t31 * t34 * t55 + t42 * t34 * t55 * t45 / 0.9e1
  t68 = t20 / t22
  t69 = t21 ** 2
  t71 = 0.1e1 / t35 / t69
  t79 = params.pg_mu ** 2
  t80 = t26 ** 2
  t84 = t79 * t80 / t28 / t27
  t85 = s0 ** 2
  t86 = t85 * t32
  t94 = 0.55e2 / 0.81e2 * t31 * t34 * t71 - 0.11e2 / 0.27e2 * t42 * t34 * t71 * t45 + 0.2e1 / 0.81e2 * t84 * t86 / t22 / t69 / t53 * t45
  t98 = t20 * t35
  t101 = 0.1e1 / t35 / t69 / r0
  t109 = t69 ** 2
  t117 = t27 ** 2
  t118 = 0.1e1 / t117
  t119 = t79 * params.pg_mu * t118
  t120 = t85 * s0
  t127 = -0.770e3 / 0.243e3 * t31 * t34 * t101 + 0.154e3 / 0.81e2 * t42 * t34 * t101 * t45 - 0.22e2 / 0.81e2 * t84 * t86 / t22 / t109 * t45 + 0.8e1 / 0.243e3 * t119 * t120 / t109 / t53 * t45
  t132 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t46 - t7 * t52 * t63 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t68 * t94 + 0.3e1 / 0.20e2 * t7 * t98 * t127)
  t149 = t69 * t21
  t151 = 0.1e1 / t35 / t149
  t172 = t79 ** 2
  t174 = t85 ** 2
  t189 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t53 * t46 + 0.8e1 / 0.45e2 * t7 * t25 * t63 - t7 * t52 * t94 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t68 * t127 + 0.3e1 / 0.20e2 * t7 * t98 * (0.13090e5 / 0.729e3 * t31 * t34 * t151 - 0.2618e4 / 0.243e3 * t42 * t34 * t151 * t45 + 0.1958e4 / 0.729e3 * t84 * t86 / t22 / t109 / r0 * t45 - 0.176e3 / 0.243e3 * t119 * t120 / t109 / t69 * t45 + 0.8e1 / 0.2187e4 * t172 * t118 * t174 / t35 / t109 / t149 * t31 * t33 * t45))
  v4rho4_0_ = 0.2e1 * r0 * t189 + 0.8e1 * t132

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = 3 ** (0.1e1 / 0.3e1)
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = t22 ** 2
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t26 = t17 * t25
  t27 = t8 - t26
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t31 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t28)
  t32 = t7 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = t31 * t33
  t35 = 6 ** (0.1e1 / 0.3e1)
  t36 = jnp.pi ** 2
  t37 = t36 ** (0.1e1 / 0.3e1)
  t38 = t37 ** 2
  t39 = 0.1e1 / t38
  t40 = t35 * t39
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t45 = 0.1e1 / t43 / t41
  t49 = params.pg_mu * t35
  t54 = jnp.exp(-t49 * t39 * s0 * t45 / 0.24e2)
  t55 = 0.5e1 / 0.72e2 * t40 * s0 * t45 + t54
  t59 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t60 = t59 ** 2
  t61 = t60 * f.p.zeta_threshold
  t63 = f.my_piecewise3(t21, t61, t23 * t20)
  t64 = 0.1e1 / t32
  t65 = t63 * t64
  t68 = t6 * t65 * t55 / 0.10e2
  t69 = t63 * t33
  t70 = t41 * r0
  t73 = s0 / t43 / t70
  t76 = t49 * t39
  t80 = -0.5e1 / 0.27e2 * t40 * t73 + t76 * t73 * t54 / 0.9e1
  t85 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t55 + t68 + 0.3e1 / 0.20e2 * t6 * t69 * t80)
  t87 = r1 <= f.p.dens_threshold
  t88 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t89 = 0.1e1 + t88
  t90 = t89 <= f.p.zeta_threshold
  t91 = t89 ** (0.1e1 / 0.3e1)
  t92 = t91 ** 2
  t94 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t97 = f.my_piecewise3(t90, 0, 0.5e1 / 0.3e1 * t92 * t94)
  t98 = t97 * t33
  t99 = r1 ** 2
  t100 = r1 ** (0.1e1 / 0.3e1)
  t101 = t100 ** 2
  t103 = 0.1e1 / t101 / t99
  t111 = jnp.exp(-t49 * t39 * s2 * t103 / 0.24e2)
  t112 = 0.5e1 / 0.72e2 * t40 * s2 * t103 + t111
  t117 = f.my_piecewise3(t90, t61, t92 * t89)
  t118 = t117 * t64
  t121 = t6 * t118 * t112 / 0.10e2
  t123 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t98 * t112 + t121)
  t125 = 0.1e1 / t22
  t126 = t28 ** 2
  t131 = t17 / t24 / t7
  t133 = -0.2e1 * t25 + 0.2e1 * t131
  t134 = f.my_piecewise5(t11, 0, t15, 0, t133)
  t138 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t125 * t126 + 0.5e1 / 0.3e1 * t23 * t134)
  t145 = t6 * t31 * t64 * t55
  t151 = 0.1e1 / t32 / t7
  t155 = t6 * t63 * t151 * t55 / 0.30e2
  t157 = t6 * t65 * t80
  t159 = t41 ** 2
  t162 = s0 / t43 / t159
  t168 = params.pg_mu ** 2
  t169 = t35 ** 2
  t173 = t168 * t169 / t37 / t36
  t174 = s0 ** 2
  t187 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t138 * t33 * t55 + t145 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t80 - t155 + t157 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t69 * (0.55e2 / 0.81e2 * t40 * t162 - 0.11e2 / 0.27e2 * t76 * t162 * t54 + t173 * t174 / t42 / t159 / t70 * t54 / 0.81e2))
  t188 = 0.1e1 / t91
  t189 = t94 ** 2
  t193 = f.my_piecewise5(t15, 0, t11, 0, -t133)
  t197 = f.my_piecewise3(t90, 0, 0.10e2 / 0.9e1 * t188 * t189 + 0.5e1 / 0.3e1 * t92 * t193)
  t204 = t6 * t97 * t64 * t112
  t209 = t6 * t117 * t151 * t112 / 0.30e2
  t211 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t197 * t33 * t112 + t204 / 0.5e1 - t209)
  d11 = 0.2e1 * t85 + 0.2e1 * t123 + t7 * (t187 + t211)
  t214 = -t8 - t26
  t215 = f.my_piecewise5(t11, 0, t15, 0, t214)
  t218 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t215)
  t219 = t218 * t33
  t224 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t219 * t55 + t68)
  t226 = f.my_piecewise5(t15, 0, t11, 0, -t214)
  t229 = f.my_piecewise3(t90, 0, 0.5e1 / 0.3e1 * t92 * t226)
  t230 = t229 * t33
  t234 = t117 * t33
  t235 = t99 * r1
  t238 = s2 / t101 / t235
  t244 = -0.5e1 / 0.27e2 * t40 * t238 + t76 * t238 * t111 / 0.9e1
  t249 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t230 * t112 + t121 + 0.3e1 / 0.20e2 * t6 * t234 * t244)
  t253 = 0.2e1 * t131
  t254 = f.my_piecewise5(t11, 0, t15, 0, t253)
  t258 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t125 * t215 * t28 + 0.5e1 / 0.3e1 * t23 * t254)
  t265 = t6 * t218 * t64 * t55
  t273 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t258 * t33 * t55 + t265 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t219 * t80 + t145 / 0.10e2 - t155 + t157 / 0.10e2)
  t277 = f.my_piecewise5(t15, 0, t11, 0, -t253)
  t281 = f.my_piecewise3(t90, 0, 0.10e2 / 0.9e1 * t188 * t226 * t94 + 0.5e1 / 0.3e1 * t92 * t277)
  t288 = t6 * t229 * t64 * t112
  t295 = t6 * t118 * t244
  t298 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t281 * t33 * t112 + t288 / 0.10e2 + t204 / 0.10e2 - t209 + 0.3e1 / 0.20e2 * t6 * t98 * t244 + t295 / 0.10e2)
  d12 = t85 + t123 + t224 + t249 + t7 * (t273 + t298)
  t303 = t215 ** 2
  t307 = 0.2e1 * t25 + 0.2e1 * t131
  t308 = f.my_piecewise5(t11, 0, t15, 0, t307)
  t312 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t125 * t303 + 0.5e1 / 0.3e1 * t23 * t308)
  t319 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t312 * t33 * t55 + t265 / 0.5e1 - t155)
  t320 = t226 ** 2
  t324 = f.my_piecewise5(t15, 0, t11, 0, -t307)
  t328 = f.my_piecewise3(t90, 0, 0.10e2 / 0.9e1 * t188 * t320 + 0.5e1 / 0.3e1 * t92 * t324)
  t338 = t99 ** 2
  t341 = s2 / t101 / t338
  t347 = s2 ** 2
  t360 = f.my_piecewise3(t87, 0, 0.3e1 / 0.20e2 * t6 * t328 * t33 * t112 + t288 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t230 * t244 - t209 + t295 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t234 * (0.55e2 / 0.81e2 * t40 * t341 - 0.11e2 / 0.27e2 * t76 * t341 * t111 + t173 * t347 / t100 / t338 / t235 * t111 / 0.81e2))
  d22 = 0.2e1 * t224 + 0.2e1 * t249 + t7 * (t319 + t360)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
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
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t23 = 0.1e1 / t22
  t24 = t7 ** 2
  t25 = 0.1e1 / t24
  t27 = -t17 * t25 + t8
  t28 = f.my_piecewise5(t11, 0, t15, 0, t27)
  t29 = t28 ** 2
  t32 = t22 ** 2
  t34 = 0.1e1 / t24 / t7
  t37 = 0.2e1 * t17 * t34 - 0.2e1 * t25
  t38 = f.my_piecewise5(t11, 0, t15, 0, t37)
  t42 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t23 * t29 + 0.5e1 / 0.3e1 * t32 * t38)
  t43 = t7 ** (0.1e1 / 0.3e1)
  t44 = t43 ** 2
  t45 = t42 * t44
  t46 = 6 ** (0.1e1 / 0.3e1)
  t47 = jnp.pi ** 2
  t48 = t47 ** (0.1e1 / 0.3e1)
  t49 = t48 ** 2
  t50 = 0.1e1 / t49
  t51 = t46 * t50
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t56 = 0.1e1 / t54 / t52
  t60 = params.pg_mu * t46
  t65 = jnp.exp(-t60 * t50 * s0 * t56 / 0.24e2)
  t66 = 0.5e1 / 0.72e2 * t51 * s0 * t56 + t65
  t72 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t73 = 0.1e1 / t43
  t74 = t72 * t73
  t78 = t72 * t44
  t79 = t52 * r0
  t82 = s0 / t54 / t79
  t85 = t60 * t50
  t89 = -0.5e1 / 0.27e2 * t51 * t82 + t85 * t82 * t65 / 0.9e1
  t93 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t94 = t93 ** 2
  t95 = t94 * f.p.zeta_threshold
  t97 = f.my_piecewise3(t21, t95, t32 * t20)
  t99 = 0.1e1 / t43 / t7
  t100 = t97 * t99
  t104 = t97 * t73
  t108 = t97 * t44
  t109 = t52 ** 2
  t112 = s0 / t54 / t109
  t118 = params.pg_mu ** 2
  t119 = t46 ** 2
  t123 = t118 * t119 / t48 / t47
  t124 = s0 ** 2
  t132 = 0.55e2 / 0.81e2 * t51 * t112 - 0.11e2 / 0.27e2 * t85 * t112 * t65 + t123 * t124 / t53 / t109 / t79 * t65 / 0.81e2
  t137 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t66 + t6 * t74 * t66 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t78 * t89 - t6 * t100 * t66 / 0.30e2 + t6 * t104 * t89 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t108 * t132)
  t139 = r1 <= f.p.dens_threshold
  t140 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t141 = 0.1e1 + t140
  t142 = t141 <= f.p.zeta_threshold
  t143 = t141 ** (0.1e1 / 0.3e1)
  t144 = 0.1e1 / t143
  t146 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t147 = t146 ** 2
  t150 = t143 ** 2
  t152 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t156 = f.my_piecewise3(t142, 0, 0.10e2 / 0.9e1 * t144 * t147 + 0.5e1 / 0.3e1 * t150 * t152)
  t158 = r1 ** 2
  t159 = r1 ** (0.1e1 / 0.3e1)
  t160 = t159 ** 2
  t162 = 0.1e1 / t160 / t158
  t170 = jnp.exp(-t60 * t50 * s2 * t162 / 0.24e2)
  t171 = 0.5e1 / 0.72e2 * t51 * s2 * t162 + t170
  t177 = f.my_piecewise3(t142, 0, 0.5e1 / 0.3e1 * t150 * t146)
  t183 = f.my_piecewise3(t142, t95, t150 * t141)
  t189 = f.my_piecewise3(t139, 0, 0.3e1 / 0.20e2 * t6 * t156 * t44 * t171 + t6 * t177 * t73 * t171 / 0.5e1 - t6 * t183 * t99 * t171 / 0.30e2)
  t199 = t24 ** 2
  t203 = 0.6e1 * t34 - 0.6e1 * t17 / t199
  t204 = f.my_piecewise5(t11, 0, t15, 0, t203)
  t208 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t204)
  t231 = 0.1e1 / t43 / t24
  t245 = s0 / t54 / t109 / r0
  t251 = t109 ** 2
  t259 = t47 ** 2
  t274 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t208 * t44 * t66 + 0.3e1 / 0.10e2 * t6 * t42 * t73 * t66 + 0.9e1 / 0.20e2 * t6 * t45 * t89 - t6 * t72 * t99 * t66 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t74 * t89 + 0.9e1 / 0.20e2 * t6 * t78 * t132 + 0.2e1 / 0.45e2 * t6 * t97 * t231 * t66 - t6 * t100 * t89 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t104 * t132 + 0.3e1 / 0.20e2 * t6 * t108 * (-0.770e3 / 0.243e3 * t51 * t245 + 0.154e3 / 0.81e2 * t85 * t245 * t65 - 0.11e2 / 0.81e2 * t123 * t124 / t53 / t251 * t65 + 0.2e1 / 0.243e3 * t118 * params.pg_mu / t259 * t124 * s0 / t251 / t79 * t65))
  t284 = f.my_piecewise5(t15, 0, t11, 0, -t203)
  t288 = f.my_piecewise3(t142, 0, -0.10e2 / 0.27e2 / t143 / t141 * t147 * t146 + 0.10e2 / 0.3e1 * t144 * t146 * t152 + 0.5e1 / 0.3e1 * t150 * t284)
  t306 = f.my_piecewise3(t139, 0, 0.3e1 / 0.20e2 * t6 * t288 * t44 * t171 + 0.3e1 / 0.10e2 * t6 * t156 * t73 * t171 - t6 * t177 * t99 * t171 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t183 * t231 * t171)
  d111 = 0.3e1 * t137 + 0.3e1 * t189 + t7 * (t274 + t306)

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
  t3 = t2 ** 2
  t4 = jnp.pi ** (0.1e1 / 0.3e1)
  t6 = t3 * t4 * jnp.pi
  t7 = r0 + r1
  t8 = 0.1e1 / t7
  t11 = 0.2e1 * r0 * t8 <= f.p.zeta_threshold
  t12 = f.p.zeta_threshold - 0.1e1
  t15 = 0.2e1 * r1 * t8 <= f.p.zeta_threshold
  t16 = -t12
  t17 = r0 - r1
  t18 = t17 * t8
  t19 = f.my_piecewise5(t11, t12, t15, t16, t18)
  t20 = 0.1e1 + t19
  t21 = t20 <= f.p.zeta_threshold
  t22 = t20 ** (0.1e1 / 0.3e1)
  t24 = 0.1e1 / t22 / t20
  t25 = t7 ** 2
  t26 = 0.1e1 / t25
  t28 = -t17 * t26 + t8
  t29 = f.my_piecewise5(t11, 0, t15, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t7
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t17 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t11, 0, t15, 0, t40)
  t44 = t22 ** 2
  t45 = t25 ** 2
  t46 = 0.1e1 / t45
  t49 = -0.6e1 * t17 * t46 + 0.6e1 * t37
  t50 = f.my_piecewise5(t11, 0, t15, 0, t49)
  t54 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 * t24 * t30 * t29 + 0.10e2 / 0.3e1 * t35 * t41 + 0.5e1 / 0.3e1 * t44 * t50)
  t55 = t7 ** (0.1e1 / 0.3e1)
  t56 = t55 ** 2
  t57 = t54 * t56
  t58 = 6 ** (0.1e1 / 0.3e1)
  t59 = jnp.pi ** 2
  t60 = t59 ** (0.1e1 / 0.3e1)
  t61 = t60 ** 2
  t62 = 0.1e1 / t61
  t63 = t58 * t62
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t68 = 0.1e1 / t66 / t64
  t72 = params.pg_mu * t58
  t77 = jnp.exp(-t72 * t62 * s0 * t68 / 0.24e2)
  t78 = 0.5e1 / 0.72e2 * t63 * s0 * t68 + t77
  t87 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t88 = 0.1e1 / t55
  t89 = t87 * t88
  t93 = t87 * t56
  t94 = t64 * r0
  t97 = s0 / t66 / t94
  t100 = t72 * t62
  t104 = -0.5e1 / 0.27e2 * t63 * t97 + t100 * t97 * t77 / 0.9e1
  t110 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t112 = 0.1e1 / t55 / t7
  t113 = t110 * t112
  t117 = t110 * t88
  t121 = t110 * t56
  t122 = t64 ** 2
  t125 = s0 / t66 / t122
  t131 = params.pg_mu ** 2
  t132 = t58 ** 2
  t136 = t131 * t132 / t60 / t59
  t137 = s0 ** 2
  t145 = 0.55e2 / 0.81e2 * t63 * t125 - 0.11e2 / 0.27e2 * t100 * t125 * t77 + t136 * t137 / t65 / t122 / t94 * t77 / 0.81e2
  t149 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t150 = t149 ** 2
  t151 = t150 * f.p.zeta_threshold
  t153 = f.my_piecewise3(t21, t151, t44 * t20)
  t155 = 0.1e1 / t55 / t25
  t156 = t153 * t155
  t160 = t153 * t112
  t164 = t153 * t88
  t168 = t153 * t56
  t172 = s0 / t66 / t122 / r0
  t178 = t122 ** 2
  t186 = t59 ** 2
  t187 = 0.1e1 / t186
  t188 = t131 * params.pg_mu * t187
  t189 = t137 * s0
  t196 = -0.770e3 / 0.243e3 * t63 * t172 + 0.154e3 / 0.81e2 * t100 * t172 * t77 - 0.11e2 / 0.81e2 * t136 * t137 / t65 / t178 * t77 + 0.2e1 / 0.243e3 * t188 * t189 / t178 / t94 * t77
  t201 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t78 + 0.3e1 / 0.10e2 * t6 * t89 * t78 + 0.9e1 / 0.20e2 * t6 * t93 * t104 - t6 * t113 * t78 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t117 * t104 + 0.9e1 / 0.20e2 * t6 * t121 * t145 + 0.2e1 / 0.45e2 * t6 * t156 * t78 - t6 * t160 * t104 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t164 * t145 + 0.3e1 / 0.20e2 * t6 * t168 * t196)
  t203 = r1 <= f.p.dens_threshold
  t204 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t205 = 0.1e1 + t204
  t206 = t205 <= f.p.zeta_threshold
  t207 = t205 ** (0.1e1 / 0.3e1)
  t209 = 0.1e1 / t207 / t205
  t211 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t212 = t211 ** 2
  t216 = 0.1e1 / t207
  t217 = t216 * t211
  t219 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t222 = t207 ** 2
  t224 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t228 = f.my_piecewise3(t206, 0, -0.10e2 / 0.27e2 * t209 * t212 * t211 + 0.10e2 / 0.3e1 * t217 * t219 + 0.5e1 / 0.3e1 * t222 * t224)
  t230 = r1 ** 2
  t231 = r1 ** (0.1e1 / 0.3e1)
  t232 = t231 ** 2
  t234 = 0.1e1 / t232 / t230
  t242 = jnp.exp(-t72 * t62 * s2 * t234 / 0.24e2)
  t243 = 0.5e1 / 0.72e2 * t63 * s2 * t234 + t242
  t252 = f.my_piecewise3(t206, 0, 0.10e2 / 0.9e1 * t216 * t212 + 0.5e1 / 0.3e1 * t222 * t219)
  t259 = f.my_piecewise3(t206, 0, 0.5e1 / 0.3e1 * t222 * t211)
  t265 = f.my_piecewise3(t206, t151, t222 * t205)
  t271 = f.my_piecewise3(t203, 0, 0.3e1 / 0.20e2 * t6 * t228 * t56 * t243 + 0.3e1 / 0.10e2 * t6 * t252 * t88 * t243 - t6 * t259 * t112 * t243 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t265 * t155 * t243)
  t273 = t20 ** 2
  t276 = t30 ** 2
  t282 = t41 ** 2
  t291 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t292 = f.my_piecewise5(t11, 0, t15, 0, t291)
  t296 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t273 * t276 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t282 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t292)
  t328 = t122 * t64
  t331 = s0 / t66 / t328
  t350 = t131 ** 2
  t352 = t137 ** 2
  t379 = 0.1e1 / t55 / t36
  t384 = 0.3e1 / 0.20e2 * t6 * t296 * t56 * t78 + 0.3e1 / 0.5e1 * t6 * t57 * t104 + 0.6e1 / 0.5e1 * t6 * t89 * t104 + 0.9e1 / 0.10e2 * t6 * t93 * t145 - 0.2e1 / 0.5e1 * t6 * t113 * t104 + 0.6e1 / 0.5e1 * t6 * t117 * t145 + 0.3e1 / 0.5e1 * t6 * t121 * t196 + 0.8e1 / 0.45e2 * t6 * t156 * t104 - t6 * t160 * t145 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t164 * t196 + 0.3e1 / 0.20e2 * t6 * t168 * (0.13090e5 / 0.729e3 * t63 * t331 - 0.2618e4 / 0.243e3 * t100 * t331 * t77 + 0.979e3 / 0.729e3 * t136 * t137 / t65 / t178 / r0 * t77 - 0.44e2 / 0.243e3 * t188 * t189 / t178 / t122 * t77 + 0.2e1 / 0.2187e4 * t350 * t187 * t352 / t66 / t178 / t328 * t58 * t62 * t77) + 0.2e1 / 0.5e1 * t6 * t54 * t88 * t78 - t6 * t87 * t112 * t78 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t110 * t155 * t78 - 0.14e2 / 0.135e3 * t6 * t153 * t379 * t78
  t385 = f.my_piecewise3(t1, 0, t384)
  t386 = t205 ** 2
  t389 = t212 ** 2
  t395 = t219 ** 2
  t401 = f.my_piecewise5(t15, 0, t11, 0, -t291)
  t405 = f.my_piecewise3(t206, 0, 0.40e2 / 0.81e2 / t207 / t386 * t389 - 0.20e2 / 0.9e1 * t209 * t212 * t219 + 0.10e2 / 0.3e1 * t216 * t395 + 0.40e2 / 0.9e1 * t217 * t224 + 0.5e1 / 0.3e1 * t222 * t401)
  t427 = f.my_piecewise3(t203, 0, 0.3e1 / 0.20e2 * t6 * t405 * t56 * t243 + 0.2e1 / 0.5e1 * t6 * t228 * t88 * t243 - t6 * t252 * t112 * t243 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t259 * t155 * t243 - 0.14e2 / 0.135e3 * t6 * t265 * t379 * t243)
  d1111 = 0.4e1 * t201 + 0.4e1 * t271 + t7 * (t385 + t427)

  res = {'v4rho4': d1111}
  return res
