"""

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
    """Generate free images using various APIs"""
    
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
        """Get a free stock image based on keyword"""
        try:
            url = f"https://picsum.photos/seed/{random.randint(1, 1000)}/{width}/{height}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                return img
        except:
            pass
        
        try:
            url = f"https://source.unsplash.com/featured/{width}x{height}/?{keyword}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                return img
        except:
            pass
        
        return self.create_gradient_image(width, height)
    
    def create_gradient_image(self, width, height):
        """Create a gradient background as fallback"""
        img = Image.new('RGB', (width, height))
        for x in range(width):
            for y in range(height):
                r = int(30 + (x / width) * 100)
                g = int(40 + (y / height) * 100)
                b = int(200 - (x / width) * 80)
                img.putpixel((x, y), (r, g, b))
        return img
    
    def get_relevant_keyword(self, text):
        """Extract relevant keyword from text"""
        text_lower = text.lower()
        for topic, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return keyword
        return "nature"

# ============ FREE VIDEO GENERATION ============
class FreeVideoGenerator:
    """Generate video clips using free resources"""
    
    def __init__(self):
        self.image_gen = FreeImageGenerator()
        
    def create_text_with_image(self, text, image=None, duration=3, width=1920, height=1080):
        """Create a slide with text overlay on image"""
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
        
        # Word wrap
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
        """Create a bullet point slide with background"""
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
            bullet_text = f"• {point}"
            bbox = draw.textbbox((0, 0), bullet_text, font=bullet_font)
            x = 150
            draw.text((x, y), bullet_text, fill='white', font=bullet_font)
            y += 70
        
        img_array = np.array(image)
        clip = ImageClip(img_array).set_duration(duration)
        return clip
    
    def create_chart_slide(self, title, data, duration=3, width=1920, height=1080):
        """Create a chart slide with background"""
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
    """Parse user script into scenes automatically"""
    
    def __init__(self):
        self.scenes = []
        
    def parse_script(self, script_text):
        """Convert script text into video scenes"""
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
                            'voiceover': f"Chart showing {title} with data: {data_str}"
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
        """Generate scenes intelligently from script"""
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
                        'title': f"Key Point {i+1}",
                        'bullets': bullets,
                        'voiceover': sentence
                    })
                else:
                    numbers = re.findall(r'\d+', sentence)
                    if numbers:
                        data = {f"Item{i+1}": int(n) for i, n in enumerate(numbers[:6])}
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

# ============ VIDEO MAKER WITH AUTO CONTENT ============
class AutoVideoMaker:
    """Create videos with auto-generated content"""
    
    def __init__(self, resolution=(1920, 1080), fps=24):
        self.resolution = resolution
        self.fps = fps
        self.temp_dir = tempfile.mkdtemp()
        self.parser = ScriptParser()
        self.video_gen = FreeVideoGenerator()
        
    def generate_voiceover(self, text, output_path, lang='en'):
        """Generate voiceover using gTTS"""
        try:
            if not text or text.strip() == "":
                silent = AudioSegment.silent(duration=2000)
                silent.export(output_path, format="mp3")
                return output_path
            
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            return output_path
        except Exception as e:
            st.error(f"Error generating voiceover: {str(e)}")
            silent = AudioSegment.silent(duration=3000)
            silent.export(output_path, format="mp3")
            return output_path
    
    def get_audio_duration(self, audio_path):
        """Get audio duration in seconds"""
        try:
            audio = AudioSegment.from_mp3(audio_path)
            return len(audio) / 1000.0
        except:
            return 3.0
    
    def create_scene_visual(self, scene, duration):
        """Create visual for a scene based on its type"""
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
        """Generate complete video from script text"""
        st.info("🔍 Analyzing your script...")
        
        scenes = self.parser.auto_generate_scenes(script_text)
        
        if not scenes:
            st.error("Could not parse script. Please check your input.")
            return None
        
        st.success(f"✅ Generated {len(scenes)} scenes from your script")
        
        video_clips = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_scenes = len(scenes)
        
        for idx, scene in enumerate(scenes):
            progress = (idx / total_scenes) * 100
            progress_bar.progress(int(progress))
            status_text.text(f"🎬 Creating scene {idx + 1}/{total_scenes}: {scene.get('type', 'unknown')}")
            
            voiceover_text = scene.get('voiceover', '')
            audio_path = os.path.join(self.temp_dir, f"audio_{idx}.mp3")
            self.generate_voiceover(voiceover_text, audio_path, lang)
            
            duration = self.get_audio_duration(audio_path)
            
            clip = self.create_scene_visual(scene, duration)
            
            audio = AudioFileClip(audio_path)
            clip = clip.set_audio(audio)
            
            video_clips.append(clip)
        
        progress_bar.progress(90)
        status_text.text("🎞️ Rendering final video...")
        
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
        status_text.text("✅ Video generation complete!")
        
        st.session_state.scenes = scenes
        st.session_state.auto_generated = True
        
        return output_path

# ============ MAIN APP ============
def main():
    # Header
    st.markdown('<h1 class="main-header">🎬 AI Auto Explainer Video Generator</h1>', unsafe_allow_html=True)
    
    # Info box
    st.markdown(INFO_HTML, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
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
        
        st.divider()
        
        st.subheader("📝 Sample Scripts")
        
        if st.button("📊 Business Script"):
            sample = """# Welcome to Our Business Explainer
            
In today's competitive market, businesses need to adapt and innovate.

Key strategies for success:
- Customer-centric approach
- Digital transformation
- Data-driven decisions
- Continuous innovation

