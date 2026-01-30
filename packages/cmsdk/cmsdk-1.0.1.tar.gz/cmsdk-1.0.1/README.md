# JSONApp Python SDK

> **Note**: This is the Python port of the JSONApp SDK. This repository is a monorepo containing multiple language implementations. See the [root README](../README.md) for an overview.

A stateless backend library for building views that are sent to renderers (mobile or web). This is the Python port of the TypeScript JSONApp SDK.

## Features

- **Stateless Architecture**: No internal state, perfect for serverless and microservices
- **Ed25519 Signing**: Secure view signing and verification using Ed25519 cryptography
- **12 View Types**: Form, Reader, ActionList, ActionGrid, QRScan, QRDisplay, Message, Card, Carousel, Timeline, Media, Map
- **Type Safety**: Full type definitions using Python dataclasses and type hints
- **Validation**: Built-in field and form validation
- **Security**: XSS protection, URL validation, input sanitization

## Installation

```bash
pip install cmsdk
```

## Quick Start

```python
from cmsdk import JsonApp, JsonAppConfig
from cmsdk.views import FormView

# Initialize JsonApp
config = JsonAppConfig(
    app_id="my-app",
    view_expiration_minutes=60,
)
app = JsonApp(config)

# Create a form view
form = app.create_form_view("registration", "User Registration")
form.add_text_field("name", "Full Name", is_required=True)
form.add_email_field("email", "Email", is_required=True)
form.submit_button("Register")

# Serve with signature
response = app.serve(form)
print(response.view)  # The view JSON
print(response.signature)  # Ed25519 signature
```

## View Types

### FormView
Create forms with various field types (text, email, password, select, file, GPS, etc.)

### ReaderView
Display rich content with paragraphs, images, markdown, tables, code blocks, etc.

### ActionListView / ActionGridView
Display lists or grids of actions

### QRScanView / QRDisplayView
QR code scanning and display

### MessageView
Display messages with actions

### CardView
Display card-based content with stats and sections

### CarouselView
Display carousel slides

### TimelineView
Display chronological events

### MediaView
Display audio and video playlists

### MapView
Display geographic data on maps

## API Parity

The Python SDK maintains API parity with the TypeScript version:

- Same factory methods: `app.create_form_view()`, `app.create_reader_view()`, etc.
- Same fluent API: `view.add_field().set_intro().submit_button()` (or `set_note()` for backward compatibility)
- Same validation and security features
- Same Ed25519 signing and verification

## Examples

See `examples/basic_usage.py` for a complete example.

## Requirements

- Python 3.10+
- cryptography (for Ed25519)
- markdown (for ReaderView markdown support)
- bleach (for HTML sanitization)

## Status

✅ Core classes (BaseView, JsonApp)  
✅ All 12 view types  
✅ Type definitions  
✅ Error handling  
✅ Validation utilities  
✅ Ed25519 signing/verification  
✅ Examples  


## License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
