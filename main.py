from fastapi import Depends, FastAPI, Request, BackgroundTasks
import time
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
import pickle
import random
from fastapi.staticfiles import StaticFiles
import json

import word2vec
from process_similar import get_nearest
import crud
from database import engine, SessionLocal, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

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


def deletedb(db: Session, sid: str):
    time.sleep(7200)
    crud.d_delete(db, sid)
    pass


@app.get("/")
def root():
    return RedirectResponse("/static/select.html")


@app.get('/single/start')
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
        init = {"word": w}
        crud.d_modify(db, sid, json.dumps(init))
        background_tasks.add_task(deletedb, db, sid)
    ans = json.loads(crud.d_get(db, sid).data)["word"]
    nearests = get_nearest(ans, ans, valid_nearest_words, valid_nearest_vecs)
    return JSONResponse({"sess": sid})


@app.get('/single/guess')
def get_guess(request: Request, background_tasks: BackgroundTasks, word: str, db: Session = Depends(get_db)):
    hdr = request.headers
    sid = None
    if "word-sess" in hdr:
        sid = hdr["word-sess"]
        if not crud.d_get(db, sid):
            sid = None
    if not sid:
        return JSONResponse({"error": "unknown"}, status_code=404)
    ans = json.loads(crud.d_get(db, sid).data)["word"]
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
    ans = json.loads(crud.d_get(db, sid).data)["word"]
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
    ans = json.loads(crud.d_get(db, sid).data)["word"]
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
    ans = json.loads(crud.d_get(db, sid).data)["word"]
    return JSONResponse(get_nearest(ans, ans, valid_nearest_words, valid_nearest_vecs))


"""
@app.get('/multi/guess')
def get_guess(db: Session, request: Request, background_tasks: BackgroundTasks, word: str):
    hdr = request.headers
    if "usr-sess" in hdr and "word-sess" in hdr:
        sid = hdr["word-sess"]
    else:
        
        background_tasks.add_task(write_log, message)
    print(app.secrets[day])
    if app.secrets[day].lower() == word.lower():
        word = app.secrets[day]
    rtn = {"guess": word}
    # check most similar
    if day in app.nearests and word in app.nearests[day]:
        rtn["sim"] = app.nearests[day][word][1]
        rtn["rank"] = app.nearests[day][word][0]
    else:
        try:
            rtn["sim"] = word2vec.similarity(app.secrets[day], word)
            rtn["rank"] = "1000위 이상"
        except KeyError:
            return jsonify({"error": "unknown"}), 404
    return jsonify(rtn)
"""
