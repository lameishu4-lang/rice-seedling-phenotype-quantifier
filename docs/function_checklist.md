# 功能实现清单

项目名称：水稻秧苗图像表型量化与数据管理软件  
英文名称：Rice Seedling Phenotype Quantifier  
版本号：V1.0.0  
开发类型：Windows 桌面端软件  
主要技术路线：传统图像处理 + 本地数据管理 + 统计摘要 + 结果复核  
更新日期：2026-05-23

---

## 一、文档目的

本文档用于记录软件 V1.0.0 版本已经实现的功能边界、对应页面、主要代码文件和完成状态。

本文档仅作为项目开发与功能核对材料，不用于夸大软件能力。所有列出的功能均应在当前源码中真实存在并可运行。

---

## 二、软件功能边界

本软件定位为面向水稻秧苗图像分析场景的桌面端辅助工具，主要用于：

1. 水稻秧苗图像导入；
2. 绿色植株区域分割；
3. 二维图像表型指标计算；
4. 单图分析记录保存；
5. 批量图像分析；
6. 历史记录管理；
7. 表格数据导出；
8. 单样本 Word 报告导出；
9. 批量统计摘要；
10. 结果可视化展示；
11. 结果解释提示；
12. 图像与指标复核。

---

## 三、功能边界说明

本软件 V1.0.0 版本不包含以下功能：

1. 不包含深度学习模型训练；
2. 不包含生成式人工智能服务；
3. 不调用云端推理接口；
4. 不调用外部 AI 接口；
5. 不提供病害诊断结论；
6. 不提供品种评价结论；
7. 不提供产量预测结论；
8. 不提供田间生产决策建议；
9. 不包含三维重建；
10. 不包含遥感大田分析；
11. 不包含用户联网账户系统；
12. 不包含云端数据库同步。

软件中的“长势评分”“评分等级”“解释提示”“复核建议”等内容均基于二维图像指标和软件内部规则生成，仅用于辅助查看和结果复核，不作为农学诊断、病害判断、品种评价或生产决策依据。

---

## 四、功能实现总表

