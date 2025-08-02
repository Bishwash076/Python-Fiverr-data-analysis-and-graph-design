}
        
        self.results['temperature_profiles'][step_name] = {
            'z': z * self.column_length,
            'T_gas': T_gas_final,
            'T_solid': T_solid_final
        }
        
        # Return final state
        final_state = {
            'c_gas': c_gas_final,
            'q_solid': q_solid_final,
            'T_gas': T_gas_final,
            'T_solid': T_solid_final,
            'pressure': pressure_final
        }
        
        return final_state
    
    def run_simulation(self, num_cycles=5):
        """
        Run the complete PSA simulation for multiple cycles
        
        Parameters:
        -----------
        num_cycles : int
            Number of cycles to simulate
        """
        # Check if column dimensions are set
        if self.column_diameter is None or self.column_length is None:
            self.calculate_column_dimensions()
        
        # Initialize state for first cycle
        n_components = len(self.components)
        n_z = self.num_nodes
        
        # Initialize with uniform conditions
        c_gas_init = np.zeros((n_components, n_z))
        q_solid_init = np.zeros((n_components, n_z))
        T_gas_init = np.ones(n_z) * self.temperature
        T_solid_init = np.ones(n_z) * self.temperature
        
        initial_state = {
            'c_gas': c_gas_init,
            'q_solid': q_solid_init,
            'T_gas': T_gas_init,
            'T_solid': T_solid_init,
            'pressure': self.pressure_low
        }
        
        # Storage for cycle performance metrics
        cycle_metrics = {
            'purity': np.zeros(num_cycles),
            'recovery': np.zeros(num_cycles)
        }
        
        # Initialize storage for cycle data
        self.results['cycles'] = {}
        
        # Run simulation for specified number of cycles
        for cycle in range(num_cycles):
            print(f"Simulating cycle {cycle+1}/{num_cycles}...")
            
            # Storage for cycle data
            cycle_data = {
                'pressure': [],
                'outlet_composition': {comp: [] for comp in self.components},
                'time': []
            }
            
            # Run each step in the cycle
            current_state = initial_state.copy()
            cycle_time = 0
            
            # Track product (H2) collected and feed processed
            h2_feed = 0
            h2_product = 0
            
            for step_name in self.cycle_steps:
                print(f"  Running step: {step_name}")
                
                # Run this step
                final_state = self.run_cycle_step(step_name, current_state)
                
                # Update current state for next step
                current_state = final_state
                
                # Record data for pressure profile
                step_time = self.step_times[step_name]
                time_points = np.linspace(cycle_time, cycle_time + step_time, 20)
                
                # Simplified pressure profile based on step
                if step_name == 'adsorption':
                    pressure = np.ones_like(time_points) * self.pressure_high
                elif step_name == 'blowdown':
                    pressure = np.linspace(self.pressure_high, self.pressure_low, len(time_points))
                elif step_name == 'purge':
                    pressure = np.ones_like(time_points) * self.pressure_low
                elif step_name == 'repressurization':
                    pressure = np.linspace(self.pressure_low, self.pressure_high, len(time_points))
                elif step_name == 'pressure_equalization_down':
                    mid_pressure = (self.pressure_high + self.pressure_low) / 2
                    pressure = np.linspace(self.pressure_high, mid_pressure, len(time_points))
                elif step_name == 'pressure_equalization_up':
                    mid_pressure = (self.pressure_high + self.pressure_low) / 2
                    pressure = np.linspace(mid_pressure, self.pressure_high, len(time_points))
                else:
                    pressure = np.ones_like(time_points) * current_state['pressure']
                
                # Store pressure data
                cycle_data['time'].extend(time_points)
                cycle_data['pressure'].extend(pressure)
                
                # Store outlet composition data
                # For adsorption step, track outlet composition for raffinate (H2 product)
                if step_name == 'adsorption':
                    # Feed composition
                    for comp in self.components:
                        feed_moles = self.feed_flow * self.step_times[step_name] * self.feed_composition[comp]
                        if comp == 'H2':
                            h2_feed += feed_moles
                    
                    # Product composition (raffinate at column outlet)
                    outlet_comp = {}
                    total_outlet = 0
                    for i, comp in enumerate(self.components):
                        outlet_conc = final_state['c_gas'][i, -1]
                        outlet_comp[comp] = outlet_conc
                        total_outlet += outlet_conc
                    
                    # Normalize outlet composition
                    for comp in self.components:
                        if total_outlet > 0:
                            outlet_comp[comp] /= total_outlet
                        else:
                            outlet_comp[comp] = 0
                    
                    # Store composition for each time point
                    for comp in self.components:
                        cycle_data['outlet_composition'][comp].extend([outlet_comp[comp]] * len(time_points))
                    
                    # Calculate H2 in product
                    if 'H2' in self.components and total_outlet > 0:
                        h2_idx = self.components.index('H2')
                        h2_product += final_state['c_gas'][h2_idx, -1] * outlet_comp['H2'] * self.column_length * np.pi * (self.column_diameter/2)**2 * self.bed_porosity
                else:
                    # For other steps, use a placeholder for outlet composition
                    for comp in self.components:
                        cycle_data['outlet_composition'][comp].extend([0] * len(time_points))
                
                # Update cycle time
                cycle_time += step_time
            
            # Calculate product purity and recovery
            if h2_feed > 0:
                recovery = h2_product / h2_feed * 100
            else:
                recovery = 0
            
            # Average H2 purity in raffinate
            h2_comp_values = cycle_data['outlet_composition']['H2']
            purity = sum(h2_comp_values) / len(h2_comp_values) * 100 if h2_comp_values else 0
            
            # Store metrics
            cycle_metrics['purity'][cycle] = purity
            cycle_metrics['recovery'][cycle] = recovery
            
            # Store cycle data
            self.results['cycles'][cycle] = cycle_data
            
            # Print cycle performance
            print(f"  Cycle {cycle+1} performance:")
            print(f"    H2 purity: {purity:.2f}%")
            print(f"    H2 recovery: {recovery:.2f}%")
            
            # Use final state of this cycle as initial state for next cycle
            initial_state = current_state.copy()
        
        # Store overall performance metrics
        self.results['final_purity'] = cycle_metrics['purity'][-1]
        self.results['final_recovery'] = cycle_metrics['recovery'][-1]
        
        print("\nSimulation completed.")
        print(f"Final H2 purity: {self.results['final_purity']:.2f}%")
        print(f"Final H2 recovery: {self.results['final_recovery']:.2f}%")
    
    def plot_pressure_profile(self):
        """
        Plot pressure profile for the entire cycle
        """
        if not self.results['cycles']:
            print("No simulation results available. Run simulation first.")
            return
        
        plt.figure(figsize=(12, 6))
        
        # Use the last cycle for plotting
        last_cycle = max(self.results['cycles'].keys())
        cycle_data = self.results['cycles'][last_cycle]
        
        # Plot pressure profile
        plt.plot(cycle_data['time'], cycle_data['pressure'])
        
        # Mark cycle steps
        time_markers = [0]
        for step in self.cycle_steps:
            time_markers.append(time_markers[-1] + self.step_times[step])
        
        # Add vertical lines to separate steps
        for marker in time_markers[1:-1]:
            plt.axvline(x=marker, color='gray', linestyle='--', alpha=0.5)
        
        # Add step labels
        for i, step in enumerate(self.cycle_steps):
            mid_time = (time_markers[i] + time_markers[i+1]) / 2
            plt.text(mid_time, max(cycle_data['pressure']) * 1.05, step, 
                     horizontalalignment='center', verticalalignment='bottom', rotation=45)
        
        plt.xlabel('Time (s)')
        plt.ylabel('Pressure (bar)')
        plt.title('PSA Cycle Pressure Profile')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    def plot_breakthrough_curves(self, step_name='adsorption'):
        """
        Plot breakthrough curves (concentration vs column length) for a specific step
        
        Parameters:
        -----------
        step_name : str
            Name of the cycle step to plot
        """
        if not self.results['concentration_profiles'] or step_name not in self.results['concentration_profiles']:
            print(f"No concentration profiles available for {step_name}. Run simulation first.")
            return
        
        plt.figure(figsize=(12, 6))
        
        # Get concentration profiles for the specified step
        z = self.results['concentration_profiles'][step_name]['z']
        c_gas = self.results['concentration_profiles'][step_name]['c_gas']
        
        # Plot concentration profiles for each component
        for i, comp in enumerate(self.components):
            plt.plot(z, c_gas[i, :], label=comp)
        
        plt.xlabel('Column Length (m)')
        plt.ylabel('Concentration (mol/m³)')
        plt.title(f'Breakthrough Curve for {step_name} Step')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    def plot_temperature_profiles(self, step_name='adsorption'):
        """
        Plot temperature profiles for a specific step
        
        Parameters:
        -----------
        step_name : str
            Name of the cycle step to plot
        """
        if not self.results['temperature_profiles'] or step_name not in self.results['temperature_profiles']:
            print(f"No temperature profiles available for {step_name}. Run simulation first.")
            return
        
        plt.figure(figsize=(12, 6))
        
        # Get temperature profiles for the specified step
        z = self.results['temperature_profiles'][step_name]['z']
        T_gas = self.results['temperature_profiles'][step_name]['T_gas']
        T_solid = self.results['temperature_profiles'][step_name]['T_solid']
        
        # Plot temperature profiles
        plt.plot(z, T_gas, label='Gas Phase')
        plt.plot(z, T_solid, label='Solid Phase')
        
        plt.xlabel('Column Length (m)')
        plt.ylabel('Temperature (K)')
        plt.title(f'Temperature Profiles for {step_name} Step')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    def plot_outlet_composition(self):
        """
        Plot outlet composition over time for the last cycle
        """
        if not self.results['cycles']:
            print("No simulation results available. Run simulation first.")
            return
        
        plt.figure(figsize=(12, 6))
        
        # Use the last cycle for plotting
        last_cycle = max(self.results['cycles'].keys())
        cycle_data = self.results['cycles'][last_cycle]
        
        # Plot composition for each component
        for comp in self.components:
            plt.plot(cycle_data['time'], cycle_data['outlet_composition'][comp], label=comp)
        
        # Mark cycle steps
        time_markers = [0]
        for step in self.cycle_steps:
            time_markers.append(time_markers[-1] + self.step_times[step])
        
        # Add vertical lines to separate steps
        for marker in time_markers[1:-1]:
            plt.axvline(x=marker, color='gray', linestyle='--', alpha=0.5)
        
        # Add step labels
        for i, step in enumerate(self.cycle_steps):
            mid_time = (time_markers[i] + time_markers[i+1]) / 2
            plt.text(mid_time, 1.05, step, 
                     horizontalalignment='center', verticalalignment='bottom', rotation=45)
        
        plt.xlabel('Time (s)')
        plt.ylabel('Mole Fraction')
        plt.title('Outlet Composition Profile')
        plt.legend()
        plt.grid(True)
        plt.ylim(0, 1.1)
        plt.tight_layout()
        plt.show()
    
    def plot_performance_metrics(self):
        """
        Plot purity and recovery over cycles
        """
        if not hasattr(self.results, 'final_purity') or not hasattr(self.results, 'final_recovery'):
            print("No performance metrics available. Run simulation first.")
            return
        
        plt.figure(figsize=(12, 6))
        
        # Get cycle numbers
        cycles = list(self.results['cycles'].keys())
        
        # Extract purity and recovery values
        purity = [self.results['cycles'][cycle]['purity'] for cycle in cycles]
        recovery = [self.results['cycles'][cycle]['recovery'] for cycle in cycles]
        
        # Plot metrics
        plt.plot(cycles, purity, 'bo-', label='H2 Purity (%)')
        plt.plot(cycles, recovery, 'ro-', label='H2 Recovery (%)')
        
        plt.xlabel('Cycle Number')
        plt.ylabel('Percentage (%)')
        plt.title('PSA Performance Metrics')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()
    
    def save_results(self, filename='psa_simulation_results.npz'):
        """
        Save simulation results to a file
        
        Parameters:
        -----------
        filename : str
            Name of the output file
        """
        np.savez(filename, results=self.results)
        print(f"Results saved to {filename}")


