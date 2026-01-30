"""revSCAN exchange helper that reuses the SCAN Maple kernel.

LibXC implements revSCAN by retuning the SCAN parameters without changing the
analytic form.  Instead of generating a separate Maple file (which is not
present upstream), we delegate to the existing ``mgga_x_scan`` module so that
the AD path can import an EXC leaf for revSCAN-L and related deorbitalized
variants.
"""

from __future__ import annotations

from . import mgga_x_scan as _base_module


def pol(p, *args, **kwargs):
  return _base_module.pol(p, *args, **kwargs)


def unpol(p, *args, **kwargs):
  return _base_module.unpol(p, *args, **kwargs)


def pol_vxc(p, *args, **kwargs):
  return _base_module.pol_vxc(p, *args, **kwargs)


def unpol_vxc(p, *args, **kwargs):
  return _base_module.unpol_vxc(p, *args, **kwargs)


def pol_fxc(p, *args, **kwargs):
  return _base_module.pol_fxc(p, *args, **kwargs)


def unpol_fxc(p, *args, **kwargs):
  return _base_module.unpol_fxc(p, *args, **kwargs)


def pol_kxc(p, *args, **kwargs):
  return _base_module.pol_kxc(p, *args, **kwargs)


def unpol_kxc(p, *args, **kwargs):
  return _base_module.unpol_kxc(p, *args, **kwargs)


def pol_lxc(p, *args, **kwargs):
  return _base_module.pol_lxc(p, *args, **kwargs)


def unpol_lxc(p, *args, **kwargs):
  return _base_module.unpol_lxc(p, *args, **kwargs)
