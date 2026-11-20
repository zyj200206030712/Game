# battle.py  专门负责战斗核心逻辑与回合结算,zyj
import random
from dataclasses import dataclass, field
from config import *
from ui import FloatingText

def get_support_effect_value(multiplier, actor_value, target_value):
    return round(multiplier * (0.5 * actor_value + 0.5 * target_value))

@dataclass
class BattleAction:
    # 记录这次已结算行动的演出信息，保留原有数值和随机调用顺序。
    actor: tuple
    skill: str = ""
    targets: list = field(default_factory=list)
    hits: set = field(default_factory=set)
    controlled: bool = False
    # 随行动保存当次释放的技能说明，供演出悬停时查看。
    skill_description: str = ""


def effect_position(slot, is_enemy):
    x, y = battle_position(slot, is_enemy)
    return x, y - 106


def can_cast_skill_next_turn(character):
    return bool(character and character.current_hp > 0 and character.skills and any(cd <= 1 for cd in character.current_cds))

def get_castable_skill(actor):
    if not actor or not actor.skills:
        return None, None
    for idx, skill in enumerate(actor.skills):
        if actor.current_cds[idx] == 0:
            return idx, skill
    return None, None

def refresh_skill_ready_highlights(game):
    for character in list(game.deployed_party) + list(game.enemy_party):
        if character:
            character.skill_ready_highlight = can_cast_skill_next_turn(character)

