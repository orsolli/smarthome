import subprocess
import os

def generate_graph():
    project_dir = "."
    output_md = "FLOW.md"

    print(f"Converting DOT to Mermaid...")
    try:
        from dot2mermaid import DotParser, get_dot
    
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
