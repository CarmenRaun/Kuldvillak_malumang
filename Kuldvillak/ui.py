import pygame
import time
import os

#Mängus kasutatud fondid
CUSTOM_FONT_2 = "PressStart2P-Regular.ttf" #(allikas: https://fonts.google.com/specimen/Press+Start+2P )
CUSTOM_FONT_DYNAMIC = "Montserrat-SemiBold.ttf" #(allikas:https://fonts.google.com/specimen/Montserrat )

#Mängus kasutatud värvid ja varjud
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (20, 20, 150)
FADED_BLUE = (60, 60, 130)
YELLOW = (255, 215, 0)
GREEN = (0, 255, 127)
BUTTON_SHADOW = (200, 180, 50)

#Mängus kasutatavate piltide jaoks vajalikud muutujad
screen = None
BATTERY_ICON = None
BATTERY_ICON_OK = None
PLUS_IMG = None
MINUS_IMG = None

#Kategooriate ning rahaväärtused mänguväljal
COLUMNS, ROWS = 6, 5
categories_round1 = ["Sport", "Geograafia", "Loodus", "Kultuur", "Varia", "Huvitav"]
categories_round2 = ["Teadus", "Ajalugu", "Matemaatika", "Kunst", "Tehnoloogia", "Meelelahutus"]
money_values = [[10 * (r + 1) for r in range(ROWS)] for _ in range(COLUMNS)]
revealed = [[False for _ in range(ROWS)] for _ in range(COLUMNS)]

#Mängus kasutatavad muutujad
num_teams = None
selected_team = None
selected_question = None
selected_cell = [0, 0]
team_selection_done = False
selected_points = 0
latest_button_press = None
showing_instructions = False
question_faded = False
answer_faded = False
timer_start = None
TIMER_DURATION = 15
low_battery_controllers = {}
timer_paused = False
pause_time = None
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
back_button_rect = None
final_wager_phase = False
waiting_final_intro_space = False
image_db = {}
controller_test_active = False
current_betting_team_index = 0
current_wager_input = ""
plus_buttons = []
minus_buttons = []
debug_button_rect = None
ser = None
menu_buttons = []
current_screen = "welcome"
showing_category_intro = False
category_intro_start_time = None
category_intro_index = 0
controller_press_log = []
questions_db = {}
answers_db = {}

#Arvutab ja uuendab mänguvälja suurust vastavalt akna suuruse muutumisele
def update_grid_dimensions():
    global CELL_WIDTH, CELL_HEIGHT
    if COLUMNS == 0 or ROWS == 0:
        CELL_WIDTH = 100
        CELL_HEIGHT = 100
    else:
        CELL_WIDTH = screen.get_width() // COLUMNS
        CELL_HEIGHT = (screen.get_height() - 200) // (ROWS + 1)

#Tagastatakse dünaamiliselt muutuv tekst, mis sõltub akna suurusest
def get_dynamic_font(size_factor):
    size = max(20, int(screen.get_width() * size_factor))
    return pygame.font.Font(CUSTOM_FONT_DYNAMIC, size)

#Teksti jaotamine mitmele reale, et mahutada optimaalselt ekraanile
def render_multiline_text(text, font, color, max_width):
    words = text.split(' ')
    lines = []
    current_line = ''

    for word in words:
        test_line = current_line + word + ' '
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + ' '
    lines.append(current_line)
    rendered_lines = [font.render(line.strip(), True, color) for line in lines]
    return rendered_lines

#Joonistab kõik vajutatavad nupud ekraanile
def draw_buttons(surface, rect, text, font, text_color=BLUE, button_color=YELLOW):
    shadow_offset = 6
    shadow_rect = pygame.Rect(rect.x + shadow_offset, rect.y + shadow_offset, rect.width, rect.height)
    pygame.draw.rect(surface, BUTTON_SHADOW, shadow_rect, border_radius=12)
    pygame.draw.rect(surface, button_color, rect, border_radius=12)

    label = font.render(text, True, text_color)
    label_rect = label.get_rect(center=rect.center)
    surface.blit(label, label_rect)
    
