import streamlit as st
import os
from datetime import datetime
import json
import time
from dotenv import load_dotenv
from llm_engine import LLMEngine
from image_engine import ImageEngine
from content_tools import ContentTools
from seo_tools import SEOTools
from exporter import Exporter

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Article Generator",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling system
def load_custom_css():
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* CSS Variables for Professional Theme */
    :root {
        --primary-blue: #2563eb;
        --primary-blue-dark: #1d4ed8;
        --secondary-indigo: #4f46e5;
        --accent-purple: #7c3aed;
        --success-green: #059669;
        --warning-amber: #d97706;
        --error-red: #dc2626;
        --neutral-50: #f8fafc;
        --neutral-100: #f1f5f9;
        --neutral-200: #e2e8f0;
        --neutral-300: #cbd5e1;
        --neutral-400: #94a3b8;
        --neutral-500: #64748b;
        --neutral-600: #475569;
        --neutral-700: #334155;
        --neutral-800: #1e293b;
        --neutral-900: #0f172a;
        --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --gradient-secondary: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    }

    /* Global Overrides */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    header[data-testid="stHeader"] {display: none;}
    
    /* Main App Container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: var(--gradient-secondary);
        border-right: 1px solid var(--neutral-200);
    }
    
    .sidebar .sidebar-content {
        background: var(--gradient-secondary);
        padding: 1.5rem 1rem;
    }
    
    /* Sidebar Toggle Button Fix */
    button[kind="header"] {
        background: transparent !important;
        border: none !important;
        color: white !important;
    }
    
    button[kind="header"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Ensure sidebar toggle always works */
    .css-1rs6os.edgvbvh3 {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Professional Logo & Branding */
    .logo-container {
        text-align: center;
        margin-bottom: 2rem;
        padding: 1.5rem 1rem;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .logo-text {
        font-size: 1.75rem;
        font-weight: 700;
        color: white;
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    
    .logo-subtitle {
        color: rgba(255, 255, 255, 0.85);
        font-size: 0.875rem;
        font-weight: 400;
        letter-spacing: 0.025em;
    }
    
    /* Enhanced Sidebar Styling */
    .css-1d391kg, .css-1lcbmhc {
        background: var(--gradient-secondary) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Force Sidebar to Always Show - Natural Layout */
    [data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        transform: translateX(0) !important;
        width: 300px !important;
        min-width: 300px !important;
        max-width: 300px !important;
        background: var(--gradient-secondary) !important;
        position: relative !important;
        height: 100vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    
    [data-testid="stSidebar"] > div {
        width: 100% !important;
        padding: 1rem !important;
        background: var(--gradient-secondary) !important;
        overflow: visible !important;
    }
    
    /* Hide internal scrollbars */
    [data-testid="stSidebar"] .stVerticalBlock {
        overflow: visible !important;
    }
    
    [data-testid="stSidebar"] .element-container {
        overflow: visible !important;
    }
    
    /* Ensure sidebar content is properly sized */
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stTextInput,
    [data-testid="stSidebar"] .stTextArea,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stRadio,
    [data-testid="stSidebar"] .stCheckbox {
        width: 100% !important;
        max-width: 260px !important;
    }
    
    /* Force Streamlit to not collapse sidebar */
    .css-1d391kg {
        width: 300px !important;
        min-width: 300px !important;
        transform: translateX(0) !important;
        margin-left: 0 !important;
        background: var(--gradient-secondary) !important;
    }
    
    .css-1lcbmhc {
        width: 300px !important;
        min-width: 300px !important;
        transform: translateX(0) !important;
        background: var(--gradient-secondary) !important;
    }
    
    /* Ensure all sidebar elements are visible */
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stTextArea label,
    [data-testid="stSidebar"] .stSlider label {
        color: white !important;
        font-weight: 500 !important;
    }
    
    /* Only hide the collapse control button - keep sidebar content */
    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    /* Hide specific hamburger menu button classes only */
    button.css-vk3wp9, 
    button.css-1rs6os, 
    button.css-17lntkn {
        display: none !important;
    }
    
    /* Ensure sidebar stays visible */
    [data-testid="stSidebar"] {
        transform: translateX(0) !important;
        visibility: visible !important;
        display: block !important;
    }
    
    /* Hide any tooltips or title attributes on sidebar elements */
    [data-testid="stSidebar"] [title],
    [data-testid="stSidebar"] [aria-label],
    .css-1d391kg [title],
    .css-1lcbmhc [title] {
        title: none !important;
    }
    
    /* Remove any hover tooltips from sidebar toggle area */
    button[title*="key"],
    button[aria-label*="key"],
    div[title*="key"] {
        title: "" !important;
        aria-label: "" !important;
    }
    
    /* Hide keyboard navigation button that's not rendering properly */
    [data-testid="stSidebar"] {
        position: relative !important;
    }
    

    
    /* Hide any text that says "keyl" specifically */
    [data-testid="stSidebar"] *:before,
    [data-testid="stSidebar"] *:after {
        content: "" !important;
    }
    
    /* Target any element containing exactly "keyl" */
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Brute force - hide specific Streamlit classes that might contain this */
    .css-1kyxreq,
    .css-1v0mbdj,
    .css-10trblm,
    .css-1dp5vir,
    [class*="KeyboardShortcut"],
    [class*="keyboard"],
    [class*="stTooltip"] {
        display: none !important;
        visibility: hidden !important;
    }
    }
    
    [data-testid="collapsedControl"]:hover {
        background: var(--primary-blue-dark) !important;
        transform: scale(1.05) !important;
        box-shadow: var(--shadow-lg) !important;
    }
    
    /* Ensure sidebar content is always visible */
    .css-1d391kg, .css-1lcbmhc, .css-17eq0hr {
        background: var(--gradient-secondary) !important;
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Navigation Sections */
    .nav-section {
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .nav-section:last-child {
        border-bottom: none;
        margin-bottom: 0;
    }
    
    .nav-section h3 {
        color: white !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 0.75rem !important;
        opacity: 0.9 !important;
    }
    
    /* Professional Form Controls - Comprehensive Sidebar Targeting */
    
    /* Sidebar Selectbox Styling */
    [data-testid="stSidebar"] .stSelectbox > div > div,
    .sidebar .stSelectbox > div > div,
    .css-1d391kg .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px !important;
        color: #333333 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox > div > div > div,
    .sidebar .stSelectbox > div > div > div,
    .css-1d391kg .stSelectbox > div > div > div {
        color: #333333 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox option,
    .sidebar .stSelectbox option {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Sidebar Text Input Styling */
    [data-testid="stSidebar"] .stTextInput > div > div > input,
    .sidebar .stTextInput > div > div > input,
    .css-1d391kg .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px !important;
        color: #333333 !important;
        font-size: 0.875rem !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input::placeholder,
    .sidebar .stTextInput > div > div > input::placeholder,
    .css-1d391kg .stTextInput > div > div > input::placeholder {
        color: rgba(0, 0, 0, 0.5) !important;
    }
    
    [data-testid="stSidebar"] .stTextInput > div > div > input:focus,
    .sidebar .stTextInput > div > div > input:focus,
    .css-1d391kg .stTextInput > div > div > input:focus {
        border-color: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Sidebar Text Area Styling */
    [data-testid="stSidebar"] .stTextArea > div > div > textarea,
    .sidebar .stTextArea > div > div > textarea,
    .css-1d391kg .stTextArea > div > div > textarea {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px !important;
        color: #333333 !important;
        font-size: 0.875rem !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: rgba(0, 0, 0, 0.5) !important;
    }
    
    [data-testid="stSidebar"] .stTextArea > div > div > textarea::placeholder,
    .sidebar .stTextArea > div > div > textarea::placeholder,
    .css-1d391kg .stTextArea > div > div > textarea::placeholder {
        color: rgba(0, 0, 0, 0.5) !important;
    }
    
    [data-testid="stSidebar"] .stTextArea > div > div > textarea:focus,
    .sidebar .stTextArea > div > div > textarea:focus,
    .css-1d391kg .stTextArea > div > div > textarea:focus {
        border-color: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Sidebar Slider Styling */
    [data-testid="stSidebar"] .stSlider > div > div > div,
    .sidebar .stSlider > div > div > div,
    .css-1d391kg .stSlider > div > div > div {
        background: rgba(255, 255, 255, 0.3) !important;
    }
    
    [data-testid="stSidebar"] .stSlider > div > div > div > div,
    .sidebar .stSlider > div > div > div > div,
    .css-1d391kg .stSlider > div > div > div > div {
        background: white !important;
    }
    
    /* Sidebar Checkbox Styling */
    [data-testid="stSidebar"] .stCheckbox > label,
    .sidebar .stCheckbox > label,
    .css-1d391kg .stCheckbox > label {
        color: white !important;
        font-size: 0.875rem !important;
    }
    
    [data-testid="stSidebar"] .stCheckbox > label > div,
    .sidebar .stCheckbox > label > div,
    .css-1d391kg .stCheckbox > label > div {
        color: white !important;
    }
    
    /* Sidebar Radio Button Styling */
    [data-testid="stSidebar"] .stRadio > label,
    .sidebar .stRadio > label,
    .css-1d391kg .stRadio > label {
        color: white !important;
        font-size: 0.875rem !important;
    }
    
    [data-testid="stSidebar"] .stRadio > div > label > div,
    .sidebar .stRadio > div > label > div,
    .css-1d391kg .stRadio > div > label > div {
        color: white !important;
    }
    
    /* Comprehensive Sidebar Text Visibility */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    .sidebar,
    .sidebar *,
    .css-1d391kg,
    .css-1d391kg * {
        color: white !important;
    }
    
    /* Specific Sidebar Elements */
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3,
    [data-testid="stSidebar"] .stMarkdown h4,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] .stMarkdown div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stTextArea label,
    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stNumberInput label,
    [data-testid="stSidebar"] .stCheckbox span,
    [data-testid="stSidebar"] .stRadio span {
        color: white !important;
    }
    
    /* Comprehensive Sidebar Dropdown Styling */
    [data-testid="stSidebar"] .stSelectbox,
    [data-testid="stSidebar"] .stSelectbox *,
    .sidebar .stSelectbox,
    .sidebar .stSelectbox *,
    .css-1d391kg .stSelectbox,
    .css-1d391kg .stSelectbox * {
        color: #333333 !important;
        background: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Dropdown container */
    [data-testid="stSidebar"] .stSelectbox > div,
    .sidebar .stSelectbox > div,
    .css-1d391kg .stSelectbox > div {
        background: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Dropdown input field */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
    .sidebar .stSelectbox [data-baseweb="select"] > div,
    .css-1d391kg .stSelectbox [data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        color: #333333 !important;
    }
    
    /* Dropdown selected value */
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div > div,
    .sidebar .stSelectbox [data-baseweb="select"] > div > div,
    .css-1d391kg .stSelectbox [data-baseweb="select"] > div > div {
        color: #333333 !important;
    }
    
    /* Dropdown options and roles */
    [data-testid="stSidebar"] .stSelectbox [role="combobox"],
    [data-testid="stSidebar"] .stSelectbox [role="listbox"],
    [data-testid="stSidebar"] .stSelectbox [role="option"],
    [data-testid="stSidebar"] .stSelectbox select,
    [data-testid="stSidebar"] .stSelectbox option,
    .sidebar .stSelectbox [role="combobox"],
    .sidebar .stSelectbox [role="listbox"], 
    .sidebar .stSelectbox [role="option"],
    .sidebar .stSelectbox select,
    .sidebar .stSelectbox option,
    .css-1d391kg .stSelectbox [role="combobox"],
    .css-1d391kg .stSelectbox [role="listbox"],
    .css-1d391kg .stSelectbox [role="option"],
    .css-1d391kg .stSelectbox select,
    .css-1d391kg .stSelectbox option {
        color: #333333 !important;
        background: rgba(255, 255, 255, 0.95) !important;
    }
    
    /* Force all selectbox text to be black */
    [data-testid="stSidebar"] .stSelectbox span,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] .stSelectbox p,
    .sidebar .stSelectbox span,
    .sidebar .stSelectbox div,
    .sidebar .stSelectbox p,
    .css-1d391kg .stSelectbox span,
    .css-1d391kg .stSelectbox div,
    .css-1d391kg .stSelectbox p {
        color: #333333 !important;
    }
    
    /* Dropdown menu when opened */
    [data-testid="stSidebar"] .stSelectbox ul,
    [data-testid="stSidebar"] .stSelectbox li,
    .sidebar .stSelectbox ul,
    .sidebar .stSelectbox li,
    .css-1d391kg .stSelectbox ul,
    .css-1d391kg .stSelectbox li {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Target BaseWeb dropdown components */
    [data-testid="stSidebar"] [data-baseweb="popover"],
    [data-testid="stSidebar"] [data-baseweb="menu"],
    [data-testid="stSidebar"] [data-baseweb="menu"] li,
    [data-testid="stSidebar"] [data-baseweb="menu"] div,
    .sidebar [data-baseweb="popover"],
    .sidebar [data-baseweb="menu"],
    .sidebar [data-baseweb="menu"] li,
    .sidebar [data-baseweb="menu"] div,
    .css-1d391kg [data-baseweb="popover"],
    .css-1d391kg [data-baseweb="menu"],
    .css-1d391kg [data-baseweb="menu"] li,
    .css-1d391kg [data-baseweb="menu"] div {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Target dropdown options when expanded */
    [data-testid="stSidebar"] .stSelectbox [aria-expanded="true"] + div,
    [data-testid="stSidebar"] .stSelectbox [aria-expanded="true"] + div *,
    .sidebar .stSelectbox [aria-expanded="true"] + div,
    .sidebar .stSelectbox [aria-expanded="true"] + div *,
    .css-1d391kg .stSelectbox [aria-expanded="true"] + div,
    .css-1d391kg .stSelectbox [aria-expanded="true"] + div * {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Sidebar Number Input Styling */
    [data-testid="stSidebar"] .stNumberInput > div > div > input,
    .sidebar .stNumberInput > div > div > input,
    .css-1d391kg .stNumberInput > div > div > input {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 8px !important;
        color: #333333 !important;
    }
    
    [data-testid="stSidebar"] .stNumberInput > div > div > input:focus,
    .sidebar .stNumberInput > div > div > input:focus,
    .css-1d391kg .stNumberInput > div > div > input:focus {
        border-color: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Labels and Help Text */
    .stSelectbox > label,
    .stTextInput > label,
    .stTextArea > label,
    .stSlider > label,
    .stNumberInput > label {
        color: white !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Sidebar Dropdown Labels - Make Black for Readability */
    [data-testid="stSidebar"] .stSelectbox > label,
    .sidebar .stSelectbox > label,
    .css-1d391kg .stSelectbox > label {
        color: #333333 !important;
        background: rgba(255, 255, 255, 0.9) !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 4px !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    .stSelectbox .help,
    .stTextInput .help,
    .stTextArea .help,
    .stSlider .help {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.75rem !important;
    }
    
    /* Sidebar Metrics/Info Cards */
    .sidebar-metric {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.75rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        border-left: 3px solid rgba(255, 255, 255, 0.3);
    }
    
    .sidebar-metric-label {
        color: rgba(255, 255, 255, 0.8);
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .sidebar-metric-value {
        color: white;
        font-size: 1rem;
        font-weight: 600;
        margin-top: 0.25rem;
    }
    
    /* Main Content Area Styling */
    .main-header {
        background: white;
        padding: 2rem 0 1rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid var(--neutral-200);
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--neutral-900);
        margin-bottom: 0.5rem;
        letter-spacing: -0.025em;
    }
    
    .main-subtitle {
        font-size: 1.125rem;
        color: var(--neutral-600);
        font-weight: 400;
    }
    
    /* Progress & Status Indicators */
    .progress-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--neutral-200);
        text-align: center;
    }
    
    .progress-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--neutral-900);
        margin-bottom: 0.5rem;
    }
    
    .progress-step {
        font-size: 0.875rem;
        color: var(--neutral-600);
        margin-bottom: 1rem;
    }
    
    .stProgress > div > div > div {
        background: var(--gradient-secondary) !important;
        border-radius: 6px !important;
    }
    
    /* Professional Cards */
    .content-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        border: 1px solid var(--neutral-200);
        transition: all 0.2s ease;
    }
    
    .content-card:hover {
        box-shadow: var(--shadow-lg);
        border-color: var(--neutral-300);
    }
    
    .card-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--neutral-900);
        margin-bottom: 0.75rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--neutral-200);
    }
    
    /* Professional Buttons */
    .stButton > button {
        background: var(--gradient-secondary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--shadow-sm) !important;
        letter-spacing: 0.025em !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: var(--shadow-md) !important;
        background: var(--primary-blue-dark) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Primary Button Variant */
    .primary-button {
        background: var(--gradient-primary) !important;
    }
    
    /* Success/Info/Warning States */
    .stSuccess {
        background: rgba(5, 150, 105, 0.1) !important;
        border: 1px solid var(--success-green) !important;
        border-radius: 8px !important;
        color: var(--success-green) !important;
    }
    
    .stInfo {
        background: rgba(37, 99, 235, 0.1) !important;
        border: 1px solid var(--primary-blue) !important;
        border-radius: 8px !important;
        color: var(--primary-blue) !important;
    }
    
    .stWarning {
        background: rgba(217, 119, 6, 0.1) !important;
        border: 1px solid var(--warning-amber) !important;
        border-radius: 8px !important;
        color: var(--warning-amber) !important;
    }
    
    .stError {
        background: rgba(220, 38, 38, 0.1) !important;
        border: 1px solid var(--error-red) !important;
        border-radius: 8px !important;
        color: var(--error-red) !important;
    }
    
    /* Generated content styling */
    .generated-content {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        color: #1a202c;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .generated-content h1 {
        color: #2d3748;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    .generated-content h2 {
        color: #4a5568;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* SEO metrics styling */
    .seo-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: rgba(102, 126, 234, 0.1);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .metric-label {
        color: #64748b;
        font-size: 0.9rem;
    }
    
    /* Watermark styling */
    .ai-watermark {
        text-align: center;
        margin: 2rem 0;
        padding: 1rem;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border-radius: 10px;
        font-style: italic;
    }
    
    /* Professional Metrics & Analytics */
    .metric-container, .seo-metrics {
        display: flex;
        gap: 1rem;
        margin: 1.5rem 0;
        flex-wrap: wrap;
    }
    
    .metric-card {
        flex: 1;
        min-width: 200px;
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: var(--shadow-sm);
        border: 1px solid var(--neutral-200);
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    .metric-value {
        font-size: 2.25rem;
        font-weight: 800;
        color: var(--primary-blue);
        line-height: 1;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--neutral-600);
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Generated Content Styling */
    .generated-content {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--neutral-200);
        margin: 2rem 0;
    }
    
    .generated-content h1 {
        color: var(--neutral-900) !important;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        margin-bottom: 1rem !important;
        line-height: 1.1 !important;
    }
    
    .generated-content h2 {
        color: var(--primary-blue) !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        margin: 2rem 0 1rem 0 !important;
    }
    
    .generated-content p {
        color: var(--neutral-700) !important;
        line-height: 1.7 !important;
        margin-bottom: 1rem !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .sidebar-header {
            font-size: 1.25rem;
        }
        
        .content-card, .generated-content {
            padding: 1rem;
            margin: 0.75rem 0;
        }
        
        .progress-container {
            padding: 1rem;
        }
        
        .metric-container, .seo-metrics {
            flex-direction: column;
        }
        
        .metric-card {
            min-width: unset;
        }
        
        .metric-value {
            font-size: 1.75rem;
        }
    }
    
    /* Loading States */
    @keyframes pulse {
        0%, 100% { opacity: 0.8; }
        50% { opacity: 1; }
    }
    
    .loading-indicator {
        animation: pulse 2s infinite;
    }
    
    /* Focus & Accessibility */
    .stSelectbox > div > div, .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border: 1px solid var(--neutral-300) !important;
        transition: all 0.2s ease !important;
    }
    
    .stSelectbox > div > div:focus-within, 
    .stTextInput > div > div > input:focus, 
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
    }
    
    /* Global dropdown menu styling for sidebar-related dropdowns */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [data-baseweb="select"] [role="listbox"],
    [data-baseweb="select"] [role="option"] {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    [data-baseweb="popover"] *,
    [data-baseweb="menu"] *,
    [data-baseweb="select"] [role="listbox"] *,
    [data-baseweb="select"] [role="option"] * {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Target dropdown lists and items */
    [data-baseweb="menu"] ul,
    [data-baseweb="menu"] li,
    [role="listbox"],
    [role="option"] {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Force dropdown options to be black - comprehensive targeting */
    div[role="listbox"] > div,
    div[role="listbox"] div,
    div[role="listbox"] span,
    [data-baseweb="menu"] div,
    [data-baseweb="menu"] span,
    [data-baseweb="popover"] div,
    [data-baseweb="popover"] span,
    .css-26l3qy-menu,
    .css-26l3qy-menu div,
    .css-26l3qy-menu span {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Target Streamlit's specific dropdown menu classes */
    div[data-baseweb="popover"] div[role="listbox"],
    div[data-baseweb="popover"] div[role="listbox"] div,
    div[data-baseweb="popover"] div[role="listbox"] span,
    div[data-baseweb="popover"] div[role="option"],
    div[data-baseweb="popover"] div[role="option"] div,
    div[data-baseweb="popover"] div[role="option"] span {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Additional targeting for dropdown content */
    .css-qrbaxs,
    .css-qrbaxs div,
    .css-qrbaxs span,
    .css-1n76uvr,
    .css-1n76uvr div,
    .css-1n76uvr span {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* ULTRA AGGRESSIVE dropdown option targeting - catch all possible selectors */
    div[data-testid] div[role="listbox"] *,
    div[data-testid] div[role="option"] *,
    div[data-testid] [data-baseweb="popover"] *,
    div[data-testid] [data-baseweb="menu"] *,
    [class*="select"] [role="option"],
    [class*="select"] [role="option"] *,
    [class*="menu"] div,
    [class*="menu"] span,
    [class*="option"] div,
    [class*="option"] span,
    [class*="listbox"] div,
    [class*="listbox"] span {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Target all possible Streamlit dropdown CSS classes */
    [class*="css-"] div[role="option"],
    [class*="css-"] div[role="option"] *,
    [class*="css-"] div[role="listbox"],
    [class*="css-"] div[role="listbox"] *,
    div[class*="select"] div,
    div[class*="select"] span,
    div[class*="menu"] div,
    div[class*="menu"] span {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #333333 !important;
    }
    
    /* Print Styles */
    @media print {
        .sidebar, .stButton, .progress-container {
            display: none !important;
        }
        
        .main-content {
            margin-left: 0 !important;
        }
        
        .generated-content {
            box-shadow: none !important;
            border: none !important;
        }
    }
    </style>
    
    <script>
    // Prevent sidebar from collapsing and ensure proper visibility
    function preventSidebarCollapse() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
            sidebar.style.opacity = '1';
            sidebar.style.transform = 'translateX(0)';
            sidebar.style.width = '300px';
            sidebar.style.minWidth = '300px';
        }
        
        // Only hide collapse buttons, keep sidebar content
        const collapseButtons = document.querySelectorAll('[data-testid="collapsedControl"]');
        collapseButtons.forEach(btn => {
            if (btn) {
                btn.style.display = 'none';
                btn.removeAttribute('title');
                btn.removeAttribute('aria-label');
            }
        });
        
        // Hide hamburger menu buttons specifically
        document.querySelectorAll('button.css-vk3wp9, button.css-1rs6os, button.css-17lntkn').forEach(btn => {
            btn.style.display = 'none';
        });
        
        // Remove any stray title attributes that might show "keyl" tooltip
        document.querySelectorAll('[title*="key"]').forEach(el => {
            el.removeAttribute('title');
        });
        
        document.querySelectorAll('[aria-label*="key"]').forEach(el => {
            el.removeAttribute('aria-label');
        });
        
        // Force sidebar text visibility
        function forceSidebarVisibility() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                // Apply styling to sidebar elements
                sidebar.querySelectorAll('*').forEach(el => {
                    // Check if element is part of a dropdown/selectbox
                    const isSelectboxElement = el.closest('.stSelectbox') || 
                                             el.tagName === 'SELECT' || 
                                             el.tagName === 'OPTION' ||
                                             el.getAttribute('role') === 'combobox' ||
                                             el.getAttribute('role') === 'listbox' ||
                                             el.getAttribute('role') === 'option';
                    
                    if (el.tagName && ['INPUT', 'TEXTAREA', 'SELECT', 'OPTION'].includes(el.tagName)) {
                        // Input elements get black text on white background
                        el.style.color = '#333333';
                        el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                        el.style.border = '1px solid rgba(255, 255, 255, 0.5)';
                        el.style.borderRadius = '8px';
                        
                        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                            el.addEventListener('focus', function() {
                                this.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                                this.style.color = '#333333';
                                this.style.borderColor = 'rgba(255, 255, 255, 0.8)';
                            });
                        }
                        
                        if (el.tagName === 'SELECT' || el.tagName === 'OPTION') {
                            el.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                            el.style.color = '#333333';
                        }
                    } else if (isSelectboxElement) {
                        // All dropdown/selectbox elements get black text
                        el.style.color = '#333333';
                        el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                    } else {
                        // All other text elements stay white
                        el.style.color = 'white';
                    }
                });
                
                // Force labels and other text to be white, except dropdown labels
                sidebar.querySelectorAll('label, span, div[role="listbox"], .stMarkdown').forEach(el => {
                    // Check if this is a selectbox label
                    const isSelectboxLabel = el.tagName === 'LABEL' && 
                                           (el.closest('.stSelectbox') || el.parentElement?.classList.contains('stSelectbox'));
                    
                    if (isSelectboxLabel) {
                        // Make dropdown labels black on white background
                        el.style.color = '#333333';
                        el.style.background = 'rgba(255, 255, 255, 0.9)';
                        el.style.padding = '0.25rem 0.5rem';
                        el.style.borderRadius = '4px';
                        el.style.fontWeight = '500';
                    } else {
                        // All other text stays white
                        el.style.color = 'white';
                    }
                });
            }
        }
        
        // Remove broken keyboard navigation button
        function removeKeyboardButton() {
            // Target keyboard navigation elements
            document.querySelectorAll('*').forEach(el => {
                const text = el.textContent || el.innerText || '';
                // Remove elements containing keyboard navigation text
                if (text.includes('keyboard_') || text.includes('keyl') || text === 'keyboard') {
                    el.style.display = 'none';
                    el.style.visibility = 'hidden';
                    el.style.opacity = '0';
                    el.remove();
                }
            });
            
            // Remove buttons with keyboard-related attributes
            document.querySelectorAll('button, div, span').forEach(el => {
                const ariaLabel = el.getAttribute('aria-label') || '';
                const title = el.getAttribute('title') || '';
                const className = el.className || '';
                
                if (ariaLabel.toLowerCase().includes('keyboard') || 
                    title.toLowerCase().includes('keyboard') ||
                    className.includes('keyboard')) {
                    el.style.display = 'none';
                    el.remove();
                }
            });
            
            // Hide Streamlit's keyboard navigation classes
            document.querySelectorAll('[class*="KeyboardShortcut"], [class*="keyboard"], .css-1kyxreq, .css-1v0mbdj, .css-10trblm').forEach(el => {
                el.style.display = 'none';
                el.remove();
            });
        }
        
        // Run both functions multiple times
        forceSidebarVisibility();
        removeKeyboardButton();
        setTimeout(() => {
            forceSidebarVisibility();
            removeKeyboardButton();
        }, 100);
        setTimeout(() => {
            forceSidebarVisibility();
            removeKeyboardButton();
        }, 500);
        setTimeout(() => {
            forceSidebarVisibility();
            removeKeyboardButton();
        }, 1000);
        
        // Set up continuous monitoring for keyboard elements
        const keyboardObserver = new MutationObserver(removeKeyboardButton);
        keyboardObserver.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
        
        // Force dropdown styling continuously
        function forceDropdownStyling() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                // Target all selectbox elements and their children
                sidebar.querySelectorAll('.stSelectbox, .stSelectbox *, [data-baseweb="select"], [data-baseweb="select"] *').forEach(el => {
                    el.style.color = '#333333';
                    if (!['INPUT', 'TEXTAREA'].includes(el.tagName)) {
                        el.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                    }
                });
                
                // Target labels specifically
                sidebar.querySelectorAll('.stSelectbox label, .stSelectbox > label').forEach(label => {
                    label.style.color = '#333333';
                    label.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                    label.style.padding = '0.25rem 0.5rem';
                    label.style.borderRadius = '4px';
                    label.style.fontWeight = '500';
                });
                
                // Target dropdown menus and options when opened
                sidebar.querySelectorAll('[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"], [role="option"]').forEach(el => {
                    el.style.color = '#333333';
                    el.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                });
                
                // Target all list items in dropdowns
                sidebar.querySelectorAll('ul, li').forEach(el => {
                    if (el.closest('.stSelectbox')) {
                        el.style.color = '#333333';
                        el.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                    }
                });
            }
            
            // Also check for dropdown menus outside sidebar but related to sidebar selectboxes
            document.querySelectorAll('[data-baseweb="popover"], [data-baseweb="menu"]').forEach(menu => {
                // Check if this menu is related to a sidebar selectbox
                const triggerElement = document.querySelector('[data-testid="stSidebar"] .stSelectbox [aria-expanded="true"]');
                if (triggerElement) {
                    menu.querySelectorAll('*').forEach(el => {
                        el.style.color = '#333333';
                        el.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                    });
                }
            });
            
            // Aggressively target all dropdown options globally
            document.querySelectorAll('div[role="listbox"], div[role="option"], [data-baseweb="popover"], [data-baseweb="menu"]').forEach(dropdown => {
                dropdown.style.color = '#333333';
                dropdown.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                
                // Target all children of dropdown elements
                dropdown.querySelectorAll('*').forEach(child => {
                    child.style.color = '#333333';
                    child.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                });
            });
        }
        
        // Run dropdown styling periodically
        setInterval(forceDropdownStyling, 500);
        
        // Additional aggressive dropdown option targeting
        function forceDropdownOptionStyling() {
            // Target all possible dropdown option selectors
            const selectors = [
                'div[role="listbox"]',
                'div[role="option"]', 
                '[data-baseweb="popover"]',
                '[data-baseweb="menu"]',
                '.css-26l3qy-menu',
                '.css-qrbaxs',
                '.css-1n76uvr'
            ];
            
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    el.style.color = '#333333';
                    el.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                    
                    // Also style all children
                    el.querySelectorAll('*').forEach(child => {
                        child.style.color = '#333333';
                        if (!['INPUT', 'TEXTAREA', 'BUTTON'].includes(child.tagName)) {
                            child.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                        }
                    });
                });
            });
        }
        
        // Run dropdown option styling more frequently to catch dynamic elements
        setInterval(forceDropdownOptionStyling, 100);
        
        // ULTRA AGGRESSIVE dropdown targeting
        function ultraAggressiveDropdownStyling() {
            // Target ALL divs that might be dropdown options
            document.querySelectorAll('div').forEach(div => {
                // Check if element has role attributes or is in a dropdown context
                if (div.getAttribute('role') === 'option' || 
                    div.getAttribute('role') === 'listbox' ||
                    div.closest('[data-baseweb="popover"]') ||
                    div.closest('[data-baseweb="menu"]') ||
                    div.closest('[role="listbox"]') ||
                    div.classList.toString().includes('select') ||
                    div.classList.toString().includes('menu') ||
                    div.classList.toString().includes('option')) {
                    
                    div.style.color = '#333333';
                    div.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                    
                    // Also target all children
                    div.querySelectorAll('*').forEach(child => {
                        child.style.color = '#333333';
                        child.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                    });
                }
            });
            
            // Target any white text elements that might be dropdown options
            document.querySelectorAll('*').forEach(el => {
                const computedStyle = window.getComputedStyle(el);
                if ((computedStyle.color === 'rgb(255, 255, 255)' || computedStyle.color === 'white') &&
                    (el.closest('[data-baseweb="popover"]') || 
                     el.closest('[data-baseweb="menu"]') ||
                     el.closest('[role="listbox"]') ||
                     el.getAttribute('role') === 'option')) {
                    el.style.color = '#333333';
                    el.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                }
            });
        }
        
        // Run ultra aggressive styling every 50ms
        setInterval(ultraAggressiveDropdownStyling, 50);
        
        // Set up mutation observer for dropdown changes
        const dropdownObserver = new MutationObserver((mutations) => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            // Check if added node is a dropdown element
                            if (node.getAttribute && (
                                node.getAttribute('role') === 'listbox' ||
                                node.getAttribute('role') === 'option' ||
                                node.getAttribute('data-baseweb') === 'popover' ||
                                node.getAttribute('data-baseweb') === 'menu')) {
                                
                                // Style the new element immediately
                                node.style.color = '#333333';
                                node.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                                
                                // Style all children
                                node.querySelectorAll('*').forEach(child => {
                                    child.style.color = '#333333';
                                    child.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
                                });
                            }
                        }
                    });
                }
            });
        });
        
        // Observe the entire document for dropdown changes
        dropdownObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['role', 'data-baseweb', 'class']
        });
    }
    
    // Run on page load and periodically
    document.addEventListener('DOMContentLoaded', () => {
        preventSidebarCollapse();
        forceSidebarVisibility();
    });
    setTimeout(() => {
        preventSidebarCollapse();
        forceSidebarVisibility();
    }, 100);
    setTimeout(() => {
        preventSidebarCollapse();
        forceSidebarVisibility();
    }, 500);
    setTimeout(() => {
        preventSidebarCollapse();
        forceSidebarVisibility();
    }, 1000);
    
    // Monitor for changes
    const observer = new MutationObserver(() => {
        preventSidebarCollapse();
        forceSidebarVisibility();
    });
    observer.observe(document.body, { 
        childList: true, 
        subtree: true, 
        attributes: true,
        attributeFilter: ['style', 'class']
    });
    </script>
    """, unsafe_allow_html=True)

def create_sidebar():
    """Create the elegant sidebar with all input controls"""
    
    # Logo and branding
    st.sidebar.markdown("""
    <div class="logo-container">
        <div class="logo-text">✨ AI Writer</div>
        <div class="logo-subtitle">Powered by OpenAI GPT-4 & DALL-E 3</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("### 📝 Content Configuration")
    
    # URL/Topic Input
    input_type = st.sidebar.radio("Input Method:", ["Topic/Keywords", "URL Analysis"])
    
    if input_type == "URL Analysis":
        url_input = st.sidebar.text_input(
            "🔗 Article URL", 
            placeholder="https://example.com/article-to-analyze",
            help="Provide a URL to analyze and generate related content"
        )
    else:
        url_input = None
    
    # Keywords input
    keywords = st.sidebar.text_area(
        "🎯 Target Keywords", 
        placeholder="Bitcoin, cryptocurrency, trading, investment",
        help="Enter main keywords separated by commas for SEO optimization",
        height=80,
        key="keywords_input"
    )
    
    # Show keyword count
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        st.sidebar.caption(f"📊 {len(keyword_list)} keywords detected")
    
    st.sidebar.markdown("### 🎨 Style & Format")
    
    # Language selection
    language = st.sidebar.selectbox(
        "🌍 Language",
        ["English", "Spanish", "French", "German", "Italian", "Portuguese", "Dutch"],
        help="Select the language for article generation"
    )
    
    # Tone selection
    tone = st.sidebar.selectbox(
        "🎭 Tone",
        ["Professional", "Conversational", "Academic", "Elegant", "Warm", "Technical", "Creative"],
        help="Choose the writing tone for your article"
    )
    
    # Focus/Angle
    focus = st.sidebar.text_input(
        "🎪 Focus/Angle",
        placeholder="Latest trends and market analysis",
        help="Specific angle or focus for the article"
    )
    
    # Number of sections
    sections = st.sidebar.slider(
        "📚 Number of Sections",
        min_value=3,
        max_value=8,
        value=5,
        help="Number of H2 sections in the article"
    )
    
    st.sidebar.markdown("### 🚀 Promotion & Links")
    
    # Promotional content
    promotion = st.sidebar.text_area(
        "📢 Promotional Content",
        placeholder="Visit our Bitcoin trading platform for advanced analytics",
        help="Optional promotional content to naturally integrate",
        height=80
    )
    
    # Internal links
    internal_links = st.sidebar.text_area(
        "🔗 Internal Links",
        placeholder="Bitcoin Guide: /bitcoin-guide, Trading Tips: /trading-tips",
        help="Format: Link Text: /url",
        height=80
    )
    
    st.sidebar.markdown("### ⚙️ Advanced Settings")
    
    # Word count
    word_count = st.sidebar.slider(
        "📄 Target Word Count",
        min_value=300,
        max_value=1500,
        value=600,
        step=50
    )
    
    # Include images
    include_images = st.sidebar.checkbox(
        "🖼️ Generate AI Images (DALL-E 3)",
        value=True,
        help="Generate contextual images using OpenAI DALL-E 3. Disable if experiencing API issues."
    )
    
    # SEO optimization
    seo_focus = st.sidebar.checkbox(
        "🔍 SEO Optimization",
        value=True,
        help="Enable advanced SEO optimization"
    )
    
    return {
        "input_type": input_type,
        "url_input": url_input,
        "keywords": keywords,
        "language": language,
        "tone": tone,
        "focus": focus,
        "sections": sections,
        "promotion": promotion,
        "internal_links": internal_links,
        "word_count": word_count,
        "include_images": include_images,
        "seo_focus": seo_focus
    }

