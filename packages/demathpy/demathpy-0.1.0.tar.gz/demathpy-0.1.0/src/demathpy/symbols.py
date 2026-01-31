"""
Symbol normalization utilities for PDE parsing.
Converts Unicode math symbols and common LaTeX-like tokens to Python-callable forms.
"""
from __future__ import annotations

import re
from typing import Dict

SYMBOL_MAP: Dict[str, str] = {
    # Basic operators
    "−": "-",
    "×": "*",
    "·": "*",
    "÷": "/",
    "^": "**",
    "√": "sqrt",
    "∞": "inf",
    "π": "pi",
    "Π": "pi",
    "≈": "~",
    "≠": "!=",
    "≤": "<=",
    "≥": ">=",
    # Superscripts
    "²": "**2",
    "³": "**3",
    "⁴": "**4",
    "⁵": "**5",
    "⁶": "**6",
    "⁷": "**7",
    "⁸": "**8",
    "⁹": "**9",
    "⁰": "**0",
    "¹": "**1",
    "⁺": "POSITIVE_PART",
    # Subscripts
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    # Greek letters
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "ζ": "zeta",
    "η": "eta",
    "θ": "theta",
    "ι": "iota",
    "κ": "kappa",
    "λ": "lam",
    "μ": "mu",
    "ν": "nu",
    "ξ": "xi",
    "ο": "omicron",
    "π": "pi",
    "ρ": "rho",
    "σ": "sigma",
    "τ": "tau",
    "υ": "upsilon",
    "φ": "phi",
    "χ": "chi",
    "ψ": "psi",
    "ω": "omega",
    "Α": "alpha",
    "Β": "beta",
    "Γ": "gamma",
    "Δ": "delta",
    "Ε": "epsilon",
    "Ζ": "zeta",
    "Η": "eta",
    "Θ": "theta",
    "Ι": "iota",
    "Κ": "kappa",
    "Λ": "lam",
    "Μ": "mu",
    "Ν": "nu",
    "Ξ": "xi",
    "Ο": "omicron",
    "Π": "pi",
    "Ρ": "rho",
    "Σ": "sigma",
    "Τ": "tau",
    "Υ": "upsilon",
    "Φ": "phi",
    "Χ": "chi",
    "Ψ": "psi",
    "Ω": "omega",
    # Common math functions (unicode to ascii word if present)
    "∂": "",
    "Δ": "lap",
}

LHS_SYMBOL_MAP: Dict[str, str] = {
    # Keep ∂ intact for LHS parsing but normalize greek
    "α": "alpha",
    "β": "beta",
    "γ": "gamma",
    "δ": "delta",
    "ε": "epsilon",
    "ζ": "zeta",
    "η": "eta",
    "θ": "theta",
    "ι": "iota",
    "κ": "kappa",
    "λ": "lam",
    "μ": "mu",
    "ν": "nu",
    "ξ": "xi",
    "ο": "omicron",
    "π": "pi",
    "ρ": "rho",
    "σ": "sigma",
    "τ": "tau",
    "υ": "upsilon",
    "φ": "phi",
    "χ": "chi",
    "ψ": "psi",
    "ω": "omega",
    "Α": "alpha",
    "Β": "beta",
    "Γ": "gamma",
    "Δ": "delta",
    "Ε": "epsilon",
    "Ζ": "zeta",
    "Η": "eta",
    "Θ": "theta",
    "Ι": "iota",
    "Κ": "kappa",
    "Λ": "lam",
    "Μ": "mu",
    "Ν": "nu",
    "Ξ": "xi",
    "Ο": "omicron",
    "Π": "pi",
    "Ρ": "rho",
    "Σ": "sigma",
    "Τ": "tau",
    "Υ": "upsilon",
    "Φ": "phi",
    "Χ": "chi",
    "Ψ": "psi",
    "Ω": "omega",
    # Superscripts for LHS
    "²": "^2",
    "³": "^3",
    "⁴": "^4",
    "⁵": "^5",
    "⁶": "^6",
    "⁷": "^7",
    "⁸": "^8",
    "⁹": "^9",
}

