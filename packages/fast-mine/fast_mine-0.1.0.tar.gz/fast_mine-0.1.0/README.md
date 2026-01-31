# Fast-MINE

A Numba-accelerated Python implementation of MINE (Maximal Information-based Nonparametric Exploration) statistics, including MIC (Maximal Information Coefficient).

This package provides a drop-in replacement for the C-based `minepy` implementation, optimized for performance using JIT compilation via Numba.

The logic and algorithms in this package are derived from the original `minepy` implementation and the methodologies described in:

- **David N. Reshef, Yakir A. Reshef, Hilary K. Finucane, et al.** "Detecting Novel Associations in Large Data Sets." *Science* 334, 1518 (2011). DOI: [10.1126/science.1205438](https://doi.org/10.1126/science.1205438)
- **Davide Albanese, Michele Filosi, Roberto Visintainer, Samantha Riccadonna, Giuseppe Jurman, and Cesare Furlanello.** "minerva and minepy: a C engine for the MINE suite and its R, Python and MATLAB wrappers." *Bioinformatics* (2012). DOI: [10.1093/bioinformatics/bts707](https://doi.org/10.1093/bioinformatics/bts707)

This project respects the original work and aims to provide a pure Python implementation for broader compatibility and ease of use in modern Python environments without requiring C compilation.

## Features

- **High Performance:** Uses Numba to compile core algorithms to machine code, providing C-like performance.
- **Pure Python compatible:** Easy to install and modify.
- **Algorithms:**
  - **MIC (Maximal Information Coefficient)**: APPROX-MIC and MIC_e estimators.
  - **TIC (Total Information Coefficient)**
  - **GMIC (Generalized Mean Information Coefficient)**
  - **MAS (Maximum Asymmetry Score)**
  - **MEV (Maximum Edge Value)**
  - **MCN (Minimum Cell Number)**

## Installation

```bash
pip install .
```

## Usage

```python
import numpy as np
from fast_mine import mine_compute_score, MineParameter, MineProblem, mine_mic, EST_MIC_APPROX

# Generate data
x = np.linspace(0, 1, 100)
y = np.sin(10 * np.pi * x) + x

# Setup problem
prob = MineProblem(x=x, y=y, n=len(x))
param = MineParameter(alpha=0.6, c=15, est=EST_MIC_APPROX)

# Compute
score = mine_compute_score(prob, param)

# Get Statistics
print(f"MIC: {mine_mic(score)}")
```

## Attribution & Acknowledgements

### Example Datasets
Testing and verification for this library utilize datasets from the [example-causal-datasets](https://github.com/cmu-phil/example-causal-datasets) repository (CC0 1.0 Universal License).

We acknowledge the authors and contributors of the `example-causal-datasets` project for providing standardized real-world and synthetic datasets essential for benchmarking causal discovery and statistical association algorithms.

## License

Based on `minepy`, this project is licensed under the GPL-3.0 License. See the [LICENSE](LICENSE) file for details.
