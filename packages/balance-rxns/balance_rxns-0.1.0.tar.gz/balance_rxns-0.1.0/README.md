# balance-rxns

A Python package for balancing chemical equations and finding possible reactions.

[中文文档](README_zh.md)

## Installation

```bash
pip install balance-rxns
```

## Features

- Automatically balance chemical equations
- Find all possible reactions from given reactants and products
- Support for complex chemical formulas
- Accurate calculations based on sympy and pymatgen

## Usage

### Basic Usage

```python
from balance_rxns import balance_rxns

# Define reactants and products
reactants = ("Fe", "O2")
products = ("FeO", "Fe2O3", "Fe3O4")

# Find all possible balanced equations
results = balance_rxns(reactants, products)

# Print results
for equation, reactant_coeffs, product_coeffs in results:
    print(equation)
```

Output:
```
2Fe + O2 -> 2FeO
4Fe + 3O2 -> 2Fe2O3
3Fe + 2O2 -> Fe3O4
```

### Advanced Options

```python
# Limit the number of products
results = balance_rxns(
    reactants=["Cu", "Al2O3"],
    products=["CuAlO2"],
    max_products_in_equation=2,  # Maximum 2 products per equation
    require_all_reactants_used=True  # Require all reactants to be used
)

for equation, r_map, p_map in results:
    print(f"Equation: {equation}")
    print(f"Reactant coefficients: {r_map}")
    print(f"Product coefficients: {p_map}")
    print()
```

## Parameters

- `reactants`: List or tuple of reactant chemical formulas
- `products`: List or tuple of product chemical formulas
- `max_products_in_equation`: Maximum number of products in each equation (default: all)
- `require_all_reactants_used`: Whether all reactants must be used (default: True)

## Return Value

Returns a list where each element contains:
1. String representation of the balanced equation
2. Dictionary of reactants with their coefficients
3. Dictionary of products with their coefficients

## Dependencies

- pymatgen >= 2024.1.0
- sympy >= 1.12.0

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

## Changelog

### 0.1.0 (2026-01-30)
- Initial release
- Support for chemical equation balancing
