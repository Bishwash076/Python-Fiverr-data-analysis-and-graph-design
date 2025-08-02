Python 3.12.5 (tags/v3.12.5:ff3bc82, Aug  6 2024, 20:45:27) [MSC v.1940 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
# Import necessary libraries
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Prompt user input for feed composition
print("Enter the mole fractions of gas components (values should add up to 1):")
gas_components = ['H2', 'CO', 'N2']  # Multicomponent gas stream
feed_composition = {}
for component in gas_components:
    while True:
        try:
            mole_fraction = float(input(f"Mole fraction of {component}: "))
            if mole_fraction < 0 or mole_fraction > 1:
                raise ValueError("Mole fraction should be between 0 and 1.")
            feed_composition[component] = mole_fraction
            break
        except ValueError as e:
            print(f"Invalid input: {e}")

# Validate that mole fractions add up to 1
if abs(sum(feed_composition.values()) - 1) > 1e-6:
    raise ValueError("The sum of mole fractions must be equal to 1.")

# Constants and input parameters
feed_flow_rate = 1.0  # Total flow rate (mol/s)
adsorbent_density = 600  # kg/m^3, example value
bed_porosity = 0.4  # Porosity of the adsorption bed
column_length = 2.0  # Initial assumption for column length (m)
column_diameter = 0.1  # Assumed column diameter (m)
pressure_steps = [5, 3, 1]  # Example pressures in bar for adsorption, blowdown, and purge

# Utility functions
def ergun_equation(flow_rate, diameter, porosity, density, viscosity):
    """
    Calculate pressure drop using the Ergun equation.
    """
    velocity = flow_rate / (np.pi * (diameter / 2)**2)
    dp = (150 * viscosity * velocity * (1 - porosity) / (diameter**2 * porosity**3) +
          1.75 * density * velocity**2 / (diameter * porosity**3))
    return dp

def langmuir_isotherm(pressure, qm, b):
    """
    Calculate adsorption using the Langmuir isotherm.
    """
    return qm * b * pressure / (1 + b * pressure)

# PSA Cycle Simulation
def psa_cycle(t, y, pressure, adsorbent_params):
    """
    Differential equations for PSA cycle steps (mass, energy, and impulse balance).
    Handles multicomponent systems.
    """
    dydt = []
    for i, component in enumerate(gas_components):
        concentration = y[i]
        rate = -adsorbent_params[component]['rate_constant'] * concentration
        dydt.append(rate)
    return dydt

# Adsorbent data (example values; replace with your data)
adsorbent_params = {
...     'H2': {'qm': 1.0, 'b': 0.1, 'rate_constant': 0.05},
...     'CO': {'qm': 0.8, 'b': 0.2, 'rate_constant': 0.04},
...     'N2': {'qm': 0.6, 'b': 0.3, 'rate_constant': 0.03},
... }
... 
... # Initial conditions
... initial_concentration = [feed_composition[comp] for comp in gas_components]
... 
... # Simulate PSA cycle
... time_span = (0, 10)  # Total time for one step (s)
... time_eval = np.linspace(0, 10, 100)
... results = {}
... 
... for step, pressure in zip(['adsorption', 'blowdown', 'purge'], pressure_steps):
...     solution = solve_ivp(psa_cycle, time_span, initial_concentration,
...                          args=(pressure, adsorbent_params), t_eval=time_eval)
...     results[step] = solution
... 
... # Plot results
... for step, solution in results.items():
...     for i, component in enumerate(gas_components):
...         component_label = component.replace('2', '$_2$')  # Format subscripts for chemical formulas
...         plt.plot(solution.t, solution.y[i], label=f'{step} ({component_label})')
... plt.xlabel('Time (s)')
... plt.ylabel('Concentration')
... plt.title('Breakthrough Curves for PSA Cycle Steps')
... plt.legend()
... plt.show()
... 
... # Further calculations
... # Determine purity and recovery for H2 (example approach)
... final_concentration = results['adsorption'].y[0, -1]  # Final H2 concentration
... total_final_concentration = np.sum(results['adsorption'].y[:, -1])  # Sum of all components
... purity = final_concentration / total_final_concentration
... recovery = final_concentration / initial_concentration[0]
... print(f'Purity of H2: {purity:.2%}')
... print(f'Recovery of H2: {recovery:.2%}')
