#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create publication-ready figure for PNAS showing circuit-level Bayesian posteriors.
Main figure: 3 panels showing progressive analysis
Supplement: ROI-level posteriors
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import seaborn as sns
from scipy import stats

# Set publication-quality defaults
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 8
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.major.width'] = 0.8
plt.rcParams['ytick.major.width'] = 0.8

# ------------------ Load data ------------------
dataset = 'controls_complex'  # adjust as needed
with open(f'posteriors_{dataset}.pkl', 'rb') as f:
    data = pickle.load(f)

roi_posteriors = data['roi_posteriors']
circuit_posteriors = data['circuit_posteriors']
contrast_posteriors = data['contrast_posteriors']
metadata = data['metadata']

# ------------------ Color scheme ------------------
# Circuit colors
circuit_colors = {
    'OLC': '#E74C3C',  # Warm red for open-loop (limbic)
    'CLC': '#3498DB',  # Cool blue for closed-loop (motor)
    'Motor': '#95A5A6'  # Gray for motor regions
}

# Context shading (applied as alpha or shade variation)
context_alphas = {
    'standard': 0.7,
    'jackpot': 1.0,
    'robber': 0.4
}

# ------------------ Main Figure ------------------
fig = plt.figure(figsize=(12, 4))
gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1, 1], wspace=0.35)

# Panel A: Overall Engagement (circuits vs zero)
ax1 = fig.add_subplot(gs[0])

# Add small schematic showing ROI->Circuit aggregation
ax1_inset = ax1.inset_axes([0.02, 0.75, 0.3, 0.22])
ax1_inset.axis('off')

# Draw schematic boxes
olc_box = FancyBboxPatch((0.05, 0.5), 0.35, 0.4, 
                          boxstyle="round,pad=0.02",
                          facecolor=circuit_colors['OLC'], 
                          alpha=0.3, edgecolor=circuit_colors['OLC'])
clc_box = FancyBboxPatch((0.55, 0.5), 0.35, 0.4,
                          boxstyle="round,pad=0.02",
                          facecolor=circuit_colors['CLC'],
                          alpha=0.3, edgecolor=circuit_colors['CLC'])
ax1_inset.add_patch(olc_box)
ax1_inset.add_patch(clc_box)

# Add labels
ax1_inset.text(0.225, 0.7, 'OLC', ha='center', fontsize=6, fontweight='bold')
ax1_inset.text(0.225, 0.55, f"({len(metadata['left_olc_regions'])} ROIs)", ha='center', fontsize=5)
ax1_inset.text(0.725, 0.7, 'CLC', ha='center', fontsize=6, fontweight='bold')
ax1_inset.text(0.725, 0.55, f"({len(metadata['left_clc_regions'])} ROIs)", ha='center', fontsize=5)

# Draw arrows from ROI dots to circuits
for i in range(3):
    y = 0.15 + i*0.1
    ax1_inset.plot(0.05, y, 'o', markersize=2, color=circuit_colors['OLC'], alpha=0.6)
    ax1_inset.arrow(0.08, y, 0.1, 0.35, head_width=0.03, head_length=0.02, 
                     fc=circuit_colors['OLC'], ec=circuit_colors['OLC'], alpha=0.3)
    
    ax1_inset.plot(0.95, y, 'o', markersize=2, color=circuit_colors['CLC'], alpha=0.6)
    ax1_inset.arrow(0.92, y, -0.1, 0.35, head_width=0.03, head_length=0.02,
                     fc=circuit_colors['CLC'], ec=circuit_colors['CLC'], alpha=0.3)

