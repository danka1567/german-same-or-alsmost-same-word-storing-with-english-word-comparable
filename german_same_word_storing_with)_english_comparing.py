import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import time
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets API configuration
SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "third-zephyr-451003-n6",
  "private_key_id": "a6297f789b583aca63214f897b9315faa91b3595",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC2O//Fz7h0PxQd\n1EwXmgYYvETZgDQLrPN2PWl22m6zs+HGQj/hY75xIvSd/YO44xLLed3IqS6u1e7h\nc67s1d8phgsGaLHYPoWCdhWVkEwisRvKE0AkxLO9UtV4bA8m0Eb0iHOvyLk+/h75\nwnIjyiOf6eatRCYMB/UUsBqKXedRGTegtD/thKVJNNdFir1TjOxx0AFxj4SXETdD\nfrWLxxelKURAEiGuxw3pzxyi2s1MRmoJ9AxEkjlboL2gBSPtwopIGqJyD0KD2Ig4\nYyMpdSIdyHMhi0xRGqKfEijVpwZMAAA54mbe4F4gFCCjk3kbNS6FY6xRyLguo7Xi\nq7IXKMcFAgMBAAECggEAB+7iupTJXd4lHQtR6LEe1NLVWHaZTWzRCHOx9KebrB0H\nlh7qMwCpmLlB1uLjahgQiGUcv5CF5LyRcqUbl1nUJjWco0HJhDVskHpdhC5M8jGt\nmQVvhGo/vN0vR9fEbRciD6ElECD314MujAbn+yDgniSLkz1lPp7WD3l/HkjqOgCA\n/hi+8nrct5TZN8IzzSxHg5NeVo/pLhQ9W1+CYTChdpCcMiWnq3Y6wlcfnCAMzd9h\nlHfSUzCA0mW4QWomnTmwAcs1uOpbeMfnzvIdSb4kUrC8fH4u5gr4U0C1ecIOqF0w\npyGXWDeAMLNI3JN/inc58p9TTa0/vEcg/xhBXpJx3QKBgQD87VB1FL9UZ9/ai3F4\nXZVZZSS4JIDuRI3TMOxdXHpQ0PtzO67dgYL2EiFpez990MqYdeRLvZvJJ4UdQ5pq\nhsobvZMf9y42ggO5Y3eyhe7nmyqAY4B1eC9u1Z6qC6bqUM9Vbfsk7pOyyVpGcSDT\nCRFon9pv7UgzGOYkIrmFQdx+lwKBgQC4cs6/KV2R/AVTLBukT2u2mHqpDJvBe8Be\nRluhnGkpmqfH+ecYpbFdVQrBIVso58VyTGu+dmDEeBMiGUMmkeyRC0XH63u09OBU\niv0vge07mh722XCO3Q7hwOx5z9/y2NZOtF9GFV8093rPtgy0blA9+BXwexB/7Ewg\nOJxDAxO2wwKBgQCJ54bn34EWr3BRg5hBzZzB2jD0KgsWXtCJZvJpUSPr7pY7VT5Z\nzeSu8GHBVo7etbnQ+O6aEW7gdajRtOt7y7Rk/a87TZWn6KnJKh+4eegx5dt9l0MS\nSY5rOxRAmQvQVHFHnijCEUb8w2ZyY/pGtnoEdqwuPM0R9zB8YWaP7sIfTwKBgQCd\nKaYkmHiURWu8HN9IuCuNoIsTtBybVnjpW4YERKQOwSqpaLSS+cwRPL83JNbqGeLR\nq3A7D98QSUf0TBY9rSUnybUhzfLQk776CpwFeO3NVVuA9nHEKXPexGY6vPeTk1O4\nKFTuAJPpK95HUlWtADn7M4JuME400gFjixkKuHp5xQKBgQDWX8xPDrKSGZDcQxjw\nvjNmsUBLl3Ss3Fe3pQp9K9xOueHsjqiWrW1a077HbX3QiLTawLw+azz85dIz86TP\nOnzVXDgdwaxkglr8HHoKnnUrTWF95J8u8IvAFQIc91GBngU7LSa1C4Epgccw/zYH\npZJMVBC6/LRCIcGdksLeyV42pQ==\n-----END PRIVATE KEY-----\n",
  "client_email": "german-english-similar-or--775@third-zephyr-451003-n6.iam.gserviceaccount.com",
  "client_id": "112189292366267497212",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/german-english-similar-or--775%40third-zephyr-451003-n6.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# Google Sheets configuration
