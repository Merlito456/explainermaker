""")

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
            # Create and show preview
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
st.subheader("Generate Video")

if not st.session_state.scenes:
st.warning("Please analyze your script first (Tab 1) to generate scenes.")
else:
# Parse resolution
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
        "Video Name",
        value="explainer_" + datetime.now().strftime('%Y%m%d_%H%M%S')
    )

with col2:
    st.write("")
    if st.button("Generate Images", type="primary", use_container_width=True):
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
            status_text.text("Images generated successfully!")
            
            # Save images to a zip file
            import zipfile
            zip_path = os.path.join(tempfile.gettempdir(), video_name + "_slides.zip")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, img in enumerate(images):
                    img_path = os.path.join(tempfile.gettempdir(), "slide_" + str(i) + ".png")
                    img.save(img_path)
                    zipf.write(img_path, "slide_" + str(i) + ".png")
                    os.remove(img_path)
            
            st.session_state.video_path = zip_path
            st.session_state.video_generated = True
            
            st.success("Images generated successfully! Download the slides below.")
            
        except Exception as e:
            st.error("Error generating images: " + str(e))
            st.exception(e)

if st.session_state.video_generated and st.session_state.video_path:
    st.divider()
    st.markdown(SUCCESS_HTML, unsafe_allow_html=True)
    
    try:
        with open(st.session_state.video_path, 'rb') as f:
            zip_bytes = f.read()
        
        st.download_button(
            label="📥 Download Slides (ZIP)",
            data=zip_bytes,
            file_name=video_name + "_slides.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        st.info("💡 You can use these images to create a video using any video editing software.")
        
    except Exception as e:
        st.error("Error loading file: " + str(e))

if __name__ == "__main__":
main()