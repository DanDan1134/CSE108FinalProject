"""
Database models for Wordle Battle game.
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for storing player information."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    matches_as_player1 = relationship("Match", foreign_keys="Match.player1_id", back_populates="player1")
    matches_as_player2 = relationship("Match", foreign_keys="Match.player2_id", back_populates="player2")
    wins_as_winner = relationship("Match", foreign_keys="Match.winner_id", back_populates="winner")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', wins={self.wins}, losses={self.losses})>"


class Match(Base):
    """Match model for storing game results."""
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    player1_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    player2_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    winner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    player1_score = Column(Integer, default=0)
    player2_score = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # Relationships
    player1 = relationship("User", foreign_keys=[player1_id], back_populates="matches_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="matches_as_player2")
    winner = relationship("User", foreign_keys=[winner_id], back_populates="wins_as_winner")
    
    def __repr__(self):
        return f"<Match(id={self.id}, player1_id={self.player1_id}, player2_id={self.player2_id}, winner_id={self.winner_id})>"

