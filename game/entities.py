import pygame
import random
import math
import os
import heapq
from collections import deque

class Tree:
    def __init__(self, x, y, size):
        self.draw_size = int(size * 2) 
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        try:
            t_img = pygame.image.load(os.path.join(BASE_DIR, 'tree1.png')).convert_alpha()
            self.image = pygame.transform.scale(t_img, (self.draw_size, self.draw_size))
        except FileNotFoundError:
            self.image = pygame.Surface((self.draw_size, self.draw_size))
            self.image.fill((0, 100, 0)) 
        self.rect = pygame.Rect(x + size // 2, y + int(self.draw_size * 0.7), size, size) 
        self.hp = 3

    def draw(self, surface, camera):
        if self.hp > 0:
            draw_pos = camera.apply(self.rect)
            draw_pos.x -= (self.draw_size - self.rect.width) // 2
            draw_pos.y -= (self.draw_size - self.rect.height)
            surface.blit(self.image, draw_pos)

def generate_trees(game_map, tile_size, num_trees=300):
    trees = []
    cols = game_map.width // tile_size
    rows = game_map.height // tile_size
    for _ in range(num_trees):
        while True: 
            r_col = random.randint(0, cols - 1)
            r_row = random.randint(0, rows - 1)
            if game_map.grid[r_row][r_col] == "grass":
                x = r_col * tile_size
                y = r_row * tile_size
                trees.append(Tree(x, y, tile_size))
                break
    return trees

class HUD:
    def __init__(self):
        self.x = 20
        self.y = 20
        self.bar_w = 150
        self.bar_h = 15
        self.spacing = 25 
        pygame.font.init() 

    def draw_bar(self, surface, x, y, current_val, max_val, color):
        ratio = current_val / max_val
        current_w = int(self.bar_w * ratio)
        pygame.draw.rect(surface, (100, 100, 100), (x, y, self.bar_w, self.bar_h))
        pygame.draw.rect(surface, color, (x, y, current_w, self.bar_h))
        pygame.draw.rect(surface, (255, 255, 255), (x, y, self.bar_w, self.bar_h), 1)

    def draw(self, surface, player):
        self.draw_bar(surface, self.x, self.y, player.hp, player.max_hp, (255, 0, 0))            
        self.draw_bar(surface, self.x, self.y + self.spacing, player.food, player.max_food, (210, 105, 30))   
        self.draw_bar(surface, self.x, self.y + self.spacing*2, player.water, player.max_water, (30, 144, 255)) 
        self.draw_bar(surface, self.x, self.y + self.spacing*3, player.stamina, player.max_stamina, (255, 215, 0)) 

class Hotbar:
    def __init__(self, screen_w, screen_h):
        self.slots = 4
        self.slot_size = 60
        self.spacing = 10
        self.total_w = (self.slot_size * self.slots) + (self.spacing * (self.slots - 1))
        self.x = (screen_w - self.total_w) // 2
        self.y = screen_h - self.slot_size - 20
        self.selected = 1
        self.font_num = pygame.font.SysFont('Arial', 16, bold=True)
        self.font_item = pygame.font.SysFont('Arial', 14, bold=True)

    def draw(self, surface, player):
        for i in range(self.slots):
            slot_x = self.x + i * (self.slot_size + self.spacing)
            rect = pygame.Rect(slot_x, self.y, self.slot_size, self.slot_size)

            bg_color = (100, 100, 100, 200) if (i+1) == self.selected else (40, 40, 40, 200)
            s = pygame.Surface((self.slot_size, self.slot_size), pygame.SRCALPHA)
            s.fill(bg_color)
            surface.blit(s, (slot_x, self.y))
            pygame.draw.rect(surface, (212, 175, 55) if (i+1) == self.selected else (200,200,200), rect, 2, border_radius=5)

            num_txt = self.font_num.render(str(i+1), True, (255, 255, 255))
            surface.blit(num_txt, (slot_x + 5, self.y + 5))

            text1, text2 = "", ""
            color = (255, 255, 255)
            
            if i == 0:
                text1 = "Tay"
                text2 = "(DMG:1)"
            elif i == 1:
                if player.has_axe:
                    text1 = "Riu"
                    text2 = "(DMG:3)"
                    color = (100, 255, 100)
            elif i == 2:
                text1 = "Thit"
                text2 = f"x{player.inventory.get('meat', 0)}"
                color = (255, 100, 100)
            elif i == 3:
                text1 = "Vat pham"
                text2 = "Boss"
                if player.inventory.get('boss_item', 0) > 0: color = (255, 215, 0)

            if text1:
                t1 = self.font_item.render(text1, True, color)
                surface.blit(t1, (slot_x + 5, self.y + 25))
            if text2:
                t2 = self.font_item.render(text2, True, color)
                surface.blit(t2, (slot_x + 5, self.y + 40))

class InventoryUI:
    def __init__(self, screen_width, screen_height):
        self.width, self.height = 400, 300
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.title_font = pygame.font.SysFont('Georgia', 28, bold=True)
        self.item_font = pygame.font.SysFont('Arial', 24, bold=True)

    def draw(self, surface, player):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((30, 30, 30, 240))
        surface.blit(overlay, (self.x, self.y))
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 3, border_radius=10)

        title = self.title_font.render("HANH TRANG (Nhan E dong)", True, (255, 255, 255))
        surface.blit(title, (self.x + 20, self.y + 20))
        pygame.draw.line(surface, (150, 150, 150), (self.x + 20, self.y + 60), (self.x + self.width - 20, self.y + 60), 2)

        items = [
            ("Go (Wood):", player.inventory.get('wood', 0), (210, 180, 140)),
            ("Thit (Meat):", player.inventory.get('meat', 0), (255, 99, 71)),
            ("Da thu (Leather):", player.inventory.get('leather', 0), (160, 82, 45)),
            ("Vat pham Boss:", player.inventory.get('boss_item', 0), (255, 215, 0))
        ]

        for i, (name, count, color) in enumerate(items):
            txt = self.item_font.render(f"{name} {count}", True, color)
            surface.blit(txt, (self.x + 40, self.y + 80 + i * 45))

