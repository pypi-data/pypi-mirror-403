"""Mappings between JXC functional names and LibXC registry aliases."""

from __future__ import annotations

from jxc.get_params import PARAM_ALIASES

# Base remaps reused from parameter aliasing.
LIBXC_ALIAS_REMAP: dict[str, str] = {
    name: canonical
    for name, canonical in PARAM_ALIASES.items()
    if canonical != name
}

# Additional LibXC remaps discovered from parity probing.
_ADDITIONAL_REMAPS: dict[str, str | None] = {
    "gga_k_mpbe": "gga_k_pbe4",
    "gga_k_pg": "gga_k_pg1",
    "gga_k_pw86": "gga_k_fr_pw86",
    "gga_k_tflw": "gga_k_tfvw",
    "gga_x_bkl": "gga_x_bkl1",
  "gga_x_dk87": "gga_x_dk87_r1",
  "gga_x_ft97": "gga_x_ft97_b",
  "gga_x_hjs": "gga_x_hjs_b88",
  "gga_x_hjs_b88": "gga_x_hjs_b88_v2",
    "gga_x_kt": "gga_x_kt1",
    "gga_x_s12": "gga_x_s12g",
    "gga_x_vmt": "gga_x_vmt_pbe",
    "gga_x_vmt84": "gga_x_vmt84_pbe",
    "gga_xc_b97": "gga_xc_b97_d",
    # Map ωB97x family variants to canonical Maple leaf wb97 for codegen/runtime.
    # Parameter objects (cam_omega/alpha/beta, internal coeffs) differentiate the variants.
    "hyb_gga_xc_wb97x": "hyb_gga_xc_wb97",
    "hyb_gga_xc_wb97x_d": "hyb_gga_xc_wb97",
    "hyb_gga_xc_wb97x_d3": "hyb_gga_xc_wb97",
    "hyb_gga_xc_wb97x_v": "hyb_gga_xc_wb97",
    "hyb_gga_x_cam_s12": "hyb_gga_x_cam_s12g",
    "hyb_mgga_xc_wb97mv": "hyb_mgga_xc_wb97m_v",
    "hyb_mgga_xc_wb97m_v": "hyb_mgga_xc_wb97mv",
    "lda_c_epc18": "lda_c_epc18_1",
    "lda_xc_1d_ehwlrg": "lda_xc_1d_ehwlrg_1",
    "mgga_c_ltapw": "mgga_c_hltapw",
    "mgga_c_m06l": "mgga_c_m06_l",
    "mgga_c_m08": "mgga_c_m08_so",
    "mgga_k_csk": "mgga_k_csk1",
    "mgga_k_csk_loc": "mgga_k_csk_loc1",
    "mgga_k_lk": "mgga_k_l04",
    "mgga_k_pgslb": "mgga_k_pgsl025",
    "mgga_x_2d_prp10": "mgga_x_2d_prhg07_prp10",
    "mgga_x_gdme": "mgga_x_gdme_nv",
    "mgga_x_ktbm": "mgga_x_ktbm_0",
    "mgga_x_m06l": "mgga_x_m06_l",
    "mgga_x_m08": "mgga_x_ms0",
    "mgga_x_m11": "mgga_x_m11_l",
    "mgga_x_mn12": "mgga_x_mn12_l",
    "mgga_x_ms": "mgga_x_ms0",
    "mgga_x_msb": "mgga_x_msb86bl",
    "mgga_xc_b97mv": "mgga_xc_b97m_v",
    # Extra mappings discovered during AD runs
    "mgga_c_r2scan01": "mgga_c_r2scan",
    "mgga_c_revm06_l": "mgga_c_revm06",
    # Map Minnesota correlation variants to available leaves when Maple files are missing
    "mgga_c_revm06": "mgga_c_m06l",
    "mgga_c_m06_sx": "mgga_c_m06l",
    # Minnesota correlation aliases: map non-L variants to available L leaves
    "mgga_c_m06": "mgga_c_m06l",
    "mgga_c_m06_2x": "mgga_c_m06l",
    "mgga_c_m06_hf": "mgga_c_m06l",
    "gga_k_pbe3": "gga_k_pbe4",
    # Common curated aliases
    "hyb_gga_xc_bhandhlyp": "hyb_gga_xc_b5050lyp",
    # Deorbitalized variants now have explicit Python modules (no aliasing)
}

LIBXC_ALIAS_REMAP.update({k: v for k, v in _ADDITIONAL_REMAPS.items() if v is not None})

LIBXC_UNAVAILABLE: set[str] = {
    k for k, v in _ADDITIONAL_REMAPS.items() if v is None
}

DOC_ALIAS_MAP: dict[str, str | None] = _ADDITIONAL_REMAPS.copy()

__all__ = ["LIBXC_ALIAS_REMAP", "LIBXC_UNAVAILABLE", "DOC_ALIAS_MAP"]
