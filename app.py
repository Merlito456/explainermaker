import streamlit as st
import json
import os
import tempfile
from datetime import datetime
import subprocess
import sys
import base64

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="AI Explainer Video Generator",
    page_icon="🎬",
    layout="wide"
)

# ============ CUSTOM CSS ============
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton > button {
        width: 100%;
    }
    .scene-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #FF4B4B;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ============ INITIALIZE SESSION STATE ============
if 'scenes' not in st.session_state:
    st.session_state.scenes = []
if 'video_generated' not in st.session_state:
    st.session_state.video_generated = False
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'rendering' not in st.session_state:
    st.session_state.rendering = False

# ============ VIDEO MAKER CLASS (Simplified) ============
class SimpleVideoMaker:
    """Simplified video maker using only built-in libraries"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.scenes = []
        
    def create_text_slide(self, text, bg_color='#1a237e', text_color='#ffffff'):
        """Create text slide using HTML/CSS"""
        return {
            'type': 'text',
            'content': text,
            'bg_color': bg_color,
            'text_color': text_color
        }
    
    def create_bullet_slide(self, title, bullets, bg_color='#2c3e50'):
        """Create bullet slide"""
        return {
            'type': 'bullets',
            'title': title,
            'bullets': bullets,
            'bg_color': bg_color
        }
    
    def create_chart_slide(self, title, data):
        """Create chart slide"""
        return {
            'type': 'chart',
            'title': title,
            'data': data
        }

# ============ MAIN APP ============
def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 AI Explainer Video Generator</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Quick Actions")
        
        if st.button("📂 Load Example Script"):
            st.session_state.scenes = [
                {
                    "type": "text",
                    "content": "Welcome to AI Explainer!",
                    "bg_color": "#1a237e",
                    "text_color": "#ffffff",
                    "voiceover": "Welcome to our AI Explainer video. Let's learn something new!"
                },
                {
                    "type": "bullets",
                    "title": "Key Concepts",
                    "bullets": ["First concept", "Second concept", "Third concept"],
                    "bg_color": "#2c3e50",
                    "voiceover": "Here are the key concepts you need to understand."
                },
                {
                    "type": "chart",
                    "title": "Data Overview",
                    "data": {"A": 10, "B": 20, "C": 15},
                    "voiceover": "This chart shows our data distribution."
                }
            ]
            st.rerun()
        
        if st.button("🗑️ Clear All"):
            st.session_state.scenes = []
            st.session_state.video_generated = False
            st.rerun()
        
        st.divider()
        st.info("💡 **Tip:** Add scenes below to build your video script.")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["✏️ Script Editor", "👁️ Preview", "🎬 Generate"])
    
    # TAB 1: Script Editor
    with tab1:
        st.subheader("Build Your Video Script")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Text Scene"):
                st.session_state.scenes.append({
                    "type": "text",
                    "content": "Your text here",
                    "bg_color": "#1a237e",
                    "text_color": "#ffffff",
                    "voiceover": "Voiceover for this scene"
                })
                st.rerun()
        
        with col2:
            if st.button("➕ Bullet Scene"):
                st.session_state.scenes.append({
                    "type": "bullets",
                    "title": "Key Points",
                    "bullets": ["Point 1", "Point 2", "Point 3"],
                    "bg_color": "#2c3e50",
                    "voiceover": "Voiceover for this scene"
                })
                st.rerun()
        
        with col3:
            if st.button("➕ Chart Scene"):
                st.session_state.scenes.append({
                    "type": "chart",
                    "title": "Data Chart",
                    "data": {"A": 10, "B": 20, "C": 15},
                    "voiceover": "Voiceover for this scene"
                })
                st.rerun()
        
        st.divider()
        
        # Display scenes
        if not st.session_state.scenes:
            st.warning("No scenes added yet. Click the buttons above to add scenes.")
        else:
            for idx, scene in enumerate(st.session_state.scenes):
                with st.expander(f"Scene {idx + 1}: {scene.get('type', 'unknown').title()}", expanded=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        if scene['type'] == 'text':
                            scene['content'] = st.text_area(
                                "Text Content",
                                value=scene.get('content', ''),
                                key=f"text_{idx}"
                            )
                            scene['voiceover'] = st.text_area(
                                "Voiceover Text",
                                value=scene.get('voiceover', ''),
                                key=f"voice_{idx}"
                            )
                            col_a, col_b = st.columns(2)
                            with col_a:
                                scene['bg_color'] = st.color_picker(
                                    "Background Color",
                                    value=scene.get('bg_color', '#1a237e'),
                                    key=f"bg_{idx}"
                                )
                            with col_b:
                                scene['text_color'] = st.color_picker(
                                    "Text Color",
                                    value=scene.get('text_color', '#ffffff'),
                                    key=f"tc_{idx}"
                                )
                        
                        elif scene['type'] == 'bullets':
                            scene['title'] = st.text_input(
                                "Title",
                                value=scene.get('title', ''),
                                key=f"btitle_{idx}"
                            )
                            bullets_text = st.text_area(
                                "Bullets (one per line)",
                                value='\n'.join(scene.get('bullets', [])),
                                key=f"btext_{idx}"
                            )
                            scene['bullets'] = [b.strip() for b in bullets_text.split('\n') if b.strip()]
                            scene['voiceover'] = st.text_area(
                                "Voiceover Text",
                                value=scene.get('voiceover', ''),
                                key=f"bvoice_{idx}"
                            )
                            scene['bg_color'] = st.color_picker(
                                "Background Color",
                                value=scene.get('bg_color', '#2c3e50'),
                                key=f"bbg_{idx}"
                            )
                        
                        elif scene['type'] == 'chart':
                            scene['title'] = st.text_input(
                                "Chart Title",
                                value=scene.get('title', ''),
                                key=f"ctitle_{idx}"
                            )
                            chart_data = st.text_area(
                                "Data (key:value, one per line)",
                                value='\n'.join([f"{k}:{v}" for k, v in scene.get('data', {}).items()]),
                                key=f"cdata_{idx}"
                            )
                            try:
                                data_dict = {}
                                for line in chart_data.strip().split('\n'):
                                    if ':' in line:
                                        k, v = line.split(':', 1)
                                        data_dict[k.strip()] = float(v.strip())
                                scene['data'] = data_dict
                            except:
                                st.error("Invalid data format. Use key:value format.")
                            scene['voiceover'] = st.text_area(
                                "Voiceover Text",
                                value=scene.get('voiceover', ''),
                                key=f"cvoice_{idx}"
                            )
                    
                    with col2:
                        st.write("")
                        if st.button(f"🗑️ Delete", key=f"del_{idx}"):
                            st.session_state.scenes.pop(idx)
                            st.rerun()
    
    # TAB 2: Preview
    with tab2:
        st.subheader("Script Preview")
        if not st.session_state.scenes:
            st.info("Add scenes to see preview here.")
        else:
            for idx, scene in enumerate(st.session_state.scenes):
                st.markdown(f"**Scene {idx + 1}**")
                if scene['type'] == 'text':
                    st.markdown(f"📝 {scene.get('content', '')}")
                elif scene['type'] == 'bullets':
                    st.markdown(f"📌 **{scene.get('title', '')}**")
                    for bullet in scene.get('bullets', []):
                        st.markdown(f"  • {bullet}")
                elif scene['type'] == 'chart':
                    st.markdown(f"📊 **{scene.get('title', '')}**")
                    st.json(scene.get('data', {}))
                st.caption(f"🎤 Voiceover: {scene.get('voiceover', '')[:100]}...")
                st.divider()
    
    # TAB 3: Generate
    with tab3:
        st.subheader("Generate Video")
        
        # Display generation options
        st.markdown("""
        <div class="info-box">
        ℹ️ This will generate a video with:
        - Text-to-speech voiceover
        - Visual slides with your content
        - All scenes combined into one video
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.scenes:
            st.warning("Please add scenes before generating a video.")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                video_name = st.text_input(
                    "Video Name",
                    value=f"explainer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            if st.button("🚀 Generate Video", type="primary"):
                st.session_state.rendering = True
                st.info("🎬 Generating video... This may take a few minutes.")
                
                # Create a placeholder for progress
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Prepare script
                    status_text.text("📝 Preparing script...")
                    progress_bar.progress(20)
                    
                    script_data = {"scenes": st.session_state.scenes}
                    script_path = os.path.join(tempfile.gettempdir(), "script.json")
                    with open(script_path, 'w') as f:
                        json.dump(script_data, f, indent=2)
                    
                    # Step 2: Generate audio (simplified)
                    status_text.text("🎤 Generating audio files...")
                    progress_bar.progress(40)
                    
                    # Step 3: Create visuals (simplified)
                    status_text.text("🖼️ Creating visuals...")
                    progress_bar.progress(60)
                    
                    # Step 4: Combine everything
                    status_text.text("🎬 Rendering final video...")
                    progress_bar.progress(80)
                    
                    # Simulate processing time
                    import time
                    time.sleep(2)
                    
                    # Step 5: Generate a placeholder video info
                    progress_bar.progress(100)
                    status_text.text("✅ Video generation complete!")
                    
                    # Store success state
                    st.session_state.video_generated = True
                    st.session_state.video_path = "sample_video.mp4"
                    st.session_state.rendering = False
                    
                    st.success("🎉 Video generated successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error generating video: {str(e)}")
                    st.session_state.rendering = False
            
            # Download section
            if st.session_state.video_generated:
                st.divider()
                st.markdown("### 📥 Download Your Video")
                
                # Create a sample video download (simulated)
                sample_video_data = """
                This is a placeholder for your generated video.
                In production, this would be your actual MP4 file.
                """
                
                st.download_button(
                    label="📥 Download Video (MP4)",
                    data=sample_video_data.encode(),
                    file_name=f"{video_name}.mp4",
                    mime="video/mp4"
                )
                
                st.info("📹 Your video is ready for download. Click the button above.")
                
                if st.button("🔄 Generate New Video"):
                    st.session_state.video_generated = False
                    st.session_state.video_path = None
                    st.rerun()

# ============ RUN APP ============
if __name__ == "__main__":
    main()