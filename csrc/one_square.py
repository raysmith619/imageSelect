# one_square.py
from dots_commands import *
"""
Create one completed square
"""
lg("one_square.crc - create one completed square")
set_playing("Ax,G")
set_player("G")
select("h", 1, 1)
enter()
select("v",1, 2)
enter()
select("h", 2, 1)
enter()
select("v", 1, 1)
enter()
lg("square should be displayed")