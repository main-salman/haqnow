#!/usr/bin/env python3
"""
Direct database insert for expose documents.
Runs INSIDE the k8s pod via: kubectl exec deployment/backend-api -- python3 /tmp/bulk_insert.py

This bypasses the upload API entirely (no virus scan, no metadata strip, no OOM crashes).
It generates tiny PDFs, uploads them to S3, and inserts DB records directly.
"""

import io
import os
import uuid
import boto3
from datetime import datetime

import sys
sys.path.insert(0, '/app')

# These will be available inside the pod
from app.database.database import SessionLocal
from app.database.models import Document

# S3 config from environment (available in pod)
S3_ACCESS_KEY = os.getenv("EXOSCALE_S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("EXOSCALE_S3_SECRET_KEY")
S3_ENDPOINT = os.getenv("EXOSCALE_S3_ENDPOINT", "sos-ch-dk-2.exo.io")
S3_REGION = os.getenv("EXOSCALE_S3_REGION", "ch-dk-2")
S3_BUCKET = os.getenv("EXOSCALE_BUCKET", "foi-archive-terraform")
S3_PUBLIC_URL = os.getenv("EXOSCALE_S3_PUBLIC_URL", f"https://{S3_ENDPOINT}/{S3_BUCKET}")

# Document definitions
DOCUMENTS = [
    # Tier 1
    ("Jeffrey Epstein Files - DOJ Release", "United States", "District of Columbia",
     "Court records, DOJ disclosures, FBI documents, FOIA releases, and House Oversight Committee materials related to Jeffrey Epstein's sex trafficking network. Source: justice.gov/epstein", "english"),
    ("JFK Assassination Records", "United States", "District of Columbia",
     "6+ million pages of records related to the 1963 assassination of President Kennedy, including CIA, FBI, and Secret Service documents. Source: archives.gov/research/jfk", "english"),
    ("CIA Torture Report - Senate Intelligence Committee", "United States", "District of Columbia",
     "525-page executive summary of the Committee Study of the CIA's Detention and Interrogation Program. Source: intelligence.senate.gov", "english"),
    ("Pentagon Papers - Vietnam War Deception", "United States", "District of Columbia",
     "~7,000 pages exposing systematic government deception about the Vietnam War. Fully declassified 2011. Source: catalog.archives.gov", "english"),

    # Tier 2
    ("Panama Papers - Offshore Tax Haven Expose", "Panama", "Panama",
     "11.5 million documents from law firm Mossack Fonseca exposing offshore tax havens. Source: offshoreleaks.icij.org", "english"),
    ("Paradise Papers - Appleby Leak", "Bermuda", "Pembroke",
     "13.4 million documents from offshore law firm Appleby exposing tax avoidance. Source: offshoreleaks.icij.org", "english"),
    ("Pandora Papers - Global Offshore Expose", "United States", "District of Columbia",
     "11.9 million documents from 14 offshore service providers exposing hidden wealth of world leaders. Source: icij.org/investigations/pandora-papers", "english"),
    ("Xinjiang Police Files - Uyghur Detention Evidence", "China", "Xinjiang",
     "Leaked internal Chinese police files from Uyghur detention camps including detainee photos and shooting orders. Source: xinjiangpolicefiles.org", "english"),
    ("The Drone Papers - US Assassination Program", "United States", "District of Columbia",
     "Classified Pentagon documents revealing inner workings of the U.S. drone assassination program (2011-2013). Source: theintercept.com/drone-papers", "english"),
    ("9/11 - The 28 Pages Saudi Connection", "United States", "District of Columbia",
     "The classified final chapter of the 2002 Joint Congressional Inquiry into 9/11. Declassified July 2016. Source: intelligence.house.gov", "english"),

    # Tier 3 - Surveillance
    ("Snowden NSA Surveillance Archive", "United States", "District of Columbia",
     "Classified NSA documents revealing global mass surveillance programs (PRISM, XKeyscore, Tempora). Source: archive.org/details/nsa-snowden-documents", "english"),
    ("COINTELPRO - FBI Domestic Surveillance", "United States", "District of Columbia",
     "Declassified FBI records on the Counter Intelligence Program (1956-1971). Source: vault.fbi.gov", "english"),
    ("CIA MKUltra Mind Control Program", "United States", "District of Columbia",
     "Surviving declassified records of the CIA's illegal mind control program (1953-1973). Source: foia.cia.gov", "english"),
    ("Church Committee Reports - Intelligence Abuses", "United States", "District of Columbia",
     "14 final reports documenting illegal intelligence activities including assassination plots. Source: aarclibrary.org", "english"),

    # Tier 4 - War Crimes
    ("Guantanamo Bay Detainee Files", "Cuba", "Guantanamo",
     "765 classified Detainee Assessment Briefs from Pentagon's Joint Task Force Guantanamo (2002-2009). Source: wikileaks.org", "english"),
    ("Iraq War Logs - 400,000 Military Reports", "Iraq", "Baghdad",
     "~400,000 U.S. military field reports from the Iraq War (2004-2009). Source: wikileaks.org", "english"),
    ("Afghanistan War Diary", "Afghanistan", "Kabul",
     "91,000+ U.S. military incident reports from the Afghanistan War (2004-2009). Source: wikileaks.org", "english"),
    ("Abu Ghraib and Torture Archive", "Iraq", "Baghdad",
     "Tens of thousands of pages of declassified documents on U.S. detention and interrogation practices. Source: nsarchive.gwu.edu", "english"),

    # Tier 5
    ("U.S. Diplomatic Cables - Cablegate", "United States", "District of Columbia",
     "250,000+ U.S. State Department diplomatic cables. Source: wikileaks.org/plusd", "english"),

    # Government Scandals
    ("Watergate Tapes and Transcripts", "United States", "District of Columbia",
     "Nixon White House recordings exposing the Watergate cover-up. 3,700+ hours. Source: nixonlibrary.gov", "english"),
    ("Iran-Contra Affair Documents", "United States", "District of Columbia",
     "Declassified records of illegal arms sales to Iran and covert funding of Nicaraguan Contras. Source: nsarchive.gwu.edu", "english"),
    ("CIA Family Jewels - Catalog of Illegal Activities", "United States", "Virginia",
     "702 pages of CIA's own catalog of illegal activities (1959-1973). Declassified 2007. Source: cia.gov/readingroom", "english"),
    ("Operation Northwoods - False Flag Proposal", "United States", "District of Columbia",
     "1962 Joint Chiefs of Staff proposal for false-flag attacks on U.S. soil to justify invading Cuba. Source: nsarchive.gwu.edu", "english"),
    ("Gulf of Tonkin - NSA Declassified Documents", "United States", "Maryland",
     "NSA's own records proving the August 4, 1964 'attack' that escalated the Vietnam War never happened. Source: nsa.gov", "english"),
    ("Operation Gladio - NATO Stay-Behind Armies", "Italy", "Lazio",
     "Declassified documents on secret NATO paramilitary networks in Western Europe during the Cold War. Source: European Parliament archives", "english"),
    ("Vault 7 - CIA Hacking Tools", "United States", "Virginia",
     "Thousands of documents detailing CIA cyber weapons: smartphone exploits, smart TV surveillance. Source: wikileaks.org", "english"),
    ("Operation CHAOS - CIA Domestic Surveillance", "United States", "Virginia",
     "CIA domestic surveillance program (1967-1974) targeting anti-war activists. Source: aarclibrary.org", "english"),

    # Human Rights
    ("Goldstone Report - Gaza 2009", "Israel", "Southern District",
     "UN Fact-Finding Mission report on Gaza conflict documenting potential war crimes. Source: un.org/unispal", "english"),
    ("Khashoggi Murder - UN Investigation Report", "Saudi Arabia", "Makkah",
     "UN report on the extrajudicial killing of journalist Jamal Khashoggi. Source: ohchr.org", "english"),
    ("Chilcot Report - UK Iraq War Inquiry", "United Kingdom", "England",
     "2.6 million word inquiry into UK's role in the Iraq War. 12 volumes. Source: UK National Archives", "english"),
    ("Myanmar Rohingya - UN Fact-Finding Mission", "Myanmar", "Rakhine",
     "Evidence of genocide and crimes against humanity committed against the Rohingya people. Source: ohchr.org", "english"),
    ("Syria Caesar Photos - Systematic Torture Evidence", "Syria", "Damascus",
     "Evidence from 'Caesar' documenting systematic torture and killing in Assad's prisons. Source: Human Rights Watch", "english"),
    ("CIA Rendition and Black Sites - EU Parliament Report", "Poland", "Masovia",
     "European Parliament investigation documenting 1,245+ CIA rendition flights. Source: europarl.europa.eu", "english"),
    ("Collateral Murder - Baghdad Airstrike Video", "Iraq", "Baghdad",
     "Classified gunsight footage of 2007 U.S. Apache helicopter attack killing civilians. Source: collateralmurder.wikileaks.org", "english"),
    ("Yemen War Crimes - UN Eminent Experts Reports", "Yemen", "Amanat Al Asimah",
     "Evidence of war crimes by all parties in Yemen conflict. Source: ohchr.org", "english"),

    # Medical
    ("Tuskegee Syphilis Experiment Documents", "United States", "Alabama",
     "Records of the 40-year (1932-1972) government experiment withholding syphilis treatment from Black men. Source: NLM Digital Collections", "english"),
    ("Guatemala Syphilis Experiments", "Guatemala", "Guatemala",
     "Documents showing U.S. researchers deliberately infected Guatemalan prisoners with STDs (1946-1948). Source: Presidential Commission for Bioethical Issues", "english"),
    ("Tobacco Industry Internal Documents", "United States", "North Carolina",
     "14+ million internal documents revealing decades of deception about health risks. Source: industrydocuments.ucsf.edu/tobacco", "english"),
    ("Opioid Crisis - Purdue Pharma Documents", "United States", "Connecticut",
     "Internal Purdue Pharma communications exposing aggressive OxyContin marketing. Source: court repositories", "english"),

    # Corporate
    ("Facebook Papers - Meta Internal Documents", "United States", "California",
     "Internal Meta documents showing the company knew its platforms harmed teens. Source: FBarchive (Harvard)", "english"),
    ("Boeing 737 MAX Internal Documents", "United States", "Illinois",
     "Internal Boeing communications revealing employees knew about MCAS safety flaws. Source: transportation.house.gov", "english"),
    ("Uber Files - Global Lobbying Expose", "Netherlands", "North Holland",
     "124,000+ leaked documents exposing Uber's lobbying of world leaders. Source: theguardian.com/uber-files", "english"),
    ("Swiss Leaks - HSBC Tax Evasion", "Switzerland", "Geneva",
     "Leaked files from HSBC's Swiss private bank revealing 100,000+ accounts. Source: icij.org/swiss-leaks", "english"),
    ("Suisse Secrets - Credit Suisse Expose", "Switzerland", "Zurich",
     "Leaked data on 30,000+ Credit Suisse clients including autocrats and war criminals. Source: icij.org", "english"),
    ("Luanda Leaks - Isabel dos Santos", "Angola", "Luanda",
     "715,000 documents exposing how Africa's richest woman siphoned billions from Angola. Source: icij.org/luanda-leaks", "english"),
    ("1MDB Scandal - DOJ Filings", "Malaysia", "Kuala Lumpur",
     "U.S. DOJ filings detailing $4.5 billion embezzled from Malaysia's sovereign wealth fund. Source: justice.gov", "english"),
    ("FinCEN Files - $2 Trillion in Dirty Money", "United States", "District of Columbia",
     "2,100+ suspicious activity reports showing how global banks moved dirty money. Source: icij.org/fincen-files", "english"),
    ("Mauritius Leaks - Tax Treaty Exploitation", "Mauritius", "Port Louis",
     "200,000+ documents revealing how corporations exploit Mauritius tax treaties. Source: icij.org/mauritius-leaks", "english"),

    # Surveillance
    ("Pegasus Project - NSO Group Spyware", "Israel", "Tel Aviv",
     "Investigation revealing NSO Group's Pegasus spyware targeted 50,000+ phone numbers. Source: forbiddenstories.org", "english"),
    ("Operation Rubicon - Crypto AG CIA Front Company", "Switzerland", "Zug",
     "CIA and German BND secretly owned Swiss encryption company Crypto AG for decades. Source: Washington Post/ZDF", "english"),
    ("GCHQ Tempora - Mass Internet Surveillance", "United Kingdom", "England",
     "Documents showing Britain's GCHQ tapped undersea fiber optic cables. Source: Snowden archives", "english"),
    ("Five Eyes Intelligence Alliance Documents", "Australia", "Australian Capital Territory",
     "Leaked intelligence-sharing alliance documents between US, UK, Canada, Australia, NZ. Source: theintercept.com", "english"),

    # UN Reports
    ("UN Commission of Inquiry - Israel Palestine", "Israel", "Jerusalem",
     "Reports documenting apartheid, occupation practices, and potential crimes against humanity. Source: ohchr.org", "english"),
    ("ICJ Advisory Opinion - Israeli Occupation 2024", "Netherlands", "South Holland",
     "International Court of Justice ruling that Israel's occupation is unlawful. Source: icj-cij.org", "english"),
    ("Amnesty International - Israel Apartheid Report", "United Kingdom", "England",
     "280-page investigation concluding Israel's treatment of Palestinians constitutes apartheid. Source: amnesty.org", "english"),
    ("Human Rights Watch - A Threshold Crossed", "United States", "New York",
     "Report concluding Israeli authorities are committing crimes of apartheid and persecution. Source: hrw.org", "english"),
    ("UN Report - North Korean Human Rights", "South Korea", "Seoul",
     "UN Commission finding crimes against humanity in North Korea. Source: ohchr.org", "english"),
    ("Srebrenica Genocide - ICTY Evidence", "Bosnia and Herzegovina", "Federation of B&H",
     "ICTY records documenting the 1995 Srebrenica massacre. Source: icty.org, irmct.org", "english"),
    ("Rwanda Genocide - ICTR Records", "Rwanda", "Kigali",
     "ICTR judgments documenting the 1994 genocide that killed 800,000 people. Source: irmct.org", "english"),

    # Historical
    ("CIA Coup - Guatemala 1954 PBSUCCESS", "Guatemala", "Guatemala",
     "Declassified documents on CIA-engineered overthrow of President Jacobo Arbenz. Source: nsarchive.gwu.edu", "english"),
    ("CIA Coup - Iran 1953 TPAJAX", "Iran", "Tehran",
     "Declassified CIA history of the overthrow of PM Mohammad Mossadegh. Source: nsarchive.gwu.edu", "english"),
    ("CIA Coup - Chile 1973", "Chile", "Santiago Metropolitan",
     "Documents on CIA involvement in overthrow of President Salvador Allende. Source: nsarchive.gwu.edu", "english"),
    ("Operation Condor - South American Repression", "Argentina", "Buenos Aires",
     "Declassified records on coordinated political repression by South American dictatorships with U.S. support. Source: nsarchive.gwu.edu", "english"),
    ("Phoenix Program - Vietnam CIA Assassinations", "Vietnam", "Ho Chi Minh",
     "Declassified documents on CIA's assassination program during the Vietnam War. Source: cia.gov/readingroom", "english"),
    ("Japanese-American Internment Records", "United States", "California",
     "WWII-era documents on the forced internment of 120,000 Japanese Americans. Source: archives.gov, densho.org", "english"),
    ("Operation Paperclip - Nazi Scientist Recruitment", "United States", "District of Columbia",
     "Records on the secret U.S. program recruiting over 1,600 Nazi German scientists. Source: archives.gov", "english"),

    # Whistleblower
    ("The Black Vault - Comprehensive FOIA Archive", "United States", "California",
     "Massive archive of FOIA-obtained government documents spanning UFOs, CIA, FBI, NSA. Source: theblackvault.com", "english"),
    ("WikiLeaks Global Intelligence Files - Stratfor", "United States", "Texas",
     "5+ million emails from private intelligence firm Stratfor. Source: wikileaks.org", "english"),
    ("Hacking Team Leaked Emails", "Italy", "Lombardy",
     "400GB of internal data from Italian surveillance company Hacking Team. Source: wikileaks.org", "english"),
]


def create_minimal_pdf(title, description):
    """Create a minimal valid PDF without any external dependencies."""
    # Minimal PDF structure
    content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

4 0 obj
<< /Length {len(title) + len(description) + 200} >>
stream
BT
/F1 16 Tf
72 720 Td
({title}) Tj
/F1 10 Tf
0 -30 Td
({description[:200]}) Tj
0 -15 Td
(Source document reference - see HaqNow.org for details) Tj
ET
endstream
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000266 00000 n 
0000000206 00000 n 

trailer
<< /Size 6 /Root 1 0 R >>
startxref
{400 + len(title) + len(description)}
%%EOF"""
    return content.encode('latin-1', errors='replace')


def main():
    db = SessionLocal()
    
    # Set up S3
    s3 = boto3.client(
        's3',
        endpoint_url=f"https://{S3_ENDPOINT}",
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION
    )
    
    # Get existing titles to skip duplicates
    existing = {d.title for d in db.query(Document.title).all()}
    print(f"Found {len(existing)} existing documents")
    
    success = 0
    skipped = 0
    failed = 0
    
    for i, (title, country, state, desc, lang) in enumerate(DOCUMENTS, 1):
        if title in existing:
            print(f"  [{i}/{len(DOCUMENTS)}] SKIP: {title[:50]}")
            skipped += 1
            continue
        
        try:
            # Generate PDF
            pdf_bytes = create_minimal_pdf(title, desc)
            
            # Upload to S3
            s3_key = f"documents/{uuid.uuid4().hex}.pdf"
            s3.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=pdf_bytes,
                ContentType="application/pdf",
                ACL="public-read"
            )
            file_url = f"{S3_PUBLIC_URL}/{s3_key}"
            
            # Insert DB record
            doc = Document(
                title=title,
                country=country,
                state=state,
                description=desc,
                document_language=lang,
                file_path=s3_key,
                file_url=file_url,
                original_filename=f"expose_{i:03d}.pdf",
                file_size=len(pdf_bytes),
                content_type="application/pdf",
                status="pending",
                ocr_text=desc,
                search_text=f"{title} {desc}",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            print(f"  [{i}/{len(DOCUMENTS)}] OK (id={doc.id}): {title[:50]}")
            success += 1
            
        except Exception as e:
            db.rollback()
            print(f"  [{i}/{len(DOCUMENTS)}] FAIL: {title[:50]} - {e}")
            failed += 1
    
    db.close()
    print(f"\nDone: {success} success, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
