# Public web release: Colombia Exam

Target URL: https://nt.es-pro.org/colombia/
Source repository: neuroteacher-examen.
Local Windows application and private learning history remain separate.

## Prepared implementation

- backend/web_app.py exposes the existing study API with an immutable shared bank and a small separate progress SQLite file per signed visitor cookie.
- Cookies are Secure, HttpOnly, SameSite=Lax and scoped to /colombia. Progress belongs to that browser; there is no claim of account or cross-device synchronization.
- Authoring and OpenAPI endpoints are not exposed. Foreign-origin writes are rejected.
- frontend/public/web-session.js completes a session handshake before application fetches, preventing parallel first requests from splitting browser progress.
- scripts/prepare_web_release.py packages static assets under /colombia, preserves source references, removes all progress rows and vacuums the seed. It never includes .env, credentials, the original private database, backup files or dependency caches.
- Only pure Python edge-tts 7.3.1, python-dotenv 1.2.2 and pypdf 6.15.0 are vendored off-host.
- The compose manifest reuses the existing approved lightweight backend image by exact image ID. No production image build or model installation is required.
- Runtime limits: 0.5 CPU, 256 MiB RAM, no additional swap, 64 PIDs, read-only root filesystem and writable /state only.
- nginx configuration is additive under /colombia; the NeuroTeacher API, website and other routes are retained. Update the company product link only after public acceptance.

## Resource gate observed before publication

The existing production /health endpoint returns 200. /health/ready returns 503 with storage_free_space_below_gate.
Observed available root storage: approximately 4.18 billion bytes (3.9 GiB).
Required by the production readiness check: 6,442,450,944 bytes (6 GiB).
This shortfall exists before this application is uploaded. The 50 GiB virtual disk is already partitioned; there is no unallocated capacity to grow into.
Docker build cache is empty, and image/volume reclaim estimates do not cover the shortfall. No broad prune, backup deletion, reduced gate, reduced filesystem reserve or unrelated cleanup has been performed.

Public activation must remain pending until normal readiness passes with enough additional room for the release and rollback material. Do not remove protected or retained production backups merely to publish this application.

## Release procedure after readiness passes

1. Run test_web_isolation.py against the desktop bank; run the existing locale/content/browser regressions off-host.
2. Commit the prepared source, then run prepare_web_release.py --database PATH. Preserve the generated release manifest and archive checksum.
3. Transfer the immutable release to a new /opt/colombia-exam/releases/SHA directory; verify every manifest checksum.
4. Set /var/lib/colombia-exam ownership to UID/GID 10001. Create a root-only /etc/colombia-exam.env containing the selected AI provider configuration and a newly generated COLOMBIA_SESSION_SECRET of at least 32 characters. Never put it in the release archive or Git.
5. Pin COLOMBIA_IMAGE to the already installed approved runtime image ID, set COLOMBIA_RELEASE_DIR, and start the bounded compose service. Run small loopback API checks.
6. Back up nginx configuration. Install the HTTP rate zones and the /colombia locations, run nginx -t, then reload.
7. From an off-host browser verify static paths, both PDFs, all four translated question locales, real TTS, all 24 translated recordings and isolation between two independent browser contexts.
8. Recheck the original NeuroTeacher /health, /health/ready and /company/. Only then update the company product link.

Rollback: stop only the Colombia compose project, restore the saved nginx configuration and company page, validate and reload nginx. Preserve visitor state and existing NeuroTeacher images/data.

## Verification completed during preparation

The targeted test_web_isolation.py passed: two visitors have separate attempts; a forged cookie cannot read existing progress; the shared bank stays unchanged; answer keys remain hidden; authoring is blocked. The original desktop history checksum is unchanged.

This document records a prepared release, not proof that the public URL is live.
