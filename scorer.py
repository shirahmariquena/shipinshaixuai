class Scorer:
    def __init__(self, weights=None):
        """
        初始化评分器，可选指定组件权重。
        
        参数:
            weights (dict, optional): 组件权重的字典
        """
        self.weights = weights or {
            'visual': 0.3,     # 视觉分析权重
            'audio': 0.3,      # 音频分析权重
            'content': 0.4     # 内容分析权重
        }
        
        # 特征权重
        self.feature_weights = {
            # 视觉特征
            'eye_contact': 0.4,
            'posture': 0.3,
            'expression_variation': 0.3,
            
            # 音频特征
            'speaking_rate': 0.25,
            'pitch_variation': 0.25,
            'volume_variation': 0.2,
            'clarity': 0.3,
            
            # 内容特征
            'keyword_relevance': 0.4,
            'confidence': 0.3,
            'clarity': 0.3
        }
    
    def process(self, input_data):
        """
        基于所有分析组件计算分数。
        
        参数:
            input_data (dict): 包含所有分析结果的完整数据对象
        
        返回:
            dict: 包含总体分数和组件分数
        """
        # 确保所有必需的分析结果都存在
        visual_features = input_data.get('visual_features', {})
        audio_features = input_data.get('audio_features', {})
        content_features = input_data.get('content_features', {})
        
        # 计算视觉组件得分（0-100范围）
        visual_score = 0
        if visual_features:
            eye_contact = visual_features.get('eye_contact', 0) * 100
            posture = visual_features.get('posture', 0) * 100
            expression = visual_features.get('expression_variation', 0) * 100
            
            visual_score = (
                (eye_contact * self.feature_weights['eye_contact']) +
                (posture * self.feature_weights['posture']) +
                (expression * self.feature_weights['expression_variation'])
            )
        
        # 计算音频组件得分（0-100范围）
        audio_score = 0
        if audio_features:
            speaking_rate = audio_features.get('speaking_rate', 0) * 100
            pitch_var = audio_features.get('pitch_variation', 0) * 100
            volume_var = audio_features.get('volume_variation', 0) * 100
            audio_clarity = audio_features.get('clarity', 0) * 100
            
            audio_score = (
                (speaking_rate * self.feature_weights['speaking_rate']) +
                (pitch_var * self.feature_weights['pitch_variation']) +
                (volume_var * self.feature_weights['volume_variation']) +
                (audio_clarity * self.feature_weights['clarity'])
            )
        
        # 计算内容组件得分（0-100范围）
        content_score = 0
        if content_features:
            keyword_rel = content_features.get('keyword_relevance', 0) * 100
            confidence = content_features.get('confidence', 0) * 100
            content_clarity = content_features.get('clarity', 0) * 100
            
            content_score = (
                (keyword_rel * self.feature_weights['keyword_relevance']) +
                (confidence * self.feature_weights['confidence']) +
                (content_clarity * self.feature_weights['clarity'])
            )
        
        # 计算总体得分
        overall_score = (
            (visual_score * self.weights['visual']) +
            (audio_score * self.weights['audio']) +
            (content_score * self.weights['content'])
        )
        
        # 生成特征得分
        feature_scores = {}
        
        if visual_features:
            feature_scores['eye_contact'] = eye_contact
            feature_scores['posture'] = posture
            feature_scores['expression'] = expression
            
        if audio_features:
            feature_scores['speaking_rate'] = speaking_rate
            feature_scores['tone_variation'] = pitch_var
            feature_scores['volume_control'] = volume_var
            feature_scores['voice_clarity'] = audio_clarity
            
        if content_features:
            feature_scores['job_relevance'] = keyword_rel
            feature_scores['confidence'] = confidence
            feature_scores['speech_clarity'] = content_clarity
        
        # 生成优势和改进建议
        strengths = []
        improvements = []
        
        # 识别最强和最弱的特征
        if feature_scores:
            sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
            
            # 添加top 3优势
            for feature, score in sorted_features[:3]:
                if score >= 70:  # 高于70分被视为优势
                    strengths.append(feature)
            
            # 添加bottom 3改进点
            for feature, score in sorted_features[-3:]:
                if score < 60:  # 低于60分需要改进
                    improvements.append(feature)
        
        return {
            'overall_score': overall_score,
            'component_scores': {
                'visual': visual_score,
                'audio': audio_score,
                'content': content_score
            },
            'feature_scores': feature_scores,
            'strengths': strengths,
            'improvements': improvements
        }