Our approach has shown remarkable results:
Customer satisfaction: 95%
Revenue growth: 150%
Market share: 35%
Employee engagement: 90%

# Join us in transforming your business"""
            st.session_state.script_input = sample
            st.rerun()
        
        if st.button("🔬 Science Script"):
            sample = """# The Future of Science
            
Science is advancing at an unprecedented pace.

Breakthrough technologies:
- Artificial Intelligence
- Gene Editing
- Quantum Computing
- Renewable Energy

Impact on society:
Healthcare: 85%
Environment: 70%
Education: 65%
Economy: 90%

# A brighter future through science"""
            st.session_state.script_input = sample
            st.rerun()
        
        if st.button("🎓 Education Script"):
            sample = """# Learn Anywhere, Anytime
            
Education is evolving with technology.

Modern learning methods:
- Online courses
- Interactive content
- AI tutors
- Collaborative projects

Student success rates:
Online: 88%
Traditional: 75%
Blended: 92%

# Empowering learners worldwide"""
            st.session_state.script_input = sample
            st.rerun()
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["✍️ Script Input", "👁️ Scene Preview", "🎬 Generate Video"])
    
    # TAB 1: Script Input
    with tab1:
        st.subheader("Enter Your Script")
        
        default_script = """# Welcome to Our Explainer Video

This is a powerful way to communicate your message.

Key benefits:
- Easy to understand
- Engaging visual content
- Professional voiceover
- Automated generation

Our platform makes it simple:
User satisfaction: 95%
Efficiency: 85%
Cost savings: 70%

# Start creating your video today!"""
        
        script_input = st.text_area(
            "✍️ Write or paste your script here",
            value=st.session_state.get('script_input', default_script),
            height=400,
            help="Use # for titles, - for bullet points, and key=value for charts"
        )
        
        # Store the script input in session state
        st.session_state.script_input = script_input
        
        with st.expander("📖 Script Writing Tips"):
            st.markdown(TIPS_HTML)
        
        st.divider()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Analyze Script", use_container_width=True):
                if script_input.strip():
                    parser = ScriptParser()
                    scenes = parser.auto_generate_scenes(script_input)
                    st.session_state.scenes = scenes
                    st.session_state.auto_generated = True
                    st.success(f"✅ Analyzed! Found {len(scenes)} scenes")
                    st.rerun()
                else:
                    st.warning("Please enter a script first")
        
        with col2:
            if st.button("🗑️ Clear Script", use_container_width=True):
                st.session_state.script_input = ""
                st.session_state.scenes = []
                st.session_state.auto_generated = False
                st.rerun()
    
    # TAB 2: Scene Preview
    with tab2:
        st.subheader("Auto-Generated Scenes")
        
        if not st.session_state.scenes:
            st.info("Enter a script and click 'Analyze Script' to generate scenes")
        else:
            st.success(f"📊 {len(st.session_state.scenes)} scenes generated")
            
            for idx, scene in enumerate(st.session_state.scenes):
                with st.expander(f"Scene {idx + 1}: {scene.get('type', 'unknown').title()}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if scene['type'] == 'text':
                            st.markdown(f"📝 **Content:** {scene.get('content', '')}")
                        elif scene['type'] == 'bullets':
                            st.markdown(f"📌 **Title:** {scene.get('title', '')}")
                            for bullet in scene.get('bullets', []):
                                st.markdown(f"  • {bullet}")
                        elif scene['type'] == 'chart':
                            st.markdown(f"📊 **Chart:** {scene.get('title', '')}")
                            st.json(scene.get('data', {}))
                    
                    with col2:
                        voiceover = scene.get('voiceover', '')
                        st.caption(f"🎤 Voiceover: {voiceover[:100]}{'...' if len(voiceover) > 100 else ''}")
                        duration = len(voiceover) * 0.3
                        st.caption(f"⏱️ Estimated: {int(duration)} seconds")
    
    # TAB 3: Generate Video
    with tab3:
        st.subheader("Generate Your Video")
        
        if not st.session_state.scenes:
            st.warning("Please analyze your script first (Tab 1) to generate scenes.")
        else:
            total_duration = sum(len(scene.get('voiceover', '')) * 0.3 for scene in st.session_state.scenes)
            st.info(f"📊 Video will have {len(st.session_state.scenes)} scenes and be approximately {int(total_duration)} seconds long")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                video_name = st.text_input(
                    "Video Name",
                    value=f"auto_explainer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
            
            with col2:
                st.write("")
                if st.button("🚀 Generate Video", type="primary", use_container_width=True):
                    try:
                        res_parts = resolution.split('x')
                        width = int(res_parts[0].strip())
                        height = int(res_parts[1].split('(')[0].strip())
                        
                        video_maker = AutoVideoMaker(resolution=(width, height), fps=24)
                        
                        script_text = st.session_state.get('script_input', '')
                        if not script_text:
                            st.error("No script found. Please enter a script first.")
                            return
                        
                        output_filename = f"{video_name}.mp4"
                        output_path = os.path.join(tempfile.gettempdir(), output_filename)
                        
                        video_maker.generate_video(script_text, output_path, lang)
                        
                        st.session_state.video_path = output_path
                        st.session_state.video_generated = True
                        
                        st.success("🎉 Video generated successfully with auto-created scenes!")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating video: {str(e)}")
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
                            label="📥 Download Video (MP4)",
                            data=video_bytes,
                            file_name=f"{video_name}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    
                    st.video(st.session_state.video_path)
                    
                except Exception as e:
                    st.error(f"Error loading video: {str(e)}")

# ============ RUN APP ============
if __name__ == "__main__":
    main()