# Nebula Python Wrapper

Nebula 仿真相关的 Python 工具集与脚本集合，包含运行/分析仿真结果的实用脚本，以及一个“图像转视频”的桌面 GUI 工具，便于将多张图片合成为 MP4/AVI 视频。

- 语言：Python
- 平台：Linux（优先支持），其他平台可尝试（依赖可用性决定）

---

## 功能总览
- 运行 Nebula 仿真并处理输出数据
- 生成/管理网格及仿真参数的辅助脚本
- SEM 分析脚本与可视化
- 新增：图像转视频 GUI（一次选择多张图片，设置帧率/分辨率/质量并导出）

---

## 安装与环境

推荐在虚拟环境或 Conda 环境中使用：

```bash
# 克隆仓库
git clone <your-repo-url-or-ssh>
cd nebula_python_wrapper

# 安装依赖
pip install -r requirements.txt

# 可选：开发模式安装（提供入口脚本，参见 setup.py）
pip install -e .
```

主要依赖：
- numpy
- matplotlib
- PyQt6（图形界面）
- opencv-python（视频编码）

> 注：不同平台的 OpenCV 二进制包所带视频编码器不同。本项目会在 HEVC/H.265、H.264、mp4v 之间自动回退，尽量保证生成成功。

---

## 快速开始

### 1) 图像转视频 GUI（Images → Video）

启动 GUI：

```bash
python source/images_to_video_gui.py
```

功能与操作：
- 选择图片：
  - “选择图片”替换当前选择
  - “添加更多图片”在已有基础上追加
  - “添加文件夹”从整个目录批量导入
- 排序：按“名称/日期”排序
- 输出：选择输出文件（建议 .mp4）
- 参数：设置帧率（FPS）、分辨率（预设或自定义）、宽高比策略（保持/拉伸）、质量（高/标准/压缩）
- 进度：底部进度条显示实时进度

细节说明：
- 支持格式：.png, .jpg, .jpeg, .bmp, .tif, .tiff
- 分辨率：
  - 提供 4K/2K/1080p/720p/480p 预设或自定义宽高
  - 为了编码器兼容，程序会自动将奇数宽高修正为偶数
- 宽高比：
  - 保持：按比例缩放并在空白处填充黑边
  - 拉伸：直接缩放到目标尺寸（可能变形）
- 质量选项：
  - 高质量：清晰但文件更大（Cubic 插值）
  - 标准：质量与速度平衡（Linear 插值）
  - 压缩：体积更小，适合预览（Area 插值）
- 编码器回退：
  1) HEVC/H.265（hev1）→ 2) H.264（avc1）→ 3) mp4v
  若前两者不可用，会自动回退到 mp4v（兼容性最好）

常见问题：
- 无法创建视频文件：
  - 尝试 .mp4 或 .avi 后缀
  - 确认输出目录可写
  - 降低分辨率或选择“标准/压缩”
- HEVC/H.264 不可用：
  - OpenCV 未启用相关编码器很常见；程序会回退到 mp4v
- GUI 启动失败：
  - 确认已安装 PyQt6：`pip install PyQt6`
  - 重新安装依赖：`pip install -r requirements.txt`

### 2) SEM 分析与仿真脚本

示例：运行 SEM 分析脚本（路径按需调整）：

```bash
python source/sem-analysis.py
```

自动仿真脚本：

```bash
python source/auto_run_simulation.py
```

脚本流程概览（`source/auto_run_simulation.py`）：
- 遍历 `stl_dir` 下的 .stl 文件
- 生成 .tri / .pri 文件
- 调用 Nebula 可执行程序运行仿真
- 保存图像（.png）和相机参数（JSON）

关键参数（脚本顶部）：
- `mat_paths_list`：材料 `.mat` 文件路径列表
- `nebula_gpu_path`：Nebula 可执行文件路径（确保存在且可执行）
- `stl_dir`：输入 STL 目录
- `output_path`：输出 `.det` 文件路径
- 其他：`rotate_angle_*`、`roi_array`、`pixel_size`、`energy`、`epx` 等

> 提示：不同系统的路径格式不同，请按需修改；确保路径真实存在并具备权限。

---

## 项目结构

```
nebula_python_wrapper/
├── CHANGELOG.md
├── PROJECT_DOCUMENTATION.md
├── README.md
├── requirements.txt
├── setup.py
├── TECHNICAL_DOCUMENTATION.md
├── troubleshooting.md
├── USER_GUIDE.md
├── docs/
│   └── nebula_gpu_python_wrapper_doc.md
└── source/
    ├── __init__.py
    ├── analysis.py
    ├── auto_run_simulation.py
    ├── generate_circular_mesh.py
    ├── generate_cylinder_mesh.py
    ├── generate_tri_pri.py
    ├── images_to_video_gui.py      # 图像转视频 GUI
    ├── nebula_gpu                  # Nebula 可执行（Linux 示例）
    ├── nebula_gui.py
    ├── parameters.py
    ├── process_stl_to_tri.py
    ├── read_stl_to_txt.py
    ├── rotate_cylinder.py
    ├── rotation_matrix.py
    ├── run_nebula.py
    ├── save_parameters.py
    ├── sem-analysis.py
    ├── sem_pri.py
    ├── tri_view_gui.py
    └── voxel_to_mesh.py
```

---

## 故障排查（Troubleshooting）

- 视频质量或体积不理想：
  - 降低分辨率/帧率、选择“压缩”质量；统一图片尺寸可减少插值处理
- 图片尺寸不统一：
  - 按策略自动适配；“保持”会产生黑边，“拉伸”可能变形
- “无法读取图片”：
  - 确认路径存在且文件未损坏；尝试去除过于特殊的路径字符
- 仿真失败提示可执行文件不存在：
  - 检查 `nebula_gpu_path` 是否正确，Linux 下需要有执行权限（`chmod +x`）

---

## 贡献（Contributing）
1. Fork 本仓库
2. 为功能或修复创建分支
3. 提交 PR 并说明改动动机与细节

## 许可（License）
MIT
