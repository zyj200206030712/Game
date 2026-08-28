# Card Place（卡牌放置）运行与开发教程

Card Place 是一款使用 Python 和 Pygame 开发的放置卡牌游戏。玩家可以召唤并培养角色、配置六人阵容、挑战关卡，并观看角色按照阵位和技能冷却自动战斗。

本文档面向第一次运行或修改本项目的开发者，主要说明环境安装、游戏启动方式、代码模块分工，以及新增角色、关卡、技能和 UI 的具体位置。

## 1. 运行环境

### 1.1 推荐环境

| 项目 | 推荐配置 |
| --- | --- |
| 操作系统 | Windows 10 / Windows 11 |
| Python | Python 3.10～3.12 |
| IDE | PyCharm（也可以使用 VS Code 或命令行） |
| 第三方包 | Pygame |

项目除 Pygame 外只使用了 Python 标准库，例如 `json`、`math`、`pathlib`、`random` 和 `sys`。

角色图片统一存放在项目根目录的 `picture` 文件夹中。不要只复制或移动 `Code/Card_Place` 文件夹，否则游戏可能找不到图片资源。

### 1.2 检查 Python

打开 PowerShell 或 PyCharm Terminal，执行：

```powershell
python --version
```

如果能够显示 Python 版本，说明 Python 已加入系统环境变量。若提示找不到 `python`，需要重新安装 Python，并在安装时勾选 **Add Python to PATH**。

### 1.3 创建虚拟环境（推荐）

在项目根目录，也就是包含 `Code`、`picture` 等文件夹的 `Game` 目录中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

激活成功后，终端命令行前通常会出现 `(.venv)`。

如果 PowerShell 禁止执行激活脚本，也可以不手动激活，直接使用：

```powershell
.\.venv\Scripts\python.exe -m pip install pygame
.\.venv\Scripts\python.exe Code\Card_Place\main.py
```

### 1.4 安装 Pygame

```powershell
python -m pip install pygame
```

安装后执行下面的命令检查版本：

```powershell
python -c "import pygame; print(pygame.version.ver)"
```

能够输出 Pygame 版本号即表示安装成功。使用 `python -m pip` 可以避免把 Pygame 安装到另一个 Python 解释器中。

## 2. 启动游戏

### 2.1 命令行启动

先进入项目根目录 `Game`，再运行游戏入口：

```powershell
python Code\Card_Place\main.py
```

`Code/Card_Place/main.py` 是游戏唯一入口文件，其中的 `main()` 函数负责创建窗口、初始化游戏数据并启动每秒 60 帧的主循环。

虽然资源加载代码能够从项目位置寻找图片，但仍建议始终从项目根目录启动，便于保持统一的运行方式。

### 2.2 使用 PyCharm 启动

1. 使用 PyCharm 打开整个 `Game` 项目，不要只打开 `Card_Place` 子目录。
2. 在 **Settings → Project → Python Interpreter** 中选择安装了 Pygame 的解释器。
3. 打开 `Code/Card_Place/main.py`，右键选择 **Run 'main'**。
4. 如果启动配置不正确，打开 **Run → Edit Configurations**，设置：
   - **Script path**：`$PROJECT_DIR$/Code/Card_Place/main.py`
   - **Working directory**：`$PROJECT_DIR$`
   - **Python interpreter**：安装了 Pygame 的项目解释器

### 2.3 基本操作

游戏主要使用鼠标操作：

- **战斗**：查看双方阵容并开始当前关卡。
- **角色**：查看已拥有角色，进行升级、升星、上阵和下阵。
- **召唤**：消耗金币进行单次召唤或十连召唤；重复角色会转化为碎片。
- **进度保存**：将金币、关卡、角色养成和阵位写入本地存档。
- **暂停 / 倍速 / 撤退**：在战斗过程中控制自动战斗。
- **鼠标滚轮**：在战斗和结算页面滚动查看战斗日志。

### 2.4 存档位置与重置进度

存档文件位于：

```text
Code/Card_Place/save_data.json
```

游戏启动时会自动读取该文件；点击右上角的“进度保存”按钮时会覆盖保存当前进度。

如需重新开始，先退出游戏并备份存档，然后删除原存档：

