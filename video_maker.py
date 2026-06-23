import os
import json
import tempfile
from gtts import gTTS
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExplainerVideoMaker:
    def __init__(self, output_resolution=(1920, 1080), fps=24):
        self.resolution = output_resolution
        self.fps = fps
        self.temp_dir = tempfile.mkdtemp()
        self.audio_clips = []
        self.video_clips = []
        logger.info(f"Initialized video maker with resolution {self.resolution}")
        
    def load_script(self, script_path):
        """Load JSON script with scenes."""
        with open(script_path, 'r') as f:
            return json.load(f)
    
    def text_to_speech(self, text, output_path, lang='en', tts_engine='gtts'):
        """Generate speech from text using gTTS or OpenAI."""
        try:
            if tts_engine == 'gtts':
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(output_path)
                logger.info(f"Generated TTS audio: {output_path}")
            elif tts_engine == 'openai':
                try:
                    from openai import OpenAI
                    client = OpenAI()
                    response = client.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=text
                    )
                    response.stream_to_file(output_path)
                    logger.info(f"Generated OpenAI TTS audio: {output_path}")
                except ImportError:
                    logger.error("OpenAI library not installed. Falling back to gTTS.")
                    tts = gTTS(text=text, lang=lang, slow=False)
                    tts.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Error in TTS generation: {e}")
            raise
    
    def create_text_slide(self, text, duration, bg_color='black', text_color='white', font_size=70):
        """Create a static text slide with MoviePy."""
        # Convert hex color to RGB if needed
        if bg_color.startswith('#'):
            bg_color = self.hex_to_rgb(bg_color)
        if text_color.startswith('#'):
            text_color = self.hex_to_rgb(text_color)
        
        img = Image.new('RGB', self.resolution, color=bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Word wrap
        lines = []
        words = text.split()
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] > self.resolution[0] - 100:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text centered
        y_offset = (self.resolution[1] - len(lines) * font_size) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = (self.resolution[0] - bbox[2]) // 2
            draw.text((x, y_offset), line, fill=text_color, font=font)
            y_offset += font_size + 10
        
        img_array = np.array(img)
        clip = ImageClip(img_array).set_duration(duration)
        return clip
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def create_bullet_slide(self, title, bullets, duration, bg_color='darkblue'):
        """Create a slide with title and bullet points."""
        if bg_color.startswith('#'):
            bg_color = self.hex_to_rgb(bg_color)
        
        img = Image.new('RGB', self.resolution, color=bg_color)
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 80)
            bullet_font = ImageFont.truetype("arial.ttf", 50)
        except:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 80)
                bullet_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
            except:
                title_font = ImageFont.load_default()
                bullet_font = ImageFont.load_default()
        
        # Draw title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (self.resolution[0] - bbox[2]) // 2
        draw.text((x, 100), title, fill='white', font=title_font)
        
        # Draw bullets
        y = 250
        for i, point in enumerate(bullets[:6]):  # Max 6 bullets
            bullet_text = f"• {point}"
            bbox = draw.textbbox((0, 0), bullet_text, font=bullet_font)
            x = 150
            draw.text((x, y), bullet_text, fill='lightyellow', font=bullet_font)
            y += 80
        
        img_array = np.array(img)
        clip = ImageClip(img_array).set_duration(duration)
        return clip
    
    def create_bar_chart(self, data, duration, title="Chart"):
        """Create a simple bar chart slide."""
        img = Image.new('RGB', self.resolution, color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 40)
            title_font = ImageFont.truetype("arial.ttf", 60)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
            except:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
        
        # Draw title
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (self.resolution[0] - bbox[2]) // 2
        draw.text((x, 50), title, fill='black', font=title_font)
        
        # Draw bars
        if not data:
            data = {'No Data': 0}
        
        max_val = max(data.values()) if data else 1
        if max_val == 0:
            max_val = 1
        
        bar_width = (self.resolution[0] - 300) // len(data)
        bar_width = min(bar_width, 150)  # Max width
        x_start = (self.resolution[0] - (bar_width * len(data) + 50 * (len(data) - 1))) // 2
        y_base = self.resolution[1] - 200
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F']
        
        for i, (label, value) in enumerate(data.items()):
            bar_height = (value / max_val) * (self.resolution[1] - 350)
            if bar_height < 10:
                bar_height = 10
            x = x_start + i * (bar_width + 50)
            color = colors[i % len(colors)]
            
            # Draw bar
            draw.rectangle(
                [x, y_base - bar_height, x + bar_width, y_base],
                fill=color
            )
            
            # Draw value on top
            draw.text(
                (x + bar_width//2 - 20, y_base - bar_height - 40),
                str(int(value)),
                fill='black',
                font=font
            )
            
            # Draw label
            bbox = draw.textbbox((0, 0), label, font=font)
            draw.text(
                (x + (bar_width - bbox[2])//2, y_base + 20),
                label,
                fill='black',
                font=font
            )
        
        img_array = np.array(img)
        clip = ImageClip(img_array).set_duration(duration)
        return clip
    
    def process_scene(self, scene):
        """Process a single scene from JSON."""
        scene_type = scene.get('type', 'text')
        duration = scene.get('duration', 3)
        audio = None
        
        # Generate TTS if text is provided
        if 'text' in scene and scene['text']:
            try:
                audio_path = os.path.join(self.temp_dir, f"audio_{len(self.audio_clips)}.mp3")
                self.text_to_speech(scene['text'], audio_path)
                audio = AudioFileClip(audio_path)
                duration = audio.duration
                self.audio_clips.append(audio)
                logger.info(f"Generated audio for scene: {scene_type}")
            except Exception as e:
                logger.error(f"Error generating audio: {e}")
        
        # Generate visual based on type
        try:
            if scene_type == 'text':
                clip = self.create_text_slide(
                    scene.get('content', 'Hello World'),
                    duration,
                    bg_color=scene.get('bg_color', 'black'),
                    text_color=scene.get('text_color', 'white')
                )
            elif scene_type == 'bullets':
                clip = self.create_bullet_slide(
                    scene.get('title', 'Key Points'),
                    scene.get('bullets', ['Point 1', 'Point 2']),
                    duration,
                    bg_color=scene.get('bg_color', 'darkblue')
                )
            elif scene_type == 'chart':
                clip = self.create_bar_chart(
                    scene.get('data', {'A': 10, 'B': 20, 'C': 15}),
                    duration,
                    scene.get('chart_title', 'Data')
                )
            else:
                raise ValueError(f"Unknown scene type: {scene_type}")
            
            # Add fade effects
            if duration > 1:
                clip = fadein(clip, min(0.5, duration/2), 'linear')
                clip = fadeout(clip, min(0.5, duration/2), 'linear')
            
            # Attach audio if exists
            if audio:
                clip = clip.set_audio(audio)
            
            self.video_clips.append(clip)
            logger.info(f"Processed scene: {scene_type}")
            return clip
            
        except Exception as e:
            logger.error(f"Error processing scene: {e}")
            raise
    
    def render(self, script_path, output_path="explainer_video.mp4"):
        """Main render function."""
        try:
            script = self.load_script(script_path)
            logger.info(f"Loaded script with {len(script['scenes'])} scenes")
            
            for idx, scene in enumerate(script['scenes']):
                logger.info(f"Processing scene {idx + 1}/{len(script['scenes'])}")
                self.process_scene(scene)
            
            if not self.video_clips:
                raise ValueError("No video clips generated!")
            
            # Concatenate all clips
            logger.info("Concatenating video clips...")
            final_video = concatenate_videoclips(self.video_clips, method="compose")
            
            # Write output
            logger.info(f"Rendering final video to {output_path}")
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                threads=4,
                verbose=False,
                logger=None
            )
            
            logger.info(f"✅ Video saved to {output_path}")
            
            # Cleanup
            for clip in self.video_clips:
                clip.close()
            if final_video:
                final_video.close()
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error rendering video: {e}")
            raise