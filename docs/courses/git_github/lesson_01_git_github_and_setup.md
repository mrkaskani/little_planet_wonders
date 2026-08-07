# Git and GitHub for Absolute Beginners

## Lesson 1 of 4: Git, GitHub, and First-Time Setup

**Study time:** 10 minutes  
**Practice time:** 10 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- Explain the difference between Git and GitHub.
- Check whether Git is installed.
- Set the name and email recorded in your commits.
- Turn a normal folder into a Git repository.
- Check the repository status.

---

## 2. Git and GitHub are different

**Git** is a version-control tool on your computer. It records changes to files so you can understand what changed and return to earlier versions.

**GitHub** is a website that stores Git repositories online. It helps you back up code and collaborate with other people.

```text
Git    = tracks versions on your computer
GitHub = stores and shares Git repositories online
```

You can use Git without GitHub. GitHub repositories use Git.

---

## 3. Check that Git is installed

Open Terminal, PowerShell, or the terminal in your code editor and run:

```bash
git --version
```

If Git is installed, you will see a version number. If the command is not found, install Git from [git-scm.com](https://git-scm.com/downloads), then reopen the terminal.

---

## 4. Set your commit identity

Run these commands once, replacing the example values with your own:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Use an email connected to your GitHub account if you want GitHub to associate commits with your profile.

Check the values:

```bash
git config --global user.name
git config --global user.email
```

This information is written into commits. It is not your GitHub password.

---

## 5. Create your first repository

Create or open a small practice folder, then run:

```bash
git init
```

Git creates a hidden `.git` directory. That directory stores the repository history. Do not edit or delete it manually.

Check the repository:

```bash
git status
```

`git status` is the safest command for a beginner. It tells you:

- Which branch you are on.
- Which files changed.
- Which files are staged for the next commit.
- Which files Git is not tracking yet.

---

## 6. Important vocabulary

| Term | Meaning |
|---|---|
| Repository | A project tracked by Git |
| Working tree | The files currently in your project folder |
| Commit | A saved checkpoint in Git history |
| Branch | A named line of development |
| Remote | An online copy, usually on GitHub |

---

## 7. Practice activity

1. Create a folder named `git-practice`.
2. Open that folder in a terminal.
3. Run `git init`.
4. Run `git status`.
5. Create a file named `notes.md` and write one sentence in it.
6. Run `git status` again.

You should see `notes.md` listed as an untracked file.

---

## 8. Short quiz

1. What does Git do?
2. What does GitHub do?
3. Which command creates a Git repository?
4. Which command shows the current repository state?
5. Is your configured Git email a password?

---

## 9. Quiz answers

1. Git tracks versions of files and records project history.
2. GitHub stores and shares Git repositories online.
3. `git init`
4. `git status`
5. No. It is identity information stored in commits.

---

## 10. Completion checklist

- [ ] Git is installed.
- [ ] My Git name and email are configured.
- [ ] I can explain Git versus GitHub.
- [ ] I created a practice repository.
- [ ] I can use `git status`.
