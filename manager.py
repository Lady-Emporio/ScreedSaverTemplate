import os
import sys
import win32api as api
import win32con as con
import win32gui as gui
import win32ts as ts
from multiprocessing import Process
from sqlalchemy.sql import func
import winreg
import time
import ctypes

import datetime

from sqlalchemy import Table, Column,DateTime,Boolean, Integer, String, MetaData, ForeignKey, create_engine,select
from sqlalchemy.orm import mapper,sessionmaker
from sqlalchemy.ext.declarative import declarative_base

#shell:startup 
#open in explorer
DIR="D:\\screenSaver\\PyVersion\\"
IMAGES_DIR=DIR+"images\\"

Base = declarative_base()
class ImSave(Base):
    __tablename__ = 'images'
    id = Column('id', Integer, primary_key=True)
    pathToImage = Column('pathToImage', String)
    url = Column('url', String)
    createDate = Column("createDate",DateTime, default=datetime.datetime.utcnow)

class NextIm(Base):
    __tablename__ = 'nextIm'
    id = Column('id', Integer, primary_key=True)
    image = Column("image", ForeignKey("images.id"), nullable=False)

class Log(Base):
    __tablename__ = 'log'
    id = Column('id', Integer, primary_key=True)
    message = Column('message', String)
    isError = Column('isError', Boolean)  
    addDataInt = Column('addDataInt', Integer) 
    now = Column("now",DateTime, default=datetime.datetime.utcnow)

echo=True
#engine = create_engine('sqlite:///./imagesМ.sqlite', echo=echo, connect_args={'timeout': 30})
engine = create_engine(f"sqlite:///{DIR}imagesМ.sqlite", echo=echo, connect_args={'timeout': 30})
Base.metadata.create_all(engine)

def log(message,isError=False,addDataInt=-1):
    session = sessionmaker(bind=engine)()
    log=Log()
    log.message=message
    log.isError=isError
    log.addDataInt=addDataInt
    session.add(log)
    session.commit()

def rechargeNextIm():
    log(f"rechargeNextIm.")
    session = sessionmaker(bind=engine)()
    result=session.query(ImSave).all()
    for imsave in result:
        nextIm=NextIm()
        nextIm.image=imsave.id
        session.add(nextIm)
    session.commit()
    
def getNextImage():
    session = sessionmaker(bind=engine)()
    nextIm=session.query(NextIm).order_by(func.random()).first()
    if None==nextIm:
        rechargeNextIm()
        nextIm=session.query(NextIm).order_by(func.random()).first()
        if None==nextIm:
            log("Error with rechargeNextIm. Mayby images empty.",True)

    image=session.query(ImSave).get(nextIm.image)

    session = sessionmaker(bind=engine)()
    session.query(NextIm).filter(NextIm.id==nextIm.id).delete()
    session.commit()

    return image




# window messages
WM_WTSSESSION_CHANGE        = 0x2B1
# WM_WTSSESSION_CHANGE events (wparam)
WTS_CONSOLE_CONNECT        = 0x1
WTS_CONSOLE_DISCONNECT        = 0x2
WTS_REMOTE_CONNECT        = 0x3
WTS_REMOTE_DISCONNECT        = 0x4
WTS_SESSION_LOGON        = 0x5
WTS_SESSION_LOGOFF        = 0x6
WTS_SESSION_LOCK        = 0x7
WTS_SESSION_UNLOCK        = 0x8
WTS_SESSION_REMOTE_CONTROL    = 0x9

def changeLockScreenImage():

    image=getNextImage()
    pathToImage=IMAGES_DIR+image.pathToImage

    log("changeLockScreenImage id: '{image.id}', --- '{pathToImage}'",False,image.id)

    keyval="SOFTWARE\\Policies\\Microsoft\\Windows\\Personalization"
    Registrykey= winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, keyval, 0,winreg.KEY_WRITE)
    winreg.SetValueEx(Registrykey,"LockScreenImage",0,winreg.REG_SZ,pathToImage)
    winreg.CloseKey(Registrykey)

def changeBackgroundImage():

    image=getNextImage()
    pathToImage=IMAGES_DIR+image.pathToImage

    log("changeBackgroundImage id: '{image.id}', --- '{pathToImage}'",False,image.id)

    SPI_SETDESKWALLPAPER = 20 
    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, pathToImage , 0)

class Monitor():
    className = "Monitor"
    wndName = "Monitor"
    def __init__(self):
        wc = gui.WNDCLASS()
        wc.hInstance = hInst = api.GetModuleHandle(None)
        wc.lpszClassName = self.className
        wc.lpfnWndProc = self.WndProc
        self.classAtom = gui.RegisterClass(wc)

        style = 0
        self.hWnd = gui.CreateWindow(self.classAtom, self.wndName,
            style, 0, 0, con.CW_USEDEFAULT, con.CW_USEDEFAULT,
            0, 0, hInst, None)
        gui.UpdateWindow(self.hWnd)

        # you can optionally use ts.NOTIFY_FOR_ALL_SESSIONS
        ts.WTSRegisterSessionNotification(self.hWnd, ts.NOTIFY_FOR_THIS_SESSION)

        log("Monitor init")
        changeLockScreenImage()
        changeBackgroundImage()

    def WndProc(self, hWnd, message, wParam, lParam):
        if message == WM_WTSSESSION_CHANGE:
            self.OnSession(wParam, lParam)
        elif message == con.WM_CLOSE:
            gui.DestroyWindow(hWnd)
        elif message == con.WM_DESTROY:
            gui.PostQuitMessage(0)
        elif message == con.WM_QUERYENDSESSION:
            return True

    def OnSession(self, event, sessionID):
        print("event 0x%x on session %d" % (event, sessionID))

        #if sessionID == ts.ProcessIdToSessionId(os.getpid()):

        # Since you already have a Python script, you can use it here directly.
        # Otherwise, replace this with something involving subprocess.Popen()
        #raise NotImplemented

        if WTS_SESSION_LOCK==event:
            self.sessionLock(sessionID)
        elif WTS_SESSION_UNLOCK==event:
            self.sessionUnlock(sessionID)

    def sessionLock(self,sessionID):
        print("Заблокировал экран")
        changeBackgroundImage()
        

    def sessionUnlock(self,sessionID):
        print("Разблокировал экран")
        changeLockScreenImage()

if __name__ == '__main__':
    log("Script start")
    Monitor()
    gui.PumpMessages()