# Example usage
if __name__ == "__main__":
    # Create simulation object
    psa = PSASimulation()
    
    # Get user input
    psa.get_user_input()
    
    # Load adsorbent data
    # You can either load from a file or provide data directly
    # For this example, we'll use default values
    psa.load_adsorbent_data()
    
    # Set bed properties
    psa.set_bed_properties(porosity=0.4, particle_porosity=0.5, 
                          particle_diameter=0.002, adsorbent_density=1100.0)
    
    # Set cycle parameters
    cycle_steps = ['adsorption', 'pressure_equalization_down', 'blowdown', 
                  'purge', 'pressure_equalization_up', 'repressurization']
    step_times = {
        'adsorption': 120.0,
        'pressure_equalization_down': 30.0,
        'blowdown': 60.0,
        'purge': 90.0,
        'pressure_equalization_up': 30.0,
        'repressurization': 60.0
    }
    psa.set_cycle_parameters(cycle_steps=cycle_steps, step_times=step_times)
    
    # Calculate column dimensions
    psa.calculate_column_dimensions()
    
    # Run simulation
    psa.run_simulation(num_cycles=3)
    
    # Plot results
    psa.plot_pressure_profile()
    psa.plot_breakthrough_curves()
    psa.plot_temperature_profiles()
    psa.plot_outlet_composition()
    
    # Save results
    psa.save_results()
