import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # no windows: everything is saved to files instead
import matplotlib.pyplot as plt
plt.rcParams['agg.path.chunksize'] = 10000  # draw long lines in chunks (the Moon's 10,000-year path overflows Agg otherwise)
from matplotlib.animation import FFMpegWriter, writers
from scipy.signal import find_peaks

# Output settings
output_dir = 'plots'
os.makedirs(output_dir, exist_ok=True)
video_fps = 60   # frames per second of the saved animation (1 frame = 1 day)
save_every = 1   # save every n-th day; 1 = every frame

# File reading (binary file written by elliptic_solar_system.py)
# Each body is an (N, 2) array: column 0 = x, column 1 = y, one row per day
with np.load("kepler_planetary_positions.npz") as data:
    planet_positions = {name: data[name] for name in data.files}

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

# How many days (rows) to animate; the FFT fits still use all the data
total_days = min(len(c) for c in planet_positions.values())
while True:
    answer = input(f"How many days to animate? (1-{total_days}, press Enter for all): ").strip()
    if answer == "":
        animate_days = total_days
        break
    try:
        animate_days = int(answer)
        if 1 <= animate_days <= total_days:
            break
        print(f"Please enter a number from 1 to {total_days}.")
    except ValueError:
        print("Please enter a whole number (e.g. 3650 for 10 years).")

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
    z = coords[:, 0] + 1j * coords[:, 1]
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
    x_obs = coords[:, 0]
    y_obs = coords[:, 1]

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
    ax_spec.legend(loc='upper right', fontsize=8)
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
    ax_fit.legend(loc='upper right')
    ax_fit.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(output_dir, f'{planet}_fft_{max_epicycles}_epicycles.png')
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)  # free memory
    print(f"Saved {plot_path}")

# Animation
# Find ffmpeg (needed to write .mp4); fall back to the imageio-ffmpeg package if installed
if not writers.is_available('ffmpeg'):
    try:
        import imageio_ffmpeg
        plt.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

if not writers.is_available('ffmpeg'):
    print("ffmpeg not found, so the animation was not saved. "
          "Install ffmpeg or run: pip install imageio-ffmpeg")
else:
    dpi = 100
    fig, ax = plt.subplots(figsize=(8, 8), dpi=dpi)
    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.set_aspect('equal')
    ax.set_facecolor('black')
    ax.grid(True, color='grey', alpha=0.3)
    ax.set_title('Geocentric Planetary Motion')
    ax.plot(0, 0, 'o', markersize=6, color=colors['Earth'], label='Earth')

    static_artists = []

    # 1) Real trajectories (only the animated days)
    for planet, data in planet_positions.items():
        x_real = data[:animate_days, 0]
        y_real = data[:animate_days, 1]
        static_artists += ax.plot(x_real, y_real, color='lightgrey', linestyle=':', linewidth=0.5, alpha=0.4)

    # 2) Fitted trajectories: full path drawn once (faint), then a moving dot + short trail
    trail_length = 200  # in days
    planet_dots = {}
    planet_trails = {}
    for planet, (x_fit, y_fit) in fitted_planet_positions.items():
        color = colors[planet]
        static_artists += ax.plot(x_fit[:animate_days], y_fit[:animate_days], '-', linewidth=0.8, alpha=0.25, color=color)
        planet_trails[planet] = ax.plot([], [], '-', linewidth=2, color=color)[0]
        planet_dots[planet] = ax.plot([], [], 'o', markersize=5, color=color, label=f"{planet} (Fit)")[0]
    legend = ax.legend(loc='upper right', fontsize=7)

    # Speed-up: the full paths are millions of points, and saving redraws everything every frame.
    # So render the static parts once into an image, remove them, and use that image as the background.
    fig.canvas.draw()
    background = np.asarray(fig.canvas.buffer_rgba()).copy()
    for artist in static_artists:
        artist.remove()
    legend.set_visible(False)
    ax.patch.set_visible(False)
    ax.axis('off')
    fig.patch.set_visible(False)
    fig.figimage(background, 0, 0, origin='upper', zorder=-1)

    def animate(i):
        for planet in planet_dots:
            x_fit, y_fit = fitted_planet_positions[planet]
            start = max(0, i - trail_length)
            planet_trails[planet].set_data(x_fit[start:i + 1], y_fit[start:i + 1])
            planet_dots[planet].set_data([x_fit[i]], [y_fit[i]])

    frames = range(0, animate_days, save_every)
    video_path = os.path.join(output_dir, f'geocentric_{max_epicycles}_epicycles_{animate_days}_days.mp4')
    progress_every = 5000  # print a progress message every this many frames

    print(f"Saving animation ({len(frames)} frames) to {video_path}...")
    writer = FFMpegWriter(fps=video_fps)
    with writer.saving(fig, video_path, dpi=dpi):  # dpi must match the figure's for the background to line up
        for n, i in enumerate(frames, start=1):
            animate(i)
            writer.grab_frame()
            if n % progress_every == 0:
                print(f"  {n}/{len(frames)} frames ({100 * n / len(frames):.1f}%)")
    plt.close(fig)
    print(f"Saved {video_path}")
