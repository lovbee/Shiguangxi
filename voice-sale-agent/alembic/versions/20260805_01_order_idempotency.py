"""为 Agent 订单增加数据库级幂等键。

迁移必须兼容两种数据库：旧库没有字段；由最新 schema.sql 创建的新库已经有
字段/约束。因此 upgrade/downgrade 都先反射当前结构，再决定是否执行 DDL。
"""

import sqlalchemy as sa

from alembic import op

revision = "20260805_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """新增字段、回填历史订单，并建立非空唯一约束。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("order_record")}
    if "idempotency_key" not in columns:
        op.add_column("order_record", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    # 历史订单没有请求幂等键，用主键构造稳定且互不冲突的占位值。
    op.execute("UPDATE order_record SET idempotency_key = 'legacy:' || id WHERE idempotency_key IS NULL")
    op.alter_column("order_record", "idempotency_key", nullable=False)
    unique_constraints = inspector.get_unique_constraints("order_record")
    has_unique_key = any(
        constraint.get("column_names") == ["idempotency_key"]
        for constraint in unique_constraints
    )
    if not has_unique_key:
        op.create_unique_constraint("uq_order_record_idempotency_key", "order_record", ["idempotency_key"])


def downgrade() -> None:
    """安全移除本迁移创建的唯一约束和字段。"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    constraints = {
        constraint["name"]
        for constraint in inspector.get_unique_constraints("order_record")
        if constraint.get("name")
        and constraint.get("column_names") == ["idempotency_key"]
    }
    for constraint_name in constraints:
        op.drop_constraint(constraint_name, "order_record", type_="unique")
    columns = {column["name"] for column in inspector.get_columns("order_record")}
    if "idempotency_key" in columns:
        op.drop_column("order_record", "idempotency_key")
