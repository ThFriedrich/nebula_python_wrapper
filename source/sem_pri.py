import numpy as np
import os
import sys
import time

"""
SEM Image Simulation Generator

This script generates scanning electron microscope(SEM)image simulate data，creates.prifile。
.prifileformat stores position, direction, energy and pixel information for each simulated electron。

output:
- sem.pri: binary file containing electron datafile
"""
def generate_sem_pri_data(
        z: float, 
        xpx: np.ndarray, 
        ypx: np.ndarray, 
        energy:float = 500, 
        epx: int=1000, 
        sigma:float = 1,
        poisson: bool = True, 
        dx: float = 0, 
        dy: float = 0, 
        dz: float = -1, 
        file_path: str = 'sem.pri'
        ):
    """
    # parametersSet:
    z = 150                            # Starting z position (nm)
    xpx = np.linspace(-128, 128, 512)  # xpixels: range from-200nmto+200nm, step size2nm
    ypx = np.linspace(-128, 128, 512)  # ypixels: range from-200nmto+200nm, step size2nm
    energy = 500                      # 电子束能量, 单位eV
    epx = 1000                        # 每个pixelsof电子数量(使用泊松分布时为平均值)
    sigma = 1                         # 高斯光束斑点大小of标准差 (nm)
    poisson = True                    # 是否使用泊松散粒噪声
    dx = 0                           # x方toof方toto量
    dy = 0                           # y方toof方toto量
    dz = -1                          # z方toof方toto量
    """
   
    # 计算实际步长
    x_range = xpx[-1] - xpx[0]  # 动态计算x方toof范围
    y_range = ypx[-1] - ypx[0]  # 动态计算y方toof范围
    x_step = x_range / (len(xpx) - 1)
    y_step = y_range / (len(ypx) - 1)
    print(f"x方toof步长: {x_step:.4f} nm")
    print(f"y方toof步长: {y_step:.4f} nm")

    # 这是一个对应prifile格式ofnumpy数据类型
    electron_dtype = np.dtype([
        ('x',  '=f'), ('y',  '=f'), ('z',  '=f'), # 位置
        ('dx', '=f'), ('dy', '=f'), ('dz', '=f'), # 方to
        ('E',  '=f'),                             # 能量
        ('px', '=i'), ('py', '=i')])              # pixels索引

    #print(f"outputfile: {file_path}")

    try:
       
        # 估算内存使用和file大小
        pixel_count = len(xpx) * len(ypx)
        avg_electrons = epx * pixel_count
        memory_estimate = avg_electrons * electron_dtype.itemsize / (1024*1024)  # MB
        print(f"pixels总数: {pixel_count}")
        print(f"预计电子总数: {avg_electrons:,}")
        print(f"预计内存使用: {memory_estimate:.2f} MB")
        print(f"预计file大小: {memory_estimate:.2f} MB")
        
        # 方toto量归一化因子 (对于(0,0,-1)to量，归一化因子为1)
        norm_factor = 1.0
        
        total_electrons = 0
        start_time = time.time()
        
        print("开始generationSEM数据...")
        with open(file_path, 'wb') as file:
            # Iterate throughpixels
            for i, xmid in enumerate(xpx):
                # 每处理10%ofpixels显示once进degrees
                if i % (len(xpx) // 10) == 0 and i > 0:
                    percent = i * 100 // len(xpx)
                    elapsed = time.time() - start_time
                    remaining = elapsed * (len(xpx) - i) / i
                    print(f"进degrees: {percent}%, 已处理电子数: {total_electrons}, "
                        f"已用时间: {elapsed:.1f}秒, 预计剩余: {remaining:.1f}秒")
                    
                for j, ymid in enumerate(ypx):
                    try:
                        # 计算此pixelsof电子数量
                        N_elec = np.random.poisson(epx) if poisson else epx
                        total_electrons += N_elec
                        
                        # 分批处理大量电子以节省内存
                        batch_size = min(N_elec, 10000)  # 每批最多处理10000个电子
                        
                        for batch_start in range(0, N_elec, batch_size):
                            batch_end = min(batch_start + batch_size, N_elec)
                            batch_count = batch_end - batch_start
                            
                            # 分配numpy缓冲区
                            buffer = np.empty(batch_count, dtype=electron_dtype)
                            
                            # 填充数据
                            buffer['x'] = np.random.normal(xmid, sigma, batch_count)
                            buffer['y'] = np.random.normal(ymid, sigma, batch_count)
                            buffer['z'] = z
                            buffer['dx'] = dx
                            buffer['dy'] = dy
                            buffer['dz'] = dz * norm_factor  # 使用归一化of方toto量
                            buffer['E'] = energy
                            buffer['px'] = i
                            buffer['py'] = j
                            
                            # 写入file
                            buffer.tofile(file)
                    except Exception as e:
                            # if发生错误，打印错误信息并继续处理下一个pixels
                            raise RuntimeError(f"处理pixels({i},{j})时出错: {str(e)}")        
        total_time = time.time() - start_time
        print(f"完成! 总共处理了 {total_electrons:,} 个电子")
        print(f"总用时: {total_time:.2f} 秒")
        print(f"处理速degrees: {total_electrons/total_time:.2f} 电子/秒")
        print(f"file已保存to: {file_path}")
        
    except Exception as e:
        #print(f"错误: {str(e)}")
        sys.exit(1)