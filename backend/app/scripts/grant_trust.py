"""Юзерге trust_level беру (алғашқы админ/модераторды тағайындау жолы).

Қолдану: uv run python -m app.scripts.grant_trust user@email.kz admin
"""

import asyncio
import sys

from sqlalchemy import select

from app.db.session import async_session
from app.models import User
from app.models.user import TRUST_LEVELS


async def main(email: str, level: str) -> None:
    if level not in TRUST_LEVELS:
        print(f"Жарамсыз деңгей: {level}. Нұсқалар: {', '.join(TRUST_LEVELS)}")
        sys.exit(1)
    async with async_session() as db:
        user = await db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            print(f"Юзер табылмады: {email}")
            sys.exit(1)
        user.trust_level = level
        await db.commit()
        print(f"{user.pseudonym} ({email}) -> {level}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
