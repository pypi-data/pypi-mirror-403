import json
import re
import sympy
import numpy as np
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor


def _convert_ternary(expr: str) -> str:
    """
    Convert a single C-style ternary (cond ? a : b) into SymPy Piecewise.
    Supports one level (no nesting).
    """
    if "?" not in expr or ":" not in expr:
        return expr

    # naive split for single ternary
    # pattern: <cond> ? <a> : <b>
    parts = expr.split("?")
    if len(parts) != 2:
        return expr
    cond = parts[0].strip()
    rest = parts[1]
    if ":" not in rest:
        return expr
    a, b = rest.split(":", 1)
    a = a.strip()
    b = b.strip()
    return f"Piecewise(({a}, {cond}), ({b}, True))"


def robust_parse(expr_str):
    """
    Parses a string into a SymPy expression with relaxed syntax rules:
    - Implicit multiplication (5x -> 5*x)
    - Caret for power (x^2 -> x**2)
    - Aliases 'y' to 'z' for 2D convenience
    """
    if not isinstance(expr_str, str):
        return sympy.sympify(expr_str) 
        
    transformations = (standard_transformations + (implicit_multiplication_application, convert_xor))
    
    # Define symbols and alias y -> z
    x, z, vx, vz, t, pid = sympy.symbols('x z vx vz t id')
    local_dict = {
        'x': x, 'z': z, 'y': z, 'vx': vx, 'vz': vz, 't': t, 'id': pid,
        'pi': sympy.pi, 'e': sympy.E
    }

    # Ensure common functions are recognized (Abs not abs)
    local_dict.update({
        'sin': sympy.sin,
        'cos': sympy.cos,
        'tan': sympy.tan,
        'exp': sympy.exp,
        'sqrt': sympy.sqrt,
        'log': sympy.log,
        'abs': sympy.Abs,
        'Abs': sympy.Abs,
        'Piecewise': sympy.Piecewise,
    })

    try:
        pre = _convert_ternary(expr_str)
        return parse_expr(pre, transformations=transformations, local_dict=local_dict)
    except Exception:
        # Fallback
        return sympy.sympify(expr_str, locals=local_dict)


def parse_odes_to_function(ode_json_str):
    """
    Parses a JSON string of ODEs and returns a dynamic update function.
    """
    try:
        if isinstance(ode_json_str, str):
            odes = json.loads(ode_json_str)
        else:
            odes = ode_json_str
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON from LLM: {e}")
        return None

    # Define standard symbols
    x, z, vx, vz, t = sympy.symbols('x z vx vz t')
    
    deriv_map = {}
    keys = ['dx', 'dz', 'dvx', 'dvz']
    
    for key in keys:
        expr_str = odes.get(key, "0")
        try:
            # Parse the expression safely using robust parser
            expr = robust_parse(str(expr_str))
            
            # Create a localized function
            # Arguments match the order we will call them
            func = sympy.lambdify((x, z, vx, vz, t), expr, modules=['numpy', 'math'])
            deriv_map[key] = func
        except Exception as e:
            print(f"Error parsing expression for {key}: {e}")
            return None

    def dynamics(particle, dt):
        # Current state
        cx, cz, cvx, cvz = particle.x, particle.z, particle.vx, particle.vz
        # We assume particle might track time, or we just pass 0 if autonomous
        ct = getattr(particle, 'time', 0.0)
        
        try:
            # Calculate derivatives
            val_dx = deriv_map['dx'](cx, cz, cvx, cvz, ct)
            val_dz = deriv_map['dz'](cx, cz, cvx, cvz, ct)
            val_dvx = deriv_map['dvx'](cx, cz, cvx, cvz, ct)
            val_dvz = deriv_map['dvz'](cx, cz, cvx, cvz, ct)
            
            # Simple Euler Integration
            particle.x += float(val_dx) * dt
            particle.z += float(val_dz) * dt
            particle.vx += float(val_dvx) * dt
            particle.vz += float(val_dvz) * dt
            
            # Update time if tracked
            if hasattr(particle, 'time'):
                particle.time += dt
                
        except Exception as e:
            # Prevent crashing the renderer on math errors (e.g. div by zero)
            print(f"Runtime error in dynamics: {e}")

    return dynamics