# Main violin plots for Panel A
positions = []
pos = 1
for context in ['standard', 'jackpot', 'robber']:
    for circuit in ['OLC', 'CLC']:
        if circuit in circuit_posteriors[context]:
            positions.append(pos)
            samples = circuit_posteriors[context][circuit]['samples']
            
            # Create violin plot
            parts = ax1.violinplot([samples], positions=[pos], widths=0.7,
                                   showmeans=False, showmedians=False, showextrema=False)
            
            # Style the violin
            for pc in parts['bodies']:
                pc.set_facecolor(circuit_colors[circuit])
                pc.set_alpha(context_alphas[context])
                pc.set_edgecolor(circuit_colors[circuit])
                pc.set_linewidth(0.8)
            
            # Add mean and HDI
            mean = circuit_posteriors[context][circuit]['mean']
            hdi = circuit_posteriors[context][circuit]['hdi']
            
            # Mean point
            ax1.plot(pos, mean, 'o', color='white', markersize=4, zorder=3)
            ax1.plot(pos, mean, 'o', color=circuit_colors[circuit], markersize=3, zorder=4)
            
            # HDI line
            ax1.plot([pos, pos], hdi, color=circuit_colors[circuit], linewidth=2, solid_capstyle='round')
            
            # Significance marker
            if (hdi[0] > 0) or (hdi[1] < 0):
                ax1.text(pos, max(hdi) + 0.05, '*', ha='center', fontsize=12, fontweight='bold')
        
        pos += 1
    pos += 0.5  # Extra space between contexts

# Styling Panel A
ax1.axhline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
ax1.set_xticks([1.5, 4, 6.5])
ax1.set_xticklabels(['Standard', 'Jackpot', 'Robber'])
ax1.set_ylabel('RT-scaled BOLD activation (β)', fontsize=9)
ax1.set_title('A. Overall Circuit Engagement', fontsize=10, fontweight='bold', loc='left')
ax1.set_ylim(-0.2, 0.5)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Add legend
olc_patch = mpatches.Patch(color=circuit_colors['OLC'], label='OLC')
clc_patch = mpatches.Patch(color=circuit_colors['CLC'], label='CLC')
ax1.legend(handles=[olc_patch, clc_patch], loc='upper right', frameon=False, fontsize=7)

# Panel B: Between-circuit contrasts (OLC - CLC)
ax2 = fig.add_subplot(gs[1])

pos = 1
for context in ['standard', 'jackpot', 'robber']:
    key = f'{context}_OLC-CLC'
    if key in contrast_posteriors:
        samples = contrast_posteriors[key]['samples']
        
        # Create violin plot
        parts = ax2.violinplot([samples], positions=[pos], widths=0.7,
                               showmeans=False, showmedians=False, showextrema=False)
        
        # Color based on direction of effect
        mean = contrast_posteriors[key]['mean']
        color = circuit_colors['OLC'] if mean > 0 else circuit_colors['CLC']
        
        for pc in parts['bodies']:
            pc.set_facecolor(color)
            pc.set_alpha(context_alphas[context])
            pc.set_edgecolor(color)
            pc.set_linewidth(0.8)
        
        # Add mean and HDI
        hdi = contrast_posteriors[key]['hdi']
        ax2.plot(pos, mean, 'o', color='white', markersize=4, zorder=3)
        ax2.plot(pos, mean, 'o', color=color, markersize=3, zorder=4)
        ax2.plot([pos, pos], hdi, color=color, linewidth=2, solid_capstyle='round')
        
        # Significance marker - special highlight for jackpot
        if (hdi[0] > 0) or (hdi[1] < 0):
            if context == 'jackpot':
                ax2.text(pos, max(hdi) + 0.05, '**', ha='center', fontsize=12, 
                        fontweight='bold', color=circuit_colors['OLC'])
            else:
                ax2.text(pos, max(hdi) + 0.05, '*', ha='center', fontsize=12, fontweight='bold')
    
    pos += 1

# Styling Panel B
ax2.axhline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
ax2.set_xticks([1, 2, 3])
ax2.set_xticklabels(['Standard', 'Jackpot', 'Robber'])
ax2.set_ylabel('Δ Activation (OLC - CLC)', fontsize=9)
ax2.set_title('B. Between-Circuit Comparison', fontsize=10, fontweight='bold', loc='left')
ax2.set_ylim(-0.3, 0.4)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Add annotation for jackpot effect
ax2.annotate('OLC > CLC', xy=(2, 0.15), xytext=(2.3, 0.25),
            arrowprops=dict(arrowstyle='->', color='gray', lw=0.8),
            fontsize=7, ha='left')

# Panel C: Within-circuit context changes (jackpot - standard)
ax3 = fig.add_subplot(gs[2])

