"""
Code generation utilities.

Generates standalone Python code for evaluating analytic continuations.
"""

from .models import ContinuationDefinition


def generate_python_continuation_code(cont: ContinuationDefinition) -> str:
    """Generate standalone Python code to evaluate the continuation."""

    coeffs_neg = cont.laurent_map.coeffs_neg
    coeffs_pos = cont.laurent_map.coeffs_pos

    code = f'''"""
Analytic Continuation: F(z) = A(f(B(z)))

Generated from session: {cont.session_id or "unknown"}
Created: {cont.created_at or "unknown"}
Expression: {cont.expression or "rational function from zeros/poles"}

This evaluates the Schwarz reflection composition through a Jordan curve.
"""

import numpy as np
from typing import Optional

# Laurent map coefficients for z(zeta)
N = {cont.laurent_map.N}
CURVE_SCALE = {cont.laurent_map.curve_scale}

# a_0, a_1, ..., a_N (positive powers)
COEFFS_POS = np.array({coeffs_pos}, dtype=complex)
# Convert to complex
COEFFS_POS = np.array([c[0] + 1j*c[1] for c in COEFFS_POS])

# b_1, ..., b_N (negative powers)
COEFFS_NEG = np.array({coeffs_neg}, dtype=complex)
COEFFS_NEG = np.array([c[0] + 1j*c[1] for c in COEFFS_NEG])

# Zeros and poles of the meromorphic function
ZEROS = {[(z["re"], z["im"], z.get("multiplicity", 1)) for z in cont.zeros]}
POLES = {[(p["re"], p["im"], p.get("multiplicity", 1)) for p in cont.poles]}
'''

    if cont.expression:
        code += f'''
# Symbolic expression
EXPRESSION = "{cont.expression}"
'''

    code += '''

def eval_laurent_map(zeta: complex) -> complex:
    """Evaluate z(zeta) = a_0 + sum a_k*zeta^k + sum b_k*zeta^-k"""
    z = COEFFS_POS[0]  # a_0

    # Positive powers
    p = zeta
    for k in range(N):
        z += COEFFS_POS[k+1] * p
        p *= zeta

    # Negative powers
    q = 1.0 / zeta
    p = q
    for k in range(N):
        z += COEFFS_NEG[k] * p
        p *= q

    return z


def eval_laurent_deriv(zeta: complex) -> complex:
    """Evaluate z'(zeta)"""
    dz = 0.0

    # Positive powers: k * a_k * zeta^(k-1)
    p = 1.0
    for k in range(N):
        dz += (k + 1) * COEFFS_POS[k+1] * p
        p *= zeta

    # Negative powers: -k * b_k * zeta^(-k-1)
    q = 1.0 / zeta
    p = q * q
    for k in range(N):
        dz -= (k + 1) * COEFFS_NEG[k] * p
        p *= q

    return dz


def invert_laurent_map(z_query: complex, max_iters: int = 40, tol: float = 1e-10) -> Optional[complex]:
    """
    Invert z(zeta) = z_query using Newton iteration.

    Returns zeta such that z(zeta) approx z_query, or None if inversion fails.
    """
    # Multi-start: try several initial guesses
    n_theta = 64
    best_zeta = None
    best_residual = float('inf')

    for r in [0.99, 1.0, 1.01]:
        for theta in np.linspace(0, 2*np.pi, n_theta, endpoint=False):
            zeta = r * np.exp(1j * theta)

            for _ in range(max_iters):
                z = eval_laurent_map(zeta)
                residual = z - z_query

                if abs(residual) < tol * CURVE_SCALE:
                    if abs(residual) < best_residual:
                        best_residual = abs(residual)
                        best_zeta = zeta
                    break

                dz = eval_laurent_deriv(zeta)
                if abs(dz) < 1e-14:
                    break

                # Damped Newton step
                step = residual / dz
                alpha = 1.0
                for _ in range(8):
                    zeta_new = zeta - alpha * step
                    if abs(eval_laurent_map(zeta_new) - z_query) < abs(residual):
                        break
                    alpha *= 0.5
                zeta = zeta_new

    return best_zeta


def eval_meromorphic(z: complex) -> complex:
    """Evaluate the meromorphic function f(z) from zeros and poles."""
    result = 1.0

    for re, im, mult in ZEROS:
        result *= (z - complex(re, im)) ** mult

    for re, im, mult in POLES:
        result /= (z - complex(re, im)) ** mult

    return result


def eval_continuation(z_query: complex) -> Optional[complex]:
    """
    Evaluate the analytic continuation F(z) at a point.

    F(z) = A(f(B(z))) where A, B are Schwarz reflections.
    Due to the shared parameterization, this simplifies to f(z(zeta))
    where zeta is found by inverting z(zeta) = z_query.

    Parameters
    ----------
    z_query : complex
        The point at which to evaluate the continuation

    Returns
    -------
    complex or None
        The value F(z_query), or None if inversion failed
    """
    # Step 1: Find zeta such that z(zeta) = z_query
    zeta = invert_laurent_map(z_query)
    if zeta is None:
        return None

    # Step 2: Evaluate f(z(zeta))
    z_on_curve = eval_laurent_map(zeta)
    return eval_meromorphic(z_on_curve)


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        # Parse complex number from command line
        z_str = sys.argv[1]
        try:
            z = complex(z_str.replace('i', 'j'))
        except ValueError:
            print(f"Could not parse '{z_str}' as complex number")
            sys.exit(1)
    else:
        z = 0.5 + 0.5j

    result = eval_continuation(z)
    if result is not None:
        print(f"F({z}) = {result}")
    else:
        print(f"Failed to evaluate F({z}) - inversion did not converge")
'''

    return code
