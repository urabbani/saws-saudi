"""
SAWS Alerts API Endpoints

Alert management and notification system.
"""

from datetime import datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.orm import selectinload

from app.dependencies import DBSession, UserId
from app.schemas.alert import (
    Alert,
    AlertCreate,
    AlertListResponse,
    AlertSeverity,
    AlertUpdate,
)
from app.models.alert import Alert as AlertModel

router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    db: DBSession,
    user_id: UserId,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    severity: AlertSeverity | None = None,
    is_read: bool | None = None,
    field_id: str | None = None,
) -> AlertListResponse:
    """
    List alerts for the user.

    Args:
        db: Database session
        user_id: Authenticated user ID
        skip: Number of records to skip
        limit: Maximum records to return
        severity: Filter by severity level
        is_read: Filter by read status
        field_id: Filter by field ID

    Returns:
        List of alerts with pagination metadata
    """
    # Build query
    stmt = select(AlertModel).where(AlertModel.user_id == user_id)

    # Apply filters
    if severity:
        stmt = stmt.where(AlertModel.severity == severity.value)
    if is_read is not None:
        stmt = stmt.where(AlertModel.is_read == is_read)
    if field_id:
        stmt = stmt.where(AlertModel.field_id == field_id)

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Apply pagination and ordering
    stmt = stmt.order_by(AlertModel.created_at.desc(), AlertModel.priority.desc())
    stmt = stmt.offset(skip).limit(limit)

    result = await db.execute(stmt)
    alerts = result.scalars().all()

    # Convert to response format
    items = [
        Alert(
            id=alert.id,
            user_id=alert.user_id,
            field_id=alert.field_id,
            severity=alert.severity,
            alert_type=alert.alert_type,
            title=alert.title,
            message=alert.message,
            district=alert.district,
            priority=alert.priority,
            data=alert.data,
            is_read=alert.is_read,
            read_at=alert.read_at,
            email_sent=alert.email_sent,
            sms_sent=alert.sms_sent,
            whatsapp_sent=alert.whatsapp_sent,
            created_at=alert.created_at,
            expires_at=alert.expires_at,
        )
        for alert in alerts
    ]

    return AlertListResponse(
        total=total,
        skip=skip,
        limit=limit,
        items=items,
    )


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: str,
    db: DBSession,
    user_id: UserId,
) -> Alert:
    """
    Get alert details by ID.

    Args:
        alert_id: Alert ID
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Alert details
    """
    stmt = select(AlertModel).where(
        and_(
            AlertModel.id == alert_id,
            AlertModel.user_id == user_id,
        )
    )

    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return Alert(
        id=alert.id,
        user_id=alert.user_id,
        field_id=alert.field_id,
        severity=alert.severity,
        alert_type=alert.alert_type,
        title=alert.title,
        message=alert.message,
        district=alert.district,
        priority=alert.priority,
        data=alert.data,
        is_read=alert.is_read,
        read_at=alert.read_at,
        email_sent=alert.email_sent,
        sms_sent=alert.sms_sent,
        whatsapp_sent=alert.whatsapp_sent,
        created_at=alert.created_at,
        expires_at=alert.expires_at,
    )


@router.post("", response_model=Alert, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    db: DBSession,
    user_id: UserId,
) -> Alert:
    """
    Create a new alert.

    Args:
        alert_data: Alert creation data
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Created alert
    """
    # Create new alert
    new_alert = AlertModel(
        id=uuid4().hex,
        user_id=user_id,
        field_id=alert_data.field_id,
        severity=alert_data.severity.value,
        alert_type=alert_data.alert_type.value,
        title=alert_data.title,
        message=alert_data.message,
        district=alert_data.district,
        priority=alert_data.priority,
        data=alert_data.data,
    )

    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    # Broadcast via WebSocket if available
    try:
        from app.api.v1.websocket import broadcast_alert
        await broadcast_alert(
            Alert(
                id=new_alert.id,
                user_id=new_alert.user_id,
                field_id=new_alert.field_id,
                severity=new_alert.severity,
                alert_type=new_alert.alert_type,
                title=new_alert.title,
                message=new_alert.message,
                district=new_alert.district,
                priority=new_alert.priority,
                data=new_alert.data,
                is_read=new_alert.is_read,
                read_at=new_alert.read_at,
                email_sent=new_alert.email_sent,
                sms_sent=new_alert.sms_sent,
                whatsapp_sent=new_alert.whatsapp_sent,
                created_at=new_alert.created_at,
                expires_at=new_alert.expires_at,
            ),
            user_id,
        )
    except Exception:
        pass  # WebSocket broadcast is optional

    return Alert(
        id=new_alert.id,
        user_id=new_alert.user_id,
        field_id=new_alert.field_id,
        severity=new_alert.severity,
        alert_type=new_alert.alert_type,
        title=new_alert.title,
        message=new_alert.message,
        district=new_alert.district,
        priority=new_alert.priority,
        data=new_alert.data,
        is_read=new_alert.is_read,
        read_at=new_alert.read_at,
        email_sent=new_alert.email_sent,
        sms_sent=new_alert.sms_sent,
        whatsapp_sent=new_alert.whatsapp_sent,
        created_at=new_alert.created_at,
        expires_at=new_alert.expires_at,
    )


