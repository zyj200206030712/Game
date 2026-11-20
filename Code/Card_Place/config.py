# config.py  存放所有静态配置（颜色、常量、角色属性、关卡阵容）
# ================= 1. 基础配置 =================
WIDTH, HEIGHT = 1280, 800  
# 明亮的银蓝背景、象牙白面板与暖金装饰，文字使用深色保证对比度。
WHITE, BLACK, BG_COLOR = (255, 253, 247), (34, 51, 71), (205, 222, 237)
TOP_BAR_COLOR, PANEL_COLOR, SHADOW_COLOR = (229, 238, 246), (250, 247, 238), (169, 147, 101)
DARK_GRAY, RED, GREEN, BLUE, GOLD = (80, 97, 115), (166, 55, 53), (35, 116, 87), (35, 100, 143), (126, 89, 29)
PURPLE = (112, 65, 145)


def formation_position(slot, is_enemy):
    # 我方右列、敌方左列为前排，与战斗位置的空间关系一致。
    column = slot // 3 if is_enemy else 1 - slot // 3
    return (689 if is_enemy else 99) + column * 249, 194 + (slot % 3) * 90


# 槽位 1–3 为前排，4–6 为后排，画面依然与原有行动顺序一致。
def battle_position(slot, is_enemy):
    # 交错纵深让放大的人物仍有独立轮廓，普通攻击可进入中央交战区。
    positions = ((420, 351), (352, 523), (438, 715),
                 (166, 329), (128, 497), (190, 692))
    x, y = positions[slot]
    return (WIDTH - x if is_enemy else x), y


