import platform
import os
import json
import matplotlib.pyplot as plot
import pathlib
import torch

# Import functionality from existing modules
from parameters import tri_parameters, pri_parameters
from run_nebula import nebula_gpu
from save_parameters import add_frame_to_parameters, save_parameters

import numpy as np

def run_simulate(nebula_paras, tri_paras, pri_paras, mat_paths_list):
    simu_result = None
    sample_tilt_x = tri_paras['sample_tilt_x']
    # Convertsimulate上of逻辑转换to实验上，makingparametersSet与实验一致
    if 'fib' in tri_paras['beam_type'].lower():
        # FIBIon beam imaging，parameterssettings
        tri_paras['sample_tilt_x'] = 55 - sample_tilt_x
        tri_paras['det_tilt_x'] = 0
        pass
    elif 'sem' in tri_paras['beam_type'].lower():
        # SEMElectron beam imaging，Detector default76.8,tilt angle here may vary on different devices
        tri_paras['det_tilt_x'] = 76.8


    # Getrotation angledegrees. ifstop = step，then onlyRotationonce
    rotate_angle_start = tri_paras['rotate_angle_start']
    rotate_angle_stop = tri_paras['rotate_angle_stop']
    rotate_angle_step = tri_paras['rotate_angle_step']
    rotate_angle_list = np.arange(rotate_angle_start, rotate_angle_stop, rotate_angle_step)
    # Iterate throughrotation angledegrees
    for rotate_angle in rotate_angle_list:
        print(f"rotate_angle: {rotate_angle}",'\n\n')
        # generation.trifile
        stl_path = pathlib.Path(tri_paras['stl_path'])
        mesh_path = pathlib.Path(tri_paras['mesh_path'])
        TRI = tri_parameters(
            stl_path=stl_path,
            mesh_path=mesh_path,
            sample_tilt_x=tri_paras['sample_tilt_x'],
            sample_tilt_y=tri_paras['sample_tilt_y'],
            sample_tilt_new_z=rotate_angle,
            det_tilt_x=tri_paras['det_tilt_x'],  # 0 or 76.8
        )
        v, d_zmin, d_zmax, tri_file_path, R = TRI.run()
        print(f"R: {R}")
        print(f".tri file已generation，path: {tri_file_path}")

        if rotate_angle == rotate_angle_start:

            roi_array = pri_paras['roi_array']
            print(f"设定 roi_array: {roi_array}")
            if roi_array is None:
                # 计算pixels范围
                x_min = int(torch.floor(torch.min(v[:, 0])).item())
                x_max = int(torch.ceil(torch.max(v[:, 0])).item())   
                y_min = int(torch.floor(torch.min(v[:, 1])).item())
                y_max = int(torch.ceil(torch.max(v[:, 1])).item())
                roi_array = [x_min, x_max, y_min, y_max]
                print(f"roi_array: {roi_array}")

            PRI = pri_parameters(
                pri_dir=pri_paras['pri_dir'],  # output .pri fileofpath
                pixel_size=pri_paras['pixel_size'],  # pixels大小，单位为nm
                energy=pri_paras['energy'],
                epx=pri_paras['epx'],       # 每pixels电子数
                sigma=pri_paras['sigma'],    # 高斯模糊parameters，default1.0
                poisson=pri_paras['poisson'],
                roi_x_min=roi_array[0],  # 这里ofroiSet也可以Set为模型of尺寸范围
                roi_x_max=roi_array[1],  
                roi_y_min=roi_array[2],
                roi_y_max=roi_array[3],
                d_zmin=d_zmin,
                d_zmax=d_zmax,
            )
            pri_file_path = PRI.run()
            if pri_file_path is None:
                raise ValueError("generation .pri file失败，path为 None")
            
        print(f".pri file已generation，path: {pri_file_path}")

        print("tri_paras:", tri_paras)
        print("pri_paras:", pri_paras)
 

        # Convertmat_paths_list中ofpath直接用空格分隔，不使用shlex.quote
        mat_paths_quoted = " ".join(str(path) for path in mat_paths_list)

        nebula_path = nebula_paras['nebula_path']
        output_path = nebula_paras['output_path']

        # 检查path是否存on
        if not pathlib.Path(nebula_path).is_file():
            raise FileNotFoundError(f"可执行file {nebula_path} 不存on")
        if not pathlib.Path(tri_file_path).exists():
            raise FileNotFoundError(f"file {tri_file_path} 不存on")
        if not pathlib.Path(pri_file_path).exists():
            raise FileNotFoundError(f"file {pri_file_path} 不存on")



        # 适配多平台，保持原有命令格式 "nebula_gpu sem.tri sem.pri silicon.mat pmma.mat > output.det"
        if platform.system() == "Windows":
            # Windows 下使用 cmd /c 执行重定to
            command = f'"{nebula_path}" "{tri_file_path}" "{pri_file_path}" {mat_paths_quoted} > "{output_path}"'
        else:
            # Linux/Mac 下使用相同格式
            command = f'"{nebula_path}" "{tri_file_path}" "{pri_file_path}" {mat_paths_quoted} > "{output_path}"'
        
        print(f"运行命令: {command}")
        image_path = pathlib.Path(f"{tri_file_path}").with_suffix(".png")
        
        try:
            print(f"[DEBUG] 完整命令: {command}")
            NEBULA = nebula_gpu(
                command=command,
                sem_simu_result=output_path,
                image_path=image_path,
                plot=nebula_paras['plot'],
                save=nebula_paras['save'],
            )
            NEBULA.run()
        except Exception as e:
            print(f"[ERROR] 调用 nebula_gpu 时发生异常: {e}")
            print(f"[提示] 尝试直接on终端中运行命令: {command}")
            raise
        #NEBULA.show_image(plot=False, save=True)
        print(f"图像已保存至: {image_path}")

        # # Convert R 转换为 list 或其他可序列化of类型
        if hasattr(R, 'tolist'):
            R = R.tolist()
        if rotate_angle == rotate_angle_start:
            parameters = {
                "camera": {
                    "width": roi_array[1] - roi_array[0] + 1,  # 512
                    "height": roi_array[3] - roi_array[2] + 1,  # 512
                    "cx": (roi_array[1] - roi_array[0] + 1) / 2,  # 256.0
                    "cy": (roi_array[3] - roi_array[2] + 1) / 2,  # 256.0
                },
                "frames": [
                    {
                    "file_path": str(image_path),
                    "rotation": json.dumps(R),   #Rotation
                    "translation": json.dumps([0.0, 0.0, 0.0]) #translation
                    },
                ]
            }
        else:
            # 添加新帧
            parameters = add_frame_to_parameters(
                parameters,
                str(image_path),
                json.dumps(R),
                json.dumps([0.0, 0.0, 0.0])
            )

    # Create相机parameters保存path
    parameters_path = os.path.join(mesh_path, "camera_parameters.json")
    save_parameters(parameters, parameters_path)
    print(f"相机parameters已保存至: {parameters_path}")
    #return write_result(energy, roi_array, R, image_path)