class CraftingMenu:
    def __init__(self, screen_width, screen_height):
        self.width, self.height = 500, 350
        self.x = (screen_width - self.width) // 2
        self.y = (screen_height - self.height) // 2
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.title_font = pygame.font.SysFont('Georgia', 32, bold=True)
        self.item_font = pygame.font.SysFont('Arial', 22)
        self.btn_font = pygame.font.SysFont('Arial', 20, bold=True)

    def draw(self, surface, player):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((20, 20, 20, 230)) 
        surface.blit(overlay, (self.x, self.y))
        pygame.draw.rect(surface, (212, 175, 55), self.rect, 3, border_radius=10)
        
        title_surf = self.title_font.render("XUONG CHE TAC", True, (212, 175, 55))
        title_rect = title_surf.get_rect(centerx=self.x + self.width//2, top=self.y + 25)
        surface.blit(title_surf, title_rect)
        pygame.draw.line(surface, (100, 100, 100), (self.x + 50, self.y + 80), (self.x + self.width - 50, self.y + 80), 1)

        self.draw_item_row(surface, self.x + 50, self.y + 110, "Riu Khai Thac", "3 Go", player.inventory['wood'] >= 3, player.has_axe)

    def draw_item_row(self, surface, x, y, name, cost, can_craft, owned):
        name_txt = self.item_font.render(name, True, (255, 255, 255))
        surface.blit(name_txt, (x, y))
        cost_txt = self.item_font.render(f"Gia: {cost}", True, (200, 200, 200))
        surface.blit(cost_txt, (x, y + 30))
        btn_rect = pygame.Rect(x + 250, y + 5, 150, 45)
        if owned:
            color = (60, 60, 60)
            label = "DA SO HUU"
        elif can_craft:
            color = (40, 120, 40)
            label = "CHE TAO"
        else:
            color = (120, 40, 40)
            label = "THIEU GO"

        pygame.draw.rect(surface, color, btn_rect, border_radius=5)
        pygame.draw.rect(surface, (212, 175, 55), btn_rect, 1, border_radius=5)
        lbl_surf = self.btn_font.render(label, True, (255, 255, 255))
        lbl_rect = lbl_surf.get_rect(center=btn_rect.center)
        surface.blit(lbl_surf, lbl_rect)
        self.btn_axe_rect = btn_rect

    def handle_click(self, mouse_pos, player):
        if hasattr(self, 'btn_axe_rect') and self.btn_axe_rect.collidepoint(mouse_pos):
            if not player.has_axe and player.inventory['wood'] >= 3:
                player.inventory['wood'] -= 3
                player.has_axe = True
                player.chop_damage = 3

class Animal:
    def __init__(self, x, y, animal_type, size):
        self.draw_size = size
        self.type = animal_type
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        sprite_name = 'deer_passive.png' if self.type == "passive" else 'boar_aggressive.png'
        try:
            a_img = pygame.image.load(os.path.join(BASE_DIR, sprite_name)).convert_alpha()
            self.image = pygame.transform.scale(a_img, (self.draw_size, self.draw_size))
        except FileNotFoundError:
            self.image = pygame.Surface((self.draw_size, self.draw_size))
            self.image.fill((210, 180, 140) if self.type == "passive" else (139, 69, 19))

        self.rect = pygame.Rect(x, y, self.draw_size, self.draw_size) 
        if self.type == "passive": 
            self.max_hp = 3
            self.speed = 4
            self.damage = 0
            self.meat_drop = 1
            self.leather_drop = 0
        else:                      
            self.max_hp = 5
            self.speed = 3
            self.damage = 10
            self.meat_drop = 2
            self.leather_drop = 1

        self.hp = self.max_hp
        self.state = "wander"
        self.vx, self.vy = 0, 0
        self.timer = 0
        self.attack_cooldown = 0

    def update(self, player, map_width, map_height):
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        dist_x = player.rect.centerx - self.rect.centerx
        dist_y = player.rect.centery - self.rect.centery
        dist = math.hypot(dist_x, dist_y)
        
        if self.type == "passive" and self.hp < self.max_hp: self.state = "flee"
        elif self.type == "aggressive" and dist < 200: self.state = "chase"
        elif self.state != "flee": self.state = "wander"
        
        if self.state == "wander":
            self.timer -= 1
            if self.timer <= 0:
                self.vx = random.choice([-1, 0, 1]) * (self.speed - 1)
                self.vy = random.choice([-1, 0, 1]) * (self.speed - 1)
                self.timer = random.randint(30, 90)
        elif self.state == "flee":
            if dist > 0:
                self.vx = -(dist_x / dist) * self.speed
                self.vy = -(dist_y / dist) * self.speed
        elif self.state == "chase":
            if dist > 0:
                self.vx = (dist_x / dist) * self.speed
                self.vy = (dist_y / dist) * self.speed
                
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.rect.x = max(0, min(self.rect.x, map_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, map_height - self.rect.height))
        
        if self.state == "chase" and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            player.hp -= self.damage
            self.attack_cooldown = 60

    def draw(self, surface, camera):
        if self.hp > 0:
            surface.blit(self.image, camera.apply(self.rect))
            if self.hp < self.max_hp:
                bar_w = 20
                ratio = self.hp / self.max_hp
                cam_rect = camera.apply(self.rect)
                pygame.draw.rect(surface, (255, 0, 0), (cam_rect.x, cam_rect.y - 8, bar_w * ratio, 4))

class Pig:
    def __init__(self, x, y, size):
        self.draw_size = int(size * 0.8) 
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        try:
            p_img = pygame.image.load(os.path.join(BASE_DIR, 'pig.png')).convert_alpha()
            self.image = pygame.transform.scale(p_img, (self.draw_size, self.draw_size))
        except FileNotFoundError:
            self.image = pygame.Surface((self.draw_size, self.draw_size))
            self.image.fill((255, 182, 193)) 

        self.rect = pygame.Rect(x, y, self.draw_size, self.draw_size) 
        self.hp, self.max_hp = 3, 3
        self.speed = 3
        self.state = "wander"
        self.vx, self.vy, self.timer = 0, 0, 0
        self.meat_drop = 2
        self.leather_drop = 1 

    def update(self, player, map_width, map_height):
        dist_x = player.rect.centerx - self.rect.centerx
        dist_y = player.rect.centery - self.rect.centery
        dist = math.hypot(dist_x, dist_y)

        if self.hp < self.max_hp: self.state = "flee"
        else: self.state = "wander"

        if self.state == "wander":
            self.timer -= 1
            if self.timer <= 0:
                self.vx = random.choice([-1, 0, 1]) * (self.speed - 1)
                self.vy = random.choice([-1, 0, 1]) * (self.speed - 1)
                self.timer = random.randint(30, 90)
        elif self.state == "flee" and dist > 0:
            self.vx = -(dist_x / dist) * self.speed
            self.vy = -(dist_y / dist) * self.speed

        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.rect.x = max(0, min(self.rect.x, map_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, map_height - self.rect.height))

    def draw(self, surface, camera):
        if self.hp > 0:
            surface.blit(self.image, camera.apply(self.rect))
            if self.hp < self.max_hp:
                bar_w, ratio = 20, self.hp / self.max_hp
                cam_rect = camera.apply(self.rect)
                pygame.draw.rect(surface, (255, 0, 0), (cam_rect.x, cam_rect.y - 8, bar_w * ratio, 4))

class Bear:
    def __init__(self, x, y, size):
        self.draw_size = size 
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        try:
            b_img = pygame.image.load(os.path.join(BASE_DIR, 'bear.png')).convert_alpha()
            self.image = pygame.transform.scale(b_img, (self.draw_size, self.draw_size))
        except FileNotFoundError:
            self.image = pygame.Surface((self.draw_size, self.draw_size))
            self.image.fill((139, 69, 19)) 

        self.rect = pygame.Rect(x, y, self.draw_size, self.draw_size) 
        self.hp, self.max_hp = 15, 15
        self.speed = 2
        self.damage = 25 
        self.state = "wander"
        self.vx, self.vy, self.timer, self.attack_cooldown = 0, 0, 0, 0
        self.meat_drop = 5
        self.leather_drop = 3 

    def update(self, player, map_width, map_height):
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        dist_x = player.rect.centerx - self.rect.centerx
        dist_y = player.rect.centery - self.rect.centery
        dist = math.hypot(dist_x, dist_y)

        if dist < 200: self.state = "chase"
        else: self.state = "wander"

        if self.state == "wander":
            self.timer -= 1
            if self.timer <= 0:
                self.vx = random.choice([-1, 0, 1]) * (self.speed - 1)
                self.vy = random.choice([-1, 0, 1]) * (self.speed - 1)
                self.timer = random.randint(30, 90)
        elif self.state == "chase" and dist > 0:
            self.vx = (dist_x / dist) * self.speed
            self.vy = (dist_y / dist) * self.speed
                
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.rect.x = max(0, min(self.rect.x, map_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, map_height - self.rect.height))
        
        if self.state == "chase" and self.rect.colliderect(player.rect) and self.attack_cooldown == 0:
            player.hp -= self.damage
            self.attack_cooldown = 60 

    def draw(self, surface, camera):
        if self.hp > 0:
            surface.blit(self.image, camera.apply(self.rect))
            if self.hp < self.max_hp:
                bar_w, ratio = 20, self.hp / self.max_hp
                cam_rect = camera.apply(self.rect)
                pygame.draw.rect(surface, (255, 0, 0), (cam_rect.x, cam_rect.y - 8, bar_w * ratio, 4))

def generate_animals(game_map, tile_size, num_animals=50):
    animals = []
    cols = game_map.width // tile_size
    rows = game_map.height // tile_size
    
    for _ in range(num_animals):
        while True:
            r_col = random.randint(0, cols - 1)
            r_row = random.randint(0, rows - 1)
            tile_type = game_map.grid[r_row][r_col]
            rand = random.random()
            
            if tile_type == "grass": 
                x, y = r_col * tile_size, r_row * tile_size
                if rand < 0.4: animals.append(Animal(x, y, "passive", tile_size))
                elif rand < 0.8: animals.append(Animal(x, y, "aggressive", tile_size))
                else: animals.append(Pig(x, y, tile_size))
                break
            elif tile_type == "rock" and rand < 0.1: 
                x, y = r_col * tile_size, r_row * tile_size
                animals.append(Bear(x, y, tile_size))
                break
    return animals

class Chest:
    def __init__(self, x, y, size):
        self.rect = pygame.Rect(x, y, size, size)
        self.hp = 1 
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        try:
            img = pygame.image.load(os.path.join(BASE_DIR, 'chest.png')).convert_alpha()
            self.image = pygame.transform.scale(img, (size, size))
        except:
            self.image = pygame.Surface((size, size))
            self.image.fill((255, 215, 0))

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))

