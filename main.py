import time
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
from buildhat import Motor # Motorクラスをインポート
from ultralytics import YOLO
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import threading
import socket
import datetime

import keypad as keypad_code
import display as display_code
import speaker as speaker_code
import motor as motor_code
import camera as camera_code
import check_people as check_people_code
import light as light_code

#%% 定数定義
# 勉強中かどうか
IS_STUDYING = False
IS_DISTRACTING = False

MODE = [
    "ﾍﾞﾝｷｮｳ",
    "ﾗｲﾄ",
    "ﾀｽｸ+ﾀｲﾏｰ",
    "ﾀｲﾏｰｾｯﾃｲ",
    "ﾀｽｸｾｯﾃｲ",
    "ｵﾌﾟｼｮﾝ",
    "IPｱﾄﾞﾚｽ",
    "ｼｭｳﾘｮｳ"
]

TASKS = [
    "ｼｭｸﾀﾞｲ",
    "ｹｲｻﾝ",
    "ｶﾝｼﾞ",
    "ｵﾝﾄﾞｸ",
    "ｺｸｺﾞ",
    "ｻﾝｽｳ",
    "ｴｲｺﾞ",
    "ｼﾞｼｭｳ",
    "ｼﾞﾕｳﾆｭｳﾘｮｸ"
]

OPTION = [
    "ﾀｽｸﾆｭｳﾘｮｸ",
    "ﾀｽｸｻｸｼﾞｮ",
    "ﾍﾞﾝｷｮｳｼﾞｶﾝｾｯﾃｲ",
    "ｷｭｳｹｲｼﾞｶﾝｾｯﾃｲ",
    "ｶｸﾆﾝｼﾞｶﾝｾｯﾃｲ"
]

# キーパッドのレイアウト定義
KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

KEYPAD_CHANGE_NUM_DIC = {"1":1, "2":2, "3":3, "4":4, "5":5, "6":6, "7":7, "8":8, "9":9, "*":10, "0":11 ,"#":12,"C":13}

FRICK_KEYPAD = [
    ["ｱ", "ｲ", "ｳ", "ｴ", "ｵ"],
    ["ｶ", "ｷ", "ｸ", "ｹ", "ｺ"],
    ["ｻ", "ｼ", "ｽ", "ｾ", "ｿ"],
    ["ﾀ", "ﾁ", "ﾂ", "ﾃ", "ﾄ"],
    ["ﾅ", "ﾆ", "ﾇ", "ﾈ", "ﾉ"],
    ["ﾊ", "ﾋ", "ﾌ", "ﾍ", "ﾎ"],
    ["ﾏ", "ﾐ", "ﾑ", "ﾒ", "ﾓ"],
    ["ﾔ", "ﾕ", "ﾖ"],
    ["ﾗ", "ﾘ", "ﾙ", "ﾚ", "ﾛ"],
    ["゛","ﾟ","小"],
    ["ﾜ", "ｦ", "ﾝ"],
    ["ｰ"," "],
    ["!","?","@","#","$","&","'","(",")","*","+",",",".","/","%"]
]

#゛ﾟ小が該当する文字リスト
DOUBLE_DOT_WORD = ["ｶ","ｷ","ｸ","ｹ","ｺ","ｻ","ｼ","ｽ","ｾ","ｿ","ﾀ","ﾁ","ﾂ","ﾃ","ﾄ","ﾊ","ﾋ","ﾌ","ﾍ","ﾎ"]
CIRCLE_WORD = ["ﾊ","ﾋ","ﾌ","ﾍ","ﾎ"]
SMALL_WORD = ["ｱ","ｲ","ｳ","ｴ","ｵ","ﾔ","ﾕ","ﾖ","ﾂ"]
SMALLED_WORD = ["ｧ","ｨ","ｩ","ｪ","ｫ","ｬ","ｭ","ｮ","ｯ"]

#音源
SOUND_ALARM = '目覚まし時計のアラーム.mp3'
SOUND_ERROR = 'キャンセル5.mp3'
SOUND_FANFARE = 'ラッパのファンファーレ.mp3'

# 配線したキーパッドのGPIOピン番号
ROW_PINS = [21, 20, 25, 24]  # 行
COL_PINS = [26, 19, 13, 6]   # 列

LIGHT_PIN_1 = 5
LIGHT_PIN_2 = 22

#ライトに繋げたモータのピン
LIGHT_MOTOR_PIN = Motor('A')

#機械学習のモデル
MODEL_CHECK_PEOPLE = YOLO('yolov8n.pt')
if(MODEL_CHECK_PEOPLE == None):
    print("ERROR")

#メモリファイル名
MEMORYFILE_NAME = "MemoryFile.txt"

