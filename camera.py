from picamera2 import Picamera2
import time

def Take_Photo(wait_time,filename):
    picam2 = Picamera2()

    # カメラの設定を作成
    config = picam2.create_still_configuration()
    picam2.configure(config)

    # ★★★ カメラを起動 ★★★
    picam2.start()

    # カメラが安定するまで少し待つ
    time.sleep(wait_time)

    # ファイルに保存
    file_path = filename
    picam2.capture_file(file_path)
    print(f"写真を {file_path} として保存しました。")

    # ★★★ カメラを停止 ★★★
    picam2.stop()
    picam2.close()
    print("カメラを停止しました。")
