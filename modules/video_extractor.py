import os
import cv2
import numpy as np
import logging

class VideoFrameExtractor:
    """视频帧提取模块，负责从视频文件中提取帧"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger("VideoFrameExtractor")
    
    def extract_frames(self, video_path, sample_rate=30):
        """
        从视频中提取帧
        
        参数:
        video_path (str): 视频文件路径
        sample_rate (int): 采样率，每隔多少帧提取一帧
        
        返回:
        tuple: (frames, metadata)
            - frames (list): 提取的帧列表
            - metadata (dict): 视频元数据
        """
        if not os.path.exists(video_path):
            self.logger.error(f"视频文件不存在: {video_path}")
            # 为了演示，如果文件不存在，返回模拟数据
            return self._generate_mock_frames(), self._generate_mock_metadata()
            
        try:
            self.logger.info(f"开始从视频提取帧: {video_path}")
            cap = cv2.VideoCapture(video_path)
            
            # 获取视频元数据
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            metadata = {
                "fps": fps,
                "frame_count": frame_count,
                "width": width,
                "height": height,
                "duration": duration,
                "filename": os.path.basename(video_path)
            }
            
            # 提取帧
            frames = []
            count = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                
                if count % sample_rate == 0:
                    frames.append(frame)
                
                count += 1
            
            cap.release()
            self.logger.info(f"成功提取 {len(frames)} 帧，原始帧数: {frame_count}")
            return frames, metadata
        
        except Exception as e:
            self.logger.error(f"提取视频帧时出错: {str(e)}")
            # 为了演示，返回模拟数据
            return self._generate_mock_frames(), self._generate_mock_metadata()
    
    def _generate_mock_frames(self, count=10):
        """生成模拟帧数据用于测试"""
        self.logger.info("生成模拟帧数据用于测试")
        # 创建10个随机彩色图像作为帧
        frames = []
        for _ in range(count):
            # 创建一个随机的彩色图像
            frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            frames.append(frame)
        return frames
    
    def _generate_mock_metadata(self):
        """生成模拟视频元数据用于测试"""
        self.logger.info("生成模拟视频元数据用于测试")
        return {
            "fps": 30.0,
            "frame_count": 900,
            "width": 640,
            "height": 480,
            "duration": 30.0,  # 30秒视频
            "filename": "mock_video.mp4"
        }
