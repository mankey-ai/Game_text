# -*- coding: utf-8 -*-
import pygame
import sys
import random
import os
import math  # 新增，用于角度计算

pygame.init()

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("飞机射击游戏 - 自动发射+随机偏移")

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# ---------- 加载图片（缺失则使用默认图形）----------
try:
    player_img = pygame.image.load("./assets/player.png")
except FileNotFoundError:
    print("未找到 1.png，使用默认绿色三角形")
    player_img = pygame.Surface((50, 50), pygame.SRCALPHA)
    pygame.draw.polygon(player_img, GREEN, [(25, 0), (0, 50), (50, 50)])

try:
    enemy_img = pygame.image.load("./assets/enemy.png")
except FileNotFoundError:
    print("未找到 敌人.png，使用默认红色矩形")
    enemy_img = pygame.Surface((40, 40), pygame.SRCALPHA)
    enemy_img.fill(RED)

try:
    bullet_img = pygame.image.load("./assets/bullet.png")
except FileNotFoundError:
    print("未找到 子弹.png，使用默认亮青色矩形")
    bullet_img = pygame.Surface((10, 20), pygame.SRCALPHA)
    bullet_img.fill(CYAN)

try:
    background_img = pygame.image.load("./assets/bg.jpeg")
    background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
except FileNotFoundError:
    print("未找到 背景.jpeg，使用纯黑色背景")
    background_img = None

# 获取图片矩形
player_rect = player_img.get_rect()
player_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)

# 游戏参数
player_speed = 5
bullet_speed = 8               # 子弹速度大小（像素/帧）
player_shoot_cooldown = 10      # 每5帧自动发射一颗
shoot_timer = 0

enemy_speed = 1.8
enemy_bullet_speed = 5
enemy_bullet_lifetime = 80
enemy_spawn_interval = 60
score = 0
game_over = False

# 子弹与敌人列表
# 玩家子弹: [rect, vx, vy, rotate_angle]   (旋转角度用于pygame.transform.rotate)
player_bullets = []
enemy_bullets = []             # [rect, speed_y, lifetime]
enemies = []

clock = pygame.time.Clock()
FPS = 60
enemy_spawn_timer = 0

# 加载字体
font = None
font_paths = [
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/yahei.ttf",
]
for path in font_paths:
    if os.path.exists(path):
        font = pygame.font.Font(path, 36)
        break
if font is None:
    print("未找到中文字体，中文可能会显示为方框")
    font = pygame.font.Font(None, 36)

def reset_game():
    global player_rect, player_bullets, enemy_bullets, enemies, score, game_over, enemy_spawn_timer, shoot_timer
    player_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
    player_bullets.clear()
    enemy_bullets.clear()
    enemies.clear()
    score = 0
    game_over = False
    enemy_spawn_timer = 0
    shoot_timer = 0

def draw_text(text, x, y, color=WHITE):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

