from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from app.database import get_db
from app.models import User, Friendship
from app.schemas import FriendshipCreate, FriendshipRespond, FriendshipOut
from app.routers.users import get_current_user
from typing import List

router = APIRouter(prefix="/friends", tags=["Friends"])

# 1. Send Friend Request
@router.post("/request", status_code=201)
async def send_friend_request(
    request: FriendshipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if request.receiver_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot add yourself.")

    # Check if receiver exists
    result = await db.execute(select(User).where(User.id == request.receiver_id))
    receiver = result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found.")

    # Check for existing request or friendship
    result = await db.execute(
        select(Friendship).where(
            ((Friendship.sender_id == current_user.id) & (Friendship.receiver_id == request.receiver_id)) |
            ((Friendship.sender_id == request.receiver_id) & (Friendship.receiver_id == current_user.id))
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Friend request already exists or you're already friends.")

    friendship = Friendship(
        sender_id=current_user.id,
        receiver_id=request.receiver_id,
        status="pending"
    )
    db.add(friendship)
    await db.commit()
    return {"message": "Friend request sent."}


# 2. Respond to Friend Request (Accept/Reject)
@router.post("/respond")
async def respond_to_request(
    response: FriendshipRespond,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Friendship).where(
            (Friendship.sender_id == response.sender_id) &
            (Friendship.receiver_id == current_user.id) &
            (Friendship.status == "pending")
        )
    )
    friendship = result.scalar_one_or_none()
    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found.")

    if response.action.lower() == "accept":
        friendship.status = "accepted"
    elif response.action.lower() == "reject":
        friendship.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'accept' or 'reject'.")

    await db.commit()
    return {"message": f"Friend request {response.action.lower()}ed."}


# 3. Get Friend List
@router.get("/list", response_model=List[FriendshipOut])
async def get_friends(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Friendship).where(
        (Friendship.status == "accepted") &
        ((Friendship.sender_id == current_user.id) | (Friendship.receiver_id == current_user.id))
    )
    result = await db.execute(stmt)
    friendships = result.scalars().all()

    # Convert to FriendshipOut list
    friend_out_list = []
    for f in friendships:
        friend_id = f.receiver_id if f.sender_id == current_user.id else f.sender_id
        friend_result = await db.execute(select(User).where(User.id == friend_id))
        friend = friend_result.scalar_one_or_none()
        if not friend:
            continue

        friend_out_list.append(FriendshipOut(
            id=f.id,
            friend_id=friend.id,
            friend_username=friend.username,
            status=f.status,
            created_at=f.created_at
        ))

    return friend_out_list


# 4. Remove Friend
@router.delete("/remove/{friend_id}")
async def remove_friend(
    friend_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Friendship).where(
        ((Friendship.sender_id == current_user.id) & (Friendship.receiver_id == friend_id)) |
        ((Friendship.sender_id == friend_id) & (Friendship.receiver_id == current_user.id))
    )
    result = await db.execute(stmt)
    friendship = result.scalar_one_or_none()

    if not friendship or friendship.status != "accepted":
        raise HTTPException(status_code=404, detail="Friendship not found.")

    await db.delete(friendship)
    await db.commit()
    return {"message": "Friend removed."}


# 5. View Incoming Friend Requests
@router.get("/requests/incoming", response_model=List[FriendshipOut])
async def get_incoming_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Friendship).where(
        (Friendship.receiver_id == current_user.id) &
        (Friendship.status == "pending")
    )
    result = await db.execute(stmt)
    requests = result.scalars().all()

    pending_list = []
    for f in requests:
        sender_result = await db.execute(select(User).where(User.id == f.sender_id))
        sender = sender_result.scalar_one_or_none()
        if not sender:
            continue

        pending_list.append(FriendshipOut(
            id=f.id,
            friend_id=sender.id,
            friend_username=sender.username,
            status=f.status,
            created_at=f.created_at
        ))

    return pending_list



# 6. Cancel Sent Friend Request
@router.delete("/request/cancel/{receiver_id}")
async def cancel_sent_request(
    receiver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Friendship).where(
        (Friendship.sender_id == current_user.id) &
        (Friendship.receiver_id == receiver_id) &
        (Friendship.status == "pending")
    )
    result = await db.execute(stmt)
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(status_code=404, detail="Pending friend request not found.")

    await db.delete(friendship)
    await db.commit()
    return {"message": "Friend request canceled."}
