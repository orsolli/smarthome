import subprocess
import tempfile
import os

from code2flow import code2flow

dot_file = "code-flow.dot"

def read(input_file):
    with open(input_file, 'r') as file:
        content = file.read()
    return content

def get_dot(code_path):
    #with tempfile.NamedTemporaryFile(delete=True, suffix=".dot") as temp_file:
    #    temp_file_path = temp_file.name
    code2flow(code_path, dot_file, hide_legend=False, exclude_namespaces=["generate_dependency_graph"])
    dot_content = read(dot_file)

    return dot_content

def generate_graph():
    project_dir = "."
    output_md = "FLOW.md"

    try:
        from dot2mermaid import DotParser
    
        print(f"Converting DOT to Mermaid...")
        parser = DotParser(get_dot(project_dir))
        colors = {
            'regular': '#555555',
            'trunk': '#AA5555',
            'leaf': '#5555FF'
        }
        markdown_content = parser.to_mermaid(colors=colors)
        parser.add_to_markdown(output_md, markdown_content)
    except Exception as e:
        print(f"Error converting dot to mermaid: {e}")
        return

    print("Dependency graph generation complete.")
    print(f"Mermaid diagram: {output_md}")

if __name__ == "__main__":
    generate_graph()
