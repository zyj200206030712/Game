# 战斗模块

import pygame  # 游戏开发
from pathlib import Path
from data import define_skills, Character_battle_data, Skill  # 导入技能实例和角色实例
import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PICTURE_DIR = PROJECT_ROOT / "picture"
EFFECTS_DIR = PROJECT_ROOT / "effects"

PLAYER_COLOR = (0, 200, 0)  # 玩家阵营颜色（绿色）
ENEMY_COLOR = (255, 50, 50)  # 敌人阵营颜色（红色）
DAMAGE_COLOR = (200, 0, 0)  # 伤害数值颜色（暗红色）
HEAL_COLOR = (0, 200, 0)  # 治疗数值颜色（绿色）
TEXT_COLOR = (0, 0, 0)  # 常规日志文本颜色（黑色）
SKILL_COLOR = (150, 50, 150)  # 技能颜色（紫色）
HUNLIANG_COLOR = (60, 80, 255)  # 魂量条颜色（青蓝色）
PUPPET_COLOR = (100, 200, 100)  # 傀儡颜色（淡绿色）
IDENTITY_COLOR = (255, 215, 0)  # 境界/身份变化颜色（金色）

# 定义所有身份及境界等级
identity_LEVELS = {
    "魂师": ["初师前", "初师中", "初师后", "中师前", "中师中", "中师后", "高师前", "高师中", "高师后"],
    "魂铠": ["初铠前", "初铠中", "初铠后", "中铠前", "中铠中", "中铠后", "高铠前", "高铠中", "高铠后"],
    "魂灵": ["初灵前", "初灵中", "初灵后", "中灵前", "中灵中", "中灵后", "高灵前", "高灵中", "高灵后"],
    "凡神": [str(i) for i in range(1, 100)],  # 1-99
    "界王": [str(i) for i in range(100, 1000, 100)],  # 100-900
    "神王": [str(i) for i in range(1000, 11000, 1000)],  # 1000-10000
}
IDENTITY_HIERARCHY = ["魂师", "魂铠", "魂灵", "凡神", "界王", "神王"]  # 身份的阶级，用于身份压制判断
STAT_MULTIPLIER_PATTERN = [2, 2, 5, 2, 2, 5, 2, 2]  # 定义每提升一小级境界时，属性的增长倍率模式（等期2，等级5）

class VideoPlayer:
    """
    视频播放管理类，负责打开视频、循环读取帧并调整大小。
    """
    def __init__(self, path, size=None):
        self.path = path
        self.cap = cv2.VideoCapture(path)
        self.size = size # (width, height)
        self.current_surface = None

    def get_next_frame(self):
        if not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret: # 如果视频结束，回到第一帧实现循环
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        if ret:
            # OpenCV 默认是 BGR 格式，需要转为 RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 转置和翻转是因为 OpenCV 和 Pygame 的坐标系差异（通常 OpenCV 宽x高，需要转换）
            frame = cv2.transpose(frame)
            surface = pygame.surfarray.make_surface(frame)
            
            # 如果指定了缩放大小
            if self.size:
                self.current_surface = pygame.transform.smoothscale(surface, self.size)
            else:
                self.current_surface = surface
                
        return self.current_surface

    def release(self):
        self.cap.release()


# 通过调用函数加载技能和角色数据
all_skills = define_skills()


# 创建可交互的UI按钮
class Button:
    def __init__(self, text, position, size, action, disabled=False):
        self.rect = pygame.Rect(position, size)  # 按钮的矩形区域
        try:  # 尝试加载指定字体
            self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 24)  # 设置按钮文本字体
        except FileNotFoundError:  # 如果字体不存在
            self.font = pygame.font.Font(None, 24)  # 使用默认字体
        self.text, self.action, self.disabled = text, action, disabled  # 按钮的文本、关联的动作（点击按钮后返回的参数）、是否禁用
        self.base_color, self.disabled_color = (100, 100, 200), (120, 120, 120)  # 按钮的正常蓝色和禁用灰色

    # 在屏幕上绘制按钮
    def draw(self, screen):
        color = self.disabled_color if self.disabled else self.base_color  # 根据是否禁用选择颜色
        pygame.draw.rect(screen, color, self.rect)  # 在窗口上绘制按钮的背景矩形

        lines = self.text.split('\n')  # 按行分割文本
        line_spacing = 2  # 行间距
        font_height = self.font.get_height()  # 获取字体高度
        total_text_height = (font_height * len(lines)) + (line_spacing * (len(lines) - 1))  # 计算文本块的总高度
        start_y = self.rect.centery - (total_text_height / 2)  # 计算第一行文本的起始Y坐标，以使整个文本块垂直居中

        for i, line in enumerate(lines):
            line_surf = self.font.render(line, True, (255, 255, 255))  # 将每一行都水平居中
            line_rect = line_surf.get_rect(centerx=self.rect.centerx)
            line_rect.y = int(start_y + (i * (font_height + line_spacing)))  # 根据行号和行高计算当前行的Y坐标
            screen.blit(line_surf, line_rect)

    # 检查鼠标点击是否在按钮上
    def check_click(self, mouse_pos):
        return not self.disabled and self.rect.collidepoint(mouse_pos)  # 只有在按钮未禁用时，点击才有效


# 角色基类，定义了所有单位（玩家、敌人、傀儡）的属性
class Character:
    def __init__(self, name, hp, hundu, hunliang, image_path, identity, level="", **kwargs):
        self.name, self.hp, self.max_hp = name, hp, hp  # 角色的名字、当前生命值、最大生命值
        self.hunliang, self.max_hunliang = hunliang, hunliang  # 角色的当前魂量、最大魂量
        self.base_hundu, self.hundu = hundu, hundu  # 角色的基础魂度、当前魂度
        self.image_path, self.identity, self.level = image_path, identity, level  # 角色的图片路径、身份（魂师/魂铠等）、境界等级
        self.is_alive, self.active_effects = True, []  # 角色是否存活、当前承受的主动效果列表
        self.is_puppet = kwargs.get('is_puppet', False)  # 角色是否为傀儡
        self.summoner = kwargs.get('summoner', None)  # 傀儡的召唤者
        self.puppet_duration = kwargs.get('puppet_duration', 0)  # 作为傀儡的持续时间
        self.original_stats = None  # 用于存储被临时改变属性前的原始属性
        self.is_player_side = True  # 角色是否属于玩家阵营

    # 根据角色类型获取其颜色
    def get_color(self):
        if self.is_puppet: return PUPPET_COLOR  # 如果是傀儡，返回淡绿色
        return PLAYER_COLOR if self.is_player_side else ENEMY_COLOR  # 玩家蓝色、敌人红色

    # 给角色施加一个状态效果
    def apply_effect(self, effect, combat_log):
        self.active_effects.append(effect)  # 将施法者及状态效果添加到目标角色激活效果列表中
        effect.on_apply(self, combat_log)  # 效果应用
        return False

    # 更新角色身上的所有状态效果（回合开始时触发，关键）
    def update_effects(self, combat_log):
        if not self.is_alive: return []  # 如果角色已死亡，不处理

        triggered_vfx_assets = []  # 用于存储本回合触发的特效名称
        surviving_effects = []  # 更新的存活效果列表
        for effect in self.active_effects:
            if effect.duration > 0:
                surviving_effects.append(effect)  # 将持续时间大于0的技能效果添加到存活效果列表中，表明该回合还需要触发效果
                combat_log.add_message([(self.name, self.get_color()), (f" 的 ", TEXT_COLOR),
                                        (f"[{effect.name}]", SKILL_COLOR), (f" 效果剩余 ", TEXT_COLOR),
                                        (f"{effect.duration}", DAMAGE_COLOR), (f" 回合。", TEXT_COLOR)])
        self.active_effects = surviving_effects  # 删除失效的技能效果

        if self.is_puppet:  # 傀儡不是效果，不能放到tick中触发
            if self.puppet_duration <= 0:
                self.hp = 0
                self.is_alive = False
                combat_log.add_message([(self.name, PUPPET_COLOR), (" 的持续时间结束了。", TEXT_COLOR)])
            else:
                combat_log.add_message([(self.name, self.get_color()), (" 还可存在 ", TEXT_COLOR),
                                        (f"{self.puppet_duration}", DAMAGE_COLOR), (" 回合。", TEXT_COLOR)])
            self.puppet_duration -= 1  # 傀儡持续回合减一

        effects_to_process = list(self.active_effects)  # 创建激活效果副本，因为激活效果在触发后可能会改变
        for effect in effects_to_process:
            if effect.duration > 0:
                # 捕获tick方法返回的特效名称
                asset_name = effect.tick(self, combat_log)
                if asset_name:
                    triggered_vfx_assets.append(asset_name)

        return triggered_vfx_assets  # 返回需要播放的特效列表


    # 角色承受伤害，扣除血量，返回伤害值
    def take_damage(self, damage, combat_log):
        was_alive = self.is_alive  # 记录受伤前的存活状态

        # 防御技能逻辑，筛选出所有防御效果
        defense_effects = [e for e in self.active_effects if e.skill_type == 'defense' and e.current_turn_shield  > 0]
        original_damage = int(damage)  # 存储原始伤害值

        if defense_effects:
            strongest_defense = max(defense_effects, key=lambda e: e.current_turn_shield )
            block_value = strongest_defense.current_turn_shield   #  找到最强的防御效果值
            blocked_damage = min(original_damage, block_value)
            actual_damage = original_damage - blocked_damage  # 获取实际受到的伤害
            strongest_defense.current_turn_shield  -= blocked_damage  # 更新护盾值

            # 如果有伤害被吸收
            if blocked_damage > 0:
                combat_log.add_message([
                    (self.name, self.get_color()), (f" 的 ", TEXT_COLOR),
                    (f"[{strongest_defense.name}]", SKILL_COLOR), (f" 效果吸收了 ", TEXT_COLOR),
                    (f"{int(blocked_damage)}", DAMAGE_COLOR), (" 点伤害。", TEXT_COLOR),(f" 护盾剩余", TEXT_COLOR),
                    (f" {int(strongest_defense.current_turn_shield )} ", HEAL_COLOR), ("点。", TEXT_COLOR)
                ])
        else:
            actual_damage = original_damage  # 无防御技能直接使用原始伤害值

        self.hp -= actual_damage  # 扣除生命值
        if self.hp <= 0: self.hp, self.is_alive = 0, False  # 如果生命值低于等于0，则使生命值为0，角色死亡
        died_this_hit = was_alive and not self.is_alive  # 如果受伤前是活的，而现在不是，说明刚刚被击杀
        return actual_damage, died_this_hit  # 返回实际造成的伤害值和是否被击杀

    # 角色接受治疗
    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + int(amount))  # 增加生命值，但不超过最大生命值

    @property  # 使用属性装饰器，让方法可以像变量一样被调用
    # 判断角色是否被控制（定身）
    def is_controlled(self):
        return any(e.skill_type == 'control' for e in self.active_effects)  # 检查是否存在“control”类型的效果

    # 恢复角色魂量
    def restore_hunliang(self, amount):
        self.hunliang = min(self.max_hunliang, self.hunliang + int(amount))  # 增加魂量，但不能超过最大魂量

    # 技能消耗后角色剩余的魂量
    def use_hunliang(self, amount):
        self.hunliang = max(0, self.hunliang - int(amount))  # 减少魂量，不低于0

    # 保存角色的原始核心属性
    def save_original_stats(self):
        if self.original_stats is None:  # 只有在未保存时才保存，防止覆盖
            self.original_stats = {'max_hp': self.max_hp, 'base_hundu': self.base_hundu, 'max_hunliang': self.max_hunliang,
                                   'level': self.level}  # 将原始属性存入字典

    # 恢复角色的原始属性
    def restore_original_stats(self):
        if self.original_stats:  # 确保有已保存的属性
            hp_ratio = self.hp / self.max_hp if self.max_hp > 0 else 0 # 在恢复前计算当前生命值的百分比
            hunliang_ratio = self.hunliang / self.max_hunliang  # 当前魂量的百分比

            # 复制基础属性和境界等级
            stats = self.original_stats
            self.max_hp = stats['max_hp']
            self.base_hundu = stats['base_hundu']
            self.max_hunliang = stats['max_hunliang']
            self.level = stats['level']

            # 根据计算的百分比，恢复当前的生命值和魂量
            self.hp = int(self.max_hp * hp_ratio)
            self.hunliang = int(self.max_hunliang * hunliang_ratio)
            self.hundu = self.base_hundu

            self.original_stats = None  # 清除已保存的原始属性


