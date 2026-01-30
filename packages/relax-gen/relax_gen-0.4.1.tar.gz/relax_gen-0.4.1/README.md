# 🧬 RelaxGEN: Genetic & Probabilistic Optimization Library

[![PyPI Version](https://img.shields.io/pypi/v/relax-gen?color=blue)](https://pypi.org/project/relax-gen/)
[![License](https://img.shields.io/github/license/LuisPablo54/relax_gen)](https://github.com/LuisPablo54/relax_gen/blob/main/LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/LuisPablo54/relax_gen)](https://github.com/LuisPablo54/relax_gen/commits/main/)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)]()

## 💡 What is RelaxGEN?

**RelaxGEN** is a modern, high-level **Python library** designed to make it easy to implement and experiment with **metaheuristic optimization algorithms**.

It provides a clean, unified API for several powerful paradigms:

1. **Classical Genetic Algorithms** — Binary encoding with standard operators (crossover, mutation, selection). Very robust when the problem structure is unknown.
2. **Quantum Genetic Algorithms (QGA)** — Probabilistic representation using **qubits**, enabling very fast search with minimal population size.
3. **Estimation of Distribution Algorithms (EDA)** — Advanced probabilistic modeling that captures variable dependencies — excellent for complex, epistatic problems.
4. **Genetic Programming (GP)** — Evolves executable hierarchical structures (trees), allowing automatic synthesis of mathematical expressions, programs or symbolic models.

> The main goal is to offer a **flexible, fast and user-friendly tool** for function optimization, hyperparameter tuning, and solving complex real-world problems.

## 🚀 Installation

The easiest way is via **pip**:

```bash
pip install relax-gen
```

## Quick Start Example

```bash
import numpy as np
from relax_gen import GEN

# ackley = 20 + e - 20 * exp(-0.2 * sqrt(0.5 * (x^2 + y^2))) - exp(0.5 * (cos(2 * pi * x) + cos(2 * pi * y)))
def ackley(valor, a=20, b=0.2, c=2*np.pi):
    x = valor[:,0]
    y = valor[:,1]

    term1 = -a * np.exp(-b * np.sqrt(0.5 * (x**2 + y**2)))
    term2 = -np.exp(0.5 * (np.cos(c * x) + np.cos(c * y)))
    return term1 + term2 + a + np.e

modelo = GEN(ackley, 
        population=300, 
        i_min=-2, 
        i_max=2,
        num_variables=2
        )

result = modelo.alg_stn_bin()
print("Best result:", result)
```

<img width="508" height="509" alt="Figure_1_Ackley" src="https://github.com/user-attachments/assets/91a584a0-2ea8-43e0-9168-f1023353e291" />


RelaxGEN lets you easily switch between different optimization models.
Parameter names and behavior adapt depending on the selected algorithm.

More information about the different functions can be found on the Wiki:
https://github.com/LuisPablo54/relax_gen/wiki

## Key Features

- Unified and intuitive high-level API
- Support for continuous, discrete and mixed problems
- Multiple state-of-the-art evolutionary paradigms in one package
- Designed for rapid prototyping and research experimentation
- Extensible — easy to add new algorithms or custom operators



## 🤝 Contributing
Contributions are very welcome!
Whether you want to:

- Add a new optimization algorithm
- Improve performance
- Enhance documentation
- Fix bugs
- Add new examples or benchmarks

Please follow these steps:

- Fork the repository
- Create your feature branch 
- Commit your changes 
- Push to the branch 
- Open a Pull Request

We appreciate every contribution

## 📄 License

This project is licensed under the MIT License — see the LICENSE file for details.


**Happy optimizing!**

Feel free to ⭐ the repository if you find it useful!


