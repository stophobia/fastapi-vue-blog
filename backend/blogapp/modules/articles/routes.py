from datetime import datetime
from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from .models import ArticleCreateOrUpdate, ArticleResponse, ArticleDocument
from .utils import check_user_can_modify_article
from ..users.model import UserDocument
from ...core.security.roles import RolesEnum
from ...core.security.utilities import RoleChecker

router = APIRouter(prefix="/articles")


@router.post("/", response_model=ArticleResponse)
async def create_article(
    article_data: ArticleCreateOrUpdate,
    current_user: Annotated[
        UserDocument, Depends(RoleChecker(allowed_role=RolesEnum.AUTHOR.value))
    ],
):
    article = ArticleDocument(
        author=current_user,
        created_at=datetime.utcnow(),
        **article_data.model_dump(),
    )
    await ArticleDocument.insert_one(article)
    return {"article": article}


@router.get("/{article_id}", response_model=ArticleResponse)
async def read_article(
    article_id: PydanticObjectId,
    current_user: Annotated[
        UserDocument, Depends(RoleChecker(allowed_role=RolesEnum.READER.value))
    ],
):
    article = await ArticleDocument.get(document_id=article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Article not found"
        )
    return {"article": article}


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: PydanticObjectId,
    article_data: ArticleCreateOrUpdate,
    current_user: Annotated[
        UserDocument, Depends(RoleChecker(allowed_role=RolesEnum.AUTHOR.value))
    ],
):
    # Получить документ статьи
    article = await ArticleDocument.get_or_404(document_id=article_id, fetch_links=True)
    # Проверить права редактирования
    check_user_can_modify_article(article=article, user=current_user)
    # Обновить поля и сохранить документ
    article = article.model_copy(update=article_data.model_dump(exclude_unset=True))
    article.updated_at = datetime.utcnow()
    await article.save()

    return {"article": article}
