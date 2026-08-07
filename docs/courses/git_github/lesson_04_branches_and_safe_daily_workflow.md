# Git and GitHub for Absolute Beginners

## Lesson 4 of 4: Branches and a Safe Daily Workflow

**Study time:** 10 minutes  
**Practice time:** 15 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- Explain why branches are useful.
- Create and switch to a branch.
- Merge a completed branch into `main`.
- Undo a simple unstaged or staged mistake.
- Follow a safe daily Git routine.

---

## 2. What is a branch?

A branch is a separate line of work inside the same repository.

```text
main
  └── add-readme
```

Use a branch when you want to make a feature or fix without changing `main` immediately.

Create and switch to a branch:

```bash
git switch -c add-readme
```

Check your current branch:

```bash
git branch
```

The branch marked with `*` is active.

---

## 3. Work and commit on the branch

Edit your files, then use the same workflow:

```bash
git status
git diff
git add README.md
git diff --staged
git commit -m "Add project README"
```

Push the new branch:

```bash
git push -u origin add-readme
```

On GitHub, you can open a pull request to review the change before merging it.

---

## 4. Merge locally

For a simple solo project, switch back to `main`, update it, and merge:

```bash
git switch main
git pull
git merge add-readme
git push
```

After confirming the merge, delete the local branch if you no longer need it:

```bash
git branch -d add-readme
```

If Git reports a merge conflict, open each listed file, choose the correct content, remove the conflict markers, stage the resolved files, and commit. Ask for help if you are unsure; do not guess or force the operation.

---

## 5. Undo two common beginner mistakes

Discard unstaged changes in one file:

```bash
git restore notes.md
```

This replaces your current edits with the last committed version. Review the file first because the discarded edits are difficult to recover.

Remove a file from the staging area while keeping its edits:

```bash
git restore --staged notes.md
```

Then use `git status` to confirm the result.

Avoid destructive commands such as `git reset --hard` while learning Git.

---

## 6. Safe daily workflow

Use this routine:

```bash
git switch main
git pull
git switch -c short-task-name

# Edit files

git status
git diff
git add <files>
git diff --staged
git commit -m "Describe the completed change"
git push -u origin short-task-name
```

Before every commit, ask:

- Am I on the correct branch?
- Did I review the changes?
- Did I exclude secrets and generated files?
- Does the commit contain one understandable change?
- Does the message explain that change?

---

## 7. Essential command reference

| Command | Purpose |
|---|---|
| `git status` | Show the current state |
| `git diff` | Show unstaged line changes |
| `git add <file>` | Stage a file |
| `git commit -m "message"` | Save a checkpoint |
| `git log --oneline` | Show compact history |
| `git pull` | Download and integrate commits |
| `git push` | Upload local commits |
| `git switch -c <branch>` | Create and enter a branch |
| `git switch main` | Return to `main` |
| `git merge <branch>` | Merge a branch into the current branch |
| `git restore <file>` | Discard unstaged edits |
| `git restore --staged <file>` | Unstage while keeping edits |

---

## 8. Practice activity

1. Create a branch named `update-notes`.
2. Add a second sentence to `notes.md`.
3. Review, stage, and commit it.
4. Push the branch to GitHub.
5. Switch to `main` and merge `update-notes`.
6. Push `main`.
7. Confirm the new sentence appears on GitHub.

---

## 9. Short quiz

1. Why use a branch?
2. Which command creates and switches to a new branch?
3. What does `git restore --staged notes.md` do?
4. What should you do before `git push` if the remote may have newer commits?
5. Should a beginner use `git reset --hard` casually?

---

## 10. Quiz answers

1. To isolate a change from the main line of work.
2. `git switch -c <branch-name>`
3. It removes the file from staging but keeps its edits.
4. Run `git pull` and resolve any conflicts safely.
5. No. It can destroy uncommitted work.

---

## 11. Completion checklist

- [ ] I can create and switch branches.
- [ ] I can commit and push a branch.
- [ ] I can merge a completed branch into `main`.
- [ ] I can unstage a file without deleting its edits.
- [ ] I can follow the safe daily workflow.
