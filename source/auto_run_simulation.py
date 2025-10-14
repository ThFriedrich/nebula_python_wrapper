import sys
import os
import json
import matplotlib.pyplot as plt
import pathlib


# 导入现有模块的功能
from sem_simu import run_simulation

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


nebula_path_linux = os.path.join("/home/chenguisen/AISI/nebula/nebula_python_wrapper/source/nebula_gpu")
nebula_path_windows = os.path.join("/home/chenguisen/AISI/nebula/nebula_python_wrapper/source/mynebula.exe")
import platform
nebula_path = pathlib.Path(nebula_path_windows if platform.system() == "Windows" else nebula_path_linux)
pri_file_path = None


stl_dir = "/home/chenguisen/AISI/nebula/simulation_results/FIB_electron"
output_path = pathlib.Path(stl_dir)/'output.det'

#可以指定特定的stl文件，则初始化stl_list为指定的文件路径，则不需要遍历目录
stl_list = []                                    # 存储所有.stl文件的路径;也可以指定特定的stl文件

# 遍历stl_dir目录下的所有文件，如果文件名以.stl结尾，则将其路径添加到stl_list中
for file in os.listdir(stl_dir):
    if file.endswith('.stl'):
        stl_path = os.path.join(stl_dir, file)
        stl_list.append(stl_path)        
        print(stl_path)





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

    # 模拟参数
    tri_paras = {
        'stl_path': stl_path,
        'mesh_path': mesh_path,
        'beam_type': 'fib',     # 'fib' or 'sem'  fib和sem与大小写无关 FIB离子束成像，SEM电子束成像,通过该参数，使得模拟逻辑与实验一致
        'sample_tilt_x': 0,
        'sample_tilt_y': 0,
        'det_tilt_x': 76.8,         # 0 or 76.8 # 当为SEM电子束成像时，需要设置为76.8
        'rotate_angle_start': 0,
        'rotate_angle_stop': 360,
        'rotate_angle_step': 360,
    }

    pri_paras = {
        'pri_dir': stl_dir,
        'pixel_size': 2,  # 像素大小，单位为nm
        'energy': 500,    # 电子束能量，单位：eV
        'epx': 500,       # 每像素电子数
        'sigma': 1.0,     # 高斯模糊参数，默认为1.0
        'poisson': True,   # 泊松分布，默认为True
        'roi_array': [-256, 255, -256, 255],  # [roi_x_min, roi_x_max, roi_y_min, roi_y_max]，如果为None，则模拟整个模型
    }
    # mat_paths_list = [
    #     os.path.join(src_path, 'simulator/materials/silicon.mat')
    # ]
    mat_paths_list = [
    "/home/chenguisen/AISI/nebula/data/silicon.mat"
    ]

    
    nebula_paras = {
    'nebula_path': nebula_path,
    'output_path': output_path,
    'plot': True,   # 是否显示图像，默认为False
    'save': True,   # 是否保存图像，默认为True
    }

    # 运行模拟
    run_simulation(nebula_paras, tri_paras, pri_paras, mat_paths_list)