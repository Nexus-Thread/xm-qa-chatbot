Monthly QA Summary Generator – Requirements (Developer Spec)

0. Purpose

Build an application that generates the monthly QA summary report.

The report consists of (at minimum):
	1.	Quality Metrics (per stream + per project + portfolio aggregate)
	2.	Test Coverage Manual and Automation (per stream + per project + portfolio total)

1. Report Structure (Output)

1.1 Output formats
	•	SHOULD generate HTML/Web view for drill-down.

1.2 Sections

Section A: Quality Metrics
A single table with:
	•	One portfolio aggregate row (“All Streams, average”)
	•	Multiple rows grouped by Business Stream, each with one or more Projects

Columns (exactly these data concepts):
	1.	Business Stream
	2.	Project Name
	3.	Supported releases during the month (number)
	4.	Bugs found by QAs during the month (P1–P2, P3–P4) - these will be linked to JIRA filters - we will use mocked data for initial delivery to simulate JIRA
	5.	Production incidents during the month (P1–P2, P3–P4) - these will be linked to JIRA filters - we will use mocked data for initial delivery to simulate JIRA
	6.	CAPAs of production incidents during the month (link/filter)
	7.	Defect Leakage Rate %
	8.	Time for full regression in hours

Section B: Test Coverage Manual and Automation
Includes:
	•	A headline: Overall number of test cases across all projects:
	•	A table grouped by stream/project

Columns:
	1.	Business stream
	2.	Project Name
	3.	Percentage of automation
	4.	Manual TCs
	5.	Created Manual TCs (Last Month)
	6.	Updated Manual TCs (Last Month)
	7.	Automated TCs
	8.	Created Automated TCs (Last Month)
	9.	Updated Automated TCs (Last Month)

2. Data Model (Domain)

2.1 Entities

ReportingPeriod
	•	year: int
	•	month: int
	•	start_datetime: datetime
	•	end_datetime: datetime (exclusive)
	•	timezone: str (IANA)

BusinessStream
	•	id: str
	•	name: str
	•	order: int (stable ordering)

Project
	•	id: str
	•	name: str
	•	business_stream_id: str
	•	aliases: list[str] (optional)
	•	is_active: bool

QualityMetrics (per Project, per Period)
	•	supported_releases_count: int
	•	bugs_found: { p1_p2: int, p3_p4: int }
	•	production_incidents: { p1_p2: int, p3_p4: int }
	•	capa: { count: int | null, status: 'N/A' | 'OK' | 'MISSING_SOURCE' }
	•	defect_leakage: { numerator: int, denominator: int, rate_percent: float }
	•	regression_time: RegressionTimeBlock (structured + renderable)

RegressionTimeBlock
	•	entries: list[RegressionTimeEntry]
	•	free_text_override: str | null (optional)

RegressionTimeEntry
	•	category: enum('manual','automation','api','ui','e2e','integration','component','other')
	•	suite_name: str
	•	platform: enum('web','pwa_web','pwa_ios','pwa_android','ios','android','backend','mixed','other')
	•	duration_minutes: float (canonical)
	•	threads: int | null
	•	context_count: int | null (e.g., values shown in parentheses)
	•	notes: str | null

TestCoverageMetrics (per Project, per Period)
	•	manual_total: int
	•	automated_total: int
	•	manual_created_last_month: int
	•	manual_updated_last_month: int
	•	automated_created_last_month: int
	•	automated_updated_last_month: int
	•	percentage_automation: float (computed)

Portfolio Aggregates
	•	all_streams_supported_releases_total: int
	•	all_streams_supported_releases_avg: float
	•	all_streams_bugs_avg: { p1_p2: float, p3_p4: float }
	•	all_streams_incidents_avg: { p1_p2: float, p3_p4: float }
	•	all_streams_defect_leakage: { numerator: int, denominator: int, rate_percent: float }


3. Data Sources & Connectors

3.1 Jira (Defects, Incidents, CAPAs)

The application MUST support per-project configuration of:
	•	Jira project keys and/or components
	•	Issue type(s) included (e.g., Bug/Defect, Incident)
	•	Time window definition for “during the month” (created vs resolved vs transitioned)
	•	Priority mapping for buckets:
	•	P1–P2
	•	P3–P4
	•	Logic for “found by QAs” (configurable):
	•	reporter in QA group OR
	•	label/component OR
	•	custom field OR
	•	environment field

Output must include:
	•	Counts per bucket (P1–P2, P3–P4)

Initial delivery: use mocked Jira data to simulate query results while keeping the Jira source model intact.

Jira filters MUST be auto-generated from static templates, with only the reporting time window substituted.

3.2 Defect Leakage (UAT/Prod vs QA all-env)

The system MUST compute defect leakage using two explicitly defined sets:
	•	Numerator: defects found in UAT or Production
	•	Denominator: total defects found by QAs on all environments

Both numerator and denominator MUST:
	•	Have explicit scope (projects/components)
	•	Have the same reporting period

3.3 Supported Releases

Must be pluggable per project. Allowed sources:
	•	Jira releases/fixVersions
	•	Release calendar / deployment system
	•	Manual override

3.4 Manual test coverage inputs via chatbot

The system MUST collect test coverage metrics via chatbot submissions from team members for each project:
	•	total manual test cases
	•	total automated test cases
	•	created/updated counts for last month
	•	portfolio total “Overall number of test cases across all projects” (provided directly, not derived)

Chatbot submissions MAY overwrite previous values for the same project and reporting period.

Initial delivery: the chatbot is the only source of test coverage data (no TMS integration).

4. Calculations & Rules

4.1 Priority bucket mapping

