"""Generated from lda_c_ml1.mpl."""

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
  params_fc_raw = params.fc
  if isinstance(params_fc_raw, (str, bytes, dict)):
    params_fc = params_fc_raw
  else:
    try:
      params_fc_seq = list(params_fc_raw)
    except TypeError:
      params_fc = params_fc_raw
    else:
      params_fc_seq = np.asarray(params_fc_seq, dtype=np.float64)
      params_fc = np.concatenate((np.array([np.nan], dtype=np.float64), params_fc_seq))
  params_q_raw = params.q
  if isinstance(params_q_raw, (str, bytes, dict)):
    params_q = params_q_raw
  else:
    try:
      params_q_seq = list(params_q_raw)
    except TypeError:
      params_q = params_q_raw
    else:
      params_q_seq = np.asarray(params_q_seq, dtype=np.float64)
      params_q = np.concatenate((np.array([np.nan], dtype=np.float64), params_q_seq))

  ml1_C = 6.187335

  ml1_b = np.array([np.nan, 2.763169, 1.757515, 1.741397, 0.568985, 1.572202, 1.885389], dtype=np.float64)

  ml1_alpha = lambda z: params_fc * ((1 + z) ** params_q + (1 - z) ** params_q)

  ml1_beta = lambda z: (1 - z ** 2) ** (1 / 3) / ((1 + z) ** (1 / 3) + (1 - z) ** (1 / 3))

  ml1_k = lambda rs, z: ml1_C * f.n_total(rs) ** (1 / 3) * ml1_alpha(z) * ml1_beta(z)

  ml1_Q = lambda rs, z: -ml1_b[1] / (1 + ml1_b[2] * ml1_k(rs, z)) + ml1_b[3] * jnp.log(1 + ml1_b[4] / ml1_k(rs, z)) / ml1_k(rs, z) + ml1_b[5] / ml1_k(rs, z) - ml1_b[6] / ml1_k(rs, z) ** 2

  ml1_f = lambda rs, z: f.n_total(rs) * f.my_piecewise3(1 - jnp.abs(z) <= f.p.zeta_threshold, 0, (1 - z ** 2) / 4 * ml1_Q(rs, f.z_thr(z)))

  functional_body = lambda rs, z: ml1_f(rs, z)

  res = functional_body(
      f.r_ws(f.dens(r0, r1)),
      f.zeta(r0, r1),
  )
  return res


