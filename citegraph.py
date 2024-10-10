import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import mplcursors
from matplotlib.colors import LinearSegmentedColormap

def parse_articles(file_path):
    """
    Parses the articles file and returns articles and citations dictionaries.
    """
    articles = {}
    citations = {}
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    current_entry = None
    state = None  # Keeps track of which part of the entry we're parsing
    for line in lines:
        line = line.strip()
        if not line:
            continue  # Skip empty lines
        if line == '[Entry]':
            if current_entry:
                # Process the previous entry
                title = current_entry['title']
                year = current_entry['year']
                cited_articles = current_entry.get('citations', [])
                articles[title] = {'year': year}
                citations[title] = cited_articles
            # Start a new entry
            current_entry = {'citations': []}
            state = 'title'
        else:
            if state == 'title':
                current_entry['title'] = line
                state = 'year'
            elif state == 'year':
                try:
                    current_entry['year'] = int(line)
                except ValueError:
                    print(f"Error parsing year for article '{current_entry['title']}'. Line: {line}")
                    current_entry['year'] = None
                state = 'citations'
            elif state == 'citations':
                current_entry['citations'].append(line)
    
    # Process the last entry
    if current_entry:
        title = current_entry['title']
        year = current_entry['year']
        cited_articles = current_entry.get('citations', [])
        articles[title] = {'year': year}
        citations[title] = cited_articles
    
    return articles, citations

def main():
    # Parse articles from the file
    articles_file = 'articles.txt'  # Change this to your file path
    articles, citations = parse_articles(articles_file)
    
    # Build the graph
    G = nx.DiGraph()
    
    # Add nodes with the year attribute
    for title, data in articles.items():
        G.add_node(title, year=data['year'])
    
    # Add edges based on citations
    for citing_article, cited_articles in citations.items():
        for cited_article in cited_articles:
            if cited_article in articles:
                G.add_edge(citing_article, cited_article)
            else:
                print(f"Warning: '{cited_article}' cited by '{citing_article}' not found in articles list.")
    
    # Position nodes by year
    years = sorted({data['year'] for _, data in G.nodes(data=True)})
    y_spacing = 10  # Adjust vertical spacing as needed
    num_years = len(years)
    
    # Map years to Y positions (earliest year at the top)
    year_to_y = {}
    for idx, year in enumerate(years):
        y = (num_years - idx - 1) * y_spacing  # Earliest year at highest Y value
        year_to_y[year] = y
    
    # Assign X positions to spread out nodes horizontally within the same year
    x_positions = {}
    max_nodes_in_year = max(len([n for n, data in G.nodes(data=True) if data['year'] == year]) for year in years)
    x_spacing = 10  # Adjust horizontal spacing as needed
    
    for year in years:
        nodes_in_year = [n for n, data in G.nodes(data=True) if data['year'] == year]
        num_nodes = len(nodes_in_year)
        total_width = (max_nodes_in_year - 1) * x_spacing
        start_x = -total_width / 2
        if num_nodes == 1:
            x_positions[nodes_in_year[0]] = 0  # Center single nodes
        else:
            offset = ((max_nodes_in_year - num_nodes) * x_spacing) / 2
            for idx, node in enumerate(nodes_in_year):
                x_positions[node] = start_x + idx * x_spacing + offset
    
    # Combine X and Y positions
    pos = {}
    for node in G.nodes():
        year = G.nodes[node]['year']
        pos[node] = (x_positions[node], year_to_y[year])
    
    # Prepare labels with truncated titles
    labels = {}
    for node in G.nodes():
        words = node.split()
        if len(words) > 3:
            labels[node] = ' '.join(words[:3]) + '...'
        else:
            labels[node] = node
    
    # Compute in-degree of each node
    in_degrees = dict(G.in_degree())
    
    # Normalize in-degree values for colormap
    in_degree_values = list(in_degrees.values())
    norm = colors.Normalize(vmin=min(in_degree_values), vmax=max(in_degree_values))
    
    # Create a custom pastel colormap from pastel yellow to pastel red
    cmap = LinearSegmentedColormap.from_list('pastel_yellow_red', ['#FFFFCC', '#FFD1B2', '#FF6666'])
    
    node_colors = [cmap(norm(in_degrees[node])) for node in G.nodes()]
    
    # Draw the graph
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Draw nodes with computed colors
    nodes_collection = nx.draw_networkx_nodes(G, pos, node_size=2000, node_color=node_colors, ax=ax)
    
    # Draw edges with arrows
    nx.draw_networkx_edges(
        G,
        pos,
        arrows=True,
        arrowstyle='->',
        arrowsize=30,
        edge_color='black',
        min_source_margin=20,
        min_target_margin=20,
        ax=ax
    )
    
    # Draw labels with truncated titles
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_family='sans-serif', verticalalignment='center', ax=ax)
    
    # Add interactivity with mplcursors
    cursor = mplcursors.cursor(nodes_collection, hover=True, multiple=False)
    
    @cursor.connect("add")
    def on_add(sel):
        node_index = sel.target.index
        node_name = list(G.nodes())[node_index]
        full_title = node_name
        sel.annotation.set_text(full_title)
        sel.annotation.get_bbox_patch().set_alpha(0.9)
    
    # Draw horizontal lines between years
    x_start = - (max_nodes_in_year * x_spacing)
    x_end = (max_nodes_in_year * x_spacing)
    year_y_positions = [year_to_y[year] for year in years]
    
    # Compute positions for horizontal lines (between years)
    for i in range(len(year_y_positions) - 1):
        y_line = (year_y_positions[i] + year_y_positions[i+1]) / 2
        ax.hlines(y_line, x_start, x_end, linestyles='dotted', colors='gray')
    
    # Draw year labels aligned with the articles
    for year in years:
        y = year_to_y[year]
        ax.text(x_start - 5, y, str(year), verticalalignment='center', fontsize=10, horizontalalignment='right')
    
    # Adjust plot limits
    ax.set_xlim(x_start - 10, x_end + 10)
    y_min = min(year_y_positions) - y_spacing / 2 - 5
    y_max = max(year_y_positions) + y_spacing / 2 + 5
    ax.set_ylim(y_min, y_max)
    
    # Hide axes
    ax.axis('off')
    
    # Add title
    ax.set_title('Citation Graph', fontsize=14)
    
    # Add colorbar legend
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.01)
    cbar.set_label('Number of Citations')
    cbar.set_ticks(sorted(set(in_degree_values)))
    
    # Display the graph
    plt.tight_layout()
    plt.show()
    
if __name__ == '__main__':
    main()