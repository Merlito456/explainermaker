import streamlit as st
import os
import tempfile
from datetime import datetime
import requests
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import re
from io import BytesIO
import random
import base64
import subprocess
import sys
import time

# Check and install required packages
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    from gtts import gTTS
except ImportError:
    install_package("gtts")
    from gtts import gTTS

try:
    import cv2
except ImportError:
    install_package("opencv-python-headless")
    import cv2

# Try to use ffmpeg-python if available
try:
    import ffmpeg
except ImportError:
    install_package("ffmpeg-python")
    import ffmpeg

st.set_page_config(
    page_title="AI Explainer Video Generator",
    page_icon="🎬",
    layout="wide"
)

CSS_STYLES = (
    "<style>"
    ".main-header {"
    "    font-size: 2.5rem;"
    "    color: #FF4B4B;"
    "    text-align: center;"
    "    margin-bottom: 1rem;"
    "}"
    ".stButton > button {"
    "    width: 100%;"
    "}"
    ".info-box {"
    "    background-color: #e3f2fd;"
    "    padding: 1rem;"
    "    border-radius: 0.5rem;"
    "    margin: 1rem 0;"
    "    border-left: 4px solid #2196F3;"
    "}"
    ".success-box {"
    "    background-color: #d4edda;"
    "    padding: 1rem;"
    "    border-radius: 0.5rem;"
    "    margin: 1rem 0;"
    "    border-left: 4px solid #28a745;"
    "}"
    "</style>"
)

INFO_HTML = (
    '<div class="info-box">'
    '🎬 <b>Generate a complete MP4 video with voiceover!</b><br>'
    'Our AI will automatically:'
    '• Parse your script into scenes'
    '• Generate images for each scene'
    '• Create voiceovers using TTS'
    '• Combine everything into a professional MP4 video'
    '</div>'
)

SUCCESS_HTML = (
    '<div class="success-box">'
    '<h3>✅ Your Video is Ready!</h3>'
    '</div>'
)

st.markdown(CSS_STYLES, unsafe_allow_html=True)

if 'scenes' not in st.session_state:
    st.session_state.scenes = []
if 'video_generated' not in st.session_state:
    st.session_state.video_generated = False
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'script_input' not in st.session_state:
    st.session_state.script_input = ""

class FreeImageGenerator:
    def __init__(self):
        self.topic_keywords = {
            'technology': ['technology', 'computer', 'digital', 'coding', 'ai'],
            'business': ['business', 'office', 'meeting', 'team', 'corporate'],
            'education': ['education', 'school', 'learning', 'book', 'study'],
            'health': ['health', 'medical', 'doctor', 'hospital', 'wellness'],
            'nature': ['nature', 'green', 'forest', 'ocean', 'mountain'],
            'science': ['science', 'laboratory', 'research', 'experiment'],
            'finance': ['finance', 'money', 'banking', 'investment'],
            'creative': ['creative', 'design', 'art', 'innovation']
        }
        
    def get_random_image(self, keyword="nature", width=1920, height=1080):
        try:
            url = "https://picsum.photos/seed/" + str(random.randint(1, 1000)) + "/" + str(width) + "/" + str(height)
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                return img
        except:
            pass
        
        try:
            url = "https://source.unsplash.com/featured/" + str(width) + "x" + str(height) + "/?" + keyword
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                return img
        except:
            pass
        
        return self.create_gradient_image(width, height)
    
    def create_gradient_image(self, width, height):
        img = Image.new('RGB', (width, height))
        for x in range(width):
            for y in range(height):
                r = int(30 + (x / width) * 100)
                g = int(40 + (y / height) * 100)
                b = int(200 - (x / width) * 80)
                img.putpixel((x, y), (r, g, b))
        return img
    
    def get_relevant_keyword(self, text):
        text_lower = text.lower()
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return keyword
        return "nature"

