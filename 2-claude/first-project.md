# Your First Project with Claude Code

This walks you through using Claude Code to build a small project of your own,
modeled on the example in [`demo/`](./demo).

The `demo/` directory contains a tiny in-memory FastAPI "Books API" together
with a `CLAUDE.md` describing it. The goal here is to have Claude Code build
something similar from scratch, in a new directory called `firstproj`, so you
can see the whole workflow end to end: writing a `CLAUDE.md`, letting Claude
plan and implement, and reviewing what it did.

`firstproj/` is already covered by `.gitignore` in this directory, so you can
experiment freely without worrying about committing throwaway code.

## Steps

1. Create the project directory and start Claude Code in it:
   ```
   mkdir firstproj
   cd firstproj
   claude
   ```

2. Look at `../demo/CLAUDE.md` and `../demo/main.py` for inspiration, then ask
   Claude Code to scaffold a similar project — same idea (a small in-memory
   REST API), different resource.

   **Demo prompt** — paste this in as-is to see it work, or swap `movies` for
   a resource of your own:
   > Create a small FastAPI REST API for managing movies, storing data in
   > memory only (no database). Each movie should have a title, director,
   > and year. Include a CLAUDE.md like the one in ../demo, a
   > requirements.txt, and tests that cover create/list/get/update/delete.

   Pick something simple you know well — movies, recipes, todo items,
   whatever. The point is to see Claude Code produce the same shape of
   project as `demo/`, not to copy it exactly.

3. Read the `CLAUDE.md` Claude writes for `firstproj`. Compare it against
   `../demo/CLAUDE.md` — does it cover commands, structure, conventions, and
   any gotchas for your project?

4. Ask Claude Code to run the tests it wrote, and confirm they pass.

5. Try a follow-up change (e.g. "add a search endpoint by title") and notice
   how Claude Code uses the `CLAUDE.md` it already wrote to stay consistent
   with the conventions it set up in step 2.
