Write a diagnostic report in XML-tagged Markdown format and generate structured outputs.

Use this tool when:
- You have completed analysis and want to write the final report
- You have identified one or more root causes (P1, P2, etc.)
- You have built evidence chains and timelines
- You want to generate both human-readable and machine-readable outputs

The report should follow the XML-tagged Markdown format.
This tool will parse the XML tags and generate:
- report.json: Complete structured data
- summary.md: Human-readable summary
- timeline.md: Standalone timeline (if present)
- diagnosis_P1.md, diagnosis_P2.md: Individual problem reports
- evidence_chain_P1.md, evidence_chain_P2.md: Evidence chains per problem

**report format**:
```markdown
<report>
<summary>
## 1. 问题总览

- P1：{{问题简述 + 时间 + 根因描述+ 置信度（简要理由）}}
- P2：{{...}}

### 完整时间线
{{使用【时间线】模版}}
</summary>

<timeline>
{{如果summary中未包含完整时间线，在此处使用【时间线】模版}}
</timeline>

<diagnosis_list>
<diagnosis>
<title>
### 2.1 P1：{{问题名称}}
</title>

<conclusion>
#### 2.1.1 诊断结论
- 根因：{{根因描述}}
- 置信度：高/中/低（简要理由）
</conclusion>

<confidence>高/中/低</confidence>
<confidence_score>0.0-1.0</confidence_score>
<root_cause_level>L1/L2/L3</root_cause_level>
<root_cause_score>数值</root_cause_score>

<reproduction_path>
#### 2.1.2 复现路径
（使用【复现路径】模板）
</reproduction_path>

<timeline>
#### 2.1.3 时间轴
（使用【时间轴】模板）
</timeline>

<evidence_chain>
#### 2.1.4 证据链
（使用【证据链】模板）
</evidence_chain>

<alternative_causes>
#### 2.1.6 其他可能原因
如果有多个，按置信度和根因深度从高到低列举

<alternative_cause>
<hypothesis>备选假设 H2：{{描述}}</hypothesis>
<confidence>中/低</confidence>
<confidence_score>数值</confidence_score>
<root_cause_level>L1/L2/L3</root_cause_level>
<root_cause_score>得分</root_cause_score>
<exclusion_reason>被排除/尚未完全排除的原因</exclusion_reason>
</alternative_cause>

</alternative_causes>
</diagnosis>

<diagnosis>
<title>
### 2.2 P2：{{问题名称}}
</title>

<conclusion>
#### 2.2.1 诊断结论
- 根因：{{根因描述}}
- 置信度：高/中/低（简要理由）
</conclusion>

<confidence>高/中/低</confidence>
<confidence_score>0.0-1.0</confidence_score>
<root_cause_level>L1/L2/L3</root_cause_level>
<root_cause_score>数值</root_cause_score>

<reproduction_path>
#### 2.2.2 复现路径
（使用【复现路径】模板）
</reproduction_path>

<timeline>
#### 2.2.3 时间轴
（使用【时间轴】模板）
</timeline>

<evidence_chain>
#### 2.2.4 证据链
（使用【证据链】模板）
</evidence_chain>

<alternative_causes>
<!-- 如果有其他可能原因，在此处添加 -->
</alternative_causes>
</diagnosis>
</diagnosis_list>

<cross_analysis>
## 3. 跨问题综合分析（可选，如果多个 Px 共享根因）

- 说明共享根因 Hx 如何分别传导到 P1、P2…
- 若部分子问题无法被统一解释，需明确指出
</cross_analysis>

<recommendations>
## 4. 后续建议与待确认事项

- [ ] 需用户/团队确认的关键问题
- [ ] 需要补充的日志/监控/配置
- [ ] 推荐的系统性改进措施
</recommendations>

<metadata>
<diagnosis_date>{{实际诊断日期 (ISO 8601格式)}}</diagnosis_date>
<review_count>{{实际评审次数}}</review_count>
<review_result>通过|未通过|N/A</review_result>
<review_summary>{{Review结论简述}}</review_summary>
<knowledge_keys>
<key>{{知识Key}}</key>
</knowledge_keys>
<attachment_paths>
<path>{{附件路径}}</path>
</attachment_paths>
<code_paths>
<path>{{代码路径}}</path>
</code_paths>
</metadata>
</report>

```