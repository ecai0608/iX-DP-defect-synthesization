import numpy as np

numbers = range(1,100)
rand_set = []
remaining = 50

new_numbers = np.random.choice(numbers, 50, replace = False)

print(new_numbers)
print(len(set(new_numbers)))