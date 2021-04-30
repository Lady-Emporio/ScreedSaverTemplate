
import requests
import datetime
from bs4 import BeautifulSoup
from sqlalchemy import Table, Column,DateTime, Integer, String, MetaData, ForeignKey, create_engine,select
from sqlalchemy.orm import mapper,sessionmaker
import time

URL="https://wallpaperscraft.ru/catalog/food/downloads/1920x1080"
GROUP="food"
#######################################################################################
#######################################################################################
###############################         SQL         ###################################
#######################################################################################
#######################################################################################

metadata = MetaData()
users_table = Table('images', metadata,
    Column('id', Integer, primary_key=True),
    Column('pathToImage', String),
    Column('type', String),
    Column('rating', Integer),
    Column('url', String),
    Column("createDate",DateTime, default=datetime.datetime.utcnow)
)
class ImSave(object):
    def __init__(self, pathToImage, url,group):
        self.pathToImage = pathToImage
        self.rating = 0
        self.url = url
        self.group = group

mapper(ImSave, users_table) 
echo=False
engine = create_engine('sqlite:///./imagesМ.sqlite', echo=echo, connect_args={'timeout': 30})
metadata.create_all(engine)

def downloadImage(url,group):
    url=url.replace("_300x168","_1920x1080")

    if alreadyUseUrl(url):
        return
    r=requests.get(url)
    if 200!=r.status_code:
        print("problem with:"+url)
    names=url.rpartition("/")
    name=names[2]
    with open("./images/"+name,"wb") as f:
        f.write(r.content)
    Session = sessionmaker(bind=engine)
    session = Session()
    imsave = ImSave(name, url,group)
    session.add(imsave)
    session.commit()
    time.sleep(1)

def alreadyUseUrl(url):
    session = sessionmaker(bind=engine)()
    stmt = select(ImSave).where(ImSave.url == url)
    result = session.execute(stmt)
    sqlalchemyEngineRowRow=result.fetchone()
    if(sqlalchemyEngineRowRow==None):
        print(f"------- new {url}")
        return False
    imsave=sqlalchemyEngineRowRow["ImSave"]
    print(f"--- adready download: '{imsave.url} in {imsave.createDate}'")
    return True
    
print("Begin")
for i in range(1,200):
    r=requests.get(URL+"/page"+str(i))
    print(r.url)
    if(200!=r.status_code):
        print(f"wtf with status_code: {r.status_code}.")
    soup = BeautifulSoup (r.content, 'html.parser')
    img_wallpapers__image=soup.select(".wallpapers__image")
    if(len(img_wallpapers__image)!=15):
        print("!!!!!!!!!!!!!! problem with l")
    for imageTag in img_wallpapers__image:
        src=imageTag.attrs["src"]
        downloadImage(src,GROUP)

print("End")
