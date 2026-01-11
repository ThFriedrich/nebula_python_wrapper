import math
import torch
def rotate_cylinder():
    rotated_data = []
    with open('data/circle_mesh.tri', 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) >= 11:
                material1, material2 = parts[0], parts[1]
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                x1, y1, z1 = float(parts[5]), float(parts[6]), float(parts[7])
                x2, y2, z2 = float(parts[8]), float(parts[9]), float(parts[10])
               
           
                # Rotation
                cos_tx = cos_ty = 1.0
                sin_tx = sin_ty = 0.0
                
                # Apply tilts
                tilt_x = 55
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

                        x = x * 1e3
                        x1 = x1 * 1e3
                        x2 = x2 * 1e3
                        y_r = y_r * 1e3
                        y1_r = y1_r * 1e3
                        y2_r = y2_r * 1e3
                        z_r = z_r * 1e3
                        z1_r = z1_r * 1e3
                        z2_r = z2_r * 1e3
      
                       # ConvertRotation后of坐标和材质一起写入数组
                rotated_data.append([material1, material2, x, y_r, z_r, x1, y1_r, z1_r, x2, y2_r, z2_r])

    # ConvertRotation后of数据写入file
    with open('data/circle_mesh_rotated.tri', 'w') as file:
        for data in rotated_data:
            file.write(' '.join(map(str, data)) + '\n')
                                        
rotate_cylinder()                    
 
    