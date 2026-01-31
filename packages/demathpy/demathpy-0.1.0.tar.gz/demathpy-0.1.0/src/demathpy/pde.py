"""
Field math utilities (PDE/field-space helpers).

Provides a grid-based PDE solver and sampling utilities for projecting
field PDEs into particle motion without hardcoded dynamics.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Any, Optional

import re
import json
import numpy as np

from .symbols import normalize_symbols, normalize_lhs


def _preprocess_expr(expr: str) -> str:
    expr = (expr or "").strip()
    expr = re.sub(r"\(\s*approx\s*\)", "", expr, flags=re.IGNORECASE)
    expr = re.sub(r"\bapprox\b", "", expr, flags=re.IGNORECASE)
    if "=" in expr:
        expr = expr.split("=")[-1]
    expr = normalize_symbols(expr)
    return expr.strip()


def normalize_pde(pde: str) -> str:
    return (pde or "").strip()


def parse_pde(pde: str) -> Tuple[str, int, str, str]:
    """
    Returns (var, order, lhs_coeff_expr, rhs_expr).
    """
    pde = normalize_pde(pde)
    if "=" not in pde:
        return "u", 1, "1", pde

    lhs, rhs = pde.split("=", 1)
    lhs = normalize_lhs(lhs.strip())
    rhs = rhs.strip()

    def _extract_coeff(lhs_expr: str, deriv_expr: str) -> str:
        coeff = lhs_expr.replace(deriv_expr, "").strip()
        if not coeff:
            return "1"
        coeff = coeff.strip("*")
        return _preprocess_expr(coeff) or "1"
    
    pattern = r"(?:∂|d)\s*(?:\^?(\d+))?\s*([a-zA-Z_]\w*)\s*/\s*(?:∂|d)t\s*(?:\^?(\d+))?"
    m = re.search(pattern, lhs)
    
    if m:
        ord1 = m.group(1)
        var = m.group(2)
        ord2 = m.group(3)
        
        order = 1
        if ord1:
            order = int(ord1)
        elif ord2:
            order = int(ord2)
            
        coeff = _extract_coeff(lhs, m.group(0))
        return var, order, coeff, _preprocess_expr(rhs)

    return "u", 1, "1", _preprocess_expr(rhs)


class PDE:
    equation: str
    desc: str
    mode: str

    u: np.ndarray 
    u_desc: str
    u_shape: List[str] 

    boundry: List[str] # List of equations like "x(0, t) = 0"
    initial: List[str] # List of equations like "u(x,0) = sin(x)"
    
    space_axis: List[str]
    external_variables: Dict[str, float]

    grid_dx: float
    time: float # Internal time tracker
    
    _u_t: np.ndarray | None = None
    _parsed_bcs: List[Dict[str, Any]] = []

    def __init__(self, equation: str = "", desc: str = "", space_axis: List[str] = None):
        self.equation = equation
        self.desc = desc

        self.u = np.array([])
        self.u_desc = ""
        self.u_shape = ["u"] 

        self.boundry = []
        self.initial = []

        self.space_axis = space_axis or ["z", "x"]
        self.external_variables = {}

        self.grid_dx = 1.0
        self.time = 0.0
        self._u_t = None
        self._parsed_bcs = []

    def init_grid(self, width: int = 0, height: int = 0, depth: int = 0, dx: float = 0.1, shape: tuple = None):
        self.grid_dx = dx
        self.time = 0.0
        
        if shape:
            grid_shape = shape
        else:
            dims = []
            for axis in self.space_axis:
                if axis == 'x':
                    dims.append(max(2, int(width / dx)))
                elif axis == 'y':  
                    dims.append(max(2, int(height / dx)))
                elif axis == 'z':
                    if 'y' in self.space_axis:
                        dims.append(max(2, int(depth / dx)))
                    else: 
                        dims.append(max(2, int(height / dx)))
                else:
                    dims.append(max(2, int(width / dx)))
            
            grid_shape = tuple(dims)
            if not grid_shape:
                 grid_shape = (max(2, int(height/dx)), max(2, int(width/dx)))

        if not self.u_shape:
             self.u_shape = ["u"]
        
        num_components = len(self.u_shape)
        if num_components > 1:
            self.u = np.zeros((num_components, *grid_shape), dtype=float)
        else:
            self.u = np.zeros(grid_shape, dtype=float)
            
        self._u_t = np.zeros_like(self.u)
        
        # Initialize default boundaries only if empty and no equations provided
        if not self.boundry:
            # Default to periodic strings if user hasn't provided equations
            pass # We will rely on empty -> periodic or logic in parsing

    def set_initial_state(self):
        """
        Parses and applies initial conditions from self.initial.
        Equations format: "u = sin(x)" or "ux = ..." or "u(x,0) = ..."
        """
        env = self._build_eval_env()
        env["t"] = 0.0
        
        if not self.initial:
            return

        for ic_eqn in self.initial:
            # Simple parsing: LHS = RHS
            if "=" not in ic_eqn: continue
            lhs, rhs = ic_eqn.split("=", 1)
            lhs = lhs.strip()
            rhs_expr = rhs.strip()
            
            # Determine target component
            target_idx = None
            target_name = "u"
            
            # Check for "u", "ux", "u(x,0)", etc.
            # Regex to match var name at start
            m = re.match(r"^([a-zA-Z_]\w*)", lhs)
            if m:
                target_name = m.group(1)
            
            # Map target_name to u index
            if target_name == "u" and len(self.u_shape) == 1:
                target_idx = None # Scalar u
            elif target_name in self.u_shape:
                target_idx = self.u_shape.index(target_name)
            
            # Evaluate RHS
            try:
                # Preprocess rhs to safe python
                rhs_expr = _preprocess_expr(rhs_expr)
                val = eval(rhs_expr, {}, env)
                
                # Apply
                if target_idx is None:
                    #Scalar
                    if np.shape(val) == np.shape(self.u):
                        self.u[:] = val
                    else:
                        # Broadcast?
                        self.u[:] = val
                else:
                    # Vector component
                    if target_idx < len(self.u):
                         self.u[target_idx][:] = val
            except Exception as e:
                print(f"Failed to set IC '{ic_eqn}': {e}")


    def get_grid(self, u_state: np.ndarray = None, dt: float = 0.0) -> np.ndarray:
        """
        Calculates the change (du) or rate of change (forcing) for the current PDE state
        without modifying the internal state. Useful for visualization (vector fields).

        Args:
            u_state (np.ndarray, optional): A state to evaluate instead of self.u.
                Must match self.u shape.
            dt (float, optional): Time step. 
                If > 0, returns the delta (du = forcing * dt).
                If 0 (default), returns the rate of change (forcing).

        Returns:
            np.ndarray: The computed change or rate grid (same shape as u).
        """
        # 1. Backup state
        original_u = self.u
        original_u_t = self._u_t
        
        # 2. Swap State (Temporarily)
        if u_state is not None:
            if u_state.shape != self.u.shape:
                # Try to run anyway but this might crash later if env injection fails
                pass 
            self.u = u_state
            # For 2nd order, we might ideally need a u_t_state. 
            # We'll assume existing u_t or zeros if shape mismatch.
            if self._u_t is not None and self._u_t.shape != u_state.shape:
                self._u_t = np.zeros_like(u_state)
            elif self._u_t is None:
                self._u_t = np.zeros_like(u_state)
        
        # 3. Prepare Environment
        var_name, order, coeff_expr, rhs_expr = parse_pde(self.equation)
        
        env = self._build_eval_env()
        env["t"] = self.time

        # Inject u components (Logic duplicated from step)
        if len(self.u_shape) == 1:
            name = self.u_shape[0]
            env[name] = self.u
            v_t = self._u_t if self._u_t is not None else np.zeros_like(self.u)
            env[f"{name}_t"] = v_t
        else:
            for i, name in enumerate(self.u_shape):
                env[name] = self.u[i]
                v_t = self._u_t[i] if self._u_t is not None else np.zeros_like(self.u[i])
                env[f"{name}_t"] = v_t
            env["u"] = self.u
            env["u_t"] = self._u_t if self._u_t is not None else np.zeros_like(self.u)

        # 4. Compute Forcing
        try:
            rhs = self.evaluate_rhs(rhs_expr, env)
            if isinstance(rhs, list):
                rhs = np.array(rhs)
            
            coeff = self.evaluate_scalar(coeff_expr, env)
            forcing = rhs / (coeff if coeff else 1.0)
            
            # 5. Handle Order logic for return value
            if order == 2:
                # 2nd Order: u'' = forcing.
                if dt > 0:
                     # Update logic approximation: u_new ~ u + dt * v + 0.5 * dt^2 * a
                     v = self._u_t if self._u_t is not None else np.zeros_like(self.u)
                     du = dt * v + 0.5 * (dt**2) * forcing
                else:
                    # If dt=0, return forcing (acceleration).
                    # Note: du/dt (velocity) is u_t, but usually one probes the field of forces.
                    du = forcing 
            else:
                # 1st Order
                if dt > 0:
                    du = forcing * dt
                else:
                    du = forcing # Rate of change

        except Exception as e:
            # Restore and re-raise
            self.u = original_u
            self._u_t = original_u_t
            raise e

        # 6. Restore
        self.u = original_u
        self._u_t = original_u_t
        
        return du


    def _parse_boundaries(self):
        """
        Parses `self.boundry` list of equations into structured BCs.
        Supports formats:
          - "x=0 = 1.0" (Dirichlet on Axis X at 0)
          - "u(x=0) = 1.0" (Dirichlet)
          - "dx(u)(x=0) = 0" (Neumann)
        """
        self._parsed_bcs = []
        
        # Helper to map axis name to index
        def get_axis_idx(name):
            try:
                return self.space_axis.index(name)
            except ValueError:
                return -1

        for bc_eqn in self.boundry:
            bc_eqn = bc_eqn.strip()
            if not bc_eqn: continue
            
            # 1. Handle "periodic" keyword
            if bc_eqn.lower() == "periodic":
                 self._parsed_bcs.append({"type": "periodic", "axis": None})
                 continue
            
            # 2. Split LHS = RHS
            # Use rsplit to split on the last equals sign, to allow "u(x=0) = 5"
            parts = bc_eqn.rsplit("=", 1)
            if len(parts) != 2:
                # Fallback for "periodic x" or just "periodic" mixed in text
                if "periodic" in bc_eqn.lower():
                     self._parsed_bcs.append({"type": "periodic", "axis": None})
                continue

            lhs, rhs = parts
            lhs = _preprocess_expr(lhs) # Normalize symbols in LHS
            rhs = rhs.strip()
            
            # 3. Detect Boundary Type
            # Neumann if derivative operator present
            bc_type = "dirichlet"
            if any(op in lhs for op in ["dx", "dy", "dz", "grad", "∂", "d/d"]):
                bc_type = "neumann"
            
            # 4. Detect Axis and Side
            # Look for explicit assignment "x=0" or "x=10" inside LHS
            # OR implicit function arg "u(0, y)" style (harder, stick to explicit first)
            
            # Regex for "axis = value" inside parentheses or standalone
            # Matches: "x=0", "x = 10.0", "z=5"
            # Note: _preprocess_expr might have removed spaces
            axis_match = re.search(r"([a-z])\s*=\s*([0-9\.]+)", lhs)
            
            target_axis = -1
            boundary_side = 0 
            
            if axis_match:
                ax_name = axis_match.group(1)
                val_str = axis_match.group(2)
                val = float(val_str)
                target_axis = get_axis_idx(ax_name)
                
                # Determine "Left/Lower" or "Right/Upper" based on 0 check or relative?
                # For robustness, we should probably check against grid size if possible,
                # but grid isn't always init when parsing.
                # Convention: 0 is start (0), anything > 0 is end (1) ?? 
                # Better: 0 is side 0. If val > 0 implies side 1??
                # Let's assume user provides 0 for left, and Width/L for right.
                if val <= 1e-9: boundary_side = 0
                else: boundary_side = 1
                
            else:
                # Fallback: check if LHS starts with axis name? "x(0)"
                # Or "u(0)" implies axis 0, coordinate 0?
                # This is ambiguous. Let's warn or skip.
                pass
            
            # Evaluate RHS validity check? No, keep as string/expression.

            self._parsed_bcs.append({
                "type": bc_type,
                "axis": target_axis,
                "side": boundary_side,
                "rhs": rhs,
                "eqn": bc_eqn
            })


    def _apply_boundary_conditions(self):
        """
        Enforce BCs on the grid state `self.u`.
        """
        if not self._parsed_bcs and self.boundry:
            self._parse_boundaries()
            
        env = self._build_eval_env()
        env["t"] = self.time

        # If no equations, and user didn't specify periodic string, what default?
        # If user explicitly put "periodic" in boundry list, handled by parser.
        
        for bc in self._parsed_bcs:
            if bc["type"] == "periodic":
                # Periodic is handled by _get_neighbor implicitly usually. 
                # No data clamping needed unless we use ghost nodes explicitly.
                continue
                
            if bc["axis"] == -1: continue
            
            # Map space axis to array axis
            # self.u ndim vs spatial dims
            spatial_dims = len(self.space_axis)
            ndim = self.u.ndim
            arr_axis = (ndim - spatial_dims) + bc["axis"]
            
            # Slice for boundary
            # side 0 -> index 0. side 1 -> index -1.
            idx = 0 if bc["side"] == 0 else -1
            
            # Construct slice object to access all other dims
            # e.g. u[..., 0] or u[..., -1]
            sl = [slice(None)] * ndim
            sl[arr_axis] = idx
            tuple_sl = tuple(sl)
            
            # Evaluate RHS
            try:
                rhs_val = self.evaluate_rhs(bc["rhs"], env)
                
                if bc["type"] == "dirichlet":
                    # Hard set boundary value
                    # If u is vector, and equation didn't specify component?
                    # Assuming scalar u or eqn u(...) applies to all? 
                    # For now assume matches u shape.
                    self.u[tuple_sl] = rhs_val
                
                elif bc["type"] == "neumann":
                    # Neumann: du/dn = rhs
                    # n is outward normal.
                    # Left boundary (side 0): normal is -x. du/dn = -du/dx.
                    # Right boundary (side 1): normal is +x. du/dn = +du/dx.
                    
                    # Approximating: u[0] = u[1] - rhs * dx (if normal is -x ?)
                    # Left (idx 0): du/dx ~ (u[1]-u[0])/dx. 
                    # If du/dn = g, then -du/dx = g => du/dx = -g.
                    # (u[1]-u[0])/dx = -g => u[1]-u[0] = -g*dx => u[0] = u[1] + g*dx.
                    
                    # Right (idx -1): du/dx ~ (u[-1]-u[-2])/dx.
                    # du/dn = +du/dx = g.
                    # u[-1] - u[-2] = g*dx => u[-1] = u[-2] + g*dx.
                    
                    g = rhs_val
                    dx = self.grid_dx
                    
                    if bc["side"] == 0: # Left
                        neighbor_sl = list(sl)
                        neighbor_sl[arr_axis] = 1 # Inner point u[1]
                        self.u[tuple_sl] = self.u[tuple(neighbor_sl)] + g * dx
                    else: # Right
                        neighbor_sl = list(sl)
                        neighbor_sl[arr_axis] = -2 # Inner point u[-2]
                        self.u[tuple_sl] = self.u[tuple(neighbor_sl)] + g * dx
                    
            except Exception as e:
                # Log error?
                pass


    def _get_neighbor(self, u_in: np.ndarray, axis: int, step: int) -> np.ndarray:
        # Check explicit equation-based BCs first?
        # My _apply_boundary_conditions modifies the grid boundaries.
        # If boundaries are modified (Dirichlet/Neumann) directly on the grid,
        # then `np.roll` (periodic) is NOT appropriate for those axes.
        # We need `shift` that respects the "Edge" condition.
        
        # If we have parsed BCs for this axis, assume NOT periodic unless specified?
        # If no BCs for axis, default to Periodic?
        
        # Determine BC type for this axis
        ndim = u_in.ndim
        spatial_dims = len(self.space_axis)
        if ndim < spatial_dims: return np.roll(u_in, -step, axis=axis)
        space_idx = axis - (ndim - spatial_dims)
        
        is_periodic = True
        # Check parsed BCs for Dirichlet/Neumann on this axis
        # (This is slow, optimizable)
        if not self._parsed_bcs and self.boundry:
             self._parse_boundaries()
             
        for bc in self._parsed_bcs:
            if bc.get("axis") == space_idx and bc["type"] in ["dirichlet", "neumann"]:
                is_periodic = False
                break
        
        if is_periodic:
            return np.roll(u_in, -step, axis=axis)
        else:
            # Shift with edge padding (Clamping)
            # The actual values at boundary are set by _apply_boundary_conditions
            # So calculating derivatives at the boundary using clamped neighbors 
            # (or just simple neighbors) is standard.
            # E.g. derivative at boundary? Usually skipped or one-sided.
            # Central difference dx uses (i+1) and (i-1).
            # At i=0, uses i=1 and i=-1 (ghost).
            # By using Pad with Edge, i=-1 becomes i=0.
            # So dx(0) = (u[1] - u[0]) / 2dx. This is roughly one-sided.
            
            if step > 0:
                pad_width = [(0,0)] * ndim
                pad_width[axis] = (0, step)
                # mode='edge' repeats the updated boundary value
                padded = np.pad(u_in, pad_width, mode='edge')
                slices = [slice(None)] * ndim
                slices[axis] = slice(step, None)
                return padded[tuple(slices)]
            else:
                s = -step
                pad_width = [(0,0)] * ndim
                pad_width[axis] = (s, 0)
                padded = np.pad(u_in, pad_width, mode='edge')
                slices = [slice(None)] * ndim
                slices[axis] = slice(0, -s)
                return padded[tuple(slices)]

    def _build_eval_env(self) -> Dict[str, object]:
        grid_dx = self.grid_dx
        
        def _resolve_axis(u: np.ndarray, name: str) -> int:
            spatial_dims = len(self.space_axis)
            try:
                s_idx = self.space_axis.index(name)
                return (u.ndim - spatial_dims) + s_idx
            except ValueError:
                return -1

        def dx(u):
            ax = _resolve_axis(u, "x")
            if ax == -1: return np.zeros_like(u)
            return (self._get_neighbor(u, ax, 1) - self._get_neighbor(u, ax, -1)) / (2 * grid_dx)

        def dz(u):
            ax = _resolve_axis(u, "z")
            if ax == -1: return np.zeros_like(u)
            return (self._get_neighbor(u, ax, 1) - self._get_neighbor(u, ax, -1)) / (2 * grid_dx)
            
        def dy(u): 
            ax = _resolve_axis(u, "y")
            if ax == -1: return np.zeros_like(u)
            return (self._get_neighbor(u, ax, 1) - self._get_neighbor(u, ax, -1)) / (2 * grid_dx)

        def dxx(u):
            ax = _resolve_axis(u, "x")
            if ax == -1: return np.zeros_like(u)
            return (self._get_neighbor(u, ax, 1) - 2 * u + self._get_neighbor(u, ax, -1)) / (grid_dx ** 2)

        def dzz(u):
            ax = _resolve_axis(u, "z")
            if ax == -1: return np.zeros_like(u)
            return (self._get_neighbor(u, ax, 1) - 2 * u + self._get_neighbor(u, ax, -1)) / (grid_dx ** 2)

        def lap(u):
            val = np.zeros_like(u)
            spatial_dims = len(self.space_axis)
            base_axis = u.ndim - spatial_dims
            
            for i, axis_name in enumerate(self.space_axis):
                ax = base_axis + i
                d2 = (self._get_neighbor(u, ax, 1) - 2 * u + self._get_neighbor(u, ax, -1)) / (grid_dx ** 2)
                val += d2
            return val
            
        # ... (rest as before) ...
        def gradmag(u):
            val = np.zeros_like(u)
            spatial_dims = len(self.space_axis)
            base_axis = u.ndim - spatial_dims
            for i in enumerate(self.space_axis):
                ax = base_axis + i[0]
                d1 = (self._get_neighbor(u, ax, 1) - self._get_neighbor(u, ax, -1)) / (2 * grid_dx)
                val += d1**2
            return val
            
        def gradl1(u):
            val = np.zeros_like(u)
            spatial_dims = len(self.space_axis)
            base_axis = u.ndim - spatial_dims
            for i in enumerate(self.space_axis):
                ax = base_axis + i[0]
                d1 = (self._get_neighbor(u, ax, 1) - self._get_neighbor(u, ax, -1)) / (2 * grid_dx)
                val += np.abs(d1)
            return val

        def grad(u):
            comps = []
            spatial_dims = len(self.space_axis)
            base_axis = u.ndim - spatial_dims
            for i in enumerate(self.space_axis):
                ax = base_axis + i[0]
                d1 = (self._get_neighbor(u, ax, 1) - self._get_neighbor(u, ax, -1)) / (2 * grid_dx)
                comps.append(d1)
            return np.stack(comps, axis=0) 

        def div(v):
            val = 0.0
            spatial_dims = len(self.space_axis)
            def get_comp(idx):
                if isinstance(v, (list, tuple)): return v[idx]
                elif isinstance(v, np.ndarray): return v[idx]
                return None
            for i, axis_name in enumerate(self.space_axis):
                comp = get_comp(i)
                if comp is None: continue
                ax = (comp.ndim - spatial_dims) + i
                d1 = (self._get_neighbor(comp, ax, 1) - self._get_neighbor(comp, ax, -1)) / (2 * grid_dx)
                val += d1
            return val

        def advect(u_vel, f):
            val = np.zeros_like(f) if isinstance(f, np.ndarray) else 0.0
            spatial_dims = len(self.space_axis)
            
            f_is_vector = False
            f_comps = []
            if isinstance(f, (list, tuple)):
                f_is_vector = True
                f_comps = f
            elif isinstance(f, np.ndarray) and f.ndim > spatial_dims and f.shape[0] == len(self.u_shape): 
                f_is_vector = True
                f_comps = [f[k] for k in range(f.shape[0])]
            else:
                f_comps = [f]

            res_comps = [np.zeros_like(fc) for fc in f_comps]

            for i, axis_name in enumerate(self.space_axis):
                vel_comp = u_vel[i] if (isinstance(u_vel, (list, tuple, np.ndarray)) and len(u_vel) > i) else 0
                ax = (f_comps[0].ndim - spatial_dims) + i
                
                for k, fc in enumerate(f_comps):
                     df_di = (self._get_neighbor(fc, ax, 1) - self._get_neighbor(fc, ax, -1)) / (2 * grid_dx)
                     res_comps[k] += vel_comp * df_di
            
            if f_is_vector:
                if isinstance(f, (list, tuple)): return tuple(res_comps)
                else: return np.stack(res_comps, axis=0)
            else:
                return res_comps[0]

        def pos(u): return np.maximum(u, 0.0)
        def sech(u): return 1.0 / np.cosh(u)
        def sign(u): return np.sign(u)

        env = {
            "np": np,
            "sin": np.sin, "cos": np.cos, "tan": np.tan,
            "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
            "arcsin": np.arcsin, "arccos": np.arccos, "arctan": np.arctan,
            "log": np.log, "log10": np.log10, "log2": np.log2,
            "exp": np.exp, "sqrt": np.sqrt, "abs": np.abs,
            "pi": np.pi, "inf": np.inf,
            "lap": lap,
            "dx": dx, "dz": dz, "dy": dy, 
            "dxx": dxx, "dzz": dzz,
            "gradmag": gradmag, "gradl1": gradl1,
            "grad": grad, "div": div, "advect": advect,
            "pos": pos, "sech": sech, "sign": sign,
        }
        
        env.update(self.external_variables)
        
        if "t" not in env:
            env["t"] = 0.0
            
        if self.u.size > 0:
            shape = self.u.shape
            spatial_dims = len(self.space_axis)
            grid_shape = shape[-spatial_dims:]
            
            # Generalize coordinate generation
            coords = []
            for i, axis_len in enumerate(grid_shape):
                coords.append(np.arange(axis_len) * grid_dx)
                
            if len(coords) > 1:
                # Use indexing='ij' for matrix indexing (y, x) style 
                # OR 'xy' for Cartesian?
                # init_grid dims are appended in order of space_axis.
                # if space_axis=['z', 'x'], dim0 is z, dim1 is x.
                # We want Meshgrid to return Z, X arrays matching that shape.
                # np.meshgrid(z_ax, x_ax, indexing='ij') returns (Z, X) where Z[i,j] = z_ax[i].
                grids = np.meshgrid(*coords, indexing='ij')
            else:
                grids = [coords[0]]
                
            for i, axis_name in enumerate(self.space_axis):
                env[axis_name] = grids[i]
        
        return env

    def evaluate_rhs(self, rhs_expr: str, env: Dict[str, Any]) -> np.ndarray:
        rhs_expr = _preprocess_expr(rhs_expr)
        return eval(rhs_expr, {}, env)

    def evaluate_scalar(self, expr: str, env: Dict[str, Any]) -> float:
        if expr in ("", "1"): return 1.0
        val = self.evaluate_rhs(expr, env)
        if np.isscalar(val): return float(val)
        return float(np.mean(val))

    def step(self, dt: float):
        var_name, order, coeff_expr, rhs_expr = parse_pde(self.equation)
        
        self.time += dt # Update internally managed time
        
        env = self._build_eval_env()
        env["t"] = self.time # use current time
        
        # Inject u components
        if len(self.u_shape) == 1:
            name = self.u_shape[0]
            env[name] = self.u
            # Inject time derivative if exists (or zero)
            v_t = self._u_t if self._u_t is not None else np.zeros_like(self.u)
            env[f"{name}_t"] = v_t
        else:
            for i, name in enumerate(self.u_shape):
                env[name] = self.u[i]
                v_t = self._u_t[i] if self._u_t is not None else np.zeros_like(self.u[i])
                env[f"{name}_t"] = v_t
            env["u"] = self.u
            env["u_t"] = self._u_t if self._u_t is not None else np.zeros_like(self.u)

        try:
            rhs = self.evaluate_rhs(rhs_expr, env)
            if isinstance(rhs, list):
                rhs = np.array(rhs)
            
            coeff = self.evaluate_scalar(coeff_expr, env)
            
            target_indices = []
            if var_name == "u" and len(self.u_shape) == 1:
                target_indices = [None] 
            elif var_name in self.u_shape:
                idx = self.u_shape.index(var_name)
                target_indices = [idx]
            elif var_name == "u" and len(self.u_shape) > 1:
                target_indices = range(len(self.u_shape))
            
            forcing = rhs / (coeff if coeff else 1.0)
            
            # Apply Time Update
            if order == 2:
                if self._u_t is None: self._u_t = np.zeros_like(self.u)
                
                if var_name == "u" and len(self.u_shape) > 1:
                     self._u_t += dt * forcing
                     self.u += dt * self._u_t
                elif len(target_indices) == 1:
                     idx = target_indices[0]
                     target_u = self.u if idx is None else self.u[idx]
                     target_ut = self._u_t if idx is None else self._u_t[idx]
                     target_ut[:] += dt * forcing
                     target_u[:] += dt * target_ut
            else:
                if var_name == "u" and len(self.u_shape) > 1:
                     self.u += dt * forcing
                elif len(target_indices) == 1:
                     idx = target_indices[0]
                     if idx is None:
                         self.u += dt * forcing
                     else:
                         self.u[idx] += dt * forcing
            
            # Apply Boundary Conditions
            self._apply_boundary_conditions()
                         
        except Exception as e:
            print(f"Error stepping PDE: {e}")
            raise e

    def to_json(self) -> str:
        return json.dumps({
            "equation": self.equation,
            "desc": self.desc,
            "u_shape": self.u_shape,
            "space_axis": self.space_axis,
            "boundry": self.boundry,
            "constants": self.external_variables,
            "grid_dx": self.grid_dx,
            "time": self.time
        }, indent=2)

    def __str__(self):
        return self.to_json()


# Legacy wrappers 
def init_grid(width: int, height: int, dx: float) -> Tuple[np.ndarray, float]:
    p = PDE(space_axis=["z", "x"])
    p.init_grid(width, height, dx=dx)
    return p.u, dx

def step_pdes(
    field_pdes: List[str],
    grids: Dict[str, np.ndarray],
    constants: Dict[str, float],
    grid_dx: float,
    dt: float,
    external_grids: Dict[str, np.ndarray] | None = None,
) -> List[str]:
    errors = []
    full_grids = dict(grids)
    if external_grids:
        full_grids.update(external_grids)
        
    for i, eq in enumerate(field_pdes):
        try:
            p = PDE(equation=eq, space_axis=["z", "x"])
            p.grid_dx = grid_dx
            p.external_variables = constants.copy()
            p.external_variables.update({k: v for k,v in full_grids.items() if k not in constants})
            
            var, order, _, rhs_expr = parse_pde(eq)
            env = p._build_eval_env() 
            env.update(full_grids)
            env["t"] = constants.get("t", 0.0)
            
            rhs = p.evaluate_rhs(rhs_expr, env)
            forcing = rhs 
            
            val = grids.get(var)
            if val is None:
                 grids[var] = np.zeros_like(next(iter(grids.values())))
                 val = grids[var]

            if order == 2:
                 v_t_name = f"{var}_t"
                 if v_t_name not in grids: grids[v_t_name] = np.zeros_like(val)
                 grids[v_t_name] += dt * forcing
                 grids[var] += dt * grids[v_t_name]
            else:
                 grids[var] += dt * forcing
                 
        except Exception as exc:
            errors.append(f"Error {exc}")
            
    return errors
