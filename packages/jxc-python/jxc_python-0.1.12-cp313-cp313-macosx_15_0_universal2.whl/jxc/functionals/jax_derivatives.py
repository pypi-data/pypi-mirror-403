"""JAX-based automatic differentiation for computing XC functional derivatives.

This module replicates the logic used in libxc's maple2c code generation, but
uses JAX's automatic differentiation to compute VXC, FXC, KXC, and LXC from
exchange-correlation energy functionals.

Similar to how maple2c uses Maple's diff() function, we use JAX's grad() and
jacfwd() functions to compute functional derivatives.
"""

from __future__ import annotations

from typing import Dict, Tuple, Optional, Callable, Union
import functools

import jax
import jax.numpy as jnp
import numpy as np

# Type aliases for clarity
Density = Union[float, jnp.ndarray]  # ρ
DensityGradient = Union[float, jnp.ndarray]  # σ = |∇ρ|²
Laplacian = Union[float, jnp.ndarray]  # ∇²ρ
KineticEnergyDensity = Union[float, jnp.ndarray]  # τ


def _ensure_array(value):
    """Convert scalar or array-like to JAX array."""
    if value is None:
        return None
    return jnp.atleast_1d(jnp.asarray(value))


class LDAFunctional:
    """Base class for LDA functionals with automatic derivative computation."""

    def __init__(self, energy_per_particle_fn: Callable):
        """Initialize with an energy per particle function.

        Args:
            energy_per_particle_fn: Function f(rs, zeta) returning energy per particle
                where rs is Wigner-Seitz radius and zeta is spin polarization.
        """
        self.f = energy_per_particle_fn

    def _rs_from_density(self, rho: jnp.ndarray) -> jnp.ndarray:
        """Convert density to Wigner-Seitz radius."""
        # rs = (3/(4π))^(1/3) * rho^(-1/3)
        return jnp.where(
            rho > 1e-30,
            (3.0 / (4.0 * jnp.pi))**(1.0/3.0) * rho**(-1.0/3.0),
            1e10  # Large rs for vanishing density
        )

    def energy_density_unpolarized(self, rho: jnp.ndarray) -> jnp.ndarray:
        """Compute energy density εxc * ρ for unpolarized system."""
        rho = _ensure_array(rho)
        rs = self._rs_from_density(rho)
        zeta = jnp.zeros_like(rho)
        return rho * self.f(rs, zeta)

    def energy_density_polarized(self, rho_up: jnp.ndarray, rho_dn: jnp.ndarray) -> jnp.ndarray:
        """Compute energy density εxc * ρ for spin-polarized system."""
        rho_up = _ensure_array(rho_up)
        rho_dn = _ensure_array(rho_dn)
        rho_total = rho_up + rho_dn
        rs = self._rs_from_density(rho_total)
        zeta = jnp.where(
            rho_total > 1e-30,
            (rho_up - rho_dn) / rho_total,
            0.0
        )
        return rho_total * self.f(rs, zeta)

    def compute_derivatives_unpolarized(self, rho: jnp.ndarray, max_order: int = 1) -> Dict[str, jnp.ndarray]:
        """Compute all derivatives up to max_order for unpolarized case.

        This mimics libxc's approach where:
        - VXC = ∂(ρ*εxc)/∂ρ = vrho
        - FXC = ∂²(ρ*εxc)/∂ρ² = v2rho2
        - KXC = ∂³(ρ*εxc)/∂ρ³ = v3rho3
        - LXC = ∂⁴(ρ*εxc)/∂ρ⁴ = v4rho4

        Returns:
            Dictionary with keys 'vrho', 'v2rho2', 'v3rho3', 'v4rho4'
        """
        rho = _ensure_array(rho)
        results = {}

        # Energy density
        energy_fn = lambda r: self.energy_density_unpolarized(r)

        if max_order >= 0:
            # Energy per particle
            rs = self._rs_from_density(rho)
            zk = self.f(rs, jnp.zeros_like(rho))
            results['zk'] = zk

        if max_order >= 1:
            # First derivative: VXC
            # For scalar inputs, we need to handle the gradient properly
            def scalar_energy(r_scalar):
                return energy_fn(jnp.array([r_scalar]))[0]

            vrho_list = []
            for r in rho:
                vrho_val = jax.grad(scalar_energy)(float(r))
                vrho_list.append(vrho_val)
            results['vrho'] = jnp.array(vrho_list)

        if max_order >= 2:
            # Second derivative: FXC
            def scalar_energy(r_scalar):
                return energy_fn(jnp.array([r_scalar]))[0]

            v2rho2_list = []
            for r in rho:
                v2rho2_val = jax.grad(jax.grad(scalar_energy))(float(r))
                v2rho2_list.append(v2rho2_val)
            results['v2rho2'] = jnp.array(v2rho2_list)

        if max_order >= 3:
            # Third derivative: KXC
            def scalar_energy(r_scalar):
                return energy_fn(jnp.array([r_scalar]))[0]

            v3rho3_list = []
            for r in rho:
                v3rho3_val = jax.grad(jax.grad(jax.grad(scalar_energy)))(float(r))
                v3rho3_list.append(v3rho3_val)
            results['v3rho3'] = jnp.array(v3rho3_list)

        if max_order >= 4:
            # Fourth derivative: LXC
            def scalar_energy(r_scalar):
                return energy_fn(jnp.array([r_scalar]))[0]

            v4rho4_list = []
            for r in rho:
                v4rho4_val = jax.grad(jax.grad(jax.grad(jax.grad(scalar_energy))))(float(r))
                v4rho4_list.append(v4rho4_val)
            results['v4rho4'] = jnp.array(v4rho4_list)

        return results

    def compute_derivatives_polarized(self, rho_up: jnp.ndarray, rho_dn: jnp.ndarray,
                                     max_order: int = 1) -> Dict[str, jnp.ndarray]:
        """Compute all derivatives up to max_order for spin-polarized case.

        Returns:
            Dictionary with keys like 'vrho' (2 components), 'v2rho2' (3 components), etc.
        """
        rho_up = _ensure_array(rho_up)
        rho_dn = _ensure_array(rho_dn)
        results = {}

        # Energy density function of both spin densities
        energy_fn = lambda ru, rd: self.energy_density_polarized(ru, rd)

        if max_order >= 0:
            # Energy per particle
            rho_total = rho_up + rho_dn
            rs = self._rs_from_density(rho_total)
            zeta = jnp.where(rho_total > 1e-30, (rho_up - rho_dn) / rho_total, 0.0)
            zk = self.f(rs, zeta)
            results['zk'] = zk

        if max_order >= 1:
            # First derivatives: VXC
            # vrho[0] = ∂E/∂ρ↑, vrho[1] = ∂E/∂ρ↓
            def scalar_energy(ru, rd):
                return jnp.sum(energy_fn(ru, rd))

            grad_fn = jax.grad(scalar_energy, argnums=(0, 1))
            vrho = jax.vmap(lambda ru, rd: jnp.array(grad_fn(ru, rd)))(rho_up, rho_dn)
            results['vrho'] = vrho

        if max_order >= 2:
            # Second derivatives: FXC
            # v2rho2[0,0] = ∂²E/∂ρ↑², v2rho2[0,1] = ∂²E/∂ρ↑∂ρ↓, v2rho2[1,1] = ∂²E/∂ρ↓²
            def scalar_energy(ru, rd):
                return jnp.sum(energy_fn(ru, rd))

            hess_fn = jax.hessian(scalar_energy, argnums=(0, 1))

            def compute_hessian_components(ru, rd):
                ((d2_uu, d2_ud), (d2_du, d2_dd)) = hess_fn(ru, rd)
                # Return in libxc order: (u_u, u_d, d_d)
                return jnp.array([d2_uu, d2_ud, d2_dd])

            v2rho2 = jax.vmap(compute_hessian_components)(rho_up, rho_dn)
            results['v2rho2'] = v2rho2

        # Higher order derivatives would follow similar pattern
        # but require more complex indexing for the tensor components

        return results