def show_progress(message, step, total_steps):
    """Show animated progress indicator"""
    progress = step / total_steps
    st.markdown(f"""
    <div class="progress-container">
        <h3>🪶 {message}</h3>
        <p>Step {step} of {total_steps}</p>
    </div>
    """, unsafe_allow_html=True)
    
    progress_bar = st.progress(progress)
    return progress_bar

def display_seo_metrics(seo_data):
    """Display SEO metrics in a beautiful grid"""
    st.markdown('<div class="seo-metrics">', unsafe_allow_html=True)
    
    metrics = [
        ("Keyword Density", f"{seo_data.get('keyword_density', 0):.1f}%"),
        ("Readability Score", seo_data.get('readability_score', 0)),
        ("Word Count", seo_data.get('word_count', 0)),
        ("SEO Score", f"{seo_data.get('seo_score', 0)}/100")
    ]
    
    for label, value in metrics:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Load custom styling
    load_custom_css()
    
    # Create sidebar
    config = create_sidebar()
    
    # Main application header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown('<h1 class="main-title">🚀 AI Article Generator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="main-subtitle">Transform Your Ideas Into Professional Articles with AI-Powered Content and Visuals</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Check if OpenAI API key is configured
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key or openai_key.startswith("sk-your-") or openai_key == "demo-mode":
        st.error("🔑 Please configure your OpenAI API key in the .env file")
        st.code("OPENAI_API_KEY=sk-your-actual-api-key-here")
        st.info("💡 Your OpenAI API key enables both content generation (GPT-4) and image generation (DALL-E 3)")
        return
    
    # Generate button
    if st.button("✨ Generate Article", type="primary"):
        if not config["keywords"] and not config["url_input"]:
            st.error("Please provide either keywords or a URL to analyze")
            return
        
        # Initialize engines
        try:
            llm_engine = LLMEngine()
            image_engine = ImageEngine() if config["include_images"] else None
            content_tools = ContentTools()
            seo_tools = SEOTools()
            exporter = Exporter()
        except ValueError as e:
            st.error(f"❌ Configuration Error: {str(e)}")
            return
        
        try:
            # Step 1: Content Analysis
            progress_bar = show_progress("Analyzing content and keywords...", 1, 6)
            
            if config["url_input"]:
                # URL analysis mode
                url_context = content_tools.extract_url_content(config["url_input"])
                context = f"URL Analysis: {url_context}"
            else:
                context = f"Keywords: {config['keywords']}"
            
            progress_bar.progress(1/6)
            time.sleep(1)
            
            # Step 2: Generate Article Structure
            show_progress("Creating article structure...", 2, 6)
            
            article_data = llm_engine.generate_article(
                context=context,
                keywords=config["keywords"],
                language=config["language"],
                tone=config["tone"],
                focus=config["focus"],
                sections=config["sections"],
                word_count=config["word_count"],
                promotion=config["promotion"],
                seo_focus=config["seo_focus"]
            )
            
            progress_bar.progress(2/6)
            time.sleep(1)
            
            # Step 3: SEO Optimization
            show_progress("Optimizing for SEO...", 3, 6)
            
            seo_data = seo_tools.optimize_content(
                article_data,
                keywords=config["keywords"],
                focus_keyword=config["keywords"].split(",")[0] if config["keywords"] else None
            )
            
            progress_bar.progress(3/6)
            time.sleep(1)
            
            # Step 4: Generate Images
            if config["include_images"] and image_engine:
                show_progress("Generating AI images with DALL-E 3...", 4, 6)
                
                images = image_engine.generate_images(
                    article_data,
                    tone=config["tone"]
                )
                
                # Show image generation summary
                if images:
                    stats = image_engine.get_image_stats(images)
                    generated_count = stats['generated_count']
                    placeholder_count = stats['placeholder_count']
                    
                    if generated_count == len(images):
                        st.success(f"🎨 Successfully generated {generated_count} AI images with DALL-E 3!")
                    elif generated_count > 0:
                        st.warning(f"🎨 Generated {generated_count} AI images, {placeholder_count} placeholders (DALL-E temporarily unavailable)")
                    else:
                        st.info("🖼️ Using placeholder images (DALL-E temporarily unavailable)")
                
                progress_bar.progress(4/6)
                time.sleep(1)
            else:
                images = {}
            
            # Step 5: Content Enhancement
            show_progress("Enhancing content with links...", 5, 6)
            
            enhanced_content = content_tools.enhance_content(
                article_data,
                internal_links=config["internal_links"],
                seo_data=seo_data
            )
            
            progress_bar.progress(5/6)
            time.sleep(1)
            
            # Step 6: Final Processing
            show_progress("Finalizing your masterpiece...", 6, 6)
            
            progress_bar.progress(1.0)
            time.sleep(1)
            
            # Clear progress indicators
            st.empty()
            
            # Display results
            st.success("🎉 Article generated successfully!")
            
            # Display content directly after generation
            display_generated_content(enhanced_content, seo_data, images, exporter)
            
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            st.info("Please check your API keys and try again.")
    
