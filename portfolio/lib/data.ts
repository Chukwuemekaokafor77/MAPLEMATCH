export const NAV_LINKS = ['About', 'Projects', 'Experience', 'Publications', 'Contact'];

export type ProjectCategory = 'all' | 'saas' | 'ml' | 'data';

export interface Project {
  id: number;
  title: string;
  description: string;
  tags: string[];
  category: ProjectCategory;
  github: string | null;
  live: string | null;
  highlights: string[];
}

export const PROJECTS: Project[] = [
  {
    id: 1,
    title: 'ElderCare Companion',
    description:
      'Production-ready multi-tenant SaaS platform for Canadian personal support agencies — PIPEDA-compliant with GPS-verified task completion, real-time WebSocket messaging, digital MAR, and Stripe billing.',
    tags: ['FastAPI', 'React Native', 'PostgreSQL', 'Redis', 'Python', 'Expo'],
    category: 'saas',
    github: 'https://github.com/Chukwuemekaokafor77/elderly-care',
    live: 'https://elderly-care-zeta.vercel.app/login',
    highlights: [
      '537 backend + 379 frontend tests',
      'PIPEDA compliant (PHI encryption)',
      '5-role RBAC',
      'GPS shift verification',
      'Payroll module + CSV export',
      '6 CI/CD workflows',
    ],
  },
  {
    id: 2,
    title: 'MapleMatch',
    description:
      'AI-powered affordable housing matching platform for Canada — rules + semantic + ML scoring engine matching applicants to RGI listings across all 13 provinces with wait-time prediction.',
    tags: ['Next.js', 'FastAPI', 'PostgreSQL', 'PostGIS', 'Redis', 'Clerk'],
    category: 'saas',
    github: null,
    live: 'https://maplematch-app.vercel.app',
    highlights: [
      '74 real listings (all 13 provinces)',
      'AI matching engine',
      'Bilingual EN/FR',
      'WCAG accessible',
      'PostGIS spatial queries',
      '51 frontend tests',
    ],
  },
  {
    id: 3,
    title: 'OrgPulse Analyzer',
    description:
      'Organizational health assessment platform — full CSV-to-insights pipeline: strict validation, 5-domain scoring, 13-case AI engine, role heatmap dashboard, trend tracking, and 25-page PDF report.',
    tags: ['Next.js', 'TypeScript', 'Tailwind', 'jsPDF', 'PapaParse'],
    category: 'data',
    github: null,
    live: 'https://twine-orpin.vercel.app',
    highlights: [
      '13-case AI insight engine',
      '25-page structured PDF',
      'Domain × role heatmap',
      'localStorage trend tracking',
      'Full validation pipeline',
    ],
  },
  {
    id: 4,
    title: 'SCOUT AI — Football Prediction',
    description:
      'Self-hosted football prediction dashboard covering 50 competitions — 7-factor statistical model, over/under xG blend, match-fixing anomaly detection, and real-time bookmaker odds integration.',
    tags: ['Ruby', 'Sinatra', 'JavaScript', 'REST API'],
    category: 'ml',
    github: null,
    live: null,
    highlights: [
      '50 leagues across 4 tiers',
      '7-factor weighted model',
      'Match-fixing risk detection',
      'API quota management',
      '30-min in-memory cache',
    ],
  },
  {
    id: 5,
    title: 'Predictive Sensor Analytics',
    description:
      'End-to-end ML system for high-frequency manufacturing sensor streams — anomaly detection pipeline with Isolation Forest, Autoencoder, and LSTM reconstruction, with AWS SageMaker-ready deployment.',
    tags: ['Python', 'FastAPI', 'PostgreSQL', 'scikit-learn', 'TensorFlow', 'AWS SageMaker', 'Docker'],
    category: 'ml',
    github: 'https://github.com/Chukwuemekaokafor77/predictive-sensor-analytics',
    live: null,
    highlights: [
      '10ms sensor sampling',
      'Butterworth + Kalman filtering',
      'RMS / Kurtosis / Spectral features',
      'SageMaker train + inference',
      'FastAPI /predict endpoint',
    ],
  },
  {
    id: 6,
    title: 'SkinBurnPro',
    description:
      'AI-powered burn severity classification app — deep learning ensemble predicting 1st, 2nd, and 3rd degree burns from images, managed with Azure DevOps CI/CD and distributed via Docker Hub.',
    tags: ['TensorFlow', 'FastAPI', 'Streamlit', 'PostgreSQL', 'Docker', 'Azure DevOps'],
    category: 'ml',
    github: 'https://github.com/Chukwuemekaokafor77/SkinBurnPro',
    live: null,
    highlights: [
      'Deep learning ensemble classifier',
      '3-class burn severity detection',
      'Azure DevOps CI/CD pipelines',
      'Docker Hub distribution',
      'User auth + feedback system',
    ],
  },
  {
    id: 7,
    title: 'ASD Screening Tool',
    description:
      'Machine learning screening tool for early autism spectrum disorder detection in toddlers — 99.7% accuracy on Q-Chat-10 behavioral dataset using logistic regression with full Docker deployment.',
    tags: ['Python', 'Flask', 'scikit-learn', 'Docker', 'Pandas'],
    category: 'ml',
    github: 'https://github.com/Chukwuemekaokafor77/Autism-Spectrum-Disorder-Prediction',
    live: null,
    highlights: [
      '99.7% accuracy',
      '5-fold cross-validation',
      '1,054 records, 18 attributes',
      'Docker containerized',
      'Flask web interface',
    ],
  },
  {
    id: 8,
    title: 'Customer Churn Pipeline',
    description:
      'Production-grade ML pipeline for real-time customer churn prediction — automated weekly model retraining, Prometheus observability, data quality scoring, and FastAPI serving.',
    tags: ['Python', 'FastAPI', 'Prometheus', 'scikit-learn', 'PostgreSQL'],
    category: 'ml',
    github: 'https://github.com/Chukwuemekaokafor77/customer-churn-prediction',
    live: null,
    highlights: [
      'Real-time REST API predictions',
      'Automated weekly retraining',
      'Prometheus metrics dashboard',
      'Data quality monitoring',
      'Scheduled pipeline runs',
    ],
  },
  {
    id: 9,
    title: 'Loan Default Prediction',
    description:
      'Streamlit ML application for loan approval prediction — logistic regression and random forest models with interactive data analysis, correlation visualizations, and Docker deployment.',
    tags: ['Python', 'Streamlit', 'scikit-learn', 'Docker', 'Pandas', 'Seaborn'],
    category: 'ml',
    github: 'https://github.com/Chukwuemekaokafor77/Loan-Default-Prediction-App',
    live: null,
    highlights: [
      'Dual model comparison (LR + RF)',
      'Interactive Streamlit UI',
      'Correlation & missing-value analysis',
      'Docker ready',
    ],
  },
  {
    id: 10,
    title: 'RAG Legal Document Platform',
    description:
      'Retrieval-augmented generation platform for legal document ingestion, semantic search, and AI-assisted summarization — Rails API backend with React frontend and async processing pipelines.',
    tags: ['Ruby on Rails', 'React', 'PostgreSQL', 'FastAPI', 'Docker', 'GitHub Actions'],
    category: 'saas',
    github: 'https://github.com/Chukwuemekaokafor77/legal-form-wizard',
    live: null,
    highlights: [
      'RAG architecture',
      'Semantic document search',
      'AI-assisted summarization',
      'Background job processing',
      'RBAC access control',
    ],
  },
];