@router.put("/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: str,
    alert_data: AlertUpdate,
    db: DBSession,
    user_id: UserId,
) -> Alert:
    """
    Update an existing alert.

    Args:
        alert_id: Alert ID
        alert_data: Alert update data
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Updated alert
    """
    stmt = select(AlertModel).where(
        and_(
            AlertModel.id == alert_id,
            AlertModel.user_id == user_id,
        )
    )

    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Update fields
    if alert_data.title is not None:
        alert.title = alert_data.title
    if alert_data.message is not None:
        alert.message = alert_data.message
    if alert_data.priority is not None:
        alert.priority = alert_data.priority
    if alert_data.is_read is not None:
        alert.is_read = alert_data.is_read
        if alert_data.is_read and not alert.read_at:
            alert.read_at = datetime.now()

    await db.commit()
    await db.refresh(alert)

    return Alert(
        id=alert.id,
        user_id=alert.user_id,
        field_id=alert.field_id,
        severity=alert.severity,
        alert_type=alert.alert_type,
        title=alert.title,
        message=alert.message,
        district=alert.district,
        priority=alert.priority,
        data=alert.data,
        is_read=alert.is_read,
        read_at=alert.read_at,
        email_sent=alert.email_sent,
        sms_sent=alert.sms_sent,
        whatsapp_sent=alert.whatsapp_sent,
        created_at=alert.created_at,
        expires_at=alert.expires_at,
    )


@router.put("/{alert_id}/read", response_model=Alert)
async def mark_alert_read(
    alert_id: str,
    db: DBSession,
    user_id: UserId,
) -> Alert:
    """
    Mark an alert as read.

    Args:
        alert_id: Alert ID
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Updated alert
    """
    stmt = select(AlertModel).where(
        and_(
            AlertModel.id == alert_id,
            AlertModel.user_id == user_id,
        )
    )

    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    alert.read_at = datetime.now()

    await db.commit()
    await db.refresh(alert)

    return Alert(
        id=alert.id,
        user_id=alert.user_id,
        field_id=alert.field_id,
        severity=alert.severity,
        alert_type=alert.alert_type,
        title=alert.title,
        message=alert.message,
        district=alert.district,
        priority=alert.priority,
        data=alert.data,
        is_read=alert.is_read,
        read_at=alert.read_at,
        email_sent=alert.email_sent,
        sms_sent=alert.sms_sent,
        whatsapp_sent=alert.whatsapp_sent,
        created_at=alert.created_at,
        expires_at=alert.expires_at,
    )


@router.put("/{alert_id}/unread", response_model=Alert)
async def mark_alert_unread(
    alert_id: str,
    db: DBSession,
    user_id: UserId,
) -> Alert:
    """
    Mark an alert as unread.

    Args:
        alert_id: Alert ID
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Updated alert
    """
    stmt = select(AlertModel).where(
        and_(
            AlertModel.id == alert_id,
            AlertModel.user_id == user_id,
        )
    )

    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = False
    alert.read_at = None

    await db.commit()
    await db.refresh(alert)

    return Alert(
        id=alert.id,
        user_id=alert.user_id,
        field_id=alert.field_id,
        severity=alert.severity,
        alert_type=alert.alert_type,
        title=alert.title,
        message=alert.message,
        district=alert.district,
        priority=alert.priority,
        data=alert.data,
        is_read=alert.is_read,
        read_at=alert.read_at,
        email_sent=alert.email_sent,
        sms_sent=alert.sms_sent,
        whatsapp_sent=alert.whatsapp_sent,
        created_at=alert.created_at,
        expires_at=alert.expires_at,
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: str,
    db: DBSession,
    user_id: UserId,
) -> None:
    """
    Delete an alert.

    Args:
        alert_id: Alert ID
        db: Database session
        user_id: Authenticated user ID
    """
    stmt = select(AlertModel).where(
        and_(
            AlertModel.id == alert_id,
            AlertModel.user_id == user_id,
        )
    )

    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()


@router.get("/stats/summary")
async def get_alert_stats(
    db: DBSession,
    user_id: UserId,
) -> dict:
    """
    Get alert statistics for the user.

    Returns counts of alerts by severity and read status.

    Args:
        db: Database session
        user_id: Authenticated user ID

    Returns:
        Alert statistics
    """
    # Get counts by severity
    severity_stmt = select(
        AlertModel.severity,
        func.count().label("count")
    ).where(
        AlertModel.user_id == user_id
    ).group_by(AlertModel.severity)

    severity_result = await db.execute(severity_stmt)
    by_severity = {row.severity: row.count for row in severity_result}

    # Get unread count
    unread_stmt = select(func.count()).where(
        and_(
            AlertModel.user_id == user_id,
            AlertModel.is_read == False
        )
    )
    unread_result = await db.execute(unread_stmt)
    unread = unread_result.scalar() or 0

    # Get total
    total_stmt = select(func.count()).where(AlertModel.user_id == user_id)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar() or 0

    return {
        "total": total,
        "unread": unread,
        "by_severity": by_severity,
    }