#Joonistab esimese ekraani, kust võimalik valida mäng variant (pultidega või pultideta) 
def draw_welcome_screen():
    global start_button_rect, debug_button_rect

    screen.fill(BLUE)
    TITLE_FONT = pygame.font.Font(CUSTOM_FONT_2, int(screen.get_width() * 0.08))
    BUTTON_FONT = get_dynamic_font(0.035)

    title = TITLE_FONT.render("KULDVILLAK", True, YELLOW)
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
    screen.blit(title, title_rect)
    button_width = screen.get_width() // 3
    button_height = 60

    start_button_rect = pygame.Rect(
        (screen.get_width() - button_width) // 2,
        (screen.get_height() * 2 // 3) - (button_height // 2),
        button_width,
        button_height
    )
    debug_button_rect = pygame.Rect(
        (screen.get_width() - button_width) // 2,
        start_button_rect.bottom + 20,
        button_width,
        button_height
    )
    draw_buttons(screen, start_button_rect, "Alusta", BUTTON_FONT)
    draw_buttons(screen, debug_button_rect, "Testi ilma pultideta", BUTTON_FONT)

#Joonistab Menüü, kus on võimalik teha erinevaid valikuid
def draw_menu_options():
    global menu_buttons
    screen.fill(BLUE)

    TITLE_FONT = get_dynamic_font(0.06)
    BUTTON_FONT = get_dynamic_font(0.032)

    title = TITLE_FONT.render("Menüü", True, YELLOW)
    screen.blit(title, title.get_rect(center=(screen.get_width() // 2, int(screen.get_height() * 0.1))))
    menu_buttons = []
    
    options = [
        "Alusta mängu",
        "Instruktsioonid",
        "Puldi test",
        "1. voor",
        "2. voor",
        "Finaal",
        "Tagasi"
    ]
    button_width = int(screen.get_width() * 0.45)
    button_height = int(screen.get_height() * 0.07)
    spacing = int(screen.get_height() * 0.025)
    start_y = int(screen.get_height() * 0.2)
    
    for i, text in enumerate(options):
        y = start_y + i * (button_height + spacing)
        rect = pygame.Rect(
            (screen.get_width() - button_width) // 2,
            y,
            button_width,
            button_height
        )
        draw_buttons(screen, rect, text, BUTTON_FONT)
        menu_buttons.append((rect, text))
    draw_battery_status()
    

#Joonistab ekraani, kus on võimalik valida mängijate/pultide arv
def draw_team_selection(current_team_selection):
    screen.fill(BLUE)

    TITLE_FONT = get_dynamic_font(0.06)  
    TEXT_FONT = get_dynamic_font(0.07)  

    title = TITLE_FONT.render("Vali mängijate arv", True, WHITE)
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 6))
    screen.blit(title, title_rect)
    
    base_y = screen.get_height() // 2.2  
    spacing = max(int(screen.get_height() * 0.10), 50)  

    for i in range(1, 7):
        color = YELLOW if i == current_team_selection else WHITE
        text = TEXT_FONT.render(f"{i}", True, color)
        text_rect = text.get_rect(center=(screen.get_width() // 2, base_y + (i - 2) * spacing))  
        screen.blit(text, text_rect)
        
#Joonistab ekraani, kus on võimalik sisestada mängijate nimed
def draw_team_name_entry(team_names, temp_team_name):
    screen.fill(BLUE)

    NAME_FONT = get_dynamic_font(0.05)  
    prompt = NAME_FONT.render(f"Sisesta mängija nimi {len(team_names) + 1}:", True, WHITE)
    prompt_rect = prompt.get_rect(center=(screen.get_width() // 2, screen.get_height() // 4))
    screen.blit(prompt, prompt_rect)
    
    name_text = NAME_FONT.render(temp_team_name, True, YELLOW)
    name_text_rect = name_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
    screen.blit(name_text, name_text_rect)

#Joonistab mängijate nimed mänguväljadele koos punktiskooride ning +/- nuppudega skoori modifitseerimiseks
#Muudab dünaamiliselt nimede ning +/- ikoonide paigutust vastavalt mängijate arvule
def draw_teams(teams):
    global plus_buttons, minus_buttons 
    
    plus_buttons = []
    minus_buttons = []

    screen_width = screen.get_width()
    screen_height = screen.get_height()
    team_count = len(teams)

    button_area_height = screen_height * 0.15
    y_offset = screen_height - button_area_height + 10
    if team_count <= 3:
          y_offset-= 30

    team_font = get_dynamic_font(0.020 if team_count > 4 else 0.025)
    button_size = max(30, min(screen_height // 12, screen_width // (team_count * 6)))      
    name_y = y_offset - team_font.get_height() - 10
    score_y = name_y + int(screen_height * 0.04)
    button_y = score_y + int(screen_height * 0.05)

    for i, (team, score) in enumerate(teams.items()):
        x_offset = screen_width // (team_count + 1) * (i + 1)
        #Joonistatakse mängijate nimed
        team_text = team_font.render(team, True, WHITE)
        screen.blit(team_text, (x_offset - team_text.get_width() // 2, name_y))
        #Joonistatakse punktiskoorid
        score_text = team_font.render(str(score), True, YELLOW)
        screen.blit(score_text, (x_offset - score_text.get_width() // 2, score_y))
        #Joonistatakse +/- nupud
        plus_rect = pygame.Rect(x_offset - button_size - 4, button_y, button_size, button_size)
        minus_rect = pygame.Rect(x_offset + 4, button_y, button_size, button_size)
        plus_buttons.append(plus_rect)
        minus_buttons.append(minus_rect)
        shadow_offset = 3
        for rect in [plus_rect, minus_rect]:
            shadow = pygame.Rect(rect.x + shadow_offset, rect.y + shadow_offset, rect.width, rect.height)
            pygame.draw.rect(screen, BUTTON_SHADOW, shadow, border_radius=6)
            pygame.draw.rect(screen, WHITE, rect, border_radius=6)
        icon_size = int(button_size * 0.6)
        plus_img_scaled = pygame.transform.smoothscale(PLUS_IMG, (icon_size, icon_size))
        minus_img_scaled = pygame.transform.smoothscale(MINUS_IMG, (icon_size, icon_size))
        screen.blit(plus_img_scaled, plus_img_scaled.get_rect(center=plus_rect.center))
        screen.blit(minus_img_scaled, minus_img_scaled.get_rect(center=minus_rect.center))
        
 #Joonistab vooru kategooriate kuvamise enne vastava mänguvälja avamist     
def draw_category_intro(current_round, index):
    screen.fill(BLUE)
    TITLE_FONT = get_dynamic_font(0.07)
    category_list = get_current_categories(current_round)

    if index < len(category_list):
        cat_text = TITLE_FONT.render(category_list[index], True, YELLOW)
        cat_rect = cat_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(cat_text, cat_rect)

    pygame.display.flip()
        
#Joonistab mänguvälja(vastavalt voorule) koos kategooriate, punktisummadega, tiimidega ja puldi patarei %-ga
def draw_grid(current_round, money_values, teams):
    global low_battery_controllers, back_button_rect  

    if current_round == 2:
        screen.fill((0, 50, 100))
    else:
        screen.fill(BLUE)
    update_grid_dimensions()

    CATEGORY_FONT = get_dynamic_font(min(0.05, CELL_WIDTH * 0.15 / screen.get_width()))
    MONEY_FONT = get_dynamic_font(0.06)
    DARK_BLUE = (10, 10, 100, 255)
    LIGHT_BLUE = (50, 50, 200, 50)
    
    #Joonistab kategooriad
    for col in range(COLUMNS):
        x = col * CELL_WIDTH
        pygame.draw.rect(screen, BLUE, (x, 0, CELL_WIDTH, CELL_HEIGHT))
        category_text = CATEGORY_FONT.render(get_current_categories(current_round)[col], True, WHITE)
        category_rect = category_text.get_rect(center=(x + CELL_WIDTH // 2, CELL_HEIGHT // 2))
        screen.blit(category_text, category_rect)
        #Joonistab punktisummad, tiimid
        for row in range(ROWS):
            y = (row + 1) * CELL_HEIGHT
            color = FADED_BLUE if revealed[col][row] else YELLOW

            rect = pygame.Rect(x, y, CELL_WIDTH, CELL_HEIGHT)
            draw_fade_rect(screen, rect, DARK_BLUE, LIGHT_BLUE)
            text = MONEY_FONT.render(f"{money_values[col][row]}€", True, color)
            text_rect = text.get_rect(center=(x + CELL_WIDTH // 2, y + CELL_HEIGHT // 2))
            screen.blit(text, text_rect)
            pygame.draw.rect(screen, WHITE, rect, 2)
    #Joonistab patarei ikoonid iga tiimi kohta
    if teams:
        draw_teams(teams)
    for i, team in enumerate(teams):
        controller_number = i + 1
        x = int(screen.get_width() / len(teams) * i + 10)
        y = screen.get_height() - 60
        #Tühjenev patarei
        if controller_number in low_battery_controllers:
            voltage_text = low_battery_controllers[controller_number][0]
        else:
            voltage_text = ""
        font = pygame.font.Font(None, 18)
        text_surface = font.render(voltage_text, True, WHITE)
        screen.blit(text_surface, (x + 28, y + 4))
  
    BUTTON_WIDTH = int(screen.get_width() * 0.1)  
    BUTTON_HEIGHT = int(screen.get_height() * 0.05)  
    BUTTON_X = 20  
    BUTTON_Y = screen.get_height() - BUTTON_HEIGHT - 20 

    if len(teams) >= 5:
       BUTTON_Y -= 40
    final_back_button_rect = None 

    BACK_FONT = get_dynamic_font(0.025)
    back_button_rect = pygame.Rect(BUTTON_X, BUTTON_Y, BUTTON_WIDTH, BUTTON_HEIGHT)
    draw_buttons(screen, back_button_rect, "Menüü", BACK_FONT)

    now = time.time()
    expired_keys = [k for k, (_, ts) in low_battery_controllers.items() if now - ts >= 10]
    for k in expired_keys:
        del low_battery_controllers[k]

    draw_battery_status()

#Kuvab timeri küsimuse ekraanil kui aeg saab otsa ning kuvab automaatselt vastuse ekraani
def handle_timer_expired():
    global showing_question, showing_answer
    print("⏳ Aeg on läbi!")
    showing_question = False
    showing_answer = True  
    pygame.time.delay(500) 
      
#Joonistab küsimuse akna koos timeriga ning kui küsimuses on pilt, siis kuvab ka pildi(piltküsimus)
#Kuvab esimesena puldinuppu vajutanud mängija
def draw_question(selected_col, selected_row, question_text, timer_started, timer_start, timer_paused, pause_time, selected_points, latest_button_press):
    global question_faded, showing_question

    if not question_faded:
        question_faded = True
    screen.fill(BLUE)

    TIMER_FONT = get_dynamic_font(0.06)
    QUESTION_FONT = get_dynamic_font(0.05)
    POINTS_FONT = get_dynamic_font(0.045)
    INSTRUCTIONS_FONT = get_dynamic_font(0.04)
    TEAM_FONT = get_dynamic_font(0.045)

    #Timeri loogika
    if timer_started and not timer_paused:
        remaining_time = max(0, TIMER_DURATION - (time.time() - timer_start))
    elif timer_started and timer_paused:
        remaining_time = max(0, TIMER_DURATION - (pause_time - timer_start))
    else:
        remaining_time = TIMER_DURATION
    timer_text = TIMER_FONT.render(f"{int(remaining_time)} sek", True, YELLOW)
    timer_rect = timer_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 10))
    screen.blit(timer_text, timer_rect)

    points_y = screen.get_height() // 3
    image_path = image_db.get((selected_col, selected_row))
    #Pildi olemasolu kontroll 
    if image_path:
       if os.path.exists(image_path):
            try:
               image_surface = pygame.image.load(image_path).convert_alpha()
               max_w = screen.get_width() * 0.45
               max_h = screen.get_height() * 0.4
               iw, ih = image_surface.get_size()
               scale = min(max_w / iw, max_h / ih)
               image_surface = pygame.transform.smoothscale(
               image_surface, (int(iw * scale), int(ih * scale))
                )
               image_rect = image_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() //3))
               screen.blit(image_surface, image_rect)
               question_start_y = image_rect.bottom + 25
            except Exception as e:
               print(f"❌ Pilti ei laetud '{image_path}': {e}")
               question_start_y = screen.get_height() // 3
       else:
           print(f"⚠️ Pildi asukohta ei eksisteeri: {image_path}")
           question_start_y = screen.get_height() // 3
    else:
       question_start_y = screen.get_height() // 3

    #Joonistab küsimuse teksti
    wrapped_lines = []
    if question_text:
        wrapped_lines = render_multiline_text(question_text, QUESTION_FONT, WHITE, screen.get_width() * 0.9)
        line_spacing = QUESTION_FONT.get_height() + 10
        for i, line_surface in enumerate(wrapped_lines):
            line_rect = line_surface.get_rect(center=(screen.get_width() // 2, question_start_y + i * line_spacing))
            screen.blit(line_surface, line_rect)
        points_y = question_start_y + len(wrapped_lines) * line_spacing + 10

    #Valitud vihje punktisummma kuvamine
    points_text = POINTS_FONT.render(f"Punktisumma: {selected_points}", True, YELLOW)
    points_rect = points_text.get_rect(center=(screen.get_width() // 2, points_y))
    screen.blit(points_text, points_rect)

    #Puldinupu vajutuse kuvamine
    if latest_button_press:
        pressed_text = TEAM_FONT.render(f"{latest_button_press} vajutas esimesena!", True, GREEN)
        pressed_rect = pressed_text.get_rect(center=(screen.get_width() // 2, points_y + 40))
        screen.blit(pressed_text, pressed_rect)

    #Instruktsioonid
    if not timer_started:
        instructions = "Vajuta ENTER, et alustada taimerit"
    else:
        instructions = "Vajuta SPACE, et näha vastust"
    instructions_text = INSTRUCTIONS_FONT.render(instructions, True, YELLOW)
    instructions_rect = instructions_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 80))
    screen.blit(instructions_text, instructions_rect)


#Joonistab vastuse ekraani
def draw_answer(selected_col, selected_row, answers_db):
    screen.fill(BLUE)

    ANSWER_FONT = get_dynamic_font(0.07)
    POINTS_FONT = get_dynamic_font(0.045)
    TEAM_FONT = get_dynamic_font(0.05)

    if selected_col is not None and selected_row is not None and (selected_col, selected_row) in answers_db:
       raw_answer = answers_db[(selected_col, selected_row)]
    else:
       raw_answer = "Vastust ei ole"

    wrapped_lines = render_multiline_text(raw_answer, ANSWER_FONT, WHITE, screen.get_width() * 0.9)

    start_y = screen.get_height() // 3
    line_spacing = ANSWER_FONT.get_height() + 10

    for i, line_surface in enumerate( wrapped_lines):
        rect = line_surface.get_rect(center=(screen.get_width() // 2, start_y + i * line_spacing))
        screen.blit(line_surface, rect)

    #Instruktsioonid
    back_text = POINTS_FONT.render("Vajuta + või -, et uuendada skoori", True, YELLOW) 
    back_text_rect = back_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 120))
    screen.blit(back_text, back_text_rect)

    if selected_team:
        team_text = TEAM_FONT.render(f"Mängija: {selected_team}", True, YELLOW) 
        team_text_rect = team_text.get_rect(center=(screen.get_width() // 2, screen.get_height() - 160))
        screen.blit(team_text, team_text_rect)

#Patarei pinge protsendiks arvutamine (Allikas: https://calculator.academy/battery-voltage-percentage-calculator/)
def voltage_to_percentage(voltage, max_v=9.0):
    percentage = (voltage ) / (max_v ) * 100
    #Vahemik 0% - 100%
    return max(0, min(100, int(percentage))) 

#Joonistab patarei tühjenemise teate, kui puldi patarei protsent on alla 50% 
def draw_battery_status():
    if not low_battery_controllers:
        return

    WARNING_FONT = get_dynamic_font(0.018)
    padding = 20
    spacing = 5
    y_start = screen.get_height() - padding - (WARNING_FONT.get_height() + 5) * len(low_battery_controllers)

    for i, (controller, (voltage, _)) in enumerate(low_battery_controllers.items()):
        voltage_value = float(voltage.replace("V", ""))
        battery_pct = voltage_to_percentage(voltage_value)

        if battery_pct >= 80:
            warning_color = (50, 255, 100)
            battery_icon = BATTERY_ICON_OK
        else:
            warning_color = (255, 80, 80)
            battery_icon = BATTERY_ICON
        #Kuvab patarei protsendi teksti
        warning_text = WARNING_FONT.render(f"Pult {controller}: {battery_pct}% aku", True, warning_color)
        icon_size = battery_icon.get_width()
        total_width = warning_text.get_width() + icon_size + spacing

        x = screen.get_width() - total_width - padding
        y = y_start + i * (WARNING_FONT.get_height() + 5)
        screen.blit(battery_icon, (x, y))
        screen.blit(warning_text, (x + icon_size + spacing, y))
        
#Küsib kasutajalt hõbevillaku punktide summa ning tagastab sisestatud punktid või vaikimisi punktid
def ask_for_hobevillak_points():
    input_active = True
    custom_points = ""

    while input_active:
        screen.fill(BLUE)

        TITLE_FONT = get_dynamic_font(0.05)  
        INPUT_FONT = get_dynamic_font(0.08) 
        title_text = TITLE_FONT.render("Hõbevillak! Mis punktidele mängid?:", True, WHITE)
        title_rect = title_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 4))
        screen.blit(title_text, title_rect)

        input_text = INPUT_FONT.render(custom_points if custom_points else "0", True, YELLOW)
        input_rect = input_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        screen.blit(input_text, input_rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  
                    input_active = False
                elif event.key == pygame.K_BACKSPACE: 
                    custom_points = custom_points[:-1]
                elif event.unicode.isdigit():
                    custom_points += event.unicode

    return int(custom_points) if custom_points else 0  

#Joonistab finaalvooru kategooria
def draw_final_intro(final_category):
    screen.fill(BLUE)

    TITLE_FONT = get_dynamic_font(0.06)
    CATEGORY_FONT = get_dynamic_font(0.05)
    INFO_FONT = get_dynamic_font(0.035)
    title = TITLE_FONT.render("Finaalvooru teema on:", True, YELLOW)
    category = CATEGORY_FONT.render(final_category, True, WHITE)  # <- this uses DB value
    info = INFO_FONT.render("Vajuta SPACE, et alustada panustamist", True, YELLOW)
    
    screen.blit(title, title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3)))
    screen.blit(category, category.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2)))
    screen.blit(info, info.get_rect(center=(screen.get_width() // 2, screen.get_height() - 100)))
    draw_battery_status()
    pygame.display.flip()
    
#Joonistab finaalküsimuse panuste ekraani
def draw_final_wager_screen(team_name, teams):
    screen.fill(BLUE)
    
    TITLE_FONT = get_dynamic_font(0.045)
    INPUT_FONT = get_dynamic_font(0.07)

    title = f"{team_name}, palju panustad? (max {teams[team_name]}):"
    title_text = TITLE_FONT.render(title, True, WHITE)
    title_rect = title_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 3))
    screen.blit(title_text, title_rect)

    input_text = INPUT_FONT.render(current_wager_input if current_wager_input else "0", True, YELLOW)
    input_rect = input_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(input_text, input_rect)
    pygame.display.flip()

#Tagastab hetkel valitud kategooria (1. või 2. voor)
def get_current_categories(current_round):
    return categories_round1 if current_round == 1 else categories_round2

#Joonistab instruktsioonide ekraani koos instruktsioonidega
def draw_instructions():
    screen.fill(BLUE)
    
    TITLE_FONT = get_dynamic_font(0.08)  
    INSTR_FONT = get_dynamic_font(0.03)
    title_text = TITLE_FONT.render("Instruktsioonid", True, YELLOW)
    title_rect = title_text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 6))
    screen.blit(title_text, title_rect)

    instructions = [
        " Kasuta NOOLI, et valida mängijate arv",
        " Siseta mängijate nimed ning vajuta ENTER",
        " VAJUTA küsimusele, et see valida",
        " VAJUTA ENTER, et alustada timerit",
        " VAJUTA PULDI NUPPU, et vastata küsimusele",
        " Vajuta ESC või Menüü nuppu, et restartida mäng",
        " Vajuta SPACE, et näha õiget vastust",
        " Vajuta BACKSPACE, et minna tagasi Menüüsse",
    ]
    
    start_y = screen.get_height() // 4
    line_spacing = int(INSTR_FONT.get_height() * 1.4)

    for i, text in enumerate(instructions):
        bullet_text = f"• {text.strip()}"
        instr_text = INSTR_FONT.render(bullet_text, True, WHITE)
        instr_rect = instr_text.get_rect(center=(screen.get_width() // 2, start_y + i * line_spacing))         
        screen.blit(instr_text, instr_rect)
    pygame.display.flip()    

#Joonistab puldi testimise ekraani
def draw_controller_test(screen):
    from time import time
    global controller_press_log
    screen.fill(BLUE)
    
    TITLE_FONT = get_dynamic_font(0.06)
    INFO_FONT = get_dynamic_font(0.04)
    title = TITLE_FONT.render("Puldi Test", True, YELLOW)
    screen.blit(title, title.get_rect(center=(screen.get_width() // 2, 100)))

    #Instruktsioonid
    instructions = INFO_FONT.render("Vajuta puldi nuppu testimiseks...", True, WHITE)
    screen.blit(instructions, instructions.get_rect(center=(screen.get_width() // 2, 200)))
    back_text = INFO_FONT.render("Tagasi menüüse - vajuta BACKSPACE", True, WHITE)
    screen.blit(back_text, back_text.get_rect(center=(screen.get_width() // 2, 260)))

    #Kuvab viimased kuue puldi vajutused/ kuus vajutust (5. sekundiks)
    now = time()
    recent = [msg for msg in controller_press_log if now - msg[1] < 5]
    controller_press_log = recent[-6:]

    for i, (msg, ts) in enumerate(reversed(controller_press_log)):
        text = INFO_FONT.render(msg, True, (0, 255, 127))
        screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, 300 + i * 40))       

#Joonistab finaalküsimuse vastuse
def draw_final_answer(final_answer):
    global final_back_button_rect
    screen.fill(BLUE)

    TITLE_FONT = get_dynamic_font(0.06)
    ANSWER_FONT = get_dynamic_font(0.045)
    BUTTON_FONT = get_dynamic_font(0.035)
    title = TITLE_FONT.render("Õige Vastus", True, YELLOW)
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 6))
    screen.blit(title, title_rect)

    lines = render_multiline_text(final_answer, ANSWER_FONT, WHITE, screen.get_width() * 0.9)
    start_y = screen.get_height() // 3
    line_spacing = lines[0].get_height() + 10

    for i, line in enumerate(lines):
        y = start_y + i * line_spacing
        rect = line.get_rect(center=(screen.get_width() // 2, y))
        screen.blit(line, rect)

    #Tagasi menüüsse nupu joonistamine
    button_width = screen.get_width() // 3
    button_height = 55
    button_x = (screen.get_width() - button_width) // 2
    button_y = screen.get_height() - button_height - 40
    final_back_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    draw_buttons(screen, final_back_button_rect, "Tagasi Menüüse", BUTTON_FONT)
    
    pygame.display.flip()

#Joonistab finaalküsimuse
def draw_final_question(final_question):
    screen.fill(BLUE)

    TITLE_FONT = get_dynamic_font(0.06)
    QUESTION_FONT = get_dynamic_font(0.045)
    INFO_FONT = get_dynamic_font(0.035)
    title = TITLE_FONT.render("Finaalküsimus!", True, YELLOW)
    title_rect = title.get_rect(center=(screen.get_width() // 2, screen.get_height() // 6))
    #Instruktsioonid
    info = INFO_FONT.render("Vajuta SPACE, et näha vastust", True, YELLOW)
    screen.blit(info, info.get_rect(center=(screen.get_width() // 2, screen.get_height() - 100)))
    screen.blit(title, title_rect)

    lines = render_multiline_text(final_question, QUESTION_FONT, WHITE, screen.get_width() * 0.9)
    start_y = screen.get_height() // 3
    line_spacing = QUESTION_FONT.get_height() + 10
    #Teksti õige paigutus vastavalt finaalküsimuse pikkusele
    for i, line in enumerate(lines):
        y = start_y + i * line_spacing
        rect = lines[i].get_rect(center=(screen.get_width() // 2, y))
        screen.blit(lines[i], rect)
    draw_battery_status()
    pygame.display.flip()
    
#Joonistab värvi gradiendiga ristküliku punktisummade ümber, et parandada mängu visuaalsust
def draw_fade_rect(surface, rect, color1, color2):
    
    fade_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    #Värvide tugevus/sügavus
    for i in range(rect.height):
        blend_ratio = i / rect.height 
        r = int(color1[0] * (1 - blend_ratio) + color2[0] * blend_ratio)
        g = int(color1[1] * (1 - blend_ratio) + color2[1] * blend_ratio)
        b = int(color1[2] * (1 - blend_ratio) + color2[2] * blend_ratio)
        a = int(255 * (1 - blend_ratio) + 50 * blend_ratio)
        pygame.draw.line(fade_surface, (r, g, b, a), (0, i), (rect.width, i))

    surface.blit(fade_surface, (rect.x, rect.y))

#Algseadistab kasutajaliidese ja tagab ekraani skaleerumise ning resolutsiooni kohandumise vastavalt
def init_ui(scr):
    global screen, TEAM_FONT, QUESTION_FONT
    screen = scr
    update_grid_dimensions()
    