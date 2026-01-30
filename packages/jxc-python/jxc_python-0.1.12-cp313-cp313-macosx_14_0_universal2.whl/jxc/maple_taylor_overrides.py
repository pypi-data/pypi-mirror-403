"""Precomputed Taylor expansions for Maple convert(taylor(...), polynom)."""

from __future__ import annotations

TAYLOR_OVERRIDES: dict[str, dict[str, str]] = {
    "vt84f_f0_orig": {
        "0": (
            "1 + (-params_a_mu + params_a_alpha + 5/3)*st^2 + (params_a_alpha*params_a_mu + params_a_mu^2 - params_a_alpha)*st^4 + (-1/2*params_a_mu*params_a_alpha^2 - (params_a_alpha*params_a_mu + params_a_mu^2)*params_a_mu - 1/2*params_a_alpha^2)*st^6 + (1/6*params_a_mu*params_a_alpha^3 - (-1/2*params_a_mu*params_a_alpha^2 - params_a_alpha*params_a_mu^2 - params_a_mu^3)*params_a_mu + 1/2*params_a_alpha^2)*st^8"
        ),
    },
    "ft98_q2_orig": {
        "0": "1 - qt + 1/2*qt^2 - 1/8*qt^4 + 1/16*qt^6 - 5/128*qt^8",
        "-infinity": "-2*qt - 1/2/qt + 1/8/qt^3 - 1/16/qt^5",
    },
    "lak_fx0": {
        "0": "0.9999999998 - 0.3359715472*b - 0.6452139360*b^2 - 0.5894205272*b^3 - 0.1336260624*b^4 + 0.4596061922*b^5 + 0.8255440178*b^6 + 0.6915383116*b^7 - 0.1350990235e-2*b^8",
    },
    "mbrxc_v0": {
        "0": "-1/12*32^(1/3)*Pi^(1/3)*3^(2/3)/(1/Pi)^(1/3)*4^(1/3) - 1/108*32^(1/3)*Pi^(1/3)*3^(2/3)/(1/Pi)^(1/3)*4^(1/3)*y^2 + 1/108*32^(1/3)*Pi^(1/3)*3^(2/3)/(1/Pi)^(1/3)*4^(1/3)*y^3 - 13/1620*32^(1/3)*Pi^(1/3)*3^(2/3)/(1/Pi)^(1/3)*4^(1/3)*y^4 + 67/9720*32^(1/3)*Pi^(1/3)*3^(2/3)/(1/Pi)^(1/3)*4^(1/3)*y^5 - 52/8505*32^(1/3)*Pi^(1/3)*3^(2/3)/(1/Pi)^(1/3)*4^(1/3)*y^6 + 1811/326592*32^(1/3)*Pi^(1/3)*3^(2/3)/(1/Pi)^(1/3)*4^(1/3)*y^7",
    },
}
