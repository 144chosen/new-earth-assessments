"""Local owner preview. Install server/requirements.txt, then run this file."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT/'server'))
os.environ['NEU_MODE']='preview'
os.environ['NEU_PUBLIC_URL']='http://127.0.0.1:8765'
from app import create_app
if __name__=='__main__':
 print('Open http://127.0.0.1:8765/heritage in your browser. Preview payments are disabled.')
 create_app().run(host='127.0.0.1',port=8765,debug=False)
