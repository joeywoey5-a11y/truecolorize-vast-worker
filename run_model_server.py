import uvicorn
from model_server import app
if __name__=="__main__": uvicorn.run(app,host="127.0.0.1",port=18000,log_level="info")
