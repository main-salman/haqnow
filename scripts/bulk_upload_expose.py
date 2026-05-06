#!/usr/bin/env python3
"""
Bulk upload expose documents to haqnow.org via the upload API.

This script:
1. Creates an API key in the database (if needed)
2. Generates a small placeholder PDF for each document
3. Uploads via POST /api/upload with X-API-Key header (bypasses rate limits & captcha)
"""

import os
import sys
import io
import time
import json
import hashlib
import secrets
import requests
from fpdf import FPDF

# --- Configuration ---
API_BASE = os.getenv("API_BASE", "https://haqnow.org/api")
DB_URL = os.getenv("DATABASE_URL")

# --- Document definitions: (title, country, state, description, language) ---
DOCUMENTS = [
    # Tier 1 - Highest Profile
    ("Jeffrey Epstein Files — DOJ Release", "United States", "District of Columbia",
     "Court records, DOJ disclosures, FBI documents, FOIA releases, and House Oversight Committee materials related to Jeffrey Epstein's sex trafficking network. Millions of pages including indictments, motions, exhibits, emails, and photographs. Source: justice.gov/epstein", "english"),
    ("JFK Assassination Records", "United States", "District of Columbia",
     "6+ million pages of records related to the 1963 assassination of President Kennedy, including CIA, FBI, and Secret Service documents. Also covers RFK and MLK Jr. assassinations. Source: archives.gov/research/jfk", "english"),
    ("CIA Torture Report — Senate Intelligence Committee", "United States", "District of Columbia",
     "525-page executive summary of the Committee Study of the CIA's Detention and Interrogation Program. Documents 'enhanced interrogation techniques' used at CIA black sites post-9/11. Source: intelligence.senate.gov", "english"),
    ("Pentagon Papers — Vietnam War Deception", "United States", "District of Columbia",
     "~7,000 pages — 'Report of the Office of the Secretary of Defense Vietnam Task Force.' Exposed systematic government deception about the Vietnam War spanning multiple administrations. Fully declassified 2011. Source: catalog.archives.gov (ID 5890484)", "english"),

    # Tier 2 - Major International
    ("Panama Papers — Offshore Tax Haven Exposé", "Panama", "Panamá",
     "11.5 million documents from law firm Mossack Fonseca exposing offshore tax havens and shell companies used by world leaders, billionaires, and corporations. Source: offshoreleaks.icij.org", "english"),
    ("Paradise Papers — Appleby Leak", "Bermuda", "Pembroke",
     "13.4 million documents from offshore law firm Appleby exposing tax avoidance by corporations and wealthy individuals. Source: offshoreleaks.icij.org", "english"),
    ("Pandora Papers — Global Offshore Exposé", "United States", "District of Columbia",
     "11.9 million documents from 14 offshore service providers exposing hidden wealth of world leaders and billionaires. Source: icij.org/investigations/pandora-papers", "english"),
    ("Xinjiang Police Files — Uyghur Detention Evidence", "China", "Xinjiang",
     "Leaked internal Chinese police files from Uyghur detention camps including detainee photos, internal speeches by officials, security protocols, and shooting orders. Published May 2022. Source: xinjiangpolicefiles.org", "english"),
    ("The Drone Papers — US Assassination Program", "United States", "District of Columbia",
     "Classified Pentagon documents revealing inner workings of the U.S. drone assassination program (2011-2013). Includes kill list targeting processes and civilian casualty data. Source: theintercept.com/drone-papers", "english"),
    ("9/11 — The '28 Pages' Saudi Connection", "United States", "District of Columbia",
     "The classified final chapter of the 2002 Joint Congressional Inquiry into 9/11, detailing investigative leads regarding potential connections between the hijackers and Saudi Arabian government officials. Declassified July 2016. Source: intelligence.house.gov", "english"),

    # Tier 3 - Surveillance & Civil Liberties
    ("Snowden NSA Surveillance Archive", "United States", "District of Columbia",
     "Classified NSA documents revealing global mass surveillance programs (PRISM, XKeyscore, Tempora), domestic phone metadata collection, and surveillance of allied heads of state. Source: archive.org/details/nsa-snowden-documents", "english"),
    ("COINTELPRO — FBI Domestic Surveillance", "United States", "District of Columbia",
     "Declassified FBI records on the Counter Intelligence Program (1956-1971) — covert campaign to surveil, infiltrate, discredit, and disrupt domestic political organizations including civil rights groups and the Black Panther Party. Source: vault.fbi.gov", "english"),
    ("CIA MKUltra Mind Control Program", "United States", "District of Columbia",
     "Surviving declassified records of the CIA's illegal mind control program (1953-1973), involving experiments on unwitting human subjects using drugs (LSD), hypnosis, and other methods. Source: foia.cia.gov", "english"),
    ("Church Committee Reports — Intelligence Abuses", "United States", "District of Columbia",
     "14 final reports from the Senate Select Committee (1975-1976) documenting illegal intelligence activities including assassination plots against foreign leaders, domestic surveillance, and CIA/FBI abuses. Source: aarclibrary.org", "english"),

    # Tier 4 - War Crimes & Military
    ("Guantánamo Bay Detainee Files", "Cuba", "Guantánamo",
     "765 classified Detainee Assessment Briefs from Pentagon's Joint Task Force Guantanamo (2002-2009). Reveal detainees held for years without charge, including individuals later deemed low-risk or innocent. Source: wikileaks.org", "english"),
    ("Iraq War Logs — 400,000 Military Reports", "Iraq", "Baghdad",
     "~400,000 U.S. military field reports from the Iraq War (2004-2009). Document civilian casualties, detainee abuse, and unreported incidents. Source: wikileaks.org", "english"),
    ("Afghanistan War Diary", "Afghanistan", "Kabul",
     "91,000+ U.S. military incident reports from the Afghanistan War (2004-2009). Expose unreported civilian casualties, friendly fire incidents, and Taliban operations. Source: wikileaks.org", "english"),
    ("Abu Ghraib & Torture Archive", "Iraq", "Baghdad",
     "Tens of thousands of pages of declassified documents on U.S. detention and interrogation practices, including the 'Torture Memos' that justified enhanced interrogation. Source: nsarchive.gwu.edu", "english"),

    # Tier 5 - Diplomatic & Financial
    ("U.S. Diplomatic Cables — Cablegate", "United States", "District of Columbia",
     "250,000+ U.S. State Department diplomatic cables revealing candid assessments of world leaders, covert operations, and U.S. foreign policy positions. Source: wikileaks.org/plusd", "english"),

    # Additional Collections (18-67)
    # Government Scandals
    ("Watergate Tapes & Transcripts", "United States", "District of Columbia",
     "Nixon White House recordings exposing the Watergate cover-up. 3,700+ hours of secretly recorded conversations. Source: nixonlibrary.gov, nixontapes.org", "english"),
    ("Iran-Contra Affair Documents", "United States", "District of Columbia",
     "Declassified records of illegal arms sales to Iran and covert funding of Nicaraguan Contras during the Reagan administration. Source: nsarchive.gwu.edu", "english"),
    ("CIA 'Family Jewels' — Catalog of Illegal Activities", "United States", "Virginia",
     "702 pages of CIA's own catalog of illegal activities (1959-1973): domestic spying, assassination plots, wiretapping journalists. Declassified 2007. Source: cia.gov/readingroom", "english"),
    ("Operation Northwoods — False Flag Proposal", "United States", "District of Columbia",
     "1962 Joint Chiefs of Staff proposal for false-flag attacks on U.S. soil to justify invading Cuba. Rejected by President Kennedy. Source: nsarchive.gwu.edu", "english"),
    ("Gulf of Tonkin — NSA Declassified Documents", "United States", "Maryland",
     "NSA's own records proving the August 4, 1964 'attack' that escalated the Vietnam War never actually happened. Source: nsa.gov/Gulf-of-Tonkin", "english"),
    ("Operation Gladio — NATO Stay-Behind Armies", "Italy", "Lazio",
     "European Parliament resolution and declassified documents on secret NATO paramilitary networks in Western Europe during the Cold War, linked to terrorism and political manipulation. Source: European Parliament archives", "english"),
    ("Vault 7 — CIA Hacking Tools", "United States", "Virginia",
     "Thousands of documents detailing CIA cyber weapons: smartphone exploits, smart TV surveillance ('Weeping Angel'), zero-day exploits for iOS, Android, Windows. Source: wikileaks.org (Vault 7)", "english"),
    ("Operation CHAOS — CIA Domestic Surveillance", "United States", "Virginia",
     "CIA domestic surveillance program (1967-1974) targeting anti-war activists, violating the CIA's charter prohibiting domestic operations. Documented in Church Committee reports. Source: aarclibrary.org", "english"),

    # Human Rights & War Crimes
    ("Goldstone Report — Gaza 2009", "Israel", "Southern District",
     "UN Fact-Finding Mission report on Gaza conflict documenting potential war crimes by both Israel and Hamas. 575 pages. Source: un.org/unispal", "english"),
    ("Khashoggi Murder — UN Investigation Report", "Saudi Arabia", "Makkah",
     "Agnès Callamard's UN report on the extrajudicial killing of journalist Jamal Khashoggi at the Saudi consulate in Istanbul, Turkey, October 2018. Source: ohchr.org", "english"),
    ("Chilcot Report — UK Iraq War Inquiry", "United Kingdom", "England",
     "2.6 million word inquiry into UK's role in the Iraq War. 12 volumes documenting misleading intelligence and flawed decision-making by Tony Blair's government. Source: UK National Archives", "english"),
    ("Myanmar/Rohingya — UN Fact-Finding Mission", "Myanmar", "Rakhine",
     "Detailed evidence of genocide, crimes against humanity, and war crimes committed against the Rohingya people by Myanmar's military. Source: ohchr.org", "english"),
    ("Syria Caesar Photos — Systematic Torture Evidence", "Syria", "Damascus",
     "Evidence from 'Caesar,' a military defector who smuggled 55,000 photos documenting systematic torture and killing in Assad's prisons. Source: Human Rights Watch", "english"),
    ("CIA Rendition & Black Sites — EU Parliament Report", "Poland", "Masovia",
     "European Parliament investigation documenting 1,245+ CIA rendition flights through European airspace and secret prisons in Poland, Romania, Lithuania. Source: europarl.europa.eu", "english"),
    ("Collateral Murder — Baghdad Airstrike Video", "Iraq", "Baghdad",
     "Classified gunsight footage of 2007 U.S. Apache helicopter attack in Baghdad killing civilians including two Reuters journalists. Source: collateralmurder.wikileaks.org", "english"),
    ("Yemen War Crimes — UN Eminent Experts Reports", "Yemen", "Sana'a",
     "Evidence of war crimes by all parties in Yemen conflict, including Saudi-led coalition airstrikes on civilians, blockade, and use of child soldiers. Source: ohchr.org", "english"),

    # Medical & Scientific Ethics
    ("Tuskegee Syphilis Experiment Documents", "United States", "Alabama",
     "Records of the 40-year (1932-1972) U.S. government experiment withholding syphilis treatment from Black men. One of the most infamous examples of unethical medical research. Source: NLM Digital Collections, CDC Stacks", "english"),
    ("Guatemala Syphilis Experiments", "Guatemala", "Guatemala",
     "Documents showing U.S. researchers deliberately infected Guatemalan prisoners and mental patients with STDs (1946-1948). Exposed 2010. Source: Presidential Commission for Bioethical Issues", "english"),
    ("Tobacco Industry Internal Documents", "United States", "North Carolina",
     "14+ million internal documents from tobacco companies revealing decades of deception about health risks, addiction science, and marketing to children. Source: industrydocuments.ucsf.edu/tobacco", "english"),
    ("Opioid Crisis — Purdue Pharma Documents", "United States", "Connecticut",
     "Internal Purdue Pharma communications and court filings exposing aggressive OxyContin marketing despite known addiction risks. Contributed to 500,000+ overdose deaths. Source: court repositories", "english"),

    # Corporate & Financial
    ("Facebook Papers — Meta Internal Documents", "United States", "California",
     "Tens of thousands of internal Meta documents leaked by Frances Haugen showing the company knew its platforms harmed teens, amplified misinformation, and fueled political violence globally. Source: FBarchive (Harvard)", "english"),
    ("Boeing 737 MAX Internal Documents", "United States", "Illinois",
     "Internal Boeing communications revealing employees knew about MCAS safety flaws before two fatal crashes killing 346 people. Released by House Transportation Committee. Source: transportation.house.gov", "english"),
    ("Uber Files — Global Lobbying Exposé", "Netherlands", "North Holland",
     "124,000+ leaked documents exposing Uber's lobbying of world leaders, use of 'kill switch' to evade police raids, and exploitation of driver violence for PR. Source: theguardian.com/uber-files", "english"),
    ("Swiss Leaks — HSBC Tax Evasion", "Switzerland", "Geneva",
     "Leaked files from HSBC's Swiss private bank revealing 100,000+ accounts enabling tax evasion across 200+ countries. Over $100 billion exposed. Source: icij.org/swiss-leaks", "english"),
    ("Suisse Secrets — Credit Suisse Exposé", "Switzerland", "Zürich",
     "Leaked data on 30,000+ Credit Suisse clients including autocrats, war criminals, and human traffickers holding over 100 billion Swiss francs. Source: icij.org", "english"),
    ("Luanda Leaks — Isabel dos Santos", "Angola", "Luanda",
     "715,000 documents exposing how Africa's richest woman, Isabel dos Santos, siphoned billions from Angola through Western consulting firms and banks. Source: icij.org/luanda-leaks", "english"),
    ("1MDB Scandal — DOJ Filings", "Malaysia", "Kuala Lumpur",
     "U.S. Department of Justice filings detailing $4.5 billion embezzled from Malaysia's sovereign wealth fund 1MDB, involving Goldman Sachs and political corruption. Source: justice.gov", "english"),
    ("FinCEN Files — $2 Trillion in Dirty Money", "United States", "District of Columbia",
     "2,100+ suspicious activity reports showing how global banks moved $2 trillion in dirty money while filing reports with FinCEN but continuing transactions. Source: icij.org/fincen-files", "english"),
    ("Mauritius Leaks — Tax Treaty Exploitation", "Mauritius", "Port Louis",
     "200,000+ documents revealing how multinational corporations exploit Mauritius tax treaties to avoid paying taxes in Africa and Asia. Source: icij.org/mauritius-leaks", "english"),

    # Surveillance & Cyber
    ("Pegasus Project — NSO Group Spyware", "Israel", "Tel Aviv",
     "Investigation revealing NSO Group's Pegasus spyware targeted 50,000+ phone numbers of journalists, activists, and heads of state worldwide. Source: forbiddenstories.org", "english"),
    ("Operation Rubicon — Crypto AG / CIA Front Company", "Switzerland", "Zug",
     "CIA and German BND secretly owned Swiss encryption company Crypto AG for decades, reading encrypted communications of 120+ governments worldwide. Exposed 2020. Source: Washington Post/ZDF", "english"),
    ("GCHQ Tempora — Mass Internet Surveillance", "United Kingdom", "England",
     "Documents showing Britain's GCHQ tapped undersea fiber optic cables to mass-intercept global internet traffic and shared data with NSA. Source: Snowden archives", "english"),
    ("Five Eyes Intelligence Alliance Documents", "Australia", "Australian Capital Territory",
     "Leaked agreements and operational documents detailing the intelligence-sharing alliance between US, UK, Canada, Australia, and New Zealand. Source: Snowden archives, theintercept.com", "english"),

    # UN & International Reports
    ("UN Commission of Inquiry — Israel/Palestine", "Israel", "Jerusalem",
     "Reports from the UN Commission of Inquiry (2022-present) documenting apartheid, occupation practices, and potential crimes against humanity in occupied Palestinian territories. Source: ohchr.org", "english"),
    ("ICJ Advisory Opinion — Israeli Occupation (2024)", "Netherlands", "South Holland",
     "International Court of Justice ruling that Israel's prolonged occupation of Palestinian territories is unlawful under international law. Source: icj-cij.org", "english"),
    ("Amnesty International — Israel Apartheid Report", "United Kingdom", "England",
     "280-page Amnesty International investigation (2022) concluding Israel's treatment of Palestinians constitutes apartheid under international law. Source: amnesty.org", "english"),
    ("Human Rights Watch — 'A Threshold Crossed'", "United States", "New York",
     "Human Rights Watch report (2021) concluding Israeli authorities are committing crimes of apartheid and persecution against Palestinians. Source: hrw.org", "english"),
    ("UN Report — North Korean Human Rights", "South Korea", "Seoul",
     "UN Commission of Inquiry (2014) finding crimes against humanity in North Korea including extermination, enslavement, torture, and political prison camps. Source: ohchr.org", "english"),
    ("Srebrenica Genocide — ICTY Evidence", "Bosnia and Herzegovina", "Federation of B&H",
     "International Criminal Tribunal for the former Yugoslavia records documenting the 1995 Srebrenica massacre where 8,000+ Bosniak men and boys were killed. Source: icty.org, irmct.org", "english"),
    ("Rwanda Genocide — ICTR Records", "Rwanda", "Kigali",
     "International Criminal Tribunal for Rwanda judgments and evidence documenting the 1994 genocide that killed an estimated 800,000 people. Source: irmct.org", "english"),

    # Historical Declassified
    ("CIA Coup — Guatemala 1954 (PBSUCCESS)", "Guatemala", "Guatemala",
     "Declassified documents on CIA-engineered overthrow of democratically elected President Jacobo Árbenz in 1954, at the behest of United Fruit Company. Source: nsarchive.gwu.edu, cia.gov/readingroom", "english"),
    ("CIA Coup — Iran 1953 (TPAJAX)", "Iran", "Tehran",
     "Declassified CIA history of the overthrow of democratically elected Prime Minister Mohammad Mossadegh in 1953 to protect British oil interests. Released 2013 & 2017. Source: nsarchive.gwu.edu", "english"),
    ("CIA Coup — Chile 1973", "Chile", "Santiago Metropolitan",
     "Documents on CIA involvement in the overthrow and death of democratically elected President Salvador Allende, replaced by Pinochet dictatorship. Source: nsarchive.gwu.edu", "english"),
    ("Operation Condor — South American Repression", "Argentina", "Buenos Aires",
     "Declassified records on the coordinated campaign of political repression, torture, and assassination by South American dictatorships (1970s-80s) with U.S. support. Source: nsarchive.gwu.edu", "english"),
    ("Phoenix Program — Vietnam CIA Assassinations", "Vietnam", "Ho Chi Minh City",
     "Declassified documents on CIA's assassination and detention program targeting Viet Cong infrastructure during the Vietnam War. Estimated 20,000-40,000 killed. Source: cia.gov/readingroom", "english"),
    ("Japanese-American Internment Records", "United States", "California",
     "WWII-era documents on the forced internment of 120,000 Japanese Americans in concentration camps following Executive Order 9066. Source: archives.gov, densho.org", "english"),
    ("Operation Paperclip — Nazi Scientist Recruitment", "United States", "District of Columbia",
     "Records on the secret U.S. program recruiting over 1,600 Nazi German scientists, engineers, and technicians after WWII, many with war crimes connections. Source: archives.gov, cia.gov/readingroom", "english"),

    # Whistleblower & Accountability
    ("The Black Vault — Comprehensive FOIA Archive", "United States", "California",
     "Independent researcher John Greenewald's massive archive of FOIA-obtained government documents spanning UFOs, CIA, FBI, NSA, and classified military programs. Source: theblackvault.com", "english"),
    ("WikiLeaks Global Intelligence Files — Stratfor", "United States", "Texas",
     "5+ million emails from private intelligence firm Stratfor revealing surveillance of activists, corporate espionage, and covert government contractor practices. Source: wikileaks.org", "english"),
    ("Hacking Team Leaked Emails", "Italy", "Lombardy",
     "400GB of internal data from Italian surveillance company Hacking Team, revealing sales of intrusion software to authoritarian governments including Sudan, Saudi Arabia, and Ethiopia. Source: wikileaks.org", "english"),
]


