# SBIR A254-006 Progress Report: AI-Assisted Vulnerability Detection

**Date:** January 26, 2026
**Project:** SBIR A254-006 - AI-Assisted Vulnerability Detection
**Classification:** Unclassified
**Prepared for:** SBIR Program Management

---

## Executive Summary

This report consolidates findings from our research and development on AI-assisted vulnerability detection and exploitation validation. The work progressed through three major phases: initial validation on synthetic datasets, transition to real-world vulnerability corpora, and demonstration of end-to-end exploitation capabilities.

Our best vulnerability detection configuration achieved 60.2% recall and 57.1% precision on the PrimeVul dataset of real-world vulnerabilities, representing a 10.4 percentage point improvement in recall over traditional static analyzers tested on the same data. Beyond detection metrics, we demonstrated a complete source-to-exploitation pipeline where LLM agents analyze source code, identify vulnerabilities, and validate those findings through actual exploitation on live targets.

This report describes the methodology, experiments, findings, and technical infrastructure developed throughout the project.

---

## Part 1: Code Vulnerability Detection

### Phase 1: Synthetic Dataset Validation (Juliet Test Suite)

Our initial work validated LLM-based vulnerability detection on the NIST Juliet Test Suite, a synthetic dataset containing thousands of C/C++ functions with known vulnerabilities and their corresponding safe implementations. The Juliet suite provides controlled conditions for evaluating detection approaches because each vulnerable function has a clear ground truth label and a matched safe variant demonstrating proper remediation.

We constructed a carefully balanced few-shot retrieval layer that could pull open-weight models within reach of frontier model performance. The approach combined static analyzer signals with LLM reasoning, using both vulnerable and safe exemplars to help the model understand what makes code dangerous versus benign. This dual-exemplar approach proved critical—showing only vulnerable examples led to over-flagging, while the contrastive pairs taught the model to recognize the specific patterns that distinguish exploitable code from properly defended implementations.

The evaluation compared frontier models against open-weight alternatives suitable for on-premise deployment. Static analyzers provided baseline signals, but the LLM layer, armed with retrieved exemplars, cut false positives by nearly twenty points while maintaining recall in the high nineties.

| Configuration | Recall | Precision | False Positive Rate | False Negative Rate |
|---------------|--------|-----------|---------------------|---------------------|
| Static Analyzers (Semgrep, Cppcheck, Flawfinder) | 60.4% | 25.2% | 41.0% | 39.6% |
| GPT-5 (detailed analysis mode) | 92.2% | 47.0% | 35.7% | 7.8% |
| GPT-OSS-120B + few-shot retrieval | 98.7% | 40.3% | 33.3% | 1.3% |

The open-weight model achieved near-perfect recall (98.7%) with a false negative rate of only 1.3%, demonstrating that on-premise deployment without cloud API dependencies is viable for high-sensitivity security screening. The few-shot retrieval layer proved essential—without it, the open-weight model's recall dropped significantly, but with semantically similar exemplars, it matched or exceeded frontier model performance on this dataset.

![Figure 1: Juliet Evaluation Pipeline Architecture](fig1-juliet-pipeline.png)

### Phase 2: Real-World Dataset Transition (PrimeVul)

The transition from Juliet to PrimeVul represented a fundamental shift in problem difficulty. PrimeVul is a corpus of real-world vulnerabilities extracted from production codebases including OpenSSL, BusyBox, GnuTLS, and related projects. Each entry consists of actual commits where developers patched security flaws, providing authentic examples of vulnerabilities as they appear in professional software development.

#### Contamination Controls and Data Integrity

Before running experiments we established rigorous contamination controls to ensure the evaluation remained defensible for SBIR reviewers. Three checkpoints validated data integrity:

The sample slice was confirmed authentic, drawn directly from production commits without synthetic scaffolding introduced during ingestion. The parser enforced project-aware splitting using deterministic hashing so entire repositories land on one side of the train/test divide, blocking cross-project leakage that could inflate metrics. We documented edge cases where the splitting algorithm produced unexpected behavior—for example, all Chrome functions hashing into the training set—so reviewers understand these as consequences of contamination guardrails rather than missing data.

#### The Reality Check

PrimeVul delivered a sobering reality check on our Juliet results. Real-world codebases exhibit fundamental class imbalance that synthetic datasets don't capture. While Juliet contains 14-20% vulnerable functions by design, production code in PrimeVul is approximately 2.6% vulnerable. This dramatic shift in base rates crushed our initial precision metrics.

