import cv2
import numpy as np

def rotation_matrix(tilt_x: float = 0, tilt_y: float = 0, rotate_angle: float = 0) -> np.ndarray:
    """
    计算绕指定轴的旋转矩阵。
    
    参数:
        tilt_x (float): 绕 X 轴的旋转角度（度）。
        tilt_y (float): 绕 Y 轴的旋转角度（度）。
        rotate_angle (float): 绕旋转轴的旋转角度（度）。
    
    返回:
        np.ndarray: 3x3 旋转矩阵。
    """
    # 样品绕x轴旋转
    tilt_x_rad = np.radians(tilt_x)
    cos_tx = np.cos(tilt_x_rad)
    sin_tx = np.sin(tilt_x_rad)

    # 样品绕y轴旋转
    tilt_y_rad = np.radians(tilt_y)
    cos_ty = np.cos(tilt_y_rad)
    sin_ty = np.sin(tilt_y_rad)

    # 定义旋转轴方向（单位向量）
    if tilt_x != 0:
        rotation_axis = np.array([0, -sin_tx, cos_tx], dtype=np.float32)
    elif tilt_y != 0:
        rotation_axis = np.array([sin_ty, 0, cos_ty], dtype=np.float32)
    else:
        rotation_axis = np.array([0, 0, 1], dtype=np.float32)

    # 归一化旋转轴（确保是单位向量）
    rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

    # 定义旋转角度（例如45度）
    rotation_angle_rad = np.radians(rotate_angle)

    # 构建旋转向量（方向为旋转轴，长度为旋转角度）
    rotation_vector = rotation_axis * rotation_angle_rad

    # 转换为旋转矩阵
    rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
    return rotation_matrix

import torch
if __name__ == "__main__":
    xmax = 300
    xmin = -300
    ymax = 300
    ymin = -300
    base_z = 0
    v = torch.tensor([
        [xmax, ymin, base_z],
        [xmin, ymin, base_z],
        [xmax, ymax, base_z],
        [xmin, ymax, base_z]
    ], dtype=torch.float32)
    print("原始点坐标:")
    print(v)

    tilt_x_rad = torch.tensor(np.radians(55), dtype=torch.float32)
    cos_tx = torch.cos(tilt_x_rad)
    sin_tx = torch.sin(tilt_x_rad)
    y = v[:, 1] * cos_tx - v[:, 2] * sin_tx
    z = v[:, 1] * sin_tx + v[:, 2] * cos_tx
    v[:, 1] = y
    v[:, 2] = z

    R = torch.tensor(rotation_matrix(tilt_x=55, rotate_angle=45), dtype=torch.float32).to('cuda' if torch.cuda.is_available() else 'cpu')
    points = torch.stack([v[:, 0], v[:, 1], v[:, 2]], dim=1).to(R.device)
    rotated_points = torch.mm(points, R.T)  # 矩阵乘法
    print("绕x轴旋转后点坐标:")
    print(v)
    print("旋转后的点坐标:")
    print(rotated_points)
    xmax = rotated_points[:, 0].max()
    xmin = rotated_points[:, 0].min()
    ymax = rotated_points[:, 1].max()
    ymin = rotated_points[:, 1].min()
    print(xmax, xmin, ymax, ymin)
    print(R)