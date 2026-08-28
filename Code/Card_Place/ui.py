# ui.py 存放所有与画面绘制相关的工具（按钮、浮动文字、字体、图片缓存）。
import pygame
from pathlib import Path
from config import *

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 提前初始化字体模块
pygame.font.init()

try:
    font = pygame.font.SysFont("SimHei", 18, bold=True)
    title_font = pygame.font.SysFont("SimHei", 24, bold=True)
    large_font = pygame.font.SysFont("SimHei", 32, bold=True)
except:
    font = pygame.font.Font(None, 18)
    title_font = pygame.font.Font(None, 24)
    large_font = pygame.font.Font(None, 32)

IMAGE_CACHE = {} 

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
        img = pygame.transform.smoothscale(img, size)
    else:
        img = pygame.Surface(size)
        img.fill((223, 230, 233)) 
        pygame.draw.rect(img, (178, 190, 195), (0, 0, size[0], size[1]), 3)
        
    IMAGE_CACHE[cache_key] = img
    return img

class FloatingText:
    def __init__(self, x, y, text, color):
        self.x, self.y, self.text, self.color, self.life = x, y, text, color, 40
    def update_and_draw(self, surface):
        self.y -= 1.5
        self.life -= 1
        img = large_font.render(self.text, True, self.color)
        surface.blit(img, (self.x, self.y))

class Button:
    def __init__(self, x, y, w, h, text, color=SHADOW_COLOR, text_color=BLACK):
        self.rect = pygame.Rect(x, y, w, h)
        self.text, self.base_color, self.text_color = text, color, text_color
        self.radius = 8
        
    def update_text(self, new_text): self.text = new_text
        
    def draw(self, surface, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        color = tuple(min(255, c + 25) for c in self.base_color) if hovered else self.base_color
        pygame.draw.rect(surface, (150, 160, 170), (self.rect.x, self.rect.y+4, self.rect.w, self.rect.h), border_radius=self.radius)
        pygame.draw.rect(surface, color, self.rect, border_radius=self.radius)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=self.radius)
        text_img = font.render(self.text, True, self.text_color)
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
    alpha_color = (231, 76, 60, 100) # 这里的 100 可以根据你的喜好调整
    
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
