import sys
import pathlib
import torch
import numpy as np
from sem_pri import generate_sem_pri_data
from voxel_to_mesh import run_interface
# Example usage
# Can use anyfilenameasinput，including those with spaces and special charactersfilename，program will preserve originalfilename
# For example：
# voxel_path = '/path/to/your/input/file with spaces.stl'  # containing spacesfilename
# mesh_path = '/path/to/output directory/'  # containing spacesdirectory
# run_interface(voxel_path, mesh_path, final_side=1000)
#
# Or when running from command line：
# python voxel_to_mesh.py "/path/to/file with spaces.stl" "/output directory/"

# if需要from命令行运行，can use the following code：
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # from命令行Getinputfilepath，确保正确处理containing spacesfilename
        input_file = sys.argv[1]
        
        # 处理引号包裹offilename（可能包含空格）
        if (input_file.startswith('"') and input_file.endswith('"')) or \
           (input_file.startswith("'") and input_file.endswith("'")):
            input_file = input_file[1:-1]
        
        # 默认outputdirectory为inputfile所ondirectory
        output_dir = pathlib.Path(input_file).parent
        
        if len(sys.argv) > 2:
            # if提供了outputdirectory，则使用提供ofoutputdirectory
            output_dir = sys.argv[2]
            # 处理引号包裹ofdirectoryname（可能包含空格）
            if (output_dir.startswith('"') and output_dir.endswith('"')) or \
               (output_dir.startswith("'") and output_dir.endswith("'")):
                output_dir = output_dir[1:-1]
        
        print(f"处理file: {input_file}")
        print(f"outputdirectory: {output_dir}")
        
        # 确保path正确处理，特别是containing spacespath
        run_interface(input_file, output_dir, final_side=512)
    else:
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


        # 应当有必要，为了更快ofsimulate速degrees，应该进行一个scale，即应当使用final_side进行缩放  
        voxel_path = pathlib.Path('/home/chenguisen/AISI/nebula/nebula_python_wrapper/data/4_Trench Milling.stl')
        mesh_path = pathlib.Path('/home/chenguisen/AISI/nebula/nebula_python_wrapper/data')
        electron_ion_um = {"ion_beam": "ion_beam", "electron_beam": "electron_beam"}

        sample_tilt_x = 0
        det_tilt_x = 0
        beam_type = "ion_beam"
        if electron_ion_um["ion_beam"] == beam_type:
            # 1. generationSEM PRIfile
            sample_tilt_x = 55    # 样品倾转角
        elif electron_ion_um["electron_beam"] == beam_type:
            # 2. generationSEM PRIfile
            sample_tilt_x = 0   # 样品倾转角,可Select任意角degrees
            det_tilt_x = 76.8  # 探测器倾转角  
        else:
            raise ValueError("electron_ion_um must be 'ion_beam' or 'electron_beam'")
        
        v, faces, d_zmin, d_zmax = run_interface(voxel_path, mesh_path, final_side=1000,sample_tilt_x=sample_tilt_x,sample_tilt_new_z=0, det_tilt_x=det_tilt_x)

        x_min = int(np.floor(torch.min(v[:, 0]).cpu()))
        x_max = int(np.ceil(torch.max(v[:, 0]).cpu()))   
        y_min = int(np.floor(torch.min(v[:, 1]).cpu()))
        y_max = int(np.ceil(torch.max(v[:, 1]).cpu()))   
        
        print("x_min, x_max, y_min, y_max = ", x_min, x_max, y_min, y_max)


        pixel_size =2     # in nanometer
        x_pixel_num = int((np.abs(x_max)+np.abs(x_min))/pixel_size+1)
        y_pixel_num = int((np.abs(y_max)+np.abs(y_min))/pixel_size+1)


        xpx = np.linspace(x_min, x_max, x_pixel_num)
        ypx = np.linspace(y_min, y_max, y_pixel_num)
        print(x_pixel_num, y_pixel_num)
        


        beam_incident_dir = np.array([0, 0, -1])  # 束入射方to
        print("beam_incident_dir = ",beam_incident_dir)
        beam_zmax = (d_zmax+d_zmin)/2
        print("beam_zmax = ",beam_zmax)

        

        generate_sem_pri_data(
            z=beam_zmax,
            xpx=xpx,
            ypx=ypx,
            energy=500,
            epx=500,
            sigma=1,
            poisson=True,
            dx=beam_incident_dir[0],
            dy=beam_incident_dir[1],
            dz=beam_incident_dir[2],
            file_path=mesh_path/'sem.pri'
        )
       
        
