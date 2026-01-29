from typing import List, Dict, Any, Optional, Set
import asyncio
import logging
import time
from datetime import datetime, timedelta

from gpt_researcher.llm_provider.generic.base import ReasoningEfforts
from ..utils.llm import create_chat_completion
from ..utils.enum import ReportType, ReportSource, Tone
from ..actions.query_processing import get_search_results

logger = logging.getLogger(__name__)

# Maximum words allowed in context (25k words for safety margin)
MAX_CONTEXT_WORDS = 25000


def count_words(text: str) -> int:
    """Count words in a text string"""
    return len(text.split())


def trim_context_to_word_limit(context_list: List[str], max_words: int = MAX_CONTEXT_WORDS) -> List[str]:
    """Trim context list to stay within word limit while preserving most recent/relevant items"""
    total_words = 0
    trimmed_context = []

    # Process in reverse to keep most recent items
    for item in reversed(context_list):
        words = count_words(item)
        if total_words + words <= max_words:
            trimmed_context.insert(0, item)  # Insert at start to maintain original order
            total_words += words
        else:
            break

    return trimmed_context


class ResearchProgress:
    def __init__(self, total_depth: int, total_breadth: int):
        self.current_depth = 1  # Start from 1 and increment up to total_depth
        self.total_depth = total_depth
        self.current_breadth = 0  # Start from 0 and count up to total_breadth as queries complete
        self.total_breadth = total_breadth
        self.current_query: Optional[str] = None
        self.total_queries = 0
        self.completed_queries = 0


