import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle

# Orbital parameters
mars_radius = 1
epicycle_radius = 0.3

# Time setup for one full orbit
t = np.linspace(0, 2 * np.pi, 360)

# Initial orbital positions
mars_x = mars_radius * np.cos(t)
mars_y = mars_radius * np.sin(t)
epicycle_x = mars_x + epicycle_radius * np.cos(5 * t)
epicycle_y = mars_y + epicycle_radius * np.sin(5 * t)

# Plot setup
fig, ax = plt.subplots(figsize=(8, 8))
line_mars, = ax.plot([], [], 'r-', label='Mars Orbit (Deferent)')
line_epicycle, = ax.plot([], [], 'r--', label='Mars Epicycle Path')
point_mars, = ax.plot([], [], 'ro', markersize=5)
point_epicycle, = ax.plot([], [], 'r*', markersize=7)
epicycle_circle = Circle((0, 0), epicycle_radius, fill=False, color='r', linestyle=':')
ax.add_patch(epicycle_circle)
ax.plot(0, 0, 'bo', markersize=10)  # Earth

# Limits and aspect
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.grid(True)
ax.legend()

def init():
    line_mars.set_data([], [])
    line_epicycle.set_data([], [])
    point_mars.set_data([], [])
    point_epicycle.set_data([], [])
    epicycle_circle.center = (0, 0)
    return line_mars, line_epicycle, point_mars, point_epicycle, epicycle_circle

def update(frame):
    line_mars.set_data(mars_x[:frame], mars_y[:frame])
    line_epicycle.set_data(epicycle_x[:frame], epicycle_y[:frame])
    point_mars.set_data(mars_x[frame], mars_y[frame])
    point_epicycle.set_data(epicycle_x[frame], epicycle_y[frame])
    epicycle_circle.center = (mars_x[frame], mars_y[frame])
    return line_mars, line_epicycle, point_mars, point_epicycle, epicycle_circle

# Creating the animation
ani = FuncAnimation(fig, update, frames=len(t), init_func=init, blit=True, repeat=True, interval=50)

fig, axes = plt.subplots(2, 1, figsize=(10, 8))

# X Coordinate vs Time
axes[0].plot(t, epicycle_x, 'b-', label='X Coordinate')
axes[0].set_title('X Coordinate vs Time')
axes[0].set_xlabel('Time (radians)')
axes[0].set_ylabel('X Coordinate (AU)')
axes[0].grid(True)
axes[0].legend()

# Y Coordinate vs Time
axes[1].plot(t, epicycle_y, 'r-', label='Y Coordinate')
axes[1].set_title('Y Coordinate vs Time')
axes[1].set_xlabel('Time (radians)')
axes[1].set_ylabel('Y Coordinate (AU)')
axes[1].grid(True)
axes[1].legend()

plt.tight_layout()
plt.show()
