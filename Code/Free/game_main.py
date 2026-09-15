# 游戏主程序

import sys
import os
import warnings
from pathlib import Path
# 忽略特定的警告
warnings.filterwarnings('ignore', category=UserWarning, message='.*pkg_resources.*')
warnings.filterwarnings('ignore', category=UserWarning, message='.*iCCP.*')
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import copy
import battle
import data
from battle import identity_LEVELS, Character_battle_data, calculate_stats_by_level, VideoPlayer
from data import get_location_character_map, Location_background_map, Background_file_map


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PICTURE_DIR = PROJECT_ROOT / "picture"


SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 900
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_PLAYER = (0, 255, 0)
COLOR_ENEMY = (255, 0, 0)


def wrap_text_by_char(text, font, max_width):
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    lines.append(current_line)
    return lines


class BattleManager:
    def __init__(self):
        self.player_team = []
        self.enemy_team = []
        self.is_selection_mode_active = False

    def toggle_selection_mode(self):
        self.is_selection_mode_active = not self.is_selection_mode_active
        if not self.is_selection_mode_active:
            self.clear_teams()

    def _get_char_name(self, char_data):
        if 'stats' in char_data:
            return char_data['stats'].get('姓名')
        return char_data.get('姓名')

    def add_to_player_team(self, char_data):
        self.remove_from_teams(char_data)
        self.player_team.append(char_data)

    def add_to_enemy_team(self, char_data):
        self.remove_from_teams(char_data)
        self.enemy_team.append(char_data)

    def remove_from_teams(self, char_data):
        char_name = self._get_char_name(char_data)
        self.player_team = [p for p in self.player_team if self._get_char_name(p) != char_name]
        self.enemy_team = [e for e in self.enemy_team if self._get_char_name(e) != char_name]

    def is_character_selected(self, char_data):
        char_name = self._get_char_name(char_data)
        if any(self._get_char_name(p) == char_name for p in self.player_team):
            return 'player'
        if any(self._get_char_name(e) == char_name for e in self.enemy_team):
            return 'enemy'
        return None

    def clear_teams(self):
        self.player_team.clear()
        self.enemy_team.clear()


class SmallButton:
    def __init__(self, text, rect, font, color, hover_color, action=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.is_enabled = True

    def draw(self, surface):
        bg_color = self.color
        if self.is_enabled:
            if self.is_hovered:
                bg_color = self.hover_color
        else:
            bg_color = (128, 128, 128)

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, COLOR_BLACK, self.rect, 1, border_radius=5)
        label = self.font.render(self.text, True, COLOR_BLACK)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if not self.is_enabled:
            self.is_hovered = False
            return

        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if self.is_hovered and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.action:
                self.action()


class LocationButton:
    def __init__(self, text, font, action=None):
        self.text = text
        self.font = font
        self.action = action
        self.color = (210, 180, 140)
        self.hover_color = (188, 158, 120)
        self.is_hovered = False
        self.rect = pygame.Rect(0, 0, 0, 0)

    def update_rect(self, x, y, width, height):
        self.rect.topleft = (int(x), int(y))
        self.rect.size = (int(width), int(height))

    def draw(self, surface):
        bg_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_BLACK, self.rect, 2, border_radius=10)
        label = self.font.render(self.text, True, COLOR_BLACK)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def handle_event(self, event):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if self.is_hovered and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.action:
                self.action()


class CharacterCard:
    def __init__(self, char_data, action):
        self.char_data = char_data
        self.image_original = char_data['image']
        self.stats = char_data['stats']
        self.action = action
        self.image_scaled = self.image_original
        self.rect = self.image_scaled.get_rect()
        self.is_hovered = False
        self.border_color = COLOR_YELLOW

    def update_layout(self, x, y, width, height):
        container_rect = pygame.Rect(x, y, width, height)
        orig_w, orig_h = self.image_original.get_size()
        aspect_ratio = orig_w / orig_h

        new_w, new_h = width, height
        if new_w / aspect_ratio > new_h:
            new_w = int(new_h * aspect_ratio)
        else:
            new_h = int(new_w / aspect_ratio)

        self.image_scaled = pygame.transform.smoothscale(self.image_original, (new_w, new_h))
        self.rect = self.image_scaled.get_rect(center=container_rect.center)

    def draw(self, surface, battle_manager=None):
        surface.blit(self.image_scaled, self.rect)

        border_to_draw = None
        if battle_manager and battle_manager.is_selection_mode_active:
            selection_status = battle_manager.is_character_selected(self.char_data)
            if selection_status == 'player':
                border_to_draw = COLOR_PLAYER
            elif selection_status == 'enemy':
                border_to_draw = COLOR_ENEMY
            elif self.is_hovered:
                border_to_draw = self.border_color
        elif self.is_hovered:
            border_to_draw = self.border_color

        if border_to_draw:
            pygame.draw.rect(surface, border_to_draw, self.rect, 3, border_radius=5)

    def handle_event(self, event):
        self.is_hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        if self.is_hovered and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.action:
                self.action(self.char_data)


