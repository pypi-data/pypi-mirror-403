"""
Hill curve fitting module for sprime.

Implements four-parameter logistic (4PL) regression for fitting dose-response curves.
Adapted to work with sprime's domain entities.
"""

from typing import Optional, List, Tuple, Dict, Any, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .sprime import HillCurveParams
    import numpy as np

# Import scipy (numpy comes as scipy dependency)
# Import at module level for type hints, but handle ImportError gracefully
try:
    import numpy as np
    from scipy.optimize import curve_fit
except ImportError:
    np = None
    curve_fit = None


def hill_equation(x, lower: float, hill_coefficient: float, ec50: float, upper: float):
    """
    Four-parameter Hill equation (4PL model).
    
    Formula: y = D + (A - D) / (1 + (x/C)^n)
    Where:
        A = upper (upper asymptote)
        D = lower (lower asymptote)  
        C = ec50 (half-maximal concentration)
        n = hill_coefficient (slope/steepness)
    
    Args:
        x: Concentration values
        lower: Lower asymptote (A parameter)
        hill_coefficient: Hill coefficient/slope (n parameter)
        ec50: Half-maximal concentration (C parameter)
        upper: Upper asymptote (D parameter)
        
    Returns:
        Response values
    """
    return upper + (lower - upper) / (1 + (x / ec50) ** hill_coefficient)


def fit_hill_curve(
    concentrations: List[float],
    responses: List[float],
    *,
    # Initial parameter guesses (all optional with defaults)
    initial_lower: Optional[float] = None,
    initial_upper: Optional[float] = None,
    initial_ec50: Optional[float] = None,
    initial_hill_coefficient: Optional[float] = None,
    # Curve direction
    curve_direction: Optional[str] = None,  # "up", "down", or None for auto-detect
    # Optimization parameters
    maxfev: int = 3000000,
    # Zero concentration handling
    zero_replacement: float = 1e-24,
    # Parameter bounds (optional)
    bounds: Optional[Tuple[List[float], List[float]]] = None,
    # Additional scipy.optimize.curve_fit parameters
    **curve_fit_kwargs
):
    """
    Fit four-parameter Hill equation to dose-response data.
    
    Fits a sigmoidal curve to concentration-response data and returns
    HillCurveParams with fitted parameters.
    
    Args:
        concentrations: List of concentration values
        responses: List of response values (must match length of concentrations)
        initial_lower: Initial guess for lower asymptote (default: auto-estimated)
        initial_upper: Initial guess for upper asymptote (default: auto-estimated)
        initial_ec50: Initial guess for EC50 (default: auto-estimated)
        initial_hill_coefficient: Initial guess for Hill coefficient (default: auto-estimated)
        curve_direction: Curve direction - "up" (increasing), "down" (decreasing), 
                        or None for auto-detect (tries both, selects best R²)
        maxfev: Maximum function evaluations for optimization (default: 3,000,000)
        zero_replacement: Value to replace zero concentrations (default: 1e-24)
        bounds: Optional parameter bounds as (lower_bounds, upper_bounds) tuples
                Format: ([lower_min, hill_min, ec50_min, upper_min], 
                        [lower_max, hill_max, ec50_max, upper_max])
        **curve_fit_kwargs: Additional arguments passed to scipy.optimize.curve_fit
        
    Returns:
        HillCurveParams: Fitted curve parameters with R²
        
    Raises:
        ValueError: If inputs are invalid
        RuntimeError: If curve fitting fails
        ImportError: If numpy/scipy are not installed
    """
    # Import here to avoid circular import
    from .sprime import HillCurveParams
    
    try:
        import numpy as np
        from scipy.optimize import curve_fit
    except ImportError as e:
        raise ImportError(
            "Hill curve fitting requires scipy. "
            "Install with: pip install scipy"
        ) from e
    
    # Validate inputs
    if len(concentrations) != len(responses):
        raise ValueError("Concentrations and responses must have same length")
    
    if len(concentrations) < 4:
        raise ValueError("Need at least 4 data points to fit 4-parameter Hill equation")
    
    # Convert to numpy arrays (make copies to avoid modifying originals)
    concentrations = list(concentrations)
    responses = list(responses)
    
    # Sort data if needed (ascending concentrations)
    if concentrations[0] > concentrations[-1]:
        concentrations.reverse()
        responses.reverse()
    
    # Handle zero concentrations
    if concentrations[0] == 0:
        concentrations[0] = zero_replacement
    
    x_data = np.array(concentrations)
    y_data = np.array(responses)
    
    # Auto-detect or use specified curve direction
    if curve_direction is None:
        # Try both directions, return best fit
        return _fit_with_auto_direction(
            x_data, y_data,
            initial_lower, initial_upper, initial_ec50, initial_hill_coefficient,
            maxfev, bounds, **curve_fit_kwargs
        )
    else:
        # Fit with specified direction
        return _fit_single_direction(
            x_data, y_data, curve_direction,
            initial_lower, initial_upper, initial_ec50, initial_hill_coefficient,
            maxfev, bounds, **curve_fit_kwargs
        )


