import mediapipe as mp
import numpy as np
import cv2
import logging
from typing import List, Dict, Tuple, Any, Optional

class VisualAnalyzer:
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]
        self.RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
        self.LEFT_IRIS_INDICES = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS_INDICES = [473, 474, 475, 476, 477]
        self.LIPS_INDICES = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
        self.LEFT_EYEBROW_INDICES = [276, 283, 282, 295, 285]
        self.RIGHT_EYEBROW_INDICES = [46, 53, 52, 65, 55]
    
    def process(self, input_data):
        frames = input_data['frames']
        self.logger.info(f"开始处理 {len(frames)} 帧进行视觉分析")
        
        eye_contact_scores = []
        posture_scores = []
        expression_scores = []
        frame_results = []
        
        for i, frame in enumerate(frames):
            if i % 10 == 0:
                self.logger.info(f"处理第 {i}/{len(frames)} 帧")
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            face_results = self.face_mesh.process(frame_rgb)
            pose_results = self.pose.process(frame_rgb)
            
            eye_score = 0.0
            expression_score = 0.0
            posture_score = 0.0
            
            if face_results.multi_face_landmarks:
                face_landmarks = face_results.multi_face_landmarks[0]
                
                left_eye_score = self._calculate_eye_contact(face_landmarks, 'left')
                right_eye_score = self._calculate_eye_contact(face_landmarks, 'right')
                eye_score = (left_eye_score + right_eye_score) / 2
                eye_contact_scores.append(eye_score)
                
                expression_score = self._calculate_expression(face_landmarks)
                expression_scores.append(expression_score)
            
            if pose_results.pose_landmarks:
                posture_score = self._calculate_posture(pose_results.pose_landmarks)
                posture_scores.append(posture_score)
            
            frame_result = {
                'eye_contact': eye_score,
                'expression': expression_score,
                'posture': posture_score,
                'has_face': bool(face_results.multi_face_landmarks),
                'has_pose': bool(pose_results.pose_landmarks)
            }
            frame_results.append(frame_result)
        
        result = {
            'eye_contact': sum(eye_contact_scores) / len(eye_contact_scores) if eye_contact_scores else 0.0,
            'expression_variation': np.std(expression_scores) if expression_scores else 0.0,
            'posture': sum(posture_scores) / len(posture_scores) if posture_scores else 0.0,
            'face_detection_rate': len(eye_contact_scores) / len(frames) if frames else 0.0,
            'frame_results': frame_results
        }
        
        result.update(self._generate_analysis_summary(result))
        
        self.logger.info("视觉分析完成")
        return result
    
    def _calculate_eye_contact(self, landmarks, eye='left'):
        eye_indices = self.LEFT_EYE_INDICES if eye == 'left' else self.RIGHT_EYE_INDICES
        iris_indices = self.LEFT_IRIS_INDICES if eye == 'left' else self.RIGHT_IRIS_INDICES
        
        eye_landmarks = np.array([(landmarks.landmark[idx].x, landmarks.landmark[idx].y) for idx in eye_indices])
        eye_center = np.mean(eye_landmarks, axis=0)
        
        iris_landmarks = np.array([(landmarks.landmark[idx].x, landmarks.landmark[idx].y) for idx in iris_indices if idx < len(landmarks.landmark)])
        
        if len(iris_landmarks) == 0:
            return 0.5
            
        iris_center = np.mean(iris_landmarks, axis=0)
        
        distance = np.linalg.norm(iris_center - eye_center)
        
        eye_size = np.linalg.norm(np.max(eye_landmarks, axis=0) - np.min(eye_landmarks, axis=0))
        
        normalized_distance = 1.0 - min(distance / (eye_size * 0.5), 1.0)
        
        return normalized_distance
    
    def _calculate_expression(self, landmarks):
        upper_lip = np.array((landmarks.landmark[13].x, landmarks.landmark[13].y))
        lower_lip = np.array((landmarks.landmark[14].x, landmarks.landmark[14].y))
        mouth_distance = np.linalg.norm(upper_lip - lower_lip)
        
        left_eyebrow = np.mean([(landmarks.landmark[idx].x, landmarks.landmark[idx].y) 
                               for idx in self.LEFT_EYEBROW_INDICES], axis=0)
        right_eyebrow = np.mean([(landmarks.landmark[idx].x, landmarks.landmark[idx].y) 
                                for idx in self.RIGHT_EYEBROW_INDICES], axis=0)
        
        left_eye = np.mean([(landmarks.landmark[idx].x, landmarks.landmark[idx].y) 
                          for idx in self.LEFT_EYE_INDICES], axis=0)
        right_eye = np.mean([(landmarks.landmark[idx].x, landmarks.landmark[idx].y) 
                           for idx in self.RIGHT_EYE_INDICES], axis=0)
        
        left_distance = np.linalg.norm(left_eyebrow - left_eye)
        right_distance = np.linalg.norm(right_eyebrow - right_eye)
        eyebrow_distance = (left_distance + right_distance) / 2
        
        expression_score = 0.7 * mouth_distance + 0.3 * eyebrow_distance
        
        normalized_score = min(max(expression_score * 5.0, 0.0), 1.0)
        
        return normalized_score
    
    def _calculate_posture(self, pose_landmarks):
        landmarks = pose_landmarks.landmark
        
        left_shoulder = np.array((landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER].x,
                                 landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER].y))
        right_shoulder = np.array((landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER].x,
                                  landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER].y))
        
        shoulder_levelness = 1.0 - min(abs(left_shoulder[1] - right_shoulder[1]) * 10, 1.0)
        
        nose = np.array((landmarks[mp.solutions.pose.PoseLandmark.NOSE].x,
                        landmarks[mp.solutions.pose.PoseLandmark.NOSE].y))
        mid_shoulder = (left_shoulder + right_shoulder) / 2
        
        vertical_alignment = 1.0 - min(abs(nose[0] - mid_shoulder[0]) * 5, 1.0)
        
        posture_score = (shoulder_levelness * 0.5) + (vertical_alignment * 0.5)
        
        return posture_score
    
    def _generate_analysis_summary(self, metrics):
        eye_contact = metrics['eye_contact']
        expression = metrics['expression_variation']
        posture = metrics['posture']
        detection_rate = metrics['face_detection_rate']
        
        eye_rating = min(5, int(eye_contact * 5) + 1)
        expr_rating = min(5, int(expression * 10) + 1)
        posture_rating = min(5, int(posture * 5) + 1)
        
        overall_score = (eye_contact * 0.4) + (expression * 0.3) + (posture * 0.3)
        overall_rating = min(5, max(1, int(overall_score * 5) + 1))
        
        explanations = []
        
        if eye_contact < 0.3:
            explanations.append("候选人很少与相机保持目光接触，这可能表现出缺乏自信或专注度。")
        elif eye_contact < 0.7:
            explanations.append("候选人与相机保持了适度的目光接触。")
        else:
            explanations.append("候选人与相机保持了出色的目光接触，表现出良好的专注度和自信。")
            
        if expression < 0.1:
            explanations.append("面部表情变化很少，显得缺乏情感参与。")
        elif expression < 0.3:
            explanations.append("面部表情有一定变化，展示了适度的情感参与。")
        else:
            explanations.append("面部表情丰富多变，很好地展示了情感参与度和交流能力。")
            
        if posture < 0.4:
            explanations.append("姿势较为随意，可能需要改善。")
        elif posture < 0.7:
            explanations.append("姿势适当，展现了一定的专业性。")
        else:
            explanations.append("姿势专业，展现了良好的自信和专业性。")
            
        if detection_rate < 0.5:
            explanations.append("注意：面部检测率较低，分析结果可能不够准确。")
        
        return {
            'eye_contact_rating': eye_rating,
            'expression_rating': expr_rating,
            'posture_rating': posture_rating,
            'overall_rating': overall_rating,
            'overall_score': overall_score,
            'analysis_explanation': ' '.join(explanations)
        }
    
    def visualize_analysis(self, frame, face_landmarks=None, pose_landmarks=None):
        annotated_frame = frame.copy()
        
        if face_landmarks:
            mp_drawing = mp.solutions.drawing_utils
            drawing_spec = mp.solutions.drawing_utils.DrawingSpec(thickness=1, circle_radius=1, color=(0, 255, 0))
            mp_drawing.draw_landmarks(
                image=annotated_frame,
                landmark_list=face_landmarks,
                connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=drawing_spec,
                connection_drawing_spec=drawing_spec
            )
            
            for idx in self.LEFT_EYE_INDICES + self.RIGHT_EYE_INDICES:
                landmark = face_landmarks.landmark[idx]
                pos = (int(landmark.x * frame.shape[1]), int(landmark.y * frame.shape[0]))
                cv2.circle(annotated_frame, pos, 2, (0, 0, 255), -1)
        
        if pose_landmarks:
            mp_drawing.draw_landmarks(
                annotated_frame,
                pose_landmarks,
                mp.solutions.pose.POSE_CONNECTIONS,
                mp.solutions.drawing_utils.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                mp.solutions.drawing_utils.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
            )
        
        return annotated_frame
