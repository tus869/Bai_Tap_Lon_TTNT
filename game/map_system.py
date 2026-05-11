import pygame
import random
import os
import math

# --- CẤU HÌNH BẢN ĐỒ ---
TILE_SIZE = 32
MAP_COLS = 100 
MAP_ROWS = 100 

class Camera:
    def __init__(self, width, height, screen_width, screen_height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.screen_w = screen_width
        self.screen_h = screen_height

    def apply(self, entity_rect):
        return entity_rect.move(self.camera.topleft)

    def apply_bg(self):
        return self.camera.topleft

    def update(self, target_rect):
        x = -target_rect.centerx + int(self.screen_w / 2)
        y = -target_rect.centery + int(self.screen_h / 2)
        x = min(0, max(-(self.width - self.screen_w), x))
        y = min(0, max(-(self.height - self.screen_h), y))
        self.camera = pygame.Rect(x, y, self.width, self.height)

class GameMap:
    def __init__(self):
        self.width = MAP_COLS * TILE_SIZE
        self.height = MAP_ROWS * TILE_SIZE
        self.grid = self.generate_biomes() 
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        
        try:
            grass_img = pygame.image.load(os.path.join(BASE_DIR, 'image.png')).convert()
            self.grass_texture = pygame.transform.scale(grass_img, (TILE_SIZE, TILE_SIZE))
            rock_img = pygame.image.load(os.path.join(BASE_DIR, 'rock.png')).convert()
            self.rock_texture = pygame.transform.scale(rock_img, (TILE_SIZE, TILE_SIZE))
        except:
            self.grass_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.grass_texture.fill((34, 139, 34))
            self.rock_texture = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.rock_texture.fill((100, 100, 100))

    def generate_biomes(self):
        grid = [["grass" for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
        seeds = []
        for _ in range(8): seeds.append({'r': random.randint(0, MAP_ROWS-1), 'c': random.randint(0, MAP_COLS-1), 'type': 'water'})
        for _ in range(6): seeds.append({'r': random.randint(0, MAP_ROWS-1), 'c': random.randint(0, MAP_COLS-1), 'type': 'rock'})
        
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                closest_seed = min(seeds, key=lambda s: math.hypot(r - s['r'], c - s['c']))
                dist = math.hypot(r - closest_seed['r'], c - closest_seed['c'])
                
                if closest_seed['type'] == 'water' and dist < 7: grid[r][c] = "water"
                elif closest_seed['type'] == 'rock' and dist < 5: grid[r][c] = "rock"
                
                # --- KHU VỰC CỦA BOSS ---
                # Tạo một vùng đất sẫm màu ở chính giữa tâm bản đồ
                dist_to_center = math.hypot(r - MAP_ROWS//2, c - MAP_COLS//2)
                if dist_to_center < 8:
                    grid[r][c] = "boss_zone"
        return grid

    def draw(self, surface, camera):
        cam_x, cam_y = camera.apply_bg()
        start_col = max(0, -cam_x // TILE_SIZE)
        end_col = min(MAP_COLS, start_col + (surface.get_width() // TILE_SIZE) + 2)
        start_row = max(0, -cam_y // TILE_SIZE)
        end_row = min(MAP_ROWS, start_row + (surface.get_height() // TILE_SIZE) + 2)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile = self.grid[row][col]
                rect = pygame.Rect(col * TILE_SIZE + cam_x, row * TILE_SIZE + cam_y, TILE_SIZE, TILE_SIZE)
                if tile == "grass":
                    surface.blit(self.grass_texture, rect)
                elif tile == "rock":
                    surface.blit(self.rock_texture, rect)
                elif tile == "water":
                    pygame.draw.rect(surface, (30, 144, 255), rect)
                elif tile == "boss_zone":
                    pygame.draw.rect(surface, (60, 20, 20), rect) # Khu vực Boss màu đỏ sẫm

class MiniMap:
    def __init__(self, image_path, total_map_width, total_map_height):
        self.total_map_width = total_map_width
        self.total_map_height = total_map_height
        self.minimap_w, self.minimap_h = 160, 100
        try:
            img = pygame.image.load(image_path).convert()
            self.image = pygame.transform.scale(img, (self.minimap_w, self.minimap_h))
        except:
            self.image = pygame.Surface((self.minimap_w, self.minimap_h))
            self.image.fill((50, 50, 50))

    def draw(self, surface, player_rect, screen_width):
        x, y = screen_width - self.minimap_w - 15, 15
        surface.blit(self.image, (x, y))
        pygame.draw.rect(surface, (255, 255, 255), (x, y, self.minimap_w, self.minimap_h), 2)
        bx = x + int((player_rect.centerx / self.total_map_width) * self.minimap_w)
        by = y + int((player_rect.centery / self.total_map_height) * self.minimap_h)
        pygame.draw.circle(surface, (255, 0, 0), (bx, by), 4)