# Regex replacements for structured operators
REGEX_RULES = [
    # divergence operator: ∇·u or ∇·(u)
    (r"∇\s*·\s*\(([^\)]*)\)", r"div(\1)"),
    (r"∇\s*·\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"div(\1)"),
    # divergence shorthand: ∇ * u or ∇ * (u)
    (r"∇\s*\*\s*\(([^\)]*)\)", r"div(\1)"),
    (r"∇\s*\*\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"div(\1)"),
    # advection operator: (u · ∇) v -> advect(u, v)
    # Match (u · ∇) or (u * ∇) followed by v or (v)
    # Handle both · (before replacement) and * (after replacement if regex runs late)?
    # actually SYMBOL_MAP runs later or earlier?
    # In normalize_symbols, SYMBOL_MAP runs BEFORE regex rules.
    # So · becomes *.
    # But wait, in code:
    # 1. replace greek
    # 2. replace ∇·, ∇(
    # 3. balanced paren calls
    # 4. SYMBOL_MAP replacement (· -> *)
    # 5. REGEX_RULES
    # So we only need to match * for dot product.
    
    # (u * ∇) v -> advect(u, v)
    (r"\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\*\s*∇\s*\)\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"advect(\1, \2)"),
    (r"\(\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\*\s*∇\s*\)\s*\(([^\)]*)\)", r"advect(\1, \2)"),

    # gradient: ∇(u)
    (r"∇\s*\(([^\)]*)\)", r"grad(\1)"),
    # gradient magnitude |∇u|^2
    (r"\|\s*∇\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\^?2", r"gradmag(\1)"),
    # Laplacian
    (r"∇²\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"lap(\1)"),
    # Gradient
    (r"∇\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"grad(\1)"),
]


def normalize_symbols(expr: str) -> str:
    if not expr:
        return ""

    # --- Helpers ---------------------------------------------------------
    def _replace_balanced_paren_call(s: str, start_idx: int, fn_name: str, op_len: int) -> tuple[str, int] | None:
        """Replace an operator call like '∇·( ... )' (possibly nested) with 'div( ... )'.

        Args:
            s: input string
            start_idx: index where the operator starts (the '∇')
            fn_name: replacement function name (e.g. 'div' or 'grad')
            op_len: number of characters to skip from start_idx to the '(' (inclusive of operator symbols)

        Returns:
            (new_string, next_scan_index) or None if no balanced paren call found.
        """
        # Find the '(' that starts the argument list
        i = start_idx + op_len
        while i < len(s) and s[i].isspace():
            i += 1
        if i >= len(s) or s[i] != "(":
            return None

        # Find matching ')'
        depth = 0
        j = i
        while j < len(s):
            ch = s[j]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    inner = s[i + 1 : j]
                    replaced = f"{fn_name}({inner})"
                    new_s = s[:start_idx] + replaced + s[j + 1 :]
                    return new_s, start_idx + len(replaced)
            j += 1
        return None

    # Normalize greek letters early so time-derivative regex can match
    greek_map = {
        "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
        "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
        "λ": "lam", "μ": "mu", "ν": "nu", "ξ": "xi", "ο": "omicron",
        "π": "pi", "ρ": "rho", "σ": "sigma", "τ": "tau", "υ": "upsilon",
        "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega",
        "Α": "alpha", "Β": "beta", "Γ": "gamma", "Δ": "delta", "Ε": "epsilon",
        "Ζ": "zeta", "Η": "eta", "Θ": "theta", "Ι": "iota", "Κ": "kappa",
        "Λ": "lam", "Μ": "mu", "Ν": "nu", "Ξ": "xi", "Ο": "omicron",
        "Π": "pi", "Ρ": "rho", "Σ": "sigma", "Τ": "tau", "Υ": "upsilon",
        "Φ": "phi", "Χ": "chi", "Ψ": "psi", "Ω": "omega",
    }
    for k, v in greek_map.items():
        expr = expr.replace(k, v)

    # Strip stray question marks sometimes added by LLM output
    expr = expr.replace("?", "")

    # Normalize common whitespace variants around nabla operators so we can
    # safely do balanced-parenthesis rewrites.
    expr = re.sub(r"∇\s*[·\*]\s*", "∇·", expr)
    expr = re.sub(r"∇\s*\(", "∇(", expr)

    # Balanced-parenthesis rewrites for divergence / gradient:
    #   ∇·( ... )  -> div( ... )   (handles nested parentheses)
    #   ∇( ... )   -> grad( ... )
    i = 0
    while i < len(expr):
        if expr.startswith("∇·", i):
            out = _replace_balanced_paren_call(expr, i, "div", op_len=2)
            if out is not None:
                expr, i = out
                continue
        if expr.startswith("∇(", i):
            out = _replace_balanced_paren_call(expr, i, "grad", op_len=1)
            if out is not None:
                expr, i = out
                continue
        i += 1

    # Remove primes like t' -> t
    expr = re.sub(r"([a-zA-Z_][a-zA-Z0-9_]*)'", r"\1", expr)

    # Normalize partial derivatives BEFORE stripping ∂
    # Time derivatives in RHS: ∂u/∂t -> u_t, ∂²u/∂t² -> u_tt
    expr = re.sub(r"∂\s*\^?2\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*/\s*∂t\s*\^?2", r"\1_tt", expr)
    expr = re.sub(r"∂\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*/\s*∂t", r"\1_t", expr)
    expr = re.sub(r"∂x\s*\(\s*∂x\s*\(([^\)]*)\)\s*\)", r"dxx(\1)", expr)
    expr = re.sub(r"∂z\s*\(\s*∂z\s*\(([^\)]*)\)\s*\)", r"dzz(\1)", expr)
    expr = re.sub(r"∂x\s*\(", "dx(", expr)
    expr = re.sub(r"∂z\s*\(", "dz(", expr)

    # Positive part: (x)⁺ or x⁺ -> pos(x)
    expr = re.sub(r"\(([^\)]+)\)\s*⁺", r"pos(\1)", expr)
    expr = re.sub(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*⁺", r"pos(\1)", expr)

    # Apply direct symbol replacement
    for k, v in SYMBOL_MAP.items():
        expr = expr.replace(k, v)

    # Fix concatenated greek-constant prefixes such as "alphasin(u)" or "betau**3".
    greek_words = (
        "alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lam|mu|nu|xi|"
        "omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega"
    )
    fn_words = "sin|cos|tan|sinh|cosh|tanh|exp|log|log10|log2|sqrt|abs|sech|sign"
    # Use word boundary \b to avoid matching inside words
    expr = re.sub(rf"\b({greek_words})(?=({fn_words})\b)", r"\1*", expr)
    # Greek word directly followed by a single-letter variable (e.g., beta u) or concatenated (betau).
    # BUT do not split axis-suffixed coefficients like alphax/alphaz (common in anisotropic diffusion terms).
    _axis_coeffs = {
        "alphax", "alphaz", "betax", "betaz", "gammax", "gammaz", "deltax", "deltaz",
        "sigmax", "sigmaz", "thetax", "thetaz", "kappax", "kappaz", "lambdax", "lambdaz",
        "rhox", "rhoz", "mux", "muz", "nux", "nuz",
        # Also protect eps/epsilon from being split
        "epsilon", "eps",
    }

    def _split_greek_letter_var(m: re.Match) -> str:
        greek = m.group(1)
        letter = m.group(2)
        combined = f"{greek}{letter}"
        # Don't split if this creates a known coefficient (e.g., alphax, sigmaz)
        if combined in _axis_coeffs:
            return combined
        # Don't split if combined is the start of a greek word (to avoid "epsi*lon" from "epsilon")
        # Check if any greek word starts with the combined string
        all_greek_words = {"alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta", 
                          "iota", "kappa", "lam", "mu", "nu", "xi", "omicron", "pi", "rho", 
                          "sigma", "tau", "upsilon", "phi", "chi", "psi", "omega"}
        for gw in all_greek_words:
            if gw.startswith(combined) and len(gw) > len(combined):
                # combined is a prefix of a longer greek word, so don't split
                return combined
        # Otherwise, insert multiplication: betau -> beta*u
        return f"{greek}*{letter}"

    # Only match at word boundaries to avoid splitting within words like 'epsilon'
    # Use lookahead to detect when a greek word is followed by a single letter that starts a new token
    expr = re.sub(rf"\b({greek_words})([A-Za-z])(?=([^a-zA-Z]|$))", _split_greek_letter_var, expr)

    # Absolute value for variables/parentheses
    expr = re.sub(r"\|\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|", r"abs(\1)", expr)
    expr = re.sub(r"\|\s*\(([^\)]*)\)\s*\|", r"abs(\1)", expr)

    # |∇u| -> sqrt(gradmag(u))
    expr = re.sub(r"\|\s*∇\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|", r"sqrt(gradmag(\1))", expr)

    # Catch-all for remaining absolute-value bars like |lap(u)|
    expr = re.sub(r"\|([^|]+)\|", r"abs(\1)", expr)

    # Apply regex-based transformations
    for pattern, repl in REGEX_RULES:
        expr = re.sub(pattern, repl, expr)

    # Handle ∇**2 and nested ∇**2
    prev = None
    while prev != expr:
        prev = expr
        expr = re.sub(r"∇\s*\*\*\s*2\s*\(([^\)]*)\)", r"lap(\1)", expr)
        expr = re.sub(r"∇\s*\*\*\s*2\s*([a-zA-Z_][a-zA-Z0-9_]*)", r"lap(\1)", expr)

    # Interpret ∇²u³ as lap(u**3)
    expr = re.sub(r"∇²\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\*\*\s*3", r"lap((\1)**3)", expr)
    expr = re.sub(r"∇²\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*³", r"lap((\1)**3)", expr)
    # If lap(u)**3 appears, interpret as lap(u**3)
    expr = re.sub(r"lap\(([^\)]+)\)\s*\*\*\s*3", r"lap((\1)**3)", expr)

    # Fix nested laplacian call pattern: lap(lap)(u) -> lap(lap(u))
    expr = re.sub(r"lap\(\s*lap\s*\)\s*\(([^\)]*)\)", r"lap(lap(\1))", expr)

    # Implicit multiplication: 2mu -> 2*mu, )u -> )*u, u( -> u*(
    # Avoid breaking scientific notation like 1e-9.
    expr = re.sub(r"(\d)\s*(?![eE][+-]?\d)([a-zA-Z_])", r"\1*\2", expr)
    expr = re.sub(r"(\d)\s*(\()", r"\1*\2", expr)
    expr = re.sub(r"(\))\s*([a-zA-Z_])", r"\1*\2", expr)
    # Symbol followed by operator function: eta lap(u) -> eta*lap(u)
    expr = re.sub(
        r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(lap|grad|div|dx|dz|dxx|dzz|pos|gradl1|gradmag)\s*\(",
        r"\1*\2(",
        expr,
    )

    # Fix accidental insertions like gradl1*(u) -> gradl1(u)
    expr = re.sub(r"\b(gradl1|gradmag|lap|dx|dz|dxx|dzz|grad|div|pos)\s*\*\s*\(", r"\1(", expr)
    # Avoid inserting * for known functions
    def _fn_mul(match):
        name = match.group(1)
        if name in {
            "sin", "cos", "tan",
            "sinh", "cosh", "tanh",
            "arcsin", "arccos", "arctan",
            "exp", "sqrt",
            "log", "log10", "log2",
            "abs", "sech", "sign",
            "lap", "dx", "dz", "dxx", "dzz", "grad", "div", "advect", "gradmag", "gradl1", "pos",
        }:
            return f"{name}("
        return f"{name}*("

    expr = re.sub(r"([a-zA-Z_][a-zA-Z0-9_]*)\(", _fn_mul, expr)

    return expr


def normalize_lhs(expr: str) -> str:
    if not expr:
        return ""
    for k, v in LHS_SYMBOL_MAP.items():
        expr = expr.replace(k, v)
    return expr
