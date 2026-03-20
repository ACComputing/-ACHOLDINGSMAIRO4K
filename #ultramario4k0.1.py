"""
ULTRA MARIO 2D. BROS
A simple Super Mario Bros homage using Pygame.
Includes levels 1-1 and 8-4, an intro screen, basic physics,
enemies, coins, and a flagpole to end each level.

CREDIT TO NINTENDO [C] AC HOLDINGS 1999-2026 NINTENDO 1985-2026
AND CREATED BY DEEEPSEEK A.C ENGINE
"""

import pygame
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 60
GRAVITY = 0.8
JUMP_POWER = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 2
CAMERA_SMOOTH = 0.1

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)
SKY_BLUE = (135, 206, 235)

# Set up display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ULTRA MARIO 2D. BROS")
clock = pygame.time.Clock()

# Font for text
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Game states
INTRO = 0
PLAYING = 1
LEVEL_COMPLETE = 2
GAME_OVER = 3

# ----------------------------------------------------------------------
# Sprite classes
# ----------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((30, 40))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.facing_right = True

    def update(self, platforms, enemies, coins, flag):
        # Horizontal movement
        keys = pygame.key.get_pressed()
        self.vx = 0
        if keys[pygame.K_LEFT]:
            self.vx = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT]:
            self.vx = PLAYER_SPEED
            self.facing_right = True
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = JUMP_POWER

        # Apply gravity
        self.vy += GRAVITY

        # Move horizontally and check collisions
        self.rect.x += self.vx
        self.collide_horizontal(platforms)

        # Move vertically and check collisions
        self.rect.y += self.vy
        self.on_ground = False
        self.collide_vertical(platforms)

        # Check enemy collisions
        enemy_hits = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in enemy_hits:
            if self.vy > 0 and self.rect.bottom <= enemy.rect.centery:
                # Player is falling on enemy: kill enemy and bounce
                enemy.kill()
                self.vy = JUMP_POWER / 2
            else:
                # Player hit from side: game over
                return "game_over"

        # Check coin collisions
        coin_hits = pygame.sprite.spritecollide(self, coins, True)
        # In a full game you would increase score here

        # Check flag collision
        if pygame.sprite.spritecollide(self, flag, False):
            return "level_complete"

        return None

    def collide_horizontal(self, platforms):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for hit in hits:
            if self.vx > 0:  # Moving right
                self.rect.right = hit.rect.left
            elif self.vx < 0:  # Moving left
                self.rect.left = hit.rect.right

    def collide_vertical(self, platforms):
        hits = pygame.sprite.spritecollide(self, platforms, False)
        for hit in hits:
            if self.vy > 0:  # Falling down
                self.rect.bottom = hit.rect.top
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:  # Jumping up
                self.rect.top = hit.rect.bottom
                self.vy = 0


class Block(pygame.sprite.Sprite):
    """ Generic platform block """
    def __init__(self, x, y, width, height, color=BROWN):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Enemy(pygame.sprite.Sprite):
    """ Simple Goomba-like enemy that moves back and forth """
    def __init__(self, x, y, width=30, height=30):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 1  # 1 = right, -1 = left
        self.speed = ENEMY_SPEED

    def update(self, platforms):
        # Move horizontally
        self.rect.x += self.direction * self.speed

        # Check for collision with platforms or edges
        hits = pygame.sprite.spritecollide(self, platforms, False)
        if hits:
            self.direction *= -1
            self.rect.x += self.direction * self.speed * 2


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Flag(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 60))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


class Camera:
    """ Simple camera that follows the player """
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = -target.rect.centerx + SCREEN_WIDTH // 2
        y = -target.rect.centery + SCREEN_HEIGHT // 2

        # Limit scrolling to level bounds
        x = min(0, x)  # Left bound
        x = max(-(self.width - SCREEN_WIDTH), x)  # Right bound
        y = min(0, y)  # Top bound
        y = max(-(self.height - SCREEN_HEIGHT), y)  # Bottom bound

        self.camera = pygame.Rect(x, y, self.width, self.height)


# ----------------------------------------------------------------------
# Level definitions
# ----------------------------------------------------------------------
def create_level_1():
    """ Build level 1-1: ground, platforms, enemies, coins, flag """
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    flag = pygame.sprite.Group()

    # Ground (long stretch)
    for i in range(0, 2000, 40):
        block = Block(i, SCREEN_HEIGHT - 40, 40, 40)
        platforms.add(block)

    # Some floating platforms
    platforms.add(Block(300, 300, 80, 20, GREEN))
    platforms.add(Block(500, 250, 80, 20, GREEN))
    platforms.add(Block(700, 200, 80, 20, GREEN))
    platforms.add(Block(900, 300, 80, 20, GREEN))
    platforms.add(Block(1100, 250, 80, 20, GREEN))

    # Enemies
    enemies.add(Enemy(400, SCREEN_HEIGHT - 70))
    enemies.add(Enemy(800, SCREEN_HEIGHT - 70))
    enemies.add(Enemy(1200, SCREEN_HEIGHT - 70))

    # Coins
    coins.add(Coin(320, 270))
    coins.add(Coin(520, 220))
    coins.add(Coin(720, 170))
    coins.add(Coin(920, 270))
    coins.add(Coin(1120, 220))

    # Flag at the end
    flag.add(Flag(1500, SCREEN_HEIGHT - 100))

    level_width = 2000
    level_height = SCREEN_HEIGHT
    return platforms, enemies, coins, flag, level_width, level_height


def create_level_2():
    """ Build level 8-4: castle theme with more hazards """
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    flag = pygame.sprite.Group()

    # Ground
    for i in range(0, 2000, 40):
        block = Block(i, SCREEN_HEIGHT - 40, 40, 40, (100, 100, 100))  # Gray ground
        platforms.add(block)

    # More complex platforms
    platforms.add(Block(200, 320, 80, 20, (150, 150, 150)))
    platforms.add(Block(400, 280, 80, 20, (150, 150, 150)))
    platforms.add(Block(600, 240, 80, 20, (150, 150, 150)))
    platforms.add(Block(800, 200, 80, 20, (150, 150, 150)))
    platforms.add(Block(1000, 240, 80, 20, (150, 150, 150)))
    platforms.add(Block(1200, 280, 80, 20, (150, 150, 150)))
    platforms.add(Block(1400, 320, 80, 20, (150, 150, 150)))

    # Enemies (more of them)
    enemies.add(Enemy(300, SCREEN_HEIGHT - 70))
    enemies.add(Enemy(500, SCREEN_HEIGHT - 70))
    enemies.add(Enemy(700, SCREEN_HEIGHT - 70))
    enemies.add(Enemy(900, SCREEN_HEIGHT - 70))
    enemies.add(Enemy(1100, SCREEN_HEIGHT - 70))

    # Coins in hard-to-reach places
    coins.add(Coin(220, 290))
    coins.add(Coin(420, 250))
    coins.add(Coin(620, 210))
    coins.add(Coin(820, 170))
    coins.add(Coin(1020, 210))
    coins.add(Coin(1220, 250))
    coins.add(Coin(1420, 290))

    # Flag at the end
    flag.add(Flag(1600, SCREEN_HEIGHT - 100))

    level_width = 2000
    level_height = SCREEN_HEIGHT
    return platforms, enemies, coins, flag, level_width, level_height


# ----------------------------------------------------------------------
# Intro screen
# ----------------------------------------------------------------------
def show_intro():
    screen.fill(SKY_BLUE)

    # Title
    title_text = font.render("ULTRA MARIO 2D. BROS", True, RED)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 100))
    screen.blit(title_text, title_rect)

    # Credit lines
    credit_lines = [
        "CREDIT TO NINTENDO [C]",
        "AC HOLDINGS 1999-2026",
        "NINTENDO 1985-2026",
        "AND CREATED BY DEEEPSEEK A.C ENGINE"
    ]
    y_offset = 180
    for line in credit_lines:
        line_text = small_font.render(line, True, BLACK)
        line_rect = line_text.get_rect(center=(SCREEN_WIDTH//2, y_offset))
        screen.blit(line_text, line_rect)
        y_offset += 30

    # Press any key prompt
    prompt_text = small_font.render("Press any key to start", True, BLACK)
    prompt_rect = prompt_text.get_rect(center=(SCREEN_WIDTH//2, 320))
    screen.blit(prompt_text, prompt_rect)

    pygame.display.flip()

    # Wait for key press
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False
        clock.tick(FPS)


# ----------------------------------------------------------------------
# Level complete / game over screens
# ----------------------------------------------------------------------
def show_level_complete(level_num):
    screen.fill(BLACK)
    complete_text = font.render(f"LEVEL {level_num} COMPLETE!", True, GREEN)
    complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH//2, 150))
    screen.blit(complete_text, complete_rect)

    if level_num == 1:
        next_text = small_font.render("Press any key for 8-4", True, WHITE)
    else:
        next_text = small_font.render("Press any key to play again", True, WHITE)
    next_rect = next_text.get_rect(center=(SCREEN_WIDTH//2, 250))
    screen.blit(next_text, next_rect)

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False
        clock.tick(FPS)


def show_game_over():
    screen.fill(BLACK)
    over_text = font.render("GAME OVER", True, RED)
    over_rect = over_text.get_rect(center=(SCREEN_WIDTH//2, 150))
    screen.blit(over_text, over_rect)

    restart_text = small_font.render("Press any key to try again", True, WHITE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, 250))
    screen.blit(restart_text, restart_rect)

    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False
        clock.tick(FPS)


# ----------------------------------------------------------------------
# Main game function
# ----------------------------------------------------------------------
def main():
    current_level = 1
    game_state = INTRO

    while True:
        if game_state == INTRO:
            show_intro()
            game_state = PLAYING
            # Reset to level 1
            current_level = 1
            platforms, enemies, coins, flag, level_width, level_height = create_level_1()
            player = Player(100, SCREEN_HEIGHT - 100)
            all_sprites = pygame.sprite.Group()
            all_sprites.add(player)
            all_sprites.add(platforms)
            all_sprites.add(enemies)
            all_sprites.add(coins)
            all_sprites.add(flag)
            camera = Camera(level_width, level_height)

        elif game_state == PLAYING:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Update
            result = player.update(platforms, enemies, coins, flag)
            if result == "game_over":
                game_state = GAME_OVER
            elif result == "level_complete":
                game_state = LEVEL_COMPLETE

            enemies.update(platforms)

            # Camera follow
            camera.update(player)

            # Draw
            screen.fill(SKY_BLUE)
            for sprite in all_sprites:
                screen.blit(sprite.image, camera.apply(sprite))
            pygame.display.flip()
            clock.tick(FPS)

            # Check if player fell off the bottom
            if player.rect.top > level_height:
                game_state = GAME_OVER

        elif game_state == LEVEL_COMPLETE:
            if current_level == 1:
                show_level_complete(1)
                # Load level 2 (8-4)
                current_level = 2
                platforms, enemies, coins, flag, level_width, level_height = create_level_2()
                player = Player(100, SCREEN_HEIGHT - 100)
                all_sprites = pygame.sprite.Group()
                all_sprites.add(player)
                all_sprites.add(platforms)
                all_sprites.add(enemies)
                all_sprites.add(coins)
                all_sprites.add(flag)
                camera = Camera(level_width, level_height)
                game_state = PLAYING
            else:
                show_level_complete(2)
                # Both levels done, return to intro
                game_state = INTRO

        elif game_state == GAME_OVER:
            show_game_over()
            game_state = INTRO  # Restart from intro


if __name__ == "__main__":
    main()