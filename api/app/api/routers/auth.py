"""Authentication routes."""
from fastapi import APIRouter, status

from app.api.deps import CurrentUserId, DatabaseSession
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: DatabaseSession,
):
    """Register a new user."""
    service = AuthService(session)
    user, access_token, refresh_token = await service.register(
        email=data.email,
        password=data.password,
    )
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at.isoformat(),
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    session: DatabaseSession,
):
    """Login user and return tokens."""
    service = AuthService(session)
    user, access_token, refresh_token = await service.login(
        email=data.email,
        password=data.password,
    )
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at.isoformat(),
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    session: DatabaseSession,
):
    """Refresh access token using refresh token."""
    service = AuthService(session)
    new_access_token, new_refresh_token = await service.refresh(data.refresh_token)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user_id: CurrentUserId,
    session: DatabaseSession,
):
    """Logout user by revoking refresh tokens."""
    service = AuthService(session)
    await service.logout(user_id)
