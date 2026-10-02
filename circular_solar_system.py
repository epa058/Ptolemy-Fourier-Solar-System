import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Planet names
names = ['Mercury', 'Venus', 'Earth', 'Moon', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']

# Source: Intuition, colors have been exaggerated
colors = {
    'Mercury': 'dimgrey',
    'Venus': 'orange',
    'Earth':  'blue',
    'Moon':  'grey',
    'Mars':  'red',
    'Jupiter': 'sandybrown',
    'Saturn': 'wheat',
    'Uranus': 'paleturquoise',
    'Neptune': 'dodgerblue',
    'Pluto': 'tan'
}

# --- Source: https://nssdc.gsfc.nasa.gov/planetary/factsheet/planet_table_ratio.html ---

# Orbital radii in astronomical units
orbital_radii = {
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

# Simulation
D = 10000 # duration in Earth years
time = np.arange(365 * D) / 365 # exactly one day per step

positions = {}
for planet in names:
    positions[planet] = np.zeros((len(time), 2))

# Calculate positions assuming circular orbits
for planet in names:
    angle = 2 * np.pi * time / orbital_periods[planet]
    positions[planet][:, 0] = orbital_radii[planet] * np.cos(angle)  # x-coordinate
    positions[planet][:, 1] = orbital_radii[planet] * np.sin(angle)  # y-coordinate

# Adjust moon position relative to Earth
positions['Moon'] += positions['Earth']

# Plot setup
fig, ax = plt.subplots()
ax.set_aspect('equal', 'box')
ax.set_facecolor("black")
lim = 15 # I only want to visualize up to Saturn, the rest was for fun
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)

# Aesthetics
trail_length = 200  # length of the trails

sun = ax.plot(0, 0, 'o', color='yellow', markersize=10, label='Sun')[0]
sun_trail = ax.plot([], [], '-', color='yellow', linewidth=1)[0]

planets = {}
trails = {}
for planet, color in colors.items():
    planets[planet] = ax.plot([], [], 'o', color=color, markersize=2, label=planet)[0]
    trails[planet] = ax.plot([], [], '-', linewidth=1, color=color)[0]

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

# Run animations
# ani = FuncAnimation(fig, update, frames=len(time), blit=True, interval=50)
# ani = FuncAnimation(fig, update_earth_centered, frames=len(time), blit=True, interval=50)
ani = FuncAnimation(fig, update_ptolemaic, frames=len(time), blit=True, interval=50)

# Write data
relative_positions = {}
relative_positions['Sun'] = - positions['Earth']
for planet in names:
    relative_positions[planet] = positions[planet] - positions['Earth']

with open('planetary_positions.txt', 'w') as f:
    for planet, pos in relative_positions.items():
        f.write(f"{planet} positions:\n")
        for p in pos:
            f.write(f"{p[0]}, {p[1]}\n")

print("Data has been written to 'planetary_positions.txt'")


plt.legend()
plt.show()
