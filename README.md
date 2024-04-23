# nbsanity

Like nbviewer, but uses [Quarto](https://quarto.org/) as the renderer.

## Try It

[https://nbsanity.com](https://nbsanity.com)

## Setup

### Local development

First, install dependencies:

```bash
pip install -U fastapi "uvicorn[standard]" fastcore
```

Also, [install Quarto](https://quarto.org/docs/get-started/).
    
Then, run the app:

```bash
uvicorn main:app
```

### Docker

Run the script [`run_docker.sh`](./run_docker.sh) to build and run the docker image.  

## Usage

You will see instructions on how to use the app on the home page.  If running locally, you should substitute `nbsanity.com` with `localhost:<PORT>` in the instructions.

## For Hamel

To launch to [dokku](https://hamel.dev/blog/posts/dokku/), add the remote:

```bash
git remote add prod dokku@nbsanity:q
```

Then, push to the remote:

```bash
ssh dokku@nbsanity repo:purge-cache q
git push prod
```