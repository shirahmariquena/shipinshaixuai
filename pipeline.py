import logging
import os
from modules.video_extractor import VideoFrameExtractor
from modules.audio_extractor import AudioExtractorTranscriber
from modules.visual_analyzer import VisualAnalyzer
from modules.audio_analyzer import AudioAnalyzer
from modules.content_analyzer import ContentAnalyzer
from modules.scorer import Scorer

class Pipeline:
    """视频筛选系统主流水线，整合所有分析模块"""
    
    def __init__(self, logger=None):
        """初始化流水线及其组件"""
        self.logger = logger or logging.getLogger("Pipeline")
        self.logger.info("初始化视频筛选流水线...")
        
        # 初始化各个模块
        self.video_extractor = VideoFrameExtractor()
        self.audio_extractor = AudioExtractorTranscriber()
        self.visual_analyzer = VisualAnalyzer()
        self.audio_analyzer = AudioAnalyzer()
        self.content_analyzer = ContentAnalyzer()
        self.scorer = Scorer()
        
        self.logger.info("流水线初始化完成")
    
    def process_video(self, video_path, job_keywords, candidate_name):
        """
        处理视频并生成评估结果
        
        参数:
        video_path (str): 视频文件路径
        job_keywords (list): 职位关键词列表
        candidate_name (str): 候选人姓名
        
        返回:
        dict: 包含评分和分析结果的字典
        """
        result = {
            "candidate_name": candidate_name,
            "video_path": video_path,
            "job_keywords": job_keywords,
        }
        
        self.logger.info(f"开始处理视频: {video_path}")
        self.logger.info(f"候选人: {candidate_name}")
        self.logger.info(f"职位关键词: {', '.join(job_keywords)}")
        
        try:
            # 步骤1: 提取视频帧
            self.logger.info("提取视频帧...")
            frames, metadata = self.video_extractor.extract_frames(video_path)
            result["metadata"] = metadata
            
            # 步骤2: 提取和转录音频
            self.logger.info("提取和转录音频...")
            audio_path, transcript, chunks = self.audio_extractor.process(video_path)
            result["transcript"] = transcript
            result["transcript_chunks"] = chunks
            
            # 步骤3: 视觉分析
            self.logger.info("进行视觉分析...")
            visual_features = self.visual_analyzer.analyze(frames)
            result["visual_features"] = visual_features
            
            # 步骤4: 音频分析
            self.logger.info("进行音频分析...")
            audio_features = self.audio_analyzer.analyze(audio_path)
            result["audio_features"] = audio_features
            
            # 步骤5: 内容分析
            self.logger.info("进行内容分析...")
            content_features = self.content_analyzer.analyze(transcript, job_keywords)
            result["content_features"] = content_features
            
            # 步骤6: 计算得分
            self.logger.info("计算综合评分...")
            scores = self.scorer.calculate_scores(visual_features, audio_features, content_features)
            result["scores"] = scores
            
            self.logger.info(f"视频处理完成，总分: {scores['overall_score']:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"处理视频时发生错误: {str(e)}", exc_info=True)
            raise
