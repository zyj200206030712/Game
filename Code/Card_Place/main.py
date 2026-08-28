# main.py  主程序的入口，负责场景流转、事件监听和整体渲染

import pygame
import sys
import random
import math
pygame.init()
from config import *
from ui import *
from models import Character, GameData
from battle import process_turn, refresh_skill_ready_highlights

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("放置卡牌游戏")
    clock = pygame.time.Clock()
    game = GameData()
    
    # UI 按钮初始化
    nav_level = Button(WIDTH//2 - 350, 690, 200, 60, "战斗", WHITE)
    nav_hero = Button(WIDTH//2 - 100, 690, 200, 60, "角色", WHITE)
    nav_gacha = Button(WIDTH//2 + 150, 690, 200, 60, "召唤", WHITE)
    
    btn_fight = Button(WIDTH//2 - 120, 480, 240, 60, "开始战斗", RED, WHITE)
    btn_save = Button(WIDTH - 150, 10, 120, 30, "进度保存", BLUE, WHITE)
    
    btn_draw_single = Button(WIDTH//2 - 250, 560, 200, 60, "单次召唤(500金)", GOLD, BLACK)
    btn_draw_ten = Button(WIDTH//2 + 50, 560, 200, 60, "十连召唤(5000金)", GOLD, BLACK)
    
    btn_prev_page = Button(15, 220, 45, 50, "<")
    btn_next_page = Button(WIDTH - 60, 220, 45, 50, ">")
    
    btn_lvl_up = Button(WIDTH//2 + 240, 500, 110, 40, "升级(100金)", GREEN, WHITE)
    btn_star_up = Button(WIDTH//2 + 360, 500, 110, 40, "升星(碎片)", GOLD, BLACK)
    btn_remove = Button(WIDTH//2 + 480, 500, 110, 40, "下阵", RED, WHITE)
    
    btn_pos1 = Button(WIDTH//2 + 240, 555, 110, 40, "1号位", BLUE, WHITE)
    btn_pos2 = Button(WIDTH//2 + 360, 555, 110, 40, "2号位", BLUE, WHITE)
    btn_pos3 = Button(WIDTH//2 + 480, 555, 110, 40, "3号位", BLUE, WHITE)
    btn_pos4 = Button(WIDTH//2 + 240, 605, 110, 40, "4号位", BLUE, WHITE)
    btn_pos5 = Button(WIDTH//2 + 360, 605, 110, 40, "5号位", BLUE, WHITE)
    btn_pos6 = Button(WIDTH//2 + 480, 605, 110, 40, "6号位", BLUE, WHITE)

    btn_pause = Button(WIDTH//2 - 190, 55, 100, 40, "暂停", BLUE, WHITE)
    btn_speed = Button(WIDTH//2 - 50, 55, 100, 40, "1倍速", GREEN, WHITE)
    btn_flee = Button(WIDTH//2 + 90, 55, 100, 40, "撤退", RED, WHITE)
    
    btn_return = Button(WIDTH//2 - 100, 450, 200, 50, "返回关卡", SHADOW_COLOR)

    gacha_pool = list(HERO_CONFIG.keys())
    gacha_result_msg, gacha_msg_timer, gacha_display_items, gacha_display_timer = "", 0, [], 0
    sys_msg_timer = 180 
    battle_timer = 0
    combat_log = []
    wrapped_combat_log = []   # 【新增】存储换行处理后的日志
    combat_log_idx = 0        # 【新增】记录已经处理到了第几条原日志
    floating_texts = []
    
    last_idle_tick = pygame.time.get_ticks()

    running = True
    while running:
        screen.fill(BG_COLOR)
        mouse_pos = pygame.mouse.get_pos()
        clicked = False
        current_ticks = pygame.time.get_ticks()

        # 挂机金币收益
        if current_ticks - last_idle_tick >= 1000:
            last_idle_tick = current_ticks
            game.gold += game.get_idle_rate()
        
        # 事件监听
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: clicked = True
            if event.type == pygame.MOUSEWHEEL and game.current_scene in ["BATTLE", "SETTLEMENT"]: 
                game.log_scroll_y += event.y * 20 

        # 顶部状态栏
        pygame.draw.rect(screen, TOP_BAR_COLOR, (0, 0, WIDTH, 50))
        draw_text(screen, f"金币: {game.gold} (+{game.get_idle_rate()}/s)", 30, 15, GOLD, True)
        draw_text(screen, f"当前关卡: 第 {game.level} 关", WIDTH//2, 15, WHITE, True, center=True)
        btn_save.draw(screen, mouse_pos)
        
        if clicked and btn_save.is_clicked(mouse_pos):
            game.sys_message = game.save_game()
            sys_msg_timer = 180

        if sys_msg_timer > 0 and game.sys_message:
            pygame.draw.rect(screen, (0, 0, 0, 180), (WIDTH//2 - 300, 60, 600, 40), border_radius=20)
            draw_text(screen, game.sys_message, WIDTH//2, 80, GOLD, center=True)
            sys_msg_timer -= 1

        # ================= 场景逻辑 =================

        # --- 关卡选择界面 ---
        if game.current_scene == "LEVEL":
            panel_rect = pygame.Rect(WIDTH//2 - 500, 110, 1000, 350)
            pygame.draw.rect(screen, PANEL_COLOR, panel_rect, border_radius=15)
            pygame.draw.rect(screen, SHADOW_COLOR, panel_rect, 2, border_radius=15)
            
            draw_text(screen, "【 我方阵容 】", WIDTH//2 - 250, 140, BLUE, True, center=True)
            for i in range(6):
                hero = game.deployed_party[i]
                col = 1 - (i // 3) 
                row = i % 3
                base_x = WIDTH//2 - 370 + col * 240
                base_y = 180 + row * 80
                if hero:
                    draw_text(screen, f"{i+1}号: {hero.name} (Lv.{hero.level} ★{hero.star})", base_x, base_y, BLACK, center=True)
                    stats_str = f"HP:{hero.max_hp} ATK:{hero.atk} DEF:{hero.defense}"
                    draw_text(screen, stats_str, base_x, base_y + 30, DARK_GRAY, center=True)
                else:
                    draw_text(screen, f"{i+1}号: （空缺）", base_x, base_y, BLACK, center=True)

            pygame.draw.line(screen, SHADOW_COLOR, (WIDTH//2, 120), (WIDTH//2, 450), 2)

            draw_text(screen, "【 敌方阵容 】", WIDTH//2 + 250, 140, RED, True, center=True)
            for i in range(6):
                col = i // 3
                row = i % 3
                base_x = WIDTH//2 + 130 + col * 240
                base_y = 180 + row * 80
                if i < len(game.current_enemy_configs):
                    e_conf = game.current_enemy_configs[i]
                    e_name = e_conf['name']
                    e_level = e_conf.get('level', 1)
                    e_star = e_conf.get('star', 1)
                    
                    # 抓取基础属性并动态计算当前等级的面板数据
                    base_info = HERO_CONFIG.get(e_name, {"hp": 50, "atk": 50, "def": 50})
                    disp_hp = Character.scale_stat(base_info["hp"], e_level, e_star)
                    disp_atk = Character.scale_stat(base_info["atk"], e_level, e_star)
                    disp_def = Character.scale_stat(base_info["def"], e_level, e_star)
                    
                    draw_text(screen, f"{i+1}号: {e_name} (Lv.{e_level} ★{e_star})", base_x, base_y, BLACK, center=True)
                    stats_str = f"HP:{disp_hp} ATK:{disp_atk} DEF:{disp_def}"
                    draw_text(screen, stats_str, base_x, base_y + 30, DARK_GRAY, center=True)
                else:
                    draw_text(screen, f"{i+1}号: （无）", base_x, base_y, DARK_GRAY, center=True)
            
            btn_fight.draw(screen, mouse_pos)
            
            if clicked and btn_fight.is_clicked(mouse_pos) and any(game.deployed_party):
                game.current_scene, game.battle_result, game.is_paused = "BATTLE", "", False
                game.turn_counter = 0 
                game.current_attacker, game.current_target = None, None 
                
                game.enemy_party = []
                for e_conf in game.current_enemy_configs:
                    e_name = e_conf["name"]
                    e_level = e_conf.get("level", 1)
                    e_star = e_conf.get("star", 1)
                    
                    e_base_info = HERO_CONFIG.get(e_name, {})
                    img_path = e_base_info.get("image", f"picture/{e_name}.png")
                    tag = e_base_info.get("tag", "普通")
                    
                    # 1. 传入图鉴里的基础属性来初始化实例
                    enemy = Character(
                        e_name,
                        img_path,
                        e_base_info.get("hp", 50),
                        e_base_info.get("atk", 50),
                        e_base_info.get("def", 50),
                        tag,
                        e_base_info.get("skill"),
                        e_base_info.get("skills"),
                    )
                    
                    # 2. 赋予配置好的等级和星级
                    enemy.level = e_level
                    enemy.star = e_star
                    
                    # 3. 重点：重置当前血量为计算后的最大血量
                    enemy.current_hp = enemy.max_hp 
                    
                    game.enemy_party.append(enemy)

                for h in game.deployed_party:
                    if h: h.reset_battle_state()
                refresh_skill_ready_highlights(game)
                
                combat_log = [[("===== 战斗正式开始 =====", BLACK)]]
                wrapped_combat_log = []   # 【新增】
                combat_log_idx = 0        # 【新增】
                floating_texts.clear()
                game.log_scroll_y = 0
                battle_timer = pygame.time.get_ticks()

        # --- 角色管理界面 ---
        elif game.current_scene == "HERO":
            display_list = game.display_heroes
            total_pages = max(1, math.ceil(len(display_list) / 6))
            draw_text(screen, f"角色图鉴 (第 {game.hero_page+1}/{total_pages} 页)", 50, 70, BLACK, True)
            
            start_idx = game.hero_page * 6
            display_width = 1140 
            start_x = (WIDTH - display_width) // 2 
            spacing = 190
            
            for i in range(start_idx, min(start_idx + 6, len(display_list))):
                x_pos = start_x + (i - start_idx) * spacing
                hero = display_list[i]
                
                card_rect = pygame.Rect(x_pos, 110, 170, 260) 
                
                if hero is None:
                    pygame.draw.rect(screen, PANEL_COLOR, card_rect, border_radius=10)
                    pygame.draw.rect(screen, SHADOW_COLOR, card_rect, 2, border_radius=10)
                    draw_text(screen, f"【{i+1} 号阵位】", x_pos+85, 200, BLUE, True, center=True)
                    draw_text(screen, "虚位以待", x_pos+85, 240, DARK_GRAY, center=True)
                else:
                    pygame.draw.rect(screen, PANEL_COLOR, card_rect, border_radius=10)
                    if i == game.current_hero_index: 
                        pygame.draw.rect(screen, RED, card_rect, 4, border_radius=10)
                    
                    scaled_img = pygame.transform.smoothscale(hero.image, (150, 200))
                    screen.blit(scaled_img, (x_pos+10, 120))
                    draw_hero_tag(screen, x_pos+10, 120, hero.tag)
                    
                    if hero in game.deployed_party: 
                        msg = f"在阵{game.deployed_party.index(hero)+1}号位"
                        overlay = pygame.Surface((170, 30), pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, 150)) 
                        screen.blit(overlay, (x_pos, 340)) 
                        draw_text(screen, msg, x_pos+85, 355, RED, True, center=True)
                
                if clicked and card_rect.collidepoint(mouse_pos): 
                    game.current_hero_index = i

            selected = game.get_active_hero()
            if selected:
                panel_left = WIDTH//2 - 600
                panel_top = 390
                panel_width = 1200
                panel_bottom = 660
                panel_height = panel_bottom - panel_top
                desc_x = WIDTH//2 - 570
                desc_max_width = (WIDTH//2 + 210) - desc_x - 30
                desc_line_height = 22
                divider_x = WIDTH//2 + 210

                btn_lvl_up.rect.topleft = (WIDTH//2 + 240, panel_top + 20)
                btn_star_up.rect.topleft = (WIDTH//2 + 360, panel_top + 20)
                btn_remove.rect.topleft = (WIDTH//2 + 480, panel_top + 20)
                btn_pos1.rect.topleft = (WIDTH//2 + 240, panel_top + 75)
                btn_pos2.rect.topleft = (WIDTH//2 + 360, panel_top + 75)
                btn_pos3.rect.topleft = (WIDTH//2 + 480, panel_top + 75)
                btn_pos4.rect.topleft = (WIDTH//2 + 240, panel_top + 125)
                btn_pos5.rect.topleft = (WIDTH//2 + 360, panel_top + 125)
                btn_pos6.rect.topleft = (WIDTH//2 + 480, panel_top + 125)

                pygame.draw.rect(screen, PANEL_COLOR, (panel_left, panel_top, panel_width, panel_height), border_radius=10)
                pygame.draw.rect(screen, SHADOW_COLOR, (panel_left, panel_top, panel_width, panel_height), 2, border_radius=10)
                
                draw_text(screen, f"【{selected.name}】  Lv.{selected.level}  |  定位: {selected.tag}", desc_x, panel_top + 15, BLUE, True)
                draw_text(screen, f"星级:★{selected.star}  |  碎片:{selected.duplicates}  |  血量:{selected.max_hp}  |  攻击:{selected.atk}  |  防御:{selected.defense}", desc_x, panel_top + 50, BLACK)
                current_y = panel_top + 90

                if selected.skills:
                    for idx, skill in enumerate(selected.skills):
                        draw_text(screen, f"技能{idx+1}: 【{skill['name']}】 (CD: {skill['cooldown']}回合)", desc_x, current_y, PURPLE, True)
                        current_y += 30
                        for line in wrap_text_lines(f"效果: {skill['desc']}", desc_max_width):
                            if current_y > panel_bottom - 18:
                                break
                            draw_text(screen, line, desc_x, current_y, DARK_GRAY)
                            current_y += desc_line_height
                        current_y += 8
                        if current_y > panel_bottom - 18:
                            break
                else:
                    draw_text(screen, "技能: 【普通攻击】", desc_x, current_y, DARK_GRAY, True)
                    current_y += 30
                    for line in wrap_text_lines("效果: 仅造成常规的物理伤害", desc_max_width):
                        if current_y > panel_bottom - 18:
                            break
                        draw_text(screen, line, desc_x, current_y, DARK_GRAY)
                        current_y += desc_line_height
                
                pygame.draw.line(screen, SHADOW_COLOR, (divider_x, panel_top + 10), (divider_x, panel_bottom - 10), 2)
                
                btn_lvl_up.draw(screen, mouse_pos)
                btn_star_up.draw(screen, mouse_pos)
                btn_remove.draw(screen, mouse_pos)
                btn_pos1.draw(screen, mouse_pos)
                btn_pos2.draw(screen, mouse_pos)
                btn_pos3.draw(screen, mouse_pos)
                btn_pos4.draw(screen, mouse_pos)
                btn_pos5.draw(screen, mouse_pos)
                btn_pos6.draw(screen, mouse_pos)
                
                if clicked:
                    if btn_lvl_up.is_clicked(mouse_pos) and game.gold >= 100: 
                        game.gold -= 100
                        selected.level += 1
                    elif btn_star_up.is_clicked(mouse_pos):
                        if selected.duplicates >= selected.star: 
                            selected.duplicates -= selected.star
                            selected.star += 1
                            game.sys_message = f"【{selected.name}】升星成功！"
                            sys_msg_timer = 120 
                        else:
                            game.sys_message = f"碎片不足！(当前:{selected.duplicates} / 需要:{selected.star})"
                            sys_msg_timer = 120 
                    elif btn_remove.is_clicked(mouse_pos): 
                        if selected in game.deployed_party: 
                            game.deployed_party[game.deployed_party.index(selected)] = None
                    elif btn_pos1.is_clicked(mouse_pos):
                        if selected in game.deployed_party: game.deployed_party[game.deployed_party.index(selected)] = None
                        game.deployed_party[0] = selected
                        game.current_hero_index, game.hero_page = 0, 0
                    elif btn_pos2.is_clicked(mouse_pos):
                        if selected in game.deployed_party: game.deployed_party[game.deployed_party.index(selected)] = None
                        game.deployed_party[1] = selected
                        game.current_hero_index, game.hero_page = 1, 0
                    elif btn_pos3.is_clicked(mouse_pos):
                        if selected in game.deployed_party: game.deployed_party[game.deployed_party.index(selected)] = None
                        game.deployed_party[2] = selected
                        game.current_hero_index, game.hero_page = 2, 0
                    elif btn_pos4.is_clicked(mouse_pos):
                        if selected in game.deployed_party: game.deployed_party[game.deployed_party.index(selected)] = None
                        game.deployed_party[3] = selected
                        game.current_hero_index, game.hero_page = 3, 0
                    elif btn_pos5.is_clicked(mouse_pos):
                        if selected in game.deployed_party: game.deployed_party[game.deployed_party.index(selected)] = None
                        game.deployed_party[4] = selected
                        game.current_hero_index, game.hero_page = 4, 0
                    elif btn_pos6.is_clicked(mouse_pos):
                        if selected in game.deployed_party: game.deployed_party[game.deployed_party.index(selected)] = None
                        game.deployed_party[5] = selected
                        game.current_hero_index, game.hero_page = 5, 0
            
            if clicked:
                if btn_prev_page.is_clicked(mouse_pos) and game.hero_page > 0: game.hero_page -= 1
                elif btn_next_page.is_clicked(mouse_pos) and game.hero_page < total_pages - 1: game.hero_page += 1
            
            if game.hero_page > 0: btn_prev_page.draw(screen, mouse_pos)
            if game.hero_page < total_pages - 1: btn_next_page.draw(screen, mouse_pos)

        # --- 角色召唤界面 ---
        elif game.current_scene == "GACHA":
            if gacha_display_timer > 0:
                gacha_display_timer -= 1
                if len(gacha_display_items) == 1:
                    img, name, is_new = gacha_display_items[0]
                    screen.blit(img, (WIDTH//2 - 90, 160))
                    color = GREEN if is_new else DARK_GRAY
                    tag = f"【新角色加入】 {name}" if is_new else f"【转化碎片+1】 {name}"
                    draw_text(screen, tag, WIDTH//2, 430, color, True, center=True)
                else:
                    for idx, (img, name, is_new) in enumerate(gacha_display_items):
                        row, col = divmod(idx, 5)
                        x, y = (WIDTH//2 - 475) + col * 190, 80 + row * 220
                        screen.blit(img, (x, y))
                        color = GREEN if is_new else DARK_GRAY
                        tag = "New!" if is_new else "碎片"
                        draw_text(screen, name, x + 60, y + 175, color, center=True)
                        draw_text(screen, tag, x + 60, y + 195, color, center=True)
            else:
                pygame.draw.circle(screen, (220, 230, 240), (WIDTH//2, 280), 180)
                pygame.draw.circle(screen, SHADOW_COLOR, (WIDTH//2, 280), 180, 4)
                pygame.draw.circle(screen, SHADOW_COLOR, (WIDTH//2, 280), 160, 2)
                draw_text(screen, "角色召唤池", WIDTH//2, 200, BLUE, True, center=True)
                draw_text(screen, "获得重复角色将自动转化为星级碎片", WIDTH//2, 260, DARK_GRAY, center=True)

            btn_draw_single.draw(screen, mouse_pos)
            btn_draw_ten.draw(screen, mouse_pos)
            
            if gacha_msg_timer > 0:
                draw_text(screen, gacha_result_msg, WIDTH//2, 520, RED, True, center=True)
                gacha_msg_timer -= 1
                
            if clicked:
                if btn_draw_single.is_clicked(mouse_pos):
                    if game.gold >= 500:
                        game.gold -= 500
                        chosen_name = random.choice(gacha_pool)
                        is_new = game.add_hero(chosen_name)
                        img = load_image(HERO_CONFIG[chosen_name]["image"], (180, 240))
                        gacha_display_items = [(img, chosen_name, is_new)]
                        gacha_display_timer = 180
                    else:
                        gacha_result_msg, gacha_msg_timer = "金币不足，无法进行单次召唤！", 120
                        
                elif btn_draw_ten.is_clicked(mouse_pos):
                    if game.gold >= 5000:
                        game.gold -= 5000
                        gacha_display_items = []
                        for _ in range(10):
                            chosen_name = random.choice(gacha_pool)
                            is_new = game.add_hero(chosen_name)
                            img = load_image(HERO_CONFIG[chosen_name]["image"], (120, 160))
                            gacha_display_items.append((img, chosen_name, is_new))
                        gacha_display_timer = 300 
                    else:
                        gacha_result_msg, gacha_msg_timer = "金币不足，无法进行十连召唤！", 120

        # --- 战斗过程界面 ---
        elif game.current_scene == "BATTLE":
            max_slots = max(len(game.deployed_party), len(game.enemy_party))
            current_round = (game.turn_counter // (max_slots * 2)) + 1
            MAX_ROUNDS = 30  # 战斗最大回合数 
            
            time_col = RED if current_round > MAX_ROUNDS - 5 else BLACK
            draw_text(screen, f"当前战斗: 第 {current_round}/{MAX_ROUNDS} 回合", WIDTH//2, 110, time_col, True, center=True)
            
            btn_pause.update_text("继续" if game.is_paused else "暂停")
            btn_pause.draw(screen, mouse_pos)
            btn_speed.update_text(f"{game.battle_speed}倍速") 
            btn_speed.draw(screen, mouse_pos)
            btn_flee.draw(screen, mouse_pos)
            
            log_rect = pygame.Rect(WIDTH//2 - 250, 130, 500, 540)
            
            # 渲染我方与敌方...
            for i in range(6):
                h = game.deployed_party[i]
                col, row = 1 - (i // 3), i % 3
                x_pos, y_pos = 40 + col * 150, 130 + row * 225  
                
                if h:
                    # 【新增】更新该角色的动画状态
                    h.update_anim()
                    # 【新增】计算最终渲染坐标
                    draw_x = x_pos + h.offset_x
                    draw_y = y_pos + h.offset_y
                    # 【修改】把下面所有的 x_pos 和 y_pos 替换为 draw_x 和 draw_y
                    pygame.draw.rect(screen, (230, 230, 230), (draw_x, draw_y, 130, 210), border_radius=8)
                    small_img = pygame.transform.smoothscale(h.image, (110, 145)) # 顺便应用之前提到的平滑缩放
                    screen.blit(small_img, (draw_x+10, draw_y+10))
                    if h.current_hp <= 0: 
                        overlay = pygame.Surface((110, 145), pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, 150))
                        screen.blit(overlay, (x_pos+10, y_pos+10))
                    elif h.stun_turns > 0:
                        draw_text(screen, "受控", x_pos+65, y_pos+80, PURPLE, True, center=True)
                    # 【新增】免控状态 UI 显示
                    elif h.immune_turns > 0:
                        draw_text(screen, "免控", x_pos+65, y_pos+80, GOLD, True, center=True)
                    
                    if h.skill_ready_highlight:
                        pygame.draw.rect(screen, GOLD, (draw_x - 2, draw_y - 2, 134, 214), 2, border_radius=10)
                    
                    if game.current_attacker == ('ally', i):
                        pygame.draw.rect(screen, BLUE, (x_pos, y_pos, 130, 210), 4, border_radius=8)
                    elif game.current_target == ('ally', i):
                        pygame.draw.rect(screen, RED, (x_pos, y_pos, 130, 210), 4, border_radius=8)
                        
                    draw_hero_tag(screen, x_pos+10, y_pos+10, h.tag)
                    draw_text(screen, h.name, x_pos+65, y_pos+165, BLUE, True, center=True) 
                    draw_hp_bar(screen, x_pos+10, y_pos+180, 110, 12, h.current_hp, h.max_hp)
                    draw_text(screen, f"攻:{h.atk} 防:{h.defense}", x_pos+65, y_pos+200, DARK_GRAY, center=True)
                else:
                    # 如果是空位，画原本的底框就行
                    pygame.draw.rect(screen, (230, 230, 230), (x_pos, y_pos, 130, 210), border_radius=8)

            for i, e in enumerate(game.enemy_party):
                col, row = i // 3, i % 3
                x_pos, y_pos = WIDTH - 330 + col * 150, 130 + row * 225  
                
                # 【新增】更新该敌方角色的动画状态 (平滑回弹)
                e.update_anim()
                
                # 【新增】计算最终渲染坐标，加上偏移量
                draw_x = x_pos + e.offset_x
                draw_y = y_pos + e.offset_y
                
                # 【修改】以下所有的坐标都改用 draw_x 和 draw_y
                pygame.draw.rect(screen, (245, 220, 220), (draw_x, draw_y, 130, 210), border_radius=8)
                
                # 【修改】顺便应用平滑缩放，解决图片噪点问题
                small_img = pygame.transform.smoothscale(e.image, (110, 145))
                screen.blit(small_img, (draw_x+10, draw_y+10))
                
                if e.current_hp <= 0: 
                    overlay = pygame.Surface((110, 145), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 150))
                    screen.blit(overlay, (draw_x+10, draw_y+10))
                elif e.stun_turns > 0: 
                    draw_text(screen, "受控", draw_x+65, draw_y+80, PURPLE, True, center=True)
                elif e.immune_turns > 0:  # 【保留】之前加的免控显示
                    draw_text(screen, "免控", draw_x+65, draw_y+80, GOLD, True, center=True)
                
                if e.skill_ready_highlight:
                    pygame.draw.rect(screen, GOLD, (draw_x - 2, draw_y - 2, 134, 214), 2, border_radius=10)
                
                if game.current_attacker == ('enemy', i):
                    pygame.draw.rect(screen, BLUE, (draw_x, draw_y, 130, 210), 4, border_radius=8)
                elif game.current_target == ('enemy', i):
                    pygame.draw.rect(screen, RED, (draw_x, draw_y, 130, 210), 4, border_radius=8)
                    
                draw_hero_tag(screen, draw_x+10, draw_y+10, e.tag)
                draw_text(screen, e.name, draw_x+65, draw_y+165, RED, True, center=True)
                draw_hp_bar(screen, draw_x+10, draw_y+180, 110, 12, e.current_hp, e.max_hp)
                draw_text(screen, f"攻:{e.atk} 防:{e.defense}", draw_x+65, draw_y+200, DARK_GRAY, center=True)

            # ====== 核心战斗调用 ======
            if not game.is_paused and current_ticks - battle_timer > 1000 / game.battle_speed:
                battle_timer = current_ticks
                process_turn(game, combat_log, floating_texts)

            if not any(e.current_hp > 0 for e in game.enemy_party): 
                game.battle_result = "WIN"
                game.current_scene = "SETTLEMENT"
            elif not any(h and h.current_hp > 0 for h in game.deployed_party): 
                game.battle_result = "LOSE"
                game.current_scene = "SETTLEMENT"
            elif current_round > MAX_ROUNDS: 
                game.battle_result = "DRAW"
                game.current_scene = "SETTLEMENT"

            if clicked:
                if btn_pause.is_clicked(mouse_pos): 
                    game.is_paused = not game.is_paused
                    battle_timer = current_ticks 
                elif btn_speed.is_clicked(mouse_pos):
                    if game.battle_speed == 1: game.battle_speed = 2
                    elif game.battle_speed == 2: game.battle_speed = 5
                    else: game.battle_speed = 1
                elif btn_flee.is_clicked(mouse_pos): 
                    game.battle_result = "FLEE"
                    game.current_scene = "SETTLEMENT"

            pygame.draw.rect(screen, PANEL_COLOR, log_rect, border_radius=10)
            pygame.draw.rect(screen, SHADOW_COLOR, log_rect, 2, border_radius=10)
            
            # ======== 动态折行处理 ========
            max_log_width = log_rect.width - 40 # 左右预留 20 的内边距
            
            # 只有产生新日志时，才会进行换行计算（极大提升帧率）
            while combat_log_idx < len(combat_log):
                raw_segments = combat_log[combat_log_idx]
                if not raw_segments:
                    wrapped_combat_log.append([]) # 空行保留
                else:
                    wrapped_lines = wrap_text_segments(raw_segments, max_log_width)
                    wrapped_combat_log.extend(wrapped_lines)
                combat_log_idx += 1

            # ======== 绘制框体与裁剪 ========
            pygame.draw.rect(screen, PANEL_COLOR, log_rect, border_radius=10)
            pygame.draw.rect(screen, SHADOW_COLOR, log_rect, 2, border_radius=10)
            
            screen.set_clip(log_rect)
            
            # 【重要】以排版后的 wrapped_combat_log 长度来计算滚动条
            max_scroll = min(0, log_rect.height - len(wrapped_combat_log) * 25 - 20)
            game.log_scroll_y = max(min(game.log_scroll_y, 0), max_scroll)
            
            # 渲染已排版的日志
            for i, log_segments in enumerate(wrapped_combat_log): 
                y_pos = log_rect.y + 10 + i * 25 + game.log_scroll_y
                if log_rect.y - 25 <= y_pos <= log_rect.bottom:
                    current_x = log_rect.x + 20
                    for text_part, text_color in log_segments:
                        img = font.render(text_part, True, text_color)
                        screen.blit(img, (current_x, y_pos))
                        current_x += img.get_width() 
                        
            screen.set_clip(None)
            
            for ft in floating_texts[:]:
                ft.update_and_draw(screen)
                if ft.life <= 0: floating_texts.remove(ft)
            
            if game.is_paused:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 100))
                pygame.draw.rect(overlay, (0, 0, 0, 0), log_rect)
                screen.blit(overlay, (0,0))
                draw_text(screen, "战斗暂停中...", WIDTH//2, 350, RED, True, center=True)

        # --- 战斗结算界面 ---
        elif game.current_scene == "SETTLEMENT":
            settle_rect = pygame.Rect(WIDTH//2 - 450, 60, 900, 420) 
            pygame.draw.rect(screen, PANEL_COLOR, settle_rect, border_radius=20)
            
            if game.battle_result == "WIN":
                pygame.draw.rect(screen, GOLD, settle_rect, 4, border_radius=20)
                draw_text(screen, " 战 斗 胜 利 ", WIDTH//2, 90, GREEN, True, center=True)
                draw_text(screen, f"获得战利品: {600 + game.level * 50} 金币", WIDTH//2, 130, GOLD, center=True)
            elif game.battle_result == "LOSE":
                pygame.draw.rect(screen, RED, settle_rect, 4, border_radius=20)
                draw_text(screen, " 战 斗 失 败 ", WIDTH//2, 90, RED, True, center=True)
            else:
                pygame.draw.rect(screen, DARK_GRAY, settle_rect, 4, border_radius=20)
                draw_text(screen, f" 战 斗 {game.battle_result} ", WIDTH//2, 90, DARK_GRAY, True, center=True)
            
            draw_text(screen, f"--- 我方战斗数据 ---", WIDTH//2 - 225, 170, DARK_GRAY, center=True)
            for idx, h in enumerate(game.deployed_party):
                if h:
                    y_pos = 200 + idx * 25
                    draw_text(screen, f"【{h.name}】 输出:{h.dmg_dealt}  承伤:{h.dmg_taken}  治疗:{h.heal_done}", WIDTH//2 - 225, y_pos, BLUE, center=True)

            pygame.draw.line(screen, DARK_GRAY, (WIDTH//2, 170), (WIDTH//2, 350), 2)
            
            draw_text(screen, f"--- 敌方战斗数据 ---", WIDTH//2 + 225, 170, DARK_GRAY, center=True)
            for idx, e in enumerate(game.enemy_party):
                y_pos = 200 + idx * 25
                draw_text(screen, f"【{e.name}】 输出:{e.dmg_dealt}  承伤:{e.dmg_taken}  治疗:{e.heal_done}", WIDTH//2 + 225, y_pos, RED, center=True)

            log_rect = pygame.Rect(WIDTH//2 - 500, 500, 1000, 170) 
            pygame.draw.rect(screen, PANEL_COLOR, log_rect, border_radius=10)
            pygame.draw.rect(screen, SHADOW_COLOR, log_rect, 2, border_radius=10)

            # ======== 动态折行处理 ========
            max_log_width = log_rect.width - 40 # 左右预留 20 的内边距
            
            # 只有产生新日志时，才会进行换行计算（极大提升帧率）
            while combat_log_idx < len(combat_log):
                raw_segments = combat_log[combat_log_idx]
                if not raw_segments:
                    wrapped_combat_log.append([]) # 空行保留
                else:
                    wrapped_lines = wrap_text_segments(raw_segments, max_log_width)
                    wrapped_combat_log.extend(wrapped_lines)
                combat_log_idx += 1

            # ======== 绘制框体与裁剪 ========
            pygame.draw.rect(screen, PANEL_COLOR, log_rect, border_radius=10)
            pygame.draw.rect(screen, SHADOW_COLOR, log_rect, 2, border_radius=10)
            
            screen.set_clip(log_rect)

            # 【重要】以排版后的 wrapped_combat_log 长度来计算滚动条
            max_scroll = min(0, log_rect.height - len(wrapped_combat_log) * 25 - 20)
            game.log_scroll_y = max(min(game.log_scroll_y, 0), max_scroll)
            
            # 渲染已排版的日志
            for i, log_segments in enumerate(wrapped_combat_log): 
                y_pos = log_rect.y + 10 + i * 25 + game.log_scroll_y
                if log_rect.y - 25 <= y_pos <= log_rect.bottom:
                    current_x = log_rect.x + 20
                    for text_part, text_color in log_segments:
                        img = font.render(text_part, True, text_color)
                        screen.blit(img, (current_x, y_pos))
                        current_x += img.get_width() 
                        
            screen.set_clip(None)

            btn_return.rect.y = 430 
            btn_return.draw(screen, mouse_pos)
            
            if clicked and btn_return.is_clicked(mouse_pos):
                if game.battle_result == "WIN": 
                    game.gold += 600 + game.level * 50
                    game.advance_level() 
                
                for h in game.deployed_party:
                    if h: h.reset_battle_state()

                game.current_scene = "LEVEL"

        if game.current_scene not in ["BATTLE", "SETTLEMENT"]:
            pygame.draw.rect(screen, (230, 235, 240), (0, HEIGHT - 120, WIDTH, 120))
            pygame.draw.line(screen, SHADOW_COLOR, (0, HEIGHT - 120), (WIDTH, HEIGHT - 120), 3)
            nav_level.draw(screen, mouse_pos)
            nav_hero.draw(screen, mouse_pos)
            nav_gacha.draw(screen, mouse_pos)
            
            if clicked:
                if nav_level.is_clicked(mouse_pos): game.current_scene = "LEVEL"
                elif nav_hero.is_clicked(mouse_pos): game.current_scene = "HERO"
                elif nav_gacha.is_clicked(mouse_pos): 
                    game.current_scene = "GACHA"
                    gacha_display_timer = 0 

        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
