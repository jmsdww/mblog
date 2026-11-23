import os
import shutil
import zipfile
from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Set a strong secret token (match this in your GitHub Secrets)
DEPLOY_SECRET = os.environ.get("DEPLOY_SECRET", "change-this-to-a-long-random-secret")
SITE_DIR = "site_dist"

os.makedirs(SITE_DIR, exist_ok=True)
# Create a placeholder page until the first GitHub deploy arrives
if not os.path.exists(f"{SITE_DIR}/index.html"):
    with open(f"{SITE_DIR}/index.html", "w") as f:
        f.write("<h1>Blog is ready! Waiting for first GitHub Actions build...</h1>")

@app.post("/deploy")
async def deploy_site(
    file: UploadFile = File(...),
    x_deploy_token: str = Header(None)
):
    if x_deploy_token != DEPLOY_SECRET:
        raise HTTPException(status_code=401, detail="Invalid deploy token")

    zip_path = "latest_build.zip"
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Replace old static files with the new Astro build
    shutil.rmtree(SITE_DIR)
    os.makedirs(SITE_DIR, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(SITE_DIR)

    os.remove(zip_path)
    return {"status": "deployed successfully"}

# Serve the static Astro site at the root URL
app.mount("/", StaticFiles(directory=SITE_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
