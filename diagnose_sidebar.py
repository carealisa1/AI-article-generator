"""
Diagnostic tool to check sidebar styling issues
Run this after the app loads to see what's happening with sidebar elements
"""

def diagnose_sidebar_styles():
    """JavaScript to run in browser console to diagnose sidebar issues"""
    
    js_diagnostic = """
// Streamlit Sidebar Diagnostic Tool
console.log('=== STREAMLIT SIDEBAR DIAGNOSTIC ===');

// Find sidebar
const sidebar = document.querySelector('[data-testid="stSidebar"]');
if (!sidebar) {
    console.log('❌ No sidebar found with [data-testid="stSidebar"]');
    return;
}

console.log('✅ Sidebar found:', sidebar);

// Check all inputs
const inputs = sidebar.querySelectorAll('input, textarea, select');
console.log('📝 Found', inputs.length, 'input elements');

inputs.forEach((input, i) => {
    const styles = window.getComputedStyle(input);
    console.log(`Input ${i}:`, {
        tagName: input.tagName,
        type: input.type || 'N/A',
        color: styles.color,
        backgroundColor: styles.backgroundColor,
        border: styles.border,
        visibility: styles.visibility,
        opacity: styles.opacity,
        display: styles.display
    });
});

// Check labels
const labels = sidebar.querySelectorAll('label');
console.log('🏷️ Found', labels.length, 'labels');

labels.forEach((label, i) => {
    const styles = window.getComputedStyle(label);
    console.log(`Label ${i}:`, {
        text: label.textContent?.substring(0, 30) + '...',
        color: styles.color,
        visibility: styles.visibility,
        opacity: styles.opacity
    });
});

// Apply diagnostic fix
console.log('🔧 Applying diagnostic fix...');
sidebar.querySelectorAll('*').forEach(el => {
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName)) {
        el.style.setProperty('color', 'yellow', 'important');
        el.style.setProperty('background-color', 'rgba(255, 0, 0, 0.3)', 'important');
        el.style.setProperty('border', '3px solid lime', 'important');
        console.log('Fixed input:', el);
    } else if (['LABEL', 'SPAN', 'DIV', 'P'].includes(el.tagName)) {
        el.style.setProperty('color', 'cyan', 'important');
        el.style.setProperty('text-shadow', '2px 2px 4px black', 'important');
    }
});

console.log('=== DIAGNOSTIC COMPLETE ===');
"""
    
    return js_diagnostic

# Print the JavaScript to run in browser console
print("Copy and paste this JavaScript into your browser console when the Streamlit app is running:")
print("=" * 80)
print(diagnose_sidebar_styles())
print("=" * 80)
print("\nThis will:")
print("1. Find the sidebar element")
print("2. List all input fields and their current styles")
print("3. Apply high-contrast colors (yellow text, red background, lime borders)")
print("4. Show diagnostic information in the console")
print("\nIf the inputs become visible after running this, it confirms the CSS targeting works.")

if __name__ == "__main__":
    print(diagnose_sidebar_styles())