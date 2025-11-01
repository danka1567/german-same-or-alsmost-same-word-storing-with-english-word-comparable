import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import time
import requests
import base64

# GitHub Configuration - Using your existing repository and file
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
    """Get headers for GitHub API requests"""
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def get_file_sha():
    """Get the SHA of the current file for updates"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH.replace(' ', '%20')}"
    response = requests.get(url, headers=get_github_headers())
    
    if response.status_code == 200:
        return response.json()['sha']
    else:
        st.error(f"Failed to get file SHA: {response.status_code}")
        return None

def read_csv_from_github():
    """Read CSV data directly from GitHub raw URL"""
    try:
        response = requests.get(RAW_CSV_URL)
        if response.status_code == 200:
            # Read the CSV content
            from io import StringIO
            csv_content = response.text
            df = pd.read_csv(StringIO(csv_content))
            
            # Convert DataFrame to our expected format
            data = []
            for _, row in df.iterrows():
                german = row.get('German') or row.get('Word', '')
                english = row.get('English', '')
                date_added = row.get('DateAdded', '')
                date_obj_str = row.get('DateObj', '')
                
                # Handle DateObj conversion
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
    """Write CSV data back to GitHub"""
    try:
        # Get current file SHA
        sha = get_file_sha()
        if not sha:
            return False
        
        # Convert data to DataFrame
        df_data = []
        for item in data:
            df_data.append({
                'German': item['German'],
                'English': item['English'],
                'DateAdded': item['DateAdded'],
                'DateObj': item['DateObj']
            })
        
        df = pd.DataFrame(df_data)
        
        # Convert DataFrame to CSV string
        csv_content = df.to_csv(index=False)
        
        # Encode content
        content = base64.b64encode(csv_content.encode()).decode()
        
        # Update file
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH.replace(' ', '%20')}"
        update_data = {
            "message": f"Update German words - {len(data)} total words",
            "content": content,
            "sha": sha
        }
        
        response = requests.put(url, headers=get_github_headers(), json=update_data)
        
        if response.status_code == 200:
            st.success("✅ Successfully updated GitHub repository!")
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
    if 5 <= hour < 6:
        return "Dawn (Day)"
    elif 6 <= hour < 9:
        return "Morning (Day)"
    elif 9 <= hour < 12:
        return "Late Morning (Day)"
    elif 12 <= hour < 15:
        return "Afternoon (Day)"
    elif 15 <= hour < 18:
        return "Late Afternoon (Day)"
    elif 18 <= hour < 19:
        return "Sunset (Night)"
    elif 19 <= hour < 20:
        return "Twilight (Night)"
    elif 20 <= hour < 23:
        return "Evening (Night)"
    elif 23 <= hour or hour < 0:
        return "Midnight (Night)"
    elif 0 <= hour < 5:
        return "Night (Night)"
    else:
        return "Daytime (Day)"

def custom_timestamp():
    now = datetime.now()
    months = ["jano","febo","maro","apro","maio","juno","julo","augo","sepo","octo","nove","deco"]
    month_custom = months[now.month - 1]
    weekday = now.strftime("%A")
    hour = now.hour
    minute = now.minute
    am_pm = "AM" if hour < 12 else "PM"
    hour_12 = hour % 12 or 12
    tod = get_time_of_day(hour, minute)
    timestamp_str = f"{now.day} {month_custom} {now.year} : {weekday} {hour_12}:{minute:02d} {am_pm} {tod}"
    return timestamp_str, now

def time_ago(past_time):
    if isinstance(past_time, str):
        try:
            past_time = datetime.strptime(past_time, "%Y-%m-%d %H:%M:%S")
        except:
            return "Unknown time ago"
    
    now = datetime.now()
    diff = now - past_time
    seconds = diff.total_seconds()
    if seconds < 60:
        ago = f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        ago = f"{int(seconds//60)} minutes ago"
    elif seconds < 86400:
        ago = f"{int(seconds//3600)} hours ago"
    else:
        ago = f"{int(seconds//86400)} days ago"
    
    if isinstance(past_time, datetime):
        tod = get_time_of_day(past_time.hour, past_time.minute)
    else:
        tod = "Unknown"
    return f"{ago} | {tod}"

def load_existing_words():
    """Load words from GitHub CSV"""
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
    """Save word pairs to GitHub"""
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
    
    # Add new entries to current data
    updated_data = current_data + new_entries
    
    # Write back to GitHub
    if write_csv_to_github(updated_data):
        return new_entries
    else:
        return []

def read_csv_data():
    """Read all data from GitHub"""
    return read_csv_from_github()

def search_words(words):
    """Search for words in GitHub CSV"""
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
                results.append({'German': clean, 'English': '', 'DateAdded': "Not Found", 'TimeAgo': ""})
    
    return results

def delete_word_from_csv(word_or_index):
    """Delete word from GitHub CSV"""
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
    """Edit word in GitHub CSV"""
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

# ---------- Streamlit UI Functions ----------

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

def display_data(data):
    if not data:
        st.info("No words to display.")
        return
    
    df_data = []
    for item in data:
        df_data.append({
            'German': item['German'],
            'English': item.get('English', ''),
            'Date Added': item['DateAdded'],
            'Time Ago': item.get('TimeAgo', time_ago(item['DateObj']) if 'DateObj' in item else "")
        })
    
    df = pd.DataFrame(df_data)
    
    # Apply custom styling
    styled_df = df.style.set_properties(**{
        'background-color': '#ffffff',
        'color': '#2E4053',
        'border-color': '#2196F3',
        'text-align': 'center',
        'font-weight': 'bold'
    }).set_table_styles([
        {'selector': 'thead th', 'props': [('background-color', '#2196F3'), 
                                         ('color', 'white'), 
                                         ('font-weight', 'bold'),
                                         ('font-size', '14pt')]},
        {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#e6f2ff')]},
        {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#ffffff')]}
    ])
    
    st.dataframe(styled_df, use_container_width=True)

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
        st.success(f"✅ Successfully saved {len(new_entries)} new word pair(s) to GitHub!")
        show_new_words()
    else:
        st.info("No new words were added (they might already exist).")

def delete_words_action(delete_text):
    if not delete_text.strip():
        st.error("⚠️ Please enter a German/English word or row number to delete.")
        return
    
    deleted = delete_word_from_csv(delete_text)
    if deleted:
        st.success(f"✅ '{delete_text}' deleted successfully from GitHub!")
        show_all_words()
    else:
        st.error(f"❌ '{delete_text}' not found in GitHub database.")

def edit_words_action(edit_text):
    if not edit_text.strip():
        st.error("⚠️ Please enter the German word to edit.")
        return
    
    # Create columns for input
    col1, col2 = st.columns(2)
    
    with col1:
        new_german = st.text_input("New German word (leave blank to keep unchanged):", key="edit_german")
    with col2:
        new_english = st.text_input("New English word (leave blank to keep unchanged):", key="edit_english")
    
    if st.button("Confirm Edit", key="confirm_edit"):
        edited = edit_word_in_csv(edit_text, new_german.strip(), new_english.strip())
        if edited:
            st.success(f"✅ '{edit_text}' edited successfully in GitHub!")
            show_all_words()
        else:
            st.error(f"❌ '{edit_text}' not found in GitHub database.")

# ---------- Streamlit App Layout ----------

def main():
    st.set_page_config(
        page_title="German Words Manager - GitHub",
        page_icon="🇩🇪",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main { background-color: #f0f2f5; }
        .stButton button { font-weight: bold; border-radius: 5px; }
        .success-message { color: #4CAF50; }
        .error-message { color: #E53935; }
        .info-message { color: #2196F3; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🇩🇪 German Words Manager - GitHub Database")
    
    # Test connection on startup
    if not st.session_state.github_connected:
        with st.spinner("🔗 Connecting to GitHub..."):
            test_data = read_csv_from_github()
            if test_data:
                st.success("✅ Connected to GitHub successfully!")
            else:
                st.error("❌ Failed to connect to GitHub")
    
    # Connection status
    if not st.session_state.github_connected:
        st.error("🔴 Not connected to GitHub")
        st.info("""
        **Please check:**
        1. GitHub token is valid
        2. File exists at: https://github.com/danka1567/german-same-or-alsmost-same-word-storing-with-english-word-comparable/blob/main/similar%20or%20partial%20GERMAN%20english.csv
        3. You have internet connection
        """)
        
        if st.button("🔄 Retry Connection"):
            st.rerun()
    else:
        st.success("🟢 Connected to GitHub Database")
    
    st.markdown("---")
    
    # Section 1: Add New Words
    st.header("📝 Add New German-English Word Pairs")
    st.write("Enter German–English pairs (space or comma-separated, two words per pair):")
    
    input_text = st.text_area(
        "Word Pairs Input",
        placeholder="Example: Haus House, Katze Cat, Baum Tree",
        key="word_input",
        height=80
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("💾 Save Words", use_container_width=True, disabled=not st.session_state.github_connected):
            save_words_action(input_text)
    with col2:
        if st.button("🔄 Clear Input", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    
    # Section 2: Search and Manage Words
    st.header("🔍 Search and Manage Words")
    st.write("Search / Edit / Delete German words (space-separated or row number):")
    
    search_text = st.text_input(
        "Search/Edit/Delete Input",
        placeholder="Enter word(s) or row number",
        key="search_input"
    )
    
    # Action buttons in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔍 Find Words", use_container_width=True, disabled=not st.session_state.github_connected):
            find_words(search_text)
    
    with col2:
        if st.button("📋 Show All Words", use_container_width=True, disabled=not st.session_state.github_connected):
            show_all_words()
    
    with col3:
        if st.button("🆕 Show New Words", use_container_width=True):
            show_new_words()
    
    with col4:
        if st.button("🗑️ Delete Word", use_container_width=True, disabled=not st.session_state.github_connected):
            delete_words_action(search_text)
    
    # Edit section (appears when needed)
    if search_text.strip():
        st.markdown("---")
        st.subheader("✏️ Edit Word")
        edit_words_action(search_text)
    
    st.markdown("---")
    
    # Display area for results
    if st.session_state.get('data'):
        st.subheader("📊 Word List")
        display_data(st.session_state.data)
    elif st.session_state.get('search_results'):
        st.subheader("🔍 Search Results")
        display_data(st.session_state.search_results)
    
    # Sidebar with information
    with st.sidebar:
        st.header("ℹ️ GitHub Database")
        st.markdown(f"""
        **Connected to your existing repository:**
        - **Repository:** [{REPO_NAME}](https://github.com/{REPO_OWNER}/{REPO_NAME})
        - **File:** [{FILE_PATH}]({RAW_CSV_URL})
        - **Real-time synchronization**
        - **Automatic version control**
        
        **All changes are saved directly to your GitHub repository!**
        """)
        
        # Statistics
        if st.session_state.github_connected:
            try:
                data = read_csv_data()
                st.metric("Total Words in GitHub", len(data))
                st.metric("New This Session", len(st.session_state.session_new_words))
                
                # Show some file info
                if data:
                    latest_word = data[-1]['German'] if data else "None"
                    st.write(f"**Latest word:** {latest_word}")
                    
            except Exception as e:
                st.warning("Could not load data from GitHub")
        else:
            st.warning("Not connected to GitHub")

if __name__ == "__main__":
    main()
