<img alt="logo.png" height="50" src="logo.png" width="50"/> 

# MUFLON: Matrix Utility for Fuzzy Logic Operations and Norms
Muflon is a Python library designed for processing Intuitionistic Fuzzy Values (IFVs). It handles complex matrix operations by automatically splitting data into two parallel streams:

Membership (μ): Processed via T-Norms.

Non-Membership (ν): Processed via S-Conorms.

## Installation

```pip install muflon```

## Core Concept: Tuple Processing
The system treats every data cell as a tuple $(i_1, i_2)$, representing:
1.  **Membership ($\mu$):** The first value ($i_1$).
2.  **Non-Membership ($\nu$):** The second value ($i_2$).

The script automatically splits these into two parallel calculation streams and produces **two distinct result matrices**:
* **Result 1:** Derived from the matrix of first numbers ($i_1, j_1, \dots$).
* **Result 2:** Derived from the matrix of second numbers ($i_2, j_2, \dots$).

## Data Format Requirements

Muflon is designed to work with CSV files where every cell represents a tuple ($\mu$,$\nu$).

| Feature | Separator | Example | Notes |
| :--- |:----------|:---|:---|
| **Column Separator** | `;` | `col1;col2;col3` | Standard CSV delimiter for this tool. |
| **Tuple Separator** | `,` | `0.3, 0.7` | **Crucial:** Used strictly to split $\mu$ and $\nu$ values inside a cell. |
| **Decimal Point** | `.` | `0.5` | Standard float notation. |

### CSV Structure Example (`Data.csv`)
```csv
0.3, 0.7; 0.2, 0.1; 0.5, 0.9
0.7, 0.4; 0.6, 0.2; 1.0, 0.5
```
Cell `0.3`, `0.7`: The tool parses `0.3` into the Mu Matrix and `0.7` into the Nu Matrix.

Empty Tuple Values: If a cell is just `0.5`, the second value defaults to `0.0`.

## Quick Start Guide

Here is a minimal script to load data, perform a standard Max-Min composition, and save the results.

```python
import numpy as np
from muflon.io import parse_data_to_matrices, save_results_to_csv
from muflon import fuzzy_composition, solve_vector
from muflon import get_norm

# Load Data
import pandas as pd

df = pd.read_csv('data.csv', sep=';', header=None)

# Parse into Mu and Nu Matrices
# The library automatically splits the tuples for you
matrix_mu, matrix_nu = parse_data_to_matrices(df)

# Perform Composition (C = A o B)
# Mu uses Minimum T-Norm
res_mu = fuzzy_composition(matrix_mu, matrix_mu, operator='min', aggregator=np.max)

# Nu uses Maximum S-Conorm
res_nu = fuzzy_composition(matrix_nu, matrix_nu, operator='max', aggregator=np.min)

# 4. Save Results
# Generates 'output_Mu.csv' and 'output_Nu.csv'
save_results_to_csv(res_mu, res_nu, "output.csv")
```

# Available Operators

| Type        | Code   | Alias           | Description |
|:------------|:-------|:----------------|:---|
| **T-Norms** | `T_M`  | `min`           | Minimum (Zadeh) |
|             | `T_P`  | `product`       | Algebraic Product |
|             | `T_L`  | `lukasiewicz`   | Bounded Difference |
| **S-Conorms** | `S_M`  | `max`           | Maximum |
|             | `S_P`  | `probabilistic` | Probabilistic Sum |
|             | `S_L`     | `bounded_sum`   | Bounded Sum |
| **Implications** | `I_TM`  |                 | Godel Implication |
|             | `I_TP`  |                 | Goguen Implication |
|             | `I_TL`     |            | Lukasiewicz Implication |

## 1. Perform Matrix Composition: Calculates $C = A \circ B$
### Reads columns 0-2 for Matrix A, and 0-1 for Matrix B


## 2. Solve System: Solves $A \circ x = b$ for separate $\mu$ and $\nu$
### Solves for vector x given Matrix A and Vector b
```python
# Assume we have Matrix A and Vector b loaded
A_mu, A_nu = parse_data_to_matrices(df_A)
b_mu, b_nu = parse_data_to_matrices(df_b)

# Solve for Mu using Godel Implication (Induced by Min)
x_mu = solve_fuzzy_vector(A_mu, b_mu, implication='I_TM', aggregator=np.min)

# Solve for Nu using Lukasiewicz Implication (Induced by Lukasiewicz T-Norm)
x_nu = solve_fuzzy_vector(A_nu, b_nu, implication='I_TL', aggregator=np.max)
```
## Core Concepts & Logic
### Dual Matrix Processing

This script splits every input matrix into two parallel streams based on the tuple data:

Mu Stream ($\mu$): Uses the first value of the tuple. Processed using T-norms (e.g., Minimum) and Max aggregation.

Nu Stream ($\nu$): Uses the second value of the tuple. Processed using S-conorms (e.g., Maximum) and Min aggregation.

### Column Scoping

Data loading is controlled by parameters in get_data_from_csv (called internally by the run functions):

`col_start`: Index of the first column to read.

`col_end`: Index of the column to stop at (exclusive).

`header_rows`: Number of top rows to skip (e.g., for labels).