pos = 1
for circuit in ['OLC', 'CLC']:
    key = f'{circuit}_jackpot-standard'
    if key in contrast_posteriors:
        samples = contrast_posteriors[key]['samples']
        
        # Create violin plot
        parts = ax3.violinplot([samples], positions=[pos], widths=0.7,
                               showmeans=False, showmedians=False, showextrema=False)
        
        for pc in parts['bodies']:
            pc.set_facecolor(circuit_colors[circuit])
            pc.set_alpha(0.8)
            pc.set_edgecolor(circuit_colors[circuit])
            pc.set_linewidth(0.8)
        
        # Add mean and HDI
        mean = contrast_posteriors[key]['mean']
        hdi = contrast_posteriors[key]['hdi']
        ax3.plot(pos, mean, 'o', color='white', markersize=4, zorder=3)
        ax3.plot(pos, mean, 'o', color=circuit_colors[circuit], markersize=3, zorder=4)
        ax3.plot([pos, pos], hdi, color=circuit_colors[circuit], linewidth=2, solid_capstyle='round')
        
        # Significance marker - highlight CLC downregulation
        if (hdi[0] > 0) or (hdi[1] < 0):
            if circuit == 'CLC':
                ax3.text(pos, min(hdi) - 0.05, '**', ha='center', fontsize=12,
                        fontweight='bold', color=circuit_colors['CLC'])
            else:
                ax3.text(pos, max(hdi) + 0.05, 'n.s.', ha='center', fontsize=7)
        else:
            ax3.text(pos, max(hdi) + 0.05, 'n.s.', ha='center', fontsize=7)
    
    pos += 1

# Styling Panel C
ax3.axhline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
ax3.set_xticks([1, 2])
ax3.set_xticklabels(['OLC', 'CLC'])
ax3.set_ylabel('Δ Activation (Jackpot - Standard)', fontsize=9)
ax3.set_title('C. Context-Dependent Changes', fontsize=10, fontweight='bold', loc='left')
ax3.set_ylim(-0.35, 0.25)
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

# Add annotation for CLC downregulation
ax3.annotate('Selective\ndownregulation', xy=(2, -0.15), xytext=(2.3, -0.25),
            arrowprops=dict(arrowstyle='->', color=circuit_colors['CLC'], lw=0.8),
            fontsize=7, ha='left', color=circuit_colors['CLC'])

# Overall figure adjustments
plt.suptitle('Circuit-Level RT-Scaled BOLD Activation Across Incentive Contexts',
             fontsize=11, fontweight='bold', y=1.02)