# 根据角色基类显示角色卡牌
class Card:
    def __init__(self, character, is_enemy=False):  # 初始化卡牌
        self.character = character  # 卡牌关联的角色
        self.is_enemy = is_enemy  # 该卡牌是否为敌人
        try:  # 尝试加载角色图片
            self.original_image = pygame.image.load(self.character.image_path).convert_alpha()  # 加载图片并保留透明度
        except pygame.error:  # 如果加载失败，即找不到字典中对应角色的图片文件
            self.original_image = pygame.Surface((120, 160))  # 创建一个备用矩形表面
            self.original_image.fill((100, 0, 100))  # 填充颜色以作区分
        self.image = self.original_image.copy()  # 当前显示的图像，初始为原始图像的拷贝
        self.rect = self.image.get_rect()  # 获取图像的宽长
        try:  # 加载字体
            self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 18)  # 用于姓名的较大字体
            self.font_hp = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 12)  # 用于血条的较小字体
        except FileNotFoundError:  # 如果找不到指定字体
            self.font = pygame.font.Font(None, 24)  # 使用Pygame默认字体
            self.font_hp = pygame.font.Font(None, 16)  # 使用Pygame默认字体
        self.is_selected = False  # 卡牌是否被选中（用于行动规划）
        self.is_targetable = False  # 卡牌是否是当前技能的可选目标

        # 从项目根目录的 picture 文件夹寻找角色视频
        video_path = PICTURE_DIR / f"{self.character.name}.mp4"
        self.video_path = str(video_path) if video_path.exists() else None
        self.video_player = None

    # 在屏幕上绘制卡牌，self指Card类实例
    def draw(self, screen, show_stats=True):
        self.image.set_alpha(100 if not self.character.is_alive else 255)  # 如果角色死亡，则图像半透明，否则不透明

        display_img = self.image  # 默认使用静态图

        # 如果有视频且角色存活，显示视频
        if self.video_path and self.character.is_alive:
            if self.video_player is None:
                self.video_player = VideoPlayer(self.video_path, self.rect.size)
            frame = self.video_player.get_next_frame()
            if frame:
                display_img = frame

        screen.blit(display_img, self.rect)  # 将卡牌图像绘制到屏幕上
        # 如果角色是傀儡
        if self.character.is_puppet:
            puppet_overlay = self.image.copy()  # 复制一份图像
            puppet_overlay.fill((100, 200, 100, 100), special_flags=pygame.BLEND_RGBA_MULT)  # 填充半透明绿色
            screen.blit(puppet_overlay, self.rect)  # 绘制覆盖层
        # 如果角色被控制
        if self.character.is_controlled:
            control_overlay = self.image.copy()  # 复制一份图像
            control_overlay.fill((100, 100, 120, 100), special_flags=pygame.BLEND_RGBA_MULT)  # 填充半透明灰色
            screen.blit(control_overlay, self.rect)  # 绘制覆盖层
        # 如果角色被选中，绘制黄色边框
        if self.is_selected: pygame.draw.rect(screen, (255, 255, 0), self.rect.inflate(6, 6), 3)
        # 如果是可选目标，绘制红色边框
        if self.is_targetable: pygame.draw.rect(screen, (255, 0, 0), self.rect.inflate(6, 6), 3)

        # 战斗阶段我方蓝色敌方红色
        name_color = self.character.get_color()
        display_name = f"{self.character.name} ({self.character.level})" if self.character.level else self.character.name
        # 拼接名字和境界等级
        name_surface = self.font.render(display_name, True, name_color)  # 创建渲染好的名字文本surface
        name_y = self.rect.top - 20 if not self.is_enemy else self.rect.bottom + 20  # 根据敌我位置决定名字显示在上方还是下方
        screen.blit(name_surface, name_surface.get_rect(center=(self.rect.centerx, name_y)))  # 绘制名字文本

        if show_stats:  # 如果需要显示状态条
            hp_bar_y = self.rect.bottom + 5 if not self.is_enemy else self.rect.top - 30  # 根据敌我决定状态条位置
            hp_bar = pygame.Rect(self.rect.left, hp_bar_y, self.rect.width, 14)  # 定义血条背景矩形
            # 如果角色存活
            if self.character.is_alive:
                # 计算当前生命值比例
                ratio = self.character.hp / self.character.max_hp if self.character.max_hp > 0 else 0
                fill_rect = pygame.Rect(self.rect.left, hp_bar_y, self.rect.width * ratio, 14)  # 定义血条前景矩形
                pygame.draw.rect(screen, (100, 0, 0), hp_bar)  # 绘制血条背景（暗红色）
                pygame.draw.rect(screen, (0, 200, 0), fill_rect)  # 绘制血条前景（绿色）
                hp_text = f"{int(self.character.hp)}/{int(self.character.max_hp)}"  # 创建HP文本字符串
                hp_surf = self.font_hp.render(hp_text, True, (255, 255, 255))  # 渲染HP文本
                screen.blit(hp_surf, hp_surf.get_rect(center=hp_bar.center))  # 将HP文本居中绘制在血条上

            hunliang_bar_y = hp_bar_y + hp_bar.height + 2  # 计算魂量条的Y坐标
            hunliang_bar = pygame.Rect(self.rect.left, hunliang_bar_y, self.rect.width, 10)  # 定义魂量条背景矩形
            # 如果角色存活且有魂量
            if self.character.is_alive and self.character.max_hunliang > 0:
                # 计算当前魂量比例
                ratio = self.character.hunliang / self.character.max_hunliang if self.character.max_hunliang > 0 else 0
                fill_rect = pygame.Rect(self.rect.left, hunliang_bar_y, self.rect.width * ratio, 10)  # 定义魂量条前景矩形
                pygame.draw.rect(screen, (50, 50, 100), hunliang_bar)  # 绘制魂量条背景
                pygame.draw.rect(screen, HUNLIANG_COLOR, fill_rect)  # 绘制魂量条前景
                hl_text = f"{int(self.character.hunliang)}/{int(self.character.max_hunliang)}"  # 创建魂量文本字符串
                hl_surf = self.font_hp.render(hl_text, True, (255, 255, 255))  # 渲染魂量文本
                screen.blit(hl_surf, hl_surf.get_rect(center=hunliang_bar.center))  # 将魂量文本居中绘制在魂量条上

    # 检查鼠标点击是否在该卡牌上
    def check_click(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)  # 返回Pygame的矩形碰撞检测结果


# 根据选择的境界等级，计算角色的最终属性
def calculate_stats_by_level(base_stats, selected_level, identity):
    # 处理神级身份：凡神、界王、神王
    if identity in ["凡神", "界王", "神王"]:
        try:
            level_multiplier = int(selected_level)
        except ValueError:
            level_multiplier = 1
        
        # 属性 = 基础值 * 等级数字 (不再有额外倍增)
        return {
            "hp": base_stats["hp"] * level_multiplier,
            "hundu": base_stats["hundu"] * level_multiplier,
            "hunliang": base_stats["hunliang"] * level_multiplier
        }
    
    levels = identity_LEVELS.get(identity, [])  # 获取该身份的所有境界等级列表
    if not levels or selected_level not in levels: return base_stats  # 如果列表为空或选择的等级无效，返回基础属性
    target_index = levels.index(selected_level)  # 获取目标境界在列表中的索引
    # 初始化最终属性为基础属性
    final_hp, final_hundu, final_hunliang = base_stats['hp'], base_stats['hundu'], base_stats['hunliang']
    # 从最低级开始迭代到目标境界
    for i in range(target_index):
        if i < len(STAT_MULTIPLIER_PATTERN):  # 确保索引在倍率模式列表的范围内
            m = STAT_MULTIPLIER_PATTERN[i]  # 获取当前等级的成长倍率
            final_hp *= m  # 计算生命值
            final_hundu *= m  # 计算魂度
            final_hunliang *= m  # 魂量以倍率的平方增长
    return {'hp': int(final_hp), 'hundu': int(final_hundu), 'hunliang': int(final_hunliang)}  # 返回计算后的整数属性

