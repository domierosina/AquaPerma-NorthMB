
# Contributing & Git Usage

## Branching
- Base branch: `main`
- Feature branches: `feature/<short-description>`
- Fix branches: `fix/<short-description>`

## Commits
- Make **small, frequent** commits.
- Use present tense and imperative mood:
  - `add NDWI compute for Landsat bands`
  - `fix reprojection alignment in preprocessing`
- Reference issues (if any): `refs #12`

## Workflow
1. `git checkout -b feature/ndwi-thresholding`
2. Make changes, commit often.
3. `git push -u origin feature/ndwi-thresholding`
4. Open a Pull Request into `main`.
5. CI must pass (lint + tests).

## Releases / Tags
- Tag milestones: `git tag -a v0.1 -m "proposal demo"`; `git push --tags`.

## Data
- Do **not** commit raw/large data. See `data/README.md` for storage options.
