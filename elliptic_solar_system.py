import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Planet names
names = ['Mercury', 'Venus', 'Earth', 'Moon', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

# Source: Intuition, colors have been exaggerated
colors = {
    'Mercury': 'dimgrey',
    'Venus':   'orange',
    'Earth':   'blue',
    'Moon':    'grey',
    'Mars':    'red',
    'Jupiter': 'sandybrown',
    'Saturn':  'wheat',
    'Uranus':  'paleturquoise',
    'Neptune': 'dodgerblue',
    'Pluto':   'tan'
}

# --- Source: https://nssdc.gsfc.nasa.gov/planetary/factsheet/planet_table_ratio.html ---

# Semi-major axes in astronomical units
semi_major_axes = {
    'Mercury': 0.387,
    'Venus': 0.723,
    'Earth': 1.000,
    'Moon': 0.00256955,   # relative to Earth
    'Mars': 1.524,
    'Jupiter': 5.204,
    'Saturn': 9.573,
    'Uranus': 19.165,
    'Neptune': 30.180,
    'Pluto': 39.236
}

# Orbital eccentricities
eccentricities = {
    'Mercury': 0.2056,
    'Venus':   0.0068,
    'Earth':   0.0167,
    'Moon':    0.0549,   # relative to Earth
    'Mars':    0.0935,
    'Jupiter': 0.0487,
    'Saturn':  0.0520,
    'Uranus':  0.0469,
    'Neptune': 0.0113,
    'Pluto':   0.2444
}

# Orbital periods in Earth years
orbital_periods = {
    'Mercury': 0.241,
    'Venus':   0.615,
    'Earth':   1.000,
    'Moon':    0.0748,   # relative to Earth
    'Mars':    1.880,
    'Jupiter': 11.900,
    'Saturn':  29.400,
    'Uranus':  83.700,
    'Neptune': 163.700,
    'Pluto':   247.900
}

# Kepler solver
def solve_kepler(M, e, tol=1e-10):
    """
    Solve Kepler's equation M = E - e*sin(E) for the eccentric anomaly E
    given mean anomaly M and eccentricity e, using Newton's method
    """
    E = M.copy()
    for _ in range(1000):
        dE = (M - E + e * np.sin(E)) / (1 - e * np.cos(E))
        E += dE
        if np.max(np.abs(dE)) < tol:
            break
    return E

# Calculate positions (Cartesian coordinates)
def elliptic_orbit(t, a, e, T):
    """
    Parameters
    t: time in Earth years
    a: semi-major axis in AU
    e: orbital eccentricity
    T: orbital period in Earth years

    Method: mean anomaly → eccentric anomaly (Kepler) → true anomaly → (r, θ)
    Planets start at perihelion (closest approach) at t=0.
    """
    n = 2 * np.pi / T # mean motion
    M = (n * t) % (2 * np.pi) # mean anomaly, wrapped to [0, 2pi)
    E = solve_kepler(M, e) # eccentric anomaly
    nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E / 2), np.sqrt(1 - e) * np.cos(E / 2)) # true anomaly
    r = a * (1 - e * np.cos(E)) # heliocentric distance
    return r * np.cos(nu), r * np.sin(nu)

# Simulation
D = 10000 # duration in Earth years
time = np.arange(365 * D) / 365 # exactly one day per step

positions = {}
for planet in names:
    positions[planet] = np.zeros((len(time), 2))
    
for planet in names:
    a = semi_major_axes[planet]
    e = eccentricities[planet]
    T = orbital_periods[planet]
    x, y = elliptic_orbit(time, a, e, T)
    positions[planet][:, 0] = x  # x-coordinate
    positions[planet][:, 1] = y  # y-coordinate

# Adjust moon position relative to Earth
positions['Moon'] += positions['Earth']

# Plot setup
fig, ax = plt.subplots()
ax.set_aspect('equal', 'box')
ax.set_facecolor('black')
lim = 15
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)

# Aesthetics
trail_length = 200 # length of the trails

sun = ax.plot(0, 0, 'o', color='yellow', markersize=10, label='Sun')[0]
sun_trail = ax.plot([], [], '-', color='yellow', linewidth=1)[0]

