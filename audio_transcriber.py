import subprocess
import os
import tempfile
import logging
from transformers import pipeline
import torch

class AudioExtractorTranscriber:
    def __init__(self, model_name="openai/whisper-small", device=None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        if device is None:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
        
        self.device = device
        self.model_name = model_name
        
        self.logger.info(f"初始化Whisper模型 {model_name} 在设备 {device} 上")
        
        try:
            self.transcriber = pipeline(
                "automatic-speech-recognition", 
                model=model_name, 
                chunk_length_s=30,
                return_timestamps=True,
                device=device
            )
            self.logger.info("Whisper模型加载成功")
        except Exception as e:
            self.logger.error(f"Whisper模型加载失败: {str(e)}")
            raise
    
    def process(self, input_data):
        video_path = input_data['video_path']
        language = input_data.get('language', None)
        audio_format = input_data.get('audio_format', 'wav')
        
        if not os.path.exists(video_path):
            error_msg = f"视频文件不存在: {video_path}"
            self.logger.error(error_msg)
            return {'error': error_msg}
        
        try:
            temp_dir = tempfile.gettempdir()
            audio_filename = f"{os.path.splitext(os.path.basename(video_path))[0]}.{audio_format}"
            audio_path = os.path.join(temp_dir, audio_filename)
            
            command = f"ffmpeg -i \"{video_path}\" -q:a 0 -map a \"{audio_path}\" -y"
            self.logger.info(f"执行命令: {command}")
            
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                error_msg = f"音频提取失败: {stderr.decode()}"
                self.logger.error(error_msg)
                return {'error': error_msg}
            
            self.logger.info(f"音频提取成功: {audio_path}")
            
            transcribe_options = {"audio": audio_path}
            if language:
                transcribe_options["language"] = language
            
            self.logger.info("开始音频转录...")
            result = self.transcriber(**transcribe_options)
            self.logger.info("音频转录完成")
            
            text = result["text"]
            chunks = []
            
            if "chunks" in result:
                for chunk in result["chunks"]:
                    chunks.append({
                        "text": chunk["text"],
                        "start": chunk["timestamp"][0],
                        "end": chunk["timestamp"][1]
                    })
            
            self.logger.info(f"成功转录 {len(chunks)} 个文本片段")
            
            return {
                'audio_path': audio_path,
                'transcript': text,
                'chunks': chunks,
                'language': language or 'auto-detected'
            }
        
        except Exception as e:
            error_msg = f"音频转录过程中出错: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
    
    def transcribe_audio_file(self, audio_path, language=None):
        if not os.path.exists(audio_path):
            error_msg = f"音频文件不存在: {audio_path}"
            self.logger.error(error_msg)
            return {'error': error_msg}
        
        try:
            transcribe_options = {"audio": audio_path}
            if language:
                transcribe_options["language"] = language
            
            result = self.transcriber(**transcribe_options)
            
            text = result["text"]
            chunks = []
            
            if "chunks" in result:
                for chunk in result["chunks"]:
                    chunks.append({
                        "text": chunk["text"],
                        "start": chunk["timestamp"][0],
                        "end": chunk["timestamp"][1]
                    })
            
            return {
                'transcript': text,
                'chunks': chunks,
                'language': language or 'auto-detected'
            }
        
        except Exception as e:
            error_msg = f"音频转录过程中出错: {str(e)}"
            self.logger.error(error_msg)
            return {'error': error_msg}
