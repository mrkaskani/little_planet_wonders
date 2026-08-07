# Git and GitHub for Absolute Beginners

## Lesson 2 of 4: Save Changes with Commits

**Study time:** 10 minutes  
**Practice time:** 10 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- Understand the working tree, staging area, and commit history.
- Review changed files.
- Stage the files you intend to save.
- Create a clear commit.
- Read a short version of the commit history.

---

## 2. The basic Git workflow

Git saves work in three steps:

```text
Edit files → Stage selected changes → Commit a checkpoint
```

The staging area lets you choose exactly what belongs in the next commit.

```text
Working tree  --git add-->  Staging area  --git commit-->  History
```

---

## 3. Review your work

Start with:

```bash
git status
```

To inspect the actual line-by-line changes, run:

```bash
git diff
```

Always review changes before committing. This helps prevent accidental files, passwords, and unfinished work from entering history.

---

## 4. Stage files

Stage one file:

```bash
git add notes.md
```

Stage several named files:

```bash
git add notes.md README.md
```

For a small practice project, you may stage all current changes:

```bash
git add .
```

For real projects, naming files is safer because you make a deliberate choice.

Review the staged changes:

```bash
git status
git diff --staged
```

---

## 5. Create a commit

Create a commit with a short message:

```bash
git commit -m "Add project notes"
```

A good commit message completes this sentence:

```text
This commit will: Add project notes
```

Prefer messages such as:

- `Add installation instructions`
- `Fix broken navigation link`
- `Update user profile validation`

Avoid vague messages such as `changes`, `stuff`, or `update`.

---

## 6. Read the history

Show a compact history:

```bash
git log --oneline
```

Each line contains a short commit identifier and its message.

Your commit is local until you push it to a remote such as GitHub.

---

## 7. Ignore files that should not be committed

Create a `.gitignore` file for generated files, local settings, and secrets.

Example:

```gitignore
.env
__pycache__/
.venv/
node_modules/
```

Never commit passwords, API keys, personal access tokens, or private SSH keys.

---

## 8. Practice activity

In your `git-practice` repository:

1. Run `git status`.
2. Run `git diff`.
3. Stage `notes.md` with `git add notes.md`.
4. Review it with `git diff --staged`.
5. Commit it with `git commit -m "Add first practice note"`.
6. Run `git log --oneline`.

---

## 9. Short quiz

1. What is the staging area?
2. Which command stages one file?
3. Which command shows staged line changes?
4. Does a commit automatically upload to GitHub?
5. What kind of information should never be committed?

---

## 10. Quiz answers

1. It holds the selected changes for the next commit.
2. `git add <filename>`
3. `git diff --staged`
4. No. A commit is local until it is pushed.
5. Passwords, API keys, access tokens, private keys, and other secrets.

---

## 11. Completion checklist

- [ ] I understand edit, stage, and commit.
- [ ] I can review unstaged and staged changes.
- [ ] I can create a clear commit.
- [ ] I can read `git log --oneline`.
- [ ] I know not to commit secrets.
