# 自主全球科技法新闻发布（仅需一次配置）

原ChatGPT定时任务的GitHub写入可能被安全检查拒绝；仓库现有news-from-draft发布器需要ChatGPT先把新闻草稿写入news-drafts。现新增独立GitHub Actions研究程序，借助OpenAI Responses API web_search直接检索，读取网页、二次核验事实、复核出处及日期并去重；成功后调用现有publish_news_from_draft.py，原子更新新闻正文、首页、简报索引、归档、current-edition及核验记录。其他研究栏目不变。

必须由仓库所有者一次配置API密钥：打开 https://platform.openai.com/api-keys 创建单独项目的API Key，建议设置项目预算和使用上限。然后打开 https://github.com/Cyberlawresearch/cyberlaw-research/settings/secrets/actions ，点击 New repository secret，名称准确填写 OPENAI_API_KEY，值为自己的API Key。不要将密钥发到聊天中，也不要放入公开文件。ChatGPT订阅与API用量分别计费。

GitHub Actions中运行项目：Autonomous global technology law news。计划每天北京时间19:15、20:15、21:15检查并发布。第一次触发是任务启动，不意味着19:15秒级上线。工作流采用完整来源核验及最少10条合格新闻门槛；无法查证时不发布占位稿，不把API或Pages未完成说成上线。部分新闻来源可能封锁自动读取，人工专业复核仍有价值。

配置密钥后，进入Actions该工作流，选择Run workflow验证。若今天已经发布，任务会跳过研究及API调用；需在明天首次发布前才能测试完整的研究与发布流程。最终只有GitHub Pages completed/success并验证线上current-edition/正文才算完成。单次错误会生成GitHub Issue，不会停用每日计划，也不会强推覆盖其他栏目。GitHub定时事件本身可能被延迟或偶尔丢弃，三个启动时点可降低但不能消除此风险。
