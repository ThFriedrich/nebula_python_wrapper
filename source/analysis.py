import sys
import os
import numpy as np
import matplotlib
# 设置matplotlib后端为非交互式，避免GUI相关的段错误
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# 尝试导入OpenCV用于图像显示
try:
	import cv2
	HAS_CV2 = True
except ImportError:
	HAS_CV2 = False
	print("OpenCV not available, falling back to matplotlib")
def sem_analysis(sem_simu_result,image_path, plot = False, save = True):
	# Find out which file to open
	# if len(sys.argv) < 2:
	# 	print("No output file provided")
	# 	sys.exit()
	# sem_simu_result = sys.argv[1]
	if not os.path.exists(sem_simu_result):
		print("File {} cannot be found".format(sem_simu_result))
		sys.exit()


	# This is a numpy datatype that corresponds to output files
	electron_dtype = np.dtype([
		('x',  '=f'), ('y',  '=f'), ('z',  '=f'), # Position
		('dx', '=f'), ('dy', '=f'), ('dz', '=f'), # Direction
		('E',  '=f'),                             # Energy
		('px', '=i'), ('py', '=i')])              # Pixel index

	# Open the output file
	data = np.fromfile(sem_simu_result, dtype=electron_dtype)
	print("Number of electrons detected: {}".format(len(data)))


	# Make a histogram of pixel indices
	xmin = data['px'].min()
	xmax = data['px'].max()
	ymin = data['py'].min()
	ymax = data['py'].max()
	H, xedges, yedges = np.histogram2d(data['px'], data['py'],
		bins = [
			np.linspace(xmin-.5, xmax+.5, xmax-xmin+2),
			np.linspace(ymin-.5, ymax+.5, ymax-ymin+2)
		])

	if save:
		plt.imsave(image_path, H.T, cmap='gray', dpi=300,origin='lower')
	if plot:
		# 尝试使用OpenCV显示图像
		if HAS_CV2:
			try:
				# 归一化图像数据到0-255范围
				image_normalized = ((H.T - H.T.min()) / (H.T.max() - H.T.min()) * 255).astype(np.uint8)
				
				# 调整图像大小以便查看
				height, width = image_normalized.shape
				if max(height, width) < 512:
					# 放大小图像
					scale = 512 // max(height, width)
					image_resized = cv2.resize(image_normalized, (width*scale, height*scale), interpolation=cv2.INTER_NEAREST)
				else:
					image_resized = image_normalized
				
				# 显示图像
				image_flipped = cv2.flip(image_resized, 0)
				cv2.imshow('SEM Analysis Result', image_flipped)
				print("Press any key to close the image window")
				cv2.waitKey(0)  # 等待按键
				cv2.destroyAllWindows()
				print("Image displayed successfully with OpenCV")
			except Exception as e:
				print(f"OpenCV display failed: {e}")
				# 回退到matplotlib
				_display_with_matplotlib(H, len(data))
		else:
			# 使用matplotlib显示
			_display_with_matplotlib(H, len(data))

def _display_with_matplotlib(H, num_electrons):
	"""使用matplotlib显示图像的回退方法"""
	try:
		plt.figure(figsize=(8, 6))
		plt.imshow(H.T, cmap='gray')
		plt.xlabel('x pixel')
		plt.ylabel('y pixel')
		plt.title(f'SEM Analysis - {num_electrons} electrons detected')
		plt.colorbar()
		plt.show()
		print("Image displayed with matplotlib")
	except Exception as e:
		print(f"Matplotlib display also failed: {e}")

if __name__ == '__main__':
	sem_simu_result='/home/chenguisen/AISI/nebula/simulation_results/output.det'
	image_path='/home/chenguisen/AISI/nebula/simulation_results/output.png'
	sem_analysis(sem_simu_result, image_path, plot=True, save=True)