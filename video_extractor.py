from vidgear.gears import VideoGear
import cv2
import numpy as np
import os
import logging
from skimage.metrics import structural_similarity

class VideoFrameExtractor:
    def __init__(self, logger=None):
        """
        初始化视频帧提取器。
        
        参数:
            logger: 日志记录器，如果为None则创建一个新的
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def process(self, input_data):
        """
        从视频文件中定期提取帧。
        
        参数:
            input_data (dict): 包含视频路径的'video_path'键，可选'sample_rate'键
        
        返回:
            dict: 包含'frames'（numpy数组列表）和'metadata'（字典）
        """
        video_path = input_data['video_path']
        sample_rate = input_data.get('sample_rate', 5)  # 默认提取每第5帧
        
        if not os.path.exists(video_path):
            self.logger.error(f"视频文件不存在: {video_path}")
            return {'error': f"视频文件不存在: {video_path}"}
        
        try:
            # 初始化视频流
            video = VideoGear(source=video_path).start()
            
            # 提取帧和元数据
            frames = []
            frame_count = 0
            frame_indices = []
            
            while True:
                frame = video.read()
                if frame is None:
                    break
                    
                if frame_count % sample_rate == 0:
                    frames.append(frame.copy())  # 创建一个副本以避免潜在的引用问题
                    frame_indices.append(frame_count)
                    
                frame_count += 1
            
            # 停止视频流
            video.stop()
            
            # 获取视频元数据
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.logger.error(f"无法打开视频文件: {video_path}")
                return {'error': f"无法打开视频文件: {video_path}"}
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            
            # 准备输出
            metadata = {
                'fps': fps,
                'width': width,
                'height': height,
                'total_frames': total_frames,
                'duration_seconds': duration,
                'sample_rate': sample_rate,
                'frame_indices': frame_indices,
                'extracted_frames_count': len(frames)
            }
            
            self.logger.info(f"成功从 {video_path} 提取了 {len(frames)} 帧")
            
            return {
                'frames': frames,
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"视频帧提取失败: {str(e)}")
            return {'error': f"视频帧提取失败: {str(e)}"}
    
    def extract_keyframes(self, input_data):
        """
        从视频文件中提取关键帧，使用内容差异分析。
        
        参数:
            input_data (dict): 包含视频路径的'video_path'键，可选'threshold'键
        
        返回:
            dict: 包含'frames'（numpy数组列表）和'metadata'（字典）
        """
        video_path = input_data['video_path']
        threshold = input_data.get('threshold', 30.0)  # 默认阈值
        
        try:
            # 初始化视频流
            cap = cv2.VideoCapture(video_path)
            
            frames = []
            frame_indices = []
            prev_frame = None
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 第一帧总是关键帧
                if prev_frame is None:
                    frames.append(frame.copy())
                    frame_indices.append(frame_count)
                else:
                    # 计算当前帧与前一帧的差异
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                    
                    # 使用结构相似性指数 (SSIM)
                    score, _ = structural_similarity(gray_prev, gray_frame, full=True)
                    diff_score = (1.0 - score) * 100  # 转换为差异百分比
                    
                    # 如果差异大于阈值，认为是关键帧
                    if diff_score > threshold:
                        frames.append(frame.copy())
                        frame_indices.append(frame_count)
                
                prev_frame = frame
                frame_count += 1
            
            # 获取视频元数据
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            cap.release()
            
            metadata = {
                'fps': fps,
                'width': width,
                'height': height,
                'total_frames': total_frames,
                'duration_seconds': duration,
                'threshold': threshold,
                'frame_indices': frame_indices,
                'extracted_frames_count': len(frames)
            }
            
            self.logger.info(f"成功从 {video_path} 提取了 {len(frames)} 个关键帧")
            
            return {
                'frames': frames,
                'metadata': metadata
            }
            
        except Exception as e:
            self.logger.error(f"关键帧提取失败: {str(e)}")
            return {'error': f"关键帧提取失败: {str(e)}"}