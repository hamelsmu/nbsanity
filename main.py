import tempfile, hashlib, shutil, json
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastcore.utils import run, mkdir
from fastcore.net import urlsave
import urllib.error

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def git2raw(git_url: str): 
    return git_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

@app.get("/{file_path:path}")
async def render(file_path: str = ''):
    """Render the notebook or display instructions."""
    if not file_path:
        return HTMLResponse(content=generate_instruction_content())
    if not file_path.endswith('.ipynb'):
        return HTMLResponse(content=generate_error_content(file_path))
    return await serve_notebook(file_path)

def generate_instruction_content():
    """Generate styled HTML content for instructions."""
    return '''
    <html>
    <head>
        <title>Instructions</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css">
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
                line-height: 1.6;
            }
            h1 {
                color: #2E8B57;
            }
            code {
                background-color: #F5F5F5;
                padding: 2px 5px;
                border-radius: 3px;
            }
            a {
                color: #4682B4;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            footer {
                margin-top: 30px;
                border-top: 1px solid #ccc;
                padding-top: 10px;
                font-size: 0.8em;  /* Make the font size smaller */
                color: grey;        /* Change the text color to grey */
            }
            footer a {
                color: #4682B4;
            }
        </style>
    </head>
    <body>
        <h1>Notebook Renderer Instructions</h1>
        <p>Welcome to the Notebook Renderer! Here's how to use this service:</p>
        <ol>
            <li>Find the GitHub URL of the notebook you wish to render.</li>
            <li>Replace <span style="color: red;"><code>github.com</code></span> in the URL with <span style="color: red;"><code>nbsanity.com</code></span> in your browser.</li>
        </ol>
        <p>For example:</p>
        <p>For the notebook URL:</p>
        <code>https://<span style="color: red;">github</span>.com/facebookresearch/llama-recipes/blob/main/examples/quickstart.ipynb</code>
        <p>Modify it to:</p>
        <code><a href="https://nbsanity.com/facebookresearch/llama-recipes/blob/main/examples/quickstart.ipynb">https://<span style="color: red;">nbsanity</span>.com/facebookresearch/llama-recipes/blob/main/examples/quickstart.ipynb</a></code>
        <footer>
            <p>Made by <a href="https://hamel.dev">Hamel</a>
        </footer>
    </body>
    </html>
    '''


def generate_error_content(file_path):
    """Generate HTML content for errors."""
    return f"""
    <html>
    <head><title>Error</title></head>
    <body>
    <p>{file_path} is not a notebook.</p>
    <a href="https://github.com/{file_path}">Go back to GitHub</a>
    </body>
    </html>
    """

async def serve_notebook(file_path):
    """Fetch, render, and serve the notebook."""
    with tempfile.TemporaryDirectory() as d:
        full_url = 'https://github.com/' + file_path
        try:
            nm = urlsave(git2raw(full_url), d)
        except urllib.error.HTTPError as e:
            return handle_http_error(e, full_url)
        
        hash_val = hashlib.md5(open(nm,'rb').read()).hexdigest()
        new_path = Path(f'static/{hash_val}')

        # Load the notebook and modify non-compliant Quarto comments
        with open(nm, 'r') as f:
            notebook_data = json.load(f)
            for cell in notebook_data['cells']:
                if cell['cell_type'] == 'code':
                    cell['source'] = escape_quarto_comments(cell['source'])
        
        # Save the modified notebook
        with open(nm, 'w') as f:
            json.dump(notebook_data, f)
        
        if not new_path.exists():
            run(f"quarto render {nm} --no-execute --to html")
            mkdir(new_path, exist_ok=True, overwrite=True)
            shutil.copytree(d, str(new_path), dirs_exist_ok=True)

        fname = nm.with_suffix('.html').name
        return RedirectResponse(f'/static/{hash_val}/{fname}')

def handle_http_error(e, full_url):
    """Handle HTTP errors during notebook fetch."""
    if e.code == 404:
        return HTMLResponse(content=f'<p>Error: The notebook {full_url} was not found on GitHub. Please check the path and try again.</p>')
    return HTMLResponse(content=f'<p>An error occurred while fetching the notebook {full_url}: {e}</p>')

def highlight_domain(text: str) -> str:
    """Highlights specific domains in the given text."""
    domains = ['nbsanity.com', 'github.com']
    for domain in domains:
        text = text.replace(domain, f'<span style="color: red;">{domain}</span>')
    return text

def escape_quarto_comments(lines):
    """Escape comments that don't match Quarto's directive format."""
    for idx, line in enumerate(lines):
        if line.strip().startswith('#|') and ':' not in line:
            lines[idx] = '#' + line
    return lines