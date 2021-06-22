# curses.color_content(color_number)¶
# Return the intensity of the red, green, and blue (RGB) components in the color color_number, which must be between 0 and COLORS. A 3-tuple is returned, 
# containing the R,G,B values for the given color, which will be between 0 (no component) and 1000 (maximum amount of component).

# curses.color_pair(color_number)
# Return the attribute value for displaying text in the specified color. This attribute value can be combined with A_STANDOUT, A_REVERSE, and the other
#  A_* attributes. pair_number() is the counterpart to this function.

# curses.pair_content(pair_number)¶
# Return a tuple (fg, bg) containing the colors for the requested color pair. The value of pair_number must be between 1 and COLOR_PAIRS - 1.

# curses.pair_number(attr)
# Return the number of the color-pair set by the attribute value attr. color_pair() is the counterpart to this function.

# curses.init_color(color_number, r, g, b)
# Change the definition of a color, taking the number of the color to be changed followed by three RGB values (for the amounts of red, green, and blue components). 
# The value of color_number must be between 0 and COLORS. Each of r, g, b, must be a value between 0 and 1000. When init_color() is used, all occurrences of that 
# color on the screen immediately change to the new definition. This function is a no-op on most terminals; it is active only if can_change_color() returns 1.

# curses.init_pair(pair_number, fg, bg)
# Change the definition of a color-pair. It takes three arguments: the number of the color-pair to be changed, the foreground color number, and the background
# color number. The value of pair_number must be between 1 and COLOR_PAIRS - 1 (the 0 color pair is wired to white on black and cannot be changed). The value of
# fg and bg arguments must be between 0 and COLORS. If the color-pair was previously initialized, the screen is refreshed and all occurrences of that color-pair 
# are changed to the new definition.
#curses.COLORS 0-255
#curses.COLOR_PAIRS 1-255, 0 reserved for white(fg) on black(bg)

import curses
import time

#curses init
stdscr = curses.initscr()
curses.noecho()
curses.cbreak()
stdscr.keypad(True)

# Start colors in curses
curses.start_color()
trio = curses.color_content(curses.COLOR_BLACK)     #0
trio = curses.color_content(curses.COLOR_RED)       #1
trio = curses.color_content(curses.COLOR_GREEN)     #2
trio = curses.color_content(curses.COLOR_YELLOW)    #3
trio = curses.color_content(curses.COLOR_BLUE)      #4
trio = curses.color_content(curses.COLOR_MAGENTA)   #5
trio = curses.color_content(curses.COLOR_CYAN)      #6
trio = curses.color_content(curses.COLOR_WHITE)     #7

par = curses.pair_content(0)       # (7,0)


count=0
# for r in range(400,1000,75):
#     for g in range (400,1000,75):
#         for b in range (400,1000,75):
#             if count <= 255: 
#                 curses.init_color(count, r, g, b)
#             count+=1
for i in range(0,256):
    curses.init_color(i, 500, 600, 800) 

curses.resize_term(33, 80)

#for j in range(0,256):
curses.init_pair(1,  curses.COLOR_WHITE, curses.COLOR_BLACK)


# Clear and refresh the screen for a blank canvas

# for i in range (0,16):
#     for j in range (0,128):
#         stdscr.addstr(i, j, "█", curses.color_pair((i*128+j)%256+1))

# stdscr.refresh()
# time.sleep(5)

# count=0
# for b in range(400,1000,75):
#     for g in range (400,1000,75):
#         for r in range (400,1000,75):
#             if count <= 255: 
#                 curses.init_color(count, r, g, b)
#             count+=1

# for j in range(0,256):
#     curses.init_pair(j+1, j, j)

# for i in range (16,32):
#     for j in range (0,128):
#         stdscr.addstr(i, j, "█", curses.color_pair((i*128+j)%256+1))
stdscr.clear()
stdscr.addstr(2,2, f"Colors:{curses.COLORS}", curses.color_pair(0))
stdscr.addstr(3,2, f"Colors:{curses.COLOR_PAIRS}", curses.color_pair(0))
stdscr.refresh()
time.sleep(5)

curses.nocbreak()
stdscr.keypad(False)
curses.echo()
curses.endwin()