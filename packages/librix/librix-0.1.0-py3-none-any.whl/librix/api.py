from fastapi import FastAPI, Query, HTTPException
from typing import Optional, List
from .scraper import AnnasArchiveScraper
import uvicorn

app = FastAPI(title="Anna's Archive API", description="Simple API for searching books on Anna's Archive")
scraper = AnnasArchiveScraper()

@app.get("/search")
async def search(
    q: str = Query(..., description="Search query"),
    lang: Optional[str] = Query(None, description="Language filter (e.g. 'en', 'pl')"),
    ext: Optional[str] = Query(None, description="Extension filter (e.g. 'pdf', 'epub')"),
    sort: Optional[str] = Query(None, description="Sort order"),
    page: int = Query(1, description="Page number", ge=1)
):
    try:
        results = scraper.search(query=q, lang=lang, ext=ext, sort=sort, page=page)
        return {
            "query": q,
            "page": page,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/detail/{md5}")
async def detail(md5: str):
    try:
        data = scraper.get_detail(md5)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

