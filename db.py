from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker

from db_models import Base

engine = create_engine("sqlite:///congress.db")
Session = sessionmaker(bind=engine, expire_on_commit=False)


def create_row(model, **values):
    with Session() as session:
        row = model(**values)
        session.add(row)
        session.commit()
        return row


def get_row(model, pk):
    with Session() as session:
        return session.get(model, pk)


def list_rows(model, **filters):
    with Session() as session:
        stmt = select(model)
        for key, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(model, key) == value)
        return list(session.scalars(stmt).all())


def edit_row(model, pk, **values):
    with Session() as session:
        row = session.get(model, pk)
        if row is None:
            raise KeyError(f"{model.__name__} {pk!r} not found")
        for key, value in values.items():
            setattr(row, key, value)
        session.commit()
        return row


def delete_row(model, pk):
    with Session() as session:
        row = session.get(model, pk)
        if row is None:
            raise KeyError(f"{model.__name__} {pk!r} not found")
        session.delete(row)
        session.commit()


def _model_type_name(column):
    return str(column.type.compile(dialect=engine.dialect))


def sync_schema():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        inspector = inspect(conn)
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            db_columns = {column["name"]: column for column in inspector.get_columns(table.name)}
            model_columns = {column.name: column for column in table.columns}
            added = [name for name in model_columns if name not in db_columns]
            removed = [name for name in db_columns if name not in model_columns]

            for name in added:
                column = model_columns[name]
                type_sql = _model_type_name(column)
                conn.execute(text(
                    f"ALTER TABLE {table.name} ADD COLUMN {name} {type_sql}"
                ))
                db_columns[name] = {"name": name, "type": type_sql}

            for name in removed:
                conn.execute(text(
                    f"ALTER TABLE {table.name} DROP COLUMN {name}"
                ))
                db_columns.pop(name, None)
                
        conn.execute(text("PRAGMA foreign_keys = ON"))


