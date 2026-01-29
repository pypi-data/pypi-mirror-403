import numpy as np
from scipy.stats import norm
N= norm.cdf
#call = C = S₀N(d₁) - Ke⁻ʳᵗN(d₂)
#put=ke^(-rT)*N(-d2)-S*N(-d1)
#d₁ = [ln(S₀/K) + (r + σ²/2)t] / (σ√t)
#d₂ = d₁ - σ√t

def bsm(S,K,T,r,sigma,option_type="call",time_scale="Year"):
    if time_scale == "Month":
        T = T/12
    r = r/100
    sigma = sigma/100
    denominator = (sigma*np.sqrt(T))
    numerator = np.log(S/K)+(r+(sigma**2*0.5))*T
    d1 = numerator/denominator
    d2 = d1-denominator
    if option_type == "call":
        price = (S*N(d1))-((K*np.exp(-1*r*T))*(N(d2)))
    elif option_type == "put":
        price = ((K*np.exp(-1*r*T))*(N(-1*d2)))-(S*N(-d1))
    else:
        "Plz put the correct option type"
    return round(price,2)



if __name__ =="__main__":
    a=bsm(50,50,1,6,25,option_type = "call")
    
