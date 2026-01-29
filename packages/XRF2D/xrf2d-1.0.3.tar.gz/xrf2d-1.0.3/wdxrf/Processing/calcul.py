"""
This module calculates the surface mass density of MoS₂ based on its 
hexagonal crystal structure and molar mass parameters.
"""

import math

# Crystallographic parameters of MoS₂ (hexagonal structure)
a = 3.16  # Lattice parameter 'a' in angstroms
c = 12.30  # Lattice parameter 'c' in angstroms (not used here)

# Molar masses (in g/mol)
mass_Mo = 95.94
mass_S = 32.06
mass_MoS2 = mass_Mo + 2 * mass_S  # Molar mass of MoS₂

# Number of MoS₂ units per unit cell in hexagonal structure
num_units = 2

# Calculate the area of the hexagonal unit cell in Å²
unit_cell_area = (math.sqrt(3) / 2) * a**2  # in Å²

# Convert unit cell area from Å² to cm²: 1 Å² = 1e-16 cm²
unit_cell_area_cm2 = unit_cell_area * 1e-16

# Calculate the surface mass density in g/cm²
surface_mass_density = (num_units * mass_MoS2) / unit_cell_area_cm2

# Display the result
print(f"Surface mass density of MoS₂: {surface_mass_density:.4f} g/cm²")