class ModulePanel:
    def __init__(self, text, rect, description, font, small_font, color):
        self.text = text
        self.description = description
        self.rect = pygame.Rect(rect)
        self.color = color
        self.border_color = COLOR_BLACK
        self.font = font
        self.small_font = small_font
        self.child_buttons = []
        self.scroll_y = 0
        self.total_text_height = 0

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, self.border_color, self.rect, 2)
        label = self.font.render(self.text, True, COLOR_BLACK)
        surface.blit(label, (self.rect.centerx - label.get_width() // 2, self.rect.top + 10))
        self._render_description(surface)
        for btn in self.child_buttons:
            btn.draw(surface)

    def handle_scroll(self, event):
        scroll_speed = 20
        self.scroll_y -= event.y * scroll_speed
        viewable_height = self.rect.height - 120
        max_scroll_y = max(0, self.total_text_height - viewable_height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll_y))

    def _render_description(self, surface):
        text_area_rect = self.rect.inflate(-20, -120)
        text_area_rect.top = self.rect.top + 60

        lines = wrap_text_by_char(self.description, self.small_font, text_area_rect.width)
        line_height = self.small_font.get_height() + 5
        self.total_text_height = len(lines) * line_height

        surface.set_clip(text_area_rect)
        y_offset = text_area_rect.top
        for line in lines:
            desc_label = self.small_font.render(line, True, COLOR_BLACK)
            surface.blit(desc_label, (text_area_rect.left, y_offset - self.scroll_y))
            y_offset += line_height
        surface.set_clip(None)


class InfoPanel:
    def __init__(self, game, char_data, rect, close_action):
        self.game = game
        self.char_data = char_data.copy()
        stats_source = char_data.get('stats', char_data)
        self.stats = copy.deepcopy(stats_source)
        self.char_data['stats'] = self.stats
        self.rect = pygame.Rect(rect)
        self.close_action = close_action
        self.bg_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.bg_surface.fill((0, 0, 0, 180))
        self.action_buttons = []
        self.level_button = None
        self.is_level_selection_visible = False
        self.level_selection_buttons = []
        self.level_panel_rect = None
        self.level_panel_surface = None
        self.current_level_page = 0  # 新增：记录等级选择的当前页码
        self.levels_per_page = 9     # 每页显示 9 个

        self._create_buttons()

    def _show_level_selection(self):
            """点击更换等级按钮时触发"""
            identity = self.stats.get('身份')
            levels = identity_LEVELS.get(identity, [])
            if not levels:
                return

            self.is_level_selection_visible = True
            self.current_level_page = 0  # 每次打开重置为第一页
            self._create_level_buttons_grid()

    def _create_level_buttons_grid(self):
        """核心逻辑：根据当前页码创建 9 个等级按钮和翻页按钮"""
        identity = self.stats.get('身份')
        levels = identity_LEVELS.get(identity, [])
        self.level_selection_buttons.clear()

        # 1. 计算面板尺寸和位置
        panel_w, panel_h = 380, 260 # 稍微调大一点以容纳翻页键
        self.level_panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        self.level_panel_rect.center = self.rect.center
        self.level_panel_surface = pygame.Surface(self.level_panel_rect.size, pygame.SRCALPHA)
        self.level_panel_surface.fill((30, 40, 60, 240))

        # 2. 计算当前页要显示的等级
        start_idx = self.current_level_page * self.levels_per_page
        end_idx = start_idx + self.levels_per_page
        page_levels = levels[start_idx:end_idx]
        total_pages = (len(levels) + self.levels_per_page - 1) // self.levels_per_page

        # 3. 布局等级按钮 (3x3 矩阵)
        btn_w, btn_h, spacing = 100, 35, 10
        num_cols = 3
        grid_width = (btn_w * num_cols) + (spacing * (num_cols - 1))
        start_x = self.level_panel_rect.left + (panel_w - grid_width) / 2
        start_y = self.level_panel_rect.top + 20

        for i, level in enumerate(page_levels):
            row, col = divmod(i, num_cols)
            x = start_x + col * (btn_w + spacing)
            y = start_y + row * (btn_h + spacing)
            
            # 创建等级按钮
            action = lambda lvl=level: self._select_level(lvl)
            button = SmallButton(level, (x, y, btn_w, btn_h), self.game.small_font,
                                 (180, 180, 180), (255, 255, 255), action)
            self.level_selection_buttons.append(button)

        # 4. 底部功能按钮区域 (上一页 | 取消 | 下一页)
        footer_y = self.level_panel_rect.bottom - btn_h - 15
        cancel_x = self.level_panel_rect.centerx - btn_w / 2
        
        # 取消按钮 (中间)
        cancel_btn = SmallButton("取消", (cancel_x, footer_y, btn_w, btn_h),
                                 self.game.small_font, (255, 182, 193), (221, 160, 221), self._hide_level_selection)
        self.level_selection_buttons.append(cancel_btn)

        # 上一页 (取消左侧)
        if self.current_level_page > 0:
            prev_action = self._prev_level_page
            prev_btn = SmallButton("< 上页", (cancel_x - btn_w - spacing, footer_y, btn_w, btn_h),
                                   self.game.small_font, (150, 150, 200), (100, 100, 255), prev_action)
            self.level_selection_buttons.append(prev_btn)

        # 下一页 (取消右侧)
        if self.current_level_page < total_pages - 1:
            next_action = self._next_level_page
            next_btn = SmallButton("下页 >", (cancel_x + btn_w + spacing, footer_y, btn_w, btn_h),
                                   self.game.small_font, (150, 150, 200), (100, 100, 255), next_action)
            self.level_selection_buttons.append(next_btn)

        # 5. 页码显示 (装饰性)
        page_text = f"{self.current_level_page + 1} / {total_pages}"
        self.level_page_label = self.game.small_font.render(page_text, True, (200, 200, 200))
        self.level_page_label_pos = (self.level_panel_rect.centerx - self.level_page_label.get_width()//2, 
                                     footer_y - 25)

    def _next_level_page(self):
        self.current_level_page += 1
        self._create_level_buttons_grid()

    def _prev_level_page(self):
        self.current_level_page -= 1
        self._create_level_buttons_grid()

    def _hide_level_selection(self):
        self.is_level_selection_visible = False
        self.level_selection_buttons.clear()

    def _select_level(self, new_level):
        self.stats['等级'] = new_level
        self._update_stats_for_level()
        self._hide_level_selection()

    def _update_stats_for_level(self):
        char_name = self.stats.get('姓名')
        identity = self.stats.get('身份')
        selected_level = self.stats.get('等级')
        base_stats = Character_battle_data.get(char_name)
        if not base_stats or not identity or not selected_level:
            return

        new_stats = calculate_stats_by_level(base_stats, selected_level, identity)
        self.stats['血量'] = str(new_stats['hp'])
        self.stats['魂度'] = str(new_stats['hundu'])
        self.stats['魂量'] = str(new_stats['hunliang'])

    def _create_buttons(self):
        btn_w, btn_h, spacing = 80, 30, 10
        close_btn_x = self.rect.right - btn_w - 15
        close_btn_y = self.rect.bottom - btn_h - 15
        close_button = SmallButton("关闭", (close_btn_x, close_btn_y, btn_w, btn_h), self.game.small_font,
                                   (255, 182, 193), (221, 160, 221), self.close_action)
        self.action_buttons.append(close_button)

        if not self.game.battle_manager.is_selection_mode_active:
            return

        char_status = self.game.battle_manager.is_character_selected(self.char_data)
        next_btn_x = close_btn_x
        if char_status:
            next_btn_x -= (btn_w + spacing)
            remove_action = lambda: (self.game.battle_manager.remove_from_teams(self.char_data), self.close_action())
            remove_button = SmallButton("移除队伍", (next_btn_x, close_btn_y, btn_w, btn_h), self.game.small_font,
                                        (255, 218, 185), (244, 164, 96), remove_action)
            self.action_buttons.append(remove_button)
        else:
            next_btn_x -= (btn_w + spacing)
            enemy_action = lambda: (self.game.battle_manager.add_to_enemy_team(self.char_data), self.close_action())
            enemy_button = SmallButton("加入敌方", (next_btn_x, close_btn_y, btn_w, btn_h), self.game.small_font,
                                       COLOR_ENEMY, (200, 0, 0), enemy_action)
            self.action_buttons.append(enemy_button)

            next_btn_x -= (btn_w + spacing)
            player_action = lambda: (self.game.battle_manager.add_to_player_team(self.char_data), self.close_action())
            player_button = SmallButton("加入我方", (next_btn_x, close_btn_y, btn_w, btn_h), self.game.small_font,
                                        COLOR_PLAYER, (0, 200, 0), player_action)
            self.action_buttons.append(player_button)

    def draw(self, surface):
        surface.blit(self.bg_surface, self.rect.topleft)
        pygame.draw.rect(surface, COLOR_WHITE, self.rect, 2, border_radius=5)

        y_offset = self.rect.top + 20
        x_pos_key = self.rect.left + 20
        x_pos_value = self.rect.left + 120
        value_max_width = self.rect.width - (x_pos_value - self.rect.left) - 20

        stat_order = ['姓名', '身份', '等级', '血量', '魂度', '魂量', '神度', '神量', '技能', '说明']
        display_stats = {key: self.stats.get(key) for key in stat_order if self.stats.get(key) is not None}
        for key in self.stats:
            if key not in display_stats:
                display_stats[key] = self.stats[key]

        for key, value in display_stats.items():
            key_label = self.game.small_font.render(f"{key}:", True, COLOR_YELLOW)
            surface.blit(key_label, (x_pos_key, y_offset))

            if key == '等级':
                level_text = str(value)
                level_label = self.game.small_font.render(level_text, True, COLOR_WHITE)
                surface.blit(level_label, (x_pos_value, y_offset))

                btn_w, btn_h = 80, self.game.small_font.get_height() + 4
                btn_x = x_pos_value + level_label.get_width() + 10
                btn_y = y_offset - 2

                if self.level_button is None:
                    self.level_button = SmallButton("更换等级", (btn_x, btn_y, btn_w, btn_h), self.game.small_font,
                                                    (200, 200, 220), (170, 170, 190), self._show_level_selection)
                else:
                    self.level_button.rect.topleft = (btn_x, btn_y)
                self.level_button.draw(surface)
                y_offset += (level_label.get_height() + 5) + 5
            else:
                lines = wrap_text_by_char(str(value), self.game.small_font, value_max_width)
                line_height = self.game.small_font.get_height() + 5
                line_start_y = y_offset
                for i, line in enumerate(lines):
                    line_label = self.game.small_font.render(line, True, COLOR_WHITE)
                    surface.blit(line_label, (x_pos_value, line_start_y + i * line_height))
                y_offset += (len(lines) * line_height) + 5

        for btn in self.action_buttons:
            btn.draw(surface)

        if self.is_level_selection_visible:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            surface.blit(overlay, (0, 0))
            surface.blit(self.level_panel_surface, self.level_panel_rect.topleft)
            pygame.draw.rect(surface, COLOR_WHITE, self.level_panel_rect, 2, border_radius=5)
            for btn in self.level_selection_buttons:
                btn.draw(surface)
        
        if self.is_level_selection_visible:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            surface.blit(overlay, (0, 0))
            
            surface.blit(self.level_panel_surface, self.level_panel_rect.topleft)
            pygame.draw.rect(surface, COLOR_WHITE, self.level_panel_rect, 2, border_radius=5)
            
            # 新增：绘制页码
            surface.blit(self.level_page_label, self.level_page_label_pos)
            
            for btn in self.level_selection_buttons:
                btn.draw(surface)

    def handle_event(self, event):
        if self.is_level_selection_visible:
            for btn in self.level_selection_buttons:
                btn.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and not self.level_panel_rect.collidepoint(event.pos):
                self._hide_level_selection()
            return

        for btn in self.action_buttons:
            btn.handle_event(event)
        if self.level_button:
            self.level_button.handle_event(event)


class BattleRosterPanel:
    def __init__(self, game):
        self.game = game
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.bg_surface = None
        self.start_button = None
        self.clear_button = None

    def on_resize(self, screen_w, screen_h):
        panel_h = 160
        self.rect = pygame.Rect(0, screen_h - panel_h, screen_w, panel_h)
        self.bg_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.bg_surface.fill((20, 20, 20, 200))

        btn_w, btn_h, spacing = 100, 36, 20
        btn_y = self.rect.centery - btn_h / 2

        start_action = lambda: self.game.change_scene(
            BattleScene(self.game, self.game.current_scene, self.game.battle_manager.player_team,
                        self.game.battle_manager.enemy_team))
        self.start_button = SmallButton("开始战斗", (self.rect.right - btn_w - spacing, btn_y, btn_w, btn_h),
                                        self.game.small_font, (144, 238, 144), (102, 205, 170), start_action)

        clear_action = self.game.battle_manager.clear_teams
        self.clear_button = SmallButton("清空队伍",
                                        (self.start_button.rect.left - btn_w - spacing, btn_y, btn_w, btn_h),
                                        self.game.small_font, (255, 218, 185), (244, 164, 96), clear_action)

    def update(self):
        can_start = len(self.game.battle_manager.player_team) > 0 and len(self.game.battle_manager.enemy_team) > 0
        self.start_button.is_enabled = can_start

    def handle_event(self, event):
        self.start_button.handle_event(event)
        self.clear_button.handle_event(event)
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                return True
        return False

    def draw(self, surface):
        surface.blit(self.bg_surface, self.rect.topleft)
        pygame.draw.line(surface, COLOR_WHITE, self.rect.topleft, self.rect.topright, 2)
        self._draw_team_list(surface, "我方阵营", self.game.battle_manager.player_team, COLOR_PLAYER,
                             self.rect.left + 20)
        self._draw_team_list(surface, "敌方阵营", self.game.battle_manager.enemy_team, COLOR_ENEMY,
                             self.rect.centerx + 20)
        self.start_button.draw(surface)
        self.clear_button.draw(surface)

    def _draw_team_list(self, surface, title, team, color, start_x):
        title_label = self.game.small_font.render(title, True, color)
        surface.blit(title_label, (start_x, self.rect.top + 15))

        team_details = []
        for member in team:
            name = member['stats'].get("姓名", "未知")
            level = member['stats'].get("等级", "")
            team_details.append(f"{name}({level})")

        team_text = ", ".join(team_details) or "（尚未选择）"
        max_width = self.rect.width / 2 - self.clear_button.rect.width - 80
        lines = wrap_text_by_char(team_text, self.game.small_font, max_width)

        y_offset = self.rect.top + 45
        for line in lines:
            line_label = self.game.small_font.render(line, True, COLOR_WHITE)
            surface.blit(line_label, (start_x, y_offset))
            y_offset += self.game.small_font.get_height() + 2


class Scene:
    def __init__(self, game): self.game = game

    def on_resize(self, new_width, new_height): pass

    def handle_events(self, events): pass

    def update(self): pass

    def draw(self): pass

    def enter(self): pass

    def exit(self): pass


class MainMenuScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.title = "主菜单"
        self.background_original = self.game.background_images['bg_gold']
        self.background = None
        self.panels = []

        # 从中心化数据获取第一世的信息
        zhsd_master_data = self.game.character_data.get("尊皇圣帝", {})
        zhsd_stats_for_display = {
            "姓名": "尊皇圣帝",
            "身份": zhsd_master_data.get("identity"),
            "血量": str(zhsd_master_data.get("hp")),
            "神度": str(zhsd_master_data.get("hundu")),
            "神量": str(zhsd_master_data.get("hunliang")),
            "技能": zhsd_master_data.get("skills"),
            "说明": zhsd_master_data.get("description")
        }

        self.button_data = [
            {"text": "第一世",
             "desc": ("天地初开，万物寂寥。宇宙中仅有尊皇圣帝一人，拥有无上神力，手持尊皇杖和圣帝戟两大极道帝兵，尊皇杖无所不能，圣帝戟威力无穷。"
                      "因感孤独，遂决定以尊皇杖之能，化身躯为宇宙万物，精神为天道法则，衍化三千世界。圣帝戟化为众多神界本源，向宇宙散发各界神力（魂力）。"
                      "尊皇杖能量耗尽封印在宇宙深渊，尊皇圣帝最后一丝意念本源化身主角不断经历轮回。修为越高解封记忆越多，为求突破到更高境界而不断重生修行。"),
             "stats": zhsd_stats_for_display,
             "action": self.first_age},
            {"text": "第二世",
             "desc": ("上古洪荒时期，神界未显，但神界本源已存在。尊皇圣帝最后一丝意念本源化身主角降生于一个偏远村庄，与妹妹为伴。"
                      "该世有众多种族，以家族或者族群形式存在。"
                      "该世修炼体系已在天道法则指引下逐渐成型，但最高修炼只到高级魂灵后期，还未有生灵能成神。"
                      "主角首先成神后开启成神时代，并首个进入神国开始建立神国。"),
             "action": self.second_age},
            {"text": "第三世",
             "desc": "待开发。",
             "action": self.third_age}
        ]
        self.on_resize(self.game.width, self.game.height)

    def enter(self):
        pygame.display.set_caption("大世界版")

    def on_resize(self, new_width, new_height):
        self.background = pygame.transform.scale(self.background_original, (new_width, new_height))
        self.panels.clear()

        box_width = new_width / 3.5
        box_height = new_height / 1.5
        gap = (new_width - (box_width * 3)) / 4
        colors = [(255, 204, 203), (204, 229, 204), (179, 217, 255)]

        for i, data in enumerate(self.button_data):
            x = gap * (i + 1) + box_width * i
            y = (new_height - box_height) / 2
            panel = ModulePanel(data["text"], (x, y, box_width, box_height), data["desc"], self.game.font,
                                self.game.small_font, colors[i])

            btn_w, btn_h = box_width / 2.5, 40
            btn_x = x + (box_width - btn_w) / 2
            btn_y = y + box_height - btn_h - 15
            enter_button = SmallButton("进入世界", (btn_x, btn_y, btn_w, btn_h), self.game.small_font,
                                       (144, 238, 144), (102, 205, 170), data["action"])
            panel.child_buttons.append(enter_button)
            self.panels.append(panel)

    def handle_events(self, events):
        for event in events:
            for panel in self.panels:
                for button in panel.child_buttons:
                    button.handle_event(event)
                if event.type == pygame.MOUSEWHEEL and panel.rect.collidepoint(pygame.mouse.get_pos()):
                    panel.handle_scroll(event)
                    break

    def draw(self):
        self.game.screen.blit(self.background, (0, 0))
        for panel in self.panels:
            panel.draw(self.game.screen)

    def first_age(self):
        self.game.change_scene(
            CharacterDisplayScene(self.game, "第一世", self, self.game.background_images['bg_xk'],
                                  self.game.character_images.get("尊皇圣帝"), self.button_data[0]["stats"]))

    def second_age(self):
        # 初始进入时不传路径，即展示第一层（洪荒、神界等）
        self.game.change_scene(LocationSelectionScene(
            self.game, "第二世", self, self.game.background_images['bg_hh'], current_path=""
        ))

    def third_age(self):
        print("第三世内容待开发...")


class CharacterDisplayScene(Scene):
    def __init__(self, game, title, prev_scene, bg_img_orig, content_img_orig, stats):
        super().__init__(game)
        self.title = title
        self.previous_scene_instance = prev_scene
        self.background_original = bg_img_orig
        self.content_image_original = content_img_orig
        self.character_stats = stats
        self.info_panel = None
        self.info_panel_visible = False
        self.background = None
        self.content_image_scaled = None
        self.content_image_rect = None
        self.back_button = None
        self.on_resize(self.game.width, self.game.height)

    def enter(self):
        pygame.display.set_caption(self.title)

    def on_resize(self, new_width, new_height):
        self.background = pygame.transform.scale(self.background_original, (new_width, new_height))

        padding_top, padding_bottom, padding_h = 120, 80, 100
        max_w = new_width - (padding_h * 2)
        max_h = new_height - padding_top - padding_bottom
        orig_w, orig_h = self.content_image_original.get_size()

        ratio = min(max_w / orig_w, max_h / orig_h) if orig_w > 0 and orig_h > 0 else 1.0
        new_size = (int(orig_w * ratio), int(orig_h * ratio)) if ratio < 1 else (orig_w, orig_h)

        self.content_image_scaled = pygame.transform.smoothscale(self.content_image_original, new_size)
        self.content_image_rect = self.content_image_scaled.get_rect(center=(new_width // 2, new_height // 2 + 30))

        back_action = lambda: self.game.change_scene(self.previous_scene_instance)
        self.back_button = SmallButton("返回", (20, 20, 80, 36), self.game.small_font,
                                       (200, 200, 200), (170, 170, 170), back_action)
        if self.info_panel_visible: self._recreate_info_panel()

    def handle_events(self, events):
        if self.info_panel_visible:
            for event in events: self.info_panel.handle_event(event)
            return

        for event in events:
            self.back_button.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.content_image_rect.collidepoint(event.pos):
                    self._show_info_panel(self.character_stats)

    def draw(self):
        self.game.screen.blit(self.background, (0, 0))
        self.back_button.draw(self.game.screen)
        self.game.screen.blit(self.content_image_scaled, self.content_image_rect)
        if self.info_panel_visible:
            self.info_panel.draw(self.game.screen)

    def _show_info_panel(self, data):
        self.info_panel_visible = True
        self._recreate_info_panel(data)

    def _recreate_info_panel(self, data=None):
        if data is None: data = self.info_panel.char_data
        panel_w, panel_h = 450, 400
        panel_rect = pygame.Rect((self.game.width - panel_w) / 2, (self.game.height - panel_h) / 2, panel_w, panel_h)
        self.info_panel = InfoPanel(self.game, data, panel_rect, self._hide_info_panel)

    def _hide_info_panel(self):
        self.info_panel_visible = False


class LocationSelectionScene(Scene):
    def __init__(self, game, title, prev_scene, bg_img_orig, current_path=""):
        super().__init__(game)
        self.title = title
        self.previous_scene_instance = prev_scene
        self.background_original = bg_img_orig
        self.current_path = current_path  # 例如 "" 或 "神界" 或 "神界:光明神殿"

        # 1. 获取全局地点映射表
        self.location_character_map = get_location_character_map(self.game.character_data)
        
        # 2. 提取当前层级下的按钮名称
        self.display_items = self._get_items_at_current_path()
        
        # 3. 初始化按钮（点击会触发 enter_location）
        self.location_buttons = [
            LocationButton(item, self.game.small_font, lambda t=item: self.enter_location(t))
            for item in self.display_items
        ]

        # 4. 其他 UI 元素初始化
        self.cols_per_row, self.rows_per_page = 5, 3
        self.items_per_page = self.cols_per_row * self.rows_per_page
        self.current_page = 0
        self.total_pages = 0
        self.prev_button, self.next_button, self.battle_button, self.back_button = None, None, None, None
        self.roster_panel = BattleRosterPanel(self.game)
        self.on_resize(self.game.width, self.game.height)

    def _get_items_at_current_path(self):
        items = [] # 改用列表，保持顺序
        for full_path in self.location_character_map.keys():
            item_to_add = None
            if not self.current_path:
                # 根目录：提取第一级
                item_to_add = full_path.split(":")[0]
            elif full_path.startswith(self.current_path + ":"):
                # 子目录：提取下一级
                remaining = full_path[len(self.current_path) + 1:]
                item_to_add = remaining.split(":")[0]
            
            # 如果该项还没在列表中，则添加（去重且保序）
            if item_to_add and item_to_add not in items:
                items.append(item_to_add)
        return items # 直接返回列表，不再排序

    def _get_bg_by_path(self, path):
            """核心逻辑：递归查找背景图。如果子级没定义，就找父级，直到根目录"""
            if not path:
                return "bg_hh"

            # 1. 尝试匹配完整路径 (例如 "神国:凡神域")
            if path in Location_background_map:
                return Location_background_map[path]

            # 2. 尝试匹配当前地点的短名称 (例如 "凡神域")
            short_name = path.split(":")[-1]
            if short_name in Location_background_map:
                return Location_background_map[short_name]

            # 3. 如果有父级，递归向上查找 (例如 从 "神国:凡神域:混元界" 找 "神国:凡神域")
            if ":" in path:
                parent_path = path.rsplit(":", 1)[0]
                return self._get_bg_by_path(parent_path)

            # 4. 最后回退到默认洪荒背景
            return "bg_hh"

    def enter_location(self, clicked_name):
        """核心跳转逻辑：判断是【文件夹】还是【最终地点】"""
        # 1. 拼接点击后的完整路径
        new_path = f"{self.current_path}:{clicked_name}" if self.current_path else clicked_name
        
        # 2. 智能获取背景图属性名 (调用上面的递归函数)
        bg_attr = self._get_bg_by_path(new_path)
        
        # 3. 获取真正的背景图像对象
        bg_img = self.game.background_images.get(bg_attr, self.background_original)

        # 4. 检查这是否是一个最终地点 (data.py 中有直接定义的角色)
        if new_path in self.location_character_map:
            char_data = self._prepare_char_data(new_path)
            self.game.change_scene(LocationScene(self.game, clicked_name, self, bg_img, char_data))
            return

        # 5. 检查是否是文件夹 (有子地点)
        is_directory = any(full_key.startswith(new_path + ":") for full_key in self.location_character_map.keys())

        if is_directory:
            # 递归：进入下一层级
            self.game.change_scene(LocationSelectionScene(self.game, clicked_name, self, bg_img, new_path))
        else:
            print(f"Location '{new_path}' has no data in data.py!")

    def _prepare_char_data(self, path):
        """为角色列表页准备数据：加载图片、视频，并智能初始化等级"""
        chars = self.location_character_map.get(path, [])
        for char in chars:
            name = char['stats']['姓名']
            char['image'] = self.game.character_images.get(name)
            char['video_path'] = self.game.character_videos.get(name)
            
            stats = char['stats']
            identity = stats.get('身份')
            
            if identity:
                levels = identity_LEVELS.get(identity, [])
                if levels and '等级' not in stats:
                    # 根据身份和名字智能初始化起始等级
                    if identity == "凡神":
                        stats['等级'] = "1"
                    elif identity == "界王":
                        stats['等级'] = "100"
                    elif identity == "神王":
                        stats['等级'] = "1000"
                    else:
                        stats['等级'] = levels[0]  # 魂师等职业默认第一个
                    
                    # 关键：初始化后立刻刷新一次战斗属性
                    base_data = Character_battle_data.get(name)
                    if base_data:
                        new_stats = calculate_stats_by_level(base_data, stats['等级'], identity)
                        stats['血量'] = str(new_stats['hp'])
                        stats['魂度'] = str(new_stats['hundu'])
                        stats['魂量'] = str(new_stats['hunliang'])
        return chars

    def on_resize(self, new_width, new_height):
        self.background = pygame.transform.scale(self.background_original, (new_width, new_height))
        num = len(self.location_buttons)
        if num == 0: return
        self.total_pages = max(1, (num + self.items_per_page - 1) // self.items_per_page)
        self.current_page = max(0, min(self.current_page, self.total_pages - 1))
        bottom_ui_height = 100
        if self.game.battle_manager.is_selection_mode_active:
            self.roster_panel.on_resize(new_width, new_height)
            bottom_ui_height += self.roster_panel.rect.height
        padding_top, padding_side, gap_x, gap_y = 150, int(new_width * 0.08), 20, 20
        available_w = new_width - (padding_side * 2) - (gap_x * (self.cols_per_row - 1))
        available_h = new_height - padding_top - bottom_ui_height - (gap_y * (self.rows_per_page - 1))
        btn_w_loc = available_w / self.cols_per_row
        btn_h_loc = max(1, available_h / self.rows_per_page)
        start_index = self.current_page * self.items_per_page
        for button in self.location_buttons: button.update_rect(-1000, -1000, 0, 0)
        for i in range(start_index, min(start_index + self.items_per_page, num)):
            row, col = divmod(i - start_index, self.cols_per_row)
            x, y = padding_side + col * (btn_w_loc + gap_x), padding_top + row * (btn_h_loc + gap_y)
            self.location_buttons[i].update_rect(x, y, btn_w_loc, btn_h_loc)
        nav_btn_w, nav_btn_h, spacing = 100, 36, 20
        nav_y = new_height - bottom_ui_height + 50
        total_nav_width = nav_btn_w * 2 + spacing
        nav_start_x = (new_width - total_nav_width) / 2
        self.prev_button = SmallButton("上一页", (nav_start_x, nav_y, nav_btn_w, nav_btn_h), self.game.small_font, (180, 180, 180), (160, 160, 160), self._go_prev_page)
        self.next_button = SmallButton("下一页", (nav_start_x + nav_btn_w + spacing, nav_y, nav_btn_w, nav_btn_h), self.game.small_font, (180, 180, 180), (160, 160, 160), self._go_next_page)
        is_battle_mode = self.game.battle_manager.is_selection_mode_active
        battle_btn_text = "取消选择" if is_battle_mode else "战斗准备"
        battle_btn_color = (255, 218, 185) if is_battle_mode else (255, 100, 100)
        self.battle_button = SmallButton(battle_btn_text, ((new_width - 120) / 2, padding_top - 110, 120, 60), self.game.small_font, battle_btn_color, (220, 80, 80), self._toggle_battle_mode)
        back_action = lambda: self.game.change_scene(self.previous_scene_instance)
        self.back_button = SmallButton("返回", (20, 20, 80, 36), self.game.small_font, (200, 200, 200), (170, 170, 170), back_action)

    def _toggle_battle_mode(self):
        self.game.battle_manager.toggle_selection_mode()
        self.on_resize(self.game.width, self.game.height)

    def _go_prev_page(self):
        if self.current_page > 0: self.current_page -= 1; self.on_resize(self.game.width, self.game.height)

    def _go_next_page(self):
        if self.current_page < self.total_pages - 1: self.current_page += 1; self.on_resize(self.game.width, self.game.height)

    def update(self):
        if self.game.battle_manager.is_selection_mode_active: self.roster_panel.update()

    def handle_events(self, events):
        if self.game.battle_manager.is_selection_mode_active:
            for event in events:
                if self.roster_panel.handle_event(event): return
        visible_buttons = self.location_buttons[self.current_page * self.items_per_page: (self.current_page + 1) * self.items_per_page]
        for event in events:
            self.back_button.handle_event(event)
            for btn in visible_buttons: btn.handle_event(event)
            self.prev_button.handle_event(event)
            self.next_button.handle_event(event)
            self.battle_button.handle_event(event)

    def draw(self):
        self.game.screen.blit(self.background, (0, 0))
        self.back_button.draw(self.game.screen)
        visible_buttons = self.location_buttons[self.current_page * self.items_per_page: (self.current_page + 1) * self.items_per_page]
        for btn in visible_buttons: btn.draw(self.game.screen)
        page_info = f"第 {self.current_page + 1} / {self.total_pages} 页"
        page_label = self.game.small_font.render(page_info, True, (255, 255, 255))
        self.game.screen.blit(page_label, (self.game.width // 2 - page_label.get_width() // 2, self.prev_button.rect.top - 30))
        if self.current_page > 0: self.prev_button.draw(self.game.screen)
        if self.current_page < self.total_pages - 1: self.next_button.draw(self.game.screen)
        self.battle_button.draw(self.game.screen)
        if self.game.battle_manager.is_selection_mode_active: self.roster_panel.draw(self.game.screen)


class LocationScene(Scene):
    def __init__(self, game, title, prev_scene, bg_img_orig, char_data):
        super().__init__(game)
        self.title = title
        self.previous_scene_instance = prev_scene
        self.background_original = bg_img_orig
        self.background = None
        self.character_cards = [CharacterCard(d, self._show_info_panel) for d in char_data]
        self.info_panel = None
        self.info_panel_visible = False
        self.cols_per_row, self.rows_per_page = 4, 2
        self.items_per_page = self.cols_per_row * self.rows_per_page
        self.current_page = 0
        self.total_pages = 0
        self.prev_button, self.next_button, self.back_button = None, None, None
        self.on_resize(self.game.width, self.game.height)

    def enter(self):
        pygame.display.set_caption(self.title)

    def on_resize(self, new_width, new_height):
        self.background = pygame.transform.scale(self.background_original, (new_width, new_height))
        num = len(self.character_cards)
        if num == 0: return

        self.total_pages = max(1, (num + self.items_per_page - 1) // self.items_per_page)
        self.current_page = max(0, min(self.current_page, self.total_pages - 1))

        padding_top, padding_h, padding_bottom, gap_x, gap_y = 120, new_width * 0.05, 100, 20, 20
        available_w = new_width - (padding_h * 2) - (gap_x * (self.cols_per_row - 1))
        available_h = new_height - padding_top - padding_bottom - (gap_y * (self.rows_per_page - 1))
        card_w, card_h = available_w / self.cols_per_row, available_h / self.rows_per_page

        start_index = self.current_page * self.items_per_page
        for card in self.character_cards: card.update_layout(-2000, -2000, 0, 0)

        for i in range(start_index, min(start_index + self.items_per_page, num)):
            row, col = divmod(i - start_index, self.cols_per_row)
            x, y = padding_h + col * (card_w + gap_x), padding_top + row * (card_h + gap_y)
            self.character_cards[i].update_layout(x, y, card_w, card_h)

        nav_btn_w, nav_btn_h, spacing = 100, 36, 20
        nav_y = new_height - nav_btn_h - 20
        nav_start_x = (new_width - (nav_btn_w * 2 + spacing)) / 2

        self.prev_button = SmallButton("上一页", (nav_start_x, nav_y, nav_btn_w, nav_btn_h), self.game.small_font,
                                       (180, 180, 180), (160, 160, 160), self._go_prev_page)
        self.next_button = SmallButton("下一页", (nav_start_x + nav_btn_w + spacing, nav_y, nav_btn_w, nav_btn_h),
                                       self.game.small_font, (180, 180, 180), (160, 160, 160), self._go_next_page)

        back_action = lambda: self.game.change_scene(self.previous_scene_instance)
        self.back_button = SmallButton("返回", (20, 20, 80, 36), self.game.small_font,
                                       (200, 200, 200), (170, 170, 170), back_action)
        if self.info_panel_visible: self._recreate_info_panel()

    def _go_prev_page(self):
        if self.current_page > 0: self.current_page -= 1; self.on_resize(self.game.width, self.game.height)

    def _go_next_page(self):
        if self.current_page < self.total_pages - 1: self.current_page += 1; self.on_resize(self.game.width,
                                                                                            self.game.height)

    def handle_events(self, events):
        if self.info_panel_visible:
            for event in events: self.info_panel.handle_event(event)
            return

        visible_cards = self.character_cards[
                        self.current_page * self.items_per_page: (self.current_page + 1) * self.items_per_page]

        for event in events:
            self.back_button.handle_event(event)
            for card in visible_cards: card.handle_event(event)
            self.prev_button.handle_event(event)
            self.next_button.handle_event(event)

    def draw(self):
        self.game.screen.blit(self.background, (0, 0))
        self.back_button.draw(self.game.screen)

        visible_cards = self.character_cards[
                        self.current_page * self.items_per_page: (self.current_page + 1) * self.items_per_page]
        for card in visible_cards:
            card.draw(self.game.screen, self.game.battle_manager)

        if self.total_pages > 1:
            page_info = f"第 {self.current_page + 1} / {self.total_pages} 页"
            page_label = self.game.small_font.render(page_info, True, COLOR_WHITE)
            page_y = self.prev_button.rect.top - page_label.get_height() - 8
            self.game.screen.blit(page_label, (self.game.width // 2 - page_label.get_width() // 2, page_y))
            if self.current_page > 0: self.prev_button.draw(self.game.screen)
            if self.current_page < self.total_pages - 1: self.next_button.draw(self.game.screen)

        if self.info_panel_visible:
            self.info_panel.draw(self.game.screen)

    def _show_info_panel(self, char_data):
        self.info_panel_visible = True
        self._recreate_info_panel(char_data)

    def _recreate_info_panel(self, char_data=None):
        if char_data is None: char_data = self.info_panel.char_data
        panel_w, panel_h = 450, 400
        panel_rect = pygame.Rect((self.game.width - panel_w) / 2, (self.game.height - panel_h) / 2, panel_w, panel_h)
        self.info_panel = InfoPanel(self.game, char_data, panel_rect, self._hide_info_panel)

    def _hide_info_panel(self):
        self.info_panel_visible = False


class BattleScene(Scene):
    def __init__(self, game, prev_scene, player_team, enemy_team):
        super().__init__(game)
        self.previous_scene_instance = prev_scene
        self.player_team_bw = list(player_team)
        self.enemy_team_bw = list(enemy_team)
        if self.game.battle_manager.is_selection_mode_active:
            self.game.battle_manager.toggle_selection_mode()

    def _transform_team_data(self, team_data_bw):
        transformed_team = []
        for member in team_data_bw:
            stats_bw = member['stats']
            name = stats_bw.get('姓名')
            identity = stats_bw.get('身份')
            level = stats_bw.get('等级', "")

            base_stats_wdsj = Character_battle_data.get(name)
            if not base_stats_wdsj:
                print(f"Warning: Character '{name}' not found in battle.py character map. Skipping.")
                continue

            transformed_member = {
                'name': name,
                'hp': int(stats_bw.get('血量')),
                'hundu': float(stats_bw.get('魂度')),
                'hunliang': int(stats_bw.get('魂量')),
                'skills': base_stats_wdsj.get('skills', []),
                'identity': identity,
                'image_path': str(PICTURE_DIR / data.Character_data.get(name, {}).get('image_file', f"{name}.png")),
                'level': level
            }
            transformed_team.append(transformed_member)
        return transformed_team

    def enter(self):
        player_data_wdsj = self._transform_team_data(self.player_team_bw)
        enemy_data_wdsj = self._transform_team_data(self.enemy_team_bw)

        print("开始战斗模块...")
        try:
            battle.main_gui(player_data_wdsj, enemy_data_wdsj)
        except Exception as e:
            print(f"An error occurred while calling the battle logic: {e}")
        finally:
            print("战斗结束，返回...")
            pygame.init()
            self.game.screen = pygame.display.set_mode((self.game.width, self.game.height), pygame.RESIZABLE)
            self.game._load_resources()
            pygame.display.set_caption("大世界版")

        self.game.change_scene(self.previous_scene_instance)

    def draw(self):
        self.game.screen.fill(COLOR_BLACK)
        label = self.game.font.render("Loading battle...", True, COLOR_WHITE)
        self.game.screen.blit(label, label.get_rect(center=(self.game.width / 2, self.game.height / 2)))


class Game:
    def __init__(self):
        pygame.init()
        self.width, self.height = SCREEN_WIDTH, SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("大世界版")
        self.character_images = {}
        self.background_images = {}
        self.character_data = {}
        self._load_resources()
        self.battle_manager = BattleManager()
        self.current_scene = None

    def _load_resources(self):
        try:
            font_path = "C:/Windows/Fonts/msyh.ttc"
            small_font_path = "C:/Windows/Fonts/simkai.ttf"
            self.font = pygame.font.Font(font_path, 36)
            self.small_font = pygame.font.Font(small_font_path, 20)
        except FileNotFoundError:
            print(f"Warning: Specified fonts not found, using Pygame default.")
            self.font = pygame.font.Font(None, 48)
            self.small_font = pygame.font.Font(None, 24)

        try:
            # 背景图片读入
            for attr_name, filename in Background_file_map.items():
                image_path = PICTURE_DIR / filename
                try:
                    self.background_images[attr_name] = pygame.image.load(str(image_path)).convert()
                except pygame.error as e:
                    print(f"警告: 无法加载背景图片 '{filename}' at '{image_path}'. {e}")

            self.character_videos = {} # 新增：用于存储视频对象

            # 角色数据和图片动态读入
            self.character_data = data.Character_data
            for char_name, char_info in self.character_data.items():
                # 定义视频和图片路径
                video_file = f"{char_name}.mp4"
                image_file = char_info.get("image_file", f"{char_name}.png")
                
                video_path = PICTURE_DIR / video_file
                image_path = PICTURE_DIR / image_file

                # 优先检查是否存在同名 MP4
                if video_path.exists():
                    # 暂时不初始化 VideoPlayer，因为不知道具体显示尺寸
                    # 我们存储路径，在具体显示类中初始化
                    self.character_videos[char_name] = str(video_path)
                    print(f"检测到视频资源: {video_file}")
                    
                # 无论是否有视频，都加载图片作为占位符或回退方案
                try:
                    self.character_images[char_name] = pygame.image.load(str(image_path)).convert_alpha()
                except pygame.error:
                    print(f"Warning: Could not load image for '{char_name}' at '{image_path}'. Using placeholder.")
                    placeholder = pygame.Surface((120, 160))
                    placeholder.fill((128, 0, 128)) # 紫色占位符
                    self.character_images[char_name] = placeholder

        except (pygame.error, FileNotFoundError) as e:
            print(
                f"Error: Could not load resources from '{PICTURE_DIR}'. {e}")
            sys.exit()

    def change_scene(self, new_scene):
        if self.current_scene:
            self.current_scene.exit()
        self.current_scene = new_scene
        self.current_scene.enter()

    def run(self):
        clock = pygame.time.Clock()
        self.change_scene(MainMenuScene(self))
        is_running = True
        while is_running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    is_running = False
                if event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.size
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    if self.current_scene:
                        self.current_scene.on_resize(self.width, self.height)
            if self.current_scene:
                self.current_scene.handle_events(events)
                self.current_scene.update()
                self.current_scene.draw()

            pygame.display.update()
            clock.tick(60)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game_instance = Game()
    game_instance.run()
