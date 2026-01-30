"""
Reference tests for shader math operations.

These tests verify that our Python implementations of complex math
operations produce the same results as expected, serving as a
reference for the JavaScript/GLSL implementations.

Run with: pytest tests/test_shader_math.py -v
"""

import pytest
import numpy as np
from numpy.testing import assert_allclose


# ============================================================================
# Complex arithmetic (reference implementations)
# ============================================================================

def cmul(a, b):
    """Complex multiplication using tuple representation."""
    return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])


def cdiv(a, b):
    """Complex division."""
    denom = b[0] * b[0] + b[1] * b[1]
    if denom < 1e-20:
        return (float('inf'), 0)
    return (
        (a[0] * b[0] + a[1] * b[1]) / denom,
        (a[1] * b[0] - a[0] * b[1]) / denom
    )


def cabs(z):
    """Complex absolute value."""
    return np.sqrt(z[0] ** 2 + z[1] ** 2)


def carg(z):
    """Complex argument."""
    return np.arctan2(z[1], z[0])


def cadd(a, b):
    """Complex addition."""
    return (a[0] + b[0], a[1] + b[1])


def csub(a, b):
    """Complex subtraction."""
    return (a[0] - b[0], a[1] - b[1])


# ============================================================================
# Laurent series evaluation
# ============================================================================

def laurent_eval(zeta, coeffs_pos, coeffs_neg, N):
    """
    Evaluate Laurent series at point zeta.

    z(zeta) = sum_{k=0}^N a_k zeta^k + sum_{k=1}^N b_k zeta^{-k}

    where coeffs_pos = [a_0, a_1, ..., a_N]
          coeffs_neg = [b_1, b_2, ..., b_N]
    """
    result = (0.0, 0.0)

    # Positive powers
    zeta_power = (1.0, 0.0)
    for k in range(min(N + 1, len(coeffs_pos))):
        result = cadd(result, cmul(coeffs_pos[k], zeta_power))
        zeta_power = cmul(zeta_power, zeta)

    # Negative powers
    zeta_inv = cdiv((1.0, 0.0), zeta)
    zeta_inv_power = zeta_inv
    for k in range(1, min(N + 1, len(coeffs_neg) + 1)):
        result = cadd(result, cmul(coeffs_neg[k - 1], zeta_inv_power))
        zeta_inv_power = cmul(zeta_inv_power, zeta_inv)

    return result


def laurent_deriv(zeta, coeffs_pos, coeffs_neg, N):
    """
    Evaluate derivative of Laurent series.

    z'(zeta) = sum_{k=1}^N k*a_k zeta^{k-1} + sum_{k=1}^N (-k)*b_k zeta^{-k-1}
    """
    result = (0.0, 0.0)

    # Derivative of positive powers: k * a_k * zeta^{k-1}
    zeta_power = (1.0, 0.0)
    for k in range(1, min(N + 1, len(coeffs_pos))):
        coeff = (k * coeffs_pos[k][0], k * coeffs_pos[k][1])
        result = cadd(result, cmul(coeff, zeta_power))
        zeta_power = cmul(zeta_power, zeta)

    # Derivative of negative powers: -k * b_k * zeta^{-k-1}
    zeta_inv = cdiv((1.0, 0.0), zeta)
    zeta_inv_power = cmul(zeta_inv, zeta_inv)  # Start at zeta^{-2}
    for k in range(1, min(N + 1, len(coeffs_neg) + 1)):
        coeff = (-k * coeffs_neg[k - 1][0], -k * coeffs_neg[k - 1][1])
        result = cadd(result, cmul(coeff, zeta_inv_power))
        zeta_inv_power = cmul(zeta_inv_power, zeta_inv)

    return result


# ============================================================================
# HSL to RGB conversion (matches shader)
# ============================================================================

def hsl_to_rgb(h, s, l):
    """Convert HSL to RGB (matching shader implementation)."""
    c = (1 - abs(2 * l - 1)) * s
    hp = h * 6
    x = c * (1 - abs((hp % 2) - 1))

    if hp < 1:
        rgb = (c, x, 0)
    elif hp < 2:
        rgb = (x, c, 0)
    elif hp < 3:
        rgb = (0, c, x)
    elif hp < 4:
        rgb = (0, x, c)
    elif hp < 5:
        rgb = (x, 0, c)
    else:
        rgb = (c, 0, x)

    m = l - c * 0.5
    return (rgb[0] + m, rgb[1] + m, rgb[2] + m)


def domain_color(w):
    """
    Map complex value to RGB using domain coloring.

    - Hue from argument (phase)
    - Lightness from log-modulus
    """
    r = cabs(w)
    theta = carg(w)

    h = (theta + np.pi) / (2 * np.pi)
    log_r = np.log(r + 1e-10)
    l = 0.5 + 0.4 * np.tanh(log_r * 0.5)

    return hsl_to_rgb(h, 0.8, l)


