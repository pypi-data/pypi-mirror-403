"""Precomputed enforce_smooth_lr overrides eliminating SymPy usage.

Each entry maps a Maple helper name (the first argument to
``enforce_smooth_lr``) to the predicate/branches that should be used when
Maple itself cannot materialise the large-a expansion.  Expressions are
stored as strings and parsed into AST nodes during code generation.
"""

from __future__ import annotations

SERIES_OVERRIDES: dict[str, dict[str, str]] = {
    "attenuation_erf0": {
        "predicate": "_aval >= 1.35",
        "true": "-1 / 2021444812800 * (1.0 / jnp.maximum(_aval, 1.35)) ** 16 + 1 / 44590694400 * (1.0 / jnp.maximum(_aval, 1.35)) ** 14 - 1 / 1073479680 * (1.0 / jnp.maximum(_aval, 1.35)) ** 12 + 1 / 28385280 * (1.0 / jnp.maximum(_aval, 1.35)) ** 10 - 1 / 829440 * (1.0 / jnp.maximum(_aval, 1.35)) ** 8 + 1 / 26880 * (1.0 / jnp.maximum(_aval, 1.35)) ** 6 - 1 / 960 * (1.0 / jnp.maximum(_aval, 1.35)) ** 4 + 1 / 36 * (1.0 / jnp.maximum(_aval, 1.35)) ** 2",
        "false": "attenuation_erf0(jnp.minimum(_aval, 1.35))",
    },
    "attenuation_erf_f20": {
        "predicate": "_aval >= 0.27",
        "true": "-1 / 3511556992918352140755776405766144000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 46 + 1 / 33929038000650146833571361325056000000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 44 - 1 / 341095116070365837848137621831680000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 42 + 1 / 3573852336994573837102806466560000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 40 - 1 / 39097165634742908368485089280000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 38 + 1 / 447473103488807905221672960000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 36 - 1 / 5369745537516410492682240000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 34 + 1 / 67726520292999771979776000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 32 - 1 / 900231674141645733888000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 30 + 1 / 12648942844388573184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 28 - 1 / 188514051721003008000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 26 + 1 / 2991700272218112000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 24 - 1 / 50785035485184000 * (1.0 / jnp.maximum(_aval, 0.27)) ** 22 + 1 / 927028425523200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 20 - 1 / 18311911833600 * (1.0 / jnp.maximum(_aval, 0.27)) ** 18 + 1 / 394474291200 * (1.0 / jnp.maximum(_aval, 0.27)) ** 16 - 1 / 9358540800 * (1.0 / jnp.maximum(_aval, 0.27)) ** 14 + 1 / 247726080 * (1.0 / jnp.maximum(_aval, 0.27)) ** 12 - 1 / 7454720 * (1.0 / jnp.maximum(_aval, 0.27)) ** 10 + 3 / 788480 * (1.0 / jnp.maximum(_aval, 0.27)) ** 8 - 1 / 11520 * (1.0 / jnp.maximum(_aval, 0.27)) ** 6 + 3 / 2240 * (1.0 / jnp.maximum(_aval, 0.27)) ** 4",
        "false": "attenuation_erf_f20(jnp.minimum(_aval, 0.27))",
    },
    "attenuation_erf_f30": {
        "predicate": "_aval >= 0.32",
        "true": "-1 / 2104209454461863328391867505049600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 38 + 1 / 22046293272414372635684634624000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 36 - 1 / 241191070393445437962977280000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 34 + 1 / 2760851680179343645999104000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 32 - 1 / 33139778504339333578752000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 30 + 1 / 418174050435486229463040 * (1.0 / jnp.maximum(_aval, 0.32)) ** 28 - 1 / 5562511054710453043200 * (1.0 / jnp.maximum(_aval, 0.32)) ** 26 + 1 / 78244468658012160000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 24 - 1 / 1168055816159232000 * (1.0 / jnp.maximum(_aval, 0.32)) ** 22 + 1 / 18582706166169600 * (1.0 / jnp.maximum(_aval, 0.32)) ** 20 - 1 / 316612955602944 * (1.0 / jnp.maximum(_aval, 0.32)) ** 18 + 1 / 5811921223680 * (1.0 / jnp.maximum(_aval, 0.32)) ** 16 - 1 / 115811942400 * (1.0 / jnp.maximum(_aval, 0.32)) ** 14 + 1 / 2530344960 * (1.0 / jnp.maximum(_aval, 0.32)) ** 12 - 1 / 61501440 * (1.0 / jnp.maximum(_aval, 0.32)) ** 10 + 5 / 8515584 * (1.0 / jnp.maximum(_aval, 0.32)) ** 8 - 1 / 56448 * (1.0 / jnp.maximum(_aval, 0.32)) ** 6 + 3 / 7840 * (1.0 / jnp.maximum(_aval, 0.32)) ** 4",
        "false": "attenuation_erf_f30(jnp.minimum(_aval, 0.32))",
    },
    "attenuation_gau0": {
        "predicate": "_aval >= 2.07",
        "true": "-1 / 3185049600 * (1.0 / jnp.maximum(_aval, 2.07)) ** 14 + 1 / 89456640 * (1.0 / jnp.maximum(_aval, 2.07)) ** 12 - 1 / 2838528 * (1.0 / jnp.maximum(_aval, 2.07)) ** 10 + 1 / 103680 * (1.0 / jnp.maximum(_aval, 2.07)) ** 8 - 1 / 4480 * (1.0 / jnp.maximum(_aval, 2.07)) ** 6 + 1 / 240 * (1.0 / jnp.maximum(_aval, 2.07)) ** 4 - 1 / 18 * (1.0 / jnp.maximum(_aval, 2.07)) ** 2",
        "false": "attenuation_gau0(jnp.minimum(_aval, 2.07))",
    },
    "attenuation_yukawa0": {
        "predicate": "_aval >= 1.92",
        "true": "-1 / 7030 * (1.0 / jnp.maximum(_aval, 1.92)) ** 36 + 1 / 5985 * (1.0 / jnp.maximum(_aval, 1.92)) ** 34 - 1 / 5049 * (1.0 / jnp.maximum(_aval, 1.92)) ** 32 + 1 / 4216 * (1.0 / jnp.maximum(_aval, 1.92)) ** 30 - 1 / 3480 * (1.0 / jnp.maximum(_aval, 1.92)) ** 28 + 1 / 2835 * (1.0 / jnp.maximum(_aval, 1.92)) ** 26 - 1 / 2275 * (1.0 / jnp.maximum(_aval, 1.92)) ** 24 + 1 / 1794 * (1.0 / jnp.maximum(_aval, 1.92)) ** 22 - 1 / 1386 * (1.0 / jnp.maximum(_aval, 1.92)) ** 20 + 1 / 1045 * (1.0 / jnp.maximum(_aval, 1.92)) ** 18 - 1 / 765 * (1.0 / jnp.maximum(_aval, 1.92)) ** 16 + 1 / 540 * (1.0 / jnp.maximum(_aval, 1.92)) ** 14 - 1 / 364 * (1.0 / jnp.maximum(_aval, 1.92)) ** 12 + 1 / 231 * (1.0 / jnp.maximum(_aval, 1.92)) ** 10 - 1 / 135 * (1.0 / jnp.maximum(_aval, 1.92)) ** 8 + 1 / 70 * (1.0 / jnp.maximum(_aval, 1.92)) ** 6 - 1 / 30 * (1.0 / jnp.maximum(_aval, 1.92)) ** 4 + 1 / 9 * (1.0 / jnp.maximum(_aval, 1.92)) ** 2",
        "false": "attenuation_yukawa0(jnp.minimum(_aval, 1.92))",
    },
    "mbeef_xj0": {
        "predicate": "_aval >= 10000.0",
        "true": "3 * (1.0 / jnp.maximum(_aval, 10000.0)) ** 4 - 1 * (1.0 / jnp.maximum(_aval, 10000.0)) ** 3 - 3 * (1.0 / jnp.maximum(_aval, 10000.0)) ** 2 + 1",
        "false": "mbeef_xj0(jnp.minimum(_aval, 10000.0))",
    },
}
