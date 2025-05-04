import pygame
import random
import sys
import random
import os

pygame.init()
WIDTH, HEIGHT = 800, 1000
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

PLAYER_SHIP = pygame.image.load(os.path.join(ASSETS_DIR, "main_ship-2.png")).convert_alpha()
ENEMY_SHIP = pygame.image.load(os.path.join(ASSETS_DIR, "darkgrey_02.png")).convert_alpha()
TANK_ENEMY_SHIP = pygame.image.load(os.path.join(ASSETS_DIR, "enemy_2_2.png")).convert_alpha()
BULLET_IMG = pygame.image.load(os.path.join(ASSETS_DIR, "projectile_1.png")).convert_alpha()
BG = pygame.transform.scale(pygame.image.load(os.path.join(ASSETS_DIR, "background.png")).convert(), (WIDTH, HEIGHT))
BOSS_IMAGE = pygame.image.load(os.path.join(ASSETS_DIR, "large_enemy.png")).convert_alpha()
EXPLOSION_IMAGE = pygame.image.load(os.path.join(ASSETS_DIR, "explosion-3.png")).convert_alpha()
POWERUP_IMAGE = pygame.image.load(os.path.join(ASSETS_DIR, "icon-powerup.png")).convert_alpha()

font = pygame.font.SysFont("comicsans", 30)
big_font = pygame.font.SysFont("comicsans", 60)
clock = pygame.time.Clock()
FPS = 60

score = 0
wave = 0
max_waves = 10
boss_waves = [5, 10]
boss_spawned = False
powerup = None
boss_defeated = False

class Bullet:
    def __init__(self, x, y):
        self.img = BULLET_IMG
        self.x = x
        self.y = y
        self.vel = 7
        self.mask = pygame.mask.from_surface(self.img)

    def move(self):
        self.y -= self.vel

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def off_screen(self):
        return self.y < 0

    def collision(self, obj):
        offset = (int(obj.x - self.x), int(obj.y - self.y))
        return self.mask.overlap(obj.mask, offset) != None

