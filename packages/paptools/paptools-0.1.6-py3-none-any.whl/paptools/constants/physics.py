import numpy as np
from ..core.number import Number

# === Fundamental constants (CODATA 2019) ===

c = Number(2.99792458e8, None, symbol="c", unit="m/s")
# Speed of light (exact)

G = Number(6.67430e-11, 1.5e-15, symbol="G", unit="m**3/(kg*s**2)")
# Newtonian gravitational constant

h = Number(6.62607015e-34, None, symbol="h", unit="J*s")
# Planck constant (exact)

hbar = Number(1.054571817e-34, None, symbol="\\hbar ", unit="J*s")
# Reduced Planck constant ℏ (exact because h is exact)

mu0 = Number(4e-7 * np.pi, None, symbol="\\mu_0", unit="N/A**2")
# Vacuum permeability μ₀ (defined exactly)

epsilon0 = Number(8.8541878128e-12, 1.3e-21, symbol="\\varepsilon_0 ", unit="F/m")
# Vacuum permittivity ε₀

k_B = Number(1.380649e-23, None, symbol="k_B", unit="J/K")
# Boltzmann constant (exact)

N_A = Number(6.02214076e23, None, symbol="N_A", unit="1/mol")
# Avogadro constant (exact)

R = Number(8.314462618, None, symbol="R", unit="J/(mol*K)")
# Gas constant (derived from exact constants: exact)

sigma = Number(5.670374419e-8, None, symbol="\\sigma ", unit="W/(m**2*K**4)")
# Stefan–Boltzmann constant σ (derived from exact constants: exact)

mu_B = Number(9.2740100783e-24, 2.8e-33, symbol="\\mu_B", unit="J/T")
# Bohr magneton μ_B

mu_N = Number(5.0507837461e-27, 1.5e-36, symbol="\\mu_N", unit="J/T")
# Nuclear magneton μ_N

alpha = Number(7.2973525693e-3, 1.1e-12, symbol="\\alpha ")
# Fine-structure constant α (dimensionless)

e_charge = Number(1.602176634e-19, None, symbol="e", unit="C")
# Elementary charge (exact)

# === Particle masses ===

m_e = Number(9.1093837015e-31, 2.8e-40, symbol="m_e", unit="kg")
# Electron mass

m_p = Number(1.67262192369e-27, 5.1e-37, symbol="m_p", unit="kg")
# Proton mass

m_n = Number(1.67492749804e-27, 7.5e-37, symbol="m_n", unit="kg")
# Neutron mass

e_charge = Number(1.602176634e-19, None, symbol="e", unit="C")
# Elementary charge (exact)


# === Atomic constants ===

a0 = Number(5.29177210903e-11, 8.1e-21, symbol="a_0", unit="m")
# Bohr radius a₀

R_inf = Number(1.0973731568160e7, 2.1e-13, symbol="R_\\infty", unit="1/m")
# Rydberg constant R_∞


# === Astronomical constants ===

AU = Number(1.495978707e11, None, symbol="\\mathrm{AU}", unit="m")
# Astronomical unit (exact)

ly = Number(9.460730472e15, None, symbol="\\mathrm{ly}", unit="m")
# Light-year (exact, definition-based)

parsec = Number(3.08567758149137e16, None, symbol="\\mathrm{pc}", unit="m")
# Parsec (defined exactly from AU)


# === Derived constants ===

Z0 = Number((4*np.pi*1e-7) * 2.99792458e8, None, symbol="Z_0", unit="ohm")
# Vacuum impedance Z₀ (derived from exact constants)

k_e = Number(1 / (4 * np.pi * 8.8541878128e-12), 1e-21, symbol="k_e", unit="N*m**2/C**2")
# Coulomb constant kₑ
