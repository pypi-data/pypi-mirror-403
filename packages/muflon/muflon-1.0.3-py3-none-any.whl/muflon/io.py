import pandas as pd
import numpy as np
import os

def parse_data_to_matrices(df_subset):
    """
    Takes a pandas DataFrame subset where cells are strings of tuples
    (e.g., '(0.5, 0.2)' or '0.5, 0.2').
    Returns two separate matrices:
    1. Matrix Mu (First element)
    2. Matrix Nu (Second element)
    """
    if df_subset.empty:
        return None, None

    raw_strings = df_subset.to_numpy(dtype=str)

    def parse_cell(cell):
        s = str(cell).strip()
        s = s.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
        s = s.replace(' ', '')

        parts = s.split(',')

        try:
            v1 = float(parts[0])
            v2 = float(parts[1]) if len(parts) > 1 else 0.0
            return (v1, v2)
        except ValueError:
            return (0.0, 0.0)

    v_parse = np.vectorize(parse_cell, otypes=[object])
    matrix_tuples = v_parse(raw_strings)

    matrix_mu = np.vectorize(lambda x: x[0], otypes=[float])(matrix_tuples)
    matrix_nu = np.vectorize(lambda x: x[1], otypes=[float])(matrix_tuples)

    return matrix_mu, matrix_nu


def save_results_to_csv(mu_matrix, nu_matrix, filename="Result.csv"):
    """
    Saves the results into two separate files based on the provided filename.
    Example: if filename="Output.csv", it saves "Output_Mu.csv" and "Output_Nu.csv".
    """

    base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".csv"

    file_mu = f"{base}_Mu{ext}"
    pd.DataFrame(mu_matrix).to_csv(file_mu, sep=';', index=False, header=False)
    print(f"Saved Mu: {file_mu}")

    file_nu = f"{base}_Nu{ext}"
    pd.DataFrame(nu_matrix).to_csv(file_nu, sep=';', index=False, header=False)
    print(f"Saved Nu: {file_nu}")