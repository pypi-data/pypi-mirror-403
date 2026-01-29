import numpy as np
import bspmap

# print current process PID
import os

class TimeRecorder:
    def __init__(self, label: str = "Elapsed Time"):
        self.label = label

    def __enter__(self):
        import time
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        import time
        end_time = time.time()
        elapsed = end_time - self.start_time
        print(f"{self.label}: {elapsed:.6f} seconds")

print(f"Current PID: {os.getpid()}")
# input("Attach debugger and press Enter to continue...")

print(f"loaded dll path: {bspmap.capi._dll_path}")

# 获取版本
print(bspmap.get_version())

# 调试输出
bspmap.debug_print("testing")

# 计算 B-spline 基函数
knots = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0,], dtype=np.float64)
with TimeRecorder("Compute B-spline Basis Functions"):
    basis = bspmap.deboor_cox(knots, 4, 3)
    print("Basis Functions:")
    print(basis)

    basis_derivative = bspmap.basis_derivative(basis)
    print("Basis Derivative:")
    print(basis_derivative)
    print(basis.shape)


# 查找区间
x = np.arange(0.0, 4.0, 0.000001)
interval_index = bspmap.find_interval(knots, 3, x)
# print(f"Interval index for x={x}: {interval_index}")

# 计算权重
with TimeRecorder("Compute Weights"):
    weights, indices = bspmap.compute_weight(basis=basis, knot_vector=knots, x=x)
    print(weights)

    print_idx = np.random.randint(0, len(x), size=10)
    print(f"indices[print_idx]: {indices}")