"""Generated from lda_k_gds08_worker.mpl."""

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
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))

  gds08_fs = lambda rs, z: (1 + z) / 2 * (+params_A + params_B * jnp.log(2 * f.n_spin(rs, z)) + params_C * jnp.log(2 * f.n_spin(rs, z)) ** 2)

  gds08_f = lambda rs, z: +f.my_piecewise3(f.screen_dens(rs, z), 0, gds08_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens(rs, -z), 0, gds08_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: gds08_f(rs, z)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res

def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))

  gds08_fs = lambda rs, z: (1 + z) / 2 * (+params_A + params_B * jnp.log(2 * f.n_spin(rs, z)) + params_C * jnp.log(2 * f.n_spin(rs, z)) ** 2)

  gds08_f = lambda rs, z: +f.my_piecewise3(f.screen_dens(rs, z), 0, gds08_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens(rs, -z), 0, gds08_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: gds08_f(rs, z)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))

  gds08_fs = lambda rs, z: (1 + z) / 2 * (+params_A + params_B * jnp.log(2 * f.n_spin(rs, z)) + params_C * jnp.log(2 * f.n_spin(rs, z)) ** 2)

  gds08_f = lambda rs, z: +f.my_piecewise3(f.screen_dens(rs, z), 0, gds08_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens(rs, -z), 0, gds08_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: gds08_f(rs, z)

  t1 = r0 <= f.p.dens_threshold
  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t8 = f.p.zeta_threshold - 0.1e1
  t10 = 0.1e1 - t5 <= f.p.zeta_threshold
  t11 = -t8
  t12 = f.my_piecewise5(t7, t8, t10, t11, t5)
  t14 = 0.1e1 / 0.2e1 + t12 / 0.2e1
  t17 = 0.2e1 * r0 * t4 <= f.p.zeta_threshold
  t20 = 0.2e1 * r1 * t4 <= f.p.zeta_threshold
  t21 = f.my_piecewise5(t17, t8, t20, t11, t5)
  t22 = 0.1e1 + t21
  t24 = jnp.log(t22 * t3)
  t26 = t24 ** 2
  t28 = params.B * t24 + params.C * t26 + params.A
  t30 = f.my_piecewise3(t1, 0, t14 * t28)
  t31 = r1 <= f.p.dens_threshold
  t32 = f.my_piecewise5(t10, t8, t7, t11, -t5)
  t34 = 0.1e1 / 0.2e1 + t32 / 0.2e1
  t35 = f.my_piecewise5(t20, t8, t17, t11, -t5)
  t36 = 0.1e1 + t35
  t38 = jnp.log(t36 * t3)
  t40 = t38 ** 2
  t42 = params.B * t38 + params.C * t40 + params.A
  t44 = f.my_piecewise3(t31, 0, t34 * t42)
  t45 = t3 ** 2
  t47 = t2 / t45
  t48 = t4 - t47
  t49 = f.my_piecewise5(t7, 0, t10, 0, t48)
  t52 = f.my_piecewise5(t17, 0, t20, 0, t48)
  t54 = t52 * t3 + t21 + 0.1e1
  t56 = 0.1e1 / t22
  t57 = t56 * t4
  t59 = params.C * t24
  t67 = f.my_piecewise3(t1, 0, t49 * t28 / 0.2e1 + t14 * (0.2e1 * t59 * t54 * t56 * t4 + params.B * t54 * t57))
  t68 = -t48
  t69 = f.my_piecewise5(t10, 0, t7, 0, t68)
  t72 = f.my_piecewise5(t20, 0, t17, 0, t68)
  t74 = t72 * t3 + t35 + 0.1e1
  t76 = 0.1e1 / t36
  t77 = t76 * t4
  t79 = params.C * t38
  t87 = f.my_piecewise3(t31, 0, t69 * t42 / 0.2e1 + t34 * (0.2e1 * t79 * t74 * t76 * t4 + params.B * t74 * t77))
  vrho_0_ = t30 + t44 + t3 * (t67 + t87)
  t90 = -t4 - t47
  t91 = f.my_piecewise5(t7, 0, t10, 0, t90)
  t94 = f.my_piecewise5(t17, 0, t20, 0, t90)
  t96 = t94 * t3 + t21 + 0.1e1
  t106 = f.my_piecewise3(t1, 0, t91 * t28 / 0.2e1 + t14 * (0.2e1 * t59 * t96 * t56 * t4 + params.B * t96 * t57))
  t107 = -t90
  t108 = f.my_piecewise5(t10, 0, t7, 0, t107)
  t111 = f.my_piecewise5(t20, 0, t17, 0, t107)
  t113 = t111 * t3 + t35 + 0.1e1
  t123 = f.my_piecewise3(t31, 0, t108 * t42 / 0.2e1 + t34 * (0.2e1 * t79 * t113 * t76 * t4 + params.B * t113 * t77))
  vrho_1_ = t30 + t44 + t3 * (t106 + t123)
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  vrho_1_ = _b(vrho_1_)
  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res

def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_A_raw = params.A
  if isinstance(params_A_raw, (str, bytes, dict)):
    params_A = params_A_raw
  else:
    try:
      params_A_seq = list(params_A_raw)
    except TypeError:
      params_A = params_A_raw
    else:
      params_A_seq = np.asarray(params_A_seq, dtype=np.float64)
      params_A = np.concatenate((np.array([np.nan], dtype=np.float64), params_A_seq))
  params_B_raw = params.B
  if isinstance(params_B_raw, (str, bytes, dict)):
    params_B = params_B_raw
  else:
    try:
      params_B_seq = list(params_B_raw)
    except TypeError:
      params_B = params_B_raw
    else:
      params_B_seq = np.asarray(params_B_seq, dtype=np.float64)
      params_B = np.concatenate((np.array([np.nan], dtype=np.float64), params_B_seq))
  params_C_raw = params.C
  if isinstance(params_C_raw, (str, bytes, dict)):
    params_C = params_C_raw
  else:
    try:
      params_C_seq = list(params_C_raw)
    except TypeError:
      params_C = params_C_raw
    else:
      params_C_seq = np.asarray(params_C_seq, dtype=np.float64)
      params_C = np.concatenate((np.array([np.nan], dtype=np.float64), params_C_seq))

  gds08_fs = lambda rs, z: (1 + z) / 2 * (+params_A + params_B * jnp.log(2 * f.n_spin(rs, z)) + params_C * jnp.log(2 * f.n_spin(rs, z)) ** 2)

  gds08_f = lambda rs, z: +f.my_piecewise3(f.screen_dens(rs, z), 0, gds08_fs(rs, f.z_thr(z))) + f.my_piecewise3(f.screen_dens(rs, -z), 0, gds08_fs(rs, f.z_thr(-z)))

  functional_body = lambda rs, z: gds08_f(rs, z)

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t8 = t7 / 0.2e1
  t10 = jnp.log(t7 * r0)
  t12 = t10 ** 2
  t16 = f.my_piecewise3(t2, 0, t8 * (params.B * t10 + params.C * t12 + params.A))
  t17 = 0.1e1 / r0
  t24 = f.my_piecewise3(t2, 0, t8 * (0.2e1 * params.C * t10 * t17 + params.B * t17))
  vrho_0_ = 0.2e1 * r0 * t24 + 0.2e1 * t16
  _b = lambda x: (jnp.asarray(x) + jnp.zeros_like(r0))
  vrho_0_ = _b(vrho_0_)
  res = {'vrho': vrho_0_}
  return res

def unpol_fxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  
  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t8 = 0.1e1 / r0
  t11 = jnp.log(t7 * r0)
  t12 = params.C * t11
  t18 = f.my_piecewise3(t2, 0, t7 * (0.2e1 * t12 * t8 + params.B * t8) / 0.2e1)
  t20 = r0 ** 2
  t21 = 0.1e1 / t20
  t30 = f.my_piecewise3(t2, 0, t7 * (-0.2e1 * t12 * t21 - params.B * t21 + 0.2e1 * params.C * t21) / 0.2e1)
  v2rho2_0_ = 0.2e1 * r0 * t30 + 0.4e1 * t18
  res = {'v2rho2': v2rho2_0_}
  return res

def unpol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t8 = r0 ** 2
  t9 = 0.1e1 / t8
  t14 = jnp.log(t7 * r0)
  t15 = params.C * t14
  t21 = f.my_piecewise3(t2, 0, t7 * (-0.2e1 * t15 * t9 - params.B * t9 + 0.2e1 * params.C * t9) / 0.2e1)
  t24 = 0.1e1 / t8 / r0
  t34 = f.my_piecewise3(t2, 0, t7 * (0.4e1 * t15 * t24 + 0.2e1 * params.B * t24 - 0.6e1 * params.C * t24) / 0.2e1)
  v3rho3_0_ = 0.2e1 * r0 * t34 + 0.6e1 * t21

  res = {'v3rho3': v3rho3_0_}
  return res

def unpol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t2 = r0 / 0.2e1 <= f.p.dens_threshold
  t3 = 0.1e1 <= f.p.zeta_threshold
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t3, t4, t3, -t4, 0)
  t7 = 0.1e1 + t6
  t8 = r0 ** 2
  t10 = 0.1e1 / t8 / r0
  t16 = jnp.log(t7 * r0)
  t17 = params.C * t16
  t23 = f.my_piecewise3(t2, 0, t7 * (0.4e1 * t17 * t10 + 0.2e1 * params.B * t10 - 0.6e1 * params.C * t10) / 0.2e1)
  t25 = t8 ** 2
  t26 = 0.1e1 / t25
  t36 = f.my_piecewise3(t2, 0, t7 * (-0.12e2 * t17 * t26 - 0.6e1 * params.B * t26 + 0.22e2 * params.C * t26) / 0.2e1)
  v4rho4_0_ = 0.2e1 * r0 * t36 + 0.8e1 * t23

  res = {'v4rho4': v4rho4_0_}
  return res