### Configuration

You can define new fuzzy logic operators (T-norms, S-conorms, or Implications) in two ways:

### Option 1: The Quick Way (Script-Level)

If you are experimenting and don't want to modify the library code, you can simply define a Python function in your script and pass it directly to the composition engine.

The function must accept two arguments (`x`, `y`).

It must work with `NumPy` arrays (use `np.maximum`, `np.where`, etc., instead of standard `max` or if).

Example code:

```python
import numpy as np
from muflon import fuzzy_composition


# 1. Define your custom operator (e.g., Einstein Product)
def t_einstein(x, y):
    """Calculates (x * y) / (2 - (x + y - x*y))"""
    return (x * y) / (2 - (x + y - x * y))


# 2. Pass the function directly to the composition tool
result = fuzzy_composition(matrix_A, matrix_B, operator=t_einstein, aggregator=np.max)
```
### Option 2: The Permanent Way (Library-Level)

If you want your new operator to be part of the library (so you can call it via string like `T_EINSTEIN`), follow these steps:

Open `muflon/norms.py` Add your function definition at the end of the appropriate section (e.g., under T-NORMS).
```python
# In muflon/norms.py

def t_hamacher(x, y):
    """Hamacher Product (simplified parameter)"""
    numerator = x * y
    denominator = x + y - (x * y)
    # Avoid division by zero if both are 0
    return np.where(denominator == 0, 0, numerator / denominator)
```
Register it in NORM_MAP Scroll down to the NORM_MAP dictionary in the same file and add a key-value pair.

```python
NORM_MAP = {
    # ... previous norms ...
    'T_M': t_M,
    'T_P': t_P,
    
    # for clarity better to add new norms at the dictionary end:
    'T_HAMACHER': t_hamacher, 
}
```
Update get_norm (Optional but recommended) If you want to allow case-insensitive lookup (e.g., 'Hamacher'), add a quick alias in the get_norm function.

```python
def get_norm(identifier):
    # ... rest of function ...
    key = identifier.upper()
    
    # alias
    if key == 'HAMACHER': key = 'T_HAMACHER'
```
Now You can use your new string identifier anywhere in your project.

```python
from muflon import get_norm

res = fuzzy_composition(A, B, operator='T_HAMACHER', aggregator=np.max)
```
Example usage script for library:

```python
import numpy as np

from muflon.io import parse_data_to_matrices, save_results_to_csv
from muflon import fuzzy_composition_multi, solve_fuzzy_vector
from muflon import get_norm, NORM_MAP


def get_data_wrapper(filename, col_start, col_end, header_rows=0):
    """Wrapper to handle loading using your library's io module"""
    import pandas as pd
    try:
        df = pd.read_csv(filename, sep=';', header=None, skiprows=header_rows)
        df_subset = df.iloc[:, col_start:col_end]
        return parse_data_to_matrices(df_subset)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return None, None


def run_multiplication(file1, range1, header1, file2, range2, header2):
    print(f"\n=== RUNNING MODE: MULTIPLICATION ===")

    A_mu, A_nu = get_data_wrapper(file1, range1[0], range1[1], header_rows=header1)
    B_mu, B_nu = get_data_wrapper(file2, range2[0], range2[1], header_rows=header2)

    if A_mu is None: return

    t_norm = get_norm('T_M')  # Min
    s_conorm = get_norm('S_M')  # Max

    print("Computing Mu (First values)...")
    res_mu = fuzzy_composition_multi(A_mu, B_mu, [t_norm], np.max)

    print("Computing Nu (Second values)...")
    res_nu = fuzzy_composition_multi(A_nu, B_nu, [s_conorm], np.min)

    save_results_to_csv(res_mu, res_nu, "Result_Multiplication.csv")


def run_finding_vector(file_matrix, range_matrix, header_matrix, file_vector, range_vector, header_vector):
    print(f"\nRUNNING MODE: FINDING VECTOR")

    A_mu, A_nu = get_data_wrapper(file_matrix, range_matrix[0], range_matrix[1], header_matrix)
    b_mu, b_nu = get_data_wrapper(file_vector, range_vector[0], range_vector[1], header_vector)

    if A_mu is None: return

    # Use names defined in your NORM_MAP in norms.py
    imp_func_mu = get_norm('I_TM')
    imp_func_nu = get_norm('I_TL')

    print("Computing vector x for Mu...")
    res_x_mu = solve_fuzzy_vector(A_mu, b_mu, imp_func_mu, np.min)

    print("Computing vector x for Nu...")
    res_x_nu = solve_fuzzy_vector(A_nu, b_nu, imp_func_nu, np.max)

    save_results_to_csv(res_x_mu, res_x_nu, "Result_Vector.csv")


if __name__ == "__main__":
    try:
        '''
        run_multiplication(
            file1='Data1.csv', range1=(0, 2), header1=0,
            file2='Data2.csv', range2=(0, 1), header2=0
        )
        '''
        run_finding_vector(
            file_matrix='Data1.csv', range_matrix=(0, 2), header_matrix=0,
            file_vector='Data2.csv', range_vector=(0, 1), header_vector=0
        )
    except Exception as e:
        print(f"Execution failed: {e}")
```