# 勉強時間の履歴を記録するファイル
HISTORY_FILE = "study_history.csv"

#IPアドレス
IPADRESS = ""

#ライトスタンドの初期状態
LIGHT1_ON = False
LIGHT2_ON = False

#ライトスタンドのモーターの現在位置
MOTOR_CURRENT_ANGLE = LIGHT_MOTOR_PIN.get_position()
print(MOTOR_CURRENT_ANGLE)

#デフォルトのモータの回転角度
DEFAULT_MOTOR_SPIN_ANGLE = -360

#設定に関する定数
CHECK_STUDY_TIME = 30 # 勉強中のカメラチェック間隔（秒）

DEFAULT_STUDY_TIME = 1500  # デフォルトの勉強時間（秒）
DEFAULT_REST_TIME = 300    # デフォルトの休憩時間（秒）

app = Flask(__name__)
#%% FLSAK サーバー定義
# HTMLテンプレート（見た目のロック解除版）
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Study Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; padding: 20px; background-color: #f0f0f0; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 10px; }
        input[type="number"], input[type="text"] { width: 100%; padding: 10px; margin: 5px 0; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 5px; margin-top:5px;}
        .delete-btn { background-color: #dc3545; width: auto; padding: 5px 10px; font-size: 14px; }
        ul { padding-left: 0; list-style: none;}
        li { margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding: 5px 0;}
    </style>
</head>
<body>
    <h1>ラズパイ学習リモコン</h1>

    <div class="card">
        <h2>⏱ 設定 (分単位)</h2>
        <form action="/update_settings" method="post">
            <label>勉強時間 (分):</label>
            <input type="number" name="study_time_min" value="{{ study_min }}">
            <label>休憩時間 (分):</label>
            <input type="number" name="rest_time_min" value="{{ rest_min }}">
            <button type="submit">更新</button>
        </form>
   </div>

    <div class="card">
        <h2>📝 タスクリスト</h2>
        <form action="/add_task" method="post" style="margin-bottom: 15px;">
            <input type="text" name="new_task" placeholder="半角カタカナ推奨">
            <button type="submit">追加</button>
        </form>

        <ul>
            {% for task in tasks[:-1] %}
            <li>
                <span>{{ task }}</span>
                <form action="/delete_task" method="post" style="margin:0;">
                                        <input type="hidden" name="task_index" value="{{ loop.index0 }}"> 
                    <button type="submit" class="delete-btn">削除</button>
            </form>
            </li>
            {% else %}
            <p style="color: #888;">タスクはありません</p>
            {% endfor %}
        </ul>
    </div>
</body>
</ul>
    </div>

    <div class="card" style="margin-top: 20px;">
        <a href="/history" style="text-decoration: none;">
            <button style="background-color: #28a745;">📖 勉強履歴を表示</button>
        </a>
    </div>
    </body>
</html>
'''

HISTORY_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Study History</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
       body { font-family: sans-serif; padding: 20px; background-color: #f0f0f0; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 10px; }
        h1 { color: #007bff; }
        .back-btn { display: block; width: 100%; padding: 10px; margin-bottom: 20px; background-color: #6c757d; color: white; border: none; border-radius: 5px; text-align: center; text-decoration: none;}
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #f2f2f2; }
        .total-row td { font-weight: bold; background-color: #e9ecef; }
    </style>
</head>
<body>
    <a href="/" class="back-btn">⬅ メイン画面に戻る</a>
    
    <div class="card">
        <h1>📅 勉強時間 履歴</h1>

        <table>
            <tr>
                <th>日付</th>
                <th>勉強時間 (分)</th>
            </tr>
            {% set total_time = [0] %}
            {% for date, minutes in history %}
            <tr>
                <td>{{ date }}</td>
                <td>{{ minutes }}</td>
                {% set _ = total_time.append(total_time.pop() + minutes) %}
            </tr>
            {% endfor %}
            <tr class="total-row">
                <td>**合計**</td>
                <td>{{ total_time[0] }} 分</td>
            </tr>
        </table>

        {% if not history %}
            <p>まだ勉強時間の記録はありません。</p>
        {% endif %}

    </div>
</body>
</html>
'''

#%% Flask ルート定義

@app.route('/')
def index():
    # 秒を分に変換して表示
    study_min = DEFAULT_STUDY_TIME // 60
    rest_min = DEFAULT_REST_TIME // 60
    return render_template_string(HTML_TEMPLATE, 
                                  study_min=study_min, 
                                  rest_min=rest_min, 
                                  tasks=TASKS)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    global DEFAULT_STUDY_TIME, DEFAULT_REST_TIME
    
    # 勉強中は設定を受け付けない（エラーは出さず、変更もしない）
    if IS_STUDYING:
        print("※勉強中のため設定変更を無視しました")
        return redirect(url_for('index'))

    try:
        new_study_min = int(request.form.get('study_time_min'))
        new_rest_min = int(request.form.get('rest_time_min'))
        
        DEFAULT_STUDY_TIME = new_study_min * 60
        DEFAULT_REST_TIME = new_rest_min * 60
        
        print(f"Web更新: 勉強={DEFAULT_STUDY_TIME}秒, 休憩={DEFAULT_REST_TIME}秒")
    except ValueError:
        pass
    return redirect(url_for('index'))

@app.route('/add_task', methods=['POST'])
def add_task():
    # 勉強中はタスク追加を受け付けない
    if IS_STUDYING:
        print("※勉強中のためタスク追加を無視しました")
        return redirect(url_for('index'))
        
    new_task = request.form.get('new_task')
    if new_task:
        TASKS.insert(-1, new_task)
        print(f"Webタスク追加: {new_task}")
    return redirect(url_for('index'))

@app.route('/delete_task', methods=['POST'])
def delete_task():
    global TASKS
    
    # 勉強中はタスク削除を受け付けない
    if IS_STUDYING:
        print("※勉強中のためタスク削除を無視しました")
        return redirect(url_for('index'))
        
    try:
        # フォームからタスクのインデックスを受け取る
        index = int(request.form.get('task_index'))
        
        # TASKSリストから指定されたインデックスの要素を削除
        if 0 <= index < len(TASKS):
            deleted_task = TASKS.pop(index)
            print(f"Webタスク削除: {deleted_task}")
    except (ValueError, TypeError, IndexError):
        # indexが不正、またはタスクが見つからない場合
        print("タスク削除に失敗しました。")
        pass
        
    return redirect(url_for('index'))

@app.route('/report_app_usage', methods=['POST'])
def report_app_usage():
    global IS_DISTRACTING
    # MacroDroidの標準的なPOSTフォームデータを受け取る
    app_status = request.form.get('status')
    app_name = request.form.get('app_name')
    
    print(f"検知: {app_name} の状態が {app_status} になりました")

    if app_status == 'opened':
        IS_DISTRACTING = True
    else: # 'closed' またはその他の場合
        IS_DISTRACTING = False
        
    return jsonify({"message": "Received status"}), 200

@app.route('/history')
def history():
    # 履歴データを取得し、HTMLテンプレートに渡す
    study_history = Get_Study_History()
    return render_template_string(HISTORY_TEMPLATE, history=study_history)

def run_flask_server():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

#%% 関数定義
#リストの中から選択する関数
def select_from_list(Sample_List):
    global Show_Text
    task_index = 0
    Show_Text = ""
    while True:
        #表示更新
        if task_index != len(Sample_List) - 1 and Show_Text != Sample_List[task_index]:
            display_code.Show_display(lcd, ">" + Sample_List[task_index], Sample_List[task_index + 1])
            Show_Text = Sample_List[task_index]
        elif Show_Text != Sample_List[task_index]:
            display_code.Show_display(lcd, Sample_List[task_index - 1], ">" + Sample_List[task_index])
            Show_Text = Sample_List[task_index]
        #else:
        #    display_code.Show_display(lcd, "error", None)
                
        task_select_key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
        #選択処理
        #上移動
        if task_select_key == "2":
            if task_index != 0:
                task_index -= 1
        #下移動
        elif task_select_key == "8":
            if task_index != len(Sample_List) - 1:
                task_index += 1
        #決定
        elif task_select_key == "5" or task_select_key == "D":
            display_code.Show_display(lcd, Sample_List[task_index], "ﾃﾞｹｯﾃｲ!")
            time.sleep(0.5)
            return Sample_List[task_index]

        #戻る
        elif task_select_key == "B" and Sample_List[0] != "ﾍﾞﾝｷｮｳ":
            return "BACK"
        elif task_select_key != None:
            #エラー音鳴らす
            speaker_code.play_sound(SOUND_ERROR)
            continue

#フリック入力関数
def Frick_Input():
    #タスク入力モード
    global Show_Text
    new_task = ""
    before_input_key = None
    row_index = None
    column_index = None
    display_code.Show_display(lcd,"ｱﾀﾗｼｲﾀｽｸ","ﾆｭｳﾘｮｸ")
    Show_Text = ""
    while True:
        task_input_key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
        if task_input_key is not None:
            #if task_input_key in KEYPAD_CHANGE_NUM_DIC:
            #最初の入力処理
            if task_input_key in KEYPAD_CHANGE_NUM_DIC:
                if before_input_key == None:
                    if task_input_key == "*":
                        #エラー音鳴らす
                        speaker_code.play_sound(SOUND_ERROR)
                        print("a")
                        continue
                    before_input_key = task_input_key
                    row_index = KEYPAD_CHANGE_NUM_DIC[task_input_key] - 1
                    column_index = 0
                    new_task += FRICK_KEYPAD[row_index][column_index]

                #2回目以降の入力処理
                #同じキーが押された場合
                elif before_input_key == task_input_key:
                    column_index += 1
                    if column_index >= len(FRICK_KEYPAD[row_index]):
                        column_index = 0
                    check = True
                    #特殊処理：゛ﾟ小が該当しない場合のスキップ
                    if task_input_key == "*":
                        check1 = False
                        check2 = False
                        check3 = False
                        if column_index == 0:
                            checknumber = -1
                        else:
                            checknumber = -2
                        while True:
                            if column_index == 0:
                                if new_task[checknumber] not in DOUBLE_DOT_WORD:
                                    column_index += 1
                                    check1 = True
                                else:
                                    break
                            elif column_index == 1:
                                if new_task[checknumber] not in CIRCLE_WORD:
                                    column_index += 1
                                    check2 = True
                                else:
                                    break
                            elif column_index == 2:
                                if new_task[checknumber] not in SMALL_WORD:
                                    column_index += 1
                                    check3 = True
                                else:
                                    break
                            if column_index >= len(FRICK_KEYPAD[row_index]):
                                column_index = 0
                            if check1 and check2 and check3:
                                #エラー音鳴らす
                                speaker_code.play_sound(SOUND_ERROR)
                                print("ddd")
                                check = False
                                break
                    if not check:
                        continue
                    new_task = new_task[:-1] + FRICK_KEYPAD[row_index][column_index]
                    
                #違うキーが押された場合
                elif before_input_key != task_input_key:
                    check = True
                    column_index = 0
                    if task_input_key == "*":
                        check1 = False
                        check2 = False
                        check3 = False
                        while True:
                            if column_index == 0:
                                if new_task[-1] not in DOUBLE_DOT_WORD:
                                    column_index += 1
                                    check1 = True
                                else:
                                    break
                            elif column_index == 1:
                                if new_task[-1] not in CIRCLE_WORD:
                                    column_index += 1
                                    check2 = True
                                else:
                                    break
                            elif column_index == 2:
                                if new_task[-1] not in SMALL_WORD:
                                    column_index += 1
                                    check3 = True
                                else:
                                    break
                            if column_index >= len(FRICK_KEYPAD[row_index]):
                                column_index = 0
                            if check1 and check2 and check3:
                                #エラー音鳴らす
                                speaker_code.play_sound(SOUND_ERROR)
                                check = False
                                print("b")
                                break
                    if not check:
                        continue
                    before_input_key = task_input_key
                    row_index = KEYPAD_CHANGE_NUM_DIC[task_input_key] - 1
                    new_task += FRICK_KEYPAD[row_index][column_index]
                #表示更新
                if Show_Text != new_task:
                    if new_task[-1] == "小":
                        word_index = SMALL_WORD.index(new_task[-2])
                        new_task = new_task[:-2] + SMALLED_WORD[word_index]
                    display_code.Show_display(lcd, new_task, None)
                    Show_Text = new_task

            #1文字削除
            if task_input_key == "A":
                new_task = new_task[:-1]
                before_input_key = None
                display_code.Show_display(lcd, new_task, None)
            #戻る
            elif task_input_key == "B":
                return "BACK"
            #入力確定
            elif task_input_key == "D":
                if len(new_task) == 0:
                    display_code.Show_display(lcd, "ﾀｽｸｦ", "ﾆｭｳﾘｮｸ!")
                    continue
                display_code.Show_display(lcd, new_task, "ﾃﾞｹｯﾃｲ!")
                time.sleep(0.5)
                return new_task
            else:
                #エラー音鳴らす
                #speaker_code.play_sound(SOUND_ERROR)
                continue

def set_timer():
    global Show_Text
    timer_str = ""
    show_timer_str = ""
    # ★ 最初の表示をループに入る前に一度実行する
    display_code.Show_display(lcd, "ｼﾞｶﾝｾｯﾃｲ", show_timer_str)
    Show_Text = show_timer_str  # Show_Textも初期表示に合わせて更新

    while True:
        timer_set_key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
        
        # フラグや古い値を保持する変数を追加し、キー入力があった場合にのみ表示処理を行う
        
        # キー入力処理（timer_strの変更）
        if timer_set_key is not None:
            timer_str_before = timer_str # 変更前の値を保持

            if timer_set_key in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]:
                # ...（数字入力の処理はそのまま）...
                if len(timer_str) == 0 and timer_set_key == "0":
                    speaker_code.play_sound(SOUND_ERROR)
                    continue
                # ここでtimer_strが更新される
                timer_str += timer_set_key
            
            elif timer_set_key == "*" or timer_set_key == "A":
                # ここでtimer_strが更新される
                timer_str = timer_str[:-1]

            # ...（Dキー、Bキーの処理はそのまま。ただしDキー処理内でreturnする前に表示を更新する処理が必要な場合あり）...

            # キー入力によってtimer_strが変わった場合のみ表示文字列を再構築し、表示を更新する
            if timer_str != timer_str_before: 
                show_timer_str = timer_str
                if len(timer_str) == 3:
                    show_timer_str = timer_str[:1] + ":" + timer_str[1:]
                elif len(timer_str) == 4:
                    show_timer_str = timer_str[:2] + ":" + timer_str[2:]
                elif len(timer_str) == 5:
                    show_timer_str = timer_str[:1] + ":" + timer_str[1:3] + ":" + timer_str[3:]
                if len(timer_str) > 5:
                    show_timer_str = timer_str[:-4] + ":" + timer_str[-4:-2] + ":" + timer_str[-2:]

                display_code.Show_display(lcd, "ｼﾞｶﾝｾｯﾃｲ", show_timer_str)
                # Show_Textの更新はここでは不要だが、他のコードで参照されているなら維持
                Show_Text = show_timer_str 

            # Dキー、Bキーの処理は元のコードのまま
            elif timer_set_key == "D":
                if len(timer_str) == 0:
                    display_code.Show_display(lcd, "ｼﾞｶﾝｦ", "ﾆｭｳﾘｮｸ!")
                    continue
                # returnする前に最後の表示を更新（show_timer_strは既に上記で最新になっているはず）
                display_code.Show_display(lcd, "ｾｯﾃｲｼﾏｼﾀ", show_timer_str) 
                time.sleep(0.5)
                return show_timer_str
            elif timer_set_key == "B":
                return "BACK"
            elif timer_set_key not in ["0", ..., "9", "*", "A", "D", "B"]:
                #エラー音鳴らす
                speaker_code.play_sound(SOUND_ERROR)
                continue
            
        # キー入力がない場合（Noneが返された場合）は、何もせずにループの先頭に戻る
        # time.sleep() など、チャタリング対策やCPU負荷軽減の処理が別途必要になることが多い

