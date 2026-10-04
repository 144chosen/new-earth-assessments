NEW EARTH UNIVERSITY — TWO CONNECTED ASSESSMENTS
Version 1.0 · prepared October 3, 2026

WHAT IS INCLUDED
A free Celestial Heritage Assessment with 30 questions, 19 illustrated founder / guardian expressions, multiple matches, source-based celestial context, and a plain-language glossary. The wider supplied race list is retained as a reference catalogue. Orders, collectives, and race expressions are identified as different categories.

A separate $29 purpose assessment, The 144,000: Discover Your Role. It uses the earlier answer themes, asks 20 questions across ten areas of service, then 18 specific questions across the strongest three areas. All 60 supplied roles are represented. Practical questions cover experience, preferred employment/business route, visibility, available time, income urgency, obstacles, and optional hardships, skills, audience, and intention.

Personal results include three role matches, relevant spiritual and conventional career options, training considerations, a first-month plan, and a branded five-page PDF download. The report incorporates the heritage results and optional birth-pattern reflection. It does not invent hardship, qualifications, a destined trauma story, or a verified cosmic ancestry.

The visual design uses deep blue, champagne gold, ivory, editorial serif headings, clear sans-serif text, and the supplied New Earth University images. It follows the website’s themes of consciousness, creation, and embodiment. The small star emblem is an assessment design element, not a claim to be the official university logo.

QUICK REVIEW — NO INSTALLATION
Open review/interactive-owner-preview.html in a browser to explore both quizzes. This is an owner-only demonstration with no payments, birth calculations, or transmitted answers. Its PDF button opens the clearly labeled fictional sample, not a report based on the demo answers. The full running service generates personal PDFs and real birth calculations. Do not publish this owner demo as a paid assessment.

QUICK OWNER PREVIEW — FULL RUNNING SERVICE
1. Unzip the package.
2. Install Python 3.12 or newer.
3. From this folder, create a virtual environment:
   python -m venv .venv
   Activate it on macOS/Linux: source .venv/bin/activate
   Activate it on Windows: .venv\Scripts\activate
4. Install the tested dependencies:
   python -m pip install -r server/requirements.txt
5. Run:
   python start_preview.py
6. Open http://127.0.0.1:8765/heritage

Preview mode is restricted to localhost. Complete the free quiz, then click the clearly labeled “Preview paid assessment · no charge” button. No money is collected and no payment credentials are included. You can enter birth coordinates/time zone manually; the public place-search integration requires a genuine contact User-Agent before use. The included JPL ephemeris enables real birth calculations in the preview.

The sample PDF uses a fictional participant and is a review example, not a personalized report for Elizabeth. Screenshot previews show the completed application, including mobile results. The local service must be running for the functional HTML to work; this is not one static HTML file that can securely process payments on its own.

PUT IT INTO KAJABI
1. Deploy the included Python service to an HTTPS host with persistent disk storage. A host that can run a Docker container is suitable; build from this folder using:
   docker build -f server/Dockerfile -t neu-assessments .
   Mount persistent storage at /data and supply the environment variables from server/.env.example through the host’s secret settings.
   The container listens on port 8080. Configure the host’s health check to use /api/config.
2. Prefer a same-site domain such as quiz.newearthuniversity.org. This helps the free and paid assessment keep a private session in browsers that restrict storage in third-party frames. Configure DNS and HTTPS for the actual host before copying the embeds.
3. Generate one persistent encryption key privately on your host:
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   Save it as NEU_DATA_KEY in your host’s secret environment. Keep the key and database protected and backed up together. Rotating/deleting the key without migration makes existing encrypted records unreadable.
4. Set NEU_MODE=production and NEU_PUBLIC_URL to your actual HTTPS assessment origin.
5. Set NEU_DB=/data/assessments.sqlite3. Run server/maintenance.py daily. Keep NEU_TRUST_PROXY=0 unless your host strips untrusted forwarded headers and you have deliberately configured a trusted reverse proxy.
6. Configure Square as described below, first in Sandbox, then in production after a real test purchase/refund.
7. Generate embeds for your actual service origin:
   python build_embeds.py --url https://quiz.newearthuniversity.org
8. Create two separate Kajabi landing pages. Add a Custom Code block to each. Paste kajabi/heritage-embed.html into the free page and kajabi/purpose-embed.html into the purpose page. Remove a duplicate Kajabi page title if it crowds the assessment.
9. Publish the pages only after testing the live service. The embeds do not install the Python service, configure DNS, or connect a payment account by themselves.

SQUARE — INCLUDED PAYMENT INTEGRATION
Create a Square developer application. Use the access token and location ID from your own account in the host’s secret environment. Never put them into Kajabi code, public JavaScript, or a chat message.

Sandbox setup:
SQUARE_ENV=sandbox
SQUARE_ACCESS_TOKEN=<your sandbox token>
SQUARE_LOCATION_ID=<your sandbox location>
SQUARE_WEBHOOK_SIGNATURE_KEY=<your subscription signature key>
SQUARE_WEBHOOK_URL=https://your-assessment-domain/api/webhooks/square

Subscribe to payment.created, payment.updated, refund.created, and refund.updated. The notification URL must match SQUARE_WEBHOOK_URL exactly; Square signs the URL together with the raw request body. The service verifies the signature and rechecks the order/payment with Square.

