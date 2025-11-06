                # Export options
                st.markdown("### 📥 Export Options")
                st.info("💡 Click the buttons below to generate and download your content.")
                
                # Create timestamp for consistent file naming
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # Create three columns for download options  
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📄 Word Document")
                    st.caption("Professional formatted document")
                    
                    if st.button("Generate DOCX", key="btn_docx", type="primary"):
                        with st.spinner("Generating Word document..."):
                            try:
                                docx_file = exporter.generate_docx(enhanced_content, seo_data, images)
                                docx_filename = f"article_{timestamp}.docx"
                                
                                st.success(f"Generated {len(docx_file):,} bytes")
                                
                                st.download_button(
                                    label="Download DOCX File",
                                    data=docx_file,
                                    file_name=docx_filename,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    key=f"dl_docx_{timestamp}"
                                )
                                
                            except Exception as e:
                                st.error(f"Generation failed: {str(e)}")
                
                with col2:
                    st.markdown("#### 🌐 HTML File")
                    st.caption("Web-ready with SEO optimization")
                    
                    if st.button("Generate HTML", key="btn_html", type="primary"):
                        with st.spinner("Generating HTML file..."):
                            try:
                                html_content = exporter.generate_html(enhanced_content, seo_data, images)
                                html_filename = f"article_{timestamp}.html"
                                
                                st.success(f"Generated {len(html_content):,} characters")
                                
                                st.download_button(
                                    label="Download HTML File",
                                    data=html_content,
                                    file_name=html_filename,
                                    mime="text/html",
                                    key=f"dl_html_{timestamp}"
                                )
                                
                            except Exception as e:
                                st.error(f"Generation failed: {str(e)}")
                
                with col3:
                    st.markdown("#### 📊 Analytics Data")
                    st.caption("SEO and content metrics")
                    
                    if st.button("Generate Analytics", key="btn_analytics", type="primary"):
                        with st.spinner("Generating analytics..."):
                            try:
                                analytics_data = exporter.generate_analytics(enhanced_content, seo_data)
                                analytics_filename = f"analytics_{timestamp}.json"
                                
                                st.success(f"Generated {len(analytics_data):,} characters")
                                
                                st.download_button(
                                    label="Download Analytics JSON",
                                    data=analytics_data,
                                    file_name=analytics_filename,
                                    mime="application/json",
                                    key=f"dl_analytics_{timestamp}"
                                )
                                
                            except Exception as e:
                                st.error(f"Generation failed: {str(e)}")
                
                # Quick downloads section
                st.markdown("---")
                st.markdown("#### ⚡ Quick Downloads")
                st.caption("Instant downloads without processing delay")
                
                try:
                    qd_col1, qd_col2, qd_col3 = st.columns(3)
                    
                    with qd_col1:
                        # Quick HTML
                        quick_html = exporter.generate_html(enhanced_content, seo_data, {})
                        st.download_button(
                            label="Quick HTML Download",
                            data=quick_html,
                            file_name=f"quick_article_{timestamp}.html",
                            mime="text/html",
                            key="quick_html_download"
                        )
                    
                    with qd_col2:
                        # Quick analytics
                        quick_analytics = exporter.generate_analytics(enhanced_content, seo_data)
                        st.download_button(
                            label="Quick Analytics Download", 
                            data=quick_analytics,
                            file_name=f"quick_analytics_{timestamp}.json",
                            mime="application/json",
                            key="quick_analytics_download"
                        )
                    
                    with qd_col3:
                        # Plain text version
                        text_content = f"# {enhanced_content.get('title', '')}\n\n"
                        text_content += f"{enhanced_content.get('meta_description', '')}\n\n"
                        for section in enhanced_content.get('sections', []):
                            text_content += f"## {section.get('heading', '')}\n\n{section.get('content', '')}\n\n"
                        
                        st.download_button(
                            label="Plain Text Download",
                            data=text_content,
                            file_name=f"article_{timestamp}.txt",
                            mime="text/plain",
                            key="quick_text_download"
                        )
                        
                except Exception as e:
                    st.warning(f"Quick downloads unavailable: {str(e)}")
                
                # File information
                st.markdown("---")
                st.caption(f"Article: {enhanced_content.get('title', 'N/A')} | Words: {seo_data.get('word_count', 0):,} | SEO Score: {seo_data.get('seo_score', 0)}/100")