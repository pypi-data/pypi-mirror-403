# JXC

Translation of LibXC into JAX and Julia.

## Quickstart

### Python Usage

**Preferred API: `get_xc_functional()` (supports composites)**

`jxc.get_xc_functional()` returns a callable that handles both single-component
and composite functionals without having to import generated Maple modules:

``` python
import jxc
import jax.numpy as jnp

# Works with single-component functionals
lda_func = jxc.get_xc_functional('lda_x', polarized=False)
rho = jnp.array([0.1, 0.2, 0.3])
print(lda_func(rho))  # Returns epsilon_xc values

# Works with composite functionals (e.g., B3LYP)
b3lyp = jxc.get_xc_functional('hyb_gga_xc_b3lyp', polarized=False)
sigma = jnp.array([0.01, 0.05, 0.1])  # |grad rho|^2
print(b3lyp(rho, s=sigma))  # Composite of 4 functionals

# Access hybrid parameters
print(b3lyp.cam_alpha)  # 0.2 for B3LYP (20% HF exchange)
```

This API automatically handles:
- **Single-component functionals**: Direct calls to generated Maple translations (272 functionals)
- **Composite functionals**: Weighted combinations like B3LYP (407 additional functionals)
- **Hybrid metadata**: Exposes `cam_alpha`, `cam_beta`, `cam_omega` for range-separated hybrids
- **NLC parameters**: Exposes `nlc_b`, `nlc_C` for non-local correlation

#### High-Level Derivative API (Python)

`get_xc_functional` also returns fully assembled derivative callables:

```python
import jxc
import numpy as np

rho = np.linspace(1e-4, 0.5, 32)
sigma = 0.1 * rho**(4/3)

vxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="vxc")
print("vrho:", vxc(rho, sigma=sigma)["vrho"][:3])

fxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="fxc")
print("v2rho2:", fxc(rho, sigma=sigma)["v2rho2"][:3])

# Higher orders use the same API:
kxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="kxc")
lxc = jxc.get_xc_functional("gga_x_pbe", polarized=False, order="lxc")
print("v3rho3 shape:", kxc(rho, sigma=sigma)["v3rho3"].shape)
print("v4rho4 shape:", lxc(rho, sigma=sigma)["v4rho4"].shape)
```

All derivative orders (`vxc`, `fxc`, `kxc`, `lxc`) can also accept a
precomputed parameter object as the first positional argument
(`f(params, rho, ...)`), but this is optional; if omitted, `get_xc_functional`
internally calls `get_params` for you. Julia’s API remains EXC-only for now.

#### Listing available functionals

To discover which LibXC functionals JXC can use, call:

```python
import jxc

all_names = jxc.list_functionals()
print(len(all_names), "functionals available")
print([n for n in all_names if "blyp" in n.lower()])
```

This uses LibXC’s registry via `pylibxc.util.xc_available_functional_names()`
when available and otherwise falls back to the set of generated Maple modules
in `jxc.functionals`.

#### Example: constructing BLYP from components

LibXC does not expose a single `gga_xc_blyp` name; “BLYP” is conventionally
`B88` exchange + `LYP` correlation. You can build it explicitly:

```python
import jax.numpy as jnp
import jxc

rho = jnp.linspace(1e-4, 0.5, 32)
s = 0.1 * rho ** (4 / 3)  # |∇ρ|^2 for GGA

ex_b88 = jxc.get_xc_functional("gga_x_b88", polarized=False)  # exchange only
ec_lyp = jxc.get_xc_functional("gga_c_lyp", polarized=False)  # correlation only

def blyp(rho, s=None):
    """Pure BLYP = B88 exchange + LYP correlation."""
    return ex_b88(rho, s=s) + ec_lyp(rho, s=s)

eps_xc = blyp(rho, s=s)
print("BLYP ε_xc:", eps_xc[:3])
```

This BLYP construction is different from “B3LYP without HF”: B3LYP uses
additional LSDA/VWN mixing and fixed coefficients on B88/LYP, whereas the
example above is pure B88 + pure LYP.

**Important Note on Hybrid Functionals:**
JXC returns the DFT component (epsilon_xc) only. For hybrid functionals with exact (Hartree-Fock) exchange:
- Use `cam_alpha` to determine the HF exchange fraction (e.g., 0.2 for B3LYP = 20% HF exchange)
- Your upstream code must compute the HF exchange term separately
- Total energy: E_xc = (1 - cam_alpha) * E_DFT + cam_alpha * E_HF

### Julia Usage (Package: JXC)

We provide a native Julia module named `JXC` under `JXC.jl`.

