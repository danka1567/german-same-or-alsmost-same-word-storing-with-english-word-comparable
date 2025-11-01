
import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import time
import requests
import base64

# GitHub Configuration
GITHUB_TOKEN = "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"
REPO_OWNER = "danka1567"
REPO_NAME = "german-same-or-alsmost-same-word-storing-with-english-word-comparable"
FILE_PATH = "similar or partial GERMAN english.csv"
RAW_CSV_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH.replace(' ', '%20')}"

# Initialize session state variables
if 'session_new_words' not in st.session_state:
    st.session_state.session_new_words = []
if 'data' not in st.session_state:
    st.session_state.data = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'github_connected' not in st.session_state:
    st.session_state.github_connected = False

# ---------- GitHub Helper Functions ----------

def get_github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_file_sha():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH.replace(' ', '%20')}"
    response = requests.get(url, headers=get_github_headers())
    
    if response.status_code == 200:
        return response.json()['sha']
    else:
        st.error(f"Failed to get file SHA: {response.status_code}")
        return None

def read_csv_from_github():
    try:
        response = requests.get(RAW_CSV_URL)
        if response.status_code == 200:
            from io import StringIO
            csv_content = response.text
            df = pd.read_csv(StringIO(csv_content))
            
            data = []
            for _, row in df.iterrows():
                german = row.get('German') or row.get('Word', '')
                english = row.get('English', '')
                date_added = row.get('DateAdded', '')
                date_obj_str = row.get('DateObj', '')
                
                try:
                    if date_obj_str and pd.notna(date_obj_str):
                        date_obj = datetime.strptime(str(date_obj_str), "%Y-%m-%d %H:%M:%S")
                    else:
                        date_obj = datetime.now()
                except:
                    date_obj = datetime.now()
                
                data.append({
                    'German': german,
                    'English': english,
                    'DateAdded': date_added,
                    'DateObj': date_obj
                })
            
            st.session_state.github_connected = True
            return data
        else:
            st.error(f"Failed to read CSV file: {response.status_code}")
            return []
            
    except Exception as e:
        st.error(f"Error reading from GitHub: {e}")
        return []

def write_csv_to_github(data):
    try:
        sha = get_file_sha()
        if not sha:
            return False
        
        df_data = []
        for item in data:
            df_data.append({
                'German': item['German'],
                'English': item['English'],
                'DateAdded': item['DateAdded'],
                'DateObj': item['DateObj']
            })
        
        df = pd.DataFrame(df_data)
        csv_content = df.to_csv(index=False)
        content = base64.b64encode(csv_content.encode()).decode()
        
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH.replace(' ', '%20')}"
        update_data = {
            "message": f"Update German words - {len(data)} total words",
            "content": content,
            "sha": sha
        }
        
        response = requests.put(url, headers=get_github_headers(), json=update_data)
        
        if response.status_code == 200:
            return True
        else:
            st.error(f"Failed to update file: {response.status_code}")
            return False
            
    except Exception as e:
        st.error(f"Error writing to GitHub: {e}")
        return False

# ---------- Data Operations ----------

def clean_word(word):
    word_clean = re.sub(r"[^a-zA-ZäöüÄÖÜß]", "", word)
    return word_clean.capitalize() if word_clean else ""

def get_time_of_day(hour, minute=0):
    time_mapping = {
        (5, 6): "🌅 Dawn (Day)",
        (6, 9): "☀️ Morning (Day)",
        (9, 12): "🌞 Late Morning (Day)",
        (12, 15): "🏙️ Afternoon (Day)",
        (15, 18): "🌇 Late Afternoon (Day)",
        (18, 19): "🌆 Sunset (Night)",
        (19, 20): "🌃 Twilight (Night)",
        (20, 23): "🌙 Evening (Night)",
        (23, 0): "🌌 Midnight (Night)",
        (0, 5): "🌠 Night (Night)"
    }
    
    for (start, end), description in time_mapping.items():
        if start <= hour < end or (start == 23 and hour >= 23) or (end == 0 and hour < 5):
            return description
    return "☀️ Daytime (Day)"

def custom_timestamp():
    now = datetime.now()
    months = ["🌸 Jan", "❄️ Feb", "🌱 Mar", "🌷 Apr", "🌞 May", "🌻 Jun", 
              "🏖️ Jul", "🌊 Aug", "🍂 Sep", "🎃 Oct", "🍁 Nov", "🎄 Dec"]
    month_custom = months[now.month - 1]
    weekday = now.strftime("%A")
    hour = now.hour
    minute = now.minute
    am_pm = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    tod = get_time_of_day(hour, minute)
    timestamp_str = f"{now.day} {month_custom} {now.year} | {weekday} {hour_12}:{minute:02d} {am_pm} | {tod}"
    return timestamp_str, now

