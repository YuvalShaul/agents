# RAG data
These directories contain structured (csv files) and unstructured (pdf files - natural language) derived from an imaginary small health provider called **medcare**.
These are mock files to demonstrate unstructured data usage in a vector db (Chroma). Following is a description of the data.

### Unstructured data (pdf files)

**1. 1-Medcare_Membership_Eligibility.pdf**
Summary: Membership & Eligibility Guide Enrollment Architecture This section details the specific operational guidelines for Enrollment Architecture within the...

**2. 2-Medcare_Clinical_Services.pdf**
Summary: Clinical Services & Specialties Specialized Diagnostic Modalities This section details the specific operational guidelines for Specialized Diagnostic...

**3. 3-Medcare_Privacy_Rights.pdf**
Summary: Patient Privacy & Legal Rights Data Encryption Standards This section details the specific operational guidelines for Data Encryption Standards within...

**4. 4-Medcare_Financial_Policy.pdf**
Summary: Financial Policy & Billing Payment Collection Lifecycle This section details the specific operational guidelines for Payment Collection Lifecycle with...

**5. 5-Medcare_Facilities_Network.pdf**
Summary: Facility Network & Locations Medcare Primary Care Locations This section details the specific operational guidelines for Medcare Primary Care Location...

**6. 6-Medcare_Admin_Procedures.pdf**
Summary: Administrative Workflows Patient Intake Workflows This section details the specific operational guidelines for Patient Intake Workflows within the Med...

**7. 7-Medcare_Legal_Compliance.pdf**
Summary: Legal Liability & Standards Malpractice Indemnification This section details the specific operational guidelines for Malpractice Indemnification withi...

**8. 8-Medcare_Urgent_Care.pdf**
Summary: Emergency & Urgent Care Protocols Emergency Department Triage Levels This section details the specific operational guidelines for Emergency Department...

**9. 9-Medcare_Pharmacy_Policy.pdf**
Summary: Pharmacy & Medication Benefits Drug Formulary Management This section details the specific operational guidelines for Drug Formulary Management within...

**10. 10-Medcare_Telehealth_Terms.pdf**
Summary: Telehealth & Digital Operations Virtual Consultation Platforms This section details the specific operational guidelines for Virtual Consultation Platf...

Document features:
- Varied Document Types - Medical, HR, Financial, Safety domains
- Unstructured Text - Natural language that RAG systems need to parse

### Structured data (csv files) in "data" directory

#### CSV files explained
1. **Facility Locations (medcare_facility_locations.csv)**  
This file logs the different facilities operated by or affiliated with Medcare.  
**Type** = identifies whether it is the main hospital, urgent care, wellness center, partner hospital, or lab.  

2. **Membership Tiers (medcare_membership_tiers.csv)**  
This outlines the different membership plans available to patients.  
**Monthly Premium** & **Annual Deductible** = outline standard costs for the patient.  
**In-Network Coverage %**, **Pharmacy Benefit**, and **Telehealth Eligible** = dictate the specific benefits for each tier.  

3. **Provider Directory (medcare_provider_directory.csv)**  
This lists the doctors and healthcare providers associated with Medcare.  
**Specialty** = the medical field of the provider (e.g., Family Medicine, Cardiology).  
**Affiliation** = whether they are Medcare Internal or an Affiliate Partner.  
**Accepting New Patients** & **Language Fluency** = provide patient accessibility details.  

4. **Service Pricing (medcare_service_pricing.csv)**  
This details the costs associated with common medical services and procedures.  
**CPT Code** = standard billing medical code.  
**Base Price** = full standard cost of the service.  
**Gold Copay** = patient cost if they are on the "Gold Premium" membership tier.