Start a Julia REPL in the module folder (set `JULIA_PKG_SERVER=""` if your network blocks the regional mirrors):
```bash
pushd JXC.jl
export JULIA_PKG_SERVER=""   # optional but avoids geo-routed mirrors such as in.pkg.julialang.org
julia --project
```

Then in Julia (option A: use as a package):
```julia
using Pkg
Pkg.instantiate()
using JXC

# Python-style EXC API parity
lda = JXC.get_xc_functional("lda_x"; polarized=false)
rho = fill(0.3, 4)
p = JXC.get_params("lda_x", JXC.XC_UNPOLARIZED)
println("LDA ε_xc: ", lda(p, rho))

# Composite example (B3LYP)
b3lyp = JXC.get_xc_functional("hyb_gga_xc_b3lyp"; polarized=false)
sigma = fill(0.01, length(rho))
println("B3LYP ε_xc: ", b3lyp(rho; s=sigma))
println("B3LYP cam_alpha: ", b3lyp.cam_alpha)
```

Or (option B: without package registration): `include("src/JXC.jl"); using .JXC`
If you are activating a different project and want to make this checkout available globally,
run `Pkg.develop(path="/path/to/JXC.jl")` from that outer environment.

Notes:
- Python Maple outputs live under `jxc/functionals/` (tracked in git).
- Julia Maple outputs live under `JXC.jl/src/functionals/` (tracked in git).
- Julia callables expose the same hybrid/NLC metadata as Python (`cam_alpha`, `cam_beta`, `cam_omega`, `nlc_b`, `nlc_C`) so you can inspect HF fractions directly from `get_xc_functional`.
- To (re)generate locally, run `make convert-maple` and/or `make convert-maple-julia`, then `make pregenerate-commit` to commit the results.

## Testing & Parity

| Command | Scope | Notes |
| --- | --- | --- |
| `bazel test //tests:jax_parity_test_*` | Python energy parity | auto-generated targets covering the full LibXC catalogue |
| `bazel test //tests/derivatives/vxc:all_vxc_functionals` | Python VXC parity | compares `jxc.derivatives.ad_derivs` derivatives against LibXC |
| `bazel test //tests:julia_parity_test` | Julia energy smoke | mirrors the structure of `jax_parity_test.py` for a small representative set (`lda_x`, `lda_c_pw`, `gga_x_pbe`, `gga_c_pbe`) |
| `bazel test //tests:julia_vxc_parity_test` | Julia VXC smoke | ensures the PythonCall-backed Laplacian helpers are wired correctly |
| `make julia-test` | Convenience wrapper | runs the two Julia Bazel targets above |

The parity suites are the canonical source of truth—consult `tests/jax_parity_test.py`, `tests/derivatives/vxc/`, and `tests/julia_parity_test.jl` for the exact tolerances in use. Expand the Julia list as additional functionals stabilise.

## Prerequisites

### Required Software

1. **Maple 18** (optional) – Only needed if you regenerate functionals
   - If not available, pre-generated functionals in `JXC.jl/src/functionals` are used

2. **Python 3.12** - Required Python version (project uses `uv` for env management)

3. **Build tools**:
   - CMake (>= 3.5)
   - C/C++ compiler (gcc/clang)
   - wget
   - tar
   - patch

### System Dependencies
`Arch Linux`
```bash
sudo pacman -S cmake gcc wget tar patch
```

`Ubuntu/Debian`
```bash
sudo apt install cmake build-essential wget tar patch
```


## Local Build

