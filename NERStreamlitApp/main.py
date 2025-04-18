import streamlit as st
import pandas as pd
import spacy
from spacy import displacy

# Set up the Streamlit app
st.set_page_config(page_title="Custom NER App", layout="wide") # Set the page title and layout

st.title("🧠 Named Entity Recognition (NER) App with spaCy")
st.write("Upload or paste your text, define custom entity patterns, and see the named entities highlighted below!") # App description

# Initialize session state for text input and entity list
if "entity_list" not in st.session_state: # Check if entity_list is in session state
    st.session_state.entity_list = []

# Example texts for demonstration
example_1 = "Taylor Swift's *The Eras Tour* grossed over $1 billion in 2023." 
example_2 = "Frodo Baggins left the Shire with the One Ring to destroy it in Mount Doom."
example_3 = "Lionel Messi scored a hat-trick in the World Cup final against France."

# Buttons to load example text
st.subheader("📄 Try Example Texts")
col1, col2, col3 = st.columns(3) # Create three columns for buttons
with col1: # Load example text for Taylor Swift
    if st.button("🎤 Taylor Swift"):
        st.session_state["text_input"] = example_1
with col2: # Load example text for Lord of the Rings
    if st.button("🧙‍♂️ Lord of the Rings"):
        st.session_state["text_input"] = example_2
with col3: # Load example text for Soccer
    if st.button("⚽ Soccer"):
        st.session_state["text_input"] = example_3

# Text input area
st.header("✍️ Enter Text")
text = st.text_area("Paste or write your text here:", value=st.session_state.get("text_input", ""), height=200)

# Upload .txt file
uploaded_file = st.file_uploader("📂 Or upload a .txt file", type=["txt"])
if uploaded_file is not None: # Check if a file is uploaded
    uploaded_text = uploaded_file.read().decode("utf-8") # Read the file content
    st.session_state["text_input"] = uploaded_text # Store the text in session state
    st.success("✅ Text file uploaded and loaded!")

# Sidebar for custom pattern input
st.sidebar.header("🧩 Add a Custom Entity")

words = text.split() if text else [] # Split text into words for selection
with st.sidebar.form("pattern_form"): # Create a form in the sidebar
    label = st.text_input("Entity Label (e.g., CHARACTER, EVENT)").upper() # Input for entity label
    selected_words = st.multiselect("Select words to match", options=words) # Multi-select for words
    submit_btn = st.form_submit_button("➕ Add Pattern") # Submit button for adding patterns

    if submit_btn: # Check if the form is submitted
        if label and selected_words: # Check if label and words are provided
            pattern = [{"TEXT": word} for word in selected_words] # Create pattern for entity ruler
            st.session_state.entity_list.append({"label": label, "pattern": pattern}) # Append to entity list
            st.sidebar.success(f"Added pattern for: {label}") # Success message
        else: # Check if label and words are provided
            st.sidebar.warning("Please enter a label and select words.")

# Display saved patterns
if st.session_state.entity_list:
    st.sidebar.markdown("### 📋 Saved Patterns")
    pattern_display = [
        {
            "Label": ent["label"],
            "Pattern": " ".join([token["TEXT"] for token in ent["pattern"]]) # Join tokens in pattern
        }
        for ent in st.session_state.entity_list 
    ]
    st.sidebar.dataframe(pd.DataFrame(pattern_display)) # Display saved patterns
# Clear patterns button
if st.sidebar.button("🗑️ Clear Patterns"):
    st.session_state.entity_list = [] # Clear the entity list
    st.sidebar.success("Cleared all patterns!") # Success message

# Entity recognition
st.header("🔍 Entity Recognition Results")

if text:
    nlp = spacy.load("en_core_web_sm") # Load spaCy model
    try:
        ruler = nlp.get_pipe("entity_ruler") # Try to get existing entity ruler
    except:
        ruler = nlp.add_pipe("entity_ruler", before="ner") # Add entity ruler if it doesn't exist
    ruler.add_patterns(st.session_state.entity_list) # Add custom patterns to the entity ruler

    doc = nlp(text) # Process the text with spaCy

    if doc.ents: # Check if any entities were recognized
        st.subheader("🖼️ Visual Entity Highlighting")
        html = displacy.render(doc, style="ent", page=True)
        st.components.v1.html(html, height=500, scrolling=True)
    else:
        st.info("No entities were recognized.")
else:
    st.info("Please enter some text to see recognized entities.") # Info message if no text is entered

# Footer
st.markdown("---")
st.markdown("Built with [spaCy](https://spacy.io) and [Streamlit](https://streamlit.io) 💬")
