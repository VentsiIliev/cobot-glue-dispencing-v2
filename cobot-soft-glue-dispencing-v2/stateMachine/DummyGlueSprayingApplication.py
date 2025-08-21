import time

from stateMachine.StateMachineEnhancedGlueSprayingApplication import StateMachineEnhancedGlueSprayingApplication


# ---- Dummy GlueSprayingApplication to mock original methods ----
class DummyGlueSprayingApplication:
    def __init__(self):
        self.state = None
        self.robotService = self  # To satisfy ErrorState moveToStartPosition()

    def start(self, contourMatching=True):
        print(f"[Dummy] Executing start with contourMatching={contourMatching}")
        time.sleep(0.2)
        return "Start OK"

    def calibrateRobot(self):
        print("[Dummy] Calibrating robot...")
        time.sleep(0.2)
        return "Calibration OK"

    def calibrateCamera(self):
        print("[Dummy] Calibrating camera...")
        return "Camera Calibration OK"

    def createWorkpiece(self):
        print("[Dummy] Creating workpiece...")
        time.sleep(0.2)
        return "Workpiece created"

    def measureHeight(self):
        print("[Dummy] Measuring height...")
        return "Height measured"

    def updateToolChangerStation(self):
        print("[Dummy] Updating tool changer...")
        return "Tool changer updated"

    def handleBelt(self):
        print("[Dummy] Handling belt...")
        return "Belt handled"

    def testRun(self):
        print("[Dummy] Running test...")
        return "Test run OK"

    def handleExecuteFromGallery(self):
        print("[Dummy] Executing from gallery...")
        return "Gallery execution OK"

    def moveToStartPosition(self):
        print("[Dummy] Robot moved to safe start position")


# ---- Test Harness ----
if __name__ == "__main__":
    # Wrap dummy app with state machine
    original_app = DummyGlueSprayingApplication()
    app = StateMachineEnhancedGlueSprayingApplication(original_app)

    def wait():
        """Helper to allow async threads to finish work"""
        time.sleep(0.5)

    print("\n=== TEST 1: Start Operation ===")
    success, msg = app.start(contourMatching=True)
    print("Start request:", success, msg)
    wait()
    print("Current state:", app.get_current_state())

    print("\n=== TEST 2: Calibrate Robot ===")
    success, msg, _ = app.calibrateRobot()
    print("Calibration request:", success, msg)
    wait()
    print("Current state:", app.get_current_state())

    print("\n=== TEST 3: Create Workpiece ===")
    success, msg = app.createWorkpiece()
    print("Create workpiece request:", success, msg)
    wait()
    print("Current state:", app.get_current_state())

    print("\n=== TEST 4: Emergency Stop ===")
    success, msg = app.emergency_stop()
    print("Emergency stop:", success, msg)
    wait()
    print("Current state:", app.get_current_state())

    print("\n=== TEST 5: Reset System ===")
    success, msg = app.reset()
    print("Reset request:", success, msg)
    wait()
    print("Current state:", app.get_current_state())