# 角色与技能配置（hp:100~1000, atk:10~100, def:10~100；角色可使用单个 skill 或 skills 列表；skills 中每个技能可配置 priority，优先级越高越先释放；damage类multiplier按施法者攻击结算；heal/buff/debuff按施法者与目标各50%的对应属性混合结算；lifesteal按刚造成的实际伤害 * multiplier 回血；resurrect按施法者与目标各50%最大生命值混合后 * multiplier 复活，并重置目标战斗态，cd）
HERO_CONFIG = {
    "安迷修": {
        "image": "picture/安迷修铠.png", "hp": 500, "atk": 50, "def": 60, "tag": "单体减攻",
        "skill": {
            "name": "紫鳞刺", "target": "enemy_highest_atk", "cooldown": 3, 
            "desc": "发动刺击，降低敌方攻击最高的单体：安迷修与目标攻击力均值的30%的攻击值",
            "effects": [{"type": "debuff", "stat": "atk", "multiplier": 0.3}]
        }
    },
    "暗魂": {
        "image": "picture/暗系魂铠.png", "hp": 500, "atk": 50, "def": 60, "tag": "单体减防",
        "skill": {
            "name": "暗影侵蚀", "target": "enemy_highest_def", "cooldown": 3, 
            "desc": "发动暗影之力，降低敌方防御力最高的单体：暗魂与目标防御力均值的30%的防御值",
            "effects": [{"type": "debuff", "stat": "def", "multiplier": 0.3}]
        }
    },
    "净世圣女": {
        "image": "picture/白皇铠.png", "hp": 300, "atk": 10, "def": 40, "tag": "群体免控",
        "skill": {
            "name": "天降甘霖", "target": "ally_aoe", "cooldown": 12, 
            "desc": "洗涤一切污秽，解除我方全体的控制状态并附加2回合免控",
            "effects": [{"type": "immune", "duration": 2}]
        }
    },
    "白骨夫人": {
        "image": "picture/白灵.png", "hp": 400, "atk": 70, "def": 40, "tag": "后排杀手",
        "skill": {
            "name": "骨杀·刺", "target": "enemy_back", "cooldown": 2, 
            "desc": "瞬间化作骨影绕到敌方最后排，对敌方最后排单体造成白骨夫人200%攻击力的伤害",
            "effects": [{"type": "damage", "multiplier": 2.0}]
        }
    },
    "冰云剑仙": {
        "image": "picture/冰系魂铠.png", "hp": 400, "atk": 70, "def": 40, "tag": "群体伤害",
        "skill": {
            "name": "万剑霜华", "target": "enemy_aoe", "cooldown": 4, 
            "desc": "霜华剑气席卷战场，对敌方全体造成冰云剑仙70%攻击力的冰冻剑伤",
            "effects": [{"type": "damage", "multiplier": 0.70}]
        }
    },
    "魅狐妖姬": {
        "image": "picture/妲己.png", "hp": 400, "atk": 20, "def": 40, "tag": "群体短控",
        "skill": {
            "name": "倾城乱心", "target": "enemy_aoe", "cooldown": 6, 
            "desc": "睁开狐媚之眼，魅惑敌方全体1回合",
            "effects": [{"type": "control", "duration": 1}]
        }
    },
    "帝皇": {
        "image": "picture/帝皇铠.png", "hp": 999, "atk": 99, "def": 99, "tag": "群体伤害",
        "skill": {
            "name": "五圣·乾坤破", "target": "enemy_aoe", "cooldown": 9, 
            "desc": "汇聚五圣之力，对敌方全体造成帝皇99%攻击力的毁灭性伤害",
            "effects": [{"type": "damage", "multiplier": 0.99}]
        }
    },
    "五灵龙神": {
        "image": "picture/帝皇神.png", "hp": 555, "atk": 55, "def": 55, "tag": "全能对群",
        "skill": {
            "name": "五行·八卦阵", "target": "enemy_aoe", "cooldown": 21, 
            "desc": "对敌方全体造成：五灵龙神50%攻击力的伤害、1回合束缚，五灵龙神与目标各攻击力均值和防御力均值的10%的两项属性值降低",
            "effects": [
                {"type": "damage", "multiplier": 0.5},
                {"type": "control", "duration": 1},
                {"type": "debuff", "stat": "atk, def", "multiplier": 0.1}
            ]
        }
    },
    "毒孤博": {
        "image": "picture/毒系魂铠.png", "hp": 400, "atk": 40, "def": 60, "tag": "群体减益",
        "skill": {
            "name": "紫魂毒雾", "target": "enemy_aoe", "cooldown": 24, 
            "desc": "布下毒雾使敌方全体中毒，降低敌方全体：毒孤博与目标攻击力均值和防御力均值的20%的两项属性值",
            "effects": [{"type": "debuff", "stat": "atk, def", "multiplier": 0.2}]
        }
    },
    "小花仙": {
        "image": "picture/粉仙子.png", "hp": 300, "atk": 10, "def": 20, "tag": "群体回血",
        "skill": {
            "name": "繁花映血", "target": "ally_aoe", "cooldown": 12, 
            "desc": "唤起生命花海，为我方全体恢复：小花仙与目标各最大生命值均值的20%的血量",
            "effects": [{"type": "heal", "multiplier": 0.2}]
        }
    },
    "光明神王": {
        "image": "picture/光明神王.png", "hp": 700, "atk": 70, "def": 70, "tag": "群体伤害",
        "skill": {
            "name": "圣光·审魔斩", "target": "enemy_aoe", "cooldown": 4, 
            "desc": "汇聚圣光之力，对敌方全体造成光明神王70%攻击力的光属性剑伤",
            "effects": [{"type": "damage", "multiplier": 0.7}]
        }
    },
    "艾莎": {
        "image": "picture/寒冰界王.png", "hp": 300, "atk": 30, "def": 30, "tag": "群体长控",
        "skill": {
            "name": "凛冬·归寂", "target": "enemy_aoe", "cooldown": 18, 
            "desc": "制造寒冰领域，冰冻敌方全体3回合",
            "effects": [{"type": "control", "duration": 3}]
        }
    },
    "黑迪": {
        "image": "picture/黑暗界王.png", "hp": 900, "atk": 60, "def": 60, "tag": "群体减攻",
        "skill": {
            "name": "黑暗本源", "target": "enemy_aoe", "cooldown": 12, 
            "desc": "发动黑暗本源之力，降低敌方全体：黑迪与目标各50%攻击力混合后20%的攻击值",
            "effects": [{"type": "debuff", "stat": "atk", "multiplier": 0.2}]
        }
    },
    "黑骑女将": {
        "image": "picture/黑骑女将.png", "hp": 400, "atk": 80, "def": 50, "tag": "坦克杀手",
        "skill": {
            "name": "骑士战魂", "target": "enemy_highest_hp", "cooldown": 3, 
            "desc": "燃烧灵魂进入战斗状态，对敌方血量百分比最高的目标造成黑骑女将300%攻击力的伤害",
            "effects": [{"type": "damage", "multiplier": 3.0}]
        }
    },
    "极光神使": {
        "image": "picture/极光界王.png", "hp": 600, "atk": 50, "def": 70, "tag": "群体加攻",
        "skill": {
            "name": "极光之辉", "target": "ally_aoe", "cooldown": 12, 
            "desc": "召唤极光星辰之力，提升我方全体：极光神使与目标各50%攻击力混合后20%的攻击值",
            "effects": [{"type": "buff", "stat": "atk", "multiplier": 0.2}]
        }
    },
    "精灵公主": {
        "image": "picture/精灵公主.png", "hp": 400, "atk": 60, "def": 45, "tag": "连击前单",
        "skill": {
            "name": "森之箭", "target": "enemy_front", "cooldown": 1, 
            "desc": "射出箭矢，对敌方最前排单体目标造成精灵公主199%攻击力的伤害",
            "effects": [{"type": "damage", "multiplier": 1.99}]
        }
    }, 
    "巨甲象": {
        "image": "picture/巨甲象灵.png", "hp": 999, "atk": 60, "def": 80, "tag": "前排回血",
        "skill": {
            "name": "不屈意志", "target": "self", "cooldown": 5, 
            "desc": "唤醒古山之志，恢复自身：最大生命值50%的血量",
            "effects": [{"type": "heal", "multiplier": 0.5}]
        }
    },
    "巨爪熊": {
        "image": "picture/巨爪熊.png", "hp": 800, "atk": 60, "def": 60, "tag": "本体强化",
        "skill": {
            "name": "蛮熊震怒", "target": "self", "cooldown": 4, 
            "desc": "进入红眼暴走状态，提升自身20%的攻击力和防御力",
            "effects": [{"type": "buff", "stat": "atk, def", "multiplier": 0.2}]
        }
    },
    "库忿斯": {
        "image": "picture/库忿斯铠.png", "hp": 600, "atk": 60, "def": 70, "tag": "本体强化",
        "skill": {
            "name": "地狱之血", "target": "self", "cooldown": 10, 
            "desc": "燃烧精血，提升自身50%的攻击力和防御力",
            "effects": [{"type": "buff", "stat": "atk, def", "multiplier": 0.5}]
        }
    },
    "傀儡女王": {
        "image": "picture/傀儡界王.png", "hp": 200, "atk": 90, "def": 20, "tag": "残血收割",
        "skill": {
            "name": "幽冥·瞬狱杀", "target": "enemy_lowest_hp", "cooldown": 1, 
            "desc": "召唤骷髅头，对敌方血量百分比最低的单体造成傀儡女王100%攻击力的致命打击",
            "effects": [{"type": "damage", "multiplier": 1.0}]
        }
    },
    "七彩鲲鹏": {
        "image": "picture/鲲鹏灵.png", "hp": 600, "atk": 50, "def": 70, "tag": "单体治疗",
        "skill": {
            "name": "扶摇直上", "target": "ally_lowest_hp", "cooldown": 5, 
            "desc": "天降祥瑞，恢复我方血量百分比最低的单体：七彩鲲鹏与目标各50%最大生命值混合后50%的血量",
            "effects": [{"type": "heal", "multiplier": 0.5}]
        }
    },
    "金甲骑士": {
        "image": "picture/路法铠.png", "hp": 600, "atk": 60, "def": 70, "tag": "前排加防",
        "skill": {
            "name": "不灭金魂", "target": "self", "cooldown": 5, 
            "desc": "金光一闪，增加自身30%的防御值",
            "effects": [{"type": "buff", "stat": "def", "multiplier": 0.3}]
        }
    },
    "美杜莎": {
        "image": "picture/美杜莎.png", "hp": 400, "atk": 40, "def": 50, "tag": "群体减防",
        "skill": {
            "name": "美杜莎凝望", "target": "enemy_aoe", "cooldown": 12, 
            "desc": "眼神震慑，降低敌方全体：美杜莎与目标各50%防御力混合后20%的防御值",
            "effects": [{"type": "debuff", "stat": "def", "multiplier": 0.2}]
        }
    },
    "紫萱": {
        "image": "picture/能量界王.png", "hp": 300, "atk": 40, "def": 40, "tag": "群体强化",
        "skill": {
            "name": "星华焕彩", "target": "ally_aoe", "cooldown": 24, 
            "desc": "星光落下，提升我方全体：紫萱与目标攻击力均值和防御力均值的20%的属性值",
            "effects": [{"type": "buff", "stat": "atk, def", "multiplier": 0.2}]
        }
    },
    "女武神": {
        "image": "picture/女帝甲灵.png", "hp": 300, "atk": 10, "def": 60, "tag": "单体加防",
        "skill": {
            "name": "武神降临", "target": "ally_lowest_def", "cooldown": 4, 
            "desc": "召唤武神附身我方防御最低的单体，提升其：女武神与目标防御力均值的40%的防御值",
            "effects": [{"type": "buff", "stat": "def", "multiplier": 0.4}]
        }
    },
    "殿主": {
        "image": "picture/女皇铠.png", "hp": 200, "atk": 40, "def": 40, "tag": "单体控制",
        "skill": {
            "name": "天使之息", "target": "enemy_random", "cooldown": 2, 
            "desc": "召唤天使呼出天使气息，禁锢敌方随机单体2回合",
            "effects": [{"type": "control", "duration": 2}]
        }
    },
    "无相菩萨": {
        "image": "picture/菩萨无相灵.png", "hp": 600, "atk": 40, "def": 60, "tag": "群体加防",
        "skill": {
            "name": "我佛慈悲", "target": "ally_aoe", "cooldown": 12, 
            "desc": "念经诵佛，提升我方全体：无相菩萨与目标各50%防御力混合后20%的防御值",
            "effects": [{"type": "buff", "stat": "def", "multiplier": 0.2}]
        }
    },
    "乔奢费": {
        "image": "picture/乔奢费铠.png", "hp": 500, "atk": 70, "def": 60, "tag": "本体强化",
        "skill": {
            "name": "地狱之血", "target": "self", "cooldown": 2, 
            "desc": "燃烧精血，提升自身10%的攻击力和防御力",
            "effects": [{"type": "buff", "stat": "atk, def", "multiplier": 0.1}]
        }
    },
    "人鱼公主": {
        "image": "picture/人鱼公主.png", "hp": 300, "atk": 10, "def": 20, "tag": "群体控制",
        "skill": {
            "name": "凛冬·归寂", "target": "enemy_aoe", "cooldown": 12, 
            "desc": "吹出笛声，迷惑敌方全体2回合",
            "effects": [{"type": "control", "duration": 2}]
        }
    },
    "若溪": {
        "image": "picture/弱水界王.png", "hp": 300, "atk": 30, "def": 20, "tag": "单体加攻",
        "skill": {
            "name": "柔情似水", "target": "ally_highest_atk", "cooldown": 5, 
            "desc": "以极致的服务提升我方攻击力最高的单体：若溪与目标各50%攻击力混合后50%的攻击值",
            "effects": [{"type": "buff", "stat": "atk", "multiplier": 0.5}]
        }
    },
    "兽神王": {
        "image": "picture/兽神王.png", "hp": 700, "atk": 80, "def": 80, "tag": "全能对单",
        "skill": {
            "name": "真龙·神降", "target": "enemy_random", "cooldown": 5, 
            "desc": "对敌方随机单体造成：兽神王50%攻击力的伤害、1回合控制，兽神王与目标各50%攻击力和防御力的20%的两项属性值降低",
            "effects": [
                {"type": "damage", "multiplier": 0.5},
                {"type": "control", "duration": 1},
                {"type": "debuff", "stat": "atk, def", "multiplier": 0.2}
            ]
        }
    },
    "净水使": {
        "image": "picture/水系魂铠.png", "hp": 300, "atk": 10, "def": 40, "tag": "单体免控",
        "skill": {
            "name": "净水莲华", "target": "ally_random", "cooldown": 2, 
            "desc": "洗涤污秽，解除我方随机单体的控制状态并附加2回合免控",
            "effects": [{"type": "immune", "duration": 2}]
        }
    },
    "剑光仙": {
        "image": "picture/小剑仙.png", "hp": 400, "atk": 90, "def": 40, "tag": "群体伤害",
        "skill": {
            "name": "万剑归宗", "target": "enemy_aoe", "cooldown": 6, 
            "desc": "召唤群剑，对敌方全体造成剑光仙100%攻击力的光明剑气伤害",
            "effects": [{"type": "damage", "multiplier": 1.0}]
        }
    },
    "刑天": {
        "image": "picture/刑天铠.png", "hp": 500, "atk": 60, "def": 65, "tag": "攻击强化",
        "skill": {
            "name": "火刑剑势", "target": "self", "cooldown": 3, 
            "desc": "每次使用火刑剑势都会叠加伤害，增加刑天30%攻击力",
            "effects": [{"type": "buff", "stat": "atk", "multiplier": 0.3}]
        }
    },
    "炎龙": {
        "image": "picture/炎龙铠.png", "hp": 500, "atk": 80, "def": 65, "tag": "强攻前单",
        "skill": {
            "name": "龙炎斩", "target": "enemy_front", "cooldown": 3, 
            "desc": "向前挥出火刀，对敌方最前排单体造成炎龙300%攻击力的伤害",
            "effects": [{"type": "damage", "multiplier": 3.0}]
        }
    },
    "烈火战龙": {
        "image": "picture/炎龙灵.png", "hp": 700, "atk": 70, "def": 70, "tag": "连击随单",
        "skill": {
            "name": "喷射火焰", "target": "enemy_random", "cooldown": 1, 
            "desc": "向敌方随机单体喷射火焰，造成烈火战龙200%攻击力的灼烧伤害",
            "effects": [{"type": "damage", "multiplier": 2.0}]
        }
    },
    "萧炎": {
        "image": "picture/异火界王.png", "hp": 600, "atk": 80, "def": 80, "tag": "群伤吸血",
        "skill": {
            "name": "佛怒火莲", "target": "enemy_aoe", "cooldown": 6, 
            "desc": "凝聚火莲，对敌方全体造成萧炎50%攻击力的伤害并回复萧炎实际造成伤害的50%血量",
            "effects": [
                {"type": "damage", "multiplier": 0.5},
                {"type": "lifesteal", "multiplier": 0.5}
            ]
        }
    },
    # skills
    "尊皇圣帝": {
        "image": "picture/尊皇圣帝.png", "hp": 1000, "atk": 100, "def": 100, "tag": "最强全能",
        "skills": [
            # {
            # "name": "敌", "target": "enemy_aoe", "cooldown": 2, 
            # "desc": "对敌方全体造成：尊皇圣帝100%攻击力的伤害、1回合静止，尊皇圣帝与目标各50%攻击力和防御力的100%的两项属性值降低，并回复尊皇圣帝实际造成伤害的100%血量",
            # "effects": [
            #     {"type": "damage", "multiplier": 1.0},
            #     {"type": "lifesteal", "multiplier": 1.0},
            #     {"type": "control", "duration": 1},
            #     {"type": "debuff", "stat": "atk, def", "multiplier": 1.0},
            #     ]
            # },
            # {
            # "name": "友", "target": "ally_aoe", "cooldown": 2, 
            # "desc": "对我方全体造成：恢复尊皇圣帝与目标各50%最大生命值混合后100%的血量，尊皇圣帝与目标各50%攻击力和防御力的100%的两项属性值增加，并且全体免控1回合",
            # "effects": [
            #     {"type": "heal", "multiplier": 1.0},
            #     {"type": "buff", "stat": "atk, def", "multiplier": 1.0},
            #     {"type": "immune", "duration": 1},
            #     ]
            # },
            # {
            # "name": "复活神光", "target": "ally_dead_aoe", "cooldown": 1, 
            # "desc": "复活我方全体死亡角色并恢复其血量至尊皇圣帝与目标各50%最大生命值混合后100%的血量",
            # "effects": [{"type": "resurrect", "multiplier": 1.0}]
            # },
            {
            "name": "单体复活", "target": "ally_dead_random", "cooldown": 1, 
            "desc": "复活我方随机一个死亡角色，并恢复其血量至尊皇圣帝与目标各最大生命值均值的100%的血量",
            "effects": [{"type": "resurrect", "multiplier": 1.0}]
            },
            # {
            # "name": "随单降攻", "target": "enemy_random", "cooldown": 3, 
            # "desc": "降低敌方随机单体：安迷修与目标各50%攻击力混合后30%的攻击值",
            # "effects": [{"type": "debuff", "stat": "atk", "multiplier": 0.3}]
            # },
            # {
            # "name": "随单减防", "target": "enemy_higest_def", "cooldown": 3, 
            # "desc": "降低敌方随机单体：暗魂与目标各50%防御力混合后30%的防御值",
            # "effects": [{"type": "debuff", "stat": "def", "multiplier": 0.3}]
            # }
        ]
    },

}

