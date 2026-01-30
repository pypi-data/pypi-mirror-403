from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def generate_stack(context: dict, is_dockerized: bool = True):
    """
    Generates a cloud-init startup script from a Jinja2 template.

    Args:
        context: A dictionary containing information for rendering the template,
                 e.g., {'domain': 'example.com', 'email': 'user@example.com'}
        is_dockerized: Whether to setup Docker and Docker Compose (default: True)
    """
    # Path to the templates directory
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))

    template = env.get_template("cloud-init.sh.j2")

    # The context will contain all necessary variables for the template.
    # Pass is_dockerized to the template for conditional setup
    render_context = {**context, "is_dockerized": is_dockerized}
    script = template.render(render_context)

    return script
