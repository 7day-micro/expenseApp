"""merge diverged heads

Revision ID: 0820896632c6
Revises: 73da91ee514c, 23a84e08b076
Create Date: 2026-04-10 13:21:23.709023

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "0820896632c6"
down_revision: str | Sequence[str] | None = ("73da91ee514c", "23a84e08b076")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
