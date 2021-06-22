from typing import TypeVar, Generic, List, NewType, Type
import random

class PopMember:
    def __init__(self):
        self.x = random.randint(0, 100)
    def __repr__(self):
        return "Pop({})".format(self.x)

TPopMember = TypeVar("TPopMember")
Population = NewType('Population', List[TPopMember])

class EvolutionaryAlgorithm(Generic[TPopMember]):
    def __init__(self, member_class: Type[TPopMember], populationSize: int) -> None:
        self.__population = Population([member_class() for _ in range(populationSize)])
    def __repr__(self):
        return "EA({})".format(self.__population)

    def get(self):
        return self.__population[0]

x = EvolutionaryAlgorithm(PopMember, 5)
print(x)
print(type(x))
print(x.get())
print(type(x.get()))