class ScriptParser:
    def __init__(self):
        self.scenes = []
        
    def parse_script(self, script_text):
        lines = script_text.strip().split('\n')
        scenes = []
        current_scene = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('#'):
                scenes.append({
                    'type': 'text',
                    'content': line.lstrip('#').strip(),
                    'voiceover': line.lstrip('#').strip()
                })
            elif line.startswith('-'):
                if current_scene and current_scene['type'] == 'bullets':
                    current_scene['bullets'].append(line.lstrip('- ').strip())
                    current_scene['voiceover'] += ". " + line.lstrip('- ').strip()
                else:
                    if current_scene:
                        scenes.append(current_scene)
                    current_scene = {
                        'type': 'bullets',
                        'title': 'Key Points',
                        'bullets': [line.lstrip('- ').strip()],
                        'voiceover': line.lstrip('- ').strip()
                    }
            elif ':' in line and any(word in line.lower() for word in ['chart', 'data', 'graph']):
                parts = line.split(':')
                if len(parts) == 2:
                    title = parts[0].strip()
                    data_str = parts[1].strip()
                    try:
                        data_items = data_str.split(',')
                        data = {}
                        for item in data_items:
                            if '=' in item:
                                k, v = item.split('=')
                                data[k.strip()] = float(v.strip())
                        scenes.append({
                            'type': 'chart',
                            'title': title,
                            'data': data,
                            'voiceover': "Chart showing " + title + " with data: " + data_str
                        })
                        current_scene = None
                    except:
                        pass
            else:
                if current_scene and current_scene['type'] != 'text':
                    scenes.append(current_scene)
                    current_scene = None
                
                scenes.append({
                    'type': 'text',
                    'content': line,
                    'voiceover': line
                })
        
        if current_scene:
            scenes.append(current_scene)
        
        return scenes
    
    def auto_generate_scenes(self, script_text, num_scenes=5):
        scenes = self.parse_script(script_text)
        
        if not scenes:
            sentences = re.split(r'[.!?]+', script_text)
            sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
            
            for i, sentence in enumerate(sentences[:num_scenes]):
                if i % 3 == 0:
                    scenes.append({
                        'type': 'text',
                        'content': sentence,
                        'voiceover': sentence
                    })
                elif i % 3 == 1:
                    words = sentence.split()
                    bullets = [' '.join(words[i:i+3]) for i in range(0, len(words), 3)]
                    bullets = [b for b in bullets if len(b) > 5][:5]
                    scenes.append({
                        'type': 'bullets',
                        'title': "Key Point " + str(i+1),
                        'bullets': bullets,
                        'voiceover': sentence
                    })
                else:
                    numbers = re.findall(r'\d+', sentence)
                    if numbers:
                        data = {}
                        for i, n in enumerate(numbers[:6]):
                            data["Item" + str(i+1)] = int(n)
                        scenes.append({
                            'type': 'chart',
                            'title': "Data Visualization",
                            'data': data,
                            'voiceover': sentence
                        })
                    else:
                        scenes.append({
                            'type': 'text',
                            'content': sentence,
                            'voiceover': sentence
                        })
        
        return scenes

