from typing import AnyStr, Callable

class EntradaSalida:
    nombre:str = "EntradaSalida"

    def __init__(self, valorEnt=0, valorSal=0) -> None:
        self.valorEnt = valorSal
        self.valorSal = valorSal

    @classmethod
    def estado(cls) -> str:
        return cls.nombre

    def entrada(self, entrada:int) -> None:
        self.valorEnt = entrada

    def salida(self) -> int:
        return self.valorSal

class Procesa_ES:
    #valor_proc:str
    def __init__(self) -> None:
        valor_proc:str=""

    #@classmethod
    #def procesa(cls, vgen: Callable) -> None:
    def procesa(self, vgen: Callable) -> None:
        #cls.valor_proc = str(vgen())
        self.valor_proc = str(vgen()) * 10

if __name__ == "__main__":
    obj1 = EntradaSalida(1,2)
    proc1 = Procesa_ES()
    proc1.procesa(obj1.salida)
    print(proc1.valor_proc)