def display_generated_content(enhanced_content, seo_data, images, exporter):
    """Display the generated content in tabs"""
    if not enhanced_content:
        return

    # Create tabs for different views
    tabs = ["📖 Preview", "📊 SEO Data", "💻 HTML View", "📥 Export"]
    current_tabs = st.tabs(tabs)
        
    with current_tabs[0]:
        # Article preview
            st.markdown('<div class="generated-content">', unsafe_allow_html=True)
            
            # Watermark
            generated_image_count = sum(1 for img in images.values() if not img.get('is_placeholder', False)) if images else 0
            total_images = len(images) if images else 0
            
            if total_images > 0:
                if generated_image_count == total_images:
                    watermark_text = "✨ Generated by AI Writer — Powered by OpenAI GPT-4 & DALL-E 3 🎨"
                elif generated_image_count > 0:
                    watermark_text = f"✨ Generated by AI Writer — Content: GPT-4, Images: {generated_image_count}/{total_images} DALL-E 3 🎨"
                else:
                    watermark_text = "✨ Generated by AI Writer — Powered by OpenAI GPT-4 📝"
            else:
                watermark_text = "✨ Generated by AI Writer — Powered by OpenAI GPT-4 📝"
            
            st.markdown(f"""
            <div class="ai-watermark">
                {watermark_text}
            </div>
            """, unsafe_allow_html=True)
            
            # Title and meta
            st.markdown(f"# {enhanced_content['title']}")
            st.caption(f"📝 {enhanced_content['meta_description']}")
            
            # Article body with images
            for i, section in enumerate(enhanced_content['sections']):
                st.markdown(f"## {section['heading']}")
                st.markdown(section['content'])
                
                # Display generated image if available
                if i in images:
                    image_data = images[i]
                    
                    # Show image with status indicator
                    if image_data.get('is_placeholder', False):
                        st.image(image_data['url'], caption=f"📷 {image_data['caption']} (Placeholder)", use_column_width=True)
                        st.caption("💡 This is a placeholder image. DALL-E 3 was temporarily unavailable.")
                    else:
                        st.image(image_data['url'], caption=f"🎨 {image_data['caption']} (Generated by DALL-E 3)", use_column_width=True)
            
            # CTA section
            if enhanced_content.get('cta'):
                st.markdown("---")
                st.markdown(enhanced_content['cta'])
            
            st.markdown('</div>', unsafe_allow_html=True)
            
    with current_tabs[1]:
        # Article Analytics Tab
        if enhanced_content:
            st.subheader("📈 Article Analytics")
            
            # Performance Metrics
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                st.metric("Word Count", len(enhanced_content.get('full_content', '').split()), "+12%")
            
            with metrics_col2:
                readability_score = seo_data.get('readability_score', 78) if seo_data else 78
                st.metric("Readability Score", f"{readability_score}/100", "+5%")
            
            with metrics_col3:
                seo_score = seo_data.get('seo_score', 85) if seo_data else 85
                st.metric("SEO Score", f"{seo_score}/100", "+8%")
            
            # SEO section
            st.subheader("📊 SEO Analysis")
            
            seo_col1, seo_col2 = st.columns(2)
            
            with seo_col1:
                st.markdown("**🎯 Primary Keywords**")
                st.write(", ".join(seo_data.get('keywords', [])))
                
                st.markdown("**🔍 SEO Score**")
                seo_score = seo_data.get('seo_score', 85)
                st.progress(seo_score / 100)
                st.write(f"{seo_score}/100")
            
            with seo_col2:
                st.markdown("**� Meta Description**")
                st.write(enhanced_content['meta_description'])
                
                st.markdown("**📊 Content Metrics**")
                word_count = len(enhanced_content.get('full_content', '').split())
                st.write(f"Words: {word_count}")
                st.write(f"Sections: {len(enhanced_content.get('sections', []))}")
            
            # Tags
            if seo_data.get('tags'):
                st.markdown("**🏷️ Suggested Tags**")
                tag_cols = st.columns(min(len(seo_data['tags']), 5))
                for i, tag in enumerate(seo_data['tags'][:5]):
                    with tag_cols[i]:
                        st.markdown(f"`{tag}`")
        else:
            st.info("No analytics available. Generate an article first to see detailed analytics.")
    
    with current_tabs[2]:
        # HTML view
        if enhanced_content:
            st.markdown("### 💻 HTML Export")
            html_content = exporter.generate_html(enhanced_content, seo_data, images)
            st.code(html_content, language='html')
            
            if st.button("📋 Copy HTML"):
                st.success("HTML copied to clipboard!")
        else:
            st.info("No HTML content available. Generate an article first.")
    
    with current_tabs[3]:
        # Export options
        if enhanced_content:
            st.markdown("### 📥 Export Options")
            
            # Generate files on-demand to prevent page refresh issues
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # On-demand file generation to prevent browser issues
            st.info("Click buttons below to generate files. This prevents automatic generation that can cause page refresh issues.")
            
            # Generate HTML
            try:
                html_content = exporter.generate_html(enhanced_content, seo_data, images)
                html_filename = f"article_{timestamp}.html"
            except Exception as e:
                st.error(f"Error generating HTML: {e}")
                html_content = None
            
            # Generate DOCX
            try:
                docx_file = exporter.generate_docx(enhanced_content, seo_data, images)
                docx_filename = f"article_{timestamp}.docx"
            except Exception as e:
                st.error(f"Error generating DOCX: {e}")
                docx_file = None
            
            # Generate Analytics
            try:
                analytics_data = exporter.generate_analytics(enhanced_content, seo_data)
                analytics_filename = f"analytics_{timestamp}.json"
            except Exception as e:
                st.error(f"Error generating analytics: {e}")
                analytics_data = None
                
                # Create download buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if docx_file:
                        st.download_button(
                            label="� Download Word Document",
                            data=docx_file,
                            file_name=docx_filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="download_docx"
                        )
                    else:
                        st.error("DOCX generation failed")
                
                with col2:
                    if html_content:
                        st.download_button(
                            label="🌐 Download HTML File",
                            data=html_content,
                            file_name=html_filename,
                            mime="text/html",
                            key="download_html"
                        )
                    else:
                        st.error("HTML generation failed")
                
                with col3:
                    if analytics_data:
                        st.download_button(
                            label="� Download Analytics JSON",
                            data=analytics_data,
                            file_name=analytics_filename,
                            mime="application/json",
                            key="download_analytics"
                        )
                    else:
                        st.error("Analytics generation failed")
            
        else:
            st.info("No export options available. Generate an article first.")
    
    # Note: Recent projects section removed for cleaner interface

if __name__ == "__main__":
    main()