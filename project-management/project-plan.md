# Project Plan

## Goal

[What will the team understand, build, test, or demonstrate by the end of the event?]

By the end of the event, the team will have built and demonstrated a working Text-to-SQL + RAG agent that can interpret natural-language clinical questions, retrieve relevant information from real clinical data, generate and execute SQL queries, and return clear answers through a Streamlit chat interface. The team will also test the agent’s ability to produce accurate, relevant, and reliable responses to representative clinical questions.

## Tools

[What tools do you plan to use for this project?]

We are using the MIMIC-IV dataset, as well as ___.

## First Tasks

- [Azure Infrastructure Set Up] [Small task] - [Sri]
- [Basic UI] [Small task] - [Parth]
- [Text to SQL, RAG, and Orchestration layer] [Small task] - [Sri, Sukesh]

## Milestones


- **Day 1:** [Question, data/inputs, stack, roles, and first working step]

- **Day 2:** [Main build, analysis, testing, or comparison]
- **Day 3:** [Stabilized result, documentation, demo, or handoff]

## Definition of Done

When is the project complete? If this is achieved early on, what would the next steps be to increase the scope?

The project is complete when we are able to have a working agent that can process human questions regarding clinical data and return proper statistial analysis and/or visualization for a statistician or clinician to be able to parse and utilize. This agent would have to be in a state where it has minimal hallucinations and properly applies the correct statistical analysis (as checked by a statistician). The next steps to increase the scope would be to include more tables of the MIMIC-IV dataset to broaden the capabilities. Another step could be to incorporate role-specific tailoring of the chatbot to the profession of whoever is querying it, so that they may have the best possible response for them to be able to understand.
 
## Risks and Questions

- [What might block the team?]
- [What assumption needs checking?]
- [Who can help?]
