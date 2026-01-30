"""Deorbitalized r2SCAN-L exchange functional."""

from __future__ import annotations

from . import mgga_x_r2scan as _base_module
from .deorbitalized_common import (
  evaluate_deorbitalized,
  prepare_base_params,
  prepare_pc07_params,
)

_BASE_FIELDS = ("c1", "c2", "d", "dp2", "eta", "k1")


def pol(p, r, s=(None, None, None), l=(None, None), tau=(None, None)):
  base = prepare_base_params("mgga_x_r2scan", True, p.params, _BASE_FIELDS)
  pc07 = prepare_pc07_params(True, p.params)
  return evaluate_deorbitalized(_base_module, base, pc07, r, s, l, polarized=True)


def unpol(p, r, s=None, l=None, tau=None):
  base = prepare_base_params("mgga_x_r2scan", False, p.params, _BASE_FIELDS)
  pc07 = prepare_pc07_params(False, p.params)
  return evaluate_deorbitalized(_base_module, base, pc07, r, s, l, polarized=False)