# 核心战斗循环界面
def main_gui(player_data, enemy_data):
    pygame.init()  # 初始化所有Pygame模块
    SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 900  # 设置初始屏幕宽度和高度
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)  # 创建一个可调整大小的显示窗口
    pygame.display.set_caption("我的世界 - 战斗")  # 设置窗口标题
    clock = pygame.time.Clock()  # 创建一个时钟对象来控制帧率
    try:  # 尝试加载资源文件
        # 使用项目根目录下的固定资源路径加载战斗背景
        background_image_original = pygame.image.load(str(PICTURE_DIR / "background_gold.png")).convert()

        font_big = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 50)  # 加载大号字体（用于标题）
        font_log = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 16)  # 加载小号字体（用于战斗日志）
        font_tooltip = pygame.font.Font("C:/Windows/Fonts/msyh.ttc", 14)  # 新增：提示框字体
    except Exception as e:  # 如果加载失败
        print(f"加载资源失败: {e}")  # 打印错误信息
        background_image_original = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))  # 创建一个备用背景表面
        background_image_original.fill((20, 40, 60))  # 填充深色背景
        font_big = pygame.font.Font(None, 60)  # 使用默认大号字体
        font_log = pygame.font.Font(None, 20)  # 使用默认小号字体
        font_tooltip = pygame.font.Font(None, 18)  # 新增：默认提示框字体
    font_big.set_bold(True)  # 将标题大号字体设为粗体

    combat_log = CombatLogDisplay(20, 20, SCREEN_WIDTH // 4, SCREEN_HEIGHT - 40, font_log)  # 初始化战斗日志显示框
    player_chars = [CharacterWithSkills(**p) for p in player_data]  # 创建玩家角色列表（属性、技能、状态）
    for char in player_chars: char.is_player_side = True  # 标记所有玩家角色属于玩家阵营
    enemy_chars = [CharacterWithSkills(**e) for e in enemy_data]  # 根据传入的数据创建敌人角色对象列表
    player_cards = [Card(c) for c in player_chars]  # 为每个玩家角色创建一张卡牌
    enemy_cards = [Card(c, is_enemy=True) for c in enemy_chars]  # 为每个敌人角色创建一张敌方卡牌
    for card in enemy_cards: card.character.is_player_side = False  # 标记所有敌人角色不属于玩家阵营

    effects_group = pygame.sprite.Group()  # 技能特效智能管理组，可以自动调用特效类的update函数和draw函数
    effect_queue = []  # 初始化特效队列
    recalculate_layout(SCREEN_WIDTH, SCREEN_HEIGHT, player_cards, enemy_cards, effects_group)  # 初始化战斗布局

    game_state, turn_phase = 'playing', 'START_ROUND'  # 初始化游戏状态为“游戏中”，回合阶段为“开始阶段”
    planned_actions, actors_with_plan = [], set()  # 初始化计划行动列表和已规划行动的角色集合
    selected_attacker_card, active_action, selected_targets, action_buttons = None, None, [], []  # 初始化行动规划相关的变量
    tooltip_info = None  # 新增：用于存储提示信息的状态
    targets_to_select_count = 0  # 初始化需要选择的目标数量
    pending_puppet = []  # 暂存待召唤的傀儡信息
    confirm_button = Button("确认行动", (SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2 - 30), (200, 60),
                            "confirm_turn", disabled=True)  # 创建确认回合行动的按钮
    current_round = 1  # 添加回合计数器，初始化为1

    # 重置与单次行动选择相关的状态，包括攻击者、行动、目标、按钮和目标数量
    def reset_action_state():
        # 声明要修改的外部函数变量
        nonlocal selected_attacker_card, active_action, selected_targets, action_buttons, targets_to_select_count
        if selected_attacker_card: selected_attacker_card.is_selected = False  # 如果有选中的攻击者，取消其选中状态
        for card in player_cards + enemy_cards: card.is_targetable = False  # 取消所有卡牌的可选目标状态
        selected_attacker_card, active_action, selected_targets, action_buttons = None, None, [], []  # 重置所有行动状态变量
        targets_to_select_count = 0  # 重置需选择目标数量

    # 从卡牌列表中筛选出所有能够行动的角色（存活、未被控制、魂量足够）
    def get_able_characters(card_list):
        return [card for card in card_list if
                card.character.is_alive and not card.character.is_controlled and can_character_act(card.character)]

    # 处理并结算所有已计划行动（关键）
    def resolve_planned_actions(actions, combat_log, effect_queue):
        puppets_plans = []
        potential_damage_map = {}
        total_damage_potential = {}
        all_involved_characters = set()  # 用于追踪所有参与本回合的角色

        # 遍历所有计划，计算伤害效果的可能伤害
        for plan in actions:
            actor_char, action = plan['actor'], plan['action']  # 获取计划中的施法者和技能
            is_potential_damage, base_value = False, 0
            # 计算可能的伤害
            if action == 'attack':
                is_potential_damage, base_value = True, actor_char.hundu  # 普攻的基础伤害值=魂度
            elif action == 'weapon_attack':
                is_potential_damage, base_value = True, actor_char.hundu * 2  # 普攻(武器)的基础伤害值=魂度*2
            elif isinstance(action, Skill) and action.skill_type == 'hp_debuff':
                # 伤害技能的每回合伤害基础值=技能值*角色最大魂量/持续时间
                is_potential_damage, base_value = True, (actor_char.hundu * action.value / action.duration)

            if not is_potential_damage: continue  # 非伤害型技能则跳过
            plan['damage_potential_map'] = {}  # 为当前行动计划创建一个可能伤害字典
            for target_card in plan['targets']:
                target_char = target_card.character  # 获取目标角色
                # 获取攻击者等级和目标等级（魂师0、魂铠1、魂灵2、神3）
                attacker_rank, target_rank = (IDENTITY_HIERARCHY.index(actor_char.identity),
                                              IDENTITY_HIERARCHY.index(target_char.identity))
                damage = 0
                if attacker_rank > target_rank:
                    damage = target_char.hp  # 攻击者等级高于目标等级则伤害为目标当前生命值（秒杀）
                elif attacker_rank == target_rank:
                    damage = base_value  # 攻击者等级等于目标等级则伤害为基本伤害
                elif attacker_rank < target_rank:
                    damage = 0  # 等级被压制时，伤害为0
                plan['damage_potential_map'][target_char] = damage  # 添加伤害信息到可能伤害字典中
                key = (actor_char, target_char)  # 构建攻击者-目标键
                potential_damage_map[key] = potential_damage_map.get(key, 0) + damage  # 累计特定角色对特定目标的伤害（抵消后伤害）
                total_damage_potential[key] = total_damage_potential.get(key, 0) + damage  # 累计特定角色对特定目标的伤害（初始总）

        processed_pairs = set()  # 重置已处理的相互攻击角色对
        # 查找可能伤害字典，相互攻击伤害抵消
        for attacker, target in list(potential_damage_map.keys()):
            if (attacker, target) in processed_pairs: continue  # 跳过已处理的相互攻击角色对
            reverse_key = (target, attacker)  # 反向键
            # 如果可能伤害字典中存在反向键，则说明有相互攻击
            if reverse_key in potential_damage_map:
                damage_to_target = potential_damage_map.get((attacker, target), 0)  # 获取攻击者对目标的伤害值
                damage_to_attacker = potential_damage_map.get(reverse_key, 0)  # 获取目标对攻击者的伤害值
                reduction = min(damage_to_target, damage_to_attacker)  # 较小的值作为抵消量
                # 如果抵消量大于0，则将伤害值减去抵消量
                if reduction > 0:
                    potential_damage_map[(attacker, target)] -= reduction  # 攻击者对目标的伤害值减去抵消量
                    potential_damage_map[reverse_key] -= reduction  # 目标对攻击者的伤害值减去抵消量
                    combat_log.add_message([(attacker.name, attacker.get_color()), (" 与 ", TEXT_COLOR),
                                            (target.name, target.get_color()), (" 的攻击互相冲突，", TEXT_COLOR),
                                            ("抵消了 ", TEXT_COLOR), (f"{int(reduction)}", DAMAGE_COLOR),
                                            (" 点伤害！", TEXT_COLOR)])
                processed_pairs.add((attacker, target))  # 添加已处理的冲突角色对以及反向对
                processed_pairs.add(reverse_key)

        # 按顺序应用所有行动
        for plan in actions:
            if not plan['actor'].is_alive: continue  # 忽略已死亡角色
            actor_char, action, target_cards = plan['actor'], plan['action'], plan['targets']

            # 统一计算消耗并扣除魂量
            cost = 0
            if action == 'attack':
                cost = max(0, actor_char.hundu)
            elif action == 'weapon_attack':
                cost = max(0, actor_char.hundu * 2)
            elif isinstance(action, Skill):
                cost = calculate_skill_cost(action, actor_char)
            actor_char.use_hunliang(cost)

            # 将行动者和目标都加入追踪集合
            all_involved_characters.add(plan['actor'])
            for target_card in plan['targets']:
                all_involved_characters.add(target_card.character)

            # 召唤类技能处理（puppet）
            if isinstance(action, Skill) and action.skill_type == 'puppet':
                for target_card in target_cards:
                    if target_card.character.is_alive:
                        puppets_plans.append({'actor': actor_char, 'action': action, 'source': target_card.character})
                continue  # 傀儡技能处理完毕，直接开始下一个行动计划，不进入后续流程

            # 大部分技能效果处理
            for target_card in target_cards:
                if not target_card.character.is_alive: continue
                target_char = target_card.character  # 目标角色
                duration = getattr(action, 'duration', 1)

                # 处理伤害性行动（普攻、伤害技能）的伤害
                is_damage_action = 'damage_potential_map' in plan
                if is_damage_action:
                    skill_type = 'hp_debuff'
                    # 将普攻和普攻(武器)的skill_type也设置为'hp_debuff'，封装成持续1回合的、类型为hp_debuff的特殊技能效果
                    if action == 'attack':
                        action_name = "普攻"
                    elif action == 'weapon_attack':
                        action_name = "普攻(武器)"
                    else:
                        action_name = action.name

                    # 从预计算的伤害结果中获取最终伤害值
                    total_potential = total_damage_potential.get((actor_char, target_char), 0)  # 施法者对目标的总伤害
                    net_damage = potential_damage_map.get((actor_char, target_char), 0)  # 相互抵消后的总净伤害
                    plan_potential = plan['damage_potential_map'].get(target_char, 0)  # 当前技能的伤害
                    # 计算当前技能的最终伤害（当前技能伤害与总伤害的比值*总净伤害）
                    final_damage = (net_damage * (plan_potential / total_potential)) if total_potential > 0 else 0
                    value_per_tick = final_damage  # 技能每回合的伤害，float
                # 处理所有非伤害性技能
                else:
                    action_name = action.name
                    skill_type = action.skill_type
                    value_per_tick = (actor_char.hundu * action.value) / max(1, duration)  # float

                # 如果最终效果值为0，则记录日志并跳过，不再创建StatusEffect。
                if value_per_tick <= 0:
                    attacker_rank = IDENTITY_HIERARCHY.index(actor_char.identity)
                    target_rank = IDENTITY_HIERARCHY.index(target_char.identity)
                    log_reason = " 被完全抵消了！"
                    if attacker_rank < target_rank: log_reason = " 由于身份压制而无效！"
                    if action != 'attack' and action != 'weapon_attack': log_reason = " 没有生效！"
                    combat_log.add_message([(actor_char.name, actor_char.get_color()), (" 对 ", TEXT_COLOR),
                                            (target_char.name, target_char.get_color()), (f" 的 ", TEXT_COLOR),
                                            (f"[{action_name}]", SKILL_COLOR), (log_reason, TEXT_COLOR)])
                    continue  # 继续处理下一个目标

                # 技能效果不为0时添加技能效果，在创建StatusEffect时，传入技能的特效名称
                asset_name_for_effect = getattr(action, 'asset_name', None) if isinstance(action, Skill) else None
                eff = StatusEffect(action_name, skill_type, value_per_tick, duration, caster=actor_char, asset_name=asset_name_for_effect)


                if action_name not in ["普攻", "普攻(武器)"]:
                    combat_log.add_message([(target_char.name, target_char.get_color()), (" 受到 ", TEXT_COLOR),
                                            (actor_char.name, actor_char.get_color()), (" 的", TEXT_COLOR),
                                            (f" [{action_name}] ", SKILL_COLOR), (f"效果，将持续 ", TEXT_COLOR),
                                            (f"{duration}", DAMAGE_COLOR), (f" 回合！", TEXT_COLOR)])

                target_char.apply_effect(eff, combat_log)  # 为目标角色添加效果状态（仅添加未触发，之前回合添加的不再添加）

                # 对于需要立即生效的技能，统一在此处触发首次 tick结算。
                instant_effect_types = ['hp_debuff', 'hp_buff', 'hunliang_buff', 'hunliang_debuff', 'defense']
                if skill_type in instant_effect_types:
                    eff.tick(target_char, combat_log)

            # 统一处理技能特效的视觉播放
            if isinstance(action, Skill) and action.asset_name and action.skill_type != 'puppet':
                for target_card in target_cards:
                    effect_queue.append({'position': target_card.rect.center, 'asset_name': action.asset_name,
                                         'size': target_card.rect.size})

        # 所有行动结算完后，确保在本回合内到期的效果，在进入下一回合前被彻底清除（1回合的护盾）
        for character in all_involved_characters:
            if not character.is_alive: continue
            surviving_effects = []  # 下回合仍然存活的效果

            for effect in character.active_effects:
                if effect.duration <= 0:
                    is_skill_effect = effect.name not in ["普攻", "普攻(武器)"]
                    if is_skill_effect:
                        combat_log.add_message([(character.name, character.get_color()), (f" 受到的 ", TEXT_COLOR),
                                                (f"[{effect.name}]", SKILL_COLOR), (f" 效果结束了。", TEXT_COLOR)])
                    effect.on_remove(character, combat_log)  # 恢复原始属性
                else:
                    surviving_effects.append(effect)

            character.active_effects = surviving_effects  # 保留下回合依然存在的效果

        # 返回傀儡计划
        return puppets_plans

    running = True  # 主循环标志
    while running:  # 开始主游戏循环
        clock.tick(60)  # 控制游戏最高帧率为60 FPS
        # 如果游戏正在进行中
        if game_state == 'playing':
            # 如果是“回合开始”阶段
            if turn_phase == 'START_ROUND':
                effect_queue.clear()  # <-- 新增：在此处清空特效队列
                combat_log.add_message([("第", (255, 255, 255)), (f"{current_round}", DAMAGE_COLOR), ("回合开始！", (255, 255, 255))])
                # 日志记录新回合开始
                current_round += 1  # 回合数增加1
                all_alive_cards = [c for c in player_cards + enemy_cards if c.character.is_alive]  # 获取所有存活的角色

                for card in all_alive_cards:
                    # 捕获update_effects返回的特效列表，并添加到主特效队列
                    triggered_vfx_assets = card.character.update_effects(combat_log)
                    for asset in triggered_vfx_assets:
                        effect_queue.append({
                            'position': card.rect.center,
                            'asset_name': asset,
                            'size': card.rect.size
                        })


                # 获取更新状态后所有存活的角色
                player_cards[:] = [c for c in player_cards if c.character.is_alive]
                enemy_cards[:] = [c for c in enemy_cards if c.character.is_alive]
                # 如果存活角色数发生改变，重新计算卡牌布局
                if len(player_cards) + len(enemy_cards) != len(all_alive_cards):
                    recalculate_layout(SCREEN_WIDTH, SCREEN_HEIGHT, player_cards, enemy_cards, effects_group)

                planned_actions.clear()  # 清空上一回合的行动计划
                actors_with_plan.clear()  # 清空已规划行动的角色集合
                reset_action_state()  # 重置单次行动选择的状态
                turn_phase = 'PLANNING'  # 转为行动规划阶段
                combat_log.add_message([("请规划角色行动：", (255, 255, 255))])

            # 如果是效果“结算”阶段
            elif turn_phase == 'RESOLUTION':
                # 调用结算函数，传入已规划的行动列表，返回
                combat_log.add_message([ ("伤害结算开始：", (255, 255, 255))])
                pending_puppet = resolve_planned_actions(planned_actions, combat_log, effect_queue)
                turn_phase = 'WAIT_FOR_EFFECTS'  # 技能效果结算后进入特效播放阶段

            # 特效检查阶段，待所有技能效果播放完毕后再进入清理阶段重新计算布局
            elif turn_phase == 'WAIT_FOR_EFFECTS':
                # 如果当前没有特效在播放，并且特效队列里还有待播放的特效
                if not effects_group and effect_queue:
                    effect_info = effect_queue.pop(0)  # 从队列中一次取出特效的信息
                    # 根据信息创建特效实例并添加到特效组中，准备播放
                    effects_group.add(SkillEffect(effect_info['position'], effect_info['asset_name'], effect_info['size']))

                # 只有当前播放特效和特效队列(等待播放)都为空时，才认为所有特效已播放完毕
                elif not effects_group and not effect_queue:
                    if pending_puppet:  # 如果有待召唤的傀儡
                        turn_phase = 'PROCESS_SPAWNS'  # 进入傀儡处理阶段
                    else:  # 如果没有
                        turn_phase = 'CLEANUP'  # 直接进入清理阶段

            # 傀儡召唤阶段
            elif turn_phase == 'PROCESS_SPAWNS':
                for spawn_info in pending_puppet:
                    actor_char = spawn_info['actor']  # 施法者
                    action = spawn_info['action']
                    p_source = spawn_info['source']  # 召唤的傀儡角色

                    # 获取源角色的技能列表
                    source_skills = p_source.skills if isinstance(p_source, CharacterWithSkills) else []

                    # 创建傀儡角色和卡牌 (继承一半最大魂量和全部技能)
                    p_char = CharacterWithSkills(f"{p_source.name}的召唤", p_source.max_hp // 2, p_source.hundu // 2,
                                                 p_source.max_hunliang // 2, p_source.image_path, source_skills, p_source.identity,
                                                 p_source.level, is_puppet=True, puppet_duration=action.duration, summoner=actor_char)
                    p_char.is_player_side = p_source.is_player_side
                    p_card = Card(p_char, is_enemy=not p_source.is_player_side)

                    # 将傀儡加入对应的卡牌列表
                    if p_source.is_player_side:
                        player_cards.append(p_card)
                    else:
                        enemy_cards.append(p_card)

                    combat_log.add_message([(actor_char.name, actor_char.get_color()), (f" 为 ", TEXT_COLOR),
                                            (p_source.name, p_source.get_color()), (" 召唤了傀儡，", TEXT_COLOR),
                                            ("持续", TEXT_COLOR), (f" {action.duration} ", DAMAGE_COLOR),
                                            ("回合。", TEXT_COLOR)])
                    spawn_info['new_card'] = p_card

                # 所有傀儡都创建完毕后，统一重新计算布局
                recalculate_layout(SCREEN_WIDTH, SCREEN_HEIGHT, player_cards, enemy_cards, effects_group)

                # 布局更新后，在傀儡的“新位置”上创建召唤特效
                for spawn_info in pending_puppet:
                    if spawn_info['action'].asset_name:
                        new_card = spawn_info['new_card']
                        effects_group.add(SkillEffect(new_card.rect.center, spawn_info['action'].asset_name, new_card.rect.size))
                # 清空待办列表，并返回等待特效播放阶段
                pending_puppet.clear()
                turn_phase = 'WAIT_FOR_EFFECTS'
            # 清理阶段重新（死亡、傀儡）计算布局
            elif turn_phase == 'CLEANUP':
                card_count_before_cleanup = len(player_cards) + len(enemy_cards)  # 记录清理前的卡牌总数
                player_cards[:] = [c for c in player_cards if c.character.is_alive]  # 再次清理玩家死亡单位
                enemy_cards[:] = [c for c in enemy_cards if c.character.is_alive]  # 再次清理敌人死亡单位

                if len(player_cards) + len(enemy_cards) != card_count_before_cleanup:  # 如果有单位在结算中死亡
                    recalculate_layout(SCREEN_WIDTH, SCREEN_HEIGHT, player_cards, enemy_cards, effects_group)  # 重新计算布局

                if not any(c.character.is_alive for c in player_cards):  # 检查玩家是否全部阵亡
                    game_state = 'enemy_win'  # 游戏状态变为“敌人胜利”
                elif not any(c.character.is_alive for c in enemy_cards):  # 检查敌人是否全部阵亡
                    game_state = 'player_win'  # 游戏状态变为“玩家胜利”
                else:  # 如果双方都有人存活
                    player_can_act = any(can_character_act(c.character) for c in player_cards if c.character.is_alive)
                    # 检查玩家是否还有角色能行动
                    enemy_can_act = any(can_character_act(c.character) for c in enemy_cards if c.character.is_alive)
                    # 检查敌人是否还有角色能行动
                    if not player_can_act:  # 如果玩家因魂量耗尽无法行动
                        game_state = 'enemy_win'  # 判定为敌人胜利
                        combat_log.add_message([("我方魂量耗尽，已无力再战！", TEXT_COLOR)])  # 显示提示信息
                    elif not enemy_can_act:  # 如果敌人因魂量耗尽无法行动
                        game_state = 'player_win'  # 判定为玩家胜利
                        combat_log.add_message([("敌方魂量耗尽，已是强弩之末！", TEXT_COLOR)])  # 显示提示信息

                if game_state == 'playing':  # 如果战斗继续
                    pygame.time.delay(200)  # 短暂延迟，给玩家反应时间
                    combat_log.add_message([("", TEXT_COLOR)])  # 添加空行
                    turn_phase = 'START_ROUND'  # 进入下一个“回合开始”阶段

        able_planning_cards = []  # 重置可行动角色列表
        # 如果处于“规划”阶段（回合开始阶段之后），获取可操作卡牌列表
        if turn_phase == 'PLANNING':
            all_planning_cards = player_cards + enemy_cards  # 合并我方和敌方所有卡牌
            able_planning_cards = get_able_characters(all_planning_cards)  # 获取所有能行动的角色

        # 开始事件循环，处理点击操作
        for event in pygame.event.get():
            combat_log.handle_event(event)  # 将事件传递给战斗日志处理
            if event.type == pygame.QUIT: running = False  # 如果点击关闭按钮，则退出游戏循环
            if event.type == pygame.VIDEORESIZE:  # 如果窗口大小被调整
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h  # 获取新的宽高
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)  # 重设屏幕
                recalculate_layout(SCREEN_WIDTH, SCREEN_HEIGHT, player_cards, enemy_cards, effects_group)  # 重新计算所有布局
                combat_log.rect.height = SCREEN_HEIGHT - 40  # 调整战斗日志的高度
                confirm_button.rect.topleft = (SCREEN_WIDTH - 220, SCREEN_HEIGHT / 2 - 30)  # 调整确认按钮的位置
            if event.type == pygame.MOUSEMOTION:
                tooltip_info = None  # 鼠标一动就重置提示信息
                if turn_phase == 'PLANNING':  # 只在规划阶段检查
                    for btn in action_buttons:
                        if btn.check_click(event.pos):
                            # 检查按钮的 action 是否是 Skill 实例并且有 text 属性
                            if isinstance(btn.action, Skill) and btn.action.text:
                                tooltip_info = {'text': btn.action.text, 'pos': event.pos}
                                break  # 找到一个悬停的按钮就够了
            # 如果不是在规划阶段，则忽略后续的鼠标事件，继续下一次事件循环
            if game_state != 'playing' or turn_phase != 'PLANNING': continue
            # 如果检测到鼠标点击
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 如果点击了“确认行动”按钮
                if confirm_button.check_click(event.pos):
                    turn_phase = 'RESOLUTION'  # 直接切换到结算阶段
                    continue  # 本次点击事件处理完毕
                if event.button == 3: reset_action_state(); continue  # 如果是鼠标右键点击，则重置单个行动状态，关闭技能按钮及框
                # 如果是鼠标左键点击
                if event.button == 1:
                    # 如果已经点击过了个行动技能按钮（即选择技能目标时）
                    if active_action:
                        skill_is_friendly = (isinstance(active_action, Skill) and active_action.skill_type in
                                             ['hp_buff', 'hundu_buff', 'hunliang_buff', 'identity_buff', 'puppet',
                                              'defense'])
                        # 判断技能是友方技能还是敌方技能，根据技能类型和使用者阵营确定目标阵营
                        potential_targets = player_cards if (
                                selected_attacker_card.character.is_player_side == skill_is_friendly) else enemy_cards
                        enemy_puppets = [c for c in potential_targets if c.character.is_alive and c.character.is_puppet]
                        # 查找目标阵营中的傀儡
                        if not skill_is_friendly and enemy_puppets:  # 如果是敌方技能且对方场上有傀儡
                            targetable_cards = enemy_puppets  # 只能选择傀儡作为技能目标
                        else:  # 对于友方技能，或者当敌方没有傀儡时，所有活着的目标阵营单位都是可选目标
                            targetable_cards = [c for c in potential_targets if c.character.is_alive]
                        # 遍历所有可选目标
                        for card in targetable_cards:
                            # 如果点击了某个未被选中的可选目标
                            if card.is_targetable and card not in selected_targets and card.check_click(event.pos):
                                selected_targets.append(card)  # 将其加入已选目标列表
                                card.is_targetable = False  # 取消其红色边框，表示“已选”
                                break  # 跳出循环
                        # 如果已选目标的数量达到了技能要求的数量
                        if len(selected_targets) == targets_to_select_count:
                            cost = 0 # 计算魂量消耗
                            if active_action == 'attack':  # 普攻消耗等于魂度
                                cost = max(0, selected_attacker_card.character.hundu)
                            elif active_action == 'weapon_attack':  # 普攻(武器)消耗等于魂度*2
                                cost = max(0, selected_attacker_card.character.hundu * 2)
                            elif isinstance(active_action, Skill):
                                cost = calculate_skill_cost(active_action, selected_attacker_card.character)
                            # 如果魂量足够
                            if selected_attacker_card.character.hunliang >= cost:
                                action_name = ""
                                if active_action == 'attack':
                                    action_name = "普攻"
                                elif active_action == 'weapon_attack':
                                    action_name = "普攻(武器)"
                                elif isinstance(active_action, Skill):
                                    action_name = active_action.name
                                target_names = ", ".join([t.character.name for t in selected_targets])

                                # 创建日志，将行动计划（施法者、技能、目标、日志）添加到激活行动列表
                                log_entry = [(selected_attacker_card.character.name, selected_attacker_card.character.get_color()),
                                             (f" 计划对 ", TEXT_COLOR), (target_names, selected_targets[0].character.get_color()),
                                             (f" 使用 ", TEXT_COLOR), (f"[{action_name}]", SKILL_COLOR)]
                                planned_actions.append({'actor': selected_attacker_card.character, 'action': active_action,
                                                        'targets': selected_targets, 'log_message': log_entry})
                                actors_with_plan.add(selected_attacker_card.character)  # 将角色添加到已计划行动角色列表中
                                combat_log.add_message(log_entry)  # 添加日志
                            # 如果魂量不足
                            else:
                                combat_log.add_message([(selected_attacker_card.character.name,  # 添加提示日志
                                                         selected_attacker_card.character.get_color()),
                                                        (f" 魂量不足，请重新选择！", TEXT_COLOR)])
                            reset_action_state()  # 完成一次行动规划后，重置单个行动状态
                        continue  # 本次点击事件处理完毕
                    # 如果点击技能按钮时
                    if any(btn.check_click(event.pos) for btn in action_buttons):
                        for btn in action_buttons:  # 遍历所有行动按钮
                            if btn.check_click(event.pos):  # 找到被点击的那个
                                active_action = btn.action  # 设置为已点击激活的技能，下一次循环进入上面的if
                                skill_is_friendly = isinstance(active_action, Skill) and active_action.skill_type in [
                                    'hp_buff', 'hundu_buff', 'hunliang_buff', 'identity_buff', 'puppet', 'defense']
                                # 判断技能类型为对敌还是对己，确定技能目标阵营
                                potential_targets = player_cards if (selected_attacker_card.character.is_player_side
                                                                     == skill_is_friendly) else enemy_cards
                                puppets = [c for c in potential_targets if
                                           c.character.is_alive and c.character.is_puppet]  # 查找傀儡
                                if not skill_is_friendly and puppets:  # 对敌技能且对方有傀儡
                                    targetable_cards = puppets  # 目标只能是傀儡
                                else:
                                    targetable_cards = [c for c in potential_targets if c.character.is_alive]
                                # 获取技能的目标数量
                                num_targets = active_action.num_targets if isinstance(active_action, Skill) else 1
                                targets_to_select_count = min(num_targets, len(targetable_cards))  # 确定实际可选择的目标数
                                for card in targetable_cards: card.is_targetable = True  # 在draw函数中红色框选所有可选目标
                                action_buttons = []  # 隐藏技能按钮
                                break  # 结束按钮检查
                        continue  # 本次点击事件处理完毕
                    # 点击角色时，遍历所有能行动的卡牌找到被点击的卡牌
                    for card in able_planning_cards:
                        if card.check_click(event.pos):
                            # 如果这张被点击的卡牌对应的角色已经有计划了，则取消该角色已规划的行动
                            if card.character in actors_with_plan:
                                plan_to_remove = next((p for p in planned_actions if p['actor'] == card.character),None)
                                if plan_to_remove:
                                    combat_log.remove_message(plan_to_remove['log_message'])
                                    planned_actions.remove(plan_to_remove)# 从日志和计划列表中移除
                                actors_with_plan.remove(card.character)  # 从已规划角色列表移除该角色
                                reset_action_state()  #  重置单个行动状态
                            # 如果该角色还没有计划，则选择
                            else:
                                reset_action_state()
                                card.is_selected = True  # 设置该角色为已选择，黄色边框
                                selected_attacker_card = card  # 用于显示中央文本
                                btn_y = card.rect.bottom + 35 if card.is_enemy else card.rect.y - 50  # 计算技能显示按钮的Y坐标
                                spacing, temp_buttons = 10, []  # 定义按钮间距和临时按钮列表

                                atk_cost = max(0, card.character.hundu)  # 计算普攻消耗
                                weapon_atk_cost = max(0, card.character.hundu * 2)  # 计算普攻(武器)消耗
                                temp_buttons.append(Button(f"普攻\n({int(atk_cost)})", (0, btn_y), (100, 70), "attack",
                                                           disabled=card.character.hunliang < atk_cost)) # 创建普攻按钮
                                is_weapon_attack_locked = (card.character.identity == "魂师" or card.character.level in ["初铠前", "初铠中", "初铠后"])
                                # 普攻(武器)按钮 (当角色等级为中铠以下时禁用)
                                temp_buttons.append(Button(f"普攻(武器)\n({int(weapon_atk_cost)})", (0, btn_y), (140, 70),
                                           "weapon_attack", disabled=(card.character.hunliang < weapon_atk_cost) or is_weapon_attack_locked))
                                # 如果角色有技能
                                if isinstance(card.character, CharacterWithSkills):
                                    for skill in card.character.skills:  # 遍历技能
                                        cost = calculate_skill_cost(skill, card.character)  # 计算技能消耗
                                        # 根据魂量、等级、技能类型判断是否禁用
                                        is_disabled = card.character.hunliang < cost
                                        if card.character.level in ["初铠前", "初铠中", "初铠后", "中铠前", "中铠中", "中铠后"]:
                                            if skill.name == '爆种(天赋)':
                                                is_disabled = False
                                            else: is_disabled = True
                                        # 使用最终的禁用状态创建技能按钮，返回技能类
                                        temp_buttons.append(Button(f"{skill.name}\n({int(cost)})", (0, btn_y),
                                                                   (200, 70), skill, disabled=is_disabled))
                                # 技能按钮布局
                                max_width = SCREEN_WIDTH * 0.9  # 按钮区域最大宽度为屏幕的90%
                                line_height = temp_buttons[0].rect.height + 10 if temp_buttons else 0  # 按钮高度 + 垂直间距
                                rows = []
                                current_row = []
                                current_width = 0

                                # 将按钮分组到行
                                for btn in temp_buttons:
                                    btn_width = btn.rect.width
                                    # 如果当前行是空的，或者加上新按钮不会超宽
                                    if not current_row or current_width + spacing + btn_width <= max_width:
                                        current_row.append(btn)
                                        current_width += btn_width + (spacing if len(current_row) > 1 else 0)
                                    # 如果会超宽，则开始新的一行
                                    else:
                                        rows.append(current_row)
                                        current_row = [btn]
                                        current_width = btn_width
                                # 添加最后一行
                                if current_row:
                                    rows.append(current_row)

                                # 为每一行按钮设置位置
                                total_rows_height = len(rows) * line_height - 10  # 计算按钮区域总高度
                                # 根据敌我双方决定按钮组的起始Y坐标
                                start_y = (card.rect.y - total_rows_height - 15) if not card.is_enemy else (
                                            card.rect.bottom + 15)
                                for i, row in enumerate(rows):
                                    row_width = sum(b.rect.width for b in row) + spacing * (len(row) - 1)
                                    current_x = card.rect.centerx - row_width / 2  # 计算当前行的起始X坐标以居中

                                    screen_margin = 10  # 设置一个屏幕边缘的最小间距
                                    # 如果按钮组的左侧超出了屏幕左边缘
                                    if current_x < screen_margin:
                                        current_x = screen_margin
                                    # 如果按钮组的右侧超出了屏幕右边缘
                                    if current_x + row_width > SCREEN_WIDTH - screen_margin:
                                        current_x = SCREEN_WIDTH - row_width - screen_margin

                                    current_y = start_y + i * line_height
                                    for btn in row:
                                        btn.rect.topleft = (int(current_x), int(current_y))
                                        action_buttons.append(btn)
                                        current_x += btn.rect.width + spacing
                            break

        effects_group.update()  # 更新剩余特效帧（调用SkillEffect类的update函数）
        # 绘制背景图
        screen.blit(pygame.transform.scale(background_image_original, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))

        # 遍历所有卡牌
        for card in player_cards + enemy_cards:
            card.draw(screen, show_stats=True)  # 绘制卡牌及其状态条
            if card.character in actors_with_plan:  # 如果该卡牌的角色已规划行动
                overlay = card.image.copy()  # 复制图像
                overlay.fill((0, 0, 0, 128), special_flags=pygame.BLEND_RGBA_MULT)  # 填充半透明黑色覆盖层
                screen.blit(overlay, card.rect)  # 绘制覆盖层以表示“已行动”
            elif card.character.is_alive and not can_character_act(card.character):  # 如果角色存活但无法行动
                overlay = card.image.copy()  # 复制图像
                overlay.fill((180, 50, 50, 150), special_flags=pygame.BLEND_RGBA_MULT)  # 填充半透明红色覆盖层
                screen.blit(overlay, card.rect)  # 绘制覆盖层以表示“无法行动”
        # 已选中的技能目标绘制绿框
        for target in selected_targets: pygame.draw.rect(screen, HEAL_COLOR, target.rect.inflate(8, 8), 4)
        effects_group.draw(screen)  # 绘制所有技能特效
        combat_log.draw(screen)  # 绘制战斗日志
        for button in action_buttons: button.draw(screen)  # 绘制所有行动技能按钮
        # 行动规划阶段
        if game_state == 'playing' and turn_phase == 'PLANNING':
            num_able = len(able_planning_cards)  # 获取能行动的角色数量
            confirm_button.disabled = len(actors_with_plan) != num_able  # 如果已规划数量不等于可行动数量，则禁用确认按钮
            confirm_button.draw(screen)  # 绘制确认按钮
            # 如果正在选择技能使用目标（技能按钮已激活），屏幕中央提示选择目标
            if active_action:
                turn_text = f"请为[{selected_attacker_card.character.name}]选择 {targets_to_select_count - len(selected_targets)} 个目标"
            # 如果正在选择角色/行动，屏幕中央提示规划行动
            else:
                turn_text = "无角色可行动" if num_able == 0 else f"请规划角色行动 ({len(actors_with_plan)}/{num_able})"
            turn_surf = font_big.render(turn_text, True, TEXT_COLOR)  # 渲染回合提示文本
            turn_rect = turn_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))  # 获取文本矩形背景并居中
            pygame.draw.rect(screen, (255, 255, 255, 150), turn_rect.inflate(20, 10))  # 绘制一个半透明的白色背景框
            screen.blit(turn_surf, turn_rect)  # 绘制文本
        # 如果游戏结束
        elif game_state != 'playing':
            text = "恭喜你，获得胜利！" if game_state == 'player_win' else "很遗憾，你失败了"  # 根据胜负结果设置文本
            surf = font_big.render(text, True, (255, 200, 0))  # 渲染结束文本
            screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)))  # 将结束文本居中绘制

        if tooltip_info:
            padding = 5
            # 渲染文本
            tooltip_surf = font_tooltip.render(tooltip_info['text'], True, (255, 255, 255))
            tooltip_rect = tooltip_surf.get_rect()

            # 创建背景矩形，并设置其位置
            bg_rect = tooltip_rect.inflate(padding * 2, padding * 2)
            # 基础位置在鼠标指针右下方
            bg_rect.topleft = (tooltip_info['pos'][0] + 15, tooltip_info['pos'][1] + 10)

            # 防止提示框超出屏幕边界
            if bg_rect.right > SCREEN_WIDTH: bg_rect.right = SCREEN_WIDTH
            if bg_rect.bottom > SCREEN_HEIGHT: bg_rect.bottom = SCREEN_HEIGHT

            # 确定文本在背景框内的位置
            tooltip_rect.topleft = (bg_rect.left + padding, bg_rect.top + padding)

            # 绘制半透明背景和文本
            s = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            s.fill((20, 20, 30, 220))  # 半透明背景色 (R, G, B, Alpha)
            screen.blit(s, bg_rect.topleft)
            pygame.draw.rect(screen, (150, 150, 150), bg_rect, 1)  # 边框
            screen.blit(tooltip_surf, tooltip_rect)

        pygame.display.flip()  # 更新整个屏幕显示
    return 'main_menu'  # 战斗结束后，返回到主菜单


