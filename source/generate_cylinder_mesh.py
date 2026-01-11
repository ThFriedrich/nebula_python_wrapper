detector_str =f"""-125 -125 1150000.0 -2457456.1328669754 1720729.3090531386 810000.0 -1992859.2194226277 2384242.464927222 0.0 -1797843.2310632723 2662754.159985479
-125 -125 1150000.0 -2457456.1328669754 1720729.3090531386 0.0 -1797843.2310632723 2662754.159985479 -810000.0 -1992859.2194226277 2384242.464927222
-125 -125 1150000.0 -2457456.1328669754 1720729.3090531386 -810000.0 -1992859.2194226277 2384242.464927222 -1150000.0 -2457456.1328669754 1720729.3090531386
-125 -125 1150000.0 -2457456.1328669754 1720729.3090531386 -1150000.0 -2457456.1328669754 1720729.3090531386 -810000.0 -2922053.0463113226 1057216.153179055
-125 -125 1150000.0 -2457456.1328669754 1720729.3090531386 -810000.0 -2922053.0463113226 1057216.153179055 0.0 -3117069.034670678 778704.4581207981
-125 -125 1150000.0 -2457456.1328669754 1720729.3090531386 0.0 -3117069.034670678 778704.4581207981 810000.0 -2922053.0463113226 1057216.153179055
-125 -125 1150000.0 -2457456.1328669754 1720729.3090531386 810000.0 -2922053.0463113226 1057216.153179055 1150000.0 -2457456.1328669754 1720729.3090531386
"""
import math
def read_detector_str(detector_str):
    lines = detector_str.split('\n')
    rotated_data = []
    for line in lines:
            parts = line.strip().split()
            if len(parts) >= 11:
                material1, material2 = parts[0], parts[1]
                x, y, z = float(parts[2])*1e-6, float(parts[3])*1e-6, float(parts[4])*1e-6
                x1, y1, z1 = float(parts[5])*1e-6, float(parts[6])*1e-6, float(parts[7])*1e-6
                x2, y2, z2 = float(parts[8])*1e-6, float(parts[9])*1e-6, float(parts[10])*1e-6
                # Rotation
                cos_tx = cos_ty = 1.0
                sin_tx = sin_ty = 0.0
                
                # Apply tilts
                tilt_x = -55
                if tilt_x != 0:
                        tilt_x_rad = math.radians(tilt_x)
                        cos_tx = math.cos(tilt_x_rad)
                        sin_tx = math.sin(tilt_x_rad)
                        y_r = y * cos_tx - z * sin_tx
                        z_r = y * sin_tx + z * cos_tx
                        y1_r = y1 * cos_tx - z1 * sin_tx
                        z1_r = y1 * sin_tx + z1 * cos_tx
                        y2_r = y2 * cos_tx - z2 * sin_tx
                        z2_r = y2 * sin_tx + z2 * cos_tx
                       # ConvertRotation后of坐标和材质一起写入数组
                rotated_data.append([material1, material2, x, y_r, z_r, x1, y1_r, z1_r, x2, y2_r, z2_r])
        # ConvertRotation后of数据写入file
    with open('data/detector.tri', 'w') as file:
            for data in rotated_data:
                file.write(' '.join(map(str, data)) + '\n')
    print(rotated_data)
read_detector_str(detector_str)