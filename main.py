import hashlib, shutil, json, uuid
import requests, os
import nbformat
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse, JSONResponse
from fastcore.utils import run, mkdir, Path
from fastcore.net import urlsave
import urllib.error
from rjsmin import jsmin
from bs4 import BeautifulSoup as bs

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("assets/icon.png")

def gist_raw(gist_url):
    # Extract gist ID from URL
    gist_id = gist_url.split('/')[-1]
    
    api_url = f"https://api.github.com/gists/{gist_id}"
    headers = {'Cache-Control': 'no-store', 'Pragma': 'no-cache'}
    response = requests.get(api_url, headers=headers)
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


@app.get("/api/check-version/{hash_val}")
async def check_version(hash_val: str, url: str):
    """Check if there's a newer version of the notebook available"""
    try:
        # Add timestamp to URL to bust cache
        cache_buster = f"{'&' if '?' in url else '?'}_={uuid.uuid4()}"
        url_with_cache_buster = f"{git2raw(url)}{cache_buster}"
        
        # Enhanced no-cache headers
        headers = {
            'Cache-Control': 'no-store',
            'Pragma': 'no-cache',
            'Expires': '0',
        }
        
        nb = requests.get(url_with_cache_buster, headers=headers).content
        current_hash = hashlib.md5(nb).hexdigest()
        return JSONResponse({"hasUpdate": current_hash != hash_val})
    except Exception as e:
        return JSONResponse({"hasUpdate": False})

@app.get("/{file_path:path}")
async def render(file_path: str = ''):
    """Render the notebook or display instructions."""
    if not file_path:
        return HTMLResponse(content=generate_instruction_content())
    if os.path.normpath(file_path).startswith(('/', '..')):
        return HTMLResponse(content=generate_error_content(file_path))
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
    js_code = """javascript:(function(e) {{
if ((!location.hostname.includes('github.com') || !location.href.endsWith('.ipynb')) && 
    !location.hostname.includes('gist.github.com')
) {{
    alert('Please use this bookmarklet on a GitHub notebook URL (.ipynb file) or a Gist URL');
    e.preventDefault();
    return;
}}

const newUrl = location.href.replace(location.hostname, 
                                location.hostname.includes('gist.github.com') ? 'nbsanity.com/gist' : 'nbsanity.com');
window.open(newUrl, '_blank');
}})(event);"""

    bookmarklet_code = jsmin(js_code)

    return f'''
    <html>
    <head>
        <title>nbsanity</title>
        <meta property="og:title" content="nbsanity | Jupyter Notebook Viewer" />
        <meta property="og:description" content="A modern way to view public Jupyter notebooks on GitHub" />
        <meta property="og:image" content="https://nbsanity.com/assets/nbsanity.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:image" content="https://nbsanity.com/assets/nbsanity.png" />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:url" content="https://nbsanity.com" />
        <meta property="og:type" content="website" />
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
                padding: 0.5rem 1rem;
                background-color: #4a76d4;
                color: #ffffff !important;
                border: 1px solid #4a76d4;
                border-radius: 0.375rem;
                font-weight: 500;
                font-size: 0.875rem;
                text-decoration: none;
            }}

            .bookmarklet i {{
                color: #ffffff;
                margin-right: 0.5rem;
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
            .domain-highlight {{
                color: #dc2626;
                font-weight: 500;
            }}
            .source-link {{
                font-size: 0.8rem;
                color: #6b7280;
            }}
            
            .source-link a {{
                color: #4a76d4;
            }}
            
            .example-box code a {{
                color: inherit;  /* Keep the original text color for code links */
                text-decoration: none;
            }}
            
            .example-box code a:hover {{
                text-decoration: underline;
            }}
        </style>
    </head>
    <body>
        <h1>nbsanity: Render Notebooks On GitHub</h1>
        <p>Welcome to the Notebook Renderer! You can use this service in two ways:</p>

        <div class="method-section">
            <h2><i class="fas fa-bookmark"></i> Option 1: Bookmarklet</h2>
            <p>Drag this button to your bookmarks bar:</p>
            <p><a class="bookmarklet" href="{bookmarklet_code}"><img src="/assets/icon.png" style="height: 1em; margin-right: 0.5rem;">nbsanity</a></p>
            <p>While viewing any .ipynb file on GitHub or Gist, click the bookmarklet to open it in nbsanity.</p>
            <p class="source-link">View source code on <a href="https://github.com/hamelsmu/nbsanity/">GitHub</a></p>
        </div>

        <div class="method-section">
            <h2><i class="fas fa-link"></i> Option 2: Modify The URL</h2>
            <p>Modify any GitHub notebook URL to use nbsanity:</p>
            
            <div class="example-box">
                <h3>For Repository Notebooks:</h3>
                <p><strong>Original:</strong> <code><a href="https://github.com/{NOTEBOOK_PATH}"><span class="domain-highlight">github.com</span>/{NOTEBOOK_PATH}</a></code></p>
                <p><strong>Modified:</strong> <code><a href="https://nbsanity.com/{NOTEBOOK_PATH}"><span class="domain-highlight">nbsanity.com</span>/{NOTEBOOK_PATH}</a></code></p>
            </div>
            
            <div class="example-box">
                <h3>For Gists:</h3>
                <p><strong>Original:</strong> <code><a href="https://gist.github.com/{GIST_PATH}"><span class="domain-highlight">gist.github.com</span>/{GIST_PATH}</a></code></p>
                <p><strong>Modified:</strong> <code><a href="https://nbsanity.com/gist/{GIST_PATH}"><span class="domain-highlight">nbsanity.com</span>/gist/{GIST_PATH}</a></code></p>
            </div>
        </div>
        <hr>
        <p><strong>Made by <a href="https://hamel.dev">Hamel Husain</a></strong></p>
    </body>
    </html>
    '''

