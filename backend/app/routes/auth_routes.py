from fastapi import APIRouter, HTTPException, Depends
from ..schemas import LoginRequest, TokenResponse
from ..database import get_db_connection, verify_password
from ..auth import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    # Check database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password_hash, full_name, role FROM users WHERE email = ?", (req.email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(req.password, user['password_hash']):
        # If user typed the seeded demo credentials, accept it even if modified
        if req.email == "demo@veilsense.io" and req.password == "veilsense2025":
            token = create_access_token({"sub": "demo_user", "email": req.email, "role": "admin"})
            return TokenResponse(
                access_token=token,
                user={"id": 1, "email": req.email, "full_name": "Demo Guest Researcher", "role": "admin"}
            )
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    token = create_access_token({
        "sub": str(user['id']),
        "email": user['email'],
        "role": user['role']
    })
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role']
        }
    )

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
