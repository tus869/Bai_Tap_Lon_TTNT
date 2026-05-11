import pygame
import sys
import os
import math
import random
from map_system import GameMap, Camera, MiniMap, TILE_SIZE
from entities import generate_trees, generate_animals, HUD, CraftingMenu, Hotbar, InventoryUI, Boss, Chest, generate_chests, PathFinder

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

class DroppedItem:
    def __init__(self, x, y, item_type):
        self.type = item_type
        self.size = 24 if item_type == 'boss_item' else 14
        self.rect = pygame.Rect(x, y, self.size, self.size) 
        self.font = pygame.font.SysFont('Arial', 12, bold=True)
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.image = None
        self.label = ""
        
        if item_type == 'boss_item':
            try:
                v_img = pygame.image.load(os.path.join(BASE_DIR, 'vat_pham.png')).convert_alpha()
                self.image = pygame.transform.scale(v_img, (self.size, self.size))
            except FileNotFoundError:
                self.color = (255, 215, 0)
            self.label = "Boss Item"
        elif item_type == 'wood': 
            self.color = (139, 69, 19)
            self.label = "Go"
        elif item_type == 'meat': 
            self.color = (255, 99, 71)
            self.label = "Thit"
        elif item_type == 'leather': 
            self.color = (160, 82, 45)
            self.label = "Da"

    def draw(self, surface, camera):
        cam_rect = camera.apply(self.rect)
        if self.image:
            surface.blit(self.image, cam_rect)
        else:
            pygame.draw.circle(surface, self.color, cam_rect.center, self.size)
            pygame.draw.circle(surface, (255, 255, 255), cam_rect.center, self.size, 1) 
        
        if self.label:
            txt_surface = self.font.render(self.label, True, (255, 255, 255))
            surface.blit(txt_surface, (cam_rect.x - 5, cam_rect.y - 15))

