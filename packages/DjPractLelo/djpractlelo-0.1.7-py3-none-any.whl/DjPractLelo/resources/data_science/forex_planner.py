prices = [74, 76, 75, 78, 77, 79, 80, 82, 81, 83, 80]

for i in range(1, len(prices)):
    if prices[i] > prices[i-1]:
        print("Day", i, ": BUY")
    else:
        print("Day", i, ": SELL")
