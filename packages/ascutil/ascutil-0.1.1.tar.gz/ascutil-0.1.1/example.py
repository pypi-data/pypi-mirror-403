import time
import shutil
import numpy as np
from ascutil import mutate

shutil.copy("circuit.asc", "circuit_copy.asc")

rows = np.array(range(16))
columns = np.array(range(54))

t1 = time.time()
mutate("circuit_copy.asc", rows, columns, 0.5)
print(time.time() - t1)
