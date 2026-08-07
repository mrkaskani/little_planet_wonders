# Git and GitHub for Absolute Beginners

## Lesson 3 of 4: Connect and Sync with GitHub

**Study time:** 10 minutes  
**Practice time:** 15 minutes

---

## 1. Lesson objective

By the end of this lesson, you will be able to:

- Create an empty GitHub repository.
- Connect a local repository to GitHub with HTTPS.
- Push local commits.
- Clone an existing repository.
- Pull changes from GitHub.

---

## 2. Create an empty repository on GitHub

On GitHub:

1. Select **New repository**.
2. Enter a repository name.
3. Choose public or private.
4. For this exercise, do not add a README, `.gitignore`, or license because the local project already has a commit.
5. Select **Create repository**.

GitHub will show the repository HTTPS address, similar to:

```text
https://github.com/YOUR-NAME/git-practice.git
```

---

## 3. Connect your local repository

In the local practice repository, rename the main branch if needed:

```bash
git branch -M main
```

Add GitHub as a remote named `origin`:

```bash
git remote add origin https://github.com/YOUR-NAME/git-practice.git
```

Check the remote:

```bash
git remote -v
```

Push the branch for the first time:

```bash
git push -u origin main
```

After `-u` sets the upstream branch, future pushes can usually use:

```bash
git push
```

---

## 4. HTTPS authentication

GitHub does not accept your account password for Git operations over HTTPS. Depending on your setup, Git Credential Manager may open a browser and ask you to sign in. Follow that browser flow when it appears.

If the terminal asks for a username and password, use:

```text
Username: your GitHub username
Password: a GitHub personal access token
```

Treat the token like a password. Do not place it in the remote URL, a file, a screenshot, or a commit.

Your operating system may store the token securely. On macOS, manually cached GitHub credentials may use `git-credential-osxkeychain`, which stores them in the macOS Keychain.

See GitHub's official guides for [command-line authentication](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github) and [personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

---

## 5. Clone an existing repository

To download a repository into a new folder:

```bash
git clone https://github.com/YOUR-NAME/REPOSITORY.git
```

Then enter the folder:

```bash
cd REPOSITORY
```

Cloning downloads the files, history, and remote configuration.

---

## 6. Pull before you work

If the GitHub repository may have newer commits, update your local branch:

```bash
git pull
```

A simple solo workflow is:

```text
git pull
→ edit
→ git status
→ git add
→ git commit
→ git push
```

If `git push` is rejected because GitHub has newer commits, do not force-push. Run `git pull`, resolve any conflict, then push again.

---

## 7. Practice activity

1. Create an empty GitHub repository.
2. Copy its HTTPS URL.
3. Add it as `origin`.
4. Run `git remote -v` and confirm the URL.
5. Push your `main` branch.
6. Refresh GitHub and confirm that `notes.md` is visible.

---

## 8. Short quiz

1. What is a remote?
2. What is the usual name of the main GitHub remote?
3. Which command uploads commits?
4. Which command downloads and integrates newer commits?
5. What should you use instead of your GitHub password over HTTPS?

---

## 9. Quiz answers

1. An online copy or connection to another Git repository.
2. `origin`
3. `git push`
4. `git pull`
5. A GitHub personal access token.

---

## 10. Completion checklist

- [ ] I created an empty GitHub repository.
- [ ] I connected my local repository with HTTPS.
- [ ] I can push and pull commits.
- [ ] I understand what cloning does.
- [ ] I know how to protect my personal access token.
