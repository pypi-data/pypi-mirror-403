"""
Generate comprehensive visualizations for LoPace compression metrics.
Creates publication-quality SVG plots suitable for research papers.
"""

import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import matplotlib
matplotlib.use('SVG')  # Use SVG backend for vector graphics
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import pandas as pd

# Add parent directory to path to import lopace
sys.path.insert(0, str(Path(__file__).parent.parent))

from lopace import PromptCompressor, CompressionMethod


# Set style for publication-quality plots
sns.set_style("whitegrid")
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 11,
    'figure.titlesize': 18,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.format': 'svg',
    'svg.fonttype': 'none',  # Editable text in SVG
    'mathtext.default': 'regular',
    'axes.linewidth': 1.2,
    'grid.linewidth': 0.8,
    'lines.linewidth': 2.0,
    'patch.linewidth': 1.5,
})


def generate_test_prompts() -> List[Tuple[str, str]]:
    """Generate test prompts of various sizes."""
    prompts = []
    
    # Small prompts (50-200 chars)
    small_prompts = [
        "You are a helpful AI assistant.",
        "Translate the following text to French.",
        "Summarize this document in 3 sentences.",
        "You are an expert Python developer.",
    ]
    
    # Medium prompts (500-2000 chars)
    medium_prompts = [
        """You are a helpful AI assistant designed to provide accurate, 
detailed, and helpful responses to user queries. Your goal is to assist users 
by understanding their questions and providing relevant information, explanations, 
or guidance. Always be respectful, clear, and concise in your communications. 
If you are uncertain about something, it's better to acknowledge that uncertainty 
rather than provide potentially incorrect information.""",
        
        """As an advanced language model, your primary function is to understand 
and respond to user inputs in a helpful, accurate, and safe manner. You should 
provide informative answers, assist with problem-solving, engage in creative 
writing tasks, and support various learning activities. Maintain objectivity, 
cite sources when appropriate, and always prioritize user safety and ethical 
considerations in your responses.""",
        
        """You are a professional software engineer with expertise in multiple 
programming languages including Python, JavaScript, Java, and C++. Your role 
is to help users write clean, efficient, and maintainable code. Provide 
code examples, explain best practices, debug issues, and suggest improvements. 
Always consider performance, security, and scalability in your recommendations.""",
    ]
    
    # Large prompts (5000-20000 chars)
    large_prompts = [
        """You are a comprehensive AI assistant specializing in technical documentation 
and educational content. Your expertise spans multiple domains including computer science, 
data science, machine learning, software engineering, and web development. When responding 
to queries, you should provide thorough explanations, include relevant examples, and 
structure your responses in a clear and organized manner. Always aim to educate while 
solving problems. Break down complex concepts into digestible parts, use analogies when 
helpful, and provide practical applications of theoretical knowledge. Maintain accuracy 
by acknowledging when you're uncertain and suggest reliable sources for further learning. 
Your communication style should be professional yet accessible, avoiding unnecessary 
jargon while ensuring precision in technical details. Consider the user's background 
and adjust your explanation depth accordingly. For code-related queries, always provide 
complete, working examples with comments explaining key parts. For conceptual questions, 
use diagrams, step-by-step breakdowns, and real-world analogies. When discussing 
best practices, explain not just what to do but why, including trade-offs and 
alternative approaches. Your goal is to empower users with knowledge and skills 
rather than just providing answers. Encourage critical thinking, experimentation, 
and continuous learning. Address potential pitfalls, common mistakes, and how to 
avoid them. Provide context about industry standards and emerging trends when relevant. 
Remember that effective teaching involves understanding the learner's perspective, 
patience, and encouragement. Always prioritize clarity, accuracy, and educational value 
in every interaction. Balance thoroughness with conciseness, ensuring responses are 
comprehensive yet not overwhelming. Use formatting effectively to improve readability, 
including bullet points, numbered lists, and section headers when appropriate.""",
        
        """System Prompt for Advanced Multi-Modal AI Assistant: This AI system is designed 
to be a versatile, intelligent, and highly capable assistant that can handle a wide range 
of tasks across multiple domains. The system integrates natural language processing, 
reasoning capabilities, knowledge retrieval, and contextual understanding to provide 
comprehensive support. Primary capabilities include question answering, problem-solving, 
creative tasks, analysis, code generation, data interpretation, and educational support. 
The assistant maintains a knowledge base spanning science, technology, humanities, 
business, arts, and current events. When interacting with users, the system should 
prioritize accuracy, helpfulness, safety, and ethical considerations. Responses should 
be well-structured, clear, and appropriately detailed based on the complexity of the query. 
The assistant should ask clarifying questions when necessary, acknowledge limitations, 
and provide sources or references when making factual claims. For technical questions, 
provide detailed explanations with examples. For creative tasks, demonstrate imagination 
while maintaining coherence and appropriateness. For analytical tasks, show step-by-step 
reasoning and present conclusions clearly. The system should adapt its communication style 
to match the user's level of expertise and the context of the conversation. Always aim 
to be constructive, respectful, and professional. When dealing with sensitive topics, 
exercise caution and provide balanced perspectives. For coding tasks, write clean, 
well-commented code following best practices. For writing tasks, ensure proper grammar, 
style, and structure. The assistant should continuously learn from interactions while 
maintaining core principles and guidelines. It should handle ambiguity gracefully, 
provide multiple perspectives when appropriate, and help users think critically about 
complex issues. The system is designed to be a tool for empowerment, education, and 
efficient problem-solving.""",
    ]
    
    # Combine and label prompts
    for prompt in small_prompts:
        prompts.append(("Small", prompt))
    
    for prompt in medium_prompts:
        prompts.append(("Medium", prompt))
    
    for large_prompts_list in large_prompts:
        prompts.append(("Large", large_prompts_list))
    
    # Add one more large prompt if needed
    if len(prompts) < 10:
        additional_large = """Comprehensive System Prompt for Advanced AI Assistant: This sophisticated 
artificial intelligence system represents a state-of-the-art language model designed to excel across 
a multitude of domains and applications. The system integrates deep learning architectures, extensive 
knowledge bases, and advanced reasoning capabilities to provide exceptional assistance. Core competencies 
include natural language understanding and generation, logical reasoning, creative problem-solving, 
technical expertise, and ethical decision-making. The assistant maintains extensive knowledge spanning 
STEM fields, humanities, arts, business, law, medicine, and contemporary issues. When engaging with users, 
the system employs sophisticated contextual understanding, adapts communication styles appropriately, 
and provides nuanced, well-reasoned responses. The architecture supports multi-modal interactions, 
real-time learning, and seamless integration with external tools and databases. Quality assurance 
mechanisms ensure accuracy, relevance, and safety in all outputs. The system demonstrates exceptional 
capabilities in code generation and analysis, creative writing, data analysis, educational instruction, 
research assistance, and complex problem decomposition. Advanced features include meta-cognitive reasoning, 
uncertainty quantification, bias detection and mitigation, and explainable AI principles. The assistant 
prioritizes user empowerment through education, transparency, and collaborative problem-solving approaches."""
        prompts.append(("Large", additional_large))
    
    # Ensure we have exactly 10 prompts
    prompts = prompts[:10]
    
    return prompts


