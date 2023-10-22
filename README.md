# nbsanity

Like nbviewer, but for standalone quarto notebooks

## Setup

### Local development

First, install dependencies:

```bash
pip install -U fastapi "uvicorn[standard]" fastcore
```
    
Then, run the app:

```bash
uvicorn main:app
```

You will see instructions on how to use the app on the home page.  If running locally, you should substitute `nbsanity.com` with `localhost:<PORT>` in the instructions.

### Docker

Run the script `run_docker.sh` to build and run the docker image.  

## Usage

You will see instructions on how to use the app on the home page.  If running locally, you should substitute `nbsanity.com` with `localhost:<PORT>` in the instructions.
