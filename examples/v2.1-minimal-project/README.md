# V2.1 Minimal Project

This synthetic, metadata-only project demonstrates Shot 001 with a rejected
first candidate and an approved second candidate selected for a rough cut.
It contains no production media. Run `drama validate --project . --level
structure` from this directory to validate metadata. `--level files` is
expected to fail because `video.placeholder` paths deliberately do not exist;
empty placeholders are never treated as valid media.
