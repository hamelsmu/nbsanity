import tempfile, hashlib, shutil, json
import requests
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from fastcore.utils import run, mkdir
from fastcore.net import urlsave
import urllib.error
from rjsmin import jsmin

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def gist_raw(gist_url):
    # Extract gist ID from URL
    gist_id = gist_url.split('/')[-1]
    
    # Get gist info from GitHub API
    api_url = f"https://api.github.com/gists/{gist_id}"
    response = requests.get(api_url)
    data = response.json()
    
    # Check if 'files' or 'raw_url' is missing and raise HTTPError
    if 'files' not in data or not data['files']:
        raise urllib.error.HTTPError(api_url, 404, "No files found in the gist", None, None)
    
    raw_url = list(data['files'].values())[0].get('raw_url')
    if not raw_url:
        raise urllib.error.HTTPError(api_url, 404, "No raw_url found for the file", None, None)
    
    return raw_url

def git2raw(git_url: str): 
    if git_url.startswith('https://gist.github.com/'): return gist_raw(git_url)
    if git_url.startswith('https://gist.githubusercontent.com') and 'raw' in git_url: return git_url
    return git_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")


@app.get("/{file_path:path}")
async def render(file_path: str = ''):
    """Render the notebook or display instructions."""
    if not file_path:
        return HTMLResponse(content=generate_instruction_content())
    if file_path.startswith('gist/'): return await render_gist(file_path)
    if not file_path.endswith('.ipynb'):
        return HTMLResponse(content=generate_error_content(file_path))
    return await serve_notebook(file_path)


async def render_gist(gist_path: str=''):
    """Render a gist."""
    print("This is the gist path:", gist_path)
    gist_path = gist_path.lstrip('gist/')
    try: raw_gist_url = git2raw(f'https://gist.github.com/{gist_path}')
    except urllib.error.HTTPError as e: return handle_http_error(e, f'https://gist.github.com/{gist_path}')
    if not raw_gist_url.endswith('.ipynb'): return HTMLResponse(content=generate_error_content(gist_path, gist=True))
    return await serve_notebook(gist_path, gist=True)
    
NOTEBOOK_PATH="jakevdp/PythonDataScienceHandbook/blob/master/notebooks/01.07-Timing-and-Profiling.ipynb"
GIST_PATH="arfon/295dcd8636b7659fcbb9"

def generate_instruction_content():
    """Generate styled HTML content for instructions."""
    # Minified bookmarklet code
    js_code = """javascript:(function(e) {
    if ((!location.hostname.includes('github.com') || !location.href.endsWith('.ipynb')) && 
        !location.hostname.includes('gist.github.com')
    ) {
        alert('Please use this bookmarklet on a GitHub notebook URL (.ipynb file) or a Gist URL');
        e.preventDefault();
        return;
    }

    const newUrl = location.href.replace(location.hostname, 
                                    location.hostname.includes('gist.github.com') ? 'nbsanity.com/gist' : 'nbsanity.com');
    window.open(newUrl, '_blank');
})(event);"""

    bookmarklet_code = jsmin(js_code)

    return f'''
    <html>
    <head>
        <title>nbsanity</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css">
        <style>
            body {{
                font-family: Arial, sans-serif;
                padding: 20px;
                line-height: 1.6;
            }}
            h1, h2 {{
                color: #2E8B57;
            }}
            code {{
                background-color: #F5F5F5;
                padding: 2px 5px;
                border-radius: 3px;
            }}
            pre {{
                background-color: #F5F5F5;
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            a {{
                color: #4682B4;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .bookmarklet {{
                display: inline-block;
                padding: 8px 15px;
                background-color: #4682B4;
                color: white;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .bookmarklet:hover {{
                background-color: #3B6E8F;
                text-decoration: none;
            }}
            footer {{
                margin-top: 30px;
                border-top: 1px solid #ccc;
                padding-top: 10px;
                font-size: 0.8em;
                color: grey;
            }}
            footer a {{
                color: #4682B4;
            }}
            .method-section {{
                border: 1px solid #ddd;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
        </style>
    </head>
    <body>
        <h1>Notebook Renderer Instructions</h1>
        <p>Welcome to the Notebook Renderer! You can use this service in two ways:</p>

        <div class="method-section">
            <h2>Option 1: Bookmarklet (Recommended)</h2>
            <p>Drag this button to your bookmarks bar: <a class="bookmarklet" href="{bookmarklet_code}">NBSanity Viewer</a></p>
            <p>Then, while viewing any .ipynb file on GitHub or Gist, click the bookmarklet to open it in NBSanity.</p>
            
            <details>
                <summary>View bookmarklet source code</summary>
                <pre><code>{js_code}</code></pre>
            </details>
        </div>

        <div class="method-section">
            <h2>Option 2: Manual URL Modification</h2>
            <ol>
                <li>Find the GitHub URL of the notebook or gist you wish to render.</li>
                <li>Modify the URL in your browser:</li>
                <ul>
                    <li><strong>For Notebooks in Repos:</strong> Replace <span style="color: red;"><code>github.com</code></span> with <span style="color: red;"><code>nbsanity.com</code></span>.</li>
                    <li><strong>For Gists:</strong> Replace <span style="color: red;"><code>gist.github.com</code></span> with <span style="color: red;"><code>nbsanity.com/gist</code></span>.</li>
                </ul>
            </ol>

            <h3>Examples:</h3>
            <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                <p><strong>Notebook URL: </strong><code>https://<span style="color: red;">github</span>.com/{NOTEBOOK_PATH}</code></p>
                <p>Modify it to: <code><a href="https://nbsanity.com/{NOTEBOOK_PATH}">https://<span style="color: red;">nbsanity</span>.com/{NOTEBOOK_PATH}</a></code></p>
            </div>
            <div style="border: 1px solid #ccc; padding: 10px;">
                <p><strong>Gist URL: </strong><code>https://<span style="color: red;">gist.github.com</span>/{GIST_PATH}</code></p>
                <p>Modify it to: <code><a href="https://nbsanity.com/gist/{GIST_PATH}">https://<span style="color: red;">nbsanity.com/gist</span>/{GIST_PATH}</a></code></p>
            </div>
        </div>
        <hr>
        <p><strong>Made by <a href="https://hamel.dev">Hamel Husain</a></strong></p>
    </body>
    </html>
    '''

def generate_error_content(file_path, gist=False):
    """Generate HTML content for errors."""
    back = f'<a href="https://github.com/{file_path}">Go back to GitHub</a>' if not gist else f'<a href="https://gist.github.com/{file_path}">Go back to Gist</a>'
    return f"""
    <html>
    <head><title>Error</title></head>
    <body>
    <p>{file_path} is not a notebook.</p>
    {back}
    </body>
    </html>
    """

async def serve_notebook(file_path, gist=False):
    """Fetch, render, and serve the notebook."""
    with tempfile.TemporaryDirectory() as d:
        full_url = 'https://github.com/' + file_path if not gist else 'https://gist.github.com/' + file_path
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
            run(f'quarto render {nm} --no-execute --to html -M subtitle:"Rendered from:  {full_url}" --metadata-file nb.yml')
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
