import numpy as np
from stl import mesh
import os
import sys
import argparse

# Constant definitions
SCALE_FACTOR = 20  # Coordinate scaling factor
POSITIVE_MARKER = "0 -123"  # Positive normal vector marker
NEGATIVE_MARKER = "-123 0"  # Negative normal vector marker
PROGRESS_INTERVAL = 10000  # Progress display interval

def process_stl_to_tri(input_path, output_path=None, scale_factor=SCALE_FACTOR):
    """
    ConvertSTLfileconvert to specified formatTRIfile
    
    parameters:
        input_path: inputSTLfilepath
        output_path: outputTRIfilepath(可选)
        scale_factor: Coordinate scaling factor(default20)
    
    Returns:
        Number of triangles written andoutputfilepath
    """
    # Set默认outputpath
    if output_path is None:
        base_name = os.path.splitext(input_path)[0]
        output_path = f"{base_name}.tri"
    
    try:
        # 检查inputfile是否存on
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"inputfile不存on: {input_path}")
            
        # 加载STL模型
        stl_mesh = mesh.Mesh.from_file(input_path)
        
        # Get三角形数量
        num_triangles = len(stl_mesh.vectors)
        print(f"发现 {num_triangles} 个三角形")
        
        # 确保outputdirectory存on
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 打开outputfile
        with open(output_path, 'w') as f:
            # 处理每个三角形
            for i, triangle in enumerate(stl_mesh.vectors):
                # Get法to量
                normal = stl_mesh.normals[i] if i < len(stl_mesh.normals) else None
                
                # 确定法to量方to标记
                marker = POSITIVE_MARKER if (normal is None or np.sum(normal) >= 0) else NEGATIVE_MARKER
                
                # Get三角形of三个顶点坐标
                v1, v2, v3 = triangle
                
                # Create格式化of顶点字符串（应用Scaling factor）
                vertices_str = " ".join(f"{(coord * scale_factor):.6f}" for vertex in [v1, v2, v3] for coord in vertex)
                
                # 写入一行
                line = f"{marker} {vertices_str}\n"
                f.write(line)
                
                # 显示进degrees
                if (i + 1) % PROGRESS_INTERVAL == 0:
                    print(f"已处理 {i+1} 个三角形...")
        
        print(f"转换完成! outputfile: {output_path}")
        return num_triangles, output_path
        
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 0, None

def _build_cli():
    parser = argparse.ArgumentParser(description='Convert STL to TRI format')
    parser.add_argument('input_stl', help='Path to input .stl file')
    parser.add_argument('output_tri', nargs='?', help='Path to output .tri file; default: <input>.tri')
    parser.add_argument('--scale', type=float, default=SCALE_FACTOR, help='Scale factor for coordinates (default: %(default)s)')
    return parser

def main():
    parser = _build_cli()
    args = parser.parse_args()
    process_stl_to_tri(args.input_stl, args.output_tri, scale_factor=args.scale)

if __name__ == '__main__':
    main()

