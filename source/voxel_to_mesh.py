import os 
import pathlib
from skimage import io
import time
import numpy as np
import torch
from torchmcubes import marching_cubes
import random
import math
import pyvista as pv
from rotation_matrix import rotation_matrix
from detector import read_detector_str
from detector import detector_str
def generate_mesh_from_stl(stl_path, tri_dir, scale=10, sample_tilt_x=0, sample_tilt_new_z=0, sample_tilt_y=0, det_tilt_x=0, det_tilt_y=0):  # final_side设置为1000
    """
    从STL文件生成网格
    
    参数:
        stl_path: STL文件路径
        output_path: 输出路径
        final_side: 最终网格大小。目前设置为模型实际的大小。
        scale: 缩放因子。目前设置为10，将1微米视为0.001微米，然后转为纳米，纯粹为了加速计算。
        tilt_x: X轴旋转角度
        tilt_y: Y轴旋转角度
        pad_scale: 填充缩放因子
    """
    stl_path = sanitize_path(stl_path)
    tri_dir = sanitize_path(tri_dir)

    os.makedirs(tri_dir, exist_ok=True)
    # 保留原始文件名
    name = os.path.basename(stl_path).split('.')[0]
    
    # 读取STL文件
    t_start = time.time()
    mesh = pv.read(stl_path)
    points = torch.tensor(mesh.points, dtype=torch.float32)  # 显式转换为 Tensor

    R = torch.eye(3, device=points.device).float()
    # Apply tilts
    if sample_tilt_x != 0 or sample_tilt_y != 0:
        if sample_tilt_x != 0:
            
            mesh = mesh.rotate_x(sample_tilt_x, point=(0,0,0), inplace=False)
            points = torch.tensor(mesh.points, dtype=torch.float32)  # 显式转换为 Tensor
            # 绕x轴旋转后，如果样品倾转角为55度，绕样品表面法线方向旋转
            # 计算旋转角度（弧度）
            # tilt_new_z_rad = math.radians(sample_tilt_new_z)
             #tilt_new_z_rad_tensor = torch.tensor(tilt_new_z_rad, device=v.device)
            
            # 计算新的Z轴方向（样品表面法线方向）- 预计算常量
            # 当样品倾转角为55度时，新的Z轴方向为 [0, -sin(55°), cos(55°)]
            # rotation_axis = torch.tensor([0, -sin_tx, cos_tx], device=v.device)
            R = torch.tensor(rotation_matrix(tilt_x=sample_tilt_x, rotate_angle=sample_tilt_new_z), dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
            points_ = torch.stack([points[:, 0], points[:, 1], points[:, 2]], dim=1).to(R.device)
            rotated_points = torch.mm(points_, R.T)  # 矩阵乘法

        if sample_tilt_y != 0:
            mesh.rotate_y(sample_tilt_y, point=(0,0,0), inplace=False)
            points = torch.tensor(mesh.points, dtype=torch.float32)  # 显式转换为 Tensor
            # # 绕 Y 轴旋转后的旋转轴方向（新的 Z 轴方向）
            # rotation_axis = torch.tensor([sin_ty, 0, cos_ty], device=v.device)
            R = rotation_matrix(tilt_y=sample_tilt_y, rotate_angle=sample_tilt_new_z)
            R = torch.tensor(R, dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
            points_ = torch.stack([points[:, 0], points[:, 1], points[:, 2]], dim=1).to(R.device)
            rotated_points = torch.mm(points_, R.T)  # 矩阵乘法
        # 更新顶点坐标
        points[:, 0] = rotated_points[:, 0]
        points[:, 1] = rotated_points[:, 1]
        points[:, 2] = rotated_points[:, 2]
    else:
        R = torch.tensor(rotation_matrix(rotate_angle=sample_tilt_new_z), dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
        points_ = torch.stack([points[:, 0], points[:, 1], points[:, 2]], dim=1).to(R.device)
        rotated_points = torch.mm(points_, R.T)  # 矩阵乘法

        # 更新顶点坐标
        points[:, 0] = rotated_points[:, 0]
        points[:, 1] = rotated_points[:, 1]
        points[:, 2] = rotated_points[:, 2]

    #verts = torch.tensor(mesh.vertices * 1000, dtype=torch.float32).cuda()   # 获取顶点和面，并把顶点坐标从微米转为纳米
    # 如果stl模型的单位为微米，获取顶点和面，并把顶点坐标视为0.001倍的单位，并把0.001微米单位转为纳米，纯粹为了加速计算。  
    points = (points * scale).detach().clone().to(torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')   
    #verts = torch.tensor(mesh.vertices * 10, dtype=torch.float32).cuda()
    faces = torch.tensor(mesh.faces, dtype=torch.int32).to('cuda' if torch.cuda.is_available() else 'cpu')
    faces = faces.reshape(-1, 4)[:, 1:]  # 转换为 (m, 3)
    t_end = time.time()
    
    print(f"顶点数: {points.size(0)}, 面片数: {faces.size(0)}, 用时: {t_end - t_start:.1f}s")
    #print(torch.max(verts, dim=0), torch.min(verts, dim=0))
    # 36边形探测器
    material1, material2, detector_x, detector_y, detector_z = read_detector_str(detector_str)
    
    d_xmin, d_xmax = np.min(detector_x), np.max(detector_x)
    d_ymin, d_ymax = np.min(detector_y), np.max(detector_y)
    d_zmin, d_zmax = np.min(detector_z), np.max(detector_z)
    terminator_z = torch.min(points[:, 2]) # 在样品下方放置终止器  
    mirror_ymax = max(torch.max(points[:, 1]), d_ymax) 

    env_str = f"""
-122 -122  {d_xmax}   {d_ymin} {terminator_z}  {d_xmax}   {mirror_ymax} {terminator_z}  {d_xmax}   {mirror_ymax}     {d_zmax}
-122 -122  {d_xmax}   {d_ymin} {terminator_z}  {d_xmax}   {mirror_ymax} {d_zmax}    {d_xmax}   {d_ymin}     {d_zmax}
-122 -122  {d_xmin}   {mirror_ymax} {terminator_z}  {d_xmin}   {d_ymin} {terminator_z}  {d_xmin}   {mirror_ymax}     {d_zmax}
-122 -122  {d_xmin}   {mirror_ymax} {d_zmax}    {d_xmin}   {d_ymin} {terminator_z}  {d_xmin}   {d_ymin}     {d_zmax}
-122 -122  {d_xmin}   {d_ymin} {terminator_z}  {d_xmax}   {d_ymin} {terminator_z}  {d_xmax}   {d_ymin}     {d_zmax}
-122 -122  {d_xmin}   {d_ymin} {terminator_z}  {d_xmax}   {d_ymin} {d_zmax}    {d_xmin}   {d_ymin}     {d_zmax}
-122 -122  {d_xmax}   {mirror_ymax} {terminator_z}  {d_xmin}   {mirror_ymax} {terminator_z}  {d_xmax}   {mirror_ymax}     {d_zmax}
-122 -122  {d_xmax}   {mirror_ymax} {d_zmax}    {d_xmin}   {mirror_ymax} {terminator_z}  {d_xmin}   {mirror_ymax}     {d_zmax}
-127 -127  {d_xmax}   {d_ymin} {terminator_z}  {d_xmin}   {d_ymin} {terminator_z}  {d_xmax}   {mirror_ymax}     {terminator_z}
-127 -127  {d_xmax}   {mirror_ymax} {terminator_z}  {d_xmin}   {d_ymin} {terminator_z}  {d_xmin}   {mirror_ymax}     {terminator_z}"""

    # 生成输出文件名，保留原始文件名
    output_filename = f'{name}_sampleTiltx{55-sample_tilt_x}_sampleTilty{sample_tilt_y}_sampleTiltNewZ{sample_tilt_new_z}_detTiltx{det_tilt_x}_{faces.size(0)}.tri'
    # 只对输出文件名进行安全处理，确保文件系统兼容性
    safe_output_filename = ''.join(c if c.isalnum() or c in '_-.' else '_' for c in output_filename)
    print("tri_dir:", tri_dir)
    tri_path = os.path.join(tri_dir, safe_output_filename)
    print("tri_path:", tri_path)
    # 生成网格文件
    with open(tri_path, 'w') as f:
        for face in faces:
            f.write(
                f"0 -123 {points[face[0], 0]:.2f} {points[face[0], 1]:.2f} {points[face[0], 2]:.2f} {points[face[1], 0]:.2f} {points[face[1], 1]:.2f} {points[face[1], 2]:.2f} {points[face[2], 0]:.2f} {points[face[2], 1]:.2f} {points[face[2], 2]:.2f}\n"
            )
        f.write("\n")
        f.write("\n")
        d_j = 0
        for i in range(len(material1)):        
            f.write(f"{material1[i]} {material2[i]} {detector_x[d_j]:.6f} {detector_y[d_j]:.6f} {detector_z[d_j]:.6f} {detector_x[d_j+1]:.6f} {detector_y[d_j+1]:.6f} {detector_z[d_j+1]:.6f} {detector_x[d_j+2]:.6f} {detector_y[d_j+2]:.6f} {detector_z[d_j+2]:.6f}\n")
            d_j += 3

        f.write("\n")
        f.write("\n")
        f.write(env_str)

    return points, d_zmin, d_zmax, tri_path, R


    """
    从体素数据生成网格
    
    参数:
        voxel_path: 体素文件路径
        output_path: 输出路径
        final_side: 最终网格大小
        tilt_x: X轴旋转角度
        tilt_y: Y轴旋转角度
        pad_scale: 填充缩放因子
        length: 体素数据长度
        reverse: 是否反转体素值
    """
    voxel_path = sanitize_path(voxel_path)
    tri_dir = sanitize_path(tri_dir)
    tri_dir = tri_dir / "mesh"
    tri_dir.mkdir(parents=True, exist_ok=True)
    # 保留原始文件名
    name = voxel_path.stem
    try:
        voxel = io.imread(voxel_path)
    except Exception as e:
        print(f"读取体素文件时出错: {e}")
        raise

    # 计算体素数据的边界尺寸
    side = max(voxel.shape[1], voxel.shape[2])  # 取高度和宽度的最大值作为边长
    scale = final_side / side

    # 获取体素数据的实际尺寸
    voxel_depth, voxel_height, voxel_width = voxel.shape
    
    # 确保不会超出体素数据的边界
    max_z = max(0, voxel_depth - length - 1)
    max_x = max(0, voxel_height - side - 1)
    max_y = max(0, voxel_width - side - 1)
    
    # 如果体素数据尺寸不足，则调整length和side
    actual_length = min(length, voxel_depth)
    actual_side_x = min(side, voxel_height)
    actual_side_y = min(side, voxel_width)
    
    z_start = random.randint(0, max_z) if max_z > 0 else 0
    x_start = random.randint(0, max_x) if max_x > 0 else 0
    y_start = random.randint(0, max_y) if max_y > 0 else 0
    
    print(f"体素数据尺寸: {voxel.shape}, 使用区域: z={z_start}:{z_start+actual_length}, x={x_start}:{x_start+actual_side_x}, y={y_start}:{y_start+actual_side_y}")
    u = torch.from_numpy(voxel[z_start:z_start+actual_length, x_start:x_start+actual_side_x, y_start:y_start+actual_side_y].astype(np.float32))
    pad3d = (1, 1, 1, 1, 1, 1)
    u = 1 - u.to('cuda' if torch.cuda.is_available() else 'cpu') if reverse else u.to('cuda' if torch.cuda.is_available() else 'cpu')
        
    u = torch.nn.functional.pad(u, pad3d, 'constant', 0)
    t_start = time.time()
    verts, faces = marching_cubes(u, 0.5)
    t_end = time.time()
    print(f"顶点数: {verts.size(0)}, 面片数: {faces.size(0)}, 用时: {t_end - t_start:.1f}s")
    print(torch.max(verts, dim=0), torch.min(verts, dim=0))

    v = verts.clone()
    v[:, 0] -= actual_side_x / 2
    v[:, 1] -= actual_side_y / 2
    v[:, 2] -= actual_length
    v *= scale

    # 预先定义旋转变量，避免在后续代码中未定义的问题
    cos_tx = cos_ty = 1.0
    sin_tx = sin_ty = 0.0
    
    # Apply tilts
    if tilt_x != 0 or tilt_y != 0:
        if tilt_x != 0:
            tilt_x_rad = math.radians(tilt_x)
            cos_tx = math.cos(tilt_x_rad)
            sin_tx = math.sin(tilt_x_rad)
            y = v[:, 1] * cos_tx - v[:, 2] * sin_tx
            z = v[:, 1] * sin_tx + v[:, 2] * cos_tx
            v[:, 1] = y
            v[:, 2] = z

        if tilt_y != 0:
            tilt_y_rad = math.radians(tilt_y)
            cos_ty = math.cos(tilt_y_rad)
            sin_ty = math.sin(tilt_y_rad)
            x = v[:, 0] * cos_ty + v[:, 2] * sin_ty
            z = -v[:, 0] * sin_ty + v[:, 2] * cos_ty
            v[:, 0] = x
            v[:, 2] = z

    xmin = ymin = -final_side / 2
    xmax = ymax = final_side / 2
    terminator_z = -10000  
    detector_z = float(torch.max(v[:, 2]).item()) + 100  # 在样品上方10个单位处放置探测器
    print("detector_z", detector_z)
    base_z = -actual_length * scale 

    # Define base points
    base_points = torch.tensor([
        [xmax, ymin, base_z],
        [xmin, ymin, base_z],
        [xmax, ymax, base_z],
        [xmin, ymax, base_z]
    ], dtype=torch.float32)

    # Apply rotations to base points
    if tilt_x != 0 or tilt_y != 0:
        if tilt_x != 0:
            y = base_points[:, 1] * cos_tx - base_points[:, 2] * sin_tx
            z = base_points[:, 1] * sin_tx + base_points[:, 2] * cos_tx
            base_points[:, 1] = y
            base_points[:, 2] = z

        if tilt_y != 0:
            x = base_points[:, 0] * cos_ty + base_points[:, 2] * sin_ty
            z = -base_points[:, 0] * sin_ty + base_points[:, 2] * cos_ty
            base_points[:, 0] = x
            base_points[:, 2] = z

    p1 = base_points[0]
    p2 = base_points[1]
    p3 = base_points[2]
    p4 = base_points[3]

    base_str = f"""-123 1  {p1[0]:.1f}   {p1[1]:.1f} {p1[2]:.1f}  {p2[0]:.1f}   {p2[1]:.1f} {p2[2]:.1f}  {p3[0]:.1f}   {p3[1]:.1f} {p3[2]:.1f}
-123 1 {p3[0]:.1f}   {p3[1]:.1f} {p3[2]:.1f}  {p2[0]:.1f}   {p2[1]:.1f} {p2[2]:.1f}  {p4[0]:.1f}   {p4[1]:.1f} {p4[2]:.1f}
"""

    env_str = f"""
-125 -125  {xmin}   {ymin} {detector_z}   {xmax}   {ymin}   {detector_z}   {xmax}   {ymax}     {detector_z}
-125 -125  {xmin}   {ymin} {detector_z}    {xmax}   {ymax} {detector_z}    {xmin}   {ymax}     {detector_z}

-122 -122  {xmax}   {ymin} {terminator_z}  {xmax}   {ymax} {terminator_z}  {xmax}   {ymax}     {detector_z}

-122 -122  {xmax}   {ymin} {terminator_z}  {xmax}   {ymax} {detector_z}    {xmax}   {ymin}     {detector_z}
-122 -122  {xmin}   {ymax} {terminator_z}  {xmin}   {ymin} {terminator_z}  {xmin}   {ymax}     {detector_z}
-122 -122  {xmin}   {ymax} {detector_z}    {xmin}   {ymin} {terminator_z}  {xmin}   {ymin}     {detector_z}
-122 -122  {xmin}   {ymin} {terminator_z}  {xmax}   {ymin} {terminator_z}  {xmax}   {ymin}     {detector_z}
-122 -122  {xmin}   {ymin} {terminator_z}  {xmax}   {ymin} {detector_z}    {xmin}   {ymin}     {detector_z}
-122 -122  {xmax}   {ymax} {terminator_z}  {xmin}   {ymax} {terminator_z}  {xmax}   {ymax}     {detector_z}
-122 -122  {xmax}   {ymax} {detector_z}    {xmin}   {ymax} {terminator_z}  {xmin}   {ymax}     {detector_z}
-127 -127  {xmax}   {ymin} {terminator_z}  {xmin}   {ymin} {terminator_z}  {xmax}   {ymax}     {terminator_z}
-127 -127  {xmax}   {ymax} {terminator_z}  {xmin}   {ymin} {terminator_z}  {xmin}   {ymax}     {terminator_z}"""

    # 生成输出文件名，保留原始文件名
    output_filename = f'{name}_{actual_side_x}x{actual_side_y}to{final_side}_{actual_length}_tiltx{tilt_x}_tilty{tilt_y}_{faces.size(0)}.tri'
    # 只对输出文件名进行安全处理，确保文件系统兼容性
    safe_output_filename = ''.join(c if c.isalnum() or c in '_-.' else '_' for c in output_filename)
    with open(tri_dir / safe_output_filename, 'w') as f:
        for face in faces:
            f.write(
            f"-123 0 {v[face[0], 0] * 1000:.2f} {v[face[0], 1] * 1000:.2f} {v[face[0], 2] * 1000:.2f} {v[face[1], 0] * 1000:.2f} {v[face[1], 1] * 1000:.2f} {v[face[1], 2] * 1000:.2f} {v[face[2], 0] * 1000:.2f} {v[face[2], 1] * 1000:.2f} {v[face[2], 2] * 1000:.2f}\n")        
        #f.write(base_str)
        f.write(env_str)

    return v, faces

def sanitize_path(path):
    """
    处理路径，确保能正确处理包含空格和特殊字符的路径，但不修改文件名
    
    参数:
        path (str或Path): 需要处理的路径
        
    返回:
        Path: 处理后的Path对象
    """
    # 如果是字符串且被引号包裹，则去除引号
    if isinstance(path, str):
        if (path.startswith('"') and path.endswith('"')) or \
           (path.startswith("'") and path.endswith("'")):
            path = path[1:-1]
    
    # 转换为Path对象，保留原始文件名
    return pathlib.Path(str(path))

def run_interface(voxel_path, mesh_path, scale=10, sample_tilt_x=0, sample_tilt_y=0, sample_tilt_new_z=0, det_tilt_x=0):  
    """
    运行接口函数，将体素数据转换为网格数据并保存。

    参数:
        voxel_path (Path或str): 体素文件路径，可以是任意文件名（包含空格）
        mesh_path (Path或str): 网格文件保存路径
        side (int): 初始边长
        scale: 缩放因子。目前设置为10，将1微米视为0.001微米，然后转为纳米，纯粹为了加速计算。
        length (int): 长度
        tilt_x (float): X轴倾斜角度
        tilt_y (float): Y轴倾斜角度

    返回:
        tuple: (顶点数据, 面片数据)
    """
    try:
        # 处理路径格式，但保留原始文件名
        voxel_path = sanitize_path(voxel_path)
        mesh_path = sanitize_path(mesh_path)
        
        # 检查输入文件是否存在
        if not voxel_path.exists():
            raise FileNotFoundError(f"输入文件 '{voxel_path}' 不存在")            
            return None, None
        
        return generate_mesh_from_stl(stl_path=voxel_path, tri_dir=mesh_path, scale=scale, sample_tilt_x=sample_tilt_x, sample_tilt_y=sample_tilt_y, sample_tilt_new_z=sample_tilt_new_z, det_tilt_x = det_tilt_x)

            
    except Exception as e:
        raise FileNotFoundError(f"处理文件 '{voxel_path}' 时出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    