MUST be configurable:
	•	map raw priorities into two buckets: P1–P2 and P3–P4

4.2 Defect leakage rate

For each project:
	•	rate_percent = (numerator / denominator) * 100
	•	Render in report cell as:
	•	(numerator/denominator) * 100 = <rate>%

Edge cases:
	•	If denominator == 0, MUST render one consistent rule:
	•	default: (0/0) * 100 = 0%
	•	alternative (allowed if chosen globally): N/A

4.3 Percentage of automation

MUST compute:
	•	percentage_automation = automated_total / (manual_total + automated_total) * 100

Edge cases:
	•	if both totals are 0 → render 0% or N/A (choose globally)

4.4 Portfolio aggregates (“All Streams, average”)

MUST compute:
	•	Supported releases:
	•	total across included projects
	•	average across included projects
	•	Bugs found by QAs:
	•	average P1–P2
	•	average P3–P4
	•	Production incidents:
	•	average P1–P2
	•	average P3–P4
	•	Defect leakage:
	•	portfolio numerator/denominator and computed percent

Inclusion rules MUST be defined and enforced:
	•	which projects are included (active only by default)
	•	whether projects with no activity are included in averages

Rounding rules MUST be defined (e.g., 2 decimals for averages, 2 decimals for leakage %).

5. Rendering Rules

5.1 Quality Metrics table
	•	Bugs and incidents columns MUST render as two-line blocks:
	•	P1–P2  <value>
	•	P3–P4  <value>
	•	CAPA column MUST render:
	•	N/A OR
	•	a link to a Jira filter/query OR
	•	a placeholder “/” only if explicitly configured
	•	Regression time MUST support multi-line structured text.

5.2 Regression time formatting

The system MUST:
	•	store durations canonically in minutes
	•	render using human-friendly units:
	•	seconds (< 1 min)
	•	minutes
	•	hours
	•	preserve annotations:
	•	“(N)” context counts
	•	“X threads run”
	•	“In progress”
	•	“per brand”

5.3 Test Coverage table
	•	MUST render each row with computed automation % to 2 decimals.
	•	MUST render the portfolio total number as a headline.

6. Data Quality, Validation, and Auditability

6.1 Traceability (POC level)

No traceability or audit requirements beyond ensuring data is present for report generation.

6.2 Validation rules

The system MUST detect and report:
	•	Missing required data fields for any metric
	•	Invalid or unmapped priority values
	•	Period window inconsistencies across sources

6.3 Report completeness status

Each generated report MUST produce a completeness summary:
	•	COMPLETE
	•	PARTIAL with a list of missing cells/sources
	•	FAILED (no report generated)

6.4 Reproducibility

Every report MUST embed metadata:
	•	reporting period
	•	generation timestamp

7. Configuration Requirements

7.1 Config model

MUST support a versioned configuration file (YAML/JSON) defining:
	•	Streams and projects (ordering, active flags)
	•	Source definitions per project for each metric
	•	Priority mapping rules
	•	Regression suite definitions (optional, recommended)

7.2 Manual overrides

Chatbot submissions are treated as the default input mechanism for test coverage metrics and can overwrite prior values for the same project and reporting period.


8. Non-Functional Requirements
	•	Reliability: generation must succeed for all projects even if some sources are missing (report becomes PARTIAL).
	•	Security: credentials stored securely; least-privileged access to Jira/TMS.
	•	Performance: full report generation time target defined by engineering (e.g., < 5 minutes for N projects).
	•	Observability: structured logs per metric fetch + error reporting.


9. Acceptance Criteria
	1.	Given a configured month, the app generates the 3-section report (HTML required; PDF optional).
	2.	For each project row in Quality Metrics, the app outputs:
	•	supported releases count
	•	bugs found (P1–P2, P3–P4) + links
	•	production incidents (P1–P2, P3–P4) + links
	•	CAPA link or N/A
	•	defect leakage shown as (n/d)*100 = x% + links for n and d
	•	regression time rendered as structured multi-line text
	3.	For Test Coverage, the app outputs:
	•	portfolio total number of test cases (provided via chatbot submission)
	•	per project manual/automated totals and monthly deltas (provided via chatbot submission)
	•	computed % automation with consistent formula
	4.	The report includes “All Streams, average” aggregate row with totals and averages.
	5.	The report includes completeness status metadata.

Streams and projects

Affiliates
	•	Affiliate

Backbone Systems / Bridge
	•	Bridge

Backbone Systems / Platform Systems
	•	JThales
	•	jManager Server and Portal
	•	Symbols Management Service
	•	Local Depositors Service
	•	Fees Management Service
	•	Admin Tools Service
	•	Funding Service (Not Live)
	•	JTools
	•	Data Access Layer (DAL)

Backbone Systems / Trading Platform
	•	MetaProxy
	•	Plugins
	•	TSDA
	•	HORN

Client Engagement
	•	Social Trading – Copy Trading
	•	Social Trading – Competitions
	•	Promotions Tool
	•	Client Loyalty – Loyalty
	•	Client Loyalty – Bonus
	•	Market Intelligence
	•	Artificial Intelligence (AI)
	•	Client Communication
	•	Education

Client Journey
	•	Client Support
	•	Client Authentication
	•	Client Trading
	•	Onboarding & Account Management
	•	Realtime Communications

Funding
	•	Payments
	•	Withdrawals

Internal Systems
	•	KYC
	•	SCC
	•	CRM
	•	Digital Marketing

Mobile
	•	Mobile – XM Trading Point

WWW / Client Face Application (CFA)
	•	Angular Core Web
	•	Angular WWW