def measure_compression(
    compressor: PromptCompressor,
    prompt: str,
    method: CompressionMethod
) -> Dict:
    """Measure compression metrics for a given prompt and method."""
    # Memory tracking
    tracemalloc.start()
    
    # Compression
    start_time = time.perf_counter()
    compressed = compressor.compress(prompt, method)
    compression_time = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    compression_memory = peak / (1024 * 1024)  # MB
    
    tracemalloc.stop()
    
    # Decompression
    tracemalloc.start()
    start_time = time.perf_counter()
    decompressed = compressor.decompress(compressed, method)
    decompression_time = time.perf_counter() - start_time
    current, peak = tracemalloc.get_traced_memory()
    decompression_memory = peak / (1024 * 1024)  # MB
    tracemalloc.stop()
    
    # Verify losslessness
    is_lossless = prompt == decompressed
    
    # Calculate metrics
    original_size = len(prompt.encode('utf-8'))
    compressed_size = len(compressed)
    
    metrics = {
        'method': method.value,
        'original_size_bytes': original_size,
        'compressed_size_bytes': compressed_size,
        'compression_ratio': original_size / compressed_size if compressed_size > 0 else 0,
        'space_savings_percent': (1 - compressed_size / original_size) * 100 if original_size > 0 else 0,
        'bytes_saved': original_size - compressed_size,
        'compression_time_ms': compression_time * 1000,
        'decompression_time_ms': decompression_time * 1000,
        'compression_throughput_mbps': (original_size / (1024 * 1024)) / compression_time if compression_time > 0 else 0,
        'decompression_throughput_mbps': (compressed_size / (1024 * 1024)) / decompression_time if decompression_time > 0 else 0,
        'compression_memory_mb': compression_memory,
        'decompression_memory_mb': decompression_memory,
        'is_lossless': is_lossless,
        'num_characters': len(prompt),
    }
    
    return metrics


