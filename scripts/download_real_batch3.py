#!/usr/bin/env python3
"""Batch 3 - More verified real documents. Runs inside k8s pod."""
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
    # JFK - Warren Commission Report
    ("Warren Commission Report - JFK Assassination (1964)",
     "United States", "District of Columbia",
     "The complete 888-page Report of the President's Commission on the Assassination of President Kennedy (Warren Commission Report, September 1964). Concluded that Lee Harvey Oswald acted alone in assassinating President John F. Kennedy on November 22, 1963. One of the most scrutinized and debated government reports in American history.",
     "english",
     "https://www.govinfo.gov/content/pkg/GPO-WARRENCOMMISSIONREPORT/pdf/GPO-WARRENCOMMISSIONREPORT.pdf"),

    # MKUltra - Church Committee testimony
    ("CIA Project MKUltra - Church Committee Testimony and Documents",
     "United States", "District of Columbia",
     "Church Committee testimony and declassified documents on Project MKUltra, the CIA's illegal mind control program (1953-1973). Documents experiments on unwitting human subjects using LSD, hypnosis, sensory deprivation, and other techniques. Most MKUltra files were destroyed in 1973 by order of CIA Director Richard Helms.",
     "english",
     "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB54/st20.pdf"),

    # CIA Coup Guatemala 1954
    ("CIA Coup in Guatemala 1954 (Operation PBSUCCESS) - Declassified Documents",
     "Guatemala", "Guatemala",
     "Declassified CIA documents on the covert operation to overthrow democratically elected President Jacobo Arbenz of Guatemala in 1954. The coup was orchestrated at the behest of the United Fruit Company and installed a military dictatorship, leading to decades of civil war that killed over 200,000 people.",
     "english",
     "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB4/docs/doc01.pdf"),

    # CIA Coup Chile 1973
    ("CIA Involvement in Chile 1973 Coup - Declassified Documents",
     "Chile", "Santiago Metropolitan",
     "Declassified CIA and State Department documents on U.S. involvement in the September 11, 1973 military coup that overthrew democratically elected President Salvador Allende. The Pinochet dictatorship that followed killed over 3,000 people and tortured tens of thousands.",
     "english",
     "https://nsarchive2.gwu.edu/NSAEBB/NSAEBB8/docs/doc01.pdf"),

    # Tuskegee Syphilis Study
    ("Tuskegee Syphilis Study - Final Report of the Legacy Committee (1996)",
     "United States", "Alabama",
     "CDC Final Report of the Tuskegee Syphilis Study Legacy Committee documenting the 40-year (1932-1972) U.S. Public Health Service experiment that withheld syphilis treatment from 399 Black men in Macon County, Alabama. One of the most infamous examples of unethical medical experimentation in history.",
     "english",
     "https://stacks.cdc.gov/view/cdc/27130/cdc_27130_DS1.pdf"),
]


def download_pdf(url, max_size_mb=100):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/pdf,*/*',
        })
        resp = urllib.request.urlopen(req, timeout=300, context=ssl_ctx)
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
    print(f"Existing: {len(existing)}, Batch 3: {len(DOCUMENTS)}\n")

    ok = skip = fail = 0
    for i, (title, country, state, desc, lang, url) in enumerate(DOCUMENTS, 1):
        if title in existing:
            print(f"[{i}] SKIP: {title[:55]}"); skip += 1; continue
        print(f"[{i}/{len(DOCUMENTS)}] {title[:60]}...")
        print(f"    URL: {url[:80]}...")
        data = download_pdf(url)
        if not data: fail += 1; continue
        sz = f"{len(data)/(1024*1024):.1f}MB" if len(data)>1024*1024 else f"{len(data)//1024}KB"
        print(f"    Downloaded: {sz}")
        try:
            key = f"documents/{uuid.uuid4().hex}.pdf"
            s3.put_object(Bucket=S3_BUCKET, Key=key, Body=data, ContentType="application/pdf", ACL="public-read")
            doc = Document(title=title, country=country, state=state, description=desc,
                document_language=lang, file_path=key, file_url=f"{S3_PUBLIC_URL}/{key}",
                original_filename=f"{title[:50].replace(' ','_')}.pdf",
                file_size=len(data), content_type="application/pdf", status="pending",
                ocr_text=desc, search_text=f"{title} {desc}")
            db.add(doc); db.commit(); db.refresh(doc)
            print(f"    UPLOADED (id={doc.id})"); ok += 1
        except Exception as e:
            db.rollback(); print(f"    ERR: {e}"); fail += 1
        time.sleep(2)
    db.close()
    print(f"\nBatch 3 complete: {ok} ok, {skip} skip, {fail} fail")

if __name__ == "__main__":
    main()
