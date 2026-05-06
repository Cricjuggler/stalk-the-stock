"""Usage router — lets a user see their own monthly token consumption."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

import config
import database
from routers.auth import get_current_user

router = APIRouter(tags=["usage"])


@router.get("")
def get_usage(user: dict = Depends(get_current_user)):
    """Return the authenticated user's token usage for the current month."""
    user_id = int(user["sub"])
    used = database.get_month_tokens(user_id)
    limit = config.TOKEN_LIMIT_PER_USER
    remaining = max(0, limit - used)
    pct = round((used / limit) * 100, 1) if limit > 0 else 0.0
    return {
        "tokens_used": used,
        "tokens_limit": limit,
        "tokens_remaining": remaining,
        "pct_used": pct,
        "period": datetime.utcnow().strftime("%Y-%m"),
    }