class DeepResearchSkill:
    def __init__(self, researcher):
        self.researcher = researcher
        self.breadth = getattr(researcher.cfg, 'deep_research_breadth', 4)
        self.depth = getattr(researcher.cfg, 'deep_research_depth', 2)
        self.concurrency_limit = getattr(researcher.cfg, 'deep_research_concurrency', 2)
        self.websocket = researcher.websocket
        self.tone = researcher.tone
        self.config_path = researcher.cfg.config_path if hasattr(researcher.cfg, 'config_path') else None
        self.headers = researcher.headers or {}
        self.visited_urls = researcher.visited_urls
        self.learnings = []
        self.research_sources = []  # Track all research sources
        self.context = []  # Track all context

    async def generate_search_queries(self, query: str, num_queries: int = 3) -> List[Dict[str, str]]:
        """Generate SERP queries for research"""
        messages = [
            {"role": "system", "content": "You are an expert researcher generating search queries."},
            {"role": "user",
             "content": f"Given the following prompt, generate {num_queries} unique search queries to research the topic thoroughly. For each query, provide a research goal. Format as 'Query: <query>' followed by 'Goal: <goal>' for each pair: {query}"}
        ]

        response = await create_chat_completion(
            messages=messages,
            llm_provider=self.researcher.cfg.strategic_llm_provider,
            model=self.researcher.cfg.strategic_llm_model,
            reasoning_effort=self.researcher.cfg.reasoning_effort,
            temperature=0.4
        )

        # 添加调试日志
        logger.debug(f"LLM 响应内容 (前 1000 字符): {response[:1000]}")
        print(f"\n🔍 调试：LLM 原始响应:\n{'-' * 60}\n{response}\n{'-' * 60}\n", flush=True)

        # 改进的解析逻辑 - 支持多种格式
        import re
        queries = []

        # 尝试多种解析策略

        # 策略 1: 原始格式 (Query: ... Goal: ...)
        lines = response.split('\n')
        current_query = {}

        for line in lines:
            line = line.strip()
            # 支持多种 Query 格式
            if re.match(r'^(Query|查询|\*\*Query\*\*|\d+\.\s*Query)[:\s：]', line, re.IGNORECASE):
                if current_query and 'query' in current_query:
                    queries.append(current_query)
                # 提取查询内容
                query_text = re.sub(r'^(Query|查询|\*\*Query\*\*|\d+\.\s*Query)[:\s：]+', '', line,
                                    flags=re.IGNORECASE).strip()
                query_text = query_text.strip('*').strip()  # 移除可能的 markdown 标记
                current_query = {'query': query_text}
            # 支持多种 Goal 格式
            elif re.match(r'^(Goal|目标|\*\*Goal\*\*)[:\s：]', line, re.IGNORECASE) and current_query:
                goal_text = re.sub(r'^(Goal|目标|\*\*Goal\*\*)[:\s：]+', '', line, flags=re.IGNORECASE).strip()
                goal_text = goal_text.strip('*').strip()
                current_query['researchGoal'] = goal_text

        if current_query and 'query' in current_query:
            queries.append(current_query)

        # 策略 2: 如果策略 1 失败，尝试提取编号列表格式
        if not queries:
            logger.info("策略 1 失败，尝试策略 2：提取编号列表")
            print(f"⚠️ 策略 1 解析失败，尝试策略 2...", flush=True)

            # 匹配类似 "1. xxx" 或 "1) xxx" 的格式
            numbered_items = re.findall(r'(?:^|\n)\s*(\d+)[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\Z)', response, re.DOTALL)
            for num, content in numbered_items[:num_queries]:
                # 尝试从内容中提取查询和目标
                content_lines = content.strip().split('\n')
                query_text = content_lines[0].strip()
                goal_text = ' '.join(content_lines[1:]).strip() if len(content_lines) > 1 else "Research this topic"

                queries.append({
                    'query': query_text,
                    'researchGoal': goal_text or "Research this topic"
                })

        # 策略 3: 如果仍然失败，尝试按段落分割
        if not queries:
            logger.info("策略 2 失败，尝试策略 3：按段落分割")
            print(f"⚠️ 策略 2 解析失败，尝试策略 3...", flush=True)

            paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]
            for para in paragraphs[:num_queries]:
                # 取第一句作为查询
                sentences = para.split('.')
                if sentences:
                    queries.append({
                        'query': sentences[0].strip(),
                        'researchGoal': para[:200]  # 取前 200 字符作为目标
                    })

        # 确保所有查询都有 researchGoal
        for q in queries:
            if 'researchGoal' not in q or not q['researchGoal']:
                q['researchGoal'] = f"Research: {q['query']}"

        # 验证和日志
        if not queries:
            logger.error(f"❌ 无法从 LLM 响应中解析任何查询。完整响应: {response}")
            print(f"❌ 错误：未能从 LLM 响应中解析出查询！", flush=True)
            print(f"   模型: {self.researcher.cfg.strategic_llm_model}", flush=True)
            print(f"   提供商: {self.researcher.cfg.strategic_llm_provider}", flush=True)
        else:
            logger.info(f"✅ 成功解析 {len(queries)} 个查询")
            print(f"✅ 成功解析 {len(queries)} 个查询", flush=True)
            for i, q in enumerate(queries[:num_queries], 1):
                print(f"   {i}. 查询: {q['query'][:80]}...", flush=True)
                print(f"      目标: {q.get('researchGoal', 'N/A')[:80]}...", flush=True)

        return queries[:num_queries]

    async def generate_research_plan(self, query: str, num_questions: int = 3) -> List[str]:
        """Generate follow-up questions to clarify research direction"""
        try:
            # Get initial search results to inform query generation
            # Pass the researcher so MCP retriever receives cfg and mcp_configs
            search_results = await get_search_results(
                query,
                self.researcher.retrievers[0],
                researcher=self.researcher
            )
            logger.info(f"Initial web knowledge obtained: {len(search_results)} results")

            # Get current time for context
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            messages = [
                {"role": "system",
                 "content": "You are an expert researcher. Your task is to analyze the original query and search results, then generate targeted questions that explore different aspects and time periods of the topic."},
                {"role": "user",
                 "content": f"""Original query: {query}

Current time: {current_time}

Search results:
{search_results}

Based on these results, the original query, and the current time, generate {num_questions} unique questions. Each question should explore a different aspect or time period of the topic, considering recent developments up to {current_time}.

Format each question on a new line starting with 'Question: '"""}
            ]

            response = await create_chat_completion(
                messages=messages,
                llm_provider=self.researcher.cfg.strategic_llm_provider,
                model=self.researcher.cfg.strategic_llm_model,
                reasoning_effort=ReasoningEfforts.High.value,
                temperature=0.4
            )

            # 添加调试日志
            logger.debug(f"研究计划 LLM 响应 (前 500 字符): {response[:500]}")

            # 改进的解析逻辑
            import re
            questions = []

            # 策略 1: 查找 "Question:" 格式
            for line in response.split('\n'):
                line = line.strip()
                if re.match(r'^(Question|问题|\*\*Question\*\*|\d+\.\s*Question)[:\s：]', line, re.IGNORECASE):
                    question_text = re.sub(r'^(Question|问题|\*\*Question\*\*|\d+\.\s*Question)[:\s：]+', '', line,
                                           flags=re.IGNORECASE).strip()
                    question_text = question_text.strip('*').strip()
                    if question_text:
                        questions.append(question_text)

            # 策略 2: 如果没有找到，尝试提取编号列表
            if not questions:
                logger.info("研究计划策略 1 失败，尝试策略 2")
                numbered_items = re.findall(r'(?:^|\n)\s*(\d+)[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\Z)', response, re.DOTALL)
                for num, content in numbered_items[:num_questions]:
                    question_text = content.strip().split('\n')[0].strip()
                    if question_text:
                        questions.append(question_text)

            # 验证
            if not questions:
                logger.warning(f"无法从响应中解析问题，使用默认问题。响应: {response[:200]}")
                questions = [
                    f"What are the key aspects of {query}?",
                    f"What are recent developments in {query}?",
                    f"What are the implications of {query}?"
                ]
            else:
                logger.info(f"✅ 成功生成 {len(questions)} 个研究问题")

            return questions[:num_questions]

        except Exception as e:
            logger.error(f"生成研究计划时出错: {str(e)}", exc_info=True)
            print(f"⚠️ 生成研究计划失败，使用默认问题: {str(e)}", flush=True)
            # 返回默认问题
            return [
                f"What are the key aspects of {query}?",
                f"What are recent developments in {query}?",
                f"What are the implications of {query}?"
            ][:num_questions]

    async def process_research_results(self, query: str, context: str, num_learnings: int = 3) -> Dict[str, List[str]]:
        """Process research results to extract learnings and follow-up questions"""
        try:
            messages = [
                {"role": "system",
                 "content": "You are an expert researcher analyzing search results. You MUST format your response exactly as specified."},
                {"role": "user",
                 "content": f"""Given the following research results for the query '{query}', extract {num_learnings} key learnings and suggest {num_learnings} follow-up questions.

IMPORTANT - Your response MUST follow this EXACT format:

Learning: <first key insight from the research>
Learning: <second key insight from the research>
Learning: <third key insight from the research>

Question: <first follow-up question to explore further>
Question: <second follow-up question to explore further>
Question: <third follow-up question to explore further>

Rules:
1. Start each learning with "Learning:" (no numbers, no bullets, no markdown)
2. Start each question with "Question:" (no numbers, no bullets, no markdown)
3. Each item should be on its own line
4. Do not use "1.", "2.", "*", "-", or any other formatting
5. Keep learnings concise and factual
6. Make questions specific and actionable

Research results:
{context}"""}
            ]

            response = await create_chat_completion(
                messages=messages,
                llm_provider=self.researcher.cfg.strategic_llm_provider,
                model=self.researcher.cfg.strategic_llm_model,
                temperature=0.4,
                reasoning_effort=ReasoningEfforts.High.value,
                max_tokens=1000
            )

            # 添加调试日志
            logger.debug(f"处理研究结果 LLM 响应 (前 500 字符): {response[:500]}")
            print(f"\n📝 调试：处理研究结果的完整LLM响应:\n{'-' * 60}\n{response}\n{'-' * 60}\n", flush=True)

            lines = response.split('\n')
            learnings = []
            questions = []
            citations = {}

            import re

            # 策略 1: 标准格式解析 (Learning: ... / Question: ...)
            for line in lines:
                line = line.strip()
                # 解析 Learning
                if re.match(r'^(Learning|学习|\*\*Learning\*\*|\d+\.\s*Learning)', line, re.IGNORECASE):
                    url_match = re.search(r'\[(.*?)\]:', line)
                    if url_match:
                        url = url_match.group(1)
                        learning = line.split(':', 1)[1].strip() if ':' in line else line
                        learnings.append(learning)
                        citations[learning] = url
                    else:
                        # Try to find URL in the line itself
                        url_match = re.search(
                            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', line)
                        if url_match:
                            url = url_match.group(0)
                            learning = line.replace(url, '').replace('Learning:', '').strip()
                            learning = re.sub(r'^(Learning|学习|\*\*Learning\*\*|\d+\.\s*Learning)[:\s：]+', '',
                                              learning, flags=re.IGNORECASE).strip()
                            learnings.append(learning)
                            citations[learning] = url
                        else:
                            learning = re.sub(r'^(Learning|学习|\*\*Learning\*\*|\d+\.\s*Learning)[:\s：]+', '', line,
                                              flags=re.IGNORECASE).strip()
                            if learning:
                                learnings.append(learning)
                # 解析 Question
                elif re.match(r'^(Question|问题|\*\*Question\*\*|\d+\.\s*Question)', line, re.IGNORECASE):
                    question = re.sub(r'^(Question|问题|\*\*Question\*\*|\d+\.\s*Question)[:\s：]+', '', line,
                                      flags=re.IGNORECASE).strip()
                    if question:
                        questions.append(question)

            # 策略 2: 如果策略 1 失败，尝试提取编号列表格式
            if not learnings and not questions:
                logger.info("处理研究结果策略 1 失败，尝试策略 2：提取编号列表")
                print(f"⚠️ 处理研究结果策略 1 解析失败，尝试策略 2...", flush=True)

                # 尝试匹配编号列表
                numbered_items = re.findall(r'(?:^|\n)\s*(\d+)[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\Z)', response, re.DOTALL)

                # 前半部分作为 learnings，后半部分作为 questions
                mid_point = len(numbered_items) // 2
                for num, content in numbered_items[:mid_point]:
                    learning_text = content.strip().split('\n')[0].strip()
                    if learning_text:
                        learnings.append(learning_text)

                for num, content in numbered_items[mid_point:]:
                    question_text = content.strip().split('\n')[0].strip()
                    if question_text:
                        questions.append(question_text)

            # 策略 3: 如果仍然失败，尝试按段落分割
            if not learnings and not questions:
                logger.info("处理研究结果策略 2 失败，尝试策略 3：按段落分割")
                print(f"⚠️ 处理研究结果策略 2 解析失败，尝试策略 3...", flush=True)

                paragraphs = [p.strip() for p in response.split('\n\n') if p.strip()]

                # 前半部分作为 learnings
                mid_point = len(paragraphs) // 2
                for para in paragraphs[:mid_point]:
                    sentences = para.split('.')
                    if sentences:
                        learning_text = sentences[0].strip()
                        if learning_text:
                            learnings.append(learning_text)

                # 后半部分作为 questions
                for para in paragraphs[mid_point:]:
                    sentences = para.split('.')
                    if sentences:
                        question_text = sentences[0].strip()
                        if question_text:
                            questions.append(question_text)

            # 策略 4: 如果还是失败，尝试按句子分割
            if not learnings:
                logger.info("处理研究结果策略 3 失败，尝试策略 4：按句子分割提取学习内容")
                print(f"⚠️ 处理研究结果策略 3 解析失败，尝试策略 4（学习内容）...", flush=True)

                # 使用上下文的前几句作为学习内容
                context_sentences = context.split('.')[:num_learnings * 2]
                for s in context_sentences:
                    s = s.strip()
                    if s and len(s) > 20:  # 只保留有意义的句子
                        learnings.append(s)
                        if len(learnings) >= num_learnings:
                            break

            if not questions:
                logger.info("生成默认后续问题")
                print(f"⚠️ 无法提取后续问题，生成默认问题", flush=True)
                questions = [
                    f"What are the implications of these findings about {query}?",
                    f"What additional research is needed on {query}?",
                    f"How does this relate to broader trends in {query}?"
                ]

            # 最终验证
            if not learnings:
                logger.warning(f"所有策略失败，使用上下文摘要作为学习内容")
                print(f"⚠️ 所有策略失败，使用上下文摘要", flush=True)
                learnings = [context[:200]] if context else ["No learnings extracted from research"]

            logger.info(f"✅ 提取了 {len(learnings)} 个学习内容和 {len(questions)} 个后续问题")
            print(f"✅ 成功提取 {len(learnings)} 个学习内容和 {len(questions)} 个后续问题", flush=True)

            return {
                'learnings': learnings[:num_learnings],
                'followUpQuestions': questions[:num_learnings],
                'citations': citations
            }

        except Exception as e:
            logger.error(f"处理研究结果时出错: {str(e)}", exc_info=True)
            print(f"⚠️ 处理研究结果失败: {str(e)}", flush=True)
            # 返回基本结果
            return {
                'learnings': [context[:200]] if context else ["No learnings extracted"],
                'followUpQuestions': [f"What more can we learn about {query}?"],
                'citations': {}
            }

    async def deep_research(
            self,
            query: str,
            breadth: int,
            depth: int,
            learnings: List[str] = None,
            citations: Dict[str, str] = None,
            visited_urls: Set[str] = None,
            on_progress=None
    ) -> Dict[str, Any]:
        """Conduct deep iterative research"""
        print(f"\n📊 DEEP RESEARCH: depth={depth}, breadth={breadth}, query={query[:100]}...", flush=True)
        if learnings is None:
            learnings = []
        if citations is None:
            citations = {}
        if visited_urls is None:
            visited_urls = set()

        progress = ResearchProgress(depth, breadth)

        if on_progress:
            on_progress(progress)

        # Generate search queries
        print(f"🔎 Generating {breadth} search queries...", flush=True)
        try:
            serp_queries = await self.generate_search_queries(query, num_queries=breadth)
        except Exception as e:
            logger.error(f"生成搜索查询时出错: {str(e)}", exc_info=True)
            print(f"❌ 生成搜索查询失败: {str(e)}", flush=True)
            # 返回空结果而不是崩溃
            return {
                'learnings': [],
                'visited_urls': [],
                'citations': {},
                'context': [],
                'sources': []
            }

        print(f"✅ Generated {len(serp_queries)} queries: {[q['query'] for q in serp_queries]}", flush=True)

        # 验证查询结果
        if not serp_queries:
            logger.error(f"❌ 未能生成任何搜索查询！query={query[:100]}")
            print(f"❌ 错误：未能生成搜索查询，无法继续研究", flush=True)
            print(f"   请检查：", flush=True)
            print(f"   1. LLM 模型配置是否正确", flush=True)
            print(f"   2. API 密钥是否有效", flush=True)
            print(f"   3. 模型是否支持当前的提示格式", flush=True)
            # 返回空结果
            return {
                'learnings': [],
                'visited_urls': [],
                'citations': {},
                'context': [],
                'sources': []
            }

        progress.total_queries = len(serp_queries)

        all_learnings = learnings.copy()
        all_citations = citations.copy()
        all_visited_urls = visited_urls.copy()
        all_context = []
        all_sources = []

        # Process queries with concurrency limit
        semaphore = asyncio.Semaphore(self.concurrency_limit)

        async def process_query(serp_query: Dict[str, str]) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    progress.current_query = serp_query['query']
                    if on_progress:
                        on_progress(progress)

                    from .. import GPTResearcher
                    researcher = GPTResearcher(
                        query=serp_query['query'],
                        report_type=ReportType.ResearchReport.value,
                        report_source=ReportSource.Web.value,
                        tone=self.tone,
                        websocket=self.websocket,
                        config_path=self.config_path,
                        headers=self.headers,
                        visited_urls=self.visited_urls,
                        # Propagate MCP configuration to nested researchers
                        mcp_configs=self.researcher.mcp_configs,
                        mcp_strategy=self.researcher.mcp_strategy
                    )

                    # Conduct research
                    context = await researcher.conduct_research()

                    # Get results and visited URLs
                    visited = researcher.visited_urls
                    sources = researcher.research_sources

                    # Process results to extract learnings and citations
                    results = await self.process_research_results(
                        query=serp_query['query'],
                        context=context
                    )

                    # Update progress
                    progress.completed_queries += 1
                    progress.current_breadth += 1
                    if on_progress:
                        on_progress(progress)

                    return {
                        'learnings': results['learnings'],
                        'visited_urls': list(visited),
                        'followUpQuestions': results['followUpQuestions'],
                        'researchGoal': serp_query['researchGoal'],
                        'citations': results['citations'],
                        'context': context if context else "",
                        'sources': sources if sources else []
                    }

                except Exception as e:
                    import traceback
                    error_details = traceback.format_exc()
                    logger.error(f"Error processing query '{serp_query['query']}': {str(e)}")
                    print(f"\n❌ DEEP RESEARCH ERROR: {str(e)}\n{error_details}", flush=True)
                    return None

        # Process queries concurrently with limit
        tasks = [process_query(query) for query in serp_queries]
        results = await asyncio.gather(*tasks)
        results = [r for r in results if r is not None]

        # Update breadth progress based on successful queries
        progress.current_breadth = len(results)
        if on_progress:
            on_progress(progress)

        # Collect all results
        for result in results:
            all_learnings.extend(result['learnings'])
            all_visited_urls.update(result['visited_urls'])
            all_citations.update(result['citations'])
            if result['context']:
                all_context.append(result['context'])
            if result['sources']:
                all_sources.extend(result['sources'])

            # Continue deeper if needed
            if depth > 1:
                new_breadth = max(2, breadth // 2)
                new_depth = depth - 1
                progress.current_depth += 1

                # Create next query from research goal and follow-up questions
                next_query = f"""
                Previous research goal: {result['researchGoal']}
                Follow-up questions: {' '.join(result['followUpQuestions'])}
                """

                # Recursive research
                deeper_results = await self.deep_research(
                    query=next_query,
                    breadth=new_breadth,
                    depth=new_depth,
                    learnings=all_learnings,
                    citations=all_citations,
                    visited_urls=all_visited_urls,
                    on_progress=on_progress
                )

                all_learnings = deeper_results['learnings']
                all_visited_urls.update(deeper_results['visited_urls'])
                all_citations.update(deeper_results['citations'])
                if deeper_results.get('context'):
                    all_context.extend(deeper_results['context'])
                if deeper_results.get('sources'):
                    all_sources.extend(deeper_results['sources'])

        # Update class tracking
        self.context.extend(all_context)
        self.research_sources.extend(all_sources)

        # Trim context to stay within word limits
        trimmed_context = trim_context_to_word_limit(all_context)
        logger.info(
            f"Trimmed context from {len(all_context)} items to {len(trimmed_context)} items to stay within word limit")

        return {
            'learnings': list(set(all_learnings)),
            'visited_urls': list(all_visited_urls),
            'citations': all_citations,
            'context': trimmed_context,
            'sources': all_sources
        }

    async def run(self, on_progress=None) -> str:
        """Run the deep research process and generate final report"""
        print(
            f"\n🔍 DEEP RESEARCH: Starting with breadth={self.breadth}, depth={self.depth}, concurrency={self.concurrency_limit}",
            flush=True)
        start_time = time.time()

        # Log initial costs
        initial_costs = self.researcher.get_costs()

        follow_up_questions = await self.generate_research_plan(self.researcher.query)
        answers = ["Automatically proceeding with research"] * len(follow_up_questions)

        qa_pairs = [f"Q: {q}\nA: {a}" for q, a in zip(follow_up_questions, answers)]
        combined_query = f"""
        Initial Query: {self.researcher.query}\nFollow - up Questions and Answers:\n
        """ + "\n".join(qa_pairs)

        results = await self.deep_research(
            query=combined_query,
            breadth=self.breadth,
            depth=self.depth,
            on_progress=on_progress
        )

        # Get costs after deep research
        research_costs = self.researcher.get_costs() - initial_costs

        # Log research costs if we have a log handler
        if self.researcher.log_handler:
            await self.researcher._log_event("research", step="deep_research_costs", details={
                "research_costs": research_costs,
                "total_costs": self.researcher.get_costs()
            })

        # Prepare context with citations
        context_with_citations = []
        for learning in results['learnings']:
            citation = results['citations'].get(learning, '')
            if citation:
                context_with_citations.append(f"{learning} [Source: {citation}]")
            else:
                context_with_citations.append(learning)

        # Add all research context
        if results.get('context'):
            context_with_citations.extend(results['context'])

        # Trim final context to word limit
        final_context = trim_context_to_word_limit(context_with_citations)

        # Set enhanced context and visited URLs
        self.researcher.context = "\n".join(final_context)
        self.researcher.visited_urls = results['visited_urls']

        # Set research sources
        if results.get('sources'):
            self.researcher.research_sources = results['sources']

        # Log total execution time
        end_time = time.time()
        execution_time = timedelta(seconds=end_time - start_time)
        logger.info(f"Total research execution time: {execution_time}")
        logger.info(f"Total research costs: ${research_costs:.2f}")

        # Return the context - don't generate report here as it will be done by the main agent
        return self.researcher.context