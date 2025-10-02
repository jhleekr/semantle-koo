from fastapi import Depends, FastAPI, Request, BackgroundTasks
import time
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
import pickle
import random
from fastapi.staticfiles import StaticFiles
import os
import logging

import word2vec
from process_similar import get_nearest
import crud
from database import engine, SessionLocal, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
gunicorn_logger = logging.getLogger("gunicorn.error")

with open('data/valid_nearest.dat', 'rb') as f:
    valid_nearest_words, valid_nearest_vecs = pickle.load(f)

with open('data/secrets.txt', 'r', encoding='utf-8') as f:
    words = [l.strip() for l in f.readlines()]

app.mount("/static", StaticFiles(directory="xstatic"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def deletedb(sid: str):
    gunicorn_logger.info(f"[{sid}] Session Generated")
    time.sleep(45000)
    gunicorn_logger.info(f"[{sid}] Session Expired")
    db = SessionLocal()
    ans = crud.d_get(db, sid).data
    crud.d_delete(db, sid)
    os.remove(f"data/near/{ans}.dat")
    db.close()
    gunicorn_logger.info(f"[{sid}] Session Deleted")


@app.get("/")
def root():
    return RedirectResponse("/static/select.html")


@app.get('/start')
def start(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    hdr = request.headers
    sid = None
    if "word-sess" in hdr:
        sid = hdr["word-sess"]
        if not crud.d_get(db, sid):
            sid = None
    if not sid:
        sid = crud.d_new(db)
        w = random.choice(words)
        crud.d_modify(db, sid, w)
        background_tasks.add_task(deletedb, sid)
    ans = crud.d_get(db, sid).data
    nearests = get_nearest(ans, ans, valid_nearest_words, valid_nearest_vecs) #just generate
    return JSONResponse({"sess": sid})


@app.get('/check')
def start(request: Request, db: Session = Depends(get_db)):
    hdr = request.headers
    sid = None
    if "word-sess" in hdr:
        sid = hdr["word-sess"]
        if not crud.d_get(db, sid):
            sid = None
    if not sid:
        return JSONResponse({"error": "unknown"}, status_code=404)
    return JSONResponse({"sess": sid})


@app.get('/guess')
def get_guess(request: Request, word: str, db: Session = Depends(get_db)):
    hdr = request.headers
    sid = None
    if "word-sess" in hdr:
        sid = hdr["word-sess"]
        if not crud.d_get(db, sid):
            sid = None
    if not sid:
        return JSONResponse({"error": "unknown"}, status_code=404)
    ans = crud.d_get(db, sid).data
    nearests = get_nearest(ans, ans, valid_nearest_words, valid_nearest_vecs)
    if ans.lower() == word.lower():
        word = ans
    rtn = {"guess": word}
    # check most similar
    if word in nearests:
        rtn["sim"] = nearests[word][1]
        rtn["rank"] = nearests[word][0]
    else:
        try:
            rtn["sim"] = word2vec.similarity(ans, word)
            rtn["rank"] = "1000위 이상"
        except KeyError:
            return JSONResponse({"error": "unknown"}, status_code=404)
    return JSONResponse(rtn)


@app.get('/similarity')
def get_similarity(request: Request, db: Session = Depends(get_db)):
    hdr = request.headers
    sid = None
    if "word-sess" in hdr:
        sid = hdr["word-sess"]
        if not crud.d_get(db, sid):
            sid = None
    if not sid:
        return JSONResponse({"error": "unknown"}, status_code=404)
    ans = crud.d_get(db, sid).data
    nearests = get_nearest(ans, ans, valid_nearest_words, valid_nearest_vecs)
    nearest_dists = sorted([v[1] for v in nearests.values()])
    return JSONResponse({"top": nearest_dists[-2], "top10": nearest_dists[-11], "rest": nearest_dists[0]})


@app.get('/giveup')
def giveup(request: Request, db: Session = Depends(get_db)):
    hdr = request.headers
    sid = None
    if "word-sess" in hdr:
        sid = hdr["word-sess"]
        if not crud.d_get(db, sid):
            sid = None
    if not sid:
        return JSONResponse({"error": "unknown"}, status_code=404)
    ans = crud.d_get(db, sid).data
    return JSONResponse({"word": ans})


@app.get('/near1k')
def near1k(request: Request, db: Session = Depends(get_db)):
    hdr = request.headers
    sid = None
    if "word-sess" in hdr:
        sid = hdr["word-sess"]
        if not crud.d_get(db, sid):
            sid = None
    if not sid:
        return JSONResponse({"error": "unknown"}, status_code=404)
    ans = crud.d_get(db, sid).data
    return JSONResponse(get_nearest(ans, ans, valid_nearest_words, valid_nearest_vecs))


@app.get('/favicon.ico')
def favicon():
    return RedirectResponse("https://www.bfy.kr/files/2020/08/cropped-BFY_LOGO_BIG-32x32.png")
