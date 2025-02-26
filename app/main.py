from typing import Annotated

from fastapi import Depends, FastAPI, Query, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select

class BaseTravel(SQLModel):
    title: str
    description: str
    pickup_location: str
    price: float

class Travel(BaseTravel, table=True):
    id: int | None = Field(default=None, primary_key=True)

class TravelPublic(BaseTravel):
    pass

class TravelUpdate(BaseTravel):
    title: str | None = None
    description: str | None = None
    pickup_location: str | None = None
    price: float | None = None

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/travels/")
def get_travels(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Travel]:
    travels = session.exec(select(Travel).offset(offset).limit(limit)).all()
    return travels

@app.get("/travels/{travel_id}")
def get_travel(travel_id:int, session: SessionDep):
    travel = session.get(Travel, travel_id)
    if not travel:
        raise HTTPException(status_code=404, detail="Travel Not Found")
    return travel

@app.delete("/travels/{travel_id}")
def delete_travel(travel_id:int, session: SessionDep):
    travel = session.get(Travel, travel_id)
    if not travel:
        raise HTTPException(status_code=404, detail="Travel Not Found")
    session.delete(travel)
    session.commit()
    return {"ok": True}

@app.post('/travels/')
def create_travel(travel: Travel, session: SessionDep):
    session.add(travel)
    session.commit()
    session.refresh(travel)
    return travel

@app.patch("/travels/{travel_id}", response_model=TravelPublic)
def update_travel(travel_id: int, travel: TravelUpdate, session: SessionDep):
    travel_db = session.get(Travel, travel_id)
    if not travel_db:
        raise HTTPException(status_code=404, detail="Travel not found")
    travel_data = travel.model_dump(exclude_unset=True)
    travel_db.sqlmodel_update(travel_data)
    session.add(travel_db)
    session.commit()
    session.refresh(travel_db)
    return travel_db