import numpy as np
from scipy.optimize import linprog

# ================================
# Triangular Fuzzy Number (TFN)
# ================================

class TFN:
    def __init__(self, a, b, c):
        self.a, self.b, self.c = float(a), float(b), float(c)

    def membership(self, x):
        if x <= self.a or x >= self.c:
            return 0.0
        if self.a < x <= self.b:
            return (x - self.a) / (self.b - self.a)
        if self.b < x < self.c:
            return (self.c - x) / (self.c - self.b)
        return 0.0

    def support_points(self, n=11):
        return np.linspace(self.a, self.c, n)

    def __add__(self, other):
        return TFN(self.a + other.a, self.b + other.b, self.c + other.c)

    def __sub__(self, other):
        return TFN(self.a - other.c, self.b - other.b, self.c - other.a)

    def __mul__(self, other):
        vals = [self.a*other.a, self.a*other.c, self.c*other.a, self.c*other.c]
        return TFN(min(vals), self.b*other.b, max(vals))

    # ✅ SAFE (regularized) division
    def __truediv__(self, other, eps=1e-6):
        a, b, c = other.a, other.b, other.c
        if a <= 0 <= c:
            a += eps
            b += eps
            c += eps
        vals = [self.a/a, self.a/c, self.c/a, self.c/c]
        return TFN(min(vals), self.b/b, max(vals))

    def __repr__(self):
        return f"({self.a:.3f}, {self.b:.3f}, {self.c:.3f})"


# ================================
# LP solver for B-part
# ================================

def solve_lp(muA, target_b):
    n = len(muA)
    c = np.zeros(n)
    A_eq = np.vstack([np.ones(n), muA])
    b_eq = np.array([1.0, target_b])
    bounds = [(0, None)] * n
    res = linprog(c, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")
    if res.success:
        p = res.x
        p[p < 1e-12] = 0
        return p / p.sum()
    return None


# ================================
# Build B-part after operation
# ================================

def build_B(Z1_A, Z1_B, Z2_A, Z2_B, n_points=11, m_points=11, operation="+"):
    x1, x2 = Z1_A.support_points(n_points), Z2_A.support_points(n_points)
    muA1, muA2 = [Z1_A.membership(x) for x in x1], [Z2_A.membership(x) for x in x2]

    b1_vals = np.linspace(Z1_B.a, Z1_B.c, m_points)
    b2_vals = np.linspace(Z2_B.a, Z2_B.c, m_points)

    feasible1, feasible2 = [], []
    for b in b1_vals:
        p = solve_lp(muA1, b)
        if p is not None:
            feasible1.append((b, p, Z1_B.membership(b)))
    for b in b2_vals:
        p = solve_lp(muA2, b)
        if p is not None:
            feasible2.append((b, p, Z2_B.membership(b)))

    conv_results = []
    for b1, p1, mu1 in feasible1:
        for b2, p2, mu2 in feasible2:
            probs, sums = [], []
            for i in range(len(x1)):
                for j in range(len(x2)):
                    if operation == "+": sums.append(x1[i] + x2[j])
                    elif operation == "-": sums.append(x1[i] - x2[j])
                    elif operation == "*": sums.append(x1[i] * x2[j])
                    elif operation == "/":
                        if x2[j] == 0: continue
                        sums.append(x1[i] / x2[j])
                    probs.append(p1[i] * p2[j])

            if not sums:
                continue

            sums, probs = np.array(sums), np.array(probs)
            uniq, idx = np.unique(np.round(sums, 5), return_inverse=True)
            agg_probs = np.zeros(len(uniq))
            for k, pr in zip(idx, probs):
                agg_probs[k] += pr

            if operation == "+": A3 = Z1_A + Z2_A
            elif operation == "-": A3 = Z1_A - Z2_A
            elif operation == "*": A3 = Z1_A * Z2_A
            elif operation == "/": A3 = Z1_A / Z2_A

            muA3_vals = np.array([A3.membership(xx) for xx in uniq])
            P_A3 = float(np.dot(muA3_vals, agg_probs))
            conv_results.append((P_A3, min(mu1, mu2)))

    if len(conv_results) == 0:
        return TFN(0, 0, 0)

    P_vals = [r[0] for r in conv_results]
    mu_vals = [r[1] for r in conv_results]
    a, c = min(P_vals), max(P_vals)
    mode = P_vals[np.argmax(mu_vals)]
    return TFN(a, mode, c)


# ================================
# ZNumber
# ================================

class ZNumber:
    def __init__(self, A: TFN, B: TFN):
        self.A = A
        self.B = B

    def __add__(self, other):
        return ZNumber(self.A + other.A,
                       build_B(self.A, self.B, other.A, other.B, operation="+"))

    def __sub__(self, other):
        return ZNumber(self.A - other.A,
                       build_B(self.A, self.B, other.A, other.B, operation="-"))

    def __mul__(self, other):
        return ZNumber(self.A * other.A,
                       build_B(self.A, self.B, other.A, other.B, operation="*"))

    def __truediv__(self, other):
        return ZNumber(self.A / other.A,
                       build_B(self.A, self.B, other.A, other.B, operation="/"))

    def __repr__(self):
        return f"Z(A={self.A}, B={self.B})"


# ================================
# Z-number Gauss Solver (regularized)
# ================================

def solve_gauss_regularized(A, b, eps=1e-6):
    """
    Solve A x = b using Gauss elimination with regularized Z-number division.
    Suitable for 2x2 and 3x3 systems.
    """

    n = len(b)

    A = [[A[i][j] for j in range(n)] for i in range(n)]
    b = [b[i] for i in range(n)]

    for k in range(n):

        # regularize pivot
        if A[k][k].A.a <= 0 <= A[k][k].A.c:
            A[k][k] = ZNumber(
                TFN(A[k][k].A.a + eps, A[k][k].A.b + eps, A[k][k].A.c + eps),
                A[k][k].B
            )

        pivot = A[k][k]

        # normalize row
        for j in range(k, n):
            A[k][j] = A[k][j] / pivot
        b[k] = b[k] / pivot

        # eliminate below
        for i in range(k + 1, n):
            factor = A[i][k]
            for j in range(k, n):
                A[i][j] = A[i][j] - factor * A[k][j]
            b[i] = b[i] - factor * b[k]

    # back substitution
    x = [None] * n
    for i in range(n - 1, -1, -1):
        s = b[i]
        for j in range(i + 1, n):
            s = s - A[i][j] * x[j]
        x[i] = s

    return x


# ================================
# Fast TFN-only solver (approx)
# ================================

def solve_tfn_system(A, b):
    """
    Fast approximate solver using only TFN midpoints.
    Returns TFN solutions.
    """

    n = len(b)
    Am = np.zeros((n, n))
    bm = np.zeros(n)

    for i in range(n):
        bm[i] = b[i].A.b
        for j in range(n):
            Am[i, j] = A[i][j].A.b

    x_mid = np.linalg.solve(Am, bm)

    x = []
    for xi in x_mid:
        x.append(TFN(0.9 * xi, xi, 1.1 * xi))

    return x
