import pygame

def play_sound(sound_file):
    """指定された音声ファイルを再生する関数"""
    # pygameの初期化
    pygame.mixer.init()
    try:
        # 音声ファイルを読み込む
        pygame.mixer.music.load(sound_file)
        print(f"'{sound_file}' を再生します...")

        # 音声を再生
        pygame.mixer.music.play()

    except Exception as e:
        print(f"エラーが発生しました: {e}")