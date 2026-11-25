# AutoCAD ActiveX 操作

已用 AutoCAD 2024（24.3）在临时图内实测闭合多段线、面积读取、指定顶点平移、UCS 保持和 DWG 另存重开。其他版本及其他操作需按当前图纸核验。

命令形如 `python scripts/autocad_control.py call --document 'D:/项目/图纸.dwg' --json-file request.json`。每次请求只执行一个 JSON 对象。使用 Unicode 的 UTF-8 文件。连接到其他版本的已运行实例时，在 `check` 或 `call` 之前传 `--progid AutoCAD.Application.<版本>`，先确认实际版本和活动图纸。

| 操作 | 请求示例 |
| --- | --- |
| 顶层图元查询（默认模型空间） | `{"op":"query","limit":200}` |
| 查询指定布局的文字 | `{"op":"query","layout":"布局1","type":"AcDbText","limit":200}` |
| 按句柄读取实体 | `{"op":"entity","handle":"1A2"}` |
| 画线 | `{"op":"draw","type":"line","start":[0,0,0],"end":[5,0,0]}` |
| 画圆 | `{"op":"draw","type":"circle","center":[0,0,0],"radius":2}` |
| 写单行文字 | `{"op":"draw","type":"text","at":[1,1,0],"text":"J1","height":0.25}` |
| 画闭合二维多段线 | `{"op":"draw","type":"polyline","vertices":[[0,0],[4,0],[4,3],[0,3]],"closed":true}` |
| 按两个坐标平移指定图元 | `{"op":"move","handles":["1A2","1A3"],"from":[4,3,0],"to":[100,200,0]}` |
| 当前 UCS 点转换为 WCS | `{"op":"convert","point":[100,200,0],"from":"ucs","to":"wcs"}` |
| 另存到新文件 | `{"op":"save","path":"D:/项目/成果.dwg"}` |
| 保存当前原图 | `{"op":"save"}` |

查询和绘制的 `layout` 可指定一个已有布局；绘制的 `layer` 可指定一个已有且未锁定的图层。未指定图层时使用当前图层。多段线使用世界 XY 平面，顶点列表不重复写入首点；闭合面积仅在边界几何有效时有意义。查询结果的 `total` 和 `truncated` 适用于选定范围内的匹配图元；查询不递归块内容，也不把外部参照内容算作当前空间的顶层实体。

AutoCAD 轻量多段线原生顶点是 OCS，读取时用对象法向和高程转换到 WCS。其他已支持的几何使用 WCS。坐标基准见 [Autodesk ActiveX 文档](https://help.autodesk.com/cloudhelp/2026/ENU/AutoCAD-ActiveX-Reference/files/GUID-9B897CC9-2AE8-4411-BDA9-E337CBFACF8B.htm)。

复杂标注、填充、图块属性、视口比例或打印使用当前版本的 AutoCAD 原生功能。确需另写 ActiveX 或 AutoLISP 时，按实际命令/接口逐步核对，并从小样验证；不复用中望桥接 DLL 或猜测命令提示。发生弹窗或命令等待时先读当前界面，避免在模态期间反复派发操作。
