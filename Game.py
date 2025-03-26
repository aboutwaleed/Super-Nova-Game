import pygame
import random
import math
import sys

# Global constants
W, H = 1200, 800
DEGTORAD = math.pi / 180

# Initialize pygame
pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Asteroids!")
clock = pygame.time.Clock()

# Animation class manages sprite sheet animations
class Animation:
    def __init__(self, image, x, y, w, h, count, speed):
        self.frames = []
        for i in range(count):
            rect = pygame.Rect(x + i * w, y, w, h)
            frame = image.subsurface(rect).copy()
            self.frames.append(frame)
        self.speed = speed
        self.frame = 0
        # For rotation, we store the original frame image
        self.image = self.frames[0]
        self.w = w
        self.h = h

    def update(self):
        self.frame += self.speed
        n = len(self.frames)
        if self.frame >= n:
            self.frame -= n
        self.image = self.frames[int(self.frame)]

    def is_end(self):
        return self.frame + self.speed >= len(self.frames)

# Base class for all entities
class Entity:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.dx = 0.0
        self.dy = 0.0
        self.angle = 0.0
        self.R = 1
        self.life = True
        self.name = ""
        self.anim = None

    def settings(self, anim, X, Y, Angle=0, radius=1):
        self.anim = anim
        self.x = X
        self.y = Y
        self.angle = Angle
        self.R = radius

    def update(self):
        pass

    def draw(self, surface):
        # Rotate the current image. +90 to match original rotation offset.
        rotated_image = pygame.transform.rotate(self.anim.image, -(self.angle + 90))
        rect = rotated_image.get_rect(center=(self.x, self.y))
        surface.blit(rotated_image, rect.topleft)
        # Optionally, for debugging, draw the collision circle:
        # pygame.draw.circle(surface, (255, 0, 0, 170), (int(self.x), int(self.y)), self.R, 1)

# Asteroid entity moves with constant velocity and wraps around the screen.
class Asteroid(Entity):
    def __init__(self):
        super().__init__()
        self.dx = random.randint(-4, 4)
        self.dy = random.randint(-4, 4)
        self.name = "asteroid"

    def update(self):
        self.x += self.dx
        self.y += self.dy
        if self.x > W: self.x = 0
        if self.x < 0: self.x = W
        if self.y > H: self.y = 0
        if self.y < 0: self.y = H

# Bullet entity moves in the direction of the angle
class Bullet(Entity):
    def __init__(self):
        super().__init__()
        self.name = "bullet"

    def update(self):
        self.dx = math.cos(self.angle * DEGTORAD) * 6
        self.dy = math.sin(self.angle * DEGTORAD) * 6
        self.x += self.dx
        self.y += self.dy
        # Kill bullet if it goes out of bounds
        if self.x > W or self.x < 0 or self.y > H or self.y < 0:
            self.life = False

# Player entity which responds to user input
class Player(Entity):
    def __init__(self):
        super().__init__()
        self.name = "player"
        self.thrust = False

    def update(self):
        if self.thrust:
            self.dx += math.cos(self.angle * DEGTORAD) * 0.2
            self.dy += math.sin(self.angle * DEGTORAD) * 0.2
        else:
            self.dx *= 0.99
            self.dy *= 0.99

        max_speed = 15
        speed = math.hypot(self.dx, self.dy)
        if speed > max_speed:
            self.dx *= max_speed / speed
            self.dy *= max_speed / speed

        self.x += self.dx
        self.y += self.dy

        if self.x > W: self.x = 0
        if self.x < 0: self.x = W
        if self.y > H: self.y = 0
        if self.y < 0: self.y = H

def is_collide(a, b):
    dist_sq = (b.x - a.x) ** 2 + (b.y - a.y) ** 2
    radius_sum = a.R + b.R
    return dist_sq < radius_sum ** 2

