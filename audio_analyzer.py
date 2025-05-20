import librosa
import numpy as np
import logging
import os
import matplotlib.pyplot as plt
from scipy.signal import medfilt

class AudioAnalyzer:
    def __init__(self, logger=None):
        """
        初始化音频分析器。
        
        参数:
            logger: 日志记录器实例
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def process(self, input_data):
        """
        分析音频特征以评估说话质量。
        
        参数:
            input_data (dict): 包含音频文件路径的'audio_path'键
        
        返回:
            dict: 包含音频质量指标
        """
        audio_path = input_data['audio_path']
        
        if not os.path.exists(audio_path):
            error_msg = f"音频文件不存在: {audio_path}"
            self.logger.error(error_msg)
            return {'error': error_msg}
        
        try:
            # 加载音频文件
            self.logger.info(f"开始加载音频文件: {audio_path}")
            y, sr = librosa.load(audio_path, sr=None)
            self.logger.info(f"音频加载成功，采样率: {sr}Hz, 时长: {len(y)/sr:.2f}秒")
            
            # 处理静音部分
            y_trimmed, trim_indexes = librosa.effects.trim(y, top_db=25)
            non_silent_duration = len(y_trimmed) / sr
            total_duration = len(y) / sr
            speech_ratio = non_silent_duration / total_duration if total_duration > 0 else 0
            
            self.logger.info(f"有效语音占比: {speech_ratio:.2%}")
            
            # 计算说话速率（节奏）
            self.logger.info("计算说话速率...")
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
            
            # 提取音频特征
            self.logger.info("提取音频特征...")
            
            # 计算音高变化
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitches_nonzero = pitches[pitches > 0]
            pitch_variation = np.std(pitches_nonzero) if len(pitches_nonzero) > 0 else 0
            
            # 计算平均音高 (对人声有意义的区间)
            pitch_mean = np.mean(pitches_nonzero) if len(pitches_nonzero) > 0 else 0
            
            # 计算音量变化
            rms = librosa.feature.rms(y=y)[0]
            volume_variation = np.std(rms)
            volume_mean = np.mean(rms)
            
            # 计算停顿
            # 基于RMS能量的简化算法来检测停顿
            pause_threshold = 0.1 * np.max(rms)
            is_pause = rms < pause_threshold
            pause_count = np.sum(np.diff(is_pause.astype(int)) > 0)
            
            # 使用梅尔频谱系数(MFCC)评估清晰度
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_var = np.mean(np.var(mfccs, axis=1))
            
            # 使用谱质心评估音色
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
            
            # 使用过零率评估杂音
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            zcr_mean = np.mean(zero_crossing_rate)
            
            # 将值归一化到0-1范围
            normalized_tempo = min(1.0, tempo / 240)  # 假设最大合理节奏是240 BPM
            normalized_pitch_var = min(1.0, pitch_variation / 100)  # 归一化音高变化
            normalized_volume_var = min(1.0, volume_variation * 20)  # 归一化音量变化
            normalized_mfcc_var = min(1.0, mfcc_var / 20)  # 归一化MFCC变化
            
            # 计算语音清晰度得分
            clarity_features = [
                normalized_mfcc_var * 0.4,
                normalized_pitch_var * 0.3,
                normalized_volume_var * 0.3
            ]
            clarity_score = sum(clarity_features)
            
            # 评估节奏性和音调变化
            rhythmic_score = min(1.0, (0.5 + (normalized_tempo - 0.4) * 1.5))
            tonal_score = min(1.0, normalized_pitch_var * 2.0)
            
            # 生成评分和解释
            ratings = self._generate_ratings({
                'tempo': normalized_tempo,
                'pitch_variation': normalized_pitch_var,
                'volume_variation': normalized_volume_var,
                'clarity': clarity_score,
                'speech_ratio': speech_ratio
            })
            
            self.logger.info("音频分析完成")
            
            return {
                'speaking_rate': normalized_tempo,
                'pitch_variation': normalized_pitch_var,
                'volume_variation': normalized_volume_var,
                'pause_count': int(pause_count),
                'clarity': clarity_score,
                'speech_ratio': speech_ratio,
                'rhythmic_score': rhythmic_score,
                'tonal_score': tonal_score,
                'raw': {
                    'tempo_bpm': float(tempo),
                    'pitch_std': float(pitch_variation),
                    'pitch_mean': float(pitch_mean),
                    'volume_std': float(volume_variation),
                    'volume_mean': float(volume_mean),
                    'mfcc_var': float(mfcc_var),
                    'spectral_centroid_mean': float(np.mean(spectral_centroid)),
                    'spectral_bandwidth_mean': float(np.mean(spectral_bandwidth)),
                    'zero_crossing_rate': float(zcr_mean),
                    'duration': float(total_duration),
                    'non_silent_duration': float(non_silent_duration)
                },
                'ratings': ratings
            }
        
        except Exception as e:
            error_msg = f"音频分析失败: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def _generate_ratings(self, metrics):
        """
        根据音频分析指标生成评级和解释
        
        参数:
            metrics: 分析指标字典
            
        返回:
            dict: 评级和解释
        """
        # 提取指标
        tempo = metrics['tempo']
        pitch_var = metrics['pitch_variation']
        volume_var = metrics['volume_variation']
        clarity = metrics['clarity']
        speech_ratio = metrics['speech_ratio']
        
        # 评级系统 (1-5星)
        tempo_rating = 3  # 默认中等评分
        if tempo < 0.3:
            tempo_rating = 2  # 说话速度偏慢
            tempo_comment = "说话速度偏慢，可能影响听众注意力"
        elif tempo < 0.45:
            tempo_rating = 3  # 适中
            tempo_comment = "说话速度适中，节奏自然"
        elif tempo < 0.6:
            tempo_rating = 4  # 良好
            tempo_comment = "说话速度流畅自然，节奏感好"
        elif tempo < 0.75:
            tempo_rating = 5  # 优秀
            tempo_comment = "说话速度活力充沛，节奏感强"
        else:
            tempo_rating = 2  # 说话速度过快
            tempo_comment = "说话速度过快，可能影响清晰度和理解"
        
        # 音调变化评分
        if pitch_var < 0.1:
            pitch_rating = 1
            pitch_comment = "语调变化很少，声音较为单调"
        elif pitch_var < 0.3:
            pitch_rating = 3
            pitch_comment = "语调变化适中，表现力一般"
        else:
            pitch_rating = 5
            pitch_comment = "语调变化丰富，表现力强，能很好地表达情感"
        
        # 音量变化评分
        if volume_var < 0.1:
            volume_rating = 2
            volume_comment = "音量变化较小，表现力受限"
        elif volume_var < 0.3:
            volume_rating = 3
            volume_comment = "音量变化适中，声音表现合理"
        else:
            volume_rating = 5
            volume_comment = "音量变化恰当，强调重点，声音富有表现力"
        
        # 清晰度评分
        if clarity < 0.3:
            clarity_rating = 2
            clarity_comment = "发音清晰度有限，可能存在模糊或难以理解的部分"
        elif clarity < 0.6:
            clarity_rating = 3
            clarity_comment = "发音清晰度良好，总体上容易理解"
        else:
            clarity_rating = 5
            clarity_comment = "发音非常清晰，易于理解"
        
        # 总体评分（加权平均）
        weights = [0.25, 0.25, 0.25, 0.25]  # 各项权重
        ratings = [tempo_rating, pitch_rating, volume_rating, clarity_rating]
        overall_score = sum(r * w for r, w in zip(ratings, weights))
        overall_rating = min(5, max(1, round(overall_score)))
        
        # 生成总体评论
        if overall_rating <= 2:
            overall_comment = "说话表现需要提升，建议改善语调变化和清晰度"
        elif overall_rating == 3:
            overall_comment = "说话表现良好，有一定的表现力和清晰度"
        else:
            overall_comment = "说话表现出色，语音富有表现力，清晰度高，能够有效传达信息"
        
        # 语音占比评论
        if speech_ratio < 0.4:
            speech_ratio_comment = "有效语音比例偏低，可能有较多停顿或沉默时间"
        elif speech_ratio < 0.7:
            speech_ratio_comment = "有效语音比例适中，语流自然"
        else:
            speech_ratio_comment = "有效语音比例高，语流连贯"
        
        return {
            'tempo_rating': tempo_rating,
            'pitch_rating': pitch_rating,
            'volume_rating': volume_rating,
            'clarity_rating': clarity_rating,
            'overall_rating': overall_rating,
            'comments': {
                'tempo': tempo_comment,
                'pitch': pitch_comment,
                'volume': volume_comment,
                'clarity': clarity_comment,
                'speech_ratio': speech_ratio_comment,
                'overall': overall_comment
            }
        }
    
    def generate_visualizations(self, audio_path, output_dir):
        """
        为音频分析生成可视化图表
        
        参数:
            audio_path: 音频文件路径
            output_dir: 输出目录
            
        返回:
            dict: 图表文件路径
        """
        if not os.path.exists(audio_path):
            return {'error': f"音频文件不存在: {audio_path}"}
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 加载音频
            y, sr = librosa.load(audio_path, sr=None)
            
            # 准备文件名基础
            base_filename = os.path.splitext(os.path.basename(audio_path))[0]
            
            # 生成波形图
            plt.figure(figsize=(12, 4))
            plt.title('音频波形')
            librosa.display.waveshow(y, sr=sr)
            waveform_path = os.path.join(output_dir, f"{base_filename}_waveform.png")
            plt.tight_layout()
            plt.savefig(waveform_path)
            plt.close()
            
            # 生成频谱图
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
            plt.figure(figsize=(12, 4))
            plt.title('频谱图')
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
            plt.colorbar(format='%+2.0f dB')
            spectrogram_path = os.path.join(output_dir, f"{base_filename}_spectrogram.png")
            plt.tight_layout()
            plt.savefig(spectrogram_path)
            plt.close()
            
            # 生成音高曲线
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            plt.figure(figsize=(12, 4))
            plt.title('音高曲线')
            
            # 提取主要音高并平滑
            pitch_times = librosa.times_like(pitches)
            pitches_max = np.zeros_like(pitch_times)
            
            for i in range(pitches.shape[1]):
                index = magnitudes[:, i].argmax()
                pitch = pitches[index, i]
                if pitch > 0:  # 只考虑有效的音高值
                    pitches_max[i] = pitch
            
            # 应用中值滤波器平滑音高曲线
            pitches_max_smooth = medfilt(pitches_max, kernel_size=15)
            
            # 绘制音高曲线
            plt.plot(pitch_times, pitches_max_smooth)
            plt.xlabel('时间 (秒)')
            plt.ylabel('频率 (Hz)')
            pitch_path = os.path.join(output_dir, f"{base_filename}_pitch.png")
            plt.tight_layout()
            plt.savefig(pitch_path)
            plt.close()
            
            # 生成音量曲线
            rms = librosa.feature.rms(y=y)[0]
            plt.figure(figsize=(12, 4))
            plt.title('音量曲线')
            times = librosa.times_like(rms)
            plt.plot(times, rms)
            plt.xlabel('时间 (秒)')
            plt.ylabel('能量')
            volume_path = os.path.join(output_dir, f"{base_filename}_volume.png")
            plt.tight_layout()
            plt.savefig(volume_path)
            plt.close()
            
            return {
                'waveform': waveform_path,
                'spectrogram': spectrogram_path,
                'pitch': pitch_path,
                'volume': volume_path
            }
            
        except Exception as e:
            return {'error': f"生成可视化失败: {str(e)}"}
