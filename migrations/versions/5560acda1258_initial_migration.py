"""Initial migration

Revision ID: 5560acda1258
Revises: 
Create Date: 2024-10-16 11:08:26.920669

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5560acda1258'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('elections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('election_name', sa.String(length=100), nullable=False),
    sa.Column('election_type', sa.String(length=50), nullable=False),
    sa.Column('max_votes', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('election_name')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('candidates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('election_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['election_id'], ['elections.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('election_id', 'name', name='unique_candidate_per_election')
    )
    op.create_table('user_votes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('election_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['election_id'], ['elections.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'election_id', name='unique_user_election')
    )
    op.create_table('votes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('candidate_id', sa.Integer(), nullable=False),
    sa.Column('election_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
    sa.ForeignKeyConstraint(['election_id'], ['elections.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('votes')
    op.drop_table('user_votes')
    op.drop_table('candidates')
    op.drop_table('users')
    op.drop_table('elections')
    # ### end Alembic commands ###
