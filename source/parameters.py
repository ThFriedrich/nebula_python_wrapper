import numpy as np
from voxel_to_mesh import run_interface
from sem_pri import generate_sem_pri_data
import os
class tri_parameters:
    def __init__(self, stl_path, mesh_path, sample_tilt_x, sample_tilt_y, sample_tilt_new_z, det_tilt_x):
        """
        初始化 .tri 文件生成所需的参数。

        Attributes:
            stl_path (pathlib.Path): 输入 STL 文件的路径。
            mesh_path (pathlib.Path): 输出 .tri 文件的路径。
            beam_type (str): 光束类型。
            sample_tilt_x (float): 样品在 X 轴上的倾斜角度。
            sample_tilt_new_z (float): 样品在 Z 轴上的新倾斜角度。
            det_tilt_x (float): 探测器在 X 轴上的倾斜角度。
        """
        self.stl_path = stl_path
        self.mesh_path = mesh_path
        self.scale = 10
        self.sample_tilt_x = sample_tilt_x
        self.sample_tilt_y = sample_tilt_y  # 样品绕y轴旋转的角度，暂时设为和x轴相同
        self.sample_tilt_new_z = sample_tilt_new_z
        self.det_tilt_x = det_tilt_x


    def run(self):
        return run_interface(
                    voxel_path=self.stl_path, 
                    mesh_path=self.mesh_path,
                    scale=self.scale, 
                    sample_tilt_x=self.sample_tilt_x,
                    sample_tilt_y=self.sample_tilt_y, 
                    sample_tilt_new_z=self.sample_tilt_new_z,
                    det_tilt_x=self.det_tilt_x
                    )

class pri_parameters:
    """
    初始化 .pri 文件生成所需的参数。

    Attributes:
        mesh_path (pathlib.Path): 输出 .pri 文件的路径。
        pixel_size (float): 像素大小。
        energy (float): 能量值。
        epx (float): EPX 参数。
        sigma (float): Sigma 参数。
        poisson (bool): 是否启用泊松分布。
        use_roi (bool): 是否启用 ROI（感兴趣区域）。
        roi_x_min (float): ROI 的 X 轴最小值。
        roi_x_max (float): ROI 的 X 轴最大值。
        roi_y_min (float): ROI 的 Y 轴最小值。
        roi_y_max (float): ROI 的 Y 轴最大值。
        d_zmin (float): Z 轴最小值。
        d_zmax (float): Z 轴最大值。
    """
    def __init__(self, pri_dir, pixel_size, energy, epx, sigma, poisson,
                 roi_x_min, roi_x_max, roi_y_min, roi_y_max, d_zmin, d_zmax):
        
        self.pri_dir = pri_dir
        self.pixel_size = pixel_size
        self.energy = energy
        self.epx = epx
        self.sigma = sigma
        self.poisson = poisson
        self.roi_x_min = roi_x_min
        self.roi_x_max = roi_x_max
        self.roi_y_min = roi_y_min
        self.roi_y_max = roi_y_max
        self.d_zmin = d_zmin
        self.d_zmax = d_zmax

    def run(self):
        # 计算像素数量
            x_pixel_num = int((np.abs(self.roi_x_max)+np.abs(self.roi_x_min))/self.pixel_size+1)
            y_pixel_num = int((np.abs(self.roi_y_max)+np.abs(self.roi_y_min))/self.pixel_size+1)
            
            print(f"像素数量: {x_pixel_num} x {y_pixel_num}")
            
            # 生成像素坐标
            xpx = np.linspace(self.roi_x_min, self.roi_x_max, x_pixel_num)
            ypx = np.linspace(self.roi_y_min, self.roi_y_max, y_pixel_num)
            
            # 设置束入射方向
            beam_incident_dir = np.array([0, 0, -1])
            
            print(f"束入射方向: {beam_incident_dir}")
            
            # 生成.pri文件
            pri_file_path = os.path.join(self.pri_dir, 'sem.pri')



            # 计算束的z位置，使用tri类传出的d_zmax和d_zmin值
            beam_zmax = (self.d_zmax + self.d_zmin) / 2
            print(f"束z位置: {beam_zmax}")
            
            generate_sem_pri_data(
                z=beam_zmax,  # 使用tri类传出的d_zmax值计算的beam_zmax
                xpx=xpx,
                ypx=ypx,
                energy=self.energy,
                epx=self.epx,
                sigma=self.sigma,
                poisson=self.poisson,
                dx=beam_incident_dir[0],
                dy=beam_incident_dir[1],
                dz=beam_incident_dir[2],
                file_path=pri_file_path
            )
            
            print(f"生成.pri文件成功，路径: {pri_file_path}")
            
            return pri_file_path

           