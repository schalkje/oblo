# Architecure

## <blogger>

Think of a good name fot this <blogger> assistant. <blogger> help me refine an idea to a blod.

## Prompt:
Think of a setup to create a blog.

It all starts with an idea, just a couple of sentences.
The idea should have a goal, a definition of done

<blogger> helps grill the first idea

work out a plan, to get enough content
- internet research
- PoC implementation

<blogger> helps with sharing code and examples for each blog when that is applicable

Writing and tuning the article

Updating the wording; updating the tone of voice
Checking reference, adding links to official docs, other blogs and video's

### technical principles

Blogger is a multiagent setup

### Phases
- Brainstorming
- Research
- Gathering evidence
- Writing
- Publishing
- Monitoring
  - monitor references; if they change (especially documentation)
  - monitor referenced blogs; monitor comments
    - suggest changes
    - suggest deprecation
- Deprecation

Statusses (make this a mermaid flow diagram):
- ideation
- writing
- finalising
- published
  - relevant
  - outdated
  - irrelevant / paseed by
- deprecated / archived


### UI

Blogger is using a UI

* This blog is markdown based
  * Images are png
  * Dynamic mermaid diagrams to clarify; based on markread application
    * structure
    * processes
    * erd diagrams
* When making a change, a new version of the blog is created
* The storage is git based, for versioning
    * multiple versions of the blog can exist next to eachother withing the same git version; name based
    * There is always a main version
* When a change is made, 
  * changes can be shown inline
  * Changes can be shown next to each other
* It should be possible to put the current version next to every past version 
* It should be possible to select a part of the blog, and change only that part
* There should be a module to work on images
  * finetuning images, createing multiple variations on images
* Is is possible to work on multiple blogs at the same time
  * switch to and forth
  * easy to look and copy from previous blogs
  * easy to refer to old blogs, to be taken into account
  * work in parallel, 
    * work on multiple screens
    * work in multiple windows
    * work in tabs


### Publishing

When I say the post is complete, <blogger> helps with publishing, for minimum manual work.

### Comment handling

Comments should be retrieved
automatically classified, 
- advertisements automatically removed 
- unrelated comments, not published, ask for deletion
- real comments, generate proposal answer
  - make sure entire threads and related comments and answers are considered

## technical principles

Let's use an agent setup; 
- orchestrator / coordinator:
  - what is th bast mode for this? gpt-5-mini
- Image generator
  - Image tuner
- idea generator
- researcher
  - helps doing research and experiments
  - brings structure and plans
- writer
  - make the idea and the research into a compelling story
  - follow best practices of the best blogs
- tone of voice; 
  - update the the exact wording to create a personal blog
  - it is me telling the stories, 