def unpol(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau
  params_fc_raw = params.fc
  if isinstance(params_fc_raw, (str, bytes, dict)):
    params_fc = params_fc_raw
  else:
    try:
      params_fc_seq = list(params_fc_raw)
    except TypeError:
      params_fc = params_fc_raw
    else:
      params_fc_seq = np.asarray(params_fc_seq, dtype=np.float64)
      params_fc = np.concatenate((np.array([np.nan], dtype=np.float64), params_fc_seq))
  params_q_raw = params.q
  if isinstance(params_q_raw, (str, bytes, dict)):
    params_q = params_q_raw
  else:
    try:
      params_q_seq = list(params_q_raw)
    except TypeError:
      params_q = params_q_raw
    else:
      params_q_seq = np.asarray(params_q_seq, dtype=np.float64)
      params_q = np.concatenate((np.array([np.nan], dtype=np.float64), params_q_seq))

  ml1_C = 6.187335

  ml1_b = np.array([np.nan, 2.763169, 1.757515, 1.741397, 0.568985, 1.572202, 1.885389], dtype=np.float64)

  ml1_alpha = lambda z: params_fc * ((1 + z) ** params_q + (1 - z) ** params_q)

  ml1_beta = lambda z: (1 - z ** 2) ** (1 / 3) / ((1 + z) ** (1 / 3) + (1 - z) ** (1 / 3))

  ml1_k = lambda rs, z: ml1_C * f.n_total(rs) ** (1 / 3) * ml1_alpha(z) * ml1_beta(z)

  ml1_Q = lambda rs, z: -ml1_b[1] / (1 + ml1_b[2] * ml1_k(rs, z)) + ml1_b[3] * jnp.log(1 + ml1_b[4] / ml1_k(rs, z)) / ml1_k(rs, z) + ml1_b[5] / ml1_k(rs, z) - ml1_b[6] / ml1_k(rs, z) ** 2

  ml1_f = lambda rs, z: f.n_total(rs) * f.my_piecewise3(1 - jnp.abs(z) <= f.p.zeta_threshold, 0, (1 - z ** 2) / 4 * ml1_Q(rs, f.z_thr(z)))

  functional_body = lambda rs, z: ml1_f(rs, z)

  res = functional_body(
      f.r_ws(f.dens(r0 / 2, r0 / 2)),
      f.zeta(r0 / 2, r0 / 2),
  )
  return res

def pol_vxc(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  f = funcs(p)
  params = f.params
  (r0, r1), (s0, s1, s2), (l0, l1), (tau0, tau1) = r, s, l, tau

  t1 = r0 + r1
  t2 = r0 - r1
  t3 = 0.1e1 / t1
  t4 = t2 * t3
  t5 = abs(t4)
  t7 = 0.1e1 - t5 <= f.p.zeta_threshold
  t8 = t2 ** 2
  t9 = t1 ** 2
  t10 = 0.1e1 / t9
  t12 = -t8 * t10 + 0.1e1
  t13 = t1 ** (0.1e1 / 0.3e1)
  t14 = t13 * params.fc
  t16 = 0.1e1 + t4 <= f.p.zeta_threshold
  t17 = f.p.zeta_threshold - 0.1e1
  t19 = 0.1e1 - t4 <= f.p.zeta_threshold
  t21 = f.my_piecewise5(t16, t17, t19, -t17, t4)
  t22 = 0.1e1 + t21
  t23 = t22 ** params.q
  t24 = 0.1e1 - t21
  t25 = t24 ** params.q
  t26 = t23 + t25
  t27 = t21 ** 2
  t28 = 0.1e1 - t27
  t29 = t28 ** (0.1e1 / 0.3e1)
  t31 = t22 ** (0.1e1 / 0.3e1)
  t32 = t24 ** (0.1e1 / 0.3e1)
  t33 = t31 + t32
  t34 = 0.1e1 / t33
  t35 = t26 * t29 * t34
  t38 = 0.1e1 + 0.10874334072525e2 * t14 * t35
  t41 = 0.1e1 / t13
  t42 = 0.1e1 / params.fc
  t43 = t41 * t42
  t44 = 0.1e1 / t26
  t45 = 0.1e1 / t29
  t46 = t44 * t45
  t47 = t46 * t33
  t48 = t43 * t47
  t50 = 0.1e1 + 0.91959623973811018798885141987624720497597107640042e-1 * t48
  t51 = jnp.log(t50)
  t52 = t51 * t41
  t53 = t52 * t42
  t57 = t13 ** 2
  t58 = 0.1e1 / t57
  t59 = params.fc ** 2
  t60 = 0.1e1 / t59
  t61 = t58 * t60
  t62 = t26 ** 2
  t63 = 0.1e1 / t62
  t64 = t29 ** 2
  t65 = 0.1e1 / t64
  t67 = t33 ** 2
  t68 = t63 * t65 * t67
  t71 = -0.2763169e1 / t38 + 0.28144540420067767463698021846239132033419881095819e0 * t53 * t47 + 0.25410002852601321893836360888815620941810973545153e0 * t48 - 0.49248579417833934398903541033809924858145107368554e-1 * t61 * t68
  t74 = f.my_piecewise3(t7, 0, t12 * t71 / 0.4e1)
  t76 = 0.2e1 * t1 * t74
  t77 = t2 * t10
  t80 = t8 / t9 / t1
  t84 = t38 ** 2
  t85 = 0.1e1 / t84
  t88 = 0.36247780241750000000000000000000000000000000000000e1 * t58 * params.fc * t35
  t89 = t23 * params.q
  t91 = f.my_piecewise5(t16, 0, t19, 0, t3 - t77)
  t92 = 0.1e1 / t22
  t95 = t25 * params.q
  t96 = 0.1e1 / t24
  t99 = t89 * t91 * t92 - t95 * t91 * t96
  t104 = t14 * t26
  t105 = t65 * t34
  t106 = t21 * t91
  t111 = t29 / t67
  t112 = t31 ** 2
  t113 = 0.1e1 / t112
  t115 = t32 ** 2
  t116 = 0.1e1 / t115
  t119 = t113 * t91 / 0.3e1 - t116 * t91 / 0.3e1
  t127 = 0.1e1 / t13 / t1
  t129 = t127 * t42 * t47
  t130 = 0.30653207991270339599628380662541573499199035880014e-1 * t129
  t131 = t43 * t63
  t132 = t45 * t33
  t134 = t131 * t132 * t99
  t136 = t43 * t44
  t139 = 0.1e1 / t29 / t28 * t33
  t140 = t139 * t106
  t141 = t136 * t140
  t143 = t46 * t119
  t144 = t43 * t143
  t147 = 0.1e1 / t50
  t150 = t42 * t44
  t151 = t150 * t132
  t157 = 0.93815134733559224878993406154130440111399603652730e-1 * t51 * t127 * t42 * t47
  t158 = t63 * t45
  t163 = t52 * t150
  t168 = 0.84700009508671072979454536296052069806036578483843e-1 * t129
  t176 = 0.32832386278555956265935694022539949905430071579036e-1 / t57 / t1 * t60 * t68
  t179 = t61 / t62 / t26
  t180 = t65 * t67
  t184 = t61 * t63
  t187 = 0.1e1 / t64 / t28 * t67
  t191 = t65 * t33
  t195 = 0.2763169e1 * t85 * (t88 + 0.10874334072525e2 * t14 * t99 * t29 * t34 - 0.72495560483500000000000000000000000000000000000000e1 * t104 * t105 * t106 - 0.10874334072525e2 * t104 * t111 * t119) + 0.28144540420067767463698021846239132033419881095819e0 * (-t130 - 0.91959623973811018798885141987624720497597107640042e-1 * t134 + 0.61306415982540679199256761325083146998398071760028e-1 * t141 + 0.91959623973811018798885141987624720497597107640042e-1 * t144) * t147 * t41 * t151 - t157 - 0.28144540420067767463698021846239132033419881095819e0 * t53 * t158 * t33 * t99 + 0.18763026946711844975798681230826088022279920730546e0 * t163 * t140 + 0.28144540420067767463698021846239132033419881095819e0 * t53 * t143 - t168 - 0.25410002852601321893836360888815620941810973545153e0 * t134 + 0.16940001901734214595890907259210413961207315696769e0 * t141 + 0.25410002852601321893836360888815620941810973545153e0 * t144 + t176 + 0.98497158835667868797807082067619849716290214737108e-1 * t179 * t180 * t99 - 0.65664772557111912531871388045079899810860143158072e-1 * t184 * t187 * t106 - 0.98497158835667868797807082067619849716290214737108e-1 * t184 * t191 * t119
  t199 = f.my_piecewise3(t7, 0, (-0.2e1 * t77 + 0.2e1 * t80) * t71 / 0.4e1 + t12 * t195 / 0.4e1)
  vrho_0_ = t9 * t199 + t76
  t205 = f.my_piecewise5(t16, 0, t19, 0, -t3 - t77)
  t210 = t89 * t205 * t92 - t95 * t205 * t96
  t215 = t21 * t205
  t222 = t113 * t205 / 0.3e1 - t116 * t205 / 0.3e1
  t230 = t131 * t132 * t210
  t232 = t139 * t215
  t233 = t136 * t232
  t235 = t46 * t222
  t236 = t43 * t235
  t263 = 0.2763169e1 * t85 * (t88 + 0.10874334072525e2 * t14 * t210 * t29 * t34 - 0.72495560483500000000000000000000000000000000000000e1 * t104 * t105 * t215 - 0.10874334072525e2 * t104 * t111 * t222) + 0.28144540420067767463698021846239132033419881095819e0 * (-t130 - 0.91959623973811018798885141987624720497597107640042e-1 * t230 + 0.61306415982540679199256761325083146998398071760028e-1 * t233 + 0.91959623973811018798885141987624720497597107640042e-1 * t236) * t147 * t41 * t151 - t157 - 0.28144540420067767463698021846239132033419881095819e0 * t53 * t158 * t33 * t210 + 0.18763026946711844975798681230826088022279920730546e0 * t163 * t232 + 0.28144540420067767463698021846239132033419881095819e0 * t53 * t235 - t168 - 0.25410002852601321893836360888815620941810973545153e0 * t230 + 0.16940001901734214595890907259210413961207315696769e0 * t233 + 0.25410002852601321893836360888815620941810973545153e0 * t236 + t176 + 0.98497158835667868797807082067619849716290214737108e-1 * t179 * t180 * t210 - 0.65664772557111912531871388045079899810860143158072e-1 * t184 * t187 * t215 - 0.98497158835667868797807082067619849716290214737108e-1 * t184 * t191 * t222
  t267 = f.my_piecewise3(t7, 0, (0.2e1 * t77 + 0.2e1 * t80) * t71 / 0.4e1 + t12 * t263 / 0.4e1)
  vrho_1_ = t9 * t267 + t76

  res = {'vrho': jnp.stack([vrho_0_, vrho_1_], axis=-1)}
  return res


def unpol_vxc(p, r, s=None, l=None, tau=None):
  f = funcs(p)
  params = f.params
  r0, s0, l0, tau0 = r, s, l, tau

  t1 = 0.1e1 <= f.p.zeta_threshold
  t2 = r0 ** (0.1e1 / 0.3e1)
  t4 = f.p.zeta_threshold - 0.1e1
  t6 = f.my_piecewise5(t1, t4, t1, -t4, 0)
  t7 = 0.1e1 + t6
  t8 = t7 ** params.q
  t9 = 0.1e1 - t6
  t10 = t9 ** params.q
  t11 = t8 + t10
  t12 = t6 ** 2
  t14 = (0.1e1 - t12) ** (0.1e1 / 0.3e1)
  t16 = t7 ** (0.1e1 / 0.3e1)
  t17 = t9 ** (0.1e1 / 0.3e1)
  t18 = t16 + t17
  t20 = t11 * t14 / t18
  t23 = 0.1e1 + 0.10874334072525e2 * t2 * params.fc * t20
  t26 = 0.1e1 / t2
  t27 = 0.1e1 / params.fc
  t32 = 0.1e1 / t11 / t14 * t18
  t33 = t26 * t27 * t32
  t35 = 0.1e1 + 0.91959623973811018798885141987624720497597107640042e-1 * t33
  t36 = jnp.log(t35)
  t42 = t2 ** 2
  t43 = 0.1e1 / t42
  t44 = params.fc ** 2
  t45 = 0.1e1 / t44
  t47 = t11 ** 2
  t48 = 0.1e1 / t47
  t49 = t14 ** 2
  t50 = 0.1e1 / t49
  t52 = t18 ** 2
  t53 = t48 * t50 * t52
  t57 = f.my_piecewise3(t1, 0, -0.69079225000000000000000000000000000000000000000000e0 / t23 + 0.70361351050169418659245054615597830083549702739548e-1 * t36 * t26 * t27 * t32 + 0.63525007131503304734590902222039052354527433862882e-1 * t33 - 0.12312144854458483599725885258452481214536276842138e-1 * t43 * t45 * t53)
  t60 = r0 ** 2
  t61 = t23 ** 2
  t69 = 0.1e1 / t42 / r0 * t45
  t77 = 0.1e1 / t2 / r0
  t88 = f.my_piecewise3(t1, 0, 0.25039685670704026437500000000000000000000000000000e1 / t61 * t43 * params.fc * t20 - 0.21568011282876309254216097560827039616727033320625e-2 * t69 * t48 * t50 * t52 / t35 - 0.23453783683389806219748351538532610027849900913183e-1 * t36 * t77 * t27 * t32 - 0.21175002377167768244863634074013017451509144620961e-1 * t77 * t27 * t32 + 0.82080965696389890664839235056349874763575178947587e-2 * t69 * t53)
  vrho_0_ = 0.2e1 * r0 * t57 + t60 * t88

  res = {'vrho': vrho_0_}
  return res