class Enemy:
    def __init__(self, x, y, tank=False):
        self.img = TANK_ENEMY_SHIP if tank else ENEMY_SHIP
        self.x = x
        self.y = y
        self.vel = 1 if tank else 2
        self.health = 3 if tank else 2
        self.mask = pygame.mask.from_surface(self.img)
        self.last_shot = pygame.time.get_ticks()

    def move(self):
        self.y += self.vel

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def can_shoot(self):
        return 0 < self.y < HEIGHT

    def shoot(self, bullets):
        if self.can_shoot():
            now = pygame.time.get_ticks()
            if now - self.last_shot > 2000:
                bullets.append(EnemyBullet(self.x + self.img.get_width()//2 - 3, self.y + self.img.get_height()))
                self.last_shot = now

class Boss(Enemy):
    def __init__(self, x, y, health):
        super().__init__(x, y, tank=True)
        self.img = pygame.transform.scale(BOSS_IMAGE, (200, 200))
        self.health = health
        self.max_health = health
        self.mask = pygame.mask.from_surface(self.img)
        self.vel = 0.8
        self.last_shot = pygame.time.get_ticks()

    def draw_health_bar(self, window):
        pygame.draw.rect(window, (255, 0, 0), (self.x, self.y - 10, self.img.get_width(), 10))
        pygame.draw.rect(window, (0, 255, 0), (self.x, self.y - 10, self.img.get_width() * self.health / self.max_health, 10))

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))
        self.draw_health_bar(window)

    def shoot(self, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot > 1500:
            self.last_shot = now
            num_bullets = random.randint(1, 5)

            for _ in range(num_bullets):
                random_x = random.randint(self.x + 10, self.x + self.img.get_width() - 10)
                bullet = EnemyBullet(random_x, self.y + self.img.get_height())
                bullets.append(bullet)

class EnemyBullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 3
        self.rect = pygame.Rect(self.x - 3, self.y, 6, 12)

    def move(self):
        self.y += self.speed
        self.rect.y = self.y

    def draw(self, window):
        pygame.draw.rect(window, (255, 0, 0), self.rect)

    def off_screen(self):
        return self.y > HEIGHT

class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 15
        self.img = EXPLOSION_IMAGE

    def draw(self, window):
        win.blit(self.img, (self.x - self.img.get_width() // 2, self.y - self.img.get_height() // 2))

    def update(self):
        self.timer -= 1
        return self.timer <= 0

class PowerUp:
    def __init__(self, x, y, type="faster_shoot"):
        self.x = x
        self.y = y
        self.img = POWERUP_IMAGE
        self.mask = pygame.mask.from_surface(self.img)
        self.vel = 2
        self.type = type

    def move(self):
        self.y += self.vel

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def off_screen(self):
        return self.y > HEIGHT

    def collision(self, obj):
        offset = (int(obj.x - self.x), int(obj.y - self.y))
        return self.mask.overlap(obj.mask, offset) != None

    def apply(self, player):
        if self.type == "faster_shoot":
            player.cooldown = 17
            print("Faster shooting activated!")

class Player:
    def __init__(self):
        self.img = PLAYER_SHIP
        self.x = WIDTH // 2 - self.img.get_width() // 2
        self.y = HEIGHT - 100
        self.cooldown = 28
        self.bullets = []
        self.cool_timer = 0
        self.mask = pygame.mask.from_surface(self.img)

    def move(self, pos):
        self.x = pos[0] - self.img.get_width() // 2
        self.y = pos[1] - self.img.get_height() // 2
        if self.x < 0:
            self.x = 0
        if self.x > WIDTH - self.img.get_width():
            self.x = WIDTH - self.img.get_width()
        if self.y < 0:
            self.y = 0
        if self.y > HEIGHT - self.img.get_height():
            self.y = HEIGHT - self.img.get_height()

    def shoot(self):
        if self.cool_timer == 0:
            bullet = Bullet(self.x + self.img.get_width() // 2 - 5, self.y)
            self.bullets.append(bullet)
            self.cool_timer = self.cooldown

    def update_cooldown(self):
        if self.cool_timer > 0:
            self.cool_timer -= 1

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))
        for bullet in self.bullets:
            bullet.draw(window)

    def get_rect(self):
        return self.img.get_rect(topleft=(self.x, self.y))

player = Player()
enemies = []
enemy_bullets = []
explosions = []
boss = None
game_over = False
victory = False
game_started = False

def reset_game():
    global score, wave, boss, enemies, enemy_bullets, explosions, player, game_over, victory, boss_spawned, powerup
    score = 0
    wave = 0
    boss = None
    enemies = []
    enemy_bullets = []
    explosions = []
    player = Player()
    game_over = False
    victory = False
    boss_spawned = False
    powerup = None
    boss_defeated = False

def draw_menu():
    win.blit(BG, (0, 0))
    title_text = big_font.render("Space Shooter", 1, (255, 255, 255))
    start_text = font.render("Start Game", 1, (255, 255, 255))
    exit_text = font.render("Exit Game", 1, (255, 255, 255))

    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 3))
    start_rect = start_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    exit_rect = exit_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))

    win.blit(title_text, title_rect)
    win.blit(start_text, start_rect)
    win.blit(exit_text, exit_rect)
    pygame.display.update()

    return start_rect, exit_rect

def redraw_game():
    win.blit(BG, (0, 0))
    player.draw(win)
    for e in enemies:
        e.draw(win)
    for b in enemy_bullets:
        b.draw(win)
    for e in explosions:
        e.draw(win)
    if boss:
        boss.draw(win)
    if powerup:
        powerup.draw(win)

    wave_text = font.render(f"Wave: {wave}", 1, (255, 255, 255))
    score_text = font.render(f"Score: {score}", 1, (255, 255, 255))
    win.blit(wave_text, (10, 10))
    win.blit(score_text, (10, 40))

    if game_over:
        msg = big_font.render("Game Over", True, (255, 0, 0))
        win.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - msg.get_height()))
    elif victory:
        msg = big_font.render("You Win!", True, (0, 255, 0))
        win.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - msg.get_height()))

    pygame.display.update()

