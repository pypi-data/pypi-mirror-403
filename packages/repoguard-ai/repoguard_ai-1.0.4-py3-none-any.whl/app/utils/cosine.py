import math

def sim_check(a,b):
    summation=0
    for x,y in zip(a,b):
        summation=summation+x*y
    cumm1=0
    for x in a:
        cumm1=cumm1+x*x
    cumm2=0
    for y in b:
        cumm2=cumm2+y*y
    if not cumm1 or not cumm2:
       return 0.0
    mag_a= math.sqrt(cumm1)
    mag_b= math.sqrt(cumm2)

    return summation/(mag_a*mag_b)
    
    

