from LscCalculator import *
import inspect


class Number:
    def __init__(self, number):
        self.number = self.__to_num__(number)

    @staticmethod
    def __to_num__(n):
        if not isinstance(n, (int, float)):
            if "." in str(n):
                return float(n)
            else:
                return int(n)
        else:
            return n

    @classmethod
    def __get_magic_method__(cls):
        magic_methods = []
        for attr_name in cls.__dict__:
            if attr_name.startswith('__') and attr_name.endswith('__'):
                attr_value = getattr(cls, attr_name)
                if callable(attr_value):
                    magic_methods.append(attr_name)
        return magic_methods

    def __repr__(self):
        return f"Number({self.number})"

    def __getattribute__(self, attr_name):
        caller_frame = inspect.stack()[1]
        caller_func_name = caller_frame.function

        is_magic_method = caller_func_name.startswith('__') and caller_func_name.endswith('__')
        if (not is_magic_method and attr_name == "number") or (not is_magic_method and attr_name in self.__get_magic_method__()):
            raise AttributeError(f"禁止访问{attr_name}！")
        else:
            return super().__getattribute__(attr_name)

    def __add__(self, other):
        return Number(nc().addition(self.number, self.__to_num__(other)))

    def __sub__(self, other):
        return Number(nc().subtraction(self.number, self.__to_num__(other)))

    def __mul__(self, other):
        return Number(nc().multiplication(self.number, self.__to_num__(other)))

    def __truediv__(self, other):
        return Number(nc().division(self.number, self.__to_num__(other)))

    def __int__(self):
        return int(self.number)

    def __float__(self):
        return float(self.number)

    def __round__(self, n=None):
        return Number(round(self.number, n))

    def __pow__(self, power, modulo=None):
        return Number(nc().power(self.number, power, modulo))

    def __str__(self):
        return str(self.number)

    def __eq__(self, other):
        return self.number == self.__to_num__(other)

    def __ne__(self, other):
        return self.number != self.__to_num__(other)

    def __lt__(self, other):
        return self.number < self.__to_num__(other)

    def __gt__(self, other):
        return self.number > self.__to_num__(other)

    def __le__(self, other):
        return self.number <= self.__to_num__(other)

    def __ge__(self, other):
        return self.number >= self.__to_num__(other)


if __name__ == '__main__':
    n1 = Number('1')
    n1 += 13
    n2 = Number('10')
    n1 -= n2
    n21 = Number(input())
    print(n21 / Number(21))
    print(n1 == n2)
    print(n1)
    print(n2)
