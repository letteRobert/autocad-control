---
name: autocad-control
description: Operate Autodesk AutoCAD on Windows to inspect, draw, move, and save DWG entities with ActiveX; use the optional AutoCAD 2024 .NET plug-in for interactive rectangle drawing. 适用于 AutoCAD 绘图、改图、读图、定位、另存与矩形参数弹窗。中望 CAD 使用 zwcad-control；整图重建优先选相应重绘技能。
---

# AutoCAD 操作

通过 AutoCAD 自带的 Windows ActiveX 接口操作当前图纸。预置脚本需要 Python 3 和 `pywin32`，连接已运行的 AutoCAD，不自动启动、切换或关闭文档。原生命令的自动化以实际界面、版本和提示为准。

## 连接与操作

1. 在技能目录运行 `python scripts/autocad_control.py check`。核对图名、完整路径、AutoCAD 版本、模型/布局、单位及当前 UCS。多窗口时与用户目标交叉核实。连接不可用时确认图纸已打开、进程与权限相容；已有实例未注册时可切换焦点后重试只读连接。
2. 读 [请求格式与操作方式](references/activex.md)。先查当前图纸中的顶层图元、图层和空间，再按真实句柄操作。修改已有 DWG 使用绝对路径指定图纸；未保存的图按 `check` 返回的准确图名指定。
3. 通过几何属性核对操作结果。改图前定位锚点、记录原坐标与关联尺寸；改图后核对同一对象的坐标、面积或边长。中途失败先检查图纸的实际状态及受影响对象，再决定如何恢复。
4. 原图内保存和另存是不同操作。按用户要求保存，并核对目标路径、文件及原生读回结果；需要精确交付时可在不影响原会话的情况下重新打开输出副本核验。详细规则见 [保存与案例复盘](references/experience-index.md)。

**保留文件对话框：** 不要把 `FILEDIA` 设置为 `0`，临时设置也不允许。执行 `NETLOAD`、打开、另存等需要文件窗口的操作时，按实际弹窗填写路径，不为自动化切换成命令行提示。若当前 `FILEDIA` 已是 `0` 且需要弹窗，告知用户；只有明确获准后才设为 `1`。

## .NET 参数绘图插件

AutoCAD 2024 x64 的可选 [CodexAutoCAD 插件](references/dotnet-plugin.md) 提供 `CODEXRECT` 矩形参数窗口。交互命令通过 AutoCAD 自己的窗口打开；弹窗可见时核对输入与确认/取消按钮，等待命令结束后再用 ActiveX 读回几何。常规查询、绘图、平移和保存仍走 ActiveX。新增其他弹窗命令需要分别验证。

**回退：** .NET 加载失败、命令不可用或不支持所需绘图时，若用户仍要完成同一绘图任务，且参数和坐标含义已明确，使用 [ActiveX](references/activex.md) 的已支持操作完成。先确认目标图纸、命令已结束以及 .NET 未写入对应图元；断连或结果不明时先只读核验，不能直接重发。用户取消绘图、要求验证弹窗本身，或 ActiveX 无法保持同样的几何、图层和坐标约束时，停止并说明原因。

## 宗地与界址点定位

- 把点号对应到轮廓的实际顶点，用相邻边、顺序和值交叉核对。点号不等于顶点数组下标，也不要用文字的插入点作基点。
- 用户明确指定的 CAD X/Y 按原顺序使用。工具的点参数使用世界坐标（WCS）。如果用户给的是当前 UCS 坐标，用当前图纸的 `Utility.TranslateCoordinates` 转成 WCS 再操作，并转回用户坐标系核验，不改变现有 UCS。测量坐标约定不明确时按来源坐标系或已知点核对。
- 单个已知点只能约束平移。明确整图的图元范围，移动后读回同一顶点至要求精度，并核对图形尺寸和方向。图上标注、边长和面积相互矛盾时记录差异及取值依据。

## 从案例改进

先按任务关键词查阅 [经验索引](references/experience-index.md) 和工作区根目录已有的 `.autocad-control/experience.md`。本机启用自动记录后，只在发现可复用且已验证的纠正、故障或新做法时记录。发布更新与本机记录分别处理。