def write_result(energy, roi_array, R, image_path):
    simu_result = {
            "type": "SimulationNode",
            "template": "recipe/node/template/acquire_image_template.yaml",
            "node_name": "SemFibSimuNode",
            "parameters": {
                "x0": "{{IonDepositionNode(4).result.parameters.rec_settings.CenterX * 1.0e6 }}",
                "y0": "{{IonDepositionNode(4).result.parameters.rec_settings.CenterY * 1.0e6 }}",
                "z0": "{{IonDepositionNode(4).result.parameters.rec_settings.Depth / 2 * 1.0e6}}",
                "x_size": "{{IonDepositionNode(4).result.parameters.rec_settings.Width * 1.0e6}}",
                "y_size": "{{IonDepositionNode(4).result.parameters.rec_settings.Height * 1.0e6}}",
                "z_size": "{{IonDepositionNode(4).result.parameters.rec_settings.Depth * 1.0e6}}",

                "energy": energy,               # 能量, eV
                "image_path": str(image_path),  # 保存图像ofpath
                "rotation": json.dumps(R),      #Rotation
                "translation": json.dumps([0.0, 0.0, 0.0]), #translation
                "width": roi_array[1] - roi_array[0] + 1,  # 512
                "height": roi_array[3] - roi_array[2] + 1,  # 512
                "cx": (roi_array[1] - roi_array[0] + 1) / 2,  # 256.0
                "cy": (roi_array[3] - roi_array[2] + 1) / 2,  # 256.0
            }
    }
    return simu_result