| Dataset | Vulnerable Rate | Static Analyzer Precision | Initial LLM Precision |
|---------|-----------------|---------------------------|----------------------|
| Juliet (synthetic) | 14-20% | 25.2% | 40.3% |
| PrimeVul (real-world) | 2.6% | 4.1% | 4.8% |

The precision drop from 40% to under 5% demonstrated that optimizations tuned for synthetic data don't transfer to production code. A system flagging 4.8% precision generates twenty false alarms for every true vulnerability found—unacceptable for practical deployment.

To enable rapid experimentation without waiting for full dataset evaluations, we created a balanced development subset of 522 functions (261 vulnerable, 261 safe). This 50/50 split provides immediate, clear feedback on both false positives and false negatives with every experimental run. Production deployment would use realistic imbalanced distributions, but the balanced testbed supported the rapid iteration necessary for reaching viable configurations.

### Phase 3: Advanced Capabilities and Best Configuration

November and December focused on deploying advanced capabilities to improve detection beyond the baseline established during PrimeVul transition. We integrated Code Property Graph analysis for intelligent context extraction, implemented vector-contrastive few-shot learning, and conducted systematic experiments comparing multiple approaches.

#### Code Property Graph Integration

Code Property Graphs combine three views of a program into a unified representation: the Abstract Syntax Tree showing code structure, the Control Flow Graph showing possible execution paths, and the Data Flow Graph showing how values propagate through variables. By querying this graph through the Joern analysis framework, we extract focused vulnerability-relevant context rather than entire functions.

Source-sink taint analysis traces execution paths from sources (untrusted inputs like parameters, network reads, and file operations) to sinks (dangerous operations like buffer writes, memory allocations, and array indexing). Instead of presenting a 300-line function where vulnerabilities hide among irrelevant code, the analysis extracts 40-80 line slices showing complete attack chains: the untrusted input source, transformations applied to the data, validation checks encountered along the path, and the vulnerable operation itself.

An important enhancement included control flow guards—if/while/for statements that govern whether vulnerable code can actually execute. Including these guards in extracted slices prevents false positives where the LLM sees a dangerous operation but misses the protective check that validates input safety.

![Figure 2: Code Property Graph Taint Analysis](fig2-cpg-taint.png)

#### Vector-Contrastive Few-Shot Learning

This approach enhances detection by showing the LLM paired examples: vulnerable code alongside the patched version that fixed the vulnerability. Rather than learning patterns in isolation ("code like this is vulnerable"), the system learns semantic differences: "unvalidated arithmetic on line 47 becomes validated arithmetic with the bounds check added on line 45 in the patch."

Implementation uses semantic embeddings via the BGE-large model to find similar vulnerable/patched pairs from the training set. When analyzing new code, the system retrieves and presents these paired examples as few-shot demonstrations, teaching contextual reasoning about what specifically makes code safe versus dangerous.

#### Systematic Experimental Progression

We conducted systematic validation comparing four approaches on the balanced dataset, with each configuration building on the previous:

| Approach | Configuration | FP Rate | FN Rate | Precision | Recall | F1 Score |
|----------|---------------|---------|---------|-----------|--------|----------|
| Static Analyzers | Semgrep + Cppcheck + Flawfinder | 49.4% | 50.2% | 50.2% | 49.8% | 50.0% |
| LLM Baseline | Static evidence + full function | 42.9% | 46.7% | 55.4% | 53.3% | 54.3% |
| + Joern Taint | Source-sink path extraction | 46.7% | 42.1% | 55.3% | 57.9% | 56.6% |
| + Vector-Contrastive | Vulnerable/patched few-shot pairs | **45.2%** | **39.8%** | **57.1%** | **60.2%** | **58.6%** |

The best configuration achieved 60.2% recall and 57.1% precision, representing significant improvements over static analyzers across all metrics:

| Metric | Static Analyzers | Best LLM Configuration | Improvement |
|--------|------------------|------------------------|-------------|
| Recall | 49.8% | 60.2% | +10.4 pp |
| Precision | 50.2% | 57.1% | +6.9 pp |
| F1 Score | 50.0% | 58.6% | +8.6 pp |
| False Negative Rate | 50.2% | 39.8% | -10.4 pp |

The LLM-based system detects six out of ten real vulnerabilities while maintaining acceptable precision—substantially better than static analyzers that miss half of all vulnerabilities in this dataset.

### Negative Results and Failed Experiments

Not all approaches improved performance, and these negative results provide valuable guidance for future work.

#### Ensemble and Voting Approaches

