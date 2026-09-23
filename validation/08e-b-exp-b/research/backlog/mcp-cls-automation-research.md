# Research Prompt — MCP 自动化 Fusion Character Level Styling (StyledTextCLS)

> 供高级 LLM / Fusion 专家使用。目标：找出 **无需 GUI、无需预烘焙 .setting 文件** 即可通过 Scripting API / MCP 写入 per-character size emphasis 的可行方案。

---

## 背景

我们在 **DaVinci Resolve Studio 21.1.0.14** 上验证 **Experiment B — Inline Keyword Emphasis**：

- 路由：`timeline.insert_fusion_title("Text+")` → `StyledTextCLS` modifier → `CharacterLevelStyling1`
- 文本示例：`价格直接涨了 40%`
- 目标：字符索引 **7–9**（`40%`）放大到 Size **0.189**，基线 Size **0.073**（Microsoft YaHei UI）

**GUI 已证实可行**（用户在 Fusion 检查器 → 修改器 → CharacterLevelStyling1 → 选中文本 → 大小 = 0.189）。

---

## 已验证事实

### GUI 成功后的 Fusion 图结构（gold standard）

文件：`validation/08e-b-exp-b/evidence/B00-gui-cls-working.setting`

```lua
CharacterLevelStyling1 = StyledTextCLS {
    Inputs = {
        Text = Input { Value = "价格直接涨了 40%", },
        CharacterLevelStyling = Input {
            Value = StyledText {
                Array = {
                    { 102, 7, 9, Value = 0.189 }   -- Parameter=102(Size), First=7, Last=9
                },
                Value = ""
            },
        }
    },
},
Template = TextPlus {
    Inputs = {
        StyledText = Input {
            SourceOp = "CharacterLevelStyling1",
            Source = "StyledText",
        },
        Size = Input { Value = 0.073, },
        Font = Input { Value = "Microsoft YaHei UI", },
    },
},
```

**关键：** GUI 使用 **positional tuple** `{ 102, 7, 9, Value = 0.189 }`，**不是** `{ Parameter, Index, First, Last, Value }`。

### MCP `fusion_comp.set_input` — 失败

通过 Samuel davinci-resolve-mcp **4.8.13**，以下调用均 `success: true`，但：

| 检查项 | 结果 |
|--------|------|
| `get_input(CharacterLevelStyling1, "CharacterLevelStyling")` | 始终 `""` |
| `timeline_frame` @ 86580 | **无可见放大** |
| `export_comp` | 无 `CharacterLevelStyling` Array 块 |

已尝试的 value 格式（均失败）：

```json
{"Array": [{"Parameter": 102, "Index": 0, "First": 7, "Last": 9, "Value": 0.189}]}
{"Value": {"Array": [{"1": 102, "2": 7, "3": 9, "Value": 0.189}], "Value": ""}}
{"Array": [[102, 7, 9, {"Value": 0.189}]], "Value": ""}
```

直接 `set_input(CharacterLevelStyling1, "Size", 0.189)` 可读回 0.189，但 **无 per-span 效果**（全局 Size 不等于 CLS span）。

### MCP `timeline_item_fusion.import_comp` — 成功

```json
{
  "action": "import_comp",
  "params": {
    "track_type": "video",
    "track_index": 1,
    "item_index": 1,
    "path": "<absolute-path-to-B00-gui-export-retry.setting>",
    "index": 1
  }
}
```

| 检查项 | 结果 |
|--------|------|
| `timeline_frame` @ 86580 | **40% 明显放大** |
| `export_comp`（import 后） | 含 `{ 102, 7, 9, Value = 0.189 }` |
| Deliver PNG @ MarkIn=86580 | **可见放大**，`actual_width_px=572` |

**局限：** 需要预先生成/维护 `.setting` 文件；不能动态改 span 而不重新 import。

---

## 研究问题（请逐条回答）

