import picozero
import time

pot1 = picozero.Pot(26)
pot2 = picozero.Pot(27)
pot3 = picozero.Pot(28)

while True:
    v1 = pot1.value
    v2 = pot2.value
    v3 = pot3.value
    print(f"{v1:1.4} {v2:1.4} {v3:1.4}")
    time.sleep(0.1)
    