# 主循环
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
            reset_game()

    if game_over:
        screen.fill(BLACK)
        draw_text("游戏结束！", SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 - 50, RED)
        draw_text(f"最终得分：{score}", SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, WHITE)
        draw_text("按 R 键重新开始", SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 50, WHITE)
        pygame.display.flip()
        continue

    # ---------- 玩家控制（移动） ----------
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_rect.left > 0:
        player_rect.x -= player_speed
    if keys[pygame.K_RIGHT] and player_rect.right < SCREEN_WIDTH:
        player_rect.x += player_speed
    if keys[pygame.K_UP] and player_rect.top > 0:
        player_rect.y -= player_speed
    if keys[pygame.K_DOWN] and player_rect.bottom < SCREEN_HEIGHT:
        player_rect.y += player_speed

    # ---------- 玩家自动发射子弹（带冷却） ----------
    if shoot_timer <= 0:
        # 随机偏移角度（-30° ~ +30°），相对于垂直向上方向
        offset_deg = random.uniform(-10, 10)
        offset_rad = math.radians(offset_deg)
        # 计算速度分量：向上为负y，向右为正x
        vx = bullet_speed * math.sin(offset_rad)
        vy = -bullet_speed * math.cos(offset_rad)
        # 旋转图片：pygame旋转是逆时针为正，垂直向上方向需要顺时针旋转 offset_deg，所以取负
        rotate_angle = -offset_deg

        # 创建子弹矩形
        new_bullet_rect = bullet_img.get_rect()
        new_bullet_rect.centerx = player_rect.centerx
        new_bullet_rect.centery = player_rect.top  # 从玩家顶部发出

        player_bullets.append([new_bullet_rect, vx, vy, rotate_angle])
        shoot_timer = player_shoot_cooldown
    else:
        shoot_timer -= 1

    # ---------- 更新玩家子弹（移动 + 边界移除） ----------
    for bullet in player_bullets[:]:
        rect, vx, vy, _ = bullet
        rect.x += vx
        rect.y += vy
        # 如果完全离开屏幕（任意方向），移除
        if (rect.right < 0 or rect.left > SCREEN_WIDTH or
            rect.bottom < 0 or rect.top > SCREEN_HEIGHT):
            player_bullets.remove(bullet)

    # ---------- 敌人生成 ----------
    enemy_spawn_timer += 1
    if enemy_spawn_timer >= enemy_spawn_interval:
        enemy_spawn_timer = 0
        new_enemy_rect = enemy_img.get_rect()
        new_enemy_rect.x = random.randint(0, SCREEN_WIDTH - new_enemy_rect.width)
        new_enemy_rect.y = -new_enemy_rect.height
        enemies.append(new_enemy_rect)

    # ---------- 更新敌人（移动 + 发射子弹） ----------
    for enemy in enemies[:]:
        enemy.y += enemy_speed
        if random.random() < 0.15:
            enemy_bullet_rect = pygame.Rect(0, 0, 10, 15)
            enemy_bullet_rect.centerx = enemy.centerx
            enemy_bullet_rect.top = enemy.bottom
            enemy_bullets.append([enemy_bullet_rect, enemy_bullet_speed, enemy_bullet_lifetime])
        if enemy.top > SCREEN_HEIGHT:
            enemies.remove(enemy)

    # ---------- 更新敌人子弹 ----------
    for bullet in enemy_bullets[:]:
        bullet[0].y += bullet[1]
        bullet[2] -= 1
        if bullet[2] <= 0 or bullet[0].top > SCREEN_HEIGHT:
            enemy_bullets.remove(bullet)

    # ---------- 碰撞检测 ----------
    # 玩家子弹 vs 敌人
    for bullet in player_bullets[:]:
        bullet_rect = bullet[0]
        for enemy in enemies[:]:
            if bullet_rect.colliderect(enemy):
                player_bullets.remove(bullet)
                enemies.remove(enemy)
                score += 1
                break

    # 玩家 vs 敌人本体
    for enemy in enemies:
        if player_rect.colliderect(enemy):
            game_over = True
            break

    # 玩家 vs 敌人子弹
    if not game_over:
        for bullet in enemy_bullets:
            if player_rect.colliderect(bullet[0]):
                game_over = True
                break

    # ---------- 绘制画面 ----------
    if background_img:
        screen.blit(background_img, (0, 0))
    else:
        screen.fill(BLACK)

    # 绘制玩家
    screen.blit(player_img, player_rect)

    # 绘制敌人
    for enemy in enemies:
        screen.blit(enemy_img, enemy)

    # 绘制玩家子弹（旋转图片以匹配飞行方向）
    for rect, vx, vy, angle in player_bullets:
        rotated_img = pygame.transform.rotate(bullet_img, angle)
        # 旋转后图片尺寸会变，需要将新图片的中心对准子弹矩形的中心
        new_rect = rotated_img.get_rect(center=rect.center)
        screen.blit(rotated_img, new_rect)

    # 绘制敌人子弹（橙红色矩形）
    for bullet in enemy_bullets:
        pygame.draw.rect(screen, ORANGE, bullet[0])

    # 显示信息
    draw_text(f"得分: {score}", 10, 10)
    draw_text(f"用上下左右移动", 10, 50)


    pygame.display.flip()

pygame.quit()