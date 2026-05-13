# -*- coding: utf-8 -*-
"""
Created on Sun May 10 13:04:53 2026

@author: Olive
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.analyse  import router as analyse_router
from api.routes.interact import router as interact_router
from api.routes.export   import router as export_router
from api.routes.progress import router as progress_router

import asyncio

app = FastAPI(title="Music Analyser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyse_router,  prefix="/api")
app.include_router(interact_router, prefix="/api")
app.include_router(export_router,   prefix="/api")
app.include_router(progress_router, prefix="/api")

@app.on_event("startup")
async def startup():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)