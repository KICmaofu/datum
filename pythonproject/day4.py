class Student:
    def __init__(self, name="", student_id="", age=0, major=""):
        self.name = name
        self.student_id = student_id
        self.age = age
        self.major = major
        self.grades = {}

    def add_grade(self, course, grade):
        if 0 <= grade <= 150:
            self.grades[course] = grade
        else:
            print("成绩必须在0-100之间")

    def get_grade(self, course):
        return self.grades.get(course, "该课程没有成绩记录")

    def get_average_grade(self):
        if not self.grades:
            return 0
        return sum(self.grades.values()) / len(self.grades)

    def get_max_grade(self):
        if not self.grades:
            return "暂无成绩记录"
        max_course = max(self.grades, key=self.grades.get)
        return max_course, self.grades[max_course]

    def get_min_grade(self):
        if not self.grades:
            return "暂无成绩记录"
        min_course = min(self.grades, key=self.grades.get)
        return min_course, self.grades[min_course]

    def display_info(self):
        print(f"姓名: {self.name}")
        print(f"学号: {self.student_id}")
        print(f"年龄: {self.age}")
        print(f"专业: {self.major}")
        if self.grades:
            print("成绩:")
            for course, grade in self.grades.items():
                print(f"  {course}: {grade}")
            print(f"平均成绩: {self.get_average_grade():.2f}")
            max_course, max_grade = self.get_max_grade()
            print(f"最高成绩: {max_course} - {max_grade}")
            min_course, min_grade = self.get_min_grade()
            print(f"最低成绩: {min_course} - {min_grade}")
        else:
            print("暂无成绩记录")

    def __str__(self):
        return f"Student(name='{self.name}', student_id='{self.student_id}', age={self.age}, major='{self.major}')"


if __name__ == "__main__":
    student1 = Student("卯富", "2023001", 20, "计算机应用技术")
    student1.add_grade("数学", 100)
    student1.add_grade("英语", 136)
    student1.add_grade("编程", 110)

    print(student1)
    print("\n详细信息:")
    student1.display_info()
    print("\n获取数学成绩:", student1.get_grade("数学"))
    print("\n获取英语成绩:", student1.get_grade("英语"))
    print("\n获取编程成绩:", student1.get_grade("编程"))

    student2 = Student("卯富", "2023001", 20, "计算机应用技术")
    student2.add_grade("数学", 100)
    student2.add_grade("英语", 136)
    student2.add_grade("编程", 110)

    print(student2)
    print("\n详细信息:")
    student2.display_info()
    print("\n获取数学成绩:", student2.get_grade("数学"))
    print("\n获取英语成绩:", student2.get_grade("英语"))
    print("\n获取编程成绩:", student2.get_grade("编程"))