All commands below assume you are inside `projects/jxc/`. The repository uses
[`uv`](https://docs.astral.sh/uv/) so you can stay in a regular shell—prefix
build steps with `uv run` instead of activating the virtualenv.

```bash
# create venv, build and install both pylibxc + jxc (default python version 3.13)
make install

# switch to python 3.12
PYVER=3.12 make install

# Launch an interactive shell
uv run ipython

# Discover other handy targets
make help
```

`make build-wheel` automatically runs `git submodule update --init --recursive`,
regenerates the helper glue, builds (or reuses) the LibXC core under
`.libxc-core/`, compiles the pybind11 helper against that installation, bundles
the Python sources, and drops a wheel into `dist/`. Use `make install` to
install the freshly built `pylibxc` and `jxc` wheels into the selected `uv`
environment. The first phase (`scripts/build_libxc_core.sh`) only
runs when `.libxc-core` is absent; subsequent builds for new Python versions
reuse the same C artifacts.

The Makefile always targets `.venv`; when you set `PYVER=3.12` (or similar)
the `venv` prerequisite will recreate `.venv` with that interpreter before the
rest of the build runs. `make build` remains an alias for the same pipeline.

### Julia (Native Package: JXC)

The Julia package now lives under `projects/jxc/JXC.jl`.

> **Heads-up:** `JXC.get_params` defers to the Python helper via
> [PythonCall.jl](https://github.com/JuliaPy/PythonCall.jl). Build the helper
> (`make build-wheel` / `make install`) so that `pylibxc7` and the `jxc.helper`
> extension are importable, or point Julia at your existing virtualenv with
> `JULIA_CONDAPKG_BACKEND=Null JULIA_PYTHONCALL_EXE=@venv julia --project`.
> If those prerequisites are missing, the Julia API will fall back to a minimal
> parameter stub and emit a warning.

> Use `make sync-julia-wheels` (and optionally `PYVER=3.12 make sync-julia-wheels`)
> to copy freshly built `pylibxc7`/`jxc` wheels, the matching helper, and a cached
> NumPy wheel into `JXC.jl/python_wheels`. Run `make package-julia` to produce a
> tarball under `artifacts/` that GitHub Actions can publish as the Julia bundle.

If you are preparing a distributable Julia package, run `make sync-julia-wheels`
after building so the latest `pylibxc7`/`jxc` wheels are copied into
`JXC.jl/python_wheels/`. The Julia runtime will install from that cache on first
use when the helper is absent.

```bash
# Start Julia REPL in project
pushd projects/jxc/JXC.jl && julia --project
```

```julia
using Pkg; Pkg.instantiate(); using JXC
p = JXC.get_params("lda_x", JXC.XC_UNPOLARIZED); println("LDA unpol:", JXC.lda_x.unpol(p, 0.3))
pp = JXC.get_params("gga_x_pbe", JXC.XC_UNPOLARIZED); println("PBE unpol:", JXC.gga_x_pbe.unpol(pp, 0.3))
```

## Performance Benchmarks

JXC provides significant performance improvements over pylibxc, especially for larger batch sizes. Below are benchmark results comparing JXC against pylibxc on both CPU and GPU backends.

### CPU Performance

![CPU Benchmark](docs/bench_cpu.png)

**CPU Speedup Distribution:**
- **Batch=1,000**: Median 7.6x faster, Mean 9.5x faster (range: 0.3x - 120x)
- **Batch=100,000**: Median 439x faster, Mean 616x faster (range: 3.1x - 9,120x)

### GPU Performance

![GPU Benchmark](docs/bench_gpu.png)

**GPU Speedup Distribution:**
- **Batch=1,000**: Median 2.7x faster, Mean 3.3x faster (range: 0.0x - 14.9x)
- **Batch=100,000**: Median 194x faster, Mean 243x faster (range: 0.0x - 1,413x)

The histograms show that JXC provides substantial speedups across most functionals, with performance gains increasing significantly for larger batch sizes. The CPU backend shows particularly impressive speedups, with many functionals achieving >100x performance improvements at batch size 100,000.

### Derivative Performance (VXC)

![VXC Derivative Benchmark](docs/bench_deriv_vxc.png)

**VXC Derivative Speedup Highlights:**
- **Maple-generated code**: Up to 130x faster than pylibxc for functionals like `mgga_x_r2scan` and `hyb_gga_xc_b3lyp`
- **JAX AD**: Comparable performance to Maple code, with most functionals showing 20-100x speedup
- Median speedup across all functionals: ~25x for both Maple and AD approaches

The chart compares first derivative (VXC) computation performance for a batch size of 100 points. Blue bars show speedup from Maple-generated analytical derivatives, while orange bars show JAX automatic differentiation performance. Both approaches significantly outperform pylibxc's implementation.

**Benchmark Details:**
- Tested on 620 functionals (626 total, 6 excluded due to extreme compilation times)
- Each functional tested with polarized/unpolarized variants
- Batch sizes: 1,000 and 100,000 grid points
- Speedup = pylibxc_time / jxc_time (higher is better)

## Notes on Coverage

- The Bazel parity suites (see table above) are the authoritative source for supported functionals and tolerances.
- The Julia harness is intentionally limited to a smoke subset while the native codegen evolves.
- Deprecated tables that previously tracked unsupported or numerically delicate functionals have been removed; refer to the test logs instead.

## Troubleshooting

### Maple Not Found
Maple is only required for local code generation (`make convert-maple*`). CI never runs Maple.
If you need to regenerate locally:
1. Ensure Maple 18 is installed
2. Add to PATH: `export PATH="$HOME/maple18/bin:$PATH"`
3. Or set: `export MAPLE_PATH="$HOME/maple18/bin"`

### CMake Errors
If CMake fails:
- Ensure CMake >= 3.5 is installed
- Check that the patch file is applied correctly
- Run `make distclean` and try again
