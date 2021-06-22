# Konami-2 CPU + Aliens Arcade Simulator in Python 3

!["Simulator Screen Capture 1](https://github.com/RndMnkIII/k051962_verilog/blob/main/img/cap01.png)
!["Simulator Screen Capture 2](https://github.com/RndMnkIII/k051962_verilog/blob/main/img/cap02.png)
!["Simulator Screen Capture 3](https://github.com/RndMnkIII/k051962_verilog/blob/main/img/cap03.png)

Este proyecto es un simulador de la CPU Konami-2 empleada en varias máquinas arcade de Konami de
finales de los 80's y principios de los 90's. Es un desarrollo único basado en la CPU de 8-bit MC6809
funcionando a una velocidad más elevada (3MHz) y con ciertas características tomadas de la CPU 68000
tales como el uso de señales para controlar el bus del sistema de forma asíncrona (AS, DTAC).
No se trata de un emulador pensado para jugar, de ello es horriblemente lento. Está pensado fundamentalmente
para estudiar el funcionamiento de dicha CPU utilizando como ejemplo una implementación de un juego.
Está basado fundamentalmente en el código fuente de MAME por lo se menciona aquí dicho reconomiento, pero toda
la parte del mapeo en memoria de dispositivos (`memory_mapper.py`) y la memoria para la paleta de colores (CRAM)
está basado mayormente en los esquemáticos del hardware original y no sigue el esquema implementado por MAME.
La finalidad es permitir una plataforma de estudio para ayudar a ser implementado en una FPGA utilizando un
lenguaje de descripción de hardware (HDL), Verilog o VHDL.

Para que funcione adecuadamente debes descomprimir el contenido del repositorio dentro de una carpeta.
Dentro de esa carpeta debes crear otra llamada `eproms` donde deberas copiar los archivos del juego Aliens (Romset ).
Debes ser el poseedor original de dichas ROMS que estarán contenidas en la pcb de dicho juego y volcarlas a un formato
de archivo binario. O bien obtener una copia de respaldo de dichos archivos que podrás encontrar en diversos sitios en
Internet. En concreto dichos archivos deberán coincidir con el ROMSET 3 de MAME (ver aliens3.zip):

```
	875_c01.c24
	875_w3_2.e24
	875_b03.g04
	875b11.k13
	875b12.k19
	875b07.j13
	875b08.j19
	875b10.k08
	875b09.k02
	875b06.j08
	875b05.j02
	821a08.h14
	875b04.e05
```

Para ejecutar la emulación deberás tener una versión de Python 3 que tenga soporte para Type Hints (3.5+), ctypes y curses. Además deberás instalar
el modulo numpy.
Para ejecutar abre un terminal e introduce:

`python3 aliens_machine.py`

Ten en cuenta que tienes que utilizar un terminal que pueda disminuir de forma arbitraria el tamaño del texto de manera
que no será posible leerlo ya que hay un obtener un tamaño de al menos 670x240 caracteres en una pantalla con una resolución típica de 1920x1080.
si no se mostrará una imagen totalmente distorsionada, ya que funciona en modo de texto curses con color.
En concreto lo he probado en MacOS Big Sur (ITerm2, Terminal) y terminal de Windows 10 (cmd y WSL2 Ubuntu).
Las capacidades del terminal deben permitir una paleta de 256 colores, lo que permite mostrar al mismo tiempo
los colores de las capas de tiles (FIX, LAYER-A, LAYER-B) que utilizan 192 colores (64 colores cada capa).
La capa de sprites no está implementada pero necesitaría 256 colores independientes de los de los tiles
 para ella por lo que no se podrían mostrar de manera simultánea con las capas de tiles en modo de texto curses,
 ya que se utilizan 192 + 256 colores en total.

