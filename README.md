# AI Inquiry Processing Agent

面向外贸销售场景的 AI 询盘处理系统。它将海外客户的邮件或平台消息转换为结构化采购需求，判断信息完整性，并根据情况自动生成澄清问题或执行产品检索、匹配、业务查询和英文回复生成。

## Workflow

```text
Inquiry Input
  -> Inquiry Parser
  -> Completeness Checker
       -> Clarification Generator
       -> Product Retrieval -> Product Matching
          -> Price / Inventory / Lead Time / Specification Tools
          -> English Response Generator
```

LangGraph 管理完整询盘与信息缺失两类处理分支。前端工作台会在一个页面展示结构化字段、完整性判断、Top-K 候选产品、匹配理由、工具结果、英文回复草稿和执行轨迹。

## Features

- Pydantic Inquiry Schema：产品、数量、国家、规格、目标价格和交付要求。
- 双解析模式：默认离线规则解析；可切换 OpenAI Structured Output。
- Embedding 产品知识库与 Top-K 语义检索。
- MOQ、库存、目标价格和规格驱动的可解释产品匹配。
- 价格、库存、交期、规格四项独立业务工具。
- 信息不足时生成英文澄清邮件，信息完整时生成报价建议。
- 固定 Benchmark 覆盖抽取、意图、检索、工具调用及端到端完成率。
- 响应式 HTML/CSS/JavaScript 演示前端。

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

打开：

- Agent 工作台：http://127.0.0.1:8000/ui/
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

默认不需要 API Key。需要真实 LLM 结构化解析时：

```bash
pip install -e ".[openai]"
```

然后在 `.env` 中设置：

```text
OPENAI_API_KEY=your_key
INQUIRY_PARSER_PROVIDER=openai
INQUIRY_PARSER_MODEL=gpt-4o-mini
```

## API Example

创建询盘：

```bash
curl -X POST http://127.0.0.1:8000/inquiries \
  -H "Content-Type: application/json" \
  -d '{"content":"Please quote 1,000 pcs cotton canvas tote bags shipping to Australia, FOB."}'
```

使用返回的 `inquiry_id` 运行完整工作流：

```bash
curl -X POST http://127.0.0.1:8000/inquiries/INQUIRY_ID/process
```

## Evaluation

```bash
python eval/run_inquiry_eval.py
```

输出指标：

- Information Extraction Accuracy
- Intent Classification Accuracy
- Product Retrieval Recall@K
- Tool Calling Accuracy
- End-to-End Task Completion Rate

## Project Structure

```text
app/
  inquiry/               # Schema、解析、校验、检索、匹配、工具和工作流
  evaluation/            # 询盘评测指标
  main.py                # FastAPI 与前端入口
data/
  inquiry/products.json  # 产品知识库
  eval/                  # 固定 Benchmark
frontend/                # 演示工作台
tests/                   # 模块和端到端测试
docs/                    # 简历项目描述
```

## Current Boundaries

- 默认使用内存 Repository，服务重启后询盘记录会清空。
- 默认产品索引是本地向量索引，生产环境可以替换为 Milvus、Qdrant 或 Chroma。
- 报价为演示业务数据，正式发送前需要销售人工审核。
