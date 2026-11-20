# main.py  主程序的入口，负责场景显示、事件监听和整体渲染

import pygame
import random
import math
from config import *
from ui import *

# 以独立美术资源绘制按钮和窗口，点击行为保持一致。
Button = ArtButton

from models import Character, GameData
from battle import process_turn, refresh_skill_ready_highlights

MAX_ROUNDS = 30

def start_battle(game):
    game.current_scene, game.battle_result, game.is_paused = "BATTLE", "", False
    game.turn_counter, game.log_scroll_y = 0, 0
    game.current_attacker = game.current_target = None
    game.enemy_party = []
    for enemy_config in game.current_enemy_configs:
        if enemy_config is None:
            game.enemy_party.append(None)
            continue
        name = enemy_config["name"]
        base = HERO_CONFIG[name]
        enemy = Character(name, base["image"], base["hp"], base["atk"], base["def"],
                          base.get("tag", "普通"), base.get("skill"), base.get("skills"))
        enemy.level, enemy.star = enemy_config.get("level", 1), enemy_config.get("star", 1)
        enemy.reset_battle_state()
        game.enemy_party.append(enemy)
    for hero in game.deployed_party:
        if hero:
            hero.reset_battle_state()
    refresh_skill_ready_highlights(game)
    # 开战时预热动作贴图，后续命中帧只使用缓存。
    for enemy_side, party in ((False, game.deployed_party), (True, game.enemy_party)):
        for index, hero in enumerate(party):
            if hero:
                for pose in ("idle", "prepare", "release", "hit"):
                    battle_sprite(hero.name, hero.image_file, pose, index % 3, enemy_side)


def snapshot_team_status(game):
    # 回合先用原逻辑结算，演出在命中前暂时显示行动前的血量与状态。
    return {
        (side, index): (hero.current_hp, hero.stun_turns, hero.immune_turns, hero.skill_ready_highlight)
        for side, party in (("ally", game.deployed_party), ("enemy", game.enemy_party))
        for index, hero in enumerate(party) if hero
    }


class BattlePlayback:
    def __init__(self):
        self.elapsed = 0
        self.timer = 0
        self.duration = 640
        self.action = None
        self.before = {}
        self.texts = []
        self.log = [[("战斗开始", GOLD)]]
        self.pending_log = []

    @property
    def progress(self):
        return min(1, self.timer / self.duration) if self.action else 1

    def update(self, game, dt):
        if game.is_paused:
            return
        dt *= game.battle_speed
        self.elapsed += dt
        self.timer += dt
        if self.action and self.progress >= IMPACT_POINT and self.pending_log:
            self.log.extend(self.pending_log)
            self.pending_log.clear()
        if self.timer < self.duration:
            return

        # 先展示最后一次命中和倒地，再进入结算。
        if not any(hero and hero.current_hp > 0 for hero in game.enemy_party):
            game.battle_result = "WIN"
        elif not any(hero and hero.current_hp > 0 for hero in game.deployed_party):
            game.battle_result = "LOSE"
        elif game.turn_counter >= MAX_ROUNDS * 2 * max(len(game.deployed_party), len(game.enemy_party)):
            game.battle_result = "DRAW"
        if game.battle_result:
            game.current_scene = "SETTLEMENT"
            game.log_scroll_y = 0
            return

        self.timer = 0
        self.duration = 1000
        self.before = snapshot_team_status(game)
        self.texts.clear()
        self.action = process_turn(game, self.pending_log, self.texts)


