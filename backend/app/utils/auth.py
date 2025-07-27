from passlib.context import CryptContext
from datetime import datetime, timedelta,timezone
from jose import jwt, JWTError
from fastapi import HTTPException
from app.config import (
    SECRET_KEY,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ALGORITHM
)
from logging import basicConfig,getLogger,INFO



#PASSWORD HASHING

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")# deprecated is not actually part of the cryptcontext but my own keyword argument that i give due to **kwds


class Hasher:
    @staticmethod
    def verify_password(plain_password:str ,hashed_password:str) ->bool:
        return pwd_context.verify(plain_password,hashed_password)
    

    @staticmethod
    def hash_password(password:str) ->str:
        return pwd_context.hash(password)
    





# TOKEN CREATION
class Token:
    #logging setup
    basicConfig(level=INFO)
    logger = getLogger(__name__)




    #error checking for token data is dictionary or not : 400
    @staticmethod
    def check_valid(data):
        if not isinstance(data,dict):
            Token.logger.error("Invalid data format for token creation. Expected a dictionary.")
            raise HTTPException(status_code=400,detail="Invalid data formmat. Expected a dictionary.")
        

    
    #error func for invalid token :401
    @staticmethod
    def invalid_expired_token(e):#e is excepion object. will be a jwt error : 401
        Token.logger.error(f"Token error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    

      #for a missing required claim 401
    @staticmethod
    def missing_claim(claim):
        Token.logger.warning(f"Missing required claim: {claim}")
        raise HTTPException(status_code=401, detail=f"Missing required claim: {claim}")
    

    #error func for invalid refresh token :401
    @staticmethod
    def invalid_refresh_token(e):
        Token.logger.warning("Token is not a refresh token.")
        raise HTTPException(status_code=401, detail="Invalid token type.")



    # for an unexpected error during creation : 500
    @staticmethod
    def unexpected_error(e): # e is exception object
        Token.logger.error(f"Unexpected error during token creation: {e}")
        raise HTTPException(status_code=500,detail="An error occurred while creating the access token.")  


    # for an unexpected error during decoding : 500,same as during creation but to differentiate
    @staticmethod
    def unexpected_error_decode(e): # e is exception object
        Token.logger.error(f"Unexpected error during token decoding: {e}")
        raise HTTPException(status_code=500,detail="An error occurred while decoding the access token.")
    

    # for an unexpected error during validating : 500,same as during creation,decoding but to differentiate
    @staticmethod
    def unexpected_error_val(e): # e is exception object
        Token.logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(status_code=500,detail="An error occurred while validating the access token.")
    

    # for an unexpected error during verifying refresh token : 500,same as during creation,decode,validating but to differentiate
    @staticmethod
    def unexpected_error_ver(e): # e is exception object
        Token.logger.error(f"Unexpected error during refresh token verification: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while verifying the refresh token.")
    





    @staticmethod
    def create_access_token(data:dict)->str:
        '''create a token for logging in'''
        
        Token.check_valid(data)# check for invalid data format and httpexception 400

        try:
            to_encode=data.copy()
            expire=datetime.now(timezone.utc) +timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp":expire, "type": "access"})

            encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
            return encoded_jwt #this is the encoded json web token in str
        
        except Exception as e:#for an unexpected error duirng creation of first token and httpexception 500
            Token.unexpected_error(e)
    

    @staticmethod
    def create_refresh_token(data:dict) ->str:
        ''' Create a long-lived refresh token.'''

        Token.check_valid(data)#check for invalid data format and httpexception 400

        try:
            to_encode = data.copy()
            expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            to_encode.update({"exp": expire,"type": "refresh"})

            encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
            return encoded_jwt# will be str
        
        except Exception as e: #for an unexpected error during creation of refresh token and httpexception 500
            Token.unexpected_error(e)







    @staticmethod
    def decode_token(token:str)->dict:
        '''Decode a token (access or refresh).'''
        try:
            payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
            return payload# this is the decoded token in dict format
        
        except JWTError as e: # for an inavalid/expired token and httpexcepton 401
            Token.invalid_expired_token(e)

        except Exception as e:
            Token.unexpected_error_decode(e)#unexpected error during validating and httpexception 500
    


    @staticmethod
    def validate_tokens(token:str, required_claims:list=None)->dict:
        ''' Validate a token and ensure required claims are present.'''

        try:
            payload=Token.decode_token(token)
            #validate required claims
            if required_claims:#meaning if there are any claims or not
                for claim in required_claims:
                    if claim not in payload:
                        Token.missing_claim(claim)# warning for a missing claim and httpexception 401
            return payload
        except HTTPException:
            raise
        except Exception as e:
            Token.unexpected_error_val(e)# error func for unexpected error during validation and httpexception 500


    @staticmethod
    def verify_refresh_token(token:str)-> dict:
        '''Decode and validate a refresh token specifically.'''

        try:
            payload=Token.decode_token(token)
            if payload.get("type") != "refresh":
                Token.invalid_refresh_token(e)# error if token is not refresh so invalid and httpexception 401
            return payload
        except HTTPException:
            raise
        except Exception as e:
            Token.unexpected_error_ver(e)
