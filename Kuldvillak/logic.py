from tkinter.messagebox import showinfo
import pygame
import serial
import time
import threading
import sqlite3
import random
import re
import csv
import ui
import os
from datetime import datetime

pygame.init()

#Ekraani seaded
WIDTH, HEIGHT = 800, 600
COLUMNS, ROWS = 6, 5
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE) #Võimaldab ekraani suurust muuta
ui.init_ui(screen)
pygame.display.set_caption("Kuldvillak") #Kuvab ekraani ülaosas rakenduse nime

#Kasutusel värvid
WHITE = (255, 255, 255)
BLUE = (20, 20, 150)
YELLOW = (255, 215, 0)

#Mängus kasutusel olevad pildid ja ikoonid
ui.BATTERY_ICON = pygame.image.load("battery_icon.png") #(allikas: https://www.flaticon.com/free-icon/battery-status_3103496?term=battery&page=2&position=70&origin=tag&related_id=3103496 )
ui.BATTERY_ICON = pygame.transform.scale(ui.BATTERY_ICON, (24, 24))
ui.BATTERY_ICON_OK = pygame.image.load("batter_icon_full.png")  # (allikas: https://www.flaticon.com/free-icon/power_16725843?term=battery&page=1&position=61&origin=tag&related_id=16725843.)
ui.BATTERY_ICON_OK = pygame.transform.scale(ui.BATTERY_ICON_OK, (24, 24))
ui.PLUS_IMG = pygame.image.load("add.png") # (allikas: https://www.flaticon.com/free-icon/add_10337471?term=plus&page=1&position=33&origin=search&related_id=10337471)
ui.MINUS_IMG = pygame.image.load("minus.png") # (allikas: https://www.flaticon.com/free-icon/minus_10337430?related_id=10336176&origin=search)
# Piltküsimuse allikas(bird.jpg): https://et.wikipedia.org/wiki/Rabapistrik#/media/Fail:Falco_peregrinus_nest_USFWS_free.jpg

#Mänguvälja seaded 
money_values = [[10 * (r + 1) for r in range(ROWS)] for _ in range(COLUMNS)]

#Mängus kasutatavad muutujad
num_teams = None
teams = {}
selected_team = None
selected_question = None
hobevillak_question = []
showing_question = False
showing_answer = False
selected_cell = [0, 0]
team_selection_done = False
current_team_selection = 1
entering_team_names = False
temp_team_name = ""
team_names = []
selected_points = 0
latest_button_press = None
showing_instructions = False
question_faded = False
answer_faded = False
timer_start = None
DOUBLE_JEOPARDY_ROWS = 5
DOUBLE_JEOPARDY_COLS = 6
TIMER_DURATION = 15
low_battery_controllers = {}  
timer_paused = False
pause_time = None
current_round = 1
double_jeopardy_loaded = False
in_final_jeopardy = False
final_question = ""
final_answer = ""
final_wagers = {}
final_answers = {}
final_category = ""
eligible_final_teams = []
final_answer_revealed = False
final_scores_updated = False
welcome_screen = True
showing_menu_options = False
timer_started = False
DEBUG_MODE = False 
final_back_button_rect = None
showing_final_intro = False
final_wager_phase = False
waiting_final_intro_space = False
image_db = {}
controller_test_active = False
final_question_reveal = False 
current_betting_team_index = 0 
current_wager_input = ""
plus_buttons = []
minus_buttons = []
debug_button_rect = None
ser = None
current_screen = "welcome" 
showing_category_intro = False
category_intro_start_time = None
category_intro_index = 0
final_phase_state = "intro"
questions_db = {}
answers_db = {}

'''Ühendus Arduino Unoga COM3 pordi kaudu, allikas: https://forum.arduino.cc/t/serial-communication-with-python-beginner-qestion/944780/17
modifitseeritud Chat GPT abil :ChatGPT. (2025), OpenAI. Kasutatud märts 5, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com 
'''
def initialize_serial_connection():
    global ser, DEBUG_MODE
    if ser and ser.is_open:
        print("🔁 Serial already connected.")
        return True  # already connected!

    try:
        ser = serial.Serial("COM3", 9600, timeout=1)
        time.sleep(2)
        ser.flush()
        print("✅ Serial connected to Arduino on COM3")
        threading.Thread(target=read_arduino, daemon=True).start()
        return True
    except serial.SerialException as e:
        print("❌ Error: Could not open serial port:", e)
        ser = None
        return False

