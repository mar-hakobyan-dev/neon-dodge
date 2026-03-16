import pygame
import sys

pygame.init()

# Window settings
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON DODGE: Phase 1")
clock = pygame.time.Clock()
FPS = 60

# Colors
BLACK = (10, 10, 14)
WHITE = (245, 245, 245)
PLAYER_COLOR = (210, 210, 210)

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

# Game loop
player = Player(WIDTH / 2 - 14, HEIGHT - 78)

running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Movement input
    keys = pygame.key.get_pressed()
    move_dir = 0
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        move_dir -= 1
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        move_dir += 1
    if keys[pygame.K_SPACE]:
        player.start_dash(move_dir if move_dir != 0 else 0)

    # Update
    player.update(dt, move_dir)

    # Draw
    screen.fill(BLACK)
    pygame.draw.rect(screen, PLAYER_COLOR, player.rect(), border_radius=6)

    pygame.display.flip()

pygame.quit()
sys.exit()