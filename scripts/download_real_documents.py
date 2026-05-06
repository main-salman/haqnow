#!/usr/bin/env python3
"""
Download real source documents and upload to HaqNow.org.
Runs INSIDE k8s pod: kubectl cp + kubectl exec
Only includes VERIFIED working PDF URLs.
"""
import sys
sys.path.insert(0, '/app')

import io
import os
import uuid
import time
import urllib.request
import ssl
import boto3
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

# VERIFIED WORKING PDF URLs - tested 2026-05-01
# (title, country, state, description, language, pdf_url)
DOCUMENTS = [
    # === EPSTEIN ===
    ("Jeffrey Epstein Federal Indictment (SDNY 2019)",
     "United States", "New York",
     "Federal indictment of Jeffrey Epstein (Case 1:19-cr-00490-RMB) filed July 2, 2019 by the U.S. Attorney for the Southern District of New York, charging sex trafficking and sex trafficking conspiracy involving dozens of minor victims.",
     "english",
     "https://www.justice.gov/usao-sdny/press-release/file/1180481/dl"),

    # === CIA TORTURE REPORT ===
    ("CIA Detention and Interrogation Program - Senate Intelligence Committee Report",
     "United States", "District of Columbia",
     "Full 525-page Executive Summary of the Senate Select Committee on Intelligence's Committee Study of the CIA's Detention and Interrogation Program (CRPT-113srpt288). Declassified December 9, 2014. Documents enhanced interrogation techniques, CIA black sites, and concludes the program was not effective.",
     "english",
     "https://www.govinfo.gov/content/pkg/CRPT-113srpt288/pdf/CRPT-113srpt288.pdf"),

    # === OPERATION NORTHWOODS ===
    ("Operation Northwoods - Joint Chiefs of Staff False Flag Proposal (1962)",
     "United States", "District of Columbia",
     "March 13, 1962 memorandum from the Joint Chiefs of Staff to the Secretary of Defense proposing false-flag operations against U.S. targets to justify military intervention in Cuba. Included plans for fake terrorist attacks, hijackings, and bombings. Rejected by President Kennedy. Declassified by the National Security Archive.",
     "english",
     "https://nsarchive2.gwu.edu/news/20010430/northwoods.pdf"),

    # === ICJ ADVISORY OPINION ===
    ("ICJ Advisory Opinion - Legal Consequences of Israeli Occupation (2024)",
     "Netherlands", "South Holland",
     "Full text of the International Court of Justice advisory opinion (July 19, 2024) ruling that Israel's continued presence in the Occupied Palestinian Territory, including East Jerusalem, is unlawful under international law and must be brought to an end as rapidly as possible.",
     "english",
     "https://www.icj-cij.org/sites/default/files/case-related/186/186-20240719-adv-01-00-en.pdf"),

    # === AMNESTY APARTHEID REPORT ===
    ("Amnesty International - Israel's Apartheid Against Palestinians (2022)",
     "United Kingdom", "England",
     "Full 280-page Amnesty International investigation (February 2022) titled 'Israel's Apartheid against Palestinians: Cruel System of Domination and Crime against Humanity.' Concludes that Israel's treatment of Palestinians constitutes apartheid under international law.",
     "english",
     "https://www.amnesty.org/en/wp-content/uploads/2022/02/MDE1551412022ENGLISH.pdf"),

    # === HRW THRESHOLD CROSSED ===
    ("Human Rights Watch - A Threshold Crossed: Israeli Authorities and the Crimes of Apartheid and Persecution (2021)",
     "United States", "New York",
     "Full Human Rights Watch report (April 27, 2021) concluding that Israeli authorities are committing the crimes against humanity of apartheid and persecution against millions of Palestinians. 213 pages with detailed legal analysis.",
     "english",
     "https://www.hrw.org/sites/default/files/media_2021/04/israel_palestine0421_web_0.pdf"),

    # === GOLDSTONE REPORT ===
    ("Goldstone Report - UN Fact-Finding Mission on Gaza Conflict (2009)",
     "Israel", "Southern District",
     "Full report of the United Nations Fact-Finding Mission on the Gaza Conflict (A/HRC/12/48, September 2009). 575 pages documenting potential war crimes and crimes against humanity by both Israeli forces and Palestinian armed groups during the 2008-2009 Gaza conflict. Chaired by Justice Richard Goldstone.",
     "english",
     "https://documents-dds-ny.un.org/doc/UNDOC/GEN/G09/158/66/PDF/G0915866.pdf"),

    # === MYANMAR ROHINGYA ===
    ("UN Fact-Finding Mission on Myanmar - Genocide Against Rohingya (2018)",
     "Myanmar", "Rakhine",
     "Report of the Independent International Fact-Finding Mission on Myanmar (A/HRC/39/64, September 2018). Documents genocide, crimes against humanity, and war crimes committed against the Rohingya people by Myanmar's military (Tatmadaw), recommending referral to the International Criminal Court.",
     "english",
     "https://www.ohchr.org/sites/default/files/Documents/HRBodies/HRCouncil/FFM-Myanmar/A_HRC_39_64.pdf"),

    # === CHILCOT REPORT ===
    ("Chilcot Report - Iraq Inquiry Executive Summary (2016)",
     "United Kingdom", "England",
     "Executive Summary of the Iraq Inquiry (Chilcot Report, July 2016). Documents how the UK decided to join the 2003 invasion of Iraq based on flawed intelligence, inadequate planning, and misleading public statements by Prime Minister Tony Blair's government.",
     "english",
     "https://webarchive.nationalarchives.gov.uk/ukgwa/20160708115158mp_/http://www.iraqinquiry.org.uk/media/246416/the-report-of-the-iraq-inquiry_executive-summary.pdf"),

    # === UN NORTH KOREA ===
    ("UN Commission of Inquiry - Human Rights in North Korea (2014)",
     "South Korea", "Seoul",
     "Report of the Commission of Inquiry on Human Rights in the DPRK (A/HRC/25/63, February 2014). Finds systematic, widespread, and gross human rights violations amounting to crimes against humanity, including extermination, enslavement, torture, imprisonment, rape, and enforced disappearances.",
     "english",
     "https://documents-dds-ny.un.org/doc/UNDOC/GEN/G14/108/66/PDF/G1410866.pdf"),

    # === KHASHOGGI ===
    ("UN Report on Killing of Jamal Khashoggi (2019)",
     "Saudi Arabia", "Makkah",
     "Report by UN Special Rapporteur Agnes Callamard (A/HRC/41/CRP.1) on the investigation into the extrajudicial killing of journalist Jamal Khashoggi at the Saudi consulate in Istanbul, Turkey on October 2, 2018. Finds credible evidence warranting investigation of senior Saudi officials.",
     "english",
     "https://documents-dds-ny.un.org/doc/UNDOC/GEN/G19/156/03/PDF/G1915603.pdf"),

    # === UN COMMISSION OF INQUIRY ISRAEL/PALESTINE ===
    ("UN Commission of Inquiry on Israel and Occupied Palestinian Territory (2022)",
     "Israel", "Jerusalem",
     "First report of the Independent International Commission of Inquiry on the Occupied Palestinian Territory, including East Jerusalem, and Israel (A/HRC/50/21, June 2022). Documents root causes of recurrent tensions, instability, and protracted conflict.",
     "english",
     "https://www.ohchr.org/sites/default/files/2022-06/A_HRC_50_21_AdvanceEditedVersion.pdf"),
]


