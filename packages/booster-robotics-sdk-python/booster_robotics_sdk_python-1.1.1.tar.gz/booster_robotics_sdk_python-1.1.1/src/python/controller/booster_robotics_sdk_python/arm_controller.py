import time
import math
import threading
import booster_robotics_sdk_python as br

# Constant: B1 usually has 20 joints (12 legs + 2 head + 6 arms)
MAX_JOINT_COUNT = 20 

class ArmJoint:
    """ Joint Index Definitions (2-9) """
    # Left Arm
    LeftPitch = 2  # Negative = Forward
    LeftRoll  = 3  # Negative = Inward
    LeftYaw   = 4  
    LeftElbow = 5  
    
    # Right Arm
    RightPitch = 6 # Negative = Forward
    RightRoll  = 7 # Positive = Inward
    RightYaw   = 8 
    RightElbow = 9 

class _LowStateTracker:
    """ Background subscriber for motor states. """
    def __init__(self):
        self.motor_states = [None] * MAX_JOINT_COUNT
        self.ready = False
        self._lock = threading.Lock()

        def callback(msg: br.LowState):
            with self._lock:
                ms = msg.motor_state_parallel
                count = min(len(ms), MAX_JOINT_COUNT)
                for i in range(count):
                    self.motor_states[i] = ms[i] 
                self.ready = True

        self.sub = br.B1LowStateSubscriber(callback)
        self.sub.InitChannel()

    def get_joint_q(self, idx):
        with self._lock:
            if not self.ready or idx >= len(self.motor_states) or self.motor_states[idx] is None:
                return 0.0
            return self.motor_states[idx].q

    def get_all_q(self):
        with self._lock:
            if not self.ready: return [0.0] * MAX_JOINT_COUNT
            return [m.q if m else 0.0 for m in self.motor_states]

    def close(self):
        self.sub.CloseChannel()

class ArmController:
    def __init__(self, ip: str = ""):
        print(f"[Arm] Connecting to robot")
        self.factory = br.ChannelFactory.Instance()
        self.factory.Init(0, ip)

        self.client = br.B1LocoClient()
        self.client.Init()

        self.pub = br.B1LowCmdPublisher()
        self.pub.InitChannel()

        self.tracker = _LowStateTracker()
        self.pending_actions = {}

        # Wait for data sync
        wait_start = time.time()
        while not self.tracker.ready:
            if time.time() - wait_start > 5.0:
                print("[WARN] LowState timeout.")
                break
            time.sleep(0.01)
        time.sleep(2)

        # --- 修改部分开始：使用重试机制开启上身控制 ---
        print("[Arm] Enabling UpperBodyCustomControl...")
        
        # 定义内部函数，处理不同 SDK 版本的参数类型兼容性
        def enable_cmd():
            try:
                # 尝试直接传 bool
                self.client.UpperBodyCustomControl(True)
            except TypeError:
                # 如果参数类型错误，说明需要传 Parameter 对象
                param = br.UpperBodyCustomControlParameter(True)
                self.client.UpperBodyCustomControl(param)

        # 执行重试
        if not self._retry_api_call(enable_cmd, "Enable UpperBody Control"):
            print("[ERROR] Failed to enable UpperBodyCustomControl after retries. Arm control may not work.")
        # --- 修改部分结束 ---
            
        time.sleep(0.5) 
        print("[Arm] Ready.")

    def _retry_api_call(self, func, description, max_retries=5, delay=1.0):
        """
        Helper function to retry RPC calls when error code 100 occurs.
        """
        for attempt in range(max_retries):
            try:
                func()
                return True
            except RuntimeError as e:
                # 检查错误信息是否包含 code = 100 (RPC Timeout)
                if "code = 100" in str(e):
                    print(f"[Retry] '{description}' failed (RPC Timeout 100). Retrying {attempt + 1}/{max_retries}...")
                    time.sleep(delay)
                else:
                    # 其他 Runtime 错误 (如 code 101) 不重试，直接抛出
                    print(f"[Error] '{description}' failed with unexpected error: {e}")
                    raise e
            except Exception as e:
                # 其他异常 (如 TypeError, ValueError) 不重试
                print(f"[Error] '{description}' failed with generic exception: {e}")
                raise e
        
        print(f"[Fail] '{description}' failed after {max_retries} attempts.")
        return False

    def ControlArm(self, joint_idx: int, target_rad: float, duration_ms: float):
        """ Chainable control method. """
        if joint_idx < 2 or joint_idx > 9:
            return self
        
        # Min duration 50ms to prevent jumps
        duration_ms = max(50.0, duration_ms)

        self.pending_actions[joint_idx] = {
            'target': target_rad,
            'duration': duration_ms / 1000.0
        }
        return self

    def finish(self):
        """ Execute pending actions. """
        if not self.pending_actions:
            return

        tasks = {}
        max_duration = 0.0

        # Plan trajectory: Interpolate from Current -> Target
        for idx, action in self.pending_actions.items():
            start_q = self.tracker.get_joint_q(idx)
            duration = action['duration']
            max_duration = max(max_duration, duration)
            
            tasks[idx] = {
                'start_q': start_q,
                'end_q': action['target'],
                'duration': duration
            }

        start_time = time.time()
        
        try:
            while True:
                now = time.time()
                elapsed = now - start_time
                
                if elapsed > max_duration + 0.02: 
                    break

                cmd_msg = br.LowCmd()
                cmd_list = []

                # Get all current positions to hold idle joints
                current_real_q = self.tracker.get_all_q()

                for i in range(MAX_JOINT_COUNT):
                    motor = br.MotorCmd()
                    motor.mode = 0x0A # Position Mode
                    motor.dq = 0.0
                    motor.tau = 0.0
                    
                    if i in tasks:
                        # === Active Moving Joint (Interpolation) ===
                        task = tasks[i]
                        progress = min(1.0, elapsed / task['duration'])
                        target_q = task['start_q'] + (task['end_q'] - task['start_q']) * progress
                        
                        motor.q = target_q
                        motor.kp = 60.0 
                        motor.kd = 3.0
                    
                    elif 2 <= i <= 9:
                        # === Idle Arm Joint (Hold Position) ===
                        motor.q = current_real_q[i]
                        motor.kp = 60.0
                        motor.kd = 3.0
                    
                    else:
                        # === Legs/Head (Zero Torque) ===
                        # Let internal controller handle balance
                        motor.q = 0.0
                        motor.kp = 0.0
                        motor.kd = 0.0
                    
                    cmd_list.append(motor)

                cmd_msg.motor_cmd = cmd_list
                self.pub.Write(cmd_msg)
                time.sleep(0.01) # 100Hz

        except Exception as e:
            print(f"[Error] {e}")
        finally:
            self.pending_actions = {}

    def close(self):
        print("[Arm] Disabling UpperBodyCustomControl...")
        
        # --- 修改部分开始：使用重试机制关闭上身控制 ---
        def disable_cmd():
            try:
                self.client.UpperBodyCustomControl(False)
            except TypeError:
                param = br.UpperBodyCustomControlParameter(False)
                self.client.UpperBodyCustomControl(param)

        self._retry_api_call(disable_cmd, "Disable UpperBody Control", max_retries=3)
        # --- 修改部分结束 ---

        if hasattr(self, 'tracker') and self.tracker: 
            self.tracker.close()
        if hasattr(self, 'pub') and self.pub: 
            self.pub.CloseChannel()
        print("[Arm] Closed.")