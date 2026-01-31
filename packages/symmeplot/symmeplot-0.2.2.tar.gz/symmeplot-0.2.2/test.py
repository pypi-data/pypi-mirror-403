import numpy as np
from symmeplot.pyqtgraph import Scene3D
from sympy.physics.mechanics import Point, ReferenceFrame, dynamicsymbols

# Create the system in sympy
N = ReferenceFrame("N")
A = ReferenceFrame("A")
q = dynamicsymbols("q")
A.orient_axis(N, N.z, q)
N0 = Point("N_0")
v = 0.2 * N.x + 0.2 * N.y + 0.7 * N.z
A0 = N0.locatenew("A_0", v)
# Create the instance of the scene specifying the inertial frame and origin
scene = Scene3D(N, N0, scale=0.5)
# Add the objects to the system
scene.add_vector(v)
scene.add_frame(A, A0)
scene.add_point(A0, color="g")
# Evaluate the system.
scene.lambdify_system(q)
scene.evaluate_system(0.5)
# Plot the system
scene.plot()