planets = {}
trails  = {}
for planet, color in colors.items():
    planets[planet] = ax.plot([], [], 'o', color=color, markersize=2, label=planet)[0]
    trails[planet]  = ax.plot([], [], '-', linewidth=1, color=color)[0]

# Three animation versions below

# Standard Solar System
def update(frame):
    for planet in names:
        planets[planet].set_data([positions[planet][frame, 0]], [positions[planet][frame, 1]])
        trail_start = max(0, frame - trail_length)
        trails[planet].set_data(positions[planet][trail_start:frame, 0], positions[planet][trail_start:frame, 1])
    return list(planets.values()) + list(trails.values())

# Earth-centered Solar System
def update_earth_centered(frame):
    # Calculate the shift needed to center on Earth's position
    shift_x = -positions['Earth'][frame, 0]
    shift_y = -positions['Earth'][frame, 1]
    sun.set_data([shift_x], [shift_y])
    
    for planet in names:
        # Adjust positions relative to Earth's current position
        centered_x = positions[planet][frame, 0] + shift_x
        centered_y = positions[planet][frame, 1] + shift_y
        planets[planet].set_data([centered_x], [centered_y])
        
        trail_start = max(0, frame - trail_length)
        trail_x = positions[planet][trail_start:frame, 0] + shift_x
        trail_y = positions[planet][trail_start:frame, 1] + shift_y
        trails[planet].set_data(trail_x, trail_y)
        
    return [sun] + list(planets.values()) + list(trails.values())

# Ptolemaic model of the Solar System
def update_ptolemaic(frame):
    # Make the Earth stationary at the origin
    planets['Earth'].set_data([0], [0])
    
    for planet in names:
        if planet == 'Earth':
            continue
        
        # Calculate relative positions to the Earth
        relative_x = positions[planet][frame, 0] - positions['Earth'][frame, 0]
        relative_y = positions[planet][frame, 1] - positions['Earth'][frame, 1]
        planets[planet].set_data([relative_x], [relative_y])

        # Update trails relative to Earth
        trail_start = max(0, frame - trail_length)
        trail_x = positions[planet][trail_start:frame, 0] - positions['Earth'][trail_start:frame, 0]
        trail_y = positions[planet][trail_start:frame, 1] - positions['Earth'][trail_start:frame, 1]
        trails[planet].set_data([trail_x], [trail_y])

    # Adjust the Sun's position relative to Earth
    sun_x = -positions['Earth'][frame, 0]
    sun_y = -positions['Earth'][frame, 1]
    sun.set_data([sun_x], [sun_y])

    # The Sun has a trail too now
    trail_start_sun = max(0, frame - trail_length)
    trail_sun_x = -positions['Earth'][trail_start_sun:frame, 0]
    trail_sun_y = -positions['Earth'][trail_start_sun:frame, 1]
    sun_trail.set_data([trail_sun_x], [trail_sun_y])
    
    return [sun, sun_trail] + list(planets.values()) + list(trails.values())

# Run animation
# ani = FuncAnimation(fig, update, frames=len(time), blit=True, interval=50)
# ani = FuncAnimation(fig, update_earth_centered, frames=len(time), blit=True, interval=50)
ani = FuncAnimation(fig, update_ptolemaic, frames=len(time), blit=True, interval=50)

# Write data
relative_positions = {}
relative_positions['Sun'] = - positions['Earth']
for planet in names:
    relative_positions[planet] = positions[planet] - positions['Earth']

with open('kepler_planetary_positions.txt', 'w') as f:
    for planet, pos in relative_positions.items():
        f.write(f"{planet} positions:\n")
        for p in pos:
            f.write(f"{p[0]}, {p[1]}\n")

print("Data written to 'kepler_planetary_positions.txt'")

# Binary copy for fft.py: one (N, 2) array of [x, y] per body, keyed by name
np.savez('kepler_planetary_positions.npz', **relative_positions)
print("Data written to 'kepler_planetary_positions.npz'")

plt.legend(loc='upper right')
plt.show()
