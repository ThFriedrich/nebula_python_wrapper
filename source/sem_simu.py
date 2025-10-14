import platform
import os
import json
import matplotlib.pyplot as plot
import pathlib
import torch

# 导入现有模块的功能
from parameters import tri_parameters, pri_parameters
from run_nebula import nebula_gpu
from save_parameters import add_frame_to_parameters, save_parameters

import numpy as np

def run_simulation(nebula_paras, tri_paras, pri_paras, mat_paths_list):
    simu_result = None
    sample_tilt_x = tri_paras['sample_tilt_x']
    # 将模拟上的逻辑转换到实验上，使得参数设置与实验一致
    if 'fib' in tri_paras['beam_type'].lower():
        # FIB离子束成像，参数的设定
        tri_paras['sample_tilt_x'] = 55 - sample_tilt_x
        tri_paras['det_tilt_x'] = 0
        pass
    elif 'sem' in tri_paras['beam_type'].lower():
        # SEM电子束成像，探测器默认76.8,这里的倾转角在不同设备上可能不同
        tri_paras['det_tilt_x'] = 76.8


    # 获取旋转角度. 如果stop = step，则只旋转一次
    rotate_angle_start = tri_paras['rotate_angle_start']
    rotate_angle_stop = tri_paras['rotate_angle_stop']
    rotate_angle_step = tri_paras['rotate_angle_step']
    rotate_angle_list = np.arange(rotate_angle_start, rotate_angle_stop, rotate_angle_step)
    # 遍历旋转角度
    for rotate_angle in rotate_angle_list:
        print(f"rotate_angle: {rotate_angle}",'\n\n')
        # 生成.tri文件
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
        print(f".tri 文件已生成，路径: {tri_file_path}")

        if rotate_angle == rotate_angle_start:

            roi_array = pri_paras['roi_array']
            print(f"设定 roi_array: {roi_array}")
            if roi_array is None:
                # 计算像素范围
                x_min = int(torch.floor(torch.min(v[:, 0])).item())
                x_max = int(torch.ceil(torch.max(v[:, 0])).item())   
                y_min = int(torch.floor(torch.min(v[:, 1])).item())
                y_max = int(torch.ceil(torch.max(v[:, 1])).item())
                roi_array = [x_min, x_max, y_min, y_max]
                print(f"roi_array: {roi_array}")

            PRI = pri_parameters(
                pri_dir=pri_paras['pri_dir'],  # 输出 .pri 文件的路径
                pixel_size=pri_paras['pixel_size'],  # 像素大小，单位为nm
                energy=pri_paras['energy'],
                epx=pri_paras['epx'],       # 每像素电子数
                sigma=pri_paras['sigma'],    # 高斯模糊参数，默认为1.0
                poisson=pri_paras['poisson'],
                roi_x_min=roi_array[0],  # 这里的roi设置也可以设置为模型的尺寸范围
                roi_x_max=roi_array[1],  
                roi_y_min=roi_array[2],
                roi_y_max=roi_array[3],
                d_zmin=d_zmin,
                d_zmax=d_zmax,
            )
            pri_file_path = PRI.run()
            if pri_file_path is None:
                raise ValueError("生成 .pri 文件失败，路径为 None")
            
        print(f".pri 文件已生成，路径: {pri_file_path}")

        print("tri_paras:", tri_paras)
        print("pri_paras:", pri_paras)
 

        # 将mat_paths_list中的路径直接用空格分隔，不使用shlex.quote
        mat_paths_quoted = " ".join(str(path) for path in mat_paths_list)

        nebula_path = nebula_paras['nebula_path']
        output_path = nebula_paras['output_path']

        # 检查路径是否存在
        if not pathlib.Path(nebula_path).is_file():
            raise FileNotFoundError(f"可执行文件 {nebula_path} 不存在")
        if not pathlib.Path(tri_file_path).exists():
            raise FileNotFoundError(f"文件 {tri_file_path} 不存在")
        if not pathlib.Path(pri_file_path).exists():
            raise FileNotFoundError(f"文件 {pri_file_path} 不存在")



        # 适配多平台，保持原有命令格式 "nebula_gpu sem.tri sem.pri silicon.mat pmma.mat > output.det"
        if platform.system() == "Windows":
            # Windows 下使用 cmd /c 执行重定向
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
            print(f"[提示] 尝试直接在终端中运行命令: {command}")
            raise
        #NEBULA.show_image(plot=False, save=True)
        print(f"图像已保存至: {image_path}")

        # # 将 R 转换为 list 或其他可序列化的类型
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
                    "rotation": json.dumps(R),   #旋转
                    "translation": json.dumps([0.0, 0.0, 0.0]) #平移
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

    # 创建相机参数保存路径
    parameters_path = os.path.join(mesh_path, "camera_parameters.json")
    save_parameters(parameters, parameters_path)
    print(f"相机参数已保存至: {parameters_path}")
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
                "image_path": str(image_path),  # 保存图像的路径
                "rotation": json.dumps(R),      #旋转
                "translation": json.dumps([0.0, 0.0, 0.0]), #平移
                "width": roi_array[1] - roi_array[0] + 1,  # 512
                "height": roi_array[3] - roi_array[2] + 1,  # 512
                "cx": (roi_array[1] - roi_array[0] + 1) / 2,  # 256.0
                "cy": (roi_array[3] - roi_array[2] + 1) / 2,  # 256.0
            }
    }
    return simu_result
