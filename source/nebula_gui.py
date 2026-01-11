import sys
import os
import subprocess
import pathlib
import torch
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QPlainTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QTabWidget, QProgressBar,
    QTextEdit
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtCore import QSettings


from sem_pri import generate_sem_pri_data
from voxel_to_mesh import run_interface


class NebulaGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Nebula GPU Toolset")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize d_zmin and d_zmax attributes
        self.d_zmin = 0
        self.d_zmax = 0
        self.R = None  # Initialize rotation matrix
        #self.v_orig = None
        # Main widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Layout
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # CreateNebula GPUparametersconfiguration tab
        self.nebula_tab = QWidget()
        self.nebula_layout = QVBoxLayout(self.nebula_tab)
        self.tabs.addTab(self.nebula_tab, "Nebula GPU parametersconfiguration")
        
        # CreateTRI和PRIgeneration器选项卡
        self.tri_pri_tab = QWidget()
        self.tri_pri_layout = QVBoxLayout(self.tri_pri_tab)
        self.tabs.addTab(self.tri_pri_tab, "TRI和PRIgeneration器")
        
        
        # InitializeNebula GPUparametersconfiguration tab
        self.init_nebula_tab()
        
        # InitializeTRI和PRIgeneration器选项卡
        self.init_tri_pri_tab()
        

        
    def init_nebula_tab(self):
        """InitializeNebula GPUparametersconfiguration tab"""
        # nebula_gpu path
        self.nebula_gpu_layout = QHBoxLayout()
        self.nebula_gpu_label = QLabel("nebula_gpu path:")
        self.nebula_gpu_input = QLineEdit()
        self.nebula_gpu_input.setText("")
        self.nebula_gpu_button = QPushButton("Select")
        self.nebula_gpu_button.clicked.connect(self.select_nebula_gpu_path)
        self.nebula_gpu_layout.addWidget(self.nebula_gpu_label)
        self.nebula_gpu_layout.addWidget(self.nebula_gpu_input)
        self.nebula_gpu_layout.addWidget(self.nebula_gpu_button)
        self.nebula_layout.addLayout(self.nebula_gpu_layout)

        # tri filepath
        self.tri_layout = QHBoxLayout()
        self.tri_label = QLabel(".tri filepath:")
        self.tri_input = QLineEdit()
        self.tri_button = QPushButton("Select")
        self.tri_button.clicked.connect(lambda: self.select_file(self.tri_input, "TRI Files (*.tri)"))
        self.tri_layout.addWidget(self.tri_label)
        self.tri_layout.addWidget(self.tri_input)
        self.tri_layout.addWidget(self.tri_button)
        self.nebula_layout.addLayout(self.tri_layout)

        # pri filepath
        self.pri_layout = QHBoxLayout()
        self.pri_label = QLabel(".pri filepath:")
        self.pri_input = QLineEdit()
        self.pri_button = QPushButton("Select")
        self.pri_button.clicked.connect(lambda: self.select_file(self.pri_input, "PRI Files (*.pri)"))
        self.pri_layout.addWidget(self.pri_label)
        self.pri_layout.addWidget(self.pri_input)
        self.pri_layout.addWidget(self.pri_button)
        self.nebula_layout.addLayout(self.pri_layout)

        # mat filepath（支持多选）
        self.mat_layout = QHBoxLayout()
        self.mat_label = QLabel(".mat filepath:")
        self.mat_input = QLineEdit()
        self.mat_input.setPlaceholderText("支持多选，点击右侧按钮Select")
        self.mat_button = QPushButton("Select多个")
        self.mat_button.clicked.connect(self.select_mat_files)
        self.mat_layout.addWidget(self.mat_label)
        self.mat_layout.addWidget(self.mat_input)
        self.mat_layout.addWidget(self.mat_button)
        self.nebula_layout.addLayout(self.mat_layout)

        # outputfilepath
        self.output_layout = QHBoxLayout()
        self.output_label = QLabel("outputfilepath:")
        self.output_path_input = QLineEdit()
        self.output_button = QPushButton("Select")
        self.output_button.clicked.connect(self.select_output_path)
        self.output_layout.addWidget(self.output_label)
        self.output_layout.addWidget(self.output_path_input)
        self.output_layout.addWidget(self.output_button)
        self.nebula_layout.addLayout(self.output_layout)

        # 运行按钮
        self.run_button = QPushButton("运行 nebula_gpu")
        self.run_button.clicked.connect(self.run_nebula_gpu)
        self.nebula_layout.addWidget(self.run_button)

        # 日志output
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("font-family: monospace;")
        self.nebula_layout.addWidget(self.log_output)
        
   
    def init_tri_pri_tab(self):
        """InitializeTRI和PRIgeneration器选项卡"""
        # fileSelect部分
        file_group = QGroupBox("fileSet")
        file_layout = QVBoxLayout()
        
        # STLfileSelect
        stl_layout = QHBoxLayout()
        stl_label = QLabel("STLfile:")
        self.stl_path_edit = QLineEdit()
        self.stl_path_edit.setReadOnly(True)
        stl_browse_btn = QPushButton("浏览...")
        stl_browse_btn.clicked.connect(self.browse_stl_file)
        stl_layout.addWidget(stl_label)
        stl_layout.addWidget(self.stl_path_edit)
        stl_layout.addWidget(stl_browse_btn)
        file_layout.addLayout(stl_layout)
        
        # outputdirectorySelect
        tri_pri_output_layout = QHBoxLayout()
        tri_pri_output_label = QLabel("outputdirectory:")
        self.tri_pri_output_path_edit = QLineEdit()
        self.tri_pri_output_path_edit.setReadOnly(True)
        tri_pri_output_layout.addWidget(tri_pri_output_label)
        tri_pri_output_layout.addWidget(self.tri_pri_output_path_edit)
        file_layout.addLayout(tri_pri_output_layout)
        
        file_group.setLayout(file_layout)
        self.tri_pri_layout.addWidget(file_group)
        
        # 束类型Set
        beam_group = QGroupBox("束类型Set")
        beam_layout = QVBoxLayout()
        
        beam_type_layout = QHBoxLayout()
        beam_type_label = QLabel("束类型:")
        self.beam_type_combo = QComboBox()
        self.beam_type_combo.addItem("离子束 (Ion Beam)", "ion_beam")
        self.beam_type_combo.addItem("电子束 (Electron Beam)", "electron_beam")
        self.beam_type_combo.currentIndexChanged.connect(self.update_tilt_values)
        beam_type_layout.addWidget(beam_type_label)
        beam_type_layout.addWidget(self.beam_type_combo)
        beam_layout.addLayout(beam_type_layout)
        
        # 样品倾转角
        sample_tilt_layout = QHBoxLayout()
        sample_tilt_label = QLabel("样品倾转角 (°):")
        self.sample_tilt_spin = QDoubleSpinBox()
        self.sample_tilt_spin.setRange(-90, 90)
        self.sample_tilt_spin.setValue(0)  # 初始值设为0
        self.sample_tilt_spin.setDecimals(1)
        sample_tilt_layout.addWidget(sample_tilt_label)
        sample_tilt_layout.addWidget(self.sample_tilt_spin)
        beam_layout.addLayout(sample_tilt_layout)
        
        # 样品新Zaxisrotation angle
        sample_tilt_new_z_layout = QHBoxLayout()
        sample_tilt_new_z_label = QLabel("样品新Zaxisrotation angle (°):")
        self.sample_tilt_new_z_spin = QDoubleSpinBox()
        self.sample_tilt_new_z_spin.setRange(-360, 360)
        self.sample_tilt_new_z_spin.setValue(0)  # 初始值设为0
        self.sample_tilt_new_z_spin.setDecimals(1)
        sample_tilt_new_z_layout.addWidget(sample_tilt_new_z_label)
        sample_tilt_new_z_layout.addWidget(self.sample_tilt_new_z_spin)
        beam_layout.addLayout(sample_tilt_new_z_layout)
        
        # 探测器倾转角
        det_tilt_layout = QHBoxLayout()
        det_tilt_label = QLabel("探测器倾转角 (°):")
        self.det_tilt_spin = QDoubleSpinBox()
        self.det_tilt_spin.setRange(-90, 90)
        self.det_tilt_spin.setValue(0)
        self.det_tilt_spin.setDecimals(1)
        det_tilt_layout.addWidget(det_tilt_label)
        det_tilt_layout.addWidget(self.det_tilt_spin)
        beam_layout.addLayout(det_tilt_layout)
        
        beam_group.setLayout(beam_layout)
        self.tri_pri_layout.addWidget(beam_group)
        
        # PRIfileSet
        pri_group = QGroupBox("PRIfileSet")
        pri_layout = QVBoxLayout()
        
        # pixels范围显示区域
        pixel_range_group = QGroupBox("pixels范围")
        pixel_range_layout = QGridLayout()
        
        # X范围
        x_min_label = QLabel("X最小值:")
        self.x_min_value = QLabel("0")
        x_max_label = QLabel("X最大值:")
        self.x_max_value = QLabel("0")
        
        # Y范围
        y_min_label = QLabel("Y最小值:")
        self.y_min_value = QLabel("0")
        y_max_label = QLabel("Y最大值:")
        self.y_max_value = QLabel("0")
        
        # 添加to网格Layout
        pixel_range_layout.addWidget(x_min_label, 0, 0)
        pixel_range_layout.addWidget(self.x_min_value, 0, 1)
        pixel_range_layout.addWidget(x_max_label, 0, 2)
        pixel_range_layout.addWidget(self.x_max_value, 0, 3)
        pixel_range_layout.addWidget(y_min_label, 1, 0)
        pixel_range_layout.addWidget(self.y_min_value, 1, 1)
        pixel_range_layout.addWidget(y_max_label, 1, 2)
        pixel_range_layout.addWidget(self.y_max_value, 1, 3)
        
        pixel_range_group.setLayout(pixel_range_layout)
        pri_layout.addWidget(pixel_range_group)
        
        # ROISet区域
        roi_group = QGroupBox("ROI区域Set")
        roi_layout = QGridLayout()
        
        # ROI X范围
        roi_x_min_label = QLabel("ROI X最小值:")
        self.roi_x_min_spin = QSpinBox()
        self.roi_x_min_spin.setRange(-100000, 100000)
        self.roi_x_min_spin.setValue(0)
        
        roi_x_max_label = QLabel("ROI X最大值:")
        self.roi_x_max_spin = QSpinBox()
        self.roi_x_max_spin.setRange(-100000, 100000)
        self.roi_x_max_spin.setValue(0)
        
        # ROI Y范围
        roi_y_min_label = QLabel("ROI Y最小值:")
        self.roi_y_min_spin = QSpinBox()
        self.roi_y_min_spin.setRange(-100000, 100000)
        self.roi_y_min_spin.setValue(0)
        
        roi_y_max_label = QLabel("ROI Y最大值:")
        self.roi_y_max_spin = QSpinBox()
        self.roi_y_max_spin.setRange(-100000, 100000)
        self.roi_y_max_spin.setValue(0)
        
        # 使用ROI区域of复选框
        self.use_roi_checkbox = QCheckBox("使用ROI区域")
        self.use_roi_checkbox.setChecked(False)
        self.use_roi_checkbox.stateChanged.connect(self.toggle_roi_controls)
        
        # 添加to网格Layout
        roi_layout.addWidget(roi_x_min_label, 0, 0)
        roi_layout.addWidget(self.roi_x_min_spin, 0, 1)
        roi_layout.addWidget(roi_x_max_label, 0, 2)
        roi_layout.addWidget(self.roi_x_max_spin, 0, 3)
        roi_layout.addWidget(roi_y_min_label, 1, 0)
        roi_layout.addWidget(self.roi_y_min_spin, 1, 1)
        roi_layout.addWidget(roi_y_max_label, 1, 2)
        roi_layout.addWidget(self.roi_y_max_spin, 1, 3)
        roi_layout.addWidget(self.use_roi_checkbox, 2, 0, 1, 4)
        
        roi_group.setLayout(roi_layout)
        pri_layout.addWidget(roi_group)
        
        # pixels大小
        pixel_size_layout = QHBoxLayout()
        pixel_size_label = QLabel("pixels大小 (nm):")
        self.pixel_size_spin = QDoubleSpinBox()
        self.pixel_size_spin.setRange(0.1, 100)
        self.pixel_size_spin.setValue(2)
        self.pixel_size_spin.setDecimals(1)
        pixel_size_layout.addWidget(pixel_size_label)
        pixel_size_layout.addWidget(self.pixel_size_spin)
        pri_layout.addLayout(pixel_size_layout)
        
        # 电子束能量
        energy_layout = QHBoxLayout()
        energy_label = QLabel("电子束能量 (eV):")
        self.energy_spin = QSpinBox()
        self.energy_spin.setRange(100, 10000)
        self.energy_spin.setValue(500)
        self.energy_spin.setSingleStep(100)
        energy_layout.addWidget(energy_label)
        energy_layout.addWidget(self.energy_spin)
        pri_layout.addLayout(energy_layout)
        
        # 每pixels电子数
        epx_layout = QHBoxLayout()
        epx_label = QLabel("每pixels电子数:")
        self.epx_spin = QSpinBox()
        self.epx_spin.setRange(1, 10000)
        self.epx_spin.setValue(500)
        self.epx_spin.setSingleStep(100)
        epx_layout.addWidget(epx_label)
        epx_layout.addWidget(self.epx_spin)
        pri_layout.addLayout(epx_layout)
        
        # 高斯光束斑点大小
        sigma_layout = QHBoxLayout()
        sigma_label = QLabel("高斯光束斑点大小 (nm):")
        self.sigma_spin = QDoubleSpinBox()
        self.sigma_spin.setRange(0.1, 10)
        self.sigma_spin.setValue(1)
        self.sigma_spin.setDecimals(1)
        sigma_layout.addWidget(sigma_label)
        sigma_layout.addWidget(self.sigma_spin)
        pri_layout.addLayout(sigma_layout)
        
        # 泊松散粒噪声
        poisson_layout = QHBoxLayout()
        poisson_label = QLabel("使用泊松散粒噪声:")
        self.poisson_check = QCheckBox()
        self.poisson_check.setChecked(True)
        poisson_layout.addWidget(poisson_label)
        poisson_layout.addWidget(self.poisson_check)
        pri_layout.addLayout(poisson_layout)
        
        pri_group.setLayout(pri_layout)
        self.tri_pri_layout.addWidget(pri_group)
        
        # 日志output区域
        log_group = QGroupBox("日志output")
        log_layout = QVBoxLayout()
        self.tri_pri_log_text = QTextEdit()
        self.tri_pri_log_text.setReadOnly(True)
        log_layout.addWidget(self.tri_pri_log_text)
        log_group.setLayout(log_layout)
        self.tri_pri_layout.addWidget(log_group)
        
        # 进degrees条
        self.tri_pri_progress_bar = QProgressBar()
        self.tri_pri_progress_bar.setRange(0, 0)  # Set为不确定模式
        self.tri_pri_progress_bar.setVisible(True)
        self.tri_pri_layout.addWidget(self.tri_pri_progress_bar)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.generate_tri_btn = QPushButton("generationTRIfile")
        self.generate_tri_btn.clicked.connect(self.generate_tri_file)
        self.generate_pri_btn = QPushButton("generationPRIfile")
        self.generate_pri_btn.clicked.connect(self.generate_pri_file)
        button_layout.addStretch()
        button_layout.addWidget(self.generate_tri_btn)
        button_layout.addWidget(self.generate_pri_btn)
        self.tri_pri_layout.addLayout(button_layout)
        
        # Initialize默认值
        self.update_tilt_values()
        
        # InitializeROI控件状态
        self.toggle_roi_controls(Qt.CheckState.Unchecked)
        
        # Initialize时不Set默认path，ConvertonSelectSTLfile后自动Set


    def select_nebula_gpu_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select nebula_gpu 可执行file", "", "Executable Files (*)")
        if path:
            self.nebula_gpu_input.setText(path)

    def select_file(self, input_widget, file_filter="All Files (*)"):
        path, _ = QFileDialog.getOpenFileName(self, "Selectfile", "", file_filter)
        if path:
            input_widget.setText(path)

    def select_mat_files(self):
        paths = []
        while True:
            path, _ = QFileDialog.getOpenFileName(self, "Select .mat file", "", "MAT Files (*.mat);;All Files (*)")
            if not path:
                break
            paths.append(path)
            self.mat_input.setText(", ".join(paths))
            reply = QMessageBox.question(self, "继续Select", "是否继续Select下一个 .mat file？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                break
        if paths:
            self.mat_input.setText(", ".join(paths))

    def select_output_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Selectoutputfilepath", "", "All Files (*)")
        if path:
            self.output_path_input.setText(path)
            
    def browse_stl_file(self):
        """浏览SelectSTLfile"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "SelectSTLfile", "", "STLfile (*.stl);;所有file (*.*)"
        )
        if file_path:
            self.stl_path_edit.setText(file_path)
            
            # 自动Setoutputdirectory为STLfile所onofdirectory
            stl_dir = str(pathlib.Path(file_path).parent)
            self.tri_pri_output_path_edit.setText(stl_dir)
    
    
    def update_tilt_values(self):
        """根据束类型更新倾转角默认值"""
        beam_type = self.beam_type_combo.currentData()
        if beam_type == "ion_beam":
            self.sample_tilt_spin.setValue(0)
            self.sample_tilt_new_z_spin.setValue(0)
            self.det_tilt_spin.setValue(0)
            self.det_tilt_spin.setEnabled(False)  # 离子束模式下禁用探测器倾转角
        else:  # electron_beam
            self.sample_tilt_spin.setValue(0)
            self.sample_tilt_new_z_spin.setValue(0)
            self.det_tilt_spin.setValue(76.8)
            self.det_tilt_spin.setEnabled(True)  # 电子束模式下Enable探测器倾转角
            
    def toggle_roi_controls(self, state):
        """
        根据 ROI（Region of Interest）复选框of状态，Enable或禁用 ROI 相关控件。

        当复选框被勾选时（非未选中状态），ROI 控件（包括 X/Y axis最小/最大值input框）Convert被Enable，
        允许用户input ROI of范围值。当复选框未被勾选时，这些控件Convert被禁用，防止用户修改。

        Args:
            state (Qt.CheckState): 复选框of状态，可以是以下值之一：
                - Qt.CheckState.Unchecked: 未选中状态
                - Qt.CheckState.PartiallyChecked: 部分选中状态
                - Qt.CheckState.Checked: 选中状态
        """
        if state == Qt.CheckState.Checked.value:
            # Enable ROI 控件
            self.roi_x_min_spin.setEnabled(True)
            self.roi_x_max_spin.setEnabled(True)
            self.roi_y_min_spin.setEnabled(True)
            self.roi_y_max_spin.setEnabled(True)
        else:
            # 禁用 ROI 控件
            self.roi_x_min_spin.setEnabled(False)
            self.roi_x_max_spin.setEnabled(False)
            self.roi_y_min_spin.setEnabled(False)
            self.roi_y_max_spin.setEnabled(False)


        
        
    def update_pixel_range(self, x_min, x_max, y_min, y_max):
        """更新pixels范围标签并SetROI默认值"""
        # 更新标签
        self.x_min_value.setText(str(x_min))
        self.x_max_value.setText(str(x_max))
        self.y_min_value.setText(str(y_min))
        self.y_max_value.setText(str(y_max))
        
        # SetROI默认值
        self.roi_x_min_spin.setValue(x_min)
        self.roi_x_max_spin.setValue(x_max)
        self.roi_y_min_spin.setValue(y_min)
        self.roi_y_max_spin.setValue(y_max)
        
        # SetROI范围
        self.roi_x_min_spin.setRange(x_min, x_max)
        self.roi_x_max_spin.setRange(x_min, x_max)
        self.roi_y_min_spin.setRange(y_min, y_max)
        self.roi_y_max_spin.setRange(y_min, y_max)
    
    def tri_pri_log(self, message):
        """添加TRI和PRIgeneration器日志消息"""
        self.tri_pri_log_text.append(message)
        # 滚动to底部
        self.tri_pri_log_text.verticalScrollBar().setValue(
            self.tri_pri_log_text.verticalScrollBar().maximum()
        )
    
    def generate_tri_file(self):
        """仅generation.trifile"""
        # 检查input
        if not self.stl_path_edit.text():
            QMessageBox.warning(self, "警告", "请SelectSTLfile")
            return
                
        # 收集parameters
        params = {
            'voxel_path': pathlib.Path(self.stl_path_edit.text()),
            'mesh_path': pathlib.Path(self.tri_pri_output_path_edit.text()),
            'beam_type': self.beam_type_combo.currentData(),
            'sample_tilt_x': self.sample_tilt_spin.value(),
            'sample_tilt_new_z': self.sample_tilt_new_z_spin.value(),
            'det_tilt_x': self.det_tilt_spin.value(),
        }
        
        # 清空日志
        #self.tri_pri_log_text.clear()
                
        # Create并启动工作线程
        self.tri_worker = TriGeneratorWorker(params)
        self.tri_worker.progress_signal.connect(self.tri_pri_log)
        self.tri_worker.finished_signal.connect(self.on_tri_generation_finished)
        self.tri_worker.update_pixel_range_signal.connect(self.update_pixel_range)
        self.tri_worker.start()
    
    def on_tri_generation_finished(self, success, message, tri_file_path):
        """仅generation.trifile完成of回调"""
 
        if success:
            self.tri_pri_log("✅ " + message)
            QMessageBox.information(self, "成功", message)
            
            # 直接使用传递过来oftrifilepath
            self.tri_pri_log(f"使用trifile: {tri_file_path}")
            
            # 填充pathtoinput框
            if tri_file_path:
                self.tri_input.setText(tri_file_path)
            
            # 自动填充主界面oftrifilepath
            self.tri_input.setText(tri_file_path)
            
            # 保存d_zmin和d_zmax值，以便ongenerate_pri_file中使用
            self.d_zmin = self.tri_worker.d_zmin
            self.d_zmax = self.tri_worker.d_zmax
            self.R = self.tri_worker.R
            #self.v_orig = self.tri_worker.v_orig
            self.tri_pri_log(f"保存d_zmin: {self.d_zmin}, d_zmax: {self.d_zmax}")
        else:
            self.tri_pri_log("❌ " + message)
            QMessageBox.critical(self, "错误", message)

    def generate_pri_file(self):
        """generation.prifile"""
    
        # 检查input
        if not self.tri_input.text():
            QMessageBox.warning(self, "警告", "请先generation或Select.trifile")
            self.generate_pri_btn.setEnabled(True)
            return

        # roi_x_min = self.roi_x_min_spin.value()
        # roi_x_max = self.roi_x_max_spin.value() 
        # roi_y_min = self.roi_y_min_spin.value()
        # roi_y_max = self.roi_y_max_spin.value()
        # self.tri_pri_log(f"初始设定ROI范围: X({roi_x_min:.1f}, {roi_x_max:.1f}), Y({roi_y_min:.1f}, {roi_y_max:.1f})")
        # #if self.sample_tilt_spin.value() != 0:
        #     #if self.sample_tilt_new_z_spin.value()!=0:
        #         # 计算pixels范围
        # # x_min_ori = int(torch.floor(torch.min(self.v_orig[:, 0])).item())
        # # x_max_ori = int(torch.ceil(torch.max(self.v_orig[:, 0])).item())   
        # # y_min_ori = int(torch.floor(torch.min(self.v_orig[:, 1])).item())
        # # y_max_ori = int(torch.ceil(torch.max(self.v_orig[:, 1])).item())

        # z_min_ori = int(torch.floor(torch.min(self.v_orig[:, 2])).item())
        # z_max_ori = int(torch.ceil(torch.max(self.v_orig[:, 2])).item())
        # # z_size_ori = z_max_ori - z_min_ori
        # # y_max_offset = abs(z_size_ori * np.sin(np.radians(self.sample_tilt_spin.value())))  # 计算Y方toof偏移量
        # # y_min_offset = abs(z_size_ori * np.cos(np.radians(self.sample_tilt_spin.value())))  # 计算Y方toof偏移量
        # # # x_min = int(self.x_min_value.text())
        # # # x_max = int(self.x_max_value.text())
        # # # y_min = int(self.y_min_value.text())
        # # # y_max = int(self.y_max_value.text())

        # # # 计算偏移量
        # # # x_min_offset = abs(x_min_ori - x_min)
        # # # y_min_offset = abs(y_min_ori - y_min)
        # # # x_max_offset = abs(x_max_ori - x_max)
        # # # y_max_offset = abs(y_max_ori - y_max)

        # # # x_offset_max = max(x_min_offset, x_max_offset)
        # # # y_offset_max = max(y_min_offset, y_max_offset)*2
        # # self.tri_pri_log(f"偏移量:  Y({y_min_offset:.1f}, {y_max_offset:.1f})")
        # # self.tri_pri_log(f"原始pixels范围: X({x_min_ori}, {x_max_ori}), Y({y_min_ori}, {y_max_ori})")

        # roi_v = torch.tensor([
        #     [roi_x_min, roi_y_min, z_max_ori],
        #     [roi_x_max, roi_y_min, z_max_ori],
        #     [roi_x_min, roi_y_max, z_max_ori],
        #     [roi_x_max, roi_y_max, z_max_ori]
        # ], dtype=torch.float32)

        # tilt_x_rad = torch.tensor(np.radians(self.sample_tilt_spin.value()), dtype=torch.float32)
        # cos_tx = torch.cos(tilt_x_rad)
        # sin_tx = torch.sin(tilt_x_rad)
        # y = roi_v[:, 1] * cos_tx - roi_v[:, 2] * sin_tx
        # z = roi_v[:, 1] * sin_tx + roi_v[:, 2] * cos_tx
        # roi_v[:, 1] = y
        # roi_v[:, 2] = z
        # points = torch.stack([roi_v[:, 0], roi_v[:, 1], roi_v[:, 2]], dim=1).to(self.R.device)
        # roi_rotated = torch.mm(points, self.R.T)

        # roi_x_min = int(torch.floor(torch.min(roi_rotated[:, 0])).item())
        # roi_x_max = int(torch.ceil(torch.max(roi_rotated[:, 0])).item())
        # roi_y_min = int(torch.floor(torch.min(roi_rotated[:, 1])).item())
        # roi_y_max = int(torch.ceil(torch.max(roi_rotated[:, 1])).item())

        # # 计算新ofROI范围。aroundxaxisRotation，x方to偏移量不考虑
        # # roi_x_min = roi_x_min # - x_offset_max
        # # roi_x_max = roi_x_max #- x_offset_max
        # # roi_y_min = int(roi_y_min - y_min_offset)
        # # roi_y_max = int(roi_y_max - y_max_offset)
        # self.tri_pri_log(f"根据样品倾转角更新后ofROI范围: X({roi_x_min:.1f}, {roi_x_max:.1f}), Y({roi_y_min:.1f}, {roi_y_max:.1f})")
        # # 更新ROI范围
        # self.roi_x_min_spin.setValue(roi_x_min)
        # self.roi_x_max_spin.setValue(roi_x_max)
        # self.roi_y_min_spin.setValue(roi_y_min)
        # self.roi_y_max_spin.setValue(roi_y_max)

        # 收集parameters
        params = {
            'mesh_path': pathlib.Path(self.tri_pri_output_path_edit.text()),
            'pixel_size': self.pixel_size_spin.value(),
            'energy': self.energy_spin.value(),
            'epx': self.epx_spin.value(),
            'sigma': self.sigma_spin.value(),
            'poisson': self.poisson_check.isChecked(),
            'use_roi': self.use_roi_checkbox.isChecked(),
            'roi_x_min': self.roi_x_min_spin.value(),
            'roi_x_max': self.roi_x_max_spin.value(),
            'roi_y_min': self.roi_y_min_spin.value(),
            'roi_y_max': self.roi_y_max_spin.value(),
            # 添加d_zmin和d_zmaxparameters
            'd_zmin': self.d_zmin,
            'd_zmax': self.d_zmax
        }
        
        # 清空日志
        #self.tri_pri_log_text.clear()
        
        # 记录d_zmin和d_zmax值
        self.tri_pri_log(f"使用d_zmin: {self.d_zmin}, d_zmax: {self.d_zmax}计算beam_zmax")
       
        # Create并启动工作线程
        sample_tilt = self.sample_tilt_spin.value()
        self.pri_worker = PriGeneratorWorker(params, sample_tilt)
        self.pri_worker.progress_signal.connect(self.tri_pri_log)
        self.pri_worker.finished_signal.connect(self.on_pri_generation_finished)
        self.pri_worker.start()
    
    def on_pri_generation_finished(self, success, message, pri_file_path):
        """generation.prifile完成of回调"""
        
        if success:
            self.tri_pri_log("✅ " + message)
            QMessageBox.information(self, "成功", message)
            
            # 直接使用传递过来ofprifilepath
            self.tri_pri_log(f"使用prifile: {pri_file_path}")
            
            # 填充pathtoinput框
            if pri_file_path:
                self.pri_input.setText(pri_file_path)
        else:
            self.tri_pri_log("❌ " + message)
            QMessageBox.critical(self, "错误", message)
            return
        

    def run_nebula_gpu(self):
        nebula_gpu_path = self.nebula_gpu_input.text()
        tri_path = self.tri_input.text()
        pri_path = self.pri_input.text()
        mat_paths = self.mat_input.text()
        output_path = self.output_path_input.text()

        if not nebula_gpu_path:
            QMessageBox.warning(self, "警告", "请Select nebula_gpu 可执行filepath！")
            return
        if not tri_path:
            QMessageBox.warning(self, "警告", "请Select .tri filepath！")
            return
        if not pri_path:
            QMessageBox.warning(self, "警告", "请Select .pri filepath！")
            return
        if not mat_paths:
            QMessageBox.warning(self, "警告", "请Select .mat filepath！")
            return
        if not output_path:
            QMessageBox.warning(self, "警告", "请Selectoutputfilepath！")
            return

        mat_paths_list = [f'"{path.strip()}"' for path in mat_paths.split(",")]
        mat_paths_quoted = " ".join(mat_paths_list)
        command = f"{nebula_gpu_path} {tri_path} {pri_path} {mat_paths_quoted} > {output_path}"
        image_path = str(pathlib.Path(tri_path).with_suffix(".png"))
        self.log_output.clear()
        self.log_output.appendPlainText(f"运行命令: {command}")

        self.worker_thread = WorkerThread(command, output_path,image_path=image_path)
        self.worker_thread.log_signal.connect(self.log_output.appendPlainText)
        self.worker_thread.start()


class WorkerThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, command, output_file="output.det",image_path=None):
        super().__init__()
        self.command = command
        self.output_file = output_file
        self.image_path = image_path
    def run(self):
        #try:
        import select
        import time
        import re
        process = subprocess.Popen(
            self.command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=0  # 无缓冲模式
        )

        progress_completed = False
        progress_100_time = None
        # 使用 select Monitor标准output和错误
        while True:
            reads = [process.stdout.fileno(), process.stderr.fileno()]
            ret = select.select(reads, [], [])
            for fd in ret[0]:                                           
                if fd == process.stderr.fileno():
                    error = process.stderr.readline()
                    if error:
                        error_stripped = error.strip()
                        self.log_signal.emit(error_stripped)
                        # 检测是否为detected: 0
                        if "running: 0 | detected: 0" in error_stripped:
                            message = "检测todetected: 0，需要对input进行优化"
                            self.log_signal.emit(message)
                            process.terminate()
                            return_code = 1
                            message2 = "nebula_gpu 运行结束，未检测to有效数据，请优化input"
                            self.log_signal.emit(message2)
                            return
                        
                        # 检测进degrees是否为100.00%
                        if "Progress 100.00%" in error_stripped and not progress_completed:                       
                            message = "检测to进degrees100.00%，Converton20秒后终止进程并展示结果"
                            self.log_signal.emit(message)
                            progress_completed = True
                            progress_100_time = time.time()
                            
                        # if已经检测to100%进degrees且已经过了5秒，则终止进程
                        if progress_completed and progress_100_time is not None and time.time() - progress_100_time >= 20:
                            message1 = "if等待20秒完成，进程未自然结束，则终止进程并展示结果"
                            self.log_signal.emit(message1)
                            process.terminate()
                            message2 = "nebula_gpu 运行成功！"
                            self.log_signal.emit(message2)
                            self.show_image()
                            return

            # 检查进程是否自然结束
            if process.poll() is not None:
                message2 = "nebula_gpu 运行成功！"
                self.log_signal.emit(message2)
                self.show_image()
                break

        # except Exception as e:
        #     error_msg = f"调用 nebula_gpu 时发生异常: {str(e)}"
        #     print(f"[ERROR] {error_msg}")  # on终端打印异常信息
        #     self.log_signal.emit(error_msg)
            
    def show_image(self):
        # 自动调用 sem-analysis.py
        try:
            self.log_signal.emit(f"开始调用 sem-analysis.py 展示图像，outputfile: {self.output_file}")
            
            # 定义脚本path
            import os
            import sys
            
            # Get当前脚本所ondirectory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            primary_script_path = os.path.join(current_dir, "sem-analysis.py")
            
            # if当前directory下没有，则尝试使用相对path
            if not os.path.exists(primary_script_path):
                primary_script_path = "sem-analysis.py"
            
            # 使用系统Python解释器
            python_path = sys.executable
            
            # 检查主要path是否存on
            if not os.path.exists(primary_script_path):
                self.log_signal.emit(f"未找to sem-analysis.py，请确保该fileon当前directory或指定path下")
                return
            else:
                script_path = primary_script_path
                
            analysis_process = subprocess.Popen(
                [python_path, script_path, self.output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0
            )
            for output in analysis_process.stdout:
                if output:
                    output_stripped = output.strip()
                    self.log_signal.emit(output_stripped)
            
            # 过滤GTK警告信息
            for error in analysis_process.stderr:
                if error:
                    error_stripped = error.strip()
                    # 过滤掉GTK相关of警告信息
                    if not ("Gtk-CRITICAL" in error_stripped or 
                            "gtk_tree_view_scroll_to_cell" in error_stripped or
                            "assertion" in error_stripped):
                        self.log_signal.emit(error_stripped)
            analysis_process.wait()
            self.log_signal.emit(f"sem-analysis.py 执行完成，Returns码: {analysis_process.returncode}")
        except Exception as e:
            error_msg = f"调用 sem-analysis.py 时发生异常: {str(e)}"
            self.log_signal.emit(error_msg)
       
class PriGeneratorWorker(QThread):
    """工作线程，仅用于generation.prifile"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, str)  # 成功标志, 消息, prifilepath
    
    def __init__(self, params, sample_tilt=0):
        super().__init__()
        self.params = params
        self.pri_file_path = None  # 用于存储generationofprifilepath
        # 添加d_zmax和d_zminparameters
        self.d_zmax = params.get('d_zmax', 0)
        self.d_zmin = params.get('d_zmin', 0)
        self.R = None  # Initialize rotation matrix
        self.sample_tilt = sample_tilt  # 存储传递ofsample_tilt值
        
    def run(self):
        try:
            # 提取parameters
            mesh_path = self.params['mesh_path']
            #beam_type = self.params.get('beam_type', 'electron_beam')
            pixel_size = self.params['pixel_size']
            energy = self.params['energy']
            epx = self.params['epx']
            sigma = self.params['sigma']
            poisson = self.params['poisson']
            use_roi = self.params['use_roi']
            roi_x_min = self.params['roi_x_min']
            roi_x_max = self.params['roi_x_max']
            roi_y_min = self.params['roi_y_min']
            roi_y_max = self.params['roi_y_max']
            
            
            self.progress_signal.emit("正ongeneration.prifile...")
            
            # 计算pixels数量
            x_pixel_num = int((np.abs(roi_x_max)+np.abs(roi_x_min))/pixel_size+1)
            y_pixel_num = int((np.abs(roi_y_max)+np.abs(roi_y_min))/pixel_size+1)
            
            self.progress_signal.emit(f"pixels数量: {x_pixel_num} x {y_pixel_num}")
            
            # generationpixels坐标
            xpx = np.linspace(roi_x_min, roi_x_max, x_pixel_num)
            ypx = np.linspace(roi_y_min, roi_y_max, y_pixel_num)
            
            # Set束入射方to
            beam_incident_dir = np.array([0, 0, -1])
            
            self.progress_signal.emit(f"束入射方to: {beam_incident_dir}")
            
            # generation.prifile
            pri_file_path = mesh_path/'sem.pri'
            try:
                # 计算束ofz位置，使用tri类传出ofd_zmax和d_zmin值
                beam_zmax = (self.d_zmax + self.d_zmin) / 2
                self.progress_signal.emit(f"束z位置: {beam_zmax}")
                
                generate_sem_pri_data(
                    z=beam_zmax,  # 使用tri类传出ofd_zmax值计算ofbeam_zmax
                    xpx=xpx,
                    ypx=ypx,
                    energy=energy,
                    epx=epx,
                    sigma=sigma,
                    poisson=poisson,
                    dx=beam_incident_dir[0],
                    dy=beam_incident_dir[1],
                    dz=beam_incident_dir[2],
                    file_path=pri_file_path
                )
                
                # 验证.prifile是否成功generation
                if not pri_file_path.exists():
                    raise Exception("未generation.prifile")
                
                self.pri_file_path = str(pri_file_path)
                
                self.progress_signal.emit(f"✅成功generation.prifile: {self.pri_file_path}")
                self.finished_signal.emit(True, "成功generation.prifile", self.pri_file_path)

            except Exception as e:
                error_msg = f"generation.prifile时发生错误: {str(e)}"
                self.progress_signal.emit(f"❌ {error_msg}")
                self.finished_signal.emit(False, error_msg, "")
            
        except Exception as e:
            import traceback
            error_msg = f"发生错误: {str(e)}\n{traceback.format_exc()}"
            self.progress_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg, "")


