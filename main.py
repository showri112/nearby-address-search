from app.main import app, create_tables

if __name__ == "__main__":
    import uvicorn

    create_tables()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
