from transformers import pipeline
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import numpy as np
import re
import logging
import os
import json
from collections import Counter

class ContentAnalyzer:
    def __init__(self, language="english", logger=None):
        """
        初始化内容分析器。
        
        参数:
            language: 分析的语言，默认为英语
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self.language = language
        
        self.logger.info("初始化内容分析器...")
        
        # 初始化NLTK组件
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.logger.info("NLTK组件加载成功")
            
            if language.lower() == "chinese" or language.lower() == "zh":
                self.language = "chinese"
                # 中文分析可能需要不同的模型
                self.sentiment_analyzer = pipeline("sentiment-analysis", model="uer/roberta-base-finetuned-jd-binary-chinese")
                self.logger.info("加载中文情感分析模型")
            else:
                self.language = "english"
                # 初始化情感分析模型
                self.sentiment_analyzer = pipeline("sentiment-analysis")
                self.logger.info("加载英文情感分析模型")
                
            # 加载零件词库
            self.stopwords = set(stopwords.words(self.language)) if self.language == "english" else set()
            
        except Exception as e:
            self.logger.error(f"初始化组件失败: {str(e)}")
            raise
    
    def process(self, input_data):
        """
        分析转录内容的工作相关性和质量。
        
        参数:
            input_data (dict): 包含'transcript'文本，可选包含'job_keywords'和'job_description'
        
        返回:
            dict: 包含内容分析指标
        """
        transcript = input_data['transcript']
        job_keywords = input_data.get('job_keywords', [
            "streaming", "content", "media", "production", "digital", "creative"
        ])
        
        job_description = input_data.get('job_description', '')
        
        self.logger.info(f"开始分析转录内容，长度: {len(transcript)} 字符")
        
        # 确保转录不为空
        if not transcript or len(transcript.strip()) == 0:
            self.logger.warning("转录内容为空，返回默认分数")
            return {
                'keyword_relevance': 0.0,
                'confidence': 0.0,
                'clarity': 0.0,
                'matched_keywords': [],
                'sentence_count': 0,
                'word_count': 0
            }
        
        try:
            # 计算关键词相关性
            keyword_results = self._analyze_keywords(transcript, job_keywords)
            
            # 使用情感分析计算信心
            confidence_score, sentiment_details = self._analyze_sentiment(transcript)
            
            # 计算清晰度指标
            clarity_results = self._calculate_clarity(transcript)
            
            # 分析主题相关性（如果有职位描述）
            topic_relevance = 0.0
            topic_analysis = {}
            if job_description:
                topic_relevance, topic_analysis = self._analyze_topic_relevance(transcript, job_description)
            
            # 计算总体内容质量分数
            content_quality = (clarity_results['clarity'] * 0.4) + \
                             (confidence_score * 0.3) + \
                             (keyword_results['keyword_relevance'] * 0.2) + \
                             (topic_relevance * 0.1)
            
            # 生成内容分析评级和解释
            ratings = self._generate_ratings({
                'keyword_relevance': keyword_results['keyword_relevance'],
                'confidence': confidence_score,
                'clarity': clarity_results['clarity'],
                'sentence_complexity': clarity_results['sentence_complexity'],
                'content_quality': content_quality,
                'matched_keywords': keyword_results['matched_keywords'],
                'topic_relevance': topic_relevance
            })
            
            # 组合所有结果
            result = {
                **keyword_results,
                'confidence': confidence_score,
                'sentiment_details': sentiment_details,
                **clarity_results,
                'content_quality': content_quality,
                'ratings': ratings
            }
            
            # 如果分析了主题相关性，添加到结果
            if job_description:
                result['topic_relevance'] = topic_relevance
                result['topic_analysis'] = topic_analysis
            
            self.logger.info("内容分析完成")
            return result
            
        except Exception as e:
            self.logger.error(f"内容分析出错: {str(e)}")
            return {
                'error': str(e),
                'keyword_relevance': 0.0,
                'confidence': 0.0,
                'clarity': 0.0,
                'matched_keywords': [],
                'sentence_count': 0,
                'word_count': 0
            }
    
    def _analyze_keywords(self, transcript, job_keywords):
        """分析关键词匹配度"""
        transcript_lower = transcript.lower()
        
        # 关键词匹配 - 检查每个关键词出现的次数
        keyword_counts = {}
        matched_keywords = []
        
        for keyword in job_keywords:
            keyword_lower = keyword.lower()
            count = transcript_lower.count(keyword_lower)
            if count > 0:
                matched_keywords.append(keyword)
                keyword_counts[keyword] = count
        
        # 计算关键词匹配度
        keyword_relevance = len(matched_keywords) / len(job_keywords) if job_keywords else 0
        
        # 提取高频词汇（排除停用词）
        if self.language == "english":
            words = word_tokenize(transcript_lower)
            filtered_words = [w for w in words if w.isalnum() and w not in self.stopwords]
        else:
            # 简单的中文分词（实际应用可能需要更复杂的分词库）
            filtered_words = list(transcript_lower)
        
        word_freq = Counter(filtered_words).most_common(10)
        
        return {
            'keyword_relevance': keyword_relevance,
            'matched_keywords': matched_keywords,
            'keyword_counts': keyword_counts,
            'top_words': word_freq
        }
    
    def _analyze_sentiment(self, transcript):
        """分析情感和信心"""
        # 对于长文本，分段分析可能更准确
        max_length = 512  # 适应模型的最大长度限制
        segments = []
        
        sentences = sent_tokenize(transcript)
        current_segment = ""
        
        for sentence in sentences:
            if len(current_segment + " " + sentence) <= max_length:
                current_segment += " " + sentence if current_segment else sentence
            else:
                segments.append(current_segment)
                current_segment = sentence
        
        if current_segment:
            segments.append(current_segment)
        
        # 分析每个段落
        sentiment_scores = []
        segment_results = []
        
        for segment in segments:
            result = self.sentiment_analyzer(segment)[0]
            
            # 根据不同模型调整标签
            if self.language == "chinese":
                # 假设中文模型使用 "positive"/"negative" 标签
                is_positive = result['label'].lower() == 'positive'
                score = result['score'] if is_positive else 1 - result['score']
            else:
                # 英文模型使用 "POSITIVE"/"NEGATIVE" 标签
                is_positive = result['label'] == 'POSITIVE'
                score = result['score'] if is_positive else 0.5 - (result['score'] - 0.5)
            
            sentiment_scores.append(score)
            segment_results.append({
                'text': segment[:50] + '...' if len(segment) > 50 else segment,
                'sentiment': result['label'],
                'confidence_score': score,
                'raw_score': result['score']
            })
        
        # 计算平均信心分数
        confidence_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
        
        return confidence_score, {
            'segments': segment_results,
            'overall_sentiment': 'POSITIVE' if confidence_score > 0.6 else 'NEUTRAL' if confidence_score > 0.4 else 'NEGATIVE'
        }
    
    def _calculate_clarity(self, transcript):
        """计算清晰度指标"""
        # 分割句子和词
        sentences = sent_tokenize(transcript)
        sentence_count = len(sentences)
        
        if self.language == "english":
            words = re.findall(r'\b\w+\b', transcript)
        else:
            # 简单的中文词计数（在实际应用中可以使用更复杂的分词器）
            words = list(re.sub(r'[^\u4e00-\u9fa5]', '', transcript))
        
        word_count = len(words)
        
        # 计算每句话的词数
        words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
        
        # 基于句子长度的清晰度评分
        if words_per_sentence == 0:
            clarity_score = 0
        elif self.language == "english":
            # 英文句子长度标准
            if words_per_sentence < 5:
                clarity_score = 0.5  # 句子太短
            elif words_per_sentence <= 20:
                clarity_score = 1.0  # 理想长度
            else:
                clarity_score = 1.0 - min(1.0, (words_per_sentence - 20) / 15)  # 减分过长句子
        else:
            # 中文句子长度标准 (字符更少)
            if words_per_sentence < 3:
                clarity_score = 0.5  # 句子太短
            elif words_per_sentence <= 15:
                clarity_score = 1.0  # 理想长度
            else:
                clarity_score = 1.0 - min(1.0, (words_per_sentence - 15) / 10)  # 减分过长句子
        
        # 分析句子复杂度
        sentence_lengths = [len(re.findall(r'\b\w+\b', s)) if self.language == "english" 
                          else len(re.sub(r'[^\u4e00-\u9fa5]', '', s)) for s in sentences]
        
        sentence_complexity = min(1.0, np.mean(sentence_lengths) / (25 if self.language == "english" else 15))
        
        # 分析词汇多样性
        unique_words = len(set(w.lower() for w in words))
        vocabulary_richness = min(1.0, unique_words / (word_count * 0.7)) if word_count > 0 else 0
        
        return {
            'clarity': clarity_score,
            'sentence_complexity': sentence_complexity,
            'vocabulary_richness': vocabulary_richness,
            'sentence_count': sentence_count,
            'word_count': word_count,
            'words_per_sentence': words_per_sentence,
            'unique_words': unique_words
        }
    
    def _analyze_topic_relevance(self, transcript, job_description):
        """分析与职位描述的主题相关性"""
        # 简化实现 - 基于关键词匹配
        # 在实际系统中可以使用词向量或主题模型
        
        # 提取职位描述中的关键词（简单方法）
        if self.language == "english":
            job_words = word_tokenize(job_description.lower())
            job_words = [w for w in job_words if w.isalnum() and w not in self.stopwords]
        else:
            # 简单的中文分词
            job_words = list(re.sub(r'[^\u4e00-\u9fa5]', '', job_description))
            
        # 计算关键词频率
        job_word_freq = Counter(job_words)
        top_job_words = job_word_freq.most_common(20)
        
        # 提取转录文本中的关键词
        if self.language == "english":
            transcript_words = word_tokenize(transcript.lower())
            transcript_words = [w for w in transcript_words if w.isalnum() and w not in self.stopwords]
        else:
            transcript_words = list(re.sub(r'[^\u4e00-\u9fa5]', '', transcript))
            
        transcript_word_freq = Counter(transcript_words)
        
        # 计算职位关键词在转录中的匹配度
        matched_words = 0
        total_job_keywords = sum(count for _, count in top_job_words)
        
        for word, count in top_job_words:
            if word in transcript_word_freq:
                matched_words += min(count, transcript_word_freq[word])
        
        # 计算相关性得分
        relevance_score = matched_words / total_job_keywords if total_job_keywords > 0 else 0
        
        return relevance_score, {
            'top_job_keywords': top_job_words,
            'matched_words': matched_words,
            'total_job_keywords': total_job_keywords
        }
    
    def _generate_ratings(self, metrics):
        """生成评分和解释"""
        # 提取指标
        keyword_relevance = metrics['keyword_relevance']
        confidence = metrics['confidence']
        clarity = metrics['clarity']
        content_quality = metrics['content_quality']
        matched_keywords = metrics['matched_keywords']
        
        # 将分数转换为1-5星级
        keyword_rating = round(keyword_relevance * 5)
        confidence_rating = round(confidence * 5)
        clarity_rating = round(clarity * 5)
        overall_rating = round(content_quality * 5)
        
        # 确保最低评分为1星
        keyword_rating = max(1, keyword_rating)
        confidence_rating = max(1, confidence_rating)
        clarity_rating = max(1, clarity_rating)
        overall_rating = max(1, overall_rating)
        
        # 生成解释文字
        explanations = []
        
        # 关键词相关性解释
        if keyword_relevance < 0.2:
            keyword_comment = "内容中几乎没有包含职位相关的关键词，与职位的相关性很低。"
        elif keyword_relevance < 0.5:
            keyword_comment = f"内容包含了部分职位相关关键词 ({', '.join(matched_keywords[:3])})，但相关性不够强。"
        else:
            keyword_comment = f"内容很好地包含了职位相关关键词 ({', '.join(matched_keywords[:5])})，表现出对职位的理解。"
        
        # 信心解释
        if confidence < 0.4:
            confidence_comment = "语气缺乏自信，可能给人留下犹豫不决的印象。"
        elif confidence < 0.7:
            confidence_comment = "语气适中，展现了一定程度的自信。"
        else:
            confidence_comment = "语气自信有力，能够给人留下积极正面的印象。"
        
        # 清晰度解释
        if clarity < 0.4:
            clarity_comment = "表达不够清晰，句子结构可能过于简单或过于复杂。"
        elif clarity < 0.7:
            clarity_comment = "表达较为清晰，句子结构适中。"
        else:
            clarity_comment = "表达非常清晰，句子结构适合有效沟通。"
        
        # 总体评价
        if content_quality < 0.4:
            overall_comment = "内容质量有待提高，建议增加与职位相关的关键词和提升表达清晰度。"
        elif content_quality < 0.7:
            overall_comment = "内容质量良好，能够基本满足要求，但仍有提升空间。"
        else:
            overall_comment = "内容质量优秀，展现了对职位的理解和良好的表达能力。"
        
        return {
            'keyword_rating': keyword_rating,
            'confidence_rating': confidence_rating,
            'clarity_rating': clarity_rating,
            'overall_rating': overall_rating,
            'comments': {
                'keyword': keyword_comment,
                'confidence': confidence_comment,
                'clarity': clarity_comment,
                'overall': overall_comment
            }
        }
