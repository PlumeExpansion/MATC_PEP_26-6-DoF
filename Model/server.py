import eventlet
import socketio
import numpy as np
import time

# 1. Initialize Socket.IO server
sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)

# Simple 6 DoF State: [x, y, z, roll, pitch, yaw]
state = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

def simulation_loop():
    """Simulates a simple bobbing and rotating motion"""
    global state
    t = 0
    dt = 0.01  # 100Hz simulation
    
    while True:
        t += dt
        # Example 6 DoF Dynamics (Sine waves for demo)
        state[0] = np.sin(t) * 2  # X position
        state[1] = np.cos(t) * 2  # Y position
        state[5] += 0.02          # Yaw rotation
        
        # Broadcast state to all connected clients
        sio.emit('update_state', {
            'pos': [state[0], state[1], state[2]],
            'rot': [state[3], state[4], state[5]] # Euler angles
        })
        
        sio.sleep(dt) 

if __name__ == '__main__':
    # Start simulation in a background thread
    sio.start_background_task(simulation_loop)
    # Start webserver on port 5000
    eventlet.wsgi.server(eventlet.listen(('', 5000)), app)