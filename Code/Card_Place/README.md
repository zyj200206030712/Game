# Card Place（卡牌放置）——项目说明与内容扩展指南

## 一、项目是什么

Card Place 是使用 Python + Pygame 开发的单机放置式卡牌战斗游戏。玩家通过召唤角色获得卡牌，重复召唤转化为同名碎片；使用金币提升等级、使用碎片提高星级，最多选择 6 名角色布阵并挑战自动战斗关卡。


**主要玩法：**

- 角色图鉴：查看角色立绘、属性、技能，进行升级、升星与阵位配置。
- 关卡战斗：按照前排/后排阵位自动普攻、释放技能、结算战斗。
- 召唤养成：单抽 500 金币，十连 5000 金币，重复角色变成 1 个碎片。
- 挂机资源：每秒获得“当前关卡编号”数量的金币。
- 胜利奖励：600 + 当前关卡编号 × 50 金币，然后进入下一关。
- 测试模式：可单独指定双方角色、等级、星级，进行临时模拟战斗。
- 战斗演出：角色四姿势图集、近战位移、远程投射物、受击和技能特效。

角色、关卡、技能和数值主要在 `config.py` / `models.py` / `battle.py` 中维护；
界面和美术显示主要由 `main.py` / `ui.py` 维护。


## 二、项目文件分别负责什么

项目结构如下：

```
Game/
├── Code/
│   └── Card_Place/
│       ├── main.py          # 游戏入口、场景切换、升级与升星交互
│       ├── config.py        # 角色、关卡和战斗演出静态配置
│       ├── models.py        # 角色成长、存档和自动关卡
│       ├── battle.py        # 战斗行动与技能效果结算
│       ├── ui.py            # UI 绘制、人物动作和技能特效
│       ├── save_data.json   # 金币、关卡、角色和阵位存档
│       └── README.md        # 项目开发说明
├── art/                     # 新版及归档美术资源
└── picture/                 # 原始角色图片及兼容回退图片
```

五个模块的调用关系：

```text
  main.py → models.py（角色、养成与存档）
          → battle.py（战斗规则）
          → ui.py（画面绘制）
  config.py 提供各模块共用的静态配置。
```


**常见修改目标：**

- 角色数值、技能文本、关卡名单：`config.py`
- 成长公式、伤害、存档、后续关卡算法：`models.py`
- 技能选目标与作用效果：`battle.py`
- 新页面、交互、升级/升星按钮、场景流程：`main.py`
- 图鉴布局、按钮样式、图片加载、人物动作、特效：`ui.py`

注意：上述目录是当前源码按 Code/Card_Place 所设定的相对结构；`ui.py` 用所在目录的第三级父目录作为项目根目录（PROJECT_ROOT）。


## 三、如何新增角色：配置、基础属性和成长机制


### 1. 现有角色与基础属性的含义

`config.py` 中的 `HERO_CONFIG` 目前有 38 名角色。每个角色的 hp、atk、def 是生命、攻击、防御。



### 2. 实际属性成长：`models.py` / Character.scale_stat()

- `level` 和 `star` 决定最终属性,每升一级，属性在上一级基础上乘以 1.1 并四舍六入五成双取整；每升一星，属性直接翻倍。男性角色平均属性为 {"hp": 500, "atk": 50, "def": 50}，女性角色平均属性为 {"hp": 400, "atk": 40, "def": 40}，可作为设计新角色的参考。

计算顺序：先计算等级成长（每一级都 round 取整），再计算星级倍率。

`属性 = round(等级成长后的属性 × 2 ** (星级 - 1))`

等级成长：从 1 级基础值开始，每提升一级，进行一次
`value = round(value × 1.1)`
例如 1→10 级，需要连续执行 9 次，不能简单把最后结果
当作 round(基础值 × 1.1**9)，因为每一级都取整。
星级倍率：★1=1 倍、★2=2 倍、★3=4 倍、★4=8 倍、
★5=16 倍、★6=32 倍、★7=64 倍……
round()：使用 Python 默认的最近偶数舍入规则，恰好遇到 x.5 时
取相邻偶数；乘法浮点表示可能影响极少数边界值。


**示例：安迷修的基础属性（500 / 50 / 60）**

Lv.1  ★1：生命 500，攻击 50，防御 60
Lv.10 ★1：生命 1181，攻击 119，防御 143
Lv.10 ★2：生命 2362，攻击 238，防御 286
Lv.10 ★3：生命 4724，攻击 476，防御 572


