import numpy as np


def fuzzy_composition_multi(A, B, operator_list, aggregator_func):
    """
    Calculates [C] = [A] * [B]
    """
    rows_A, cols_A = A.shape
    rows_B, cols_B = B.shape

    if cols_A != rows_B:
        raise ValueError(f"Dimension mismatch: A columns ({cols_A}) != B rows ({rows_B})")

    result = np.zeros((rows_A, cols_B))

    for i in range(rows_A):
        for j in range(cols_B):
            row_from_a = A[i, :]
            col_from_b = B[:, j]
            combined = [
                operator_list[k % len(operator_list)](row_from_a[k], col_from_b[k])
                for k in range(cols_A)
            ]
            result[i, j] = aggregator_func(combined)

    return result


def solve_fuzzy_vector(A, b, impl_func, aggregator_func):
    """
    Finds vector x in equation: A * x = b
    Using Theorem 9: g_j = Aggregator_i( Implication(a_ij, b_i) )
    """
    rows_A, cols_A = A.shape
    rows_b = b.shape[0]

    if rows_A != rows_b:
        raise ValueError(f"Dimension mismatch: A rows ({rows_A}) != b rows ({rows_b})")

    x_result = np.zeros(cols_A)

    for j in range(cols_A):
        column_a = A[:, j]
        implications = impl_func(column_a, b.flatten())
        x_result[j] = aggregator_func(implications)

    return x_result.reshape(-1, 1)