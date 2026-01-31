# 🚀 BROKENXAPI

**Official Async Python SDK for BrokenX YouTube API**

<p align="center">
  <strong>Fast • Secure • Async • Production-Ready</strong>
</p>

---

## 📌 Overview

**BROKENXAPI** is the official asynchronous Python SDK for the **BrokenX YouTube API**,
designed for developers who want a **simple, secure, and scalable** way to search and download YouTube media via BrokenX’s backend infrastructure.

The SDK abstracts all backend complexity and exposes a **clean, minimal interface** that works with nothing more than an API key.

> ⚠️ Backend logic, infrastructure, and internal mechanisms are intentionally not exposed.

---

## ✨ Key Features

* ⚡ **Async-first** (built on `aiohttp`)
* 🔐 **Secure header-based authentication**
* 🧼 **Clean SDK interface** (no base URLs or backend details required)
* 🚫 **No logic exposure** (protected client implementation)
* 📦 **PyPI-ready & production-stable**
* 📡 **Telegram-backed media delivery**
* 🧠 **Rate-limit & usage tracking enforced server-side**

---

## 📦 Installation

Install directly from PyPI:

```bash
pip install BROKENXAPI
```

### Requirements

* Python **3.8+**
* Valid **BROKENXAPI** key
* Internet access

---

## 🔑 Authentication

BROKENXAPI uses **header-based authentication**.

You only need to provide your API key when creating the client.

```text
Authorization: Bearer YOUR_API_KEY
```

* API keys are issued by **Broken X Network**
* Never share your API key publicly
* Rate limits are enforced automatically

---

## 🚀 Quick Start

```python
import asyncio
from brokenxapi import BrokenXAPI

async def main():
    async with BrokenXAPI(
        api_key="BROKENXAPI-XXXX"
    ) as api:

        result = await api.search("Arijit Singh")
        print(result)

asyncio.run(main())
```

That’s it.
No base URL. No configuration. No setup noise.

---

## 🔍 Search API

Search YouTube content using BrokenX backend.

### Example

```python
await api.search("lofi beats", video=False)
```

### Parameters

| Name    | Type   | Description                     |
| ------- | ------ | ------------------------------- |
| `query` | `str`  | Search keyword                  |
| `video` | `bool` | `False` = audio, `True` = video |

### Response (Example)

```json
{
  "success": true,
  "status": "found",
  "title": "Lofi Beats",
  "video_id": "abcd1234",
  "duration": "3:24",
  "thumbnail": "https://...",
  "stream_url": "https://youtube.com/watch?v=abcd1234"
}
```

---

## ⬇️ Download API

Download audio or video using BrokenX’s processing pipeline.

### Audio Download

```python
await api.download("VIDEO_ID", media_type="audio")
```

### Video Download

```python
await api.download("VIDEO_ID", media_type="video")
```

### Notes

* Files are delivered via **Telegram hosting**
* Cached results may be returned instantly
* Backend handles format selection and optimization

---

## ⚠️ Error Handling

All SDK errors inherit from `BrokenXAPIError`.

```python
from brokenxapi.exceptions import BrokenXAPIError

try:
    await api.download("invalid_id")
except BrokenXAPIError as e:
    print("Error:", e)
```

### Common Errors

* Invalid API key
* Rate limit exceeded
* Backend processing failure
* Network errors

---

## 🧠 Design Philosophy

BROKENXAPI follows a **backend-first security model**:

* SDK = **thin, controlled client**
* Backend = **source of truth**
* Logic is intentionally protected
* API keys are validated server-side only

> Even if the SDK is copied, backend security remains intact.

---

## 📁 Documentation

Full documentation is available in the [`docs/`](./docs) directory:

* Installation
* Authentication
* Search API
* Download API
* Examples
* Changelog

---

## 🧩 Versioning

This project follows **semantic versioning**.

| Version | Meaning          |
| ------- | ---------------- |
| `MAJOR` | Breaking changes |
| `MINOR` | New features     |
| `PATCH` | Bug fixes        |

Current version: **v2.0.0**

---

## 📜 License

This project is licensed under the **MIT License**.

```
© 2025–2026 MR BROKEN
All Rights Reserved
```

---

## 🏁 Final Notes

* BROKENXAPI is designed for **developers, bots, and backend services**
* Not intended for browser-side usage
* Abuse, scraping, or misuse may result in key revocation

---