| 功能编号 | 功能名称             | 所属模块 / 页面     | 主要文件                                                | 完成状态 | 可运行验证 |
| -------- | -------------------- | ------------------- | ------------------------------------------------------- | -------- | ---------- |
| F01      | 项目基础结构         | 项目工程            | main.py / pyproject.toml / requirements.txt             | 已完成   | 是         |
| F02      | Windows 桌面端主界面 | 主窗口              | app.py / main_window.py                                 | 已完成   | 是         |
| F03      | 首页功能说明         | 首页                | main_window.py                                          | 已完成   | 是         |
| F04      | 软件功能边界展示     | 首页 / 侧边栏       | main_window.py                                          | 已完成   | 是         |
| F05      | 参数设置页面         | 参数设置            | page_settings.py                                        | 已完成   | 是         |
| F06      | 参数持久化保存       | 参数设置            | settings.py / page_settings.py                          | 已完成   | 是         |
| F07      | HSV 分割参数设置     | 参数设置            | settings.py / page_settings.py / segmentation.py        | 已完成   | 是         |
| F08      | ExG 阈值参数设置     | 参数设置            | settings.py / page_settings.py / segmentation.py        | 已完成   | 是         |
| F09      | 最小连通域面积设置   | 参数设置            | settings.py / page_settings.py / segmentation.py        | 已完成   | 是         |
| F10      | 形态学核大小设置     | 参数设置            | settings.py / page_settings.py / segmentation.py        | 已完成   | 是         |
| F11      | 默认比例尺设置       | 参数设置            | settings.py / calibration.py / page_settings.py         | 已完成   | 是         |
| F12      | 单张图像导入         | 单图分析            | page_single_analysis.py                                 | 已完成   | 是         |
| F13      | 单张图像预览         | 单图分析            | image_qt.py / page_single_analysis.py                   | 已完成   | 是         |
| F14      | 传统图像分割         | 图像处理核心        | segmentation.py                                         | 已完成   | 是         |
| F15      | 分割掩膜显示         | 单图分析            | segmentation.py / image_qt.py / page_single_analysis.py | 已完成   | 是         |
| F16      | 叠加结果显示         | 单图分析            | segmentation.py / image_qt.py / page_single_analysis.py | 已完成   | 是         |
| F17      | 比例尺换算           | 表型计算核心        | calibration.py / metrics.py                             | 已完成   | 是         |
| F18      | 株高估算             | 表型计算核心        | metrics.py                                              | 已完成   | 是         |
| F19      | 冠幅估算             | 表型计算核心        | metrics.py                                              | 已完成   | 是         |
| F20      | 投影面积计算         | 表型计算核心        | metrics.py                                              | 已完成   | 是         |
| F21      | 绿色覆盖率计算       | 表型计算核心        | metrics.py                                              | 已完成   | 是         |
| F22      | ExG 叶色指数计算     | 表型计算核心        | metrics.py                                              | 已完成   | 是         |
| F23      | Green Ratio 计算     | 表型计算核心        | metrics.py                                              | 已完成   | 是         |
| F24      | 软件内部长势评分     | 表型计算核心        | metrics.py                                              | 已完成   | 是         |
| F25      | 单图分析流程控制     | 单图分析            | page_single_analysis.py                                 | 已完成   | 是         |
| F26      | 单图结果解释提示     | 单图分析            | page_single_analysis.py                                 | 已完成   | 是         |
| F27      | 单图记录保存         | 单图分析 / 历史记录 | page_single_analysis.py / database.py                   | 已完成   | 是         |
| F28      | 单图 Word 报告导出   | 单图分析            | page_single_analysis.py                                 | 已完成   | 是         |
| F29      | SQLite 数据库初始化  | 数据管理            | database.py / paths.py                                  | 已完成   | 是         |
| F30      | 历史记录写入         | 数据管理            | database.py                                             | 已完成   | 是         |
| F31      | 历史记录查询         | 历史记录            | database.py / page_records.py                           | 已完成   | 是         |
| F32      | 历史记录连续显示序号 | 历史记录            | page_records.py                                         | 已完成   | 是         |
| F33      | 历史记录内部 ID 追踪 | 历史记录            | database.py / page_records.py                           | 已完成   | 是         |
| F34      | 历史记录备注编辑     | 历史记录            | database.py / page_records.py                           | 已完成   | 是         |
| F35      | 历史记录删除         | 历史记录            | database.py / page_records.py                           | 已完成   | 是         |
| F36      | 历史记录统计摘要     | 历史记录            | page_records.py                                         | 已完成   | 是         |
| F37      | 历史记录详情复核     | 历史记录            | record_review_dialog.py / page_records.py               | 已完成   | 是         |
| F38      | 批量文件夹选择       | 批量分析            | page_batch_analysis.py                                  | 已完成   | 是         |
| F39      | 批量图像识别         | 批量分析            | batch.py / page_batch_analysis.py                       | 已完成   | 是         |
| F40      | 批量图像分析         | 批量分析            | batch.py / page_batch_analysis.py                       | 已完成   | 是         |
| F41      | 批量分析进度显示     | 批量分析            | page_batch_analysis.py                                  | 已完成   | 是         |
| F42      | 批量结果表格显示     | 批量分析            | page_batch_analysis.py                                  | 已完成   | 是         |
| F43      | 批量失败原因显示     | 批量分析            | batch.py / page_batch_analysis.py                       | 已完成   | 是         |
| F44      | 批量统计摘要         | 批量分析            | statistics.py / page_batch_analysis.py                  | 已完成   | 是         |
| F45      | 批量结果解释提示     | 批量分析            | page_batch_analysis.py                                  | 已完成   | 是         |
| F46      | 批量结果可视化       | 批量分析            | charts.py / page_batch_analysis.py                      | 已完成   | 是         |
| F47      | 长势评分柱状图       | 批量分析            | charts.py / page_batch_analysis.py                      | 已完成   | 是         |
| F48      | 株高估算柱状图       | 批量分析            | charts.py / page_batch_analysis.py                      | 已完成   | 是         |
| F49      | 评分等级统计条       | 批量分析            | charts.py / page_batch_analysis.py                      | 已完成   | 是         |
| F50      | 批量页面滚动布局     | 批量分析            | page_batch_analysis.py                                  | 已完成   | 是         |
| F51      | 批量选中样本复核     | 批量分析            | sample_review_dialog.py / page_batch_analysis.py        | 已完成   | 是         |
| F52      | 批量成功记录保存     | 批量分析 / 历史记录 | page_batch_analysis.py / database.py                    | 已完成   | 是         |
| F53      | 批量 Excel 导出      | 批量分析 / 导出     | excel_exporter.py / page_batch_analysis.py              | 已完成   | 是         |
| F54      | 批量 CSV 导出        | 批量分析 / 导出     | excel_exporter.py / page_batch_analysis.py              | 已完成   | 是         |
| F55      | 历史记录 Excel 导出  | 历史记录 / 导出     | excel_exporter.py / page_records.py                     | 已完成   | 是         |
| F56      | 历史记录 CSV 导出    | 历史记录 / 导出     | excel_exporter.py / page_records.py                     | 已完成   | 是         |
| F57      | Excel 明细数据工作表 | 导出模块            | excel_exporter.py                                       | 已完成   | 是         |
| F58      | Excel 统计摘要工作表 | 导出模块            | excel_exporter.py / statistics.py                       | 已完成   | 是         |
| F59      | 输出目录管理         | 工具模块            | paths.py                                                | 已完成   | 是         |
| F60      | 中文路径图像读取     | 图像处理 / 工具     | batch.py / page_single_analysis.py / dialogs            | 已完成   | 是         |
| F61      | 中文路径图像保存     | 图像处理 / 工具     | page_single_analysis.py / page_batch_analysis.py        | 已完成   | 是         |
| F62      | 本地运行数据隔离     | 项目工程            | .gitignore / paths.py                                   | 已完成   | 是         |
| F63      | README 使用说明      | 文档                | README.md                                               | 已完成   | 是         |
| F64      | 功能清单文档         | 文档                | docs/function_checklist.md                              | 已完成   | 是         |
| F65      | 测试清单文档         | 文档                | docs/test_checklist.md                                  | 已完成   | 是         |

