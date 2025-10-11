import sys
import os
import json
import matplotlib.pyplot as plt
import pathlib
import torch

# 导入现有模块的功能
from parameters import tri_parameters, pri_parameters
from run_nebula import nebula_gpu
from save_parameters import add_frame_to_parameters, save_parameters
import numpy as np

# 这个脚本用于自动化运行nebula_gpu模拟,用于不同倾转角度参数的模拟
# 主要步骤包括：
# 1. 设置参数
# 2. 生成.tri文件和.pri文件
# 3. 运行nebula_gpu模拟
# 4. 分析模拟结果
# 5. 保存模拟结果
# 6. 分析模拟结果
# 7. 保存模拟结果图像
# 8. 保存相机参数

# 生成.tri文件和.pri文件的函数
# 默认示例


# 离子束成像
# 探测器的倾转角常见的有55度、52度。
# 此时离子束发射方向相对探测器平面是垂直的。
# 此时，离子束成像就转换为探测器的倾转角为0度的成像情况，离子束反射方向也变为沿z轴。
# 一般情况下，用离子束成像时，样品倾转角和探测器倾转角是相同的，也即样品不用倾转；当然，样品也可以随意倾转。



# 电子束成像
# 探测器的倾转角为76.8度
# 电子束的入射方向是固定的，沿z轴方向，即电子束的倾转角为0度。
# 样品则可以随意倾转。


# 总之，电子束和离子束都不用倾转。


mat_paths_list =[pathlib.Path('/home/chenguisen/AISI/nebula/data/silicon.mat')]

nebula_gpu_path = "/home/chenguisen/AISI/nebula/nebula_python_wrapper/source/nebula_gpu"
import platform
#nebula_gpu_path = pathlib.Path("D:/AISI/ZZZ/nebula_python_wrapper/source/mynebula.exe" if platform.system() == "Windows" else "mynebula")

pri_file_path = None


stl_dir = "/home/chenguisen/AISI/nebula/simulation_results"
output_path = pathlib.Path(stl_dir)/'output.det'

#可以指定特定的stl文件，则初始化stl_list为指定的文件路径，则不需要遍历目录
stl_list = []                                    # 存储所有.stl文件的路径;也可以指定特定的stl文件

# 遍历stl_dir目录下的所有文件，如果文件名以.stl结尾，则将其路径添加到stl_list中
for file in os.listdir(stl_dir):
    if file.endswith('.stl'):
        stl_path = os.path.join(stl_dir, file)
        stl_list.append(stl_path)        
        print(stl_path)


rotate_angle_start = 0  # 绕x轴旋转旋转一定角度后，以样品新的法线方向为轴的旋转角度,单位为度
rotate_angle_stop = 10  # 旋转终止角度  如果stop = step，则只旋转一次
rotate_angle_step = 10  # 旋转步长
rotate_angle_list = np.arange(rotate_angle_start, rotate_angle_stop, rotate_angle_step)
roi_array = [-256, 255, -456, 55]  # [roi_x_min, roi_x_max, roi_y_min, roi_y_max]
sample_tilt_x = -55  # 样品绕x轴旋转的角度
pixel_size = 2  # 像素大小，单位为nm
energy = 500  # 电子束能量，单位：eV
epx = 500  # 每像素电子数


for stl_path in stl_list:
    stl_path = pathlib.Path(stl_path)
    file_name = stl_path.name
    file_name_no_ext = file_name.split('.')[0]
    
    # 创建保存路径
    save_dir = os.path.join(os.path.dirname(stl_path), file_name_no_ext)
    os.makedirs(save_dir, exist_ok=True)
    
    # 创建相机参数保存路径
    parameters_path = os.path.join(save_dir, "camera_parameters.json")


    mesh_path = save_dir
    print(f"stl_path: {stl_path}",'\n')
    print(f"mesh_path: {mesh_path}",'\n')


    for rotate_angle in rotate_angle_list:
        print(f"rotate_angle: {rotate_angle}",'\n\n')
        # 生成.tri文件
        TRI = tri_parameters(
            stl_path=stl_path,
            mesh_path=mesh_path,
            beam_type='ion',  # 'ion' or 'electron'
            sample_tilt_x=sample_tilt_x,
            sample_tilt_y=0,
            sample_tilt_new_z=rotate_angle,
            det_tilt_x=0,  # 0 or 76.8
        )
        v, faces, d_zmin, d_zmax, tri_file_path, R = TRI.run()
        print(f"R: {R}")
        print(f".tri 文件已生成，路径: {tri_file_path}")

        if rotate_angle == rotate_angle_start:

            # 计算像素范围
            x_min = int(torch.floor(torch.min(v[:, 0])).item())
            x_max = int(torch.ceil(torch.max(v[:, 0])).item())   
            y_min = int(torch.floor(torch.min(v[:, 1])).item())
            y_max = int(torch.ceil(torch.max(v[:, 1])).item())
            roi_array = [x_min, x_max, y_min, y_max]
            print(f"roi_array: {roi_array}")

            PRI = pri_parameters(
                pri_dir=stl_dir,  # 输出 .pri 文件的路径
                pixel_size=pixel_size,  # 像素大小，单位为nm
                energy=energy,
                epx=epx,       # 每像素电子数
                sigma=1.0,    # 高斯模糊参数，默认为1.0
                poisson=True,
                roi_x_min=roi_array[0],  # 这里的roi设置也可以设置为模型的尺寸范围
                roi_x_max=roi_array[1],  # 这里的roi_x_max和roi_y_max要大于0.5，否则会报错
                roi_y_min=roi_array[2],
                roi_y_max=roi_array[3],
                d_zmin=d_zmin,
                d_zmax=d_zmax,
            )
            pri_file_path = PRI.run()
            if pri_file_path is None:
                raise ValueError("生成 .pri 文件失败，路径为 None")
            
        print(f".pri 文件已生成，路径: {pri_file_path}")
            
        # 将mat_paths_list中的路径直接用空格分隔，不使用shlex.quote
        mat_paths_quoted = " ".join(str(path) for path in mat_paths_list)
        import shlex
        import pathlib

        # 检查路径是否存在
        if not pathlib.Path(nebula_gpu_path).is_file():
            raise FileNotFoundError(f"可执行文件 {nebula_gpu_path} 不存在")
        if not pathlib.Path(tri_file_path).exists():
            raise FileNotFoundError(f"文件 {tri_file_path} 不存在")
        if not pathlib.Path(pri_file_path).exists():
            raise FileNotFoundError(f"文件 {pri_file_path} 不存在")



        # 适配多平台，保持原有命令格式 "nebula_gpu sem.tri sem.pri silicon.mat pmma.mat > output.det"
        if platform.system() == "Windows":
            # Windows 下使用 cmd /c 执行重定向
            command = f'"{nebula_gpu_path}" "{tri_file_path}" "{pri_file_path}" {mat_paths_quoted} > "{output_path}"'
        else:
            # Linux/Mac 下使用相同格式
            command = f'"{nebula_gpu_path}" "{tri_file_path}" "{pri_file_path}" {mat_paths_quoted} > "{output_path}"'
        
        print(f"运行命令: {command}")
        image_path = pathlib.Path(f"{tri_file_path}").with_suffix(".png")
        
        try:
            print(f"[DEBUG] 完整命令: {command}")
            NEBULA = nebula_gpu(
                command=command,
                sem_simu_result=output_path,
                image_path=image_path,
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



    save_parameters(parameters, parameters_path)
    print(f"相机参数已保存至: {parameters_path}")



