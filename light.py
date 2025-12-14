from gpiozero import OutputDevice

# グローバル変数の定義（最初はNoneまたは未定義）
light1_device = None
light2_device = None

def initialize_light1(pin):
    """ライトデバイスを一度だけ初期化する"""
    global light1_device
    if light1_device is None:
        print(f"Initializing light device on pin {pin}...")
        light1_device = OutputDevice(pin) # ★ ここで一度だけインスタンス化
        print("Initialization complete.")
    else:
        print("Light device already initialized.")

def Light1_ON(pin):
    """ライトをオンにする"""
    global light1_device
    # light_deviceが初期化されていることを確認
    if light1_device is None:
        # 初期化されていない場合は初期化を試みる
        initialize_light1(pin)
        
    if light1_device:
        print("ON")
        light1_device.on() # ★ 既存のインスタンスに対して操作を実行

def Light1_OFF(pin):
    """ライトをオフにする"""
    global light1_device
    # light_deviceが初期化されていることを確認
    if light1_device is None:
        initialize_light1(pin)
        
    if light1_device:
        print("OFF")
        light1_device.off() # ★ 既存のインスタンスに対して操作を実行

def initialize_light2(pin):
    """ライトデバイスを一度だけ初期化する"""
    global light2_device
    if light2_device is None:
        print(f"Initializing light device on pin {pin}...")
        light2_device = OutputDevice(pin) # ★ ここで一度だけインスタンス化
        print("Initialization complete.")
    else:
        print("Light device already initialized.")

def Light2_ON(pin):
    """ライトをオンにする"""
    global light2_device
    # light_deviceが初期化されていることを確認
    if light2_device is None:
        # 初期化されていない場合は初期化を試みる
        initialize_light2(pin)
        
    if light2_device:
        print("ON")
        light2_device.on() # ★ 既存のインスタンスに対して操作を実行

def Light2_OFF(pin):
    """ライトをオフにする"""
    global light2_device
    # light_deviceが初期化されていることを確認
    if light2_device is None:
        initialize_light1(pin)
        
    if light2_device:
        print("OFF")
        light2_device.off() # ★ 既存のインスタンスに対して操作を実行