def time_str_to_int(timer_str):
    #タイマー文字列を秒単位の整数に変換する
    parts = timer_str.split(":")
    if len(parts) > 2:
        seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        seconds = int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 1:
        seconds = int(parts[0])
    else:
        seconds = 0
    return seconds

def time_int_to_str(seconds):
    #秒単位の整数をタイマー文字列に変換する
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02}:{minutes:02}:{secs:02}"
    else:
        return f"{minutes:02}:{secs:02}"
    
def Control_Light():
    global MOTOR_CURRENT_ANGLE
    key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
    #ライトの位置調整
    if key == "4":
        # 左回転
        MOTOR_CURRENT_ANGLE = motor_code.Spin_Motor(LIGHT_MOTOR_PIN,"clockwise",MOTOR_CURRENT_ANGLE,DEFAULT_MOTOR_SPIN_ANGLE)
    elif key == "6":
        # 右回転
        MOTOR_CURRENT_ANGLE = motor_code.Spin_Motor(LIGHT_MOTOR_PIN,"counterclockwise",MOTOR_CURRENT_ANGLE,DEFAULT_MOTOR_SPIN_ANGLE)
    # ライトのON/OFF切り替え
    elif key == "5":
        Control_Light_1_ONOFF()
    elif key == "2":
        Control_Light_2_ONOFF()
    elif key == "B":
        return "BACK"