# ================= 3. 关卡配置 =================
STAGE_CONFIG = {
    1: [{"name": "安迷修", "level": 1, "star": 1}],
    2: [{"name": "暗魂", "level": 2, "star": 1}, {"name": "净世圣女", "level": 2, "star": 1}],
    3: [{"name": "白骨夫人", "level": 3, "star": 1}, {"name": "冰云剑仙", "level": 3, "star": 1}, {"name": "魅狐妖姬", "level": 3, "star": 1}],
    4: [{"name": "帝皇", "level": 4, "star": 1}, {"name": "五灵龙神", "level": 4, "star": 1}, {"name": "毒孤博", "level": 4, "star": 1}, {"name": "小花仙", "level": 4, "star": 1}],
    5: [{"name": "光明神王", "level": 5, "star": 1}, {"name": "艾莎", "level": 5, "star": 1}, {"name": "黑迪", "level": 5, "star": 1}, {"name": "极光神使", "level": 5, "star": 1}, {"name": "黑骑女将", "level": 5, "star": 1}],
    6: [{"name": "精灵公主", "level": 6, "star": 1}, {"name": "巨甲象", "level": 6, "star": 1}, {"name": "巨爪熊", "level": 6, "star": 1}, {"name": "库忿斯", "level": 6, "star": 1}, {"name": "傀儡女王", "level": 6, "star": 1}, {"name": "七彩鲲鹏", "level": 6, "star": 1}],
    7: [{"name": "金甲骑士", "level": 7, "star": 1}, {"name": "美杜莎", "level": 7, "star": 1}, {"name": "紫萱", "level": 7, "star": 1}, {"name": "女武神", "level": 7, "star": 1}, {"name": "殿主", "level": 7, "star": 1}, {"name": "无相菩萨", "level": 7, "star": 1}],
    8: [{"name": "乔奢费", "level": 8, "star": 1}, {"name": "人鱼公主", "level": 8, "star": 1}, {"name": "若溪", "level": 8, "star": 1}, {"name": "兽神王", "level": 8, "star": 1}, {"name": "净水使", "level": 8, "star": 1}, {"name": "剑光仙", "level": 8, "star": 1}],
    9: [{"name": "刑天", "level": 9, "star": 1}, {"name": "炎龙", "level": 9, "star": 1}, {"name": "烈火战龙", "level": 9, "star": 1}, {"name": "萧炎", "level": 9, "star": 1}],
    10: [{"name": "安迷修", "level": 10, "star": 2}],
    11: [{"name": "暗魂", "level": 11, "star": 2}, {"name": "净世圣女", "level": 11, "star": 2}],
    12: [{"name": "白骨夫人", "level": 12, "star": 2}, {"name": "冰云剑仙", "level": 12, "star": 2}, {"name": "魅狐妖姬", "level": 12, "star": 2}],
    13: [{"name": "帝皇", "level": 13, "star": 2}, {"name": "五灵龙神", "level": 13, "star": 2}, {"name": "毒孤博", "level": 13, "star": 2}, {"name": "小花仙", "level": 13, "star": 2}],
    14: [{"name": "光明神王", "level": 14, "star": 2}, {"name": "艾莎", "level": 14, "star": 2}, {"name": "黑迪", "level": 14, "star": 2}, {"name": "黑骑女将", "level": 14, "star": 2}, {"name": "极光神使", "level": 14, "star": 2}],
    15: [{"name": "精灵公主", "level": 15, "star": 2}, {"name": "巨甲象", "level": 15, "star": 2}, {"name": "巨爪熊", "level": 15, "star": 2}, {"name": "库忿斯", "level": 15, "star": 2}, {"name": "傀儡女王", "level": 15, "star": 2}, {"name": "七彩鲲鹏", "level": 15, "star": 2}],
    16: [{"name": "金甲骑士", "level": 16, "star": 2}, {"name": "美杜莎", "level": 16, "star": 2}, {"name": "紫萱", "level": 16, "star": 2}, {"name": "女武神", "level": 16, "star": 2}, {"name": "殿主", "level": 16, "star": 2}, {"name": "无相菩萨", "level": 16, "star": 2}],
    17: [{"name": "乔奢费", "level": 17, "star": 2}, {"name": "人鱼公主", "level": 17, "star": 2}, {"name": "若溪", "level": 17, "star": 2}, {"name": "兽神王", "level": 17, "star": 2}, {"name": "净水使", "level": 17, "star": 2}, {"name": "剑光仙", "level": 17, "star": 2}],
    18: [{"name": "刑天", "level": 18, "star": 2}, {"name": "炎龙", "level": 18, "star": 2}, {"name": "烈火战龙", "level": 18, "star": 2}, {"name": "萧炎", "level": 18, "star": 2}],
    19: [{"name": "安迷修", "level": 19, "star": 3}],
    20: [{"name": "暗魂", "level": 20, "star": 3}, {"name": "净世圣女", "level": 20, "star": 3}],
    21: [{"name": "白骨夫人", "level": 21, "star": 3}, {"name": "冰云剑仙", "level": 21, "star": 3}, {"name": "魅狐妖姬", "level": 21, "star": 3}],
    22: [{"name": "帝皇", "level": 22, "star": 3}, {"name": "五灵龙神", "level": 22, "star": 3}, {"name": "毒孤博", "level": 22, "star": 3}, {"name": "小花仙", "level": 22, "star": 3}],
    23: [{"name": "光明神王", "level": 23, "star": 3}, {"name": "艾莎", "level": 23, "star": 3}, {"name": "黑迪", "level": 23, "star": 3}, {"name": "黑骑女将", "level": 23, "star": 3}, {"name": "极光神使", "level": 23, "star": 3}],
    24: [{"name": "精灵公主", "level": 24, "star": 3}, {"name": "巨甲象", "level": 24, "star": 3}, {"name": "巨爪熊", "level": 24, "star": 3}, {"name": "库忿斯", "level": 24, "star": 3}, {"name": "傀儡女王", "level": 24, "star": 3}, {"name": "七彩鲲鹏", "level": 24, "star": 3}],
    25: [{"name": "金甲骑士", "level": 25, "star": 3}, {"name": "美杜莎", "level": 25, "star": 3}, {"name": "紫萱", "level": 25, "star": 3}, {"name": "女武神", "level": 25, "star": 3}, {"name": "殿主", "level": 25, "star": 3}, {"name": "无相菩萨", "level": 25, "star": 3}],
    26: [{"name": "乔奢费", "level": 26, "star": 3}, {"name": "人鱼公主", "level": 26, "star": 3}, {"name": "若溪", "level": 26, "star": 3}, {"name": "兽神王", "level": 26, "star": 3}, {"name": "净水使", "level": 26, "star": 3}, {"name": "剑光仙", "level": 26, "star": 3}],
    27: [{"name": "刑天", "level": 27, "star": 3}, {"name": "炎龙", "level": 27, "star": 3}, {"name": "烈火战龙", "level": 27, "star": 3}, {"name": "萧炎", "level": 27, "star": 3}],
    28: [{"name": "安迷修", "level": 28, "star": 4}],
    29: [{"name": "暗魂", "level": 29, "star": 4}, {"name": "净世圣女", "level": 29, "star": 4}],
    30: [{"name": "白骨夫人", "level": 30, "star": 4}, {"name": "冰云剑仙", "level": 30, "star": 4}, {"name": "魅狐妖姬", "level": 30, "star": 4}],
    31: [{"name": "帝皇", "level": 31, "star": 4}, {"name": "五灵龙神", "level": 31, "star": 4}, {"name": "毒孤博", "level": 31, "star": 4}, {"name": "小花仙", "level": 31, "star": 4}],
    32: [{"name": "光明神王", "level": 32, "star": 4}, {"name": "艾莎", "level": 32, "star": 4}, {"name": "黑迪", "level": 32, "star": 4}, {"name": "黑骑女将", "level": 32, "star": 4}, {"name": "极光神使", "level": 32, "star": 4}],
    33: [{"name": "精灵公主", "level": 33, "star": 4}, {"name": "巨甲象", "level": 33, "star": 4}, {"name": "巨爪熊", "level": 33, "star": 4}, {"name": "库忿斯", "level": 33, "star": 4}, {"name": "傀儡女王", "level": 33, "star": 4}, {"name": "七彩鲲鹏", "level": 33, "star": 4}],
    34: [{"name": "金甲骑士", "level": 34, "star": 4}, {"name": "美杜莎", "level": 34, "star": 4}, {"name": "紫萱", "level": 34, "star": 4}, {"name": "女武神", "level": 34, "star": 4}, {"name": "殿主", "level": 34, "star": 4}, {"name": "无相菩萨", "level": 34, "star": 4}],
    35: [{"name": "乔奢费", "level": 35, "star": 4}, {"name": "人鱼公主", "level": 35, "star": 4}, {"name": "若溪", "level": 35, "star": 4}, {"name": "兽神王", "level": 35, "star": 4}, {"name": "净水使", "level": 35, "star": 4}, {"name": "剑光仙", "level": 35, "star": 4}],
    36: [{"name": "刑天", "level": 36, "star": 4}, {"name": "炎龙", "level": 36, "star": 4}, {"name": "烈火战龙", "level": 36, "star": 4}, {"name": "萧炎", "level": 36, "star": 4}],
    37: [{"name": "安迷修", "level": 37, "star": 5}],
    38: [{"name": "暗魂", "level": 38, "star": 5}, {"name": "净世圣女", "level": 38, "star": 5}],
    39: [{"name": "白骨夫人", "level": 39, "star": 5}, {"name": "冰云剑仙", "level": 39, "star": 5}, {"name": "魅狐妖姬", "level": 39, "star": 5}],
    40: [{"name": "帝皇", "level": 40, "star": 5}, {"name": "五灵龙神", "level": 40, "star": 5}, {"name": "毒孤博", "level": 40, "star": 5}, {"name": "小花仙", "level": 40, "star": 5}],
    41: [{"name": "光明神王", "level": 41, "star": 5}, {"name": "艾莎", "level": 41, "star": 5}, {"name": "黑迪", "level": 41, "star": 5}, {"name": "黑骑女将", "level": 41, "star": 5}, {"name": "极光神使", "level": 41, "star": 5}],
    42: [{"name": "精灵公主", "level": 42, "star": 5}, {"name": "巨甲象", "level": 42, "star": 5}, {"name": "巨爪熊", "level": 42, "star": 5}, {"name": "库忿斯", "level": 42, "star": 5}, {"name": "傀儡女王", "level": 42, "star": 5}, {"name": "七彩鲲鹏", "level": 42, "star": 5}],
    43: [{"name": "金甲骑士", "level": 43, "star": 5}, {"name": "美杜莎", "level": 43, "star": 5}, {"name": "紫萱", "level": 43, "star": 5}, {"name": "女武神", "level": 43, "star": 5}, {"name": "殿主", "level": 43, "star": 5}, {"name": "无相菩萨", "level": 43, "star": 5}],
    44: [{"name": "乔奢费", "level": 44, "star": 5}, {"name": "人鱼公主", "level": 44, "star": 5}, {"name": "若溪", "level": 44, "star": 5}, {"name": "兽神王", "level": 44, "star": 5}, {"name": "净水使", "level": 44, "star": 5}, {"name": "剑光仙", "level": 44, "star": 5}],
    45: [{"name": "刑天", "level": 45, "star": 5}, {"name": "炎龙", "level": 45, "star": 5}, {"name": "烈火战龙", "level": 45, "star": 5}, {"name": "萧炎", "level": 45, "star": 5}],
}
# 请继续添加STAGE_CONFIG中的关卡配置，使其按照HERO_CONFIG中角色的顺序逐个进行配置，每一层为同一个星级，每一层前6关人数从1个逐渐递增，后面每一关都为6人，直到把HERO_CONFIG中角色放完为止，并且每一关的level逐级增加


