import math
import random
import sys
import pygame
from dataclasses import dataclass

pygame.init()

# Window
WIDTH, HEIGHT = 600, 800
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
display_surface = pygame.Surface((WIDTH, HEIGHT)) 
pygame.display.set_caption("NEON DODGE: Hard Mode")
clock = pygame.time.Clock()

# Colors
WHITE = (245, 245, 245)
BLACK = (10, 10, 14)
RED = (240, 60, 90)
CYAN = (70, 240, 240)
YELLOW = (255, 220, 90)
PURPLE = (170, 120, 255)

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

@dataclass
class Player:
    x: float
    y: float
    size: int = 28
    base_speed: float = 320.0
    dash_speed: float = 980.0
    dash_time: float = 0.085
    dash_cooldown: float = 0.55
    invuln_time: float = 0.10

    _dash_left: float = 0.0
    _cooldown_left: float = 0.0
    _invuln_left: float = 0.0
    _dash_dir: float = 0.0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def start_dash(self, direction: float):
        if self._cooldown_left > 0.0 or self._dash_left > 0.0:
            return
        if direction == 0.0:
            return
        self._dash_dir = math.copysign(1.0, direction)
        self._dash_left = self.dash_time
        self._cooldown_left = self.dash_cooldown
        self._invuln_left = self.invuln_time

    def update(self, dt: float, move_dir: float):
        if self._cooldown_left > 0.0:
            self._cooldown_left = max(0.0, self._cooldown_left - dt)
        if self._invuln_left > 0.0:
            self._invuln_left = max(0.0, self._invuln_left - dt)

        if self._dash_left > 0.0:
            self._dash_left = max(0.0, self._dash_left - dt)
            self.x += self._dash_dir * self.dash_speed * dt
        else:
            self.x += move_dir * self.base_speed * dt
        self.x = clamp(self.x, 0, WIDTH - self.size)

    @property
    def is_dashing(self) -> bool:
        return self._dash_left > 0.0

    @property
    def invulnerable(self) -> bool:
        return self._invuln_left > 0.0

    @property
    def dash_ready(self) -> bool:
        return self._cooldown_left <= 0.0 and self._dash_left <= 0.0

    @property
    def dash_cooldown_ratio(self) -> float:
        if self.dash_ready:
            return 0.0
        return clamp(self._cooldown_left / max(0.001, self.dash_cooldown), 0.0, 1.0)

@dataclass
class Hazard:
    kind: str
    x: float
    y: float
    w: int
    h: int
    vx: float
    vy: float
    color: tuple[int, int, int]

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple[int, int, int]
    size: int

    def update(self, dt: float):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, surface):
        alpha = int((self.life / self.max_life) * 255)
        s = pygame.Surface((self.size, self.size))
        s.set_alpha(alpha)
        s.fill(self.color)
        surface.blit(s, (int(self.x), int(self.y)))