def Study(Study_Time, Rest_Time, Selected_Task = None):
    global IS_STUDYING
    
    # 勉強開始：フラグON
    IS_STUDYING = True
    
    display_code.Show_display(lcd, "ﾍﾞﾝｷｮｳｰｽﾀｰﾄ", None)
    Total_Study_Time_seconds = 0

    # --- パターンA: 時間指定なしモード ---
    if (Study_Time == None):
        time.sleep(1)
        display_code.Show_display(lcd, Selected_Task, None)
        while True:
            task_end_key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
            if task_end_key == "D":
                break
            Control_Light()

            if IS_DISTRACTING:
                speaker_code.play_sound(SOUND_ALARM)
                display_code.Show_display(lcd, "ｽﾏﾎｦ", "ﾔﾒﾅｻｲ!")
            
            time.sleep(1)
            Total_Study_Time_seconds += 1
            if Total_Study_Time_seconds % CHECK_STUDY_TIME == 0:
                camera_code.Take_Photo(0, "study_check.jpg")
                if MODEL_CHECK_PEOPLE:
                    person_detected = check_people_code.Check_people(MODEL_CHECK_PEOPLE,"study_check.jpg")
                    if not person_detected:
                        speaker_code.play_sound(SOUND_ALARM)
        
        display_code.Show_display(lcd, "ﾍﾞﾝｷｮｳｰｵﾜﾘ", None)
        speaker_code.play_sound(SOUND_FANFARE)
        IS_STUDYING = False
        return
    
    # --- パターンB: 時間指定ありモード ---
    while True:
        # 勉強タイマー設定
        Time_Left_seconds = time_str_to_int(Study_Time)
        start_time = time.time() 
        Total_Study_Time_seconds = 0

        # 勉強タイマーループ
        while Time_Left_seconds > 0:
            Control_Light()
            if IS_DISTRACTING:
                speaker_code.play_sound(SOUND_ALARM)
                display_code.Show_display(lcd, "ｽﾏﾎｦ", "ﾔﾒﾅｻｲ!")

            current_time = time.time()
            elapsed_time = current_time - start_time
            
            if elapsed_time >= 1.0:
                Time_Left_seconds -= 1
                Total_Study_Time_seconds += 1
                start_time = current_time 

                if Selected_Task == None:
                    display_code.Show_display(lcd, time_int_to_str(Time_Left_seconds), None)
                else:
                    display_code.Show_display(lcd, Selected_Task, time_int_to_str(Time_Left_seconds))
                
                if Total_Study_Time_seconds % CHECK_STUDY_TIME == 0:
                    camera_code.Take_Photo(0, "study_check.jpg")
                    if MODEL_CHECK_PEOPLE:
                        person_detected = check_people_code.Check_people(MODEL_CHECK_PEOPLE,"study_check.jpg")
                        if not person_detected:
                            speaker_code.play_sound(SOUND_ALARM)

        # 勉強終了
        speaker_code.play_sound(SOUND_FANFARE)
        if Rest_Time == None:
            IS_STUDYING = False
            return

        if Total_Study_Time_seconds > 0:
            Save_Study_Time(Total_Study_Time_seconds)

        # 休憩開始
        Time_Left_seconds = time_str_to_int(Rest_Time)
        start_time = time.time()
        
        # 休憩タイマーループ
        while Time_Left_seconds > 0:
            current_time = time.time()
            elapsed_time = current_time - start_time
            task_end_key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
            if task_end_key == "D":
                IS_STUDYING = False
                return
            if elapsed_time >= 1.0:
                Time_Left_seconds -= 1
                start_time = current_time
                display_code.Show_display(lcd, "ｷｭｳｹｲｰ", time_int_to_str(Time_Left_seconds))
        
        speaker_code.play_sound(SOUND_ALARM)
        
    # 重複していたコード（global IS_STUDYING ...）はここで削除済み

