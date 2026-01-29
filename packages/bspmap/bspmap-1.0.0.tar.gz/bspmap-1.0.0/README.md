# bspmap - 高性能 B-Spline 映射库

bspmap 是一个利用 C++ 后端加速的 B-Spline 计算库，通过 Python 的 ctypes 库提供易用的接口。适用于需要高效执行 B-Spline 插值、映射和基函数计算的场景。

## 主要特性 (Features)

* **高性能**: 核心计算逻辑（如 Cox-de Boor 递归、基函数求导）由 C++ 实现，显著快于纯 Python 实现。
* **多维支持**: 支持任意维度的输入和输出空间映射。
* **灵活的 Python 接口**: 基于 `ctypes` 封装，提供直观的面向对象 API (`BSP`, `Basis`)。
* **跨平台**: 支持 Windows, Linux 和 macOS (需编译对应的动态库)。
* **张量积结构**: 自动处理多维基函数的张量积组合。

## 项目结构 (Structure)

```
bspmap/
├── src/
│   ├── cpp/                # C++ 核心源码
│   │   ├── include/        # 头文件 (.h)
│   │   └── src/            # 源文件 (.cpp)
│   └── python/             # Python 包源码
│       └── bspmap/
│           ├── __init__.py
│           ├── bsp.py      # B-Spline 映射类
│           ├── basis.py    # 基函数定义
│           └── capi.py     # Ctypes 绑定层
├── tests/                  # 测试用例
├── docs/                   # 文档
└── CMakeLists.txt          # CMake 构建配置
```

## 快速开始 (Quick Start)

### 1. 安装 (Installation)

由于本项目包含 C++ 扩展，建议通过源码编译安装。

详细步骤请参考 [安装指南](docs/installation.md)。

简述：

```bash
# 1. 编译 C++ 后端
mkdir build
cd build
cmake ..
cmake --build . --config Release

# 2. 将编译好的 bspmap.dll (或 libbspmap.so) 放入 src/python/bspmap/bin/

# 3. 安装 Python 包
cd ..
pip install -e .
```

### 2. 基本使用 (Usage)

创建一个简单的 2D -> 1D B-Spline 映射：

```python
import numpy as np
from bspmap import BSP, Basis

# 1. 定义每个维度的基函数 (Basis)
#    参数: 控制点数量 (num_cps), 阶数 (degree)
basis_x = Basis(num_cps=5, degree=2)
basis_y = Basis(num_cps=5, degree=2)

# 2. 准备控制点 (Control Points)
#    输入维度为2，每个维度大小为5，所以总共有 5x5=25 个控制点
#    输出维度假设为1
size = [5, 5]
# 随机生成控制点数据，形状 (25, 1) 或者展平
control_points = np.random.rand(25, 1)

# 3. 初始化 BSP 对象
bsp = BSP(
    basis=[basis_x, basis_y],
    size=size,
    control_points=control_points
)

# 4. 执行映射
#    输入数据 x 形状: (N, input_dim) -> (10, 2)
input_data = np.random.rand(10, 2)
output_data = bsp.map(input_data)

print("Input shape:", input_data.shape)
print("Output shape:", output_data.shape)
```

## 文档 (Documentation)

* [安装指南](docs/installation.md)
* [API 参考](docs/api.md)
* [开发指南](docs/development.md)