class GGAFunctional:
    """Base class for GGA functionals with automatic derivative computation."""

    def __init__(self, energy_per_particle_fn: Callable):
        """Initialize with an energy per particle function.

        Args:
            energy_per_particle_fn: Function f(rs, zeta, s) where:
                - rs: Wigner-Seitz radius
                - zeta: spin polarization
                - s: reduced gradient (dimensionless)
        """
        self.f = energy_per_particle_fn

    def _rs_from_density(self, rho: jnp.ndarray) -> jnp.ndarray:
        """Convert density to Wigner-Seitz radius."""
        return jnp.where(
            rho > 1e-30,
            (3.0 / (4.0 * jnp.pi))**(1.0/3.0) * rho**(-1.0/3.0),
            1e10
        )

    def _reduced_gradient(self, rho: jnp.ndarray, sigma: jnp.ndarray) -> jnp.ndarray:
        """Compute dimensionless reduced gradient s."""
        # s = |∇ρ|/(2 * (3π²)^(1/3) * ρ^(4/3))
        # sigma = |∇ρ|², so |∇ρ| = sqrt(sigma)
        kF = (3.0 * jnp.pi**2)**(1.0/3.0) * rho**(1.0/3.0)
        s = jnp.where(
            rho > 1e-30,
            jnp.sqrt(sigma) / (2.0 * kF * rho),
            0.0
        )
        return s

    def energy_density_unpolarized(self, rho: jnp.ndarray, sigma: jnp.ndarray) -> jnp.ndarray:
        """Compute energy density εxc * ρ for unpolarized system."""
        rho = _ensure_array(rho)
        sigma = _ensure_array(sigma)
        rs = self._rs_from_density(rho)
        zeta = jnp.zeros_like(rho)
        s = self._reduced_gradient(rho, sigma)
        return rho * self.f(rs, zeta, s)

    def energy_density_polarized(self, rho_up: jnp.ndarray, rho_dn: jnp.ndarray,
                                sigma_uu: jnp.ndarray, sigma_ud: jnp.ndarray,
                                sigma_dd: jnp.ndarray) -> jnp.ndarray:
        """Compute energy density for spin-polarized system."""
        rho_up = _ensure_array(rho_up)
        rho_dn = _ensure_array(rho_dn)
        sigma_uu = _ensure_array(sigma_uu)
        sigma_ud = _ensure_array(sigma_ud)
        sigma_dd = _ensure_array(sigma_dd)

        rho_total = rho_up + rho_dn
        rs = self._rs_from_density(rho_total)
        zeta = jnp.where(rho_total > 1e-30, (rho_up - rho_dn) / rho_total, 0.0)

        # Total sigma for reduced gradient
        sigma_total = sigma_uu + 2*sigma_ud + sigma_dd
        s = self._reduced_gradient(rho_total, sigma_total)

        return rho_total * self.f(rs, zeta, s)

    def compute_derivatives_unpolarized(self, rho: jnp.ndarray, sigma: jnp.ndarray,
                                       max_order: int = 1) -> Dict[str, jnp.ndarray]:
        """Compute all derivatives up to max_order for unpolarized GGA.

        Returns:
            Dictionary with keys 'vrho', 'vsigma', 'v2rho2', 'v2rhosigma', 'v2sigma2', etc.
        """
        rho = _ensure_array(rho)
        sigma = _ensure_array(sigma)
        results = {}

        # Energy density as function of inputs
        energy_fn = lambda r, s: self.energy_density_unpolarized(r, s)

        if max_order >= 0:
            # Energy per particle
            rs = self._rs_from_density(rho)
            s = self._reduced_gradient(rho, sigma)
            zk = self.f(rs, jnp.zeros_like(rho), s)
            results['zk'] = zk

        if max_order >= 1:
            # First derivatives
            def scalar_energy(r, s):
                return jnp.sum(energy_fn(r, s))

            # Compute gradients
            grad_fn = jax.grad(scalar_energy, argnums=(0, 1))
            vrho, vsigma = jax.vmap(lambda r, s: grad_fn(r, s))(rho, sigma)
            results['vrho'] = vrho
            results['vsigma'] = vsigma

        if max_order >= 2:
            # Second derivatives
            def scalar_energy(r, s):
                return jnp.sum(energy_fn(r, s))

            # Hessian
            hess_fn = jax.hessian(scalar_energy, argnums=(0, 1))

            def compute_hessian(r, s):
                ((d2_rr, d2_rs), (d2_sr, d2_ss)) = hess_fn(r, s)
                return d2_rr, d2_rs, d2_ss

            v2rho2, v2rhosigma, v2sigma2 = jax.vmap(compute_hessian)(rho, sigma)
            results['v2rho2'] = v2rho2
            results['v2rhosigma'] = v2rhosigma
            results['v2sigma2'] = v2sigma2

        # Higher orders would follow similar pattern

        return results

    def compute_derivatives_polarized(self, rho_up: jnp.ndarray, rho_dn: jnp.ndarray,
                                     sigma_uu: jnp.ndarray, sigma_ud: jnp.ndarray,
                                     sigma_dd: jnp.ndarray, max_order: int = 1) -> Dict[str, jnp.ndarray]:
        """Compute derivatives for spin-polarized GGA.

        Returns:
            Dictionary with properly indexed derivative arrays.
        """
        # This would follow similar pattern to LDA but with more complex indexing
        # due to the additional sigma components
        # For brevity, implementing just the structure

        results = {}

        # Placeholder - full implementation would compute actual derivatives
        # using JAX automatic differentiation similar to unpolarized case

        if max_order >= 1:
            # vrho: (up, dn) components
            # vsigma: (uu, ud, dd) components
            pass

        if max_order >= 2:
            # v2rho2: (u_u, u_d, d_d) components
            # v2rhosigma: (u_uu, u_ud, u_dd, d_uu, d_ud, d_dd) components
            # v2sigma2: (uu_uu, uu_ud, uu_dd, ud_ud, ud_dd, dd_dd) components
            pass

        return results


