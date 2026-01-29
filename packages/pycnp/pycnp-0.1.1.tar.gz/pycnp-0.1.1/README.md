# PyCNP: An Open-Source Python Package for Critical Node Detection Problems

[![PyPI version](https://img.shields.io/pypi/v/pycnp?style=flat-square&label=PyPI)](https://pypi.org/project/pycnp/)
[![CI](https://img.shields.io/github/actions/workflow/status/xuebo100/PyCNP/.github%2Fworkflows%2Fci.yml?branch=main&style=flat-square&logo=github&label=CI)](https://github.com/xuebo100/PyCNP/actions/workflows/ci.yml)
[![Documentation](https://img.shields.io/github/actions/workflow/status/xuebo100/PyCNP/.github%2Fworkflows%2FDOC.yml?branch=main&style=flat-square&logo=github&label=DOC)](https://xuebo100.github.io/PyCNP/)

PyCNP is an open-source, high-performance Python solver for the Critical Node Problem (CNP) and Distance-based Critical Node Problem (DCNP).

The Critical Node Problem asks: which nodes should be removed from a network to minimize its connectivity while respecting a budget constraint? This problem has applications in:

- **Network security** - Identifying critical infrastructure nodes whose removal would most disrupt a network
- **Epidemiology** - Modeling disease spread by removing highly connected individuals (vaccination strategies)
- **Social network analysis** - Understanding information flow by identifying influential nodes
- **Biological networks** - Identifying critical proteins or genes in protein-protein interaction networks

PyCNP currently supports:

- **Critical Node Problem (CNP)** - Minimize pairwise connectivity in undirected graphs
- **Distance-based Critical Node Problem (DCNP)** - CNP variant with hop distance constraints
- **Multiple search strategies** - CBNS, CHNS, DLAS, and BCLS
- **Multiple crossover operators** - DBX, IRR, and RSC

The package provides a flexible Python interface backed by efficient C++ implementations.

## Installation

PyCNP can be installed via pip:

```bash
pip install pycnp
```

To install the latest version from source:

```bash
pip install 'pycnp @ git+https://github.com/xuebo100/PyCNP'
```

For development installation:

```bash
git clone https://github.com/xuebo100/PyCNP.git
cd PyCNP
pip install -e .
```

See the [installation guide](https://xuebo100.github.io/PyCNP/setup/installation.html) for detailed requirements and instructions.

## Quick Start

```python
import pycnp

# Create a model and add nodes/edges
model = pycnp.Model()
for i in range(10):
    model.add_node(i)
model.add_edge(0, 1)
model.add_edge(1, 2)
model.add_edge(2, 3)

# Solve the problem
result = model.solve(
    problem_type="CNP",
    budget=3,
    stopping_criterion=pycnp.MaxRuntime(60),
    seed=42
)

print(f"Best solution: {result.best_solution}")
print(f"Objective value: {result.best_obj_value}")
```

See the [examples](https://xuebo100.github.io/PyCNP/examples/) for a more comprehensive introduction.

## Key Features

### Problem Types

- **CNP (Critical Node Problem)**: The standard CNP on undirected graphs. The objective is to minimize pairwise connectivity by removing at most `budget` nodes.
- **DCNP (Distance-based Critical Node Problem)**: An extension that introduces a hop distance constraint. Two nodes are only considered connected if they are within the specified `hop_distance` of each other.

### Search Strategies

| Strategy | Description                                          | Best For                           |
|----------|------------------------------------------------------|------------------------------------|
| CBNS     | Component-Based Neighborhood Search                  | General CNP instances              |
| CHNS     | Component-Based Hybrid Neighborhood Search           | Balance of quality and speed       |
| DLAS     | Diversified Late Acceptance Search                   | When diversification is important  |
| BCLS     | Betweenness Centrality-based Late Acceptance Search  | DCNP problems                      |

### Crossover Operators or Problem Reduction

| Operator | Parents | Description                                                               |
|----------|---------|---------------------------------------------------------------------------|
| DBX      | 2       | Double Backbone Based Crossover - preserves common nodes between parents  |
| IRR      | 3       | Inherit-Repair-Recombination - designed for DCNP                          |
| RSC      | 2       | Reduce-Solve-Combine - can be used for both CNP and DCNP                  |

### Stopping Criteria

- `MaxIterations` - Stop after a fixed number of iterations
- `MaxRuntime` - Stop after a specified amount of time (seconds)
- `NoImprovement` - Stop if no improving solution is found

## Documentation

The full documentation is available at [https://xuebo100.github.io/PyCNP/](https://xuebo100.github.io/PyCNP/).

Key resources:

- [Introduction to CNP](https://xuebo100.github.io/PyCNP/setup/introduction_to_cnp.html) - Learn about the Critical Node Problem
- [Installation](https://xuebo100.github.io/PyCNP/setup/installation.html) - How to install PyCNP
- [Core Concepts](https://xuebo100.github.io/PyCNP/setup/concepts.html) - Understand PyCNP's components
- [Examples](https://xuebo100.github.io/PyCNP/examples/) - Step-by-step examples
- [API Reference](https://xuebo100.github.io/PyCNP/api/) - Detailed API documentation

## Getting Help

If you have questions or need help:

1. Browse [discussions](https://github.com/xuebo100/PyCNP/discussions)
2. Open a new [discussion thread](https://github.com/xuebo100/PyCNP/discussions/new) for questions
3. Open a [bug report](https://github.com/xuebo100/PyCNP/issues/new?template=bug_report.yml) for issues

When reporting bugs, please include:

- A minimal, reproducible example
- PyCNP version (run `python -c 'import pycnp; print(pycnp.__version__)'`)
- Python version and operating system
- Any error messages or tracebacks

## Contributing

Contributions are welcome! Please see our [contributing guide](https://xuebo100.github.io/PyCNP/dev/contributing.html) for details.

Before starting, please discuss changes in a GitHub issue first.

## How to Cite PyCNP

If you use PyCNP in your research, please cite the relevant papers:

```bibtex
@article{pycnp2026,
  title={PyCNP: An Open-Source Python Package for Critical Node Detection Problems},
  author={Yangming Zhou and Bo Xue and MengChu Zhou and Tieju Ma},
  year={2026},
}
```

## License

PyCNP is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
