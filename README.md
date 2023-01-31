## Instructions

### 1. Launch app 

```bash
uvicorn main:app
```

### 2. Use the `/render/<github url>` path to render a notebook.

For example, if you want to render `https://github.com/hamelsmu/hamel/blob/master/notes/serving/tfserving/tf-serving-basics.ipynb`, you would navigate to this URL:

```
open http://127.0.0.1:8000/render/https://github.com/hamelsmu/hamel/blob/master/notes/serving/tfserving/tf-serving-basics.ipynb
```

Your browser will redirect you to a rendered quarto notebook!

Another example:

```bash
open http://127.0.0.1:8000/render/https://github.com/seeM/blog/blob/main/posts/jupyter-server-a-whirlwind-tour.ipynb
```
