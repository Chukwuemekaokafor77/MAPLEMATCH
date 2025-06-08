# Canadian Legal Aid Case Management System

A comprehensive case management system designed specifically for Canadian legal aid organizations. This system provides advanced features for managing legal cases, including metadata extraction, case tracking, verification, and reporting.

## Features

### Case Management
- Automated metadata extraction from legal documents
- Support for 20+ Canadian legal practice areas
- Case tracking with verification workflow
- Manual updates with audit trail
- Integration with Canadian legal databases

### Practice Areas Supported
- Family Law
- Criminal Law
- Immigration Law
- Aboriginal Law
- Employment Law
- Constitutional Law
- Environmental Law
- Intellectual Property
- Tax Law
- Bankruptcy & Insolvency
- Corporate & Commercial
- Construction Law
- Labour Relations
- Class Actions
- Indigenous Rights
- Public Interest
- Cyber Law
- Health Law

### Key Features

#### Metadata Extraction
- Extracts case details from PDF documents
- Detects Canadian-specific legal terms and patterns
- Identifies practice areas and case categories
- Extracts property details and financial information
- Tracks case duration and outcomes

#### Verification System
- Manual verification workflow
- Audit trail for all updates
- Verification history tracking
- User-based verification system

#### Reporting
- Comprehensive case statistics
- Province-based reporting
- Practice area analytics
- Case duration analysis
- Legal costs tracking

#### Integration
- CanLII database integration
- Support for bilingual proceedings
- Indigenous case tracking
- Language rights detection

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- Git
- pip (Python package manager)

### 2. Database Setup
1. Create a new MySQL database:
```sql
CREATE DATABASE legal_aid_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Create a user with proper permissions:
```sql
CREATE USER 'legal_aid_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON legal_aid_db.* TO 'legal_aid_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Application Setup
1. Clone the repository:
```bash
git clone https://github.com/anujbhsharma/themis-core-ai.git
```

2. Navigate to the project directory:
```bash
cd themis-core-ai
```

3. Create a virtual environment:
```bash
python -m venv venv
```

4. Activate the virtual environment:
```bash
# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

5. Install dependencies:
```bash
pip install -r requirements.txt
```

6. Configure environment:
Create a `.env` file in the project root with the following variables:
```
DB_HOST=localhost
DB_USER=legal_aid_user
DB_PASSWORD=your_password
DB_NAME=legal_aid_db
```

7. Initialize the database schema:
```bash
python database_schema.py
```

### 4. Running the Application
1. Organizing cases:
```bash
python organize_cases.py path/to/case/documents
```

2. Querying cases:
```bash
python query_cases.py
```

### 5. Testing
To run tests:
```bash
python -m pytest tests/
```

### 6. Configuration Options
Environment variables that can be configured:
```
# Database Configuration
DB_HOST=localhost
DB_USER=legal_aid_user
DB_PASSWORD=your_password
DB_NAME=legal_aid_db

# Application Settings
LOG_LEVEL=INFO
MAX_CASES_PER_BATCH=100
CACHE_ENABLED=true
CACHE_TIMEOUT=3600
```

### 7. Troubleshooting
#### Common Issues
1. Database Connection Error:
   - Verify database credentials in .env file
   - Ensure MySQL server is running
   - Check firewall settings

2. Missing Dependencies:
   - Run `pip install -r requirements.txt` again
   - Verify Python version compatibility

3. Permission Errors:
   - Check MySQL user permissions
   - Verify file permissions
   - Run commands with appropriate privileges

#### Error Messages
- "Database connection failed": Check database credentials
- "Module not found": Run pip install again
- "Permission denied": Check file permissions

### 8. Security Considerations
1. Never commit the .env file to version control
2. Use strong passwords for database access
3. Regularly update dependencies
4. Enable SSL/TLS for database connections
5. Implement proper access controls

### 9. Performance Optimization
1. Indexes have been added for:
   - Province
   - Practice Area
   - Status
   - Priority
   - Next Action Date

2. For large datasets:
   - Increase batch size in configuration
   - Optimize database indexes
   - Consider partitioning large tables

### 10. Backup and Recovery
1. Regular database backups:
```bash
mysqldump -u legal_aid_user -p legal_aid_db > backup.sql
```

2. Restore from backup:
```bash
mysql -u legal_aid_user -p legal_aid_db < backup.sql
```

## Usage

### Organizing Cases
```bash
python organize_cases.py path/to/case/documents
```

### Querying Cases
```bash
python query_cases.py
```

### Generating Reports
```bash
python query_cases.py --stats
```

## Database Schema

The system uses a MySQL database with the following main tables:
- `cases`: Stores case information and metadata
- `case_documents`: Stores document information
- `case_participants`: Stores participant information
- `verification_history`: Tracks verification actions
- `update_history`: Tracks manual updates
- `case_statistics`: Stores aggregated statistics
- `canlii_integration`: Stores CanLII integration data
- `legal_aid_statistics`: Stores legal aid metrics

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- CanLII for providing legal information
- Python community for excellent libraries
- All contributors who have helped improve this project
