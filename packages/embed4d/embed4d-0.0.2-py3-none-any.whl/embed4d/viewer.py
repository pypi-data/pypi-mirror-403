import base64
import os

from embed4d.utilities import file_to_base64

# ----------------- Configuration -----------------
HTML_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "index.html")


# ----------------- Helper Functions -----------------
def get_template_html() -> str:
    """Load and return the raw HTML template as a string."""
    if not os.path.exists(HTML_TEMPLATE_PATH):
        return ""
    with open(HTML_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def get_viewer_html(glb_base64: str) -> str:
    """Return the HTML viewer page with the base64 placeholder replaced."""
    html_template = get_template_html()
    return html_template.replace("{{GLB_BASE64}}", glb_base64 or "")


def iframe_srcdoc_html(glb_base64: str, height=500) -> str:
    """Return an iframe HTML embedding the viewer page via srcdoc."""
    html_content = get_viewer_html(glb_base64)
    escaped_html = html_content.replace('"', "&quot;")
    return (
        f'<iframe srcdoc="{escaped_html}" width="100%" height="{height}px" '
        'style="border:none;border-radius:12px;"></iframe>'
    )


# Backwards-compatible alias
def get_glb_html(glb_base64: str, height=500):
    """Return an iframe HTML embedding the GLB file as base64."""
    if not os.path.exists(HTML_TEMPLATE_PATH):
        return '<p style="color:red;">HTML template not found!</p>'
    return iframe_srcdoc_html(glb_base64=glb_base64, height=height)


def model3d_viewer(file_path, height=500):
    """Function to render a GLB file in HTML."""
    return get_glb_html(file_to_base64(file_path), height=height)


def open_viewer_webview(
    file_path=None, title="3D Model Viewer", width=1200, height=800
):
    """
    Open the 3D model viewer in a native webview window.

    Args:
        file_path: Optional path to a GLB/GLTF file to load.
            If None, shows the upload interface.
        title: Window title (default: "3D Model Viewer")
        width: Window width in pixels (default: 1200)
        height: Window height in pixels (default: 800)

    Example:
        >>> from embed4d import open_viewer_webview
        >>> open_viewer_webview("model.glb")
    """
    try:
        import webview
    except ImportError as exc:
        raise ImportError(
            "pywebview is required for webview functionality. "
            "Install it with: pip install pywebview"
        ) from exc

    # JS API class for fullscreen support in webview
    class WebviewAPI:
        def __init__(self):
            self.window = None

        def set_window(self, window):
            """Set the window reference after creation."""
            self.window = window

        def toggle_fullscreen(self):
            """Toggle fullscreen mode for the webview window."""
            if self.window is None:
                return False

            try:
                # Prefer toggle_fullscreen() method (works on macOS)
                if hasattr(self.window, "toggle_fullscreen"):
                    self.window.toggle_fullscreen()
                    if hasattr(self.window, "fullscreen"):
                        return bool(self.window.fullscreen)
                    return True

                # Fallback: set fullscreen property directly
                if hasattr(self.window, "fullscreen"):
                    current_state = bool(self.window.fullscreen)
                    new_state = not current_state
                    self.window.fullscreen = new_state
                    return new_state

                return False
            except (AttributeError, RuntimeError, TypeError, ValueError):
                return False

    # Get the HTML content
    if file_path:
        glb_base64 = file_to_base64(file_path)
        html_content = get_viewer_html(glb_base64)
    else:
        html_content = get_viewer_html("")

    # Create JS API instance and window
    api = WebviewAPI()
    window = webview.create_window(
        title, html=html_content, width=width, height=height, js_api=api
    )
    api.set_window(window)

    # Start webview (this blocks until window is closed)
    webview.start(debug=False)


def _prepare_html_for_notebook(html_content: str, height: int) -> str:
    """
    Prepare HTML content for notebook display by fixing viewport heights and adding styles.

    Args:
        html_content: The HTML content to modify
        height: Target height in pixels

    Returns:
        Modified HTML content suitable for notebook iframe display
    """
    height_px = f"{height}px"

    # Replace viewport height units with explicit pixel height
    import re

    # Replace in CSS (height: 100vh or height:100vh) but preserve base64 data
    modified = re.sub(r"height:\s*100vh", f"height: {height_px}", html_content)
    modified = re.sub(r"height:100vh", f"height:{height_px}", modified)
    modified = re.sub(r"\b100vh\b", height_px, modified)

    # Inject notebook-specific styles
    notebook_style = f"""<style id="notebook-override">
        html, body {{ margin: 0 !important; padding: 0 !important; overflow: hidden !important; height: {height_px} !important; width: 100% !important; }}
        .container {{ height: {height_px} !important; min-height: {height_px} !important; }}
        .viewer {{ height: {height_px} !important; min-height: {height_px} !important; }}
        #canvas-container {{ height: {height_px} !important; min-height: {height_px} !important; }}
    </style>"""

    # Insert styles right after <head> tag
    if "<head>" in modified:
        modified = modified.replace("<head>", f"<head>\n{notebook_style}", 1)
    else:
        # Fallback: prepend to document
        modified = notebook_style + modified

    return modified


def notebook_viewer(file_path=None, height=600):
    """
    Display a 3D GLB/GLTF model viewer in a Jupyter notebook.

    Args:
        file_path: Optional path to a GLB/GLTF file to load. If None, shows upload interface.
        height: Height of the viewer in pixels (default: 600)

    Returns:
        IPython.display.IFrame: IFrame object that displays the viewer in a notebook cell

    Example:
        >>> from embed4d import notebook_viewer
        >>> notebook_viewer("model.glb")
        >>> notebook_viewer("model.glb", height=800)
    """
    try:
        from IPython.display import IFrame
    except ImportError as exc:
        raise ImportError(
            "IPython is required for Jupyter notebook display. "
            "Install it with: pip install embed4d[ipython]"
        ) from exc

    # Get base64 encoded file content and generate HTML
    glb_base64 = file_to_base64(file_path) if file_path else ""
    html_content = get_viewer_html(glb_base64)

    # Prepare HTML for notebook display
    notebook_html = _prepare_html_for_notebook(html_content, height)

    # Convert HTML to data URI and use IFrame
    html_base64 = base64.b64encode(notebook_html.encode("utf-8")).decode("utf-8")
    data_uri = f"data:text/html;base64,{html_base64}"

    return IFrame(src=data_uri, width="100%", height=height)
