<div align="center">
<h1 style="text-align: center;">INTERVENOR</h1>

<img src="assets/title.jpg" width="200px">

</div>

Source code for ACL 2024 paper [INTERVENOR : Prompt the Coding Ability of Large Language Models with the Interactive Chain of Repairing](https://arxiv.org/abs/2311.09868)

## 本fork：公开样例与独立隐藏评分

本fork保留原论文的Code Teacher建议→Code Learner修复→重新测试流程，最多5轮；没有改成TraceCoder的插桩、轨迹、patience或回退方法。原教师／学生提示仍由原函数和模板提供。

本轮适配入口是`public_adapter.py`：接收共享E0初始代码，只使用公开题面、公开样例和公开执行反馈。模型传输、候选隔离及独立隐藏评分由[self-debug](https://github.com/yangxu18645796499/self-debug)统一承担；本仓库不重复存放题库和实验结果。

- [四方法完整实验报告](https://github.com/yangxu18645796499/self-debug/blob/main/docs/实验结果汇总.md)：HumanEval／HE+、MBPP-500／MBPP+、LiveCodeBench、ClassEval。
- [改造、冻结与运行说明](https://github.com/yangxu18645796499/self-debug/blob/main/docs/intervenor/改造与运行说明.md)。
- [TraceCoder对比方法](https://github.com/yangxu18645796499/TraceCoder)：独立保留原轨迹方法，不与本方法混写。

本轮实际方法源码提交为`53945b2`，基于上游`45c3e461f1c169baf9e412733ec8548f58ab1713`；后续发布说明和Git属性提交不改变已完成实验的冻结版本。四个冻结文件的逐文件换行规则仅保持当时字节，不批量格式化代码。

模型调用为官方DeepSeek `deepseek-flash`，关闭thinking、1024输出tokens、temperature=0.2、180秒、串行、重试0。E0、SELF-DEBUG、INTERVENOR和TraceCoder共享初始代码；隐藏结果不返回给模型或停止判断。完整批次已结束，克隆仓库不会自动调用API。

以下保留原作者的背景与旧复现说明，不是本轮安全运行入口。**不要照旧教程把密钥写入源码，也不要直接用原隐藏评测反馈调试。** 本轮凭证仅由self-debug通过内存传递；原始命令中的模型、数据和预算不代表本轮配置。保留原作者及现有许可文件，不新增仓库级许可证声明。



## Overview
INTERVENOR conducts an interactive code-repair process, facilitating the collaboration among agents and the code compiler.

In the initial step (**Step A^0**, where 0 signifies the initial turn), we prompt the Code Learner to generate code for the given task. Subsequently, the Code Learner executes the generated code using the code compiler to assess its correctness (**Step B**). Following this, the Code Teacher generates code repair instructions (CoR) based on the bug report and the associated buggy code (**Step C**). These instructions elucidate the reason of the bug, such as ``modified to handle the case where the input decimal is 0``, and include code correction planning, for example, ``we can simply return db0db``. Such instructions are informative and enhance the guidance for the Code Learner. Ultimately, the Code Learner follows the chain-of-repair (CoR) to rectify the code and subsequently resubmits the corrected version to the compiler for execution in the subsequent turn ((**Step A^i**), where i≥1 denotes the code repair process). The A^i, B, and C steps are iterated sequentially until either the code meets the compiler's estimation or the maximum turn limit is reached.
![model](assets/model.gif)
## Requirements

Install dependencies:

```
git clone https://github.com/NEUIR/INTERVENOR.git
cd INTERVENOR
pip install -r requirements.txt
pip install -e human-eval
```



## Reproduce

### 1.Code Generation
Set your API KEY in [this](https://github.com/NEUIR/INTERVENOR/blob/532c9c26d4845d995b5d0cf38d9dcb32fe70b712/agents/gpt/gpt_wrapper.py#L9).

First, we need to generate initial code based on natural language descriptions.

```bash
python intervenor.py \
        --problem_file =human_eval/data/human-eval-v2-20210705.jsonl \
        --dataset humaneval \ # choices=["humaneval", "mbpp", "humanevalx", "codeerror"]
        --language python \ # choices=["python", "cpp", "java", "js"]
        --model gpt-3.5-turbo-instruct-0914 \
        --max_tokens 512 \
        --temperature 0.2 \
        --num_samples_per_task 1 \
        --todo code_generation # choices=["code_generation", "cor_generation", "code_reapir"]
```

The result file is saved in  `./results/code_generation/{dataset}/{language}.jsonl`.

After obtaining the initial generated code, it is necessary to test the generated code and retain the test results along with error information.

For more detailed testing steps, please refer to [HumanEval Repo](https://github.com/openai/human-eval)

```bash
evaluate_functional_correctness {result path} --problem_file={problem_path}
```

The test result file is saved in the `./results/code_generation/{dataset}/{language}.jsonl_results.jsonl`.



### 2.Chain-of-Reapiring (CoR) Generation

After obtaining the test results, we know which code is correct and which is incorrect. For erroneous code, we employ Code Teacher to provide the Chain-of-Repairing (CoR).

```bash
python intervenor.py \
        --problem_file =human_eval/data/human-eval-v2-20210705.jsonl \
        --dataset humaneval \
        --language python \
        --model gpt-3.5-turbo-instruct-0914 \
        --max_tokens 512 \
        --temperature 0.2 \
        --num_samples_per_task 1 \
        --todo cor_generation # change to cor_generation
```

The cor file is saved in  `./results/cor_generation/{dataset}/{language}_cor.jsonl`.



### 3.Code Repair

After obtaining the Chain-of-Repairing (CoR), we proceed to fix the buggy code and save the repaired code to  `./results/code_repair/{dataset}/{language}.jsonl`.

```bash
python intervenor.py \
        --problem_file =human_eval/data/human-eval-v2-20210705.jsonl \
        --dataset humaneval \
        --language python \
        --model gpt-3.5-turbo-instruct-0914 \
        --max_tokens 512 \
        --temperature 0.2 \
        --num_samples_per_task 1 \
        --todo code_repair # change to cor_repair
```

Then, we test the repaired code.

```bash
evaluate_functional_correctness {result path} --problem_file={problem_path}
```



## Prompts

INTERVENOR involves the integration of two agents, Code Learner and Code Teacher, who work interactively to repair the generated codes.  The prompts they use are as follows:

**Code Teacher：**

```
You are an experienced and insightful programming instructor, and you need to identify the bugs in the given code based on the error messages.

- buggy code:
%%%buggy_code%%%

When testing the above code, errors occurred: %%%error_message%%%, some test cases did not pass!
Please check the implementation of the function and provide a method for modification based on the error message. No need to provide the modified code.

Modification method:

```



**Code Learner：**

```
You are a student assistant with excellent code repair capabilities. You can attempt to fix the bugs in the above code based on the provided error information and the method for modification. Please make sure to carefully check every potentially problematic area and make appropriate adjustments and corrections.

- buggy code:
%%%buggy_code%%%

When testing the above code, errors occurred: %%%error_message%%% , some test cases did not pass! Please check the implementation of the function and fix the code based on the modification method.

- modification method:
%%%repair_method%%%

Correct the code:

```

For additional prompts, please refer to this [directory](./prompt) and our [paper](https://arxiv.org/abs/2311.09868).



## Citation

If you use our code or our data for your research, feel free to cite our publication:

```
@inproceedings{wang2024intervenor,
      title={INTERVENOR: Prompt the Coding Ability of Large Language Models with the Interactive Chain of Repair}, 
      author={Hanbin Wang and Zhenghao Liu and Shuo Wang and Ganqu Cui and Ning Ding and Zhiyuan Liu and Ge Yu},
      booktitle={Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics},
      year={2024}  
}
```



## Contact

Please send email to [wanghanbinpanda@gmail.com](mailto:wanghanbinpanda@gmail.com).

## 2026-10-27整理说明

本仓库只保留原方法及公开输入适配，完整数据和四方法成绩统一放在self-debug。新增SELF-DEBUG方法独立位于https://github.com/yangxu18645796499/SelfDebug_prompts_in_TraceCoder ，没有改写本方法。此次只更新说明、移除IDE配置，不修改实际算法、prompt或已完成实验结果。旧文件树保存在本地`codex/archive-before-main-review-20261027`分支。当前整理分支等待用户确认后再合并main和推送。
