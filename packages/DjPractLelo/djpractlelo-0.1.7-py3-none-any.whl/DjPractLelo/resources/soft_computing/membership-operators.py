print("---- Membership Operators ----")

nums = [10, 20, 30]
text = "Python"
data = {"name": "Sam", "age": 22}

print(nums,"\n",text,"\n",data)

print("20 is present in 'nums' array :",20 in nums)        
print("40 is not present in 'nums' array :",40 not in nums)    
 
print("\n---- Identity Operators ----")

a = [1, 2, 3]
b = a          
c = [1, 2, 3]  

print(a is b)       
print(a is not b)   

print(a is c)       
print("Array 'a' has same elements like 'c' ",a == c)
