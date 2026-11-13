from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime

from app.database import get_db
from app.models import User, Challenge, ChallengeProgress
from app.schemas.challenge import ChallengeProgressUpdate
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/challenges", tags=["challenges"])


@router.get("")
async def list_challenges(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    challenges = (await db.execute(select(Challenge))).scalars().all()
    progs = (await db.execute(select(ChallengeProgress).where(ChallengeProgress.user_id == user.id))).scalars().all()
    by_ch = {p.challenge_id: p for p in progs}
    out = []
    for c in challenges:
        prog = by_ch.get(c.id)
        out.append({
            "id": c.id, "title": c.title, "description": c.description,
            "start_date": c.start_date, "end_date": c.end_date,
            "reward_points": c.reward_points, "participants": c.participants,
            "joined": prog is not None,
            "progress": prog.progress if prog else 0,
            "completed": prog.completed if prog else False,
        })
    return out


@router.post("/{challenge_id}/join")
async def join_challenge(challenge_id: int, user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    challenge = (await db.execute(select(Challenge).where(Challenge.id == challenge_id))).scalar_one_or_none()
    if not challenge:
        raise HTTPException(404, "Challenge not found")

    existing = (await db.execute(select(ChallengeProgress).where(
        ChallengeProgress.challenge_id == challenge_id, ChallengeProgress.user_id == user.id
    ))).scalars().first()
    if existing:
        return {"ok": True, "message": "Already joined"}

    db.add(ChallengeProgress(challenge_id=challenge_id, user_id=user.id, progress=0,
                             completed=False, updated_at=datetime.utcnow()))
    await db.execute(update(Challenge).where(Challenge.id == challenge_id)
                     .values(participants=Challenge.participants + 1))
    await db.commit()
    return {"ok": True, "message": "Joined"}


@router.post("/{challenge_id}/progress")
async def update_progress(challenge_id: int, req: ChallengeProgressUpdate,
                          user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    p = (await db.execute(select(ChallengeProgress).where(
        ChallengeProgress.challenge_id == challenge_id, ChallengeProgress.user_id == user.id
    ))).scalars().first()
    if not p:
        raise HTTPException(404, "Join the challenge first")
    ch = (await db.execute(select(Challenge).where(Challenge.id == challenge_id))).scalar_one()

    new_prog = max(0, min(100, req.progress))
    just_done = new_prog >= 100 and not p.completed
    p.progress, p.completed, p.updated_at = new_prog, new_prog >= 100, datetime.utcnow()
    if just_done:
        await db.execute(update(User).where(User.id == user.id)
                         .values(points=User.points + (ch.reward_points or 0)))
    await db.commit()
    return {"ok": True, "progress": p.progress, "completed": p.completed}


@router.get("/my-progress")
async def my_progress(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    progs = (await db.execute(select(ChallengeProgress).where(ChallengeProgress.user_id == user.id))).scalars().all()
    out = []
    for p in progs:
        c = (await db.execute(select(Challenge).where(Challenge.id == p.challenge_id))).scalar_one_or_none()
        out.append({
            "challenge_id": p.challenge_id, "title": c.title if c else "Unknown",
            "progress": p.progress, "completed": p.completed,
            "reward_points": c.reward_points if c else 0,
        })
    return out