```powershell
Copy-Item Code\Card_Place\save_data.json Code\Card_Place\save_data.backup.json
Remove-Item Code\Card_Place\save_data.json
```

再次启动后，游戏会发放初始金币和第一个角色。需要持久化新进度时，请再点击一次“进度保存”。

## 3. 项目结构与模块职责

```text
Game/
├── Code/
│   └── Card_Place/
│       ├── main.py           # 游戏入口、主循环、事件和场景 UI
│       ├── config.py         # 窗口、颜色、角色、技能和关卡配置
│       ├── models.py         # 角色模型、成长、阵容和存档
│       ├── battle.py         # 回合调度、目标选择和技能结算
│       ├── ui.py             # 通用 UI 控件、文字、血条和图片缓存
│       ├── save_data.json    # 本地游戏进度
│       └── README.md         # 本教程
└── picture/                  # 角色图片资源
```

| 文件 | 主要职责 | 常见修改场景 |
| --- | --- | --- |
| `main.py` | 初始化 Pygame、监听鼠标事件、切换场景、绘制页面、处理召唤与结算 | 新增按钮、页面或交互流程 |
| `config.py` | 定义分辨率、颜色、`HERO_CONFIG` 和 `STAGE_CONFIG` | 新增角色、技能、关卡或修改数值 |
| `models.py` | `Character` 和 `GameData` 数据模型、属性成长、阵容及 JSON 存档 | 修改成长公式、挂机收益或存档字段 |
| `battle.py` | 角色行动顺序、技能选择、目标筛选和效果结算 | 新增目标规则、技能效果或战斗机制 |
| `ui.py` | 按钮、文字换行、血条、浮动文字、标签和图片缓存 | 新增可复用 UI 控件或调整通用样式 |
| `save_data.json` | 保存金币、关卡、角色等级、星级、碎片和阵位 | 调试存档或重置进度 |

当前场景名称定义在 `main.py` 的逻辑中：

- `LEVEL`：关卡及双方阵容页面。
- `HERO`：角色查看与养成页面。
- `GACHA`：召唤页面。
- `BATTLE`：自动战斗页面。
- `SETTLEMENT`：战斗结算页面。

## 4. 功能修改指南

### 4.1 修改窗口大小和颜色

打开 `Code/Card_Place/config.py` 顶部：

```python
WIDTH, HEIGHT = 1280, 800
WHITE, BLACK, BG_COLOR = (255, 255, 255), (30, 30, 30), (245, 246, 250)
```

- 修改 `WIDTH`、`HEIGHT` 可以改变窗口分辨率。
- 修改颜色元组可以调整全局主题。
- `main.py` 中部分 UI 坐标按照当前 1280×800 布局编写，大幅修改分辨率后需要同步检查按钮和卡牌位置。

### 4.2 新增角色和技能

角色配置位于 `Code/Card_Place/config.py` 的 `HERO_CONFIG` 字典。召唤池会通过 `list(HERO_CONFIG.keys())` 自动读取所有角色，因此新增角色后不需要再手动注册召唤池。

首先将角色图片放入项目根目录的 `picture` 文件夹，然后在 `HERO_CONFIG` 中增加配置。下面的模板可以直接复制：

```python
"示例角色": {
    "image": "picture/示例角色.png",
    "hp": 500,
    "atk": 80,
    "def": 50,
    "tag": "单体输出",
    "skills": [
        {
            "name": "破空斩",
            "target": "enemy_front",
            "cooldown": 3,
            "priority": 10,
            "desc": "对敌方前排造成150%攻击力的伤害",
            "effects": [
                {"type": "damage", "multiplier": 1.5}
            ]
        }
    ]
},
```

字段说明：

| 字段 | 作用 |
| --- | --- |
| `image` | 图片路径，以项目根目录为起点，推荐使用 PNG |
| `hp` | 角色 1 级 1 星的基础生命值 |
| `atk` | 角色 1 级 1 星的基础攻击力 |
| `def` | 角色 1 级 1 星的基础防御力 |
| `tag` | 显示在角色卡片上的定位文字，不直接参与结算 |
| `skills` | 技能列表；只有一个技能时也可以使用原项目中的 `skill` 字段 |
| `name` | 技能显示名称 |
| `target` | 目标选择规则，必须与 `battle.py` 中实现的名称一致 |
| `cooldown` | 技能释放后的冷却行动轮数 |
| `priority` | 多个技能同时可用时的释放优先级，数值越大越优先；省略时为 0 |
| `desc` | 角色页面显示的技能说明，不参与实际计算 |
| `effects` | 按顺序执行的效果列表 |

