from fastapi.routing import APIRouter


router = APIRouter()


@router.get("")
async def health():
    return {"status": "Healthy"}