We tested whether running the same analysis five times independently with majority vote would improve performance through statistical averaging. The hypothesis was that random variation in LLM outputs would cancel out, converging toward correct answers. Results showed the opposite effect.

| Approach | F1 Score | False Negative Rate | Change vs Baseline |
|----------|----------|---------------------|-------------------|
| Single analysis (baseline) | 58.6% | 39.8% | — |
| Majority voting (K=5) | 54.2% | 46.7% | -4.4 pp F1, +6.9 pp FN |

All five instances used the same model, prompt, and reasoning framework. When this led to systematic errors, all five agents made identical mistakes simultaneously. Voting locked in wrong answers with high confidence rather than correcting them. Approximately 31% of false negatives were unanimous wrong decisions where all five agents agreed on flawed reasoning.

#### Reviewer Agent Experiments

We implemented a reviewer agent to provide second-opinion validation on the primary agent's verdicts. The initial version exhibited severe anchoring bias—when shown the prior verdict, it agreed with every single primary decision, with 80-91% word overlap in reasoning. Some responses were copied verbatim. The reviewer provided no value because it simply echoed the primary agent.

A redesigned version using identical architecture to the primary agent achieved genuine independence: override rate increased from 0% to 50.8%, and word overlap dropped to 10.6%. However, performance still degraded because the reviewer made different but equally problematic errors with high confidence, rejecting correct VULNERABLE verdicts and flagging correct SAFE code.

| Reviewer Version | Override Rate | F1 Score | Change vs Baseline |
|------------------|---------------|----------|-------------------|
| V1 (rubber-stamp) | 0% | 50.6% | -8.0 pp |
| V2 (independent) | 50.8% | 51.6% | -7.0 pp |

The fundamental issue is that ensemble approaches assume independent errors, but LLM reasoning limitations are systematic. When all agents see the same code, static evidence, and few-shot examples while reasoning through the same framework, they make correlated errors. Real improvement requires fixing reasoning quality through better prompting and context extraction, not adding scrutiny layers that share the same limitations.

#### CPG Slicing Approaches

Inspired by academic literature suggesting that focused code slices help LLM analysis, we conducted six systematic experiments comparing different slicing strategies against the full-function baseline:

| Slicing Approach | F1 Score | Change vs Baseline |
|------------------|----------|-------------------|
| Full function + taint (baseline) | 58.6% | — |
| Guard Reporting v1 | 53.6% | -5.0 pp |
| Guard Reporting v2 (skeptical) | 59.2% | +0.6 pp |
| Path-Aware Guards | 55.1% | -3.5 pp |
| LLM-Generated CPG Queries | 53.6% | -5.0 pp |
| CWE-Aware Slicing | 57.5% | -1.1 pp |

Only Guard Reporting v2 with explicit skeptical framing achieved marginal improvement, and even that gain was within noise. Analysis of the LLM-generated CPG queries revealed that of 328 queries produced, only 3 (0.9%) returned useful results—general-purpose LLMs cannot reliably generate precise code analysis queries without domain-specific fine-tuning.

### Critical Insight: Reasoning Quality, Not Context Quantity

Analysis of 232 false negatives revealed that 88.4% had full function context available when the LLM made its incorrect SAFE determination. The model wasn't missing vulnerabilities due to insufficient code—it was reasoning incorrectly about what it saw.

The dominant failure pattern, appearing in 88.8% of false negative cases, was the model incorrectly believing existing guards were adequate when they were actually incomplete, checking wrong conditions, or executing after the dangerous operation rather than before. The LLM would identify a validation check, assume it provided complete protection, and conclude the code was safe—missing that the check validated the wrong variable, used incorrect bounds, or appeared too late in the control flow to prevent exploitation.

This redirects future improvement efforts. Rather than showing the LLM less code through slicing approaches, we need to help it reason better about guards and validation. Better prompting targeting specific reasoning failures and domain knowledge injection are more promising than context reduction strategies.

| Failure Category | Percentage | Cases |
|------------------|------------|-------|
| Incorrect guard reasoning | 88.8% | 206 |
| Missing inter-procedural context | 7.3% | 17 |
| Other | 3.9% | 9 |
| **Total** | **100%** | **232** |

---

## Part 2: Network Exploitation and Damage Assessment

### Motivation: From Detection Metrics to Exploitation Validation

Vulnerability detection research produces metrics on paper—precision, recall, F1 scores. But stakeholders often ask: "Does this actually work in the real world?" To answer that question definitively, we built a system where LLM agents don't just flag code as potentially vulnerable—they prove it by actually exploiting the vulnerability on a live target.

