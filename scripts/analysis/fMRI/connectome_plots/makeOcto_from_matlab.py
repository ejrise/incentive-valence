"""
Connectome Plot Generator - Real Data Version with Opacity Control
====================================================================
Creates publication-quality circular connectome plots from real data.
Figure Specifications:
- Width: 8.9 cm (3.5039 inches)
- DPI: 600 (high resolution for publication)
- Font: Helvetica, 7pt (with Arial fallback)
- Aspect: Square (equal width and height)
Features:
- Loads real correlation and p-value matrices from CSV files
- Filters connections by p-value threshold
- Applies region name mapping
- Ribbon-style connections (thin at edges, thick in middle)
- Color-coded by correlation strength
- Node clustering/grouping with same color scheme
- Automatic label rotation and positioning
- Non-connected nodes labels have reduced opacity (0.25)
- Alphabetized regions within clusters
- Handles missing nodes (keeps positions consistent)
- Only plots positive connections
- option to FDR correct or not
Usage:
    model = "ROI_full"  # Model name
    seed = "L_PUTv"     # Seed region (in original format)
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.io as sio
import matplotlib.patches as mpatches
import os
from statsmodels.stats.multitest import multipletests

# ========== CONFIGURATION ==========
model = "ROI_no_dPut"  # Model name
seed = "L_PUTv"     # Seed region (in original format like "L_PUTv")
use_fdr = True

# Colorbar range control
# Set to None to auto-detect from data, or specify [min, max] for fixed range
# Example: colorbar_range = [-5, 5] for fixed range
# Example: colorbar_range = None for auto-detection
colorbar_range = [-18,18]  # None = auto from data, or [min, max] for fixed range
# ===================================

# Set font to Helvetica with size 7
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans']
plt.rcParams['font.size'] = 7
plt.rcParams['axes.linewidth'] = 0.5
plt.rcParams['xtick.major.width'] = 0.5
plt.rcParams['ytick.major.width'] = 0.5

# Region name lookup table
REGION_LOOKUP = {
    'LizAtlas.L_BF_ch1-3': 'L_SA',
    'LizAtlas.L_BF_ch4': 'L_NBM',
    'LizAtlas.L_CMA': 'L_CMA',
    'LizAtlas.L_GPi': 'L_GPi',
    'LizAtlas.L_M1_ul': 'L_M1_UL',
    'LizAtlas.L_NAc': 'L_NAc',
    'LizAtlas.L_PMd': 'L_PMd',
    'LizAtlas.L_PMv': 'L_PMv',
    'LizAtlas.L_SMA': 'L_SMA',
    'LizAtlas.L_STN': 'L_STN',
    'LizAtlas.L_ThalVL': 'L_VL',
    'LizAtlas.R_BF_ch1-3': 'R_SA',
    'LizAtlas.R_BF_ch4': 'R_NBM',
    'LizAtlas.R_CMA': 'R_CMA',
    'LizAtlas.R_GPi': 'R_GPi',
    'LizAtlas.R_M1_ul': 'R_M1_UL',
    'LizAtlas.R_NAc': 'R_NAc',
    'LizAtlas.R_PMd': 'R_PMd',
    'LizAtlas.R_PMv': 'R_PMv',
    'LizAtlas.R_SMA': 'R_SMA',
    'LizAtlas.R_STN': 'R_STN',
    'LizAtlas.R_ThalVL': 'R_VL',
    'L_Amy_BL_Complex': 'L_BLA',
    'R_Amy_BL_Complex': 'R_BLA',
    'L_Amy_CEN_Complex': 'L_CeA',
    'R_Amy_CEN_Complex': 'R_CeA',
    'LizAtlas.R_dPut': 'R_PUTd',
    'LizAtlas.L_dPut': 'L_PUTd',
    'LizAtlas.L_vPut': 'L_PUTv',
    'LizAtlas.R_vPut': 'R_PUTv',
}

def load_data(model_name, data_dir='.'):
    """Load p-value and statistic matrices from .mat file."""
    mat_path = os.path.join(data_dir, f'{model_name}.mat')
    
    if not os.path.exists(mat_path):
        raise FileNotFoundError(f"MAT file not found: '{mat_path}'")
    
    print(f"Loading: {mat_path}")
    
    mat = sio.loadmat(mat_path)
    results = mat['summary'][0,0]['results'][0,0]
    
    # Extract matrices and names
    stat_mat = results['RRC_F']
    pval_mat = results['RRC_p']
    names_raw = results['RRC_names'].flatten()
    names = [str(n[0]) for n in names_raw]
    
    # Map to short names
    mapped_names = [REGION_LOOKUP.get(n, n) for n in names]
    
    # Create DataFrames
    pval_df = pd.DataFrame(pval_mat, index=mapped_names, columns=mapped_names)
    stat_df = pd.DataFrame(stat_mat, index=mapped_names, columns=mapped_names)
    
    return pval_df, stat_df

def extract_seed_connections(seed, stat_df, pval_df, pval_threshold=0.01, 
                            use_fdr=False, fdr_method='upper_triangle', fdr_alpha=0.05, 
                            pvals_are_twotailed=True):
    """
    Extract connections for a seed region filtered by p-value threshold or FDR.
    
    Parameters:
    -----------
    seed : str
        Seed region name (e.g., 'L_PUTv')
    stat_df : pandas.DataFrame
        Statistic matrix
    pval_df : pandas.DataFrame
        P-value matrix
    pval_threshold : float
        P-value threshold for significance when use_fdr=False (default: 0.01)
    use_fdr : bool
        If True, use FDR correction instead of fixed p-value threshold (default: False)
    fdr_method : str
        Scope of FDR correction (default: 'seed_row'):
        - 'seed_row': FDR within seed's row only
        - 'entire_matrix': FDR across entire matrix (both triangles)
        - 'upper_triangle': FDR across upper triangle only (CONN toolbox method)
    fdr_alpha : float
        FDR alpha level for significance (default: 0.05)
    pvals_are_twotailed : bool
        Whether p-values are already two-tailed (default: True)
        If False, will convert one-tailed to two-tailed
        
    Returns:
    --------
    filtered_stats : pandas.Series
        Statistics for significant connections from seed
    """
    # Get the seed row from both matrices
    seed_stats = stat_df.loc[seed]
    seed_pvals = pval_df.loc[seed]
    
    # Determine significance mask based on method
    if use_fdr:
        print(f"Using FDR correction with method: {fdr_method}, alpha: {fdr_alpha}")
        
        if fdr_method == 'seed_row':
            # Apply FDR only to the seed's row
            # Remove self-connection before FDR correction
            mask_no_self = seed_pvals.index != seed
            pvals_no_self = seed_pvals[mask_no_self].values
            
            # Convert to two-tailed if needed
            if not pvals_are_twotailed:
                pvals_no_self = 2 * np.minimum(pvals_no_self, 1 - pvals_no_self)
                print("  Converted one-tailed p-values to two-tailed")
            
            # Perform FDR correction (returns rejected, pvals_corrected, alphac_sidak, alphac_bonf)
            rejected, pvals_corrected, _, _ = multipletests(pvals_no_self, alpha=fdr_alpha, method='fdr_bh')
            
            # Create significance mask
            significant_mask = pd.Series(False, index=seed_pvals.index)
            significant_mask[seed_pvals[mask_no_self].index[rejected]] = True
            
        elif fdr_method == 'entire_matrix':
            # Apply FDR across the entire correlation matrix
            # Flatten the p-value matrix (excluding diagonal)
            n = len(pval_df)
            all_pvals = []
            all_indices = []
            
            for i in range(n):
                for j in range(n):
                    if i != j:  # Exclude diagonal
                        all_pvals.append(pval_df.iloc[i, j])
                        all_indices.append((pval_df.index[i], pval_df.columns[j]))
            
            # Convert to two-tailed if needed
            if not pvals_are_twotailed:
                all_pvals = [2 * min(p, 1 - p) for p in all_pvals]
                print("  Converted one-tailed p-values to two-tailed")
            
            # Perform FDR correction on all p-values (returns rejected, pvals_corrected, alphac_sidak, alphac_bonf)
            rejected, pvals_corrected, _, _ = multipletests(all_pvals, alpha=fdr_alpha, method='fdr_bh')
            
            # Create a set of significant connections
            significant_connections = set()
            for idx, is_significant in enumerate(rejected):
                if is_significant:
                    significant_connections.add(all_indices[idx])
            
            # Create significance mask for the seed row
            significant_mask = pd.Series(False, index=seed_pvals.index)
            for region in seed_pvals.index:
                if (seed, region) in significant_connections:
                    significant_mask[region] = True
                    
        elif fdr_method == 'upper_triangle':
            # CONN TOOLBOX METHOD: Apply FDR across upper triangle only
            # This avoids double-counting symmetric connections
            print("  Using CONN toolbox method (upper triangle only)")
            
            n = len(pval_df)
            upper_tri_pvals = []
            upper_tri_indices = []
            
            # Extract upper triangle (i < j, excluding diagonal)
            for i in range(n):
                for j in range(i + 1, n):
                    upper_tri_pvals.append(pval_df.iloc[i, j])
                    upper_tri_indices.append((pval_df.index[i], pval_df.columns[j]))
            
            # Convert to two-tailed if needed
            if not pvals_are_twotailed:
                upper_tri_pvals = [2 * min(p, 1 - p) for p in upper_tri_pvals]
                print("  Converted one-tailed p-values to two-tailed")
            
            # Perform FDR correction on upper triangle only
            rejected, pvals_corrected, _, _ = multipletests(upper_tri_pvals, alpha=fdr_alpha, method='fdr_bh')
            
            # Create a set of significant connections (bidirectional)
            significant_connections = set()
            for idx, is_significant in enumerate(rejected):
                if is_significant:
                    roi_i, roi_j = upper_tri_indices[idx]
                    # Add both directions since matrix is symmetric
                    significant_connections.add((roi_i, roi_j))
                    significant_connections.add((roi_j, roi_i))
            
            # Create significance mask for the seed row
            significant_mask = pd.Series(False, index=seed_pvals.index)
            for region in seed_pvals.index:
                if (seed, region) in significant_connections:
                    significant_mask[region] = True
            
            print(f"  Total unique connections tested: {len(upper_tri_pvals)} (upper triangle)")
        else:
            raise ValueError(f"Invalid fdr_method: {fdr_method}. Must be 'seed_row', 'entire_matrix', or 'upper_triangle'")
        
        print(f"  FDR correction: {significant_mask.sum()} significant connections found")
    else:
        # Use fixed p-value threshold
        print(f"Using fixed p-value threshold: {pval_threshold}")
        significant_mask = seed_pvals < pval_threshold
    
    filtered_stats = seed_stats[significant_mask]
    
    # Remove self-connection if present
    if seed in filtered_stats.index:
        filtered_stats = filtered_stats.drop(seed)
    
    return filtered_stats

def create_correlation_matrix_from_seed(seed_connections, all_regions):
    """
    Create a full correlation matrix from seed connections.
    Only the seed row will have values; all other connections are zero.
    
    Parameters:
    -----------
    seed_connections : pandas.Series
        Significant connections from seed region
    all_regions : list
        List of all region names in desired order
        
    Returns:
    --------
    corr_matrix : numpy.ndarray
        Full correlation matrix with seed row populated
    seed_idx : int
        Index of seed region in the matrix
    """
    n_regions = len(all_regions)
    corr_matrix = np.zeros((n_regions, n_regions))
    
    # Find seed index
    seed_idx = all_regions.index(seed_connections.name) if hasattr(seed_connections, 'name') else None
    
    # Populate seed row with connections
    for region, value in seed_connections.items():
        if region in all_regions:
            target_idx = all_regions.index(region)
            if seed_idx is not None:
                corr_matrix[seed_idx, target_idx] = value
                corr_matrix[target_idx, seed_idx] = value  # Make symmetric
    
    return corr_matrix, seed_idx

def plot_connectome(corr_matrix, labels=None, node_groups=None, threshold=0.0, 
                   title='Brain Connectivity', figsize=(3.5039, 3.5039),
                   colormap='RdYlBu_r', show_colorbar=True, seed_node=None, 
                   rotation_degrees=0, non_connected_alpha=0.25, node_exists=None,
                   colorbar_range=None):
    """
    Create a circular connectome plot.
    
    Parameters:
    -----------
    corr_matrix : numpy.ndarray
        Correlation matrix (n_regions x n_regions)
    labels : list, optional
        Labels for each region
    node_groups : list or numpy.ndarray, optional
        Group assignment for each node (e.g., [0, 0, 1, 1, 2, 2])
    threshold : float
        Minimum absolute correlation to display
    title : str
        Plot title
    figsize : tuple
        Figure size in inches (8.9cm = 3.5039 inches)
    colormap : str
        Matplotlib colormap name
    show_colorbar : bool
        Whether to show colorbar
    seed_node : str, optional
        Label of the seed node to highlight with a red box
    rotation_degrees : float
        Rotation angle in degrees (clockwise)
    non_connected_alpha : float
        Opacity for non-connected nodes and labels (default: 0.25)
    node_exists : list or numpy.ndarray, optional
        Boolean array indicating which nodes exist in the data
    colorbar_range : list or None, optional
        Fixed colorbar range as [min, max]. If None, auto-detect from data.
    """
    n_regions = corr_matrix.shape[0]
    
    # Generate default labels if none provided
    if labels is None:
        labels = [f'Region_{i+1}' for i in range(n_regions)]
    
    # Default node_exists to all True if not provided
    if node_exists is None:
        node_exists = np.ones(n_regions, dtype=bool)
    else:
        node_exists = np.array(node_exists)
    
    # Handle node grouping/clustering
    if node_groups is not None:
        node_groups = np.array(node_groups)
        # Sort nodes by group to cluster them together
        sorted_indices = np.argsort(node_groups)
        labels = [labels[i] for i in sorted_indices]
        corr_matrix = corr_matrix[sorted_indices][:, sorted_indices]
        node_groups = node_groups[sorted_indices]
        node_exists = node_exists[sorted_indices]
        
        # Calculate group boundaries for visual separation
        unique_groups = np.unique(node_groups)
        group_sizes = [np.sum(node_groups == g) for g in unique_groups]
        group_boundaries = np.cumsum([0] + group_sizes)
    else:
        group_boundaries = None
    
    # Determine which nodes have connections (for opacity control)
    seed_idx = None
    if seed_node is not None:
        try:
            seed_idx = labels.index(seed_node)
        except ValueError:
            # Seed node not in labels
            pass
    
    # Create a boolean array for connected nodes
    has_connection = np.zeros(n_regions, dtype=bool)
    if seed_idx is not None:
        # Mark seed as connected
        has_connection[seed_idx] = True
        # Mark all nodes connected to seed
        has_connection[corr_matrix[seed_idx, :] != 0] = True
    else:
        # If no seed specified, all nodes are "connected"
        has_connection[:] = True
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(aspect='equal'))
    
    # Calculate positions of nodes on circle with clustering
    if group_boundaries is not None:
        scalar = 1.5  # Multiplier for total virtual positions
        total_virtual_positions = int(np.round(n_regions * scalar))
        gap_positions = total_virtual_positions - n_regions
        n_gaps = len(unique_groups)
        gap_size = gap_positions / n_gaps
        
        angle_per_position = 2 * np.pi / total_virtual_positions
        
        angles = []
        current_position = 0
        for i, (start, end) in enumerate(zip(group_boundaries[:-1], group_boundaries[1:])):
            group_size = end - start
            for j in range(group_size):
                angle = current_position * angle_per_position
                angles.append(angle)
                current_position += 1
            current_position += gap_size
        
        angles = np.array(angles)
    else:
        angles = np.linspace(0, 2 * np.pi, n_regions, endpoint=False)
    
    # Apply rotation
    rotation_radians = np.radians(rotation_degrees)
    angles = angles + rotation_radians
    
    radius = 1.0
    
    # Node positions
    x_pos = radius * np.cos(angles)
    y_pos = radius * np.sin(angles)
    
    # Get upper triangle indices (avoid duplicates)
    upper_tri = np.triu_indices(n_regions, k=1)
    
    # Filter connections by threshold
    connections = []
    for i, j in zip(upper_tri[0], upper_tri[1]):
        if abs(corr_matrix[i, j]) > threshold:
            connections.append((i, j, corr_matrix[i, j]))
    
    # Sort connections by absolute value (draw weaker ones first)
    connections.sort(key=lambda x: abs(x[2]))
    
    # Create colormap
    cmap = plt.get_cmap(colormap)
    
    # Determine color range
    if colorbar_range is not None:
        # Use specified range
        max_abs_corr = max(abs(colorbar_range[0]), abs(colorbar_range[1]))
        vmin, vmax = colorbar_range[0], colorbar_range[1]
    else:
        # Auto-detect from data
        max_abs_corr = max([abs(c[2]) for c in connections]) if connections else 1.0
        vmin, vmax = -max_abs_corr, max_abs_corr
    
    # Draw connections as ribbons
    for i, j, corr_val in connections:
        # Start and end points
        start = np.array([x_pos[i], y_pos[i]])
        end = np.array([x_pos[j], y_pos[j]])
        
        # Calculate angular distance between nodes
        angle_i = angles[i]
        angle_j = angles[j]
        angular_distance = abs(angle_j - angle_i)
        # Handle wrap-around (e.g., if one is at 0° and other at 350°)
        if angular_distance > np.pi:
            angular_distance = 2 * np.pi - angular_distance
        
        # Scale control radius based on angular distance
        # Nearby nodes (small angular distance) get small arcs
        # Distant nodes (large angular distance) get larger arcs
        # Normalize angular distance to [0, 1] where π is max distance
        normalized_distance = angular_distance / np.pi
        control_radius = 0.95 - 0.90 * normalized_distance  # 0.95..0.35
        
        # Control point (pulled toward center)
        mid = (start + end) / 2
        mid_angle = np.arctan2(mid[1], mid[0])
        control = control_radius * np.array([np.cos(mid_angle), np.sin(mid_angle)])
        
        # Normalize correlation to color
        norm_corr = corr_val / max_abs_corr
        color = cmap((norm_corr + 1) / 2)
        
        # Width is uniform for all connections (not based on correlation)
        max_width = 0.05  # Maximum width in middle (same for all)
        edge_width = 0.005  # Thin width at edges
        
        # Create Bezier curve points
        n_points = 100
        t = np.linspace(0, 1, n_points)
        curve_x = (1-t)**2 * start[0] + 2*(1-t)*t * control[0] + t**2 * end[0]
        curve_y = (1-t)**2 * start[1] + 2*(1-t)*t * control[1] + t**2 * end[1]
        
        # Calculate tangent vectors
        dx = np.gradient(curve_x)
        dy = np.gradient(curve_y)
        
        # Add organic "kick" near edges
        kick_profile = np.zeros_like(t)
        edge_zone = 0.15
        kick_amount = 0.01
        
        mask_start = t < edge_zone
        kick_profile[mask_start] = kick_amount * np.sin(np.pi * t[mask_start] / edge_zone)
        
        mask_end = t > (1 - edge_zone)
        kick_profile[mask_end] = kick_amount * np.sin(np.pi * (1 - t[mask_end]) / edge_zone)
        
        lengths = np.sqrt(dx**2 + dy**2)
        perp_x_curve = -dy / (lengths + 1e-10)
        perp_y_curve = dx / (lengths + 1e-10)
        
        kick_direction = 1 if (i + j) % 2 == 0 else -1
        curve_x = curve_x + perp_x_curve * kick_profile * kick_direction
        curve_y = curve_y + perp_y_curve * kick_profile * kick_direction
        
        # Width varies: thin at edges, thick in middle
        t_centered = 2 * t - 1
        width_profile = 1 - np.abs(t_centered)**1.5
        widths = edge_width + (max_width - edge_width) * width_profile
        
        # Recalculate perpendicular direction
        dx = np.gradient(curve_x)
        dy = np.gradient(curve_y)
        lengths = np.sqrt(dx**2 + dy**2)
        
        perp_x = -dy / lengths
        perp_y = dx / lengths
        
        # Create ribbon edges
        top_x = curve_x + perp_x * widths / 2
        top_y = curve_y + perp_y * widths / 2
        bottom_x = curve_x - perp_x * widths / 2
        bottom_y = curve_y - perp_y * widths / 2
        
        ribbon_x = np.concatenate([top_x, bottom_x[::-1]])
        ribbon_y = np.concatenate([top_y, bottom_y[::-1]])
        
        ribbon = mpatches.Polygon(np.column_stack([ribbon_x, ribbon_y]),
                                 facecolor=color,
                                 edgecolor='none',
                                 alpha=0.6)
        ax.add_patch(ribbon)
    
    # Define group colors (same as original)
    group_colors_rgb = {
        0: np.array([252/255, 242/255, 129/255]),
        1: np.array([0/255, 127/255, 255/255]),
        2: np.array([0/255, 0/255, 138/255]) * 0.9
    }
    
    # Draw nodes only for existing connected regions
    node_size = 40
    if node_groups is not None:
        for i in range(n_regions):
            if has_connection[i] and node_exists[i]:  # Only draw if exists and connected
                node_color = group_colors_rgb[node_groups[i]]
                ax.scatter(x_pos[i], y_pos[i], s=node_size, c=[node_color], 
                          edgecolors=[.9,.9,.9], zorder=10, linewidths=.70)
    else:
        for i in range(n_regions):
            if has_connection[i] and node_exists[i]:  # Only draw if exists and connected
                ax.scatter(x_pos[i], y_pos[i], s=node_size, c='lightgray', 
                          edgecolors=[.9,.9,.9], zorder=10, linewidths=.70)
    
    # Add labels with better positioning and variable opacity
    label_radius = 1.05
    for i, (angle, label) in enumerate(zip(angles, labels)):
        # Only draw labels for nodes that exist
        if not node_exists[i]:
            continue
            
        x_label = label_radius * np.cos(angle)
        y_label = label_radius * np.sin(angle)
        
        normalized_angle = np.arctan2(np.sin(angle), np.cos(angle))
        
        if -np.pi/2 <= normalized_angle <= np.pi/2:
            ha = 'left'
            rotation = np.degrees(normalized_angle)
        else:
            ha = 'right'
            rotation = np.degrees(normalized_angle) + 180
        
        # Set alpha based on connectivity
        label_alpha = 1.0 if has_connection[i] else non_connected_alpha
        
        # Highlight seed node with red box
        bbox_props = None
        if seed_node is not None and label == seed_node:
            bbox_props = dict(boxstyle='round,pad=0.3', facecolor='none', 
                            edgecolor='red', linewidth=1.5)
        
        ax.text(x_label, y_label, label, 
                rotation=rotation,
                rotation_mode='anchor',
                ha=ha, va='center',
                fontweight='normal',
                bbox=bbox_props,
                alpha=label_alpha)
    
    # Set axis properties
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.axis('off')
    
    # Add minimal colorbar (half the previous size)
    if show_colorbar and connections:
        from mpl_toolkits.axes_grid1.inset_locator import inset_axes
        cbar_ax = inset_axes(ax, width="3%", height="12%", loc='lower right',
                            bbox_to_anchor=(0.05, 0.05, 1, 1), bbox_transform=ax.transAxes,
                            borderpad=0)
        
        sm = plt.cm.ScalarMappable(cmap=cmap, 
                                   norm=plt.Normalize(vmin=vmin, vmax=vmax))
        sm.set_array([])
        cbar = plt.colorbar(sm, cax=cbar_ax)
        cbar.set_ticks([vmin, vmax])
        cbar.set_ticklabels([f'{vmin:.1f}', f'{vmax:.1f}'])
        cbar.ax.tick_params(labelsize=6, size=0, pad=1)
        cbar.outline.set_linewidth(0.5)
    
    plt.tight_layout()
    return fig, ax

# Main execution
if __name__ == "__main__":
    # ========== CONFIGURATION ==========
    # LEVER 1: Method for determining significance
    # True = use FDR correction, False = use fixed p-value threshold
    
    # If use_fdr = False:
    pval_threshold = 0.01  # Fixed p-value threshold for significance
    
    # If use_fdr = True:
    fdr_alpha = 0.05  # FDR alpha level (typically 0.05)
    
    # LEVER 2: Scope of FDR correction (only relevant if use_fdr = True)
    fdr_method = 'upper_triangle'  # Options:
                                    # 'seed_row' = FDR within seed's row only (lenient)
                                    # 'entire_matrix' = FDR across entire matrix (very conservative)
                                    # 'upper_triangle' = FDR across upper triangle only 
                                    #                    (CONN toolbox method, RECOMMENDED)
    
    # Are your p-values already two-tailed? (relevant for FDR)
    pvals_are_twotailed = True  # True if your statistical test was two-tailed
                                 # False if one-tailed (will convert to two-tailed)
    
    # Directory containing CSV files (3 levels up, then preprocessed_data/fMRI)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(script_dir, '..', '..', '..', 'data', 'preprocessed', 'fMRI'))
    non_connected_alpha = 0.10  # Opacity for non-connected nodes/labels
    # ===================================
    
    print("=" * 60)
    print("Connectome Plot Generator - Updated Version")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"Seed: {seed}")
    if use_fdr:
        print(f"Significance method: FDR correction")
        print(f"  FDR alpha: {fdr_alpha}")
        print(f"  FDR method: {fdr_method}")
        if fdr_method == 'upper_triangle':
            print(f"  ✓ Using CONN toolbox method (upper triangle only)")
        print(f"  P-values are two-tailed: {pvals_are_twotailed}")
    else:
        print(f"Significance method: Fixed p-value threshold (p < {pval_threshold})")
    print(f"Data directory: {data_dir}")
    print(f"Non-connected opacity: {non_connected_alpha}")
    if colorbar_range is not None:
        print(f"Colorbar range: Fixed [{colorbar_range[0]}, {colorbar_range[1]}]")
    else:
        print(f"Colorbar range: Auto-detect from data")
    print("=" * 60)
    
    # Load data
    print(f"\nLoading data for model: {model}")
    try:
        pval_df, stat_df = load_data(model, data_dir=data_dir)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print(f"\nCurrent working directory: {os.getcwd()}")
        print(f"\nPlease ensure:")
        print(f"  1. Create a '{data_dir}' folder in the same directory as this script")
        print(f"  2. Place these files in the '{data_dir}' folder:")
        print(f"     - {model}_pvalMat.csv")
        print(f"     - {model}_statMat.csv")
        exit(1)
    
    # Extract seed connections
    print(f"Extracting connections for seed: {seed}")
    seed_connections = extract_seed_connections(
        seed, stat_df, pval_df, 
        pval_threshold=pval_threshold,
        use_fdr=use_fdr,
        fdr_method=fdr_method,
        fdr_alpha=fdr_alpha,
        pvals_are_twotailed=pvals_are_twotailed
    )
    
    # Filter to only positive connections
    seed_connections = seed_connections[seed_connections > 0]
    
    if use_fdr:
        print(f"Found {len(seed_connections)} significant connections (FDR alpha={fdr_alpha})")
    else:
        print(f"Found {len(seed_connections)} significant connections (p < {pval_threshold})")
    
    # Define master region list - ALPHABETIZED within groups
    # This defines ALL possible regions; missing ones will have empty positions
    master_regions = {
        0: ['BLA', 'CeA', 'NBM', 'PUTv', 'SA'],           # Group 0 (alphabetical)
        1: ['GPi', 'PUTd', 'VL'],                         # Group 1 (alphabetized)
        2: ['CMA', 'M1UL', 'PMd', 'PMv', 'SMA']  # Group 2 (alphabetical)
    }
    
    # Control reading direction for each group after rotation
    # True = forward (A-Z clockwise), False = reverse (A-Z counter-clockwise)
    # Adjust these based on your rotation to ensure A-Z reads "down"
    group_forward = {
        0: True,   # Group 0: read forward
        1: False,  # Group 1: read reverse (for better "down" reading after 180° rotation)
        2: False   # Group 2: read reverse (INVERTED for navy group)
    }
    
    def format_region_label(region, laterality):
        """Format region label: 'PUTv L' instead of 'L_PUTv', with M1_UL subscript"""
        if region == 'M1UL':
            return f'M1$_{{UL}}$ ({laterality})'
        else:
            return f'{region} ({laterality})'
    
    def create_label_from_short(short_region, laterality):
        """Create full label name that matches REGION_LOOKUP output"""
        if short_region == 'M1UL':
            return f'{laterality}_M1_UL'
        else:
            return f'{laterality}_{short_region}'
    
    # Create labels and groups, respecting reading direction
    labels = []
    label_short_names = []  # For matching with data
    node_groups = []
    
    for group_id in sorted(master_regions.keys()):
        regions = master_regions[group_id].copy()
        
        # Reverse if needed for better reading direction
        if not group_forward[group_id]:
            regions = regions[::-1]
        
        for region in regions:
            # Add L and R versions
            for laterality in ['L', 'R']:
                labels.append(format_region_label(region, laterality))
                label_short_names.append(create_label_from_short(region, laterality))
                node_groups.append(group_id)
    
    print(f"\nTotal possible regions: {len(labels)}")
    print(f"Regions defined in master list: {list(set([r.split()[0] for r in labels]))}")
    
    # Check which nodes exist in the data
    available_regions = set(stat_df.index)
    node_exists = np.array([short_name in available_regions for short_name in label_short_names])
    print(f"Regions present in data: {np.sum(node_exists)}")
    print(f"Missing regions: {[label_short_names[i] for i in range(len(node_exists)) if not node_exists[i]]}")
    
    # Create correlation matrix from seed connections
    n_regions = len(labels)
    corr_matrix = np.zeros((n_regions, n_regions))
    
    # Find seed index and formatted seed label
    seed_idx = label_short_names.index(seed) if seed in label_short_names else None
    seed_label = labels[seed_idx] if seed_idx is not None else None
    
    print(f"Seed '{seed}' displayed as: '{seed_label}'")
    
    # Populate seed row with connections (only if both seed and target exist)
    for target_region, value in seed_connections.items():
        if target_region in label_short_names:
            target_idx = label_short_names.index(target_region)
            if seed_idx is not None and node_exists[seed_idx] and node_exists[target_idx]:
                corr_matrix[seed_idx, target_idx] = value
                corr_matrix[target_idx, seed_idx] = value  # Make symmetric
    
    # Create connectome plot
    fig, ax = plot_connectome(
        corr_matrix, 
        labels=labels,
        node_groups=node_groups,
        threshold=0.0,
        colormap='RdYlBu_r',
        seed_node=seed_label,
        rotation_degrees=180,
        non_connected_alpha=non_connected_alpha,
        node_exists=node_exists,
        colorbar_range=colorbar_range
    )
    
    # Save figure
    output_filename = f'connectome_{model}_{seed}.png'
    plt.savefig(output_filename, dpi=600, bbox_inches='tight')
    print(f"\nPlot saved to: {output_filename}")
    print(f"Number of regions in plot: {n_regions} ({np.sum(node_exists)} present, {n_regions - np.sum(node_exists)} missing)")
    print(f"Number of significant connections: {len(seed_connections)}")
    print(f"Statistic range: [{seed_connections.min():.3f}, {seed_connections.max():.3f}]")
    print(f"Seed node: {seed} (displayed as '{seed_label}')")
    
    plt.show()