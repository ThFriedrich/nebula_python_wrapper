import numpy as np
from voxel_to_mesh import run_interface
from sem_pri import generate_sem_pri_data
import os
class tri_parameters:
    def __init__(self, stl_path, mesh_path, sample_tilt_x, sample_tilt_y, sample_tilt_new_z, det_tilt_x):
        """
        Initialize .tri filegeneration所需ofparameters。

        Attributes:
            stl_path (pathlib.Path): input STL fileofpath。
            mesh_path (pathlib.Path): output .tri fileofpath。
            beam_type (str): Beam type。
            sample_tilt_x (float): 样品on X axis上of倾斜角degrees。
            sample_tilt_new_z (float): 样品on Z axis上of新倾斜角degrees。
            det_tilt_x (float): 探测器on X axis上of倾斜角degrees。
        """
        self.stl_path = stl_path
        self.mesh_path = mesh_path
        self.scale = 10
        self.sample_tilt_x = sample_tilt_x
        self.sample_tilt_y = sample_tilt_y  # 样品aroundyaxisRotationof角degrees，暂时设为和xaxis相同
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
    Initialize .pri filegeneration所需ofparameters。

    Attributes:
        mesh_path (pathlib.Path): output .pri fileofpath。
        pixel_size (float): pixels大小。
        energy (float): 能量值。
        epx (float): EPX parameters。
        sigma (float): Sigma parameters。
        poisson (bool): 是否Enable泊松分布。
        use_roi (bool): 是否Enable ROI（感兴趣区域）。
        roi_x_min (float): ROI of X axis最小值。
        roi_x_max (float): ROI of X axis最大值。
        roi_y_min (float): ROI of Y axis最小值。
        roi_y_max (float): ROI of Y axis最大值。
        d_zmin (float): Z axis最小值。
        d_zmax (float): Z axis最大值。
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
        # 计算pixels数量
            x_pixel_num = int((np.abs(self.roi_x_max)+np.abs(self.roi_x_min))/self.pixel_size+1)
            y_pixel_num = int((np.abs(self.roi_y_max)+np.abs(self.roi_y_min))/self.pixel_size+1)
            
            print(f"pixels数量: {x_pixel_num} x {y_pixel_num}")
            
            # generationpixels坐标
            xpx = np.linspace(self.roi_x_min, self.roi_x_max, x_pixel_num)
            ypx = np.linspace(self.roi_y_min, self.roi_y_max, y_pixel_num)
            
            # Set束入射方to
            beam_incident_dir = np.array([0, 0, -1])
            
            print(f"束入射方to: {beam_incident_dir}")
            
            # generation.prifile
            pri_file_path = os.path.join(self.pri_dir, 'sem.pri')



            # 计算束ofz位置，使用tri类传出ofd_zmax和d_zmin值
            beam_zmax = (self.d_zmax + self.d_zmin) / 2
            print(f"束z位置: {beam_zmax}")
            
            generate_sem_pri_data(
                z=beam_zmax,  # 使用tri类传出ofd_zmax值计算ofbeam_zmax
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
            
            print(f"generation.prifile成功，path: {pri_file_path}")
            
            return pri_file_path

           