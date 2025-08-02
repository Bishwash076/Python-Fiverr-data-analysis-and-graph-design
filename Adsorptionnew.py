import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# Prompt user input for feed composition
print("Enter the mole fractions of gas components (values should add up to 1):")
gas_components = ['H2', 'CO', 'N2']
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

# Validate mole fraction sums to 1
if abs(sum(feed_composition.values()) - 1) > 1e-6:
    raise ValueError("The sum of mole fractions must be equal to 1.")

# PSA cycle steps and parameters
pressure_steps = [16, 8, 1, 8, 16]  # Adsorption, Equalization, Blowdown, Purge, Pressurization
cycle_names = ['Adsorption', 'Equalization', 'Blowdown', 'Purge', 'Pressurization']
num_cycles = 10  # Number of iterations to reach cyclic steady state
tolerance = 1e-3  # Convergence threshold for cyclic steady state

# Adsorption parameters (Langmuir isotherm)
adsorbent_params = {
    'H2': {'qm': 1.0, 'b': 0.1},
    'CO': {'qm': 0.8, 'b': 0.2},
    'N2': {'qm': 0.6, 'b': 0.3}
}

# Column sizing calculation
feed_flow_rate = 1.0  # m³/s
u_mf = 0.1  # Minimum fluidization velocity (m/s)
velocity_safety_factor = 1.2
adsorbent_mass = 50.0  # kg
adsorption_capacity = 1.0  # kg/m³

superficial_velocity = u_mf * velocity_safety_factor
column_diameter = np.sqrt((4 * feed_flow_rate) / (np.pi * superficial_velocity))
column_length = adsorbent_mass / (adsorption_capacity * (np.pi * (column_diameter / 2)**2))

print(f"Column Diameter: {column_diameter:.2f} m")
print(f"Column Length: {column_length:.2f} m")

# Langmuir adsorption isotherm function
def langmuir_isotherm(concentration, pressure, qm, b):
    return qm * b * pressure / (1 + b * pressure) * concentration

# PSA cycle simulation differential equations
def psa_cycle_model(t, y, pressure, adsorbent_params):
    dydt = []
    for i, component in enumerate(gas_components):
        concentration = y[i]
        qm, b = adsorbent_params[component]['qm'], adsorbent_params[component]['b']
        rate = -langmuir_isotherm(concentration, pressure, qm, b)
        dydt.append(rate)
    return dydt

# Initialize cyclic steady state tracking
prev_concentration = None
steady_state_reached = False

# Generate refined pressure profile with interpolated points
num_pressure_points = len(pressure_steps) * 10  # Increase resolution for smooth transitions
time_steps = np.linspace(0, 50 * num_cycles, num_cycles * num_pressure_points)
pressure_values = np.interp(time_steps, np.linspace(0, 50 * len(pressure_steps), len(pressure_steps)), pressure_steps)

# PSA cycle simulation over multiple iterations for cyclic steady state
for cycle in range(num_cycles):
    results = {}
    steady_state_error = 0
    
    for step_idx, pressure in enumerate(pressure_steps):
        time_span = (0, 10)  # Time per step
        time_eval = np.linspace(0, 10, 200)  # Increased resolution for smoother breakthrough curves
        initial_concentration = prev_concentration if prev_concentration is not None else [feed_composition[c] for c in gas_components]
        
        solution = solve_ivp(psa_cycle_model, time_span, initial_concentration,
                             args=(pressure, adsorbent_params), t_eval=time_eval)
        
        results[cycle_names[step_idx]] = solution
        prev_concentration = solution.y[:, -1]  # Update for next step
        
        if steady_state_reached:
            steady_state_error = max(steady_state_error, np.max(abs(prev_concentration - initial_concentration)))

    # Check cyclic steady state convergence
    if steady_state_error < tolerance:
        steady_state_reached = True
        break  # Stop iterating once steady state is reached

# Plot breakthrough curves separately for each cycle step
for step in cycle_names:
    plt.figure(figsize=(10, 6))
    for i, component in enumerate(gas_components):
        plt.plot(results[step].t, results[step].y[i], label=component.replace('2', '$_2$'))
    plt.xlabel('Time (s)')
    plt.ylabel('Concentration')
    plt.title(f'Breakthrough Curve - {step}')
    plt.legend()
    plt.grid()
    plt.show()

# Plot refined pressure profile with interpolated points
plt.figure(figsize=(10, 6))
plt.plot(time_steps, pressure_values, marker='o', color='blue', label='Pressure Profile')
plt.xlabel('Time (s)')
plt.ylabel('Pressure (bar)')
plt.title('Refined Pressure Profile Across PSA Cycles')
plt.grid()
plt.legend()
plt.show()
