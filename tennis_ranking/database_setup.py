from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Club(Base):
    __tablename__ = 'club'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class Associate(Base):
    __tablename__ = 'associate'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    birthDate = Column(String(20))
    classe = Column(String(8))
    ranking = Column(String(8))
    gender = Column(String(250))
    points = Column(String(20))
    club_id = Column(Integer, ForeignKey('club.id'))
    club = relationship(Club)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'birthDate': self.birthDate,
            'classe': self.classe,
            'ranking': self.ranking,
            'points': self.points,
        }


engine = create_engine('sqlite:///clubs.db')


Base.metadata.create_all(engine)
