"""Pytest configuration and shared fixtures for analytic_continuation tests."""

import pytest
import numpy as np


@pytest.fixture
def unit_circle_points():
    """Generate points on the unit circle."""
    n = 100
    thetas = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.exp(1j * thetas)


@pytest.fixture
def ellipse_points():
    """Generate points on an ellipse with semi-axes 2 and 1."""
    n = 100
    thetas = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return 2 * np.cos(thetas) + 1j * np.sin(thetas)


@pytest.fixture
def sample_spline_export_data():
    """Sample SplineExport data for testing."""
    return {
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z",
        "closed": True,
        "parameters": {
            "tension": 0.5,
            "adaptiveTolerance": 3.0,
            "minDistance": 15.0,
        },
        "controlPoints": [
            {"x": 100, "y": 100},
            {"x": 200, "y": 100},
            {"x": 200, "y": 200},
            {"x": 100, "y": 200},
        ],
        "spline": [],
        "adaptivePolyline": [
            {"x": 100, "y": 100},
            {"x": 150, "y": 100},
            {"x": 200, "y": 100},
            {"x": 200, "y": 150},
            {"x": 200, "y": 200},
            {"x": 150, "y": 200},
            {"x": 100, "y": 200},
            {"x": 100, "y": 150},
        ],
    }