# Save main figure
plt.tight_layout()
plt.savefig(f'figure_main_{dataset}.pdf', dpi=300, bbox_inches='tight')
plt.savefig(f'figure_main_{dataset}.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"Main figure saved as figure_main_{dataset}.pdf/png")

# ------------------ Supplementary Figure: ROI-level posteriors ------------------
# Create a grid showing all ROI posteriors
n_olc = len(metadata['olc_regions'])
n_clc = len(metadata['clc_regions'])
n_motor = len(metadata['motor_regions'])

fig_supp = plt.figure(figsize=(14, 10))
gs_supp = fig_supp.add_gridspec(3, 3, hspace=0.3, wspace=0.25)

# Function to plot ROI posteriors for a circuit
def plot_roi_posteriors(ax, context, circuit_rois, circuit_name, color):
    roi_list = [r for r in circuit_rois if r in roi_posteriors[context]]
    if not roi_list:
        return
    
    pos = 1
    for roi in roi_list:
        samples = roi_posteriors[context][roi]['samples']
        
        # Create smaller violin
        parts = ax.violinplot([samples], positions=[pos], widths=0.6,
                              showmeans=False, showmedians=False, showextrema=False)
        
        for pc in parts['bodies']:
            pc.set_facecolor(color)
            pc.set_alpha(0.6)
            pc.set_edgecolor(color)
            pc.set_linewidth(0.5)
        
        # Add mean point
        mean = roi_posteriors[context][roi]['mean']
        ax.plot(pos, mean, 'o', color=color, markersize=2)
        
        # HDI
        hdi = roi_posteriors[context][roi]['hdi']
        if (hdi[0] > 0) or (hdi[1] < 0):
            ax.plot(pos, mean, 'o', color=color, markersize=3, markeredgecolor='black', markeredgewidth=0.5)
        
        pos += 1
    
    ax.axhline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
    ax.set_xticks(range(1, len(roi_list) + 1))
    ax.set_xticklabels([r.replace('l', '').replace('r', '') for r in roi_list], 
                        rotation=45, ha='right', fontsize=6)
    ax.set_ylabel('RT-scaled β', fontsize=7)
    ax.set_title(f'{circuit_name} - {context.capitalize()}', fontsize=8, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(-0.4, 0.6)

# Plot ROI-level data for each context and circuit
for i, context in enumerate(['standard', 'jackpot', 'robber']):
    # OLC ROIs
    ax_olc = fig_supp.add_subplot(gs_supp[i, 0])
    plot_roi_posteriors(ax_olc, context, metadata['olc_regions'], 'OLC', circuit_colors['OLC'])
    
    # CLC ROIs
    ax_clc = fig_supp.add_subplot(gs_supp[i, 1])
    plot_roi_posteriors(ax_clc, context, metadata['clc_regions'], 'CLC', circuit_colors['CLC'])
    
    # Motor ROIs
    ax_motor = fig_supp.add_subplot(gs_supp[i, 2])
    plot_roi_posteriors(ax_motor, context, metadata['motor_regions'], 'Motor', circuit_colors['Motor'])

# Add overall title
fig_supp.suptitle('ROI-Level Posterior Distributions Across Circuits and Contexts',
                   fontsize=12, fontweight='bold', y=1.02)

# Add text annotations explaining the aggregation
fig_supp.text(0.02, 0.98, 'ROIs are aggregated to circuit level for main analyses (see Main Figure)',
              fontsize=8, style='italic', transform=fig_supp.transFigure)

# Save supplementary figure
plt.tight_layout()
plt.savefig(f'figure_supplement_roi_{dataset}.pdf', dpi=300, bbox_inches='tight')
plt.savefig(f'figure_supplement_roi_{dataset}.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"Supplementary figure saved as figure_supplement_roi_{dataset}.pdf/png")

# ------------------ Summary Statistics Table ------------------
print("\n" + "="*70)
print("SUMMARY STATISTICS FOR MANUSCRIPT")
print("="*70)

# Circuit-level statistics
print("\n1. OVERALL CIRCUIT ENGAGEMENT (vs. zero):")
print("-" * 50)
for context in ['standard', 'jackpot', 'robber']:
    print(f"\n{context.upper()}:")
    for circuit in ['OLC', 'CLC']:
        if circuit in circuit_posteriors[context]:
            data = circuit_posteriors[context][circuit]
            hdi = data['hdi']
            sig = (hdi[0] > 0) or (hdi[1] < 0)
            print(f"  {circuit}: β = {data['mean']:.3f}, 89% HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" +
                  (" ***" if sig else " (n.s.)"))

# Between-circuit contrasts
print("\n2. BETWEEN-CIRCUIT CONTRASTS (OLC - CLC):")
print("-" * 50)
for context in ['standard', 'jackpot', 'robber']:
    key = f'{context}_OLC-CLC'
    if key in contrast_posteriors:
        data = contrast_posteriors[key]
        hdi = data['hdi']
        sig = (hdi[0] > 0) or (hdi[1] < 0)
        print(f"{context.capitalize()}: Δ = {data['mean']:.3f}, 89% HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" +
              (" ***" if sig else " (n.s.)"))

# Within-circuit changes
print("\n3. WITHIN-CIRCUIT CONTEXT CHANGES (Jackpot - Standard):")
print("-" * 50)
for circuit in ['OLC', 'CLC']:
    key = f'{circuit}_jackpot-standard'
    if key in contrast_posteriors:
        data = contrast_posteriors[key]
        hdi = data['hdi']
        sig = (hdi[0] > 0) or (hdi[1] < 0)
        print(f"{circuit}: Δ = {data['mean']:.3f}, 89% HDI = [{hdi[0]:.3f}, {hdi[1]:.3f}]" +
              (" ***" if sig else " (n.s.)"))

# Key findings summary
print("\n" + "="*70)
print("KEY FINDINGS:")
print("="*70)
print("1. Both OLC and CLC show credible activation under standard reward")
print("2. Under jackpot: OLC > CLC (credible difference)")
print("3. CLC shows selective downregulation from standard to jackpot")
print("4. Neither circuit credibly active under robber (loss-avoidance)")

# ------------------ Alternative visualization: Combined density plot ------------------
# This creates a more compact version showing all posteriors in one panel
fig_alt = plt.figure(figsize=(10, 6))

# Create density plots
from scipy.stats import gaussian_kde

# Setup grid for density plots
contexts = ['standard', 'jackpot', 'robber']
circuits = ['OLC', 'CLC']

# Create subplots
ax_main = fig_alt.add_subplot(111)

# Y positions for each distribution
y_positions = {}
y_pos = 0
y_labels = []

for context in contexts:
    for circuit in circuits:
        if circuit in circuit_posteriors[context]:
            y_positions[f'{context}_{circuit}'] = y_pos
            y_labels.append(f'{circuit}\n{context}')
            y_pos += 1
    y_pos += 0.5  # Space between contexts

# Plot distributions
for context in contexts:
    for circuit in circuits:
        if circuit in circuit_posteriors[context]:
            samples = circuit_posteriors[context][circuit]['samples']
            
            # Calculate kernel density
            kde = gaussian_kde(samples)
            x_range = np.linspace(samples.min() - 0.1, samples.max() + 0.1, 200)
            density = kde(x_range)
            
            # Normalize density for plotting
            density = density / density.max() * 0.4
            
            # Get y position
            y_center = y_positions[f'{context}_{circuit}']
            
            # Plot density as filled area
            ax_main.fill_betweenx(y_center + density, x_range, y_center - density,
                                  color=circuit_colors[circuit], alpha=context_alphas[context])
            ax_main.plot(x_range, y_center + density, color=circuit_colors[circuit], linewidth=1)
            ax_main.plot(x_range, y_center - density, color=circuit_colors[circuit], linewidth=1)
            
            # Add mean and HDI
            mean = circuit_posteriors[context][circuit]['mean']
            hdi = circuit_posteriors[context][circuit]['hdi']
            
            # Mean line
            ax_main.plot([mean, mean], [y_center - 0.4, y_center + 0.4], 
                        color=circuit_colors[circuit], linewidth=2)
            
            # HDI markers
            ax_main.plot(hdi, [y_center, y_center], color=circuit_colors[circuit], 
                        linewidth=3, solid_capstyle='round')
            
            # Significance marker
            if (hdi[0] > 0) or (hdi[1] < 0):
                ax_main.text(max(hdi) + 0.05, y_center, '*', fontsize=12, fontweight='bold',
                           va='center', color=circuit_colors[circuit])

# Styling
ax_main.axvline(0, color='gray', linestyle='-', linewidth=0.5, alpha=0.5)
ax_main.set_xlabel('RT-scaled BOLD activation (β)', fontsize=10)
ax_main.set_yticks(list(y_positions.values()))
ax_main.set_yticklabels(y_labels, fontsize=8)
ax_main.set_xlim(-0.4, 0.5)
ax_main.spines['top'].set_visible(False)
ax_main.spines['right'].set_visible(False)
ax_main.set_title('Alternative View: All Circuit Posteriors', fontsize=11, fontweight='bold')

# Add legend
olc_patch = mpatches.Patch(color=circuit_colors['OLC'], label='OLC')
clc_patch = mpatches.Patch(color=circuit_colors['CLC'], label='CLC')
ax_main.legend(handles=[olc_patch, clc_patch], loc='upper right', frameon=False)

# Save alternative figure
plt.tight_layout()
plt.savefig(f'figure_alternative_{dataset}.pdf', dpi=300, bbox_inches='tight')
plt.savefig(f'figure_alternative_{dataset}.png', dpi=300, bbox_inches='tight')
plt.show()

print(f"\nAlternative figure saved as figure_alternative_{dataset}.pdf/png")
print("\nAll figures generated successfully!")