export const SKILL_GROUPS = [
  {
    label: 'Languages & Frameworks',
    icon: '⚡',
    skills: [
      'Ruby on Rails',
      'Python',
      'TypeScript',
      'JavaScript',
      'React',
      'React Native',
      'Next.js',
      'FastAPI',
      'Flask',
      'Sinatra',
    ],
  },
  {
    label: 'Backend & Data',
    icon: '🗄️',
    skills: [
      'PostgreSQL',
      'PostGIS',
      'Redis',
      'SQLAlchemy',
      'ActiveRecord',
      'RESTful APIs',
      'WebSockets',
      'Multi-tenant SaaS',
    ],
  },
  {
    label: 'ML & AI',
    icon: '🤖',
    skills: [
      'scikit-learn',
      'TensorFlow',
      'Isolation Forest',
      'LSTM',
      'Logistic Regression',
      'Random Forest',
      'RAG',
      'AWS SageMaker',
    ],
  },
  {
    label: 'Cloud & DevOps',
    icon: '☁️',
    skills: ['AWS', 'Docker', 'GitHub Actions', 'Azure DevOps', 'CI/CD', 'Vercel', 'Render', 'Cloudflare R2'],
  },
  {
    label: 'Engineering Practices',
    icon: '🏗️',
    skills: [
      'TDD',
      'RBAC',
      'PIPEDA Compliance',
      'API Design',
      'System Design',
      'Agile/Scrum',
      'Code Review',
      'Zero-downtime Migrations',
    ],
  },
];

