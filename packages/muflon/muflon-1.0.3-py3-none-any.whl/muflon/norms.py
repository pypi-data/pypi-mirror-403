import numpy as np


# --- T-NORMS (Triangular Norms)


def t_M(x, y):
    """T_M: Minimum (eq. 2)"""
    return np.minimum(x, y)


def t_P(x, y):
    """T_P: Product (eq. 3)"""
    return x * y


def t_L(x, y):
    """T_L: Lukasiewicz t-norm (eq. 4)"""
    return np.maximum(0, x + y - 1)


def t_D(x, y):
    """T_D: Drastic product (eq. 5)"""

    return np.where(x == 1, y, np.where(y == 1, x, 0))


def t_FD(x, y):
    """T_FD: Fodor t-norm (eq. 6)"""

    return np.where(x + y <= 1, 0, np.minimum(x, y))


# --- S-CONORMS (Triangular Conorms)


def s_M(x, y):
    """S_M: Maximum (eq. 7)"""
    return np.maximum(x, y)


def s_P(x, y):
    """S_P: Probabilistic sum (eq. 8)"""
    return x + y - (x * y)


def s_L(x, y):
    """S_L: Lukasiewicz t-conorm (eq. 9)"""
    return np.minimum(1, x + y)


def s_D(x, y):
    """S_D: Drastic sum (eq. 10)"""

    return np.where(x == 0, y, np.where(y == 0, x, 1))


def s_FD(x, y):
    """S_FD: Fodor t-conorm (eq. 11)"""
    # 1 if x+y >= 1, else max(x,y)
    return np.where(x + y >= 1, 1, np.maximum(x, y))

# --- INDUCED IMPLICATIONS [cite: 157] ---

def i_TM(a, b):
    """Implication induced by T_M (Godel implication)"""

    return np.where(a <= b, 1.0, b)


def i_TP(a, b):
    """Implication induced by T_P (Goguen implication)"""

    with np.errstate(divide='ignore', invalid='ignore'):
        res = np.where(a <= b, 1.0, b / a)
        res = np.where(a == 0, 1.0, res)
    return res


def i_TL(a, b):
    """Implication induced by T_L (Lukasiewicz implication)"""

    return np.minimum(1, 1 - a + b)


def i_FP(a, b):
    """Implication induced by T_FP (Fodor implication)"""

    return np.where(a <= b, 1.0, np.maximum(1 - a, b))



NORM_MAP = {
    # T-Norms
    'T_M': t_M,  # Minimum
    'T_P': t_P,  # Product
    'T_L': t_L,  # Lukasiewicz
    'T_D': t_D,  # Drastic
    'T_FD': t_FD,  # Fodor

    # S-Conorms
    'S_M': s_M,  # Maximum
    'S_P': s_P,  # Probabilistic
    'S_L': s_L,  # Lukasiewicz
    'S_D': s_D,  # Drastic
    'S_FD': s_FD,  # Fodor

    # Implications
    'I_TM': i_TM,  # Induced by T_M
    'I_TP': i_TP,  # Induced by T_P
    'I_TL': i_TL,  # Induced by T_L
    'I_FP': i_FP  # Induced by T_FP (Fodor)
}


def get_norm(identifier):
    """Retrieves a function by the paper's notation string."""
    if callable(identifier):
        return identifier
    if isinstance(identifier, str):

        key = identifier.upper()

        if key == 'MIN': key = 'T_M'
        if key == 'MAX': key = 'S_M'

        if key in NORM_MAP:
            return NORM_MAP[key]

    raise ValueError(f"Norm '{identifier}' not found in registry. Please use paper notation (e.g., 'T_M', 'S_L').")