def load_image(path, colorkey=None, smooth=False):
    try:
        image = pygame.image.load(path).convert_alpha()
    except pygame.error as message:
        print("Cannot load image:", path)
        raise SystemExit(message)
    # Optionally scale the image smoothly if needed
    if smooth:
        image = pygame.transform.smoothscale(image, image.get_size())
    return image

def main():
    # Load images
    t1 = load_image("images/spaceship.png", smooth=True)
    t2 = load_image("images/background.jpg", smooth=True)
    t3 = load_image("images/explosions/type_C.png")
    t4 = load_image("images/rock.png")
    t5 = load_image("images/fire_blue.png")
    t6 = load_image("images/rock_small.png")
    t7 = load_image("images/explosions/type_B.png")

    # Create background
    background = t2

    # Create animations
    sExplosion       = Animation(t3, 0, 0, 256, 256, 48, 0.5)
    sRock            = Animation(t4, 0, 0, 64, 64, 16, 0.2)
    sRock_small      = Animation(t6, 0, 0, 64, 64, 16, 0.2)
    sBullet          = Animation(t5, 0, 0, 32, 64, 16, 0.8)
    sPlayer          = Animation(t1, 40, 0, 40, 40, 1, 0)
    sPlayer_go       = Animation(t1, 40, 40, 40, 40, 1, 0)
    sExplosion_ship  = Animation(t7, 0, 0, 192, 192, 64, 0.5)

    # Entities list
    entities = []

    # Create asteroids
    for i in range(15):
        a = Asteroid()
        a.settings(sRock, random.randint(0, W), random.randint(0, H), random.randint(0, 360), 25)
        entities.append(a)

    # Create player
    p = Player()
    p.settings(sPlayer, 200, 200, 0, 20)
    entities.append(p)

    running = True
    while running:
        clock.tick(60)  # 60 FPS
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    b = Bullet()
                    b.settings(sBullet, p.x, p.y, p.angle, 10)
                    entities.append(b)

        # Key state handling for player control
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            p.angle += 3
        if keys[pygame.K_LEFT]:
            p.angle -= 3
        if keys[pygame.K_UP]:
            p.thrust = True
        else:
            p.thrust = False

        # Collision detection and response
        for a in entities[:]:
            for b in entities[:]:
                if a.name == "asteroid" and b.name == "bullet":
                    if is_collide(a, b):
                        a.life = False
                        b.life = False
                        # Create explosion at asteroid position
                        e = Entity()
                        e.settings(sExplosion, a.x, a.y)
                        e.name = "explosion"
                        entities.append(e)
                        # Spawn two small asteroids if original asteroid is not already small
                        if a.R != 15:
                            for _ in range(2):
                                e2 = Asteroid()
                                e2.settings(sRock_small, a.x, a.y, random.randint(0, 360), 15)
                                entities.append(e2)
                if a.name == "player" and b.name == "asteroid":
                    if is_collide(a, b):
                        b.life = False
                        # Create explosion for the ship
                        e = Entity()
                        e.settings(sExplosion_ship, a.x, a.y)
                        e.name = "explosion"
                        entities.append(e)
                        # Reset player to center
                        p.settings(sPlayer, W // 2, H // 2, 0, 20)
                        p.dx = 0
                        p.dy = 0

        # Update player animation based on thrust state
        if p.thrust:
            p.anim = sPlayer_go
        else:
            p.anim = sPlayer

        # Mark explosion animations as dead when finished
        for e in entities:
            if e.name == "explosion":
                if e.anim.is_end():
                    e.life = False

        # Occasionally add new asteroids
        if random.randint(0, 149) == 0:
            a = Asteroid()
            a.settings(sRock, 0, random.randint(0, H), random.randint(0, 360), 25)
            entities.append(a)

        # Update entities and remove dead ones
        for e in entities:
            e.update()
            e.anim.update()
        entities = [e for e in entities if e.life]

        # Draw everything
        screen.blit(background, (0, 0))
        for e in entities:
            e.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
