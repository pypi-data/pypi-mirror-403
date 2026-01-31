"""
基本使用示例 / Basic Usage Example
"""

from balance_rxns import balance_rxns


def example1():
    """示例1: 铁的氧化反应"""
    print("=== 示例1: 铁的氧化反应 ===")
    reactants = ("Fe", "O2")
    products = ("FeO", "Fe2O3", "Fe3O4")
    
    results = balance_rxns(reactants, products)
    
    for equation, r_map, p_map in results:
        print(f"方程式: {equation}")
        print(f"  反应物系数: {r_map}")
        print(f"  产物系数: {p_map}")
        print()


def example2():
    """示例2: 铜和氧化铝反应"""
    print("=== 示例2: 铜和氧化铝反应 ===")
    reactants = ["Cu", "Al2O3"]
    products = ["CuAlO2"]
    
    results = balance_rxns(reactants, products)
    
    for equation, r_map, p_map in results:
        print(f"方程式: {equation}")
        print(f"  反应物系数: {r_map}")
        print(f"  产物系数: {p_map}")
        print()


def example3():
    """示例3: 使用高级选项"""
    print("=== 示例3: 限制产物数量 ===")
    reactants = ("Fe", "O2")
    products = ("FeO", "Fe2O3", "Fe3O4", "O3")
    
    # 限制每个方程式最多使用2个产物
    results = balance_rxns(
        reactants, 
        products,
        max_products_in_equation=2
    )
    
    for equation, r_map, p_map in results:
        print(f"方程式: {equation}")
        print()


if __name__ == "__main__":
    example1()
    example2()
    example3()