The server creates a Square-hosted checkout for one $29.00 USD item, binds the resulting order ID to the private assessment session, and unlocks only a completed payment with the correct order, location, amount, and currency and no refund. It does not accept ?paid=true, a browser flag, a supplied amount, or a checkout redirect as payment proof. Repeated checkout clicks reuse the same idempotency key/link. Repeated webhook events are handled idempotently. Current payment state is checked again before paid content and PDF access. Square Quick Pay can leave a paid digital order OPEN; the service accepts OPEN or COMPLETED order state only when the associated Payment is COMPLETED. It resolves both Tender.payment_id and Tender.id according to the provider response.

The checkout link opens as a top-level secure checkout from the Kajabi embed. The return route is the standalone /purpose screen on the assessment service, which carries the same New Earth branding. Returning in the same browser uses the saved private session; a visitor can also restore their access key from another device.

Production setup uses SQUARE_ENV=production and production credentials. No live payments, external account settings, or publishing were performed while building this package. The configured product is $29.00 USD with no tips, discounts, shipping, or extra taxes in the supplied checkout request; review your actual tax configuration and any tax requirements with the person responsible for your commerce setup before launch. Do not reuse an existing higher-priced course checkout.

NATIVE KAJABI PAYMENTS
This package uses Square as the operational payment provider while Kajabi hosts your pages. A native Kajabi Offer checkout has not been wired into this build. If you prefer Kajabi Payments, add a separate verified purchase/authentication adapter before changing the checkout route; simply linking a $29 Kajabi Offer will not unlock this service.

Kajabi’s current developer documentation exposes purchases and transactions, and its Payment Succeeded webhook carries offer, member, and transaction data. A native implementation must verify the right offer and completed payment server-side, establish that the visitor controls the purchasing account/email, bind entitlement to the private session, and handle revocation/refunds. Do not trust a browser-supplied customer ID, email address, or paid flag. A protected Kajabi lesson can be a presentation layer, but a public report API still needs its own reliable access enforcement.

BIRTH DATA AND ACCURACY
NASA/JPL DE440s + Skyfield computes apparent geocentric Sun/Moon positions in the tropical ecliptic of date. IANA historical clock rules convert the confirmed local birth time to UTC. The ascendant is calculated only with a known time and is withheld at polar latitudes. No houses or a full natal chart are presented.

Public Nominatim searches are explicit button clicks, cached, and capped globally at one request per second. Set NEU_GEOCODE_AGENT to a genuine application name and contact email. It receives only the place name. timezonefinder suggests a current IANA zone using coordinates; the user confirms the historical zone. You can switch NEU_GEOCODE_URL to a compatible geocoder you host or choose. There is no automatic typing/autocomplete traffic to public Nominatim.

Unknown birth time: sample the whole local birth date, retain any sign changes, withhold precise degrees and the ascendant. Ambiguous daylight-saving times require an explicit first/second occurrence; nonexistent local times are rejected. Very old timezone boundaries or unreliable birth records can remain uncertain; no guessed noon time is labeled as known.

Astrology is a subtle editorial layer, contributing at most 2% to the heritage score, with no direct “zodiac sign equals star race” mapping. The paid score carries 3% of earlier answer themes and otherwise uses the new role questions. Accurate astronomical positions do not establish accurate personality predictions or celestial ancestry. The report keeps the spiritual framework while being honest about that distinction.

PRIVACY AND RETURN ACCESS
No email service is configured; the requested report is delivered as a PDF download on the results screen. Birth details and answers are encrypted in the private server database. The browser keeps only an opaque private session access key, not birth data or paid entitlement. The access key can be copied/restored across devices; anyone holding it can access that session, so it must be treated privately.

Sessions expire after 90 days. Daily cleanup removes expired encrypted records. Visitors can delete their session and browser key from the “Your private session” control; deletion also removes that session’s access to a previously purchased report. Download the report first. Square’s transaction records are separate and are not deleted by that button. Add the actual host, retention, support contact, and geocoder disclosures to the university’s privacy information before publishing.

If you want to grow the email list, place a native Kajabi opt-in form before or alongside the free assessment, with an appropriate consent choice. Do not silently send birth data to a marketing form. The package does not automatically enroll visitors into marketing or email a PDF.

EDITING CONTENT
server/free.json — 19 illustrated profiles, heritage question bank, glossary, and wider reference catalogue.
server/purpose.json — 60 roles, current domain questions, role questions, careers, training notes, and service pilots.
server/engine.py — transparent scoring and practical action logic.
server/astro.py — birth calculation method and uncertainty handling.
server/report.py — branded five-page report template.
public/styles.css — deep-blue/gold theme and responsive layout.
public/app.js — assessment screens and access-aware browser interactions.
public/assets — optimized supplied portraits and gateway image.
server/fonts — bundled DejaVu fonts and license.
server/data/de440s.bsp — public JPL ephemeris data; source information in RESEARCH-NOTES.txt.

Changing question IDs, dimensions, or score rules requires a version change and tests for old/new sessions. These content files are authoritative. The development source importer is not required for deployment; all content and optimized images are already present.

VERIFY BEFORE LAUNCH
Automated command:
   cd server
   python -m unittest test_assessments -v
The optional independent ephemeris test is skipped unless its test-only Swiss Ephemeris reference package is installed; it is not a runtime dependency.

In Square Sandbox, verify an actual completed purchase, a declined or incomplete payment, a full/partial refund, a repeated webhook, and a return in Safari/mobile. Check PDF download and session restoration. Test the Kajabi iframe in your live theme and use the full-window link if browser storage is restricted. The automated provider tests use controlled responses; they do not replace a credentialed Sandbox purchase test.