def pol_fxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau
  
  t1 = r0 <= f.p.dens_threshold
  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t9 = 0.1e1 - t5 <= f.p.zeta_threshold
  t10 = t3 ** 2
  t11 = 0.1e1 / t10
  t12 = t2 * t11
  t13 = t4 - t12
  t14 = f.my_piecewise5(t7, 0, t9, 0, t13)
  t17 = 0.2e1 * r0 * t4 <= f.p.zeta_threshold
  t18 = f.p.zeta_threshold - 0.1e1
  t21 = 0.2e1 * r1 * t4 <= f.p.zeta_threshold
  t22 = -t18
  t23 = f.my_piecewise5(t17, t18, t21, t22, t5)
  t24 = 0.1e1 + t23
  t26 = jnp.log(t24 * t3)
  t28 = t26 ** 2
  t30 = params.B * t26 + params.C * t28 + params.A
  t32 = f.my_piecewise5(t7, t18, t9, t22, t5)
  t33 = 0.1e1 + t32
  t34 = f.my_piecewise5(t17, 0, t21, 0, t13)
  t36 = t34 * t3 + t23 + 0.1e1
  t37 = params.B * t36
  t38 = 0.1e1 / t24
  t39 = t38 * t4
  t41 = params.C * t26
  t42 = t36 * t38
  t46 = 0.2e1 * t41 * t42 * t4 + t37 * t39
  t50 = f.my_piecewise3(t1, 0, t14 * t30 / 0.2e1 + t33 * t46 / 0.2e1)
  t52 = r1 <= f.p.dens_threshold
  t53 = -t13
  t54 = f.my_piecewise5(t9, 0, t7, 0, t53)
  t55 = f.my_piecewise5(t21, t18, t17, t22, -t5)
  t56 = 0.1e1 + t55
  t58 = jnp.log(t56 * t3)
  t60 = t58 ** 2
  t62 = params.B * t58 + params.C * t60 + params.A
  t64 = f.my_piecewise5(t9, t18, t7, t22, -t5)
  t65 = 0.1e1 + t64
  t66 = f.my_piecewise5(t21, 0, t17, 0, t53)
  t68 = t66 * t3 + t55 + 0.1e1
  t69 = params.B * t68
  t70 = 0.1e1 / t56
  t71 = t70 * t4
  t73 = params.C * t58
  t74 = t68 * t70
  t78 = 0.2e1 * t73 * t74 * t4 + t69 * t71
  t82 = f.my_piecewise3(t52, 0, t54 * t62 / 0.2e1 + t65 * t78 / 0.2e1)
  t86 = t2 / t10 / t3
  t88 = -0.2e1 * t11 + 0.2e1 * t86
  t89 = f.my_piecewise5(t7, 0, t9, 0, t88)
  t93 = f.my_piecewise5(t17, 0, t21, 0, t88)
  t96 = t93 * t3 + 0.2e1 * t34
  t99 = t24 ** 2
  t100 = 0.1e1 / t99
  t101 = t100 * t4
  t102 = t101 * t34
  t104 = t38 * t11
  t106 = t36 ** 2
  t108 = t100 * t11
  t125 = f.my_piecewise3(t1, 0, t89 * t30 / 0.2e1 + t14 * t46 + t33 * (0.2e1 * t41 * t96 * t38 * t4 - 0.2e1 * t41 * t36 * t102 + 0.2e1 * params.C * t106 * t108 - 0.2e1 * t41 * t42 * t11 + params.B * t96 * t39 - t37 * t102 - t37 * t104) / 0.2e1)
  t126 = -t88
  t127 = f.my_piecewise5(t9, 0, t7, 0, t126)
  t131 = f.my_piecewise5(t21, 0, t17, 0, t126)
  t134 = t131 * t3 + 0.2e1 * t66
  t137 = t56 ** 2
  t138 = 0.1e1 / t137
  t139 = t138 * t4
  t140 = t139 * t66
  t142 = t70 * t11
  t144 = t68 ** 2
  t146 = t138 * t11
  t163 = f.my_piecewise3(t52, 0, t127 * t62 / 0.2e1 + t54 * t78 + t65 * (0.2e1 * t73 * t134 * t70 * t4 - 0.2e1 * t73 * t74 * t11 + params.B * t134 * t71 - 0.2e1 * t73 * t68 * t140 + 0.2e1 * params.C * t144 * t146 - t69 * t140 - t69 * t142) / 0.2e1)
  d11 = 0.2e1 * t50 + 0.2e1 * t82 + t3 * (t125 + t163)
  t166 = -t4 - t12
  t167 = f.my_piecewise5(t7, 0, t9, 0, t166)
  t169 = f.my_piecewise5(t17, 0, t21, 0, t166)
  t171 = t169 * t3 + t23 + 0.1e1
  t172 = params.B * t171
  t174 = t171 * t38
  t178 = 0.2e1 * t41 * t174 * t4 + t172 * t39
  t182 = f.my_piecewise3(t1, 0, t167 * t30 / 0.2e1 + t33 * t178 / 0.2e1)
  t183 = -t166
  t184 = f.my_piecewise5(t9, 0, t7, 0, t183)
  t186 = f.my_piecewise5(t21, 0, t17, 0, t183)
  t188 = t186 * t3 + t55 + 0.1e1
  t189 = params.B * t188
  t191 = t188 * t70
  t195 = 0.2e1 * t73 * t191 * t4 + t189 * t71
  t199 = f.my_piecewise3(t52, 0, t184 * t62 / 0.2e1 + t65 * t195 / 0.2e1)
  t200 = 0.2e1 * t86
  t201 = f.my_piecewise5(t7, 0, t9, 0, t200)
  t205 = f.my_piecewise5(t17, 0, t21, 0, t200)
  t207 = t205 * t3 + t169 + t34
  t211 = t172 * t104
  t220 = t41 * t171
  t225 = 0.2e1 * t41 * t174 * t11
  t230 = f.my_piecewise3(t1, 0, t201 * t30 / 0.2e1 + t167 * t46 / 0.2e1 + t14 * t178 / 0.2e1 + t33 * (0.2e1 * params.C * t36 * t108 * t171 + 0.2e1 * t41 * t207 * t38 * t4 + params.B * t207 * t39 - t172 * t102 - 0.2e1 * t220 * t102 - t211 - t225) / 0.2e1)
  t231 = f.my_piecewise5(t9, 0, t7, 0, -t200)
  t235 = f.my_piecewise5(t21, 0, t17, 0, -t200)
  t237 = t235 * t3 + t186 + t66
  t241 = t189 * t142
  t250 = t73 * t188
  t255 = 0.2e1 * t73 * t191 * t11
  t260 = f.my_piecewise3(t52, 0, t231 * t62 / 0.2e1 + t184 * t78 / 0.2e1 + t54 * t195 / 0.2e1 + t65 * (0.2e1 * params.C * t68 * t146 * t188 + 0.2e1 * t73 * t237 * t70 * t4 + params.B * t237 * t71 - t189 * t140 - 0.2e1 * t250 * t140 - t241 - t255) / 0.2e1)
  d12 = t50 + t82 + t182 + t199 + t3 * (t230 + t260)
  t266 = 0.2e1 * t11 + 0.2e1 * t86
  t267 = f.my_piecewise5(t7, 0, t9, 0, t266)
  t271 = f.my_piecewise5(t17, 0, t21, 0, t266)
  t274 = t271 * t3 + 0.2e1 * t169
  t277 = t101 * t169
  t279 = t171 ** 2
  t293 = f.my_piecewise3(t1, 0, t267 * t30 / 0.2e1 + t167 * t178 + t33 * (0.2e1 * t41 * t274 * t38 * t4 + 0.2e1 * params.C * t279 * t108 + params.B * t274 * t39 - t172 * t277 - 0.2e1 * t220 * t277 - t211 - t225) / 0.2e1)
  t294 = -t266
  t295 = f.my_piecewise5(t9, 0, t7, 0, t294)
  t299 = f.my_piecewise5(t21, 0, t17, 0, t294)
  t302 = t299 * t3 + 0.2e1 * t186
  t305 = t139 * t186
  t307 = t188 ** 2
  t321 = f.my_piecewise3(t52, 0, t295 * t62 / 0.2e1 + t184 * t195 + t65 * (0.2e1 * t73 * t302 * t70 * t4 + 0.2e1 * params.C * t307 * t146 + params.B * t302 * t71 - t189 * t305 - 0.2e1 * t250 * t305 - t241 - t255) / 0.2e1)
  d22 = 0.2e1 * t182 + 0.2e1 * t199 + t3 * (t293 + t321)
  res = {'v2rho2': jnp.stack([d11, d12, d22], axis=-1) if 'd12' in locals() else d11}
  return res

