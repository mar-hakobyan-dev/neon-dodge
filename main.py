import pygame
import sys
import random

pygame.init()

# Window settings
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON DODGE: Phase 2")
clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (10, 10, 14)
WHITE = (245, 245, 245)
PLAYER_COLOR = (210, 210, 210)
HAZARD_COLOR = (240, 60, 90)

# Helper
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# Player class
class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 28
        self.speed = 320.0
        self.dash_speed = 980.0
        self.dash_time = 0.085
        self._dash_left = 0.0
        self._dash_dir = 0.0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def start_dash(self, direction):
        if direction == 0:
            return
        self._dash_dir = direction
        self._dash_left = self.dash_time

    def update(self, dt, move_dir):
        if self._dash_left > 0:
            self.x += self._dash_dir * self.dash_speed * dt
            self._dash_left = max(0.0, self._dash_left - dt)
        else:
            self.x += move_dir * self.speed * dt
        self.x = clamp(self.x, 0, WIDTH - self.size)

# Hazard class
class Hazard:
    def __init__(self, x, y, size, vy):
        self.x = x
        self.y = y
        self.size = size
        self.vy = vy

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

# Game setup
player = Player(WIDTH / 2 - 14, HEIGHT - 78)
hazards = []
spawn_timer = 0.0
score = 0.0
alive = True
rng = random.Random()

# Game loop
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Input
    keys = pygame.key.get_pressed()
    move_dir = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        move_dir -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        move_dir += 1
    if keys[pygame.K_SPACE]:
        player.start_dash(move_dir if move_dir != 0 else 0)

    # Update player
    player.update(dt, move_dir)

    # Spawn hazards
    spawn_timer -= dt
    if spawn_timer <= 0.0:
        spawn_timer = 0.8  # spawn interval
        size = rng.randint(20, 40)
        x = rng.uniform(0, WIDTH - size)
        y = -size
        vy = rng.uniform(180, 260)
        hazards.append(Hazard(x, y, size, vy))

    # Update hazards
    for hz in hazards:
        hz.y += hz.vy * dt

    # Collision detection
    player_rect = player.rect()
    for hz in hazards:
        if player_rect.colliderect(hz.rect()):
            alive = False

    # Remove off-screen hazards
    hazards = [hz for hz in hazards if hz.y < HEIGHT + 50]

    # Update score
    if alive:
        score += dt * 10

    # Draw
    screen.fill(BLACK)
    for hz in hazards:
        pygame.draw.rect(screen, HAZARD_COLOR, hz.rect(), border_radius=6)
    pygame.draw.rect(screen, PLAYER_COLOR, player.rect(), border_radius=6)

    # Draw score
    font = pygame.font.SysFont("consolas", 18)
    score_text = font.render(f"SCORE: {int(score)}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Game over text
    if not alive:
        game_over_text = font.render("GAME OVER", True, WHITE)
        screen.blit(game_over_text, (WIDTH / 2 - game_over_text.get_width() / 2, HEIGHT / 2))

    pygame.display.flip()

pygame.quit()
sys.exit()