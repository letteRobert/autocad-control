# AutoCAD Control for Codex · AutoCAD 自动化技能

用 Codex 在 Windows 上读取、绘制和编辑 Autodesk AutoCAD 的 DWG 图纸。适合日常制图、界址点定位、面积查询和另存核验。常规操作通过 ActiveX 直接连接打开的 AutoCAD；可选的 AutoCAD 2024 .NET 插件提供 `CODEXRECT` 矩形参数弹窗。

A Windows Codex skill for Autodesk AutoCAD. Inspect, draw, move, and save DWG entities through Python and ActiveX (COM). An optional AutoCAD 2024 .NET plug-in adds interactive rectangle drafting with a native modal dialog.

## 能做什么

| 场景 | 支持的操作 |
| --- | --- |
| DWG 读图 | 查询图纸单位、图层、布局、文字、多段线顶点和面积，按句柄读回图元。 |
| 基础制图 | 绘制直线、圆、单行文字和闭合多段线。 |
| 测绘定位 | 区分 WCS 和当前 UCS，按已核对的顶点平移指定图元，保留图形尺寸和坐标系。 |
| 保存核验 | 保存指定图纸、另存新 DWG，重开后核对结果。 |
| 参数弹窗 | 在 `CODEXRECT` 中输入矩形基点、宽度和高度，点「绘制」出图，点「取消」不写入。 |

## 快速开始

准备 **Windows、AutoCAD、Python 3 和 pywin32**。目前在 AutoCAD 2024 x64 上完成了实机验证。

1. 克隆本仓库，或下载 ZIP，再把整个 `autocad-control` 目录放到 Codex 使用的技能目录。保留 [SKILL.md](SKILL.md)、`scripts/`、`references/`、`plugin/` 和 `assets/` 的相对位置。
2. 打开 AutoCAD 和目标 DWG。在技能目录运行以下命令，检查连接、活动图纸和坐标设置。

```powershell
python -m pip install pywin32
python scripts/autocad_control.py --progid AutoCAD.Application.24.3 check
```

例如，可以对 Codex 说：“读取当前图纸的模型空间，列出闭合多段线、顶点和面积。”支持的请求格式见 [ActiveX 使用说明](references/activex.md)。

## 可选的 .NET 绘图弹窗

普通 ActiveX 操作可以直接使用。需要矩形参数弹窗时，在 **AutoCAD 2024 x64** 中执行 `NETLOAD`，选择 [CodexAutoCAD.dll](assets/autocad2024/CodexAutoCAD.dll)，再在命令行输入 `CODEXRECT`。插件基于 .NET Framework 4.8，加载和构建步骤见 [.NET 插件说明](references/dotnet-plugin.md)。

如果 .NET 命令不可用，先确认命令已结束且没有生成对应图元。参数和坐标明确、ActiveX 能保持相同绘图约束时，可以用 ActiveX 完成绘图。用户取消时结束任务。

## 验证范围

- **ActiveX**：在 AutoCAD 2024 实测基础绘图、图层和布局查询、UCS 转换、指定顶点平移、防止改错图、另存与重开读回。
- **.NET**：`CODEXRECTCHECK` 核心控制台自检通过。桌面端实测点击「绘制」新增一个 4×3 的闭合矩形，面积为 12；再次打开后点击「取消」未新增图元。
- **待单独验证**：其他 AutoCAD 版本、其他插件或 DCL 对话框、复杂标注和打印流程。

技能通过[案例复盘说明](references/experience-index.md)积累可复用的纠错和核验方法。中望 CAD 用户可使用 [zwcad-control](https://github.com/letteRobert/zwcad-control)。
