"""
演示如何在内存中保存和管理多个 BSP 对象
"""
import numpy as np
import io
from bspmap import BSP, Basis, BasisClamped

# 方案 1: 使用字典管理多个 BytesIO 对象
def example_multiple_bsp_dict():
    """使用字典保存多个 BSP"""
    
    # 创建多个 BSP 对象
    bsp1 = BSP(
        basis=[Basis(5, 2), Basis(5, 2)],
        degree=2,
        size=[5, 5],
        control_points=np.random.rand(25, 3)
    )
    
    bsp2 = BSP(
        basis=[BasisClamped(6, 2), BasisClamped(6, 2)],
        degree=2,
        size=[6, 6],
        control_points=np.random.rand(36, 2)
    )
    # 保存到内存字典
    bsp_storage = {}
    
    for name, bsp in [("model_A", bsp1), ("model_B", bsp2)]:
        buffer = io.BytesIO()
        bsp.save(buffer)
        buffer.seek(0)  # 重置到开头，方便后续读取
        bsp_storage[name] = buffer
    
    print(f"已保存 {len(bsp_storage)} 个模型到内存")
    print(f"模型名称: {list(bsp_storage.keys())}")
    
    # 从内存加载
    loaded_bsp1 = BSP.load(bsp_storage["model_A"])
    loaded_bsp2 = BSP.load(bsp_storage["model_B"])
    
    print(f"model_A: 输入维度={loaded_bsp1.input_dimension}, 输出维度={loaded_bsp1.output_dimension}")
    print(f"model_B: 输入维度={loaded_bsp2.input_dimension}, 输出维度={loaded_bsp2.output_dimension}")
    
    # 获取内存占用
    total_size = sum(buf.getbuffer().nbytes for buf in bsp_storage.values())
    print(f"总内存占用: {total_size / 1024:.2f} KB")


# 方案 2: 创建一个 BSP 集合管理类
class BSPCollection:
    """管理多个 BSP 对象的集合"""
    
    def __init__(self):
        self._storage = {}
    
    def add(self, name: str, bsp: BSP):
        """添加 BSP 对象到集合"""
        buffer = io.BytesIO()
        bsp.save(buffer)
        buffer.seek(0)
        self._storage[name] = buffer
        print(f"已添加 '{name}' 到集合")
    
    def get(self, name: str) -> BSP:
        """从集合中获取 BSP 对象"""
        if name not in self._storage:
            raise KeyError(f"未找到名为 '{name}' 的 BSP")
        
        buffer = self._storage[name]
        buffer.seek(0)  # 确保从头读取
        return BSP.load(buffer)
    
    def list(self) -> list[str]:
        """列出所有已保存的 BSP 名称"""
        return list(self._storage.keys())
    
    def remove(self, name: str):
        """从集合中移除 BSP"""
        if name in self._storage:
            del self._storage[name]
            print(f"已移除 '{name}'")
    
    def memory_usage(self) -> dict[str, float]:
        """获取每个模型的内存占用（KB）"""
        return {
            name: buf.getbuffer().nbytes / 1024 
            for name, buf in self._storage.items()
        }
    
    def save_to_disk(self, directory: str):
        """批量保存到磁盘"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        for name, buffer in self._storage.items():
            filepath = os.path.join(directory, f"{name}.npz")
            buffer.seek(0)
            with open(filepath, 'wb') as f:
                f.write(buffer.read())
            print(f"已保存 '{name}' 到 {filepath}")


def example_bsp_collection():
    """使用 BSPCollection 管理多个 BSP"""
    
    collection = BSPCollection()
    
    # 添加多个 BSP
    for i in range(3):
        bsp = BSP(
            basis=[Basis(5, 2), Basis(5, 2)],
            degree=2,
            size=[5, 5],
            control_points=np.random.rand(25, 3)
        )
        collection.add(f"model_{i}", bsp)
    
    print(f"\n集合中的模型: {collection.list()}")
    print(f"内存占用: {collection.memory_usage()}")
    
    # 获取特定模型
    bsp = collection.get("model_1")
    print(f"\n加载 model_1: 输入维度={bsp.input_dimension}, 输出维度={bsp.output_dimension}")
    
    # 移除模型
    collection.remove("model_0")
    print(f"移除后的模型: {collection.list()}")


if __name__ == "__main__":
    print("=== 方案 1: 使用字典 ===")
    example_multiple_bsp_dict()
    
    print("\n" + "="*50)
    print("=== 方案 2: 使用 BSPCollection 类 ===")
    example_bsp_collection()
