# Downloads organiser

Suggests clearer file names and a simple folder structure for a messy folder
such as Downloads. You see the plan first, and nothing moves until you say yes.

**Safety:**
- Claude only sees file **names, sizes and dates**, never what's inside the files.
- It only looks at files directly inside the folder. Subfolders and hidden files are left alone.
- Nothing is ever deleted or overwritten. If a name clashes, that file is skipped.
- Each run that moves files saves an **undo log**, so you can put everything back.

## Try it

Start with a test folder, as the project suggests: copy about 20 files into
`~/Desktop/test-downloads`, then preview the plan. This changes nothing:

```bash
python -m downloads_organiser.main ~/Desktop/test-downloads
```

If you like the plan, run it again with `--apply`. It shows the preview and
asks you to type `yes` before moving anything:

```bash
python -m downloads_organiser.main ~/Desktop/test-downloads --apply
```

To put everything back:

```bash
python -m downloads_organiser.main --undo ~/Desktop/test-downloads/.organiser-undo-<date>.json
```

By default it looks at the newest 20 files. Use `--limit 50` to look at more.
It's also on the test page (`streamlit run app.py`), with Preview, Apply and
Undo buttons.

The plan is a new suggestion each time, so applying always uses the preview
you just saw.

## Ideas to improve it

- Remember your folder structure and reuse it next time.
- Peek inside PDFs (with your OK) to name receipts and bills better.
- Run weekly and only handle new files.
