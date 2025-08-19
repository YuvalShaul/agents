# RAG data
These directories contain structured (csv files) and unstructured (pdf files - natural language) derived from an imaginary small health provider called **medcare**.  
following is a description of the data

### Unstructured data (pdf files)

**1. Medical Policies & Procedures Manual (PDF-style)**

HIPAA compliance, patient care protocols
Medical records management, infection control
Prescription management, lab procedures
~4,200 words - Realistic healthcare policy content

**2. Employee Handbook (PDF-style)**

Employment policies, compensation & benefits
Work schedules, professional development
Workplace conduct, health & safety
~3,800 words - Complete HR documentation

**3. Financial Procedures & Billing Manual (PDF-style)**

Patient billing, insurance processing
Expense management, revenue cycle
Financial reporting, accounts payable
~3,600 words - Detailed financial operations

**4. Emergency Response Plan (PDF-style)**

Medical emergencies, fire response
Security procedures, natural disasters
Utility failures, communication protocols
~3,200 words - Comprehensive safety procedures


Document features:
- Varied Document Types - Medical, HR, Financial, Safety domains
- Appropriate Length - 3,000-4,000 words each (manageable but substantial)
- Unstructured Text - Natural language that RAG systems need to parse
- Cross-References - Documents reference each other (realistic complexity)

### Unstructured data

#### CSV files explained
**1. Monthly Revenue Data (monthly_revenue_2024.csv)**  
This tracks how much money the clinic makes each month.  
Gross Charges = what they bill patients  
Contractual Adjustments = discounts they must give to insurance companies  
Collections = actual cash received  
DSO (Days Sales Outstanding) = how long it takes to get paid (lower is better).  

2. Operating Expenses (operating_expenses_2024.csv)  
This breaks down where the clinic spends money by category and quarter. Personnel Costs = salaries and benefits (usually 60-70% of healthcare expenses), Facility Costs = rent, utilities, insurance. Variance % shows if they spent more or less than budgeted.
3. A/R Aging Analysis (ar_aging_analysis.csv)  
A/R = Accounts Receivable = money owed to the clinic for services already provided. The aging columns (0-30 days, 31-60 days, etc.) show how long bills have been unpaid. Older bills are harder to collect, so clinics want most A/R in the "Current" column.
4. Provider Productivity (provider_productivity_2024.csv)  
This measures how productive each doctor/nurse practitioner is. RVUs (Relative Value Units) = a standard way to measure medical work complexity - a simple office visit might be 1 RVU, surgery might be 20 RVUs. Revenue per RVU shows how efficiently they generate income.
5. Payer Mix Analysis (payer_mix_analysis.csv)  
This shows what percentage of patients have different insurance types. Commercial insurance pays the best rates, Medicare/Medicaid pay lower government rates, Self-Pay patients often can't pay at all. Reimbursement Rate = what insurance actually pays vs. what the clinic bills.