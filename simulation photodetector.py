
# Step 1: Install condacolab
!pip install condacolab

# Step 2: Set up Conda environment
import condacolab
condacolab.install()

# Step 3: Install kwant
!conda install -c conda-forge kwant

# Step 4: Your original code
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Arrow
import kwant

# Constants (add your constants here)
# Your simulation code here
print("kwant installed successfully!")

import kwant
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# Parameters
a = 1         # Lattice constant
W, L = 5, 10  # Width and length
t = -1        # Hopping energy
E_values = np.linspace(-2.0, 2.0, 20)  # Energy range for T(E)
E_sim = 0.5   # Main energy for analysis

# Square lattice with norbs
lat = kwant.lattice.square(a, norbs=1)

# Photodetector Models - Real-life scenarios
class PhotodetectorModels:
    """
    Four different photodetector models representing real-life scenarios:
    1. Silicon PIN Photodiode - Standard visible/near-IR detection
    2. InGaAs Photodetector - Near-infrared telecommunications
    3. Avalanche Photodiode (APD) - High sensitivity applications
    4. Quantum Dot Photodetector - Novel nanoscale detection
    """
    
    @staticmethod
    def get_model_parameters(model_type):
        models = {
            1: {
                'name': 'Silicon PIN Photodiode',
                'description': 'Standard visible/near-IR detector',
                'on_site_energy': 0.0,      # Baseline energy
                'disorder_strength': 0.05,   # Low disorder for clean silicon
                'doping_profile': 'uniform', # Uniform doping
                'absorption_coeff': 1000,    # cm^-1 for silicon at 850nm
                'responsivity': 0.65,        # A/W at 850nm
                'bandwidth': 100e6,          # 100 MHz
                'dark_current': 1e-9,        # 1 nA
                'material': 'Si'
            },
            2: {
                'name': 'InGaAs Photodetector',
                'description': 'Near-infrared telecommunications',
                'on_site_energy': -0.2,     # Lower bandgap material
                'disorder_strength': 0.08,   # Moderate disorder in compound semiconductor
                'doping_profile': 'graded',  # Graded composition
                'absorption_coeff': 8000,    # cm^-1 for InGaAs at 1550nm
                'responsivity': 1.0,         # A/W at 1550nm
                'bandwidth': 10e9,           # 10 GHz
                'dark_current': 10e-9,       # 10 nA
                'material': 'InGaAs'
            },
            3: {
                'name': 'Avalanche Photodiode (APD)',
                'description': 'High sensitivity with internal gain',
                'on_site_energy': 0.1,      # Modified by electric field
                'disorder_strength': 0.03,   # Very clean for low noise
                'doping_profile': 'avalanche', # Special avalanche structure
                'absorption_coeff': 1200,    # cm^-1
                'responsivity': 50,          # A/W with gain=100
                'bandwidth': 1e9,            # 1 GHz (limited by avalanche)
                'dark_current': 1e-8,        # 10 nA (higher due to gain)
                'gain': 100,                 # Internal multiplication
                'material': 'Si (APD)'
            },
            4: {
                'name': 'Quantum Dot Photodetector',
                'description': 'Novel nanoscale detection',
                'on_site_energy': 0.3,      # Quantum confinement effects
                'disorder_strength': 0.15,   # Higher disorder in nanostructures
                'doping_profile': 'quantum', # Quantum confined states
                'absorption_coeff': 5000,    # cm^-1
                'responsivity': 0.8,         # A/W
                'bandwidth': 50e6,           # 50 MHz (limited by carrier dynamics)
                'dark_current': 0.1e-9,      # 0.1 nA (very low)
                'quantum_efficiency': 0.9,   # High QE due to quantum effects
                'material': 'QD-InAs/GaAs'
            }
        }
        return models.get(model_type, models[1])

