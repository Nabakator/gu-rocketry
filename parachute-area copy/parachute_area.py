# Parachute design helping tool
# S = (2 * g * m) / (rho_air * C_d * V^2)
# D = = sqrt(S * 4 / pi)

import numpy as np

deployment_mode = str(input('Deployment mode? ("single" or "dual") '))
safety_factor = float(input("Safety factor? (e.g. 1.1) "))

# Conversions (SI to Imperial)
m2_to_ft2 = 10.7639 # 1 m^2 = 10.7639 ft^2
m_to_inch = 39.3701 # 1 m = 39.3701 in
m_to_ft = 3.28084 # 1 m = 3.28084 ft

if deployment_mode == "single":

    g = float(input("g: gravitational acceleration (e.g. 9.81) [m/s^2]: "))
    m = float(input("m: dry mass of the rocket (i.e. after fuel has burned out e.g. 10) [kg]: "))
    rho_air = float(input("rho_air: density of air at sea level (e.g. 1.225) [kg/m^3]: "))
    C_d = float(input("C_d: drag coefficient (e.g. 1.2) [dimensionless]: "))
    V = float(input("V: target descent rate (should be less than 15)[m/s]: "))

    # Computations
    S_total = round((2.0 * g * m) / (rho_air * C_d * V * V), 3)
    D_total = round(np.sqrt(S_total * 4 / np.pi),1)

    S_total_ft2 = round(S_total * m2_to_ft2, 3)
    D_total_in = round(D_total * m_to_inch, 1)
    D_total_ft = round(D_total * m_to_ft, 1)

    if D_total_ft > 1:
        D_total_ft = round(D_total_ft)

    # Results
    print("Minimum chute area = ~", S_total, "m^2 = ~", S_total_ft2, "ft^2 or", round(safety_factor * S_total_ft2, 3), "ft^2 with safety factor of", safety_factor)
    print("Equivalent diameter = ~", D_total, "m = ~", D_total_in, "in = ~", D_total_ft, "ft or", round(safety_factor * D_total_ft, 3), "ft with safety factor of", safety_factor)
    

else:

    g = float(input("g: gravitational acceleration (e.g. 9.81) [m/s^2]: "))
    m = float(input("m: dry mass of the rocket (i.e. after fuel has burned out e.g. 10) [kg]: "))
    rho_air = float(input("rho_air: density of air at sea level (e.g. 1.225) [kg/m^3]: "))
    C_d_drogue = float(input("C_d_drogue: drag coefficient of the drogue chute (e.g. 1.2) [dimensionless]: "))
    C_d_main = float(input("C_d_main: drag coefficient of the main chute (e.g. 1.2) [dimensionless]: "))
    V = float(input("V: target descent rate (should be less than 15)[m/s]: "))

    # Computations
    C_d_avg = (C_d_drogue + C_d_main) / 2

    S_total = round((2.0 * g * m) / (rho_air * C_d_avg * V * V), 3)
    D_total = round(np.sqrt(S_total * 4 / np.pi), 1)

    S_drogue = round(S_total * 0.2, 3)
    D_drogue = round(D_total * 0.2, 1)

    S_main = round(S_total * 0.8, 3)
    D_main = round(D_total * 0.8, 1)

    S_total_ft2 = round(S_total * m2_to_ft2, 3)
    D_total_in = round(D_total * m_to_inch, 1)
    D_total_ft = round(D_total * m_to_ft, 1)

    S_drogue_ft2 = round(S_drogue * m2_to_ft2, 3)
    D_drogue_in = round(D_drogue * m_to_inch, 1)
    D_drogue_ft = round(D_drogue * m_to_ft, 1)

    if D_drogue_ft > 1:
        D_drogue_ft = round(D_drogue_ft)

    S_main_ft2 = round(S_main * m2_to_ft2, 3)
    D_main_in = round(D_main * m_to_inch, 1)
    D_main_ft = round(D_main * m_to_ft, 1)

    if D_main_ft > 1:
        D_main_ft = round(D_main_ft)

    # Results
    print("Minimum total chute area = ~", S_total, "m^2 = ~", S_total_ft2, "ft^2 or", round(safety_factor * S_total_ft2, 3), "ft^2 with safety factor of", safety_factor)

    print("Minimum drogue chute area = ~", S_drogue, "m^2 = ~", S_drogue_ft2, "ft^2 or", round(safety_factor * S_drogue_ft2, 3), "ft^2 with safety factor of", safety_factor)
    print("Equivalent diameter = ~", D_drogue, "m = ~", D_drogue_in, "in = ~", D_drogue_ft, "ft or", round(safety_factor * D_drogue_ft, 1), "ft with safety factor of", safety_factor)

    print("Minimum main chute area = ~", S_main, "m^2 = ~", S_main_ft2, "ft^2 or", round(safety_factor * S_main_ft2, 3), "ft^2 with safety factor of", safety_factor)
    print("Equivalent diameter = ~", D_main, "m = ~", D_main_in, "in = ~", D_main_ft, "ft or", round(safety_factor * D_main_ft, 1), "ft with safety factor of", safety_factor)