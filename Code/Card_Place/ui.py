# ui.py 存放所有与画面绘制相关的工具（按钮、浮动文字、字体、图片缓存）。
import pygame
from pathlib import Path
from config import *
from models import Character
from functools import lru_cache
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ART_DIR = PROJECT_ROOT / "art"  # 与 Free 共用项目根目录下的美术资源。
ILLUSTRATED_DIR = ART_DIR / "illustrated"
# 角色名称直接对应立绘与四帧动作图集的文件名。
CINEMATIC_POSES = ART_DIR / "cinematic" / "poses"
BATTLE_LOG_RECT = pygame.Rect(18, 741, WIDTH - 36, 48)
IMPACT_POINT = 0.52
LAUNCH_POINT = 0.22

# 提前初始化字体模块
pygame.font.init()

# 按系统中实际存在的中文字体选择，避免英文默认字体显示方框。
font_name = pygame.font.match_font("microsoftyahei,simhei,notosanscjk,arialunicode", bold=True)
font = pygame.font.Font(font_name, 18)
title_font = pygame.font.Font(font_name, 24)
large_font = pygame.font.Font(font_name, 34)
small_font = pygame.font.Font(font_name, 14)

IMAGE_CACHE = {} 


class GameWindow:
    """用固定设计画布绘制，显示和鼠标命中共用同一个等比缩放区域。"""

    def __init__(self):
        self.display = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT)).convert()

    @property
    def viewport(self):
        # Pygame 2 会随窗口拖动更新显示面，不需要每次 resize 都重建窗口。
        bounds = self.display.get_rect()
        ratio = min(bounds.width / WIDTH, bounds.height / HEIGHT)
        rect = pygame.Rect(0, 0, max(1, round(WIDTH * ratio)), max(1, round(HEIGHT * ratio)))
        rect.center = bounds.center
        return rect

    def to_game(self, pos):
        rect = self.viewport
        # 留白区自然映射到画布外，避免点到游戏边缘的按钮。
        return ((pos[0] - rect.x) * WIDTH // rect.width,
                (pos[1] - rect.y) * HEIGHT // rect.height)

    def pointer_event(self, event):
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            return event
        data = event.dict.copy()
        data["pos"] = self.to_game(event.pos)
        if event.type == pygame.MOUSEMOTION:
            # 用前后两点换算拖动距离，慢速拖动也不会因逐帧取整而丢失位移。
            previous = self.to_game((event.pos[0] - event.rel[0], event.pos[1] - event.rel[1]))
            data["rel"] = (data["pos"][0] - previous[0], data["pos"][1] - previous[1])
        return pygame.event.Event(event.type, data)

    def present(self):
        rect = self.viewport
        if rect.size != self.display.get_size():
            self.display.fill((12, 18, 30))
        if rect.size == self.canvas.get_size():
            self.display.blit(self.canvas, rect)
        else:
            # 直接缩放到显示面的可视区域，避免每帧分配全屏大小的临时图片。
            pygame.transform.smoothscale(self.canvas, rect.size, self.display.subsurface(rect))
        pygame.display.flip()


def load_image(filepath, size=(180, 240)):
    image_path = Path(filepath)
    if not image_path.is_absolute():
        cwd_path = Path.cwd() / image_path
        image_path = cwd_path if cwd_path.exists() else PROJECT_ROOT / image_path

    cache_key = (str(image_path), size)
    if cache_key in IMAGE_CACHE:
        return IMAGE_CACHE[cache_key]

    if image_path.exists():
        img = pygame.image.load(str(image_path)).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
    else:
        img = pygame.Surface(size or (90, 120))
        img.fill((223, 230, 233)) 
        pygame.draw.rect(img, (178, 190, 195), (0, 0, img.get_width(), img.get_height()), 3)
        
    IMAGE_CACHE[cache_key] = img
    return img

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y, self.text, self.color = x, y, text, color

    def draw(self, surface, progress):
        # 伤害、治疗与状态文字跟随战斗时间，暂停时也暂停。
        x, y = self.x, max(118, self.y - 35 * progress)
        face = large_font if self.text.startswith(("+", "-")) else font
        color = RED if self.text.startswith("-") and self.color == BLACK else self.color
        shadow = face.render(self.text, True, BG_COLOR)
        label = face.render(self.text, True, color)
        alpha = round(255 * min(1, (1 - progress) * 3))
        shadow.set_alpha(alpha)
        label.set_alpha(alpha)
        surface.blit(shadow, shadow.get_rect(center=(x + 1, y + 2)))
        surface.blit(label, label.get_rect(center=(x, y)))

class Button:
    def __init__(self, x, y, w, h, text, color=SHADOW_COLOR, text_color=BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.text, self.base_color, self.text_color = text, color, text_color
        self.radius = 8
        
    def update_text(self, new_text): self.text = new_text
        
    def draw(self, surface, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        accent = self.base_color if self.base_color not in (WHITE, SHADOW_COLOR) else GOLD
        amount = 0.28 if hovered else 0.13
        color = tuple(round(base + (highlight - base) * amount)
                      for base, highlight in zip(PANEL_COLOR, accent))
        pygame.draw.rect(surface, BG_COLOR, self.rect.move(0, 3), border_radius=self.radius)
        pygame.draw.rect(surface, color, self.rect, border_radius=self.radius)
        pygame.draw.rect(surface, accent if hovered else SHADOW_COLOR, self.rect, 1,
                         border_radius=self.radius)
        pygame.draw.line(surface, accent, (self.rect.left + 10, self.rect.top + 2),
                         (self.rect.right - 10, self.rect.top + 2))
        text_img = font.render(self.text, True, BLACK)
        surface.blit(text_img, text_img.get_rect(center=self.rect.center))
        
    def is_clicked(self, pos): return self.rect.collidepoint(pos)

def draw_text(surface, text, x, y, color=BLACK, use_title_font=False, center=False):
    f = title_font if use_title_font else font
    img = f.render(text, True, color)
    if center: surface.blit(img, img.get_rect(center=(x, y)))
    else: surface.blit(img, (x, y))

def wrap_text_lines(text, max_width, use_title_font=False):
    f = title_font if use_title_font else font
    if not text:
        return [""]
    if max_width <= 0:
        return [text]

    wrapped_lines = []
    current_line = ""

    for char in text:
        test_line = current_line + char
        if current_line and f.render(test_line, True, BLACK).get_width() > max_width:
            wrapped_lines.append(current_line)
            current_line = char
        else:
            current_line = test_line

    if current_line:
        wrapped_lines.append(current_line)

    return wrapped_lines

def draw_hp_bar(surface, x, y, w, h, current_hp, max_hp):
    ratio = max(0, current_hp) / max_hp
    pygame.draw.rect(surface, DARK_GRAY, (x, y, w, h), border_radius=4)
    if ratio > 0: pygame.draw.rect(surface, GREEN if ratio > 0.3 else RED, (x, y, int(w * ratio), h), border_radius=4)
    pygame.draw.rect(surface, BLACK, (x, y, w, h), 2, border_radius=4)
    draw_text(surface, f"{max(0, current_hp)}/{max_hp}", x + w//2, y + h//2, WHITE, center=True)

def draw_hero_tag(surface, x, y, tag_text):
    # 1. 渲染文字
    tag_img = font.render(tag_text, True, WHITE)
    tag_w, tag_h = tag_img.get_width() + 10, tag_img.get_height() + 6
    
    # 2. 创建一个带透明度的 Surface (SRCALPHA 标志是关键)
    # 尺寸与原本的矩形一致
    tag_bg = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
    
    # 3. 填充颜色，最后的 100 就是透明度 (0-255，数值越小越透明)
    alpha_color = (*BLUE, 255) # 不透明深蓝标签保证白字对比度
    
    # 画带圆角的矩形到这个透明层上
    pygame.draw.rect(tag_bg, alpha_color, (0, 0, tag_w, tag_h), border_bottom_right_radius=8, border_top_left_radius=4)
    
    # 4. 将透明背景层贴到主屏幕上
    surface.blit(tag_bg, (x, y))
    
    # 5. 最后把不透明的文字贴上去
    surface.blit(tag_img, (x + 5, y + 3))

def wrap_text_segments(segments, max_width):
    """
    将单行多段带颜色的文本(segments)拆分为多行，以适应 max_width 宽度
    """
    if not segments: 
        return [[]]
        
    wrapped_lines = []
    current_line = []
    current_w = 0
    
    for text, color in segments:
        # 预判：如果这一整段文字加起来没超宽，直接塞入当前行
        seg_w = font.render(text, True, color).get_width()
        if current_w + seg_w <= max_width:
            current_line.append((text, color))
            current_w += seg_w
        else:
            # 超宽了：需要逐字检测并进行切分
            current_text = ""
            for char in text:
                char_w = font.render(char, True, color).get_width()
                # 如果加上这个字还能放下
                if current_w + char_w <= max_width:
                    current_text += char
                    current_w += char_w
                else:
                    # 放不下了，把当前凑齐的文字归入当前行，并开启新的一行
                    if current_text:
                        current_line.append((current_text, color))
                    wrapped_lines.append(current_line)
                    
                    # 重新初始化新行
                    current_line = []
                    current_text = char
                    current_w = char_w
            
            # 把段落切分后剩余的尾巴加到当前行
            if current_text:
                current_line.append((current_text, color))
                
    # 把最后一行也加进去
    if current_line:
        wrapped_lines.append(current_line)
        
    return wrapped_lines


@lru_cache(maxsize=128)
def rendered_label(text, color, small=False):
    face = small_font if small else font
    return face.render(text, True, color)


def draw_panel(surface, rect, color=PANEL_COLOR, border=SHADOW_COLOR):
    """所有场景共用的暖金细边、象牙白底和切角装饰。"""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, color, rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, 1, border_radius=10)
    for x in (rect.left + 12, rect.right - 12):
        y = rect.top + 1
        pygame.draw.polygon(surface, border, ((x - 4, y), (x, y + 3), (x + 4, y)))


@lru_cache(maxsize=1)
def backdrop():
    # 渐变只在初始化时生成一次，通用页面和战场边缘使用同一底色。
    background = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        weight = (1 - y / HEIGHT) * 0.75
        color = tuple(round(a + (b - a) * weight) for a, b in zip(BG_COLOR, PANEL_COLOR))
        pygame.draw.line(background, color, (0, y), (WIDTH, y))
    # 缓存淡色魔法圆环与星点纹饰，丰富留白且不影响文字阅读。
    ornament = (190, 208, 225)
    for center in ((70, 520), (WIDTH - 65, 220)):
        for radius in (120, 145, 190):
            pygame.draw.circle(background, ornament, center, radius, 1)
        for i in range(12):
            angle = i * math.tau / 12
            x, y = round(center[0] + 145 * math.cos(angle)), round(center[1] + 145 * math.sin(angle))
            pygame.draw.polygon(background, (181, 163, 122), ((x, y-4), (x+3, y), (x, y+4), (x-3, y)), 1)
    return background


@lru_cache(maxsize=1)
def arena_background():
    rect = pygame.Rect(0, 100, WIDTH, 636)
    path = ILLUSTRATED_DIR / "arena.png"
    if path.exists():
        arena = load_image(path, rect.size).convert()
    else:
        arena = pygame.Surface(rect.size)
        arena.fill((27, 44, 56))
    pygame.draw.rect(arena, SHADOW_COLOR, arena.get_rect(), 1)
    return arena, rect


@lru_cache(maxsize=152)
def atlas_frame(key, pose="idle"):
    # 四个关键姿势使用原始高清图集，在加载时分格并按透明边缘确定轮廓。
    path = CINEMATIC_POSES / f"{key}.png"
    atlas = load_image(path, None)
    column, row = {"idle": (0, 0), "prepare": (1, 0),
                   "release": (0, 1), "hit": (1, 1)}[pose]
    width, height = atlas.get_width() // 2, atlas.get_height() // 2
    frame = atlas.subsurface((column * width, row * height, width, height)).copy()
    # alpha 阈值仅用于排除背景微弱噪声，人物内部的透明度及边缘仍使用原图。
    opaque = pygame.mask.from_surface(frame, 110)
    largest = opaque.connected_component()
    silhouette = pygame.mask.Mask(frame.get_size())
    # 保留独立的光环、法器和尾鳍；只排除面积很小的游离背景噪声。
    for component in opaque.connected_components(max(48, largest.count() // 600)):
        silhouette.draw(component, (0, 0))
    clean = silhouette.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(255, 255, 255, 0))
    frame.blit(clean, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    bounds = frame.get_bounding_rect(min_alpha=110)
    return frame.subsurface(bounds).copy() if bounds else frame


def display_art(name):
    # 展示立绘独立于动作图集，放大查看不再使用四宫格中的小图。
    return load_image(ART_DIR / "cinematic" / "portraits" / f"{name}.png", None)


@lru_cache(maxsize=64)
def load_portrait(name, size):
    portrait = pygame.Surface(size, pygame.SRCALPHA)
    portrait.fill((18, 33, 58))
    sprite = fit_image(display_art(name), size[0] - 8, size[1] - 4)
    portrait.blit(sprite, sprite.get_rect(midbottom=(size[0] // 2, size[1])))
    return portrait


def fit_image(image, width, height):
    factor = min(width / image.get_width(), height / image.get_height())
    size = (max(1, round(image.get_width() * factor)),
            max(1, round(image.get_height() * factor)))
    return pygame.transform.smoothscale(image, size)


@lru_cache(maxsize=256)
def battle_sprite(name, pose, depth, is_enemy):
    image = atlas_frame(name, pose)
    # 以待机身体高度确定同一角色的比例，出招弯腰时不会被错误拉高。
    idle = atlas_frame(name)
    height = 189 + depth * 14
    factor = min(height / idle.get_height(), 238 / idle.get_width())
    sprite = pygame.transform.smoothscale(image, (
        max(1, round(image.get_width() * factor)),
        max(1, round(image.get_height() * factor))))
    # 动作原图统一朝右，敌方在绘制时水平翻转。
    return pygame.transform.flip(sprite, True, False) if is_enemy else sprite


def action_style(hero, action):
    # 控制和减益同样是对敌行动，不用“是否造成伤害”判断攻击距离。
    hostile = action and any(t[0] != action.actor[0] for t in action.targets)
    return HERO_CONFIG[hero.name]["presentation"]["style"] if hostile else "support"


def actor_offset(hero, slot, enemy, action, progress):
    # 近战普攻和技能共享接近、停留命中、回位路径；远程及辅助留在原位。
    if not action or action.controlled or action.actor != slot or action_style(hero, action) != "melee":
        return 0, 0
    target = next(t for t in action.targets if t[0] != slot[0])
    dx, dy = attack_distance(slot, target, enemy)
    if progress < 0.12:
        amount = 0
    elif progress < IMPACT_POINT:
        t = (progress - 0.12) / (IMPACT_POINT - 0.12)
        amount = t * t * (3 - 2 * t)
    elif progress < 0.62:
        amount = 1
    else:
        t = min(1, (progress - 0.62) / 0.28)
        amount = 1 - t * t * (3 - 2 * t)
    return round(dx * amount), round(dy * amount)


def sprite_pose(hero, slot, depth, enemy, elapsed, action, progress, hp):
    # 面向校准在 battle_sprite 内完成，运动与投射物共用同一命中时间。
    direction = -1 if enemy else 1
    pose, previous, blend = "idle", None, 1
    acting = action and action.actor == slot and not action.controlled
    hit = action and slot in action.hits and IMPACT_POINT <= progress < 0.84
    move_x, move_y = actor_offset(hero, slot, enemy, action, progress)
    if hit:
        pose = "hit"
        push = math.sin(math.pi * (progress - IMPACT_POINT) / (0.84 - IMPACT_POINT))
        move_x -= round(direction * 25 * push)
        if progress < IMPACT_POINT + 0.05:
            previous, blend = "idle", (progress - IMPACT_POINT) / 0.05
    elif acting:
        release = IMPACT_POINT - 0.08 if action_style(hero, action) == "melee" else LAUNCH_POINT
        if progress < release:
            pose = "prepare"
            if progress < 0.06:
                previous, blend = "idle", progress / 0.06
        elif progress < 0.8:
            # 新辅助动作专为治疗、增益和复活绘制，原地也展示释放帧。
            pose = "release"
            if progress < release + 0.05:
                previous, blend = "prepare", (progress - release) / 0.05
        elif progress < 0.9:
            previous = "release"
            blend = (progress - 0.8) / 0.1
    sprite = battle_sprite(hero.name, pose, depth, enemy)
    if previous:
        sprite = blend_pose(battle_sprite(hero.name, previous, depth, enemy), sprite, blend)
    if hp <= 0 and not hit:
        sprite = pygame.transform.rotozoom(sprite, -direction * 64, 0.8)
        sprite.set_alpha(80)
    elif pose == "idle":
        breath = math.sin(elapsed / 405 + depth * 1.2)
        sprite = pygame.transform.smoothscale(sprite, (sprite.get_width(), max(1, round(sprite.get_height() * (1 + .008 * breath)))))
        if hero.name in {"五灵龙神", "光明神王", "极光神使", "七彩鲲鹏", "女武神", "无相菩萨", "人鱼公主"}:
            move_y -= round(8 - breath * 5)
    return sprite, move_x, move_y


def blend_pose(previous, current, amount):
    width = max(previous.get_width(), current.get_width())
    height = max(previous.get_height(), current.get_height())
    frame = pygame.Surface((width, height), pygame.SRCALPHA)
    for image, opacity in ((previous, 1 - amount), (current, amount)):
        layer = image.copy()
        layer.set_alpha(round(max(0, min(1, opacity)) * 255))
        frame.blit(layer, layer.get_rect(midbottom=(width // 2, height)))
    return frame


def attack_distance(slot, target, enemy):
    x, y = battle_position(slot[1], enemy)
    tx, ty = battle_position(target[1], target[0] == "enemy")
    return tx - x + (84 if enemy else -84), ty - y


@lru_cache(maxsize=32)
def light_sprite(color, radius):
    # 缓存柔光贴图，通过加色混合呈现光晕，避免逐帧读取资源。
    light = pygame.Surface((radius * 2, radius * 2))
    for ring in range(radius, 0, -1):
        strength = (1 - ring / radius) ** 2
        tint = tuple(round(value * strength * 0.8) for value in color)
        pygame.draw.circle(light, tint, (radius, radius), ring)
    return light


def add_light(surface, position, color, radius):
    light = light_sprite(color, radius)
    surface.blit(light, light.get_rect(center=position), special_flags=pygame.BLEND_RGB_ADD)


def draw_projectile(surface, point, unit, kind, color, travel):
    # 局部坐标沿飞行方向旋转，敌我双方及斜向弹道共用同一套造型。
    normal = pygame.Vector2(-unit.y, unit.x)
    if kind == "ice":
        tip, rear = point + unit * 19, point - unit * 17
        pygame.draw.polygon(surface, color, [tip, point + normal * 8, rear, point - normal * 8])
        pygame.draw.aaline(surface, WHITE, rear, tip)
        return
    if kind == "poison":
        for index, size in enumerate((10, 7, 5, 3)):
            sway = math.sin(travel * 12 + index * 2) * index * 3
            bubble = point - unit * index * 10 + normal * sway
            pygame.draw.circle(surface, color, bubble, size)
            pygame.draw.circle(surface, WHITE, bubble - normal * size * .4, 2)
        return
    if kind == "shadow":
        for index, size in enumerate((12, 8, 5)):
            echo = point - unit * index * 16 + normal * math.sin(travel * 9 + index) * index * 3
            pygame.draw.circle(surface, (35, 23, 52), echo, size)
            pygame.draw.circle(surface, color, echo, size, 2)
        return
    if kind == "blade":
        # 两条相接的弧线形成月牙，凸面始终朝向飞行方向。
        outer, inner = [], []
        for step in range(-12, 13):
            t = step / 12
            bend = 1 - t * t
            offset = point + normal * (29 * t)
            outer.append(offset + unit * (26 * bend - 13))
            inner.append(offset + unit * (15 * bend - 13))
        pygame.draw.polygon(surface, color, outer + inner[::-1])
        # 刃缘稍微提亮，保留角色自身的金色或冰蓝色。
        edge = tuple(round(channel + (255 - channel) * .38) for channel in color)
        pygame.draw.aalines(surface, edge, False, outer)
        return
    tail = point - unit * (38 if kind == "arrow" else 24)
    pygame.draw.line(surface, color, tail, point, 3)
    if kind == "arrow":
        pygame.draw.polygon(surface, WHITE, [point + unit * 9, point - unit * 9 + normal * 5, point - unit * 9 - normal * 5])
    elif kind == "wave":
        pygame.draw.circle(surface, color, point, 12, 2)
        pygame.draw.circle(surface, WHITE, point, 6, 1)
    else:
        add_light(surface, point, color, 24 if kind == "fire" else 16)
        pygame.draw.circle(surface, WHITE, point, 4)


def draw_attack_impact(surface, center, kind, color, burst, facing):
    # 穿刺和爪痕随攻方镜像；碎冰、毒雾向外扩散，暗影向中心收缩。
    radius = 18 + round(burst * 55)
    width = max(1, round(5 * (1 - burst)))
    if kind == "slash":
        rect = pygame.Rect(0, 0, radius * 2, radius * 2)
        rect.center = center
        start = -.8 if facing == 1 else math.pi - 2.2
        pygame.draw.arc(surface, color, rect, start, start + 3, width)
    elif kind in {"thrust", "claw"}:
        direction = pygame.Vector2(facing, -.35 if kind == "thrust" else .85).normalize()
        normal = pygame.Vector2(-direction.y, direction.x)
        for offset in ((-11, 0, 11) if kind == "claw" else (0,)):
            middle = center + normal * offset
            pygame.draw.polygon(surface, color, [middle - direction * radius,
                                middle + normal * width, middle + direction * radius, middle - normal * width])
    elif kind == "collapse":
        pygame.draw.circle(surface, color, center, max(2, round(52 * (1 - burst))), 2)
        pygame.draw.circle(surface, (39, 22, 54), center, 3 + round(8 * burst))
    else:
        if kind == "spark":
            pygame.draw.circle(surface, color, center, radius, 2)
        for index in range(8):
            ray = pygame.Vector2(1, 0).rotate(index * 45)
            tip = center + ray * radius
            base = center + ray * radius * .65
            if kind == "shatter":
                side = pygame.Vector2(-ray.y, ray.x) * width
                pygame.draw.polygon(surface, color, [tip, base + side, base - ray * 5, base - side])
            elif kind == "mist":
                cloud = center + ray * radius * (.65 + .18 * (index % 2))
                pygame.draw.circle(surface, color, cloud, 5 + round(burst * 8), width)
            else:
                pygame.draw.line(surface, color, base, tip, 2)


def draw_effects(surface, game, action, progress):
    if not action or action.controlled or not action.targets or progress > 0.86:
        return
    enemy = action.actor[0] == "enemy"
    party = game.enemy_party if enemy else game.deployed_party
    hero = party[action.actor[1]]
    # 颜色、弹道与命中形状均从当前角色的配置读取。
    presentation = HERO_CONFIG[hero.name]["presentation"]
    color = presentation["color"]
    projectile = presentation.get("projectile", "bolt")
    x, feet = battle_position(action.actor[1], enemy)
    y = feet - 110
    style = action_style(hero, action)
    # 根据本次实际释放技能选择辅助符号，仅改变演出，不参与任何结算。
    skill = next((s for s in hero.skills if s["name"] == action.skill), {})
    effects = skill.get("effects", [])
    kinds = {effect.get("type") for effect in effects}
    # 近战特效起点跟随身体；远程的箭矢和法术在命中前抵达目标。
    dx, dy = actor_offset(hero, action.actor, enemy, action, progress)
    idle = battle_sprite(hero.name, "idle", action.actor[1] % 3, enemy)
    # 发射点贴近弓或施法手的高度，镜像后偏移方向也一起反转。
    hand_height = .82 if projectile == "arrow" else .65
    hand_x = (-1 if enemy else 1) * min(58, idle.get_width() * .3)
    origin = pygame.Vector2(x + dx + hand_x, feet + dy - idle.get_height() * hand_height)
    if progress < IMPACT_POINT:
        if progress < LAUNCH_POINT:
            add_light(surface, origin, color, 35 + round(progress * 80))
        elif style == "ranged":
            travel = (progress - LAUNCH_POINT) / (IMPACT_POINT - LAUNCH_POINT)
            for target in action.targets:
                tx, ty = battle_position(target[1], target[0] == "enemy")
                end = pygame.Vector2(tx, ty - 110)
                point = origin.lerp(end, travel)
                vector = end - origin
                unit = vector.normalize() if vector.length_squared() else pygame.Vector2(1, 0)
                draw_projectile(surface, point, unit, projectile, color, travel)
        return
    burst = min(1, (progress - IMPACT_POINT) / (0.86 - IMPACT_POINT))
    for target in action.targets:
        tx, ty = battle_position(target[1], target[0] == "enemy")
        ty -= 110
        tint = GREEN if target[0] == action.actor[0] and "heal" in kinds else color
        radius = 18 + round(burst * 55)
        add_light(surface, (tx, ty), tint, max(8, round(60 * (1 - burst))))
        if style == "support":
            pygame.draw.circle(surface, tint, (tx, ty), radius, 2)
            # 治疗、护盾和增益直接在友方身上显现，不朝友军挥刀或冲锋。
            pygame.draw.ellipse(surface, tint, (tx - radius, ty + 90, radius * 2, radius // 2), 2)
            if "resurrect" in kinds:
                for offset in (-16, 0, 16):
                    pygame.draw.line(surface, GOLD, (tx+offset,ty+60), (tx+offset,ty-65-round(burst*45)), 2)
                pygame.draw.ellipse(surface,GOLD,(tx-26,ty-60,52,16),2)
            elif "heal" in kinds:
                lift=round(burst*45)
                for offset in (-22,22):
                    pygame.draw.line(surface,tint,(tx+offset-7,ty-lift),(tx+offset+7,ty-lift),3)
                    pygame.draw.line(surface,tint,(tx+offset,ty-lift-7),(tx+offset,ty-lift+7),3)
            elif "immune" in kinds:
                pygame.draw.ellipse(surface,tint,(tx-36,ty-62,72,132),2)
            elif any("def" in effect.get("stat","") for effect in effects):
                pygame.draw.polygon(surface,tint,((tx,ty-34),(tx+27,ty-22),(tx+21,ty+18),(tx,ty+36),(tx-21,ty+18),(tx-27,ty-22)),3)
            else:
                for offset in (-22,0,22):
                    pygame.draw.lines(surface,tint,False,((tx+offset-8,ty+8),(tx+offset,ty-8),(tx+offset+8,ty+8)),2)
        else:
            draw_attack_impact(surface, pygame.Vector2(tx, ty), presentation["impact"],
                               tint, burst, -1 if enemy else 1)



def skill_banner_rect(action):
    # 技能名的实际绘制区域也是悬停区域，多技能角色按本次行动显示。
    if action and action.skill:
        width = rendered_label(action.skill, GOLD).get_width() + 44
        return pygame.Rect(WIDTH // 2 - width // 2, 104, width, 32)
    return pygame.Rect(0, 0, 0, 0)


@lru_cache(maxsize=128)
def skill_description_lines(description):
    return wrap_text_lines(description, 404)


@lru_cache(maxsize=16)
def ready_ring(phase):
    # 缓存十六级呼吸亮度，厚金边和四个刻度在明暗地面上都能辨认。
    ring = pygame.Surface((150, 36), pygame.SRCALPHA)
    strength = phase / 15
    for inset, color, width in (
        (0, (255, 170, 38, 45 + round(45 * strength)), 5),
        (5, (85, 42, 16, 230), 5),
        (6, (255, 194 + round(36 * strength), 67, 255), 3),
        (12, (255, 243, 172, 220), 2),
    ):
        pygame.draw.ellipse(ring, color, (inset, inset // 3, 150 - 2 * inset, 36 - 2 * (inset // 3)), width)
    for x, y in ((5, 18), (145, 18), (75, 4), (75, 32)):
        pygame.draw.polygon(ring, (255, 251, 207), ((x-4, y), (x, y-3), (x+4, y), (x, y+3)))
    return ring


def skill_dim_amount(action, progress):
    # 只在实际释放技能时淡入暗幕，命中后逐渐恢复亮度。
    if not action or not action.skill or action.controlled:
        return 0
    return round(154 * max(0, min(1, progress / .12, (1 - progress) / .16)))


def dim_region(surface, rect, amount):
    # 直接乘以亮度系数，避免在每个动画帧创建全屏半透明图层。
    level = 255 - amount
    surface.fill((level, level, level), rect, special_flags=pygame.BLEND_RGB_MULT)


def draw_battlefield(surface, game, elapsed, action, progress, before, floating_texts, mouse):
    arena, rect = arena_background()
    surface.blit(arena, rect)
    previous_clip = surface.get_clip()
    surface.set_clip(rect)
    figures, plates = [], []
    dim = skill_dim_amount(action, progress)
    caster = None
    hover = None
    for enemy, party in ((False, game.deployed_party), (True, game.enemy_party)):
        for index, hero in enumerate(party):
            if not hero:
                continue
            x, y = battle_position(index, enemy)
            slot = ("enemy" if enemy else "ally", index)
            hp, stun, immune, ready = before.get(slot, (hero.current_hp, hero.stun_turns,
                                                       hero.immune_turns, hero.skill_ready_highlight))
            accent = RED if enemy else GREEN
            # 软阴影与细薄地面光环帮助人物落地。
            shadow = pygame.Surface((156, 32), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (6, 8, 22, 100), shadow.get_rect())
            surface.blit(shadow, (x - 78, y - 14))
            if ready and hp > 0:
                phase = round(7.5 * (1 + math.sin(elapsed * .006)))
                ring = ready_ring(phase)
                surface.blit(ring, ring.get_rect(center=(x, y)))
            sprite, dx, dy = sprite_pose(hero, slot, index % 3, enemy, elapsed, action, progress, hp)
            draw_rect = sprite.get_rect(midbottom=(x + dx, y + dy))
            if dim and slot == action.actor:
                caster = sprite, draw_rect
            else:
                figures.append((y + dy, sprite, draw_rect))
            idle = battle_sprite(hero.name, "idle", index % 3, enemy)
            # 血条跟随人物位移，位置按站立身高保持稳定。
            bar_y = max(rect.top + 30, y + dy - idle.get_height() - 20)
            plates.append((x + dx, bar_y, hp, hero.max_hp, accent, stun, immune))
            if draw_rect.collidepoint(mouse):
                hover = hero, hp, enemy

    for _, sprite, draw_rect in sorted(figures, key=lambda item: item[0]):
        surface.blit(sprite, draw_rect)
    if not dim:
        draw_effects(surface, game, action, progress)
    for x, y, hp, max_hp, accent, stun, immune in plates:
        ratio = max(0, min(1, hp / max_hp))
        pygame.draw.polygon(surface, GOLD, ((x - 49, y), (x + 50, y),
                            (x + 45, y + 10), (x - 51, y + 10)), 1)
        pygame.draw.rect(surface, (19, 23, 37), (x - 47, y + 2, 91, 6))
        if ratio:
            pygame.draw.rect(surface, accent, (x - 47, y + 2, max(1, round(91 * ratio)), 6))
            pygame.draw.line(surface, WHITE, (x - 47, y + 2), (x - 47 + round(90 * ratio), y + 2))
        if stun or immune:
            # 不同状态使用不同配色，统一绘制底色、边框和文字。
            if stun:
                text, background, border = "控", (58, 25, 83), (223, 181, 255)
            else:
                text, background, border = "免", (77, 52, 12), (255, 214, 112)

            label = rendered_label(text, WHITE, True)
            badge = label.get_rect().inflate(8, 2)
            badge.bottomleft = (x - 50, y - 1)

            pygame.draw.rect(surface, background, badge, border_radius=4)
            pygame.draw.rect(surface, border, badge, 1, border_radius=4)
            surface.blit(label, label.get_rect(center=badge.center))

    if progress >= IMPACT_POINT:
        for text in floating_texts:
            text.draw(surface, (progress - IMPACT_POINT) / (1 - IMPACT_POINT))
    if dim:
        # 其他角色、血条和飘字先暗化，再按原亮度绘制施法者和技能特效。
        dim_region(surface, rect, dim)
        if caster:
            surface.blit(*caster)
        draw_effects(surface, game, action, progress)
    surface.set_clip(previous_clip)
    banner = skill_banner_rect(action)
    if banner:
        name_image = rendered_label(action.skill, GOLD)
        draw_panel(surface, banner, BG_COLOR, SHADOW_COLOR)
        surface.blit(name_image, name_image.get_rect(center=banner.center))
    if banner.collidepoint(mouse):
        # 描述来自实际释放的技能，置于名称下方，以免遮挡悬停目标。
        lines = skill_description_lines(action.skill_description or "暂无技能描述")
        row_height = font.get_linesize()
        tip = pygame.Rect(0, 0, 436, 24 + len(lines) * row_height)
        tip.midtop = (banner.centerx, banner.bottom + 5)
        draw_panel(surface, tip, PANEL_COLOR, GOLD)
        for index, line in enumerate(lines):
            draw_text(surface, line, tip.x + 16, tip.y + 12 + index * row_height)
    elif hover:
        hero, hp, enemy = hover
        x = min(WIDTH - 250, max(12, mouse[0] + 18))
        y = max(140, min(630, mouse[1] - 76))
        draw_panel(surface, (x, y, 238, 70), BG_COLOR, GOLD)
        draw_text(surface, hero.name, x + 12, y + 7, RED if enemy else BLUE)
        surface.blit(rendered_label(f"生命 {max(0, hp):,} / {hero.max_hp:,}", WHITE, True), (x + 12, y + 32))
        surface.blit(rendered_label(f"攻击 {hero.atk:,}   防御 {hero.defense:,}", DARK_GRAY, True),
                     (x + 12, y + 50))


def draw_battle_log(surface, combat_log, scroll_y):
    # 简讯只占一行，滚轮可回看所有行动，结算页仍展示完整记录。
    rect = BATTLE_LOG_RECT
    draw_panel(surface, rect)
    draw_text(surface, "战报", rect.x + 16, rect.y + 12, GOLD)
    draw_text(surface, "点击查看全部", rect.right - 138, rect.y + 12, BLUE)
    lines = [line for line in combat_log if line]
    if not lines:
        return
    last = max(0, min(len(lines) - 1, len(lines) - 1 + min(0, scroll_y) // 20))
    previous_clip = surface.get_clip()
    surface.set_clip(pygame.Rect(rect.x + 76, rect.y + 4, rect.width - 230, rect.height - 8))
    x = rect.x + 78
    for text, color in lines[last]:
        label = rendered_label(text, color)
        surface.blit(label, (x, rect.y + 12))
        x += label.get_width()
    surface.set_clip(previous_clip)


class DetailViewer:
    """统一模态窗口：拦截底层操作，角色使用高清图，战报只读已发生记录。"""
    def __init__(self):
        self.kind = None
        self.panel = pygame.Rect(100, 60, 1080, 680)
        self.viewport = pygame.Rect(130, 145, 1020, 490)
        self.close_button = Button(1060, 80, 95, 38, "关闭")
        self.reset_button = Button(500, 670, 180, 40, "恢复完整显示")
        self.first_button = Button(750, 670, 180, 40, "最早记录")
        self.last_button = Button(950, 670, 180, 40, "最新记录")
        self.zoom = 1.0
        self.pan = pygame.Vector2()
        self.dragging = False
        self.scroll = 0

    def open_hero(self, hero):
        self.kind, self.title = "hero", hero.name + " · 高清立绘"
        self.source = display_art(hero.name)
        self.zoom, self.pan, self.dragging = 1.0, pygame.Vector2(), False
        self.scaled = None

    def open_log(self, game, records):
        self.kind, self.title = "log", "本场战斗 · 历史战报"
        self.was_paused = game.is_paused
        game.is_paused = True
        # 展开时快照并换行；未到命中时间的 pending_log 不提前透露。
        self.rows = []
        for line in records:
            self.rows.extend(wrap_text_segments(line, self.viewport.width - 38) if line else [[]])
        self.max_scroll = max(0, len(self.rows) * 26 - self.viewport.height)
        self.scroll = self.max_scroll

    def close(self, game):
        if self.kind == "log":
            game.is_paused = self.was_paused
        self.kind, self.dragging = None, False

    def handle(self, event, game):
        # 所有事件由主循环送入窗口，关闭事件也不穿透至底层按钮。
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.close(game)
            elif self.kind == "log":
                if event.key == pygame.K_HOME: self.scroll = 0
                elif event.key == pygame.K_END: self.scroll = self.max_scroll
                elif event.key == pygame.K_PAGEUP: self.scroll -= self.viewport.height
                elif event.key == pygame.K_PAGEDOWN: self.scroll += self.viewport.height
        elif event.type == pygame.MOUSEWHEEL:
            if self.kind == "hero":
                self.zoom = max(.25, min(6, self.zoom * 1.15 ** event.y))
                self.scaled = None
            else:
                self.scroll -= event.y * 78
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.is_clicked(event.pos):
                self.close(game)
            elif self.kind == "hero":
                if self.reset_button.is_clicked(event.pos):
                    self.zoom, self.pan, self.scaled = 1.0, pygame.Vector2(), None
                elif self.viewport.collidepoint(event.pos): self.dragging = True
            elif self.first_button.is_clicked(event.pos): self.scroll = 0
            elif self.last_button.is_clicked(event.pos): self.scroll = self.max_scroll
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.pan += pygame.Vector2(event.rel)
        if self.kind == "log": self.scroll = max(0, min(self.max_scroll, self.scroll))

    def draw(self, screen, mouse_pos):
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((25, 42, 62, 120));screen.blit(shade, (0, 0))
        draw_panel(screen, self.panel)
        draw_text(screen, self.title, 135, 90, BLUE, True)
        self.close_button.draw(screen, mouse_pos)
        pygame.draw.rect(screen, TOP_BAR_COLOR, self.viewport, border_radius=8)
        old_clip = screen.get_clip();screen.set_clip(self.viewport)
        if self.kind == "hero":
            if self.scaled is None:
                factor = min((self.viewport.width - 24) / self.source.get_width(), (self.viewport.height - 24) / self.source.get_height()) * self.zoom
                self.scaled = pygame.transform.smoothscale(self.source, (max(1, round(self.source.get_width()*factor)), max(1, round(self.source.get_height()*factor))))
            # 拖动后至少保留一部分人物可见，避免丢失画面。
            for axis, extent in enumerate(self.scaled.get_size()):
                limit = (extent + self.viewport.size[axis]) / 2 - 40
                self.pan[axis] = max(-limit, min(limit, self.pan[axis]))
            screen.blit(self.scaled, self.scaled.get_rect(center=pygame.Vector2(self.viewport.center)+self.pan))
        else:
            first = int(self.scroll // 26)
            for i in range(first, min(len(self.rows), first + self.viewport.height//26 + 2)):
                x, y = self.viewport.x + 12, self.viewport.y + i * 26 - self.scroll
                for text, color in self.rows[i]:
                    label = rendered_label(text, color);screen.blit(label,(x,y));x += label.get_width()
            if self.max_scroll:
                height = max(24, self.viewport.height ** 2 / (len(self.rows) * 26))
                y = self.viewport.y + (self.viewport.height-height) * self.scroll/self.max_scroll
                pygame.draw.rect(screen, SHADOW_COLOR, (self.viewport.right-9,y,5,height), border_radius=2)
        screen.set_clip(old_clip)
        if self.kind == "hero":
            draw_text(screen, f"滚轮缩放 · 拖动查看 · Esc 关闭  |  {self.zoom:.0%}", 135, 645, DARK_GRAY)
            self.reset_button.draw(screen, mouse_pos)
        else:
            draw_text(screen, "滚轮翻阅 · Home / End 跳转 · Esc 关闭", 135, 645, DARK_GRAY)
            self.first_button.draw(screen, mouse_pos)
            self.last_button.draw(screen, mouse_pos)


# 页面美术、角色图鉴、召唤展示和测试布阵
ROOT = ART_DIR / "cinematic"
INK = (249, 238, 211)
MUTED = (188, 205, 224)
GILT = (242, 198, 105)


def label(screen, text, x, y, color=INK, title=False, center=False):
    draw_text(screen, text, x, y, color, title, center)


@lru_cache(maxsize=3)
def scene_background(scene):
    name = {"LEVEL": "home", "HERO": "hero", "GACHA": "summon"}[scene]
    path = ROOT / "ui" / (name + ".png")
    return load_image(path, (WIDTH, HEIGHT)) if path.exists() else backdrop()


@lru_cache(maxsize=4)
def widget(index):
    path = ROOT / "ui/widgets.png"
    if not path.exists(): return None
    source = load_image(path, None)
    w, h = source.get_width()//2, source.get_height()//2
    cell = source.subsurface(((index%2)*w, (index//2)*h, w, h)).copy()
    # 按主体连通轮廓裁切按钮，排除图集中游离装饰造成的纵向压缩。
    if index in (0, 1):
        mask = pygame.mask.from_surface(cell, 100).connected_component()
        rects = mask.get_bounding_rects()
        bounds = rects[0] if rects else cell.get_bounding_rect(min_alpha=100)
    else:
        bounds = cell.get_bounding_rect(min_alpha=100)
    return cell.subsurface(bounds).copy() if bounds else cell


@lru_cache(maxsize=48)
def widget_size(index, size):
    image = widget(index)
    return pygame.transform.smoothscale(image, size) if image else None


class ArtButton(Button):
    # 文字实时渲染，图片只负责装饰；点击矩形与实际按钮始终一致。
    def draw(self, surface, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        gold = self.text.startswith(("开始", "十连", "升级", "升星")) or hovered
        art = widget_size(0 if gold else 1, self.rect.size)
        if art is None:
            super().draw(surface, mouse_pos)
            return
        surface.blit(art, self.rect)
        # 三个主导航使用独立金属徽章，文字与图标均由实际按钮承载。
        emblem = {"战斗": 0, "角色": 1, "召唤": 2}.get(self.text)
        center_x = self.rect.centerx
        if emblem is not None:
            icon = navigation_icon(emblem)
            if icon:
                surface.blit(icon, icon.get_rect(center=(self.rect.left+52,self.rect.centery)))
                center_x += 20
        face = font
        text = face.render(self.text, True, INK)
        surface.blit(face.render(self.text, True, (30, 23, 36)), text.get_rect(center=(center_x+1,self.rect.centery+1)))
        surface.blit(text, text.get_rect(center=(center_x,self.rect.centery)))


@lru_cache(maxsize=3)
def navigation_icon(index):
    path = ROOT / "ui/icons.png"
    if not path.exists():return None
    atlas = load_image(path,None)
    w,h=atlas.get_width()//2,atlas.get_height()//2
    icon=atlas.subsurface(((index%2)*w,(index//2)*h,w,h))
    return fit_image(icon,46,46)


def glass(screen, rect):
    # 深蓝半透明底与金属线条衬托场景，不用整块纯色遮住背景。
    rect = pygame.Rect(rect)
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill((12, 28, 57, 222));screen.blit(panel,rect)
    pygame.draw.rect(screen, GILT, rect, 1, border_radius=9)
    pygame.draw.rect(screen, (105, 133, 172), rect.inflate(-8,-8), 1, border_radius=7)
    for x in (rect.left+14,rect.right-14):
        for y in (rect.top+7,rect.bottom-7):
            pygame.draw.polygon(screen,GILT,((x-7,y),(x,y-4),(x+7,y),(x,y+4)),1)


def draw_header(screen, game):
    glass(screen,(20,12,275,55));glass(screen,(490,12,300,48))
    label(screen, f"第 {game.level} 关", 40, 27, GILT, True)
    label(screen,f"金币 {game.gold:,}  ·  +{game.get_idle_rate()}/秒",640,37,GILT,center=True)


# 常用展示尺寸只缩放一次，场景绘制直接复用高清立绘的缩放结果。
@lru_cache(maxsize=64)
def figure_art(name, width, height):
    return fit_image(display_art(name), width, height)


def small(screen, text, x, y, color=MUTED):
    screen.blit(rendered_label(str(text), color, True), (x, y))


def slot_rect(enemy, slot):
    # 点击和绘制共用同一阵位坐标，保留前后排的镜像关系。
    col = slot // 3 if enemy else 1 - slot // 3
    return pygame.Rect((662 if enemy else 24) + col * 301, 178 + slot % 3 * 124, 293, 112)


def draw_home(screen, game):
    # 双方前排相对，空位也保留编号，便于直接对照布阵。
    for enemy, left, title in ((False, 24, "我方阵容"), (True, 662, "敌方阵容")):
        glass(screen, (left, 112, 594, 52))
        label(screen, title, left + 22, 124, GILT, True)
        small(screen, "前排 1–3   ·   后排 4–6", left + 390, 130)
        for slot in range(6):
            rect = slot_rect(enemy, slot)
            glass(screen, rect)
            hero = None if enemy else game.deployed_party[slot]
            config = game.current_enemy_configs[slot] if enemy and slot < len(game.current_enemy_configs) else None
            if config:
                name = config["name"]
                data = HERO_CONFIG[name]
                level, star = config.get("level", 1), config.get("star", 1)
                hp, attack, defense = (Character.scale_stat(data[k], level, star) for k in ("hp", "atk", "def"))
            elif hero:
                name, level, star = hero.name, hero.level, hero.star
                hp, attack, defense = hero.max_hp, hero.atk, hero.defense
            else:
                label(screen, f"{slot + 1} 号位  ·  空位", *rect.center, MUTED, center=True)
                continue
            screen.blit(load_portrait(name, (76, 96)), (rect.x + 8, rect.y + 8))
            x, y = rect.x + 94, rect.y + 10
            label(screen, name, x, y, GILT)
            small(screen, f"{slot + 1}号位   Lv.{level}   ★{star}", x, y + 31)
            small(screen, f"生命 {hp}", x, y + 55)
            small(screen, f"攻击 {attack}    防御 {defense}", x, y + 77)


CATALOG_AREA = pygame.Rect(180, 86, 174, 580)


def draw_hero_page(screen, game, mouse_pos, clicked, buttons):
    owned = {hero.name: hero for hero in game.owned_heroes}
    names = list(HERO_CONFIG)
    start = game.catalog_offset
    label(screen, "上阵位置", 23, 92, GILT)
    label(screen, "角色图鉴", 183, 92, GILT)
    small(screen, f"{start+1}–{min(start+6,len(names))}/{len(names)}", 266, 96)
    # 阵位固定；仅图鉴列随滚轮移动，两列共享当前选中的角色。
    for column in range(2):
        for row in range(6):
            rect = pygame.Rect(18 + column * 162, 128 + row * 89, 156, 80)
            glass(screen, rect)
            if column == 0:
                hero = game.deployed_party[row]
                name = hero.name if hero else None
                caption = f"{row+1}号位 · " + ("前排" if row < 3 else "后排")
            else:
                if start + row >= len(names):
                    continue
                name = names[start + row]
                hero = owned.get(name)
                caption = f"Lv.{hero.level}  ★{hero.star}" if hero else "未获得"
            if name:
                screen.blit(load_portrait(name, (49, 66)), (rect.x+6, rect.y+7))
                if clicked and rect.collidepoint(mouse_pos):
                    game.selected_name = name
                small(screen, name, rect.x+60, rect.y+17, INK)
                small(screen, caption, rect.x+60, rect.y+44)
                if game.selected_name == name:
                    pygame.draw.rect(screen, GILT, rect, 2, border_radius=8)
            else:
                small(screen, caption, rect.x+16, rect.y+15)
                small(screen, "空位", rect.x+16, rect.y+42)
    selected = game.get_active_hero()
    figure = figure_art(selected.name, 520, 535)
    screen.blit(figure, figure.get_rect(midbottom=(608,665)))
    glass(screen,(872,100,386,565))
    label(screen,selected.name,890,119,GILT,True)
    label(screen,f"Lv.{selected.level}  ·  ★{selected.star}  ·  {selected.tag}",890,158)
    # 并列展示培养前后的数值，基础值始终直接读取角色模板的原始三项属性。
    rows = (
        ("属性", "生命", "攻击", "防御"),
        ("当前", selected.max_hp, selected.atk, selected.defense),
        ("初始（1级1星）", selected.base_hp, selected.base_atk, selected.base_def),
    )
    for row, values in enumerate(rows):
        for x, value in zip((890, 1022, 1104, 1182), values):
            small(screen, value, x, 188 + row * 20, MUTED if row == 0 else INK)
    small(screen, f"角色碎片 {selected.duplicates}" if selected.name in owned else "未获得", 890, 251)
    y = 275
    for skill in selected.skills:
        label(screen, f"{skill['name']}  ·  冷却 {skill['cooldown']} 回合",890,y,GILT)
        y += 30
        # 技能说明使用 18 像素正文字号，按实际宽度折行。
        line = ""
        for char in skill.get("desc", ""):
            if font.size(line + char)[0] > 345:
                label(screen,line,890,y,MUTED)
                line = ""
                y += 25
            line += char
        label(screen,line,890,y,MUTED)
        y += 32
    if selected.name in owned:
        for j, button in enumerate(buttons):
            button.rect = pygame.Rect(884+(j%3)*122, 523+(j//3)*44, 119, 40)
            button.draw(screen,mouse_pos)


def draw_summon(screen, items, timer, index, mouse_pos, clicked):
    if not items:
        label(screen,"星门召唤",WIDTH//2,94,GILT,True,True)
        label(screen,"与命运相遇 · 召唤你的同行者",WIDTH//2,486,INK,center=True)
        return 0
    multiple = len(items) > 1
    age = (300 if multiple else 180) - timer
    # 十连保留十个独立结果，点选已揭示卡牌可切换左侧大图。
    if multiple:
        label(screen, "十连召唤", 605, 119, GILT, True)
        for i, (name, fresh) in enumerate(items):
            rect = pygame.Rect(603 + (i%5)*128, 175 + (i//5)*202, 122, 192)
            glass(screen,rect)
            if age < 12 + 7*i:
                card = widget_size(2,(104,170))
                if card:
                    screen.blit(card,(rect.x+9,rect.y+11))
                continue
            if clicked and rect.collidepoint(mouse_pos):
                index = i
            art = figure_art(name, 108, 130)
            screen.blit(art, art.get_rect(midtop=(rect.centerx,rect.y+8)))
            label(screen,name,rect.centerx,rect.bottom-38,INK,center=True)
            small(screen,"新角色" if fresh else "碎片 +1",rect.x+34,rect.bottom-25,GILT)
            if i == index:
                pygame.draw.rect(screen,GILT,rect,3,border_radius=8)
    center = 310 if multiple else WIDTH//2
    glass(screen,(center-272,93,544,497))
    if age < 12:
        card = widget_size(2,(270,400))
        if card:
            screen.blit(card,card.get_rect(center=(center,342)))
    else:
        name, fresh = items[index]
        art = figure_art(name, 520, 426)
        screen.blit(art, art.get_rect(midbottom=(center,532)))
        label(screen,name,center,549,GILT,True,True)
        small_text = rendered_label("新角色" if fresh else "碎片 +1", MUTED, True)
        screen.blit(small_text,small_text.get_rect(center=(center,576)))
    return index


class TestPicker(DetailViewer):
    """测试布阵窗口：编辑草稿，确认后才替换指定阵位。"""

    def __init__(self):
        super().__init__()
        self.cards = {name: pygame.Rect(98 + i % 8 * 137, 141 + i // 8 * 87, 129, 80)
                      for i, name in enumerate(HERO_CONFIG)}
        self.fields = [pygame.Rect(269, 601, 94, 44), pygame.Rect(529, 601, 94, 44)]
        self.clear_slot = ArtButton(725, 600, 160, 49, "清空阵位")
        self.confirm = ArtButton(922, 600, 180, 49, "确认上阵")

    def open_slot(self, trial, enemy, slot):
        self.kind = "slot"
        self.trial, self.enemy, self.slot = trial, enemy, slot
        current = trial.current_enemy_configs[slot] if enemy else trial.deployed_party[slot]
        if current and not enemy:
            current = dict(name=current.name, level=current.level, star=current.star)
        self.name = current["name"] if current else next(iter(HERO_CONFIG))
        self.values = [str(current[k]) if current else "1" for k in ("level", "star")]
        self.field = None
        self.replace_value = False

    def apply_slot(self, clear=False):
        if not clear and not all(v and int(v) >= 1 for v in self.values):
            return
        level, star = (int(v or 1) for v in self.values)
        if self.enemy:
            self.trial.current_enemy_configs[self.slot] = None if clear else dict(name=self.name, level=level, star=star)
        else:
            hero = None
            if not clear:
                data = HERO_CONFIG[self.name]
                hero = Character(self.name, data["hp"], data["atk"], data["def"],
                                 data["tag"], data.get("skill"), data.get("skills"))
                hero.level, hero.star = level, star
                hero.reset_battle_state()
            self.trial.deployed_party[self.slot] = hero
        self.kind = None

    def handle(self, event, game):
        if self.kind != "slot":
            return super().handle(event, game)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.kind = None
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.apply_slot()
            elif self.field is not None:
                # 首次键入直接替换旧值；退格可修正，只有 1–99 才能提交。
                value = self.values[self.field]
                if event.key == pygame.K_BACKSPACE:
                    self.values[self.field] = value[:-1]
                    self.replace_value = False
                elif event.unicode in tuple("0123456789"):
                    self.values[self.field] = ((("" if self.replace_value else value) + event.unicode)[:2])
                    self.replace_value = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.close_button.is_clicked(event.pos):
                self.kind = None
            elif self.clear_slot.is_clicked(event.pos):
                self.apply_slot(clear=True)
            elif self.confirm.is_clicked(event.pos):
                self.apply_slot()
            else:
                self.field = next((i for i,r in enumerate(self.fields) if r.collidepoint(event.pos)), None)
                self.replace_value = self.field is not None
                for name, rect in self.cards.items():
                    if rect.collidepoint(event.pos):
                        self.name = name
                        break

    def draw(self, screen, mouse_pos):
        if self.kind != "slot":
            return super().draw(screen, mouse_pos)
        shade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        shade.fill((8, 15, 29, 195))
        screen.blit(shade, (0, 0))
        glass(screen,(72,62,1136,625))
        side = "敌方" if self.enemy else "我方"
        label(screen,f"{side} {self.slot+1} 号位 · 选择角色",101,85,GILT,True)
        self.close_button.draw(screen, mouse_pos)
        for name, rect in self.cards.items():
            glass(screen,rect)
            art = figure_art(name, 106, 48)
            screen.blit(art,art.get_rect(midtop=(rect.centerx,rect.top+5)))
            label(screen,name,rect.centerx,rect.bottom-16,INK,center=True)
            if name == self.name:
                pygame.draw.rect(screen,GILT,rect,3,border_radius=7)
        for i,(caption,rect) in enumerate(zip(("等级","星级"),self.fields)):
            label(screen,caption,rect.left-58,rect.y+10)
            glass(screen,rect)
            if i == self.field:
                pygame.draw.rect(screen,GILT,rect,2,border_radius=7)
            label(screen,self.values[i],*rect.center,GILT,center=True)
        small(screen,"点击数值框输入 1–99",210,654)
        for button in (self.clear_slot,self.confirm):
            button.draw(screen, mouse_pos)
