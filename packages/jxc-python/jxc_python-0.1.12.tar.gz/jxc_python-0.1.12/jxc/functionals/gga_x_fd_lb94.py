"""Generated from gga_x_fd_lb94.mpl."""

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  fd_beta = params_beta

  fd_csi = 2 ** (1 / 3)

  fd_f_inter = lambda n, t: -3 / 4 * fd_beta * fd_csi * jnp.log(t) ** n / (1 + 3 * fd_beta * fd_csi * t * jnp.log(fd_csi * t + jnp.sqrt((fd_csi * t) ** 2 + 1)))

  fd_f = lambda x: 1 - x / X_FACTOR_C * (fd_int0(x / fd_csi) * jnp.log(x / fd_csi) - fd_int1(x / fd_csi))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, fd_f, rs, z, xs0, xs1)

  fd_int0 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(0, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

  fd_int1 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(1, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  fd_beta = params_beta

  fd_csi = 2 ** (1 / 3)

  fd_f_inter = lambda n, t: -3 / 4 * fd_beta * fd_csi * jnp.log(t) ** n / (1 + 3 * fd_beta * fd_csi * t * jnp.log(fd_csi * t + jnp.sqrt((fd_csi * t) ** 2 + 1)))

  fd_f = lambda x: 1 - x / X_FACTOR_C * (fd_int0(x / fd_csi) * jnp.log(x / fd_csi) - fd_int1(x / fd_csi))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, fd_f, rs, z, xs0, xs1)

  fd_int0 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(0, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

  fd_int1 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(1, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  fd_beta = params_beta

  fd_csi = 2 ** (1 / 3)

  fd_f_inter = lambda n, t: -3 / 4 * fd_beta * fd_csi * jnp.log(t) ** n / (1 + 3 * fd_beta * fd_csi * t * jnp.log(fd_csi * t + jnp.sqrt((fd_csi * t) ** 2 + 1)))

  fd_f = lambda x: 1 - x / X_FACTOR_C * (fd_int0(x / fd_csi) * jnp.log(x / fd_csi) - fd_int1(x / fd_csi))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, fd_f, rs, z, xs0, xs1)

  fd_int0 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(0, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

  fd_int1 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(1, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

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
  t28 = jnp.sqrt(s0)
  t29 = r0 ** (0.1e1 / 0.3e1)
  t31 = 0.1e1 / t29 / r0
  t32 = t28 * t31
  t33 = t2 ** 2
  t36 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t38 = 4 ** (0.1e1 / 0.3e1)
  t39 = 0.1e1 / t36 * t38
  t40 = 2 ** (0.1e1 / 0.3e1)
  t41 = t40 ** 2
  t43 = t32 * t41 / 0.2e1
  t44 = fd_int0(t43)
  t45 = jnp.log(t43)
  t47 = fd_int1(t43)
  t49 = t39 * (t44 * t45 - t47)
  t52 = 0.1e1 - 0.2e1 / 0.9e1 * t32 * t33 * t49
  t56 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * t52)
  t57 = r1 <= f.p.dens_threshold
  t58 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t59 = 0.1e1 + t58
  t60 = t59 <= f.p.zeta_threshold
  t61 = t59 ** (0.1e1 / 0.3e1)
  t63 = f.my_piecewise3(t60, t22, t61 * t59)
  t64 = t63 * t26
  t65 = jnp.sqrt(s2)
  t66 = r1 ** (0.1e1 / 0.3e1)
  t68 = 0.1e1 / t66 / r1
  t69 = t65 * t68
  t72 = t69 * t41 / 0.2e1
  t73 = fd_int0(t72)
  t74 = jnp.log(t72)
  t76 = fd_int1(t72)
  t78 = t39 * (t73 * t74 - t76)
  t81 = 0.1e1 - 0.2e1 / 0.9e1 * t69 * t33 * t78
  t85 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t64 * t81)
  t86 = t6 ** 2
  t88 = t16 / t86
  t89 = t7 - t88
  t90 = f.my_piecewise5(t10, 0, t14, 0, t89)
  t93 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t90)
  t98 = t26 ** 2
  t99 = 0.1e1 / t98
  t103 = t5 * t25 * t99 * t52 / 0.8e1
  t104 = r0 ** 2
  t108 = t28 / t29 / t104 * t33
  t110 = t39 * t44
  t118 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t93 * t26 * t52 - t103 - 0.3e1 / 0.8e1 * t5 * t27 * (0.8e1 / 0.27e2 * t108 * t110 + 0.8e1 / 0.27e2 * t108 * t49))
  t120 = f.my_piecewise5(t14, 0, t10, 0, -t89)
  t123 = f.my_piecewise3(t60, 0, 0.4e1 / 0.3e1 * t61 * t120)
  t131 = t5 * t63 * t99 * t81 / 0.8e1
  t133 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t123 * t26 * t81 - t131)
  vrho_0_ = t56 + t85 + t6 * (t118 + t133)
  t136 = -t7 - t88
  t137 = f.my_piecewise5(t10, 0, t14, 0, t136)
  t140 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t23 * t137)
  t146 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t140 * t26 * t52 - t103)
  t148 = f.my_piecewise5(t14, 0, t10, 0, -t136)
  t151 = f.my_piecewise3(t60, 0, 0.4e1 / 0.3e1 * t61 * t148)
  t156 = r1 ** 2
  t160 = t65 / t66 / t156 * t33
  t162 = t39 * t73
  t170 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t151 * t26 * t81 - t131 - 0.3e1 / 0.8e1 * t5 * t64 * (0.8e1 / 0.27e2 * t160 * t162 + 0.8e1 / 0.27e2 * t160 * t78))
  vrho_1_ = t56 + t85 + t6 * (t146 + t170)
  t175 = 0.1e1 / t28 * t31 * t33
  t183 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t27 * (-t175 * t110 / 0.9e1 - t175 * t49 / 0.9e1))
  vsigma_0_ = t6 * t183
  vsigma_1_ = 0.0e0
  t186 = 0.1e1 / t65 * t68 * t33
  t194 = f.my_piecewise3(t57, 0, -0.3e1 / 0.8e1 * t5 * t64 * (-t186 * t162 / 0.9e1 - t186 * t78 / 0.9e1))
  vsigma_2_ = t6 * t194
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
  params_beta_raw = params.beta
  if isinstance(params_beta_raw, (str, bytes, dict)):
    params_beta = params_beta_raw
  else:
    try:
      params_beta_seq = list(params_beta_raw)
    except TypeError:
      params_beta = params_beta_raw
    else:
      params_beta_seq = np.asarray(params_beta_seq, dtype=np.float64)
      params_beta = np.concatenate((np.array([np.nan], dtype=np.float64), params_beta_seq))

  fd_beta = params_beta

  fd_csi = 2 ** (1 / 3)

  fd_f_inter = lambda n, t: -3 / 4 * fd_beta * fd_csi * jnp.log(t) ** n / (1 + 3 * fd_beta * fd_csi * t * jnp.log(fd_csi * t + jnp.sqrt((fd_csi * t) ** 2 + 1)))

  fd_f = lambda x: 1 - x / X_FACTOR_C * (fd_int0(x / fd_csi) * jnp.log(x / fd_csi) - fd_int1(x / fd_csi))

  functional_body = lambda rs, z, xt, xs0, xs1: gga_exchange(f, params, fd_f, rs, z, xs0, xs1)

  fd_int0 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(0, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

  fd_int1 = lambda arg: integrate_adaptive(lambda t: fd_f_inter(1, jnp.clip(t, 1e-18, None)), 1e-18, arg, epsabs=1e-14, epsrel=1e-14, max_depth=32)

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
  t19 = t17 * t18
  t20 = jnp.sqrt(s0)
  t21 = 2 ** (0.1e1 / 0.3e1)
  t22 = t20 * t21
  t24 = 0.1e1 / t18 / r0
  t26 = t3 ** 2
  t28 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t30 = t26 / t28
  t31 = 4 ** (0.1e1 / 0.3e1)
  t32 = t20 * t24
  t33 = fd_int0(t32)
  t34 = jnp.log(t32)
  t36 = fd_int1(t32)
  t39 = t30 * t31 * (t33 * t34 - t36)
  t42 = 0.1e1 - 0.2e1 / 0.9e1 * t22 * t24 * t39
  t46 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * t42)
  t47 = t18 ** 2
  t53 = r0 ** 2
  t56 = t22 / t18 / t53
  t59 = t30 * t31 * t33
  t67 = f.my_piecewise3(t2, 0, -t6 * t17 / t47 * t42 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t19 * (0.8e1 / 0.27e2 * t56 * t39 + 0.8e1 / 0.27e2 * t56 * t59))
  vrho_0_ = 0.2e1 * r0 * t67 + 0.2e1 * t46
  t72 = 0.1e1 / t20 * t21 * t24
  t80 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t19 * (-t72 * t39 / 0.9e1 - t72 * t59 / 0.9e1))
  vsigma_0_ = 0.2e1 * r0 * t80
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
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t21 = t17 / t19
  t22 = jnp.sqrt(s0)
  t23 = 2 ** (0.1e1 / 0.3e1)
  t24 = t22 * t23
  t26 = 0.1e1 / t18 / r0
  t27 = t24 * t26
  t28 = t3 ** 2
  t30 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t31 = 0.1e1 / t30
  t32 = t28 * t31
  t33 = 4 ** (0.1e1 / 0.3e1)
  t34 = t22 * t26
  t35 = fd_int0(t34)
  t36 = jnp.log(t34)
  t38 = fd_int1(t34)
  t41 = t32 * t33 * (t35 * t36 - t38)
  t44 = 0.1e1 - 0.2e1 / 0.9e1 * t27 * t41
  t48 = t17 * t18
  t49 = r0 ** 2
  t51 = 0.1e1 / t18 / t49
  t52 = t24 * t51
  t55 = t32 * t33 * t35
  t58 = 0.8e1 / 0.27e2 * t52 * t41 + 0.8e1 / 0.27e2 * t52 * t55
  t63 = f.my_piecewise3(t2, 0, -t6 * t21 * t44 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t48 * t58)
  t74 = t49 * r0
  t77 = t24 / t18 / t74
  t82 = t23 ** 2
  t83 = s0 * t82
  t84 = t49 ** 2
  t92 = 0.1e1 / t19 / t49
  t95 = jnp.sqrt(t83 * t92 + 0.1e1)
  t97 = jnp.log(t27 + t95)
  t104 = t31 * t33 * params.beta / (0.3e1 * params.beta * t23 * t34 * t97 + 0.1e1)
  t112 = f.my_piecewise3(t2, 0, t6 * t17 / t19 / r0 * t44 / 0.12e2 - t6 * t21 * t58 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t48 * (-0.56e2 / 0.81e2 * t77 * t41 - 0.88e2 / 0.81e2 * t77 * t55 + 0.8e1 / 0.27e2 * t83 / t19 / t84 * t28 * t104))
  v2rho2_0_ = 0.2e1 * r0 * t112 + 0.4e1 * t63
  t116 = 0.1e1 / t22 * t23
  t117 = t116 * t26
  t121 = -t117 * t41 / 0.9e1 - t117 * t55 / 0.9e1
  t125 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t48 * t121)
  t129 = t116 * t51
  t145 = f.my_piecewise3(t2, 0, -t6 * t21 * t121 / 0.8e1 - 0.3e1 / 0.8e1 * t6 * t48 * (0.4e1 / 0.27e2 * t129 * t41 + 0.8e1 / 0.27e2 * t129 * t55 - t82 / t19 / t74 * t28 * t104 / 0.9e1))
  v2rhosigma_0_ = 0.2e1 * r0 * t145 + 0.2e1 * t125
  t164 = f.my_piecewise3(t2, 0, -0.3e1 / 0.8e1 * t6 * t48 * (0.1e1 / t22 / s0 * t23 * t26 * t41 / 0.18e2 + 0.1e1 / s0 * t82 * t92 * t28 * t104 / 0.24e2))
  v2sigma2_0_ = 0.2e1 * r0 * t164
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
  t13 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t15 = t11 ** (0.1e1 / 0.3e1)
  t17 = f.my_piecewise3(t11 <= f.p.zeta_threshold, t13 * f.p.zeta_threshold, t15 * t11)
  t18 = r0 ** (0.1e1 / 0.3e1)
  t19 = t18 ** 2
  t22 = t17 / t19 / r0
  t23 = jnp.sqrt(s0)
  t24 = 2 ** (0.1e1 / 0.3e1)
  t25 = t23 * t24
  t27 = 0.1e1 / t18 / r0
  t28 = t25 * t27
  t29 = t3 ** 2
  t31 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t32 = 0.1e1 / t31
  t33 = t29 * t32
  t34 = 4 ** (0.1e1 / 0.3e1)
  t35 = t23 * t27
  t36 = fd_int0(t35)
  t37 = jnp.log(t35)
  t39 = fd_int1(t35)
  t42 = t33 * t34 * (t36 * t37 - t39)
  t45 = 0.1e1 - 0.2e1 / 0.9e1 * t28 * t42
  t50 = t17 / t19
  t51 = r0 ** 2
  t53 = 0.1e1 / t18 / t51
  t54 = t25 * t53
  t57 = t33 * t34 * t36
  t60 = 0.8e1 / 0.27e2 * t54 * t42 + 0.8e1 / 0.27e2 * t54 * t57
  t64 = t17 * t18
  t65 = t51 * r0
  t68 = t25 / t18 / t65
  t73 = t24 ** 2
  t74 = s0 * t73
  t75 = t51 ** 2
  t79 = t74 / t19 / t75 * t29
  t80 = t32 * t34
  t81 = params.beta * t24
  t83 = 0.1e1 / t19 / t51
  t86 = jnp.sqrt(t74 * t83 + 0.1e1)
  t87 = t28 + t86
  t88 = jnp.log(t87)
  t92 = 0.3e1 * t81 * t35 * t88 + 0.1e1
  t95 = t80 * params.beta / t92
  t98 = -0.56e2 / 0.81e2 * t68 * t42 - 0.88e2 / 0.81e2 * t68 * t57 + 0.8e1 / 0.27e2 * t79 * t95
  t103 = f.my_piecewise3(t2, 0, t6 * t22 * t45 / 0.12e2 - t6 * t50 * t60 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t64 * t98)
  t117 = t25 / t18 / t75
  t129 = t92 ** 2
  t160 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t17 * t83 * t45 + t6 * t22 * t60 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t50 * t98 - 0.3e1 / 0.8e1 * t6 * t64 * (0.560e3 / 0.243e3 * t117 * t42 + 0.368e3 / 0.81e2 * t117 * t57 - 0.200e3 / 0.81e2 * t74 / t19 / t75 / r0 * t29 * t95 - 0.8e1 / 0.27e2 * t79 * t80 * params.beta / t129 * (-0.4e1 * t81 * t23 * t53 * t88 + 0.3e1 * t81 * t23 * t27 * (-0.4e1 / 0.3e1 * t54 - 0.4e1 / 0.3e1 / t86 * t73 * s0 / t19 / t65) / t87)))
  v3rho3_0_ = 0.2e1 * r0 * t160 + 0.6e1 * t103

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
  t23 = t17 * t22
  t24 = jnp.sqrt(s0)
  t25 = 2 ** (0.1e1 / 0.3e1)
  t26 = t24 * t25
  t28 = 0.1e1 / t19 / r0
  t29 = t26 * t28
  t30 = t3 ** 2
  t32 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t33 = 0.1e1 / t32
  t34 = t30 * t33
  t35 = 4 ** (0.1e1 / 0.3e1)
  t36 = t24 * t28
  t37 = fd_int0(t36)
  t38 = jnp.log(t36)
  t40 = fd_int1(t36)
  t43 = t34 * t35 * (t37 * t38 - t40)
  t46 = 0.1e1 - 0.2e1 / 0.9e1 * t29 * t43
  t52 = t17 / t20 / r0
  t54 = 0.1e1 / t19 / t18
  t55 = t26 * t54
  t58 = t34 * t35 * t37
  t61 = 0.8e1 / 0.27e2 * t55 * t43 + 0.8e1 / 0.27e2 * t55 * t58
  t66 = t17 / t20
  t67 = t18 * r0
  t69 = 0.1e1 / t19 / t67
  t70 = t26 * t69
  t75 = t25 ** 2
  t76 = s0 * t75
  t77 = t18 ** 2
  t79 = 0.1e1 / t20 / t77
  t81 = t76 * t79 * t30
  t82 = t33 * t35
  t83 = params.beta * t25
  t85 = t76 * t22 + 0.1e1
  t86 = jnp.sqrt(t85)
  t87 = t29 + t86
  t88 = jnp.log(t87)
  t92 = 0.3e1 * t83 * t36 * t88 + 0.1e1
  t95 = t82 * params.beta / t92
  t98 = -0.56e2 / 0.81e2 * t70 * t43 - 0.88e2 / 0.81e2 * t70 * t58 + 0.8e1 / 0.27e2 * t81 * t95
  t102 = t17 * t19
  t105 = t26 / t19 / t77
  t110 = t77 * r0
  t114 = t76 / t20 / t110 * t30
  t117 = t92 ** 2
  t119 = params.beta / t117
  t124 = t83 * t24
  t126 = 0.1e1 / t86 * t75
  t128 = 0.1e1 / t20 / t67
  t132 = -0.4e1 / 0.3e1 * t126 * s0 * t128 - 0.4e1 / 0.3e1 * t55
  t134 = 0.1e1 / t87
  t138 = 0.3e1 * t124 * t28 * t132 * t134 - 0.4e1 * t83 * t24 * t54 * t88
  t140 = t82 * t119 * t138
  t143 = 0.560e3 / 0.243e3 * t105 * t43 + 0.368e3 / 0.81e2 * t105 * t58 - 0.200e3 / 0.81e2 * t114 * t95 - 0.8e1 / 0.27e2 * t81 * t140
  t148 = f.my_piecewise3(t2, 0, -0.5e1 / 0.36e2 * t6 * t23 * t46 + t6 * t52 * t61 / 0.4e1 - 0.3e1 / 0.8e1 * t6 * t66 * t98 - 0.3e1 / 0.8e1 * t6 * t102 * t143)
  t165 = t26 / t19 / t110
  t182 = t138 ** 2
  t199 = s0 ** 2
  t214 = t132 ** 2
  t216 = t87 ** 2
  t231 = f.my_piecewise3(t2, 0, 0.10e2 / 0.27e2 * t6 * t17 * t128 * t46 - 0.5e1 / 0.9e1 * t6 * t23 * t61 + t6 * t52 * t98 / 0.2e1 - t6 * t66 * t143 / 0.2e1 - 0.3e1 / 0.8e1 * t6 * t102 * (-0.7280e4 / 0.729e3 * t165 * t43 - 0.16592e5 / 0.729e3 * t165 * t58 + 0.4504e4 / 0.243e3 * t76 / t20 / t77 / t18 * t30 * t95 + 0.104e3 / 0.27e2 * t114 * t140 + 0.16e2 / 0.27e2 * t81 * t82 * params.beta / t117 / t92 * t182 - 0.8e1 / 0.27e2 * t81 * t82 * t119 * (0.28e2 / 0.3e1 * t83 * t24 * t69 * t88 - 0.8e1 * t124 * t54 * t132 * t134 + 0.3e1 * t124 * t28 * (0.28e2 / 0.9e1 * t70 - 0.32e2 / 0.9e1 / t86 / t85 * t25 * t199 / t19 / t77 / t67 + 0.44e2 / 0.9e1 * t126 * s0 * t79) * t134 - 0.3e1 * t124 * t28 * t214 / t216)))
  v4rho4_0_ = 0.2e1 * r0 * t231 + 0.8e1 * t148

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
  t32 = jnp.sqrt(s0)
  t33 = r0 ** (0.1e1 / 0.3e1)
  t35 = 0.1e1 / t33 / r0
  t36 = t32 * t35
  t37 = t2 ** 2
  t40 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t42 = 4 ** (0.1e1 / 0.3e1)
  t43 = 0.1e1 / t40 * t42
  t44 = 2 ** (0.1e1 / 0.3e1)
  t45 = t44 ** 2
  t47 = t36 * t45 / 0.2e1
  t48 = fd_int0(t47)
  t49 = jnp.log(t47)
  t51 = fd_int1(t47)
  t53 = t43 * (t48 * t49 - t51)
  t56 = 0.1e1 - 0.2e1 / 0.9e1 * t36 * t37 * t53
  t60 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t61 = t60 * f.p.zeta_threshold
  t63 = f.my_piecewise3(t20, t61, t21 * t19)
  t64 = t30 ** 2
  t65 = 0.1e1 / t64
  t66 = t63 * t65
  t69 = t5 * t66 * t56 / 0.8e1
  t70 = t63 * t30
  t71 = r0 ** 2
  t75 = t32 / t33 / t71 * t37
  t77 = t43 * t48
  t80 = 0.8e1 / 0.27e2 * t75 * t53 + 0.8e1 / 0.27e2 * t75 * t77
  t85 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t31 * t56 - t69 - 0.3e1 / 0.8e1 * t5 * t70 * t80)
  t87 = r1 <= f.p.dens_threshold
  t88 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t89 = 0.1e1 + t88
  t90 = t89 <= f.p.zeta_threshold
  t91 = t89 ** (0.1e1 / 0.3e1)
  t93 = f.my_piecewise5(t14, 0, t10, 0, -t25)
  t96 = f.my_piecewise3(t90, 0, 0.4e1 / 0.3e1 * t91 * t93)
  t97 = t96 * t30
  t98 = jnp.sqrt(s2)
  t99 = r1 ** (0.1e1 / 0.3e1)
  t101 = 0.1e1 / t99 / r1
  t102 = t98 * t101
  t105 = t102 * t45 / 0.2e1
  t106 = fd_int0(t105)
  t107 = jnp.log(t105)
  t109 = fd_int1(t105)
  t111 = t43 * (t106 * t107 - t109)
  t114 = 0.1e1 - 0.2e1 / 0.9e1 * t102 * t37 * t111
  t119 = f.my_piecewise3(t90, t61, t91 * t89)
  t120 = t119 * t65
  t123 = t5 * t120 * t114 / 0.8e1
  t125 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t97 * t114 - t123)
  t127 = t21 ** 2
  t128 = 0.1e1 / t127
  t129 = t26 ** 2
  t134 = t16 / t22 / t6
  t136 = -0.2e1 * t23 + 0.2e1 * t134
  t137 = f.my_piecewise5(t10, 0, t14, 0, t136)
  t141 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t128 * t129 + 0.4e1 / 0.3e1 * t21 * t137)
  t148 = t5 * t29 * t65 * t56
  t154 = 0.1e1 / t64 / t6
  t158 = t5 * t63 * t154 * t56 / 0.12e2
  t160 = t5 * t66 * t80
  t166 = t32 / t33 / t71 / r0 * t37
  t171 = t71 ** 2
  t172 = t33 ** 2
  t182 = jnp.sqrt(s0 / t172 / t71 + 0.1e1)
  t184 = jnp.log(t36 + t182)
  t199 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t141 * t30 * t56 - t148 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t31 * t80 + t158 - t160 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t70 * (-0.56e2 / 0.81e2 * t166 * t53 - 0.88e2 / 0.81e2 * t166 * t77 + 0.8e1 / 0.27e2 * s0 / t172 / t171 * t37 * t43 * params.beta / (0.3e1 * params.beta * t32 * t35 * t184 + 0.1e1)))
  t200 = t91 ** 2
  t201 = 0.1e1 / t200
  t202 = t93 ** 2
  t206 = f.my_piecewise5(t14, 0, t10, 0, -t136)
  t210 = f.my_piecewise3(t90, 0, 0.4e1 / 0.9e1 * t201 * t202 + 0.4e1 / 0.3e1 * t91 * t206)
  t217 = t5 * t96 * t65 * t114
  t222 = t5 * t119 * t154 * t114 / 0.12e2
  t224 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t210 * t30 * t114 - t217 / 0.4e1 + t222)
  d11 = 0.2e1 * t85 + 0.2e1 * t125 + t6 * (t199 + t224)
  t227 = -t7 - t24
  t228 = f.my_piecewise5(t10, 0, t14, 0, t227)
  t231 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t228)
  t232 = t231 * t30
  t237 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t232 * t56 - t69)
  t239 = f.my_piecewise5(t14, 0, t10, 0, -t227)
  t242 = f.my_piecewise3(t90, 0, 0.4e1 / 0.3e1 * t91 * t239)
  t243 = t242 * t30
  t247 = t119 * t30
  t248 = r1 ** 2
  t252 = t98 / t99 / t248 * t37
  t254 = t43 * t106
  t257 = 0.8e1 / 0.27e2 * t252 * t111 + 0.8e1 / 0.27e2 * t252 * t254
  t262 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t243 * t114 - t123 - 0.3e1 / 0.8e1 * t5 * t247 * t257)
  t266 = 0.2e1 * t134
  t267 = f.my_piecewise5(t10, 0, t14, 0, t266)
  t271 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t128 * t228 * t26 + 0.4e1 / 0.3e1 * t21 * t267)
  t278 = t5 * t231 * t65 * t56
  t286 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t271 * t30 * t56 - t278 / 0.8e1 - 0.3e1 / 0.8e1 * t5 * t232 * t80 - t148 / 0.8e1 + t158 - t160 / 0.8e1)
  t290 = f.my_piecewise5(t14, 0, t10, 0, -t266)
  t294 = f.my_piecewise3(t90, 0, 0.4e1 / 0.9e1 * t201 * t239 * t93 + 0.4e1 / 0.3e1 * t91 * t290)
  t301 = t5 * t242 * t65 * t114
  t308 = t5 * t120 * t257
  t311 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t294 * t30 * t114 - t301 / 0.8e1 - t217 / 0.8e1 + t222 - 0.3e1 / 0.8e1 * t5 * t97 * t257 - t308 / 0.8e1)
  d12 = t85 + t125 + t237 + t262 + t6 * (t286 + t311)
  t316 = t228 ** 2
  t320 = 0.2e1 * t23 + 0.2e1 * t134
  t321 = f.my_piecewise5(t10, 0, t14, 0, t320)
  t325 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t128 * t316 + 0.4e1 / 0.3e1 * t21 * t321)
  t332 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t325 * t30 * t56 - t278 / 0.4e1 + t158)
  t333 = t239 ** 2
  t337 = f.my_piecewise5(t14, 0, t10, 0, -t320)
  t341 = f.my_piecewise3(t90, 0, 0.4e1 / 0.9e1 * t201 * t333 + 0.4e1 / 0.3e1 * t91 * t337)
  t355 = t98 / t99 / t248 / r1 * t37
  t360 = t248 ** 2
  t361 = t99 ** 2
  t371 = jnp.sqrt(s2 / t361 / t248 + 0.1e1)
  t373 = jnp.log(t102 + t371)
  t388 = f.my_piecewise3(t87, 0, -0.3e1 / 0.8e1 * t5 * t341 * t30 * t114 - t301 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t243 * t257 + t222 - t308 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t247 * (-0.56e2 / 0.81e2 * t355 * t111 - 0.88e2 / 0.81e2 * t355 * t254 + 0.8e1 / 0.27e2 * s2 / t361 / t360 * t37 * t43 * params.beta / (0.3e1 * params.beta * t98 * t101 * t373 + 0.1e1)))
  d22 = 0.2e1 * t237 + 0.2e1 * t262 + t6 * (t332 + t388)
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
  t44 = jnp.sqrt(s0)
  t45 = r0 ** (0.1e1 / 0.3e1)
  t47 = 0.1e1 / t45 / r0
  t48 = t44 * t47
  t49 = t2 ** 2
  t52 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t53 = 0.1e1 / t52
  t54 = 4 ** (0.1e1 / 0.3e1)
  t55 = t53 * t54
  t56 = 2 ** (0.1e1 / 0.3e1)
  t57 = t56 ** 2
  t59 = t48 * t57 / 0.2e1
  t60 = fd_int0(t59)
  t61 = jnp.log(t59)
  t63 = fd_int1(t59)
  t65 = t55 * (t60 * t61 - t63)
  t68 = 0.1e1 - 0.2e1 / 0.9e1 * t48 * t49 * t65
  t74 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t28)
  t75 = t42 ** 2
  t76 = 0.1e1 / t75
  t77 = t74 * t76
  t81 = t74 * t42
  t82 = r0 ** 2
  t84 = 0.1e1 / t45 / t82
  t85 = t44 * t84
  t86 = t85 * t49
  t88 = t55 * t60
  t91 = 0.8e1 / 0.27e2 * t86 * t65 + 0.8e1 / 0.27e2 * t86 * t88
  t95 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t96 = t95 * f.p.zeta_threshold
  t98 = f.my_piecewise3(t20, t96, t21 * t19)
  t100 = 0.1e1 / t75 / t6
  t101 = t98 * t100
  t105 = t98 * t76
  t109 = t98 * t42
  t110 = t82 * r0
  t114 = t44 / t45 / t110 * t49
  t119 = t82 ** 2
  t120 = t45 ** 2
  t123 = s0 / t120 / t119
  t125 = params.beta * t44
  t130 = jnp.sqrt(s0 / t120 / t82 + 0.1e1)
  t131 = t48 + t130
  t132 = jnp.log(t131)
  t136 = 0.3e1 * t125 * t47 * t132 + 0.1e1
  t139 = t55 * params.beta / t136
  t142 = -0.56e2 / 0.81e2 * t114 * t65 - 0.88e2 / 0.81e2 * t114 * t88 + 0.8e1 / 0.27e2 * t123 * t49 * t139
  t147 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t43 * t68 - t5 * t77 * t68 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t81 * t91 + t5 * t101 * t68 / 0.12e2 - t5 * t105 * t91 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t109 * t142)
  t149 = r1 <= f.p.dens_threshold
  t150 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t151 = 0.1e1 + t150
  t152 = t151 <= f.p.zeta_threshold
  t153 = t151 ** (0.1e1 / 0.3e1)
  t154 = t153 ** 2
  t155 = 0.1e1 / t154
  t157 = f.my_piecewise5(t14, 0, t10, 0, -t27)
  t158 = t157 ** 2
  t162 = f.my_piecewise5(t14, 0, t10, 0, -t36)
  t166 = f.my_piecewise3(t152, 0, 0.4e1 / 0.9e1 * t155 * t158 + 0.4e1 / 0.3e1 * t153 * t162)
  t168 = jnp.sqrt(s2)
  t169 = r1 ** (0.1e1 / 0.3e1)
  t172 = t168 / t169 / r1
  t175 = t172 * t57 / 0.2e1
  t176 = fd_int0(t175)
  t177 = jnp.log(t175)
  t179 = fd_int1(t175)
  t184 = 0.1e1 - 0.2e1 / 0.9e1 * t172 * t49 * t55 * (t176 * t177 - t179)
  t190 = f.my_piecewise3(t152, 0, 0.4e1 / 0.3e1 * t153 * t157)
  t196 = f.my_piecewise3(t152, t96, t153 * t151)
  t202 = f.my_piecewise3(t149, 0, -0.3e1 / 0.8e1 * t5 * t166 * t42 * t184 - t5 * t190 * t76 * t184 / 0.4e1 + t5 * t196 * t100 * t184 / 0.12e2)
  t212 = t24 ** 2
  t216 = 0.6e1 * t33 - 0.6e1 * t16 / t212
  t217 = f.my_piecewise5(t10, 0, t14, 0, t216)
  t221 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 / t22 / t19 * t29 * t28 + 0.4e1 / 0.3e1 * t23 * t28 * t37 + 0.4e1 / 0.3e1 * t21 * t217)
  t244 = 0.1e1 / t75 / t24
  t258 = t44 / t45 / t119 * t49
  t273 = t136 ** 2
  t300 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t221 * t42 * t68 - 0.3e1 / 0.8e1 * t5 * t41 * t76 * t68 - 0.9e1 / 0.8e1 * t5 * t43 * t91 + t5 * t74 * t100 * t68 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t77 * t91 - 0.9e1 / 0.8e1 * t5 * t81 * t142 - 0.5e1 / 0.36e2 * t5 * t98 * t244 * t68 + t5 * t101 * t91 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t105 * t142 - 0.3e1 / 0.8e1 * t5 * t109 * (0.560e3 / 0.243e3 * t258 * t65 + 0.368e3 / 0.81e2 * t258 * t88 - 0.200e3 / 0.81e2 * s0 / t120 / t119 / r0 * t49 * t139 - 0.8e1 / 0.27e2 * t123 * t49 * t53 * t54 * params.beta / t273 * (-0.4e1 * t125 * t84 * t132 + 0.3e1 * t125 * t47 * (-0.4e1 / 0.3e1 * t85 - 0.4e1 / 0.3e1 / t130 * s0 / t120 / t110) / t131)))
  t310 = f.my_piecewise5(t14, 0, t10, 0, -t216)
  t314 = f.my_piecewise3(t152, 0, -0.8e1 / 0.27e2 / t154 / t151 * t158 * t157 + 0.4e1 / 0.3e1 * t155 * t157 * t162 + 0.4e1 / 0.3e1 * t153 * t310)
  t332 = f.my_piecewise3(t149, 0, -0.3e1 / 0.8e1 * t5 * t314 * t42 * t184 - 0.3e1 / 0.8e1 * t5 * t166 * t76 * t184 + t5 * t190 * t100 * t184 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t196 * t244 * t184)
  d111 = 0.3e1 * t147 + 0.3e1 * t202 + t6 * (t300 + t332)

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
  t21 = t19 ** (0.1e1 / 0.3e1)
  t22 = t21 ** 2
  t24 = 0.1e1 / t22 / t19
  t25 = t6 ** 2
  t26 = 0.1e1 / t25
  t28 = -t16 * t26 + t7
  t29 = f.my_piecewise5(t10, 0, t14, 0, t28)
  t30 = t29 ** 2
  t34 = 0.1e1 / t22
  t35 = t34 * t29
  t36 = t25 * t6
  t37 = 0.1e1 / t36
  t40 = 0.2e1 * t16 * t37 - 0.2e1 * t26
  t41 = f.my_piecewise5(t10, 0, t14, 0, t40)
  t44 = t25 ** 2
  t45 = 0.1e1 / t44
  t48 = -0.6e1 * t16 * t45 + 0.6e1 * t37
  t49 = f.my_piecewise5(t10, 0, t14, 0, t48)
  t53 = f.my_piecewise3(t20, 0, -0.8e1 / 0.27e2 * t24 * t30 * t29 + 0.4e1 / 0.3e1 * t35 * t41 + 0.4e1 / 0.3e1 * t21 * t49)
  t54 = t6 ** (0.1e1 / 0.3e1)
  t55 = t53 * t54
  t56 = jnp.sqrt(s0)
  t57 = r0 ** (0.1e1 / 0.3e1)
  t59 = 0.1e1 / t57 / r0
  t60 = t56 * t59
  t61 = t2 ** 2
  t64 = (0.1e1 / jnp.pi) ** (0.1e1 / 0.3e1)
  t65 = 0.1e1 / t64
  t66 = 4 ** (0.1e1 / 0.3e1)
  t67 = t65 * t66
  t68 = 2 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t71 = t60 * t69 / 0.2e1
  t72 = fd_int0(t71)
  t73 = jnp.log(t71)
  t75 = fd_int1(t71)
  t77 = t67 * (t72 * t73 - t75)
  t80 = 0.1e1 - 0.2e1 / 0.9e1 * t60 * t61 * t77
  t89 = f.my_piecewise3(t20, 0, 0.4e1 / 0.9e1 * t34 * t30 + 0.4e1 / 0.3e1 * t21 * t41)
  t90 = t54 ** 2
  t91 = 0.1e1 / t90
  t92 = t89 * t91
  t96 = t89 * t54
  t97 = r0 ** 2
  t99 = 0.1e1 / t57 / t97
  t100 = t56 * t99
  t101 = t100 * t61
  t103 = t67 * t72
  t106 = 0.8e1 / 0.27e2 * t101 * t103 + 0.8e1 / 0.27e2 * t101 * t77
  t112 = f.my_piecewise3(t20, 0, 0.4e1 / 0.3e1 * t21 * t29)
  t114 = 0.1e1 / t90 / t6
  t115 = t112 * t114
  t119 = t112 * t91
  t123 = t112 * t54
  t124 = t97 * r0
  t126 = 0.1e1 / t57 / t124
  t127 = t56 * t126
  t128 = t127 * t61
  t133 = t97 ** 2
  t134 = t57 ** 2
  t136 = 0.1e1 / t134 / t133
  t137 = s0 * t136
  t139 = params.beta * t56
  t143 = s0 / t134 / t97 + 0.1e1
  t144 = jnp.sqrt(t143)
  t145 = t60 + t144
  t146 = jnp.log(t145)
  t150 = 0.3e1 * t139 * t59 * t146 + 0.1e1
  t153 = t67 * params.beta / t150
  t156 = -0.56e2 / 0.81e2 * t128 * t77 - 0.88e2 / 0.81e2 * t128 * t103 + 0.8e1 / 0.27e2 * t137 * t61 * t153
  t160 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t161 = t160 * f.p.zeta_threshold
  t163 = f.my_piecewise3(t20, t161, t21 * t19)
  t165 = 0.1e1 / t90 / t25
  t166 = t163 * t165
  t170 = t163 * t114
  t174 = t163 * t91
  t178 = t163 * t54
  t182 = t56 / t57 / t133 * t61
  t187 = t133 * r0
  t190 = s0 / t134 / t187
  t194 = t61 * t65
  t195 = t137 * t194
  t196 = t66 * params.beta
  t197 = t150 ** 2
  t198 = 0.1e1 / t197
  t203 = 0.1e1 / t144 * s0
  t208 = -0.4e1 / 0.3e1 * t100 - 0.4e1 / 0.3e1 * t203 / t134 / t124
  t210 = 0.1e1 / t145
  t214 = 0.3e1 * t139 * t59 * t208 * t210 - 0.4e1 * t139 * t99 * t146
  t216 = t196 * t198 * t214
  t219 = 0.560e3 / 0.243e3 * t182 * t77 + 0.368e3 / 0.81e2 * t182 * t103 - 0.200e3 / 0.81e2 * t190 * t61 * t153 - 0.8e1 / 0.27e2 * t195 * t216
  t224 = f.my_piecewise3(t1, 0, -0.3e1 / 0.8e1 * t5 * t55 * t80 - 0.3e1 / 0.8e1 * t5 * t92 * t80 - 0.9e1 / 0.8e1 * t5 * t96 * t106 + t5 * t115 * t80 / 0.4e1 - 0.3e1 / 0.4e1 * t5 * t119 * t106 - 0.9e1 / 0.8e1 * t5 * t123 * t156 - 0.5e1 / 0.36e2 * t5 * t166 * t80 + t5 * t170 * t106 / 0.4e1 - 0.3e1 / 0.8e1 * t5 * t174 * t156 - 0.3e1 / 0.8e1 * t5 * t178 * t219)
  t226 = r1 <= f.p.dens_threshold
  t227 = f.my_piecewise5(t14, t11, t10, t15, -t17)
  t228 = 0.1e1 + t227
  t229 = t228 <= f.p.zeta_threshold
  t230 = t228 ** (0.1e1 / 0.3e1)
  t231 = t230 ** 2
  t233 = 0.1e1 / t231 / t228
  t235 = f.my_piecewise5(t14, 0, t10, 0, -t28)
  t236 = t235 ** 2
  t240 = 0.1e1 / t231
  t241 = t240 * t235
  t243 = f.my_piecewise5(t14, 0, t10, 0, -t40)
  t247 = f.my_piecewise5(t14, 0, t10, 0, -t48)
  t251 = f.my_piecewise3(t229, 0, -0.8e1 / 0.27e2 * t233 * t236 * t235 + 0.4e1 / 0.3e1 * t241 * t243 + 0.4e1 / 0.3e1 * t230 * t247)
  t253 = jnp.sqrt(s2)
  t254 = r1 ** (0.1e1 / 0.3e1)
  t257 = t253 / t254 / r1
  t260 = t257 * t69 / 0.2e1
  t261 = fd_int0(t260)
  t262 = jnp.log(t260)
  t264 = fd_int1(t260)
  t269 = 0.1e1 - 0.2e1 / 0.9e1 * t257 * t61 * t67 * (t261 * t262 - t264)
  t278 = f.my_piecewise3(t229, 0, 0.4e1 / 0.9e1 * t240 * t236 + 0.4e1 / 0.3e1 * t230 * t243)
  t285 = f.my_piecewise3(t229, 0, 0.4e1 / 0.3e1 * t230 * t235)
  t291 = f.my_piecewise3(t229, t161, t230 * t228)
  t297 = f.my_piecewise3(t226, 0, -0.3e1 / 0.8e1 * t5 * t251 * t54 * t269 - 0.3e1 / 0.8e1 * t5 * t278 * t91 * t269 + t5 * t285 * t114 * t269 / 0.4e1 - 0.5e1 / 0.36e2 * t5 * t291 * t165 * t269)
  t302 = t56 / t57 / t187 * t61
  t319 = t214 ** 2
  t334 = s0 ** 2
  t348 = t208 ** 2
  t350 = t145 ** 2
  t364 = t19 ** 2
  t367 = t30 ** 2
  t373 = t41 ** 2
  t382 = -0.24e2 * t45 + 0.24e2 * t16 / t44 / t6
  t383 = f.my_piecewise5(t10, 0, t14, 0, t382)
  t387 = f.my_piecewise3(t20, 0, 0.40e2 / 0.81e2 / t22 / t364 * t367 - 0.16e2 / 0.9e1 * t24 * t30 * t41 + 0.4e1 / 0.3e1 * t34 * t373 + 0.16e2 / 0.9e1 * t35 * t49 + 0.4e1 / 0.3e1 * t21 * t383)
  t431 = 0.1e1 / t90 / t36
  t436 = -0.3e1 / 0.8e1 * t5 * t178 * (-0.7280e4 / 0.729e3 * t302 * t77 - 0.16592e5 / 0.729e3 * t302 * t103 + 0.4504e4 / 0.243e3 * s0 / t134 / t133 / t97 * t61 * t153 + 0.104e3 / 0.27e2 * t190 * t194 * t216 + 0.16e2 / 0.27e2 * t195 * t196 / t197 / t150 * t319 - 0.8e1 / 0.27e2 * t195 * t196 * t198 * (0.28e2 / 0.3e1 * t139 * t126 * t146 - 0.8e1 * t139 * t99 * t208 * t210 + 0.3e1 * t139 * t59 * (0.28e2 / 0.9e1 * t127 - 0.16e2 / 0.9e1 / t144 / t143 * t334 / t57 / t133 / t124 + 0.44e2 / 0.9e1 * t203 * t136) * t210 - 0.3e1 * t139 * t59 * t348 / t350)) - 0.3e1 / 0.8e1 * t5 * t387 * t54 * t80 - 0.3e1 / 0.2e1 * t5 * t55 * t106 - 0.3e1 / 0.2e1 * t5 * t92 * t106 - 0.9e1 / 0.4e1 * t5 * t96 * t156 + t5 * t115 * t106 - 0.3e1 / 0.2e1 * t5 * t119 * t156 - 0.3e1 / 0.2e1 * t5 * t123 * t219 - 0.5e1 / 0.9e1 * t5 * t166 * t106 + t5 * t170 * t156 / 0.2e1 - t5 * t174 * t219 / 0.2e1 - t5 * t53 * t91 * t80 / 0.2e1 + t5 * t89 * t114 * t80 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t112 * t165 * t80 + 0.10e2 / 0.27e2 * t5 * t163 * t431 * t80
  t437 = f.my_piecewise3(t1, 0, t436)
  t438 = t228 ** 2
  t441 = t236 ** 2
  t447 = t243 ** 2
  t453 = f.my_piecewise5(t14, 0, t10, 0, -t382)
  t457 = f.my_piecewise3(t229, 0, 0.40e2 / 0.81e2 / t231 / t438 * t441 - 0.16e2 / 0.9e1 * t233 * t236 * t243 + 0.4e1 / 0.3e1 * t240 * t447 + 0.16e2 / 0.9e1 * t241 * t247 + 0.4e1 / 0.3e1 * t230 * t453)
  t479 = f.my_piecewise3(t226, 0, -0.3e1 / 0.8e1 * t5 * t457 * t54 * t269 - t5 * t251 * t91 * t269 / 0.2e1 + t5 * t278 * t114 * t269 / 0.2e1 - 0.5e1 / 0.9e1 * t5 * t285 * t165 * t269 + 0.10e2 / 0.27e2 * t5 * t291 * t431 * t269)
  d1111 = 0.4e1 * t224 + 0.4e1 * t297 + t6 * (t437 + t479)

  res = {'v4rho4': d1111}
  return res
