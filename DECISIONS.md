# Decisions

The calls behind how this repository is built. Each one says what was decided, why, and when. Where no reason was written down at the time, it says what the choice does instead of inventing one after the fact.

## How the repository is organised

**BI has its own repository, apart from reporting.** *25 October 2026.* Power BI and Tableau started in reporting-and-bi. Reporting and BI tools should be shown separately, so they moved here with their history, and the reporting work stayed in [reporting](https://github.com/nurah-kamal/reporting).

**One folder per project, each with its own workflow.** *25 October 2026.* `.github/workflows/<project>.yml` runs only when that project's folder changes. `secrets.yml` scans the whole history of the whole repository.

**Projects came in with their history.** *25 October 2026.* Each project was moved in from its earlier repository with its commits kept.

## Power BI

**Saved as `.pbip`, not `.pbix`.** *25 October 2026.* A `.pbix` is a single binary file: Git can store it but can't show what changed. As a `.pbip`, the semantic model is TMDL and the report is one JSON file per visual, so a change to a measure or a visual shows up line by line in a diff and can be reviewed like code.

**The model is checked against an answer worked out somewhere else.** *25 October 2026.* [Power BI Turnaround](power-bi-turnaround/) is built on the same seeded synthetic data as [SA Turnaround](https://github.com/nurah-kamal/reporting/tree/main/sa-turnaround), so its figures can be checked against that project's SQL. `data/expected.json` holds the figures worked out in plain code, the measures were checked against it by DAX query, and a test checks that `expected.json` agrees with the published SQL results. Two independent routes to the same numbers is the check; one tool agreeing with itself isn't.

**The date table comes from code, not a typed list of holidays.** *25 October 2026.* It's written by the same tested working-day library as the SQL project, so the two can't drift apart on a public holiday.

## Data

**Synthetic or public data only, and never a connection to a work model.** *25 October 2026.* Projects that come from my work are rebuilt from scratch. Nothing here was built against, or connected to, work data.

**No people in any data.** *25 October 2026.* No names, real or invented, no contact details and no free text about a person.

## Writing

**READMEs describe only what is in the repository.** *25 October 2026.* Every figure in a README comes from the data or a run in the folder.

**Commits are one short line.** *Since 30 September 2026.* Explanations go in the READMEs and docs, not in commit messages.
