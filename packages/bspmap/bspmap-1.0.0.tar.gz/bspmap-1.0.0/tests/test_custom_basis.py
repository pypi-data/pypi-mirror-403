"""
测试自定义 Basis 类型的自动注册
"""
import numpy as np
import tempfile
import os
from bspmap import BSP, Basis
from bspmap.basis import BasisFactory


class MyCustomBasis(Basis):
    """自定义的 Basis 类型，会自动注册到工厂"""
    def _build_knots(self, degree: int, num_cps: int) -> np.ndarray:
        # 自定义的节点向量构建逻辑
        knots = super()._build_knots(degree, num_cps)
        # 示例：稍微调整一下节点向量
        knots = knots * 0.9 + 0.05
        return knots


def test_custom_basis_auto_register():
    """测试自定义 Basis 是否自动注册"""
    
    # 检查是否已自动注册
    print("注册的 Basis 类型:", list(BasisFactory._registry.keys()))
    assert 'MyCustomBasis' in BasisFactory._registry, "自定义类型应该自动注册"
    
    # 创建使用自定义 Basis 的 BSP
    custom_basis = MyCustomBasis(num_cps=5, degree=2)
    basis_y = Basis(num_cps=6, degree=2)
    
    size = [5, 6]
    control_points = np.random.rand(30, 2)
    
    bsp_original = BSP(
        basis=[custom_basis, basis_y],
        degree=2,
        size=size,
        control_points=control_points
    )
    
    # 测试保存和加载
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "custom_bsp.npz")
        bsp_original.save(filepath)
        
        # 加载
        bsp_loaded = BSP.load(filepath)
        
        # 验证类型
        print(f"原始第一个 Basis 类型: {type(bsp_original._basis[0]).__name__}")
        print(f"加载第一个 Basis 类型: {type(bsp_loaded._basis[0]).__name__}")
        
        assert type(bsp_loaded._basis[0]).__name__ == 'MyCustomBasis', "应该正确加载自定义类型"
        
        # 验证 knots 匹配
        assert np.allclose(bsp_original._basis[0].knots, bsp_loaded._basis[0].knots), "Knots 应该匹配"
        
        print("✓ 自定义 Basis 自动注册测试通过！")


if __name__ == "__main__":
    test_custom_basis_auto_register()
