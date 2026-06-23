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
import zipfile
import base64

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
    '🤖 <b>Just provide your script - we will do the rest!</b><br>'
    'Our AI will automatically:'
    '• Parse your script into scenes'
    '• Generate relevant images for each scene'
    '• Package them into a downloadable ZIP file'
    '</div>'
)

SUCCESS_HTML = (
    '<div class="success-box">'
    '<h3>✅ Your Slides are Ready!</h3>'
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
        
    def get_random_image(self, keyword="nature", width=800, height=600):
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

class SlideCreator:
    def __init__(self):
        self.image_gen = FreeImageGenerator()
        
    def create_text_slide(self, text, bg_color='#1a237e', text_color='#ffffff', width=800, height=600):
        bg_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        img = Image.new('RGB', (width, height), color=bg_rgb)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
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
        
        y_offset = (height - len(lines) * 50) // 2
        text_rgb = tuple(int(text_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (width - bbox[2]) // 2
            draw.text((x+2, y_offset+2), line, fill='black', font=font)
            draw.text((x, y_offset), line, fill=text_rgb, font=font)
            y_offset += 50
        
        return img
    
    def create_bullet_slide(self, title, bullets, width=800, height=600):
        img = self.image_gen.get_random_image("business", width, height)
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
            title_font = ImageFont.truetype("arial.ttf", 50)
            bullet_font = ImageFont.truetype("arial.ttf", 30)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
                bullet_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
            except:
                title_font = ImageFont.load_default()
                bullet_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (width - bbox[2]) // 2
        draw.text((x, 50), title, fill='#FFD700', font=title_font)
        
        y = 150
        for point in bullets[:6]:
            bullet_text = "• " + point
            bbox = draw.textbbox((0, 0), bullet_text, font=bullet_font)
            x = 100
            draw.text((x, y), bullet_text, fill='white', font=bullet_font)
            y += 50
        
        return img
    
    def create_chart_slide(self, title, data, width=800, height=600):
        img = self.image_gen.get_random_image("finance", width, height)
        if img.size != (width, height):
            img = img.resize((width, height), Image.LANCZOS)
        
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        for x in range(width):
            for y in range(height):
                overlay.putpixel((x, y), (0, 0, 0, 100))
        
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 40)
            label_font = ImageFont.truetype("arial.ttf", 25)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
                label_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 25)
            except:
                title_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (width - bbox[2]) // 2
        draw.text((x, 30), title, fill='#FFD700', font=title_font)
        
        if not data:
            data = {'No Data': 1}
        
        max_val = max(data.values()) if data else 1
        if max_val == 0:
            max_val = 1
        
        bar_width = min((width - 200) // len(data), 80)
        x_start = (width - (bar_width * len(data) + 30 * (len(data) - 1))) // 2
        y_base = height - 100
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
        
        for i, (label, value) in enumerate(data.items()):
            bar_height = (value / max_val) * (height - 200)
            if bar_height < 10:
                bar_height = 10
            x = x_start + i * (bar_width + 30)
            color = colors[i % len(colors)]
            
            draw.rectangle([x, y_base - bar_height, x + bar_width, y_base], fill=color)
            draw.text((x + bar_width//2 - 10, y_base - bar_height - 25), 
                     str(int(value)), fill='white', font=label_font)
            
            bbox = draw.textbbox((0, 0), label, font=label_font)
            draw.text((x + (bar_width - bbox[2])//2, y_base + 10), 
                     label, fill='white', font=label_font)
        
        return img

def main():
    st.markdown('<h1 class="main-header">🎬 AI Explainer Video Generator</h1>', unsafe_allow_html=True)
    st.markdown(INFO_HTML, unsafe_allow_html=True)
    
    with st.sidebar:
        st.header("Settings")
        
        resolution = st.selectbox(
            "Image Quality",
            ["High (800x600)", "Medium (600x400)", "Low (400x300)"],
            index=0
        )
    
    tab1, tab2, tab3 = st.tabs(["Script Input", "Scene Preview", "Generate Slides"])
    
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
            st.code("# Welcome to AI Explainer\n\nArtificial intelligence is transforming our world.\n\nKey AI applications:\n- Healthcare diagnosis\n- Self-driving cars\n\nAI adoption by industry:\nTechnology: 85%\nFinance: 72%")
        
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
            
            slide_creator = SlideCreator()
            width, height = 600, 400
            
            for idx, scene in enumerate(st.session_state.scenes):
                with st.expander("Scene " + str(idx + 1), expanded=False):
                    if scene['type'] == 'text':
                        st.markdown("**Content:** " + scene.get('content', ''))
                        img = slide_creator.create_text_slide(
                            scene.get('content', ''),
                            width=width,
                            height=height
                        )
                        st.image(img, caption="Preview")
                    elif scene['type'] == 'bullets':
                        st.markdown("**Title:** " + scene.get('title', ''))
                        for bullet in scene.get('bullets', []):
                            st.markdown("  • " + bullet)
                        img = slide_creator.create_bullet_slide(
                            scene.get('title', ''),
                            scene.get('bullets', []),
                            width=width,
                            height=height
                        )
                        st.image(img, caption="Preview")
                    elif scene['type'] == 'chart':
                        st.markdown("**Chart:** " + scene.get('title', ''))
                        st.json(scene.get('data', {}))
                        img = slide_creator.create_chart_slide(
                            scene.get('title', ''),
                            scene.get('data', {}),
                            width=width,
                            height=height
                        )
                        st.image(img, caption="Preview")
                    
                    voiceover = scene.get('voiceover', '')
                    st.caption("Voiceover: " + voiceover[:100])
    
    with tab3:
        st.subheader("Generate Slides")
        
        if not st.session_state.scenes:
            st.warning("Please analyze your script first (Tab 1) to generate scenes.")
        else:
            if "High" in resolution:
                width, height = 800, 600
            elif "Medium" in resolution:
                width, height = 600, 400
            else:
                width, height = 400, 300
            
            total_duration = sum(len(scene.get('voiceover', '')) * 0.3 for scene in st.session_state.scenes)
            st.info(str(len(st.session_state.scenes)) + " scenes, estimated duration: " + str(int(total_duration)) + " seconds")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                video_name = st.text_input(
                    "File Name",
                    value="slides_" + datetime.now().strftime('%Y%m%d_%H%M%S')
                )
            
            with col2:
                st.write("")
                if st.button("Generate Slides", type="primary", use_container_width=True):
                    try:
                        slide_creator = SlideCreator()
                        images = []
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        total_scenes = len(st.session_state.scenes)
                        
                        for idx, scene in enumerate(st.session_state.scenes):
                            progress = (idx / total_scenes) * 100
                            progress_bar.progress(int(progress))
                            status_text.text("Creating scene " + str(idx + 1) + "/" + str(total_scenes))
                            
                            if scene['type'] == 'text':
                                img = slide_creator.create_text_slide(
                                    scene.get('content', ''),
                                    width=width,
                                    height=height
                                )
                            elif scene['type'] == 'bullets':
                                img = slide_creator.create_bullet_slide(
                                    scene.get('title', ''),
                                    scene.get('bullets', []),
                                    width=width,
                                    height=height
                                )
                            elif scene['type'] == 'chart':
                                img = slide_creator.create_chart_slide(
                                    scene.get('title', ''),
                                    scene.get('data', {}),
                                    width=width,
                                    height=height
                                )
                            else:
                                img = slide_creator.create_text_slide(
                                    "Scene " + str(idx + 1),
                                    width=width,
                                    height=height
                                )
                            
                            images.append(img)
                        
                        progress_bar.progress(100)
                        status_text.text("Slides generated successfully!")
                        
                        zip_path = os.path.join(tempfile.gettempdir(), video_name + ".zip")
                        
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for i, img in enumerate(images):
                                img_path = os.path.join(tempfile.gettempdir(), "slide_" + str(i) + ".png")
                                img.save(img_path)
                                zipf.write(img_path, "slide_" + str(i) + ".png")
                                os.remove(img_path)
                        
                        st.session_state.video_path = zip_path
                        st.session_state.video_generated = True
                        
                        st.success("Slides generated successfully! Download the ZIP file below.")
                        
                    except Exception as e:
                        st.error("Error generating slides: " + str(e))
                        st.exception(e)
            
            if st.session_state.video_generated and st.session_state.video_path:
                st.divider()
                st.markdown(SUCCESS_HTML, unsafe_allow_html=True)
                
                try:
                    with open(st.session_state.video_path, 'rb') as f:
                        zip_bytes = f.read()
                    
                    st.download_button(
                        label="Download Slides (ZIP)",
                        data=zip_bytes,
                        file_name=video_name + ".zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    
                    st.info("You can use these images to create a video with any video editing software.")
                    
                except Exception as e:
                    st.error("Error loading file: " + str(e))

if __name__ == "__main__":
    main()