"""
Audit services.

Provides log_event for writing audit trail entries, compute_lock_hash for
generating tamper-detection hashes, and verify_lock_integrity for checking
that locked records haven't been modified.
"""
import hashlib
import json

from apps.audit.models import AuditEvent, AuditLock


def log_event(actor, entity, action, before=None, after=None, request=None):
    """
    Create an AuditEvent for any state transition.

    Args:
        actor: User performing the action (can be None for system actions)
        entity: The model instance being acted upon (must have .organization or .organization_id)
        action: String describing the action (e.g. 'RECORD_APPROVED')
        before: Dict of state before the action
        after: Dict of state after the action
        request: Optional Django request for IP extraction
    """
    ip = None
    if request:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            ip = forwarded.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

    # Resolve organization
    org = getattr(entity, 'organization', None)
    if org is None and hasattr(entity, 'organization_id'):
        from apps.tenancy.models import Organization
        try:
            org = Organization.objects.get(id=entity.organization_id)
        except Organization.DoesNotExist:
            org = None

    if org is None:
        raise ValueError(
            f"Cannot log audit event: entity {entity.__class__.__name__} "
            f"has no organization."
        )

    return AuditEvent.objects.create(
        organization=org,
        actor=actor,
        entity_type=entity.__class__.__name__,
        entity_id=entity.pk,
        action=action,
        before_state=before or {},
        after_state=after or {},
        ip_address=ip,
    )


def compute_lock_hash(normalized_record):
    """
    Serialize NormalizedRecord fields to canonical JSON and return SHA-256 hex.

    This hash is stored in AuditLock and can be recomputed later to verify
    that the record hasn't been tampered with.
    """
    data = {
        'id': str(normalized_record.id),
        'raw_record_id': str(normalized_record.raw_record_id),
        'quantity_normalized': normalized_record.quantity_normalized,
        'unit_normalized': normalized_record.unit_normalized,
        'emission_scope': normalized_record.emission_scope,
        'source_type': normalized_record.source_type,
        'period_start': (
            normalized_record.period_start.isoformat()
            if normalized_record.period_start else None
        ),
        'period_end': (
            normalized_record.period_end.isoformat()
            if normalized_record.period_end else None
        ),
        'facility_or_entity': normalized_record.facility_or_entity,
        'review_status': normalized_record.review_status,
        'normalization_log': normalized_record.normalization_log,
    }
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def verify_lock_integrity(audit_lock):
    """
    Recompute hash of the locked record and compare to stored hash.

    Returns True if the record hasn't been tampered with since locking.
    """
    current_hash = compute_lock_hash(audit_lock.normalized_record)
    return current_hash == audit_lock.content_hash
