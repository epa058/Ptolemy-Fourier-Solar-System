  # Epicycles as Fourier Modes: A Rigorous Reconstruction of the Ptolemaic Model of Planetary Motion
  
  I am a geocentrist and believe in the Ptolemaic model of the Solar System.
  
  This project explores planetary motion from a geocentric perspective and reconstructs Ptolemaic-style epicycles using Fourier analysis and the Fast Fourier Transform (FFT). For completeness, I also implemented the outdated heliocentric model.
  
  ## How does it work?
  
  `circular_solar_system.py` is boring, so I will describe `elliptic_solar_system.py` and `fft.py` instead. 
  
  ### Keplerian Orbits
  
  Using NASA orbital parameters (semi-major axis and eccentricity), I simulate planetary motion via Kepler's equation $M = E - e \sin(E)$. I solve for the eccentric anomaly numerically, convert it to the true anomaly, and then map this data into Cartesian coordinates. To move into a geocentric frame, I shift all positions by Earth's. This naturally reproduces retrograde motion.
  
  ### Epicycles via FFT
  
  Planetary motion is treated as a complex signal $z(t) = x(t) + i y(t)$. I apply the FFT to extract dominant frequencies $\lbrace f_k \rbrace$ and their amplitudes $\lbrace A_k \rbrace$ via peak detection. Using these, each orbit is reconstructed as a sum of rotating circles
  
  $$ z(t) \approx \sum_{k} A_k e^{2 \pi i f_k t}. $$
  
  This is basically a modern version of deferents and epicycles.
  
  ### Animation
  
  The project visualizes:
  * The original (ground truth) orbital paths
  * The reconstructed trajectories using a finite number of epicycles
  
  ## Future Work
  * Add orbital inclination for 3D orbits
  * Add argument of perihelion and starting mean anomaly (all planets currently start at perihelion on the +x axis)
  * Use real NASA ephemeris data
  * Adaptive, error-based epicycle selection
  * GPU acceleration for longer simulations
  * Interactive visualization (maybe not)
  
  ## FAQ
  
  #### Q: Are you really a geocentrist?
  
  A: Yes
