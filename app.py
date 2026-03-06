# app.py
import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av
import time
import random
from PIL import Image, ImageDraw, ImageFont
import os

# Page configuration
st.set_page_config(
    page_title="FaceCard Scanner",
    page_icon="💳",
    layout="centered"
)

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'scan_result' not in st.session_state:
    st.session_state.scan_result = None
if 'scan_complete' not in st.session_state:
    st.session_state.scan_complete = False

# Custom CSS for styling
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .main-title {
        text-align: center;
        color: white;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .subtitle {
        text-align: center;
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .slay-text {
        color: #00ff88;
        font-size: 5rem;
        font-weight: bold;
        text-align: center;
        text-shadow: 0 0 20px #00ff88;
        animation: pulse 1.5s infinite;
    }
    .chopped-text {
        color: #ff4444;
        font-size: 5rem;
        font-weight: bold;
        text-align: center;
        text-shadow: 0 0 20px #ff4444;
        animation: shake 0.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-10px); }
        75% { transform: translateX(10px); }
    }
    .credit-card-frame {
        position: relative;
        border: 3px solid gold;
        border-radius: 20px;
        padding: 10px;
        background: linear-gradient(145deg, #ffffff22, #ffffff11);
        backdrop-filter: blur(5px);
        box-shadow: 0 0 30px rgba(255,215,0,0.3);
    }
    .scan-line {
        position: absolute;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, transparent, gold, transparent);
        animation: scan 2s linear infinite;
    }
    @keyframes scan {
        0% { top: 0%; }
        50% { top: 100%; }
        100% { top: 0%; }
    }
    .stats-box {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
    }
    </style>
