import subprocess
import threading
import time
import platform
from analysis import sem_analysis
class nebula_gpu:
    def __init__(self, command, sem_simu_result:str, image_path:str, plot:bool=False, save:bool=True):
        super().__init__()
        self.command = command
        self.sem_simu_result = sem_simu_result
        self.image_path = image_path
        self.plot = plot
        self.save = save
        
    def run(self):
        try:           
            # 打印调试信息
            print(f"[DEBUG] 执行命令: {self.command}")
            print(f"[DEBUG] 操作系统: {platform.system()}")
            
            # 所有平台都使用 Popen 并监听输出
            print(f"[INFO] 在 {platform.system()} 平台上执行命令")
            
            # 创建进程
            process = subprocess.Popen(
                self.command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # 行缓冲
            )
            
            # 监听输出的函数
            def monitor_output(pipe, is_error=False):
                progress_completed = False
                progress_100_time = None
                
                for line in iter(pipe.readline, ''):
                    line_stripped = line.strip()
                    print(line_stripped)
                    
                    # 检测是否为detected: 0
                    if "running: 0 | detected: 0" in line_stripped:
                        print("检测到detected: 0，需要对输入进行优化")
                        process.terminate()
                        print("nebula_gpu 运行结束，未检测到有效数据，请优化输入")
                        return False
                    
                    # 检测进度是否为100.00%
                    if "Progress 100.00%" in line_stripped and not progress_completed:
                        print("检测到进度100.00%，将在20秒后终止进程并展示结果")
                        progress_completed = True
                        progress_100_time = time.time()
                    
                    # 如果已经检测到100%进度且已经过了20秒，则终止进程
                    if progress_completed and progress_100_time is not None and time.time() - progress_100_time >= 20:
                        print("如果等待20秒完成，进程未自然结束，则终止进程并展示结果")
                        process.terminate()
                        print("nebula_gpu 运行成功！")
                        return True
                
                return None
            
            # 创建线程监听stderr
            stderr_thread = threading.Thread(target=monitor_output, args=(process.stderr, True))
            stderr_thread.daemon = True
            stderr_thread.start()
            
            # 等待进程完成或被终止
            return_code = process.wait()
            
            # 检查进程是否正常结束
            if return_code == 0:
                print("nebula_gpu 运行成功！")
                self.show_image(plot=self.plot, save=self.save)
                return
            else:
                print(f"[WARNING] nebula_gpu 进程返回非零状态码: {return_code}")
                # 尝试显示图像，即使进程返回非零状态码
                try:
                    self.show_image(plot=self.plot, save=self.save)
                except Exception as e:
                    print(f"[ERROR] 显示图像失败: {e}")
                return
            # 所有平台都使用相同的监听方法，不再需要区分

        except Exception as e:
            error_msg = f"调用 nebula_gpu 时发生异常: {str(e)}"
            print(f"[ERROR] {error_msg}")  # 在终端打印异常信息
            print(error_msg)
    def show_image(self, plot = True, save = False):
            # 自动调用 sem-analysis.py
            try:
                print(f"开始调用 sem-analysis.py 展示图像，输出文件: {self.sem_simu_result}")
                sem_analysis(self.sem_simu_result, self.image_path, plot=plot, save=save)    
                print(f"sem-analysis.py 执行完成，展示图像完成")
            except Exception as e:
                error_msg = f"调用 sem-analysis.py 时发生异常: {str(e)}"
                print(error_msg)