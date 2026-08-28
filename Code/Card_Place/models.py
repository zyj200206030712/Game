# models.py  存放游戏核心数据结构（角色类 Character、存档与数据类 GameData）
import json
from pathlib import Path
from config import HERO_CONFIG, STAGE_CONFIG
from ui import load_image

SAVE_PATH = Path(__file__).with_name("save_data.json")

class Character:
    def __init__(self, name, image_file, base_hp, base_atk, base_def, tag="普通", skill=None, skills=None):
        self.name = name
        self.image = load_image(image_file)
        self.level, self.star, self.duplicates = 1, 1, 0
        self.base_hp, self.base_atk, self.base_def = base_hp, base_atk, base_def
        self.tag = tag 
        self.skills = self._normalize_skills(skill, skills)
        self.current_cds = [0] * len(self.skills)
        
        self.current_hp = self.max_hp
        self.dmg_dealt, self.dmg_taken = 0, 0
        self.heal_done = 0
        self.battle_atk_bonus = 0 
        self.battle_def_bonus = 0 
        self.stun_turns = 0 
        self.immune_turns = 0  # 【新增】免控剩余回合数
        self.skill_ready_highlight = False
        # 【新增】动画坐标偏移量
        self.offset_x = 0
        self.offset_y = 0

    def reset_battle_state(self):
        self.current_hp = self.max_hp
        self.dmg_dealt = 0
        self.dmg_taken = 0
        self.heal_done = 0
        self.current_cds = [0] * len(self.skills)
        self.battle_atk_bonus = 0 
        self.battle_def_bonus = 0 
        self.stun_turns = 0 
        self.immune_turns = 0  # 【新增】战斗结束后重置免控状态
        self.skill_ready_highlight = False
        # 【新增】重置动画偏移
        self.offset_x = 0
        self.offset_y = 0
    
    # 【新增】动画平滑回弹算法 (Lerp)
    def update_anim(self):
        # 每一帧让偏移量以 15% 的速度向 0 滑动，产生弹簧般的视觉效果
        if abs(self.offset_x) > 0.5:
            self.offset_x += (0 - self.offset_x) * 0.15
        else:
            self.offset_x = 0
            
        if abs(self.offset_y) > 0.5:
            self.offset_y += (0 - self.offset_y) * 0.15
        else:
            self.offset_y = 0

    def reset_on_resurrect(self):
        self.battle_atk_bonus = 0
        self.battle_def_bonus = 0
        self.stun_turns = 0
        self.immune_turns = 0
        self.skill_ready_highlight = False
        self.offset_x = 0
        self.offset_y = 0
        self.current_cds = [0] * len(self.skills)

    @staticmethod
    def _normalize_skills(skill=None, skills=None):
        raw_skills = skills if skills is not None else ([skill] if skill else [])
        normalized = []
        for idx, skill_data in enumerate(raw_skills):
            if not skill_data:
                continue
            skill_copy = dict(skill_data)
            skill_copy.setdefault("priority", 0)
            normalized.append((idx, skill_copy))
        normalized.sort(key=lambda item: (-item[1].get("priority", 0), item[0]))
        return [skill_copy for _, skill_copy in normalized]

    @property
    def skill(self):
        return self.skills[0] if self.skills else None

    @property
    def current_cd(self):
        return self.current_cds[0] if self.current_cds else 0

    @current_cd.setter
    def current_cd(self, value):
        if self.current_cds:
            self.current_cds[0] = value

    def get_available_skill_choices(self):
        return [(idx, skill) for idx, skill in enumerate(self.skills) if self.current_cds[idx] == 0]

    @staticmethod
    def scale_stat(base_value, level=1, star=1):
        scaled = base_value
        for _ in range(max(0, level - 1)):
            scaled = round(scaled * 1.1)
        return round(scaled * (2 ** max(0, star - 1)))

    @property
    def max_hp(self): return self.scale_stat(self.base_hp, self.level, self.star)
    
    @property
    def atk(self): 
        base = self.scale_stat(self.base_atk, self.level, self.star)
        return max(0, base + self.battle_atk_bonus)
        
    @property
    def defense(self): 
        base = self.scale_stat(self.base_def, self.level, self.star)
        return max(0, base + self.battle_def_bonus)

    def take_damage(self, attacker_atk):
        damage = max(0, attacker_atk - self.defense)
        self.current_hp -= damage
        self.dmg_taken += damage 
        return damage

