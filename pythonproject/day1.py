class Car:
    kpl = 200          # 类属性（默认值）
    make = "Ford"      # 类属性（默认品牌）
    model = "Mustang"  # 类属性（默认型号）
    year = 2020        # 类属性（默认年份）

    def __init__(self, make=None, model=None, year=None, kpl=None, color="Black"):
        # 如果未传入，则使用类属性的值
        self.make = make if make is not None else Car.make
        self.model = model if model is not None else Car.model
        self.year = year if year is not None else Car.year
        self.kpl = kpl if kpl is not None else Car.kpl
        self.color = color

# 无参数创建：使用所有类默认值
car1 = Car()
print(car1.make)   # Ford
print(car1.model)  # Mustang
print(car1.year)   # 2020
print(car1.kpl)    # 200（类默认）
print(car1.color)  # Black
print("______________________________")

# 有参数创建：传入部分或全部参数
car2 = Car("ckl", "lpl", 2025, kpl=10, color="df")
print(car2.make)   # ckl
print(car2.model)  # lpl
print(car2.year)   # 2025
print(car2.kpl)    # 10
print(car2.color)  # df
print("------------------------------")
#类方法
class Person:
    # 类属性：所有实例共享，记录总人数
    total = 0

    def __init__(self, name):
        self.name = name
        Person.total += 1  # 每创建一个实例，总人数+1

    # 类方法：操作类属性
    @classmethod
    def show_total(cls):
        print(f"总人数：{cls.total}")  # cls.total 等价于 Person.total


# 创建实例
p1 = Person("Alice")
p2 = Person("Bob")

# 访问类属性
print(Person.total)  # 输出：2（通过类名访问）
print(p1.total)      # 输出：2（通过实例访问，不推荐）

# 调用类方法
Person.show_total()  # 输出：总人数：2
print("-------------------------------")
class MathUtils:
    @staticmethod
    def add(a, b):  # 无self/cls参数
        return a + b

    @staticmethod
    def multiply(a, b):
        return a * b

# 调用静态方法（通过类名或实例）
print(MathUtils.add(2, 3))      # 输出：5
print(MathUtils.multiply(2, 3)) # 输出：6
print("------------------------------")
class BankAccount:
    def __init__(self, balance):
        self.__balance = balance  # 双下划线：伪私有属性（余额不希望被直接修改）

    # 暴露公开接口：查询余额
    def get_balance(self):
        return self.__balance

    # 暴露公开接口：存款
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            print(f"存款{amount}元，当前余额：{self.__balance}")

    # 私有方法：内部校验（不暴露）
    def __check_amount(self, amount):
        return amount > 0


account = BankAccount(1000)

# 不能直接访问__balance（会报错）
# print(account.__balance)  # AttributeError: 'BankAccount' object has no attribute '__balance'

# 通过公开接口访问
print(account.get_balance())  # 输出：1000
account.deposit(500)          # 输出：存款500元，当前余额：1500

# 强制访问（不推荐）：名称修饰后实际为 _BankAccount__balance
print(account._BankAccount__balance)  # 输出：1500
print("项目代码")