def main():
    pygame.init()
    window = GameWindow()
    screen = window.canvas
    pygame.display.set_caption("卡牌放置·UI美化")
    clock = pygame.time.Clock()
    campaign = GameData()
    game = campaign
    # 沙盘独立持有角色和阵位，可在本次游戏期间反复试战。
    trial = GameData(load_progress=False)
    trial.current_enemy_configs = [None] * 6
    mode_button = Button(842, 577, 225, 60, "测试模式")
    
    # UI 按钮初始化
    nav_level = Button(WIDTH//2 - 350, 700, 200, 60, "战斗", WHITE)
    nav_hero = Button(WIDTH//2 - 100, 700, 200, 60, "角色", WHITE)
    nav_gacha = Button(WIDTH//2 + 150, 700, 200, 60, "召唤", WHITE)
    
    btn_fight = Button(WIDTH//2 - 120, 480, 240, 60, "开始战斗", RED, WHITE)
    btn_save = Button(990, 10, 132, 38, "进度保存", BLUE, WHITE)
    btn_quit = Button(1128, 10, 132, 38, "退出游戏", RED, WHITE)
    
    btn_draw_single = Button(WIDTH//2 - 250, 560, 200, 60, "单次召唤(500金)", GOLD, BLACK)
    btn_draw_ten = Button(WIDTH//2 + 50, 560, 200, 60, "十连召唤(5000金)", GOLD, BLACK)
    
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
    sys_msg_timer = 120 
    playback = None
    viewer = TestPicker()
    btn_enlarge = Button(535, 88, 180, 38, "放大查看")
    summon_index = 0
    combat_log = []
    wrapped_combat_log = []   # 【新增】存储换行处理后的日志
    combat_log_idx = 0        # 【新增】记录已经处理到了第几条原日志
    
    last_idle_tick = pygame.time.get_ticks()

    running = True
    while running:
        dt = clock.tick(60)
        screen.blit(scene_background(game.current_scene) if game.current_scene in {"LEVEL", "HERO", "GACHA"} else backdrop(), (0, 0))
        events = pygame.event.get()
        mouse_pos = window.to_game(pygame.mouse.get_pos())
        clicked = False
        current_ticks = pygame.time.get_ticks()

        # 挂机金币收益
        if current_ticks - last_idle_tick >= 1000:
            last_idle_tick = current_ticks
            campaign.gold += campaign.get_idle_rate()
        
        # 窗口打开或刚关闭的这一帧均拦截底层点击，避免误触。
        modal_frame = bool(viewer.kind)
        # 事件监听
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                break
            event = window.pointer_event(event)
            # 窗口控制在所有场景和弹窗中都可用，点击由顶栏消耗。
            left_down = event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
            if left_down and btn_quit.is_clicked(event.pos):
                running = False
                break
            if event.type == pygame.MOUSEWHEEL and not screen.get_rect().collidepoint(mouse_pos):
                continue
            if viewer.kind:
                viewer.handle(event, game)
                continue
            if modal_frame:
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game is trial and game.current_scene == "LEVEL":
                    position = next(((side, slot) for side in (False, True) for slot in range(6)
                                     if slot_rect(side, slot).collidepoint(event.pos)), None)
                    if position:
                        viewer.open_slot(trial, *position)
                        modal_frame, clicked = True, False
                        continue
                if game.current_scene == "HERO" and btn_enlarge.is_clicked(event.pos) and game.get_active_hero():
                    viewer.open_hero(game.get_active_hero())
                    modal_frame, clicked = True, False
                    continue
                if game.current_scene == "BATTLE" and BATTLE_LOG_RECT.collidepoint(event.pos):
                    viewer.open_log(game, playback.log)
                    modal_frame, clicked = True, False
                    continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                clicked = True
            if event.type == pygame.MOUSEWHEEL:
                if game.current_scene == "HERO" and CATALOG_AREA.collidepoint(mouse_pos):
                    game.catalog_offset = max(0, min(len(HERO_CONFIG) - 6, game.catalog_offset - event.y))
                elif game.current_scene == "BATTLE":
                    max_scroll = max(0, sum(bool(line) for line in playback.log) - 1) * 20
                    game.log_scroll_y = max(-max_scroll, min(0, game.log_scroll_y - event.y * 20))
                elif game.current_scene == "SETTLEMENT":
                    game.log_scroll_y += event.y * 20
        if not running:
            break
        # 美术页使用真实金币与关卡信息，战斗页维持高对比状态栏。
        if game is trial:
            glass(screen,(20,12,480,50))
            label(screen,"测试模式 · " + ("点击阵位配置双方角色" if game.current_scene == "LEVEL" else "模拟对战"),40,24,GILT,True)
        elif game.current_scene in {"LEVEL", "HERO", "GACHA"}:
            draw_header(screen,game)
        else:
            pygame.draw.rect(screen, TOP_BAR_COLOR, (0, 0, WIDTH, 50))
            draw_text(screen,f"金币 {game.gold:,}",30,14,GOLD)
            draw_text(screen,f"第 {game.level} 关",WIDTH//2,25,BLACK,True,center=True)
        if game is campaign:
            btn_save.draw(screen, mouse_pos)
        if game is campaign and clicked and btn_save.is_clicked(mouse_pos):
            game.sys_message = game.save_game()
            sys_msg_timer = 180

        # ================= 场景逻辑 =================

        # --- 关卡选择界面 ---
        if game.current_scene == "LEVEL":
            if clicked and mode_button.is_clicked(mouse_pos):
                game = trial if game is campaign else campaign
                clicked = False
            mode_button.update_text("退出测试" if game is trial else "测试模式")
            mode_button.draw(screen,mouse_pos)
            btn_fight.update_text("开始测试战斗" if game is trial else "开始战斗")
            draw_home(screen,game)
            btn_fight.rect=pygame.Rect(490,575,300,66)
            btn_fight.draw(screen,mouse_pos)
            if clicked and btn_fight.is_clicked(mouse_pos) and game is trial and not (any(game.deployed_party) and any(game.current_enemy_configs)):
                game.sys_message = "请为双方各配置至少一名角色"
                sys_msg_timer = 120
            elif clicked and btn_fight.is_clicked(mouse_pos) and any(game.deployed_party):
                start_battle(game)
                playback = BattlePlayback()
                combat_log = playback.log
                wrapped_combat_log = []
                combat_log_idx = 0

        # --- 角色管理界面 ---
        elif game.current_scene == "HERO":
            draw_hero_page(screen,game,mouse_pos,clicked,
                [btn_lvl_up,btn_star_up,btn_remove,btn_pos1,btn_pos2,btn_pos3,btn_pos4,btn_pos5,btn_pos6])
            selected=game.get_active_hero()
            if selected:
                btn_enlarge.draw(screen,mouse_pos)
                if clicked and selected in game.owned_heroes:
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
                    else:
                        # 换位时先释放原槽位，被替换角色仍保留在图鉴中。
                        for slot, button in enumerate((btn_pos1, btn_pos2, btn_pos3, btn_pos4, btn_pos5, btn_pos6)):
                            if button.is_clicked(mouse_pos):
                                if selected in game.deployed_party:
                                    game.deployed_party[game.deployed_party.index(selected)] = None
                                game.deployed_party[slot] = selected
                                break

        # --- 角色召唤界面 ---
        elif game.current_scene == "GACHA":
            if gacha_display_timer > 0:gacha_display_timer-=1
            summon_index = draw_summon(screen, gacha_display_items, gacha_display_timer, summon_index, mouse_pos, clicked)
            btn_draw_single.rect=pygame.Rect(365,620,240,58)
            btn_draw_ten.rect=pygame.Rect(675,620,240,58)
            btn_draw_single.draw(screen, mouse_pos)
            btn_draw_ten.draw(screen, mouse_pos)
            
            if gacha_msg_timer > 0:
                draw_text(screen, gacha_result_msg, WIDTH//2, 602, RED, True, center=True)
                gacha_msg_timer -= 1
                
            if clicked:
                if btn_draw_single.is_clicked(mouse_pos):
                    if game.gold >= 500:
                        game.gold -= 500
                        chosen_name = random.choice(gacha_pool)
                        is_new = game.add_hero(chosen_name)
                        summon_index = 0
                        gacha_display_items = [(chosen_name, is_new)]
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
                            gacha_display_items.append((chosen_name, is_new))
                        summon_index = 0
                        gacha_display_timer = 300 
                    else:
                        gacha_result_msg, gacha_msg_timer = "金币不足，无法进行十连召唤！", 120

        # --- 战斗过程界面 ---
        elif game.current_scene == "BATTLE":
            if clicked:
                if btn_pause.is_clicked(mouse_pos):
                    game.is_paused = not game.is_paused
                elif btn_speed.is_clicked(mouse_pos):
                    game.battle_speed = {1: 2, 2: 5, 5: 1}[game.battle_speed]
                elif btn_flee.is_clicked(mouse_pos):
                    # 撤退时保留已结算结果和完整记录。
                    playback.log.extend(playback.pending_log)
                    playback.pending_log.clear()
                    game.battle_result = "FLEE"
                    game.current_scene = "SETTLEMENT"
                    game.log_scroll_y = 0

            # 停在当前技能名上即可读完说明，移开后沿用玩家原先的暂停和倍速设置。
            battle_mouse = (-1, -1) if viewer.kind else mouse_pos
            if game.current_scene == "BATTLE" and not skill_banner_rect(playback.action).collidepoint(battle_mouse):
                playback.update(game, dt)

            progress = playback.progress
            before = playback.before if progress < IMPACT_POINT else {}
            draw_battlefield(screen, game, playback.elapsed, playback.action, progress, before, playback.texts,
                             battle_mouse)
            draw_battle_log(screen, combat_log, game.log_scroll_y)
            round_number = min(MAX_ROUNDS, game.turn_counter // (2 * max(len(game.deployed_party),
                                                                        len(game.enemy_party))) + 1)
            draw_text(screen, f"回合 {round_number:02d} / {MAX_ROUNDS}", 45, 65, GOLD)
            btn_pause.update_text("继续" if game.is_paused else "暂停")
            btn_speed.update_text(f"{game.battle_speed} 倍速")
            btn_pause.draw(screen, mouse_pos)
            btn_speed.draw(screen, mouse_pos)
            btn_flee.draw(screen, mouse_pos)
            if game.is_paused:
                draw_panel(screen, (WIDTH//2 - 98, 345, 196, 59), BG_COLOR, GOLD)
                draw_text(screen, "战斗暂停", WIDTH//2, 375, GOLD, True, center=True)

        # --- 战斗结算界面 ---
        elif game.current_scene == "SETTLEMENT":
            settle_rect = pygame.Rect(WIDTH//2 - 450, 60, 900, 420)
            title, result_color = {
                "WIN": ("战斗胜利", GOLD),
                "LOSE": ("战斗失败", RED),
                "DRAW": ("战斗平局", DARK_GRAY),
                "FLEE": ("已撤退", DARK_GRAY),
            }[game.battle_result]
            draw_panel(screen, settle_rect, PANEL_COLOR, result_color)
            draw_text(screen, title, WIDTH//2, 99, result_color, True, center=True)
            if game is campaign and game.battle_result == "WIN":
                draw_text(screen, f"获得战利品  {600 + game.level * 50:,} 金币",
                          WIDTH//2, 132, GOLD, center=True)

            draw_text(screen, "我方战斗数据", WIDTH//2 - 225, 170, DARK_GRAY, center=True)
            for idx, h in enumerate(game.deployed_party):
                if h:
                    y_pos = 200 + idx * 25
                    draw_text(screen, f"【{h.name}】 输出:{h.dmg_dealt}  承伤:{h.dmg_taken}  治疗:{h.heal_done}", WIDTH//2 - 225, y_pos, BLUE, center=True)

            pygame.draw.line(screen, DARK_GRAY, (WIDTH//2, 170), (WIDTH//2, 350), 2)
            
            draw_text(screen, "敌方战斗数据", WIDTH//2 + 225, 170, DARK_GRAY, center=True)
            for idx, e in enumerate(game.enemy_party):
                if e is None:
                    continue
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

            btn_return.update_text("返回测试布阵" if game is trial else "返回关卡")
            btn_return.rect.y = 430 
            btn_return.draw(screen, mouse_pos)
            
            if clicked and btn_return.is_clicked(mouse_pos):
                if game is campaign and game.battle_result == "WIN":
                    game.gold += 600 + game.level * 50
                    game.advance_level() 
                
                for h in game.deployed_party:
                    if h: h.reset_battle_state()

                game.current_scene = "LEVEL"

        if game is campaign and game.current_scene not in ["BATTLE", "SETTLEMENT"]:
            glass(screen,(250,690,780,82))
            nav_level.draw(screen, mouse_pos)
            nav_hero.draw(screen, mouse_pos)
            nav_gacha.draw(screen, mouse_pos)
            
            if clicked:
                if nav_level.is_clicked(mouse_pos): game.current_scene = "LEVEL"
                elif nav_hero.is_clicked(mouse_pos): game.current_scene = "HERO"
                elif nav_gacha.is_clicked(mouse_pos): 
                    game.current_scene = "GACHA"
 

        # 提示最后覆盖绘制，避免盖在场景面板后面。
        if sys_msg_timer > 0 and game.sys_message:
            glass(screen,(WIDTH//2-250,54,500,36))
            label(screen,game.sys_message,WIDTH//2,72,GILT,center=True)
            sys_msg_timer -= 1
        if viewer.kind:
            viewer.draw(screen, mouse_pos)
        btn_quit.draw(screen, mouse_pos)
        window.present()

    pygame.quit()

if __name__ == "__main__":
    main()