def get_stage_enemies(level):
    if level in STAGE_CONFIG:
        return [dict(e) for e in STAGE_CONFIG[level]]
    else:
        max_level = max(STAGE_CONFIG.keys())
        base_enemies = STAGE_CONFIG[max_level]
        
        # 超出配置的关卡，通过自动提升等级和星级来增加难度
        level_diff = level - max_level
        extra_levels = level_diff * 1      # 每超出1关，敌方等级+1
        extra_stars = level_diff // 5      # 每超出5关，敌方全体升1星
        
        scaled_enemies = []
        for e in base_enemies:
            scaled_enemies.append({
                "name": e["name"],
                "level": e.get("level", 1) + extra_levels,
                "star": e.get("star", 1) + extra_stars
            })
        return scaled_enemies

class GameData:
    def __init__(self):
        self.gold = 0
        self.level = 1
        self.owned_heroes = []
        self.deployed_party = [None] * 6
        self.current_hero_index = 0
        self.hero_page = 0
        self.current_scene = "LEVEL"
        self.log_scroll_y = 0
        self.battle_result = "" 
        self.is_paused = False  
        self.battle_speed = 1  
        self.turn_counter = 0 
        self.current_attacker = None 
        self.current_target = None   
        self.sys_message = self.load_game()
        
        self.current_enemy_configs = get_stage_enemies(self.level)
        self.enemy_party = []

    @property
    def display_heroes(self):
        display = list(self.deployed_party) 
        for h in self.owned_heroes:
            if h not in self.deployed_party:
                display.append(h)
        return display

    def get_idle_rate(self): return self.level * 1

    def advance_level(self):
        self.level += 1
        self.current_enemy_configs = get_stage_enemies(self.level)

    def add_hero(self, name, level=1, star=1, duplicates=0):
        for hero in self.owned_heroes:
            if hero.name == name:
                hero.duplicates += 1
                return False
                
        stats = HERO_CONFIG.get(name, {"image": f"picture/{name}.png", "hp": 50, "atk": 50, "def": 50, "tag": "普通"})
        hero = Character(
            name,
            stats["image"],
            stats["hp"],
            stats["atk"],
            stats["def"],
            stats.get("tag", "普通"),
            stats.get("skill"),
            stats.get("skills"),
        )
        hero.level, hero.star, hero.duplicates = level, star, duplicates
        self.owned_heroes.append(hero)
        return True

    def get_active_hero(self):
        display = self.display_heroes
        if not display: return None
        if self.current_hero_index >= len(display):
            self.current_hero_index = 0
        return display[self.current_hero_index]

    def save_game(self):
        data = {"gold": self.gold, "level": self.level, "heroes":[]}
        for h in self.owned_heroes:
            pos = self.deployed_party.index(h) if h in self.deployed_party else -1
            data["heroes"].append({"name": h.name, "level": h.level, "star": h.star, "duplicates": h.duplicates, "pos": pos})
        try:
            with SAVE_PATH.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return "进度保存成功！"
        except: return "保存失败！"

    def load_game(self):
        if not SAVE_PATH.exists():
            self.gold = 1000
            first_hero_name = list(HERO_CONFIG.keys())[0]
            self.add_hero(first_hero_name)
            self.deployed_party[0] = self.owned_heroes[0]
            return "欢迎游玩！初始物资已发放"
        try:
            with SAVE_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.gold, self.level = data.get("gold", 0), data.get("level", 1)
            for h_data in data.get("heroes", []):
                self.add_hero(h_data["name"], h_data["level"], h_data["star"], h_data["duplicates"])
                if h_data.get("pos", -1) != -1 and h_data.get("pos", -1) < 6: 
                    self.deployed_party[h_data["pos"]] = self.owned_heroes[-1]
            return "存档已读取！"
        except: return "读取异常，开启新对局。"