# Example concrete functionals

def lda_x_slater_exchange(rs: jnp.ndarray, zeta: jnp.ndarray) -> jnp.ndarray:
    """Slater exchange energy per particle.

    This is the standard LDA exchange functional.
    """
    # Constants
    C = -0.73855876638  # -(3/4) * (3/π)^(1/3)

    # For unpolarized case (zeta=0), the exchange energy is simply
    ex = C / rs

    # For polarized case, apply spin-polarization scaling
    # f(zeta) = [(1+zeta)^(4/3) + (1-zeta)^(4/3)] / 2
    # But for unpolarized (zeta=0), f(0) = 1
    f_zeta = jnp.where(
        jnp.abs(zeta) > 1e-10,
        ((1 + zeta)**(4.0/3.0) + (1 - zeta)**(4.0/3.0)) / 2.0,
        1.0
    )

    return ex * f_zeta


def gga_x_pbe_exchange(rs: jnp.ndarray, zeta: jnp.ndarray, s: jnp.ndarray) -> jnp.ndarray:
    """PBE exchange enhancement factor.

    This would multiply the LDA exchange to get PBE exchange.
    """
    # PBE parameters
    kappa = 0.804
    mu = 0.2195149727645

    # Enhancement factor
    Fx = 1 + kappa - kappa / (1 + mu * s**2 / kappa)

    # Apply to LDA exchange
    ex_lda = lda_x_slater_exchange(rs, zeta)
    ex_pbe = ex_lda * Fx

    return ex_pbe


