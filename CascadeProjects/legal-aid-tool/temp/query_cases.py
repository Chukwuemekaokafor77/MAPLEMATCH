import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def connect_db():
    """Connect to the MySQL database"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_DATABASE', 'legal_aid')
    }
    
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Successfully connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def display_case_details(case_id, cursor):
    """Display details of a specific case with verification status"""
    # Get case information
    cursor.execute("""
        SELECT c.id, c.case_number, c.title, c.court, c.status, c.case_category,
               c.spouse_names, c.children_info, c.property_details,
               c.marriage_date, c.separation_date, c.custody_arrangement,
               c.support_amount, c.verification_status, c.verification_notes
        FROM cases c
        WHERE c.id = %s
    """, (case_id,))
    
    case_data = cursor.fetchone()
    if not case_data:
        print(f"No case found with ID {case_id}")
        return
    
    print(f"\nCase ID: {case_data[0]}")
    print(f"Case Number: {case_data[1]}")
    print(f"Title: {case_data[2]}")
    print(f"Court: {case_data[3]}")
    print(f"Status: {case_data[4]}")
    print(f"Category: {case_data[5]}")
    print(f"Verification Status: {case_data[13]}")
    
    if case_data[14]:  # verification_notes
        print(f"Verification Notes: {case_data[14]}")
    
    print("\nParties:")
    if case_data[6]:  # spouse_names
        print(f"Spouses: {case_data[6]}")
    
    print("\nChildren:")
    if case_data[7]:  # children_info
        print(f"Children: {case_data[7]}")
    
    print("\nProperty:")
    if case_data[8]:  # property_details
        print(f"Property: {case_data[8]}")
    
    print("\nKey Dates:")
    if case_data[9]:  # marriage_date
        print(f"Marriage Date: {case_data[9]}")
    if case_data[10]:  # separation_date
        print(f"Separation Date: {case_data[10]}")
    
    print("\nArrangements:")
    if case_data[11]:  # custody_arrangement
        print(f"Custody: {case_data[11]}")
    if case_data[12]:  # support_amount
        print(f"Support Amount: {case_data[12]}")
    
    # Get documents
    cursor.execute("""
        SELECT cd.document_name, cd.document_type, cd.file_path
        FROM case_documents cd
        WHERE cd.case_id = %s
    """, (case_id,))
    
    print("\nDocuments:")
    documents = cursor.fetchall()
    for doc in documents:
        print(f"- {doc[0]} ({doc[1]})")
        print(f"  Path: {doc[2]}")

    # Get verification history
    cursor.execute("""
        SELECT v.verified_by, v.verification_date, v.status, v.notes
        FROM case_verifications v
        WHERE v.case_id = %s
        ORDER BY v.verification_date DESC
        LIMIT 5
    """, (case_id,))
    
    print("\nVerification History:")
    verifications = cursor.fetchall()
    for ver in verifications:
        print(f"- Verified by {ver[0]} on {ver[1]}")
        print(f"  Status: {ver[2]}")
        if ver[3]:  # notes
            print(f"  Notes: {ver[3]}")

def verify_case(case_id, cursor, user_name):
    """Verify a case's information"""
    cursor.execute("""
        UPDATE cases 
        SET verification_status = 'verified', 
            verified_by = %s, 
            verification_date = CURRENT_TIMESTAMP
        WHERE id = %s
    """, (user_name, case_id))
    
    cursor.execute("""
        INSERT INTO case_verifications (case_id, verified_by, status, notes)
        VALUES (%s, %s, 'verified', %s)
    """, (case_id, user_name, "Manually verified case information"))

