import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from scipy.signal import find_peaks

# File reading
planet_positions = {}
current_planet = None

with open("kepler_planetary_positions.txt", "r") as f:
    for line in f:
        if "positions" in line:
            current_planet = line.split()[0] # name
            planet_positions[current_planet] = []
        else:
            coords = line.strip().split(',')
            if len(coords) == 2:
                x, y = float(coords[0]), float(coords[1])
                planet_positions[current_planet].append((x, y)) # coordinates

# Earth is the origin in the geocentric frame (all zeros), so don't fit it
planet_positions.pop('Earth', None)

# User input
while True:
    try:
        max_epicycles = int(input("How many epicycles?: "))
        if max_epicycles >= 1:
            break
        print("Please enter a positive integer.")
    except ValueError:
        print("Please enter a whole number (e.g. 5).")

# Planet colors
colors = {
    'Sun':     'yellow',
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

# Fast Fourier Transform
def fft_epicycles(coords, max_n, pad_factor=8, overlap_bins=2):
    # Map coordinates to complex plane
    z = np.array([x + 1j * y for x, y in coords])
    N = len(z)
    bandwidth = 1.0 / N  # one FFT bin of the unpadded signal
    overlap_threshold = overlap_bins * bandwidth

    # Remove the mean (DC term) so it can't leak into low-frequency peaks
    z_mean = z.mean()
    z_centered = z - z_mean

    # Hann window suppresses sidelobes, so they don't show up as fake peaks
    window = np.hanning(N)

    # Zero-pad and FFT (used only to locate frequencies)
    Z = np.fft.fft(z_centered * window, n=N * pad_factor)
    freqs = np.fft.fftfreq(N * pad_factor)
    amplitudes = np.abs(Z) / np.sum(window)  # window-corrected, approx. radius in AU

    # Positive frequencies only
    pos_mask = (freqs > 0)
    freqs_pos = freqs[pos_mask]
    amps_pos  = amplitudes[pos_mask]

    # Find peaks
    min_amp = np.max(amps_pos) * 0.01  # only picks local maxima above 1% of tallest peak
    peak_indices, _ = find_peaks(amps_pos, height=min_amp)
    peak_indices = peak_indices[np.argsort(amps_pos[peak_indices])[::-1]]

    # Discard peaks within overlap_threshold of a taller kept peak
    kept_freqs = []
    for idx in peak_indices:
        f0 = freqs_pos[idx]
        too_close = any(abs(f0 - kf) < overlap_threshold for kf in kept_freqs)
        if not too_close:
            kept_freqs.append(f0)
        if len(kept_freqs) == max_n:
            break
    kept_freqs = np.array(kept_freqs)

    # Least-squares fit for each circle's radius and phase at the chosen frequencies
    # (the window distorts FFT amplitudes, so we don't read them off the spectrum)
    t = np.arange(N)
    z_fit = np.full(N, z_mean, dtype=complex)
    coeffs = np.array([], dtype=complex)
    if len(kept_freqs) > 0:
        basis = np.exp(2j * np.pi * np.outer(t, kept_freqs))  # N x n_found
        coeffs, *_ = np.linalg.lstsq(basis, z_centered, rcond=None)
        z_fit += basis @ coeffs

    selected_freqs = kept_freqs
    selected_amps  = np.abs(coeffs)

    return {
        "spectrum":       (freqs_pos, amps_pos),
        "selected":       (selected_freqs, selected_amps),
        "reconstruction": (z_fit.real, z_fit.imag),
        "n_found":        len(kept_freqs)
    }

fitted_planet_positions = {}

# Individual planet plots
for planet, coords in planet_positions.items():
    x_obs = np.array([c[0] for c in coords])
    y_obs = np.array([c[1] for c in coords])

    res = fft_epicycles(coords, max_epicycles)
    freqs_pos, amps_pos = res["spectrum"]
    selected_freqs, selected_amps = res["selected"]
    x_fit, y_fit = res["reconstruction"]
    n_used = res["n_found"]

    fitted_planet_positions[planet] = (x_fit, y_fit)

    # Create figure
    fig, (ax_spec, ax_fit) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(f'{planet}: FFT Spectrum & Epicycle Fit '
                 f'({n_used} of {max_epicycles} epicycles kept)')

    # 1) Spectrum
    ax_spec.plot(freqs_pos, amps_pos, color='blue', linewidth=1, label='Spectrum')

    for i, (f0, A) in enumerate(zip(selected_freqs, selected_amps)):
        ax_spec.axvline(f0, color='red', linewidth=1.5, linestyle='-', alpha=0.8,
                        label='Kept peaks' if i == 0 else None)
        ax_spec.plot(f0, A, marker='o', color='darkred', markersize=6)

    ax_spec.set_title('Frequency Spectrum')
    ax_spec.set_xlabel('Frequency (cycles / day)')
    ax_spec.set_ylabel('Amplitude (AU)')
    ax_spec.legend(fontsize=8)
    ax_spec.grid(True, alpha=0.3)

    # Fix plot limits
    epsilon = np.max(amps_pos) * 0.005
    sig_idx = np.where(amps_pos > epsilon)
    if len(sig_idx[0]) > 0:
        max_freq = freqs_pos[sig_idx[0][-1]]
        buffer = 5 * (1.0 / len(coords))
        ax_spec.set_xlim(0, max_freq + buffer)
        ax_spec.set_ylim(0, np.max(amps_pos) * 1.1)
    else:
        ax_spec.set_xlim(0, 0.1)
        ax_spec.set_ylim(0, max(np.max(amps_pos) * 1.1, 1e-4))

    print(f"{planet}: {n_used} epicycle(s) kept")
    for f0, A in zip(selected_freqs, selected_amps):
        print(f"  f={f0:.6f} cycles/day (period {1 / (f0 * 365):.3f} yr),  radius={A:.5f} AU")

    # 2) Orbital path
    ax_fit.plot(x_obs, y_obs, 'o', markersize=2, alpha=0.4, label='Observed')
    ax_fit.plot(x_fit, y_fit, '-', linewidth=1.2, label=f'Fit ({n_used} epicycles)')
    ax_fit.plot(0, 0, 'ko', markersize=6, label='Earth')
    ax_fit.set_title('Orbital Path')
    ax_fit.set_xlabel('x (AU)')
    ax_fit.set_ylabel('y (AU)')
    ax_fit.set_aspect('equal')
    ax_fit.legend()
    ax_fit.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.draw()
    plt.pause(0.001)

plt.show()

# Animation
fig, ax = plt.subplots(figsize=(8, 8))
ax.set_xlim(-50, 50)
ax.set_ylim(-50, 50)
ax.set_aspect('equal')
ax.set_facecolor('black')
ax.grid(True, color='grey', alpha=0.3)
ax.set_title('Geocentric Planetary Motion')
ax.plot(0, 0, 'o', markersize=6, color=colors['Earth'], label='Earth')

# 1) Real trajectories
for planet, data in planet_positions.items():
    x_real = [p[0] for p in data]
    y_real = [p[1] for p in data]
    ax.plot(x_real, y_real, color='lightgrey', linestyle=':', linewidth=0.5, alpha=0.4)

# 2) Fitted trajectories: full path drawn once (faint), then a moving dot + short trail
trail_length = 200  # in days
planet_dots = {}
planet_trails = {}
for planet, (x_fit, y_fit) in fitted_planet_positions.items():
    color = colors[planet]
    ax.plot(x_fit, y_fit, '-', linewidth=0.8, alpha=0.25, color=color)
    planet_trails[planet] = ax.plot([], [], '-', linewidth=2, color=color)[0]
    planet_dots[planet] = ax.plot([], [], 'o', markersize=5, color=color, label=f"{planet} (Fit)")[0]
ax.legend(fontsize=7)

def animate(i):
    for planet in planet_dots:
        x_fit, y_fit = fitted_planet_positions[planet]
        start = max(0, i - trail_length)
        planet_trails[planet].set_data(x_fit[start:i + 1], y_fit[start:i + 1])
        planet_dots[planet].set_data([x_fit[i]], [y_fit[i]])
    return list(planet_trails.values()) + list(planet_dots.values())

max_frames = min(len(v[0]) for v in fitted_planet_positions.values())
ani = FuncAnimation(fig, animate, frames=max_frames, interval=5, blit=True)
plt.show()
