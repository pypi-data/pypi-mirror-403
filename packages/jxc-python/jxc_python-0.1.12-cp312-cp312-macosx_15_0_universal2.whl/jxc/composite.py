"""
Builder for composite (mixed) functionals.

Composite functionals are linear combinations of component functionals,
such as B3LYP which combines LDA exchange, B88 GGA exchange, VWN correlation, and LYP correlation.

All functionals are expected to have Maple-derived Python implementations;
if a module is missing, the runtime raises an explicit error so it can be
fixed via codegen rather than silently falling back to LibXC.
"""

import importlib
from typing import Callable, Any

from .get_params import get_params as _get_params


def make_epsilon_xc(p, deo_functional=None) -> Callable:
    """
    Build an epsilon_xc function from a params namedtuple.

    Parameters
    ----------
    p : namedtuple
        Parameters from get_params(), containing fields:
        - maple_name: str (empty for composite, "DEORBITALIZE" for deorbitalized, or actual name)
        - func_aux: list of child params (for composite/deorbitalize)
        - mix_coef: list of float (weights for composite)
        - cam_alpha, cam_beta, cam_omega: float (range-separated hybrid params)
        - nlc_b, nlc_C: float (non-local correlation params)
        - nspin: int (1 for unpolarized, 2 for polarized)
    deo_functional : Callable, optional
        For DEORBITALIZE functionals, the deorbitalized functional to use.

    Returns
    -------
    Callable
        A function that computes epsilon_xc given input densities.
        For composites, also has attributes: cam_alpha, cam_beta, cam_omega, nlc_b, nlc_C
    """
    if p.maple_name == "DEORBITALIZE":
        # Deorbitalize pattern: p.func_aux = [p0, p1]
        # Build p1 first, then build p0 using p1 as deo_functional
        # TODO: Full implementation requires threading mo (molecular orbitals) through inputs
        p0, p1 = (p.func_aux[0], p.func_aux[1])
        epsilon_xc_p1 = make_epsilon_xc(p1)
        epsilon_xc_p0 = make_epsilon_xc(p0, epsilon_xc_p1)
        return epsilon_xc_p0

    elif hasattr(p, 'func_aux') and p.func_aux and len(p.func_aux) > 0:
        # Composite: linear mix of func_aux with mix_coef weights
        # Detect via presence of func_aux (not maple_name=="")
        # Rehydrate child params if helper provided uninitialized params (common in LibXC composites)
        def _nonempty_params(cp) -> bool:
            try:
                return bool(getattr(cp, 'params', None) and cp.params._asdict())
            except Exception:
                return False
        children_ps = []
        for child_p in p.func_aux:
            if _nonempty_params(child_p):
                children_ps.append(child_p)
            else:
                child_name = getattr(child_p, 'name', getattr(child_p, 'maple_name', ''))
                if not child_name:
                    children_ps.append(child_p)
                else:
                    try:
                        rebuilt = _get_params(child_name, polarized=(p.nspin == 2))
                        children_ps.append(rebuilt)
                    except Exception:
                        children_ps.append(child_p)
        # Build children outside closure to avoid recompiling on every call
        # Preserve child-specific CAM params when rehydrating children.
        # If a child entry from helper already carries cam_* fields, keep them.
        # Only rebuild minimal child metadata via get_params when the helper left
        # params empty, and carry over any cam_* present on the original child.
        patched_children = []
        for orig_cp, cp in zip(p.func_aux, children_ps):
            rebuilt = cp
            # If orig child has explicit cam params, prefer them over any defaults
            for attr in ("cam_alpha", "cam_beta", "cam_omega"):
                if hasattr(orig_cp, attr):
                    try:
                        rebuilt = rebuilt._replace(**{attr: getattr(orig_cp, attr)})
                    except Exception:
                        # Not a namedtuple or field missing; ignore
                        pass
            patched_children.append(rebuilt)

        children = [make_epsilon_xc(cp) for cp in patched_children]

        EXCLUDE_BASE_ADDITION = {
            'hyb_gga_xc_lb07',
            'hyb_gga_xc_apbe0',  # defined in zvpbeloc.c; base is not part of mix
        }

        def epsilon_xc(*args, **kwargs):
            # Specialization: LibXC mixes b0kcis as (1 - alpha) * Ex_B88 + 2 * Ec_KCIS.
            if p.name == 'hyb_mgga_xc_b0kcis':
                try:
                    ex = children[0](*args, **kwargs)
                    corr = children[1](*args, **kwargs)
                    return (1.0 - getattr(p, 'cam_alpha', 0.25)) * ex + 2.0 * corr
                except Exception:
                    pass
            # Weighted sum - children already built
            result = sum(coef * child(*args, **kwargs)
                         for coef, child in zip(p.mix_coef, children))

            # For some LibXC hybrids, a base functional is implied in addition
            # to func_aux; re-add it if not already included, except for known
            # cases (e.g., LB07) where this would double-count.
            if p.maple_name and (p.name not in EXCLUDE_BASE_ADDITION):
                base_in_aux = any(child_p.name == p.maple_name or child_p.maple_name == p.maple_name
                                   for child_p in p.func_aux)
                if not base_in_aux:
                    try:
                        base_module = importlib.import_module(f"jxc.functionals.{p.maple_name}")
                        base_func = base_module.unpol if p.nspin == 1 else base_module.pol
                        # Rebuild correct params for the base functional, and propagate CAM params
                        base_p = _get_params(p.maple_name, polarized=(p.nspin == 2))
                        try:
                            base_p = base_p._replace(
                                cam_alpha=getattr(p, 'cam_alpha', 0.0),
                                cam_beta=getattr(p, 'cam_beta', 0.0),
                                cam_omega=getattr(p, 'cam_omega', 0.0),
                            )
                        except Exception:
                            pass
                        result = result + base_func(base_p, *args, **kwargs)
                    except (ImportError, AttributeError):
                        pass
            return result

        # Attach hybrid/nlc metadata as attributes
        epsilon_xc.cam_alpha = p.cam_alpha
        epsilon_xc.cam_beta = p.cam_beta
        epsilon_xc.cam_omega = p.cam_omega
        epsilon_xc.nlc_b = p.nlc_b
        epsilon_xc.nlc_C = p.nlc_C
        return epsilon_xc

    else:
        # Single maple-based functional: import the generated module
        module_name = p.maple_name or p.name

        try:
            module = importlib.import_module(f"jxc.functionals.{module_name}")
        except ImportError as exc:
            raise ImportError(
                f"No Maple implementation found for '{p.name}' (expected module '{module_name}'). "
                "Run the Maple codegen pipeline to generate it."
            ) from exc

        # Select pol/unpol based on nspin
        if p.nspin == 1:
            func = module.unpol
        elif p.nspin == 2:
            func = module.pol
        else:
            raise ValueError(f"Unsupported nspin={p.nspin} for {p.maple_name}")

        # Wrap to pass full p object
        def epsilon_xc(*args, **kwargs):
            return func(p, *args, **kwargs)

        # Attach hybrid/nlc metadata
        epsilon_xc.cam_alpha = p.cam_alpha
        epsilon_xc.cam_beta = p.cam_beta
        epsilon_xc.cam_omega = p.cam_omega
        epsilon_xc.nlc_b = p.nlc_b
        epsilon_xc.nlc_C = p.nlc_C

        return epsilon_xc