def download_pdf(url, title, max_size_mb=100):
    """Download PDF from URL. Returns bytes or None."""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,*/*',
        })
        resp = urllib.request.urlopen(req, timeout=180, context=ssl_ctx)
        data = resp.read()
        if len(data) < 500:
            print(f"    WARNING: File too small ({len(data)} bytes), likely an error page")
            return None
        if len(data) > max_size_mb * 1024 * 1024:
            print(f"    WARNING: File too large ({len(data)/(1024*1024):.1f}MB)")
            return None
        if not data[:5] == b'%PDF-':
            # Some servers return HTML error pages
            if b'<html' in data[:500].lower() or b'<!doctype' in data[:500].lower():
                print(f"    WARNING: Got HTML instead of PDF")
                return None
            # Some PDFs don't start with %PDF- exactly
            print(f"    NOTE: Non-standard PDF header: {data[:10]}")
        return data
    except Exception as e:
        print(f"    DOWNLOAD ERROR: {e}")
        return None


def main():
    db = SessionLocal()
    s3 = boto3.client('s3',
        endpoint_url=f"https://{S3_ENDPOINT}",
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION)

    existing = {d.title for d in db.query(Document.title).all()}
    print(f"Existing documents: {len(existing)}")
    print(f"Documents to process: {len(DOCUMENTS)}")
    print()

    success = 0
    skipped = 0
    failed = 0

    for i, (title, country, state, desc, lang, url) in enumerate(DOCUMENTS, 1):
        if title in existing:
            print(f"[{i}/{len(DOCUMENTS)}] SKIP (exists): {title[:60]}")
            skipped += 1
            continue

        print(f"[{i}/{len(DOCUMENTS)}] {title[:60]}...")
        print(f"    URL: {url[:80]}...")

        pdf_data = download_pdf(url, title)
        if pdf_data is None:
            failed += 1
            continue

        size_mb = len(pdf_data) / (1024*1024)
        size_str = f"{size_mb:.1f}MB" if size_mb >= 1 else f"{len(pdf_data)/1024:.0f}KB"
        print(f"    Downloaded: {size_str}")

        try:
            s3_key = f"documents/{uuid.uuid4().hex}.pdf"
            s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=pdf_data,
                         ContentType="application/pdf", ACL="public-read")
            file_url = f"{S3_PUBLIC_URL}/{s3_key}"

            doc = Document(
                title=title, country=country, state=state,
                description=desc, document_language=lang,
                file_path=s3_key, file_url=file_url,
                original_filename=f"{title[:50].replace(' ','_')}.pdf",
                file_size=len(pdf_data), content_type="application/pdf",
                status="pending", ocr_text=desc,
                search_text=f"{title} {desc}",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            print(f"    UPLOADED (id={doc.id}) [{size_str}]")
            success += 1
        except Exception as e:
            db.rollback()
            print(f"    DB/S3 ERROR: {e}")
            failed += 1

        time.sleep(2)

    db.close()
    print(f"\n=== COMPLETE ===")
    print(f"  Uploaded: {success}")
    print(f"  Skipped:  {skipped}")
    print(f"  Failed:   {failed}")
    print(f"  Total:    {len(DOCUMENTS)}")


if __name__ == "__main__":
    main()
