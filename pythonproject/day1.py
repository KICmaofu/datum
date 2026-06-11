# =========== 基类 Spacecraft ===========
class Spacecraft:
    """
    航天器基类（定义所有航天器的通用属性和方法）
    体现了“类的抽象”：提取共有的属性（name, country, launch_year, description）
    """
    def __init__(self, name, country, launch_year, description):
        # 实例属性（每个对象拥有自己的值）
        self.name = name
        self.country = country
        self.launch_year = launch_year
        self.description = description

    def display_info(self):
        """
        多态接口：基类的默认实现
        子类可重写此方法以提供不同的显示内容
        """
        print(f"🚀 航天器：{self.name}")
        print(f"   国家：{self.country}")
        print(f"   发射年份：{self.launch_year}")
        print(f"   描述：{self.description}")
        print("-" * 40)

# =========== 子类：载人航天器 ===========
class MannedSpacecraft(Spacecraft):
    """
    载人航天器类（继承自 Spacecraft）
    体现了“继承”：子类自动拥有父类的所有属性和方法
    """
    def __init__(self, name, country, launch_year, description, crew_size):
        # 调用父类构造函数，复用共性属性的初始化
        super().__init__(name, country, launch_year, description)
        # 子类新增特有属性
        self.crew_size = crew_size

    def display_info(self):
        """
        重写父类方法（多态）
        在父类显示信息的基础上，增加载员数量的显示
        """
        super().display_info()               # 先调用父类的显示方法
        print(f"   载员数量：{self.crew_size} 人")

# =========== 子类：卫星 ===========
class Satellite(Spacecraft):
    """
    卫星类（继承自 Spacecraft）
    另一个子类，展示不同的特有属性
    """
    def __init__(self, name, country, launch_year, description, orbit_type):
        super().__init__(name, country, launch_year, description)
        self.orbit_type = orbit_type

    def display_info(self):
        """重写父类方法，增加轨道类型信息"""
        super().display_info()
        print(f"   轨道类型：{self.orbit_type}")

# =========== 数据库管理类 ===========
class SpacecraftDatabase:
    """
    航天器数据库类（负责存储和查询）
    体现了“封装”：内部使用私有字典 _spacecrafts 存储数据，对外只提供 add_spacecraft 和 query 接口
    """
    def __init__(self):
        # 私有字典（名称 -> 航天器对象），外部不能直接访问
        self._spacecrafts = {}

    def add_spacecraft(self, spacecraft):
        """向数据库中添加一个航天器对象"""
        self._spacecrafts[spacecraft.name] = spacecraft

    def query(self, name):
        """
        根据名称查询航天器
        这里体现了“多态”：无论对象是 MannedSpacecraft 还是 Satellite，
        都调用 display_info() 方法，但各自执行自己的版本
        """
        sc = self._spacecrafts.get(name)
        if sc:
            sc.display_info()   # 多态调用
        else:
            print(f"❌ 未找到“{name}”")

    def load_example_data(self):
        """加载一些示例数据，演示多态效果"""
        # 注意：这里混合创建了不同子类的对象
        examples = [
            MannedSpacecraft("神舟五号", "中国", 2003,
                             "中国首次载人航天飞行", 1),
            Satellite("哈勃太空望远镜", "美国/欧洲", 1990,
                      "著名的太空望远镜", "近地轨道"),
            MannedSpacecraft("阿波罗11号", "美国", 1969,
                             "人类首次登月", 3),
            Satellite("天和核心舱", "中国", 2021,
                      "中国空间站首个舱段", "近地轨道"),
        ]
        for s in examples:
            self.add_spacecraft(s)
        print(f"已加载 {len(examples)} 个航天器。\n")

# =========== 主程序入口 ===========
def main():
    """主函数：创建数据库实例，加载示例数据，进入用户交互循环"""
    db = SpacecraftDatabase()
    db.load_example_data()
    print("航天器查询系统（支持继承与多态）\n")

    while True:
        inp = input("请输入航天器名称（输入 q 退出）：").strip()
        if inp.lower() in ('q', 'quit', 'exit'):
            break
        db.query(inp)

if __name__ == "__main__":
    main()