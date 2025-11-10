import streamlit as st
import streamlit.components.v1 as components

text_to_copy = "This text will be copied to your clipboard!"

st.code(text_to_copy, language=None)

# This creates a small custom HTML component (iframe) that handles its own JS
components.html(f"""
    <html>
    <body>
        <button id="copy-btn" 
            style="padding:8px 16px; border:none; border-radius:6px; background-color:#4CAF50; color:white; cursor:pointer;">
            📋 Copy
        </button>
        <span id="msg" style="margin-left:10px; color:green;"></span>

        <script>
        const btn = document.getElementById("copy-btn");
        btn.addEventListener("click", async () => {{
            try {{
                await navigator.clipboard.writeText(`{text_to_copy}`);
                document.getElementById("msg").innerText = "Copied!";
                setTimeout(() => document.getElementById("msg").innerText = "", 2000);
            }} catch (err) {{
                document.getElementById("msg").innerText = "Copy failed";
            }}
        }});
        </script>
    </body>
    </html>
""", height=80)
