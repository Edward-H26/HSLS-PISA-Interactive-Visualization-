# HSLS:09 (incl. 2017 PETS) Codebook Quick Summary

Scope: Student main sample (Base Year/F1/PETS), parents, school/course records, and follow-up linkages. Fields sourced from `codebook/Codebook_HSLS_17_PETS.txt`.

## Identification and Sampling
- Weights: Main student weights `W1STUDENT`, `W2STUDENT`, `W4STUDENT`; BRR/replicate weights in supplemental files (e.g., `psstudent_brr_ruf.dat`).
- IDs: Student ID (implicit in file), school ID, NCES link `X1NCESID`; school sector/control `X1CONTROL` (public, Catholic/other private).
- Response/sample status: Round-specific response/missing flags `X1SQSTAT`, `X2SQSTAT`, `X4MATCHATMPT`.

## Basic Demographics
- Sex: `X1SEX` (later `X2SEX`), PETS gender identity `X4GENDERID` (includes suppression code -5).
- Birth: `X1STDOB` (YYYYMM; top/bottom coded year), or questionnaire parts `S1BIRTHMON`, `S1BIRTHYR`.
- Immigration background: `X4IMGEN` (generation, using birthplaces of student/parents).
- Race/ethnicity: `X1RACE` (composite), sub-items `X1HISPANIC`, `X1WHITE`, etc.

## Family Background and SES
- Income: `X1FAMINCOME` (bands; missing/suppression per codebook).
- Parental education: `X1PAREDU` (highest among parents/guardians; derived from `X1PAR1EDU`, `X1PAR2EDU`), later `X2PAREDU`.
- Parental occupation: O*NET 2/6-digit `X1PAR1OCC2`, `X1PAR2OCC2` (derived mother/father `X1MOMOCC2`, `X1DADOCC2`), second round `X2PAR1OCC2` etc.; external mapping needed for ISCO/ISEI comparability.
- SES index: `X1SES` (composite of education/occupation/income; includes 5-imputation mean) with imputation flag `X1SES_IM`; urbanicity version `X1SES_U`; later `X2SES`.
- Language (partly suppressed): `X1NATIVELANG`, `X1DUALLANG` (filter suppression -5/-9).

## Achievement and Coursework
- Cognition: Math theta `X1TXMTH` (with multiple imputations `X1TXMTH1-5`), standardized T score `X1TXMTSCOR`; later `X2TXMTH`.
- Courses/credits: Course taking and credits (e.g., `X3CRS_MATH`, `X3GPA_MATH`), AP/mode flags; depends on record files.
- Status: Standardized scores; enrollment/exit/graduation `X2ENROLSTAT`.

## Attitudes, Motivation, and Scales
- Math self-efficacy: `X1MTHEFF` (later `X2MTHEFF`), sourced from items like S1MTESTS.
- Math interest/enjoyment: `X1MTHINT` (later equivalents).
- Science utility: `X1SCIUTI`.
- Belonging/school climate: `X1SCHOOLBEL`.
- Expectations/planning: Selected items/scales (e.g., `S1EXPECT` series, file-dependent).

## ICT Use and Information Behavior
- Online info search: `S1WEBINFO` (uses web to find computer/tech info).
- CS-related coursework: CS credits present in `X3` records as applicable.

## Parent Questionnaire (selected)
- Relationship/support: `X1P1RELATION`, `X1P2RELATION`; homework help/efficacy such as `P1MTHHWEFF`.
- Birthplaces/immigration: `P1USBORN*`, `P2USBORN*` (used to derive `X4IMGEN`).

## School and Environment
- Sector/control: `X1CONTROL` (public, Catholic/other private); later `X2CONTROL`, `X3CONTROL`, `X4CONTROL`.
- Locale: `X1LOCALE` (City/Suburb/Town/Rural); later `X2LOCALE`.
- School-level weights/links: See NCES/CCD/PSS linkage fields.

## Missing and Special Values
- Negative codes: -9 (missing), -8 (unit nonresponse), -7 (not applicable), -5 (suppressed). Handle per codebook before analysis.
- Imputation flags: Fields ending with `_IM` mark imputation status.

Note: HSLS represents a U.S. cohort starting in 9th grade only; use appropriate weights (e.g., `W1STUDENT`) and filter imputed/suppressed values. O*NET occupation codes require external mapping to compare with PISA ISCO/ISEI. Prefixes: X1=Base Year, X2=First Follow-up, X4=Second Follow-up (PETS).
