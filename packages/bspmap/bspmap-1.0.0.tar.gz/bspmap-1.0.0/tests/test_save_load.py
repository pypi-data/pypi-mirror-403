"""
测试 BSP 保存和加载功能
"""
import numpy as np
import io
from bspmap import BSP, Basis, BasisClamped, BasisCircular

def test_save_load():
    """测试保存和加载功能"""
    # 创建一个简单的 BSP
    basis_x = Basis(num_cps=5, degree=2)
    basis_y = BasisClamped(num_cps=6, degree=2)
    
    size = [5, 6]
    control_points = np.random.rand(30, 3)  # 30个控制点，3维输出
    
    bsp_original = BSP(
        basis=[basis_x, basis_y],
        degree=2,
        size=size,
        control_points=control_points
    )
    
    # 测试映射
    test_input = np.random.rand(10, 2)
    output_original = bsp_original.map(test_input)
    
    # 保存到内存（BytesIO）
    buffer = io.BytesIO()
    bsp_original.save(buffer)
    
    # 获取文件大小
    buffer_size = buffer.tell()
    
    # 重置指针以便读取
    buffer.seek(0)
    
    # 加载
    bsp_loaded = BSP.load(buffer)
    
    # 验证
    output_loaded = bsp_loaded.map(test_input)
    
    print(f"原始 BSP - 输入维度: {bsp_original.input_dimension}, 输出维度: {bsp_original.output_dimension}")
    print(f"加载 BSP - 输入维度: {bsp_loaded.input_dimension}, 输出维度: {bsp_loaded.output_dimension}")
    print(f"Size 匹配: {bsp_original.size == bsp_loaded.size}")
    print(f"Degree 匹配: {bsp_original.degree == bsp_loaded.degree}")
    print(f"控制点匹配: {np.allclose(bsp_original.control_points, bsp_loaded.control_points)}")
    print(f"映射结果匹配: {np.allclose(output_original, output_loaded)}")
    print(f"内存占用: {buffer_size / 1024:.2f} KB")
    
    # 验证 basis 类型
    for i, (b_orig, b_load) in enumerate(zip(bsp_original._basis, bsp_loaded._basis)):
        print(f"Basis {i} - 类型匹配: {type(b_orig).__name__} == {type(b_load).__name__}")
        print(f"Basis {i} - Knots 匹配: {np.allclose(b_orig.knots, b_load.knots)}")

if __name__ == "__main__":
    test_save_load()
