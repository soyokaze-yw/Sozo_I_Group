import RPi.GPIO as GPIO
import time

def Setup_keypad(row_pins, col_pins):
    """キーパッドとLCDの初期設定を行う"""
    # GPIOのモードを設定 (BCMモード)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # 列ピンを入力モードに設定し、内部プルアップ抵抗を有効にする
    for col_pin in col_pins:
        GPIO.setup(col_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # 行ピンを出力モードに設定
    for row_pin in row_pins:
        GPIO.setup(row_pin, GPIO.OUT)

def get_key(row_pins, col_pins, keypad):
    """キー入力をスキャンして、押されたキーを返す"""
    for i in range(len(row_pins)):
        # i番目の行ピンをLOWに設定
        GPIO.output(row_pins[i], GPIO.LOW)
        for j in range(len(col_pins)):
            # j番目の列ピンがLOWになったかチェック
            if GPIO.input(col_pins[j]) == GPIO.LOW:
                # キーが押されたのを検出
                key = keypad[i][j]
                # チャタリング（短時間のON/OFF）防止のため少し待つ
                while GPIO.input(col_pins[j]) == GPIO.LOW:
                    time.sleep(0.1)
                # i番目の行ピンをHIGHに戻す
                GPIO.output(row_pins[i], GPIO.HIGH)
                return key
        # i番目の行ピンをHIGHに戻す
        GPIO.output(row_pins[i], GPIO.HIGH)
    # 何も押されていない場合はNoneを返す
    return None


