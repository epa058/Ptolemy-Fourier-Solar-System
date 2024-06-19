import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Orbital radii for the planets and the Moon in astronomical units
# https://nssdc.gsfc.nasa.gov/planetary/factsheet/planet_table_ratio.html
orbital_radii = {
    'Mercury': 0.387,
    'Venus': 0.723,
    'Earth': 1.00,
    'Moon': 0.00257,  # relative to Earth
    'Mars': 1.52,
    'Jupiter': 5.20,
    'Saturn': 9.57,
    'Uranus': 19.17,
    'Neptune': 30.18,
    'Pluto': 39.48
}

# Orbital period for the planets and the Moon in Earth years
# https://nssdc.gsfc.nasa.gov/planetary/factsheet/planet_table_ratio.html
orbital_periods = {
    'Mercury': 0.241,
    'Venus': 0.615,
    'Earth': 1.00,
    'Moon': 0.0748,  # relative to Earth
    'Mars': 1.88,
    'Jupiter': 11.9,
    'Saturn': 29.4,
    'Uranus': 83.7,
    'Neptune': 163.7,
    'Pluto': 247.9
}

# Animation duration of 'D' Earth years
D = 2
time = np.linspace(0, D, 500)

# Array of positions
positions = {}
for planet in orbital_radii:
    positions[planet] = np.zeros((len(time), 2))

# Calculate positions assuming circular orbits
for planet in orbital_radii:
    angle = 2 * np.pi * time / orbital_periods[planet]
    positions[planet][:, 0] = orbital_radii[planet] * np.cos(angle)  # x-coordinate
    positions[planet][:, 1] = orbital_radii[planet] * np.sin(angle)  # y-coordinate

# Adjust moon position relative to Earth
positions['Moon'] += positions['Earth']

# Plot setup
fig, ax = plt.subplots()
ax.set_aspect('equal', 'box')
lim = 15 # I only want to visualize up to Saturn, the rest was for fun
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)

# Aesthetics
sun = ax.plot(0, 0, 'o', color='yellow', markersize=10, label='Sun')[0] 
sun_trail = ax.plot([], [], '-', color='yellow', linewidth=1)[0]
# Change marker size and color per planet
planets = {planet: ax.plot([], [], 'o', label=planet)[0] for planet in orbital_radii}
trails = {planet: ax.plot([], [], '-', linewidth=1)[0] for planet in orbital_radii}
trail_length = 200  # length of the trail

def update(frame):
    for planet in orbital_radii:
        planets[planet].set_data(positions[planet][frame, 0], positions[planet][frame, 1])
        start = max(0, frame - trail_length)
        trails[planet].set_data(positions[planet][start:frame, 0], positions[planet][start:frame, 1])
    return list(planets.values()) + list(trails.values())

def update_geocentric(frame):
    # Calculate the shift needed to center on Earth's position
    shift_x, shift_y = -positions['Earth'][frame, 0], -positions['Earth'][frame, 1]
    sun.set_data(shift_x, shift_y)  # Move Sun to stay centered relative to Earth

    for planet in orbital_radii:
        # Adjust positions relative to Earth's current position
        centered_x = positions[planet][frame, 0] + shift_x
        centered_y = positions[planet][frame, 1] + shift_y
        planets[planet].set_data(centered_x, centered_y)

        start = max(0, frame - trail_length)
        trail_x = positions[planet][start:frame, 0] + shift_x
        trail_y = positions[planet][start:frame, 1] + shift_y
        trails[planet].set_data(trail_x, trail_y)

    return [sun] + list(planets.values()) + list(trails.values())

def update_ptolemaic(frame):
    # Earth is stationary, we only update its trail for visual consistency
    earth_x, earth_y = 0, 0
    planets['Earth'].set_data(earth_x, earth_y)
    trails['Earth'].set_data([earth_x] * frame, [earth_y] * frame)

    for planet in orbital_radii:
        if planet == 'Earth':
            continue
        # Calculate relative positions to the Earth
        relative_x = positions[planet][frame, 0] - positions['Earth'][frame, 0]
        relative_y = positions[planet][frame, 1] - positions['Earth'][frame, 1]
        planets[planet].set_data(relative_x, relative_y)

        # Update trails relative to Earth
        start = max(0, frame - trail_length)
        trail_x = positions[planet][start:frame, 0] - positions['Earth'][start:frame, 0]
        trail_y = positions[planet][start:frame, 1] - positions['Earth'][start:frame, 1]
        trails[planet].set_data(trail_x, trail_y)

    # Adjust the Sun's position relative to Earth
    sun_x = -positions['Earth'][frame, 0]
    sun_y = -positions['Earth'][frame, 1]
    sun.set_data(sun_x, sun_y)

    start_sun = max(0, frame - trail_length)
    trail_sun_x = -positions['Earth'][start_sun:frame, 0]
    trail_sun_y = -positions['Earth'][start_sun:frame, 1]
    sun_trail.set_data(trail_sun_x, trail_sun_y)

    return [sun, sun_trail] + list(planets.values()) + list(trails.values())

# ani = FuncAnimation(fig, update, frames=len(time), blit=True, interval=50)
# ani = FuncAnimation(fig, update_geocentric, frames=len(time), blit=True, interval=50)
ani = FuncAnimation(fig, update_ptolemaic, frames=len(time), blit=True, interval=50)

plt.legend()
plt.show()