export const EXPERIENCE = [
  {
    company: 'Introhive Services Inc.',
    location: 'Fredericton, NB',
    role: 'Software Engineer',
    period: 'Mar 2025 – Dec 2025',
    current: true,
    highlights: [
      'Architected PostgreSQL solutions with GIN indexing for company deduplication, achieving sub-2ms query performance',
      'Decreased average API latency by 32% through ActiveRecord query optimization and strategic bitmap indexes',
      'Built JSON:API-compliant RESTful APIs with custom ActiveModel validators and comprehensive test coverage',
      'Reduced post-release defects by 25% through automated regression and integration tests following TDD',
      'Executed production-safe Rails migrations ensuring zero-downtime deployments across staging and production',
    ],
  },
  {
    company: 'Themiscore',
    location: 'Fredericton, NB',
    role: 'Software Engineer',
    period: 'Sept 2024 – Mar 2025',
    current: false,
    highlights: [
      'Built Rails-based RESTful APIs supporting document ingestion, semantic search, and contextual retrieval',
      'Reduced FastAPI endpoint latency by 40% through async request handling and database query optimization',
      'Implemented RBAC authentication middleware protecting sensitive legal data across multi-tenant environments',
      'Containerized Rails services with Docker and implemented CI/CD pipelines using GitHub Actions',
    ],
  },
  {
    company: 'Nnamdi Azikiwe University',
    location: 'Nigeria',
    role: 'Software Engineer',
    period: 'Dec 2019 – Dec 2023',
    current: false,
    highlights: [
      'Engineered production Rails applications serving 500+ researchers, faculty, and students across departments',
      'Designed ETL pipelines automating ingestion and validation of hundreds of thousands of research records',
      'Architected PostgreSQL schemas with targeted indexing strategies addressing critical query bottlenecks',
      'Introduced Docker containerization and CI/CD practices to a team with no prior deployment standardization',
    ],
  },
];

export const EDUCATION = [
  {
    degree: 'Post Graduate Diploma',
    field: 'Applied Artificial Intelligence & Machine Learning',
    school: 'Conestoga College',
    year: '2024',
  },
  {
    degree: 'Master of Science',
    field: 'Information Technology',
    school: 'National Open University of Nigeria',
    year: '',
  },
  {
    degree: 'Bachelor of Science',
    field: 'Computer Science',
    school: 'Nnamdi Azikiwe University, Awka',
    year: '',
  },
];

export interface Publication {
  title: string;
  journal: string;
  date: string;
  url: string;
  abstract: string;
  tags: string[];
}

export const PUBLICATIONS: Publication[] = [
  {
    title: 'Agent Based Intelligent System for Enhanced Teamwork Performance',
    journal: 'International Journal on Data Science and Technology',
    date: 'May 2024',
    url: 'https://www.sciencepublishinggroup.com/article/10.11648/j.ijdst.20241002.11',
    abstract: 'Demonstrates an event-based performance approach using an intelligent coaching agent in a supervised learning team training framework — automated performance assessment with weighted scores removes bias from evaluation.',
    tags: ['Agent Systems', 'Supervised Learning', 'ML', 'Performance Evaluation'],
  },
  {
    title: 'Semantic Web Ontology Technology and Its Impact on E-Learning',
    journal: 'American Journal of Embedded Systems and Applications',
    date: 'Nov 2021',
    url: 'https://www.researchgate.net/publication/356185590_Semantic_Web_Ontology_Technology_and_Its_Impact_on_E-Learning',
    abstract: 'Proposes integrating semantic web ontology into e-learning platforms to create adaptive, personalized, and intelligent learning environments that go beyond instructor-centric content delivery.',
    tags: ['Semantic Web', 'Ontology', 'E-Learning', 'AI'],
  },
  {
    title: 'Web Based Lands and Housing Information Tracking System',
    journal: 'ResearchGate',
    date: '2023',
    url: 'https://www.researchgate.net/publication/369453855_Web_Based_Lands_and_Housing_Information_Tracking_System',
    abstract: 'Develops a web-based databank system for storing and retrieving land registry information — enabling remote access to land size, location, ownership, and usage data to support proper town planning.',
    tags: ['Web Systems', 'PHP', 'Database', 'GIS'],
  },
  {
    title: 'Medical Diagnostic Expert System for Malaria and Typhoid Fever',
    journal: 'International Journal of Scientific Research and Development',
    date: '2022',
    url: 'https://scienceijsrd.com/article/medical-diagnostic-expert-system-malaria-and-typhoid-fever',
    abstract: 'Builds a rule-based expert system replicating physician reasoning for differential diagnosis of malaria and typhoid fever — applying facts and inference rules to assist clinical decision-making.',
    tags: ['Expert Systems', 'Healthcare AI', 'Diagnosis', 'Rule-Based Systems'],
  },
];
