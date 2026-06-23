import streamlit as st
import json
import os
import tempfile
from datetime import datetime
import time
import requests
from gtts import gTTS
from pydub import AudioSegment
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import *
import re
from io import BytesIO
import random

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="AI Explainer Video Generator",
    page_icon="🎬",
    layout="wide"
)

# ============ CUSTOM CSS ============
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
    '🤖 <b>Just provide your script - we will do the rest!</b><br>'
    'Our AI will automatically:'
    '• Parse your script into scenes'
    '• Generate relevant images for each scene'
    '• Create voiceovers from your text'
    '• Combine everything into a professional video'
    '</div>'
)

SUCCESS_HTML = (
    '<div class="success-box">'
    '<h3>✅ Your Video is Ready!</h3>'
    '</div>'
)

# ============ APPLY CSS ============
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ============ INITIALIZE SESSION STATE ============
if 'scenes' not in st.session_state:
    st.session_state.scenes = []
if 'video_generated' not in st.session_state:
    st.session_state.video_generated = False
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'auto_generated' not in st.session_state:
    st.session_state.auto_generated = False
if 'script_input' not in st.session_state:
    st.session_state.script_input = ""

# ============ FREE IMAGE GENERATION ============
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

# ============ FREE VIDEO GENERATION ============
class FreeVideoGenerator:
    def __init__(self):
        self.image_gen = FreeImageGenerator()
        
    def create_text_with_image(self, text, image=None, duration=3, width=1920, height=1080):
        if image is None:
            image = self.image_gen.get_random_image("nature", width, height)
        
        if image.size != (width, height):
            image = image.resize((width, height), Image.LANCZOS)
        
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
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
        
        y_offset = (height - len(lines) * 70) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (width - bbox[2]) // 2
            draw.text((x+2, y_offset+2), line, fill='black', font=font)
            draw.text((x, y_offset), line, fill='white', font=font)
            y_offset += 70
        
        img_array = np.array(image)
        clip = ImageClip(img_array).set_duration(duration)
        return clip
    
    def create_bullet_slide(self, title, bullets, duration=3, width=1920, height=1080):
        image = self.image_gen.get_random_image("business", width, height)
        
        if image.size != (width, height):
            image = image.resize((width, height), Image.LANCZOS)
        
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for x in range(width):
            for y in range(height):
                overlay.putpixel((x, y), (0, 0, 0, 150))
        
        image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)
        image = image.convert('RGB')
        
        draw = ImageDraw.Draw(image)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 70)
            bullet_font = ImageFont.truetype("arial.ttf", 45)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 70)
                bullet_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
            except:
                title_font = ImageFont.load_default()
                bullet_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (width - bbox[2]) // 2
        draw.text((x, 80), title, fill='#FFD700', font=title_font)
        
        y = 200
        for point in bullets[:6]:
            bullet_text = "• " + point
            bbox = draw.textbbox((0, 0), bullet_text, font=bullet_font)
            x = 150
            draw.text((x, y), bullet_text, fill='white', font=bullet_font)
            y += 70
        
        img_array = np.array(image)
        clip = ImageClip(img_array).set_duration(duration)
        return clip
    
    def create_chart_slide(self, title, data, duration=3, width=1920, height=1080):
        image = self.image_gen.get_random_image("finance", width, height)
        
        if image.size != (width, height):
            image = image.resize((width, height), Image.LANCZOS)
        
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for x in range(width):
            for y in range(height):
                overlay.putpixel((x, y), (0, 0, 0, 100))
        
        image = image.convert('RGBA')
        image = Image.alpha_composite(image, overlay)
        image = image.convert('RGB')
        
        draw = ImageDraw.Draw(image)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            label_font = ImageFont.truetype("arial.ttf", 35)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
                label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 35)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (width - bbox[2]) // 2
        draw.text((x, 50), title, fill='#FFD700', font=title_font)
        
        if not data:
            data = {'No Data': 1}
        
        max_val = max(data.values()) if data else 1
        if max_val == 0:
            max_val = 1
        
        bar_width = min((width - 300) // len(data), 120)
        x_start = (width - (bar_width * len(data) + 50 * (len(data) - 1))) // 2
        y_base = height - 150
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
        
        for i, (label, value) in enumerate(data.items()):
            bar_height = (value / max_val) * (height - 300)
            if bar_height < 10:
                bar_height = 10
            x = x_start + i * (bar_width + 50)
            color = colors[i % len(colors)]
            
            draw.rectangle([x, y_base - bar_height, x + bar_width, y_base], fill=color)
            draw.text((x + bar_width//2 - 15, y_base - bar_height - 30), 
                     str(int(value)), fill='white', font=label_font)
            
            bbox = draw.textbbox((0, 0), label, font=label_font)
            draw.text((x + (bar_width - bbox[2])//2, y_base + 10), 
                     label, fill='white', font=label_font)
        
        img_array = np.array(image)
        clip = ImageClip(img_array).set_duration(duration)
        return clip

# ============ SCRIPT PARSER ============
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

# ============ VIDEO MAKER ============
class AutoVideoMaker:
    def __init__(self, resolution=(1920, 1080), fps=24):
        self.resolution = resolution
        self.fps = fps
        self.temp_dir = tempfile.mkdtemp()
        self.parser = ScriptParser()
        self.video_gen = FreeVideoGenerator()
        
    def generate_voiceover(self, text, output_path, lang='en'):
        try:
            if not text or text.strip() == "":
                silent = AudioSegment.silent(duration=2000)
                silent.export(output_path, format="mp3")
                return output_path
            
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            return output_path
        except Exception as e:
            st.error("Error generating voiceover: " + str(e))
            silent = AudioSegment.silent(duration=3000)
            silent.export(output_path, format="mp3")
            return output_path
    
    def get_audio_duration(self, audio_path):
        try:
            audio = AudioSegment.from_mp3(audio_path)
            return len(audio) / 1000.0
        except:
            return 3.0
    
    def create_scene_visual(self, scene, duration):
        scene_type = scene.get('type', 'text')
        width, height = self.resolution
        
        if scene_type == 'text':
            return self.video_gen.create_text_with_image(
                scene.get('content', ''),
                duration=duration,
                width=width,
                height=height
            )
        elif scene_type == 'bullets':
            return self.video_gen.create_bullet_slide(
                scene.get('title', 'Key Points'),
                scene.get('bullets', ['Point 1']),
                duration=duration,
                width=width,
                height=height
            )
        elif scene_type == 'chart':
            return self.video_gen.create_chart_slide(
                scene.get('title', 'Data Chart'),
                scene.get('data', {'A': 10, 'B': 20, 'C': 15}),
                duration=duration,
                width=width,
                height=height
            )
        else:
            return self.video_gen.create_text_with_image(
                "Scene",
                duration=duration,
                width=width,
                height=height
            )
    
    def generate_video(self, script_text, output_path, lang='en'):
        st.info("Analyzing your script...")
        
        scenes = self.parser.auto_generate_scenes(script_text)
        
        if not scenes:
            st.error("Could not parse script. Please check your input.")
            return None
        
        st.success("Generated " + str(len(scenes)) + " scenes from your script")
        
        video_clips = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_scenes = len(scenes)
        
        for idx, scene in enumerate(scenes):
            progress = (idx / total_scenes) * 100
            progress_bar.progress(int(progress))
            status_text.text("Creating scene " + str(idx + 1) + "/" + str(total_scenes))
            
            voiceover_text = scene.get('voiceover', '')
            audio_path = os.path.join(self.temp_dir, "audio_" + str(idx) + ".mp3")
            self.generate_voiceover(voiceover_text, audio_path, lang)
            
            duration = self.get_audio_duration(audio_path)
            
            clip = self.create_scene_visual(scene, duration)
            
            audio = AudioFileClip(audio_path)
            clip = clip.set_audio(audio)
            
            video_clips.append(clip)
        
        progress_bar.progress(90)
        status_text.text("Rendering final video...")
        
        if video_clips:
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                verbose=False,
                logger=None
            )
            
            final_video.close()
            for clip in video_clips:
                clip.close()
        
        progress_bar.progress(100)
        status_text.text("Video generation complete!")
        
        st.session_state.scenes = scenes
        st.session_state.auto_generated = True
        
        return output_path

# ============ MAIN APP ============
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
            ["1920x1080 (HD)", "1280x720 (SD)", "854x480 (Low)"],
            index=0
        )
    
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
            st.markdown("""
            ### How to Write Your Script
            
            **Use # for titles:**  
            `# Welcome to Our Video`
            
            **Use - for bullet points:**  
            `- First important point`  
            
            **Use key=value for charts:**  
            `Sales: A=100, B=200, C=150`
            """)
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Analyze Script", use_container_width=True):
                if script_input.strip():
                    parser = ScriptParser()
                    scenes = parser.auto_generate_scenes(script_input)
                    st.session_state.scenes = scenes
                    st.session_state.auto_generated = True
                    st.success("Analyzed! Found " + str(len(scenes)) + " scenes")
                    st.rerun()
                else:
                    st.warning("Please enter a script first")
        
        with col2:
            if st.button("Clear Script", use_container_width=True):
                st.session_state.script_input = ""
                st.session_state.scenes = []
                st.session_state.auto_generated = False
                st.rerun()
    
    with tab2:
        st.subheader("Auto-Generated Scenes")
        
        if not st.session_state.scenes:
            st.info("Enter a script and click 'Analyze Script' to generate scenes")
        else:
            st.success(str(len(st.session_state.scenes)) + " scenes generated")
            
            for idx, scene in enumerate(st.session_state.scenes):
                with st.expander("Scene " + str(idx + 1), expanded=False):
                    if scene['type'] == 'text':
                        st.markdown("**Content:** " + scene.get('content', ''))
                    elif scene['type'] == 'bullets':
                        st.markdown("**Title:** " + scene.get('title', ''))
                        for bullet in scene.get('bullets', []):
                            st.markdown("  • " + bullet)
                    elif scene['type'] == 'chart':
                        st.markdown("**Chart:** " + scene.get('title', ''))
                        st.json(scene.get('data', {}))
                    
                    voiceover = scene.get('voiceover', '')
                    st.caption("Voiceover: " + voiceover[:100])
    
    with tab3:
        st.subheader("Generate Your Video")
        
        if not st.session_state.scenes:
            st.warning("Please analyze your script first (Tab 1) to generate scenes.")
        else:
            total_duration = sum(len(scene.get('voiceover', '')) * 0.3 for scene in st.session_state.scenes)
            st.info(str(len(st.session_state.scenes)) + " scenes, estimated duration: " + str(int(total_duration)) + " seconds")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                video_name = st.text_input(
                    "Video Name",
                    value="explainer_" + datetime.now().strftime('%Y%m%d_%H%M%S')
                )
            
            with col2:
                st.write("")
                if st.button("Generate Video", type="primary", use_container_width=True):
                    try:
                        res_parts = resolution.split('x')
                        width = int(res_parts[0].strip())
                        height = int(res_parts[1].split('(')[0].strip())
                        
                        video_maker = AutoVideoMaker(resolution=(width, height), fps=24)
                        
                        script_text = st.session_state.get('script_input', '')
                        if not script_text:
                            st.error("No script found. Please enter a script first.")
                            return
                        
                        output_filename = video_name + ".mp4"
                        output_path = os.path.join(tempfile.gettempdir(), output_filename)
                        
                        video_maker.generate_video(script_text, output_path, lang)
                        
                        st.session_state.video_path = output_path
                        st.session_state.video_generated = True
                        
                        st.success("Video generated successfully!")
                        
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
                            label="Download Video (MP4)",
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