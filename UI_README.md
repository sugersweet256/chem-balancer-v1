# ChemLab UI（新增文件，不改动现有核心）

这组文件只负责界面，配平/解析仍调用现有的：

- `src/parser.py`
- `src/balancer.py`

没有改动任何已经纳入版本控制的文件；可以用：

```powershell
git status --short
git diff --stat
```

确认核心文件没有 diff。

## 运行

```bash
python -m pip install -r requirements.txt
python main.py
```

Windows 可以双击 `run.bat`。

## 界面

### 配平器

- Qt Designer 源文件：`src/ui/main_window.ui`
- 控制器：`src/ui/main_window.py`
- 样式：`src/ui/styles.qss`
- 通过 `src/ui/legacy_adapter.py` 调用原核心

主界面已去掉右侧“相关工具”栏，保留输入、示例、配平结果、原子守恒和求解过程。

### 元素周期表

- 入口：顶部导航“元素周期表”
- 118 种元素，按标准长式排列
- 支持按中文名、英文名、元素符号、原子序数搜索
- 点击元素显示原子量、周期、族、分区、质子数、电子数和类别说明
- 数据在 `src/ui/periodic_data.py`，不依赖核心代码

## 预览

- `preview.png`
- `preview-periodic.png`

## Qt Designer

双击 `open_in_designer.bat`，或者运行：

```bash
pyside6-designer src/ui/main_window.ui
```

程序运行时直接加载 `.ui`，不需要先执行 `pyside6-uic`。Qt Designer 不会自动加载外部 QSS，完整配色请运行程序查看。

## 当前核心能力边界

以下功能**不是 UI 能单方面保证**的，需要核心代码或接口配合：

### 1. 多组配平解

现有 `balancer()` 在矩阵有多组解时会调用 `valence_balance()` 尝试用化合价升降定解：

- 能定解时：正常返回。
- 定不下来时：抛出“该方程式有多组配平解，化合价无法唯一确定……”错误。

例如：

```text
C + O2 -> CO + CO2
```

当前核心会报错，UI 只能把错误展示出来，不能自行选择一组系数。如果希望 UI 在这种情况下给出“最简整数解”或让用户选择，需要核心提供明确的策略或接口。

### 2. 旧式电荷写法有歧义

现有 `parser.py` 对下列写法存在歧义：

```text
SO42-     # 可能被当成 SO42 的 -1 价，而不是 SO4^2-
```

UI 推荐并提示使用：

```text
SO4^2-
```

如果希望 UI 自动纠正所有旧式多原子离子，需要核心提供明确的离子表，或者在 UI 里硬编码一份映射表——后者会隐藏核心的真实行为，所以这次没有做。

### 3. 核心没有返回结构化结果

现有 `balancer()` 只返回方程式字符串，不直接返回：

- 每个物质的系数
- 每种元素的左右原子数
- 电荷守恒数据
- 求解步骤

UI 适配层目前从 `result_print()` 的字符串格式反推系数，再自己计算原子守恒和步骤。这不影响当前使用，但如果核心修改了 `result_print()` 的格式，适配层也要同步调整。

更稳妥的长期方案是让核心增加一个返回结构化数据的函数，例如：

```python
balance_detailed(equation) -> {
    "coefficients": [...],
    "reactants": ...,
    "products": ...,
    "atom_totals": ...,
    "charge_totals": ...,
}
```

### 4. 能量变化模块尚未接入主 UI

核心新增了：

- `src/energe_change_pic.py`
- `src/substances_energy.py`

它们可以计算反应热并绘制能量变化图。但上一版 UI 并没有这块内容，所以本次只恢复配平器和元素周期表，没有把能量图放进主界面。

这部分**可以实现**，不算核心缺陷；如果希望增加“反应热 / 能量变化图”卡片，可以直接用现有的 `energy_change_canvas()`。

### 5. 电子/半反应

现有解析器面向普通化学式，未提供电子 `e^-` 或半反应法的专门解析。若 UI 要支持半反应配平，需要核心增加电子和半反应相关接口。

## 文件清单

```text
main.py
run.bat
open_in_designer.bat
UI_README.md
assets/icons/
src/ui/__init__.py
src/ui/main_window.ui
src/ui/main_window.py
src/ui/legacy_adapter.py
src/ui/render.py
src/ui/styles.qss
src/ui/periodic_data.py
src/ui/periodic_window.py
src/ui/periodic.qss
tools/screenshot.py
preview.png
preview-periodic.png
```
