import sys
import os
import json
import matplotlib.pyplot as plt
import pathlib


# Import functionality from existing modules
from sem_simu import run_simulate

# This script is used to automate runningnebula_gpusimulate,用于不同倾转角degreesparametersofsimulate
# Main steps include：
# 1. Setparameters
# 2. generation.trifile和.prifile
# 3. 运行nebula_gpusimulate
# 4. 分析simulate结果
# 5. 保存simulate结果
# 6. 分析simulate结果
# 7. 保存simulate结果图像
# 8. 保存相机parameters

# generation.trifile和.prifilefunction
# 默认示例


# Ion beam imaging
# 探测器of倾转角常见of有55degrees、52degrees。
# 此时离子束发射方to相对探测器平面是垂直of。
# 此时，Ion beam imaging就转换为探测器of倾转角为0degreesof成像情况，离子束反射方to也变为沿zaxis。
# 一般情况下，用Ion beam imaging时，样品倾转角和探测器倾转角是相同of，也即样品不用倾转；当然，样品也可以随意倾转。



# Electron beam imaging
# 探测器of倾转角为76.8degrees
# 电子束of入射方to是固定of，沿zaxis方to，即电子束of倾转角为0degrees。
# 样品则可以随意倾转。


# 总之，电子束和离子束都不用倾转。


nebula_path_linux = os.path.join("/home/chenguisen/AISI/nebula/nebula_python_wrapper/source/nebula_gpu")
nebula_path_windows = os.path.join("/home/chenguisen/AISI/nebula/nebula_python_wrapper/source/mynebula.exe")
import platform
nebula_path = pathlib.Path(nebula_path_windows if platform.system() == "Windows" else nebula_path_linux)
pri_file_path = None


stl_dir = "/home/chenguisen/AISI/nebula/simulate_results/FIB_electron"
output_path = pathlib.Path(stl_dir)/'output.det'

#可以指定特定ofstlfile，则Initializestl_list为指定offilepath，则不需要Iterate throughdirectory
stl_list = []                                    # 存储所有.stlfileofpath;也可以指定特定ofstlfile

# Iterate throughstl_dirdirectory下of所有file，iffilename以.stl结尾，则Convert其path添加tostl_list中
for file in os.listdir(stl_dir):
    if file.endswith('.stl'):
        stl_path = os.path.join(stl_dir, file)
        stl_list.append(stl_path)        
        print(stl_path)





for stl_path in stl_list:
    stl_path = pathlib.Path(stl_path)
    file_name = stl_path.name
    file_name_no_ext = file_name.split('.')[0]
    
    # Create保存path
    save_dir = os.path.join(os.path.dirname(stl_path), file_name_no_ext)
    os.makedirs(save_dir, exist_ok=True)
    
    # Create相机parameters保存path
    parameters_path = os.path.join(save_dir, "camera_parameters.json")


    mesh_path = save_dir
    print(f"stl_path: {stl_path}",'\n')
    print(f"mesh_path: {mesh_path}",'\n')

    # simulateparameters
    tri_paras = {
        'stl_path': stl_path,
        'mesh_path': mesh_path,
        'beam_type': 'fib',     # 'fib' or 'sem'  fib和sem与大小写无关 FIBIon beam imaging，SEMElectron beam imaging,通过该parameters，makingsimulate逻辑与实验一致
        'sample_tilt_x': 0,
        'sample_tilt_y': 0,
        'det_tilt_x': 76.8,         # 0 or 76.8 # 当为SEMElectron beam imaging时，需要Set为76.8
        'rotate_angle_start': 0,
        'rotate_angle_stop': 360,
        'rotate_angle_step': 360,
    }

    pri_paras = {
        'pri_dir': stl_dir,
        'pixel_size': 2,  # pixels大小，单位为nm
        'energy': 500,    # 电子束能量，单位：eV
        'epx': 500,       # 每pixels电子数
        'sigma': 1.0,     # 高斯模糊parameters，default1.0
        'poisson': True,   # 泊松分布，defaultTrue
        'roi_array': [-256, 255, -256, 255],  # [roi_x_min, roi_x_max, roi_y_min, roi_y_max]，if为None，则simulate整个模型
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
    'plot': True,   # 是否Display image，defaultFalse
    'save': True,   # 是否保存图像，defaultTrue
    }

    # 运行simulate
    run_simulate(nebula_paras, tri_paras, pri_paras, mat_paths_list)