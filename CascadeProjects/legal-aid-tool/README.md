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

## Installation

1. Clone the repository:
```bash
git clone https://github.com/anujbhsharma/themis-core-ai.git
cd themis-core-ai
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file with the following variables:
```
DB_HOST=localhost
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=legal_aid_db
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