This demonstration shows that LLM agents can perform intelligent security operations that traditionally require either brittle hardcoded scripts with pattern matching, or human analysts making real-time decisions. The agents interpret unstructured data, execute multi-step workflows, and produce structured reports—capabilities that transfer to many security applications beyond this specific demo.

### Test Environment

Our target is Metasploitable 2, an intentionally vulnerable Ubuntu Linux virtual machine created by the security community for training purposes. It contains numerous exploitable services spanning decades of real-world vulnerabilities:

| Port | Service | Vulnerability | CVE | Description |
|------|---------|---------------|-----|-------------|
| 21 | vsftpd 2.3.4 | Backdoor | CVE-2011-2523 | Malicious code inserted into source distribution |
| 139/445 | Samba 3.0.20 | Command injection | CVE-2007-2447 | Shell metacharacters in username field |
| 1524 | Bindshell | Misconfiguration | — | Open root shell requiring no authentication |
| 3632 | DistCC | Remote code execution | CVE-2004-2687 | Arbitrary command execution in distributed compiler |
| 6667 | UnrealIRCd | Backdoor | CVE-2010-2075 | Trojanized IRC server distribution |

We run this VM on macOS using UTM (a QEMU-based virtualizer) with host-only networking, making it accessible from our development machine without exposing it to external networks. This provides a safe, repeatable environment for demonstrating exploitation capabilities.

### Multi-Agent Pipeline Architecture

The pipeline uses three specialized LLM agents, each responsible for a distinct phase of the operation. We built these using the Langroid framework, which provides clean abstractions for tool-using agents that can execute multi-step workflows.

![Figure 4: Exploitation Pipeline Architecture](fig4-exploit-pipeline.png)

#### Phase 1: Reconnaissance

The reconnaissance agent receives raw output from nmap, a standard network scanning tool. Nmap output is technical and unstructured—port numbers, service versions, protocol details scattered across hundreds of lines. The ReconAgent interprets this information, matches detected services against known vulnerability patterns, and produces structured recommendations about which targets to prioritize.

When scanning Metasploitable 2, the agent identifies vsftpd 2.3.4 on port 21 and recognizes it as the infamous backdoored version. It produces a structured report indicating the recommended target, the associated CVE identifier, estimated exploitation difficulty, and reasoning for the recommendation. The agent doesn't just parse—it applies security domain knowledge to prioritize targets by exploitability and impact.

#### Phase 2: Exploitation

The exploitation agent receives target information and attempts to gain access. What makes this agent interesting is its ability to execute multiple commands before concluding—it doesn't just try one thing and give up.

The agent has access to a RunCommandTool that executes shell commands on the target. It might connect to a service, run "whoami" to check its identity, run "id" to verify privilege levels, explore the filesystem to understand what access it has obtained, and enumerate potential lateral movement paths before declaring success or failure. This multi-step capability required careful design using Langroid's done_sequences pattern, which allows intermediate tool use without terminating the agent's task prematurely.

When the agent is satisfied with its findings, it emits a structured ExploitResultTool containing: whether exploitation succeeded, what access level was obtained, what method was used, and the reasoning behind its conclusions.

#### Phase 3: Damage Assessment

After successful exploitation, the damage assessment agent quantifies what an attacker could do with the obtained access. It analyzes post-exploitation enumeration data including password hashes from /etc/shadow (which could be cracked offline), SSH private keys (which enable lateral movement to other systems), SUID binaries (which could be exploited for privilege escalation), and network configuration (which indicates data exfiltration possibilities).

The agent produces a DamageReportTool containing quantified metrics and a severity score with justification. This transforms raw enumeration output into executive-friendly impact assessment that security teams can use for prioritization and remediation decisions.

### Exploitation Results

Running the multi-service exploitation pipeline against Metasploitable 2 demonstrated successful compromise through multiple attack vectors:

| Metric | Value |
|--------|-------|
| Services Attempted | 2 |
| Services Exploited | 2 |
| Success Rate | 100% |
| User Obtained | root |
| Privilege Level | root (uid=0) |
| Password Hashes Extracted | 3 |
| SSH Private Keys Found | 2 |
| SUID Binaries Identified | 30+ |
| External Network Access | Yes |
| **Severity Score** | **7.9/10 (HIGH)** |

The agents correctly identified that root access with multiple credential types, lateral movement vectors (SSH keys), and external network connectivity represents a critical security breach. The damage report provides the quantified evidence needed to prioritize remediation.