class Game:
    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 18)
        self.big_font = pygame.font.SysFont("consolas", 46, bold=True)
        self.reset()

    def reset(self):
        self.rng = random.Random()
        self.player = Player(x=WIDTH/2-14, y=HEIGHT-78)
        self.hazards: list[Hazard] = []
        self.particles: list[Particle] = []
        self.score = 0.0
        self.best = 0.0
        self.level = 1
        self.alive = True
        self.time = 0.0
        self.spawn_timer = 0.0
        self.snipe_charge = 0.0
        self._just_died_flash = 0.0
        self.shake_intensity = 0.0

    def difficulty(self):
        return 1.0 + (self.score / 800.0)

    def compute_level(self):
        return 1 + int(self.score // 450)

    def create_particles(self, x, y, color, count=10, speed=150.0):
        for _ in range(count):
            self.particles.append(Particle(
                x=x, y=y,
                vx=random.uniform(-speed, speed),
                vy=random.uniform(-speed, speed),
                life=0.4,
                max_life=0.4,
                color=color,
                size=random.randint(3, 6)
            ))

    def spawn_fall(self, diff):
        size = int(clamp(22 + diff*2.0, 22, 52))
        x = self.rng.uniform(0, WIDTH-size)
        y = -size - self.rng.uniform(0, 120)
        vy = 260 + 90*diff + self.rng.uniform(-30, 50)
        self.hazards.append(Hazard("fall", x, y, size, size, 0.0, vy, RED))

    def spawn_zig(self, diff):
        w = int(clamp(18 + diff*2.0, 18, 40))
        h = w
        x = self.rng.uniform(0, WIDTH-w)
        y = -h - self.rng.uniform(0, 150)
        vy = 230 + 75*diff + self.rng.uniform(-20, 40)
        vx = self.rng.choice([-1,1])*(140+65*diff+self.rng.uniform(-20,40))
        self.hazards.append(Hazard("zig", x, y, w, h, vx, vy, PURPLE))

    def spawn_snipe(self, player_x, diff):
        w = int(clamp(12 + diff*1.7, 12, 26))
        h = int(clamp(34 + diff*4.0, 34, 78))
        x = clamp(player_x + self.rng.uniform(-18,18), 0, WIDTH-w)
        y = -h-10
        vy = 520 + 120*diff + self.rng.uniform(-40,60)
        self.hazards.append(Hazard("snipe", x, y, w, h, 0.0, vy, CYAN))

    def update_spawns(self, dt):
        diff = self.difficulty()
        self.spawn_timer -= dt
        base_interval = 0.32 / clamp(diff**0.55, 1.0, 3.0)
        if self.spawn_timer <= 0.0:
            self.spawn_timer = clamp(base_interval + self.rng.uniform(-0.07,0.07), 0.10, 0.40)
            roll = self.rng.random()
            if roll < 0.65: self.spawn_fall(diff)
            elif roll < 0.90: self.spawn_zig(diff)
            else: 
                self.spawn_fall(diff)
                if self.rng.random() < 0.35: self.spawn_zig(diff)
        
        self.snipe_charge += dt
        snipe_interval = clamp(1.35 / clamp(diff**0.65,1.0,4.0),0.45,1.35)
        if self.snipe_charge >= snipe_interval:
            self.snipe_charge = 0.0
            self.spawn_snipe(self.player.x, diff)

    def update_hazards(self, dt):
        diff = self.difficulty()
        for hz in self.hazards:
            hz.x += hz.vx*dt
            hz.y += hz.vy*dt
            if hz.kind=="zig":
                if hz.x<0: hz.x=0; hz.vx=abs(hz.vx)
                if hz.x>WIDTH-hz.w: hz.x=WIDTH-hz.w; hz.vx=-abs(hz.vx)
                hz.vx *= 1.0 + 0.22*dt*clamp(diff,1.0,4.0)
        self.hazards = [h for h in self.hazards if h.y<HEIGHT+140]

    def check_collisions(self):
        if self.player.invulnerable: return False
        p = self.player.rect()
        for hz in self.hazards:
            if p.colliderect(hz.rect()): return True
        return False

    def draw(self):
        display_surface.fill(BLACK)
        
        for p in self.particles:
            p.draw(display_surface)

        for hz in self.hazards:
            pygame.draw.rect(display_surface, hz.color, hz.rect(), border_radius=6)
        
        p_rect = self.player.rect()
        p_color = (240,240,240) if self.player.invulnerable else (210,210,210)
        pygame.draw.rect(display_surface, p_color, p_rect, border_radius=6)
        
        if self.player.invulnerable:
            pygame.draw.rect(display_surface, WHITE, p_rect.inflate(10,10), width=2, border_radius=8)
        
        if self._just_died_flash > 0.0:
            overlay = pygame.Surface((WIDTH,HEIGHT))
            overlay.set_alpha(int(120 * (self._just_died_flash/0.18)))
            overlay.fill((160,30,40))
            display_surface.blit(overlay,(0,0))

        render_offset = (0, 0)
        if self.shake_intensity > 0:
            render_offset = (random.uniform(-self.shake_intensity, self.shake_intensity),
                             random.uniform(-self.shake_intensity, self.shake_intensity))

        screen.fill(BLACK)
        screen.blit(display_surface, render_offset)

        self.draw_hud()

        if not self.alive:
            title = self.big_font.render("GAME OVER", True, WHITE)
            sub = self.font.render("Press R to restart | Esc to quit", True, WHITE)
            screen.blit(title,(WIDTH/2 - title.get_width()/2, HEIGHT/2-90))
            screen.blit(sub,(WIDTH/2 - sub.get_width()/2, HEIGHT/2-25))

    def draw_hud(self):
        score_txt = self.font.render(f"SCORE {int(self.score):>6}", True, WHITE)
        lvl_txt = self.font.render(f"LVL {self.level:>2}", True, WHITE)
        screen.blit(score_txt,(12,10))
        screen.blit(lvl_txt,(12,32))
        bar_w, bar_h = 140, 10
        x, y = WIDTH-bar_w-12, 14
        pygame.draw.rect(screen,(40,40,55),(x,y,bar_w,bar_h),border_radius=6)
        fill = int(bar_w*(1.0 - self.player.dash_cooldown_ratio))
        pygame.draw.rect(screen,YELLOW if self.player.dash_ready else (160,140,70),(x,y,fill,bar_h),border_radius=6)

    def update(self, dt):
        if self.shake_intensity > 0:
            self.shake_intensity = max(0.0, self.shake_intensity - dt * 30.0)

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

        if not self.alive:
            self._just_died_flash = max(0.0, self._just_died_flash - dt)
            return

        keys = pygame.key.get_pressed()
        move_dir = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_dir -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_dir += 1.0
        
        if keys[pygame.K_SPACE] and move_dir != 0:
            self.player.start_dash(move_dir)
            if self.player.is_dashing:
                self.shake_intensity = 4.0

        if self.player.is_dashing:
            self.create_particles(self.player.x + self.player.size/2, 
                                  self.player.y + self.player.size/2, 
                                  CYAN, count=2, speed=50)

        self.player.update(dt, move_dir)
        self.update_spawns(dt)
        self.update_hazards(dt)

        if self.check_collisions():
            self.alive = False
            self._just_died_flash = 0.18
            self.shake_intensity = 18.0 
            self.create_particles(self.player.x + 14, self.player.y + 14, WHITE, count=40, speed=250)
            self.best = max(self.best, self.score)
            return

        self.score += dt*(40.0 + 12.0*clamp(self.difficulty(),1.0,6.0))
        self.level = self.compute_level()

def main():
    game = Game()
    while True:
        dt = clock.tick(FPS)/1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if not game.alive and event.key == pygame.K_r:
                    game.reset()
        game.update(dt)
        game.draw()
        pygame.display.flip()

if __name__=="__main__":
    main()