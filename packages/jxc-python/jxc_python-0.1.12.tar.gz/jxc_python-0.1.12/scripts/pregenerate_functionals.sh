#!/bin/bash
# Script to pre-generate JAX functional implementations for CI builds

set -e

echo "Pre-generating JAX functional implementations..."

# Check if we have Maple available
if ! command -v maple &> /dev/null; then
    if [ -d "$HOME/maple18/bin" ]; then
        export PATH="$HOME/maple18/bin:$PATH"
    else
        echo "Error: Maple not found. Please ensure Maple is installed or available in PATH."
        exit 1
    fi
fi

echo "Running Maple conversions for Python and Julia..."
PATH="$HOME/maple18/bin:$PATH" bash scripts/convert_maple.sh
PATH="$HOME/maple18/bin:$PATH" bash scripts/convert_maple_julia.sh

# Check if functionals were generated
PY_COUNT=0
JL_COUNT=0
if [ -d "jxc/functionals" ] && [ "$(ls -A jxc/functionals)" ]; then
    PY_COUNT=$(ls -1 jxc/functionals/*.py 2>/dev/null | wc -l)
    echo "✓ Python functionals in jxc/functionals/ ($PY_COUNT files)"
fi
if [ -d "JXC.jl/src/functionals" ] && [ "$(ls -A JXC.jl/src/functionals)" ]; then
    JL_COUNT=$(ls -1 JXC.jl/src/functionals/*.jl 2>/dev/null | wc -l)
    echo "✓ Julia functionals in JXC.jl/src/functionals/ ($JL_COUNT files)"
fi

if [ "$PY_COUNT" -eq 0 ] && [ "$JL_COUNT" -eq 0 ]; then
    echo "✗ Failed to generate any functionals"
    exit 1
fi

# Optionally, commit the generated files
if [ "$1" = "--commit" ]; then
    echo "Committing pre-generated functionals..."
    git add jxc/functionals/ JXC.jl/src/functionals/
    git commit -m "chore: pre-generate Maple-based functionals (.py and .jl) for CI

Generated locally from Maple; committed for CI distribution."
    echo "✓ Committed pre-generated functionals"
fi

echo "Pre-generation complete!"
