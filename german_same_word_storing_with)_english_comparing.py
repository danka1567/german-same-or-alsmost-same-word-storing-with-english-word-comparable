import streamlit as st
import pandas as pd
import os
import csv
import re
from datetime import datetime
import time

file_name = r"C:\Users\un\Desktop\German Words\similar or partial GERMAN english.csv"

# Initialize session state variables
if 'session_new_words' not in st.session_state:
    st.session_state.session_new_words = []
if 'data' not in st.session_state:
    st.session_state.data = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []

# ---------- Helper Functions ----------

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
    tod = get_time_of_day(past_time.hour, past_time.minute)
    return f"{ago} | {tod}"

def parse_dateadded_to_datetime(date_str):
    try:
        parts = date_str.split(":")
        date_part = parts[0].strip()
        time_part = parts[1].strip().split()[0]
        am_pm = parts[1].strip().split()[1]
        day, month_str, year = date_part.split()
        months = ["jano","febo","maro","apro","maio","juno","julo","augo","sepo","octo","nove","deco"]
        month = months.index(month_str) + 1
        hour, minute = map(int, time_part.split(":"))
        if am_pm.upper() == "PM" and hour != 12:
            hour += 12
        if am_pm.upper() == "AM" and hour == 12:
            hour = 0
        return datetime(int(year), month, int(day), hour, minute)
    except:
        return datetime.now()

def load_existing_words():
    if not os.path.exists(file_name):
        return {}
    existing_words = {}
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            german = row.get('German') or row.get('Word')
            english = row.get('English', "")
            if not german:
                continue
            if 'DateObj' in row and row['DateObj']:
                dt = datetime.strptime(row['DateObj'], "%Y-%m-%d %H:%M:%S")
            else:
                dt = parse_dateadded_to_datetime(row['DateAdded'])
            existing_words[german] = {'English': english, 'DateAdded': row['DateAdded'], 'DateObj': dt}
    return existing_words

def remove_duplicate_german_rows():
    if not os.path.exists(file_name):
        return
    seen = set()
    unique_rows = []
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            g = row.get('German')
            if g and g not in seen:
                seen.add(g)
                unique_rows.append(row)
    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['German', 'English', 'DateAdded', 'DateObj']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_rows)

def save_word_pairs(pairs):
    existing_words = load_existing_words()
    new_entries = []
    for german, english in pairs:
        g_clean = clean_word(german.strip())
        e_clean = clean_word(english.strip())
        if g_clean and e_clean and g_clean not in existing_words:
            timestamp_str, dt_obj = custom_timestamp()
            entry = {'German': g_clean, 'English': e_clean, 'DateAdded': timestamp_str, 'DateObj': dt_obj}
            new_entries.append(entry)
            st.session_state.session_new_words.append(entry)
    if not new_entries:
        return []
    write_header = not os.path.exists(file_name)
    with open(file_name, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['German', 'English', 'DateAdded', 'DateObj']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for entry in new_entries:
            writer.writerow({
                'German': entry['German'],
                'English': entry['English'],
                'DateAdded': entry['DateAdded'],
                'DateObj': entry['DateObj'].strftime("%Y-%m-%d %H:%M:%S")
            })
    remove_duplicate_german_rows()
    return new_entries

def read_csv_data():
    if not os.path.exists(file_name):
        return []
    data = []
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dt = datetime.strptime(row['DateObj'], "%Y-%m-%d %H:%M:%S") if 'DateObj' in row and row['DateObj'] else parse_dateadded_to_datetime(row['DateAdded'])
            data.append({
                'German': row.get('German') or row.get('Word'),
                'English': row.get('English', ''),
                'DateAdded': row['DateAdded'],
                'DateObj': dt
            })
    return data

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
                results.append({'German': clean, 'English': '', 'DateAdded': "Not Found", 'TimeAgo': ""})
    return results

def delete_word_from_csv(word_or_index):
    if not os.path.exists(file_name):
        return False
    rows = []
    deleted = False
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        for i, row in enumerate(reader, start=1):
            if (str(i) == str(word_or_index)) or (clean_word(row['German']) == clean_word(word_or_index)) or (clean_word(row['English']) == clean_word(word_or_index)):
                deleted = True
                continue
            rows.append(row)
    if deleted:
        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['German', 'English', 'DateAdded', 'DateObj']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    return deleted

def edit_word_in_csv(search_word, new_german, new_english):
    if not os.path.exists(file_name):
        return False
    rows = []
    edited = False
    with open(file_name, newline='', encoding='utf-8') as csvfile:
        reader = list(csv.DictReader(csvfile))
        for row in reader:
            if clean_word(row['German']) == clean_word(search_word):
                if new_german:
                    row['German'] = clean_word(new_german)
                if new_english:
                    row['English'] = clean_word(new_english)
                edited = True
            rows.append(row)
    if edited:
        remove_duplicate_german_rows()
        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['German', 'English', 'DateAdded', 'DateObj']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
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
        st.success(f"✅ Successfully saved {len(new_entries)} new word pair(s)!")
        show_new_words()
    else:
        st.info("No new words were added (they might already exist).")

def delete_words_action(delete_text):
    if not delete_text.strip():
        st.error("⚠️ Please enter a German/English word or row number to delete.")
        return
    
    deleted = delete_word_from_csv(delete_text)
    if deleted:
        st.success(f"✅ '{delete_text}' deleted successfully!")
        show_all_words()
    else:
        st.error(f"❌ '{delete_text}' not found in CSV file.")

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
            st.success(f"✅ '{edit_text}' edited successfully!")
            show_all_words()
        else:
            st.error(f"❌ '{edit_text}' not found in CSV file.")

# ---------- Streamlit App Layout ----------

def main():
    st.set_page_config(
        page_title="Unique German Words Manager",
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
    
    st.title("🇩🇪 Unique German Words Manager")
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
        
        **File location:**
        ```python
        {file_name}
        ```
        """.format(file_name=file_name))
        
        # Statistics
        if os.path.exists(file_name):
            data = read_csv_data()
            st.metric("Total Words", len(data))
            st.metric("New This Session", len(st.session_state.session_new_words))
        else:
            st.warning("CSV file does not exist yet.")

if __name__ == "__main__":
    main()
