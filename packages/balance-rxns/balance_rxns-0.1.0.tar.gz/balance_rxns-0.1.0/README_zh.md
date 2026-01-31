# balance-rxns

一个用于平衡化学方程式和寻找可能反应的 Python 包。

[English Documentation](README.md)

## 安装

```bash
pip install balance-rxns
```

## 功能特性

- 自动平衡化学方程式
- 从给定的反应物和产物中寻找所有可能的化学反应
- 支持复杂的化学配方
- 基于 sympy 和 pymatgen 的精确计算

## 使用方法

### 基本用法

```python
from balance_rxns import balance_rxns

# 定义反应物和产物
reactants = ("Fe", "O2")
products = ("FeO", "Fe2O3", "Fe3O4")

# 寻找所有可能的平衡方程式
results = balance_rxns(reactants, products)

# 打印结果
for equation, reactant_coeffs, product_coeffs in results:
    print(equation)
```

输出示例：
```
2Fe + O2 -> 2FeO
4Fe + 3O2 -> 2Fe2O3
3Fe + 2O2 -> Fe3O4
```

### 高级选项

```python
# 限制产物数量
results = balance_rxns(
    reactants=["Cu", "Al2O3"],
    products=["CuAlO2"],
    max_products_in_equation=2,  # 每个方程式最多2个产物
    require_all_reactants_used=True  # 要求所有反应物都被使用
)

for equation, r_map, p_map in results:
    print(f"方程式: {equation}")
    print(f"反应物系数: {r_map}")
    print(f"产物系数: {p_map}")
    print()
```

## 参数说明

- `reactants`: 反应物化学式列表或元组
- `products`: 产物化学式列表或元组
- `max_products_in_equation`: 每个方程式中最多的产物数量（默认：所有）
- `require_all_reactants_used`: 是否要求所有反应物都被使用（默认：True）

## 返回值

返回一个列表，每个元素包含：
1. 字符串形式的平衡方程式
2. 反应物及其系数的字典
3. 产物及其系数的字典

## 示例代码

更多使用示例请参考 `examples/basic_usage.py` 文件。

### 示例 1: 铁的氧化反应

```python
from balance_rxns import balance_rxns

reactants = ("Fe", "O2")
products = ("FeO", "Fe2O3", "Fe3O4")

results = balance_rxns(reactants, products)

for equation, r_map, p_map in results:
    print(f"方程式: {equation}")
    print(f"反应物: {r_map}")
    print(f"产物: {p_map}")
    print()
```

### 示例 2: 铜和氧化铝反应

```python
from balance_rxns import balance_rxns

reactants = ["Cu", "Al2O3"]
products = ["CuAlO2"]

results = balance_rxns(reactants, products)

for equation, r_map, p_map in results:
    print(equation)
```

## 依赖项

- pymatgen >= 2024.1.0
- sympy >= 1.12.0

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

如果你在使用过程中遇到任何问题，或者有改进建议，请随时在 GitHub 上提出。

## 更新日志

### 0.1.0 (2026-01-30)
- 初始版本发布
- 支持化学方程式平衡功能
- 支持查找所有可能的反应
- 提供中英文文档

## 开发

如果你想参与开发或修改代码：

1. 克隆仓库
```bash
git clone https://github.com/yourusername/balance-rxns.git
cd balance-rxns
```

2. 安装开发依赖
```bash
pip install -e .
```

3. 运行示例
```bash
python examples/basic_usage.py
```

## 致谢

本项目基于以下优秀的开源项目：
- [pymatgen](https://pymatgen.org/) - 材料科学计算框架
- [sympy](https://www.sympy.org/) - 符号数学库

## 相关资源

- [PyPI 页面](https://pypi.org/project/balance-rxns/)
- [GitHub 仓库](https://github.com/yourusername/balance-rxns)
- [发布指南](PUBLISHING.md)