一个技能可以组合多个效果。例如先造成伤害，再根据本次实际伤害吸血：

```python
"effects": [
    {"type": "damage", "multiplier": 1.2},
    {"type": "lifesteal", "multiplier": 0.5}
]
```

`lifesteal` 使用同一次技能中最近一次 `damage` 的实际伤害进行计算，因此吸血效果应放在伤害效果之后。

新增角色后可以通过召唤获得。如果希望直接测试角色，可以临时修改存档，但必须保证角色 `name` 与 `HERO_CONFIG` 的键完全一致。

### 4.3 新增关卡

关卡阵容位于 `Code/Card_Place/config.py` 的 `STAGE_CONFIG` 字典：

```python
STAGE_CONFIG = {
    1: [
        {"name": "安迷修", "level": 1, "star": 1}
    ],
}
```

新增第 46 关的示例：

```python
46: [
    {"name": "示例角色", "level": 46, "star": 6},
    {"name": "帝皇", "level": 46, "star": 6}
],
```

注意事项：

- `name` 必须已经存在于 `HERO_CONFIG` 中。
- 单个关卡建议不超过 6 名敌人，否则当前战斗 UI 没有额外阵位。
- `level` 和 `star` 决定敌人的最终属性。
- 关卡编号是字典的键，不要重复。

未命中 `STAGE_CONFIG` 的更高关卡由 `Code/Card_Place/models.py` 中的 `get_stage_enemies(level)` 生成：它会复用当前最大配置关卡的阵容，每超过 1 关增加 1 级，每超过 5 关再增加 1 星。因此既可以手工配置固定关卡，也可以依靠该逻辑生成无限后续关卡。

### 4.4 使用或新增技能目标规则

目标规则写在技能的 `target` 字段中，并由 `Code/Card_Place/battle.py` 的 `process_turn()` 负责解释。

现有敌方目标：

| `target` | 选择方式 |
| --- | --- |
| `enemy_front` | 第一名存活敌人 |
| `enemy_back` | 最后一名存活敌人 |
| `enemy_lowest_hp` | 当前生命比例最低的敌人 |
| `enemy_highest_hp` | 当前生命比例最高的敌人 |
| `enemy_highest_atk` | 攻击力最高的敌人 |
| `enemy_higest_def` | 防御力最高的敌人 |
| `enemy_random` | 随机一名存活敌人 |
| `enemy_aoe` | 全体存活敌人 |

> 注意：当前代码中的“敌方最高防御”键确实拼写为 `enemy_higest_def`，少了一个 `h`。配置必须沿用这个拼写，否则不会进入对应分支。

现有友方及自身目标：

| `target` | 选择方式 |
| --- | --- |
| `ally_lowest_hp` | 当前生命比例最低的存活友军 |
| `ally_highest_atk` | 攻击力最高的存活友军 |
| `ally_lowest_def` | 防御力最低的存活友军 |
| `ally_random` | 随机一名存活友军 |
| `ally_aoe` | 全体存活友军 |
| `ally_dead_random` | 随机一名阵亡友军 |
| `ally_dead_aoe` | 全部阵亡友军 |
| `self` | 施法者自己 |

如果需要新增“选择防御最低的敌人”，修改步骤如下：

1. 在角色技能配置中使用新的目标名，例如 `enemy_lowest_def`。
2. 打开 `battle.py`，在 `process_turn()` 的 `skill_target` 判断链中加入目标筛选。
3. 保证返回值始终是角色列表，即使只有一个目标也要使用 `[角色]`。

示例实现：

```python
elif skill_target == "enemy_lowest_def" and enemy_pool:
    real_targets = [min(enemy_pool, key=lambda x: x.defense)]
```

建议把新分支放在其他 `enemy_*` 分支附近。对敌目标拼写错误时，现有容错逻辑会退回攻击敌方前排，因此测试时应通过战斗日志确认目标选择正确，而不能只看技能是否成功释放。

