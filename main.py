from shutil import copytree
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import tempfile
from fastcore.xtras import run, mkdir, Path
from fastcore.net import urlsave
import hashlib

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def git2raw(git_url: str):
    "Convert a git url to a raw url"
    return git_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

@app.get("/render/{file_path:path}")
async def render(file_path: str):
    "Render the notebook"
    with tempfile.TemporaryDirectory() as d:
        nm = urlsave(git2raw(file_path), d)
        hash = hashlib.md5(open(nm,'rb').read()).hexdigest()
        new_path = Path(f'static/{hash}')
        
        if not new_path.exists():
            run(f"quarto render {nm} --to html")
            mkdir(f'static/{hash}', exist_ok=True, overwrite=True)
            copytree(d, f'static/{hash}', dirs_exist_ok=True)

    #redirect to static file
    fname = nm.with_suffix('.html').name
    return RedirectResponse(f'/static/{hash}/{fname}')
