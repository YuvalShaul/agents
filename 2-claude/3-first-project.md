# Your First Project with Claude Code

This exercise guides you to use Claude Code to create a small project of your
own, modeled on the example in [`demo/`](./demo). By the end you'll have
written a prompt that makes Claude Code plan and build a project, and
reviewed the `CLAUDE.md` it produced.

`demo/` contains a tiny in-memory FastAPI "Books API" plus a `CLAUDE.md`
describing it. `firstproj/` — the directory you're about to create — is
already covered by `.gitignore` in this directory, so it won't get
committed, but keep the directory itself around.

> **DO NOT DELETE `firstproj/` WHEN YOU'RE DONE.** You'll add
> configuration to it in a later exercise.

## Steps

1. Create the project directory and start Claude Code in it:
   ```
   mkdir firstproj
   cd firstproj
   claude
   ```

2. Skim the demo project for reference, in another terminal tab or your
   editor:
   ```
   cat ../demo/CLAUDE.md
   cat ../demo/main.py
   ```
   You're not copying this — just seeing the shape of what you're about to
   ask Claude Code to build: one FastAPI file, in-memory storage, and a
   `CLAUDE.md` describing it.

3. Back in the Claude Code session (inside `firstproj/`), paste this prompt
   as-is, or edit the resource and fields to build something else you know
   well instead (recipes, todo items, book club logs, whatever):

   > Create a small FastAPI REST API for managing movies, storing data in
   > memory only (no database). Each movie should have a title, director,
   > and year. Include a CLAUDE.md like the one in ../demo, a
   > requirements.txt, and tests that cover create/list/get/update/delete.

   Let Claude Code plan and write the files, approving its plan/edits when
   it asks.

4. Once it's done, read the `CLAUDE.md` it wrote:
   ```
   cat CLAUDE.md
   ```
   Compare it against `../demo/CLAUDE.md` — does it cover commands,
   structure, conventions, and any gotchas for your project?

5. Ask Claude Code to run the tests it wrote and confirm they pass:

   > Run the test suite and confirm everything passes.

6. Try a follow-up change, and notice how Claude Code uses the `CLAUDE.md`
   it already wrote to stay consistent with the conventions it set up in
   step 3:

   > Add a search endpoint that filters movies by title.