# 战斗日志显示类
class CombatLogDisplay:
    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)  # 设置日志显示矩形区域
        self.font = font  # 存储用于渲染所有文本的字体对象
        self.messages = []  # 原始消息（未换行）
        self.wrapped_lines = []  # 经过换行处理后的所有行
        self.scroll_offset = 0  # 滚动位置。0代表滚动条在最底部（最新）
        self.line_height = self.font.get_height()  # 文本行像素高度
        self.padding = 5  # 文本距离边框的距离
        self.dirty = True  # 标志位，为True时表示日志内容发生变化，重新计算布局
        self.is_dragging = False
        self.scrollbar_bg_rect = None
        self.scrollbar_thumb_rect = None

    # 添加一条日志消息
    def add_message(self, structured_message):
        if not structured_message: return  # 忽略空的无效消息
        self.messages.append(structured_message)  # 将新的原始消息追加到 self.messages 列表中
        self.dirty = True  # 重新计算换行
        self.scroll_offset = 0  # 新消息滚动到底部

    # 移除一条日志消息
    def remove_message(self, message_to_remove):
        original_length = len(self.messages)  # 记录原始的日志数量
        # 使用列表推导式创建一个新的列表，新列表中只包含那些与我们要移除的日志对象不是同一个对象（is not）的日志
        self.messages = [msg for msg in self.messages if msg is not message_to_remove]
        # 如果列表的长度变短了，说明成功移除了一个元素
        if len(self.messages) < original_length:
            self.dirty = True

    # 计算换行
    def _rewrap_messages(self):
        self.wrapped_lines.clear()  # 清空旧的换行布局缓存
        max_width = self.rect.width - self.padding * 2  # 文本可用的最大宽度

        for msg in self.messages:
            if msg and not msg[0][0]:
                self.wrapped_lines.append([])  # 消息的第一个文本片段为空则添加一个空行（回合空行）
                continue  # 处理下一条消息
            current_line = []  # 当前行中的所有文本片段
            current_x = 0  # 当前行的水平像素位置
            space_width = self.font.size(' ')[0]  # 当前字体下一个空格的宽度5
            # 对于一条信息的每一块文本片段（文本，颜色）
            for text, color in msg:
                words = text.split(' ')  # 将消息文本按空格进行拆分
                for i, word in enumerate(words):
                    word_surf = self.font.render(word, True, color)  # 渲染单词（小图片）
                    word_width = word_surf.get_width()  # 获取单词的像素宽度
                    # 如果单词本身就比一行长，需要强制拆分
                    while word_width > max_width:
                        split_index = 0 # 找到能容纳的最大字符数
                        while self.font.size(word[:split_index + 1])[0] < max_width: split_index += 1
                        # 添加能容纳的部分，然后开始新行
                        if current_line:  # 如果当前行有内容，先提交
                            self.wrapped_lines.append(current_line)
                        self.wrapped_lines.append([(self.font.render(word[:split_index], True, color), self.padding)])
                        word = word[split_index:]  # 更新单词为剩余部分
                        word_surf = self.font.render(word, True, color)
                        word_width = word_surf.get_width()
                        current_line = []
                        current_x = 0
                    # 如果加上新单词会超出一行
                    if current_x + word_width > max_width and current_line:
                        self.wrapped_lines.append(current_line)  # 提交当前行到最终列表
                        current_line = []  # 开启新空行
                        current_x = 0
                    # 添加单词，x坐标递增
                    current_line.append((word_surf, self.padding + current_x))
                    current_x += word_width

                    # 如果不是最后一个词，加上空格
                    if i < len(words) - 1:
                        current_x += space_width

            if current_line:
                self.wrapped_lines.append(current_line)
        self.dirty = False

    # 鼠标滚轮、点击和拖动查看日志
    def handle_event(self, event):
        total_lines = len(self.wrapped_lines)
        visible_lines = self.rect.height // self.line_height
        max_scroll = max(0, total_lines - visible_lines)
        mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONDOWN:
            # 滚轮滚动
            if self.rect.collidepoint(mouse_pos):
                if event.button == 4:
                    self.scroll_offset += 1
                elif event.button == 5:
                    self.scroll_offset -= 1

            # 左键点击或拖动
            if event.button == 1:
                # 如果点击在滑块上，开始拖动
                if self.scrollbar_thumb_rect and self.scrollbar_thumb_rect.collidepoint(mouse_pos):
                    self.is_dragging = True
                # 如果点击在滚动条背景上，直接跳转
                elif self.scrollbar_bg_rect and self.scrollbar_bg_rect.collidepoint(mouse_pos):
                    # 计算点击位置在滚动条内的百分比
                    click_y_ratio = (mouse_pos[1] - self.scrollbar_bg_rect.top) / self.scrollbar_bg_rect.height
                    # 根据百分比设置滚动偏移 (注意：顶部是最大滚动值，底部是0)
                    self.scroll_offset = round(max_scroll * (1 - click_y_ratio))

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False  # 释放鼠标，停止拖动

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging and self.scrollbar_bg_rect:
                # 计算鼠标位置在滚动条内的百分比
                drag_y_ratio = (mouse_pos[1] - self.scrollbar_bg_rect.top) / self.scrollbar_bg_rect.height
                self.scroll_offset = round(max_scroll * (1 - drag_y_ratio))

        # 统一限制滚动范围
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

    # 绘制日志
    def draw(self, screen):
        if self.dirty:
            self._rewrap_messages()

        log_background = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        log_background.fill((40, 40, 50, 180))
        screen.blit(log_background, self.rect.topleft)

        total_lines = len(self.wrapped_lines)
        visible_lines = self.rect.height // self.line_height
        start_index = max(0, total_lines - self.scroll_offset - visible_lines)
        end_index = total_lines - self.scroll_offset
        lines_to_display = self.wrapped_lines[start_index:end_index]

        for i, line in enumerate(lines_to_display):
            y_pos = self.rect.top + i * self.line_height
            for segment_surf, x_offset in line:
                screen.blit(segment_surf, (self.rect.left + x_offset, y_pos))

        # 绘制滚动条
        if total_lines > visible_lines:
            # 更新滚动条背景矩形实例变量
            self.scrollbar_bg_rect = pygame.Rect(self.rect.right - 12, self.rect.top, 10, self.rect.height)
            pygame.draw.rect(screen, (70, 70, 80), self.scrollbar_bg_rect)

            total_scrollable_range = total_lines - visible_lines
            scroll_percentage = self.scroll_offset / total_scrollable_range if total_scrollable_range > 0 else 0

            thumb_height = max(20, self.rect.height * (visible_lines / total_lines))
            thumb_y_range = self.rect.height - thumb_height
            thumb_y = self.rect.top + thumb_y_range * (1 - scroll_percentage)

            # 更新滑块矩形实例变量
            self.scrollbar_thumb_rect = pygame.Rect(self.rect.right - 12, thumb_y, 10, thumb_height)
            pygame.draw.rect(screen, (150, 150, 160), self.scrollbar_thumb_rect)
        else:
            # 如果不需要滚动条，清空矩形变量
            self.scrollbar_bg_rect = None
            self.scrollbar_thumb_rect = None