---

## 五、单图分析模块说明

单图分析模块用于处理单张水稻秧苗图像。

主要流程：

1. 导入图像；
2. 显示原始图像；
3. 执行绿色区域分割；
4. 显示分割掩膜图；
5. 显示叠加结果图；
6. 设置比例尺；
7. 计算二维表型指标；
8. 生成单样本结果解释提示；
9. 保存分析记录；
10. 导出 Word 图文报告。

该模块强调用户确认流程，保存记录和导出报告必须在指标计算完成后才能执行。

---

## 六、批量分析模块说明

批量分析模块用于处理一个文件夹中的多张图像。

主要流程：

1. 选择图像文件夹；
2. 读取参数设置；
3. 执行批量分析；
4. 显示逐图分析结果；
5. 生成批量统计摘要；
6. 生成批量结果解释提示；
7. 显示批量结果可视化图表；
8. 复核选中样本；
9. 保存成功分析记录；
10. 导出 Excel / CSV。

批量分析中，失败图像不会写入历史记录，但会保留在批量结果表格和导出文件中。

---

## 七、历史记录模块说明

历史记录模块用于管理已保存的单图分析记录和批量成功记录。

主要功能包括：

1. 查询历史记录；
2. 显示历史记录表格；
3. 显示统计摘要；
4. 查看记录详情；
5. 回看原始图像、掩膜图和叠加图；
6. 查看指标和备注；
7. 编辑备注；
8. 删除记录；
9. 导出 Excel / CSV。

