import cv2

# 検出したい画像ファイルを指定
def Check_people(model,filename):
    image_path = filename
    img = cv2.imread(image_path)

    # モデルを実行して物体を検出
    # 'person'クラス (クラスID: 0) のみを検出対象にする
    # conf=0.5 は、信頼度が50%以上のものだけを結果として採用する設定
    results = model(img, classes=0, conf=0.5)

    # --- 結果の判定 ---
    person_detected = False

    # 検出された全てのバウンディングボックス（Bbox）をループ
    for r in results:
        if len(r.boxes) > 0:
            # r.boxes が空でなければ、(classes=0で指定した)人が検出された
            person_detected = True
            break # 一人でも見つかったらループを抜ける

    # 最終結果の表示
    if person_detected:
        print(f"[{image_path}] から人を検出しました。")
        
        # 検出結果を可視化する場合 (オプション)
        annotated_img = results[0].plot() # 検出結果を画像に描画
        cv2.imwrite("result_photo.jpg", annotated_img)
        print("検出結果を 'result_photo.jpg' に保存しました。")
        
    else:
        print(f"[{image_path}] から人は検出されませんでした。")

    return person_detected