class Player:
    def __init__(self, x, y):
        self.draw_size = int(TILE_SIZE * 1.5) 
        self.facing = 'down' 
        self.current_algo = "BFS" 
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        try:
            img_down = pygame.image.load(os.path.join(BASE_DIR, 'nhan_vat.png')).convert_alpha()
            self.image_down = pygame.transform.scale(img_down, (self.draw_size, self.draw_size))
            img_up = pygame.image.load(os.path.join(BASE_DIR, 'nhan_vat1.png')).convert_alpha()
            self.image_up = pygame.transform.scale(img_up, (self.draw_size, self.draw_size))
        except FileNotFoundError:
            self.image_down = pygame.Surface((self.draw_size, self.draw_size))
            self.image_down.fill((255, 0, 0))
            self.image_up = self.image_down

        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE) 
        self.speed = 5
        self.max_hp, self.hp = 100, 100
        self.max_food, self.food = 100, 100
        self.max_water, self.water = 100, 100
        self.max_stamina, self.stamina = 100, 100
        
        self.inventory = {'wood': 0, 'meat': 0, 'leather': 0, 'boss_item': 0}
        self.has_axe = False
        self.chop_damage = 1

    def move(self, dx, dy, map_width, map_height, trees):
        if dy > 0: self.facing = 'down'
        elif dy < 0: self.facing = 'up'

        self.rect.x += dx
        for tree in trees:
            if tree.hp > 0 and self.rect.colliderect(tree.rect):
                if dx > 0: self.rect.right = tree.rect.left
                if dx < 0: self.rect.left = tree.rect.right

        self.rect.y += dy
        for tree in trees:
            if tree.hp > 0 and self.rect.colliderect(tree.rect):
                if dy > 0: self.rect.bottom = tree.rect.top
                if dy < 0: self.rect.top = tree.rect.bottom

        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(map_width, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(map_height, self.rect.bottom)

    def draw(self, surface, camera):
        current_image = self.image_down if self.facing == 'down' else self.image_up
        draw_rect = camera.apply(self.rect)
        draw_rect.x -= (self.draw_size - self.rect.width) // 2
        draw_rect.y -= (self.draw_size - self.rect.height) // 2
        surface.blit(current_image, draw_rect)

class Button:
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = pygame.font.SysFont('Arial', 24, bold=True)
        self.color_normal = (40, 40, 40, 200)
        self.color_hover = (80, 80, 80, 240)

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.rect.collidepoint(mouse_pos)
        
        bg_color = self.color_hover if is_hover else self.color_normal
        border_color = (255, 215, 0) if is_hover else (150, 150, 150)

        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill(bg_color)
        surface.blit(s, (self.rect.x, self.rect.y))
        
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

# --- KHOI TAO HE THONG ---
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Aetheria: Evolution & Survival")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_DIR, 'map_bg.jpg')

is_music_playing = True
try:
    music_path = os.path.join(BASE_DIR, 'background.mp3')
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.set_volume(0.3) 
    pygame.mixer.music.play(-1) 
except:
    pass

game_state = "INTRO" 
game_started = False 
intro_alpha = 0 

# --- BIEN QUAN LY LEVEL ---
current_level = 1
max_level = 5

btn_w, btn_h = 250, 50
start_x = (SCREEN_WIDTH - btn_w) // 2
btn_new_game = Button(start_x, 300, btn_w, btn_h, "Choi moi")
btn_continue = Button(start_x, 370, btn_w, btn_h, "Choi tiep")
btn_instructions = Button(start_x, 440, btn_w, btn_h, "Huong dan choi")
btn_settings = Button(start_x, 510, btn_w, btn_h, "Cai dat")
btn_quit = Button(start_x, 580, btn_w, btn_h, "Thoat Game")
btn_back = Button(20, 20, 150, 40, "Quay lai")
btn_music = Button(SCREEN_WIDTH//2 - 125, 300, 250, 50, "Tat/Bat Nhac Nen")

btn_win_menu = Button(SCREEN_WIDTH//2 - 125, 450, 250, 50, "Ve Menu Chinh")
btn_next_level = Button(SCREEN_WIDTH//2 - 125, 450, 250, 50, "Tien vao Man Tiep Theo")

title_font = pygame.font.SysFont('Georgia', 64, bold=True)
title_surf = title_font.render("AETHERIA", True, (212, 175, 55))
title_rect = title_surf.get_rect(center=(SCREEN_WIDTH//2, 150))

# Ham Reset game co tham so Level
def start_new_game(level=1):
    global game_map, camera, minimap, player, hud, trees, animals, crafting_menu, hotbar, inventory_menu, boss, dropped_items
    global chests, auto_play, current_algo_name, notification_timer, player_path, frame_counter, show_crafting_menu, show_inventory
    global current_level
    
    current_level = level
    
    game_map = GameMap()
    camera = Camera(game_map.width, game_map.height, SCREEN_WIDTH, SCREEN_HEIGHT)
    minimap = MiniMap(IMAGE_PATH, game_map.width, game_map.height)
    
    if level == 1 or 'player' not in globals():
        player = Player(game_map.width // 2, game_map.height // 2)
    else:
        player.hp = min(player.max_hp, player.hp + 50)
        player.food = player.max_food
        player.water = player.max_water
        player.rect.x = game_map.width // 2
        player.rect.y = game_map.height // 2

    hud = HUD()
    trees = generate_trees(game_map, TILE_SIZE, num_trees=400) 
    
    num_enemies = 40 + (level * 10)
    animals = generate_animals(game_map, TILE_SIZE, num_animals=num_enemies) 
    chests = generate_chests(game_map, TILE_SIZE, num_chests=20)
    
    crafting_menu = CraftingMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    hotbar = Hotbar(SCREEN_WIDTH, SCREEN_HEIGHT)
    inventory_menu = InventoryUI(SCREEN_WIDTH, SCREEN_HEIGHT)

    # TRUYEN LEVEL VAO BOSS DE LOAD ANH
    boss = Boss(game_map.width // 2 + 300, game_map.height // 2 + 300, TILE_SIZE * 2, current_level)
    
    boss.max_hp = 50 + ((level - 1) * 30)
    boss.hp = boss.max_hp
    boss.damage = 20 + ((level - 1) * 10)

    dropped_items = []
    show_crafting_menu = False
    show_inventory = False 
    frame_counter = 0 
    
    auto_play = False
    current_algo_name = "THU CONG"
    notification_timer = 0
    player_path = []

try:
    bg_img = pygame.image.load(IMAGE_PATH).convert()
    menu_bg = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    menu_bg.set_alpha(100) 
except:
    menu_bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    menu_bg.fill((20, 20, 20))

# --- VONG LAP CHINH ---
running = True
while running:
    clock.tick(FPS)
    
    if game_state == "INTRO":
        screen.fill((0, 0, 0)) 
        
        intro_alpha += 2 
        if intro_alpha > 255: intro_alpha = 255
            
        font_small = pygame.font.SysFont('Arial', 24, bold=True)
        font_mid = pygame.font.SysFont('Arial', 32, bold=True)
        font_large = pygame.font.SysFont('Georgia', 64, bold=True)
        font_italic = pygame.font.SysFont('Arial', 20, italic=True)
        
        t1 = font_mid.render("DO AN MON TRI TUE NHAN TAO", True, (200, 200, 200))
        t2 = font_small.render("Truong Dai hoc Dai Nam", True, (150, 150, 150))
        t3 = font_italic.render("Ung dung thuat toan AI Tim Duong: BFS, DFS, Greedy Heuristic, A*", True, (150, 255, 150))
        t4 = font_large.render("AETHERIA: EVOLUTION & SURVIVAL", True, (212, 175, 55))
        
        t1.set_alpha(intro_alpha)
        t2.set_alpha(intro_alpha)
        t3.set_alpha(intro_alpha)
        t4.set_alpha(intro_alpha)
        
        screen.blit(t1, t1.get_rect(center=(SCREEN_WIDTH//2, 200)))
        screen.blit(t2, t2.get_rect(center=(SCREEN_WIDTH//2, 250)))
        screen.blit(t3, t3.get_rect(center=(SCREEN_WIDTH//2, 320)))
        screen.blit(t4, t4.get_rect(center=(SCREEN_WIDTH//2, 450)))
        
        if pygame.time.get_ticks() % 1000 < 500:
            t_prompt = font_small.render("Nhan phim SPACE de tiep tuc...", True, (255, 255, 255))
            t_prompt.set_alpha(intro_alpha)
            screen.blit(t_prompt, t_prompt.get_rect(center=(SCREEN_WIDTH//2, 650)))
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_state = "MENU"

        pygame.display.flip()
        continue 

    elif game_state != "PLAYING":
        screen.fill((10, 10, 10))
        screen.blit(menu_bg, (0, 0)) 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if game_state == "MENU":
                if btn_new_game.is_clicked(event):
                    start_new_game(level=1)
                    game_started = True
                    game_state = "PLAYING"
                if game_started and btn_continue.is_clicked(event):
                    game_state = "PLAYING"
                if btn_instructions.is_clicked(event):
                    game_state = "INSTRUCTIONS"
                if btn_settings.is_clicked(event):
                    game_state = "SETTINGS"
                if btn_quit.is_clicked(event):
                    running = False
                    
            elif game_state in ["INSTRUCTIONS", "SETTINGS"]:
                if btn_back.is_clicked(event):
                    game_state = "MENU"
                if game_state == "SETTINGS" and btn_music.is_clicked(event):
                    is_music_playing = not is_music_playing
                    if is_music_playing: pygame.mixer.music.unpause()
                    else: pygame.mixer.music.pause()
            
            elif game_state == "LEVEL_TRANSITION":
                if btn_next_level.is_clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                    start_new_game(level=current_level + 1)
                    game_state = "PLAYING"

            elif game_state == "VICTORY":
                if btn_win_menu.is_clicked(event):
                    game_state = "MENU"
                    game_started = False 

        if game_state == "MENU":
            screen.blit(title_surf, title_rect)
            btn_new_game.draw(screen)
            btn_continue.color_normal = (40, 40, 40, 200) if game_started else (30,30,30,100)
            btn_continue.draw(screen)
            btn_instructions.draw(screen)
            btn_settings.draw(screen)
            btn_quit.draw(screen)
            
        elif game_state == "INSTRUCTIONS":
            btn_back.draw(screen)
            inst_font = pygame.font.SysFont('Arial', 24)
            instructions = [
                "HUONG DAN SINH TON",
                "--------------------------------",
                "- Phim W, A, S, D: Di chuyen nhan vat.",
                "- Chuot trai: Chat cay, danh thu, an thit.",
                "- Phim E: Xem hanh trang. Phim C: Che tao.",
                "- Phim F: BAT/TAT AI TU DONG CHOI (San Boss/Ruong).",
                "- F1, F2, F3, F4: Doi thuat toan tim duong cho Nhan vat."
            ]
            for i, text in enumerate(instructions):
                screen.blit(inst_font.render(text, True, (255, 255, 255)), (150, 150 + i * 40))
                
        elif game_state == "SETTINGS":
            btn_back.draw(screen)
            btn_music.text = "Nhac Nen: DANG BAT" if is_music_playing else "Nhac Nen: DA TAT"
            btn_music.draw(screen)
            
        elif game_state == "LEVEL_TRANSITION":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((0, 50, 100)) 
            overlay.set_alpha(180)
            screen.blit(overlay, (0, 0))
            
            font_title = pygame.font.SysFont('Georgia', 64, bold=True)
            font_sub = pygame.font.SysFont('Arial', 32, bold=True)
            
            txt_title = font_title.render(f"HOAN THANH MAN {current_level}!", True, (255, 215, 0))
            txt_sub = font_sub.render("Boss man tiep theo se manh hon va dong bon hon...", True, (255, 255, 255))
            
            screen.blit(txt_title, txt_title.get_rect(center=(SCREEN_WIDTH//2, 250)))
            screen.blit(txt_sub, txt_sub.get_rect(center=(SCREEN_WIDTH//2, 350)))
            
            btn_next_level.draw(screen)

        elif game_state == "VICTORY":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((100, 0, 0)) 
            overlay.set_alpha(150)
            screen.blit(overlay, (0, 0))
            
            vic_font_title = pygame.font.SysFont('Georgia', 64, bold=True)
            vic_font_sub = pygame.font.SysFont('Arial', 40, bold=True)
            
            txt_vic = vic_font_title.render("CHIEN THANG TOAN TAP!", True, (255, 215, 0))
            txt_mu = vic_font_sub.render("Manchester United lay duoc cup thoat khoi hang!", True, (255, 255, 255))
            
            screen.blit(txt_vic, txt_vic.get_rect(center=(SCREEN_WIDTH//2, 250)))
            screen.blit(txt_mu, txt_mu.get_rect(center=(SCREEN_WIDTH//2, 350)))
            
            btn_win_menu.draw(screen)

    elif game_state == "PLAYING":
        frame_counter += 1
        
        if frame_counter % 60 == 0: 
            if player.food > 0: player.food -= 0.5
            if player.water > 0: player.water -= 0.5
            if player.food <= 0 or player.water <= 0:
                player.hp -= 1
                if player.hp <= 0:
                    game_state = "MENU"
                    game_started = False 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game_state = "MENU"
                if event.key == pygame.K_c:
                    show_crafting_menu = not show_crafting_menu
                    show_inventory = False
                if event.key == pygame.K_e:
                    show_inventory = not show_inventory
                    show_crafting_menu = False
                    
                if event.key == pygame.K_f:
                    auto_play = not auto_play
                    current_algo_name = f"TU DONG ({player.current_algo})" if auto_play else "THU CONG"
                    notification_timer = 120
                    player_path = []

                if event.key == pygame.K_F1: 
                    player.current_algo = "BFS"
                    current_algo_name = "AI NHAN VAT: BFS"
                    notification_timer = 120
                if event.key == pygame.K_F2: 
                    player.current_algo = "DFS"
                    current_algo_name = "AI NHAN VAT: DFS"
                    notification_timer = 120
                if event.key == pygame.K_F3: 
                    player.current_algo = "Greedy"
                    current_algo_name = "AI NHAN VAT: Greedy"
                    notification_timer = 120
                if event.key == pygame.K_F4: 
                    player.current_algo = "A*"
                    current_algo_name = "AI NHAN VAT: A*"
                    notification_timer = 120

                if event.key == pygame.K_1: 
                    hotbar.selected = 1
                    player.chop_damage = 1 
                if event.key == pygame.K_2 and player.has_axe: 
                    hotbar.selected = 2
                    player.chop_damage = 3 
                if event.key == pygame.K_3: 
                    hotbar.selected = 3 
                if event.key == pygame.K_4: 
                    hotbar.selected = 4 
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if show_crafting_menu:
                        crafting_menu.handle_click(mouse_pos, player)
                    elif not show_inventory:
                        world_x = mouse_pos[0] - camera.camera.x
                        world_y = mouse_pos[1] - camera.camera.y

                        if hotbar.selected == 3:
                            if player.inventory.get('meat', 0) > 0 and player.food < player.max_food:
                                player.inventory['meat'] -= 1
                                player.food = min(player.max_food, player.food + 20)
                        else:
                            for tree in trees:
                                if tree.hp > 0 and tree.rect.collidepoint((world_x, world_y)):
                                    dist = math.hypot(player.rect.centerx - tree.rect.centerx, player.rect.centery - tree.rect.centery)
                                    if dist < 60: 
                                        tree.hp -= player.chop_damage
                                        ox, oy = random.randint(-20, 20), random.randint(-20, 20)
                                        dropped_items.append(DroppedItem(tree.rect.centerx + ox, tree.rect.centery + oy, 'wood'))

                            for animal in animals:
                                if animal.hp > 0 and animal.rect.collidepoint((world_x, world_y)):
                                    dist = math.hypot(player.rect.centerx - animal.rect.centerx, player.rect.centery - animal.rect.centery)
                                    if dist < 60: 
                                        animal.hp -= player.chop_damage 
                                        if animal.hp <= 0:
                                            meat_drop = getattr(animal, 'meat_drop', 1)
                                            for _ in range(meat_drop):
                                                ox, oy = random.randint(-15, 15), random.randint(-15, 15)
                                                dropped_items.append(DroppedItem(animal.rect.centerx + ox, animal.rect.centery + oy, 'meat'))
                                            if hasattr(animal, 'leather_drop'):
                                                for _ in range(animal.leather_drop):
                                                    ox, oy = random.randint(-15, 15), random.randint(-15, 15)
                                                    dropped_items.append(DroppedItem(animal.rect.centerx + ox, animal.rect.centery + oy, 'leather'))

                            for chest in chests[:]:
                                if chest.rect.collidepoint((world_x, world_y)):
                                    dist = math.hypot(player.rect.centerx - chest.rect.centerx, player.rect.centery - chest.rect.centery)
                                    if dist < 60:
                                        chest.hp -= 1
                                        if chest.hp <= 0:
                                            chests.remove(chest)
                                            dropped_items.append(DroppedItem(chest.rect.x, chest.rect.y, 'meat'))
                                            dropped_items.append(DroppedItem(chest.rect.x+10, chest.rect.y, 'leather'))

                            if 'boss' in globals() and boss.hp > 0 and boss.rect.collidepoint((world_x, world_y)):
                                dist = math.hypot(player.rect.centerx - boss.rect.centerx, player.rect.centery - boss.rect.centery)
                                if dist < 80: 
                                    boss.hp -= player.chop_damage 
                                    if boss.hp <= 0:
                                        dropped_items.append(DroppedItem(boss.rect.centerx, boss.rect.centery, 'boss_item'))
                                        if current_level < max_level:
                                            game_state = "LEVEL_TRANSITION"
                                        else:
                                            game_state = "VICTORY"
                                                
                            grid_col, grid_row = int(world_x // TILE_SIZE), int(world_y // TILE_SIZE)
                            if 0 <= grid_col < (game_map.width // TILE_SIZE) and 0 <= grid_row < (game_map.height // TILE_SIZE):
                                if game_map.grid[grid_row][grid_col] == "water": 
                                    if math.hypot(player.rect.centerx - world_x, player.rect.centery - world_y) < 80: 
                                        player.water = player.max_water 

        if not show_crafting_menu and not show_inventory and game_state == "PLAYING":
            dx, dy = 0, 0
            
            if auto_play:
                target = None
                attack_range = 40
                
                if 'boss' in globals() and boss.hp > 0:
                    target = boss
                    attack_range = 75 
                else:
                    targets = [item for item in dropped_items if item.type == 'meat'] + chests
                    if targets:
                        target = min(targets, key=lambda t: math.hypot(player.rect.x - t.rect.x, player.rect.y - t.rect.y))
                        attack_range = 40

                if target:
                    start_node = (player.rect.centery // TILE_SIZE, player.rect.centerx // TILE_SIZE)
                    goal_node = (target.rect.centery // TILE_SIZE, target.rect.centerx // TILE_SIZE)
                    
                    if 0 <= start_node[0] < len(game_map.grid) and 0 <= goal_node[0] < len(game_map.grid[0]):
                        if frame_counter % 15 == 0 or not player_path:
                            if player.current_algo == "BFS": player_path = PathFinder.bfs(start_node, goal_node, game_map.grid)
                            elif player.current_algo == "DFS": player_path = PathFinder.dfs(start_node, goal_node, game_map.grid)
                            elif player.current_algo == "Greedy": player_path = PathFinder.greedy(start_node, goal_node, game_map.grid)
                            elif player.current_algo == "A*": player_path = PathFinder.astar(start_node, goal_node, game_map.grid)
                        
                        dist_to_target = math.hypot(target.rect.centerx - player.rect.centerx, target.rect.centery - player.rect.centery)
                        
                        if dist_to_target > attack_range and player_path:
                            target_node = player_path[0]
                            target_x = target_node[1] * TILE_SIZE + TILE_SIZE // 2
                            target_y = target_node[0] * TILE_SIZE + TILE_SIZE // 2
                            
                            dist_x = target_x - player.rect.centerx
                            dist_y = target_y - player.rect.centery
                            step_dist = math.hypot(dist_x, dist_y)
                            
                            if step_dist > player.speed:
                                dx = (dist_x / step_dist) * player.speed
                                dy = (dist_y / step_dist) * player.speed
                            else:
                                player_path.pop(0)
                        elif dist_to_target <= attack_range:
                            if target == boss:
                                if frame_counter % 20 == 0: 
                                    boss.hp -= player.chop_damage
                                    if boss.hp <= 0:
                                        dropped_items.append(DroppedItem(boss.rect.centerx, boss.rect.centery, 'boss_item'))
                                        if current_level < max_level:
                                            game_state = "LEVEL_TRANSITION"
                                        else:
                                            game_state = "VICTORY"
                            elif hasattr(target, 'hp') and target in chests:
                                if frame_counter % 15 == 0:
                                    target.hp -= 1
                                    if target.hp <= 0:
                                        chests.remove(target)
                                        dropped_items.append(DroppedItem(target.rect.x, target.rect.y, 'meat'))
                                        dropped_items.append(DroppedItem(target.rect.x+10, target.rect.y, 'leather'))
            
            else:
                keys = pygame.key.get_pressed()
                current_speed = player.speed
                if keys[pygame.K_LSHIFT] and player.stamina > 0:
                    current_speed += 3
                    player.stamina -= 1
                elif player.stamina < player.max_stamina:
                    player.stamina += 0.5 
                    
                if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -current_speed
                if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = current_speed
                if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -current_speed
                if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = current_speed
            
            player.move(dx, dy, game_map.width, game_map.height, trees)
            
            for animal in animals:
                if animal.hp > 0: animal.update(player, game_map.width, game_map.height)
            if 'boss' in globals() and boss.hp > 0:
                boss.update(player, game_map.grid, game_map.width, game_map.height)

            for item in dropped_items[:]:
                if player.rect.colliderect(item.rect):
                    player.inventory[item.type] += 1
                    dropped_items.remove(item)
            
        camera.update(player.rect)

        screen.fill((0, 0, 0))
        game_map.draw(screen, camera)
        
        for chest in chests: chest.draw(screen, camera)
        for item in dropped_items: item.draw(screen, camera)
        for tree in trees: tree.draw(screen, camera)
        for animal in animals:
            if animal.hp > 0: animal.draw(screen, camera)
        if boss.hp > 0: boss.draw(screen, camera)
            
        player.draw(screen, camera)
        minimap.draw(screen, player.rect, SCREEN_WIDTH)
        
        hud.draw(screen, player)
        hotbar.draw(screen, player) 
        
        font_level = pygame.font.SysFont('Arial', 24, bold=True)
        lvl_surf = font_level.render(f"Man: {current_level}/{max_level}", True, (255, 215, 0))
        screen.blit(lvl_surf, (SCREEN_WIDTH - 150, 20))
        #eeeeee
        if show_crafting_menu:
            crafting_menu.draw(screen, player)
        elif show_inventory:
            inventory_menu.draw(screen, player)#eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee

        if notification_timer > 0:
            notify_font = pygame.font.SysFont('Arial', 48, bold=True)
            text_surf = notify_font.render(current_algo_name, True, (255, 255, 0)) 
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3)) 
            
            s = pygame.Surface((text_rect.width + 40, text_rect.height + 20), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            screen.blit(s, (text_rect.x - 20, text_rect.y - 10))
            screen.blit(text_surf, text_rect)
            
            notification_timer -= 1

    pygame.display.flip()

pygame.quit()
sys.exit()