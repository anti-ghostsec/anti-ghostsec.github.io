# anti-ghostsec.github.io

The project site at <https://anti-ghostsec.github.io>: a home page plus one page per project, built from each repository's description and README.

Rebuild after changing a project's README or description:

```bash
python3 tools/build.py
```

The build needs the `gh` CLI. It writes the pages, `sitemap.xml` and `robots.txt`. To add a project, add a line to `PROJECTS` in `tools/build.py`.