def update_meta(html_path: str|Path, 
                image_path:str,
                title:str,
                default_title: str = "nbsanity | Jupyter Notebook Viewer"):
    """Update the meta tags in the HTML file."""
    meta_tags=f"""<meta property="og:image" content="{image_path}">
<meta property="og:site_name" content="nbsanity">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:type" content="website">
<meta property="og:url" content="https://nbsanity.com">
<meta property="og:title" content="{title}">
<meta property="og:description" content="nbsanity: A modern way to view public Jupyter notebooks on GitHub">
<meta name="twitter:image" content="{image_path}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="nbsanity: A modern way to view public Jupyter notebooks on GitHub">
""".format(image_path=image_path, title=title)

    # Updated update checker JavaScript
    update_script = """
    <script>
    async function checkForUpdates() {
        const currentUrl = document.querySelector('a[href*="github.com"]').href;
        const currentPath = window.location.pathname;
        const hash = currentPath.split('/')[2];
        
        const response = await fetch(`/api/check-version/${hash}?url=${encodeURIComponent(currentUrl)}`, {
            cache: 'no-store'  // Prevent caching of the check-version request
        });
        const {hasUpdate} = await response.json();
        console.log('hasUpdate', hasUpdate)
        
        if (hasUpdate) {
            const existingBtn = document.getElementById('update-btn');
            if (existingBtn) return;
            
            const hostingDiv = document.getElementById('nbsanity-info');
            if (!hostingDiv) return;
            
            const btn = document.createElement('button');
            btn.id = 'update-btn';
            btn.innerHTML = '🔄 New Version Available';
            btn.style = `
                margin-left: 10px;
                padding: 2px 8px;
                background: #4a76d4;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
                vertical-align: middle;
            `;
            btn.onclick = () => {
                if (currentUrl.includes('gist.github.com')) {
                    window.location.href = currentUrl.replace('gist.github.com', 'nbsanity.com/gist');
                } else {
                    window.location.href = currentUrl.replace('github.com', 'nbsanity.com');
                }
            };
            const em = hostingDiv.querySelector('em');
            em.appendChild(btn);
        }
    }

    // Check on initial load
    document.addEventListener('DOMContentLoaded', checkForUpdates);
    
    // Check on page show (back/forward navigation)
    window.addEventListener('pageshow', (event) => {
        // Check if page is loaded from cache
        if (event.persisted) {
            checkForUpdates();
        }
    });
    </script>
    """

    doc = Path(html_path)
    soup = bs(doc.read_text(encoding='utf-8'), 'html.parser')
    head = soup.find('head')
    
    # Add meta tags
    new_html = bs(meta_tags, 'html.parser')
    for element in new_html:
        head.insert(0, element)
    
    # Add update script
    script_tag = bs(update_script, 'html.parser')
    head.append(script_tag)
    
    doc.write_text(str(soup), encoding='utf-8')


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