run = True
while run:
    if not game_started:
        start_button, exit_button = draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if start_button.collidepoint(mouse_pos):
                    game_started = True
                    reset_game()
                elif exit_button.collidepoint(mouse_pos):
                    run = False
        continue

    clock.tick(FPS)
    redraw_game()

    if game_over or victory:
        pygame.time.delay(3000)
        game_started = False
        continue

    if len(enemies) == 0 and boss is None:
        wave += 1
        boss_spawned = False
        if wave in boss_waves:
            boss_health = 25 if wave == 5 else 50
            boss = Boss(WIDTH // 2 - 100, 50, boss_health)
            boss.vel = 0.65
            boss_spawned = True
        elif wave <= max_waves:
            for _ in range(5 + wave):
                enemies.append(Enemy(random.randint(50, WIDTH - 50), random.randint(-1500, -100), tank=random.random() < 0.3))

        if wave > max_waves and boss is None:
            victory = True

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.MOUSEMOTION:
            player.move(event.pos)

    if pygame.mouse.get_pressed()[0]:
        player.shoot()
    player.update_cooldown()

    for b in player.bullets[:]:
        b.move()
        if b.off_screen():
            player.bullets.remove(b)
        else:
            hit = False
            for e in enemies[:]:
                if b.collision(e):
                    e.health -= 1
                    if e.health <= 0:
                        explosions.append(Explosion(e.x + e.img.get_width()//2, e.y + e.img.get_height()//2))
                        enemies.remove(e)
                        score += 10
                    player.bullets.remove(b)
                    hit = True
                    break
            if boss and not hit and b.collision(boss):
                boss.health -= 1
                if boss.health <= 0:
                    explosions.append(Explosion(boss.x + boss.img.get_width()//2, boss.y + boss.img.get_height()//2))
                    boss = None
                    score += 100
                    boss_defeated = True
                player.bullets.remove(b)

    for e in enemies[:]:
        e.move()
        e.shoot(enemy_bullets)
        if e.y > HEIGHT:
            game_over = True
        if player.get_rect().colliderect(e.img.get_rect(topleft=(e.x, e.y))):
            explosions.append(Explosion(player.x + player.img.get_width()//2, player.y + player.img.get_height()//2))
            game_over = True

    if boss:
        boss.move()
        boss.shoot(enemy_bullets)
        if player.get_rect().colliderect(boss.img.get_rect(topleft=(boss.x, boss.y))):
            explosions.append(Explosion(player.x + player.img.get_width()//2, player.y + player.img.get_height()//2))
            game_over = True
        if boss.health <= 0:
            explosions.append(Explosion(boss.x + boss.img.get_width()//2, boss.y + boss.img.get_height()//2))
            boss = None
            score += 100
            boss_defeated = True

    for eb in enemy_bullets[:]:
        eb.move()
        if eb.off_screen():
            enemy_bullets.remove(eb)
        elif player.get_rect().colliderect(eb.rect):
            explosions.append(Explosion(player.x + player.img.get_width()//2, player.y + player.img.get_height()//2))
            game_over = True
            enemy_bullets.remove(eb)

    for e in explosions[:]:
        if e.update():
            explosions.remove(e)

    if powerup:
        powerup.move()
        if powerup.off_screen():
            powerup = None
        elif powerup.collision(player):
            powerup.apply(player)
            powerup = None

    if boss_defeated and powerup is None and wave < max_waves:
        powerup = PowerUp(random.randint(50, WIDTH - 50), 50, type="faster_shoot")
        boss_defeated = False

pygame.quit()