历史记录表格第一列为连续显示序号，数据库内部记录 ID 仅用于数据追踪。

---

## 八、导出功能说明

### 8.1 Excel 导出

批量分析结果和历史记录均支持 Excel 导出。

Excel 文件包含：

1. 明细数据工作表；
2. 统计摘要工作表。

明细数据用于保存逐图或逐记录结果。统计摘要用于保存数量统计、成功率以及主要表型指标的均值、最小值和最大值。

### 8.2 CSV 导出

批量分析结果和历史记录均支持 CSV 导出。

CSV 文件保持为明细数据，不包含多工作表。

CSV 使用 UTF-8 with BOM 编码，便于在 Excel 中打开中文字段。

### 8.3 Word 报告导出

单图分析结果支持 Word 图文报告导出。

报告内容包括：

1. 报告标题；
2. 软件版本；
3. 样本名称；
4. 原始图像路径；
5. 分析参数；
6. 原始图像；
7. 分割掩膜图；
8. 叠加结果图；
9. 表型指标表；
10. 结果解释提示；
11. 结果说明。

---

## 九、结果解释与复核说明

软件提供以下解释与复核功能：

1. 单图结果解释提示；
2. 批量结果解释提示；
3. 批量选中样本复核；
4. 历史记录详情复核。

解释提示主要基于：

1. 绿色覆盖率；
2. 外接矩形填充率；
3. 软件内部长势评分；
4. 批量统计结果；
5. 分析成功 / 失败状态。

解释提示仅用于辅助查看和人工复核，不作为农学诊断、病害判断、品种评价或生产决策依据。

---

## 十、阶段开发记录

| 阶段     | 提交说明                                           | 主要内容                       |
| -------- | -------------------------------------------------- | ------------------------------ |
| 第 1 次  | init pyside6 desktop project structure             | 初始化 PySide6 桌面端项目结构  |
| 第 2 次  | add image segmentation preview workflow            | 增加传统图像分割和结果预览     |
| 第 3 次  | add scale calibration and phenotype metrics        | 增加比例尺换算和表型指标计算   |
| 第 4 次  | add sqlite record management                       | 增加 SQLite 历史记录管理       |
| 第 5 次  | add batch image analysis workflow                  | 增加批量图像分析流程           |
| 第 6 次  | add persistent parameter settings                  | 增加参数设置与持久化           |
| 第 7 次  | connect single analysis to saved parameters        | 单图分析接入参数设置           |
| 第 8 次  | update documentation for v1.0                      | 更新 README 和基础文档         |
| 第 9 次  | add batch success record saving                    | 增加批量成功记录保存           |
| 第 10 次 | add phenotype visualization and summary statistics | 增加统计摘要、可视化和解释提示 |
| 第 11 次 | add batch sample review dialog                     | 增加批量选中样本复核弹窗       |
| 第 12 次 | add history record review dialog                   | 增加历史记录详情复核弹窗       |

实际提交名称以 GitHub 仓库记录为准。

---

## 十一、V1.0.0 功能完整性结论

截至当前版本，软件已经形成以下闭环：

1. 单图分析闭环：导入图像 → 分割 → 指标计算 → 解释提示 → 保存记录 → 导出报告；
2. 批量分析闭环：选择文件夹 → 批量分析 → 统计摘要 → 可视化 → 解释提示 → 样本复核 → 保存成功记录 / 导出数据；
3. 历史记录闭环：保存记录 → 查询记录 → 统计摘要 → 查看详情 → 编辑备注 → 导出 / 删除；
4. 数据导出闭环：明细数据导出 → 统计摘要导出 → 本地文件留存。

V1.0.0 版本功能边界清晰，主要功能均可在本地 Windows 环境下运行验证。