def generate_pdf(title: str, description: str) -> bytes:
    """Generate a simple placeholder PDF with document info."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Replace Unicode characters that fpdf can't handle
    def clean(text):
        return (text
            .replace('\u2014', '-')   # em dash
            .replace('\u2013', '-')   # en dash  
            .replace('\u2018', "'")   # left single quote
            .replace('\u2019', "'")   # right single quote
            .replace('\u201c', '"')   # left double quote
            .replace('\u201d', '"')   # right double quote
            .replace('\u2026', '...')  # ellipsis
            .replace('\u00e1', 'a')   # á
            .replace('\u00e9', 'e')   # é
            .replace('\u00f3', 'o')   # ó
            .encode('latin-1', 'replace').decode('latin-1')
        )
    
    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 10, clean(title))
    pdf.ln(5)
    
    # Separator
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Description
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, clean(description))
    pdf.ln(10)
    
    # Footer note
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 5, "This is a reference document uploaded to HaqNow.org. The original source documents are publicly available at the links referenced above.")
    
    return pdf.output()


def create_api_key_in_db() -> str:
    """Create an API key directly in the database and return the plaintext key."""
    try:
        import pymysql
    except ImportError:
        os.system("pip3 install --break-system-packages pymysql 2>/dev/null")
        import pymysql
    
    # Parse DB URL
    # mysql+pymysql://user:pass@host:port/db
    parts = DB_URL.replace("mysql+pymysql://", "").split("@")
    user_pass = parts[0].split(":")
    host_port_db = parts[1].split("/")
    host_port = host_port_db[0].split(":")
    
    conn = pymysql.connect(
        host=host_port[0],
        port=int(host_port[1]),
        user=user_pass[0],
        password=user_pass[1],
        database=host_port_db[1],
        ssl={"ssl": True}
    )
    
    # Check if key already exists
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM api_keys WHERE name = 'bulk-upload' AND is_active = 1")
    existing = cursor.fetchone()
    
    if existing:
        print("API key 'bulk-upload' already exists but we don't know the plaintext. Creating a new one...")
        # Delete old one
        cursor.execute("DELETE FROM api_keys WHERE name = 'bulk-upload'")
        conn.commit()
    
    # Generate key
    prefix = secrets.token_urlsafe(6)[:10]
    secret_part = secrets.token_urlsafe(32)
    plaintext_key = f"hn_{prefix}_{secret_part}"
    key_hash = hashlib.sha256(plaintext_key.encode("utf-8")).hexdigest()
    
    cursor.execute(
        """INSERT INTO api_keys (name, key_hash, key_prefix, scopes, is_active, created_by, created_at, last_used_at, usage_count)
        VALUES (%s, %s, %s, %s, 1, %s, NOW(), NULL, 0)""",
        ("bulk-upload", key_hash, prefix, json.dumps(["upload", "download"]), "script@haqnow.com")
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Created API key: {plaintext_key[:20]}...")
    return plaintext_key


def upload_document(session: requests.Session, api_key: str, title: str, country: str, state: str, description: str, language: str, pdf_bytes: bytes, filename: str, max_retries: int = 5) -> tuple:
    """Upload a single document via the API with retry logic."""
    headers = {
        "X-API-Key": api_key
    }
    
    for attempt in range(max_retries):
        files = {
            "file": (filename, io.BytesIO(pdf_bytes), "application/pdf")
        }
        data = {
            "title": title,
            "country": country,
            "state": state,
            "description": description,
            "document_language": language,
        }
        
        try:
            resp = session.post(
                f"{API_BASE}/file-uploader/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            
            if resp.status_code == 200:
                try:
                    return resp.status_code, resp.json()
                except Exception:
                    return resp.status_code, {"document_id": "?"}
            elif resp.status_code in (429, 502, 503):
                wait = (attempt + 1) * 15  # 15s, 30s, 45s
                print(f"{resp.status_code} - waiting {wait}s (attempt {attempt+1}/{max_retries})...", end=" ", flush=True)
                time.sleep(wait)
                continue
            else:
                try:
                    return resp.status_code, resp.json()
                except Exception:
                    return resp.status_code, resp.text[:100]
        except requests.exceptions.ConnectionError:
            wait = (attempt + 1) * 15
            print(f"connection error, waiting {wait}s (attempt {attempt+1}/{max_retries})...", end=" ", flush=True)
            time.sleep(wait)
            continue
        except requests.exceptions.Timeout:
            wait = (attempt + 1) * 15
            print(f"timeout, waiting {wait}s (attempt {attempt+1}/{max_retries})...", end=" ", flush=True)
            time.sleep(wait)
            continue
        except Exception as e:
            return 0, str(e)
    
    return 503, "Max retries exceeded"


def main():
    print(f"=== HaqNow.org Bulk Document Upload ===")
    print(f"Documents to upload: {len(DOCUMENTS)}")
    print()
    
    api_key = os.getenv("HAQNOW_API_KEY")
    print(f"Using API key: {api_key[:20]}...")
    
    start_from = 1
    if len(sys.argv) > 1:
        try:
            start_from = int(sys.argv[1])
            print(f"Resuming from document #{start_from}")
        except ValueError:
            pass
    print()
    
    # Create session with Deflect cookie support
    session = requests.Session()
    session.headers.update({
        "X-API-Key": api_key,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    # Warmup request to get Deflect cookies
    try:
        session.get(f"{API_BASE}/file-uploader/rate-limit-status", timeout=10)
    except Exception:
        pass
    
    # Check existing docs to skip duplicates
    print("Checking for existing documents...")
    existing_titles = set()
    try:
        resp = requests.get(f"{API_BASE}/search/documents?limit=200", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            docs = data.get("documents", data) if isinstance(data, dict) else data
            if isinstance(docs, list):
                for doc in docs:
                    if isinstance(doc, dict):
                        existing_titles.add(doc.get("title", ""))
        print(f"  Found {len(existing_titles)} existing documents")
    except Exception as e:
        print(f"  Could not check existing docs: {e}")
    print()
    
    print("Uploading documents...")
    success = 0
    failed = 0
    skipped = 0
    
    for i, (title, country, state, description, language) in enumerate(DOCUMENTS, 1):
        if i < start_from:
            continue
        
        if title in existing_titles:
            print(f"  [{i}/{len(DOCUMENTS)}] {title[:60]}... SKIP (exists)")
            skipped += 1
            continue
        
        pdf_bytes = generate_pdf(title, description)
        filename = f"expose_{i:03d}.pdf"
        
        print(f"  [{i}/{len(DOCUMENTS)}] {title[:60]}...", end=" ", flush=True)
        
        try:
            status_code, result = upload_document(
                session, api_key, title, country, state, description, language, pdf_bytes, filename
            )
            
            if status_code == 200:
                doc_id = result.get("document_id", "?")
                print(f"\u2705 (id={doc_id})")
                success += 1
            else:
                print(f"\u274c ({status_code}: {str(result)[:80]})")
                failed += 1
        except Exception as e:
            print(f"\u274c (error: {e})")
            failed += 1
        
        time.sleep(10)
    
    print()
    print(f"=== Upload Complete ===")
    print(f"  Success: {success}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print(f"  Total:   {len(DOCUMENTS)}")
    print()
    print("NOTE: Documents uploaded with status='pending'. Approve via admin panel.")


if __name__ == "__main__":
    main()

