"""Tab Kiến thức (công khai)."""
from fastapi import APIRouter, Depends, HTTPException, Request

from ..knowledge import ARTICLES, BY_SLUG
from ..web import current_user, render

router = APIRouter()


@router.get("/kien-thuc")
def knowledge_index(request: Request, user=Depends(current_user)):
    return render(request, "kien_thuc/index.html", {"articles": ARTICLES})


@router.get("/kien-thuc/{slug}")
def knowledge_article(slug: str, request: Request, user=Depends(current_user)):
    art = BY_SLUG.get(slug)
    if art is None:
        raise HTTPException(404, "Không tìm thấy bài")
    i = ARTICLES.index(art)
    return render(request, f"kien_thuc/{slug}.html", {
        "art": art, "prev": ARTICLES[i - 1] if i else None, "next": ARTICLES[i + 1] if i + 1 < len(ARTICLES) else None})
