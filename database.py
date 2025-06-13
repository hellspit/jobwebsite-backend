from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise ValueError("Missing Supabase credentials in .env file")

class DatabaseHandler:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.table_name = "job_postings"
        self.max_entries = 25

    async def insert_job_posting(self, job_data: dict) -> bool:
        """
        Insert a job posting into Supabase if it's for 2026 passouts
        and maintain only the latest 25 entries
        """
        try:
            if not job_data["is_relevant"]:
                return False

            structured_data = job_data["structured_data"]
            
            # Prepare data for insertion
            job_record = {
                "job_title": structured_data["job"],
                "company": structured_data["company"],
                "salary": structured_data["salary"],
                "location": structured_data["location"],
                "apply_link": structured_data["apply_link"],
                "year": "2026",
                "posted_at": datetime.now().isoformat(),
                "raw_text": job_data.get("raw_analysis", "")
            }

            # Insert new record
            result = self.supabase.table(self.table_name).insert(job_record).execute()
            
            if result.data:
                # Get total count of entries
                count_result = self.supabase.table(self.table_name).select("id", count="exact").execute()
                total_count = count_result.count

                # If we have more than max_entries, delete the oldest ones
                if total_count > self.max_entries:
                    # Get the IDs of entries to delete (oldest ones)
                    delete_query = self.supabase.table(self.table_name)\
                        .select("id")\
                        .order("posted_at", desc=False)\
                        .limit(total_count - self.max_entries)\
                        .execute()
                    
                    if delete_query.data:
                        # Delete the oldest entries
                        ids_to_delete = [entry["id"] for entry in delete_query.data]
                        self.supabase.table(self.table_name)\
                            .delete()\
                            .in_("id", ids_to_delete)\
                            .execute()
                        
                        logging.info(f"Deleted {len(ids_to_delete)} oldest entries to maintain limit of {self.max_entries}")
                
                return True
            return False

        except Exception as e:
            logging.error(f"Error inserting job posting: {e}")
            return False

    async def get_jobs(self, year: str = None) -> list:
        """
        Retrieve job postings from Supabase
        """
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            if year:
                query = query.eq("year", year)
            
            result = query.order("posted_at", desc=True).limit(self.max_entries).execute()
            return result.data

        except Exception as e:
            logging.error(f"Error retrieving jobs: {e}")
            return []

# Create a singleton instance
db_handler = DatabaseHandler() 