"""Two unrelated, deterministic development fixtures. No customer data."""
import threading

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Daedalus fixtures")
counter_lock = threading.Lock()
calls = {"inventory": 0, "tickets": 0}
tickets = []


class Ticket(BaseModel):
    title: str = Field(min_length=1, max_length=200)


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/inventory/items/{item_id}")
def inventory(item_id: str, warehouse: str = "central"):
    with counter_lock:
        calls["inventory"] += 1
    if item_id == "missing":
        raise HTTPException(404, "Item not found")
    return {"id": item_id, "name": "Precision bearing", "quantity": 42, "warehouse": warehouse}


@app.get("/tickets/{ticket_id}")
def ticket(ticket_id: str):
    with counter_lock:
        calls["tickets"] += 1
    return {"id": ticket_id, "title": "Replace workstation", "status": "open"}


@app.post("/tickets")
def create_ticket(body: Ticket):
    with counter_lock:
        calls["tickets"] += 1
        result = {"id": f"T-{len(tickets) + 1}", "title": body.title, "status": "open"}
        tickets.append(result)
    return result


@app.get("/fixture/counters")
def counters():
    return dict(calls)