def Control_Light_1_ONOFF():
    global LIGHT1_ON
    if LIGHT1_ON:
        light_code.Light_OFF(LIGHT_PIN_1)
        LIGHT1_ON = False
    else:
        light_code.Light_ON(LIGHT_PIN_1)
        LIGHT1_ON = True

def Control_Light_2_ONOFF():
    global LIGHT2_ON
    if LIGHT2_ON:
        light_code.Light_OFF(LIGHT_PIN_2)
        LIGHT2_ON = False
    else:
        light_code.Light_ON(LIGHT_PIN_2)
        LIGHT2_ON = True

def get_ip_address():
    # UDPソケットを作成
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 外部のIPアドレスとポート (GoogleのDNSなど) に接続を試みる
        # 実際にデータを送信するわけではなく、ルーティング情報を取得するだけ
        s.connect(('8.8.8.8', 80))
        # 接続に使用されたソケットの名前（ローカルIPアドレスとポート）を取得
        ip_address = s.getsockname()[0]
    except Exception as e:
        ip_address = f"エラー: {e}"
    finally:
        s.close()
    
    return ip_address

def Save_Study_Time(duration_seconds):
    """
    完了した勉強時間を日付と共にCSVファイルに追記する
    """
    today = datetime.datetime.now().strftime("%Y-%m-%d") # 今日の日付 (例: 2025-11-27)
    
    # 書き込むデータ: 日付, 時間(秒)
    data_to_save = f"{today},{duration_seconds}\n"
    
    try:
        with open(HISTORY_FILE, "a") as f: # "a" (append) モードで追記
            f.write(data_to_save)
        print(f"履歴を保存しました: {today} に {duration_seconds}秒")
    except Exception as e:
        print(f"履歴ファイルの書き込みエラー: {e}")