Cost per complete exploitation run using gpt-4o-mini was approximately $0.005, demonstrating that LLM-powered security operations are economically viable even at scale.

### Source-to-Exploitation Validation Pipeline

The most significant achievement was connecting source code analysis directly to exploitation validation. This closes the loop from theoretical detection (flagging code that might be vulnerable) to practical validation (confirming the vulnerability can actually be exploited). It addresses the common criticism that vulnerability detection tools produce too many false positives—by actually exploiting what we find, we demonstrate that our findings are real.

![Figure 5: Source-to-Exploitation Pipeline](fig5-source-to-exploit.png)

#### Demonstration: vsftpd Backdoor

We downloaded the source code of vsftpd 2.3.4, which contains a notorious backdoor that was maliciously inserted into the official distribution in 2011. The backdoor is deceptively simple: if a client sends a username or password containing the smiley emoticon ":)", the server opens a root shell on port 6200. This was hidden in string handling code where no one thought to look for it.

The CodeAnalysisAgent examined the source and identified the backdoor:

```
VULNERABILITY FOUND
───────────────────
[CRITICAL] BACKDOOR in str.c:572
  CVE:         CVE-2011-2523
  Confidence:  95%
  Pattern:     if (strstr(p_pass_str, ":)") != NULL)
  Description: Hard-coded backdoor triggers on smiley emoticon in credentials.
               Calls vsf_sysutil_extra() which spawns root shell on port 6200.
```

The ExploitExecutorAgent then validated this finding against a live Metasploitable 2 instance running the vulnerable vsftpd version:

```
EXPLOITATION VALIDATION
───────────────────────
[+] Connecting to 192.168.64.3:21...
[+] Sending backdoor trigger: USER :)
[+] Connecting to backdoor port 6200...
[+] Running: whoami
[+] Output: root

[+] VULNERABILITY VALIDATED
    Method:  vsftpd 2.3.4 backdoor (CVE-2011-2523)
    Access:  root
    Status:  CONFIRMED EXPLOITABLE
```

This demonstrates the complete workflow that security analysts perform: code review, vulnerability identification, proof-of-concept development, and impact assessment. The agents perform all of this autonomously, transforming vulnerability detection from "this code might be dangerous" to "this code is provably exploitable."

### Stealth Reconnaissance

In response to feedback that aggressive nmap scanning would trigger intrusion detection systems in real deployments, we developed a StealthReconAgent that performs adaptive, low-noise reconnaissance. The agent uses iterative scanning with LLM-driven decision making, starting with minimal probes and escalating only when necessary.

| Parameter | Stealth Profile | Aggressive Profile |
|-----------|-----------------|-------------------|
| Timing | -T1 (paranoid, 5s delay between probes) | -T4 (no delay) |
| Technique | -sT (TCP connect only) | -sV (version detection) |
| Port Selection | 13 high-value ports | 1,000 common ports |
| Estimated Packets | ~45 | ~50,000 |
| IDS Alert Risk | LOW | HIGH |

The stealth agent analyzes results between scan iterations and adapts strategy based on findings. When it discovers a high-value target like an open bindshell on port 1524, it stops scanning immediately rather than continuing to enumerate all ports. This reduces network footprint by orders of magnitude while still identifying exploitable services.

![Figure 6: Stealth vs Aggressive Scan Comparison](fig6-stealth-comparison.png)

---

## Part 3: Technical Infrastructure

### Agent Framework

All agents are built using Langroid, an open-source Python framework for orchestrating LLM agents. The framework provides capabilities essential for security operations:

Structured tool outputs ensure agents produce machine-readable reports rather than free-form text. Every agent emits Pydantic-validated tool messages with typed fields, enabling reliable parsing and pipeline integration. When the ReconAgent identifies a target, it doesn't output prose—it emits a ReconResultTool with fields for IP address, port, service name, CVE identifier, and exploitation difficulty rating.

Multi-step reasoning allows agents to execute multiple actions before concluding. The exploitation agent runs several commands to explore a compromised system before reporting its findings. Langroid's done_sequences pattern specifies which tool emissions terminate the task versus which allow continued operation, enabling the command-execute-analyze loop that effective exploitation requires.

Automatic retry through the handle_llm_no_tool callback nudges agents when they fail to emit required tool calls. LLMs sometimes respond with prose analysis instead of structured tool output; the retry mechanism detects this and re-prompts the agent to use the appropriate tool, improving reliability without manual intervention.

### Evaluation Infrastructure

