'''XOR= '''
''' 0 if inputs are same,else 1'''

x1inputs = [0, 0, 1, 1]
x2inputs = [0, 1, 0, 1]

print("x1  x2  Y")

for x1, x2 in zip(x1inputs, x2inputs):
    
    # First layer neurons
    # Neuron1 = x1 AND NOT x2
    neuron1_sum = x1 * 1 + x2 * -1
    neuron1_threshold = 1
    if neuron1_sum >= neuron1_threshold:
        neuron1 = 1
    else:
        neuron1 = 0
    
    # Neuron2 = NOT x1 AND x2
    neuron2_sum = x1 * -1 + x2 * 1
    neuron2_threshold = 1
    if neuron2_sum >= neuron2_threshold:
        neuron2 = 1
    else:
        neuron2 = 0
    
    # Output neuron = Neuron1 OR Neuron2
    output_sum = neuron1 * 1 + neuron2 * 1
    output_threshold = 1
    if output_sum >= output_threshold:
        Y = 1
    else:
        Y = 0
    
    print(f"{x1}   {x2}   {Y}")
