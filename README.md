# Business Intelligence

**BI models and dashboards: data modelled properly, measures you can trust, and pages built for exploring.** Each project lives in its own folder with its own README.

| Project | What it is | Built with |
| --- | --- | --- |
| [Power BI Turnaround](power-bi-turnaround/) | The SA Turnaround analysis rebuilt as a Power BI model: a star schema, a date table that knows every South African public holiday, 23 DAX measures and four report pages. Every figure matches the SQL version, and tests check that. | Power BI, DAX |
| [Tableau](tableau/) | Three Tableau dashboards: South African HR on synthetic data, data science salaries, and sales performance. | Tableau |

The report itself, with the working-day library and the SQL behind it, is in [reporting](https://github.com/nurah-kamal/reporting/tree/main/sa-turnaround).

## How this repo is organised

- **One folder per project,** each one standing on its own.
- **Power BI projects are saved as `.pbip`,** so the model and report are text files that show up line by line in a diff. Open the `.pbip` in Power BI Desktop (free).
- **Each project has its own checks** in `.github/workflows/<project>.yml`, running only when that folder changes. `secrets.yml` scans the whole history.
- **History came with the projects.** Each one was moved in from its earlier repo with its commits kept.

## Data

Everything here runs on invented or public data. No work data is in this repository.

## Licence

MIT.