""", unsafe_allow_html=True)

# FIXED: Initialize MediaPipe Face Detection properly
@st.cache_resource
def init_face_detection():
    """Initialize MediaPipe Face Detection model"""
    return mp.solutions.face_detection.FaceDetection(
        model_selection=0,
        min_detection_confidence=0.5
    )

class FaceCardTransformer(VideoTransformerBase):
    def __init__(self):
        # FIXED: Initialize face detection directly
        self.face_detection = init_face_detection()
        self.last_classification = None
        self.classification_time = time.time()
        
    def classify_face(self, face_roi):
        """Simple classification logic for 'Slay' or 'Chopped'"""
        if face_roi.size == 0:
            return "Chopped"
        
        # Convert to grayscale
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        # Calculate metrics
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Use Laplacian for sharpness (higher = sharper/more detailed)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Simple scoring system (for fun!)
        score = 0
        
        # Brightness score (ideal around 128)
        if 100 < brightness < 180:
            score += 2
        elif 70 < brightness < 200:
            score += 1
            
        # Contrast score (higher contrast often looks better)
        if contrast > 50:
            score += 2
        elif contrast > 30:
            score += 1
            
        # Sharpness score (sharper image = better)
        if laplacian > 100:
            score += 2
        elif laplacian > 50:
            score += 1
            
        # Add some randomness for fun (20% random factor)
        if random.random() < 0.2:
            score += 2 if random.random() > 0.5 else -2
            
        return "Slay" if score >= 3 else "Chopped"
    
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Resize for faster processing
        height, width = img.shape[:2]
        if width > 640:
            scale = 640 / width
            new_width = 640
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
        
        # Convert to RGB for MediaPipe
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        results = self.face_detection.process(rgb_img)
        
        # Draw credit card overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (20, 20), (img.shape[1]-20, img.shape[0]-20), 
                     (255, 215, 0), 3)  # Gold border
        
        # Add credit card details
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(overlay, "FaceCard", (40, 70), font, 1, (255, 215, 0), 2)
        cv2.putText(overlay, "**** **** **** " + str(random.randint(1000, 9999)), 
                   (40, 120), font, 0.7, (255, 255, 255), 2)
        
        # Add scan line animation
        scan_pos = int((time.time() * 100) % img.shape[0])
        cv2.line(overlay, (20, scan_pos), (img.shape[1]-20, scan_pos), 
                (255, 215, 0), 2)
        
        # FIXED: Check if results and detections exist
        if results and results.detections:
            for detection in results.detections:
                bboxC = detection.location_data.relative_bounding_box
                ih, iw, _ = img.shape
                x = int(bboxC.xmin * iw)
                y = int(bboxC.ymin * ih)
                w = int(bboxC.width * iw)
                h = int(bboxC.height * ih)
                
                # FIXED: Ensure coordinates are valid
                if x >= 0 and y >= 0 and w > 0 and h > 0 and y+h <= ih and x+w <= iw:
                    # Extract face ROI
                    face_roi = img[y:y+h, x:x+w]
                    
                    # Classify face
                    if time.time() - self.classification_time > 2:  # Update every 2 seconds
                        self.last_classification = self.classify_face(face_roi)
                        self.classification_time = time.time()
                        st.session_state.scan_result = self.last_classification
                    
                    # Draw detection box
                    cv2.rectangle(overlay, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Add classification label
                    if self.last_classification:
                        color = (0, 255, 0) if self.last_classification == "Slay" else (0, 0, 255)
                        cv2.putText(overlay, self.last_classification, (x, y-10), 
                                   font, 0.7, color, 2)
        
        # Blend overlay with original
        alpha = 0.3
        img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Page navigation functions
def go_to_scan():
    st.session_state.page = 'scan'
    st.session_state.scan_complete = False
    st.session_state.scan_result = None

def go_to_result():
    st.session_state.page = 'result'
    st.session_state.scan_complete = True

def go_to_home():
    st.session_state.page = 'home'
    st.session_state.scan_complete = False
    st.session_state.scan_result = None

# Home Page
if st.session_state.page == 'home':
    st.markdown('<h1 class="main-title">💳 FaceCard Scanner</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Scan your FaceCard to see if you SLAY or get CHOPPED!</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("https://img.icons8.com/fluency/96/credit-card.png", use_column_width=True)
        
        if st.button("💳 SCAN FACECARD", use_container_width=True):
            go_to_scan()
            st.rerun()
    
    # Fun stats
    st.markdown('<div class="stats-box">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Today's Slays", random.randint(42, 99))
    with col2:
        st.metric("Today's Chopped", random.randint(13, 37))
    with col3:
        st.metric("Active Scanners", "🔥 1337")
    st.markdown('</div>', unsafe_allow_html=True)

# Scan Page
elif st.session_state.page == 'scan':
    st.markdown('<h1 class="main-title">📸 Scanning Your FaceCard</h1>', unsafe_allow_html=True)
    
    # Credit card frame overlay in description
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <div class="credit-card-frame" style="display: inline-block; padding: 10px 30px;">
            <span style="color: gold; font-size: 1.2rem;">💳 POSITION YOUR FACE IN THE FRAME 💳</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize webcam
    ctx = webrtc_streamer(
        key="facecard-scanner",
        video_transformer_factory=FaceCardTransformer,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"video": {"width": {"ideal": 640}, "height": {"ideal": 480}}, "audio": False},
        async_processing=True,
    )
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("✅ DONE SCANNING", use_container_width=True):
            if st.session_state.scan_result:
                go_to_result()
                st.rerun()
            else:
                st.warning("No face detected yet! Please position your face in the frame.")
        
        if st.button("🔙 BACK TO HOME", use_container_width=True):
            go_to_home()
            st.rerun()

# Result Page
elif st.session_state.page == 'result':
    result = st.session_state.scan_result if st.session_state.scan_result else random.choice(["Slay", "Chopped"])
    
    if result == "Slay":
        st.markdown(f'<h1 class="slay-text">✨ SLAY ✨</h1>', unsafe_allow_html=True)
        st.balloons()
        st.markdown("""
        <div style="text-align: center; color: white; font-size: 1.5rem; margin: 20px;">
            Your FaceCard is approved! You're absolutely crushing it! 💅
        </div>
        """, unsafe_allow_html=True)
        st.image("https://media.giphy.com/media/3o7abKh7NwRtAg3Hba/giphy.gif", use_column_width=True)
    else:
        st.markdown(f'<h1 class="chopped-text">🔪 CHOPPED 🔪</h1>', unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; color: white; font-size: 1.5rem; margin: 20px;">
            Oof! Your FaceCard got declined. Maybe try again? 😅
        </div>
        """, unsafe_allow_html=True)
        st.image("https://media.giphy.com/media/3o7TKUM3IgJBX2as9O/giphy.gif", use_column_width=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🔄 SCAN AGAIN", use_container_width=True):
            go_to_scan()
            st.rerun()
        
        if st.button("🏠 HOME", use_container_width=True):
            go_to_home()
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: rgba(255,255,255,0.5);'>Made with 💅 for the slayest faces</p>",
    unsafe_allow_html=True
)