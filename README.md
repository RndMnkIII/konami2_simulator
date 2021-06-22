# Konami-2 CPU + Aliens Arcade Simulator in Python 3

!["Simulator Screen Capture 1](https://github.com/RndMnkIII/konami2_simulator/blob/main/img/cap01.png)
!["Simulator Screen Capture 2](https://github.com/RndMnkIII/konami2_simulator/blob/main/img/cap02.png)
!["Simulator Screen Capture 3](https://github.com/RndMnkIII/konami2_simulator/blob/main/img/cap03.png)

## English:
This project is a simulator of the Konami-2 CPU used in various Konami arcade machines from the late 80's and early 90's. It is a unique development based on the MC6809 8-bit CPU running at a higher speed (3MHz) and with certain features borrowed from the 68000 CPU such as the use of signals to control the system bus asynchronously (AS, DTAC ). It is not an emulator designed to play, in fact it is horribly slow. It is primarily intended to study the operation of said CPU using an implementation of a game as an example. It is based fundamentally on the MAME source code, so this recognition is mentioned here, but all the part of the mapping in memory of devices (memory_mapper.py) and the memory for the color palette (CRAM) is based mainly on the schematics of the original hardware and does not follow the scheme implemented by MAME. The purpose is to allow a study platform to help be implemented in an FPGA using a hardware description language (HDL), Verilog or VHDL.

For it to work properly you must unzip the content of the repository into a folder. Inside that folder you must create another called `eproms` where you must copy the Aliens game files (Romset). You must be the original owner of said ROMS that will be contained in the pcb of said game and dump them to a binary file format. Or obtain a backup copy of these files that you can find on various sites on the Internet. Specifically, these files must match MAME ROMSET 3 (see aliens3.zip):
```
	875_w3_1.c24
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
To run the simulation you must have a version of Python 3 that supports Type Hints (3.5+), ctypes and curses. You must also install the numpy module. To run open a terminal and enter:

`python3 aliens_machine.py`

Keep in mind that you have to use a terminal that can arbitrarily decrease the size of the text so that it will not be possible to read it since there is a size of at least 670x240 characters on a screen with a typical resolution of 1920x1080. if not a totally distorted image will be displayed, as it works in text mode curses with color. Specifically, I have tested it on MacOS Big Sur (ITerm2, Terminal) and Windows 10 terminal (cmd and WSL2 Ubuntu). The terminal capabilities must allow a 256 color palette, which allows the colors of the tile layers (FIX, LAYER-A, LAYER-B) to be displayed at the same time that use 192 colors (64 colors each layer). The sprite layer is not implemented but it would need 256 colors independent of the tiles for it, so they could not be displayed simultaneously with the tile layers in curses text mode, since 192 + 256 colors are used in total.

## Español:
Este proyecto es un simulador de la CPU Konami-2 empleada en varias máquinas arcade de Konami de
finales de los 80's y principios de los 90's. Es un desarrollo único basado en la CPU de 8-bit MC6809
funcionando a una velocidad más elevada (3MHz) y con ciertas características tomadas de la CPU 68000
tales como el uso de señales para controlar el bus del sistema de forma asíncrona (AS, DTAC).
No se trata de un emulador pensado para jugar, de hecho es horriblemente lento. Está pensado fundamentalmente
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
	875_w3_1.c24
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

Para ejecutar la simulación deberás tener una versión de Python 3 que tenga soporte para Type Hints (3.5+), ctypes y curses. Además deberás instalar
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