# 带技能的角色属性类，继承自Character，存储技能
class CharacterWithSkills(Character):
    def __init__(self, name, hp, hundu, hunliang, image_path, skills, identity, level="", **kwargs):  # 初始化
        super().__init__(name, hp, hundu, hunliang, image_path, identity, level, **kwargs)  # 调用父类的初始化方法
        self.skills = skills or []  # 角色的技能列表，如果传入None则为空列表


# 计算战斗页面卡牌的位置和大小
def recalculate_layout(screen_width, screen_height, player_cards, enemy_cards, effects_group):
    card_h = screen_height // 4.5  # 根据屏幕高度计算卡牌高度
    card_w = int(card_h * 0.75)  # 根据高度计算卡牌宽度以保持比例3：4
    size, spacing = (card_w, card_h), card_w + (screen_width // 25)  # 定义卡牌尺寸和卡牌间的水平间距
    # 如果玩家阵营有卡牌
    if player_cards:
        total_w_p = len(player_cards) * spacing - (screen_width // 25)  # 计算玩家卡牌区域的总宽度
        start_x_p = (screen_width - total_w_p) / 2  # 计算起始X坐标以使其居中
        for i, card in enumerate(player_cards):  # 遍历每个玩家卡牌
            card.image = pygame.transform.smoothscale(card.original_image, size)  # 平滑缩放卡牌图像到新尺寸
            card.rect = card.image.get_rect(
                topleft=(start_x_p + i * spacing, screen_height - card_h - (screen_height // 15)))  # 设置卡牌的左上角坐标
    # 如果敌人阵营有卡牌
    if enemy_cards:
        total_w_e = len(enemy_cards) * spacing - (screen_width // 25)  # 计算敌人卡牌区域的总宽度
        start_x_e = (screen_width - total_w_e) / 2  # 计算起始X坐标以使其居中
        for i, card in enumerate(enemy_cards):  # 遍历每个敌人卡牌
            card.image = pygame.transform.smoothscale(card.original_image, size)  # 平滑缩放卡牌图像到新尺寸
            card.rect = card.image.get_rect(topleft=(start_x_e + i * spacing, screen_height // 15))  # 设置卡牌的左上角坐标
    # 加载技能特效以适应卡牌大小
    for effect in effects_group: effect.load_frames(effect.asset_name, size)

# 检查角色是否有足够的魂量来执行至少一个行动
def can_character_act(character):
    if character.hunliang == 0: return False
    attack_cost = max(1, character.hundu)  # 计算普通攻击的消耗
    if character.hunliang >= attack_cost:  # 如果魂量足够进行普通攻击
        return True  # 返回True
    if isinstance(character, CharacterWithSkills):  # 如果角色是带技能的角色
        for skill in character.skills:  # 遍历所有技能
            skill_cost = calculate_skill_cost(skill, character)  # 计算技能消耗
            if character.hunliang >= skill_cost:  # 如果魂量足够使用该技能
                return True  # 返回True
    return False  # 如果所有行动的魂量都不足，返回False


# 技能特效类，用于在屏幕上播放动画
class SkillEffect(pygame.sprite.Sprite):
    def __init__(self, position, asset_name, size):  # 初始化一个技能特效
        super().__init__()  # 调用父类(Sprite)的初始化方法
        self.frames = []  # 用于存储动画的所有帧图像
        self.asset_name = asset_name  # 特效资源的名称
        self.load_frames(asset_name, size)  # 加载动画帧
        self.animation_speed = 120  # 动画播放速度（75毫秒/帧），越小越快越流畅
        self.last_update = pygame.time.get_ticks()  # 记录上一帧更新的时间
        if not self.frames:  # 如果没有加载到任何帧（无特效图）
            self.current_frame = 1  # 当前帧设为1
            self.image = pygame.Surface((0, 0))  # 创建一个空的图像
            self.rect = self.image.get_rect()  # 获取其矩形区域
        else:  # 如果成功加载到帧
            self.current_frame = 0  # 从第0帧开始
            self.image = self.frames[self.current_frame]  # 设置当前显示的图像
            self.rect = self.image.get_rect(center=position)  # 将特效居中放置在目标位置

    # 加载技能动画帧的函数
    def load_frames(self, asset_name, size):
        effect_dir = EFFECTS_DIR / asset_name  # 构建特效帧所在的文件夹路径
        i = 1  # 从第一帧开始查找
        while True:  # 无限循环，直到找不到新的帧
            filename = effect_dir / f"frame_{i}.png"  # 构建当前帧的文件名
            try:  # 尝试加载
                frame = pygame.image.load(str(filename)).convert_alpha()  # 加载图片并保留透明通道
                self.frames.append(pygame.transform.scale(frame, size))  # 缩放到指定尺寸并添加到帧列表
                i += 1  # 帧数加一，准备加载下一帧
            except (pygame.error, FileNotFoundError):  # 如果加载失败或文件不存在
                break  # 结束循环

    # 更新动画的每一帧
    def update(self):
        now = pygame.time.get_ticks()  # 获取当前时间
        if now - self.last_update > self.animation_speed:  # 如果距离上次更新已超过指定间隔
            self.last_update = now  # 更新“上次更新时间”
            self.current_frame += 1  # 切换到下一帧
            if self.current_frame >= len(self.frames):  # 如果已播放完所有帧
                self.kill()  # 从所有Sprite组中移除并销毁该特效
            else:  # 如果动画还未结束
                center = self.rect.center  # 保存当前位置
                self.image = self.frames[self.current_frame]  # 更新显示的图像为下一帧
                self.rect = self.image.get_rect(center=center)  # 保持特效位置不变


# 状态效果类，用于处理所有持续性效果（如中毒、祝福、虚弱等）
class StatusEffect:
    def __init__(self, name, skill_type, modifier, duration, caster=None, asset_name=None):
        self.name = name  # 技能名称，如“中毒”
        self.skill_type = skill_type  # 技能效果类型，如“hp_debuff”
        self.modifier = modifier  # 效果的数值（如每回合伤害、属性加成）
        self.duration = duration  # 对于持续伤害(hp_buff\defense\)等希望本回合立即触发的效果，保持原样。
        self.caster = caster  # 施法者
        self.is_first_tick = True
        self.current_turn_shield = 0  # 本回合内剩余护盾
        self.asset_name = asset_name  # 存储特效名称

    # 效果触发逻辑（改变属性的效果）
    def on_apply(self, owner, combat_log):
        # 如果效果会改变属性，则先保存其原始属性。
        if self.skill_type in ['identity_buff', 'identity_debuff', 'hundu_buff', 'hundu_debuff']:
            owner.save_original_stats()

    # 技能效果每次触发函数，回合-1（无傀儡技能，关键）
    def tick(self, owner, combat_log):
        # 效果已结束或角色已死亡，则返回
        if self.duration <= 0 or not owner.is_alive: return None

        # 每个回合开始时重置护盾值
        if self.skill_type == 'defense':
            self.current_turn_shield = self.modifier

        # 技能首次触发tick时运行一次（改变属性的技能）
        if self.is_first_tick:
            # 实现境界改变技能效果
            if self.skill_type in ['identity_buff', 'identity_debuff']:
                # 计算当前生命值和魂量比例
                hp_ratio = owner.hp / owner.max_hp if owner.max_hp > 0 else 0
                hunliang_ratio = owner.hunliang / owner.max_hunliang if owner.max_hunliang > 0 else 0
                levels = identity_LEVELS.get(owner.identity, [])  # 当前角色身份的等级列表
                current_level_index = levels.index(owner.level)  # 当前等级的索引
                # 等级索引+1或-1，并限制在等级列表的边界内
                target_level_index = current_level_index + 1 if self.skill_type == 'identity_buff' else current_level_index - 1
                target_level_index = max(0, min(len(levels) - 1, target_level_index))
                # 如果等级索引有变化，则更新角色的属性
                if target_level_index != current_level_index:
                    new_level = levels[target_level_index]  # 新的等级名
                    if owner.is_puppet: # 傀儡的名字格式为 "原始角色名 的召唤"
                        char_key = owner.name.split('的召唤')[0]
                        original_base_stats = Character_battle_data[char_key]  # 获取原始属性
                        new_stats = calculate_stats_by_level(original_base_stats, new_level, owner.identity)  # 计算新的属性
                        owner.max_hp, owner.base_hundu, owner.max_hunliang, owner.level = (
                            new_stats['hp']/2, new_stats['hundu']/2, new_stats['hunliang']/2, new_level)
                    else:
                        char_key = owner.name   # 角色的图片文件名
                        original_base_stats = Character_battle_data[char_key]  # 获取原始属性
                        new_stats = calculate_stats_by_level(original_base_stats, new_level, owner.identity)  # 计算新的属性
                        owner.max_hp, owner.base_hundu, owner.max_hunliang, owner.level = (
                            new_stats['hp'], new_stats['hundu'], new_stats['hunliang'], new_level)
                    owner.hp = int(owner.max_hp * hp_ratio)
                    owner.hunliang = int(owner.max_hunliang * hunliang_ratio)
                    owner.hundu = owner.base_hundu
                    combat_log.add_message([(owner.name, owner.get_color()), (" 的境界暂时变为 ", TEXT_COLOR),
                                            (new_level, IDENTITY_COLOR)])

            # 魂度增益/减益效果修改属性，当duration=1时就不再运行，因为结束后-1变成0日志显示效果消失，所以该回合不能触发效果
            if self.skill_type == 'hundu_buff' or self.skill_type == 'hundu_debuff':
                if self.duration > 0:
                    old_hundu = owner.base_hundu  # 记录目标变化前的魂度，用于后续比较和生成日志
                    new_hundu = 0  # 使用一个临时变量来计算，避免直接修改

                    if self.skill_type == 'hundu_buff':
                        new_hundu = old_hundu + self.modifier / 10  # 以施法者魂度比例增加魂度
                    elif self.skill_type == 'hundu_debuff':
                        new_hundu = old_hundu - self.modifier / 10  # 减少魂度

                    new_hundu = max(0, int(new_hundu))

                    if new_hundu != old_hundu:
                        owner.hundu = new_hundu  # 更新目标最终的魂度值
                        if new_hundu > old_hundu:
                            change_amount = int(new_hundu - old_hundu)
                            log_msg = [(owner.name, owner.get_color()), (" 的魂度提升了 ", TEXT_COLOR),
                                       (str(change_amount), HEAL_COLOR), (" 点！", TEXT_COLOR)]
                        else:
                            change_amount = old_hundu - new_hundu
                            log_msg = [(owner.name, owner.get_color()), (" 的魂度降低了 ", TEXT_COLOR),
                                       (str(change_amount), DAMAGE_COLOR), (" 点！", TEXT_COLOR)]
                        combat_log.add_message(log_msg)

        # 周期性逻辑 (在首次和后续的 tick 中都会运行)，如果不是延迟触发技能效果（即当前回合触发）
        if self.skill_type not in ['control', 'hundu_buff', 'hundu_debuff', 'identity_buff', 'identity_debuff']:
            # 伤害效果 (hp_debuff)
            if self.skill_type == 'hp_debuff' and self.modifier > 0:
                if self.caster:
                    caster_rank = IDENTITY_HIERARCHY.index(self.caster.identity)
                    owner_rank = IDENTITY_HIERARCHY.index(owner.identity)
                    # 身份碾压检查
                    if caster_rank > owner_rank:
                        damage_to_deal = owner.hp  # 身份碾压秒杀
                        log_msg = [(owner.name, owner.get_color()), (" 因 ", TEXT_COLOR), (f"[{self.name}]", SKILL_COLOR),
                                   (" 效果受到了来自 ", TEXT_COLOR), (self.caster.name, self.caster.get_color()),
                                   (" 的身份碾压，", TEXT_COLOR), ("造成 ", TEXT_COLOR), (f"{int(damage_to_deal)}", DAMAGE_COLOR),
                                   (" 点致命伤害！", TEXT_COLOR)]
                        if self.is_first_tick:
                            combat_log.add_message(log_msg)  # 只有在首次tick时显示更详细的“秒杀”日志，避免刷屏
                    elif caster_rank < owner_rank:# 身份压制无效
                        damage_to_deal = 0
                        combat_log.add_message([(owner.name, owner.get_color()), (" 因身份压制，免疫了来自 ", TEXT_COLOR),
                             (self.caster.name, self.caster.get_color()), (f" 的[{self.name}]伤害。", TEXT_COLOR)])
                    else:
                        damage_to_deal = self.modifier  # 常规伤害
                else:  # 如果没有施法者（例如环境伤害），则造成常规伤害
                    damage_to_deal = self.modifier
                # 如果伤害有效
                if damage_to_deal > 0:
                    # 造成伤害，返回实际伤害（防御抵消）和死亡
                    damage_dealt, died = owner.take_damage(damage_to_deal, combat_log)
                    combat_log.add_message([(f"{self.caster.name}", self.caster.get_color()),
                                            (" 的 ", TEXT_COLOR), (f"[{self.name}]", SKILL_COLOR),
                                            (" 对 ", TEXT_COLOR), (owner.name, owner.get_color()),
                                            (f" 造成了 ", TEXT_COLOR), (str(int(damage_dealt)), DAMAGE_COLOR),
                                            (" 点伤害。", TEXT_COLOR)])
                    if died:
                        combat_log.add_message([(owner.name, owner.get_color()), (" 被 ", TEXT_COLOR),
                                                (f"{self.caster.name}", self.caster.get_color()), (" 的 ", TEXT_COLOR ),
                                                (f"[{self.name}]", SKILL_COLOR), (" 效果击杀了！", TEXT_COLOR)])

            # 治疗效果 (hp_buff)
            elif self.skill_type == 'hp_buff' and self.modifier > 0:
                amount_healed = int(self.modifier)
                owner.heal(amount_healed)  # 治疗目标
                combat_log.add_message([(owner.name, owner.get_color()), (" 因", TEXT_COLOR), (f" [{self.name}] ", SKILL_COLOR),
                                        ("效果恢复了 ", TEXT_COLOR), (str(amount_healed), HEAL_COLOR), (" 点生命。", TEXT_COLOR)])

            # 魂量恢复效果 (hunliang_buff)
            elif self.skill_type == 'hunliang_buff' and self.modifier > 0:
                amount_restored = int(self.modifier)
                owner.restore_hunliang(amount_restored)  # 恢复目标魂量
                combat_log.add_message([(owner.name, owner.get_color()), (" 因", TEXT_COLOR), (f" [{self.name}] ", SKILL_COLOR),
                                        ("效果恢复了 ", TEXT_COLOR), (str(amount_restored), HUNLIANG_COLOR), (" 点魂量。", TEXT_COLOR)])

            # 魂量减少效果 (hunliang_debuff)
            elif self.skill_type == 'hunliang_debuff' and self.modifier > 0:
                amount_lost = int(self.modifier)
                owner.use_hunliang(amount_lost)  # 减少目标魂量
                combat_log.add_message([(owner.name, owner.get_color()), (" 因", TEXT_COLOR), (f" [{self.name}] ", SKILL_COLOR),
                                        ("效果失去了 ", TEXT_COLOR), (str(amount_lost), DAMAGE_COLOR), (" 点魂量。", TEXT_COLOR)])

        asset_to_return = None
        # 定义哪些类型的技能效果在每次触发时都应播放特效
        vfx_trigger_types = ['hp_debuff', 'hp_buff', 'hunliang_buff', 'hunliang_debuff', 'defense']
        # 普攻造成的持续1回合伤害效果不重复播放特效
        if self.name not in ["普攻", "普攻(武器)"] and self.skill_type in vfx_trigger_types and self.asset_name and self.modifier > 0:
            asset_to_return = self.asset_name

        self.duration -= 1  # 每次运行tick后持续时间减一
        # 在首次 tick 的所有逻辑都执行完毕后，将标志设为 false。
        if self.is_first_tick:
            self.is_first_tick = False

        return asset_to_return # 返回特效名称或None

    # 当效果消失时触发的逻辑
    def on_remove(self, owner, combat_log):
        if self.skill_type in ['identity_buff', 'identity_debuff']:  # 判断是否为改变境界的效果
            old_level = owner.level  # 记录旧的境界
            owner.restore_original_stats()  # 恢复角色到原始属性
            combat_log.add_message([(owner.name, owner.get_color()), (f" 从 ", TEXT_COLOR), (f"{old_level}", IDENTITY_COLOR),
                                    (f" 境界恢复为 ", TEXT_COLOR), (f"{owner.level}。", IDENTITY_COLOR)])  # 显示境界恢复信息
        elif self.skill_type in ['hundu_buff', 'hundu_debuff']:
            owner.restore_original_stats()


#  计算角色使用技能需要消耗的魂量
def calculate_skill_cost(skill, character):
    return int(character.hundu  * skill.value)  # 技能消耗等于技能比例值*魂度
