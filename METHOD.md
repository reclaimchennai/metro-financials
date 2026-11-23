# Method

## What is read

For every operator, the **standalone audited Statement of Profit and Loss** in each annual report
(older reports: Profit and Loss Account or Income and Expenditure Account), both columns: the year
of the report and the year before. One report thus gives two years. The year's own report is used
first; the previous-year column of the next report fills a year whose report is missing. Where a
later report restates a year, both figures are kept (`restated` in `data/finance.json`).

From each statement: revenue from operations, its split into fare and non-fare revenue (from the
note to revenue from operations), other income, total income, employee cost, finance cost,
depreciation, other expenses, total expenses, exceptional items, profit before tax, tax and
profit after tax. From the directors' report, where stated: riders in the year, average daily
riders and route km at year end.

Annual returns (Form MGT-7) give only turnover; it is recorded with a note and nothing else.

## How

Text PDFs were read with `pdftotext -layout`; scanned reports by OCR (`tesseract`) on the
accounts pages, each value checked against the rendered page image and the statement's own
totals. Every value in `data/verified/<OP>.json` carries the PDF file, the page number and the
line as printed (`quote`), so it can be found and checked.

Checks run on every year: total income = revenue from operations + other income; profit before
tax = total income − total expenses (± exceptional items); profit after tax = profit before tax −
tax. Differences (printed rounding, prior-period lines) are noted in each year's `checks`.

## Units and signs

All money in ₹ crore (1 crore = 100 lakh = 10 million). Reports in ₹ lakh, thousand or rupees are
converted. Losses are negative. Tax is a charge when positive. Financial years run April to March
("2024-25" is the year to 31 March 2025).

## Derived values

Arithmetic on audited lines only:

- **Operating cost** = total expenses − depreciation − finance cost: what running the railway and
  the company cost in the year.
- **Operating ratio** = operating cost ÷ revenue from operations.
- **Fare-box recovery** = fare revenue ÷ operating cost.
- **Per trip** figures divide by riders in the year, or by the stated daily average × 365 where
  only that is given (marked).

## What is not done

No figure is estimated, interpolated or taken from news reports. A value the reports do not give
is left empty. Figures from the former dataset in this project's predecessor (typed into a script,
many invented) are not used anywhere.