def Get_Study_History():
    """
    study_history.csvを読み込み、日付ごとの合計勉強時間（分）を計算する
    
    Returns:
        dict: {'2025-11-27': 120, '2025-11-26': 90, ...} の形式
    """
    daily_totals = {} # 日付ごとの合計時間を保持する辞書
    
    try:
        with open(HISTORY_FILE, "r") as f:
            lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(',')
                if len(parts) == 2:
                    date_str = parts[0]
                    duration_seconds = int(parts[1])
                    
                    # 日付ごとに秒数を合計
                    daily_totals[date_str] = daily_totals.get(date_str, 0) + duration_seconds
                    
    except FileNotFoundError:
        print("履歴ファイルが見つかりませんでした。")
        return {}
    except Exception as e:
        print(f"履歴ファイルの読み込みエラー: {e}")
        return {}

    # 秒数を分に変換し、辞書のキーを降順（新しい日付順）にソート
    # 表示用の最終的な形式: [('2025-11-27', 120), ('2025-11-26', 90)]
    sorted_history = []
    for date, seconds in sorted(daily_totals.items(), reverse=True):
        minutes = round(seconds / 60)
        sorted_history.append((date, minutes))
        
    return sorted_history

@app.route('/sns_detected', methods=['GET'])
def run_flask_server():
    MAX_RETRIES = 3      # 最大再試行回数
    RETRY_DELAY = 10     # 待機時間 (秒)
    
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Flaskサーバーを起動中... (試行 {attempt + 1}/{MAX_RETRIES})")
            # サーバー起動 (成功すればここでブロックされる)
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
            
            # 成功した場合はループを抜ける（到達しないが念のため）
            break 
            
        except OSError as e:
            # エラー番号98 (Address already in use) の場合を捕捉
            if e.errno == 98:
                print(f"🚨 警告: ポート5000がTIME_WAIT状態です。{RETRY_DELAY}秒待機します...")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    print("🚨 解決できませんでした。ターミナルを再起動するか、しばらくお待ちください。")
            else:
                # その他のOSErrorの場合
                raise e

