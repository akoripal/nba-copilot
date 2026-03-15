from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Game(Base):
    __tablename__ = "games"

    id = Column(String, primary_key=True)
    date = Column(Date)
    home_team = Column(String)
    away_team = Column(String)
    home_score = Column(Integer)
    away_score = Column(Integer)
    season = Column(String)

class PlayerGame(Base):
    __tablename__ = "player_games"

    id = Column(String, primary_key=True)
    game_id = Column(String)
    player_id = Column(String)
    player_name = Column(String)
    team = Column(String)
    points = Column(Float)
    rebounds = Column(Float)
    assists = Column(Float)
    minutes = Column(Float)
    fg_percentage = Column(Float)
    three_point_percentage = Column(Float)
    usage_rate = Column(Float)
    fantasy_points = Column(Float)

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True)
    name = Column(String)
    abbreviation = Column(String)
    defensive_rating = Column(Float)
    pace = Column(Float)
    offensive_rating = Column(Float)

def create_tables():
    Base.metadata.create_all(engine)
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()
    