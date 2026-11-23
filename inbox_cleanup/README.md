# Inbox clean-up helper

Give it a small batch of emails and it suggests what to do with each one:
**reply**, **keep**, **archive** or **unsubscribe**, with a short reason and
a draft reply where one is needed. It only suggests. You make the changes in
your mail app.

## Try it

From the repo root:

```bash
python -m inbox_cleanup.main inbox_cleanup/examples/sample_inbox.txt
```

## Using your own emails

Either way works:

1. **Paste:** copy emails into a text file, with a line containing only `---`
   between them. Sender, subject and the first part of the body are enough.
2. **Save as .eml:** most mail apps let you drag emails to a folder or use
   "Save as" to get `.eml` files. Then point the tool at the folder:

   ```bash
   python -m inbox_cleanup.main ~/Desktop/inbox_batch/
   ```

Start with 10 to 20 emails. It sorts at most 50 at a time.

Your emails are sent to the Claude API to be sorted, so leave out anything you
wouldn't want to share.

## Ideas to improve it

- Connect to Gmail and apply labels for you, after you approve each one.
- Learn from your corrections: keep a list of senders you always archive.
