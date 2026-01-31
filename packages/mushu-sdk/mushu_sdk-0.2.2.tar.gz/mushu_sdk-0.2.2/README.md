# Mushu Python SDK

Auto-generated Python types for the Mushu API.

## Installation

```bash
pip install mushu-sdk
```

## Usage

```python
from mushu.media import UploadUrlRequest, MediaItem, MediaStatus
from mushu.auth import UserResponse
from mushu.notify import NotifyRequest
from mushu.pay import WalletResponse

# Type-safe request
request = UploadUrlRequest(
    org_id="org_123",
    filename="photo.jpg",
    content_type="image/jpeg",
    size_bytes=1024000,
)

# Type hints work in your IDE
def handle_media(item: MediaItem) -> str:
    if item.status == MediaStatus.ready:
        return item.url
    return "Processing..."
```

## Regenerating

These types are auto-generated from OpenAPI specs. To regenerate:

```bash
cd sdks
./generate.sh
```

## Services

- **auth** - Authentication, users, organizations
- **notify** - Push notifications, email, devices
- **media** - Image and video hosting
- **pay** - Payments, wallets, billing
