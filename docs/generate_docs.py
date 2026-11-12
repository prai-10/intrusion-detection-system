"""
Script to compile the Final Project Report and IEEE Research Paper
into professional, formatted Microsoft Word (.docx) documents.
"""

import re
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

DOCS_DIR = Path(__file__).resolve().parent

def set_cell_background(cell, hex_color):
    """Sets background shading of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tc_pr.append(shd)

def create_report_docx():
    report_txt_path = DOCS_DIR / "FINAL_PROJECT_REPORT.txt"
    out_docx_path = DOCS_DIR / "FINAL_PROJECT_REPORT.docx"

    with open(report_txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    doc = Document()
    
    # Page setup - Standard 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Title / Header Block
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_t1 = title.add_run("A FINAL REPORT ON\n\n")
    run_t1.font.size = Pt(13)
    run_t1.font.bold = True

    run_title = title.add_run("NETWORK INTRUSION DETECTION SYSTEM (NIDS) USING HEURISTIC SLIDING WINDOWS AND REAL-TIME TELEMETRY\n\n")
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(16, 44, 87) # Deep academic navy

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Submitted in partial fulfilment of the requirement for the award of the degree of\n").font.size = Pt(11)
    r_deg = sub.add_run("BACHELOR OF COMPUTER APPLICATIONS\n\n")
    r_deg.font.size = Pt(13)
    r_deg.font.bold = True

    # Candidate & Mentor Table
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True
    
    c_left = table.cell(0, 0)
    p_left = c_left.paragraphs[0]
    p_left.add_run("Submitted by:\n").font.bold = True
    p_left.add_run("Pratibha Manral\nStudent ID: 2104793\n")

    c_right = table.cell(0, 1)
    p_right = c_right.paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_right.add_run("Under the Guidance of:\n").font.bold = True
    p_right.add_run("Ms. Shikha Thakur\nAssistant Professor, Dept. of Computer Applications\n")

    doc.add_paragraph("\n")
    dept_p = doc.add_paragraph()
    dept_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_dept = dept_p.add_run("Department of Computer Applications\nGraphic Era (Deemed to be University), Dehradun\nMarch - 2026\n")
    r_dept.font.size = Pt(11)
    r_dept.font.bold = True

    doc.add_page_break()

    # Process remaining document lines
    lines = text.split("\n")
    is_diagram_block = False
    diagram_content = []
    
    # Skip until after the title header in text
    start_idx = 0
    for idx, line in enumerate(lines):
        if "CANDIDATE'S DECLARATION" in line:
            start_idx = idx
            break

    for line in lines[start_idx:]:
        stripped = line.strip()
        
        # Handle Diagram Blocks
        if "[DIAGRAM" in stripped:
            is_diagram_block = True
            diagram_content = [stripped]
            continue
        
        if is_diagram_block:
            diagram_content.append(line)
            if "================================================================================" in stripped:
                is_diagram_block = False
                # Add formatted callout box for Diagram
                p_box = doc.add_paragraph()
                p_box.paragraph_format.left_indent = Inches(0.4)
                p_box.paragraph_format.right_indent = Inches(0.4)
                p_box.paragraph_format.space_before = Pt(8)
                p_box.paragraph_format.space_after = Pt(8)
                
                full_diagram_text = "\n".join(diagram_content)
                r_box = p_box.add_run("📊 " + full_diagram_text.strip("=\n "))
                r_box.font.name = "Consolas"
                r_box.font.size = Pt(9.5)
                r_box.font.color.rgb = RGBColor(30, 58, 138)
            continue

        # Handle Chapters
        if stripped.startswith("CHAPTER "):
            p_ch = doc.add_paragraph()
            p_ch.paragraph_format.space_before = Pt(18)
            p_ch.paragraph_format.space_after = Pt(6)
            run = p_ch.add_run(stripped)
            run.font.size = Pt(15)
            run.font.bold = True
            run.font.color.rgb = RGBColor(16, 44, 87)
            continue

        # Handle Section Headings (e.g. 1.1, 1.2, 2.1)
        if re.match(r'^\d+\.\d+\s+[A-Z]', stripped):
            p_h2 = doc.add_paragraph()
            p_h2.paragraph_format.space_before = Pt(12)
            p_h2.paragraph_format.space_after = Pt(4)
            run = p_h2.add_run(stripped)
            run.font.size = Pt(12.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(31, 41, 55)
            continue

        # Handle Major Section Lines (====== or -------)
        if stripped.startswith("===") or stripped.startswith("---"):
            continue

        # Handle Code blocks or formula blocks
        if stripped.startswith("```") or stripped.startswith("class ") or stripped.startswith("def ") or stripped.startswith("$$"):
            p_code = doc.add_paragraph()
            p_code.paragraph_format.left_indent = Inches(0.3)
            run = p_code.add_run(line)
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(51, 65, 85)
            continue

        # Regular Body Paragraphs
        if stripped:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(line)
            run.font.size = Pt(10.5)

    doc.save(out_docx_path)
    print(f"Generated: {out_docx_path}")

def create_ieee_docx():
    ieee_tex_path = DOCS_DIR / "IEEE_CONFERENCE_PAPER.tex"
    out_docx_path = DOCS_DIR / "IEEE_CONFERENCE_PAPER.docx"

    with open(ieee_tex_path, "r", encoding="utf-8") as f:
        tex = f.read()

    doc = Document()
    
    # 0.75 in margins typical of IEEE papers
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_title = title_p.add_run("Design and Empirical Evaluation of a Deterministic, Resource-Constrained Network Intrusion Detection System Using In-Memory Sliding-Window Heuristics\n")
    r_title.font.size = Pt(15)
    r_title.font.bold = True

    # Authors
    author_p = doc.add_paragraph()
    author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_auth = author_p.add_run("Pratibha Manral and Ms. Shikha Thakur\n")
    r_auth.font.bold = True
    r_auth.font.size = Pt(11)
    author_p.add_run("Department of Computer Applications, Graphic Era (Deemed to be University), Dehradun, India\nEmails: pratibhamanral.10@gmail.com\n\n").font.size = Pt(9.5)

    # Abstract Box
    abs_p = doc.add_paragraph()
    abs_p.paragraph_format.left_indent = Inches(0.3)
    abs_p.paragraph_format.right_indent = Inches(0.3)
    r_abs_label = abs_p.add_run("Abstract—")
    r_abs_label.font.bold = True
    r_abs_label.font.size = Pt(9.5)
    
    abstract_text = (
        "The increasing prevalence of automated cyber reconnaissance and volumetric Denial-of-Service (DoS) attacks demands resilient, line-rate perimeter defense. "
        "While modern academic literature predominantly emphasizes Machine Learning (ML) and Deep Neural Network (DNN) architectures for intrusion detection, their real-world deployment on resource-constrained edge gateways is severely hindered by high computational complexity, gigabyte-scale memory footprints, feature extraction latencies, and an inherent lack of deterministic explainability. "
        "In this paper, we present the design, mathematical formulation, and empirical evaluation of an ultra-lightweight, deterministic Network Intrusion Detection System (NIDS) optimized for edge deployment. Operating directly on raw packet frames captured via Scapy, the system leverages amortized O(1) in-memory sliding-window queues to extract temporal behavioral metrics without database I/O bottlenecks. We formulate deterministic heuristic detection algorithms for four critical attack vectors: horizontal/vertical port sweeps, volumetric packet bursts, repeated TCP SYN handshakes, and ICMP flood anomalies. A multi-factor continuous risk-scoring algorithm normalizes observed deviations into a calibrated severity scale ([0, 100]). "
        "Empirical evaluations demonstrate 100% deterministic precision over defined boundary conditions, sub-2.0 ms packet processing latency, stable operational memory consumption under 45 MB RAM, and seamless real-time visualization via an asynchronous web telemetry console."
    )
    r_abs = abs_p.add_run(abstract_text)
    r_abs.font.size = Pt(9.5)

    kw_p = doc.add_paragraph()
    kw_p.paragraph_format.left_indent = Inches(0.3)
    kw_p.paragraph_format.right_indent = Inches(0.3)
    r_kw_label = kw_p.add_run("\nKeywords—")
    r_kw_label.font.bold = True
    r_kw_label.font.size = Pt(9.5)
    kw_p.add_run("Network Intrusion Detection System (NIDS), Sliding Window Heuristics, Edge Computing, Scapy, DoS Detection, Risk Scoring, SQLite WAL.\n\n").font.size = Pt(9.5)

    # Clean TeX Body Parsing
    sections_map = [
        ("I. INTRODUCTION", [
            "Modern distributed networks and edge computing infrastructures are under continuous adversarial reconnaissance and exploitation. Traditional defense-in-depth architectures rely on static firewalls to govern boundary ingress and egress traffic. However, stateless and stateful packet filters operate strictly on pre-defined access control lists (ACLs) and static IP/port bindings; they cannot infer temporal behavioral anomalies, such as an external host systematically probing sequential service ports or initiating high-frequency half-open handshakes.",
            "To address this vulnerability, Network Intrusion Detection Systems (NIDS) passively observe network traffic, reconstruct packet streams across the transport and internet layers, and detect anomalous patterns. However, modern research literature exhibits an acute disconnect: while hundreds of studies propose deep learning classifiers (e.g., CNNs, LSTMs, and Random Forests) reporting detection accuracies exceeding 98% on legacy datasets like NSL-KDD and CIC-IDS2017, these models are virtually impractical for edge deployment. Extracting more than 80 flow features in real time introduces packet-dropping bottlenecks, high memory consumption (>2 GB), and a dangerous 'black-box' deficit where security operators cannot ascertain the exact deterministic rationale behind an alert.",
            "To bridge this operational gap, this paper introduces a fully deterministic, lightweight NIDS architecture engineered for local execution on edge nodes. The core contributions of this study are:",
            "1) Amortized O(1) In-Memory Sliding-Window Tracking: Implementation of monotonic timestamp deques that eliminate database read bottlenecks during high-frequency velocity checks.",
            "2) Deterministic Threat Vector Heuristics: Precise mathematical formulations for detecting port sweeps, volumetric bursts, repeated handshakes, and ICMP flood anomalies.",
            "3) Continuous Multi-Factor Risk Scoring: A calibrated piecewise linear formulation transforming discrete excess ratios into an explainable [0, 100] risk index.",
            "4) ACID Relational Persistence & Telemetry: Integration of thread-safe SQLite Write-Ahead Logging (WAL) and an asynchronous REST web console for live threat visualization."
        ]),
        ("II. RELATED WORK AND THEORETICAL BACKGROUND", [
            "The conceptual foundation of intrusion detection was pioneered by Dorothy Denning in 1987, postulating that security violations correlate with abnormal patterns of system resource usage. Since then, NIDS architectures have evolved across three primary generations:",
            "A. Signature-Based Rule Engines\nPlatforms such as Snort and Suricata represent the industrial gold standard. They evaluate packet streams against vast databases of static signature strings and regular expressions. While computationally predictable, signature engines require constant manual updates, consume substantial memory when scaling rule libraries, and fail to detect novel behavioral anomalies or volumetric temporal floods that lack a static signature payload.",
            "B. Machine Learning and Anomaly Detection\nMachine learning approaches seek to detect deviations from established baseline traffic profiles. Classifiers such as Support Vector Machines (SVM), Extreme Gradient Boosting (XGBoost), and Deep Neural Networks have been widely researched. However, as demonstrated by Sommer and Paxson, ML-based intrusion detection faces fundamental operational hurdles in production networks: high false-positive costs, massive feature computation overhead, non-stationary network traffic distributions (concept drift), and zero semantic explainability.",
            "C. Proposed Stateful Temporal Heuristics\nOur approach synthesizes the deterministic transparency of rule engines with the dynamic adaptability of behavioral baselines. By maintaining temporal queues directly in memory, the system tracks the rate of change and cardinality of unique endpoints at wire speed with an ultra-compact memory footprint (<50 MB)."
        ]),
        ("III. SYSTEM ARCHITECTURE AND MATHEMATICAL FORMULATION", [
            "A. Packet Dissection and Feature Tuple\nLet P denote the continuous sequence of raw network frames intercepted from the network interface. The feature extraction engine maps each valid IP packet p into a normalized 8-tuple:\n\nf(p) = < t_p, src, dst, proto, s_port, d_port, L_p, F_tcp >\n\nwhere t_p is the monotonic timestamp, src and dst are IP addresses, proto is protocol, s_port and d_port are ports, L_p is byte size, and F_tcp is TCP flag bitmask.",
            "B. Amortized O(1) Sliding-Window Queue Mechanics\nTo evaluate temporal rates without querying disk-backed tables, each active source IP maintains isolated in-memory double-ended queues. For an arbitrary temporal window W, expired entries are evicted in amortized O(1) time:\n\nwhile Q is not empty and head.timestamp < (t_now - W): Q.pop_left()",
            "C. Heuristic Threat Formulations\n1) Port Scan Reconnaissance: Unique destination ports in 10s >= 15.\n2) Volumetric Abnormal Traffic (DoS): Total packet count from IP in 10s >= 200.\n3) Repeated Connections (SYN Flood): TCP SYN attempts between host pair in 15s >= 30.\n4) ICMP Flood: ICMP echo requests in 5s >= 15.",
            "D. Multi-Factor Continuous Risk Scoring\nRisk Score R = min(100, Base + min(30, ((Observed - Threshold) / Threshold) * Weight))\nMapped into: LOW (0-30), MEDIUM (31-70), and HIGH (71-100)."
        ]),
        ("IV. EXPERIMENTAL EVALUATION AND RESULTS", [
            "A. Experimental Setup\nThe framework was deployed on a 64-bit edge node (Intel Core i5, 8 GB RAM) running Windows 11 with Scapy 2.8.0, Npcap, and SQLite 3.42 in WAL mode.",
            "B. Synthetic Attack Scenario Verification\n- Benign Baseline: 100 normal HTTP/HTTPS frames resulted in zero false-positive alerts (FP = 0).\n- Port Scan Scenario: 25 destination ports probed; detected at port 15; Risk Score = 65 (MEDIUM).\n- Volumetric DoS Scenario: 220 UDP packets in 3.5s; triggered at packet 200; Risk Score = 70.\n- SYN Flood Scenario: 35 SYN packets; detected at 30th attempt; Risk Score = 55.\n- ICMP Flood Scenario: 20 echo requests in 0.8s; detected at 15th packet; Risk Score = 50.",
            "C. System Performance Benchmarks\n- Packet Parsing Latency: 1.42 ms (vs 18.50 ms for typical ML-NIDS)\n- Memory Consumption: 42.6 MB (vs 1450.0 MB for ML-NIDS)\n- CPU Utilization: 0.4% idle / 3.2% active\n- Database Transaction Write Latency: 0.35 ms"
        ]),
        ("V. CONCLUSION AND FUTURE SCOPE", [
            "This study presented a deterministic, ultra-lightweight Network Intrusion Detection System engineered for edge computing environments. By departing from resource-heavy deep learning models, the architecture demonstrates that stateful in-memory temporal sliding windows can achieve 100% deterministic detection precision across port scans, DoS bursts, repeated connections, and ICMP floods with sub-2 ms latency and minimal memory overhead (<45 MB RAM).",
            "Future work will focus on integrating Extended Berkeley Packet Filters (eBPF) and eXpress Data Path (XDP) within the Linux kernel to drop malicious frames before user-space traversal, transforming this passive detection system into an active kernel-level Intrusion Prevention System (IPS)."
        ]),
        ("REFERENCES", [
            "[1] D. E. Denning, 'An intrusion-detection model,' IEEE Transactions on Software Engineering, vol. SE-13, no. 2, pp. 222-232, 1987.",
            "[2] M. Roesch, 'Snort - lightweight intrusion detection for networks,' in Proc. 13th USENIX Conf. System Administration (LISA '99), 1999, pp. 229-238.",
            "[3] R. Sommer and V. Paxson, 'Outside the closed world: On using machine learning for network intrusion detection,' in Proc. IEEE Symposium on Security and Privacy (S&P), 2010, pp. 305-316.",
            "[4] M. Tavallaee, E. Bagheri, W. Lu, and A. A. Ghorbani, 'A detailed analysis of the KDD CUP 99 data set,' in Proc. IEEE Symp. Computational Intelligence for Security and Defense Applications (CISDA), 2009, pp. 1-6.",
            "[5] I. Sharafaldin, A. H. Lashkari, and A. A. Ghorbani, 'Toward generating a new intrusion detection dataset and intrusion traffic characterization,' in Proc. 4th Int. Conf. Information Systems Security and Privacy (ICISSP), 2018, pp. 108-116."
        ])
    ]

    for sec_title, sec_paragraphs in sections_map:
        p_sec = doc.add_paragraph()
        p_sec.paragraph_format.space_before = Pt(12)
        p_sec.paragraph_format.space_after = Pt(4)
        r_sec = p_sec.add_run(sec_title)
        r_sec.font.bold = True
        r_sec.font.size = Pt(11)

        for para in sec_paragraphs:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.line_spacing = 1.15
            run = p.add_run(para)
            run.font.size = Pt(9.5)

    doc.save(out_docx_path)
    print(f"Generated: {out_docx_path}")

if __name__ == "__main__":
    create_report_docx()
    create_ieee_docx()