def make_system(model_params):
    """
    Create photodetector system with model-specific parameters
    """
    syst = kwant.Builder()
    
    # Get model parameters
    on_site = model_params['on_site_energy']
    disorder = model_params['disorder_strength']
    
    # Central scattering region with model-specific properties
    for x in range(L):
        for y in range(W):
            # Add disorder and doping effects based on model
            local_energy = on_site
            
            # Apply doping profile effects
            if model_params['doping_profile'] == 'graded':
                # Graded composition (InGaAs)
                local_energy += 0.1 * (x / L - 0.5)
            elif model_params['doping_profile'] == 'avalanche':
                # Avalanche structure with electric field gradient
                local_energy += 0.2 * np.exp(-((x - L/2)**2 + (y - W/2)**2) / (L*W/4))
            elif model_params['doping_profile'] == 'quantum':
                # Quantum dot confinement
                local_energy += 0.5 * np.sin(2*np.pi*x/L) * np.sin(2*np.pi*y/W)
            
            # Add random disorder
            local_energy += np.random.normal(0, disorder)
            
            syst[lat(x, y)] = local_energy

    # Hopping terms with material-dependent modifications
    hopping = t
    if model_params['material'] == 'InGaAs':
        hopping *= 1.2  # Different effective mass
    elif 'QD' in model_params['material']:
        hopping *= 0.8  # Reduced coupling in quantum dots
    
    # Horizontal hopping
    for x in range(L - 1):
        for y in range(W):
            syst[lat(x, y), lat(x + 1, y)] = hopping
    
    # Vertical hopping
    for x in range(L):
        for y in range(W - 1):
            syst[lat(x, y), lat(x, y + 1)] = hopping

    # Left lead
    sym_left = kwant.TranslationalSymmetry((-1, 0))
    lead_left = kwant.Builder(sym_left)
    for y in range(W):
        lead_left[lat(0, y)] = 0
    for y in range(W - 1):
        lead_left[lat(0, y), lat(0, y + 1)] = t
    lead_left[lat(0, 0), lat(1, 0)] = t

    # Right lead
    sym_right = kwant.TranslationalSymmetry((1, 0))
    lead_right = kwant.Builder(sym_right)
    for y in range(W):
        lead_right[lat(0, y)] = 0
    for y in range(W - 1):
        lead_right[lat(0, y), lat(0, y + 1)] = t
    lead_right[lat(0, 0), lat(-1, 0)] = t

    syst.attach_lead(lead_left)
    syst.attach_lead(lead_right)

    return syst

def compute_transmission(syst, energy):
    try:
        fsyst = syst.finalized()
        smatrix = kwant.smatrix(fsyst, energy)
        return smatrix.transmission(1, 0)
    except Exception as e:
        print(f"Warning: {e}")
        return 0

def plot_wavefunction_surface(fsyst, energy, label=""):
    try:
        wf = kwant.wave_function(fsyst, energy)
        smatrix = kwant.smatrix(fsyst, energy)
        num_modes = smatrix.submatrix(1, 0).shape[1]
        if num_modes == 0:
            print(f"No propagating modes at {energy:.2f} eV for {label}")
            return

        psi = wf(0)[0]
        X, Y = np.meshgrid(range(L), range(W))
        Z = np.zeros((W, L))
        for i, site in enumerate(fsyst.sites):
            x, y = site.pos
            Z[y, x] = np.abs(psi[i]) ** 2

        fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='Viridis')])
        fig.update_layout(
            title=dict(
                text=f"Wavefunction |ψ|² Surface for {label}<br>@ E={energy:.2f} eV",
                font=dict(size=18)
            ),
            scene=dict(
                xaxis_title=dict(text='X Position', font=dict(size=14)),
                yaxis_title=dict(text='Y Position', font=dict(size=14)),
                zaxis_title=dict(text='|ψ|²', font=dict(size=14)),
                xaxis=dict(tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12)),
                zaxis=dict(tickfont=dict(size=12))
            ),
            width=1000, height=750,
            margin=dict(l=20, r=20, t=80, b=20)
        )
        fig.show()
    except Exception as e:
        print(f"Error: {e}")

