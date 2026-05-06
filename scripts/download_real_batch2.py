#!/usr/bin/env python3
"""Batch 2 - More real documents. Runs inside k8s pod."""
import sys
sys.path.insert(0, '/app')
import os, uuid, time, urllib.request, ssl, boto3
from app.database.database import SessionLocal
from app.database.models import Document

S3_ACCESS_KEY = os.getenv("EXOSCALE_S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("EXOSCALE_S3_SECRET_KEY")
S3_ENDPOINT = os.getenv("EXOSCALE_S3_ENDPOINT", "sos-ch-dk-2.exo.io")
S3_REGION = os.getenv("EXOSCALE_S3_REGION", "ch-dk-2")
S3_BUCKET = os.getenv("EXOSCALE_BUCKET", "foi-archive-terraform")
S3_PUBLIC_URL = os.getenv("EXOSCALE_S3_PUBLIC_URL", f"https://{S3_ENDPOINT}/{S3_BUCKET}")
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

DOCUMENTS = [
    # Gulf of Tonkin
    ("Gulf of Tonkin Incident - NSA Declassified Documents",
     "United States", "Maryland",
     "Declassified NSA documents proving the August 4, 1964 Gulf of Tonkin 'attack' that escalated U.S. involvement in the Vietnam War was based on false intelligence. The second attack never happened, yet it was used to justify the Gulf of Tonkin Resolution.",
     "english",
     "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB132/relea00012.pdf"),

    # CIA Family Jewels
    ("CIA 'Family Jewels' - Internal Report on Illegal Activities (1973)",
     "United States", "Virginia",
     "The CIA's own 693-page internal catalog of illegal and unauthorized activities from 1959-1973, compiled at the direction of DCI James Schlesinger. Documents domestic spying, assassination plots against foreign leaders, wiretapping of journalists, mail opening programs, and drug experiments on unwitting citizens. Declassified 2007.",
     "english",
     "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB222/family_jewels_full_ocr.pdf"),

    # Yemen War Crimes
    ("UN Group of Eminent Experts on Yemen - Final Report (2020)",
     "Yemen", "Amanat Al Asimah",
     "Final report of the Group of Eminent International and Regional Experts on Yemen (A/HRC/45/6, September 2020). Documents war crimes and violations of international humanitarian law by all parties, including Saudi-led coalition airstrikes on civilians.",
     "english",
     "https://documents-dds-ny.un.org/doc/UNDOC/GEN/G20/240/31/PDF/G2024031.pdf"),

    # Srebrenica Genocide ICTY
    ("Srebrenica Genocide - ICTY Trial Judgment (Prosecutor v. Krstic)",
     "Bosnia and Herzegovina", "Federation of B&H",
     "Trial Chamber Judgment in Prosecutor v. Radislav Krstic (IT-98-33) at the International Criminal Tribunal for the former Yugoslavia. First international court ruling to legally classify the 1995 Srebrenica massacre of 8,000+ Bosniak men and boys as genocide.",
     "english",
     "https://www.icty.org/x/cases/krstic/tjug/en/krs-tj010802e.pdf"),

    # UN COI Israel/Palestine (fixed URL)
    ("UN Commission of Inquiry on Israel and Palestine - Report (2022)",
     "Israel", "Jerusalem",
     "First report of the Independent International Commission of Inquiry on the Occupied Palestinian Territory, including East Jerusalem, and Israel (A/HRC/50/21, June 2022). Examines root causes including the occupation and discrimination.",
     "english",
     "https://documents-dds-ny.un.org/doc/UNDOC/GEN/G22/337/18/PDF/G2233718.pdf"),

    # ICJ Advisory Opinion (trying direct UN docs link)
    ("ICJ Advisory Opinion - Israeli Occupation is Unlawful (2024)",
     "Netherlands", "South Holland",
     "International Court of Justice advisory opinion (July 19, 2024) ruling that Israel's continued presence in the Occupied Palestinian Territory is unlawful and must be brought to an end as rapidly as possible. The Court found the occupation constitutes a breach of the right of self-determination.",
     "english",
     "https://www.icj-cij.org/node/203454"),
]


def download_pdf(url, max_size_mb=100):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/pdf,*/*',
        })
        resp = urllib.request.urlopen(req, timeout=180, context=ssl_ctx)
        data = resp.read()
        if len(data) < 500:
            print(f"    Too small ({len(data)}b)"); return None
        if len(data) > max_size_mb*1024*1024:
            print(f"    Too large ({len(data)/(1024*1024):.1f}MB)"); return None
        if b'<html' in data[:500].lower() or b'<!doctype' in data[:500].lower():
            print(f"    Got HTML, not PDF"); return None
        return data
    except Exception as e:
        print(f"    ERROR: {e}"); return None


def main():
    db = SessionLocal()
    s3 = boto3.client('s3', endpoint_url=f"https://{S3_ENDPOINT}",
        aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION)
    existing = {d.title for d in db.query(Document.title).all()}
    print(f"Existing: {len(existing)}, Batch: {len(DOCUMENTS)}\n")

    ok = skip = fail = 0
    for i, (title, country, state, desc, lang, url) in enumerate(DOCUMENTS, 1):
        if title in existing:
            print(f"[{i}] SKIP: {title[:55]}"); skip += 1; continue
        print(f"[{i}] {title[:60]}...")
        data = download_pdf(url)
        if not data: fail += 1; continue
        sz = f"{len(data)/(1024*1024):.1f}MB" if len(data)>1024*1024 else f"{len(data)//1024}KB"
        print(f"    Got {sz}")
        try:
            key = f"documents/{uuid.uuid4().hex}.pdf"
            s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType="application/pdf", ACL="public-read")
            doc = Document(title=title, country=country, state=state, description=desc,
                document_language=lang, file_path=key, file_url=f"{S3_PUBLIC_URL}/{key}",
                original_filename=f"{title[:50].replace(' ','_')}.pdf",
                file_size=len(data), content_type="application/pdf", status="pending",
                ocr_text=desc, search_text=f"{title} {desc}")
            db.add(doc); db.commit(); db.refresh(doc)
            print(f"    OK id={doc.id}"); ok += 1
        except Exception as e:
            db.rollback(); print(f"    ERR: {e}"); fail += 1
        time.sleep(2)
    db.close()
    print(f"\nDone: {ok} ok, {skip} skip, {fail} fail")

if __name__ == "__main__":
    main()
