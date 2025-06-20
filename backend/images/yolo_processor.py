import cv2
import numpy as np
from ultralytics import YOLO
from django.conf import settings
import os
import logging
import time

logger = logging.getLogger(__name__)

class YOLOProcessor:
    def __init__(self, use_26_keypoints=True):
        """Initialize YOLO model with backward compatibility"""
        self.use_26_keypoints = use_26_keypoints
        
        if use_26_keypoints:
            # Use your 26-keypoint model
            model_path = getattr(settings, 'YOLO_MODEL_PATH', None)
            if not model_path or not os.path.exists(model_path):
                # Fallback to default location
                model_path = os.path.join(settings.BASE_DIR, 'models', 'yolo', 'best26.pt')
            
            if not os.path.exists(model_path):
                logger.warning(f"26-keypoint model not found at {model_path}, falling back to 17-keypoint")
                self.use_26_keypoints = False
                model_path = 'yolov8n-pose.pt'
            else:
                logger.info(f"Using 26-keypoint model: {model_path}")
        else:
            model_path = getattr(settings, 'YOLO_MODEL_PATH', 'yolov8n-pose.pt')
        
        self.model = YOLO(model_path)
        self.model_path = model_path
        
        # 26-keypoint labels for infant pose
        self.keypoint_labels_26 = [
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", 
            "left_wrist", "right_wrist", "left_hip", "right_hip", 
            "left_knee", "right_knee", "left_ankle", "right_ankle", 
            "head", "neck", "mid_back", "lower_back", "upper_back", 
            "left_palm_end", "right_palm_end", "left_foot_end", "right_foot_end"
        ]
        
        # Legacy 17-keypoint labels for backward compatibility
        self.keypoint_labels_17 = [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ]
        
        # Use appropriate labels based on model
        self.keypoint_labels = self.keypoint_labels_26 if self.use_26_keypoints else self.keypoint_labels_17
        
        # Keypoint connections for 26-keypoint system
        self.connections_26 = [
            (0, 1), (0, 2), (1, 3), (2, 4), (5, 7), (7, 9), 
            (6, 8), (8, 10), (11, 13), (13, 15), (12, 14), (14, 16), 
            (17, 18), (18, 21), (19, 21), (19, 20), (20, 11), (20, 12), 
            (15, 24), (16, 25), (9, 22), (10, 23)
        ]
        
        # Legacy connections for 17-keypoint system
        self.connections_17 = [
            (0, 1), (0, 2), (1, 3), (2, 4), (5, 6), (5, 7), (6, 8), 
            (7, 9), (8, 10), (11, 12), (11, 13), (12, 14), (13, 15), (14, 16)
        ]
        
        self.connections = self.connections_26 if self.use_26_keypoints else self.connections_17
        
        logger.info(f"Initialized YOLO processor: {len(self.keypoint_labels)} keypoints, model: {os.path.basename(model_path)}")
    
    def process_image(self, image_path):
        """Process image and extract keypoints with enhanced detection"""
        try:
            # Get full path
            full_path = os.path.join(settings.MEDIA_ROOT, image_path) if not os.path.isabs(image_path) else image_path
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Image not found: {full_path}")
            
            # Load image for preprocessing
            image = cv2.imread(full_path)
            if image is None:
                raise ValueError(f"Could not load image from {full_path}")
            
            original_shape = image.shape
            
            # Run YOLO inference
            results = self.model(full_path)
            
            annotations = []
            
            for result in results:
                # Process keypoints if available
                if hasattr(result, 'keypoints') and result.keypoints is not None:
                    keypoints = result.keypoints.data
                    
                    for person_idx, person_keypoints in enumerate(keypoints):
                        # Extract raw keypoints
                        raw_keypoints = []
                        confidences = []
                        
                        for kp_idx, (x, y, conf) in enumerate(person_keypoints):
                            if kp_idx < len(self.keypoint_labels):
                                raw_keypoints.append([float(x), float(y)])
                                confidences.append(float(conf))
                        
                        # Apply corrections for 26-keypoint system
                        if self.use_26_keypoints and len(raw_keypoints) >= 17:
                            corrected_keypoints = self.correct_keypoints_26(raw_keypoints, original_shape)
                        else:
                            corrected_keypoints = raw_keypoints
                        
                        # Create keypoint annotations
                        for kp_idx, (corrected_point, confidence) in enumerate(zip(corrected_keypoints, confidences)):
                            if kp_idx < len(self.keypoint_labels) and confidence > getattr(settings, 'YOLO_CONFIDENCE_THRESHOLD', 0.3):
                                annotations.append({
                                    'type': 'keypoint',
                                    'label': self.keypoint_labels[kp_idx],
                                    'keypoint_index': kp_idx,
                                    'x': corrected_point[0],
                                    'y': corrected_point[1],
                                    'confidence': confidence,
                                    'person_id': person_idx,
                                    'metadata': {
                                        'detection_method': f'yolo_{"26kp" if self.use_26_keypoints else "17kp"}',
                                        'model_version': os.path.basename(self.model_path),
                                        'connections': self.get_keypoint_connections(kp_idx),
                                        'original_coords': [float(x), float(y)] if kp_idx < len(raw_keypoints) else None
                                    }
                                })
                
                # Process bounding boxes
                if hasattr(result, 'boxes') and result.boxes is not None:
                    boxes = result.boxes.data
                    
                    for box_idx, box in enumerate(boxes):
                        x1, y1, x2, y2, conf, cls = box
                        
                        annotations.append({
                            'type': 'bounding_box',
                            'label': f'infant_{box_idx}' if self.use_26_keypoints else f'person_{box_idx}',
                            'x': float(x1),
                            'y': float(y1),
                            'width': float(x2 - x1),
                            'height': float(y2 - y1),
                            'confidence': float(conf),
                            'class_id': int(cls),
                            'metadata': {
                                'box_coordinates': [float(x1), float(y1), float(x2), float(y2)],
                                'detection_method': f'yolo_{"infant" if self.use_26_keypoints else "person"}_detection'
                            }
                        })
            
            logger.info(f"Processed {os.path.basename(full_path)}: found {len(annotations)} annotations ({len([a for a in annotations if a['type'] == 'keypoint'])} keypoints)")
            return annotations
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            raise
    
    def correct_keypoints_26(self, keypoints, image_shape):
        """Apply anatomical corrections for 26-keypoint system"""
        if not keypoints or len(keypoints) < 17:
            logger.warning("Insufficient keypoints for 26-point correction")
            return keypoints
        
        corrected = keypoints.copy()
        
        try:
            # Extend to 26 keypoints if we have fewer
            while len(corrected) < 26:
                corrected.append([0.0, 0.0])  # Add placeholder keypoints
            
            # Apply corrections based on your implementation
            if len(corrected) >= 22:
                # Calculate neck point (index 18) - midpoint of shoulders
                if len(corrected) > 5 and len(corrected) > 6:
                    corrected[18] = [
                        (corrected[5][0] + corrected[6][0]) / 2,
                        (corrected[5][1] + corrected[6][1]) / 2
                    ]
                
                # Calculate upper back (index 21) - estimate from shoulders and neck
                if len(corrected) > 18:
                    corrected[21] = [
                        corrected[18][0],
                        corrected[18][1] + 20  # Slightly below neck
                    ]
                
                # Calculate mid back (index 19) - midpoint between upper back and lower back
                corrected[20] = corrected[19] if len(corrected) > 19 else [corrected[21][0], corrected[21][1] + 40]  # Lower back
                corrected[19] = [
                    (corrected[20][0] + corrected[21][0]) / 2,
                    (corrected[20][1] + corrected[21][1]) / 2
                ]
                
                # Palm ends - extend from wrists
                if len(corrected) > 9:  # left wrist
                    corrected[22] = [corrected[9][0], corrected[9][1] + 15]  # left palm end
                if len(corrected) > 10:  # right wrist
                    corrected[23] = [corrected[10][0], corrected[10][1] + 15]  # right palm end
                
                # Foot ends - extend from ankles
                if len(corrected) > 15:  # left ankle
                    corrected[24] = [corrected[15][0] + 15, corrected[15][1] + 10]  # left foot end
                if len(corrected) > 16:  # right ankle
                    corrected[25] = [corrected[16][0] + 15, corrected[16][1] + 10]  # right foot end
                
                # Head point (index 17) - above nose
                if len(corrected) > 0:  # nose
                    corrected[17] = [corrected[0][0], corrected[0][1] - 30]  # head above nose
            
            # Adjust keypoints to stay within image bounds
            return self.adjust_keypoints_to_bounds(corrected, image_shape)
            
        except Exception as e:
            logger.error(f"Error in keypoint correction: {str(e)}")
            return keypoints
    
    def adjust_keypoints_to_bounds(self, keypoints, image_shape, margin=5):
        """Adjust keypoints to stay within image bounds"""
        height, width = image_shape[:2]
        adjusted = []
        
        for point in keypoints:
            if len(point) >= 2:
                x = max(margin, min(point[0], width - margin))
                y = max(margin, min(point[1], height - margin))
                adjusted.append([x, y])
            else:
                adjusted.append(point)
        
        return adjusted
    
    def get_keypoint_connections(self, keypoint_index):
        """Get connections for a specific keypoint"""
        connections = []
        for i, j in self.connections:
            if i == keypoint_index or j == keypoint_index:
                connections.append((i, j))
        return connections