def update_case(case_id, field_name, new_value, cursor, user_name):
    """Update a specific field in a case"""
    # Get old value
    cursor.execute(f"SELECT {field_name} FROM cases WHERE id = %s", (case_id,))
    old_value = cursor.fetchone()[0]
    
    # Update the field
    cursor.execute(f"UPDATE cases SET {field_name} = %s WHERE id = %s", (new_value, case_id))
    
    # Record the update
    cursor.execute("""
        INSERT INTO case_updates (case_id, updated_by, field_name, old_value, new_value, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (case_id, user_name, field_name, old_value, new_value, "Manual update"))

def generate_statistics(cursor, province=None, practice_area=None):
    """Generate statistics report for cases"""
    where_clause = ""
    if province or practice_area:
        conditions = []
        if province:
            conditions.append(f"province = '{province}'")
        if practice_area:
            conditions.append(f"practice_area = '{practice_area}'")
        where_clause = "WHERE " + " AND ".join(conditions)
    
    cursor.execute(f"""
        SELECT 
            practice_area,
            COUNT(*) as total_cases,
            AVG(DATEDIFF(COALESCE(closed_at, CURRENT_DATE), created_at)) as avg_duration,
            AVG(billable_hours) as avg_hours,
            AVG(total_amount) as avg_amount
        FROM cases
        {where_clause}
        GROUP BY practice_area
    """)
    
    print("\nCase Statistics Report")
    print("-" * 50)
    print(f"Province: {province if province else 'All'}")
    print(f"Practice Area: {practice_area if practice_area else 'All'}")
    print("\nPractice Area | Total Cases | Avg Duration | Avg Hours | Avg Amount")
    print("-" * 70)
    
    stats = cursor.fetchall()
    for stat in stats:
        print(f"{stat[0]:<20} | {stat[1]:<10} | {stat[2]:<12.1f} days | {stat[3]:<9.1f} | CAD {stat[4]:,.2f}")
    
    cursor.execute(f"""
        SELECT 
            province,
            COUNT(*) as total_cases,
            AVG(billable_hours) as avg_hours,
            AVG(total_amount) as avg_amount
        FROM cases
        {where_clause}
        GROUP BY province
    """)
    
    print("\nProvince Statistics")
    print("-" * 50)
    print("Province | Total Cases | Avg Hours | Avg Amount")
    print("-" * 50)
    
    province_stats = cursor.fetchall()
    for stat in province_stats:
        print(f"{stat[0]:<15} | {stat[1]:<10} | {stat[2]:<9.1f} | CAD {stat[3]:,.2f}")

def search_canlii(cursor, case_id):
    """Search CanLII for case information"""
    cursor.execute("""
        SELECT ci.canlii_id, ci.canlii_url, ci.canlii_citation,
               ci.canlii_decision_date, ci.canlii_judges, ci.canlii_court
        FROM canlii_integration ci
        WHERE ci.case_id = %s
    """, (case_id,))
    
    canlii_data = cursor.fetchone()
    if canlii_data:
        print("\nCanLII Information:")
        print(f"CanLII ID: {canlii_data[0]}")
        print(f"URL: {canlii_data[1]}")
        print(f"Citation: {canlii_data[2]}")
        print(f"Decision Date: {canlii_data[3]}")
        print(f"Judges: {canlii_data[4]}")
        print(f"Court: {canlii_data[5]}")
    else:
        print("No CanLII information available for this case")

def main():
    connection = connect_db()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    # Automatically search for pending verification cases
    print("\nSearching for cases pending verification...")
    cursor.execute("""
        SELECT id, case_number, title, case_category, province, practice_area
        FROM cases 
        WHERE verification_status = 'pending'
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    pending_cases = cursor.fetchall()
    if pending_cases:
        print("\nCases pending verification:")
        for case in pending_cases:
            print(f"\nCase ID: {case[0]}")
            print(f"Case Number: {case[1]}")
            print(f"Title: {case[2]}")
            print(f"Category: {case[3]}")
            print(f"Province: {case[4]}")
            print(f"Practice Area: {case[5]}")
    
    # Show menu after initial search
    while True:
        print("\nLegal Aid Case Viewer")
        print("1. Search cases by keyword")
        print("2. View case details by ID")
        print("3. Verify a case")
        print("4. Update case information")
        print("5. Generate statistics report")
        print("6. Search CanLII information")
        print("7. Exit")
        choice = input("\nEnter your choice (1-7): ")
        
        if choice == '1':
            keyword = input("Enter search keyword: ")
            search_cases(keyword, cursor)
        elif choice == '2':
            case_id = input("Enter case ID: ")
            try:
                display_case_details(int(case_id), cursor)
            except ValueError:
                print("Please enter a valid number for case ID")
        elif choice == '3':
            case_id = input("Enter case ID to verify: ")
            user_name = input("Enter your name: ")
            try:
                verify_case(int(case_id), cursor, user_name)
                print("Case verified successfully!")
            except Exception as e:
                print(f"Error verifying case: {e}")
        elif choice == '4':
            case_id = input("Enter case ID to update: ")
            field_name = input("Enter field name to update: ")
            new_value = input("Enter new value: ")
            user_name = input("Enter your name: ")
            try:
                update_case(int(case_id), field_name, new_value, cursor, user_name)
                print("Case updated successfully!")
            except Exception as e:
                print(f"Error updating case: {e}")
        elif choice == '5':
            province = input("Enter province (leave blank for all): ").strip()
            practice_area = input("Enter practice area (leave blank for all): ").strip()
            generate_statistics(cursor, province, practice_area)
        elif choice == '6':
            case_id = input("Enter case ID to search CanLII: ")
            try:
                search_canlii(cursor, int(case_id))
            except ValueError:
                print("Please enter a valid number for case ID")
        elif choice == '7':
            break
        else:
            print("Invalid choice. Please try again.")
    
    cursor.close()
    connection.commit()
    connection.close()
    print("\nGoodbye!")
    while True:
        print("\nLegal Aid Case Viewer")
        print("1. Search cases by keyword")
        print("2. View case details by ID")
        print("3. Verify a case")
        print("4. Update case information")
        print("5. Exit")
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            keyword = input("Enter search keyword: ")
            search_cases(keyword, cursor)
        elif choice == '2':
            case_id = input("Enter case ID: ")
            try:
                display_case_details(int(case_id), cursor)
            except ValueError:
                print("Please enter a valid number for case ID")
        elif choice == '3':
            case_id = input("Enter case ID to verify: ")
            user_name = input("Enter your name: ")
            try:
                verify_case(int(case_id), cursor, user_name)
                print("Case verified successfully!")
            except Exception as e:
                print(f"Error verifying case: {e}")
        elif choice == '4':
            case_id = input("Enter case ID to update: ")
            field_name = input("Enter field name to update: ")
            new_value = input("Enter new value: ")
            user_name = input("Enter your name: ")
            try:
                update_case(int(case_id), field_name, new_value, cursor, user_name)
                print("Case updated successfully!")
            except Exception as e:
                print(f"Error updating case: {e}")
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")
    
    cursor.close()
    connection.commit()  # Commit any changes made
    connection.close()
    print("\nGoodbye!")
    
    case_data = cursor.fetchall()
    if not case_data:
        print(f"No case found with ID {case_id}")
        return
    
    # Print case information
    case = case_data[0]
    print(f"\nCase ID: {case[0]}")
    print(f"Case Number: {case[1]}")
    print(f"Title: {case[2]}")
    print(f"Court: {case[3]}")
    print(f"Status: {case[4]}")
    print("\nDocuments:")
    
    # Print documents
    for row in case_data:
        if row[5]:  # If document_name exists
            print(f"- {row[5]} ({row[6]})")
            print(f"  Path: {row[7]}")

def search_cases(keyword, cursor):
    """Search cases by keyword"""
    cursor.execute("""
        SELECT c.id, c.case_number, c.title, c.court, c.status, c.case_category, c.spouse_names, c.children_info
        FROM cases c
        WHERE (c.title LIKE %s OR c.case_number LIKE %s)
        AND c.case_category IN ('divorce', 'child_custody', 'maintenance', 'adoption', 'domestic_violence')
        ORDER BY c.created_at DESC
        LIMIT 10
    """, (f"%{keyword}%", f"%{keyword}%"))
    
    results = cursor.fetchall()
    if not results:
        print(f"No family law cases found matching '{keyword}'")
        return
    
    print(f"\nFound {len(results)} family law cases matching '{keyword}':")
    for case in results:
        print(f"\nCase ID: {case[0]}")
        print(f"Case Number: {case[1]}")
        print(f"Title: {case[2]}")
        print(f"Court: {case[3]}")
        print(f"Status: {case[4]}")
        print(f"Category: {case[5]}")
        if case[6]:  # spouse_names
            print(f"Spouses: {case[6]}")
        if case[7]:  # children_info
            print(f"Children: {case[7]}")
        print("\nDocuments:")
        cursor.execute("""
            SELECT cd.document_name, cd.document_type, cd.file_path
            FROM case_documents cd
            WHERE cd.case_id = %s
        """, (case[0],))
        documents = cursor.fetchall()
        for doc in documents:
            print(f"- {doc[0]} ({doc[1]})")
            print(f"  Path: {doc[2]}")
    
    results = cursor.fetchall()
    if not results:
        print(f"No cases found matching '{keyword}'")
        return
    
    print(f"\nFound {len(results)} cases matching '{keyword}':")
    for case in results:
        print(f"\nCase ID: {case[0]}")
        print(f"Case Number: {case[1]}")
        print(f"Title: {case[2]}")
        print(f"Court: {case[3]}")
        print(f"Status: {case[4]}")

def main():
    connection = connect_db()
    if not connection:
        return
    
    cursor = connection.cursor()
    
    # Automatically search for divorce cases
    print("\nSearching for divorce cases...")
    search_cases("divorce", cursor)
    
    # Show menu after initial search
    while True:
        print("\nLegal Aid Case Viewer")
        print("1. Search cases by keyword")
        print("2. View case details by ID")
        print("3. Exit")
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '1':
            keyword = input("Enter search keyword: ")
            search_cases(keyword, cursor)
        elif choice == '2':
            case_id = input("Enter case ID: ")
            try:
                display_case_details(int(case_id), cursor)
            except ValueError:
                print("Please enter a valid number for case ID")
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")
    
    cursor.close()
    connection.close()
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
