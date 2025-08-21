# Version 2025-08-03
import re
import os
import subprocess

def clean_and_convert_to_latex(input_md_filename):
    """
    A full pipeline script that:
    1. Cleans a Notion-exported Markdown file.
    2. Asks the user to select a LaTeX template.
    3. Converts the cleaned Markdown to a .tex file using Pandoc.

    All files are expected to be in the same directory as this script.

    Args:
        input_md_filename (str): The filename of the input Markdown file.
    """
    # --- Setup: Determine the script's directory ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"--- Running in: {script_dir} ---")

    input_md_file_path = os.path.join(script_dir, input_md_filename)

    # --- Step 1: Clean the Markdown file ---
    print(f"\n--- Step 1: Cleaning '{input_md_file_path}' ---")

    if not os.path.exists(input_md_file_path):
        print(f"Error: Input file not found at '{input_md_file_path}'")
        return

    try:
        with open(input_md_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    if not lines:
        print("Input file is empty. Aborting.")
        return

    # 1.1. Skip the first line if it's a redundant title
    content_lines = lines[1:] if lines[0].startswith('# ') else lines

    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    # 1.2. [FIXED] Remove duplicate image captions, accounting for blank lines
    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
    cleaned_lines = []
    i = 0
    while i < len(content_lines):
        current_line = content_lines[i]
        image_match = re.match(r'^\s*!\[(.*)\]\(.*\)\s*$', current_line)

        # Check for an image with a non-empty caption
        if image_match and image_match.group(1).strip():
            alt_text = image_match.group(1).strip()
            
            # Find the index of the next non-empty line
            next_line_index = i + 1
            while next_line_index < len(content_lines) and not content_lines[next_line_index].strip():
                next_line_index += 1 # Skip any blank lines
            
            # If we found a non-empty line and its content matches the caption...
            if next_line_index < len(content_lines) and content_lines[next_line_index].strip() == alt_text:
                # Keep the image line itself.
                cleaned_lines.append(current_line)
                # Add any blank lines that were between the image and the duplicate text.
                # This preserves formatting.
                cleaned_lines.extend(content_lines[i + 1:next_line_index])
                # And finally, skip the duplicate line by jumping the index past it.
                i = next_line_index + 1
                continue

        # Default case: The line is not an image with a duplicate caption.
        cleaned_lines.append(current_line)
        i += 1
    # --- --- --- End of fix --- --- --- ---

    # 1.3. Ask user if they want to remove bold formatting from headings
    print("\n--- Optional Cleaning Step ---")
    unbold_choice = ''
    while unbold_choice.lower() not in ['y', 'n']:
        unbold_choice = input("Do you want to remove bold formatting from headings (e.g., '### **Title**')? (y/n): ")

    if unbold_choice.lower() == 'y':
        heading_pattern = re.compile(r'^(#+\s+)\*\*(.*?)\*\*(.*)$')
        temp_lines = []
        for line in cleaned_lines:
            new_line = heading_pattern.sub(r'\1\2\3', line)
            temp_lines.append(new_line)
        cleaned_lines = temp_lines
        print("Bold formatting removed from headings.")

    # 1.4. Save the cleaned content to a new file in the script's directory
    base_name = os.path.splitext(input_md_filename)[0]
    cleaned_md_filename = f"{base_name}_cleaned.md"
    cleaned_md_file_path = os.path.join(script_dir, cleaned_md_filename) 
    try:
        with open(cleaned_md_file_path, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        print(f"\nSuccessfully saved cleaned content to '{cleaned_md_file_path}'")
    except Exception as e:
        print(f"Error writing cleaned file: {e}")
        return

    # --- --- --- --- --- ---
    # Step 2: Select a LaTeX Template
    # --- --- --- --- --- ---
    print("\n--- Step 2: Select a LaTeX Template ---")
    
    templates = [
        "Philips-Pandoc-LaTeX-Vorlage_WK1-Format.tex",
        "Philips-Pandoc-LaTeX-Vorlage-mit-Vorwort-und-Disclaimer.tex",
        "Philips-Pandoc-LaTeX-Vorlage.tex"
    ]

    print("Please choose a template for the Pandoc conversion:")
    for i, t in enumerate(templates):
        print(f"  {i+1}: {t}")

    chosen_template_path = None
    while not chosen_template_path:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(templates):
                chosen_template_filename = templates[choice - 1]
                chosen_template_path = os.path.join(script_dir, chosen_template_filename)
                
                if not os.path.exists(chosen_template_path):
                    print(f"\nError: Template file not found at '{chosen_template_path}'")
                    chosen_template_path = None
            else:
                print(f"Invalid number. Please enter a number between 1 and {len(templates)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # --- --- --- --- --- ---
    # Step 3: Convert to LaTeX using Pandoc
    # --- --- --- --- --- ---
    print("\n--- Step 3: Converting to LaTeX ---")
    output_tex_filename = f"{base_name}.tex"
    output_tex_file_path = os.path.join(script_dir, output_tex_filename)
    
    command = [
        'pandoc',
        cleaned_md_file_path,
        '-o', output_tex_file_path,
        '--template', chosen_template_path
    ]

    print(f"Running command: {' '.join(command)}")

    try:
        subprocess.run(command, check=True, text=True, encoding='utf-8')
        print(f"\n✅ Successfully converted '{cleaned_md_filename}' to '{output_tex_filename}'.")
    except FileNotFoundError:
        print("\n--- ERROR ---")
        print("Pandoc command not found. Please make sure Pandoc is installed and in your system's PATH.")
        print("Installation instructions: https://pandoc.org/installing.html")
    except subprocess.CalledProcessError as e:
        print(f"\n--- ERROR ---")
        print(f"Pandoc failed with exit code {e.returncode}.")
        if e.stderr:
             print("Error output:\n", e.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# --- --- --- --- --- ---
# How to use the script
# --- --- --- --- --- ---
# 1. Save this code as a Python file (e.g., `notion2latex.py`).
# 2. Make sure your input Markdown file (e.g., 'input.md') and your
#    .tex template files are in the SAME DIRECTORY as the script.
# 3. Run the script from your terminal: python3 notion2latex.py
if __name__ == "__main__":
    # The script will now look for the input file in its own directory.
    clean_and_convert_to_latex('input.md')