# ============================================================================
# Tests
# ============================================================================

class TestComplexArithmetic:
    """Test complex number operations."""

    def test_cmul_real(self):
        """Multiplication of real numbers."""
        assert_allclose(cmul((2, 0), (3, 0)), (6, 0))

    def test_cmul_imaginary(self):
        """i * i = -1."""
        assert_allclose(cmul((0, 1), (0, 1)), (-1, 0))

    def test_cmul_general(self):
        """(1 + 2i)(3 + 4i) = -5 + 10i."""
        assert_allclose(cmul((1, 2), (3, 4)), (-5, 10))

    def test_cdiv_real(self):
        """Division of real numbers."""
        assert_allclose(cdiv((6, 0), (2, 0)), (3, 0))

    def test_cdiv_imaginary(self):
        """1/i = -i."""
        assert_allclose(cdiv((1, 0), (0, 1)), (0, -1))

    def test_cdiv_general(self):
        """(1 + 2i)/(3 + 4i) = (11 + 2i)/25."""
        assert_allclose(cdiv((1, 2), (3, 4)), (11/25, 2/25))

    def test_cabs_pythagorean(self):
        """3-4-5 triangle."""
        assert cabs((3, 4)) == pytest.approx(5)

    def test_carg_positive_real(self):
        """arg(1) = 0."""
        assert carg((1, 0)) == pytest.approx(0)

    def test_carg_positive_imag(self):
        """arg(i) = pi/2."""
        assert carg((0, 1)) == pytest.approx(np.pi / 2)

    def test_carg_negative_real(self):
        """arg(-1) = pi."""
        assert carg((-1, 0)) == pytest.approx(np.pi)


class TestLaurentSeries:
    """Test Laurent series evaluation."""

    @pytest.fixture
    def identity_coeffs(self):
        """z(zeta) = zeta (identity map)."""
        return {
            'coeffs_pos': [(0, 0), (1, 0)],  # a_0 = 0, a_1 = 1
            'coeffs_neg': [(0, 0)],           # b_1 = 0
            'N': 1
        }

    @pytest.fixture
    def simple_coeffs(self):
        """z(zeta) = zeta + 0.5/zeta."""
        return {
            'coeffs_pos': [(0, 0), (1, 0)],
            'coeffs_neg': [(0.5, 0)],
            'N': 1
        }

    def test_identity_at_one(self, identity_coeffs):
        """z(1) = 1 for identity map."""
        result = laurent_eval((1, 0), **identity_coeffs)
        assert_allclose(result, (1, 0))

    def test_identity_at_i(self, identity_coeffs):
        """z(i) = i for identity map."""
        result = laurent_eval((0, 1), **identity_coeffs)
        assert_allclose(result, (0, 1))

    def test_simple_at_one(self, simple_coeffs):
        """z(1) = 1 + 0.5 = 1.5."""
        result = laurent_eval((1, 0), **simple_coeffs)
        assert_allclose(result, (1.5, 0))

    def test_simple_at_i(self, simple_coeffs):
        """z(i) = i + 0.5/i = i - 0.5i = 0.5i."""
        result = laurent_eval((0, 1), **simple_coeffs)
        assert_allclose(result, (0, 0.5))

    def test_simple_at_minus_one(self, simple_coeffs):
        """z(-1) = -1 - 0.5 = -1.5."""
        result = laurent_eval((-1, 0), **simple_coeffs)
        assert_allclose(result, (-1.5, 0))

    def test_deriv_identity(self, identity_coeffs):
        """z'(zeta) = 1 for identity map."""
        result = laurent_deriv((1, 0), **identity_coeffs)
        assert_allclose(result, (1, 0))

    def test_deriv_simple_at_one(self, simple_coeffs):
        """z'(1) = 1 - 0.5 = 0.5 for z(zeta) = zeta + 0.5/zeta."""
        result = laurent_deriv((1, 0), **simple_coeffs)
        assert_allclose(result, (0.5, 0))

    def test_deriv_simple_at_i(self, simple_coeffs):
        """z'(i) = 1 + 0.5 = 1.5 for z(zeta) = zeta + 0.5/zeta."""
        result = laurent_deriv((0, 1), **simple_coeffs)
        assert_allclose(result, (1.5, 0))


