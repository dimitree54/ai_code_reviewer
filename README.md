# AI code reviewer
AI tool for automated code review. It is designed to review you code changes (for example before commit or creating pull request) for programming principles you specify. You have to provide coding principle you are interested in by populating `.coding_principles` folder in your repo and then GPT-4-Turbo model will check your changed files for these principles. The tool has CLI (similar to flake8).

# Pricing warning:
ai_code_reviewer uses openai GPT-4-Turbo model for review which is quite expensive. You need to [set up OPENAI account](https://platform.openai.com) and will be charged there based on the model usage.

For example, checking single 100-lines long file with single 100-lines long principle will cost you around 0.03$. 

To reduce price ai_code_reviewer reviews only changed files and ignores unchanged ones. But if the file is changed, all of its lines will be processed by reviewer, so be careful running ai_code_reviewer if your files are very long. Also, only `.py` files will be reviewed.

For example, if you are checking for 5 principles and have changed 20 files, each ai_code_reviewer run would cost around 3$

Plan your budget accordingly, developers of ai_code_reviewer are not responsible for your unexpected expenses.

# Usage with command line
1. Get your OPENAI_API_KEY from https://platform.openai.com/api-keys
2. `pip install ai_code_reviewer`
3. cd to you git repository dir
4. Root of your repository should contain non-empty `.coding_principles` folder. Populate it with coding principles you want to check for during code review. You can copy principles from [the library of ready to use coding principles](https://github.com/dimitree54/ai_code_reviewer/tree/main/.coding_principles) or create your own by creating a new file with [proper format](https://github.com/dimitree54/ai_code_reviewer/blob/main/README.md#custom-principles).
5. Run ai_code_reviewer:
   1. To check not committed changed files run in terminal `OPENAI_API_KEY=sk-your-openai-key ai_code_reviewer`
   2. To check you local code version compared to some specific repository revision (for example, before creating pull request): `OPENAI_API_KEY=sk-your-openai-key ai_code_reviewer --compare_with origin/develop`

# Privacy
ai_code_reviewer does not collect or process your code. Your code will be directly uploaded to openai api using your api key. [Check their privacy terms](https://openai.com/policies/business-terms) before using ai_code_reviewer with sensitive content.

# Custom-principles
The idea of ai_code_reviewer is to be highly customisable and check only those principles you need. So if you have tried some ready-to-use principle, but it did not work for you (for example it does not review where you want it to review or otherwise, reviews code you consider good), we encourage you to modify principle file, fine-tuning it for your needs.

The principle is `.yaml` file consisting of following fields:
1. principle_name
2. principle_description - here describe what you want this reviewer to check.
3. review_required_examples - provide examples when you want this reviewer to trigger
4. review_not_required_examples - provide negative examples, when you do not want it to review

# Contribution
If you like the project you could donate you time or money for its development. [Sponsor button](https://github.com/sponsors/dimitree54) works and if you want to contribute your code, lets communicate via email dimitree54@gmail.com.

# Development plan
- [x] CLI
- [ ] Project structure understanding
- [ ] GitHub pull request reviewer bot
- [ ] GitLab merge request reviewer bot
- [ ] PyCharm plugin