**属性读取位置：**

Character.max_hp：通过 scale_stat() 计算最大生命。
Character.atk：等级星级攻击 + 战斗临时攻击增减益；最低为 0。
Character.defense：等级星级防御 + 战斗临时防御增减益；最低为 0。


### 3. 玩家如何升级、升星

升级：`main.py` 点击“升级(100金)”；金币足够就扣 100，等级加 1。
升星：消耗数量等于“当前星级”的同名碎片，然后星级加 1。
例如 ★1→★2 需要 1 碎片，★2→★3 需要 2 碎片。
碎片：重复召唤到已拥有的同名角色，duplicates 加 1。
上限：当前普通养成代码没有设置角色等级/星级上限。
测试模式的输入框则单独限制为 1～99。


### 4. 新增角色具体步骤


**第一步：将原始角色图片放入项目根目录 picture/（或准备新美术资源）。**


**第二步：在 `config.py` 的 `HERO_CONFIG` 中增加角色，角色名称必须唯一：**


```python
"示例剑士": {
    "image": "picture/示例剑士.png",  # 角色原图的相对路径
    "hp": 500,                     # 1级1星基础生命
    "atk": 60,                     # 1级1星基础攻击
    "def": 50,                     # 1级1星基础防御
    "tag": "单体输出",               # 图鉴定位文本，不影响战斗计算
    "skill": {
        "name": "斩击",              # 技能名称
        "target": "enemy_front",    # 目标规则
        "cooldown": 3,              # 冷却：按角色自身行动结算
        "desc": "对敌方前排造成150%攻击力的伤害",  # 展示文本
        "effects": [
            {"type": "damage", "multiplier": 1.5}
        ]
    }
},
```


**第三步：在 `config.py` 的 `COMBAT_PRESENTATION` 中追加同名配置：**


```python
"示例剑士": {
    "style": "melee",              # 近战 melee；远程 ranged
    "projectile": "bolt",          # 远程投射物类型，近战也须保留字段
    "facing": (1, 1, 1, 1)         # idle/prepare/release/hit 的原图朝向
},
```


**第四步：如接入 2×2 角色图集，在 `ui.py` 的 `SPRITE_NAMES` 注册唯一资源 ID：**


```python
"示例剑士": "hero_38",              # 示例：现有 ID 已用到 hero_37
```

再准备 art/cinematic/poses/hero_38.png 等素材（第七节详述）。
如暂时只有 picture/ 的原图，可以先不添加 `SPRITE_NAMES` 映射，
但仍必须添加 `COMBAT_PRESENTATION`，否则战斗显示读取配置会报错。


**第五步：用图鉴、召唤、测试战斗检查属性、动作、技能命中与显示效果。**

召唤池由 list(`HERO_CONFIG`.keys()) 自动生成，无须另行登记。
旧存档不会自动拥有新增角色，需要召唤获取或在测试模式使用。


## 四、如何新增关卡：手动配置与自动生成


### 1. 手动配置

`config.py` 的 `STAGE_CONFIG` 是字典：键是关卡编号，值是该关敌人列表。
敌人每项必须包含已存在于 `HERO_CONFIG` 中的 name，
level（角色等级）和 star（星级）可自定义，缺省时按 1 计算。

例如增加第 46 关：


```python
46: [
    {"name": "安迷修", "level": 46, "star": 6},
    {"name": "炎龙", "level": 46, "star": 6},
    {"name": "巨甲象", "level": 46, "star": 6},
],
```

把这一项放进 `STAGE_CONFIG` 字典，注意与相邻条目的逗号、括号。
现有手动关卡为第 1～45 关；当前战场按最多 6 个敌人阵位设计。
手动配置的敌人属性同样使用 Character.scale_stat() 计算。


### 2. 当前自动生成逻辑

`models.py` 的 get_stage_enemies(level) 先检查是否已手动定义该关。
如果已定义，就直接返回手动配置；否则：

