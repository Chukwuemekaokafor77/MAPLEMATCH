import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import PyPDF2
import time
from datetime import datetime
from tqdm import tqdm
import psutil
import sys
import re

class CaseOrganizer:
    def __init__(self):
        load_dotenv()
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_DATABASE', 'legal_aid')
        }
        self.connection = None

    def connect_db(self):
        try:
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                print("Successfully connected to MySQL database")
        except Error as e:
            print(f"Error: {e}")
            raise

    def extract_metadata(self, file_path):
        """Extract metadata from PDF file with Canadian-specific information"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                
                # Extract basic metadata
                metadata = {
                    'title': reader.metadata.get('/Title', os.path.basename(file_path)),
                    'author': reader.metadata.get('/Author', ''),
                    'creation_date': reader.metadata.get('/CreationDate', ''),
                    'modified_date': reader.metadata.get('/ModDate', ''),
                    'practice_area': '',
                    'case_category': '',
                    'province': '',
                    'court': '',
                    'judge': '',
                    'filing_date': None,
                    'spouse_names': '',
                    'children_info': '',
                    'property_details': '',
                    'marriage_date': '',
                    'separation_date': '',
                    'custody_arrangement': '',
                    'support_amount': '',
                    'matter_id': '',
                    'client_id': '',
                    'lead_id': '',
                    'matter_status': 'open',
                    'matter_type': 'matter',
                    'priority': 'medium',
                    'next_action_date': None,
                    'next_action_description': '',
                    'matter_owner': '',
                    'team_members': '[]',
                    'matter_tags': '[]'
                }
                
                # Extract text content to determine case details
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                text_lower = text.lower()
                
                # Determine practice area and case category
                practice_patterns = {
                    'family_law': [
                        'divorce', 'custody', 'child', 'maintenance', 'support',
                        'adoption', 'domestic', 'abuse', 'pre-nuptial', 'post-nuptial'
                    ],
                    'criminal_law': [
                        'charge', 'indictment', 'plea', 'trial', 'sentence',
                        'bail', 'probation', 'parole'
                    ],
                    'immigration_law': [
                        'visa', 'permanent', 'residency', 'citizenship',
                        'work', 'permit', 'refugee', 'asylum'
                    ],
                    'aboriginal_law': [
                        'indigenous', 'aboriginal', 'first', 'nations',
                        'treaty', 'land', 'rights', 'reconciliation'
                    ],
                    'employment_law': [
                        'employment', 'workplace', 'termination', 'harassment',
                        'discrimination', 'union', 'collective', 'agreement'
                    ]
                }
                
                # Determine practice area
                for area, keywords in practice_patterns.items():
                    if any(keyword in text_lower for keyword in keywords):
                        metadata['practice_area'] = area
                        break
                else:
                    metadata['practice_area'] = 'other'
                
                # Determine case category (as before)
                if 'divorce' in text_lower or 'dissolution' in text_lower:
                    metadata['case_category'] = 'divorce'
                elif 'custody' in text_lower or 'child' in text_lower:
                    metadata['case_category'] = 'child_custody'
                elif 'maintenance' in text_lower or 'support' in text_lower:
                    metadata['case_category'] = 'maintenance'
                elif 'adoption' in text_lower:
                    metadata['case_category'] = 'adoption'
                elif 'domestic violence' in text_lower or 'abuse' in text_lower:
                    metadata['case_category'] = 'domestic_violence'
                elif 'child abuse' in text_lower or 'child neglect' in text_lower:
                    metadata['case_category'] = 'child_abuse'
                elif 'child support' in text_lower or 'child maintenance' in text_lower:
                    metadata['case_category'] = 'child_support'
                elif 'pre-nuptial' in text_lower or 'pre marriage' in text_lower:
                    metadata['case_category'] = 'pre_nuptial'
                elif 'post-nuptial' in text_lower or 'post marriage' in text_lower:
                    metadata['case_category'] = 'post_nuptial'
                elif 'annulment' in text_lower or 'invalid marriage' in text_lower:
                    metadata['case_category'] = 'annulment'
                elif 'legal separation' in text_lower or 'separation agreement' in text_lower:
                    metadata['case_category'] = 'legal_separation'
                elif 'parental rights' in text_lower or 'parental authority' in text_lower:
                    metadata['case_category'] = 'parental_rights'
                elif 'surrogacy' in text_lower or 'gestational carrier' in text_lower:
                    metadata['case_category'] = 'surrogacy'
                elif 'elder care' in text_lower or 'elder guardianship' in text_lower:
                    metadata['case_category'] = 'elder_care'
                else:
                    metadata['case_category'] = 'other'
                
                # Extract province information
                province_patterns = {
                    'Ontario': ['Ontario', 'ON'],
                    'Quebec': ['Quebec', 'QC'],
                    'British Columbia': ['British Columbia', 'BC'],
                    'Alberta': ['Alberta', 'AB'],
                    'Manitoba': ['Manitoba', 'MB'],
                    'Saskatchewan': ['Saskatchewan', 'SK'],
                    'Nova Scotia': ['Nova Scotia', 'NS'],
                    'New Brunswick': ['New Brunswick', 'NB'],
                    'Newfoundland and Labrador': ['Newfoundland', 'Labrador', 'NL'],
                    'Prince Edward Island': ['Prince Edward Island', 'PE'],
                    'Yukon': ['Yukon', 'YT'],
                    'Northwest Territories': ['Northwest Territories', 'NT'],
                    'Nunavut': ['Nunavut', 'NU']
                }
                
                for province, patterns in province_patterns.items():
                    if any(pattern.lower() in text_lower for pattern in patterns):
                        metadata['province'] = province
                        break
                else:
                    metadata['province'] = 'Unknown'
                
                # Extract court information
                court_patterns = {
                    'Supreme Court': ['Supreme Court', 'SCC'],
                    'Federal Court': ['Federal Court', 'FCT'],
                    'Court of Appeal': ['Court of Appeal', 'CA'],
                    'Superior Court': ['Superior Court', 'SC'],
                    'Provincial Court': ['Provincial Court', 'PC'],
                    'Family Court': ['Family Court', 'FC']
                }
                
                for court, patterns in court_patterns.items():
                    if any(pattern.lower() in text_lower for pattern in patterns):
                        metadata['court'] = court
                        break
                else:
                    metadata['court'] = 'Unknown'
                
                # Extract judge information
                judge_patterns = [
                    r"Honourable\s+([A-Za-z\s]+)",
                    r"Justice\s+([A-Za-z\s]+)",
                    r"Judge\s+([A-Za-z\s]+)",
                    r"J\s+\.\s+([A-Za-z\s]+)"
                ]
                
                for pattern in judge_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        metadata['judge'] = matches[0].strip()
                        break
                else:
                    metadata['judge'] = 'Unknown'
                
                # Extract filing date
                date_patterns = [
                    r"filed\s+on\s+(\d{1,2}/\d{1,2}/\d{4})",
                    r"received\s+on\s+(\d{1,2}/\d{1,2}/\d{4})",
                    r"submitted\s+on\s+(\d{1,2}/\d{1,2}/\d{4})"
                ]
                
                for pattern in date_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        metadata['filing_date'] = matches[0]
                        break
                else:
                    metadata['filing_date'] = None
                
                # Extract spouse names with more patterns
                spouse_patterns = [
                    r"(husband|wife|spouse|petitioner|respondent|plaintiff|defendant)\s+([A-Za-z\s]+)",
                    r"(petitioner|respondent|plaintiff|defendant):\s+([A-Za-z\s]+)",
                    r"(husband|wife|spouse)\s+known\s+as\s+([A-Za-z\s]+)",
                    r"(husband|wife|spouse)\s+named\s+([A-Za-z\s]+)",
                    r"(husband|wife|spouse)\s+is\s+([A-Za-z\s]+)",
                    r"(husband|wife|spouse)\s+called\s+([A-Za-z\s]+)",
                    r"(husband|wife|spouse)\s+([A-Za-z\s]+)\s+(?:of|at)"
                ]
                spouse_names = []
                for pattern in spouse_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        spouse_names.append(match[1].strip())
                metadata['spouse_names'] = ', '.join(spouse_names) if spouse_names else ''
                
                # Extract children information with more details
                children_patterns = [
                    r"child\s+(?:named|known as|called)\s+([A-Za-z\s]+)",
                    r"minor\s+child\s+([A-Za-z\s]+)\s+aged\s+(\d+)",
                    r"child\s+aged\s+(\d+)\s+years?\s+(?:old|of\s+age)",
                    r"child\s+born\s+on\s+(\d{1,2}/\d{1,2}/\d{4})",
                    r"child\s+currently\s+(\d+)\s+years?\s+old",
                    r"child\s+attending\s+(?:school|grade)\s+(\d+)"
                ]
                children_info = []
                for pattern in children_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            children_info.append(' '.join(match))
                        else:
                            children_info.append(match)
                metadata['children_info'] = ', '.join(children_info) if children_info else ''
                
                # Extract property details with more details
                property_patterns = [
                    r"property\s+at\s+([A-Za-z0-9\s,]+)",
                    r"house\s+at\s+([A-Za-z0-9\s,]+)",
                    r"property\s+valued\s+at\s+(\d+\.?\d*\s+(?:CAD|million|billion))",
                    r"real\s+estate\s+at\s+([A-Za-z0-9\s,]+)",
                    r"family\s+home\s+at\s+([A-Za-z0-9\s,]+)",
                    r"marital\s+property\s+at\s+([A-Za-z0-9\s,]+)",
                    r"property\s+acquired\s+on\s+(\d{1,2}/\d{1,2}/\d{4})",
                    r"property\s+worth\s+(\d+\.?\d*\s+(?:CAD|million|billion))"
                ]
                property_details = []
                for pattern in property_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            property_details.append(' '.join(match))
                        else:
                            property_details.append(match)
                metadata['property_details'] = ', '.join(property_details) if property_details else ''
                
                # Extract additional family law specific information
                metadata['marriage_date'] = next(
                    (match[0] for match in re.findall(r"married\s+on\s+(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['separation_date'] = next(
                    (match[0] for match in re.findall(r"separated\s+on\s+(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['custody_arrangement'] = next(
                    (match[0] for match in re.findall(r"(joint|sole|shared)\s+custody", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['support_amount'] = next(
                    (match[0] for match in re.findall(r"support\s+of\s+(\d+\.?\d*\s+(?:CAD|per\s+month|per\s+year))", text, re.IGNORECASE)),
                    ""
                )
                
                # Extract additional Canadian-specific information
                metadata['proceedings_type'] = next(
                    (match[0] for match in re.findall(r"(summary|trial|motion|application|appeal|reference|judicial\s+review)", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['court_level'] = next(
                    (match[0] for match in re.findall(r"(provincial|superior|appeal|supreme\s+court|federal\s+court)", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['legal_aid_status'] = next(
                    (match[0] for match in re.findall(r"(legal\s+aid\s+certificate|certificate\s+of\s+eligibility|legal\s+aid\s+approved)", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['indigenous_status'] = next(
                    (match[0] for match in re.findall(r"(indigenous|aboriginal|first\s+nations|metis|inuit)", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['language_rights'] = next(
                    (match[0] for match in re.findall(r"(french\s+language\s+rights|official\s+language\s+rights|bilingual\s+proceedings)", text, re.IGNORECASE)),
                    ""
                )
                
                # Extract case duration
                duration_patterns = [
                    r"case\s+duration:\s+(\d+)\s+months",
                    r"proceedings\s+lasted\s+(\d+)\s+months",
                    r"(\d+)\s+months\s+from\s+start\s+to\s+finish",
                    r"(\d+)\s+months\s+to\s+resolve"
                ]
                metadata['case_duration'] = next(
                    (match[0] for pattern in duration_patterns for match in re.findall(pattern, text, re.IGNORECASE)),
                    ""
                )
                
                # Extract legal costs
                cost_patterns = [
                    r"legal\s+fees:\s+(\d+\.?\d*\s+CAD)",
                    r"costs\s+awarded:\s+(\d+\.?\d*\s+CAD)",
                    r"disbursements:\s+(\d+\.?\d*\s+CAD)",
                    r"total\s+costs:\s+(\d+\.?\d*\s+CAD)"
                ]
                metadata['legal_costs'] = next(
                    (match[0] for pattern in cost_patterns for match in re.findall(pattern, text, re.IGNORECASE)),
                    ""
                )
                
                # Extract client income information
                income_patterns = [
                    r"annual\s+income:\s+(\d+\.?\d*\s+CAD)",
                    r"income\s+of:\s+(\d+\.?\d*\s+CAD)\s+per\s+year",
                    r"income:\s+(\d+\.?\d*\s+CAD)\s+monthly",
                    r"income:\s+(\d+\.?\d*\s+CAD)\s+weekly"
                ]
                metadata['client_income'] = next(
                    (match[0] for pattern in income_patterns for match in re.findall(pattern, text, re.IGNORECASE)),
                    ""
                )
                
                # Extract case outcome
                outcome_patterns = [
                    r"judgment\s+for\s+(plaintiff|defendant)",
                    r"case\s+(dismissed|settled|resolved)",
                    r"order\s+for\s+(payment|compensation|damages)",
                    r"(granted|denied|awarded)\s+(injunction|damages|costs)"
                ]
                metadata['case_outcome'] = next(
                    (match[0] for pattern in outcome_patterns for match in re.findall(pattern, text, re.IGNORECASE)),
                    ""
                )
                
                # Generate matter ID with more specific format
                metadata['matter_id'] = f"CAN-{metadata['province'][:3].upper()}-{metadata['practice_area'][:3].upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                metadata['separation_date'] = next(
                    (match[0] for match in re.findall(r"separated\s+on\s+(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['custody_arrangement'] = next(
                    (match[0] for match in re.findall(r"(joint|sole|shared)\s+custody", text, re.IGNORECASE)),
                    ""
                )
                
                metadata['support_amount'] = next(
                    (match[0] for match in re.findall(r"support\s+of\s+(\d+\.?\d*\s+(?:CAD|per\s+month|per\s+year))", text, re.IGNORECASE)),
                    ""
                )
                
                # Generate matter ID
                metadata['matter_id'] = f"CAN-{metadata['practice_area'][:3].upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                
                return metadata

                # Extract children information
                children_patterns = [
                    r"child\s+(?:named|known as)\s+([A-Za-z\s]+)",
                    r"minor\s+([A-Za-z\s]+)\s+aged",
                    r"child\s+aged\s+(\d+)"
                ]
                children_info = []
                for pattern in children_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    children_info.extend(matches)
                metadata['children_info'] = ', '.join(children_info) if children_info else ''

                # Extract property details
                property_patterns = [
                    r"property\s+at\s+([A-Za-z0-9\s,]+)",
                    r"house\s+at\s+([A-Za-z0-9\s,]+)",
                    r"property\s+valued\s+at\s+(\d+\s+USD|\d+\s+million|\d+\s+billion)"
                ]
                property_details = []
                for pattern in children_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    property_details.extend(matches)
                metadata['property_details'] = ', '.join(property_details) if property_details else ''
        except Exception as e:
            print(f"Error extracting metadata from {file_path}: {e}")

        return metadata

    def process_case_files(self, base_path):
        """Process all case files in the directory structure with progress tracking"""
        try:
            cursor = self.connection.cursor()
            start_time = time.time()
            total_files = 0
            processed_files = 0
            
            # First, count total files to process
            for year in range(2008, 2024):
                year_dir = os.path.join(base_path, str(year))
                if os.path.exists(year_dir):
                    for court_type in ['appeal', 'federal', 'supreme']:
                        court_dir = os.path.join(year_dir, court_type)
                        if os.path.exists(court_dir):
                            pdf_dir = os.path.join(court_dir, 'pdf_downloads')
                            if os.path.exists(pdf_dir):
                                total_files += len([f for f in os.listdir(pdf_dir) if f.endswith('.pdf')])
        
            print(f"\nTotal files to process: {total_files}\n")
            
            # Walk through the directory structure
            for year in range(2008, 2024):  # 2008-2023
                year_dir = os.path.join(base_path, str(year))
                if os.path.exists(year_dir):
                    for court_type in ['appeal', 'federal', 'supreme']:
                        court_dir = os.path.join(year_dir, court_type)
                        if os.path.exists(court_dir):
                            pdf_dir = os.path.join(court_dir, 'pdf_downloads')
                            if os.path.exists(pdf_dir):
                                pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
                                
                                if pdf_files:
                                    print(f"\nProcessing {year} {court_type} cases ({len(pdf_files)} files)...")
                                
                                for file in tqdm(pdf_files, desc=f"{year} {court_type}", unit="file"):
                                    processed_files += 1
                                    file_path = os.path.join(pdf_dir, file)
                                    
                                    # Extract case number from filename
                                    case_number = file.replace('.pdf', '')
                                    
                                    # Extract metadata
                                    document_metadata = self.extract_metadata(file_path)
                                    
                                    # Insert case record with verification status
                                    cursor.execute("""
                                        INSERT INTO cases (case_number, title, court, status, case_category, spouse_names, children_info, 
                                            marriage_date, separation_date, custody_arrangement, support_amount, 
                                            verification_status)
                                        SELECT %s, %s, %s, 'Pending', %s, %s, %s, %s, %s, %s, %s, 'pending'
                                        WHERE NOT EXISTS (
                                            SELECT 1 FROM cases WHERE case_number = %s
                                        )
                                    """, (
                                        str(case_number),
                                        str(document_metadata.get('title', case_number) or ''),
                                        str(court_type),
                                        str(document_metadata.get('case_category', '')),
                                        str(document_metadata.get('spouse_names', '')),
                                        str(document_metadata.get('children_info', '')),
                                        str(document_metadata.get('marriage_date', '')),
                                        str(document_metadata.get('separation_date', '')),
                                        str(document_metadata.get('custody_arrangement', '')),
                                        str(document_metadata.get('support_amount', '')),
                                        str(case_number)
                                    ))
                                    
                                    # Get case_id
                                    cursor.execute("SELECT id FROM cases WHERE case_number = %s", (case_number,))
                                    result = cursor.fetchone()
                                    case_id = result[0] if result else None
                                    
                                    if case_id:
                                        # Insert document record
                                        cursor.execute("""
                                            INSERT INTO case_documents (case_id, document_name, document_type, file_path)
                                            VALUES (%s, %s, %s, %s)
                                        """, (
                                            case_id,
                                            str(document_metadata['document_name']),
                                            str(document_metadata['document_type']),
                                            str(document_metadata['file_path'])
                                        ))
                                        
                                    # Show memory usage
                                    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
                                    sys.stdout.write(f"\rMemory usage: {memory_usage:.1f} MB\033[K")
                                    sys.stdout.flush()
        
            # Final progress report
            elapsed_time = time.time() - start_time
            print(f"\nProcessing complete. Processed {processed_files}/{total_files} files.")
            print(f"Total time taken: {elapsed_time:.2f}s")
            
            cursor.close()
        except Exception as e:
            print(f"Error in process_case_files: {e}")
            if cursor:
                cursor.close()
        
        self.connection.commit()
        
        # Show summary
        end_time = time.time()
        total_time = end_time - start_time
        files_per_second = total_files / total_time if total_time > 0 else 0
        
        print(f"\n\nProcessing complete!")
        print(f"Total files processed: {processed_files}")
        print(f"Total time: {total_time:.1f} seconds")
        print(f"Files per second: {files_per_second:.1f}")
        print(f"Memory usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB")
        
    def close_connection(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")

if __name__ == "__main__":
    organizer = CaseOrganizer()
    
    try:
        organizer.connect_db()
        
        # Process the case files
        base_path = "D:\\main_metadata_fed (1)\\main_metadata_fed"
        organizer.process_case_files(base_path)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        organizer.close_connection()
