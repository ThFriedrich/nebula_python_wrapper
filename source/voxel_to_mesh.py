import os
os.environ['PYOPENGL_PLATFORM'] = 'egl' 
import pathlib
from skimage import io
import time
import numpy as np
import torch
from torchmcubes import marching_cubes
import random
import math
import trimesh  # 用于读取STL文件
from rotation_matrix import rotation_matrix
def generate_mesh_from_stl(stl_path, output_path, final_side=1000, scale=10, sample_tilt_x=0, sample_tilt_new_z=0, sample_tilt_y=0, det_tilt_x=0, det_tilt_y=0):  # final_side设置为1000
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
    output_path = sanitize_path(output_path)
    mesh_path = output_path
    mesh_path.mkdir(parents=True, exist_ok=True)
    # 保留原始文件名
    name = stl_path.stem
    
    # 读取STL文件
    t_start = time.time()
    mesh = trimesh.load(stl_path)
    
    
    #verts = torch.tensor(mesh.vertices * 1000, dtype=torch.float32).cuda()   # 获取顶点和面，并把顶点坐标从微米转为纳米
    # 如果stl模型的单位为微米，获取顶点和面，并把顶点坐标视为0.001倍的微米单位，并把0.001微米单位转为纳米，纯粹为了加速计算。  
    verts = torch.tensor(mesh.vertices * scale, dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')   
    #verts = torch.tensor(mesh.vertices * 10, dtype=torch.float32).cuda()
    faces = torch.tensor(mesh.faces, dtype=torch.int32).to('cuda' if torch.cuda.is_available() else 'cpu')
    t_end = time.time()
    
    #(f"顶点数: {verts.size(0)}, 面片数: {faces.size(0)}, 用时: {t_end - t_start:.1f}s")
    #print(torch.max(verts, dim=0), torch.min(verts, dim=0))
    
    # 计算模型的边界框
    bbox_min = torch.min(verts, dim=0).values
    bbox_max = torch.max(verts, dim=0).values
    bbox_size = bbox_max - bbox_min
    
    # 计算缩放因子，使模型适应指定大小。这里的处理暂时不用这个final_side来控制大小
    final_side = max(bbox_size)
    final_size_scale = final_side / max(bbox_size)
    #print(f"缩放因子: {scale:.6f}")
    # 复制顶点进行变换
    v = verts.clone()
    
    # 将模型中心移到原点
    v -= (bbox_min + bbox_max) / 2
    
    # 应用缩放
    v *= final_size_scale
    
    # 保存原始顶点
    v_orig = v.clone()

    # 预先定义旋转变量，避免在后续代码中未定义的问题
    cos_tx = cos_ty = 1.0
    sin_tx = sin_ty = 0.0
    R = torch.eye(3, device=v.device).float()
    # Apply tilts
    if sample_tilt_x != 0 or sample_tilt_y != 0:
        if sample_tilt_x != 0:
            tilt_x_rad = math.radians(sample_tilt_x)
            cos_tx = math.cos(tilt_x_rad)
            sin_tx = math.sin(tilt_x_rad)
            y = v[:, 1] * cos_tx - v[:, 2] * sin_tx
            z = v[:, 1] * sin_tx + v[:, 2] * cos_tx
            v[:, 1] = y
            v[:, 2] = z

            # 绕x轴旋转后，如果样品倾转角为55度，绕样品表面法线方向旋转
            
            # 计算旋转角度（弧度）
            # tilt_new_z_rad = math.radians(sample_tilt_new_z)
             #tilt_new_z_rad_tensor = torch.tensor(tilt_new_z_rad, device=v.device)
            
            # 计算新的Z轴方向（样品表面法线方向）- 预计算常量
            # 当样品倾转角为55度时，新的Z轴方向为 [0, -sin(55°), cos(55°)]
            # rotation_axis = torch.tensor([0, -sin_tx, cos_tx], device=v.device)
            R = torch.tensor(rotation_matrix(tilt_x=sample_tilt_x, rotate_angle=sample_tilt_new_z), dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
            points = torch.stack([v[:, 0], v[:, 1], v[:, 2]], dim=1)
            rotated_points = torch.mm(points, R.T)  # 矩阵乘法

        if sample_tilt_y != 0:
            tilt_y_rad = math.radians(sample_tilt_y)
            cos_ty = math.cos(tilt_y_rad)
            sin_ty = math.sin(tilt_y_rad)
            x = v[:, 0] * cos_ty + v[:, 2] * sin_ty
            z = -v[:, 0] * sin_ty + v[:, 2] * cos_ty
            v[:, 0] = x
            v[:, 2] = z

            # # 绕 Y 轴旋转后的旋转轴方向（新的 Z 轴方向）
            # rotation_axis = torch.tensor([sin_ty, 0, cos_ty], device=v.device)
            R = rotation_matrix(tilt_y=sample_tilt_y, rotate_angle=sample_tilt_new_z)
            R = torch.tensor(R, dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
            points = torch.stack([v[:, 0], v[:, 1], v[:, 2]], dim=1)
            rotated_points = torch.mm(points, R.T)  # 矩阵乘法
        # 更新顶点坐标
        v[:, 0] = rotated_points[:, 0]
        v[:, 1] = rotated_points[:, 1]
        v[:, 2] = rotated_points[:, 2]
    else:
        R = torch.tensor(rotation_matrix(rotate_angle=sample_tilt_new_z), dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
        points = torch.stack([v[:, 0], v[:, 1], v[:, 2]], dim=1)
        rotated_points = torch.mm(points, R.T)  # 矩阵乘法

        # 更新顶点坐标
        v[:, 0] = rotated_points[:, 0]
        v[:, 1] = rotated_points[:, 1]
        v[:, 2] = rotated_points[:, 2]


    # 因为模型中心在坐标原点
    xmin = ymin = -final_side / 2
    xmax = ymax = final_side / 2
    
    # 对于STL文件，使用final_side的一半作为基础平面的z坐标
    base_z = -final_side / 2  

    # Define base points
    base_points = torch.tensor([
        [xmax, ymin, base_z],
        [xmin, ymin, base_z],
        [xmax, ymax, base_z],
        [xmin, ymax, base_z]
    ], dtype=torch.float32)

    # Apply rotations to base points
    if sample_tilt_x != 0 or sample_tilt_y != 0:
        if sample_tilt_x != 0:
            y = base_points[:, 1] * cos_tx - base_points[:, 2] * sin_tx
            z = base_points[:, 1] * sin_tx + base_points[:, 2] * cos_tx
            
            base_points[:, 1] = y
            base_points[:, 2] = z

            R = torch.tensor(rotation_matrix(tilt_x=sample_tilt_x, rotate_angle=sample_tilt_new_z), dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
            points = torch.stack([base_points[:, 0], base_points[:, 1], base_points[:, 2]], dim=1).to(R.device)
            rotated_points = torch.mm(points, R.T)  # 矩阵乘法
            
            base_points[:, 0] = rotated_points[:, 0]
            base_points[:, 1] = rotated_points[:, 1]
            base_points[:, 2] = rotated_points[:, 2]



        if sample_tilt_y != 0:
            x = base_points[:, 0] * cos_ty + base_points[:, 2] * sin_ty
            z = -base_points[:, 0] * sin_ty + base_points[:, 2] * cos_ty
            base_points[:, 0] = x
            base_points[:, 2] = z

            R = rotation_matrix(tilt_y=sample_tilt_y, rotate_angle=sample_tilt_new_z)
            R = torch.tensor(R, dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
            points = torch.stack([base_points[:, 0], base_points[:, 1], base_points[:, 2]], dim=1).to(R.device)
            rotated_points = torch.mm(points, R.T)  # 矩阵乘法
            
            base_points[:, 0] = rotated_points[:, 0]
            base_points[:, 1] = rotated_points[:, 1]
            base_points[:, 2] = rotated_points[:, 2]

    else:
        R = torch.tensor(rotation_matrix(rotate_angle=sample_tilt_new_z), dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
        points = torch.stack([base_points[:, 0], base_points[:, 1], base_points[:, 2]], dim=1).to(R.device)
        rotated_points = torch.mm(points, R.T)  # 矩阵乘法

        # 更新顶点坐标
        base_points[:, 0] = rotated_points[:, 0]
        base_points[:, 1] = rotated_points[:, 1]
        base_points[:, 2] = rotated_points[:, 2]

    p1 = base_points[0]
    p2 = base_points[1]
    p3 = base_points[2]
    p4 = base_points[3]
    #detector_z = torch.max(v[:, 2]) + 100  # 在样品上方10个单位处放置探测器   
    #print("detector_z", detector_z)

    '''
    base_str = f"""-123 1  {p1[0]:.1f}   {p1[1]:.1f} {p1[2]:.1f}  {p2[0]:.1f}   {p2[1]:.1f} {p2[2]:.1f}  {p3[0]:.1f}   {p3[1]:.1f} {p3[2]:.1f}
-123 1 {p3[0]:.1f}   {p3[1]:.1f} {p3[2]:.1f}  {p2[0]:.1f}   {p2[1]:.1f} {p2[2]:.1f}  {p4[0]:.1f}   {p4[1]:.1f} {p4[2]:.1f}
"""
    '''
    # 36边形探测器
    detector_str =f"""
    -125 -125 0.000000 0.000000 34.000000 17.000000 0.000000 34.000000 16.741732 2.952019 34.000000
    -125 -125 0.000000 0.000000 34.000000 16.741732 2.952019 34.000000 15.974775 5.814342 34.000000
    -125 -125 0.000000 0.000000 34.000000 15.974775 5.814342 34.000000 14.722432 8.500000 34.000000
    -125 -125 0.000000 0.000000 34.000000 14.722432 8.500000 34.000000 13.022756 10.927389 34.000000
    -125 -125 0.000000 0.000000 34.000000 13.022756 10.927389 34.000000 10.927389 13.022756 34.000000
    -125 -125 0.000000 0.000000 34.000000 10.927389 13.022756 34.000000 8.500000 14.722432 34.000000
    -125 -125 0.000000 0.000000 34.000000 8.500000 14.722432 34.000000 5.814342 15.974775 34.000000
    -125 -125 0.000000 0.000000 34.000000 5.814342 15.974775 34.000000 2.952019 16.741732 34.000000
    -125 -125 0.000000 0.000000 34.000000 2.952019 16.741732 34.000000 0.000000 17.000000 34.000000
    -125 -125 0.000000 0.000000 34.000000 0.000000 17.000000 34.000000 -2.952019 16.741732 34.000000
    -125 -125 0.000000 0.000000 34.000000 -2.952019 16.741732 34.000000 -5.814342 15.974775 34.000000
    -125 -125 0.000000 0.000000 34.000000 -5.814342 15.974775 34.000000 -8.500000 14.722432 34.000000
    -125 -125 0.000000 0.000000 34.000000 -8.500000 14.722432 34.000000 -10.927389 13.022756 34.000000
    -125 -125 0.000000 0.000000 34.000000 -10.927389 13.022756 34.000000 -13.022756 10.927389 34.000000
    -125 -125 0.000000 0.000000 34.000000 -13.022756 10.927389 34.000000 -14.722432 8.500000 34.000000
    -125 -125 0.000000 0.000000 34.000000 -14.722432 8.500000 34.000000 -15.974775 5.814342 34.000000
    -125 -125 0.000000 0.000000 34.000000 -15.974775 5.814342 34.000000 -16.741732 2.952019 34.000000
    -125 -125 0.000000 0.000000 34.000000 -16.741732 2.952019 34.000000 -17.000000 0.000000 34.000000
    -125 -125 0.000000 0.000000 34.000000 -17.000000 0.000000 34.000000 -16.741732 -2.952019 34.000000
    -125 -125 0.000000 0.000000 34.000000 -16.741732 -2.952019 34.000000 -15.974775 -5.814342 34.000000
    -125 -125 0.000000 0.000000 34.000000 -15.974775 -5.814342 34.000000 -14.722432 -8.500000 34.000000
    -125 -125 0.000000 0.000000 34.000000 -14.722432 -8.500000 34.000000 -13.022756 -10.927389 34.000000
    -125 -125 0.000000 0.000000 34.000000 -13.022756 -10.927389 34.000000 -10.927389 -13.022756 34.000000
    -125 -125 0.000000 0.000000 34.000000 -10.927389 -13.022756 34.000000 -8.500000 -14.722432 34.000000
    -125 -125 0.000000 0.000000 34.000000 -8.500000 -14.722432 34.000000 -5.814342 -15.974775 34.000000
    -125 -125 0.000000 0.000000 34.000000 -5.814342 -15.974775 34.000000 -2.952019 -16.741732 34.000000
    -125 -125 0.000000 0.000000 34.000000 -2.952019 -16.741732 34.000000 -0.000000 -17.000000 34.000000
    -125 -125 0.000000 0.000000 34.000000 -0.000000 -17.000000 34.000000 2.952019 -16.741732 34.000000
    -125 -125 0.000000 0.000000 34.000000 2.952019 -16.741732 34.000000 5.814342 -15.974775 34.000000
    -125 -125 0.000000 0.000000 34.000000 5.814342 -15.974775 34.000000 8.500000 -14.722432 34.000000
    -125 -125 0.000000 0.000000 34.000000 8.500000 -14.722432 34.000000 10.927389 -13.022756 34.000000
    -125 -125 0.000000 0.000000 34.000000 10.927389 -13.022756 34.000000 13.022756 -10.927389 34.000000
    -125 -125 0.000000 0.000000 34.000000 13.022756 -10.927389 34.000000 14.722432 -8.500000 34.000000
    -125 -125 0.000000 0.000000 34.000000 14.722432 -8.500000 34.000000 15.974775 -5.814342 34.000000
    -125 -125 0.000000 0.000000 34.000000 15.974775 -5.814342 34.000000 16.741732 -2.952019 34.000000
    -125 -125 0.000000 0.000000 34.000000 16.741732 -2.952019 34.000000 17.000000 0.000000 34.000000
"""

    def read_detector_str(detector_str):
        lines = detector_str.split('\n')
        detector_x = []
        detector_y = []
        detector_z = []
        material1 =[]
        material2 = []
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 11:
                material1.append(int(parts[0]))
                material2.append(int(parts[1]))
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                x1, y1, z1 = float(parts[5]), float(parts[6]), float(parts[7])
                x2, y2, z2 = float(parts[8]), float(parts[9]), float(parts[10])
                #print(x, y, z, x1, y1, z1, x2, y2, z2)

                 # 旋转
                cos_tx = cos_ty = 1.0
                sin_tx = sin_ty = 0.0
                
                # Apply tilts
                if det_tilt_x != 0:
                        tilt_x_rad = math.radians(det_tilt_x)
                        cos_tx = math.cos(tilt_x_rad)
                        sin_tx = math.sin(tilt_x_rad)
                        y_r = y * cos_tx - z * sin_tx
                        z_r = y * sin_tx + z * cos_tx
                        y1_r = y1 * cos_tx - z1 * sin_tx
                        z1_r = y1 * sin_tx + z1 * cos_tx
                        y2_r = y2 * cos_tx - z2 * sin_tx
                        z2_r = y2 * sin_tx + z2 * cos_tx
                        

                        z_r += 34
                        z1_r += 34
                        z2_r += 34

                        x = x * 1e3
                        x1 = x1 * 1e3
                        x2 = x2 * 1e3
                        y = (y_r) * 1e3
                        y1 = (y1_r) * 1e3
                        y2 = (y2_r) * 1e3
                        z = z_r * 1e3
                        z1 = z1_r * 1e3
                        z2 = z2_r * 1e3
                else:
                        x = x * 1e3
                        x1 = x1 * 1e3
                        x2 = x2 * 1e3
                        y = y * 1e3
                        y1 = y1 * 1e3
                        y2 = y2 * 1e3
                        z = z * 1e3
                        z1 = z1 * 1e3
                        z2 = z2 * 1e3

                detector_x.append(x)
                detector_x.append(x1)
                detector_x.append(x2)
                detector_y.append(y)
                detector_y.append(y1)
                detector_y.append(y2)
                detector_z.append(z)
                detector_z.append(z1)
                detector_z.append(z2)
                   
        return material1, material2, detector_x, detector_y, detector_z
    
    material1, material2, detector_x, detector_y, detector_z = read_detector_str(detector_str)
    
    d_xmin, d_xmax = np.min(detector_x), np.max(detector_x)
    d_ymin, d_ymax = np.min(detector_y), np.max(detector_y)
    d_zmin, d_zmax = np.min(detector_z), np.max(detector_z)
    terminator_z = torch.min(v[:, 2]) # 在样品下方放置终止器  
    mirror_ymax = max(ymax, d_ymax) 

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
    output_filename = f'{name}_stl_to_tri_sampleTiltx{sample_tilt_x}_sampleTilty{sample_tilt_y}_sampleTiltNewZ{sample_tilt_new_z}_detTiltx{det_tilt_x}_{faces.size(0)}.tri'
    # 只对输出文件名进行安全处理，确保文件系统兼容性
    safe_output_filename = ''.join(c if c.isalnum() or c in '_-.' else '_' for c in output_filename)
    mesh_path = mesh_path / safe_output_filename
    # 生成网格文件
    with open(mesh_path, 'w') as f:
        for face in faces:
            f.write(
                f"0 -123 {v[face[0], 0]:.2f} {v[face[0], 1]:.2f} {v[face[0], 2]:.2f} {v[face[1], 0]:.2f} {v[face[1], 1]:.2f} {v[face[1], 2]:.2f} {v[face[2], 0]:.2f} {v[face[2], 1]:.2f} {v[face[2], 2]:.2f}\n"
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

    return v, faces, d_zmin, d_zmax, mesh_path, R, v_orig


def generate_mesh_from_voxel(voxel_path, output_path, final_side=1000, tilt_x=0, tilt_y=0, pad_scale=1.0, length=20, reverse=False):  # final_side设置为1000
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
    output_path = sanitize_path(output_path)
    mesh_path = output_path / "mesh"
    mesh_path.mkdir(parents=True, exist_ok=True)
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
    with open(mesh_path / safe_output_filename, 'w') as f:
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

def run_interface(voxel_path, mesh_path, final_side=1000, scale=10, sample_tilt_x=0, sample_tilt_y=0, sample_tilt_new_z=0, det_tilt_x=0, pad_scale=1.0, length=64, reverse=False):  # final_side设置为1000
    """
    运行接口函数，将体素数据转换为网格数据并保存。

    参数:
        voxel_path (Path或str): 体素文件路径，可以是任意文件名（包含空格）
        mesh_path (Path或str): 网格文件保存路径
        side (int): 初始边长
        final_side (int): 最终边长
        length (int): 长度
        tilt_x (float): X轴倾斜角度
        tilt_y (float): Y轴倾斜角度
        reverse (bool): 是否反转体素值
        pad_scale (float): 填充缩放因子

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
        
        # # 确保输出目录存在
        # if not mesh_path.exists():
        #     print(f"创建输出目录: {mesh_path}")
        #     mesh_path.mkdir(parents=True, exist_ok=True)
        
        # 检查文件扩展名，如果是STL文件，则调用STL处理函数
        if str(voxel_path).lower().endswith('.stl'):
            return generate_mesh_from_stl(stl_path=voxel_path, output_path=mesh_path, final_side=final_side, scale=scale, sample_tilt_x=sample_tilt_x, sample_tilt_y=sample_tilt_y, sample_tilt_new_z=sample_tilt_new_z, det_tilt_x = det_tilt_x)
        # else:
        #     return generate_mesh_from_voxel(voxel_path, mesh_path, final_side, sample_tilt_x, sample_tilt_y, pad_scale, length, reverse)
    except Exception as e:
        raise FileNotFoundError(f"处理文件 '{voxel_path}' 时出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    