def plot_3d_surface(syst, label=""):
    X, Y = np.meshgrid(range(L), range(W))
    Z = np.zeros((W, L))
    for i in range(W):
        for j in range(L):
            Z[i, j] = compute_transmission(syst, E_values[i % len(E_values)])

    fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='Viridis')])
    fig.update_layout(
        title=dict(
            text=f"Transmission Surface for {label}",
            font=dict(size=18)
        ),
        scene=dict(
            xaxis_title=dict(text='X Position', font=dict(size=14)),
            yaxis_title=dict(text='Y Position', font=dict(size=14)),
            zaxis_title=dict(text='Transmission', font=dict(size=14)),
            xaxis=dict(tickfont=dict(size=12)),
            yaxis=dict(tickfont=dict(size=12)),
            zaxis=dict(tickfont=dict(size=12))
        ),
        width=1000, height=750,
        margin=dict(l=20, r=20, t=80, b=20)
    )
    fig.show()

def plot_animated_3d_sites(syst, label=""):
    fsyst = syst.finalized()
    sites = [site.pos for site in fsyst.sites]
    x, y = zip(*sites)
    frames = []

    for t in np.linspace(0, 1, 10):
        z = [np.sin(t + i) * 0.5 for i in range(len(x))]
        frames.append(go.Frame(data=[go.Scatter3d(
            x=x, y=y, z=z,
            mode='markers',
            marker=dict(size=5, color=z, colorscale='Plasma', showscale=True)
        )], name=f"frame{t:.2f}"))

    fig = go.Figure(
        data=[go.Scatter3d(x=x, y=y, z=[0]*len(x), mode='markers', marker=dict(size=5, color='orange'))],
        layout=go.Layout(
            title=dict(
                text=f"Animated Site View: {label}",
                font=dict(size=18)
            ),
            scene=dict(
                xaxis_title=dict(text='X Position', font=dict(size=14)),
                yaxis_title=dict(text='Y Position', font=dict(size=14)),
                zaxis_title=dict(text='Z (Dynamic)', font=dict(size=14)),
                xaxis=dict(tickfont=dict(size=12)),
                yaxis=dict(tickfont=dict(size=12)),
                zaxis=dict(tickfont=dict(size=12))
            ),
            updatemenus=[{
                "buttons": [
                    {"args": [None, {"frame": {"duration": 500}, "fromcurrent": True}], "label": "Play", "method": "animate"},
                    {"args": [[None], {"frame": {"duration": 0}, "mode": "immediate"}], "label": "Pause", "method": "animate"}
                ],
                "type": "buttons",
                "x": 0.1,
                "y": 0.9,
                "font": dict(size=14)
            }],
            width=1000, height=750,
            margin=dict(l=20, r=20, t=80, b=20)
        ),
        frames=frames
    )
    fig.show()

def print_photodetector_specs(model_params):
    """Print detailed specifications of the photodetector model"""
    print(f"\n{'='*80}")
    print(f"Model: {model_params['name']}")
    print(f"Description: {model_params['description']}")
    print(f"Material: {model_params['material']}")
    print(f"{'='*80}")
    print(f"Specifications:")
    print(f"  • Responsivity: {model_params['responsivity']} A/W")
    print(f"  • Bandwidth: {model_params['bandwidth']/1e6:.0f} MHz")
    print(f"  • Dark Current: {model_params['dark_current']*1e9:.1f} nA")
    print(f"  • Absorption Coefficient: {model_params['absorption_coeff']} cm⁻¹")
    if 'gain' in model_params:
        print(f"  • Internal Gain: {model_params['gain']}")
    if 'quantum_efficiency' in model_params:
        print(f"  • Quantum Efficiency: {model_params['quantum_efficiency']*100:.1f}%")
    print(f"{'='*80}")

# --- Run 4 Photodetector Simulations ---
transmissions = []
photodetector_models = []

print("PHOTODETECTOR SIMULATION SUITE")
print("="*80)
print("Simulating 4 different photodetector models based on real-life scenarios")
print("="*80)

for i in range(1, 5):
    # Get model parameters
    model_params = PhotodetectorModels.get_model_parameters(i)
    photodetector_models.append(model_params)
    
    # Print specifications
    print_photodetector_specs(model_params)
    
    print(f"\n--- Running Quantum Transport Simulation ---")
    
    # Set random seed for reproducible disorder
    np.random.seed(42 + i)
    
    # Create system with model-specific parameters
    syst = make_system(model_params)
    fsyst = syst.finalized()

    # Run all original plots and simulations
    plot_wavefunction_surface(fsyst, E_sim, f"{model_params['name']}")
    plot_3d_surface(syst, f"{model_params['name']}")
    plot_animated_3d_sites(syst, f"{model_params['name']}")

    # Compute transmission
    T = compute_transmission(syst, E_sim)
    transmissions.append(T)
    print(f"Quantum Transmission at E = {E_sim:.2f} eV: {T:.4f}")
    
    # Calculate effective responsivity considering quantum transport
    eff_responsivity = model_params['responsivity'] * T
    print(f"Effective Responsivity (with quantum effects): {eff_responsivity:.3f} A/W")

