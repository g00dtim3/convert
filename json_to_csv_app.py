import streamlit as st
import pandas as pd
import json
from io import StringIO
import time
import tempfile
import os

def flatten_json(data, parent_key='', sep='_'):
    """
    Flatten nested JSON objects
    """
    items = []
    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(flatten_json(item, f"{new_key}{sep}{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}{sep}{i}", item))
            else:
                items.append((new_key, v))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, dict):
                items.extend(flatten_json(item, f"{parent_key}{sep}{i}", sep=sep).items())
            else:
                items.append((f"{parent_key}{sep}{i}", item))
    else:
        items.append((parent_key, data))
    
    return dict(items)

def json_to_csv(json_data, flatten_nested=True, normalize_data=True):
    """
    Convert JSON data to CSV format
    """
    try:
        # Parse JSON if it's a string
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        # Handle different JSON structures
        if isinstance(data, list):
            # JSON array of objects
            if flatten_nested:
                flattened_data = []
                for item in data:
                    if isinstance(item, dict):
                        flattened_data.append(flatten_json(item))
                    else:
                        flattened_data.append({"value": item})
                df = pd.DataFrame(flattened_data)
            else:
                df = pd.json_normalize(data) if normalize_data else pd.DataFrame(data)
        
        elif isinstance(data, dict):
            # Single JSON object
            if flatten_nested:
                flattened_data = flatten_json(data)
                df = pd.DataFrame([flattened_data])
            else:
                df = pd.json_normalize([data]) if normalize_data else pd.DataFrame([data])
        
        else:
            # Single value
            df = pd.DataFrame({"value": [data]})
        
        return df
    
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error converting JSON to CSV: {str(e)}")
        return None

def create_download_link(df, filename="converted_data.csv"):
    """
    Create a more reliable download mechanism
    """
    try:
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        # Create a simple HTML download link
        import base64
        b64 = base64.b64encode(csv_data.encode()).decode()
        
        download_link = f'''
        <div style="margin: 10px 0;">
            <a href="data:text/csv;base64,{b64}" 
               download="{filename}"
               style="background-color: #4CAF50; color: white; padding: 10px 20px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                💾 Download CSV File
            </a>
        </div>
        '''
        
        return download_link, csv_data
    except Exception as e:
        st.error(f"Error creating download link: {str(e)}")
        return None, None

def main():
    st.set_page_config(
        page_title="JSON to CSV Converter",
        page_icon="🔄",
        layout="wide"
    )
    
    st.title("🔄 JSON to CSV Converter")
    st.markdown("Convert your JSON data to CSV format easily!")
    
    # Sidebar for options
    st.sidebar.header("⚙️ Conversion Options")
    flatten_nested = st.sidebar.checkbox("Flatten nested objects", value=True)
    normalize_data = st.sidebar.checkbox("Normalize data structure", value=True)
    
    # Main content in columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📥 Input JSON")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Paste JSON", "Upload JSON file"],
            horizontal=True
        )
        
        json_input = ""
        
        if input_method == "Paste JSON":
            json_input = st.text_area(
                "Paste your JSON data here:",
                height=300,
                placeholder='{"name": "John", "age": 30, "city": "New York"}'
            )
            
        else:  # Upload file
            uploaded_file = st.file_uploader(
                "Choose a JSON file",
                type="json",
                help="Upload a .json file"
            )
            
            if uploaded_file is not None:
                json_input = str(uploaded_file.read(), "utf-8")
                st.success(f"File '{uploaded_file.name}' loaded successfully!")
        
        # Example data button
        if st.button("📋 Load Example Data"):
            example_data = {
                "users": [
                    {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "address": {
                            "street": "123 Main St",
                            "city": "New York",
                            "zipcode": "10001"
                        },
                        "hobbies": ["reading", "swimming"]
                    },
                    {
                        "id": 2,
                        "name": "Jane Smith",
                        "email": "jane@example.com",
                        "address": {
                            "street": "456 Oak Ave",
                            "city": "Los Angeles",
                            "zipcode": "90210"
                        },
                        "hobbies": ["hiking", "cooking", "photography"]
                    }
                ]
            }
            st.session_state.json_input = json.dumps(example_data, indent=2)
        
        # Use session state for json_input to prevent rerun issues
        if 'json_input' not in st.session_state:
            st.session_state.json_input = json_input
        
        if st.session_state.json_input != json_input:
            st.session_state.json_input = json_input
    
    with col2:
        st.header("📤 CSV Output")
        
        if st.session_state.json_input or json_input:
            current_json = st.session_state.json_input or json_input
            
            # Add a progress indicator for large files
            with st.spinner("Converting JSON to CSV..."):
                # Convert JSON to CSV
                df = json_to_csv(current_json, flatten_nested, normalize_data)
            
            if df is not None:
                st.success(f"✅ Conversion successful! ({len(df)} rows, {len(df.columns)} columns)")
                
                # Display the dataframe
                st.dataframe(df, use_container_width=True)
                
                # Download button
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="💾 Download CSV",
                    data=csv_data,
                    file_name="converted_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Show CSV preview (limited for performance)
                with st.expander("🔍 CSV Preview"):
                    preview_data = csv_data[:2000] if len(csv_data) > 2000 else csv_data
                    if len(csv_data) > 2000:
                        preview_data += "\n... (truncated for display)"
                    st.code(preview_data, language="csv")
                
                # Show conversion info
                with st.expander("ℹ️ Conversion Info"):
                    st.write(f"**Rows:** {len(df)}")
                    st.write(f"**Columns:** {len(df.columns)}")
                    st.write(f"**Column Names:** {', '.join(df.columns.tolist())}")
        
        else:
            st.info("👆 Enter JSON data in the left panel to see the CSV output here.")
    
    # Instructions
    with st.expander("📖 How to Use"):
        st.markdown("""
        1. **Choose Input Method**: Either paste JSON directly or upload a JSON file
        2. **Configure Options**: Use the sidebar to customize conversion settings
        3. **Convert**: The CSV output will appear automatically
        4. **Download**: Click the download button to save your CSV file
        
        **Options Explained:**
        - **Flatten nested objects**: Converts nested JSON objects into flat columns (e.g., `address.city`)
        - **Normalize data structure**: Uses pandas' json_normalize for better handling of complex structures
        
        **Supported JSON Formats:**
        - Array of objects: `[{"key": "value"}, ...]`
        - Single object: `{"key": "value"}`
        - Nested objects and arrays
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("Built with ❤️ using Streamlit")

if __name__ == "__main__":
    main()