SPREADSHEET_NAME = "German Words Database"  # This should be the name of your Google Sheet
WORKSHEET_NAME = "Words"  # Name of the worksheet/tab

# Initialize session state variables
if 'session_new_words' not in st.session_state:
    st.session_state.session_new_words = []
if 'data' not in st.session_state:
    st.session_state.data = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# ---------- Google Sheets Helper Functions ----------

def get_google_sheets_client():
    """Initialize and return Google Sheets client"""
    try:
        creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO)
        scoped_creds = creds.with_scopes([
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        client = gspread.authorize(scoped_creds)
        return client
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

def get_or_create_spreadsheet():
    """Get existing spreadsheet or create a new one"""
    client = get_google_sheets_client()
    if not client:
        return None
    
    try:
        # Try to open existing spreadsheet
        spreadsheet = client.open(SPREADSHEET_NAME)
    except gspread.SpreadsheetNotFound:
        # Create new spreadsheet if it doesn't exist
        spreadsheet = client.create(SPREADSHEET_NAME)
        # Share with the service account email for full access
        spreadsheet.share(SERVICE_ACCOUNT_INFO['client_email'], perm_type='user', role='writer')
    
    return spreadsheet

def get_worksheet():
    """Get or create the worksheet"""
    spreadsheet = get_or_create_spreadsheet()
    if not spreadsheet:
        return None
    
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        # Create worksheet with headers
        worksheet = spreadsheet.add_worksheet(WORKSHEET_NAME, rows=1000, cols=4)
        worksheet.append_row(["German", "English", "DateAdded", "DateObj"])
    
    return worksheet

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
    """Load words from Google Sheets"""
    worksheet = get_worksheet()
    if not worksheet:
        return {}
    
    existing_words = {}
    try:
        records = worksheet.get_all_records()
        for row in records:
            if not row.get('German'):
                continue
            german = row['German']
            english = row.get('English', '')
            date_added = row.get('DateAdded', '')
            date_obj_str = row.get('DateObj', '')
            
            try:
                date_obj = datetime.strptime(date_obj_str, "%Y-%m-%d %H:%M:%S") if date_obj_str else datetime.now()
            except:
                date_obj = datetime.now()
            
            existing_words[german] = {
                'English': english,
                'DateAdded': date_added,
                'DateObj': date_obj
            }
    except Exception as e:
        st.error(f"Error loading words: {e}")
    
    return existing_words

def save_word_pairs(pairs):
    """Save word pairs to Google Sheets"""
    worksheet = get_worksheet()
    if not worksheet:
        return []
    
    existing_words = load_existing_words()
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
    
    # Append new entries to Google Sheets
    for entry in new_entries:
        worksheet.append_row([
            entry['German'],
            entry['English'],
            entry['DateAdded'],
            entry['DateObj']
        ])
    
    return new_entries

def read_csv_data():
    """Read all data from Google Sheets"""
    worksheet = get_worksheet()
    if not worksheet:
        return []
    
    data = []
    try:
        records = worksheet.get_all_records()
        for row in records:
            if not row.get('German'):
                continue
            
            date_obj_str = row.get('DateObj', '')
            try:
                date_obj = datetime.strptime(date_obj_str, "%Y-%m-%d %H:%M:%S") if date_obj_str else datetime.now()
            except:
                date_obj = datetime.now()
            
            data.append({
                'German': row['German'],
                'English': row.get('English', ''),
                'DateAdded': row.get('DateAdded', ''),
                'DateObj': date_obj
            })
    except Exception as e:
        st.error(f"Error reading data: {e}")
    
    return data

def search_words(words):
    """Search for words in Google Sheets"""
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
    """Delete word from Google Sheets"""
    worksheet = get_worksheet()
    if not worksheet:
        return False
    
    try:
        records = worksheet.get_all_records()
        updated_records = []
        deleted = False
        
        for i, row in enumerate(records, start=2):  # start=2 because of header row
            if (str(i-1) == str(word_or_index) or 
                clean_word(row.get('German', '')) == clean_word(word_or_index) or 
                clean_word(row.get('English', '')) == clean_word(word_or_index)):
                deleted = True
                continue
            updated_records.append(row)
        
        if deleted:
            # Clear worksheet and rewrite all records except deleted one
            worksheet.clear()
            worksheet.append_row(["German", "English", "DateAdded", "DateObj"])
            for record in updated_records:
                worksheet.append_row([
                    record.get('German', ''),
                    record.get('English', ''),
                    record.get('DateAdded', ''),
                    record.get('DateObj', '')
                ])
        
        return deleted
    except Exception as e:
        st.error(f"Error deleting word: {e}")
        return False

def edit_word_in_csv(search_word, new_german, new_english):
    """Edit word in Google Sheets"""
    worksheet = get_worksheet()
    if not worksheet:
        return False
    
    try:
        records = worksheet.get_all_records()
        edited = False
        
        for i, row in enumerate(records, start=2):  # start=2 because of header row
            if clean_word(row.get('German', '')) == clean_word(search_word):
                if new_german:
                    worksheet.update_cell(i, 1, clean_word(new_german))
                if new_english:
                    worksheet.update_cell(i, 2, clean_word(new_english))
                edited = True
                break
        
        return edited
    except Exception as e:
        st.error(f"Error editing word: {e}")
        return False

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
        st.success(f"✅ Successfully saved {len(new_entries)} new word pair(s) to Google Sheets!")
        show_new_words()
    else:
        st.info("No new words were added (they might already exist).")

def delete_words_action(delete_text):
    if not delete_text.strip():
        st.error("⚠️ Please enter a German/English word or row number to delete.")
        return
    
    deleted = delete_word_from_csv(delete_text)
    if deleted:
        st.success(f"✅ '{delete_text}' deleted successfully from Google Sheets!")
        show_all_words()
    else:
        st.error(f"❌ '{delete_text}' not found in Google Sheets.")

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
            st.success(f"✅ '{edit_text}' edited successfully in Google Sheets!")
            show_all_words()
        else:
            st.error(f"❌ '{edit_text}' not found in Google Sheets.")

# ---------- Streamlit App Layout ----------

def main():
    st.set_page_config(
        page_title="German Words Manager - Google Sheets",
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
    
    st.title("🇩🇪 German Words Manager - Google Sheets")
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
        if st.button("💾 Save Words", use_container_width=True):
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
        if st.button("🔍 Find Words", use_container_width=True):
            find_words(search_text)
    
    with col2:
        if st.button("📋 Show All Words", use_container_width=True):
            show_all_words()
    
    with col3:
        if st.button("🆕 Show New Words", use_container_width=True):
            show_new_words()
    
    with col4:
        if st.button("🗑️ Delete Word", use_container_width=True):
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
        st.header("ℹ️ Information")
        st.markdown("""
        **How to use:**
        - **Add words**: Enter German-English pairs separated by spaces or commas
        - **Search**: Enter one or more German words to search
        - **Edit**: Enter a German word, then provide new values
        - **Delete**: Enter a German word or row number to delete
        
        **Database:**
        - Google Sheets (Cloud Storage)
        - Real-time updates
        - Automatic backup
        """)
        
        # Statistics
        try:
            data = read_csv_data()
            st.metric("Total Words in Google Sheets", len(data))
            st.metric("New This Session", len(st.session_state.session_new_words))
        except:
            st.warning("Could not connect to Google Sheets")

if __name__ == "__main__":
    main()