''''Laeb küsimused andmebaasi tabelitest, allikas: https://github.com/jesstess/JeopardyDatabase/blob/master/jeopardy_clues.py ja
modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud märts 5, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com 
'''
def load_questions_from_db():
    global questions_db, answers_db
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()

    table_name = "jeopardy" if current_round == 1 else "double_jeopardy"
    cursor.execute(f"SELECT category, row, col, question, answer, image FROM {table_name}")
    data = cursor.fetchall()

    questions_db.clear()
    answers_db.clear()
    image_db.clear()
    #Laeb pildi tee andmebaasist
    for category, row, col, question, answer, image in data:
        if category in ui.get_current_categories(current_round):
            questions_db[(col, row)] = question
            answers_db[(col, row)] = answer
            if image:
               script_dir = os.path.dirname(__file__)
               image_path = os.path.join(script_dir, image)
               image_db[(col, row)] = image_path

    conn.close()
    ui.image_db = image_db
    
'''Laeb eraldi finaal vooru küsimuse andmebaasi tabelist "final_jeopardy"(eraldi vajalik selle veergude arvu tõttu)
Allikas: https://github.com/jesstess/JeopardyDatabase/blob/master/jeopardy_clues.py ja
modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud märts 5, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com 
'''
def load_final_question():
    global final_question, final_answer, final_category
    conn = sqlite3.connect("questions.db")
    cursor = conn.cursor()
    cursor.execute("SELECT category, question, answer FROM final_jeopardy LIMIT 1")
    row = cursor.fetchone()
    if row:
        final_category, final_question, final_answer = row
    conn.close()

'''Juhuslik Hõbevillaku küsimuse valimine vastavalt voorule
Allikas: https://www.geeksforgeeks.org/python-random-sample-function/
'''
def select_hobevillak_question():
    global hobevillak_questions
    valid_questions = list(questions_db.keys())
    hobevillak_questions = []

    if valid_questions:
        count = 1 if current_round == 1 else 2
        hobevillak_questions = random.sample(valid_questions, min(count, len(valid_questions)))
        
load_questions_from_db()
select_hobevillak_question()
print(f"Laetud {len(questions_db)} küsimused")

'''Mängijate arvu valimine nooleklahvide abil
Allikas: https://www.geeksforgeeks.org/how-to-get-keyboard-input-in-pygame/
'''
def handle_team_selection(event):
    global num_teams, current_team_selection, teams, team_selection_done, entering_team_names
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP:
            current_team_selection = max(1, current_team_selection - 1)
        elif event.key == pygame.K_DOWN:
            current_team_selection = min(6, current_team_selection + 1)
        elif event.key == pygame.K_RETURN:
            num_teams = current_team_selection
            entering_team_names = True
            
'''Mängija nimede sisestus klaviatuurilt
Allikas: https://www.geeksforgeeks.org/how-to-get-keyboard-input-in-pygame/
modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud märts 5, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com
'''
def handle_team_name_entry(event):
    global temp_team_name, team_names, entering_team_names,showing_category_intro, category_intro_start_time,category_intro_index, team_selection_done, teams
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_BACKSPACE:
            temp_team_name = temp_team_name[:-1]
        elif event.key == pygame.K_RETURN:
            if temp_team_name.strip():
                team_names.append(temp_team_name.strip())
                temp_team_name = ""
                if len(team_names) == num_teams:
                    
                    entering_team_names = False
                    team_selection_done = True
                    teams = {name: 0 for name in team_names}
                    showing_category_intro = True
                    category_intro_start_time = time.time()
                    category_intro_index = 0

                    #Kui ei ole test versioon ilma pultideta
                    if not DEBUG_MODE and ser is None:
                        initialize_serial_connection()              
        elif event.unicode.isprintable():
            temp_team_name += event.unicode

'''Topeltvillaku vooru laadimine'''           
def load_double_jeopardy_round():
    global money_values, revealed, current_round, double_jeopardy_loaded
    current_round = 2
    double_jeopardy_loaded = True
    money_values = [[20 * (r + 1) for r in range(DOUBLE_JEOPARDY_ROWS)] for _ in range(DOUBLE_JEOPARDY_COLS)]
    ui.revealed = [[False for _ in range(DOUBLE_JEOPARDY_ROWS)] for _ in range(DOUBLE_JEOPARDY_COLS)]
    load_questions_from_db()
    print("Topeltvillakusse switch!")
    select_hobevillak_question()
    
'''Kontrollib/Tagastab, kas kõik küsimused voorus on vastatud'''
def is_round_complete():
    return all(all(row) for row in ui.revealed)

