# 🧐 `scilint`

*infuse quality into notebook based workflows with a new type of build tool*

---

`scilint` aims to **bring a style and quality standard into notebook based Data Science workflows**. How you define a quality notebook is difficult and somewhat subjective. It can have the obvious meaning of being free of bugs but also legibility and ease of comprehension are important too.

`scilint` takes the approach of breaking down potentially quality relevant aspects of the notebook and providing what we believe are sensible defaults that potentially correlate with higher quality workflows. We also let users define the quality line as they see fit through configuration of existing thresholds and ability to add new metrics. As use of the library grows we anticipate being able to statistically relate some of the quality relevant attributes to key delivery metrics like "change failure rate" or "lead time to production".

# Standing on the shoulders of giants - *an nbdev library*

> `scilint` is written on top of the excellent `nbdev` library. This library is revolutionary as it truly optimises all the benefits of notebooks and compensates for some of their weaker points. For more information on `nbdev` see the [homepage](https://nbdev.fast.ai/) or [github repo](https://github.com/fastai/nbdev)

# Getting Started

[WIP] - (reviewers) this requires that the library is published to pypi which has not yet happened

`pip install scilint`

`scilint` has the following main features/commands:
    
* `scilint_tidy`: run an in-place opinionated flavour of [nbQA](https://github.com/nbQA-dev/nbQA) to tidy up your ntoebooks
* `scilint_lint`: inspect the notebooks for potential quality correlates and report on the findings
* `scilint_build`: the build command for notebooks: ensuring they all run, pass their tests and meet a consistent style/quality standard

# Development

Clone the repository and run an editable pip install `pip install -e .`.

# Contributing

After you clone this repository, please run nbdev_install_hooks in your terminal. This sets up git hooks, which clean up the notebooks to remove the extraneous stuff stored in the notebooks (e.g. which cells you ran) which causes unnecessary merge conflicts.

To run the tests in parallel, launch nbdev_test.

Before submitting a PR, check that the local library and notebooks match.

If you made a change to the notebooks in one of the exported cells, you can export it to the library with nbdev_prepare.
If you made a change to the library, you can export it back to the notebooks with nbdev_update.