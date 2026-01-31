from gui import *

n = 0

def testFunction():
   global n
   print(n)
   n = n + 1

setAnimationRate(1)
animate(testFunction)