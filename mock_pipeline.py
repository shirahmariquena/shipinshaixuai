import time
import random
import logging

class MockPipeline:
    """模拟视频处理流水线"""
    
    def __init__(self, logger=None):
        """初始化流水线"""
        self.logger = logger or logging.getLogger("MockPipeline")
    
    def process_video(self, video_path, job_keywords, candidate_name):
        """
        处理视频并返回评分结果
        
        参数:
        video_path (str): 视频文件路径
        job_keywords (list): 职位关键词列表
        candidate_name (str): 候选人姓名
        
        返回:
        dict: 包含评分和分析结果的字典
        """
        self.logger.info(f"开始处理视频: {video_path}")
        self.logger.info(f"候选人: {candidate_name}")
        self.logger.info(f"职位关键词: {', '.join(job_keywords)}")
        
        # 模拟处理时间
        self.logger.info("提取视频特征...")
        time.sleep(1)
        
        # 模拟视觉分析
        self.logger.info("分析视觉表现...")
        visual_score = round(random.uniform(6.0, 9.5), 2)
        time.sleep(0.5)
        
        # 模拟音频分析
        self.logger.info("分析音频表现...")
        audio_score = round(random.uniform(6.0, 9.5), 2)
        time.sleep(0.5)
        
        # 模拟内容分析
        self.logger.info("分析内容相关性...")
        content_score = round(random.uniform(6.0, 9.5), 2)
        time.sleep(0.5)
        
        # 计算总分
        overall_score = round((visual_score + audio_score + content_score) / 3, 2)
        
        # 生成优势和改进点
        strengths = self._generate_strengths(visual_score, audio_score, content_score, job_keywords)
        improvements = self._generate_improvements(visual_score, audio_score, content_score)
        
        self.logger.info(f"完成视频分析, 总分: {overall_score}")
        
        return {
            "candidate_name": candidate_name,
            "video_path": video_path,
            "job_keywords": job_keywords,
            "scores": {
                "overall_score": overall_score,
                "component_scores": {
                    "visual": visual_score,
                    "audio": audio_score,
                    "content": content_score
                },
                "strengths": strengths,
                "improvements": improvements
            }
        }
    
    def _generate_strengths(self, visual_score, audio_score, content_score, keywords):
        """生成候选人优势点"""
        strengths = []
        
        if visual_score > 8.0:
            strengths.append("良好的非语言表达能力和自信的肢体语言")
        
        if audio_score > 8.0:
            strengths.append("清晰的口头表达和良好的语音节奏")
        
        if content_score > 8.0:
            strengths.append(f"对{random.choice(keywords)}领域展示了专业知识")
        
        if len(strengths) == 0:
            strengths.append("表现平稳且专业")
        
        return strengths
    
    def _generate_improvements(self, visual_score, audio_score, content_score):
        """生成候选人改进点"""
        improvements = []
        
        if visual_score < 7.5:
            improvements.append("可以改善视觉表现，包括眼神接触和肢体语言")
        
        if audio_score < 7.5:
            improvements.append("可以提高语音清晰度和表达流畅性")
        
        if content_score < 7.5:
            improvements.append("可以增加专业术语使用和具体案例分析")
        
        if len(improvements) == 0:
            improvements.append("可以进一步提升回答的结构性")
        
        return improvements
