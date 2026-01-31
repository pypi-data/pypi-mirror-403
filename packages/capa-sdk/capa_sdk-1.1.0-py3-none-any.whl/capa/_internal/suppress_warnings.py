"""
Warning Suppression for CAPA - Clean Output Configuration

This module suppresses all unnecessary warnings to provide clean output.
Import this module BEFORE any other imports to ensure warnings are suppressed.

CAPA - Craniofacial Analysis & Prediction Architecture
"""

import os
import warnings
import logging
import sys

def configure_clean_environment():
    """Configure environment for clean A+ output without warnings"""
    
    # 1. Suppress TensorFlow logging BEFORE any TF imports
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Only errors
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Disable OneDNN optimizations messages
    os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'  # Suppress GPU warnings
    
    # 2. Suppress ABSL logging BEFORE imports
    os.environ['ABSL_LOG_LEVEL'] = 'ERROR'
    
    # 3. Suppress MediaPipe warnings BEFORE imports
    os.environ['GLOG_minloglevel'] = '3'  # Only fatal errors
    os.environ['GLOG_v'] = '0'  # Disable verbose logging
    os.environ['GLOG_stderrthreshold'] = '3'  # Only stderr for fatal
    
    # 4. Suppress Google Protobuf warnings - use python implementation for compatibility
    os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
    
    # 5. Configure Python warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    # 6. Configure root logger to reduce noise
    logging.getLogger().setLevel(logging.ERROR)
    
    # 7. Suppress specific MediaPipe/TensorFlow messages
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    logging.getLogger('mediapipe').setLevel(logging.ERROR)
    logging.getLogger('absl').setLevel(logging.ERROR)
    
    # 7.1. Suppress TensorFlow Lite and GPU messages
    logging.getLogger('tflite_runtime').setLevel(logging.ERROR)
    logging.getLogger('xnnpack').setLevel(logging.ERROR)
    
    # 8. Suppress specific warnings patterns
    warnings.filterwarnings("ignore", message=".*feedback manager.*")
    # CRITICAL FIX: Do not suppress NORM_RECT warnings - capture and propagate to client
    # warnings.filterwarnings("ignore", message=".*NORM_RECT.*")  
    warnings.filterwarnings("ignore", message=".*OpenGL.*")
    warnings.filterwarnings("ignore", message=".*GL version.*")
    warnings.filterwarnings("ignore", message=".*TensorFlow Lite.*")
    warnings.filterwarnings("ignore", message=".*XNNPACK.*")
    warnings.filterwarnings("ignore", message=".*inference_feedback_manager.*")
    warnings.filterwarnings("ignore", message=".*landmark_projection_calculator.*")
    warnings.filterwarnings("ignore", message=".*IMAGE_DIMENSIONS.*")
    warnings.filterwarnings("ignore", message=".*PROJECTION_MATRIX.*")
    warnings.filterwarnings("ignore", message=".*AMD Radeon.*")
    warnings.filterwarnings("ignore", message=".*ATI.*")
    
    # 9. CRITICAL: Set ABSL logging after import
    try:
        from absl import logging as absl_logging
        absl_logging.set_verbosity(absl_logging.ERROR)
        absl_logging.set_stderrthreshold(absl_logging.ERROR)
        absl_logging.use_absl_handler()
    except ImportError:
        pass
    
    return True

def suppress_opencv_warnings():
    """Suppress OpenCV specific warnings (call after cv2 import)"""
    try:
        import cv2
        # Try different methods to suppress OpenCV logs (API varies by version)
        if hasattr(cv2, 'setLogLevel'):
            cv2.setLogLevel(0)  # Suppress all OpenCV logs
        elif hasattr(cv2, 'utils') and hasattr(cv2.utils, 'logging'):
            cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        return True
    except (ImportError, AttributeError):
        return False

def suppress_mediapipe_warnings():
    """Suppress MediaPipe specific warnings during initialization"""
    try:
        # Redirect stderr temporarily during MediaPipe initialization
        class NullDevice:
            def write(self, s): pass
            def flush(self): pass
        
        original_stderr = sys.stderr
        sys.stderr = NullDevice()
        
        # Import and configure MediaPipe
        import mediapipe as mp
        
        # Restore stderr
        sys.stderr = original_stderr
        
        return True
    except ImportError:
        if 'sys' in locals():
            sys.stderr = original_stderr
        return False

# Auto-configure on import
configure_clean_environment()