1. **Fusion Scripting API 中 `StyledText` / `CharacterLevelStyling` 输入的正确 Python/Lua 对象形态是什么？**
   - `Tool.SetInput("CharacterLevelStyling", ???)` 的 `???` 应如何构造？
   - positional tuple `{ 102, 7, 9, Value = 0.189 }` 在 Python bridge 里对应什么类型？（dict? list? Fusion native object?）

2. **为何 `SetInput` 返回成功但 `GetInput` 读回空字符串，且渲染无效果？**
   - 是 serialization 层丢失 Array？
   - 是否需要 `comp.CurrentTime` / 选中字符 / `RequestMake()` / `Invalidate()` 等副作用？
   - GUI 手动选中 Viewer 字符是否触发了 API 无法模拟的状态？

3. **Parameter ID 102 的权威来源？**
   - Size = 102 是否稳定跨 Text+ / StyledTextCLS？
   - 其他 emphasis（color 2401–2403, weight 109）的正确 ID 与 value 形态？

4. **是否存在替代 API？**
   - `StyledText` XML / markup 内联样式？
   - `SetAttrs` / expression / `LoadSettings` on modifier only？
   - `fusion_comp.group_settings_load` 对 TextPlus（非 GroupOperator）是否可用？

5. **MCP 层修复建议**
   - davinci-resolve-mcp 的 `set_input` 是否需对 `StyledText` 类型做 special-case 编码？
   - 建议的 JSON → Fusion bridge 转换函数伪代码？

6. **生产可行路线排序**
   - A: 修复 `set_input` 直写 Array
   - B: 运行时生成 `.setting` + `import_comp`（模板化 span/text）
   - C: 多 Text+ compose（用户不希望，但请评估）
   - D: 放弃单对象 CLS，改用其他 Resolve 原生能力

---

## 环境约束

- Resolve **Studio 21.1.0.14**（非 19.x）
- MCP：**Samuel davinci-resolve-mcp 4.8.13**（可建议 patch，但不得假设已升级）
- 连接：GUI + Local Database
- 项目：`Astra-08E-B-Subtitle-Validation`
- 时间线：`B-MCP-CLS-CLEAN`（Text+ clip 86520–86640，Deliver MarkIn=86580）
- 禁止：自定义 renderer、FFmpeg burn-in、GUI automation bot

---

## 期望交付物

1. **可运行的最小 Python/Lua 脚本**（Resolve Scripting API），能在无 GUI 操作下让 `40%` 放大可见
2. **若需 MCP 改动**：明确指出 payload 格式 + server 侧转换逻辑
3. **失败边界声明**：哪些情况下必须退回 `import_comp` 或 GUI

---

## 附件路径

| 文件 | 说明 |
|------|------|
| `validation/08e-b-exp-b/evidence/B00-gui-cls-working.setting` | GUI 金标准 |
| `validation/08e-b-exp-b/evidence/B00-gui-export-retry.setting` | MCP export 金标准 |
| `validation/08e-b-exp-b/evidence/B-MCP-CLS-CLEAN-after-import.setting` | import_comp 后 export（含 Array） |
| `validation/08e-b-exp-b/evidence/B-MCP-CLS-CLEAN-after-mcp.setting` | set_input 失败后 export（无 Array） |
| `validation/08e-b-exp-b/renders/B-MCP-import-deliver00086580.png` | Deliver 成功帧 |
| `validation/08e-b-exp-b/measurements/B-MCP-import-deliver.measurement.json` | 宽度 572px |

---

## 成功标准

在 **同一条时间线、同一 Text+ clip** 上，仅通过 Scripting API（或 MCP `set_input` 等价调用），满足：

1. `timeline_frame` 可见 `40%` 放大
2. `export_comp` 含 `{ 102, 7, 9, Value = ... }`（或等价结构）
3. Deliver @ MarkIn=86580 可见放大
4. **无需** GUI 手动选中字符
5. **无需** import 完整预烘焙 comp（允许只 import modifier 子图，若可行）
