import json
def add_frame_to_parameters(parameters, file_path, rotation, translation):
    """
    to parameters in dictionary frames list add new frame data。
    
    parameters:
        parameters (dict): containing cameraparameters和帧数据ofdictionary。
        file_path (str): 新帧of图片path。
        rotation (list): 新帧ofRotationparameters [rx, ry, rz]。
        translation (list): 新帧oftranslationparameters [tx, ty, tz]。
    
    Returns:
        dict: 更新后of parameters dictionary。
    """
    # 确保 frames 键存on
    if "frames" not in parameters:
        parameters["frames"] = []
    
    # 添加新帧数据
    new_frame = {
        "file_path": file_path,
        "rotation": rotation,
        "translation": translation
    }
    parameters["frames"].append(new_frame)
    
    return parameters
def save_parameters(parameters, file_path):
    """
    保存相机parameters和帧数据to JSON file。
    
    parameters:
        parameters (dict): containing cameraparameters和帧数据ofdictionary，格式如下：
            {
                "camera": {
                    "width": int,
                    "height": int,
                    "cx": float,
                    "cy": float
                },
                "frames": [
                    {
                        "file_path": str,
                        "rotation": [float, float, float],
                        "translation": [float, float, float]
                    },
                    ...
                ]
            }
        file_path (str): 保存 JSON fileofpath。
    """
    with open(file_path, 'w') as f:
        json.dump(parameters, f, indent=4)

# Example usage
if __name__ == "__main__":
    example_parameters = {
        "camera": {
            "width": 1024,
            "height": 1024,
            "cx": 512.0,
            "cy": 512.0
        },
        "frames": [
            {
                "file_path": "images/view_000.png",
                "rotation": [0.0, 0.0, 0.0],
                "translation": [0.0, 0.0, 0.0]
            },
            {
                "file_path": "images/view_001.png",
                "rotation": [0.0, 55.0, 0.0],
                "translation": [0.0, 0.0, 0.0]
            }
        ]
    }
    save_parameters(example_parameters, "example_parameters.json")