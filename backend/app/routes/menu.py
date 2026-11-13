from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from app.database import get_db
from app.models import User, MenuItem
from app.schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/menu", tags=["menu"])


def _to_response(item: MenuItem) -> dict:
    return {
        "id": item.id, "menu_type": item.menu_type, "meal_type": item.meal_type,
        "name": item.name, "category": item.category, "description": item.description,
        "calories": item.calories, "protein_g": item.protein_g,
        "carbs_g": item.carbs_g, "fat_g": item.fat_g,
        "price": item.price, "timing": item.timing,
        "allergens": item.allergens or [], "available": item.available,
    }


@router.get("", response_model=list[MenuItemResponse])
async def list_menu(
    menu_type: str = Query(..., pattern="^(hostel_mess|college_canteen)$"),
    meal_type: str = Query(None, pattern="^(breakfast|lunch|snacks|dinner)$"),
    category: str = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get menu filtered by student type. Shows correct menu based on profile."""
    # Use the requested menu_type (frontend should pass based on student_type)
    query = select(MenuItem).where(MenuItem.menu_type == menu_type, MenuItem.available == True)
    if meal_type:
        query = query.where(MenuItem.meal_type == meal_type)
    if category:
        query = query.where(MenuItem.category == category)
    query = query.order_by(MenuItem.meal_type, MenuItem.name)
    result = await db.execute(query)
    return [_to_response(i) for i in result.scalars().all()]


@router.get("/my-menu", response_model=list[MenuItemResponse])
async def my_menu(
    meal_type: str = Query(None, pattern="^(breakfast|lunch|snacks|dinner)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get menu based on logged-in user's student type."""
    menu_type = "hostel_mess" if user.student_type == "hosteler" else "college_canteen"
    query = select(MenuItem).where(MenuItem.menu_type == menu_type, MenuItem.available == True)
    if meal_type:
        query = query.where(MenuItem.meal_type == meal_type)
    query = query.order_by(MenuItem.meal_type, MenuItem.name)
    result = await db.execute(query)
    return [_to_response(i) for i in result.scalars().all()]


@router.post("", response_model=MenuItemResponse)
async def create_menu_item(
    req: MenuItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a menu item (any authenticated user for prototype)."""
    item = MenuItem(**req.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _to_response(item)


@router.put("/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int, req: MenuItemUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Menu item not found")
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if updates:
        await db.execute(update(MenuItem).where(MenuItem.id == item_id).values(**updates))
        await db.commit()
        await db.refresh(item)
    return _to_response(item)


@router.delete("/{item_id}")
async def delete_menu_item(
    item_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MenuItem).where(MenuItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Menu item not found")
    await db.execute(delete(MenuItem).where(MenuItem.id == item_id))
    await db.commit()
    return {"ok": True}