from fastapi import APIRouter, HTTPException
from ..core.content import list_content, get_content
from ..schemas.register import RegistrationCreate
from .register import register
router = APIRouter(prefix='/api', tags=['catalog'])

@router.get('/{kind}')
async def listing(kind: str):
    return {'items': await list_content(kind, public=True)}

@router.get('/{kind}/{identifier}')
async def detail(kind: str, identifier: str):
    return await get_content(kind, identifier, public=True)

@router.post('/internship-applications', status_code=201)
async def application(data: RegistrationCreate):
    if not data.internship_id:
        raise HTTPException(422, 'Choose an internship program')
    return await register(data)
