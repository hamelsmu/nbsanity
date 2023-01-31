import tempfile, hashlib, shutil
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastcore.all import run, mkdir, Path, urlsave

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def git2raw(git_url: str): return git_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

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
            shutil.copytree(d, f'static/{hash}', dirs_exist_ok=True)

    fname = nm.with_suffix('.html').name
    return RedirectResponse(f'/static/{hash}/{fname}')