def _fit_single_direction(
    x_data: "np.ndarray",
    y_data: "np.ndarray",
    curve_direction: str,
    initial_lower: Optional[float],
    initial_upper: Optional[float],
    initial_ec50: Optional[float],
    initial_hill_coefficient: Optional[float],
    maxfev: int,
    bounds: Optional[Tuple[List[float], List[float]]],
    **curve_fit_kwargs
):
    """Fit curve with specified direction."""
    # Import here to avoid circular import
    from .sprime import HillCurveParams
    # Get initial guesses (use defaults if not provided)
    if curve_direction == "up":
        # For curves that go up (increasing response)
        guess_lower = initial_lower if initial_lower is not None else 0.001
        guess_hill = initial_hill_coefficient if initial_hill_coefficient is not None else 1.515
        guess_ec50 = initial_ec50 if initial_ec50 is not None else 108.0
        guess_upper = initial_upper if initial_upper is not None else 3.784
    else:  # "down"
        # For curves that go down (decreasing response)
        guess_lower = initial_lower if initial_lower is not None else 10.0
        guess_hill = initial_hill_coefficient if initial_hill_coefficient is not None else -0.3
        guess_ec50 = initial_ec50 if initial_ec50 is not None else 0.4
        guess_upper = initial_upper if initial_upper is not None else 90.0
    
    # If any parameter not provided, try to estimate from data
    if initial_lower is None:
        guess_lower = min(y_data) * 0.1 if guess_lower == 0.001 else guess_lower
    if initial_upper is None:
        guess_upper = max(y_data) * 1.1 if guess_upper in (3.784, 90.0) else guess_upper
    if initial_ec50 is None:
        # Estimate EC50 as median concentration
        guess_ec50 = float(np.median(x_data))
    
    initial_guess = [guess_lower, guess_hill, guess_ec50, guess_upper]
    
    # Fit the 4PL model
    try:
        fit_kwargs = {"p0": initial_guess, "maxfev": maxfev, **curve_fit_kwargs}
        if bounds is not None:
            fit_kwargs["bounds"] = bounds
        
        params, covariance = curve_fit(
            hill_equation,
            x_data,
            y_data,
            **fit_kwargs
        )
    except Exception as e:
        raise RuntimeError(f"Failed to fit Hill curve: {e}") from e
    
    # Extract fitted parameters
    lower_fit, hill_fit, ec50_fit, upper_fit = params
    
    # Validate results
    if np.isnan(lower_fit) or np.isnan(ec50_fit) or np.isnan(upper_fit):
        raise RuntimeError(
            f"Fitting produced invalid parameters: lower={lower_fit}, "
            f"ec50={ec50_fit}, upper={upper_fit}"
        )
    
    # Calculate R²
    y_pred = hill_equation(x_data, *params)
    residuals = y_data - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return HillCurveParams(
        ec50=float(ec50_fit),
        upper=float(upper_fit),
        lower=float(lower_fit),
        hill_coefficient=float(hill_fit),
        r_squared=float(r_squared)
    )


def _fit_with_auto_direction(
    x_data: "np.ndarray",
    y_data: "np.ndarray",
    initial_lower: Optional[float],
    initial_upper: Optional[float],
    initial_ec50: Optional[float],
    initial_hill_coefficient: Optional[float],
    maxfev: int,
    bounds: Optional[Tuple[List[float], List[float]]],
    **curve_fit_kwargs
):
    """Try both curve directions and return best fit (highest R²)."""
    # Import here to avoid circular import
    from .sprime import HillCurveParams
    """Try both curve directions and return best fit (highest R²)."""
    best_params = None
    best_r2 = None
    best_direction = None
    
    for direction in ["up", "down"]:
        try:
            params = _fit_single_direction(
                x_data, y_data, direction,
                initial_lower, initial_upper, initial_ec50, initial_hill_coefficient,
                maxfev, bounds, **curve_fit_kwargs
            )
            
            if params.r_squared is not None:
                if best_r2 is None or params.r_squared > best_r2:
                    best_params = params
                    best_r2 = params.r_squared
                    best_direction = direction
        except (RuntimeError, ValueError):
            # Try next direction if this one fails
            continue
    
    if best_params is None:
        raise RuntimeError(
            "Failed to fit Hill curve in either direction. "
            "Check data quality and initial parameter guesses."
        )
    
    return best_params

