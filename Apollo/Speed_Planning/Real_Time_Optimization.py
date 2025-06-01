import numpy as np
import matplotlib.pyplot as plt
import control as ctrl

# Define the individual transfer functions for each entry in the MIMO system
G11 = ctrl.TransferFunction([1], [1, 1])
G12 = ctrl.TransferFunction([1], [1, 3])
G21 = ctrl.TransferFunction([1], [1, 2])
G22 = ctrl.TransferFunction([1], [1, 4])

# Define the system as a transfer function matrix (2x2 MIMO system)
G = np.array([[G11, G12], [G21, G22]])

# Weighting functions for the H∞ synthesis
W1 = ctrl.TransferFunction([1], [1, 2])
W2 = ctrl.TransferFunction([1], [1, 3])
W3 = ctrl.TransferFunction([1], [1, 4])
W4 = ctrl.TransferFunction([1], [1, 5])

# Create the augmented system for H∞ synthesis (the plant and the weighting functions)
# We will define the plant model and the weighting functions
# Here we use a placeholder for the full system, combining the plant and weighting matrices.

# Use the state-space representation for the H∞ synthesis problem
P_aug = ctrl.ss(G11)

# Solve the H∞ control problem
K, _, _ = ctrl.hinfsyn(P_aug, W1, W2)

# Simulate the closed-loop system with a noisy step response
t = np.linspace(0, 10, 1000)
u = np.ones_like(t)  # Step input

# Add noise to the input (Gaussian noise)
noise = 0.1 * np.random.randn(*t.shape)
u_noisy = u + noise

# Closed-loop system (feedback control)
sys_cl = ctrl.feedback(P_aug * K)

# Simulate the response with noisy input
T, yout = ctrl.forced_response(sys_cl, t, u_noisy)

# Plot the step response with noise
plt.figure(figsize=(10, 6))
plt.plot(t, yout[0], label="Output 1")
plt.plot(t, yout[1], label="Output 2")
plt.title("Closed-loop System Response with Noisy Step Input")
plt.xlabel("Time [s]")
plt.ylabel("Output")
plt.legend()
plt.grid(True)
plt.show()