M = `STAGE_CONFIG` 中目前最大的关卡编号；初始为 45。
delta = 目标关卡 - M
选取第 M 关的敌方阵容作为模板；对模板里的每名敌人：
新等级 = 模板等级 + delta
新星级 = 模板星级 + (delta // 5)

在原配置未修改时：
第 45 关：Lv.45，★5（手动）
第 46 关：Lv.46，★5（自动，复制第45关的角色名单）
第 49 关：Lv.49，★5
第 50 关：Lv.50，★6
第 55 关：Lv.55，★7

重要：如果在 `STAGE_CONFIG` 增加了第 46 关，第 47 关起的自动生成
会改为以第 46 关为模板；继续新增更高关卡时，自动逻辑同样会跟着变化。
当前规则不限制自动生成星级上限，后期敌人的属性可能迅速膨胀。


### 3. 测试关卡

主界面“测试模式”提供临时配置双方角色、等级、星级的入口。
通过 `ui.py` 的 TestPicker 编辑阵位，可以先验证难度，不必更改真实存档。
测试配置仅供本次模拟使用，不会写进正常游戏的 `save_data.json`。


## 五、如何新增或调整技能


### 1. 技能定义位置

技能写在 `config.py` 的 `HERO_CONFIG`[角色名] 内。
单技能角色使用 "skill": {...}；多技能角色使用 "skills": [{...}, ...]。
每个技能可以包含多个 effects，按列表先后顺序执行。


**主要字段：**

| 字段 | 作用 |
|---|---|
| `name` | 技能显示名称 |
| `target` | 施法目标，必须由 `battle.py` 识别 |
| `cooldown` | 释放后设置的冷却值；角色每次自身行动开始时减 1 |
| `priority` | 多技能排序优先级，越大越靠前，默认为 0 |
| `desc` | 图鉴描述，仅用于展示 |
| `effects` | 按顺序结算的技能效果列表 |

角色行动时先将所有冷却值减 1，再选择第一个冷却为 0 的技能；
没有可释放技能时，执行普通攻击。多个技能同时可用时按
Character._normalize_skills() 的优先级排序决定先释放哪一个。


### 2. 已有技能目标 target

**敌方目标：**

| `target` | 目标选择方式 |
|---|---|
| `enemy_front` | 第一名存活敌人（按敌方列表顺序） |
| `enemy_back` | 最后一名存活敌人 |
| `enemy_lowest_hp` | 当前生命百分比最低的敌人 |
| `enemy_highest_hp` | 当前生命百分比最高的敌人 |
| `enemy_highest_atk` | 当前攻击力最高的敌人 |
| `enemy_highest_def` | 当前防御最高的敌人 |
| `enemy_random` | 随机一名存活敌人 |
| `enemy_aoe` | 所有存活敌人 |

**友方及自身目标：**

| `target` | 目标选择方式 |
|---|---|
| `ally_lowest_hp` | 当前生命百分比最低的存活友军 |
| `ally_highest_atk` | 当前攻击最高的存活友军 |
| `ally_lowest_def` | 当前防御最低的存活友军 |
| `ally_random` | 随机一名存活友军 |
| `ally_aoe` | 所有存活友军 |
| `ally_dead_random` | 随机一名阵亡友军 |
| `ally_dead_aoe` | 所有阵亡友军 |
| `self` | 自身 |

已知配置兼容问题：`config.py` 内“暗魂”的技能 target 当前写成
"enemy_highest_def"，但 `battle.py` 处理的键是 "enemy_higest_def"。
因此这个技能目前不会按“最高防御”分支选目标，
而可能触发“对敌类技能未匹配则默认敌方前排”的回退逻辑。
如果后续修复，应同步修改配置和目标判断，避免两边拼写不一致。


### 3. 已有技能效果 effects（共 8 类）

| 效果 `type` | 结算说明 |
|---|---|
| `damage` | 按 `round(施法者当前攻击 × multiplier)` 得到攻击值；实际伤害为 `max(0, 攻击值 - 目标当前防御)` |
| `lifesteal` | 按同一技能对当前目标最近一次实际伤害 × `multiplier` 回血，不超过施法者缺失生命 |
| `heal` | `round(multiplier × (施法者最大生命 + 目标最大生命) / 2)`，不超过目标缺失生命 |
| `resurrect` | 目标已阵亡才生效；先重置其战斗态，再按治疗同类公式计算复活生命，限制在 1 到最大生命之间 |
| `buff` | 对 `atk` / `def` 加成：`round(multiplier × (施法者当前属性 + 目标当前属性) / 2)` |
| `debuff` | 数值计算同 `buff`，从目标战斗加成中扣除，最终实际属性最低为 0 |
| `control` | `duration` 指定控制次数；目标处于免控状态则控制失败 |
| `immune` | `duration` 指定免控次数，并立即解除已有控制 |

> **注意：**`buff` / `debuff` 均以释放时的当前属性计算（包含已有加减益），所以自我强化可复利叠加；目前没有常规的 Buff 过期倒计时。战斗开始或复活时会清除临时攻防加成与控制、免控状态。


### 4. 多效果技能示例


```python
"skill": {
    "name": "破甲斩",
    "target": "enemy_front",
    "cooldown": 4,
    "desc": "对前排造成120%攻击伤害，并降低其20%防御",
    "effects": [
        {"type": "damage", "multiplier": 1.2},
        {"type": "debuff", "stat": "def", "multiplier": 0.2}
    ]
}
```


### 5. 新增全新的技能类型

不要只给 effects 填一个新的 "type" 字符串，否则目前不会被结算。
应同时：
- ① 在 `config.py` 角色技能中定义 type 及参数。
- ② 在 `battle.py`/process_turn() 的效果循环中添加对应的处理分支。
- ③ 如涉及持续状态，在 `models.py`/Character 中定义状态，且在
reset_battle_state()、reset_on_resurrect() 等重置逻辑中维护。
- ④ 在 `ui.py`/draw_effects() 为新效果添加必要的演出（可选但推荐）。
- ⑤ 检查伤害、治疗、战报、浮动文字与冷却顺序是否一致。


### 6. 普攻与技能的动作关系

普攻和技能是不同结算行为，但通常共用角色图集中的 prepare/release。
近战对敌行动会前进接近目标、命中后返回；远程对敌行动原地施法
并通过 projectile 类型显示飞行特效；对自身或友军的技能按 support
辅助演出处理，通常不冲向敌方。
默认四姿势：idle（待机）、prepare（蓄力）、release（出招）、hit（受击）。
人物动作来自角色图集；技能光环、箭矢、火焰、治疗符号等主要由
`ui.py` 中的绘制逻辑生成，不能把技能特效误认为来自第五张动作图片。


## 六、UI 页面与交互应该如何修改

`main.py`：负责何时显示页面、创建按钮和响应鼠标/键盘操作。
`ui.py`：负责页面具体绘制、人物/卡牌/按钮样式、图片与动作渲染。


**主要页面：**

| 场景 | 功能 |
|---|---|
| `LEVEL` | 关卡、双方阵容、战斗入口和测试模式 |
| `HERO` | 角色图鉴、立绘、属性、技能、升级升星和上阵 |
| `GACHA` | 单抽、十连展示 |
| `BATTLE` | 战场、血条、动作和战报 |
| `SETTLEMENT` | 战斗结算与奖励 |

**关键 UI 函数及对象：**

| `ui.py` 函数或类 | 作用 |
|---|---|
| `draw_home()` | 关卡与布阵卡片 |
| `draw_hero_page()` | 图鉴、当前属性、技能描述 |
| `draw_summon()` | 抽卡展示 |
| `draw_battlefield()` | 战场人物、血条、受击、技能名称 |
| `draw_effects()` | 技能特效 |
| `ArtButton` | 美术按钮 |
| `DetailViewer` | 高清立绘、历史战报窗口 |
| `TestPicker` | 测试模式选人与编辑等级星级 |

**新增按钮通常需要四步：**

- ① 在 `main.py`/main() 的初始化区创建按钮。
- ② 在目标场景绘制时调用按钮的 draw()。
- ③ 在同一场景事件处理中通过 is_clicked() 判定点击。
- ④ 点击后修改 GameData 状态或调用对应方法，并检查模态窗口
是否需要拦截底层点击。


**新增页面通常需要：**定义唯一场景名称 → 增加入口按钮 → 在 `main.py` 的 `current_scene` 分支中调用对应 `ui.py` 绘制逻辑 → 补充返回导航和交互。

若要显示“1级1星基础属性”，可直接读取 selected.base_hp / base_atk /
base_def；而 selected.max_hp / atk / defense 显示的是当前属性。
切勿把战斗过程中的 battle_atk_bonus 当作永久属性写进角色配置。

当前源码的基础布局采用 WIDTH=1280、HEIGHT=800（`config.py`），
许多组件坐标是按这一分辨率编写。更改布局大小时需同时检查
`main.py` 的按钮位置、`ui.py` 的矩形坐标、背景图片缩放和鼠标命中区域。


## 七、游戏需要的图片资源在哪里

注意：以下路径从项目根目录 Game/ 起算，不是以 Code/Card_Place/ 为根目录。


**1. picture/角色图片.png**
- `config.py` 的 `HERO_CONFIG`[角色名]["image"] 中配置的原始角色图片。
- 若对应的新版动作图/归档图不存在，头像和战场可能回退到这些图片。


**2. art/cinematic/poses/hero_00.png ～ hero_37.png**
- 38 名现有角色的新动作 2×2 图集，与 `ui.py`/SPRITE_NAMES 一一对应。
- 四格位置固定：左上 idle，右上 prepare，左下 release，右下 hit。
- 一张图可提供该角色的四种基础姿势；并非“普攻一套、技能一套”。
- 图片需考虑透明背景、各姿势的大小、角色朝向和一致性。


**3. art/archive/faithful/hero_00.png ～ hero_37.png**
- 新动作图缺失时的归档四姿势图集回退来源。
- 新旧素材按角色资源 ID 查找；不建议随意重命名。


**4. art/cinematic/portraits/hero_00.png ～ hero_37.png**
- 独立高清立绘，主要用于大图查看、卡牌/角色展示。
- 缺失时会尝试从对应动作图集中提取待机姿势。


**5. art/illustrated/arena.png**
- 战场背景；在 `ui.py`/arena_background() 中加载。


**6. art/cinematic/ui/home.png**
- 关卡界面背景。
art/cinematic/ui/hero.png
- 角色图鉴背景。
art/cinematic/ui/summon.png
- 召唤界面背景。
art/cinematic/ui/widgets.png
- 2×2 美术控件图集（包括按钮及召唤卡背）。
art/cinematic/ui/icons.png
- 导航图标图集（战斗、角色、召唤等）。


**资源映射与使用函数：**

`ui.py`/SPRITE_NAMES          中文角色名 → hero_XX 资源 ID。
`ui.py`/load_image()          根据路径读取图片并缓存。
`ui.py`/load_portrait()       加载角色缩略立绘。
`ui.py`/display_art()         优先高清 portrait，缺失则使用动作图/原图。
`ui.py`/atlas_frame()         从动作 2×2 图集中裁切单个姿势。
`ui.py`/battle_sprite()       缩放、翻转并返回战场角色姿势。
`config.py`/COMBAT_PRESENTATION
style="melee" / "ranged" 决定对敌行动采用近战位移还是远程演出；
projectile 可用 bolt、blade、arrow、wave、fire；
facing 为四种姿势的原始左右朝向。
`ui.py`/CINEMATIC_FACING      对已接入的新图集进行额外朝向校准。

新增角色图片建议：
先确保 picture/ 原图可加载；如需完整人物动作，分配唯一 hero_XX；
添加 poses 和 portraits 后检查四格位置、透明度、出招方向及受击帧。
新增 UI 美术图不应只加入文件夹，还需要在 `ui.py` 相应绘制函数中加载。


## 八、存档与修改后检查

存档路径：Code/Card_Place/save_data.json
存档字段：gold（金币）、level（关卡编号）、heroes（角色列表）。
角色记录包含 name、level、star、duplicates、pos（阵位，-1 未上阵）。
当前 `main.py` 通过“进度保存”按钮调用 GameData.save_game()；
GameData.load_game() 在正常启动时读取。测试模式使用独立的 GameData。


**建议修改检查顺序：**

- ① 保留源码和存档备份，在副本上修改，勿直接覆盖正常版本。
- ② 检查 `config.py` 语法、`HERO_CONFIG` 名称、技能 target 拼写。
- ③ 检查新增角色 `COMBAT_PRESENTATION` 与美术资源映射。
- ④ 使用 1级1星 / 高等级高星级验证数值计算。
- ⑤ 验证伤害、治疗、控制、强化、复活是否按预期结算。
- ⑥ 验证手动关卡和超出最大关卡后的自动生成逻辑。
- ⑦ 进入战斗与角色图鉴，检查动画、文本换行、按钮命中区域。
- ⑧ 手动存档、重启并检查等级/星级/阵位能否正常恢复。


## 附录：38 名现有角色的基础属性（均为 1 级、1 星）


