from src.httpprint import print

import time

i = 0

print("<test>")

while True:
    time.sleep(1)
    i += 1
    print("\033[92mHello \033[91mWorld\033[0m")
    print("testoooo \tWHOOOOOO")