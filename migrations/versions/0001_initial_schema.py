"""Create inspections and defects tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "inspections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("test_image_path", sa.Text(), nullable=False),
        sa.Column("reference_image_path", sa.Text(), nullable=True),
        sa.Column("annotated_image_path", sa.Text(), nullable=False),
        sa.Column("report_path", sa.Text(), nullable=True),
        sa.Column("model_version", sa.String(128), nullable=False),
        sa.Column("alignment_quality", sa.JSON(), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=False),
    )
    op.create_index("ix_inspections_status", "inspections", ["status"])
    op.create_index("ix_inspections_created_at", "inspections", ["created_at"])
    op.create_table(
        "defects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("inspection_id", sa.String(36), sa.ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("defect_type", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("bbox", sa.JSON(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
    )
    op.create_index("ix_defects_inspection_id", "defects", ["inspection_id"])
    op.create_index("ix_defects_defect_type", "defects", ["defect_type"])
    op.create_index("ix_defects_severity", "defects", ["severity"])


def downgrade() -> None:
    op.drop_table("defects")
    op.drop_table("inspections")