def process_turn(game, combat_log, floating_texts):
    """
    执行一个战斗回合动作。
    自动检测攻击方、目标方，处理伤害、回血、Buff及控制结算，并返回日志。
    """
    action = None
    game.current_attacker = game.current_target = None
    acted = False
    max_slots = max(len(game.deployed_party), len(game.enemy_party))
    total_actions_per_round = max_slots * 2
    
    while not acted:
        # 判断是否某一方全灭
        if not any(e and e.current_hp > 0 for e in game.enemy_party) or not any(h and h.current_hp > 0 for h in game.deployed_party):
            break
        
        # 【关键修复】将回合判定移入循环内部，且在 turn_counter 递增之前
        if game.turn_counter % total_actions_per_round == 0:
            current_round = (game.turn_counter // total_actions_per_round) + 1
            
            # 统计双方当前总血量
            ally_total_hp = sum(h.current_hp for h in game.deployed_party if h and h.current_hp > 0)
            enemy_total_hp = sum(e.current_hp for e in game.enemy_party if e and e.current_hp > 0)

            combat_log.append([])
            combat_log.append([
                (f"第 {current_round} 回合", GOLD),
                (f" [我方:{ally_total_hp}HP vs 敌方:{enemy_total_hp}HP] ", BLUE)
            ])

        slot = (game.turn_counter // 2) % max_slots
        is_enemy = (game.turn_counter % 2) == 1
        game.turn_counter += 1 
        
        actor = None
        actor_faction_color = BLACK
        actor_color = BLACK
        faction_label = ""

        if not is_enemy:
            if slot < len(game.deployed_party):
                actor = game.deployed_party[slot]
                actor_faction_color, actor_color, faction_label = BLACK, BLUE, "我方 "
                game.current_attacker = ('ally', slot)
        else:
            if slot < len(game.enemy_party):
                actor = game.enemy_party[slot]
                actor_faction_color, actor_color, faction_label = BLACK, RED, "敌方 "
                game.current_attacker = ('enemy', slot)

        if actor and actor.current_hp > 0:
            actor.current_cds = [max(0, cd - 1) for cd in actor.current_cds]

            action = BattleAction(game.current_attacker)

            # 【新增】回合开始时，减少免控回合数
            if actor.immune_turns > 0:
                actor.immune_turns -= 1
            
            # 结算控制
            if actor.stun_turns > 0:
                action.controlled = True
                actor.stun_turns -= 1
                combat_log.append([
                    (f"> {faction_label}", actor_faction_color), 
                    (actor.name, actor_color), 
                    (" 处于受控状态无法行动！", PURPLE)
                ])
                acted = True 
            else:
                # 技能释放判定
                skill_idx, skill = get_castable_skill(actor)
                if skill:
                    action.skill = skill["name"]
                    action.skill_description = skill.get("desc", "")
                    actor.current_cds[skill_idx] = skill.get("cooldown", 3)
                    
                    combat_log.append([
                        (f"> {faction_label}", actor_faction_color), (actor.name, actor_color), 
                        (" 发动了技能 ", BLACK), (f"【{skill['name']}】", PURPLE), ("!", BLACK)
                    ])

                    skill_target = skill.get("target", "enemy_single")
                    real_targets = []
                    
                    ally_pool = [h for h in (game.deployed_party if not is_enemy else game.enemy_party) if h and h.current_hp > 0]
                    dead_ally_pool = [h for h in (game.deployed_party if not is_enemy else game.enemy_party) if h and h.current_hp <= 0]
                    enemy_pool = [e for e in (game.enemy_party if not is_enemy else game.deployed_party) if e and e.current_hp > 0]

                    # ================= 敌方目标系列 =================
                    if skill_target == "enemy_front" and enemy_pool:
                        # 默认敌方第一顺位 (前排/承伤位)
                        real_targets = [enemy_pool[0]]
                    elif skill_target == "enemy_back" and enemy_pool:
                        # 敌方最后顺位 (切后排)
                        real_targets = [enemy_pool[-1]]
                    elif skill_target == "enemy_lowest_hp" and enemy_pool:
                        # 敌方血量百分比最低 (残血收割)
                        real_targets = [min(enemy_pool, key=lambda x: x.current_hp / x.max_hp)]
                    elif skill_target == "enemy_highest_hp" and enemy_pool:
                        # 敌方血量百分比最高 (巨人杀手)
                        real_targets = [max(enemy_pool, key=lambda x: x.current_hp / x.max_hp)]
                    elif skill_target == "enemy_highest_atk" and enemy_pool:
                        # 敌方攻击最高 (擒贼擒王/针对输出)
                        real_targets = [max(enemy_pool, key=lambda x: x.atk)]
                    elif skill_target == "enemy_highest_def" and enemy_pool:
                        # 敌方防御最高 (魔王之盾/针对输出)
                        real_targets = [max(enemy_pool, key=lambda x: x.defense)]
                    elif skill_target == "enemy_random" and enemy_pool:
                        # 敌方随机单体 (不可控/混乱打击)
                        real_targets = [random.choice(enemy_pool)]
                    elif skill_target == "enemy_aoe" and enemy_pool:
                        # 敌方全体
                        real_targets = enemy_pool

                    # ================= 我方目标系列 =================
                    elif skill_target == "ally_lowest_hp" and ally_pool:
                        # 我方血量百分比最低 (精准急救)
                        real_targets = [min(ally_pool, key=lambda x: x.current_hp / x.max_hp)]
                    elif skill_target == "ally_highest_atk" and ally_pool:
                        # 我方攻击最高 (精准辅助/挂Buff)
                        real_targets = [max(ally_pool, key=lambda x: x.atk)]
                    elif skill_target == "ally_lowest_def" and ally_pool:
                        # 我方防御最低 (防弹专家)
                        real_targets = [min(ally_pool, key=lambda x: x.defense)]
                    elif skill_target == "ally_random" and ally_pool:
                        # 我方随机单体 (不可控/混乱打击)
                        real_targets = [random.choice(ally_pool)]
                    elif skill_target == "ally_aoe" and ally_pool:
                        # 我方全体 (群体恢复/群体增益)
                        real_targets = ally_pool
                    elif skill_target == "ally_dead_random" and dead_ally_pool:
                        # 我方随机阵亡单位 (单体复活)
                        real_targets = [random.choice(dead_ally_pool)]
                    elif skill_target == "ally_dead_aoe" and dead_ally_pool:
                        # 我方全部阵亡单位 (群体复活)
                        real_targets = dead_ally_pool
                    
                    # ================= 自身 =================
                    elif skill_target == "self":
                        # 目标自身 (自我强化/吸血护盾等)
                        real_targets = [actor]

                    # 容错机制：如果配置写错或者未找到目标，但技能是对敌的，默认打前排
                    if not real_targets and enemy_pool and "enemy" in skill_target:
                        real_targets = [enemy_pool[0]]

                    for t in real_targets:
                        t_is_enemy = t in game.enemy_party
                        t_color = RED if t_is_enemy else BLUE
                        t_idx = game.enemy_party.index(t) if t_is_enemy else game.deployed_party.index(t)
                        game.current_target = ('enemy' if t_is_enemy else 'ally', t_idx)
                        action.targets.append(game.current_target)
                        actor_fx_x, actor_fx_y = effect_position(slot, is_enemy)
                        base_x, base_y = effect_position(t_idx, t_is_enemy)

                        msg_parts = []
                        float_delay = 0 
                        last_damage_dealt = 0

                        for effect in skill.get("effects", []):
                            e_type = effect.get("type")
                            mult = effect.get("multiplier", 1.0)
                            
                            if e_type == "damage":
                                dmg = t.take_damage(round(actor.atk * mult))
                                last_damage_dealt = dmg
                                actor.dmg_dealt += dmg
                                action.hits.add(game.current_target)
                                msg_parts.append((f"受到 {dmg} 伤害", BLACK))
                                floating_texts.append(FloatingText(base_x + random.randint(-15, 15), base_y + float_delay, f"-{dmg}", PURPLE))
                                float_delay -= 25

                            elif e_type == "lifesteal":
                                if last_damage_dealt > 0:
                                    heal_amt = round(last_damage_dealt * mult)
                                    actual_heal = min(actor.max_hp - actor.current_hp, heal_amt)
                                    if actual_heal > 0:
                                        actor.current_hp += actual_heal
                                        actor.heal_done += actual_heal
                                        msg_parts.append((f"{actor.name} 吸血 {actual_heal} 生命", GREEN))
                                        floating_texts.append(FloatingText(actor_fx_x + random.randint(-15, 15), actor_fx_y + float_delay, f"+{actual_heal}", GREEN))
                                        float_delay -= 25
                                
                            elif e_type == "heal":
                                heal_amt = get_support_effect_value(mult, actor.max_hp, t.max_hp)
                                actual_heal = min(t.max_hp - t.current_hp, heal_amt)
                                t.current_hp += actual_heal
                                actor.heal_done += actual_heal
                                msg_parts.append((f"恢复 {actual_heal} 生命", GREEN))
                                floating_texts.append(FloatingText(base_x, base_y + float_delay, f"+{actual_heal}", GREEN))
                                float_delay -= 25

                            elif e_type == "resurrect":
                                if t.current_hp <= 0:
                                    t.reset_on_resurrect()
                                    revive_hp = max(1, get_support_effect_value(mult, actor.max_hp, t.max_hp))
                                    actual_revive_hp = min(t.max_hp, revive_hp)
                                    t.current_hp = actual_revive_hp
                                    actor.heal_done += actual_revive_hp
                                    msg_parts.append((f"复活并恢复 {actual_revive_hp} 生命", GREEN))
                                    floating_texts.append(FloatingText(base_x, base_y + float_delay, f"+{actual_revive_hp}", GREEN))
                                    float_delay -= 25
                                
                            elif e_type == "buff":
                                stats = [s.strip() for s in effect.get("stat", "").split(",")]
                                for stat in stats:
                                    if stat == "atk":
                                        val = get_support_effect_value(mult, actor.atk, t.atk)
                                        t.battle_atk_bonus += val
                                        msg_parts.append((f"攻击提升{val}", GOLD))
                                        floating_texts.append(FloatingText(base_x, base_y + float_delay, "攻击提升", GOLD))
                                    elif stat == "def":
                                        val = get_support_effect_value(mult, actor.defense, t.defense)
                                        t.battle_def_bonus += val
                                        msg_parts.append((f"防御提升{val}", GOLD))
                                        floating_texts.append(FloatingText(base_x, base_y + float_delay, "防御提升", GOLD))
                                    float_delay -= 25
                                    
                            elif e_type == "debuff":
                                stats = [s.strip() for s in effect.get("stat", "").split(",")]
                                for stat in stats:
                                    if stat == "atk":
                                        val = get_support_effect_value(mult, actor.atk, t.atk)
                                        t.battle_atk_bonus -= val
                                        msg_parts.append((f"攻击下降{val}", PURPLE))
                                        floating_texts.append(FloatingText(base_x, base_y + float_delay, "攻击下降", PURPLE))
                                    elif stat == "def":
                                        val = get_support_effect_value(mult, actor.defense, t.defense)
                                        t.battle_def_bonus -= val
                                        msg_parts.append((f"防御下降{val}", PURPLE))
                                        floating_texts.append(FloatingText(base_x, base_y + float_delay, "防御下降", PURPLE))
                                    float_delay -= 25
                                    
                            elif e_type == "control":
                                # 【修改】施加控制前先判断是否有免控状态
                                if t.immune_turns > 0:
                                    msg_parts.append(("免疫了控制", GOLD))
                                    floating_texts.append(FloatingText(base_x, base_y + float_delay, "免疫!", GOLD))
                                else:
                                    dur = effect.get("duration", 1)
                                    t.stun_turns = max(t.stun_turns, dur)
                                    msg_parts.append((f"受控{dur}回合", PURPLE))
                                    floating_texts.append(FloatingText(base_x, base_y + float_delay, "受控!", PURPLE))
                                float_delay -= 25
                            # 【新增】免控及解控技能逻辑
                            elif e_type == "immune":
                                dur = effect.get("duration", 2)
                                t.immune_turns = max(t.immune_turns, dur) # 刷新/覆盖免控持续时间
                                
                                # 立即解除已有的控制状态
                                if t.stun_turns > 0:
                                    t.stun_turns = 0
                                    msg_parts.append(("解除了控制", GREEN))
                                    floating_texts.append(FloatingText(base_x + random.randint(-10, 10), base_y + float_delay, "解控!", GREEN))
                                    float_delay -= 25
                                    
                                msg_parts.append((f"获得免控{dur}回合", GOLD))
                                floating_texts.append(FloatingText(base_x, base_y + float_delay, "免控!", GOLD))
                                float_delay -= 25

                        if msg_parts:
                            log_entry = [("  - ", BLACK), (t.name, t_color)]
                            for idx, (txt, col) in enumerate(msg_parts):
                                log_entry.append((f" {txt}", col))
                                if idx < len(msg_parts) - 1:
                                    log_entry.append((",", BLACK))
                            log_entry.append(("！", BLACK))
                            combat_log.append(log_entry)

                        if t.current_hp <= 0:
                            combat_log.append([("  [击杀] ", RED), (t.name, t_color), (" 阵亡了！", DARK_GRAY)])
                
                # 普通攻击判定
                else:
                    enemy_pool = [e for e in (game.enemy_party if not is_enemy else game.deployed_party) if e and e.current_hp > 0]
                    if enemy_pool:
                        target = enemy_pool[0]
                        dmg = target.take_damage(actor.atk)
                        actor.dmg_dealt += dmg  
                        
                        t_is_enemy = target in game.enemy_party
                        t_color = RED if t_is_enemy else BLUE
                        t_idx = game.enemy_party.index(target) if t_is_enemy else game.deployed_party.index(target)
                        game.current_target = ('enemy' if t_is_enemy else 'ally', t_idx)
                        action.targets.append(game.current_target)
                        action.hits.add(game.current_target)

                        combat_log.append([
                            (f"> {faction_label}", actor_faction_color), (actor.name, actor_color), (" 普攻 ", BLACK), 
                            (target.name, t_color), (f" 造成 {dmg} 伤害！", BLACK)
                        ])
                        
                        if target.current_hp <= 0:
                            combat_log.append([("  [击杀] ", RED), (target.name, t_color), (" 阵亡了！", DARK_GRAY)])
                        
                        base_x, base_y = effect_position(t_idx, t_is_enemy)
                        floating_texts.append(FloatingText(base_x + random.randint(-15, 15), base_y, f"-{dmg}", BLACK))
                
                acted = True

    refresh_skill_ready_highlights(game)
    return action