### 4.5 使用或新增技能效果类型

技能效果由 `effects` 列表描述，在 `battle.py` 的 `process_turn()` 中按照列表顺序结算。

| `type` | 常用字段 | 作用 |
| --- | --- | --- |
| `damage` | `multiplier` | 根据施法者攻击力造成伤害 |
| `lifesteal` | `multiplier` | 根据本技能最近一次实际伤害回复生命 |
| `heal` | `multiplier` | 回复目标生命 |
| `resurrect` | `multiplier` | 复活阵亡友军并重置其战斗状态 |
| `buff` | `stat`、`multiplier` | 提高目标的攻击或防御 |
| `debuff` | `stat`、`multiplier` | 降低目标的攻击或防御 |
| `control` | `duration` | 使目标若干回合无法行动 |
| `immune` | `duration` | 解除控制并获得若干回合免控 |

`buff` 和 `debuff` 的 `stat` 可以写成 `"atk"`、`"def"` 或 `"atk, def"`。

如果新增一种效果，需要同时修改配置和战斗执行逻辑：

1. 在角色技能的 `effects` 中设计新的 `type` 和必要参数。
2. 在 `battle.py` 的 `for effect in skill.get("effects", [])` 循环内增加新的 `elif e_type == "..."` 分支。
3. 如果该效果需要持续状态，在 `models.py` 的 `Character` 中增加状态字段，并在 `reset_battle_state()` 和 `reset_on_resurrect()` 中重置。
4. 在回合开始、行动时或回合结束的正确位置更新持续时间。
5. 同步补充战斗日志和 `FloatingText`，让玩家能观察到效果。

以“护盾”为例，不能只在配置中写 `{"type": "shield"}`；还需要为 `Character` 增加护盾值、在伤害结算时优先扣除护盾，并明确开战和复活时如何重置。

### 4.6 修改或新增 UI

UI 分为“通用控件”和“具体页面”两部分：

- `Code/Card_Place/ui.py`：适合放多个页面都能复用的控件和绘制函数，例如 `Button`、`draw_text()`、`draw_hp_bar()`、`FloatingText`。
- `Code/Card_Place/main.py`：负责按钮实例、页面布局、鼠标点击和场景切换。

在已有页面新增按钮时，按照下面的顺序修改：

1. 在 `main()` 开头、现有按钮初始化区域创建 `Button`。
2. 在对应场景分支中调用 `button.draw(screen, mouse_pos)`。
3. 在该场景的点击处理内同时判断 `clicked` 和 `button.is_clicked(mouse_pos)`。
4. 在点击分支中修改 `GameData` 或调用对应功能。

示例：

```python
# 1. 初始化按钮
btn_test = Button(100, 100, 160, 50, "测试按钮", BLUE, WHITE)

# 2. 在目标场景中绘制
btn_test.draw(screen, mouse_pos)

# 3. 处理点击
if clicked and btn_test.is_clicked(mouse_pos):
    game.sys_message = "测试按钮已点击"
```

新增完整场景时，按照下面的顺序修改：

1. 为新场景确定唯一字符串，例如 `SETTINGS`。
2. 在主循环的场景判断链中增加 `elif game.current_scene == "SETTINGS":`，完成该页面的绘制和事件处理。
3. 增加进入该场景的按钮，并在点击时执行 `game.current_scene = "SETTINGS"`。
4. 增加返回按钮，确保能够回到 `LEVEL` 或其他已有场景。
5. 判断底部导航栏是否应该在新场景显示；当前导航栏只在 `BATTLE` 和 `SETTLEMENT` 之外显示。

如果只是修改字体、按钮样式、血条或图片缩放，应优先修改 `ui.py`，避免在每个场景重复绘制代码。

### 4.7 修改角色成长、伤害和挂机收益

主要数值入口位于 `Code/Card_Place/models.py`：

- `Character.scale_stat()`：根据等级和星级计算生命、攻击和防御。
- `Character.max_hp`、`Character.atk`、`Character.defense`：返回角色实时属性。
- `Character.take_damage()`：使用攻击力减防御力计算实际伤害。
- `GameData.get_idle_rate()`：计算每秒挂机金币收益。
- `GameData.advance_level()`：胜利后的关卡推进逻辑。

