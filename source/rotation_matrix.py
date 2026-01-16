import cv2
import numpy as np

def rotation_matrix(tilt_x: float = 0, tilt_y: float = 0, rotate_angle: float = 0) -> np.ndarray:
    """
    CalculateRotationmatrix。
    
    parameters:
        tilt_x (float): around X axisrotation angledegrees（degrees）。
        tilt_y (float): around Y axisrotation angledegrees（degrees）。
        rotate_angle (float): aroundRotationaxisrotation angledegrees（degrees）。
    
    Returns:
        np.ndarray: 3x3 Rotationmatrix。
    """
    # 样品aroundxaxisRotation
    tilt_x_rad = np.radians(tilt_x)
    cos_tx = np.cos(tilt_x_rad)
    sin_tx = np.sin(tilt_x_rad)

    # 样品aroundyaxisRotation
    tilt_y_rad = np.radians(tilt_y)
    cos_ty = np.cos(tilt_y_rad)
    sin_ty = np.sin(tilt_y_rad)

    # 定义Rotationaxis方to（单位to量）
    if tilt_x != 0:
        rotation_axis = np.array([0, -sin_tx, cos_tx], dtype=np.float32)
    elif tilt_y != 0:
        rotation_axis = np.array([sin_ty, 0, cos_ty], dtype=np.float32)
    else:
        rotation_axis = np.array([0, 0, 1], dtype=np.float32)

    # 归一化Rotationaxis（确保是单位to量）
    rotation_axis = rotation_axis / np.linalg.norm(rotation_axis)

    # 定义rotation angledegrees（For example45degrees）
    rotation_angle_rad = np.radians(rotate_angle)

    # 构建Rotationto量（方to为Rotationaxis，长degrees为rotation angledegrees）
    rotation_vector = rotation_axis * rotation_angle_rad

    # 转换为Rotationmatrix
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
    rotated_points = torch.mm(points, R.T)  # matrix乘法
    print("aroundxaxisRotation后点坐标:")
    print(v)
    print("Rotation后of点坐标:")
    print(rotated_points)
    xmax = rotated_points[:, 0].max()
    xmin = rotated_points[:, 0].min()
    ymax = rotated_points[:, 1].max()
    ymin = rotated_points[:, 1].min()
    print(xmax, xmin, ymax, ymin)
    print(R)