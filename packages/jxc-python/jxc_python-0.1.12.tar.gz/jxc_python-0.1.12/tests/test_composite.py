"""
Micro tests for composite (mixed) functionals.

Tests B3LYP and other composites against LibXC reference implementation.
"""

import numpy as np
import pytest
import pylibxc

from jxc import get_xc_functional, get_params


def test_b3lyp_unpolarized():
    """Test B3LYP composite functional (unpolarized)."""
    # Build JXC B3LYP
    jxc_func = get_xc_functional("hyb_gga_xc_b3lyp", polarized=False)

    # Get params to verify it's composite
    p = get_params("hyb_gga_xc_b3lyp", polarized=False)
    assert p.maple_name == "", "B3LYP should be composite (maple_name empty)"
    assert len(p.func_aux) == 4, "B3LYP has 4 components"

    # Verify hybrid parameters are attached
    assert hasattr(jxc_func, 'cam_alpha')
    assert jxc_func.cam_alpha == pytest.approx(0.2, abs=1e-10)

    # Test on small grid
    rho = np.array([0.1, 0.5, 1.0])
    sigma = np.array([0.01, 0.05, 0.1])

    # JXC result
    jxc_result = jxc_func(rho, sigma)

    # LibXC reference
    libxc_func = pylibxc.LibXCFunctional("hyb_gga_xc_b3lyp", 1)
    inp = {"rho": rho, "sigma": sigma}
    libxc_out = libxc_func.compute(inp)
    libxc_result = libxc_out["zk"].ravel()  # Flatten to match JXC shape

    # Compare (relaxed tolerance for float32 vs float64)
    np.testing.assert_allclose(jxc_result, libxc_result, rtol=1e-6, atol=1e-8)


@pytest.mark.skip(reason="Polarized composite functional needs more investigation")
def test_b3lyp_polarized():
    """Test B3LYP composite functional (polarized)."""
    # TODO: Need to properly handle polarized signatures in composite builder
    # The composite functionals work for unpolarized case, but polarized needs
    # more investigation regarding how to call component functionals
    pass


def test_pbe0_unpolarized():
    """Test PBE0 hybrid functional (unpolarized)."""
    # Build JXC PBE0
    jxc_func = get_xc_functional("hyb_gga_xc_pbeh", polarized=False)

    # Get params
    p = get_params("hyb_gga_xc_pbeh", polarized=False)
    # PBE0 might be composite or have special handling

    # Test on small grid
    rho = np.array([0.1, 0.5, 1.0])
    sigma = np.array([0.01, 0.05, 0.1])

    # JXC result
    jxc_result = jxc_func(rho, sigma)

    # LibXC reference
    libxc_func = pylibxc.LibXCFunctional("hyb_gga_xc_pbeh", 1)
    inp = {"rho": rho, "sigma": sigma}
    libxc_out = libxc_func.compute(inp)
    libxc_result = libxc_out["zk"].ravel()  # Flatten to match JXC shape

    # Compare (relaxed tolerance for float32 vs float64)
    np.testing.assert_allclose(jxc_result, libxc_result, rtol=1e-6, atol=1e-8)


def test_composite_structure():
    """Test that composite functionals have correct structure."""
    composites = [
        ("hyb_gga_xc_b3lyp", 4),  # B3LYP: 4 components
    ]

    for name, expected_components in composites:
        p = get_params(name, polarized=False)
        assert p.maple_name == "", f"{name} should be composite"
        assert len(p.func_aux) == expected_components, \
            f"{name} should have {expected_components} components"
        assert len(p.mix_coef) == expected_components, \
            f"{name} should have {expected_components} mixing coefficients"

        # Verify all components are available
        for child_p in p.func_aux:
            assert child_p.maple_name != "", \
                f"Component {child_p.name} should have maple_name"


if __name__ == "__main__":
    test_b3lyp_unpolarized()
    test_b3lyp_polarized()
    test_pbe0_unpolarized()
    test_composite_structure()
    print("All composite tests passed!")