def run_benchmarks() -> pd.DataFrame:
    """Run compression benchmarks on all prompts and methods."""
    compressor = PromptCompressor(model="cl100k_base", zstd_level=15)
    prompts = generate_test_prompts()
    
    all_results = []
    
    print("Running benchmarks...")
    for idx, (category, prompt) in enumerate(prompts, 1):
        print(f"  Processing prompt {idx}/10 ({category}, {len(prompt)} chars)...")
        
        for method in [CompressionMethod.ZSTD, CompressionMethod.TOKEN, CompressionMethod.HYBRID]:
            metrics = measure_compression(compressor, prompt, method)
            metrics['prompt_id'] = idx
            metrics['prompt_category'] = category
            metrics['prompt_length'] = len(prompt)
            all_results.append(metrics)
    
    df = pd.DataFrame(all_results)
    return df


def plot_compression_ratio(df: pd.DataFrame, output_dir: Path):
    """Plot compression ratios by method and prompt size."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left: Compression ratio by method
    ax1 = axes[0]
    method_order = ['zstd', 'token', 'hybrid']
    method_labels = ['Zstd', 'Token (BPE)', 'Hybrid']
    
    data_by_method = [df[df['method'] == m]['compression_ratio'].values for m in method_order]
    
    bp = ax1.boxplot(data_by_method, labels=method_labels, patch_artist=True,
                     widths=0.6, showmeans=True, meanline=True)
    
    colors = ['#3498db', '#2ecc71', '#9b59b6']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.set_ylabel('Compression Ratio', fontweight='bold')
    ax1.set_xlabel('Compression Method', fontweight='bold')
    ax1.set_title('(a) Compression Ratio Distribution by Method', fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_ylim(bottom=0)
    
    # Right: Compression ratio by prompt category
    ax2 = axes[1]
    categories = ['Small', 'Medium', 'Large']
    category_data = []
    
    for category in categories:
        category_df = df[df['prompt_category'] == category]
        method_data = [category_df[category_df['method'] == m]['compression_ratio'].mean() 
                      for m in method_order]
        category_data.append(method_data)
    
    x = np.arange(len(categories))
    width = 0.25
    
    for i, (method, color) in enumerate(zip(method_labels, colors)):
        values = [category_data[j][i] for j in range(len(categories))]
        ax2.bar(x + i * width, values, width, label=method, color=color, alpha=0.8)
    
    ax2.set_ylabel('Mean Compression Ratio', fontweight='bold')
    ax2.set_xlabel('Prompt Category', fontweight='bold')
    ax2.set_title('(b) Compression Ratio by Prompt Size', fontweight='bold', pad=15)
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(categories)
    ax2.legend(loc='upper left', framealpha=0.9)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'compression_ratio.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: compression_ratio.svg")


def plot_space_savings(df: pd.DataFrame, output_dir: Path):
    """Plot space savings percentages."""
    fig, ax = plt.subplots(figsize=(12, 7))
    
    categories = ['Small', 'Medium', 'Large']
    method_order = ['zstd', 'token', 'hybrid']
    method_labels = ['Zstd', 'Token (BPE)', 'Hybrid']
    colors = ['#3498db', '#2ecc71', '#9b59b6']
    
    x = np.arange(len(categories))
    width = 0.25
    
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        stds = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['space_savings_percent'].mean())
            stds.append(subset['space_savings_percent'].std())
        
        bars = ax.bar(x + i * width, means, width, label=label, color=color, alpha=0.8,
                     yerr=stds, capsize=5, error_kw={'elinewidth': 2, 'capthick': 2})
    
    ax.set_ylabel('Space Savings (%)', fontweight='bold')
    ax.set_xlabel('Prompt Category', fontweight='bold')
    ax.set_title('Space Savings by Compression Method and Prompt Size', fontweight='bold', pad=15)
    ax.set_xticks(x + width)
    ax.set_xticklabels(categories)
    ax.legend(loc='upper left', framealpha=0.9, ncol=3)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.set_ylim(0, 100)
    
    # Add value labels on bars
    for i, method in enumerate(method_order):
        for j, category in enumerate(categories):
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            mean_val = subset['space_savings_percent'].mean()
            ax.text(j + i * width, mean_val + 2, f'{mean_val:.1f}%',
                   ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'space_savings.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: space_savings.svg")


def plot_disk_size_comparison(df: pd.DataFrame, output_dir: Path):
    """Plot original vs compressed disk sizes."""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    method_order = ['zstd', 'token', 'hybrid']
    method_labels = ['Zstd', 'Token (BPE)', 'Hybrid']
    colors = ['#3498db', '#2ecc71', '#9b59b6']
    
    # Top: Stacked bar chart showing original vs compressed
    ax1 = axes[0]
    categories = ['Small', 'Medium', 'Large']
    
    x = np.arange(len(categories))
    width = 0.25
    
    for category_idx, category in enumerate(categories):
        category_df = df[df['prompt_category'] == category]
        original_sizes = category_df.groupby('prompt_id')['original_size_bytes'].first().mean()
        
        compressed_means = []
        for method in method_order:
            method_df = category_df[category_df['method'] == method]
            compressed_means.append(method_df['compressed_size_bytes'].mean())
        
        # Stack bars
        bottom = 0
        for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
            if i == 0:
                # First method: show original vs compressed
                ax1.bar(category_idx + i * width, original_sizes / 1024, width,
                       label='Original Size' if category_idx == 0 else '', color='#e74c3c', alpha=0.7)
                ax1.bar(category_idx + i * width, compressed_means[i] / 1024, width,
                       bottom=0, label=label if category_idx == 0 else '', color=color, alpha=0.8)
            else:
                # Other methods: just compressed size
                ax1.bar(category_idx + i * width, compressed_means[i] / 1024, width,
                       label=label if category_idx == 0 else '', color=color, alpha=0.8)
    
    ax1.set_ylabel('Size (KB)', fontweight='bold')
    ax1.set_xlabel('Prompt Category', fontweight='bold')
    ax1.set_title('Disk Size: Original vs Compressed', fontweight='bold', pad=15)
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(categories)
    ax1.legend(loc='upper left', framealpha=0.9, ncol=4)
    ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax1.set_yscale('log')
    
    # Bottom: Percentage reduction
    ax2 = axes[1]
    
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['space_savings_percent'].mean())
        
        ax2.plot(categories, means, marker='o', linewidth=2.5, markersize=10,
                label=label, color=color, markerfacecolor=color, markeredgewidth=2)
    
    ax2.set_ylabel('Size Reduction (%)', fontweight='bold')
    ax2.set_xlabel('Prompt Category', fontweight='bold')
    ax2.set_title('Size Reduction by Prompt Category', fontweight='bold', pad=15)
    ax2.legend(loc='best', framealpha=0.9)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_ylim(0, 100)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'disk_size_comparison.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: disk_size_comparison.svg")


def plot_speed_metrics(df: pd.DataFrame, output_dir: Path):
    """Plot compression and decompression speed metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    method_order = ['zstd', 'token', 'hybrid']
    method_labels = ['Zstd', 'Token (BPE)', 'Hybrid']
    colors = ['#3498db', '#2ecc71', '#9b59b6']
    categories = ['Small', 'Medium', 'Large']
    
    # Top-left: Compression time
    ax1 = axes[0, 0]
    x = np.arange(len(categories))
    width = 0.25
    
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['compression_time_ms'].mean())
        
        ax1.bar(x + i * width, means, width, label=label, color=color, alpha=0.8)
    
    ax1.set_ylabel('Compression Time (ms)', fontweight='bold')
    ax1.set_xlabel('Prompt Category', fontweight='bold')
    ax1.set_title('(a) Compression Time', fontweight='bold', pad=15)
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(categories)
    ax1.legend(framealpha=0.9)
    ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax1.set_yscale('log')
    
    # Top-right: Decompression time
    ax2 = axes[0, 1]
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['decompression_time_ms'].mean())
        
        ax2.bar(x + i * width, means, width, label=label, color=color, alpha=0.8)
    
    ax2.set_ylabel('Decompression Time (ms)', fontweight='bold')
    ax2.set_xlabel('Prompt Category', fontweight='bold')
    ax2.set_title('(b) Decompression Time', fontweight='bold', pad=15)
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(categories)
    ax2.legend(framealpha=0.9)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_yscale('log')
    
    # Bottom-left: Compression throughput
    ax3 = axes[1, 0]
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['compression_throughput_mbps'].mean())
        
        ax3.plot(categories, means, marker='o', linewidth=2.5, markersize=10,
                label=label, color=color, markerfacecolor=color, markeredgewidth=2)
    
    ax3.set_ylabel('Throughput (MB/s)', fontweight='bold')
    ax3.set_xlabel('Prompt Category', fontweight='bold')
    ax3.set_title('(c) Compression Throughput', fontweight='bold', pad=15)
    ax3.legend(framealpha=0.9)
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.set_ylim(bottom=0)
    
    # Bottom-right: Decompression throughput
    ax4 = axes[1, 1]
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['decompression_throughput_mbps'].mean())
        
        ax4.plot(categories, means, marker='s', linewidth=2.5, markersize=10,
                label=label, color=color, markerfacecolor=color, markeredgewidth=2)
    
    ax4.set_ylabel('Throughput (MB/s)', fontweight='bold')
    ax4.set_xlabel('Prompt Category', fontweight='bold')
    ax4.set_title('(d) Decompression Throughput', fontweight='bold', pad=15)
    ax4.legend(framealpha=0.9)
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'speed_metrics.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: speed_metrics.svg")