def time_ago(past_time):
    if isinstance(past_time, str):
        try:
            past_time = datetime.strptime(past_time, "%Y-%m-%d %H:%M:%S")
        except:
            return "⏳ Unknown time ago"
    
    now = datetime.now()
    diff = now - past_time
    seconds = diff.total_seconds()
    
    if seconds < 60:
        ago = f"🕐 {int(seconds)} seconds ago"
    elif seconds < 3600:
        ago = f"🕑 {int(seconds//60)} minutes ago"
    elif seconds < 86400:
        ago = f"🕒 {int(seconds//3600)} hours ago"
    else:
        days = int(seconds//86400)
        if days == 1:
            ago = f"📅 {days} day ago"
        else:
            ago = f"📅 {days} days ago"
    
    if isinstance(past_time, datetime):
        tod = get_time_of_day(past_time.hour, past_time.minute)
    else:
        tod = "⏰ Unknown"
    return f"{ago} | {tod}"

def load_existing_words():
    data = read_csv_from_github()
    existing_words = {}
    
    for row in data:
        german = row['German']
        if not german:
            continue
        
        existing_words[german] = {
            'English': row.get('English', ''),
            'DateAdded': row.get('DateAdded', ''),
            'DateObj': row.get('DateObj')
        }
    
    return existing_words

def save_word_pairs(pairs):
    existing_words = load_existing_words()
    current_data = read_csv_from_github()
    new_entries = []
    
    for german, english in pairs:
        g_clean = clean_word(german.strip())
        e_clean = clean_word(english.strip())
        
        if g_clean and e_clean and g_clean not in existing_words:
            timestamp_str, dt_obj = custom_timestamp()
            entry = {
                'German': g_clean,
                'English': e_clean,
                'DateAdded': timestamp_str,
                'DateObj': dt_obj.strftime("%Y-%m-%d %H:%M:%S")
            }
            new_entries.append(entry)
            st.session_state.session_new_words.append(entry)
    
    if not new_entries:
        return []
    
    updated_data = current_data + new_entries
    
    if write_csv_to_github(updated_data):
        return new_entries
    else:
        return []

def read_csv_data():
    return read_csv_from_github()

def search_words(words):
    existing_words = load_existing_words()
    results = []
    
    for word in words:
        clean = clean_word(word.strip())
        if clean:
            if clean in existing_words:
                entry = existing_words[clean]
                results.append({
                    'German': clean,
                    'English': entry['English'],
                    'DateAdded': entry['DateAdded'],
                    'TimeAgo': time_ago(entry['DateObj'])
                })
            else:
                results.append({'German': clean, 'English': '❌ Not Found', 'DateAdded': "🚫", 'TimeAgo': ""})
    
    return results

def delete_word_from_csv(word_or_index):
    current_data = read_csv_from_github()
    updated_data = []
    deleted = False
    
    for i, row in enumerate(current_data, start=1):
        if (str(i) == str(word_or_index) or 
            clean_word(row.get('German', '')) == clean_word(word_or_index) or 
            clean_word(row.get('English', '')) == clean_word(word_or_index)):
            deleted = True
            continue
        updated_data.append(row)
    
    if deleted:
        if write_csv_to_github(updated_data):
            return True
        else:
            return False
    
    return deleted

def edit_word_in_csv(search_word, new_german, new_english):
    current_data = read_csv_from_github()
    edited = False
    
    for row in current_data:
        if clean_word(row.get('German', '')) == clean_word(search_word):
            if new_german:
                row['German'] = clean_word(new_german)
            if new_english:
                row['English'] = clean_word(new_english)
            edited = True
            break
    
    if edited:
        if write_csv_to_github(current_data):
            return True
        else:
            return False
    
    return edited

# ---------- Beautiful UI Functions ----------

def display_data(data):
    if not data:
        st.info("🎯 No words to display. Start by adding some German-English pairs!")
        return
    
    df_data = []
    for item in data:
        df_data.append({
            '🇩🇪 German': item['German'],
            '🇬🇧 English': item.get('English', ''),
            '📅 Date Added': item['DateAdded'],
            '⏰ Time Ago': item.get('TimeAgo', time_ago(item['DateObj']) if 'DateObj' in item else "")
        })
    
    df = pd.DataFrame(df_data)
    
    # Beautiful styling with gradients and colors
    styled_df = df.style.set_properties(**{
        'background-color': '#0f1116',
        'color': '#ffffff',
        'border': '1px solid #2d3746',
        'text-align': 'center',
        'font-weight': 'bold',
        'font-family': 'Arial, sans-serif'
    }).set_table_styles([
        {'selector': 'thead th', 
         'props': [
             ('background', 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'),
             ('color', 'white'),
             ('font-weight', 'bold'),
             ('font-size', '14px'),
             ('border', '2px solid #4a5568'),
             ('text-align', 'center')
         ]},
        {'selector': 'tbody tr:nth-child(even)', 
         'props': [('background-color', '#1a202c')]},
        {'selector': 'tbody tr:nth-child(odd)', 
         'props': [('background-color', '#2d3748')]},
        {'selector': 'tbody tr:hover', 
         'props': [('background-color', '#4a5568')]},
        {'selector': 'td', 
         'props': [('border', '1px solid #4a5568')]}
    ])
    
    st.dataframe(styled_df, use_container_width=True, height=400)

def create_gradient_text(text, size=24):
    return f"""
    <h1 style='
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4, #FFEAA7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: {size}px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    '>{text}</h1>
    """

def create_feature_card(icon, title, description, color):
    return f"""
    <div style='
        background: {color};
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #ffffff;
    '>
        <h3 style='color: white; margin: 0; font-size: 18px;'>
            {icon} {title}
        </h3>
        <p style='color: #e2e8f0; margin: 5px 0 0 0; font-size: 14px;'>
            {description}
        </p>
    </div>
    """

def show_all_words():
    data = read_csv_data()
    st.session_state.data = data
    display_data(data)

def show_new_words():
    display_data(st.session_state.session_new_words)

def find_words(search_text):
    if not search_text:
        return
    words_list = search_text.split()
    results = search_words(words_list)
    st.session_state.search_results = results
    display_data(results)

def save_words_action(input_text):
    if not input_text.strip():
        st.error("⚠️ Please enter at least one German–English pair.")
        return
    
    words = re.split(r"[\s,]+", input_text)
    if len(words) < 2:
        st.error("⚠️ Please enter at least one German–English pair.")
        return
    if len(words) % 2 != 0:
        words = words[:-1]
    
    pairs = [(words[i], words[i + 1]) for i in range(0, len(words), 2)]
    if not pairs:
        st.error("⚠️ No complete German–English pairs found.")
        return
    
    new_entries = save_word_pairs(pairs)
    if new_entries:
        st.success(f"🎉 Successfully saved {len(new_entries)} new word pair(s) to GitHub!")
        show_new_words()
    else:
        st.info("💡 No new words were added (they might already exist).")

def delete_words_action(delete_text):
    if not delete_text.strip():
        st.error("⚠️ Please enter a German/English word or row number to delete.")
        return
    
    deleted = delete_word_from_csv(delete_text)
    if deleted:
        st.success(f"🗑️ '{delete_text}' deleted successfully from GitHub!")
        show_all_words()
    else:
        st.error(f"❌ '{delete_text}' not found in GitHub database.")

def edit_words_action(edit_text):
    if not edit_text.strip():
        st.error("⚠️ Please enter the German word to edit.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_german = st.text_input("✏️ New German word (leave blank to keep unchanged):", key="edit_german")
    with col2:
        new_english = st.text_input("✏️ New English word (leave blank to keep unchanged):", key="edit_english")
    
    if st.button("✅ Confirm Edit", key="confirm_edit", use_container_width=True):
        edited = edit_word_in_csv(edit_text, new_german.strip(), new_english.strip())
        if edited:
            st.success(f"✨ '{edit_text}' edited successfully in GitHub!")
            show_all_words()
        else:
            st.error(f"❌ '{edit_text}' not found in GitHub database.")

# ---------- Beautiful Streamlit App Layout ----------

def main():
    st.set_page_config(
        page_title="🇩🇪 German Words Master",
        page_icon="🇩🇪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for beautiful styling
    st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
    }
    
    .stButton button {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    .stTextInput input, .stTextArea textarea {
        background: #1a202c;
        color: white;
        border: 2px solid #4a5568;
        border-radius: 10px;
        padding: 10px;
    }
    
    .stSuccess {
        background: linear-gradient(45deg, #00b09b, #96c93d);
        color: white;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stError {
        background: linear-gradient(45deg, #ff416c, #ff4b2b);
        color: white;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stInfo {
        background: linear-gradient(45deg, #4facfe, #00f2fe);
        color: white;
        padding: 10px;
        border-radius: 10px;
    }
    
    .css-1d391kg {
        background: #1a202c;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with gradient text
    st.markdown(create_gradient_text("🇩🇪 German Words Master", 36), unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #cbd5e0; font-size: 18px;'>Beautiful German-English Vocabulary Manager</p>", unsafe_allow_html=True)
    
    # Connection status
    if not st.session_state.github_connected:
        with st.spinner("🔗 Connecting to GitHub..."):
            test_data = read_csv_from_github()
            if test_data:
                st.success("✅ Connected to GitHub successfully!")
            else:
                st.error("❌ Failed to connect to GitHub")
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(create_feature_card("📝", "Add Words", "Easily add new German-English pairs", "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"), unsafe_allow_html=True)
    with col2:
        st.markdown(create_feature_card("🔍", "Search & Find", "Quickly search through your vocabulary", "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"), unsafe_allow_html=True)
    with col3:
        st.markdown(create_feature_card("🔄", "Sync to GitHub", "Automatic cloud synchronization", "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Section 1: Add New Words
    with st.container():
        st.markdown("### 📝 Add New Word Pairs")
        st.write("Enter German–English pairs (space or comma-separated):")
        
        input_text = st.text_area(
            "Word Pairs Input",
            placeholder="Example: Haus House, Katze Cat, Baum Tree...",
            key="word_input",
            height=100
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("💾 Save Words", use_container_width=True, disabled=not st.session_state.github_connected):
                save_words_action(input_text)
        with col2:
            if st.button("🔄 Clear Input", use_container_width=True):
                st.rerun()
    
    st.markdown("---")
    
    # Section 2: Search and Manage
    with st.container():
        st.markdown("### 🔍 Search & Manage Vocabulary")
        st.write("Search, edit, or delete words:")
        
        search_text = st.text_input(
            "Search Input",
            placeholder="Enter German word, English word, or row number...",
            key="search_input"
        )
        
        # Action buttons in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Find Words", use_container_width=True, disabled=not st.session_state.github_connected):
                find_words(search_text)
        with col2:
            if st.button("📋 Show All", use_container_width=True, disabled=not st.session_state.github_connected):
                show_all_words()
        with col3:
            if st.button("🆕 New Words", use_container_width=True):
                show_new_words()
        with col4:
            if st.button("🗑️ Delete", use_container_width=True, disabled=not st.session_state.github_connected):
                delete_words_action(search_text)
        
        # Edit section
        if search_text.strip():
            st.markdown("---")
            st.markdown("### ✏️ Edit Word")
            edit_words_action(search_text)
    
    st.markdown("---")
    
    # Display area
    if st.session_state.get('data'):
        st.markdown("### 📊 Your Vocabulary Collection")
        display_data(st.session_state.data)
    elif st.session_state.get('search_results'):
        st.markdown("### 🔍 Search Results")
        display_data(st.session_state.search_results)
    
    # Beautiful Sidebar
    with st.sidebar:
        st.markdown(create_gradient_text("📊 Dashboard", 24), unsafe_allow_html=True)
        
        if st.session_state.github_connected:
            try:
                data = read_csv_data()
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("📚 Total Words", len(data), delta=f"+{len(st.session_state.session_new_words)} new")
                with col2:
                    if data:
                        latest = data[-1]['German'] if data else "None"
                        st.metric("🆕 Latest Word", latest)
                
                # Progress bar for word count
                word_count = len(data)
                target = 1000
                progress = min(word_count / target, 1.0)
                st.progress(progress)
                st.write(f"🎯 Progress: {word_count}/{target} words ({progress*100:.1f}%)")
                
            except:
                st.warning("📡 Could not load data")
        else:
            st.error("🔌 Not connected to GitHub")
        
        st.markdown("---")
        st.markdown("### 🌟 Features")
        st.markdown("""
        - ✨ **Beautiful Interface**
        - ☁️ **Cloud Sync**
        - 🔍 **Smart Search**
        - 📱 **Mobile Friendly**
        - 🎨 **Colorful Design**
        """)
        
        st.markdown("---")
        st.markdown("### 🔗 Quick Links")
        st.markdown(f"""
        [📁 View on GitHub](https://github.com/{REPO_OWNER}/{REPO_NAME})
        """)

if __name__ == "__main__":
    main()
