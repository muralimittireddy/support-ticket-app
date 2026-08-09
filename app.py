from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import db

app = FastAPI()

# Serves templates/*.html
templates = Jinja2Templates(directory="templates")

# Serves static/*.css, *.js (optional, but handy)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def list_tickets(request: Request):
    tickets = db.get_all_tickets()
    return templates.TemplateResponse(
        request,
        "tickets.html",
        {"tickets": tickets},
    )


@app.get("/tickets/{ticket_id}")
def ticket_detail(request: Request, ticket_id: str):
    ticket = db.get_ticket(ticket_id)
    messages = db.get_messages(ticket_id)
    return templates.TemplateResponse(
        request,
        "ticket_detail.html",
        {"ticket": ticket, "messages": messages},
    )


@app.get("/new")
def new_ticket_form(request: Request):
    return templates.TemplateResponse(request, "new_ticket.html", {})


@app.post("/tickets")
def create_ticket(title: str = Form(...), created_by: str = Form(...), priority: str = Form("medium")):
    new_id = db.create_ticket(title, created_by, priority)
    return RedirectResponse(url=f"/tickets/{new_id}", status_code=303)


@app.post("/tickets/{ticket_id}/messages")
def add_message(ticket_id: str, message_text: str = Form(...), author: str = Form(...)):
    db.add_message(ticket_id, message_text, author)
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)


@app.post("/tickets/{ticket_id}/status")
def update_status(ticket_id: str, status: str = Form(...)):
    db.update_ticket_status(ticket_id, status)
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