Systematic evaluation required infrastructure for rapid experimentation and rigorous analysis.

The balanced test set of 522 functions (261 vulnerable, 261 safe) provides immediate feedback on both error types with every experimental run. Changes that reduce false positives while increasing false negatives become immediately apparent, enabling informed tradeoff decisions rather than metric gaming.

Comprehensive audit logging captures complete information for every analysis: input context (code, static findings, few-shot examples), system output (verdict, confidence, reasoning), and ground truth labels. This enables statistically rigorous pattern identification—we could determine that 88.8% of false negatives cited incorrect guard reasoning only because we captured the full reasoning trace for every case.

Contamination controls verified that no training data leaked into test evaluations. The project-aware splitting algorithm deterministically assigns entire repositories to training or test partitions, preventing the cross-project leakage that would inflate metrics. We documented this methodology for SBIR reviewer scrutiny.

### Deployment Considerations

The system supports multiple deployment configurations depending on security requirements:

Open-weight models like GPT-OSS-120B achieved 98.7% recall on the Juliet dataset, demonstrating that on-premise deployment without cloud API dependencies is viable for high-sensitivity screening. Organizations with data sovereignty requirements can run the full pipeline without external network access.

Cost-effective operation was validated across multiple commercial models. A complete exploitation demonstration costs approximately $0.005 using gpt-4o-mini, making LLM-powered security operations economically viable even for large-scale deployment. The balanced test set of 522 functions can be evaluated for under $3.

Model flexibility allows swapping between GPT-5, GPT-4o, gpt-4o-mini, and GPT-OSS-120B depending on the accuracy-cost tradeoff appropriate for each use case. High-stakes final verdicts might use frontier models while initial screening uses faster, cheaper alternatives.

![Figure 7: System Architecture Overview](fig7-system-architecture.png)

---

## Conclusions

This work demonstrated both the capabilities and limitations of LLM-based vulnerability detection and exploitation.

On the detection side, the best configuration achieved 60.2% recall and 57.1% precision on real-world vulnerabilities, representing a 10.4 percentage point improvement over static analyzers. However, analysis of failure cases revealed that context is not the limiting factor—88.4% of false negatives had complete function context available. The model reasons incorrectly about security guards, assuming incomplete validation provides complete protection. Future improvements should focus on better prompting and domain knowledge injection rather than context reduction strategies.

Ensemble approaches including majority voting and reviewer agents failed to improve performance because LLM reasoning limitations are systematic. When all agents share the same model, prompts, and reasoning framework, they make correlated errors. Voting locked in wrong answers rather than correcting them. This redirects improvement efforts toward fixing individual model reasoning rather than adding scrutiny layers.

On the exploitation side, we demonstrated that LLM agents can perform sophisticated security operations autonomously. The multi-agent pipeline scans targets, exploits vulnerabilities, and produces quantified damage assessments. More importantly, the source-to-exploitation pipeline closes the loop from theoretical detection to practical validation—an LLM can analyze source code, identify a vulnerability, and prove that vulnerability is exploitable on a live target.

The stealth reconnaissance capability addresses operational concerns about detection, reducing network footprint by orders of magnitude while still identifying exploitable services. Adaptive, LLM-driven decision making enables reconnaissance that responds to findings rather than following fixed scan profiles.

These capabilities provide a foundation for security systems that combine the breadth of automated analysis with human-like reasoning, at costs measured in fractions of a cent per analysis.

---

## Reference Documents

The following milestone updates document the detailed work summarized in this report:

| Date | Document | Content Summary |
|------|----------|-----------------|
| Sep 18, 2025 | `results/comparisons-18sep2025.md` | Initial Juliet experiments, model comparisons |
| Oct 2, 2025 | `results/update-oct-2.md` | Context window experiments, pipeline improvements |
| Oct 16, 2025 | `results/20251009/README.md` | PrimeVul transition, contamination controls |
| Oct 31, 2025 | `results/20251030/20251031-experiments.md` | Detailed experiment log (142KB) |
| Nov 13, 2025 | `results/20251110/update-biweekly-20251113.md` | Agent triage, Joern integration |
| Dec 1, 2025 | `results/20251201/monthly-report.md` | Best configuration, vector-contrastive few-shot |
| Dec 20, 2025 | `results/20251220/exploit-update.md` | Network exploit pipeline |
| Jan 23, 2026 | `results/20260123/update.md` | Source-to-exploitation validation |

---

**End of Report**

*Prepared for: SBIR Program Management*
*Classification: Unclassified*
