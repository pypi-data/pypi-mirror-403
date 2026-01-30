Rolling agent history for infinite content:

  1. Ground truth - append-only, never summarized, persisted
  2. Projected/working history - what the LLM actually sees, includes summaries
  3. Summaries build on summaries - not re-summarizing ground truth each time

  So the projection isn't just a runtime filter - it's also persisted state that evolves over time.

  Ground Truth (append-only, saved):
  [e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, ...]  ← grows forever

  Working History (saved separately, what LLM sees):
  [summary_of_1-5, e6, e7, e8, e9, e10, ...]

  Later:
  [summary_of_1-5, summary_of_6-8, e9, e10, e11, ...]

  Later still:
  [meta_summary_of_1-8, e9, e10, e11, e12, ...]

  The working history is its own persisted list that gets compacted incrementally. Ground truth is the backup/RAG source.