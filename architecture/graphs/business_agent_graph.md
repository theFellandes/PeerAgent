# BusinessSenseAgent LangGraph Workflow

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	ask_questions(ask_questions)
	evaluate(evaluate)
	finalize(finalize)
	__end__([<p>__end__</p>]):::last
	__start__ --> ask_questions;
	ask_questions --> evaluate;
	evaluate -.-> ask_questions;
	evaluate -.-> finalize;
	finalize --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc

```