修改公式后，需要同时测试低等级、高等级、高星级、零伤害和临时 Buff/Debuff 场景，避免数值过快膨胀或出现负数。

### 4.8 修改存档字段

存档逻辑位于 `Code/Card_Place/models.py`：

- `GameData.save_game()`：将运行时数据转换成字典并写入 JSON。
- `GameData.load_game()`：读取 JSON 并恢复角色、养成和阵位。

新增字段时必须同时修改保存和读取。例如增加钻石：

```python
# GameData.__init__ 中初始化
self.diamond = 0

# save_game() 的 data 中写入
"diamond": self.diamond

# load_game() 中读取，并为旧存档提供默认值
self.diamond = data.get("diamond", 0)
```

读取新字段时应使用 `data.get("字段", 默认值)`，这样旧存档中没有该字段也能继续运行。修改存档结构前建议备份 `save_data.json`。

## 5. 常见问题

### 5.1 `ModuleNotFoundError: No module named 'pygame'`

原因通常是 Pygame 没有安装，或者安装 Pygame 和运行游戏使用了不同的 Python 解释器。

```powershell
python -m pip install pygame
python -c "import sys, pygame; print(sys.executable); print(pygame.version.ver)"
```

在 PyCharm 中检查 **Python Interpreter** 是否与上面输出的解释器一致。

### 5.2 角色图片不显示，只出现灰色占位图

依次检查：

1. 是否打开并保留了完整的 `Game` 项目结构。
2. 图片是否位于根目录的 `picture` 文件夹。
3. `HERO_CONFIG` 中的 `image` 路径、中文文件名和扩展名是否完全正确。
4. 是否从项目根目录运行 `python Code\Card_Place\main.py`。

图片加载失败时，`ui.py` 的 `load_image()` 会生成灰色占位图，而不是直接终止游戏。

### 5.3 中文显示异常或字体不正确

`ui.py` 当前通过 `pygame.font.SysFont("SimHei", ...)` 使用黑体。如果系统没有该字体，可以安装黑体，或者把字体名修改为系统已有的中文字体，例如 `Microsoft YaHei`。

修改后重新启动游戏；字体在程序启动时初始化，运行过程中修改不会自动刷新。

### 5.4 显示“读取异常，开启新对局”

通常表示 `save_data.json` 不是合法 JSON、字段类型被手工改错，或者角色名称与配置不一致。

处理方式：

1. 退出游戏。
2. 备份当前 `save_data.json`。
3. 使用编辑器检查 JSON 是否缺少逗号、引号或括号。
4. 无法修复时删除存档，让游戏重新创建初始进度。

### 5.5 修改角色或关卡后没有看到变化

- 新增角色不会自动加入已有账号，需要通过召唤获得或重新开始存档。
- 修改角色名称后，旧存档仍保存原名称，建议同步迁移存档或重新开始。
- 修改当前关卡之后，需要退出正在进行的战斗并重新进入关卡。
- Python 文件修改后必须重新启动程序。
- 如果 PyCharm 运行了其他同名文件，请再次检查启动配置的 Script path。

### 5.6 修改 `config.py` 后出现 `SyntaxError`

角色和关卡使用嵌套字典与列表，最常见的问题是漏写逗号、引号或右括号。可以在项目根目录执行语法检查：

```powershell
python -m py_compile Code\Card_Place\config.py
```

命令没有输出表示语法检查通过；如有错误，会显示具体文件和行号。

## 6. 修改后的检查清单

每次扩展功能后，建议依次确认：

- `config.py` 能通过 `py_compile` 语法检查。
- 新角色图片能够正常加载，名称与配置键一致。
- 新关卡的所有敌人都存在于 `HERO_CONFIG`。
- 新目标规则能够选中预期角色。
- 新技能效果能够正确处理死亡目标、空目标和多目标。
- Buff、控制等持续状态能在新战斗和复活时正确重置。
- 战斗日志、浮动文字和结算统计与实际数值一致。
- 保存并重启游戏后，金币、关卡、角色和阵位能够恢复。

完成以上检查后，再保留或提交新的 `save_data.json`，避免把调试进度误当成默认存档。