def pol_kxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 <= f.p.dens_threshold
  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t9 = 0.1e1 - t5 <= f.p.zeta_threshold
  t10 = t3 ** 2
  t11 = 0.1e1 / t10
  t13 = 0.1e1 / t10 / t3
  t16 = 0.2e1 * t2 * t13 - 0.2e1 * t11
  t17 = f.my_piecewise5(t7, 0, t9, 0, t16)
  t20 = 0.2e1 * r0 * t4 <= f.p.zeta_threshold
  t21 = f.p.zeta_threshold - 0.1e1
  t24 = 0.2e1 * r1 * t4 <= f.p.zeta_threshold
  t25 = -t21
  t26 = f.my_piecewise5(t20, t21, t24, t25, t5)
  t27 = 0.1e1 + t26
  t29 = jnp.log(t27 * t3)
  t31 = t29 ** 2
  t33 = params.B * t29 + params.C * t31 + params.A
  t37 = -t2 * t11 + t4
  t38 = f.my_piecewise5(t7, 0, t9, 0, t37)
  t39 = f.my_piecewise5(t20, 0, t24, 0, t37)
  t41 = t39 * t3 + t26 + 0.1e1
  t42 = params.B * t41
  t43 = 0.1e1 / t27
  t44 = t43 * t4
  t46 = params.C * t29
  t47 = t41 * t43
  t51 = 0.2e1 * t46 * t47 * t4 + t42 * t44
  t53 = f.my_piecewise5(t7, t21, t9, t25, t5)
  t54 = 0.1e1 + t53
  t55 = f.my_piecewise5(t20, 0, t24, 0, t16)
  t58 = t55 * t3 + 0.2e1 * t39
  t59 = params.B * t58
  t61 = t27 ** 2
  t62 = 0.1e1 / t61
  t63 = t62 * t4
  t64 = t63 * t39
  t66 = t43 * t11
  t68 = t41 ** 2
  t69 = params.C * t68
  t70 = t62 * t11
  t73 = t58 * t43
  t77 = t46 * t41
  t83 = -0.2e1 * t46 * t47 * t11 + 0.2e1 * t46 * t73 * t4 - t42 * t64 - t42 * t66 + t59 * t44 - 0.2e1 * t77 * t64 + 0.2e1 * t69 * t70
  t87 = f.my_piecewise3(t1, 0, t17 * t33 / 0.2e1 + t38 * t51 + t54 * t83 / 0.2e1)
  t89 = r1 <= f.p.dens_threshold
  t90 = -t16
  t91 = f.my_piecewise5(t9, 0, t7, 0, t90)
  t92 = f.my_piecewise5(t24, t21, t20, t25, -t5)
  t93 = 0.1e1 + t92
  t95 = jnp.log(t93 * t3)
  t97 = t95 ** 2
  t99 = params.B * t95 + params.C * t97 + params.A
  t102 = -t37
  t103 = f.my_piecewise5(t9, 0, t7, 0, t102)
  t104 = f.my_piecewise5(t24, 0, t20, 0, t102)
  t106 = t104 * t3 + t92 + 0.1e1
  t107 = params.B * t106
  t108 = 0.1e1 / t93
  t109 = t108 * t4
  t111 = params.C * t95
  t112 = t106 * t108
  t116 = 0.2e1 * t111 * t112 * t4 + t107 * t109
  t118 = f.my_piecewise5(t9, t21, t7, t25, -t5)
  t119 = 0.1e1 + t118
  t120 = f.my_piecewise5(t24, 0, t20, 0, t90)
  t123 = t120 * t3 + 0.2e1 * t104
  t124 = params.B * t123
  t126 = t93 ** 2
  t127 = 0.1e1 / t126
  t128 = t127 * t4
  t129 = t128 * t104
  t131 = t108 * t11
  t133 = t106 ** 2
  t134 = params.C * t133
  t135 = t127 * t11
  t138 = t123 * t108
  t142 = t111 * t106
  t148 = -0.2e1 * t111 * t112 * t11 + 0.2e1 * t111 * t138 * t4 - t107 * t129 - t107 * t131 + t124 * t109 - 0.2e1 * t142 * t129 + 0.2e1 * t134 * t135
  t152 = f.my_piecewise3(t89, 0, t91 * t99 / 0.2e1 + t103 * t116 + t119 * t148 / 0.2e1)
  t154 = t10 ** 2
  t158 = 0.6e1 * t13 - 0.6e1 * t2 / t154
  t159 = f.my_piecewise5(t7, 0, t9, 0, t158)
  t167 = 0.1e1 / t61 / t27
  t169 = t39 ** 2
  t170 = t167 * t4 * t169
  t173 = t70 * t39
  t180 = t63 * t55
  t196 = f.my_piecewise5(t20, 0, t24, 0, t158)
  t199 = t196 * t3 + 0.3e1 * t55
  t221 = -0.6e1 * t69 * t167 * t11 * t39 + 0.2e1 * t46 * t199 * t43 * t4 + 0.6e1 * params.C * t41 * t70 * t58 - 0.4e1 * t46 * t73 * t11 + 0.2e1 * t42 * t43 * t13 + 0.4e1 * t46 * t47 * t13 - 0.6e1 * t69 * t62 * t13 + params.B * t199 * t44 - 0.4e1 * t46 * t58 * t64 + 0.2e1 * t42 * t170 + 0.4e1 * t77 * t170 + 0.2e1 * t42 * t173 + 0.4e1 * t77 * t173 - t42 * t180 - 0.2e1 * t77 * t180 - 0.2e1 * t59 * t64 - 0.2e1 * t59 * t66
  t225 = f.my_piecewise3(t1, 0, t159 * t33 / 0.2e1 + 0.3e1 / 0.2e1 * t17 * t51 + 0.3e1 / 0.2e1 * t38 * t83 + t54 * t221 / 0.2e1)
  t226 = -t158
  t227 = f.my_piecewise5(t9, 0, t7, 0, t226)
  t235 = 0.1e1 / t126 / t93
  t237 = t104 ** 2
  t238 = t235 * t4 * t237
  t241 = t135 * t104
  t248 = t128 * t120
  t264 = f.my_piecewise5(t24, 0, t20, 0, t226)
  t267 = t264 * t3 + 0.3e1 * t120
  t289 = -0.6e1 * t134 * t235 * t11 * t104 + 0.6e1 * params.C * t106 * t135 * t123 + 0.2e1 * t111 * t267 * t108 * t4 + 0.2e1 * t107 * t108 * t13 + params.B * t267 * t109 - 0.4e1 * t111 * t138 * t11 + 0.4e1 * t111 * t112 * t13 - 0.4e1 * t111 * t123 * t129 - 0.6e1 * t134 * t127 * t13 + 0.2e1 * t107 * t238 + 0.2e1 * t107 * t241 - t107 * t248 - 0.2e1 * t124 * t129 - 0.2e1 * t124 * t131 + 0.4e1 * t142 * t238 + 0.4e1 * t142 * t241 - 0.2e1 * t142 * t248
  t293 = f.my_piecewise3(t89, 0, t227 * t99 / 0.2e1 + 0.3e1 / 0.2e1 * t91 * t116 + 0.3e1 / 0.2e1 * t103 * t148 + t119 * t289 / 0.2e1)
  d111 = 0.3e1 * t87 + 0.3e1 * t152 + t3 * (t225 + t293)

  res = {'v3rho3': d111}
  return res

