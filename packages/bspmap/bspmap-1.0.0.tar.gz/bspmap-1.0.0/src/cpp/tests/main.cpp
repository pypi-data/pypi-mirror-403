#include <iostream>
#include <bspmap.h>
#include <vector>

int main() {
    std::cout << "=== BSPMAP Demo ===" << std::endl;
    std::cout << "Version: " << bspmap_get_version() << std::endl;
    
    // 简单测试
    std::vector<double> knots = {0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0};
    int num_nodes = 4;
    int degree = 2;
    
    std::cout << "\nTesting deboor_cox with:" << std::endl;
    std::cout << "  num_nodes: " << num_nodes << std::endl;
    std::cout << "  degree: " << degree << std::endl;
    
    // 分配结果数组
    int interval_size = num_nodes + degree;
    std::vector<double> result(interval_size * (degree + 1) * (degree + 1), 0.0);
    
    bspmap_deboor_cox(
        knots.data(),
        static_cast<int>(knots.size()),
        num_nodes,
        degree,
        result.data()
    );
    
    std::cout << "\nDeboor-Cox computation completed successfully!" << std::endl;
    std::cout << "Result array size: " << result.size() << std::endl;
    
    return 0;
}