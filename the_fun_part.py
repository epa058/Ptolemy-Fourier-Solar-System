# Some calculations
# Compute the average distance for each planet to Earth
average_distances = {}

for planet in names:
    if planet != 'Earth':
        distances = np.linalg.norm(positions[planet] - positions['Earth'], axis=1)
        average_distance = np.mean(distances)
        average_distances[planet] = np.mean(distances)

# Display the average distances
for planet, distance in average_distances.items():
    print(f"The average distance from Earth to {planet} is {distance:.3f} astronomical units.")
