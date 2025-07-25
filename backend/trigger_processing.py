#!/usr/bin/env python3
"""
Script to manually trigger document processing for testing
"""
import sys
import os
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set environment variables
os.environ['MISTRAL_API_KEY'] = '***REMOVED***'
os.environ['DATABASE_URL'] = 'mysql+pymysql://foi_user:***REMOVED***@localhost:3306/foi_archive'
os.environ['EXOSCALE_S3_ACCESS_KEY'] = '***REMOVED***'
os.environ['EXOSCALE_S3_SECRET_KEY'] = '***REMOVED***'
os.environ['EXOSCALE_S3_ENDPOINT'] = 'sos-ch-dk-2.exo.io'
os.environ['EXOSCALE_S3_REGION'] = 'ch-dk-2'
os.environ['EXOSCALE_BUCKET'] = 'foi-archive-terraform'
os.environ['EXOSCALE_S3_PUBLIC_URL'] = 'https://sos-ch-dk-2.exo.io/foi-archive-terraform'

# Add the app directory to Python path
sys.path.append('/opt/foi-archive/backend')

from app.database.database import SessionLocal
from app.apis.document_processing import process_document_internal

async def main():
    """Trigger processing for document ID 30"""
    
    # Create database session
    db = SessionLocal()
    
    try:
        print("Triggering processing for document ID 30...")
        result = await process_document_internal(30, db)
        
        if result:
            print("✅ Processing completed successfully!")
            print(f"Result: {result}")
        else:
            print("❌ Processing failed")
            
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 