def generate_chests(game_map, tile_size, num_chests=15):
    chests = []
    cols, rows = game_map.width // tile_size, game_map.height // tile_size
    for _ in range(num_chests):
        while True:
            r, c = random.randint(0, rows - 1), random.randint(0, cols - 1)
            if game_map.grid[r][c] == "grass":
                chests.append(Chest(c * tile_size, r * tile_size, tile_size))
                break
    return chests

class PathFinder:
    @staticmethod
    def get_neighbors(node, grid):
        r, c = node
        neighbors = []
        rows = len(grid)
        cols = len(grid[0])
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if grid[nr][nc] == "grass": 
                    neighbors.append((nr, nc))
        return neighbors

    @staticmethod
    def heuristic(a, b):
        return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

    @staticmethod
    def bfs(start, goal, grid):
        queue = deque([start])
        came_from = {start: None}
        while queue:
            current = queue.popleft()
            if current == goal: break
            for next_node in PathFinder.get_neighbors(current, grid):
                if next_node not in came_from:
                    queue.append(next_node)
                    came_from[next_node] = current
        return PathFinder.reconstruct_path(came_from, start, goal)

    @staticmethod
    def dfs(start, goal, grid):
        stack = [start]
        came_from = {start: None}
        while stack:
            current = stack.pop()
            if current == goal: break
            for next_node in PathFinder.get_neighbors(current, grid):
                if next_node not in came_from:
                    stack.append(next_node)
                    came_from[next_node] = current
        return PathFinder.reconstruct_path(came_from, start, goal)

    @staticmethod
    def greedy(start, goal, grid):
        pq = []
        heapq.heappush(pq, (0, start))
        came_from = {start: None}
        while pq:
            _, current = heapq.heappop(pq)
            if current == goal: break
            for next_node in PathFinder.get_neighbors(current, grid):
                if next_node not in came_from:
                    priority = PathFinder.heuristic(next_node, goal)
                    heapq.heappush(pq, (priority, next_node))
                    came_from[next_node] = current
        return PathFinder.reconstruct_path(came_from, start, goal)

    @staticmethod
    def astar(start, goal, grid):
        pq = []
        heapq.heappush(pq, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        while pq:
            _, current = heapq.heappop(pq)
            if current == goal: break
            for next_node in PathFinder.get_neighbors(current, grid):
                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + PathFinder.heuristic(next_node, goal)
                    heapq.heappush(pq, (priority, next_node))
                    came_from[next_node] = current
        return PathFinder.reconstruct_path(came_from, start, goal)

    @staticmethod
    def reconstruct_path(came_from, start, goal):
        if goal not in came_from: return []
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

# --- CLASS BOSS CAP NHAT LOAD ANH THEO LEVEL ---
class Boss:
    def __init__(self, x, y, size, level=1):
        self.draw_size = size 
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        try:
            # Tu dong load anh mon1.png, mon2.png... theo level
            # Neu file ban luu la .jpg, hay sua ".png" thanh ".jpg" o dong duoi nhe
            image_name = f'mon{level}.png' 
            b_img = pygame.image.load(os.path.join(BASE_DIR, image_name)).convert_alpha()
            self.image = pygame.transform.scale(b_img, (self.draw_size, self.draw_size))
        except FileNotFoundError:
            self.image = pygame.Surface((self.draw_size, self.draw_size))
            self.image.fill((100 + level * 20, 0, 100)) # Mau sac thay doi neu khong co anh

        self.rect = pygame.Rect(x, y, self.draw_size, self.draw_size) 
        self.hp, self.max_hp = 50, 50 
        self.speed = 3
        self.damage = 30 
        self.attack_cooldown = 0
        
        self.path = []
        self.path_timer = 0
        self.current_algo = "A*" 
        self.tile_size = 32

    def update(self, player, game_map_grid, map_width, map_height):
        self.current_algo = "A*"
        if self.attack_cooldown > 0: self.attack_cooldown -= 1
        
        dist = math.hypot(player.rect.centerx - self.rect.centerx, player.rect.centery - self.rect.centery)
        
        if dist < 80 and self.attack_cooldown == 0:
            player.hp -= self.damage
            self.attack_cooldown = 60
            return

        self.path_timer -= 1
        if self.path_timer <= 0 and dist < 600:
            start_node = (self.rect.centery // self.tile_size, self.rect.centerx // self.tile_size)
            goal_node = (player.rect.centery // self.tile_size, player.rect.centerx // self.tile_size)
            
            if 0 <= start_node[0] < len(game_map_grid) and 0 <= goal_node[0] < len(game_map_grid[0]):
                self.path = PathFinder.astar(start_node, goal_node, game_map_grid)
            
            self.path_timer = 30 

        if self.path:
            target_node = self.path[0]
            target_x = target_node[1] * self.tile_size + self.tile_size // 2
            target_y = target_node[0] * self.tile_size + self.tile_size // 2
            
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            step_dist = math.hypot(dx, dy)
            
            if step_dist > self.speed:
                self.rect.x += int((dx / step_dist) * self.speed)
                self.rect.y += int((dy / step_dist) * self.speed)
            else:
                self.path.pop(0)

        self.rect.x = max(0, min(self.rect.x, map_width - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, map_height - self.rect.height))

    def draw(self, surface, camera):
        if self.hp > 0:
            surface.blit(self.image, camera.apply(self.rect))
            if self.hp < self.max_hp:
                bar_w, ratio = 60, self.hp / self.max_hp 
                cam_rect = camera.apply(self.rect)
                pygame.draw.rect(surface, (255, 0, 0), (cam_rect.x, cam_rect.y - 12, bar_w * ratio, 6))