# 演出配置与数值配置分离：普攻和对敌技能共用同一种攻击距离。
# 原图四姿势的朝向依次为待机、蓄力、出招、受击；1 朝右，-1 朝左。
COMBAT_PRESENTATION = {
    "安迷修": {"style": "melee", "projectile": "bolt", "facing": (-1, -1, 1, -1)},
    "暗魂": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "净世圣女": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "白骨夫人": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "冰云剑仙": {"style": "ranged", "projectile": "blade", "facing": (1, 1, 1, 1)},
    "魅狐妖姬": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "帝皇": {"style": "ranged", "projectile": "blade", "facing": (1, 1, 1, 1)},
    "五灵龙神": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "毒孤博": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "小花仙": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "光明神王": {"style": "ranged", "projectile": "blade", "facing": (1, 1, 1, 1)},
    "艾莎": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "黑迪": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "黑骑女将": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "极光神使": {"style": "ranged", "projectile": "blade", "facing": (1, 1, 1, 1)},
    "精灵公主": {"style": "ranged", "projectile": "arrow", "facing": (1, 1, 1, 1)},
    "巨甲象": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "巨爪熊": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "库忿斯": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "傀儡女王": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "七彩鲲鹏": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "金甲骑士": {"style": "melee", "projectile": "bolt", "facing": (-1, -1, 1, -1)},
    "美杜莎": {"style": "ranged", "projectile": "bolt", "facing": (-1, 1, 1, 1)},
    "紫萱": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "女武神": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "殿主": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "无相菩萨": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "乔奢费": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "人鱼公主": {"style": "ranged", "projectile": "wave", "facing": (1, 1, 1, 1)},
    "若溪": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "兽神王": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "净水使": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "剑光仙": {"style": "ranged", "projectile": "blade", "facing": (1, 1, 1, 1)},
    "刑天": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "炎龙": {"style": "melee", "projectile": "bolt", "facing": (1, 1, 1, 1)},
    "烈火战龙": {"style": "ranged", "projectile": "fire", "facing": (1, 1, 1, 1)},
    "萧炎": {"style": "ranged", "projectile": "fire", "facing": (1, 1, 1, 1)},
    "尊皇圣帝": {"style": "ranged", "projectile": "bolt", "facing": (1, 1, 1, 1)},
}