'''Küsib ja tagastab mängijate sisestatud finaalvooru panused
Allikas: https://www.geeksforgeeks.org/how-to-get-keyboard-input-in-pygame/
Allikas:  https://www.pygame.org/docs/ref/font.html#pygame.font.Font.render
'''
def ask_for_final_wager(team_name):
    input_active = True
    wager_input = ""
    max_points = teams[team_name]

    while input_active:
        screen.fill(BLUE)

        TITLE_FONT = ui.get_dynamic_font(0.045)
        INPUT_FONT = ui.get_dynamic_font(0.07)
        title = f"{team_name}, palju panustad? (max {max_points}):"
        title_text = TITLE_FONT.render(title, True, WHITE)
        title_rect = title_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
        screen.blit(title_text, title_rect)

        input_text = INPUT_FONT.render(wager_input if wager_input else "0", True, YELLOW)
        input_rect = input_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(input_text, input_rect)

        pygame.display.flip()
        #Panuste sisestamine
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    wager_input = wager_input[:-1]
                elif event.unicode.isdigit():
                    wager_input += event.unicode

    wager = int(wager_input) if wager_input else 0
    return min(wager, max_points)

'''Küsib, kas finaalvooru mängijad vastasid õigesti
Allikas: https://www.pygame.org/docs/ref/event.html#pygame.event.get
'''
def ask_final_correctness(team_name):
    input_active = True
    while input_active:
        screen.fill(BLUE)
        FONT = ui.get_dynamic_font(0.05)
        prompt = FONT.render(f"Kas {team_name} vastas õigesti? (Y/N)", True, WHITE)
        rect = prompt.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(prompt, rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return True
                elif event.key == pygame.K_n:
                    return False

'''Tagasi menüüsse navigeerimine, lähtestades kõik algolekud'''
def back_to_menu_from_grid():
    global showing_menu_options, showing_question, showing_answer, selected_question
    global timer_started, timer_paused, pause_time, question_faded, answer_faded
    global selected_team, selected_col, selected_row, latest_button_press

    print("↩️ Tagasi menüüsse mänguväljalt.")
    showing_menu_options = True
    showing_question = False
    showing_answer = False
    selected_question = None
    selected_col = None
    selected_row = None
    timer_started = False
    timer_paused = False
    pause_time = None
    question_faded = False
    answer_faded = False
    latest_button_press = None

'''Tagasi avaekraanile liikumine, lähtestades algolekusse kõik senised mängu olekud'''
def reset_to_welcome_screen():
    global welcome_screen, showing_menu_options, DEBUG_MODE, teams, team_selection_done
    global temp_team_name, team_names, num_teams, selected_question, selected_team
    global showing_question, showing_answer, current_round, double_jeopardy_loaded
    global in_final_jeopardy, final_answer_revealed, final_scores_updated
    global final_question, final_answer, final_category, final_wager_phase
    global waiting_final_intro_space, final_wagers, final_answers, eligible_final_teams
    global controller_test_active, showing_instructions, showing_final_intro
    global latest_button_press, answer_faded, question_faded, timer_paused, pause_time
    welcome_screen = True
    showing_menu_options = False
    DEBUG_MODE = False
    teams.clear()
    team_selection_done = False
    temp_team_name = ""
    team_names.clear()
    num_teams = None
    selected_question = None
    selected_team = None
    showing_question = False
    showing_answer = False
    answer_faded = False
    question_faded = False
    latest_button_press = None
    current_round = 1
    double_jeopardy_loaded = False
    in_final_jeopardy = False
    final_answer_revealed = False
    final_scores_updated = False
    final_question = ""
    final_answer = ""
    final_category = ""
    final_wager_phase = False
    waiting_final_intro_space = False
    final_wagers.clear()
    final_answers.clear()
    eligible_final_teams.clear()
    controller_test_active = False
    showing_instructions = False
    showing_final_intro = False
    
'''Võimaldab värskendada mängija punktiskoori'''
def update_team_score(team, points):
    if team in teams:
        teams[team] += points

'''Mängu lõpptulemuste salvestamine andmebaasi tabelisse results
Allikas: https://towardsdatascience.com/sqlite-3-using-pythons-sqlite-3-module-to-save-program-data-bc6b34dcc721/
modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud aprill 23, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com
'''
def save_results_to_db():
    try:
        conn = sqlite3.connect("questions.db")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS results (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         player_name TEXT NOT NULL,
         points INTEGER NOT NULL,
         played_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')

        for team, score in teams.items():
            cursor.execute("INSERT INTO results (player_name, points) VALUES (?, ?)", (team, score))

        conn.commit()
        conn.close()
        print("✅ Tulemused salvestatud andmebaasi.")
    except Exception as e:
        print(f"❌ Viga andmebaasi salvestamisel: {e}")

'''Mängu lõpptulemuste salvestamine CSV faili        
Allikas: https://www.geeksforgeeks.org/exporting-variable-to-csv-file-in-python/
Modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud aprill 23, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com
'''
def export_results_to_csv(filename="lõpptulemused.csv"):
    try:
        conn = sqlite3.connect("questions.db")
        cursor = conn.cursor()

        cursor.execute("SELECT player_name, points, played_at FROM results ORDER BY points DESC")
        results = cursor.fetchall()

        with open(filename, mode="w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Mängija", "Punktid", "Aeg"])
            for row in results:
                writer.writerow(row)

        conn.close()
        print(f"💾 Tulemused eksporditud CSV faili: {filename}")
    except Exception as e:
        print(f"❌ Viga CSV eksportimisel: {e}")
        
'''Klaviatuuri vajutuste loogika
#Allikas: https://www.geeksforgeeks.org/how-to-get-keyboard-input-in-pygame/
##Modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud märts 5, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com
'''
def handle_key_press(event):
    global showing_question, showing_answer, selected_team, selected_points, answer_faded
    global team_selection_done, entering_team_names, temp_team_name, team_names, latest_button_press, selected_question
    global num_teams, teams, revealed, questions_db, answers_db
    global showing_menu_options, showing_instructions, current_team_selection
    global timer_started, timer_start, question_faded, final_answer_revealed
    global timer_paused, pause_time
    global in_final_jeopardy, showing_final_intro, final_wager_phase, waiting_final_intro_space, final_phase_state
    global controller_test_active

    print(f"🔑 Key Pressed: {pygame.key.name(event.key)}")
    #Instruktsioonide ekraan
    if showing_instructions:
       if event.key == pygame.K_BACKSPACE:
          print("🏠 Returning to Menu from Instructions...")
          showing_instructions = False
          showing_menu_options = True
       return
    #Puldi test režiimi ekraan
    if controller_test_active:
       if event.key == pygame.K_a:
         latest_button_press = "Pult 1"
         ui.controller_press_log.append((f"Pult 1 vajutas", time.time()))
         print("🧪 Simuleeritud: Pult 1 vajutas")
         timer_paused = True
         pause_time = time.time()
       elif event.key == pygame.K_b:
         latest_button_press = "Pult 2"
         ui.controller_press_log.append((f"Pult 2 vajutas", time.time()))
         print("🧪 Simuleeritud: Pult 2 vajutas")
         timer_paused = True
         pause_time = time.time()
       elif event.key == pygame.K_c:
         latest_button_press = "Pult 3"
         print("🧪 Simuleeritud: Pult 3 vajutas")
         timer_paused = True
         pause_time = time.time()
       elif event.key == pygame.K_d:
         latest_button_press = "Pult 4"
         print("🧪 Simuleeritud: Pult 4 vajutas")
         timer_paused = True
         pause_time = time.time()
       elif event.key == pygame.K_e:
         latest_button_press = "Pult 5"
         print("🧪 Simuleeritud: Pult 5 vajutas")
         timer_paused = True
         pause_time = time.time()
       elif event.key == pygame.K_f:
         latest_button_press = "Pult 6"
         print("🧪 Simuleeritud: Pult 6 vajutas")
         timer_paused = True
         pause_time = time.time()
       elif event.key == pygame.K_BACKSPACE:
         controller_test_active = False
         showing_menu_options = True
         print("↩️ Lahkuti puldi testist")
       return
    
    if not team_selection_done:
        if entering_team_names:
            handle_team_name_entry(event)
        else:
            if event.key == pygame.K_UP:
                current_team_selection = max(1, current_team_selection - 1)
            elif event.key == pygame.K_DOWN:
                current_team_selection = min(6, current_team_selection + 1)
            elif event.key == pygame.K_RETURN:
                num_teams = current_team_selection
                entering_team_names = True
        return
    #ENTER klahvi kasutus loogika
    if event.key == pygame.K_RETURN:
        if waiting_final_intro_space:
             showing_final_intro = False
             waiting_final_intro_space = False
             final_wager_phase = True
        elif showing_question and not timer_started:
             timer_started = True
             timer_start = time.time()
             print("Timer alustas")
        elif showing_question and timer_started:
            pass
        elif showing_answer:
             showing_answer = False
             answer_faded = False
        elif in_final_jeopardy and not final_answer_revealed:
             final_answer_revealed = True
    #SPACE klahvi vajutus
    elif event.key == pygame.K_SPACE:
            if showing_question and timer_started:
               showing_question = False
               latest_button_press = None
               showing_answer = True
               answer_faded = True
            elif showing_answer:
                showing_answer = False
                answer_faded = False 
            if showing_final_intro:
              showing_final_intro = False
              waiting_final_intro_space = False
              final_wager_phase = True        
            elif in_final_jeopardy and final_phase_state == "kysimus":
                 final_phase_state = "vastus"
            elif in_final_jeopardy and final_phase_state == "vastus":
                 final_phase_state = "hinnang" 
            elif in_final_jeopardy and not final_answer_revealed:
                 final_answer_revealed = True
    #ESCAPE klahvi vajutus (kogu mängu restart)
    elif event.key == pygame.K_ESCAPE:
        print("🔄 Restart mängule.")
        showing_menu_options = True
        showing_instructions = False
        team_selection_done = False
        entering_team_names = False
        temp_team_name = ""
        team_names = []
        num_teams = None
        latest_button_press = None
        selected_question = None
        showing_question = False
        showing_answer = False
        teams = {}
        revealed = [[False for _ in range(ROWS)] for _ in range(COLUMNS)]
        load_questions_from_db()

    #"Testi ilma puldita" versioonis nupuvajutuste simulatsioon
    elif DEBUG_MODE:
        team_list = list(teams.keys())
        if event.key == pygame.K_x and len(team_list) >= 1:
          latest_button_press = team_list[0]
          print(f"Simuleeritud nupuvajutus: {team_list[0]}")
        elif event.key == pygame.K_y and len(team_list) >= 2:
           latest_button_press = team_list[1]
           print(f"Simuleeritud nupuvajutus: {team_list[1]}")
        elif event.key == pygame.K_1 and len(team_list) >= 3:
          latest_button_press = team_list[2]
          print(f"Simuleeritud nupuvajutus: {team_list[2]}")
        elif event.key == pygame.K_2 and len(team_list) >= 4:
          latest_button_press = team_list[3]
          print(f"Simuleeritud nupuvajutus: {team_list[3]}")
        elif event.key == pygame.K_3 and len(team_list) >= 5:
           latest_button_press = team_list[4]
           print(f"Simuleeritud nupuvajutus: {team_list[4]}")
        elif event.key == pygame.K_4 and len(team_list) >= 6:
           latest_button_press = team_list[5]
           print(f"Simuleeritud nupuvajutus: {team_list[5]}")

        if latest_button_press:
           timer_paused = True
           pause_time = time.time()

'''Hiirevajutuste/nupude loogika
#Allikas: https://www.pygame.org/docs/ref/mouse.html
#Modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud märts 5, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com
'''
def handle_mouse_click():
    global selected_question, showing_question, selected_points, selected_col, selected_row, latest_button_press, question_faded, answer_faded
    global showing_instructions, team_selection_done, entering_team_names, temp_team_name, team_names, num_teams, teams, revealed
    global timer_paused, pause_time, final_answer_revealed, final_scores_updated
    global welcome_screen, showing_menu_options, showing_instructions
    global team_selection_done, in_final_jeopardy, double_jeopardy_loaded, current_round
    global selected_question, showing_question, selected_points, selected_col, selected_row, latest_button_press
    global question_faded, answer_faded, timer_paused, pause_time, timer_started, timer_start, showing_answer
    global  showing_final_intro, waiting_final_intro_space,final_wager_phase, final_question_reveal,final_answer_revealed, final_scores_updated
    global current_betting_team_index, final_back_button_rect, eligible_final_teams
    global DEBUG_MODE, controller_test_active, current_team_selection, start_button_rect, debug_button_rect
    global CELL_HEIGHT, showing_category_intro, category_intro_start_time, category_intro_index
    #Hiire kursori positsioon saamine
    pos = pygame.mouse.get_pos()
    
    if not welcome_screen:
        pass
    elif ui.start_button_rect and ui.start_button_rect.collidepoint(pos):
       if initialize_serial_connection():
          welcome_screen = False
          showing_menu_options = True
          return
       else:
          showinfo("Viga", "Arduino ühendus ebaõnnestus. Kasuta 'Testi ilma pultideta' režiimi.")
    elif ui.debug_button_rect and ui.debug_button_rect.collidepoint(pos):
        DEBUG_MODE = True
        team_selection_done = True
        welcome_screen = False
        showing_menu_options = True
        print("Test versioon puldita alustatud")
        ui.low_battery_controllers[2] = ("3.45V", time.time())  #Simuleeritud pinge kuvamine arendajale testimiseks
        ui.low_battery_controllers[1] = ("8.45V", time.time())
    #Meeskonnad valitud siis näidatakse mänguvälja
    if team_selection_done and not showing_question and not showing_answer:
        ui.draw_grid(current_round, money_values, teams)
        pygame.display.flip()
    #Menüü ekraanil nuppude vajutamine    
    if showing_menu_options:
       if not ui.menu_buttons:
           ui.draw_menu_options()
           pygame.display.flip()
       for rect, label in ui.menu_buttons:
            if rect.collidepoint(pos):
              if label == "Alusta mängu":
                if not DEBUG_MODE:
                   initialize_serial_connection()                
                showing_menu_options = False
                team_selection_done = False
                entering_team_names = False
                temp_team_name = ""
                team_names = []
                teams.clear()
                num_teams = None
                current_team_selection = 1
                selected_question = None
                showing_question = False
                showing_answer = False
                answer_faded = False
                return           
              
              elif label == "Instruktsioonid":
                showing_menu_options = False
                showing_instructions = True
                
              elif label == "1. voor":
                   showing_category_intro = True
                   category_intro_start_time = time.time()
                   category_intro_index = 0 
                   in_final_jeopardy = False
                   final_answer_revealed = False
                   final_scores_updated = False
                   current_round = 1
                   double_jeopardy_loaded = False
                   team_selection_done = True
                   if not DEBUG_MODE and ser is None:
                     initialize_serial_connection()
                   load_questions_from_db()
                   showing_menu_options = False
                   
              elif label == "Puldi test":
                   controller_test_active = True
                   showing_menu_options = False
                   latest_button_press = None
                   
              elif label == "2. voor":
                   showing_category_intro = True
                   category_intro_start_time = time.time()
                   category_intro_index = 0 
                   in_final_jeopardy = False
                   final_answer_revealed = False
                   final_scores_updated = False
                   current_round = 2
                   double_jeopardy_loaded = True
                   team_selection_done = True
                   if not DEBUG_MODE and ser is None:
                     initialize_serial_connection()
                   load_double_jeopardy_round()
                   showing_menu_options = False
                   
              elif label == "Finaal":
                   team_selection_done = True
                   if not DEBUG_MODE and ser is None:
                     initialize_serial_connection()
                   if DEBUG_MODE and not teams:
                       teams["Mari"] = 2200
                       eligible_final_teams.append("Mari")
                       print("🧪 DEBUG MODE: Test mängija loodud(100 punktiga)")                       
                   eligible_final_teams = [team for team, score in teams.items() if score > 0]
                   if eligible_final_teams:
                          load_final_question()
                          print(f"✅ Finaal laetud: {final_category} | {final_question}") 
                          in_final_jeopardy = True
                          showing_final_intro = True
                          waiting_final_intro_space = False
                          final_wager_phase = False
                          final_answer_revealed = False
                          final_scores_updated = False
                          final_back_button_rect = None
                          final_wagers.clear()
                          final_answers.clear()
                          current_betting_team_index = 0
                          showing_menu_options = False
                          print("🏁 Finaalvoor valitud menüüst")                                 
              if DEBUG_MODE and not teams:
                 teams["Mari"] = 100
                 print("🧪 DEBUG MODE: Test mängija loodud (100 punktiga))")

              elif label == "Kontrolleri Test":
                  controller_test_active = True
                  showing_menu_options = False
                  latest_button_press = None
                  
              elif label == "Tagasi":
                   print(f"🧭 Tagasi clicked, DEBUG_MODE: {DEBUG_MODE}, welcome_screen: {welcome_screen}")
                   reset_to_welcome_screen()
                   print(f"🧼 After reset: welcome_screen={welcome_screen}, showing_menu_options={showing_menu_options}")
                   pygame.display.flip()
              return
       return
    #Finaalvoorus liikumine
    if in_final_jeopardy and ui.final_back_button_rect is not None and ui.final_back_button_rect.collidepoint(pos):
        print("↩️ Tagasi menüüsse finaalist")
        save_results_to_db()
        export_results_to_csv()
        showinfo("Salvestatud", "Lõpptulemused salvestatud CSV faili.")
        in_final_jeopardy = False
        final_answer_revealed = False
        final_scores_updated = False
        final_wagers.clear()
        eligible_final_teams.clear()
        showing_menu_options = True
        return    
    #Menüüsse nupu vajutamine 
    if ui.back_button_rect and ui.back_button_rect.collidepoint(pos):
        back_to_menu_from_grid()
        return
    #Küsimustele vajutamine mänguväljal
    col = min(max(pos[0] * ui.COLUMNS // screen.get_width(), 0), ui.COLUMNS - 1)
    row = min(max((pos[1] - ui.CELL_HEIGHT) // ui.CELL_HEIGHT, 0), ui.ROWS - 1) 
    if (col, row) in questions_db:
        ui.revealed[col][row] = True
        selected_question = questions_db[(col, row)]
        selected_col = col
        selected_row = row
        showing_question = True
        latest_button_press = None
        question_faded = False
        answer_faded = False
        timer_paused = False
        pause_time = None 
        timer_started = False
        timer_start = None
    #Hõbevillaku punktisummade käsitlemine
    if (col, row) in hobevillak_questions:
        selected_points = ui.ask_for_hobevillak_points()
    else:
        selected_points = money_values[col][row]

'''Loeb Arduino Uno serial monitorist infot, et kasutada neid mänguloogikas
Allikas: https://forum.arduino.cc/t/using-python-to-read-and-process-serial-data-from-arduino/1059079
Modifitseeritud Chat GPT abil: (2025), OpenAI. Kasutatud märts 5, 2025. [Võrgumaterjal] Saadaval: https://chat.openai.com
'''
def read_arduino():
    global latest_button_press, timer_paused, pause_time, ser
    while True:
        try:
            if ser is None:
                time.sleep(0.5)
                continue

            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(f"Received from Arduino: {data}")
                    #Milline mängija(pult) vajutas nuppu
                    if "Button Pressed" in data:
                        if "Controller 1" in data:
                            latest_button_press = "Mängija 1"
                        elif "Controller 2" in data:
                            latest_button_press = "Mängija 2"
                        elif "Controller 3" in data:
                            latest_button_press = "Mängija 3"
                        elif "Controller 4" in data:
                            latest_button_press = "Mängija 4"
                        elif "Controller 5" in data:
                            latest_button_press = "Mängija 5"
                        elif "Controller 6" in data:
                            latest_button_press = "Mängija 6"
                        print(f"🚀 Button Press Detected: {latest_button_press}")
                        timer_paused = True
                        pause_time = time.time()
                    #Liiga madala patarei taseme teate kuvamine
                    elif "LOW!" in data:
                         match = re.search(r"Controller (\d) .*?([\d.]+)V", data)
                         if match:
                             controller_num = int(match.group(1))
                             voltage = f"{float(match.group(2)):.2f}V"
                             ui.low_battery_controllers[controller_num] = (voltage, time.time())
                             pygame.event.post(pygame.event.Event(pygame.USEREVENT))
                         else:
                              print(f"⚠ LOW! message ignored due to missing controller ID: {data}")
                              continue
                    #Pinge kuvamine
                    elif "Voltage:" in data:
                        match = re.search(r"Controller (\d) Voltage:\s*([\d.]+)V\s+\(\d+%", data)
                        if match:
                           controller_num = int(match.group(1))
                           voltage = f"{float(match.group(2)):.2f}V"
                           ui.low_battery_controllers[controller_num] = (voltage, time.time())
                           pygame.event.post(pygame.event.Event(pygame.USEREVENT))
                    #Kui patarei tase ei ole enam madal, eemaldatakse "LOW!" teade
                    elif "BATTERY OK" in data:
                        match = re.search(r"Controller (\d) BATTERY OK", data)
                        if match:
                            controller_num = int(match.group(1))
                            if controller_num in ui.low_battery_controllers:
                                del ui.low_battery_controllers[controller_num]
                            pygame.event.post(pygame.event.Event(pygame.USEREVENT))
            time.sleep(0.05)
        except Exception as e:
            print(f"❌ Error reading from Arduino: {e}")
            ser = None
            time.sleep(1) 

#Mängu tsükkel
running = True
while running:
    screen.fill(BLUE)
    #Sündmuste käsitlemine vastavalt ekraani suuruse muutmisele, klahvi või nupuvajutusele
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            ui.update_grid_dimensions()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if welcome_screen and (ui.start_button_rect is None or ui.debug_button_rect is None):
                ui.draw_welcome_screen()
                pygame.display.flip()
            handle_mouse_click()
        elif event.type == pygame.KEYDOWN:
            if in_final_jeopardy and final_phase_state == "intro" and event.key == pygame.K_SPACE:
                final_phase_state = "panused"
            else:
                handle_key_press(event)
        elif event.type == pygame.USEREVENT:
            if showing_question:
                pass
            elif showing_instructions:
                ui.draw_instructions()
            pygame.display.flip()
        elif controller_test_active:
            ui.draw_controller_test(screen)
            pygame.display.flip()
    #Ekraanide joonistamine vastavalt mängu hetkeolekust
    if welcome_screen:
        ui.draw_welcome_screen()
    #Kategooriate kuvamine    
    elif showing_category_intro:
        elapsed = time.time() - category_intro_start_time
        if category_intro_index < len(ui.get_current_categories(current_round)):
            if elapsed >= 1:
                category_intro_index += 1
                category_intro_start_time = time.time()
            ui.draw_category_intro(current_round, category_intro_index)
        else:
            showing_category_intro = False
            if current_round == 1 and double_jeopardy_loaded:
               print("✅ Topeltvillak laetud peale kategooriate näitamist")
    #Menüü ekraani näitamine           
    elif showing_menu_options:
        ui.draw_menu_options()
    #Instruktsioonide näitamine
    elif showing_instructions:
        ui.draw_instructions()
    #Puldi test ekraani näitamine
    elif controller_test_active:
        ui.draw_controller_test(screen)
    #Finaalvooru faaside loogika
    elif in_final_jeopardy:
        if final_phase_state == "intro":
            ui.draw_final_intro(final_category)
        elif final_phase_state == "panused":
            if current_betting_team_index < len(eligible_final_teams):
                team = eligible_final_teams[current_betting_team_index]
                final_wagers[team] = ask_for_final_wager(team)
                current_betting_team_index += 1
            else:
                final_phase_state = "kysimus"
        elif final_phase_state == "ksyimus":
            ui.draw_final_question(final_question)            
        elif final_phase_state == "vastus":
             ui.draw_final_answer(final_answer)   
        elif final_phase_state == "hinnang":
            for team in eligible_final_teams:
                correct = ask_final_correctness(team)
                wager = final_wagers.get(team, 0)
                if correct:
                    teams[team] += wager
                else:
                    teams[team] -= wager
            final_phase_state = "done"
            current_round = 2
            in_final_jeopardy = False
        elif final_phase_state == "done":
            ui.draw_grid(current_round, money_values, teams)
            if not final_scores_updated:
                save_results_to_db()
                export_results_to_csv()
                showinfo("Salvestatud", "Lõpptulemused salvestatud CSV faili.")
                final_scores_updated = True
                
    #Mängijate valimine ja nimede sisestus
    elif not team_selection_done:
        if entering_team_names:
            ui.draw_team_name_entry(team_names, temp_team_name)
        else:
            ui.draw_team_selection(current_team_selection)
    #Küsimuste kuvamine
    elif showing_question:
        ui.draw_question(selected_col, selected_row, selected_question, timer_started, timer_start, timer_paused, pause_time, selected_points, latest_button_press)
        if timer_started and not timer_paused:
            remaining_time = max(0, TIMER_DURATION - (time.time() - timer_start))
            if remaining_time <= 0:
                showing_question = False
                showing_answer = True
                answer_faded = False
    #Vastuste kuvamine
    elif showing_answer:
        if not answer_faded:
            answer_faded = True
        else:
            ui.draw_answer(selected_col, selected_row, answers_db)
        if not showing_answer and is_round_complete() and current_round == 1 and not double_jeopardy_loaded:
            load_double_jeopardy_round()
    else:
        ui.draw_grid(current_round, money_values, teams)

    #Kontrollib, kas voor on lõppenud
    if is_round_complete() and current_round == 1 and not double_jeopardy_loaded and not showing_category_intro:
        current_round = 2
        showing_category_intro = True
        load_double_jeopardy_round()
        double_jeopardy_loaded = True
        category_intro_start_time = time.time()
        category_intro_index = 0             
    if is_round_complete() and current_round == 2 and not in_final_jeopardy:
        eligible_final_teams = [team for team, score in teams.items() if score > 0]
        if eligible_final_teams:
            load_final_question()
            in_final_jeopardy = True
            final_phase_state = "intro"
            final_scores_updated = False
            current_betting_team_index = 0
            final_wagers.clear()
            final_answers.clear()
    #Uue ekraani kuvamine iga tsükli lõppedes
    pygame.display.flip()
#Mäng on läbi
pygame.quit()
#Serial connection katkestatud
if ser:
    ser.close()