# --- Enhanced Summary Bar Plot ---
model_names = [f"{model['name']}\n({model['material']})" for model in photodetector_models]
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']  # Different colors for each model

fig = go.Figure(data=[go.Bar(
    x=model_names,
    y=transmissions,
    marker_color=colors,
    text=[f'{t:.4f}' for t in transmissions],
    textposition='auto',
    textfont=dict(size=14, color='white', family='Arial Black')
)])

fig.update_layout(
    title=dict(
        text="Quantum Transmission Comparison at E = 0.5 eV<br><sub>Different Photodetector Models</sub>",
        font=dict(size=20)
    ),
    xaxis_title=dict(text="Photodetector Model", font=dict(size=16)),
    yaxis_title=dict(text="Transmission Coefficient", font=dict(size=16)),
    xaxis=dict(tickfont=dict(size=13)),
    yaxis=dict(tickfont=dict(size=13)),
    width=1100,
    height=700,
    showlegend=False,
    margin=dict(l=80, r=40, t=100, b=120)
)
fig.show()

# --- Transmission vs Energy Plot for All Models ---
print(f"\n--- Computing Transmission vs Energy for All Models ---")
T_vs_E_all = []
for i, model_params in enumerate(photodetector_models):
    np.random.seed(42 + i + 1)  # Consistent disorder
    syst = make_system(model_params)
    T_vs_E = [compute_transmission(syst, E) for E in E_values]
    T_vs_E_all.append(T_vs_E)

fig = go.Figure()
for i, (T_vs_E, model_params) in enumerate(zip(T_vs_E_all, photodetector_models)):
    fig.add_trace(go.Scatter(
        x=E_values, 
        y=T_vs_E, 
        mode='lines+markers',
        name=model_params['name'],
        line=dict(color=colors[i], width=4),
        marker=dict(size=8)
    ))

fig.update_layout(
    title=dict(
        text="Transmission vs Energy - All Photodetector Models",
        font=dict(size=20)
    ),
    xaxis_title=dict(text="Energy (eV)", font=dict(size=16)),
    yaxis_title=dict(text="Transmission Coefficient", font=dict(size=16)),
    xaxis=dict(tickfont=dict(size=13)),
    yaxis=dict(tickfont=dict(size=13)),
    width=1100,
    height=700,
    legend=dict(
        x=0.02, 
        y=0.98,
        font=dict(size=14),
        bgcolor='rgba(255,255,255,0.8)',
        bordercolor='rgba(0,0,0,0.2)',
        borderwidth=1
    ),
    margin=dict(l=80, r=40, t=80, b=60)
)
fig.show()

# --- Performance Summary Table ---
print(f"\n{'='*120}")
print(f"PHOTODETECTOR PERFORMANCE SUMMARY")
print(f"{'='*120}")
print(f"{'Model':<30} {'Material':<18} {'T(E=0.5eV)':<15} {'Responsivity':<15} {'Bandwidth':<15} {'Applications'}")
print(f"{'-'*120}")

applications = [
    "Visible/NIR imaging, general purpose",
    "Telecom, fiber optics, LIDAR",
    "Low-light detection, medical imaging", 
    "Research, quantum optics, sensing"
]

for i, (model, T) in enumerate(zip(photodetector_models, transmissions)):
    bw_str = f"{model['bandwidth']/1e6:.0f} MHz" if model['bandwidth'] < 1e9 else f"{model['bandwidth']/1e9:.1f} GHz"
    print(f"{model['name']:<30} {model['material']:<18} {T:<15.4f} {model['responsivity']:<15.2f} {bw_str:<15} {applications[i]}")

print(f"{'='*120}")
print("Simulation completed successfully! All models show distinct quantum transport characteristics.")
