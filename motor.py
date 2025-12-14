def Spin_Motor(Motor_Pin,Direction,motor_angle,spin_angle):
    if Direction == "clockwise":
        if motor_angle + spin_angle > 1400:
            rotate_angle = 1400 - motor_angle
        else:
            rotate_angle = spin_angle
        print(rotate_angle)
        Motor_Pin.run_for_degrees(rotate_angle, speed=50)
    elif Direction == "counterclockwise":
        if motor_angle - spin_angle < 0:
            rotate_angle = -(motor_angle)
        else:
            rotate_angle = -spin_angle
        Motor_Pin.run_for_degrees(rotate_angle, speed=50)
    else:
        print("無効な方向です。'clockwise' または 'counterclockwise' を指定してください。") 
    current_angle = Motor_Pin.get_position()
    print(f"現在の回転角度は {current_angle} 度です。")
    return current_angle

def Set_Motor_to_Start(Motor_Pin,motor_angle):
    print(f"現在の回転角度は {motor_angle} 度です。")
    Motor_Pin.run_for_degrees(-motor_angle, speed=50)