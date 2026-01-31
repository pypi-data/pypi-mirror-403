# McCulloch-Pitts OR

x1inputs = [0, 0, 1, 1]
x2inputs = [0, 1, 0, 1]

# Weights (excitatory)
w1 = 1
w2 = 1

# Threshold (must be 1 to fire when at least one input is 1)
threshold = 1  # minimum excitatory input to fire

print("x1  x2  sum  Y")
for x1, x2 in zip(x1inputs, x2inputs):
    
    addition = x1 * w1 + x2 * w2
    
    # Apply threshold
    if addition >= threshold:
        Y = 1
    else:
        Y = 0
    
    print(f"{x1}   {x2}   {addition}    {Y}")
