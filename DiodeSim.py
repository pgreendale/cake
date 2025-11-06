#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  5 21:54:50 2025

@author: p_greendale
@about : simple nonlinear diode ; playing around with two-tone excitation
"""

import numpy as np 
from matplotlib import pyplot as plt
from scipy.special import lambertw


Is = 5e-6 #blocking current for 1N4001, normally temperature sensitive
n  = 1
kb = 1.389649e-23    #boltzmann [m^2*kg*s^-2]
e  = 1.602176634e-19 #elementary charge [C]
Ut = lambda temp : kb * (temp + 273) / e #thermal Voltage
    
def Id(Uf = 0, temp=21) : 
    #weber diode formula, current Id  
    return Is * (np.exp(Uf/(n*Ut(temp))) - 1 )
    
def Ud(Id = 0, temp=21): 
    #nrearranged for Ud  
    #return n*Ut(temp)*(1 + np.log(Id/Is))
    return np.log(Id/Is + 1 ) * n*Ut(temp)  

def UdSolvedU(Uin, R, temp=21): 
    #U = Ud + R(Id(Ud)) using Wolfram Alpha to solve for x
    return Uin + Is*R - n*Ut(temp)*lambertw(Is*np.exp((Is*R + Uin)/(n*Ut(temp)))*R/(n*Ut(temp)), k=0) 

Umax = 0.7                   #max.amplitude 
Ib   = 20e-3                 #set operating current at max. amplitude 
R    = (Umax - Ud(Ib))/Ib    #solve for current limitung resistor

f  = 1e3
f2 = 330
t = np.linspace(0, 1, num = 100*int(f))
U = Umax * np.sin(2*np.pi*f*t + 0) + Umax/2 * np.sin(2*np.pi*f2*t + 0)
UDcomplex = UdSolvedU(Uin=U,R=R)

#plotting stuff 
plt.figure(dpi=150)
plt.plot(t[:int(f)], U[:int(f)], label=r'U_q' ) 
plt.plot(t[:int(f)], np.real(UDcomplex)[:int(f)], label = r'$U_{Diode}$')
plt.title(r'Excitation and $U_{Diode}$ Voltage')
plt.xlabel('time')  
plt.ylabel('voltage')
plt.legend()
plt.show()

plt.figure()
sp = np.fft.fft(U)
so = np.fft.fft(UDcomplex)
freq = np.fft.fftfreq(t.shape[-1])
_ = plt.plot(freq, sp.real, freq, sp.imag)
plt.legend(iter(_),('Real','Imag'))
plt.title('Fourier transformed Excitation')
plt.xlabel('Frequency')
plt.ylabel('Magnitude')
plt.show()

plt.figure()
_ = plt.plot(freq, so.real, freq, so.imag)
plt.legend(iter(_),('Real','Imag'))
plt.title(r'Fourier transformed $U_{Diode}$')
plt.xlabel('Frequency')
plt.ylabel('Magnitude')