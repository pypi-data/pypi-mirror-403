#Mcclouch AND

x1inputs = [0, 0, 1, 1]
x2inputs = [0, 1, 0, 1]

# Weights (excitatory)
w1 = 1
w2 = 1

# Threshold(must be sum of weights to fire only when both inputs are 1)
threshold = w1+w2  

print("x1  x2  sum  Y")
for x1, x2 in zip(x1inputs, x2inputs):
    
    addittion = x1 * w1 + x2 * w2
    
    # Apply threshold
    if addittion >= threshold:
        Y = 1
    else:
        Y = 0
    
    print(f"{x1}   {x2}   {addittion}    {Y}")
