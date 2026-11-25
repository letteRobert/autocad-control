# AutoCAD 2024 .NET 绘图插件

插件 `assets/autocad2024/CodexAutoCAD.dll` 面向 Windows 上的 AutoCAD 2024 x64 和 .NET Framework 4.8。现有 `scripts/autocad_control.py` 可继续独立使用。

## 加载和使用

1. 在 AutoCAD 2024 打开空白图。执行 `NETLOAD` 并选择技能目录里的 `assets/autocad2024/CodexAutoCAD.dll`。如果宿主出现安全提示，按实际提示核对程序集，保留现有加载安全设置。
2. 输入 `CODEXRECT`。窗口接收当前 UCS 内的基点 X、Y、宽度和高度。坐标与尺寸采用当前图形单位。
3. 点「绘制」后创建一个闭合矩形，写入当前空间和当前图层。当前图层锁定时拒绝写入。点「取消」或关闭窗口时不创建图元。
4. 等待对话框关闭后再用 ActiveX 查询命令行返回的图元句柄、顶点、面积和闭合状态。对话框打开时不要用同步 ActiveX 循环请求图纸，也不要重复发命令。

## 构建和验证

从技能根目录执行 `powershell -File plugin/build.ps1`。如 AutoCAD 安装在其他位置，通过 `-AutoCADDirectory` 指定路径。构建使用本机 .NET Framework 编译器和 AutoCAD 2024 安装目录的托管引用，输出 DLL 和 SHA-256。

加载后运行 `CODEXRECTCHECK`，在内存测试库检查确认、取消、旋转 UCS、闭合和面积，命令行应显示 `CODEXRECTCHECK: PASS`。这个自检不弹窗，也不改当前图纸。桌面验收需另行运行 `CODEXRECT`，分别验证输入、确认和取消。

AutoCAD 2024 / CASS 11 桌面端已验证本插件的「绘制」和「取消」按钮。使用默认 4×3 参数绘制后，ActiveX 读回了一个闭合矩形，面积为 12；再次打开并取消后，未新增图元。
