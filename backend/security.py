from pwdlib import PasswordHash
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.security import OAuth2PasswordBearer

oauth_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "this is a random secret key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 200

password_hash = PasswordHash.recommended()

def hash_password(password : str):
    try:
        hashed_password = password_hash.hash(password)
        
        return hashed_password
    
    except Exception as e:
        print(e)
        

def verify_password(stored_password : str, password : str):
    return password_hash.verify(password, stored_password)


def create_access_token(
    data : dict, 
    expires_delta : timedelta | None = None
) :
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
        
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode['exp'] = expire
    
    encode_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    
    return encode_jwt