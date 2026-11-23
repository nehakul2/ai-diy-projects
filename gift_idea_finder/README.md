# Gift idea finder

Tell it who the gift is for, your budget and a few things they like. Claude
searches the web and gives you **5 gift ideas with links**, plus its top pick.
You make the final choice.

## Try it

From the repo root:

```bash
python -m gift_idea_finder.main \
  --who "my sister, 30, just moved to Denver" \
  --budget "50 USD" \
  --likes "hiking, coffee, crime podcasts" \
  --occasion birthday
```

Or just run it and answer the questions:

```bash
python -m gift_idea_finder.main
```

Add `--country UK` to shop in a particular country, and `-o gifts.md` to save
the result.

Each run uses web search, which costs a little extra on top of the normal API
usage (see Anthropic's pricing page).

## Ideas to improve it

- Remember past gifts per person so it never repeats.
- Add `--avoid` for things they already own or dislike.
- Compare prices across two shops.
