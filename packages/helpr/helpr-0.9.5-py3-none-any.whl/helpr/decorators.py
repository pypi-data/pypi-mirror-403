from functools import wraps
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from .session_cache import SessionCache
from helpr.format_response import jsonify_failure, jsonify_success
from helpr.token_service import JWTHelper, TokenMissingError, TokenExpiredError, TokenInvalidError
from typing import Dict, Any
from helpr.secret_manager import JWTSigningKeyProvider

# Global key provider instance
_global_key_provider = None

def configure_auth(key_provider: JWTSigningKeyProvider):
    """Configure global key provider for all auth decorators"""
    global _global_key_provider
    _global_key_provider = key_provider

def get_global_key_provider() -> JWTSigningKeyProvider:
    """Get the configured key provider"""
    if _global_key_provider is None:
        raise ValueError("Auth not configured. Call configure_auth() first.")
    return _global_key_provider



def get_token(request: Request) -> Dict[str, Any]:
    """Get and verify JWT token from request."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    key_provider = get_global_key_provider()
    
    jwt_helper = JWTHelper(key_provider=key_provider)
    try:
        decoded_token = jwt_helper.verify_token(token=token)
        return decoded_token
    except TokenMissingError:
        raise HTTPException(status_code=401, detail={"message": "Authorization token is missing"})
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail={"message": "Authorization token has expired"})
    except TokenInvalidError as e:
        raise HTTPException(status_code=401, detail={"message": f"Invalid authorization token: {str(e)}"})
    except ValueError as ve:
        raise HTTPException(status_code=500, detail={"message": f"Configuration Error: {str(ve)}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": f"Error in get_token: {str(e)}"})
    

def auth_check_optional(f):
    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        # Initialize user state as None by default
        request.state.user_id = None
        request.state.medusa_user_id = None
        
        # Only try to get token if Authorization header is present and not empty
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.replace("Bearer ", "").strip()
        
        if token:  # Check if token exists and is not empty
            try:
                key_provider = get_global_key_provider()
                jwt_helper = JWTHelper(key_provider=key_provider)
                decoded_token = jwt_helper.verify_token(token=token)
                
                # Attach the user id to the request state
                request.state.user_id = decoded_token.get('sub')
                request.state.medusa_user_id = decoded_token.get('alt_sub')

            except TokenExpiredError:
                raise HTTPException(status_code=401, detail={"message": "Authorization token has expired"})

            except (TokenMissingError, TokenInvalidError, ValueError, Exception):
                # For optional auth, we silently continue without setting user info
                # User state remains None as initialized above
                pass
                
        # Call the original function with the updated request
        result = await f(request, *args, **kwargs)
        return result
    return decorated_function

def auth_check_required(f):
    @wraps(f)
    async def decorated_function(request: Request, *args, **kwargs):
        # Get token using global key provider
        decoded_token = get_token(request)
        
        # Attach the user id to the request state
        request.state.user_id = decoded_token.get('sub')
        request.state.medusa_user_id = decoded_token.get('alt_sub')
        
        # Call the original function with the updated request
        result = await f(request, *args, **kwargs)
        return result
    return decorated_function


def session_required(f):
    """
    DEPRECATED: This decorator is kept for backward compatibility only.
    New services should implement their own session_required decorator.

    For session validation in other services, use @validate_session instead.
    """
    @wraps(f)
    def decorated_function(request: Request, *args, **kwargs):
        session_visit_id = request.headers.get('X-CLY-SESSION-IDENTIFIER')
        if session_visit_id:
            session_visit_id = session_visit_id.split("#")
        original_session_id = session_visit_id[0] if session_visit_id and len(session_visit_id)>0 else None

        # Use session ID directly (no hashing)
        if original_session_id:
            session_id = original_session_id
        else:
            # No session identifier provided, create a new one
            client_id = request.headers.get('X-CLY-CLIENT-IDENTIFIER', None)
            session_id = SessionCache.create_session_id(client_id)

        request.state.session_id = session_id
        user_id = getattr(request.state, 'user_id', None)

        try:
            request.state.session_cache = SessionCache(session_id=session_id, user_id = user_id)
            visit_id, visit_count = request.state.session_cache.init_if_not_exists(client_id=request.headers.get('X-CLY-CLIENT-IDENTIFIER', None))
            request.state.visit_id = visit_id
            request.state.visit_count = visit_count
        except ValueError as e:
            return HTTPException(status_code=401, detail={"message": str(e)})

        # Call the original function
        result = f(request, *args, **kwargs)

        # Handle FastAPI response formatting
        if isinstance(result, dict):
            response = JSONResponse(content=result)
        elif isinstance(result, JSONResponse):
            response = result
        else:
            response = result

        # Add session headers to response
        if hasattr(response, 'headers'):
            response.headers['X-CLY-SESSION-IDENTIFIER'] = session_id + "#" + visit_id
            response.headers['X-CLY-VISIT-NUMBER'] = str(visit_count)

        return response

    return decorated_function


def validate_session(require_auth: bool = False):
    """
    Decorator to validate existing sessions in other services (NOT for session creation).

    This decorator reads session data from Redis and validates it.
    Use this in services that need to verify a session exists (order service, cart service, etc.).

    Args:
        require_auth: If True, requires user_id in session (authenticated session)

    Sets request.state attributes:
        - session_id: UUID of the session
        - session_data: Dict containing full session data
        - user_id: User ID from session (if authenticated)

    Usage:
        # In another service (order-service, cart-service, etc.)
        from helpr.decorators import validate_session

        @app.post("/orders")
        @validate_session(require_auth=True)
        async def create_order(request: Request):
            session_data = request.state.session_data
            user_id = request.state.user_id
            # ... business logic

    Raises:
        HTTPException: If session is missing, invalid, or auth requirements not met
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(request: Request, *args, **kwargs):
            # Extract session ID from header
            session_header = request.headers.get('X-CLY-SESSION-IDENTIFIER')
            if not session_header:
                raise HTTPException(
                    status_code=401,
                    detail={"message": "Session required. Please provide X-CLY-SESSION-IDENTIFIER header."}
                )

            # Parse session_id from header (format: session_id#visit_id)
            session_parts = session_header.split('#')
            session_id = session_parts[0] if session_parts else None

            if not session_id:
                raise HTTPException(
                    status_code=401,
                    detail={"message": "Invalid session identifier format"}
                )

            # Get Redis client from app state
            # Services must configure: app.state.redis_client = redis.Redis(...)
            redis_client = getattr(request.app.state, 'redis_client', None)
            if not redis_client:
                raise HTTPException(
                    status_code=500,
                    detail={"message": "Redis client not configured in app state"}
                )

            # Validate session exists in Redis
            try:
                session_cache = SessionCache(
                    session_id=session_id,
                    redis_client=redis_client
                )
                session_data = session_cache.to_dict()

                if not session_data or not session_data.get('session_id'):
                    raise HTTPException(
                        status_code=401,
                        detail={"message": "Invalid or expired session"}
                    )

                # Check authentication requirement
                user_id = session_data.get('user_id')
                if require_auth and not user_id:
                    raise HTTPException(
                        status_code=401,
                        detail={"message": "Authentication required for this operation"}
                    )

                # Inject session data into request state
                request.state.session_id = session_id
                request.state.session_data = session_data
                request.state.user_id = user_id

                # Call the actual endpoint
                return await f(request, *args, **kwargs)

            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail={"message": f"Error validating session: {str(e)}"}
                )

        return wrapper
    return decorator