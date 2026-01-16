import math
def generate_circular_mesh(radius=1.0, segments=12, output_file="circle_mesh.tri"):
    """
    Generate a circular mesh composed of triangle facets，并Convert数据写入file。

    parameters:
        radius (float): radius of circle
        segments (int): 圆of分段数（more segments smoother）
        output_file (str): outputfilename
    """
    vertices = []
    faces = []

    # Center point
    center = (0, 0, 34)
    vertices.append(center)

    # generation圆of顶点
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        z = 34
        vertices.append((x, y, z))

    # generation三角面片
    for i in range(segments):
        v0 = 0  # Center point
        v1 = 1 + i
        v2 = 1 + (i + 1) % segments
        faces.append((v0, v1, v2))

    # 写入file
    with open(output_file, "w") as f:
        for face in faces:
            v0, v1, v2 = face
            x0, y0, z0 = vertices[v0]
            x1, y1, z1 = vertices[v1]
            x2, y2, z2 = vertices[v2]
            # 格式化为指定格式
            line = f"-125 -125 {x0:.6f} {y0:.6f} {z0:.6f} {x1:.6f} {y1:.6f} {z1:.6f} {x2:.6f} {y2:.6f} {z2:.6f}\n"
            f.write(line)

    print(f"圆形网格已generationand write tofile: {output_file}")

# 示例调用
generate_circular_mesh(radius=17.0, segments=36, output_file="/home/chenguisen/AISI/nebula/nebula_python_wrapper/data/circle_mesh.tri")