# Test utilities

def compare_with_libxc(functional_name: str, functional_jax: Union[LDAFunctional, GGAFunctional],
                       test_points: int = 10, max_order: int = 1) -> Dict[str, float]:
    """Compare JAX derivatives with libxc reference.

    Returns:
        Dictionary with maximum absolute errors for each derivative component.
    """
    import pylibxc

    errors = {}

    # Generate test points
    rho_test = np.logspace(-8, 2, test_points)

    if isinstance(functional_jax, LDAFunctional):
        # LDA comparison
        func_libxc = pylibxc.LibXCFunctional(functional_name, "unpolarized")

        # Compute with JAX
        jax_results = functional_jax.compute_derivatives_unpolarized(rho_test, max_order)

        # Compute with libxc
        libxc_input = {"rho": rho_test.reshape(-1, 1)}
        libxc_output = func_libxc.compute(libxc_input, do_exc=(max_order >= 0),
                                         do_vxc=(max_order >= 1), do_fxc=(max_order >= 2),
                                         do_kxc=(max_order >= 3), do_lxc=(max_order >= 4))

        # Compare each component
        for key in jax_results:
            if key in libxc_output:
                jax_val = np.array(jax_results[key]).flatten()
                libxc_val = np.array(libxc_output[key]).flatten()
                errors[key] = np.max(np.abs(jax_val - libxc_val))

    elif isinstance(functional_jax, GGAFunctional):
        # GGA comparison
        func_libxc = pylibxc.LibXCFunctional(functional_name, "unpolarized")

        # Generate sigma test points
        sigma_test = 0.1 * rho_test**(8.0/3.0)  # Reasonable gradient values

        # Compute with JAX
        jax_results = functional_jax.compute_derivatives_unpolarized(rho_test, sigma_test, max_order)

        # Compute with libxc
        libxc_input = {
            "rho": rho_test.reshape(-1, 1),
            "sigma": sigma_test.reshape(-1, 1)
        }
        libxc_output = func_libxc.compute(libxc_input, do_exc=(max_order >= 0),
                                         do_vxc=(max_order >= 1), do_fxc=(max_order >= 2))

        # Compare each component
        for key in jax_results:
            if key in libxc_output:
                jax_val = np.array(jax_results[key]).flatten()
                libxc_val = np.array(libxc_output[key]).flatten()
                errors[key] = np.max(np.abs(jax_val - libxc_val))

    return errors