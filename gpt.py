import os
import openai
import textwrap
import json
import shutil

# Load the key from key.json
with open('key.json', 'r') as file:
    key = json.load(file)['OPENAI_KEY']

print("OpenAI key loaded.")

# Set the OpenAI API key
openai.api_key = key

# Initialize an empty string to store the combined results
combined_results = ""

def chunk_text(text, chunk_size):
    words = text.split(' ')
    chunks = []
    current_chunk = []

    for word in words:
        if len(current_chunk) < chunk_size:
            current_chunk.append(word)
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]

    chunks.append(' '.join(current_chunk))  # append last chunk

    return chunks

def read_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()

def summarize(text, path):
    global combined_results
    refined_file_path = os.path.join(path, 'refined.txt')
    if not os.path.isfile(refined_file_path):
        chunks = chunk_text(text, 1600)
        # Loop through each chunk
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1} of {len(chunks)}...")
            
            # Send the chunk to GPT-4
            completion = openai.ChatCompletion.create(
                model= "gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that reformats a transcription of a conversation into a more readable format, deleting the parts that are not relevant to the point. you divide it into paragraphs and fixes mistakes."},
                    {"role": "user", "content": read_file('examples/input_2.txt')},
                    {"role": "assistant", "content": read_file('examples/output_2.txt')},
                    {"role": "user", "content": read_file('examples/input_3.txt')},
                    {"role": "assistant", "content": read_file('examples/output_3.txt')},
                    {"role": "user", "content": chunk}
                ],
                temperature=0,
                max_tokens=3096
            )

            # Append the result to the combined_results string
            combined_results += completion.choices[0].message['content']

        print("All chunks processed. Writing to temporary file...")

        # # Create a temporary directory
        # os.makedirs('temporary', exist_ok=True)

        # Write the combined results to a file
        with open(os.path.join(path, 'refined.txt'), 'w', encoding='utf-8') as file:
            file.write(combined_results)

        print("Temporary file written.")
    else:
        print(f"File {refined_file_path} already exists.")


def rename_directory(old_dir_path, new_dir_name):
    # Make sure the old directory exists
    if not os.path.isdir(old_dir_path):
        print(f"Directory {old_dir_path} does not exist.")
        return old_dir_path

    # Split the old directory path into a parent directory and the old directory name
    parent_dir, old_dir_name = os.path.split(old_dir_path)

    # Create a new directory path with the same parent directory but a new directory name
    new_dir_path = os.path.join(parent_dir, new_dir_name)

    # Make sure the new directory does not exist
    if os.path.exists(new_dir_path):
        print(f"Directory or file {new_dir_path} already exists.")
        return old_dir_path

    # Rename the old directory to the new directory
    os.rename(old_dir_path, new_dir_path)

    print(f"Renamed directory {old_dir_path} to {new_dir_path}.")
    
    return new_dir_path 


def create_json(path):
    json_file = os.path.join(path, 'key_info.json')
    # Check if refined.txt file exists
    if not os.path.isfile(json_file):
        print("Processing entire transcript...")
        # Send the whole processed text to GPT-4 again
        completion = openai.ChatCompletion.create(
            model= "gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": "You are an assistant that extracts key information from a text and presents it in a structured format"},
                {"role": "user", "content": read_file('examples/input_0.txt')},
                {"role": "assistant", "content": read_file('examples/output_0.txt')},
                {"role": "user", "content": read_file('examples/input_1.txt')},
                {"role": "assistant", "content": read_file('examples/output_1.txt')},
                {"role": "user", "content": read_file(os.path.join(path, 'refined.txt'))} # Assumes combined_results was written to this file
            ],
            temperature=0,
            max_tokens=3000
        )

        # Extract the key information from the completion
        key_info = completion.choices[0].message['content']
        print(key_info)

        # Convert the key information to a dictionary
        if key_info:
            key_info_dict = json.loads(key_info)
        else:
            print(f"No data found in key_info at {path}")

        print("Writing key information to file...")
        # Write the key information to a file
        with open(f'{path}/key_info.json', 'w', encoding='utf-8') as file:
            json.dump(key_info_dict, file, ensure_ascii=False, indent=4)

        print("Key information written to file. All tasks completed.")

    else:
      print(f"File {json_file} already exists.")

def rename(path):
    try:
        # check if the path is valid
        if not os.path.isdir(path):
            print(f"{path} is not a valid directory.")
            return

        # read the 'key_info.json' file and retrieve the 'name' field
        with open(os.path.join(path, 'key_info.json'), 'r') as f:
            key_info_dict = json.load(f)
            if 'name' not in key_info_dict:
                print("name field is not found in key_info.json")
                return

        # Get the name from the key information
        new_name = key_info_dict['name']

        # Rename the directory
        parent_dir = os.path.dirname(path)
        new_dir_path = os.path.join(parent_dir, new_name)
        
        if not os.path.exists(new_dir_path):
            os.rename(path, new_dir_path)
            print(f"Directory has been renamed to {new_name}")
        else:
            print(f"Cannot rename the directory to {new_name} as it already exists.")

    except FileNotFoundError:
        print(f"key_info.json file or directory not found at {path}")
    except Exception as e:
        print(f"An error occurred: {e}")


def process_text(path, text):
    summarize(text, path)
    create_json(path)
    rename(path)

def process_all_subfolders(parent_folder):
    # For each subdirectory in the parent folder
    for root, dirs, files in os.walk(parent_folder):
        for dir in dirs:
            # Construct the full directory path
            full_dir_path = os.path.join(root, dir)
            
            # Construct the full file path
            full_file_path = os.path.join(full_dir_path, 'full_text.txt')
            
            # If the file exists
            if os.path.isfile(full_file_path):
                # Read the file
                print(f"Processing file at {full_file_path}...")
                text = read_file(full_file_path)
                
                # Process the text
                process_text(full_dir_path, text)
            else:
                print(f"No 'full_text.txt' in {full_dir_path}. Skipping...")


# Load the text
path = "ff"
print("Loading text from file...")
text = read_file(os.path.join(path, 'full_text.txt'))

# process_text(path, text)

# # Call the functions
# summarize(text, path)
# process_text(path, text)
process_all_subfolders("D:\\Videos\\Trans\\HVM")
