# PISA 2022 Codebook Quick Outline

Scope: Student (cognitive + background), school (resources/management), optional parent modules, weights and derived indices. Examples from `codebook/PISA2022Codebook.txt`.

## Identification and Sampling
- `CNT`: 3-char country/economy; `CNTRYID`, `CNTSCHID`, `CNTSTUID`: country/school/student IDs; `STRATUM`: sampling stratum; `SUBNATIO`/`SUBNAT`: subnational domain.
- Weights: Student main `W_FSTUWT`, replicate `W_FSTR1`–`W_FSTR80`; school weight `W_FSCHWT`.

## Achievement (Cognitive)
- Plausible values: Math `PV1MATH`–`PV10MATH`, Reading `PV1READ`–`PV10READ`, Science `PV1SCIE`–`PV10SCIE`.
- Optional domains (e.g., Creative Thinking, by participation): `PV1CREA`–`PV10CREA`.
- Test book/assignment: `BOOKID`, domain/stage assignment (e.g., `MS1_TEST`, `RS1_TEST`).

## Student Basics and Demographics
- Grade: `ST001D01T` (international grade).
- Birth: `ST003D02T` (month), `ST003D03T` (year).
- Sex: `ST004D01T`.
- Language & immigration: `ST022Q01TA` (home language), `ST019Q01T` (birth country items), `ST021Q01TA` (age at arrival).
- Grade repetition: `ST127Q01TA`–`ST127Q03TA` (ISCED1/2/3).

## Family Background and SES
- Parental education: `ST005Q01JA` (mother), `ST007Q01JA` (father); derived `MISCED`, `FISCED`, `HISCED`, `PAREDINT`.
- Parental occupation: ISCO 4-digit `OCOD1` (mother), `OCOD2` (father); status indices `BMMJ1`, `BFMJ2`, `HISEI`.
- Household resources/wealth: `HOMEPOS` (WLE), ICT resources `ICTRES`; items `ST250Q01`–`ST250Q05` (own room, computer, ed software, smartphone, internet), durables `ST251Q01`–`ST251Q07`.
- Composite SES: `ESCS`.

## Time and Educational Experience
- Weekly subject time/homework (e.g., `ST062Q01` series).
- Tutoring/out-of-school study frequency (e.g., `ST069` series).

## Attitudes, Motivation, and Affective (student WLE indices)
- Math self-efficacy: `MATHEFF`.
- Sense of belonging: `BELONG`.
- Interest/enjoyment/self-concept: items in `ST2xx`/`ST3xx`.
- Digital self-efficacy: `ICTEFFIC`; online behavior/safety/frequency `IC1xx`/`IC2xx`.
- Emotion/anxiety single items (e.g., `ST292Q02JA`).

## ICT Use and Resources (Student)
- In-school device use frequency: `IC170Q01JA` (desktop/laptop), `IC170Q02JA` (smartphone), etc.
- Online behavior/information literacy: `IC17x`, `IC18x`, `IC2xx`.
- Household devices as above `ST250*`; linkable to school resources.

## School Questionnaire (Resources/Teaching/Environment)
- Type/size: `PRIVATESCH` (sector), `SCHSIZE` (size); strata/region per IDs.
- Resources/facilities: `SC004Q07NA` (networked computers available to teachers), `SC017Q09JA`/`Q10JA` (digital resource lack/quality), `SC190Q08JA` (responsible internet behavior program).
- Teaching and classes: `CLSIZE` (avg class size, derived), `SC052`/`SC053` (classes/grades), time/policy `SC3xx`.
- Climate: discipline/safety, student composition (immigrant/low SES) `SC024*`, `SC048*`.
- Management/governance: funding, decision authority, teacher development `SC012`, `SC018`, `TC020*` (if teacher level present).
- COVID-19 (2022): remote teaching and responses `ST351*` (student), school-side `SC4xx` where present.

## Timing/Behavior Data
- Computer-based testing durations: many variables with `_TT` suffix (e.g., `ST004_TT`).

## Missing and Special Values
- Negative codes for missing/suppressed (e.g., -9/-8/-7/-5); handle per codebook and apply weights before analysis.

Note: Indices such as `MATHEFF`, `BELONG`, `ICTEFFIC` are WLE estimates; achievement uses plausible values (PV). For cross-country inference, use student weights and replicate weights for variance estimation.
