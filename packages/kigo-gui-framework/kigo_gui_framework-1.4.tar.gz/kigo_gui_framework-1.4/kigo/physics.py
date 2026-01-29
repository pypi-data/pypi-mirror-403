# kigo/physics.py
import pybullet as p
import pybullet_data
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

class PhysicsEngine(QObject):
    """
    Kigo Physics Engine v1.1.0
    A high-level wrapper for PyBullet that integrates seamlessly with the 
    PyQt6 event loop. This allows Kigo UI elements to control 3D simulations.
    """
    
    # Signal emitted after every physics step to sync with Kigo UI updates
    frame_updated = pyqtSignal()

    def __init__(self, use_gui=True):
        super().__init__()
        # Initialize PyBullet
        # p.GUI opens the 3D visualizer; p.DIRECT runs headless for AI training
        self.mode = p.GUI if use_gui else p.DIRECT
        try:
            self.client = p.connect(self.mode)
        except Exception as e:
            print(f"Physics connection failed: {e}. Falling back to DIRECT mode.")
            self.client = p.connect(p.DIRECT)
        
        # Load standard PyBullet assets path
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.81)
        
        # Simulation Timer to sync with Kigo UI (defaulting to 60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._step)
        self.is_running = False

    def setup_scene(self):
        """Clears the world and loads a standard ground plane."""
        p.resetSimulation()
        p.setGravity(0, 0, -9.81)
        return p.loadURDF("plane.urdf")

    def spawn_object(self, shape="cube", position=[0, 0, 2], mass=1.0, color=[0.1, 0.7, 0.2, 1]):
        """
        Spawns a physics-enabled object into the Kigo-Simulation world.
        Returns the unique ID of the created object.
        """
        if shape == "cube":
            geom = p.GEOM_BOX
            dims = [0.5, 0.5, 0.5]
        elif shape == "sphere":
            geom = p.GEOM_SPHERE
            dims = [0.5, 0.5, 0.5] # used as radius
        else:
            geom = p.GEOM_BOX
            dims = [0.5, 0.5, 0.5]

        visual_id = p.createVisualShape(geom, halfExtents=dims, rgbaColor=color)
        collision_id = p.createCollisionShape(geom, halfExtents=dims)
        
        return p.createMultiBody(
            baseMass=mass,
            baseCollisionShapeIndex=collision_id,
            baseVisualShapeIndex=visual_id,
            basePosition=position
        )

    def toggle_simulation(self, start=True, fps=60):
        """Starts or stops the physics engine clock."""
        if start:
            self.timer.start(int(1000 / fps))
            self.is_running = True
        else:
            self.timer.stop()
            self.is_running = False

    def _step(self):
        """The core tick of the simulation. Notifies the UI loop on every step."""
        p.stepSimulation()
        self.frame_updated.emit()

    def apply_impulse(self, obj_id, vector=[0, 0, 100]):
        """Apply a sudden force to an object (e.g., a 'Jump' button)."""
        p.applyExternalForce(obj_id, -1, vector, [0, 0, 0], p.WORLD_FRAME)

    def get_pos(self, obj_id):
        """Returns the [x, y, z] position for display in Kigo widgets."""
        pos, _ = p.getBasePositionAndOrientation(obj_id)
        return list(pos)

    def disconnect(self):
        """Cleanly shuts down the physics server."""
        if self.is_running:
            self.timer.stop()
        p.disconnect()

# Always remember: somewhere, somehow, a duck is watching you.
__all__ = ['PhysicsEngine']