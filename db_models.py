from sqlalchemy import BigInteger, Integer, JSON, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Member(Base):
    __tablename__ = "house_members"

    bioguide_id: Mapped[str] = mapped_column(String, primary_key=True)
    congress: Mapped[int] = mapped_column(Integer, primary_key=True)
    birthYear: Mapped[str | None] = mapped_column(String)
    deathYear: Mapped[str | None] = mapped_column(String)
    cosponsoredLegislationCount: Mapped[int | None] = mapped_column(Integer)
    sponsoredLegislationCount: Mapped[int | None] = mapped_column(Integer)
    image_url: Mapped[str | None] = mapped_column(String)
    name: Mapped[str | None] = mapped_column(String)
    firstName: Mapped[str | None] = mapped_column(String)
    lastName: Mapped[str | None] = mapped_column(String)
    honorificName: Mapped[str | None] = mapped_column(String)
    party: Mapped[str | None] = mapped_column(String)
    chamber: Mapped[str | None] = mapped_column(String)
    district: Mapped[int | None] = mapped_column(Integer)
    endYear: Mapped[int | None] = mapped_column(Integer)
    memberType: Mapped[str | None] = mapped_column(String)
    startYear: Mapped[int | None] = mapped_column(Integer)
    stateCode: Mapped[str | None] = mapped_column(String)
    stateName: Mapped[str | None] = mapped_column(String)


class HouseVote(Base):
    __tablename__ = "house_votes"

    identifier: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    congress: Mapped[int] = mapped_column(Integer)
    legislationNumber: Mapped[str | None] = mapped_column(String)
    legislationType: Mapped[str | None] = mapped_column(String)
    legislationUrl: Mapped[str | None] = mapped_column(String)
    result: Mapped[str | None] = mapped_column(String)
    rollCallNumber: Mapped[int] = mapped_column(Integer)
    sessionNumber: Mapped[int] = mapped_column(Integer)
    sourceDataURL: Mapped[str | None] = mapped_column(String)
    startDate: Mapped[str | None] = mapped_column(String)
    updateDate: Mapped[str | None] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String)
    voteType: Mapped[str | None] = mapped_column(String)
    positions: Mapped[list | None] = mapped_column(JSON)
    text: Mapped[dict | None] = mapped_column(JSON)