def escape_filename(filename):
    "Replace HTML-like characters and other problematic characters"
    invalid_chars = '<>:"/\\|?*%#&{}+=`@!^;[]()$'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
def process_nb_yml(notebook_path, full_url, hash_val):
    with open('nb.yml', 'r') as f: template = f.read()
    filled = template.replace('{{full_url}}', full_url).replace('{{image_path}}', f'https://nbsanity.com/static/{hash_val}/cover.png')
    output_path = os.path.join(notebook_path, 'nb.yml')
    with open(output_path, 'w') as f: f.write(filled)

def get_title(html_path: str|Path, default_title: str = "nbsanity | Jupyter Notebook Viewer"):
    "Update the title in the HTML file."
    doc = Path(html_path)
    soup = bs(doc.read_text(encoding='utf-8'), 'html.parser')
    return soup.title.string if soup.title else default_title

def fix_nb(nbpath):
    "Mutate notebook to right version for Quarto."
    nb = nbformat.read(nbpath, as_version=4)
    nbformat.write(nb, nbpath)

async def serve_notebook(file_path, gist=False):
    """Fetch, render, and serve the notebook."""
    d = Path('tmp_notebooks') / str(uuid.uuid4())
    d.mkdir(parents=True, exist_ok=True)
    full_url = 'https://github.com/' + file_path if not gist else 'https://gist.github.com/' + file_path
    try:
        nm = urlsave(git2raw(full_url), d)
        nm = nm.rename(nm.parent/escape_filename(nm.name))
        
        hash_val = hashlib.md5(open(nm,'rb').read()).hexdigest()
        new_path = Path(f'static/{hash_val}')
        fix_nb(nm)
        # Load the notebook and modify non-compliant Quarto comments
        with open(nm, 'r') as f:
            notebook_data = json.load(f)
            for cell in notebook_data['cells']:
                if cell['cell_type'] == 'code':
                    cell['source'] = escape_quarto_comments(cell['source'])
        
        # Save the modified notebook
        with open(nm, 'w') as f:
            json.dump(notebook_data, f)
        
        fname = nm.with_suffix('.html').name
        if not new_path.exists():
            mkdir(new_path, exist_ok=True, overwrite=True)
            process_nb_yml(new_path, full_url, hash_val)
            run(f'quarto render "{nm}" --no-execute --to html --metadata-file {new_path}/nb.yml')
            shutil.copytree(d, str(new_path), dirs_exist_ok=True)
            title = get_title(f'{new_path}/{fname}')
            update_meta(f'{new_path}/{fname}', f'https://nbsanity.com/static/{hash_val}/cover.png', title)
            run(f'shot-scraper "{new_path}/{fname}" -o {new_path}/cover.png -w 1200 -h 630')
        shutil.rmtree(d, ignore_errors=True)
        return RedirectResponse(f'/{new_path}/{fname}')
    
    except urllib.error.HTTPError as e:
        shutil.rmtree(new_path, ignore_errors=True)
        return handle_http_error(e, full_url)
    except Exception as e:
        shutil.rmtree(new_path, ignore_errors=True)
        raise e
    finally: shutil.rmtree(d, ignore_errors=True)

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

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("assets/icon.png")