def plot_memory_usage(df: pd.DataFrame, output_dir: Path):
    """Plot memory usage during compression and decompression."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    method_order = ['zstd', 'token', 'hybrid']
    method_labels = ['Zstd', 'Token (BPE)', 'Hybrid']
    colors = ['#3498db', '#2ecc71', '#9b59b6']
    categories = ['Small', 'Medium', 'Large']
    
    x = np.arange(len(categories))
    width = 0.25
    
    # Left: Compression memory
    ax1 = axes[0]
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        stds = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['compression_memory_mb'].mean())
            stds.append(subset['compression_memory_mb'].std())
        
        ax1.bar(x + i * width, means, width, label=label, color=color, alpha=0.8,
               yerr=stds, capsize=5, error_kw={'elinewidth': 2, 'capthick': 2})
    
    ax1.set_ylabel('Memory Usage (MB)', fontweight='bold')
    ax1.set_xlabel('Prompt Category', fontweight='bold')
    ax1.set_title('(a) Compression Memory Usage', fontweight='bold', pad=15)
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(categories)
    ax1.legend(framealpha=0.9)
    ax1.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax1.set_ylim(bottom=0)
    
    # Right: Decompression memory
    ax2 = axes[1]
    for i, (method, label, color) in enumerate(zip(method_order, method_labels, colors)):
        means = []
        stds = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            means.append(subset['decompression_memory_mb'].mean())
            stds.append(subset['decompression_memory_mb'].std())
        
        ax2.bar(x + i * width, means, width, label=label, color=color, alpha=0.8,
               yerr=stds, capsize=5, error_kw={'elinewidth': 2, 'capthick': 2})
    
    ax2.set_ylabel('Memory Usage (MB)', fontweight='bold')
    ax2.set_xlabel('Prompt Category', fontweight='bold')
    ax2.set_title('(b) Decompression Memory Usage', fontweight='bold', pad=15)
    ax2.set_xticks(x + width)
    ax2.set_xticklabels(categories)
    ax2.legend(framealpha=0.9)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.set_ylim(bottom=0)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'memory_usage.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: memory_usage.svg")


def plot_comprehensive_comparison(df: pd.DataFrame, output_dir: Path):
    """Create a comprehensive comparison heatmap."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    method_order = ['zstd', 'token', 'hybrid']
    method_labels = ['Zstd', 'Token\n(BPE)', 'Hybrid']
    categories = ['Small', 'Medium', 'Large']
    
    # Top-left: Compression ratio heatmap
    ax1 = axes[0, 0]
    compression_ratio_matrix = []
    for method in method_order:
        row = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            row.append(subset['compression_ratio'].mean())
        compression_ratio_matrix.append(row)
    
    im1 = ax1.imshow(compression_ratio_matrix, cmap='YlOrRd', aspect='auto', vmin=0)
    ax1.set_xticks(np.arange(len(categories)))
    ax1.set_yticks(np.arange(len(method_labels)))
    ax1.set_xticklabels(categories)
    ax1.set_yticklabels(method_labels)
    ax1.set_ylabel('Compression Method', fontweight='bold')
    ax1.set_xlabel('Prompt Category', fontweight='bold')
    ax1.set_title('(a) Compression Ratio', fontweight='bold', pad=15)
    
    # Add text annotations
    for i in range(len(method_labels)):
        for j in range(len(categories)):
            text = ax1.text(j, i, f'{compression_ratio_matrix[i][j]:.2f}x',
                          ha="center", va="center", color="black", fontweight='bold')
    
    plt.colorbar(im1, ax=ax1, label='Compression Ratio')
    
    # Top-right: Space savings heatmap
    ax2 = axes[0, 1]
    space_savings_matrix = []
    for method in method_order:
        row = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            row.append(subset['space_savings_percent'].mean())
        space_savings_matrix.append(row)
    
    im2 = ax2.imshow(space_savings_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    ax2.set_xticks(np.arange(len(categories)))
    ax2.set_yticks(np.arange(len(method_labels)))
    ax2.set_xticklabels(categories)
    ax2.set_yticklabels(method_labels)
    ax2.set_ylabel('Compression Method', fontweight='bold')
    ax2.set_xlabel('Prompt Category', fontweight='bold')
    ax2.set_title('(b) Space Savings (%)', fontweight='bold', pad=15)
    
    for i in range(len(method_labels)):
        for j in range(len(categories)):
            text = ax2.text(j, i, f'{space_savings_matrix[i][j]:.1f}%',
                          ha="center", va="center", color="black", fontweight='bold')
    
    plt.colorbar(im2, ax=ax2, label='Space Savings (%)')
    
    # Bottom-left: Compression speed heatmap
    ax3 = axes[1, 0]
    speed_matrix = []
    for method in method_order:
        row = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            row.append(subset['compression_throughput_mbps'].mean())
        speed_matrix.append(row)
    
    im3 = ax3.imshow(speed_matrix, cmap='viridis', aspect='auto')
    ax3.set_xticks(np.arange(len(categories)))
    ax3.set_yticks(np.arange(len(method_labels)))
    ax3.set_xticklabels(categories)
    ax3.set_yticklabels(method_labels)
    ax3.set_ylabel('Compression Method', fontweight='bold')
    ax3.set_xlabel('Prompt Category', fontweight='bold')
    ax3.set_title('(c) Compression Throughput (MB/s)', fontweight='bold', pad=15)
    
    for i in range(len(method_labels)):
        for j in range(len(categories)):
            text = ax3.text(j, i, f'{speed_matrix[i][j]:.2f}',
                          ha="center", va="center", color="white", fontweight='bold')
    
    plt.colorbar(im3, ax=ax3, label='Throughput (MB/s)')
    
    # Bottom-right: Memory usage heatmap
    ax4 = axes[1, 1]
    memory_matrix = []
    for method in method_order:
        row = []
        for category in categories:
            subset = df[(df['method'] == method) & (df['prompt_category'] == category)]
            row.append(subset['compression_memory_mb'].mean())
        memory_matrix.append(row)
    
    im4 = ax4.imshow(memory_matrix, cmap='plasma', aspect='auto')
    ax4.set_xticks(np.arange(len(categories)))
    ax4.set_yticks(np.arange(len(method_labels)))
    ax4.set_xticklabels(categories)
    ax4.set_yticklabels(method_labels)
    ax4.set_ylabel('Compression Method', fontweight='bold')
    ax4.set_xlabel('Prompt Category', fontweight='bold')
    ax4.set_title('(d) Compression Memory Usage (MB)', fontweight='bold', pad=15)
    
    for i in range(len(method_labels)):
        for j in range(len(categories)):
            text = ax4.text(j, i, f'{memory_matrix[i][j]:.2f}',
                          ha="center", va="center", color="white", fontweight='bold')
    
    plt.colorbar(im4, ax=ax4, label='Memory (MB)')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comprehensive_comparison.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: comprehensive_comparison.svg")


def plot_scalability(df: pd.DataFrame, output_dir: Path):
    """Plot how metrics scale with prompt size."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    method_order = ['zstd', 'token', 'hybrid']
    method_labels = ['Zstd', 'Token (BPE)', 'Hybrid']
    colors = ['#3498db', '#2ecc71', '#9b59b6']
    
    # Get unique prompt sizes
    prompt_sizes = sorted(df['prompt_length'].unique())
    
    # Top-left: Compression ratio vs prompt size
    ax1 = axes[0, 0]
    for method, label, color in zip(method_order, method_labels, colors):
        means = []
        sizes = []
        for size in prompt_sizes:
            subset = df[(df['method'] == method) & (df['prompt_length'] == size)]
            if len(subset) > 0:
                means.append(subset['compression_ratio'].mean())
                sizes.append(size)
        
        ax1.plot(sizes, means, marker='o', linewidth=2.5, markersize=8,
                label=label, color=color, markerfacecolor=color, markeredgewidth=2)
    
    ax1.set_xlabel('Prompt Length (characters)', fontweight='bold')
    ax1.set_ylabel('Compression Ratio', fontweight='bold')
    ax1.set_title('(a) Compression Ratio vs Prompt Size', fontweight='bold', pad=15)
    ax1.legend(framealpha=0.9)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xscale('log')
    
    # Top-right: Space savings vs prompt size
    ax2 = axes[0, 1]
    for method, label, color in zip(method_order, method_labels, colors):
        means = []
        sizes = []
        for size in prompt_sizes:
            subset = df[(df['method'] == method) & (df['prompt_length'] == size)]
            if len(subset) > 0:
                means.append(subset['space_savings_percent'].mean())
                sizes.append(size)
        
        ax2.plot(sizes, means, marker='s', linewidth=2.5, markersize=8,
                label=label, color=color, markerfacecolor=color, markeredgewidth=2)
    
    ax2.set_xlabel('Prompt Length (characters)', fontweight='bold')
    ax2.set_ylabel('Space Savings (%)', fontweight='bold')
    ax2.set_title('(b) Space Savings vs Prompt Size', fontweight='bold', pad=15)
    ax2.legend(framealpha=0.9)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xscale('log')
    
    # Bottom-left: Compression time vs prompt size
    ax3 = axes[1, 0]
    for method, label, color in zip(method_order, method_labels, colors):
        means = []
        sizes = []
        for size in prompt_sizes:
            subset = df[(df['method'] == method) & (df['prompt_length'] == size)]
            if len(subset) > 0:
                means.append(subset['compression_time_ms'].mean())
                sizes.append(size)
        
        ax3.plot(sizes, means, marker='^', linewidth=2.5, markersize=8,
                label=label, color=color, markerfacecolor=color, markeredgewidth=2)
    
    ax3.set_xlabel('Prompt Length (characters)', fontweight='bold')
    ax3.set_ylabel('Compression Time (ms)', fontweight='bold')
    ax3.set_title('(c) Compression Time vs Prompt Size', fontweight='bold', pad=15)
    ax3.legend(framealpha=0.9)
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.set_xscale('log')
    ax3.set_yscale('log')
    
    # Bottom-right: Memory vs prompt size
    ax4 = axes[1, 1]
    for method, label, color in zip(method_order, method_labels, colors):
        means = []
        sizes = []
        for size in prompt_sizes:
            subset = df[(df['method'] == method) & (df['prompt_length'] == size)]
            if len(subset) > 0:
                means.append(subset['compression_memory_mb'].mean())
                sizes.append(size)
        
        ax4.plot(sizes, means, marker='d', linewidth=2.5, markersize=8,
                label=label, color=color, markerfacecolor=color, markeredgewidth=2)
    
    ax4.set_xlabel('Prompt Length (characters)', fontweight='bold')
    ax4.set_ylabel('Memory Usage (MB)', fontweight='bold')
    ax4.set_title('(d) Memory Usage vs Prompt Size', fontweight='bold', pad=15)
    ax4.legend(framealpha=0.9)
    ax4.grid(True, alpha=0.3, linestyle='--')
    ax4.set_xscale('log')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'scalability_analysis.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: scalability_analysis.svg")


def plot_original_vs_decompressed(output_dir: Path):
    """Plot original vs decompressed data comparison across multiple prompts."""
    compressor = PromptCompressor(model="cl100k_base", zstd_level=15)
    prompts = generate_test_prompts()
    
    # Select a few diverse prompts for visualization
    selected_prompts = [
        ("Small Prompt 1", prompts[0][1]),
        ("Medium Prompt 1", prompts[4][1]),
        ("Large Prompt 1", prompts[7][1]),
        ("Medium Prompt 2", prompts[5][1]),
        ("Small Prompt 2", prompts[1][1]),
    ]
    
    # Use Hybrid method (best compression)
    method = CompressionMethod.HYBRID
    
    fig, axes = plt.subplots(len(selected_prompts), 1, figsize=(16, 14))
    if len(selected_prompts) == 1:
        axes = [axes]
    
    fig.suptitle('Original vs Decompressed: Lossless Compression Verification', 
                 fontsize=18, fontweight='bold', y=0.995)
    
    for idx, (title, prompt) in enumerate(selected_prompts):
        ax = axes[idx]
        
        # Compress and decompress
        compressed = compressor.compress(prompt, method)
        decompressed = compressor.decompress(compressed, method)
        
        # Verify losslessness
        is_lossless = prompt == decompressed
        
        # Create representation: show byte-by-byte or character-by-character
        original_bytes = prompt.encode('utf-8')
        decompressed_bytes = decompressed.encode('utf-8')
        
        # Sample points for visualization (every Nth byte/char for performance)
        sample_rate = max(1, len(original_bytes) // 200)  # ~200 points max
        sample_indices = np.arange(0, len(original_bytes), sample_rate)
        
        # Get byte values (0-255) for visualization
        original_byte_values = np.array([original_bytes[i] for i in sample_indices])
        decompressed_byte_values = np.array([decompressed_bytes[i] for i in sample_indices])
        
        # Normalize to 0-100 range for better visualization
        original_normalized = (original_byte_values / 255.0) * 100
        decompressed_normalized = (decompressed_byte_values / 255.0) * 100
        
        # Plot original (blue line)
        ax.plot(sample_indices, original_normalized, 'b-', linewidth=2.0, 
               label='Original', alpha=0.7)
        
        # Plot decompressed (red line) - should overlap perfectly for lossless
        ax.plot(sample_indices, decompressed_normalized, 'r-', linewidth=2.0, 
               label='Decompressed', alpha=0.7, linestyle='--')
        
        # Mark key compression points (sample every Nth point)
        step = max(1, len(sample_indices) // 20)
        key_indices = sample_indices[::step]
        key_original = original_normalized[::step]
        ax.scatter(key_indices, key_original, 
                  color='red', s=40, alpha=0.8, zorder=5, 
                  label='Sample Points', marker='o', edgecolors='darkred', linewidths=1)
        
        # Add text info
        original_size = len(original_bytes)
        compressed_size = len(compressed)
        compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
        space_saved = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        
        info_text = (f"Size: {original_size} → {compressed_size} bytes "
                    f"({space_saved:.1f}% saved, {compression_ratio:.2f}x) | "
                    f"Lossless: {'✓' if is_lossless else '✗'}")
        
        ax.text(0.02, 0.95, info_text, transform=ax.transAxes,
               fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
               fontweight='bold')
        
        ax.set_ylabel(f'{title}\n(Normalized Byte Values)', fontweight='bold')
        ax.set_xlabel('Byte Position' if idx == len(selected_prompts) - 1 else '', fontweight='bold')
        ax.set_title(f'{title} - {len(original_bytes)} bytes', fontweight='bold', pad=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='upper right', framealpha=0.9, fontsize=9)
        ax.set_ylim(-5, 105)
        
        # Highlight that they overlap perfectly (lossless)
        if is_lossless:
            ax.axhspan(-5, 105, alpha=0.05, color='green', zorder=0)
    
    plt.tight_layout(rect=[0, 0, 1, 0.99])
    plt.savefig(output_dir / 'original_vs_decompressed.svg', format='svg', bbox_inches='tight')
    plt.close()
    print(f"  Saved: original_vs_decompressed.svg")


def main():
    """Main function to generate all visualizations."""
    # Create output directory
    output_dir = Path(__file__).parent.parent / 'screenshots'
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("LoPace Visualization Generator")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print()
    
    # Run benchmarks
    print("Step 1: Running compression benchmarks...")
    df = run_benchmarks()
    
    # Save raw data
    csv_path = output_dir / 'benchmark_data.csv'
    df.to_csv(csv_path, index=False)
    print(f"\n  Saved benchmark data to: {csv_path}")
    
    print("\nStep 2: Generating visualizations...")
    
    # Generate all plots
    plot_compression_ratio(df, output_dir)
    plot_space_savings(df, output_dir)
    plot_disk_size_comparison(df, output_dir)
    plot_speed_metrics(df, output_dir)
    plot_memory_usage(df, output_dir)
    plot_comprehensive_comparison(df, output_dir)
    plot_scalability(df, output_dir)
    plot_original_vs_decompressed(output_dir)
    
    print("\n" + "=" * 70)
    print("Visualization generation complete!")
    print(f"All plots saved to: {output_dir}")
    print("=" * 70)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("-" * 70)
    for method in ['zstd', 'token', 'hybrid']:
        method_df = df[df['method'] == method]
        print(f"\n{method.upper()}:")
        print(f"  Mean Compression Ratio: {method_df['compression_ratio'].mean():.2f}x")
        print(f"  Mean Space Savings: {method_df['space_savings_percent'].mean():.2f}%")
        print(f"  Mean Compression Time: {method_df['compression_time_ms'].mean():.2f} ms")
        print(f"  Mean Throughput: {method_df['compression_throughput_mbps'].mean():.2f} MB/s")


if __name__ == "__main__":
    main()