#%% メイン処理
if __name__ == '__main__':
    print("Hello, World!")
    #初期のセットアップ
    Show_Text = ""
    # charmap='A00' を追加して日本語カタカナモードにする
    lcd = CharLCD(i2c_expander='PCF8574',
                address=0x27,
                port=1,
                cols=16,
                rows=2,
                backlight_enabled=True,
                charmap='A00') # ← 日本語フォントマップを指定

    # 各モジュールの初期化
    keypad_code.Setup_keypad(ROW_PINS, COL_PINS)
    light_code.initialize_light(LIGHT_PIN_1)

    # メモリファイルから設定読み込み
    TASKS.clear()
    Read_Mode = "file"
    with open(MEMORYFILE_NAME, 'r') as f:
        for line in f:
            line = line.strip()
            # モード切替
            if line == "tasks":
                Read_Mode = "tasks"
                continue
            elif line == "default_study_time":
                Read_Mode = "default_study_time"
                continue
            elif line == "default_rest_time":
                Read_Mode = "default_rest_time"
                continue
            # モードごとのデータ読み込み
            if Read_Mode == "tasks":
                TASKS.append(line)
            elif Read_Mode == "default_study_time":
                DEFAULT_STUDY_TIME = int(line)
            elif Read_Mode == "default_rest_time":
                DEFAULT_REST_TIME = int(line)

    # Flaskサーバーを別スレッドで起動
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()
    
    #IPアドレス取得&表示
    ip_address = get_ip_address()
    display_code.Show_display(lcd, "HELLO! IPｱﾄﾞﾚｽ",ip_address)
    while True:
        key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
        if key != None:
            break


    while True:
        if Show_Text != "ﾓｰﾄﾞｦ":
            display_code.Show_display(lcd, "ﾓｰﾄﾞｦ", "ｾﾝﾀｸｼﾃｸﾀﾞｻｲ")
            Show_Text = "ﾓｰﾄﾞｦ"
            time.sleep(1)
        selected_mode = select_from_list(MODE)

        # モード選択

        # デフォルト勉強モード
        if selected_mode == "ﾍﾞﾝｷｮｳ":
            Study_Time = time_int_to_str(DEFAULT_STUDY_TIME)
            Rest_Time = time_int_to_str(DEFAULT_REST_TIME)
            Study(Study_Time, Rest_Time)
        
        #ライト調整モード
        elif selected_mode == "ﾗｲﾄ":
            while True:
                result = Control_Light()
                if result == "BACK":
                    break
        # タスク選択モード＋タイマー設定モード
        elif selected_mode == "ﾀｽｸ+ﾀｲﾏｰ":
            # タスク選択モード
            while True:
                selected_task = select_from_list(TASKS)
                if selected_task == "BACK":
                    break
                elif selected_task == "ｼﾞﾕｳﾆｭｳﾘｮｸ":
                    new_task = Frick_Input()
                    if new_task == "BACK":
                        continue
                    TASKS.insert(-1, new_task)
                    continue
                else:
                    break
            if selected_task == "BACK":
                continue
            # タイマー設定モード
            set_time = set_timer()
            if set_time == "BACK":
                continue
            # 選択結果表示
            display_code.Show_display(lcd, selected_task, set_time)
            time.sleep(1)
            Study(set_time, None,selected_task)

        # タスク選択モード
        elif selected_mode == "ﾀｽｸｾｯﾃｲ":
            while True:
                selected_task = select_from_list(TASKS)
                if selected_task == "BACK":
                    break
                elif selected_task == "ｼﾞﾕｳﾆｭｳﾘｮｸ":
                    new_task = Frick_Input()
                    if new_task == "BACK":
                        continue
                    TASKS.insert(-1, new_task)
                    continue
                break
            if selected_task == "BACK":
                continue
            display_code.Show_display(lcd, "ﾍﾞﾝｷｮｳｰｽﾀｰﾄ", None)
            time.sleep(1)
            Study(None, None, selected_task)

        # タイマー設定モード
        elif selected_mode == "ﾀｲﾏｰｾｯﾃｲ":
            set_time = set_timer()
            if set_time == "BACK":
                continue
            display_code.Show_display(lcd, set_time, "ｾｯﾃｲｼﾏｼﾀ")
            time.sleep(1)
            Study(set_time,None)

        elif selected_mode == "IPｱﾄﾞﾚｽ":
            while True:
                if Show_Text != "IPアドレス":
                    display_code.Show_display(lcd, "IPｱﾄﾞﾚｽ",ip_address)
                    Show_Text = "IPアドレス"
                Back_key = keypad_code.get_key(ROW_PINS, COL_PINS, KEYPAD)
                if Back_key == "B":
                    break

        elif selected_mode == "ｵﾌﾟｼｮﾝ":
            while True:
                selected_option = select_from_list(OPTION)
                if selected_option == "BACK":
                    break
                elif selected_option == "ﾀｽｸﾆｭｳﾘｮｸ":
                    new_task = Frick_Input()
                    if new_task == "BACK":
                        continue
                    TASKS.append(new_task)
                    continue
                elif selected_option == "ﾀｽｸｻｸｼﾞｮ":
                    task_to_delete = select_from_list(TASKS)
                    if task_to_delete == "BACK":
                        continue
                    if task_to_delete == "ｼﾞｭｳﾆｭｳﾘｮｸ":
                        display_code.Show_display(lcd,"ｻｸｼﾞｮｴﾗｰ")
                        continue
                    TASKS.remove(task_to_delete)
                    time.sleep(1)
                    continue
                elif selected_option == "ﾍﾞﾝｷｮｳｼﾞｶﾝｾｯﾃｲ":
                    new_study_time = set_timer()
                    if new_study_time == "BACK":
                        continue
                    DEFAULT_STUDY_TIME = time_str_to_int(new_study_time)
                    time.sleep(1)
                    continue
                elif selected_option == "ｷｭｳｹｲｼﾞｶﾝｾｯﾃｲ":
                    new_rest_time = set_timer()
                    if new_rest_time == "BACK":
                        continue
                    DEFAULT_REST_TIME = time_str_to_int(new_rest_time)
                    time.sleep(1)
                    continue
                elif selected_option == "ｶｸﾆﾝｼﾞｶﾝｾｯﾃｲ":
                    new_check_time = set_timer()
                    if new_check_time == "BACK":
                        continue
                    CHECK_STUDY_TIME = time_str_to_int(new_check_time)
                    time.sleep(1)
                    continue
                else:
                    break
            if selected_option == "BACK":
                continue

                
        # 終了モード        
        elif selected_mode == "ｼｭｳﾘｮｳ":
            break

        time.sleep(0.1)
    
    while (LIGHT_MOTOR_PIN.get_position() < -50):
        print("aaa")    
        motor_code.Set_Motor_to_Start(LIGHT_MOTOR_PIN,LIGHT_MOTOR_PIN.get_position())

    with open(MEMORYFILE_NAME, 'w', encoding='utf-8') as f:
        f.write("tasks\n")
        for task in TASKS:
            f.write(task + "\n")
        f.write("default_study_time\n")
        f.write(str(DEFAULT_STUDY_TIME) + "\n")
        f.write("default_rest_time\n")
        f.write(str(DEFAULT_REST_TIME) + "\n")

    #GPIO.cleanup()
    lcd.close(clear=True)
    print("終了します。")