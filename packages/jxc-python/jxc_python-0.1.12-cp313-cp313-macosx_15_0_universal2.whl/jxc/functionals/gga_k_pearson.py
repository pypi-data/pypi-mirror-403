"""Generated from gga_k_pearson.mpl."""

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
  pearson_f0 = lambda s: 1 + 5 / 27 * s ** 2 / (1 + s ** 6)

  pearson_f = lambda x: pearson_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, pearson_f, rs, zeta, xs0, xs1)

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
  pearson_f0 = lambda s: 1 + 5 / 27 * s ** 2 / (1 + s ** 6)

  pearson_f = lambda x: pearson_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, pearson_f, rs, zeta, xs0, xs1)

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
  pearson_f0 = lambda s: 1 + 5 / 27 * s ** 2 / (1 + s ** 6)

  pearson_f = lambda x: pearson_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, pearson_f, rs, zeta, xs0, xs1)

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
  t37 = t32 / t35
  t38 = r0 ** 2
  t39 = r0 ** (0.1e1 / 0.3e1)
  t40 = t39 ** 2
  t42 = 0.1e1 / t40 / t38
  t44 = t33 ** 2
  t45 = 0.1e1 / t44
  t46 = s0 ** 2
  t47 = t46 * s0
  t49 = t38 ** 2
  t50 = t49 ** 2
  t54 = 0.1e1 + t45 * t47 / t50 / 0.2304e4
  t55 = 0.1e1 / t54
  t59 = 0.1e1 + 0.5e1 / 0.648e3 * t37 * s0 * t42 * t55
  t63 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * t59)
  t64 = r1 <= f.p.dens_threshold
  t65 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t66 = 0.1e1 + t65
  t67 = t66 <= f.p.zeta_threshold
  t68 = t66 ** (0.1e1 / 0.3e1)
  t69 = t68 ** 2
  t71 = f.my_piecewise3(t67, t24, t69 * t66)
  t72 = t71 * t30
  t73 = r1 ** 2
  t74 = r1 ** (0.1e1 / 0.3e1)
  t75 = t74 ** 2
  t77 = 0.1e1 / t75 / t73
  t79 = s2 ** 2
  t80 = t79 * s2
  t82 = t73 ** 2
  t83 = t82 ** 2
  t87 = 0.1e1 + t45 * t80 / t83 / 0.2304e4
  t88 = 0.1e1 / t87
  t92 = 0.1e1 + 0.5e1 / 0.648e3 * t37 * s2 * t77 * t88
  t96 = f.my_piecewise3(t64, 0, 0.3e1 / 0.20e2 * t6 * t72 * t92)
  t97 = t7 ** 2
  t99 = t17 / t97
  t100 = t8 - t99
  t101 = f.my_piecewise5(t11, 0, t15, 0, t100)
  t104 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t101)
  t109 = 0.1e1 / t29
  t113 = t6 * t28 * t109 * t59 / 0.10e2
  t114 = t38 * r0
  t121 = t46 ** 2
  t126 = t54 ** 2
  t127 = 0.1e1 / t126
  t137 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t104 * t30 * t59 + t113 + 0.3e1 / 0.20e2 * t6 * t31 * (-0.5e1 / 0.243e3 * t37 * s0 / t40 / t114 * t55 + 0.5e1 / 0.186624e6 * t37 * t121 / t40 / t50 / t114 * t127 * t45))
  t139 = f.my_piecewise5(t15, 0, t11, 0, -t100)
  t142 = f.my_piecewise3(t67, 0, 0.5e1 / 0.3e1 * t69 * t139)
  t150 = t6 * t71 * t109 * t92 / 0.10e2
  t152 = f.my_piecewise3(t64, 0, 0.3e1 / 0.20e2 * t6 * t142 * t30 * t92 + t150)
  vrho_0_ = t63 + t96 + t7 * (t137 + t152)
  t155 = -t8 - t99
  t156 = f.my_piecewise5(t11, 0, t15, 0, t155)
  t159 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t26 * t156)
  t165 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t159 * t30 * t59 + t113)
  t167 = f.my_piecewise5(t15, 0, t11, 0, -t155)
  t170 = f.my_piecewise3(t67, 0, 0.5e1 / 0.3e1 * t69 * t167)
  t175 = t73 * r1
  t182 = t79 ** 2
  t187 = t87 ** 2
  t188 = 0.1e1 / t187
  t198 = f.my_piecewise3(t64, 0, 0.3e1 / 0.20e2 * t6 * t170 * t30 * t92 + t150 + 0.3e1 / 0.20e2 * t6 * t72 * (-0.5e1 / 0.243e3 * t37 * s2 / t75 / t175 * t88 + 0.5e1 / 0.186624e6 * t37 * t182 / t75 / t83 / t175 * t188 * t45))
  vrho_1_ = t63 + t96 + t7 * (t165 + t198)
  t216 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t31 * (0.5e1 / 0.648e3 * t37 * t42 * t55 - 0.5e1 / 0.497664e6 * t37 * t47 / t40 / t50 / t38 * t127 * t45))
  vsigma_0_ = t7 * t216
  vsigma_1_ = 0.0e0
  t232 = f.my_piecewise3(t64, 0, 0.3e1 / 0.20e2 * t6 * t72 * (0.5e1 / 0.648e3 * t37 * t77 * t88 - 0.5e1 / 0.497664e6 * t37 * t80 / t75 / t83 / t73 * t188 * t45))
  vsigma_2_ = t7 * t232
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
  pearson_f0 = lambda s: 1 + 5 / 27 * s ** 2 / (1 + s ** 6)

  pearson_f = lambda x: pearson_f0(X2S * x)

  functional_body = lambda rs, zeta, xt, xs0, xs1: gga_kinetic(f, params, pearson_f, rs, zeta, xs0, xs1)

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
  t29 = t24 / t27
  t30 = t29 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = r0 ** 2
  t37 = t25 ** 2
  t38 = 0.1e1 / t37
  t39 = s0 ** 2
  t40 = t39 * s0
  t42 = t33 ** 2
  t43 = t42 ** 2
  t47 = 0.1e1 + t38 * t40 / t43 / 0.576e3
  t48 = 0.1e1 / t47
  t49 = t32 / t22 / t33 * t48
  t52 = 0.1e1 + 0.5e1 / 0.648e3 * t30 * t49
  t56 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * t52)
  t62 = t33 * r0
  t69 = t39 ** 2
  t75 = t47 ** 2
  t77 = 0.1e1 / t75 * t38
  t86 = f.my_piecewise3(t2, 0, t7 * t20 / t21 * t52 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t23 * (-0.5e1 / 0.243e3 * t30 * t32 / t22 / t62 * t48 + 0.5e1 / 0.46656e5 * t29 * t69 * t32 / t22 / t43 / t62 * t77))
  vrho_0_ = 0.2e1 * r0 * t86 + 0.2e1 * t56
  t103 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t23 * (0.5e1 / 0.648e3 * t29 * t49 - 0.5e1 / 0.124416e6 * t29 * t40 * t32 / t22 / t43 / t33 * t77))
  vsigma_0_ = 0.2e1 * r0 * t103
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
  t29 = t24 / t27
  t30 = t29 * s0
  t31 = 2 ** (0.1e1 / 0.3e1)
  t32 = t31 ** 2
  t33 = r0 ** 2
  t34 = t21 ** 2
  t38 = t25 ** 2
  t39 = 0.1e1 / t38
  t40 = s0 ** 2
  t41 = t40 * s0
  t42 = t39 * t41
  t43 = t33 ** 2
  t44 = t43 ** 2
  t48 = 0.1e1 + t42 / t44 / 0.576e3
  t49 = 0.1e1 / t48
  t50 = t32 / t34 / t33 * t49
  t53 = 0.1e1 + 0.5e1 / 0.648e3 * t30 * t50
  t57 = t20 * t34
  t58 = t33 * r0
  t62 = t32 / t34 / t58 * t49
  t65 = t40 ** 2
  t66 = t29 * t65
  t69 = 0.1e1 / t34 / t44 / t58
  t71 = t48 ** 2
  t72 = 0.1e1 / t71
  t73 = t72 * t39
  t77 = -0.5e1 / 0.243e3 * t30 * t62 + 0.5e1 / 0.46656e5 * t66 * t32 * t69 * t73
  t82 = f.my_piecewise3(t2, 0, t7 * t23 * t53 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t57 * t77)
  t108 = t44 ** 2
  t115 = t38 ** 2
  t117 = 0.1e1 / t71 / t48 / t115
  t126 = f.my_piecewise3(t2, 0, -t7 * t20 / t21 / r0 * t53 / 0.30e2 + t7 * t23 * t77 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t57 * (0.55e2 / 0.729e3 * t30 * t32 / t34 / t43 * t49 - 0.215e3 / 0.139968e6 * t66 * t32 / t34 / t44 / t43 * t73 + 0.5e1 / 0.1679616e7 * t29 * t65 * t41 * t32 / t34 / t108 / t43 * t117))
  v2rho2_0_ = 0.2e1 * r0 * t126 + 0.4e1 * t82
  t134 = 0.1e1 / t34 / t44 / t33
  t139 = 0.5e1 / 0.648e3 * t29 * t50 - 0.5e1 / 0.124416e6 * t29 * t41 * t32 * t134 * t73
  t143 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t57 * t139)
  t149 = t29 * t32
  t168 = f.my_piecewise3(t2, 0, t7 * t23 * t139 / 0.10e2 + 0.3e1 / 0.20e2 * t7 * t57 * (-0.5e1 / 0.243e3 * t29 * t62 + 0.25e2 / 0.46656e5 * t149 * t69 * t72 * t42 - 0.5e1 / 0.4478976e7 * t29 * t65 * t40 * t32 / t34 / t108 / t58 * t117))
  v2rhosigma_0_ = 0.2e1 * r0 * t168 + 0.2e1 * t143
  t189 = f.my_piecewise3(t2, 0, 0.3e1 / 0.20e2 * t7 * t57 * (-0.5e1 / 0.31104e5 * t149 * t134 * t72 * t39 * t40 + 0.5e1 / 0.11943936e8 * t29 * t65 * s0 * t32 / t34 / t108 / t33 * t117))
  v2sigma2_0_ = 0.2e1 * r0 * t189
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
  t30 = t25 / t28
  t31 = t30 * s0
  t32 = 2 ** (0.1e1 / 0.3e1)
  t33 = t32 ** 2
  t34 = r0 ** 2
  t35 = t21 ** 2
  t39 = t26 ** 2
  t40 = 0.1e1 / t39
  t41 = s0 ** 2
  t42 = t41 * s0
  t44 = t34 ** 2
  t45 = t44 ** 2
  t49 = 0.1e1 + t40 * t42 / t45 / 0.576e3
  t50 = 0.1e1 / t49
  t54 = 0.1e1 + 0.5e1 / 0.648e3 * t31 * t33 / t35 / t34 * t50
  t59 = t20 / t21
  t60 = t34 * r0
  t67 = t41 ** 2
  t68 = t30 * t67
  t73 = t49 ** 2
  t75 = 0.1e1 / t73 * t40
  t79 = -0.5e1 / 0.243e3 * t31 * t33 / t35 / t60 * t50 + 0.5e1 / 0.46656e5 * t68 * t33 / t35 / t45 / t60 * t75
  t83 = t20 * t35
  t98 = t30 * t67 * t42
  t99 = t45 ** 2
  t106 = t39 ** 2
  t108 = 0.1e1 / t73 / t49 / t106
  t112 = 0.55e2 / 0.729e3 * t31 * t33 / t35 / t44 * t50 - 0.215e3 / 0.139968e6 * t68 * t33 / t35 / t45 / t44 * t75 + 0.5e1 / 0.1679616e7 * t98 * t33 / t35 / t99 / t44 * t108
  t117 = f.my_piecewise3(t2, 0, -t7 * t24 * t54 / 0.30e2 + t7 * t59 * t79 / 0.5e1 + 0.3e1 / 0.20e2 * t7 * t83 * t112)
  t131 = t44 * r0
  t138 = t45 * t131
  t152 = t67 ** 2
  t159 = t73 ** 2
  t172 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t20 / t21 / t34 * t54 - t7 * t24 * t79 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t59 * t112 + 0.3e1 / 0.20e2 * t7 * t83 * (-0.770e3 / 0.2187e4 * t31 * t33 / t35 / t131 * t50 + 0.1435e4 / 0.69984e5 * t68 * t33 / t35 / t138 * t75 - 0.175e3 / 0.1679616e7 * t98 * t33 / t35 / t99 / t131 * t108 + 0.5e1 / 0.40310784e8 * t30 * t152 * t41 * t33 / t35 / t99 / t138 / t159 / t106 / t39))
  v3rho3_0_ = 0.2e1 * r0 * t172 + 0.6e1 * t117

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
  t31 = t26 / t29
  t32 = t31 * s0
  t33 = 2 ** (0.1e1 / 0.3e1)
  t34 = t33 ** 2
  t35 = t22 ** 2
  t39 = t27 ** 2
  t40 = 0.1e1 / t39
  t41 = s0 ** 2
  t42 = t41 * s0
  t44 = t21 ** 2
  t45 = t44 ** 2
  t49 = 0.1e1 + t40 * t42 / t45 / 0.576e3
  t50 = 0.1e1 / t49
  t54 = 0.1e1 + 0.5e1 / 0.648e3 * t32 * t34 / t35 / t21 * t50
  t60 = t20 / t22 / r0
  t61 = t21 * r0
  t68 = t41 ** 2
  t69 = t31 * t68
  t74 = t49 ** 2
  t76 = 0.1e1 / t74 * t40
  t80 = -0.5e1 / 0.243e3 * t32 * t34 / t35 / t61 * t50 + 0.5e1 / 0.46656e5 * t69 * t34 / t35 / t45 / t61 * t76
  t85 = t20 / t22
  t100 = t31 * t68 * t42
  t101 = t45 ** 2
  t108 = t39 ** 2
  t110 = 0.1e1 / t74 / t49 / t108
  t114 = 0.55e2 / 0.729e3 * t32 * t34 / t35 / t44 * t50 - 0.215e3 / 0.139968e6 * t69 * t34 / t35 / t45 / t44 * t76 + 0.5e1 / 0.1679616e7 * t100 * t34 / t35 / t101 / t44 * t110
  t118 = t20 * t35
  t119 = t44 * r0
  t126 = t45 * t119
  t140 = t68 ** 2
  t142 = t31 * t140 * t41
  t147 = t74 ** 2
  t151 = 0.1e1 / t147 / t108 / t39
  t155 = -0.770e3 / 0.2187e4 * t32 * t34 / t35 / t119 * t50 + 0.1435e4 / 0.69984e5 * t69 * t34 / t35 / t126 * t76 - 0.175e3 / 0.1679616e7 * t100 * t34 / t35 / t101 / t119 * t110 + 0.5e1 / 0.40310784e8 * t142 * t34 / t35 / t101 / t126 * t151
  t160 = f.my_piecewise3(t2, 0, 0.2e1 / 0.45e2 * t7 * t25 * t54 - t7 * t60 * t80 / 0.10e2 + 0.3e1 / 0.10e2 * t7 * t85 * t114 + 0.3e1 / 0.20e2 * t7 * t118 * t155)
  t177 = t44 * t21
  t184 = t45 * t177
  t208 = t101 ** 2
  t215 = t108 ** 2
  t226 = f.my_piecewise3(t2, 0, -0.14e2 / 0.135e3 * t7 * t20 / t22 / t61 * t54 + 0.8e1 / 0.45e2 * t7 * t25 * t80 - t7 * t60 * t114 / 0.5e1 + 0.2e1 / 0.5e1 * t7 * t85 * t155 + 0.3e1 / 0.20e2 * t7 * t118 * (0.13090e5 / 0.6561e4 * t32 * t34 / t35 / t177 * t50 - 0.179585e6 / 0.629856e6 * t69 * t34 / t35 / t184 * t76 + 0.14245e5 / 0.5038848e7 * t100 * t34 / t35 / t101 / t177 * t110 - 0.485e3 / 0.60466176e8 * t142 * t34 / t35 / t101 / t184 * t151 + 0.5e1 / 0.725594112e9 * t31 * t140 * t68 * s0 * t34 / t35 / t208 / t177 / t147 / t49 / t215))
  v4rho4_0_ = 0.2e1 * r0 * t226 + 0.8e1 * t160

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
  t40 = t35 / t38
  t41 = r0 ** 2
  t42 = r0 ** (0.1e1 / 0.3e1)
  t43 = t42 ** 2
  t47 = t36 ** 2
  t48 = 0.1e1 / t47
  t49 = s0 ** 2
  t50 = t49 * s0
  t52 = t41 ** 2
  t53 = t52 ** 2
  t57 = 0.1e1 + t48 * t50 / t53 / 0.2304e4
  t58 = 0.1e1 / t57
  t62 = 0.1e1 + 0.5e1 / 0.648e3 * t40 * s0 / t43 / t41 * t58
  t66 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t67 = t66 ** 2
  t68 = t67 * f.p.zeta_threshold
  t70 = f.my_piecewise3(t21, t68, t23 * t20)
  t71 = 0.1e1 / t32
  t72 = t70 * t71
  t75 = t6 * t72 * t62 / 0.10e2
  t76 = t70 * t33
  t77 = t41 * r0
  t84 = t49 ** 2
  t85 = t40 * t84
  t89 = t57 ** 2
  t90 = 0.1e1 / t89
  t95 = -0.5e1 / 0.243e3 * t40 * s0 / t43 / t77 * t58 + 0.5e1 / 0.186624e6 * t85 / t43 / t53 / t77 * t90 * t48
  t100 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t34 * t62 + t75 + 0.3e1 / 0.20e2 * t6 * t76 * t95)
  t102 = r1 <= f.p.dens_threshold
  t103 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t104 = 0.1e1 + t103
  t105 = t104 <= f.p.zeta_threshold
  t106 = t104 ** (0.1e1 / 0.3e1)
  t107 = t106 ** 2
  t109 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t112 = f.my_piecewise3(t105, 0, 0.5e1 / 0.3e1 * t107 * t109)
  t113 = t112 * t33
  t114 = r1 ** 2
  t115 = r1 ** (0.1e1 / 0.3e1)
  t116 = t115 ** 2
  t120 = s2 ** 2
  t121 = t120 * s2
  t123 = t114 ** 2
  t124 = t123 ** 2
  t128 = 0.1e1 + t48 * t121 / t124 / 0.2304e4
  t129 = 0.1e1 / t128
  t133 = 0.1e1 + 0.5e1 / 0.648e3 * t40 * s2 / t116 / t114 * t129
  t138 = f.my_piecewise3(t105, t68, t107 * t104)
  t139 = t138 * t71
  t142 = t6 * t139 * t133 / 0.10e2
  t144 = f.my_piecewise3(t102, 0, 0.3e1 / 0.20e2 * t6 * t113 * t133 + t142)
  t146 = 0.1e1 / t22
  t147 = t28 ** 2
  t152 = t17 / t24 / t7
  t154 = -0.2e1 * t25 + 0.2e1 * t152
  t155 = f.my_piecewise5(t11, 0, t15, 0, t154)
  t159 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t146 * t147 + 0.5e1 / 0.3e1 * t23 * t155)
  t166 = t6 * t31 * t71 * t62
  t172 = 0.1e1 / t32 / t7
  t176 = t6 * t70 * t172 * t62 / 0.30e2
  t178 = t6 * t72 * t95
  t195 = t53 ** 2
  t202 = t47 ** 2
  t203 = 0.1e1 / t202
  t212 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t159 * t33 * t62 + t166 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t34 * t95 - t176 + t178 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t76 * (0.55e2 / 0.729e3 * t40 * s0 / t43 / t52 * t58 - 0.215e3 / 0.559872e6 * t85 / t43 / t53 / t52 * t90 * t48 + 0.5e1 / 0.26873856e8 * t40 * t84 * t50 / t43 / t195 / t52 / t89 / t57 * t203))
  t213 = 0.1e1 / t106
  t214 = t109 ** 2
  t218 = f.my_piecewise5(t15, 0, t11, 0, -t154)
  t222 = f.my_piecewise3(t105, 0, 0.10e2 / 0.9e1 * t213 * t214 + 0.5e1 / 0.3e1 * t107 * t218)
  t229 = t6 * t112 * t71 * t133
  t234 = t6 * t138 * t172 * t133 / 0.30e2
  t236 = f.my_piecewise3(t102, 0, 0.3e1 / 0.20e2 * t6 * t222 * t33 * t133 + t229 / 0.5e1 - t234)
  d11 = 0.2e1 * t100 + 0.2e1 * t144 + t7 * (t212 + t236)
  t239 = -t8 - t26
  t240 = f.my_piecewise5(t11, 0, t15, 0, t239)
  t243 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t23 * t240)
  t244 = t243 * t33
  t249 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t244 * t62 + t75)
  t251 = f.my_piecewise5(t15, 0, t11, 0, -t239)
  t254 = f.my_piecewise3(t105, 0, 0.5e1 / 0.3e1 * t107 * t251)
  t255 = t254 * t33
  t259 = t138 * t33
  t260 = t114 * r1
  t267 = t120 ** 2
  t268 = t40 * t267
  t272 = t128 ** 2
  t273 = 0.1e1 / t272
  t278 = -0.5e1 / 0.243e3 * t40 * s2 / t116 / t260 * t129 + 0.5e1 / 0.186624e6 * t268 / t116 / t124 / t260 * t273 * t48
  t283 = f.my_piecewise3(t102, 0, 0.3e1 / 0.20e2 * t6 * t255 * t133 + t142 + 0.3e1 / 0.20e2 * t6 * t259 * t278)
  t287 = 0.2e1 * t152
  t288 = f.my_piecewise5(t11, 0, t15, 0, t287)
  t292 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t146 * t240 * t28 + 0.5e1 / 0.3e1 * t23 * t288)
  t299 = t6 * t243 * t71 * t62
  t307 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t292 * t33 * t62 + t299 / 0.10e2 + 0.3e1 / 0.20e2 * t6 * t244 * t95 + t166 / 0.10e2 - t176 + t178 / 0.10e2)
  t311 = f.my_piecewise5(t15, 0, t11, 0, -t287)
  t315 = f.my_piecewise3(t105, 0, 0.10e2 / 0.9e1 * t213 * t251 * t109 + 0.5e1 / 0.3e1 * t107 * t311)
  t322 = t6 * t254 * t71 * t133
  t329 = t6 * t139 * t278
  t332 = f.my_piecewise3(t102, 0, 0.3e1 / 0.20e2 * t6 * t315 * t33 * t133 + t322 / 0.10e2 + t229 / 0.10e2 - t234 + 0.3e1 / 0.20e2 * t6 * t113 * t278 + t329 / 0.10e2)
  d12 = t100 + t144 + t249 + t283 + t7 * (t307 + t332)
  t337 = t240 ** 2
  t341 = 0.2e1 * t25 + 0.2e1 * t152
  t342 = f.my_piecewise5(t11, 0, t15, 0, t341)
  t346 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t146 * t337 + 0.5e1 / 0.3e1 * t23 * t342)
  t353 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t346 * t33 * t62 + t299 / 0.5e1 - t176)
  t354 = t251 ** 2
  t358 = f.my_piecewise5(t15, 0, t11, 0, -t341)
  t362 = f.my_piecewise3(t105, 0, 0.10e2 / 0.9e1 * t213 * t354 + 0.5e1 / 0.3e1 * t107 * t358)
  t387 = t124 ** 2
  t402 = f.my_piecewise3(t102, 0, 0.3e1 / 0.20e2 * t6 * t362 * t33 * t133 + t322 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t255 * t278 - t234 + t329 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t259 * (0.55e2 / 0.729e3 * t40 * s2 / t116 / t123 * t129 - 0.215e3 / 0.559872e6 * t268 / t116 / t124 / t123 * t273 * t48 + 0.5e1 / 0.26873856e8 * t40 * t267 * t121 / t116 / t387 / t123 / t272 / t128 * t203))
  d22 = 0.2e1 * t249 + 0.2e1 * t283 + t7 * (t353 + t402)
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
  t51 = t46 / t49
  t52 = r0 ** 2
  t53 = r0 ** (0.1e1 / 0.3e1)
  t54 = t53 ** 2
  t58 = t47 ** 2
  t59 = 0.1e1 / t58
  t60 = s0 ** 2
  t61 = t60 * s0
  t63 = t52 ** 2
  t64 = t63 ** 2
  t68 = 0.1e1 + t59 * t61 / t64 / 0.2304e4
  t69 = 0.1e1 / t68
  t73 = 0.1e1 + 0.5e1 / 0.648e3 * t51 * s0 / t54 / t52 * t69
  t79 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t32 * t28)
  t80 = 0.1e1 / t43
  t81 = t79 * t80
  t85 = t79 * t44
  t86 = t52 * r0
  t93 = t60 ** 2
  t94 = t51 * t93
  t98 = t68 ** 2
  t99 = 0.1e1 / t98
  t104 = -0.5e1 / 0.243e3 * t51 * s0 / t54 / t86 * t69 + 0.5e1 / 0.186624e6 * t94 / t54 / t64 / t86 * t99 * t59
  t108 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t109 = t108 ** 2
  t110 = t109 * f.p.zeta_threshold
  t112 = f.my_piecewise3(t21, t110, t32 * t20)
  t114 = 0.1e1 / t43 / t7
  t115 = t112 * t114
  t119 = t112 * t80
  t123 = t112 * t44
  t138 = t51 * t93 * t61
  t139 = t64 ** 2
  t144 = 0.1e1 / t98 / t68
  t146 = t58 ** 2
  t147 = 0.1e1 / t146
  t151 = 0.55e2 / 0.729e3 * t51 * s0 / t54 / t63 * t69 - 0.215e3 / 0.559872e6 * t94 / t54 / t64 / t63 * t99 * t59 + 0.5e1 / 0.26873856e8 * t138 / t54 / t139 / t63 * t144 * t147
  t156 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t45 * t73 + t6 * t81 * t73 / 0.5e1 + 0.3e1 / 0.10e2 * t6 * t85 * t104 - t6 * t115 * t73 / 0.30e2 + t6 * t119 * t104 / 0.5e1 + 0.3e1 / 0.20e2 * t6 * t123 * t151)
  t158 = r1 <= f.p.dens_threshold
  t159 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t160 = 0.1e1 + t159
  t161 = t160 <= f.p.zeta_threshold
  t162 = t160 ** (0.1e1 / 0.3e1)
  t163 = 0.1e1 / t162
  t165 = f.my_piecewise5(t15, 0, t11, 0, -t27)
  t166 = t165 ** 2
  t169 = t162 ** 2
  t171 = f.my_piecewise5(t15, 0, t11, 0, -t37)
  t175 = f.my_piecewise3(t161, 0, 0.10e2 / 0.9e1 * t163 * t166 + 0.5e1 / 0.3e1 * t169 * t171)
  t177 = r1 ** 2
  t178 = r1 ** (0.1e1 / 0.3e1)
  t179 = t178 ** 2
  t183 = s2 ** 2
  t186 = t177 ** 2
  t187 = t186 ** 2
  t196 = 0.1e1 + 0.5e1 / 0.648e3 * t51 * s2 / t179 / t177 / (0.1e1 + t59 * t183 * s2 / t187 / 0.2304e4)
  t202 = f.my_piecewise3(t161, 0, 0.5e1 / 0.3e1 * t169 * t165)
  t208 = f.my_piecewise3(t161, t110, t169 * t160)
  t214 = f.my_piecewise3(t158, 0, 0.3e1 / 0.20e2 * t6 * t175 * t44 * t196 + t6 * t202 * t80 * t196 / 0.5e1 - t6 * t208 * t114 * t196 / 0.30e2)
  t224 = t24 ** 2
  t228 = 0.6e1 * t34 - 0.6e1 * t17 / t224
  t229 = f.my_piecewise5(t11, 0, t15, 0, t228)
  t233 = f.my_piecewise3(t21, 0, -0.10e2 / 0.27e2 / t22 / t20 * t29 * t28 + 0.10e2 / 0.3e1 * t23 * t28 * t38 + 0.5e1 / 0.3e1 * t32 * t229)
  t256 = 0.1e1 / t43 / t24
  t267 = t63 * r0
  t274 = t64 * t267
  t288 = t93 ** 2
  t294 = t98 ** 2
  t307 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t233 * t44 * t73 + 0.3e1 / 0.10e2 * t6 * t42 * t80 * t73 + 0.9e1 / 0.20e2 * t6 * t45 * t104 - t6 * t79 * t114 * t73 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t81 * t104 + 0.9e1 / 0.20e2 * t6 * t85 * t151 + 0.2e1 / 0.45e2 * t6 * t112 * t256 * t73 - t6 * t115 * t104 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t119 * t151 + 0.3e1 / 0.20e2 * t6 * t123 * (-0.770e3 / 0.2187e4 * t51 * s0 / t54 / t267 * t69 + 0.1435e4 / 0.279936e6 * t94 / t54 / t274 * t99 * t59 - 0.175e3 / 0.26873856e8 * t138 / t54 / t139 / t267 * t144 * t147 + 0.5e1 / 0.2579890176e10 * t51 * t288 * t60 / t54 / t139 / t274 / t294 / t146 / t58))
  t317 = f.my_piecewise5(t15, 0, t11, 0, -t228)
  t321 = f.my_piecewise3(t161, 0, -0.10e2 / 0.27e2 / t162 / t160 * t166 * t165 + 0.10e2 / 0.3e1 * t163 * t165 * t171 + 0.5e1 / 0.3e1 * t169 * t317)
  t339 = f.my_piecewise3(t158, 0, 0.3e1 / 0.20e2 * t6 * t321 * t44 * t196 + 0.3e1 / 0.10e2 * t6 * t175 * t80 * t196 - t6 * t202 * t114 * t196 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t208 * t256 * t196)
  d111 = 0.3e1 * t156 + 0.3e1 * t214 + t7 * (t307 + t339)

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
  t63 = t58 / t61
  t64 = r0 ** 2
  t65 = r0 ** (0.1e1 / 0.3e1)
  t66 = t65 ** 2
  t70 = t59 ** 2
  t71 = 0.1e1 / t70
  t72 = s0 ** 2
  t73 = t72 * s0
  t75 = t64 ** 2
  t76 = t75 ** 2
  t80 = 0.1e1 + t71 * t73 / t76 / 0.2304e4
  t81 = 0.1e1 / t80
  t85 = 0.1e1 + 0.5e1 / 0.648e3 * t63 * s0 / t66 / t64 * t81
  t94 = f.my_piecewise3(t21, 0, 0.10e2 / 0.9e1 * t34 * t30 + 0.5e1 / 0.3e1 * t44 * t41)
  t95 = 0.1e1 / t55
  t96 = t94 * t95
  t100 = t94 * t56
  t101 = t64 * r0
  t108 = t72 ** 2
  t109 = t63 * t108
  t113 = t80 ** 2
  t114 = 0.1e1 / t113
  t119 = -0.5e1 / 0.243e3 * t63 * s0 / t66 / t101 * t81 + 0.5e1 / 0.186624e6 * t109 / t66 / t76 / t101 * t114 * t71
  t125 = f.my_piecewise3(t21, 0, 0.5e1 / 0.3e1 * t44 * t29)
  t127 = 0.1e1 / t55 / t7
  t128 = t125 * t127
  t132 = t125 * t95
  t136 = t125 * t56
  t151 = t63 * t108 * t73
  t152 = t76 ** 2
  t157 = 0.1e1 / t113 / t80
  t159 = t70 ** 2
  t160 = 0.1e1 / t159
  t164 = 0.55e2 / 0.729e3 * t63 * s0 / t66 / t75 * t81 - 0.215e3 / 0.559872e6 * t109 / t66 / t76 / t75 * t114 * t71 + 0.5e1 / 0.26873856e8 * t151 / t66 / t152 / t75 * t157 * t160
  t168 = f.p.zeta_threshold ** (0.1e1 / 0.3e1)
  t169 = t168 ** 2
  t170 = t169 * f.p.zeta_threshold
  t172 = f.my_piecewise3(t21, t170, t44 * t20)
  t174 = 0.1e1 / t55 / t25
  t175 = t172 * t174
  t179 = t172 * t127
  t183 = t172 * t95
  t187 = t172 * t56
  t188 = t75 * r0
  t195 = t76 * t188
  t209 = t108 ** 2
  t211 = t63 * t209 * t72
  t215 = t113 ** 2
  t216 = 0.1e1 / t215
  t219 = 0.1e1 / t159 / t70
  t223 = -0.770e3 / 0.2187e4 * t63 * s0 / t66 / t188 * t81 + 0.1435e4 / 0.279936e6 * t109 / t66 / t195 * t114 * t71 - 0.175e3 / 0.26873856e8 * t151 / t66 / t152 / t188 * t157 * t160 + 0.5e1 / 0.2579890176e10 * t211 / t66 / t152 / t195 * t216 * t219
  t228 = f.my_piecewise3(t1, 0, 0.3e1 / 0.20e2 * t6 * t57 * t85 + 0.3e1 / 0.10e2 * t6 * t96 * t85 + 0.9e1 / 0.20e2 * t6 * t100 * t119 - t6 * t128 * t85 / 0.10e2 + 0.3e1 / 0.5e1 * t6 * t132 * t119 + 0.9e1 / 0.20e2 * t6 * t136 * t164 + 0.2e1 / 0.45e2 * t6 * t175 * t85 - t6 * t179 * t119 / 0.10e2 + 0.3e1 / 0.10e2 * t6 * t183 * t164 + 0.3e1 / 0.20e2 * t6 * t187 * t223)
  t230 = r1 <= f.p.dens_threshold
  t231 = f.my_piecewise5(t15, t12, t11, t16, -t18)
  t232 = 0.1e1 + t231
  t233 = t232 <= f.p.zeta_threshold
  t234 = t232 ** (0.1e1 / 0.3e1)
  t236 = 0.1e1 / t234 / t232
  t238 = f.my_piecewise5(t15, 0, t11, 0, -t28)
  t239 = t238 ** 2
  t243 = 0.1e1 / t234
  t244 = t243 * t238
  t246 = f.my_piecewise5(t15, 0, t11, 0, -t40)
  t249 = t234 ** 2
  t251 = f.my_piecewise5(t15, 0, t11, 0, -t49)
  t255 = f.my_piecewise3(t233, 0, -0.10e2 / 0.27e2 * t236 * t239 * t238 + 0.10e2 / 0.3e1 * t244 * t246 + 0.5e1 / 0.3e1 * t249 * t251)
  t257 = r1 ** 2
  t258 = r1 ** (0.1e1 / 0.3e1)
  t259 = t258 ** 2
  t263 = s2 ** 2
  t266 = t257 ** 2
  t267 = t266 ** 2
  t276 = 0.1e1 + 0.5e1 / 0.648e3 * t63 * s2 / t259 / t257 / (0.1e1 + t71 * t263 * s2 / t267 / 0.2304e4)
  t285 = f.my_piecewise3(t233, 0, 0.10e2 / 0.9e1 * t243 * t239 + 0.5e1 / 0.3e1 * t249 * t246)
  t292 = f.my_piecewise3(t233, 0, 0.5e1 / 0.3e1 * t249 * t238)
  t298 = f.my_piecewise3(t233, t170, t249 * t232)
  t304 = f.my_piecewise3(t230, 0, 0.3e1 / 0.20e2 * t6 * t255 * t56 * t276 + 0.3e1 / 0.10e2 * t6 * t285 * t95 * t276 - t6 * t292 * t127 * t276 / 0.10e2 + 0.2e1 / 0.45e2 * t6 * t298 * t174 * t276)
  t306 = t20 ** 2
  t309 = t30 ** 2
  t315 = t41 ** 2
  t324 = -0.24e2 * t46 + 0.24e2 * t17 / t45 / t7
  t325 = f.my_piecewise5(t11, 0, t15, 0, t324)
  t329 = f.my_piecewise3(t21, 0, 0.40e2 / 0.81e2 / t22 / t306 * t309 - 0.20e2 / 0.9e1 * t24 * t30 * t41 + 0.10e2 / 0.3e1 * t34 * t315 + 0.40e2 / 0.9e1 * t35 * t50 + 0.5e1 / 0.3e1 * t44 * t325)
  t361 = t75 * t64
  t368 = t76 * t361
  t392 = t152 ** 2
  t399 = t159 ** 2
  t421 = 0.1e1 / t55 / t36
  t426 = 0.3e1 / 0.20e2 * t6 * t329 * t56 * t85 + 0.3e1 / 0.5e1 * t6 * t57 * t119 + 0.6e1 / 0.5e1 * t6 * t96 * t119 + 0.9e1 / 0.10e2 * t6 * t100 * t164 - 0.2e1 / 0.5e1 * t6 * t128 * t119 + 0.6e1 / 0.5e1 * t6 * t132 * t164 + 0.3e1 / 0.5e1 * t6 * t136 * t223 + 0.8e1 / 0.45e2 * t6 * t175 * t119 - t6 * t179 * t164 / 0.5e1 + 0.2e1 / 0.5e1 * t6 * t183 * t223 + 0.3e1 / 0.20e2 * t6 * t187 * (0.13090e5 / 0.6561e4 * t63 * s0 / t66 / t361 * t81 - 0.179585e6 / 0.2519424e7 * t109 / t66 / t368 * t114 * t71 + 0.14245e5 / 0.80621568e8 * t151 / t66 / t152 / t361 * t157 * t160 - 0.485e3 / 0.3869835264e10 * t211 / t66 / t152 / t368 * t216 * t219 + 0.5e1 / 0.185752092672e12 * t63 * t209 * t108 * s0 / t66 / t392 / t361 / t215 / t80 / t399) + 0.2e1 / 0.5e1 * t6 * t54 * t95 * t85 - t6 * t94 * t127 * t85 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t125 * t174 * t85 - 0.14e2 / 0.135e3 * t6 * t172 * t421 * t85
  t427 = f.my_piecewise3(t1, 0, t426)
  t428 = t232 ** 2
  t431 = t239 ** 2
  t437 = t246 ** 2
  t443 = f.my_piecewise5(t15, 0, t11, 0, -t324)
  t447 = f.my_piecewise3(t233, 0, 0.40e2 / 0.81e2 / t234 / t428 * t431 - 0.20e2 / 0.9e1 * t236 * t239 * t246 + 0.10e2 / 0.3e1 * t243 * t437 + 0.40e2 / 0.9e1 * t244 * t251 + 0.5e1 / 0.3e1 * t249 * t443)
  t469 = f.my_piecewise3(t230, 0, 0.3e1 / 0.20e2 * t6 * t447 * t56 * t276 + 0.2e1 / 0.5e1 * t6 * t255 * t95 * t276 - t6 * t285 * t127 * t276 / 0.5e1 + 0.8e1 / 0.45e2 * t6 * t292 * t174 * t276 - 0.14e2 / 0.135e3 * t6 * t298 * t421 * t276)
  d1111 = 0.4e1 * t228 + 0.4e1 * t304 + t7 * (t427 + t469)

  res = {'v4rho4': d1111}
  return res