class TestDomainColoring:
    """Test domain coloring conversion."""

    def test_hsl_red(self):
        """h=0 gives red."""
        r, g, b = hsl_to_rgb(0, 1, 0.5)
        assert r == pytest.approx(1)
        assert g == pytest.approx(0)
        assert b == pytest.approx(0)

    def test_hsl_green(self):
        """h=1/3 gives green."""
        r, g, b = hsl_to_rgb(1/3, 1, 0.5)
        assert r == pytest.approx(0)
        assert g == pytest.approx(1)
        assert b == pytest.approx(0)

    def test_hsl_blue(self):
        """h=2/3 gives blue."""
        r, g, b = hsl_to_rgb(2/3, 1, 0.5)
        assert r == pytest.approx(0)
        assert g == pytest.approx(0)
        assert b == pytest.approx(1)

    def test_hsl_white(self):
        """l=1 gives white."""
        r, g, b = hsl_to_rgb(0, 0, 1)
        assert r == pytest.approx(1)
        assert g == pytest.approx(1)
        assert b == pytest.approx(1)

    def test_hsl_black(self):
        """l=0 gives black."""
        r, g, b = hsl_to_rgb(0, 0, 0)
        assert r == pytest.approx(0)
        assert g == pytest.approx(0)
        assert b == pytest.approx(0)

    def test_domain_color_valid_rgb(self):
        """Domain coloring produces valid RGB values."""
        test_points = [
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (-1, -1), (0.01, 0), (100, 0)
        ]
        for z in test_points:
            r, g, b = domain_color(z)
            assert 0 <= r <= 1, f"Red out of range for {z}"
            assert 0 <= g <= 1, f"Green out of range for {z}"
            assert 0 <= b <= 1, f"Blue out of range for {z}"

    def test_large_values_brighter(self):
        """Larger modulus produces brighter colors."""
        small = domain_color((0.1, 0))
        large = domain_color((10, 0))

        # Average brightness
        bright_small = sum(small) / 3
        bright_large = sum(large) / 3

        assert bright_large > bright_small


class TestCrossValidation:
    """
    Cross-validate Python and expected shader results.

    These tests use known mathematical values to verify correctness.
    """

    def test_unit_circle_laurent(self):
        """Points on unit circle should map to a valid curve."""
        # Simple map: z(zeta) = zeta + 0.3/zeta
        coeffs = {
            'coeffs_pos': [(0, 0), (1, 0)],
            'coeffs_neg': [(0.3, 0)],
            'N': 1
        }

        # Test 8 points on the unit circle
        for k in range(8):
            theta = k * np.pi / 4
            zeta = (np.cos(theta), np.sin(theta))
            z = laurent_eval(zeta, **coeffs)

            # Verify we get a valid point (not NaN or infinity)
            assert np.isfinite(z[0]) and np.isfinite(z[1])

            # For this specific map, |z| should be bounded
            assert cabs(z) < 2.0

    def test_newton_convergence_consistency(self):
        """
        Verify that forward eval followed by Newton inversion recovers original.

        This tests the core algorithm that both JS and GLSL implement.
        """
        coeffs = {
            'coeffs_pos': [(0, 0), (1, 0)],
            'coeffs_neg': [(0.3, 0)],
            'N': 1
        }

        # Pick a point on the unit circle
        zeta_orig = (np.cos(np.pi/3), np.sin(np.pi/3))

        # Forward: get z
        z = laurent_eval(zeta_orig, **coeffs)

        # Newton iteration to invert (simplified version)
        zeta = (1.0, 0.0)  # Initial guess
        for _ in range(20):
            z_curr = laurent_eval(zeta, **coeffs)
            residual = csub(z_curr, z)
            res_mag = cabs(residual)

            if res_mag < 1e-10:
                break

            dz = laurent_deriv(zeta, **coeffs)
            if cabs(dz) < 1e-12:
                break

            step = cdiv(residual, dz)
            zeta = csub(zeta, step)

        # Verify convergence
        z_recovered = laurent_eval(zeta, **coeffs)
        assert_allclose(z_recovered, z, atol=1e-6)


class TestNumericalStability:
    """Test edge cases and numerical stability."""

    def test_small_zeta(self):
        """Handle small zeta values (near origin)."""
        coeffs = {
            'coeffs_pos': [(0, 0), (1, 0)],
            'coeffs_neg': [(0.5, 0)],
            'N': 1
        }
        # Small but non-zero zeta
        zeta = (0.1, 0.1)
        z = laurent_eval(zeta, **coeffs)
        # Should be dominated by the 1/zeta term
        assert cabs(z) > 1.0

    def test_unit_circle_points(self):
        """Evaluate at points exactly on unit circle."""
        coeffs = {
            'coeffs_pos': [(0, 0), (1, 0)],
            'coeffs_neg': [(0.5, 0)],
            'N': 1
        }

        # Points exactly on unit circle
        angles = [0, np.pi/4, np.pi/2, np.pi, 3*np.pi/2]
        for theta in angles:
            zeta = (np.cos(theta), np.sin(theta))
            z = laurent_eval(zeta, **coeffs)
            dz = laurent_deriv(zeta, **coeffs)

            # Both should be finite
            assert np.isfinite(z[0]) and np.isfinite(z[1])
            assert np.isfinite(dz[0]) and np.isfinite(dz[1])
