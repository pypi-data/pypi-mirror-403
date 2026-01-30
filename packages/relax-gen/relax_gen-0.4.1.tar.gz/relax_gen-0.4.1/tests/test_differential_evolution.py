# Test From the Differential Evolution with Use Case Example
import numpy as np
from relaxgen import GEN
import pytest

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)  # Ignoring runtime warnings for invalid operations

# Data from the use case

'''
Use case: Optimization of a heat exchanger design using Differential Evolution.
Objective: Maximize the effectiveness of the heat exchanger by optimizing its design parameters:
- Diameter (D_i, D_o)
- Length (L)
- Mass flow rates (m_h, m_c)
Design variables:
- D_i: Internal diameter of the heat exchanger (m)
- D_o: External diameter of the heat exchanger (m)
- L: Length of the heat exchanger (m)
- m_h: Mass flow rate of the hot fluid (kg/s)
- m_c: Mass flow rate of the cold fluid (kg/s)

'''

U = 500 # Coefficient of heat transfer in W/(m2 * K)
T_h_in = 80 + 273.15 # Inlet temperature of the hot fluid in K
T_c_in = 20 + 273.15 # Inlet temperature of the cold fluid in K

# Specific heat capacity of water in J/(kg * K)
C_h = 4180 
C_c = 4180 

# Restricctions on the design variables
D_i_min = 0.01  # Internal diameter minimum in m
D_i_max = 0.05   # Internal diameter maximum in m
D_o_min = 0.015  # External diameter minimum in m
D_o_max = 0.06   # External diameter maximum in m

L_min = 1.0     # Length minimum in m
L_max = 10.0     # Length maximum in m

m_min = 0.05   # Hot and cold fluid mass flow rate minimum in kg/s
m_max = 0.5  # Hot and cold fluid mass flow rate maximum in kg/s 
T_h_out = 80 + 273.15  # Provisional temperature of the hot fluid outlet in K
# T_h_out must be less than T_h_in
Tem_Final = T_h_out > T_c_in 

eps = 0.001 # Minimum margin between D_o and D_i

def fun_objetivo(variables):
    D_i, D_o, L, m_h, m_c = variables
    # D_i: Internal diameter in m
    # D_o: External diameter in m
    # L: Length in m
    # m_h: Mass flow rate of the hot fluid in kg/s
    # m_c: Mass flow rate of the cold fluid in kg/s

    # Process to calculate C_min and C_max
    C_h_tot = m_h * C_h
    C_c_tot = m_c * C_c
    C_min = np.minimum(C_h_tot, C_c_tot) # Minimum heat capacity
    C_max = np.maximum(C_h_tot, C_c_tot) # Maximum heat capacity

    if C_min <= 0:
        C_min = 1e-6  # Avoid division by zero
    if C_max <= 0:
        C_max = 1e-6  # Avoid division by zero


    A = np.pi * D_o * L  # Heat transfer area in m2

    NTU = U * A / C_min # Number of transfer units
    Cr = C_min / C_max  # Capacity ratio

    with np.errstate(invalid='ignore', divide='ignore'): # Handling numpy errors
        n = (1 - np.exp(-NTU * (1 - Cr))) / (1 - Cr * np.exp(-NTU * (1 - Cr)))
    if np.isnan(n) or np.isinf(n): # Handling undefined cases
        n = 0.0
    return n


limites = [(D_i_min, D_i_max), 
           (D_o_min, D_o_max),
            (L_min, L_max),
            (m_min, m_max),
            (m_min, m_max)]

population = 400
mutation = 0.8
recombination = 0.7
generations = 100

def test_de_use_case():
    """
    Description:
    Test the Differential Evolution algorithm on the heat exchanger design optimization use case.
    """
    modelo = GEN(fun_objetivo, 
            population=population,
            num_variables=5, 
            mutation_percent=mutation,
            crossing=recombination,
            num_cycles=generations,
            limits=limites,
            optimum='max'
            )

    result = modelo.alg_de()
    fitness = fun_objetivo(result)
    # Something close to 0.85 but is working with randomness
    assert fitness == pytest.approx(0.85, abs=0.2)