class TriGeneratorWorker(QThread):
    """工作线程，仅用于generation.trifile"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, str)  # 成功标志, 消息, trifilepath
    update_pixel_range_signal = pyqtSignal(int, int, int, int)  # x_min, x_max, y_min, y_max
    
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.tri_file_path = None  # 用于存储generationoftrifilepath
        self.d_zmin = 0  # Initialized_zmin
        self.d_zmax = 0  # Initialized_zmax
        self.R = None  # Initialize rotation matrix
        #self.v_orig = None  # Initialize原始顶点

    def run(self):
        try:
            # 提取parameters
            voxel_path = self.params['voxel_path']
            mesh_path = self.params['mesh_path']
            beam_type = self.params.get('beam_type', 'electron_beam')
            sample_tilt_x = self.params['sample_tilt_x']
            sample_tilt_new_z = self.params['sample_tilt_new_z']
            det_tilt_x = self.params['det_tilt_x']
            
            # Set样品倾转角和探测器倾转角
            if beam_type == "ion_beam":
                # Ion beam imaging
                sample_tilt_x = 0 if sample_tilt_x is None else sample_tilt_x
                det_tilt_x = 0  # 离子束模式下固定探测器倾转角为0
            else:
                # Electron beam imaging
                sample_tilt_x = 0 if sample_tilt_x is None else sample_tilt_x
                det_tilt_x = 76.8 if det_tilt_x is None else det_tilt_x
            
            self.progress_signal.emit(f"开始处理：{voxel_path}")
            self.progress_signal.emit(f"样品倾转角: {sample_tilt_x}°, 样品新Zaxisrotation angle: {sample_tilt_new_z}°, 探测器倾转角: {det_tilt_x}°")
            
            # generation.trifile
            self.progress_signal.emit("正ongeneration.trifile...")
            try:
                v, faces, d_zmin, d_zmax, tri_file_path,R = run_interface(
                    voxel_path, 
                    mesh_path, 
                    sample_tilt_x=sample_tilt_x, 
                    sample_tilt_new_z=sample_tilt_new_z,
                    det_tilt_x=det_tilt_x
                )
                
                # 保存d_zmin和d_zmax值
                self.d_zmin = d_zmin
                self.d_zmax = d_zmax
                self.R = R
                #self.v_orig = v_orig  # 保存原始顶点

                self.progress_signal.emit(f"d_zmin: {d_zmin}, d_zmax: {d_zmax}")
                
                if v is None or faces is None:
                    self.progress_signal.emit("❌ generation.trifile失败")
                    self.finished_signal.emit(False, "generation.trifile失败", "")
                    return
                
                self.progress_signal.emit(f"✅成功generation.trifile: {tri_file_path}")
                # 保存.trifilepath并转换为字符串类型
                self.tri_file_path = str(tri_file_path)
                
                # 计算pixels范围
                x_min = int(torch.floor(torch.min(v[:, 0])).item())
                x_max = int(torch.ceil(torch.max(v[:, 0])).item())   
                y_min = int(torch.floor(torch.min(v[:, 1])).item())
                y_max = int(torch.ceil(torch.max(v[:, 1])).item())   
                
                self.progress_signal.emit(f"x_min, x_max, y_min, y_max = {x_min}, {x_max}, {y_min}, {y_max}")
                
                # 发送信号更新GUI中ofpixels范围标签
                self.update_pixel_range_signal.emit(x_min, x_max, y_min, y_max)
                
                # 完成
                self.finished_signal.emit(True, "成功generation.trifile", self.tri_file_path)

            except Exception as e:
                self.progress_signal.emit(f"❌ generation.trifile时发生异常: {str(e)}")
                self.finished_signal.emit(False, f"generation.trifile时发生异常: {str(e)}", "")
                return
                
        except Exception as e:
            import traceback
            error_msg = f"发生错误: {str(e)}\n{traceback.format_exc()}"
            self.progress_signal.emit(error_msg)
            self.finished_signal.emit(False, error_msg, "")




if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NebulaGUI()
    window.show()
    sys.exit(app.exec())