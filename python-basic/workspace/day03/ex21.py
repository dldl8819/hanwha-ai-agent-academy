# 추상 클래스 사용 선언
from abc import ABC, abstractmethod

# 추상 클래스 선언
class Animal(ABC):
    # 추상 메서드
    # 자식 클래스에서 구현 강제하는 데코레이터 abstractmethod
    @abstractmethod 
    def sound(self):
        pass

# 추상 클래스를 선언하는 자식 클래스 선언
class Cat(Animal):
    def sound(self):
        print("야옹~~")

class Dog(Animal):
    def sound(self):
        print("멍멍!!")

dog = Dog()
dog.sound()

cat = Cat()
cat.sound()