import base64
import os
import sys
from datetime import datetime

class AgentTokenError(Exception):
    """Ошибка валидации JWT токена агента"""
    pass


def prepare_binary(name, data):
    import magic
    type = magic.from_buffer(data, mime=True)

    return {
        "name": name,
        "base64": base64.b64encode(data).decode('utf-8'),
        "type": type
    }


def prepare_file(filename):
    import magic
    import os

    type = magic.from_file(filename, mime=True)

    with open(filename, 'rb') as file:
        answer = {
            "name": filename.split(os.sep)[-1],
            "base64": base64.b64encode(file.read()).decode('utf-8'),
            "type": type
        }

    return answer

def gts():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S - ")

def safe(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GrpcConnectionError as e:
            raise e
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(gts(), exc_type, file_name, exc_tb.tb_lineno, e, "CRITICAL")
            return None

    wrapper.__name__ = func.__name__
    return wrapper


def decode_agent_token(token, api_key):
    """
    Расшифровывает JWT токен агента.
    
    Args:
        token (str): JWT токен из запроса
        api_key (str): API ключ агента для расшифровки
        
    Returns:
        dict or None: Расшифрованные данные токена или None при ошибке
        
    Example:
        payload = decode_agent_token(request_data.get('agent_token'), MY_API_KEY)
        if payload:
            contract_id = payload.get('contract_id')
            agent_id = payload['agent_id']
            roles = payload['roles']
    """
    try:
        import jwt
        return jwt.decode(token, api_key, algorithms=['HS256'])
    except ImportError:
        raise ImportError("PyJWT library required: pip install PyJWT")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def validate_agent_token(token, api_key):
    """
    Валидирует JWT токен агента и возвращает contract_id и роли.
    
    Args:
        token (str): JWT токен из запроса
        api_key (str): API ключ агента
        
    Returns:
        tuple: (contract_id, roles) - ID контракта (может быть None) и список ролей
        
    Raises:
        AgentTokenError: При любой ошибке валидации токена
        
    Example:
        try:
            contract_id, roles = validate_agent_token(
                request_data.get('agent_token'), 
                MY_API_KEY, 
                MY_AGENT_ID
            )
            # Обработка запроса
        except AgentTokenError as e:
            return jsonify({'error': str(e)}), 401
    """
    payload = decode_agent_token(token, api_key)
    
    if not payload:
        raise AgentTokenError("Invalid or expired token")
    
    if payload.get('type') != 'agent_access':
        raise AgentTokenError("Wrong token type")
    
    roles = payload.get('roles')
    if not roles:
        raise AgentTokenError("No roles in token")
    
    return payload.get('contract_id'), roles