def pol_lxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  (r0, r1) = r

  t1 = r0 <= f.p.dens_threshold
  t2 = r0 - r1
  t3 = r0 + r1
  t4 = 0.1e1 / t3
  t5 = t2 * t4
  t7 = 0.1e1 + t5 <= f.p.zeta_threshold
  t9 = 0.1e1 - t5 <= f.p.zeta_threshold
  t10 = t3 ** 2
  t12 = 0.1e1 / t10 / t3
  t13 = t10 ** 2
  t14 = 0.1e1 / t13
  t17 = -0.6e1 * t2 * t14 + 0.6e1 * t12
  t18 = f.my_piecewise5(t7, 0, t9, 0, t17)
  t21 = 0.2e1 * r0 * t4 <= f.p.zeta_threshold
  t22 = f.p.zeta_threshold - 0.1e1
  t25 = 0.2e1 * r1 * t4 <= f.p.zeta_threshold
  t26 = -t22
  t27 = f.my_piecewise5(t21, t22, t25, t26, t5)
  t28 = 0.1e1 + t27
  t30 = jnp.log(t28 * t3)
  t32 = t30 ** 2
  t34 = params.B * t30 + params.C * t32 + params.A
  t37 = 0.1e1 / t10
  t40 = 0.2e1 * t2 * t12 - 0.2e1 * t37
  t41 = f.my_piecewise5(t7, 0, t9, 0, t40)
  t43 = -t2 * t37 + t4
  t44 = f.my_piecewise5(t21, 0, t25, 0, t43)
  t46 = t44 * t3 + t27 + 0.1e1
  t47 = params.B * t46
  t48 = 0.1e1 / t28
  t49 = t48 * t4
  t51 = params.C * t30
  t52 = t46 * t48
  t56 = 0.2e1 * t51 * t52 * t4 + t47 * t49
  t59 = f.my_piecewise5(t7, 0, t9, 0, t43)
  t60 = f.my_piecewise5(t21, 0, t25, 0, t40)
  t63 = t60 * t3 + 0.2e1 * t44
  t64 = params.B * t63
  t66 = t28 ** 2
  t67 = 0.1e1 / t66
  t68 = t67 * t4
  t69 = t68 * t44
  t71 = t48 * t37
  t73 = t46 ** 2
  t74 = params.C * t73
  t75 = t67 * t37
  t78 = t63 * t48
  t82 = t51 * t46
  t88 = -0.2e1 * t51 * t52 * t37 + 0.2e1 * t51 * t78 * t4 - t47 * t69 - t47 * t71 + t64 * t49 - 0.2e1 * t82 * t69 + 0.2e1 * t74 * t75
  t91 = f.my_piecewise5(t7, t22, t9, t26, t5)
  t92 = 0.1e1 + t91
  t94 = 0.1e1 / t66 / t28
  t95 = t94 * t4
  t96 = t44 ** 2
  t97 = t95 * t96
  t100 = t75 * t44
  t107 = t68 * t60
  t109 = t48 * t12
  t112 = params.C * t46
  t116 = t94 * t37
  t120 = t67 * t12
  t123 = f.my_piecewise5(t21, 0, t25, 0, t17)
  t126 = t123 * t3 + 0.3e1 * t60
  t127 = t126 * t48
  t131 = params.B * t126
  t137 = t51 * t63
  t148 = 0.6e1 * t112 * t75 * t63 - 0.6e1 * t74 * t116 * t44 + 0.4e1 * t51 * t52 * t12 + 0.2e1 * t51 * t127 * t4 - 0.4e1 * t51 * t78 * t37 + 0.2e1 * t47 * t100 + 0.4e1 * t82 * t100 - t47 * t107 - 0.2e1 * t82 * t107 + 0.2e1 * t47 * t109 - 0.6e1 * t74 * t120 + t131 * t49 - 0.4e1 * t137 * t69 + 0.2e1 * t47 * t97 - 0.2e1 * t64 * t69 - 0.2e1 * t64 * t71 + 0.4e1 * t82 * t97
  t152 = f.my_piecewise3(t1, 0, t18 * t34 / 0.2e1 + 0.3e1 / 0.2e1 * t41 * t56 + 0.3e1 / 0.2e1 * t59 * t88 + t92 * t148 / 0.2e1)
  t154 = r1 <= f.p.dens_threshold
  t155 = -t17
  t156 = f.my_piecewise5(t9, 0, t7, 0, t155)
  t157 = f.my_piecewise5(t25, t22, t21, t26, -t5)
  t158 = 0.1e1 + t157
  t160 = jnp.log(t158 * t3)
  t162 = t160 ** 2
  t164 = params.B * t160 + params.C * t162 + params.A
  t167 = -t40
  t168 = f.my_piecewise5(t9, 0, t7, 0, t167)
  t169 = -t43
  t170 = f.my_piecewise5(t25, 0, t21, 0, t169)
  t172 = t170 * t3 + t157 + 0.1e1
  t173 = params.B * t172
  t174 = 0.1e1 / t158
  t175 = t174 * t4
  t177 = params.C * t160
  t178 = t172 * t174
  t182 = 0.2e1 * t177 * t178 * t4 + t173 * t175
  t185 = f.my_piecewise5(t9, 0, t7, 0, t169)
  t186 = f.my_piecewise5(t25, 0, t21, 0, t167)
  t189 = t186 * t3 + 0.2e1 * t170
  t190 = params.B * t189
  t192 = t158 ** 2
  t193 = 0.1e1 / t192
  t194 = t193 * t4
  t195 = t194 * t170
  t197 = t174 * t37
  t199 = t172 ** 2
  t200 = params.C * t199
  t201 = t193 * t37
  t204 = t189 * t174
  t208 = t177 * t172
  t214 = -0.2e1 * t177 * t178 * t37 + 0.2e1 * t177 * t204 * t4 - t173 * t195 - t173 * t197 + t190 * t175 - 0.2e1 * t208 * t195 + 0.2e1 * t200 * t201
  t217 = f.my_piecewise5(t9, t22, t7, t26, -t5)
  t218 = 0.1e1 + t217
  t220 = 0.1e1 / t192 / t158
  t221 = t220 * t4
  t222 = t170 ** 2
  t223 = t221 * t222
  t226 = t201 * t170
  t233 = t194 * t186
  t235 = t174 * t12
  t238 = params.C * t172
  t242 = t220 * t37
  t246 = t193 * t12
  t249 = f.my_piecewise5(t25, 0, t21, 0, t155)
  t252 = t249 * t3 + 0.3e1 * t186
  t253 = t252 * t174
  t257 = params.B * t252
  t263 = t177 * t189
  t274 = 0.4e1 * t177 * t178 * t12 - 0.6e1 * t200 * t242 * t170 - 0.4e1 * t177 * t204 * t37 + 0.2e1 * t177 * t253 * t4 + 0.6e1 * t238 * t201 * t189 + 0.2e1 * t173 * t223 + 0.2e1 * t173 * t226 - t173 * t233 + 0.2e1 * t173 * t235 + t257 * t175 - 0.2e1 * t190 * t195 - 0.2e1 * t190 * t197 - 0.4e1 * t263 * t195 - 0.6e1 * t200 * t246 + 0.4e1 * t208 * t223 + 0.4e1 * t208 * t226 - 0.2e1 * t208 * t233
  t278 = f.my_piecewise3(t154, 0, t156 * t164 / 0.2e1 + 0.3e1 / 0.2e1 * t168 * t182 + 0.3e1 / 0.2e1 * t185 * t214 + t218 * t274 / 0.2e1)
  t284 = -0.24e2 * t14 + 0.24e2 * t2 / t13 / t3
  t285 = f.my_piecewise5(t7, 0, t9, 0, t284)
  t297 = t66 ** 2
  t298 = 0.1e1 / t297
  t307 = f.my_piecewise5(t21, 0, t25, 0, t284)
  t310 = t307 * t3 + 0.4e1 * t123
  t319 = t68 * t123
  t321 = t120 * t44
  t334 = t75 * t60
  t345 = t298 * t4 * t96 * t44
  t348 = t116 * t96
  t354 = -0.12e2 * t51 * t52 * t14 + 0.22e2 * t74 * t298 * t37 * t96 + 0.28e2 * t74 * t94 * t12 * t44 + 0.2e1 * t51 * t310 * t48 * t4 - 0.3e1 * t131 * t69 - 0.3e1 * t64 * t107 - t47 * t319 - 0.6e1 * t47 * t321 + 0.8e1 * t112 * t75 * t126 - 0.8e1 * t74 * t116 * t60 + 0.6e1 * t64 * t97 + 0.6e1 * t64 * t100 + 0.3e1 * t47 * t334 - 0.28e2 * t112 * t120 * t63 - 0.6e1 * t51 * t127 * t37 - 0.6e1 * t47 * t345 - 0.6e1 * t47 * t348 + 0.12e2 * t51 * t78 * t12
  t364 = t63 ** 2
  t404 = 0.12e2 * t82 * t95 * t44 * t60 + 0.6e1 * t64 * t109 - 0.6e1 * t47 * t48 * t14 + 0.6e1 * params.C * t364 * t75 + 0.22e2 * t74 * t67 * t14 - 0.3e1 * t131 * t71 + params.B * t310 * t49 - 0.12e2 * t82 * t345 - 0.12e2 * t82 * t348 - 0.12e2 * t82 * t321 + 0.12e2 * t137 * t97 + 0.12e2 * t137 * t100 + 0.6e1 * t82 * t334 + 0.6e1 * t47 * t94 * t4 * t60 * t44 - 0.28e2 * t112 * t94 * t37 * t63 * t44 - 0.6e1 * t51 * t126 * t69 - 0.6e1 * t137 * t107 - 0.2e1 * t82 * t319
  t409 = f.my_piecewise3(t1, 0, t285 * t34 / 0.2e1 + 0.2e1 * t18 * t56 + 0.3e1 * t41 * t88 + 0.2e1 * t59 * t148 + t92 * (t354 + t404) / 0.2e1)
  t410 = -t284
  t411 = f.my_piecewise5(t9, 0, t7, 0, t410)
  t420 = f.my_piecewise5(t25, 0, t21, 0, t410)
  t423 = t420 * t3 + 0.4e1 * t249
  t432 = t201 * t186
  t441 = t192 ** 2
  t442 = 0.1e1 / t441
  t445 = t442 * t4 * t222 * t170
  t448 = t242 * t222
  t469 = t194 * t249
  t471 = t246 * t170
  t480 = 0.2e1 * t177 * t423 * t174 * t4 + 0.6e1 * t190 * t223 + 0.6e1 * t190 * t226 + 0.3e1 * t173 * t432 - 0.28e2 * t238 * t246 * t189 - 0.6e1 * t177 * t253 * t37 - 0.6e1 * t173 * t445 - 0.6e1 * t173 * t448 + 0.12e2 * t177 * t204 * t12 - 0.12e2 * t177 * t178 * t14 + 0.22e2 * t200 * t442 * t37 * t222 + 0.28e2 * t200 * t220 * t12 * t170 - 0.3e1 * t257 * t195 - 0.3e1 * t190 * t233 - t173 * t469 - 0.6e1 * t173 * t471 + 0.8e1 * t238 * t201 * t252 - 0.8e1 * t200 * t242 * t186
  t490 = t189 ** 2
  t530 = 0.12e2 * t208 * t221 * t170 * t186 + 0.6e1 * t190 * t235 - 0.6e1 * t173 * t174 * t14 + 0.6e1 * params.C * t490 * t201 + 0.22e2 * t200 * t193 * t14 - 0.3e1 * t257 * t197 + params.B * t423 * t175 - 0.12e2 * t208 * t445 - 0.12e2 * t208 * t448 - 0.12e2 * t208 * t471 + 0.12e2 * t263 * t223 + 0.12e2 * t263 * t226 + 0.6e1 * t208 * t432 + 0.6e1 * t173 * t220 * t4 * t186 * t170 - 0.28e2 * t238 * t220 * t37 * t189 * t170 - 0.6e1 * t177 * t252 * t195 - 0.6e1 * t263 * t233 - 0.2e1 * t208 * t469
  t535 = f.my_piecewise3(t154, 0, t411 * t164 / 0.2e1 + 0.2e1 * t156 * t182 + 0.3e1 * t168 * t214 + 0.2e1 * t185 * t274 + t218 * (t480 + t530) / 0.2e1)
  d1111 = 0.4e1 * t152 + 0.4e1 * t278 + t3 * (t409 + t535)

  res = {'v4rho4': d1111}
  return res
