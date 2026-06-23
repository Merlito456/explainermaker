""")

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
    st.markdown("""
    <div class="success-box">
    <h3>✅ Your Video is Ready!</h3>
    </div>
    """, unsafe_allow_html=True)
    
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