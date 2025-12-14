import time

def Show_display(lcd,word1,word2):
    lcd.clear()
    lcd.write_string(word1)
    if word2 != None:
        lcd.cursor_pos = (1, 0)
        lcd.write_string(word2)
    time.sleep(0.1)
