from sqlalchemy import BigInteger, Integer, JSON, String, Text, create_engine, insert, select, update, delete, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


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
    summary: Mapped[str | None] = mapped_column(Text)


engine = create_engine("sqlite:///congress.db")
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def create_members(members: list[dict]):
    if not members:
        return
    with SessionLocal() as session:
        session.execute(insert(Member), members)
        session.commit()


def create_house_votes(house_votes: list[dict]):
    if not house_votes:
        return
    with SessionLocal() as session:
        session.execute(insert(HouseVote), house_votes)
        session.commit()

def get_member(bioguide_id: str, congress: int) -> dict | None:
    with SessionLocal() as session:
        row = session.execute(
            select(Member.__table__).where(
                Member.bioguide_id == bioguide_id,
                Member.congress == congress,
            )
        ).mappings().first()
        return dict(row) if row else None

def named_positions(session, congress: int, positions: list | None) -> list | None:
    if not positions:
        return positions
    bioguide_ids = {
        position["bioguide_id"]
        for position in positions
        if position.get("bioguide_id")
    }
    names = dict(
        session.execute(
            select(Member.bioguide_id, Member.name).where(
                Member.congress == congress,
                Member.bioguide_id.in_(bioguide_ids),
            )
        ).all()
    )
    return [
        {**position, "name": names.get(position.get("bioguide_id"))}
        for position in positions
    ]


def get_house_vote(identifier: int) -> dict | None:
    with SessionLocal() as session:
        row = session.execute(
            select(HouseVote.__table__).where(
                HouseVote.identifier == identifier,
            )
        ).mappings().first()
        if row is None:
            return None
        vote = dict(row)
        vote["positions"] = named_positions(session, vote["congress"], vote["positions"])
        return vote


def set_house_vote_summary(identifier: int, summary: str) -> dict | None:
    with SessionLocal() as session:
        row = session.execute(
            update(HouseVote)
            .where(HouseVote.identifier == identifier)
            .values(summary=summary)
            .returning(*HouseVote.__table__.columns)
        ).mappings().first()
        session.commit()
        if row is None:
            return None
        vote = dict(row)
        vote["positions"] = named_positions(session, vote["congress"], vote["positions"])
        return vote

def edit_member(bioguide_id: str, congress: int, fields: dict) -> dict | None:
    if not fields:
        return get_member(bioguide_id, congress)
    with SessionLocal() as session:
        row = session.execute(
            update(Member)
            .where(Member.bioguide_id == bioguide_id, Member.congress == congress)
            .values(**fields)
            .returning(*Member.__table__.columns)
        ).mappings().first()
        session.commit()
        return dict(row) if row else None

def edit_house_vote(identifier: int, fields: dict) -> dict | None:
    if not fields:
        return get_house_vote(identifier)
    with SessionLocal() as session:
        row = session.execute(
            update(HouseVote)
            .where(HouseVote.identifier == identifier)
            .values(**fields)
            .returning(*HouseVote.__table__.columns)
        ).mappings().first()
        session.commit()
        return dict(row) if row else None


def delete_member(bioguide_id: str, congress: int) -> bool:
    with SessionLocal() as session:
        result = session.execute(
            delete(Member).where(
                Member.bioguide_id == bioguide_id,
                Member.congress == congress,
            )
        )
        session.commit()
        return result.rowcount > 0


def delete_house_vote(identifier: int) -> bool:
    with SessionLocal() as session:
        result = session.execute(
            delete(HouseVote).where(
                HouseVote.identifier == identifier,
            )
        )
        session.commit()
        return result.rowcount > 0


def list_members(congress=None, offset=0, limit=20):
    with SessionLocal() as session:
        stmt = select(Member.__table__)
        count_stmt = select(func.count()).select_from(Member.__table__)
        if congress is not None:
            stmt = stmt.where(Member.congress == congress)
            count_stmt = count_stmt.where(Member.congress == congress)
        total = session.scalar(count_stmt)
        rows = session.execute(
            stmt.order_by(Member.lastName, Member.bioguide_id)
            .offset(offset)
            .limit(limit)
            ).mappings().all()
        return [dict(row) for row in rows], total

def list_house_votes(congress=None, offset=0, limit=20):
    list_columns = [
        column for column in HouseVote.__table__.columns
        if column.name not in ("positions", "text")
    ]
    with SessionLocal() as session:
        stmt = select(*list_columns)
        count_stmt = select(func.count()).select_from(HouseVote.__table__)
        if congress is not None:
            stmt = stmt.where(HouseVote.congress == congress)
            count_stmt = count_stmt.where(HouseVote.congress == congress)
        total = session.scalar(count_stmt)
        rows = session.execute(
            stmt.order_by(HouseVote.startDate, HouseVote.rollCallNumber, HouseVote.identifier)
            .offset(offset)
            .limit(limit)
            ).mappings().all()
        return [dict(row) for row in rows], total