class VideoCreator:
    def __init__(self, resolution=(1280, 720), fps=24):
        self.resolution = resolution
        self.fps = fps
        self.image_gen = FreeImageGenerator()
        self.temp_dir = tempfile.mkdtemp()
        
    def create_text_slide(self, text, bg_color='#1a237e', text_color='#ffffff', width=1280, height=720):
        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        img = Image.new('RGB', (width, height), color=bg_rgb)
        draw = ImageDraw.Draw(img)
        
        try:
            font_size = 60 if width > 1000 else 40
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] > width - 100:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        line_height = font_size + 20
        y_offset = (height - len(lines) * line_height) // 2
        text_rgb = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (width - bbox[2]) // 2
            draw.text((x+2, y_offset+2), line, fill='black', font=font)
            draw.text((x, y_offset), line, fill=text_rgb, font=font)
            y_offset += line_height
        
        return img
    
    def create_bullet_slide(self, title, bullets, width=1280, height=720):
        img = self.image_gen.get_random_image("business", width, height)
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for x in range(width):
            for y in range(height):
                overlay.putpixel((x, y), (0, 0, 0, 180))
        
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        try:
            title_size = 70 if width > 1000 else 50
            bullet_size = 45 if width > 1000 else 30
            title_font = ImageFont.truetype("arial.ttf", title_size)
            bullet_font = ImageFont.truetype("arial.ttf", bullet_size)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", title_size)
                bullet_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", bullet_size)
            except:
                title_font = ImageFont.load_default()
                bullet_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (width - bbox[2]) // 2
        draw.text((x, 60), title, fill='#FFD700', font=title_font)
        
        y = 180
        for point in bullets[:6]:
            bullet_text = "• " + point
            bbox = draw.textbbox((0, 0), bullet_text, font=bullet_font)
            x = 120
            draw.text((x, y), bullet_text, fill='white', font=bullet_font)
            y += bullet_size + 20
        
        return img
    
    def create_chart_slide(self, title, data, width=1280, height=720):
        img = self.image_gen.get_random_image("finance", width, height)
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for x in range(width):
            for y in range(height):
                overlay.putpixel((x, y), (0, 0, 0, 150))
        
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        try:
            title_size = 55 if width > 1000 else 40
            label_size = 35 if width > 1000 else 25
            title_font = ImageFont.truetype("arial.ttf", title_size)
            label_font = ImageFont.truetype("arial.ttf", label_size)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", title_size)
                label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", label_size)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (width - bbox[2]) // 2
        draw.text((x, 40), title, fill='#FFD700', font=title_font)
        
        if not data:
            data = {'No Data': 1}
        
        max_val = max(data.values()) if data else 1
        if max_val == 0:
            max_val = 1
        
        bar_width = min((width - 300) // len(data), 120)
        x_start = (width - (bar_width * len(data) + 40 * (len(data) - 1))) // 2
        y_base = height - 120
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
        
        for i, (label, value) in enumerate(data.items()):
            bar_height = (value / max_val) * (height - 250)
            if bar_height < 10:
                bar_height = 10
            x = x_start + i * (bar_width + 40)
            color = colors[i % len(colors)]
            
            draw.rectangle([x, y_base - bar_height, x + bar_width, y_base], fill=color)
            draw.text((x + bar_width//2 - 15, y_base - bar_height - 35), 
                     str(int(value)), fill='white', font=label_font)
            
            bbox = draw.textbbox((0, 0), label, font=label_font)
            draw.text((x + (bar_width - bbox[2])//2, y_base + 15), 
                     label, fill='white', font=label_font)
        
        return img
    
    def generate_voiceover(self, text, output_path, lang='en'):
        if not text or text.strip() == "":
            return None
        
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            return output_path
        except Exception as e:
            st.error("Error generating voiceover: " + str(e))
            return None
    
    def create_video_ffmpeg(self, scenes, output_path, lang='en', duration_per_scene=5):
        temp_files = []
        video_parts = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_scenes = len(scenes)
        
        # Create images and audio for each scene
        for idx, scene in enumerate(scenes):
            progress = (idx / total_scenes) * 100
            progress_bar.progress(int(progress))
            status_text.text("Processing scene " + str(idx + 1) + "/" + str(total_scenes))
            
            # Generate image
            scene_type = scene.get('type', 'text')
            width, height = self.resolution
            
            if scene_type == 'text':
                img = self.create_text_slide(
                    scene.get('content', ''),
                    width=width,
                    height=height
                )
            elif scene_type == 'bullets':
                img = self.create_bullet_slide(
                    scene.get('title', ''),
                    scene.get('bullets', []),
                    width=width,
                    height=height
                )
            elif scene_type == 'chart':
                img = self.create_chart_slide(
                    scene.get('title', ''),
                    scene.get('data', {}),
                    width=width,
                    height=height
                )
            else:
                img = self.create_text_slide(
                    "Scene",
                    width=width,
                    height=height
                )
            
            # Save image
            img_path = os.path.join(self.temp_dir, "scene_" + str(idx) + ".png")
            img.save(img_path)
            temp_files.append(img_path)
            
            # Generate voiceover
            voiceover_text = scene.get('voiceover', '')
            audio_path = os.path.join(self.temp_dir, "audio_" + str(idx) + ".mp3")
            
            if voiceover_text:
                self.generate_voiceover(voiceover_text, audio_path, lang)
                if os.path.exists(audio_path):
                    temp_files.append(audio_path)
                    # Get audio duration
                    try:
                        import subprocess
                        result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path], 
                                               capture_output=True, text=True)
                        duration = float(result.stdout.strip()) if result.stdout else duration_per_scene
                    except:
                        duration = duration_per_scene
                else:
                    duration = duration_per_scene
            else:
                duration = duration_per_scene
            
            video_parts.append({'image': img_path, 'audio': audio_path if os.path.exists(audio_path) else None, 'duration': duration})
        
        progress_bar.progress(80)
        status_text.text("Creating video with FFmpeg...")
        
        # Create video using FFmpeg
        try:
            # Create a concat file for video segments
            concat_file = os.path.join(self.temp_dir, "concat.txt")
            with open(concat_file, 'w') as f:
                for part in video_parts:
                    f.write("file '" + part['image'] + "'\n")
                    f.write("duration " + str(part['duration']) + "\n")
            
            # Build FFmpeg command
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-r', str(self.fps),
                '-vf', 'scale=' + str(self.resolution[0]) + ':' + str(self.resolution[1]) + ':force_original_aspect_ratio=decrease,pad=' + str(self.resolution[0]) + ':' + str(self.resolution[1]) + ':(ow-iw)/2:(oh-ih)/2',
                output_path
            ]
            
            # Run FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                st.error("FFmpeg error: " + result.stderr)
                # Try alternative method with image sequence
                return self.create_video_with_images(video_parts, output_path)
            
        except Exception as e:
            st.warning("FFmpeg method failed, trying alternative...")
            return self.create_video_with_images(video_parts, output_path)
        
        progress_bar.progress(100)
        status_text.text("Video generation complete!")
        
        # Cleanup
        for file in temp_files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except:
                pass
        
        return output_path
    
    def create_video_with_images(self, video_parts, output_path):
        """Alternative method using image sequence"""
        import subprocess
        
        # Create a temporary directory for frames
        frames_dir = os.path.join(self.temp_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        
        frame_count = 0
        for part in video_parts:
            img = Image.open(part['image'])
            duration = part['duration']
            frames = int(duration * self.fps)
            
            for i in range(frames):
                frame_path = os.path.join(frames_dir, "frame_" + str(frame_count).zfill(6) + ".png")
                img.save(frame_path)
                frame_count += 1
        
        # Create video from frames
        cmd = [
            'ffmpeg', '-y',
            '-framerate', str(self.fps),
            '-i', os.path.join(frames_dir, "frame_%06d.png"),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=' + str(self.resolution[0]) + ':' + str(self.resolution[1]) + ':force_original_aspect_ratio=decrease,pad=' + str(self.resolution[0]) + ':' + str(self.resolution[1]) + ':(ow-iw)/2:(oh-ih)/2',
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True)
        
        # Cleanup frames
        import shutil
        shutil.rmtree(frames_dir, ignore_errors=True)
        
        return output_path

def main():
    st.markdown('<h1 class="main-header">🎬 AI Explainer Video Generator</h1>', unsafe_allow_html=True)
    st.markdown(INFO_HTML, unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("Settings")
        
        lang = st.selectbox(
            "Voiceover Language",
            ["en", "es", "fr", "de", "it", "pt", "ja", "zh", "hi"],
            index=0
        )
        
        resolution = st.selectbox(
            "Video Quality",
            ["1280x720 (HD)", "854x480 (SD)"],
            index=0
        )
        
        duration_per_scene = st.slider(
            "Default Duration per Scene (seconds)",
            min_value=2,
            max_value=10,
            value=5
        )
        
        st.divider()
        st.caption("Note: Videos are generated using FFmpeg")
    
    tab1, tab2, tab3 = st.tabs(["Script Input", "Scene Preview", "Generate Video"])
    
    with tab1:
        st.subheader("Enter Your Script")
        
        script_input = st.text_area(
            "Write or paste your script here",
            value=st.session_state.get('script_input', ''),
            height=400,
            help="Use # for titles, - for bullet points, and key=value for charts"
        )
        
        st.session_state.script_input = script_input
        
        with st.expander("Script Writing Tips"):
            st.markdown("### How to Write Your Script")
            st.markdown("**Use # for titles:**")
            st.markdown("`# Welcome to Our Video`")
            st.markdown("")
            st.markdown("**Use - for bullet points:**")
            st.markdown("`- First important point`")
            st.markdown("")
            st.markdown("**Use key=value for charts:**")
            st.markdown("`Sales: A=100, B=200, C=150`")
            st.markdown("")
            st.markdown("### Example Script:")
            st.code(
                "# Welcome to AI Explainer\n\n"
                "Artificial intelligence is transforming our world.\n\n"
                "Key AI applications:\n"
                "- Healthcare diagnosis\n"
                "- Self-driving cars\n\n"
                "AI adoption by industry:\n"
                "Technology: 85%\n"
                "Finance: 72%"
            )
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Analyze Script", use_container_width=True):
                if script_input.strip():
                    parser = ScriptParser()
                    scenes = parser.auto_generate_scenes(script_input)
                    st.session_state.scenes = scenes
                    st.success("Analyzed! Found " + str(len(scenes)) + " scenes")
                    st.rerun()
                else:
                    st.warning("Please enter a script first")
        
        with col2:
            if st.button("Clear Script", use_container_width=True):
                st.session_state.script_input = ""
                st.session_state.scenes = []
                st.rerun()
    
    with tab2:
        st.subheader("Auto-Generated Scenes")
        
        if not st.session_state.scenes:
            st.info("Enter a script and click 'Analyze Script' to generate scenes")
        else:
            st.success(str(len(st.session_state.scenes)) + " scenes generated")
            
            video_creator = VideoCreator()
            width, height = 800, 450
            
            for idx, scene in enumerate(st.session_state.scenes):
                with st.expander("Scene " + str(idx + 1), expanded=False):
                    if scene['type'] == 'text':
                        st.markdown("**Content:** " + scene.get('content', ''))
                        img = video_creator.create_text_slide(
                            scene.get('content', ''),
                            width=width,
                            height=height
                        )
                        st.image(img, caption="Preview")
                    elif scene['type'] == 'bullets':
                        st.markdown("**Title:** " + scene.get('title', ''))
                        for bullet in scene.get('bullets', []):
                            st.markdown("  • " + bullet)
                        img = video_creator.create_bullet_slide(
                            scene.get('title', ''),
                            scene.get('bullets', []),
                            width=width,
                            height=height
                        )
                        st.image(img, caption="Preview")
                    elif scene['type'] == 'chart':
                        st.markdown("**Chart:** " + scene.get('title', ''))
                        st.json(scene.get('data', {}))
                        img = video_creator.create_chart_slide(
                            scene.get('title', ''),
                            scene.get('data', {}),
                            width=width,
                            height=height
                        )
                        st.image(img, caption="Preview")
                    
                    voiceover = scene.get('voiceover', '')
                    if voiceover:
                        st.caption("Voiceover: " + voiceover[:100] + ("..." if len(voiceover) > 100 else ""))
                    else:
                        st.warning("No voiceover text")
    
    with tab3:
        st.subheader("Generate Video")
        
        if not st.session_state.scenes:
            st.warning("Please analyze your script first (Tab 1) to generate scenes.")
        else:
            total_duration = sum(len(scene.get('voiceover', '')) * 0.3 for scene in st.session_state.scenes)
            if total_duration < 1:
                total_duration = len(st.session_state.scenes) * duration_per_scene
            st.info("📊 " + str(len(st.session_state.scenes)) + " scenes, estimated duration: " + str(int(total_duration)) + " seconds")
            
            st.warning("⚠️ Video generation may take 1-3 minutes depending on the number of scenes.")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                video_name = st.text_input(
                    "Video Name",
                    value="explainer_" + datetime.now().strftime('%Y%m%d_%H%M%S')
                )
            
            with col2:
                st.write("")
                if st.button("🎬 Generate MP4 Video", type="primary", use_container_width=True):
                    try:
                        if "1280" in resolution:
                            width, height = 1280, 720
                        else:
                            width, height = 854, 480
                        
                        video_creator = VideoCreator(resolution=(width, height), fps=24)
                        
                        output_filename = video_name + ".mp4"
                        output_path = os.path.join(tempfile.gettempdir(), output_filename)
                        
                        video_creator.create_video_ffmpeg(
                            st.session_state.scenes,
                            output_path,
                            lang=lang,
                            duration_per_scene=duration_per_scene
                        )
                        
                        if os.path.exists(output_path):
                            st.session_state.video_path = output_path
                            st.session_state.video_generated = True
                            st.success("✅ Video generated successfully!")
                        else:
                            st.error("Video generation failed. Please try again.")
                        
                    except Exception as e:
                        st.error("Error generating video: " + str(e))
                        st.exception(e)
            
            if st.session_state.video_generated and st.session_state.video_path:
                st.divider()
                st.markdown(SUCCESS_HTML, unsafe_allow_html=True)
                
                try:
                    with open(st.session_state.video_path, 'rb') as f:
                        video_bytes = f.read()
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(
                            label="📥 Download MP4 Video",
                            data=video_bytes,
                            file_name=video_name + ".mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    
                    st.video(st.session_state.video_path)
                    
                except Exception as e:
                    st.error("Error loading video: " + str(e))

if __name__ == "__main__":
    main()