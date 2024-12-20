"""Add UserActivityLog and ReportDraft models

Revision ID: 7713f24f6704
Revises: afc23bbb572e
Create Date: 2024-12-04 21:34:51.935256

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7713f24f6704'
down_revision = 'afc23bbb572e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('analytics_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('session_id', sa.String(length=100), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('element_id', sa.String(length=100), nullable=True),
    sa.Column('element_class', sa.String(length=100), nullable=True),
    sa.Column('event_data', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('page_views',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('session_id', sa.String(length=100), nullable=True),
    sa.Column('referrer', sa.String(length=500), nullable=True),
    sa.Column('user_agent', sa.String(length=500), nullable=True),
    sa.Column('duration', sa.Integer(), nullable=True),
    sa.Column('bounce', sa.Boolean(), nullable=True),
    sa.Column('device_type', sa.String(length=20), nullable=True),
    sa.Column('country', sa.String(length=2), nullable=True),
    sa.Column('browser', sa.String(length=50), nullable=True),
    sa.Column('os', sa.String(length=50), nullable=True),
    sa.Column('exit_url', sa.String(length=500), nullable=True),
    sa.Column('page_type', sa.String(length=50), nullable=True),
    sa.Column('content_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('report_draft',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('metrics', sa.JSON(), nullable=True),
    sa.Column('timeframe', sa.String(length=10), nullable=True),
    sa.Column('last_modified', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_activities',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('activity_type', sa.String(length=50), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('activity_data', sa.JSON(), nullable=True),
    sa.Column('session_id', sa.String(length=100), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=True),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_activity_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('page_view')
    op.drop_table('user_activity')
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.alter_column('key',
               existing_type=sa.VARCHAR(length=64),
               type_=sa.String(length=50),
               existing_nullable=False)
        batch_op.alter_column('value',
               existing_type=sa.TEXT(),
               type_=sa.String(length=500),
               existing_nullable=True)
        batch_op.alter_column('description',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.String(length=200),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.alter_column('description',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=255),
               existing_nullable=True)
        batch_op.alter_column('value',
               existing_type=sa.String(length=500),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('key',
               existing_type=sa.String(length=50),
               type_=sa.VARCHAR(length=64),
               existing_nullable=False)

    op.create_table('user_activity',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('action', sa.VARCHAR(length=64), nullable=False),
    sa.Column('details', sa.TEXT(), nullable=True),
    sa.Column('ip_address', sa.VARCHAR(length=45), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('page_view',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('path', sa.VARCHAR(length=500), nullable=False),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('post_id', sa.INTEGER(), nullable=True),
    sa.Column('user_id', sa.INTEGER(), nullable=True),
    sa.Column('ip_address', sa.VARCHAR(length=45), nullable=True),
    sa.Column('user_agent', sa.VARCHAR(length=200), nullable=True),
    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('user_activity_log')
    op.drop_table('user_activities')
    op.drop_table('report_draft')
    op.drop_table('page_views')
    op.drop_table('analytics_events')
    # ### end Alembic commands ###
