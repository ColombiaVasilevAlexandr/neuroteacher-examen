# Database Audit

Generated: 2026-08-22T12:43:16

## Files

- database: `database\colombia_exam.db`
- database size: `1286144` bytes
- database sha256: `ac2431bff6c9f326ae4f2b5d4a90e2a0af538d100908cd7517f4fa38276e4201`
- backup: `database\colombia_exam.backup-20260821-205537.db` sha256 `ac2431bff6c9f326ae4f2b5d4a90e2a0af538d100908cd7517f4fa38276e4201` same_as_current `true`

## Tables

- `attempts`: 236
- `bookmarks`: 0
- `exam_sessions`: 0
- `material_chapters`: 46
- `material_pages`: 179
- `questions`: 646
- `review_queue`: 95
- `sources`: 1
- `study_settings`: 1

## Question Status

- `ai_reviewed`: 626
- `reviewed`: 20

## Student Modules

- `География`: 110
- `История`: 80
- `Конституция`: 91
- `Испанский`: 151
- `Культура`: 51
- `Натурализация`: 11
- `Микротемы`: 152

## Raw Topics

Raw topic count: `210`

- `Castellano`: 90
- `Geografía`: 88
- `Constitución`: 45
- `Historia`: 38
- `Cultura`: 34
- `Historia de Colombia`: 17
- `Recursos recomendados`: 16
- `Naturalización`: 7
- `Futuro simple`: 6
- `Fuentes recomendadas`: 5
- `Clasificación de palabras por número de sílabas`: 4
- `Geografía de Colombia`: 4
- `Habeas data`: 4
- `Historia patria`: 4
- `Acción de cumplimiento`: 3
- `Adjetivos`: 3
- `Biodiversidad`: 3
- `Conflicto armado en Colombia`: 3
- `Contenido del apartado 'Política Constitucional'`: 3
- `Crisis colonial y antecedentes de la independencia`: 3
- `Cultura de paz`: 3
- `División de palabras en sílabas`: 3
- `Estructura y composición de la población`: 3
- `Formación de la ética ciudadana`: 3
- `Género gramatical`: 3
- `Historia política de Colombia`: 3
- `Independencia`: 3
- `Independencia de Colombia`: 3
- `Instrucciones para el ejercicio`: 3
- `Liberal Revolution mid-19th century`: 3
- `Llegada de los españoles, sociedad e instituciones del Nuevo Reino de Granada`: 3
- `Organización Electoral`: 3
- `Período de La Violencia`: 3
- `Población afrocolombiana`: 3
- `Pretérito imperfecto`: 3
- `Pretérito perfecto`: 3
- `Preámbulo`: 3
- `Práctica de tiempos pasados`: 3
- `Rama legislativa`: 3
- `Recursos para ampliar conocimientos`: 3
- ... 170 more raw topics

## Sources

- `1` `Colombia, nuestra casa` `official_study_guide`
  https://www.cancilleria.gov.co/sites/default/files/FOTOS2025/Gu%C3%ADa%20de%20estudio_ajustada.pdf

## Study Settings

- `exam_date`: `2026-11-16`

## Encoding Dry Run

Suspicious sample count: `0`
- `questions`: 0 samples
- `material_pages`: 0 samples
- `material_chapters`: 0 samples
- `sources`: 0 samples

## Decision

- No database write-fix is required when suspicious sample count is `0`.
- The current database and the listed backup are identical when `same_as_current` is `true`.
- Raw topics are intentionally preserved; student UI consumes the 7 aggregated modules.
