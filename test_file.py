from datetime import date
import os

path = "Test"
if not os.path.exists(path):
    os.makedirs(path)
    print("no")

today = date.today()
print(str(today))