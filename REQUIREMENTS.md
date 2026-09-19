# REQUIREMENTS FOR DATA EXTRACTION TOOL

## 1\. Background

You have been engaged to support a regional public health organisation developing an approach for consolidating expenditure information from national financial systems for health expenditure analysis.

Countries use different financial management systems, charts of accounts, coding structures, terminology and data formats. The organisation needs an approach that can ingest expenditure data from different sources, harmonise it into a common structure, and support classification against a standard analytical framework.

The longer-term objective is to develop an approach that can be adapted to multiple countries. For this assessment, however, you are expected to develop only a **small working prototype** using the sample data supplied.

## 2\. Data Provided

You will receive synthetic expenditure data representing three fictitious countries.

The datasets deliberately differ in structure and format and may contain data-quality issues representative of real financial datasets.

The package will contain:

Country A expenditure extract \- CSV

Country B expenditure extract \- Excel

Country C expenditure extract \- JSON

Simplified country reference information

Simplified chart-of-account/code reference information

Simplified health expenditure classification reference

Simplified SRHR classification reference

The datasets are synthetic and have been created solely for this technical assessment.

You should review and profile the supplied data before designing your solution. Data quality and uncertainty should be treated as part of the problem rather than assumed away.

## 3\. Assignment

Develop a small prototype demonstrating how the organisation could:

ingest expenditure data supplied by different countries;

harmonise the datasets into a common structure;

store and manage the resulting information;

support mapping or classification of expenditure records against the supplied analytical classifications; and

allow an analyst to review the resulting information.

Your solution should be designed with the assumption that additional countries, data structures and classification requirements may eventually need to be incorporated.

You are free to choose the programming languages, database, frameworks, libraries and architecture you consider appropriate.

### Minimum expected functionality

Your prototype should demonstrate:

ingestion of the supplied datasets;

transformation into a common/harmonised structure;

storage using an appropriate data model;

some form of expenditure tagging, mapping or classification;

identification or handling of records that cannot be mapped/classified reliably;

a simple analyst-facing interface for reviewing the processed information; and

the ability to trace processed information back to its original source.

The interface does not need to be visually elaborate. A simple functional interface is sufficient.

### Technical design

Provide a simple architecture or data-flow diagram showing the major components of your solution.

## 4\. Classification Approach

There is deliberately no prescribed technical approach for expenditure classification.

You may use any approach you consider appropriate, including:

reference mappings;

configurable business rules;

keyword or text-based approaches;

statistical or machine-learning methods;

AI-assisted classification;

combinations of approaches; or

another method you consider suitable.

You are **not expected to develop a sophisticated predictive or AI model within the allotted time**.

I will be more interested in:

why you selected your approach;

how it works;

what assumptions it makes;

how uncertain or ambiguous classifications are handled;

how classifications could be validated; and

how the approach could evolve.

## 5\. Scope

You are not expected to develop:

a production-ready application;

a complete IFMIS integration;

enterprise authentication;

production infrastructure;

a sophisticated machine-learning platform;

a comprehensive SHA implementation;

exhaustive automated testing;

a polished enterprise user interface; or

every feature that a future operational system would require.

Where you believe additional capabilities would be important in a production system, explain them rather than attempting to implement everything.

Good prioritisation is part of the assessment.